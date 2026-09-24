#!/usr/bin/env python3
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

def scrub(x):
    volatile=('time','seconds','cpu','wall','rss','memory','timestamp','generated_at')
    if isinstance(x,dict): return {k:scrub(v) for k,v in x.items() if not any(t in k.lower() for t in volatile)}
    if isinstance(x,list): return [scrub(v) for v in x]
    return x

def run_checker(seed):
    env=dict(os.environ,PYTHONHASHSEED=str(seed))
    p=subprocess.run([sys.executable,str(ROOT/'src/checker.py'),str(ROOT/'inputs/Q014.json'),str(ROOT/'results/certificates/Q014-ordered-chain.json')],cwd=ROOT,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=60)
    try: return scrub(json.loads(p.stdout))
    except json.JSONDecodeError: return p.stdout.strip()

class HashSeedDeterminismTests(unittest.TestCase):
    def test_checker_payload(self):
        self.assertEqual(run_checker(1),run_checker(987654))
    def test_reviewer_metrics_payload(self):
        out=ROOT/'results/verification/reviewer-utility-tightness.json'
        blobs=[]
        for seed in (1,987654):
            env=dict(os.environ,PYTHONHASHSEED=str(seed))
            subprocess.run([sys.executable,str(ROOT/'src/reviewer_metrics.py')],cwd=ROOT,env=env,check=True,stdout=subprocess.DEVNULL,timeout=60)
            blobs.append(scrub(json.loads(out.read_text(encoding='utf-8'))))
        self.assertEqual(blobs[0],blobs[1])
if __name__=='__main__': unittest.main(verbosity=2)
