"""Algorithmically separate exhaustive policy-table check for the tiny public-history oracle.

This test enumerates deterministic public-history scheduler tables, simulates the
resulting exact secret-to-history channel, and compares the largest channel
capacity with ``oracle.capacity``.  It intentionally does not reuse the
oracle's mass-state recursion or expose an optimizing policy.
"""
from __future__ import annotations

import json
import resource
import sys
import time
import unittest
from fractions import Fraction as F
from itertools import product
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from model import kernel  # noqa: E402
from oracle import capacity  # noqa: E402

History = Tuple[str, ...]
Policy = Dict[History, int]


def _rows(model: Mapping[str, object]):
    parsed = {}
    for raw_key, raw_row in model["kernel"].items():
        key = tuple(map(int, raw_key.split(",")))
        parsed[key] = [(str(y), int(q), F(p)) for y, q, p in raw_row]
    return parsed


def enumerate_policy_tables(model: Mapping[str, object]) -> Iterable[Policy]:
    """Enumerate complete deterministic public-history tables for a tiny model."""
    c = model["config"]
    horizon = int(c["horizon"])
    capacity_tokens = int(c["token_capacity"])
    refill = int(c["refill_period"])
    alphabet = sorted({str(y) for row in model["kernel"].values() for y, _, _ in row})

    def extend(t: int, balances: Dict[History, int], policy: Policy):
        if t == horizon:
            yield dict(policy)
            return
        histories = sorted(balances)
        choices = [range(2 if balances[h] else 1) for h in histories]
        for actions in product(*choices):
            next_policy = dict(policy)
            next_balances: Dict[History, int] = {}
            for history, action in zip(histories, actions):
                next_policy[history] = action
                balance_next = min(
                    capacity_tokens,
                    balances[history] - action + int((t + 1) % refill == 0),
                )
                for observation in alphabet:
                    next_balances[history + (observation,)] = balance_next
            yield from extend(t + 1, next_balances, next_policy)

    yield from extend(0, {(): capacity_tokens}, {})


def channel_for_policy(model: Mapping[str, object], policy: Mapping[History, int]):
    """Simulate exact complete public-history rows without the oracle recursion."""
    c = model["config"]
    horizon = int(c["horizon"])
    capacity_tokens = int(c["token_capacity"])
    refill = int(c["refill_period"])
    rows = _rows(model)
    channel = []
    for secret, initial_queue in enumerate(c["initial_queues"]):
        mass = {(int(initial_queue), (), capacity_tokens): F(1)}
        for t in range(horizon):
            next_mass = {}
            for (queue, history, balance), weight in mass.items():
                action = policy[history]
                if action not in range(2 if balance else 1):
                    raise AssertionError("enumerator emitted an infeasible action")
                balance_next = min(
                    capacity_tokens,
                    balance - action + int((t + 1) % refill == 0),
                )
                for observation, queue_next, probability in rows[secret, queue, action]:
                    state = (queue_next, history + (observation,), balance_next)
                    next_mass[state] = next_mass.get(state, F(0)) + weight * probability
            mass = next_mass
        row = {}
        for (_queue, history, _balance), weight in mass.items():
            row[history] = row.get(history, F(0)) + weight
        if sum(row.values(), F(0)) != 1:
            raise AssertionError("simulated channel row is not normalized")
        channel.append(row)
    return channel


def channel_capacity(channel: Sequence[Mapping[History, F]]) -> F:
    histories = set().union(*(row.keys() for row in channel))
    return sum((max(row.get(history, F(0)) for row in channel) for history in histories), F(0))


def brute_capacity(model: Mapping[str, object]):
    best = F(-1)
    policies = 0
    for policy in enumerate_policy_tables(model):
        value = channel_capacity(channel_for_policy(model, policy))
        policies += 1
        if value > best:
            best = value
    return best, policies


class OracleBruteForceTests(unittest.TestCase):
    def test_exhaustive_two_slot_grid(self):
        # 192 exact cases: order, initial state, cover, visible overflow, and
        # refill timing all vary.  Only scalar optima are retained.
        rates = [
            ("0", "1"),
            ("1", "0"),
            ("1/3", "2/3"),
            ("1/2", "1/2"),
        ]
        initial = [(0, 0), (0, 1), (1, 0), (1, 1)]
        count = policy_count = 0
        for lam, queues, padding, overflow, refill in product(
            rates, initial, ("0", "1/2", "1"), (False, True), (1, 2)
        ):
            config = dict(
                scheduler="public-history",
                queue_capacity=1,
                token_capacity=1,
                horizon=2,
                refill_period=refill,
                padding=padding,
                observe_overflow=overflow,
                arrival_rates=list(lam),
                initial_queues=list(queues),
            )
            model = kernel(config)
            brute, policies = brute_capacity(model)
            dynamic, _ = capacity(model)
            self.assertEqual(brute, dynamic)
            count += 1
            policy_count += policies
        self.__class__.two_slot_cases = count
        self.__class__.two_slot_policy_tables = policy_count

    def test_three_slot_and_multi_secret_cases(self):
        # A smaller deeper grid exercises history-dependent balances and
        # multi-secret maxima without visible-overflow policy explosion.
        cases = []
        for padding, refill, token_capacity in product(("0", "1/2", "1"), (1, 2), (1, 2)):
            cases.append(
                dict(
                    scheduler="public-history",
                    queue_capacity=1,
                    token_capacity=token_capacity,
                    horizon=3,
                    refill_period=refill,
                    padding=padding,
                    observe_overflow=False,
                    arrival_rates=["0", "1/2", "1"],
                    initial_queues=[0, 1, 0],
                )
            )
        # Reversed rates and queues guard against accidentally assuming order.
        cases.extend(
            [
                {
                    **cases[i],
                    "arrival_rates": list(reversed(cases[i]["arrival_rates"])),
                    "initial_queues": list(reversed(cases[i]["initial_queues"])),
                }
                for i in range(0, len(cases), 3)
            ]
        )
        count = policy_count = 0
        for config in cases:
            model = kernel(config)
            brute, policies = brute_capacity(model)
            dynamic, _ = capacity(model)
            self.assertEqual(brute, dynamic)
            count += 1
            policy_count += policies
        self.__class__.deeper_cases = count
        self.__class__.deeper_policy_tables = policy_count


def main():
    started = time.process_time()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OracleBruteForceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "successful": result.wasSuccessful(),
        "test_methods": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "two_slot_cases": getattr(OracleBruteForceTests, "two_slot_cases", 0),
        "two_slot_policy_tables": getattr(OracleBruteForceTests, "two_slot_policy_tables", 0),
        "deeper_cases": getattr(OracleBruteForceTests, "deeper_cases", 0),
        "deeper_policy_tables": getattr(OracleBruteForceTests, "deeper_policy_tables", 0),
        "cpu_seconds": time.process_time() - started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "retained_output": "scalar optima and aggregate counts only",
    }
    out = ROOT / "results" / "oracle-bruteforce.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
