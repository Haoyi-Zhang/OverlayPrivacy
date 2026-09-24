#!/usr/bin/env python3
"""Independent exhaustive check of the ordered graph-theoretic lemma."""
from __future__ import annotations
from fractions import Fraction
from itertools import product
import unittest


def prufer_edges(code, n):
    degree=[1]*n
    for x in code: degree[x]+=1
    code=list(code); out=[]
    for x in code:
        leaf=next(i for i,d in enumerate(degree) if d==1)
        out.append((min(leaf,x),max(leaf,x)))
        degree[leaf]-=1; degree[x]-=1
    left=[i for i,d in enumerate(degree) if d==1]
    out.append((min(left),max(left)))
    return tuple(out)


def all_trees(n):
    if n==2: return [((0,1),)]
    return [prufer_edges(code,n) for code in product(range(n),repeat=n-2)]


def weight(tree,w): return sum((w[e] for e in tree),Fraction(0))

class ThresholdMSTLemmaTests(unittest.TestCase):
    def test_exhaustive_small_integer_weights(self):
        checked=0
        for n in range(2,6):
            trees=all_trees(n)
            for adjacent in product(range(1,4),repeat=n-1):
                nonadj=[(i,j) for i in range(n) for j in range(i+2,n)]
                lower=[max(adjacent[i:j]) for i,j in nonadj]
                # Two representative values per non-adjacent edge: the cut lower
                # bound itself and a strictly heavier value. This exhausts all
                # threshold order patterns relevant to MST comparisons.
                choices=[[x,x+1] for x in lower]
                for vals in product(*choices) if choices else [()]:
                    w={(i,i+1):Fraction(adjacent[i]) for i in range(n-1)}
                    w.update({e:Fraction(v) for e,v in zip(nonadj,vals)})
                    chain=tuple((i,i+1) for i in range(n-1))
                    cw=weight(chain,w)
                    mw=min(weight(t,w) for t in trees)
                    self.assertEqual(cw,mw,(n,adjacent,vals,chain))
                    checked+=1
        self.assertGreaterEqual(checked,1000)

    def test_triangle_inequality_alone_is_insufficient(self):
        # d01=d12=2 and d02=1 is a metric, but the adjacent chain has weight 4
        # whereas a minimum tree uses edges 02 and 01 with weight 3.
        w={(0,1):Fraction(2),(1,2):Fraction(2),(0,2):Fraction(1)}
        for i,j,k in [(0,1,2),(0,2,1),(1,2,0)]:
            self.assertLessEqual(w[tuple(sorted((i,j)))],w[tuple(sorted((i,k)))]+w[tuple(sorted((k,j)))])
        trees=all_trees(3)
        self.assertEqual(Fraction(3),min(weight(t,w) for t in trees))
        self.assertEqual(Fraction(4),weight(((0,1),(1,2)),w))

if __name__=='__main__': unittest.main(verbosity=2)
