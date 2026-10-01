"""Certificate synthesis, untrusted by checker.py; exact rational arithmetic."""
from fractions import Fraction as F
from itertools import combinations, product
from model import coupling


def minimum_tree(n, distances):
    parent=list(range(n))
    def find(i):
        while parent[i]!=i:
            i=parent[i]
        return i
    edges=[]
    for i,j in sorted(combinations(range(n),2),key=lambda e:(distances[e],e)):
        a,b=find(i),find(j)
        if a!=b:
            parent[a]=b;edges.append([i,j])
    return edges


def make(model, mode="all-pairs"):
    c=model['config']; n=len(c['arrival_rates']); B=c['queue_capacity']
    C=c['token_capacity']; H=c['horizon']; R=c['refill_period']
    if mode not in {'all-pairs','ordered-chain'}:
        raise ValueError('unsupported synthesis mode')
    if mode=='ordered-chain':
        rates=list(map(F,c['arrival_rates']));initial=c['initial_queues']
        if rates!=sorted(rates) or initial!=sorted(initial):
            raise ValueError('ordered-chain requires rates and initial queues ordered in the supplied label index; no automatic relabeling')
        pairs=[(i,i+1) for i in range(n-1)]
    else:
        pairs=list(combinations(range(n),2))
    gammas={};values={};distances={}
    for i,j in pairs:
        local={}
        for q,r,a in product(range(B+1),range(B+1),range(2)):
            g=coupling(c,i,j,q,r,a)
            gammas[f'{i},{j},{q},{r},{a}']=g
            local[q,r,a]=[(yi,qi,yj,qj,F(p)) for yi,qi,yj,qj,p in g]
        v={}
        for b,q,r in product(range(C+1),range(B+1),range(B+1)):
            v[H,b,q,r]=F(0)
        for t in reversed(range(H)):
            for b,q,r in product(range(C+1),range(B+1),range(B+1)):
                costs=[]
                for a in range(2 if b else 1):
                    bn=min(C,b-a+int((t+1)%R==0))
                    costs.append(sum((p*(1 if yi!=yj else v[t+1,bn,qi,qj])
                                      for yi,qi,yj,qj,p in local[q,r,a]),F(0)))
                v[t,b,q,r]=max(costs)
        for key,x in v.items(): values[','.join(map(str,(i,j)+key))]=str(x)
        distances[i,j]=v[0,C,c['initial_queues'][i],c['initial_queues'][j]]
    tree=minimum_tree(n,distances) if mode=='all-pairs' else [[i,i+1] for i in range(n-1)]
    total=1+sum((distances[tuple(e)] for e in tree),F(0))
    return {'scope':mode,'couplings':gammas,'potentials':values,
            'distances':{f'{i},{j}':str(v) for (i,j),v in distances.items()},
            'tree':tree,'capacity_bound':str(total)}


def hierarchy_witness(n, distances):
    """Abstract normalized channel, not a traffic model or a linking procedure."""
    levels=sorted({F(0),F(1),*distances.values()});columns={}
    for lo,hi in zip(levels,levels[1:]):
        remaining=set(range(n))
        while remaining:
            comp={min(remaining)}; changed=True
            while changed:
                new={v for v in remaining-comp if any(
                    distances[tuple(sorted((u,v)))]<=lo for u in comp)}
                changed=bool(new);comp|=new
            remaining-=comp
            key=tuple(sorted(comp));columns[key]=columns.get(key,F(0))+hi-lo
    return [[(p if i in members else F(0)) for members,p in columns.items()]
            for i in range(n)]


def sparsify(certificate):
    """Retain a connected tree's obligations, without claiming global optimality.

    This is packaging, not a second synthesis algorithm: the omitted distances
    are not available to the sparse checker and cannot justify an MST claim.
    """
    edges={tuple(e) for e in certificate['tree']}
    def selected(key):
        return tuple(map(int,key.split(',')[:2])) in edges
    return {'scope':'tree',
            'couplings':{k:v for k,v in certificate['couplings'].items() if selected(k)},
            'potentials':{k:v for k,v in certificate['potentials'].items() if selected(k)},
            'distances':{k:v for k,v in certificate['distances'].items() if selected(k)},
            'tree':certificate['tree'], 'capacity_bound':certificate['capacity_bound']}
