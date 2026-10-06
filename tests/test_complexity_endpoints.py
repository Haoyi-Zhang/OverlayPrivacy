"""Exact finite regressions for zero horizon and denominator-one complexity.

Only owned queue inputs are constructed. No policy or traffic is retained.
"""
from fractions import Fraction as F
from itertools import product
from math import lcm
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from checker import check
from model import kernel
from producer import make


def config(rates=("0", "1"), padding="0", horizon=0, tokens=1):
    return dict(scheduler="public-history", queue_capacity=1,
                token_capacity=tokens, horizon=horizon, refill_period=2,
                padding=padding, observe_overflow=True,
                arrival_rates=list(rates), initial_queues=[0, 1])


class ComplexityEndpointTests(unittest.TestCase):
    def test_zero_horizon_still_has_coupling_and_terminal_work(self):
        for mode in ("all-pairs", "ordered-chain"):
            model = kernel(config())
            packet = make(model, mode)
            result = check(model, packet)
            self.assertEqual(result["capacity_bound"], "1")
            self.assertEqual(result["bellman_obligations"], 0)
            self.assertEqual(result["potential_entries"], 8)
            self.assertEqual(len(packet["couplings"]), 8)
            self.assertGreater(result["coupling_entries"], 0)
            self.assertEqual(set(packet["potentials"].values()), {"0"})
            self.assertEqual(result["maximum_rational_bits"], 1)

    def test_integral_probabilities_have_one_bit_not_zero_bits(self):
        for horizon in (0, 1, 2):
            model = kernel(config(horizon=horizon))
            packet = make(model, "ordered-chain")
            for raw in packet["potentials"].values():
                value = F(raw)
                self.assertEqual(value.denominator, 1)
                self.assertLessEqual(value.numerator.bit_length(), 1)
                self.assertEqual(value.denominator.bit_length(), 1)

    def test_exact_denominator_divisibility_and_width_grid(self):
        cases = 0
        rate_pairs = (("0", "0"), ("0", "1"), ("1", "1"),
                      ("0", "1/2"), ("1/3", "2/3"))
        for rates, padding, horizon, tokens in product(
                rate_pairs, ("0", "1/2", "1"), (0, 1, 2), (1, 2)):
            model = kernel(config(rates, padding, horizon, tokens))
            denominator = lcm(*(F(x).denominator for x in (*rates, padding)))
            for mode in ("all-pairs", "ordered-chain"):
                packet = make(model, mode)
                check(model, packet)
                for key, raw in packet["potentials"].items():
                    remaining = horizon - int(key.split(",")[2])
                    grid_denominator = denominator ** (2 * remaining)
                    value = F(raw)
                    self.assertEqual(grid_denominator % value.denominator, 0)
                    self.assertLessEqual(value.numerator.bit_length(), grid_denominator.bit_length())
                    self.assertLessEqual(value.denominator.bit_length(), grid_denominator.bit_length())
            cases += 1
        self.assertEqual(cases, 90)


if __name__ == "__main__":
    unittest.main(verbosity=2)
