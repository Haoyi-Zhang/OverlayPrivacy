#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results/verification/reviewer-utility-tightness.json'
class ReviewerMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable,str(ROOT/'src/reviewer_metrics.py')],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        cls.r=json.loads(OUT.read_text(encoding='utf-8'))
    def test_expected_exact_slice(self):
        self.assertEqual(40,self.r['exact_models'])
        self.assertEqual(10,self.r['tightness']['exact_hits'])
    def test_known_frozen_statistics(self):
        g=self.r['tightness']['absolute_gap']; q=self.r['tightness']['bound_over_exact_ratio']
        self.assertAlmostEqual(0.0792,g['median'],places=4)
        self.assertAlmostEqual(0.7872,g['maximum'],places=4)
        self.assertAlmostEqual(1.396774193548387,q['maximum'],places=12)
    def test_bounds_are_nonnegative(self):
        g=self.r['tightness']['absolute_gap']; q=self.r['tightness']['bound_over_exact_ratio']
        self.assertGreaterEqual(g['minimum'],0)
        self.assertGreaterEqual(q['minimum'],1)
if __name__=='__main__': unittest.main(verbosity=2)
