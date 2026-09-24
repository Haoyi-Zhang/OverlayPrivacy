#!/usr/bin/env python3
"""Exact-rational check of the convexity used to derandomize finite policies."""
from __future__ import annotations
from fractions import Fraction
import random
import unittest

def capacity(channel):
    # Uniform-prior multiplicative guessing capacity: sum_y max_s K(y|s).
    return sum(max(channel[s][y] for s in range(len(channel))) for y in range(len(channel[0])))

def random_channel(rng,secrets=3,outputs=4,den=12):
    rows=[]
    for _ in range(secrets):
        cuts=sorted([0,den]+[rng.randrange(den+1) for _ in range(outputs-1)])
        vals=[cuts[i+1]-cuts[i] for i in range(outputs)]
        rng.shuffle(vals)
        rows.append([Fraction(v,den) for v in vals])
    return rows

def mix(a,b,lam):
    return [[lam*x+(1-lam)*y for x,y in zip(rx,ry)] for rx,ry in zip(a,b)]

class RandomizedPolicyDominanceTests(unittest.TestCase):
    def test_capacity_is_convex_under_channel_mixing(self):
        rng=random.Random(20260920)
        for _ in range(1000):
            a=random_channel(rng); b=random_channel(rng); lam=Fraction(rng.randrange(13),12)
            lhs=capacity(mix(a,b,lam)); rhs=lam*capacity(a)+(1-lam)*capacity(b)
            self.assertLessEqual(lhs,rhs)
            self.assertLessEqual(lhs,max(capacity(a),capacity(b)))
if __name__=='__main__': unittest.main(verbosity=2)
