"""Owned finite token-table conformance, independent recursive reference.

SPDX-License-Identifier: MIT. No historical code, private paths, traffic,
optimizing policies, measurements, files or persistent caches.
"""
from copy import deepcopy
from fractions import Fraction as F
from functools import lru_cache
from itertools import combinations, product
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import producer
from checker import check, InvalidCertificate
from model import kernel


def configs():
    result=[]
    for i in range(16):
        rates=["0","1"] if i%3==0 else ["1/2","1/2"] if i%3==1 else ["0","1/3","1"]
        B=1+i%2
        result.append(dict(scheduler="public-history",queue_capacity=B,token_capacity=1+(i//2)%2,
                           horizon=i%5,refill_period=1+i%4,padding=["0","1/2","1"][i%3],
                           observe_overflow=bool(i%2),arrival_rates=rates,
                           initial_queues=[min(j,B) for j in range(len(rates))]))
    return result


def recursive_reference(c, pairs):
    """Scalar Bellman recursion from analytic joint coins, no producer coupling.

    Enumerates every supplied state for comparison; stores no action policy.
    """
    B,C,H,R=c["queue_capacity"],c["token_capacity"],c["horizon"],c["refill_period"]
    pad=F(c["padding"])
    def step(q,a,x,k):
        u=min(B,q+x)
        emission=int(a==1 and (u!=0 or k==1))
        return ((emission,int(q+x>B)) if c["observe_overflow"] else (emission,),
                u-int(a==1 and u!=0))
    potentials={}
    distances={}
    for i,j in pairs:
        li,lj=F(c["arrival_rates"][i]),F(c["arrival_rates"][j])
        joint=[(0,0,1-max(li,lj)),(1,1,min(li,lj)),
               (0,1,max(lj-li,F(0))),(1,0,max(li-lj,F(0)))]
        @lru_cache(None)
        def value(t,b,q,r):
            if t==H:return F(0)
            scores=[]
            actions=(0,) if b==0 else (0,1)
            for a in actions:
                # Independent public arithmetic; deliberately not a token table.
                bn=b-a
                if (t+1)%R==0:bn+=1
                if bn>C:bn=C
                total=F(0)
                for x,z,px in joint:
                    for k,pk in [(0,1-pad),(1,pad)]:
                        if not px*pk:continue
                        yi,qn=step(q,a,x,k);yj,rn=step(r,a,z,k)
                        total+=px*pk*(F(1) if yi!=yj else value(t+1,bn,qn,rn))
                scores.append(total)
            return max(scores)
        for t,b,q,r in product(range(H+1),range(C+1),range(B+1),range(B+1)):
            potentials[f"{i},{j},{t},{b},{q},{r}"]=str(value(t,b,q,r))
        distances[f"{i},{j}"]=str(value(0,C,c["initial_queues"][i],c["initial_queues"][j]))
    return potentials,distances


class TokenActionsTests(unittest.TestCase):
    def test_all_tiny_potentials_distances_and_semantic_counts(self):
        for c in configs():
            model=kernel(c);n=len(c["arrival_rates"])
            for mode in ("all-pairs","ordered-chain"):
                pairs=list(combinations(range(n),2)) if mode=="all-pairs" else [(i,i+1) for i in range(n-1)]
                packet=producer.make(model,mode)
                potentials,distances=recursive_reference(c,pairs)
                self.assertEqual(potentials,packet["potentials"])
                self.assertEqual(distances,packet["distances"])
                result=check(model,packet)
                self.assertEqual(len(pairs)*(c["horizon"]+1)*(c["token_capacity"]+1)*(c["queue_capacity"]+1)**2,result["potential_entries"])
                self.assertEqual(len(pairs)*c["horizon"]*(1+2*c["token_capacity"])*(c["queue_capacity"]+1)**2,result["bellman_obligations"])

    def test_public_table_all_admitted_time_token_refill_dimensions(self):
        for C,R,t in product(range(1,5),range(1,65),range(64)):
            for b in range(C+1):
                expected=[]
                for a in ((0,) if b==0 else (0,1)):
                    count=b-a+(1 if R and (t+1)%R==0 else 0)
                    expected.append((a,C if count>C else count))
                self.assertEqual(tuple(expected),producer._token_actions(t,b,C,R))

    def test_preparation_once_per_public_state_and_fresh_per_call(self):
        c=configs()[3];model=kernel(c)
        with patch.object(producer,"_token_actions",wraps=producer._token_actions) as prepare:
            first=producer.make(model)
            expected=c["horizon"]*(c["token_capacity"]+1)
            self.assertEqual(expected,prepare.call_count)
            second=producer.make(model)
            self.assertEqual(expected*2,prepare.call_count)
        self.assertEqual(json.dumps(first,separators=(",",":")),json.dumps(second,separators=(",",":")))

    def test_zero_horizon_and_early_rejections_do_not_prepare(self):
        c=configs()[0];c["horizon"]=0
        with patch.object(producer,"_token_actions",side_effect=AssertionError("must not prepare")):
            self.assertEqual("1",producer.make(kernel(c))["capacity_bound"])
            with self.assertRaisesRegex(ValueError,"unsupported synthesis mode"):
                producer.make(kernel(c),"unknown")
            c["arrival_rates"]=["1","0"]
            with self.assertRaisesRegex(ValueError,"ordered in the supplied"):
                producer.make(kernel(c),"ordered-chain")

    def test_mutable_config_not_reused_or_modified(self):
        c=configs()[4];model=kernel(c);snapshot=deepcopy(model)
        producer.make(model)
        self.assertEqual(snapshot,model)
        c["refill_period"]=1
        modified=kernel(c)
        result=producer.make(modified)
        pairs=list(combinations(range(len(c["arrival_rates"])),2))
        self.assertEqual(recursive_reference(c,pairs)[0],result["potentials"])

    def test_checker_remains_independent_and_rejects_changed_obligations(self):
        model=kernel(configs()[3]);packet=producer.make(model,"ordered-chain")
        with patch.object(producer,"_token_actions",side_effect=AssertionError("checker imported producer")):
            self.assertTrue(check(model,packet)["valid"])
            bad=deepcopy(packet);key=next(k for k,v in bad["potentials"].items() if v!="0")
            bad["potentials"][key]="0"
            with self.assertRaises(InvalidCertificate):check(model,bad)


if __name__=="__main__":unittest.main(verbosity=2)
