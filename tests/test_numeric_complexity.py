#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
class NumericComplexityTests(unittest.TestCase):
 def test_inventory_is_nonempty_and_exact(self):
  subprocess.run([sys.executable,str(ROOT/'src/numeric_complexity.py')],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
  r=json.loads((ROOT/'results/verification/numeric-complexity.json').read_text())
  self.assertGreater(r['exact_rational_values'],100)
  self.assertGreaterEqual(r['denominator_bits']['maximum'],1)
  self.assertGreaterEqual(r['numerator_bits']['maximum'],1)
if __name__=='__main__': unittest.main(verbosity=2)
