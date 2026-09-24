"""Owned finite queue abstraction. No networking, traces, or identification code."""
from fractions import Fraction as F
from itertools import product


def event(config, q, action, arrival, cover):
    B = config['queue_capacity']
    lost = int(q + arrival > B)
    q = min(B, q + arrival)
    sent = int(action and (q > 0 or cover))
    qnext = q - int(action and q > 0)
    obs = (sent, lost) if config['observe_overflow'] else (sent,)
    return ','.join(map(str, obs)), qnext


def kernel(config):
    result = {}
    p = F(config['padding'])
    for s, lam in enumerate(map(F, config['arrival_rates'])):
        for q, a in product(range(config['queue_capacity']+1), range(2)):
            row = {}
            for x, y in product(range(2), repeat=2):
                prob = (lam if x else 1-lam) * (p if y else 1-p)
                out = event(config,q,a,x,y)
                row[out] = row.get(out,F(0)) + prob
            result[f'{s},{q},{a}'] = [[y,z,str(v)] for (y,z),v in sorted(row.items()) if v]
    return {'config':config,'kernel':result}


def coupling(config,i,j,q,r,a):
    """Synchronous quantile coupling for arrivals; shared independent cover coin."""
    li,lj = F(config['arrival_rates'][i]),F(config['arrival_rates'][j])
    p=F(config['padding']); levels=sorted({F(0),li,lj,F(1)})
    result={}
    for low,high in zip(levels,levels[1:]):
        if high==low: continue
        u=(low+high)/2
        for c,pc in [(0,1-p),(1,p)]:
            if not pc: continue
            yi,qi=event(config,q,a,int(u<li),c)
            yj,qj=event(config,r,a,int(u<lj),c)
            key=(yi,qi,yj,qj)
            result[key]=result.get(key,F(0))+(high-low)*pc
    return [[yi,qi,yj,qj,str(p)] for (yi,qi,yj,qj),p in sorted(result.items())]
