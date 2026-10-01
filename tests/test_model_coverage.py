#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
class ModelCoverageTests(unittest.TestCase):
 def test_frozen_model_inventory(self):
  subprocess.run([sys.executable,str(ROOT/'src/model_coverage.py')],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
  r=json.loads((ROOT/'results/verification/model-coverage.json').read_text())
  self.assertEqual(73,r['model_count'])
  self.assertEqual({'Q':27,'S':36,'A':10},r['families'])
  self.assertEqual(73,r['unique_model_encodings'])
  self.assertTrue(all('sha256' not in item for item in r['files']))
if __name__=='__main__': unittest.main(verbosity=2)
