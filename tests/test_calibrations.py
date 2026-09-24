"""Exact analytic calibration checks, added after the frozen campaign.

These validate proved special cases and continuity inequalities. They are not
additional workload samples or evidence of model-to-deployment conformance.
"""
from __future__ import annotations
import json
import random
import resource
import sys
import time
from fractions import Fraction as F
from itertools import combinations_with_replacement
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from campaign import base
from model import kernel
from producer import make
from checker import check
from oracle import capacity

def cap(rows):
    return sum(max(col) for col in zip(*rows))

def tv(left, right):
    return sum(abs(a-b) for a,b in zip(left,right))/2

def main():
    start = time.process_time()
    one_slot = 0
    for m in (2,3,4):
        for rates in combinations_with_replacement([F(k,4) for k in range(5)],m):
            for p in [F(k,4) for k in range(5)]:
                c=base(m=m,B=1,H=1)
                c.update(arrival_rates=list(map(str,rates)),padding=str(p))
                model=kernel(c)
                expected=1+(1-p)*(rates[-1]-rates[0])
                actual,_=capacity(model)
                verified=check(model,make(model,'ordered-chain'))
                assert actual==expected==F(verified['capacity_bound'])
                one_slot+=1
    # Continuity is tested independently of queues and certificates.
    rng=random.Random(229501)
    continuity=0
    for m in range(2,8):
        for columns in range(2,8):
            for _ in range(3):
                def distribution():
                    row=[rng.randrange(9) for _ in range(columns)]
                    if not sum(row):row[0]=1
                    total=sum(row)
                    return [F(x,total) for x in row]
                left=[distribution() for _ in range(m)]
                right=[distribution() for _ in range(m)]
                error=sum(tv(a,b) for a,b in zip(left,right))
                assert cap(right)<=min(F(m),cap(left)+error)
                continuity+=1
    # Compare the additional equal-initial-queue rate bound to every eligible
    # retained dense canonical result; no favorable-subset selection is used.
    eligible=0
    for path in sorted((ROOT/'results/campaign').glob('*-all-pairs.json')):
        record=json.loads(path.read_text());c=record['config']
        if len(set(c['initial_queues']))!=1:continue
        rates=list(map(F,c['arrival_rates']))
        if rates!=sorted(rates):continue
        H=c['horizon'];m=len(rates)
        value=1+sum(1-(1-(b-a))**H for a,b in zip(rates,rates[1:]))
        assert F(record['capacity_bound'])<=min(F(m),value)
        assert value<=1+H*(rates[-1]-rates[0])
        eligible+=1
    assert one_slot==600 and continuity==108
    # An empty results directory is useful when running tests before the
    # campaign; this optional cross-check is repeated after the campaign.
    report=dict(successful=True,one_slot_cases=one_slot,continuity_cases=continuity,
                continuity_seed=229501,eligible_retained_rate_cases=eligible,
                cpu_seconds=time.process_time()-start,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                status='Post-campaign validation of proved analytic calibrations; not a workload extension.')
    (ROOT/'results').mkdir(exist_ok=True)
    (ROOT/'results/calibrations.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
