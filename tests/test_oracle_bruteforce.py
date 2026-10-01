"""Algorithmically distinct exhaustive policy-table check for the tiny oracle.

The direct path shares the declared one-step kernel from ``model.kernel`` with
the production path. It does not reuse the production oracle's mass-state
recursion, memo table, or any certificate/tree algorithm. The comparison entry
calls ``oracle.capacity`` only to obtain the value under test.
"""
from __future__ import annotations

import argparse
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

History = Tuple[str, ...]
Policy = Dict[History, int]


def production_capacity(model: Mapping[str, object]):
    """Comparison entry for the production scalar dynamic program."""
    from oracle import capacity  # Imported only at the comparison boundary.

    return capacity(model)


def _rows(model: Mapping[str, object]):
    parsed = {}
    for raw_key, raw_row in model["kernel"].items():
        key = tuple(map(int, raw_key.split(",")))
        parsed[key] = [(str(y), int(q), F(p)) for y, q, p in raw_row]
    return parsed


def enumerate_policy_tables(model: Mapping[str, object]) -> Iterable[Policy]:
    """Enumerate complete deterministic public-history tables for a tiny model."""
    config = model["config"]
    horizon = int(config["horizon"])
    capacity_tokens = int(config["token_capacity"])
    refill = int(config["refill_period"])
    alphabet = sorted({str(y) for row in model["kernel"].values() for y, _, _ in row})

    def extend(t: int, balances: Dict[History, int], policy: Policy):
        if t == horizon:
            yield dict(policy)
            return
        histories = sorted(balances)
        choices = [range(2 if balances[history] else 1) for history in histories]
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
    config = model["config"]
    horizon = int(config["horizon"])
    capacity_tokens = int(config["token_capacity"])
    refill = int(config["refill_period"])
    rows = _rows(model)
    channel = []
    for secret, initial_queue in enumerate(config["initial_queues"]):
        mass = {(int(initial_queue), (), capacity_tokens): F(1)}
        for t in range(horizon):
            next_mass = {}
            for (queue, history, balance), weight in mass.items():
                action = policy[history]
                if action not in range(2 if balance else 1):
                    raise RuntimeError("enumerator emitted an infeasible action")
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
            raise RuntimeError("simulated channel row is not normalized")
        channel.append(row)
    return channel


def channel_capacity(channel: Sequence[Mapping[History, F]]) -> F:
    histories = set().union(*(row.keys() for row in channel))
    return sum(
        (max(row.get(history, F(0)) for row in channel) for history in histories),
        F(0),
    )


def brute_capacity(model: Mapping[str, object]):
    best = F(-1)
    policies = 0
    for policy in enumerate_policy_tables(model):
        value = channel_capacity(channel_for_policy(model, policy))
        policies += 1
        if value > best:
            best = value
    return best, policies


def _sorted_histogram(histogram: dict[F, int]) -> dict[str, int]:
    return {str(value): histogram[value] for value in sorted(histogram)}


class OracleBruteForceTests(unittest.TestCase):
    def test_exhaustive_two_slot_grid(self):
        # 192 exact cases: order, initial state, cover, visible overflow, and
        # refill timing all vary. Only scalar optima and aggregate counts remain.
        rates = [
            ("0", "1"),
            ("1", "0"),
            ("1/3", "2/3"),
            ("1/2", "1/2"),
        ]
        initial = [(0, 0), (0, 1), (1, 0), (1, 1)]
        count = policy_count = 0
        optimum_sum = F(0)
        histogram: dict[F, int] = {}
        for rates_pair, queues, padding, overflow, refill in product(
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
                arrival_rates=list(rates_pair),
                initial_queues=list(queues),
            )
            model = kernel(config)
            brute, policies = brute_capacity(model)
            dynamic, _ = production_capacity(model)
            self.assertEqual(brute, dynamic)
            count += 1
            policy_count += policies
            optimum_sum += brute
            histogram[brute] = histogram.get(brute, 0) + 1
        self.__class__.two_slot_cases = count
        self.__class__.two_slot_policy_tables = policy_count
        self.__class__.two_slot_optimum_sum = str(optimum_sum)
        self.__class__.two_slot_value_histogram = _sorted_histogram(histogram)

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
                    **cases[index],
                    "arrival_rates": list(reversed(cases[index]["arrival_rates"])),
                    "initial_queues": list(reversed(cases[index]["initial_queues"])),
                }
                for index in range(0, len(cases), 3)
            ]
        )
        count = policy_count = 0
        optimum_sum = F(0)
        histogram: dict[F, int] = {}
        for config in cases:
            model = kernel(config)
            brute, policies = brute_capacity(model)
            dynamic, _ = production_capacity(model)
            self.assertEqual(brute, dynamic)
            count += 1
            policy_count += policies
            optimum_sum += brute
            histogram[brute] = histogram.get(brute, 0) + 1
        self.__class__.deeper_cases = count
        self.__class__.deeper_policy_tables = policy_count
        self.__class__.deeper_optimum_sum = str(optimum_sum)
        self.__class__.deeper_value_histogram = _sorted_histogram(histogram)


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def run_suite(output: Path) -> dict:
    started = time.process_time()
    for name in (
        "two_slot_cases",
        "two_slot_policy_tables",
        "two_slot_optimum_sum",
        "two_slot_value_histogram",
        "deeper_cases",
        "deeper_policy_tables",
        "deeper_optimum_sum",
        "deeper_value_histogram",
    ):
        if hasattr(OracleBruteForceTests, name):
            delattr(OracleBruteForceTests, name)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OracleBruteForceTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "schema_version": 2,
        "successful": result.wasSuccessful(),
        "test_methods": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "two_slot_cases": getattr(OracleBruteForceTests, "two_slot_cases", 0),
        "two_slot_policy_tables": getattr(OracleBruteForceTests, "two_slot_policy_tables", 0),
        "two_slot_optimum_sum": getattr(OracleBruteForceTests, "two_slot_optimum_sum", "0"),
        "two_slot_value_histogram": getattr(OracleBruteForceTests, "two_slot_value_histogram", {}),
        "deeper_cases": getattr(OracleBruteForceTests, "deeper_cases", 0),
        "deeper_policy_tables": getattr(OracleBruteForceTests, "deeper_policy_tables", 0),
        "deeper_optimum_sum": getattr(OracleBruteForceTests, "deeper_optimum_sum", "0"),
        "deeper_value_histogram": getattr(OracleBruteForceTests, "deeper_value_histogram", {}),
        "retained_output": "scalar optima summaries and aggregate counts only; no optimizing policy",
        "environment_measurements": {
            "cpu_seconds": time.process_time() - started,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
    }
    _atomic_write_json(output, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "oracle-bruteforce.json",
    )
    args = parser.parse_args()
    report = run_suite(args.output)
    if not report["successful"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
