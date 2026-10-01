#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "verification" / "numeric-complexity.json"


class NumericComplexityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(
            [sys.executable, str(ROOT / "src" / "numeric_complexity.py")],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        cls.report = json.loads(OUT.read_text(encoding="utf-8"))

    def test_potential_field_width_is_explicit(self):
        potentials = self.report["potential_values"]
        self.assertEqual("results/certificates/*.json -> potentials[*]", potentials["field_set"])
        self.assertEqual(457555, potentials["values"])
        self.assertEqual(82, potentials["maximum_value_bits"])
        self.assertEqual(82, potentials["maximum_numerator_bits"])
        self.assertEqual(82, potentials["maximum_denominator_bits"])

    def test_aggregate_fields_are_separate(self):
        aggregate = self.report["aggregate_result_fields"]
        self.assertEqual(440, aggregate["values"])
        self.assertEqual(84, aggregate["maximum_numerator_bits"])
        self.assertEqual(82, aggregate["maximum_denominator_bits"])
        self.assertEqual(83, aggregate["by_field"]["capacity_bound"]["maximum_numerator_bits"])
        self.assertEqual(84, aggregate["by_field"]["best_star_bound"]["maximum_numerator_bits"])

    def test_named_witnesses(self):
        named = self.report["named_checks"]
        self.assertEqual(83, named["S030_capacity_bound_numerator_bits"])
        self.assertEqual(84, named["S033_best_star_bound_numerator_bits"])
        self.assertEqual(84, named["S036_best_star_bound_numerator_bits"])
        witnesses = {
            (item["case"], item["field"])
            for item in self.report["aggregate_result_fields"]["maximum_numerator_witnesses"]
        }
        self.assertEqual({("S033", "best_star_bound"), ("S036", "best_star_bound")}, witnesses)

    def test_campaign_metadata_matches_certificates(self):
        consistency = self.report["campaign_record_consistency"]
        self.assertEqual(144, consistency["records_checked"])
        self.assertTrue(consistency["all_match"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
