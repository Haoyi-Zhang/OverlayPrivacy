"""Exact tiny public-history oracle. Returns scalar values, never policies.
Uses unnormalized hidden-state masses, not couplings or certificate potentials.
"""
from fractions import Fraction as F
from functools import lru_cache

def capacity(model,secrets=None,node_cap=250000):
    c=model['config'];B=c['queue_capacity'];H=c['horizon'];C=c['token_capacity'];R=c['refill_period']
    secrets=list(range(len(c['arrival_rates']))) if secrets is None else list(secrets)
    rows={tuple(map(int,k.split(','))):[(y,q,F(p)) for y,q,p in v] for k,v in model['kernel'].items()}
    masses=tuple(tuple(F(int(q==c['initial_queues'][s])) for q in range(B+1)) for s in secrets)
    nodes=0
    @lru_cache(None)
    def walk(t,b,m):
        nonlocal nodes
        nodes+=1
        if nodes>node_cap:raise RuntimeError('exact oracle node cap exceeded')
        if t==H:return max(map(sum,m))
        candidates=[]
        for a in range(2 if b else 1):
            branches={}
            for i,s in enumerate(secrets):
                for q,mass in enumerate(m[i]):
                    if not mass:continue
                    for y,qn,p in rows[s,q,a]:
                        if y not in branches:branches[y]=[[F(0) for _ in range(B+1)] for _ in secrets]
                        branches[y][i][qn]+=mass*p
            bn=min(C,b-a+(1 if (t+1)%R==0 else 0))
            score=sum((walk(t+1,bn,tuple(map(tuple,mat))) for mat in branches.values()),F(0))
            candidates.append(score)
        return max(candidates)
    result=walk(0,C,masses)
    info=walk.cache_info()
    return result,{'oracle_nodes':nodes,'oracle_cache_hits':info.hits}
