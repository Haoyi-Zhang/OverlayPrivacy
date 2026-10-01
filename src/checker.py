"""Standalone exact checker. Does not import model, producer, or oracle.

The declared queue semantics are recomputed here without importing the producer.
The observation alphabet is still an assurance boundary: a finite checker cannot
establish that a real network has no omitted observations.
"""
import argparse,json,re
from fractions import Fraction
from itertools import combinations,product
from pathlib import Path

class InvalidCertificate(ValueError): pass

_CANONICAL_FRACTION = re.compile(r'-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?\Z')
_MODEL_KEYS = {'config', 'kernel'}
_CONFIG_KEYS = {'scheduler', 'queue_capacity', 'token_capacity', 'horizon',
                'refill_period', 'padding', 'observe_overflow',
                'arrival_rates', 'initial_queues'}
_CERTIFICATE_KEYS = {'scope', 'couplings', 'potentials', 'distances',
                     'tree', 'capacity_bound'}

def need(p,message):
    if not p: raise InvalidCertificate(message)

def frac(x):
    need(type(x) is str and len(x)<=1500,'rational encoding')
    need(_CANONICAL_FRACTION.fullmatch(x) is not None, 'noncanonical rational')
    try: value=Fraction(x)
    except (ValueError,ZeroDivisionError): raise InvalidCertificate('invalid rational')
    need(str(value)==x, 'noncanonical rational')
    need(value.numerator.bit_length()<=4096 and value.denominator.bit_length()<=4096,'bit limit')
    return value

def unique_pairs(items):
    d={}
    for k,v in items:
        need(k not in d,'duplicate JSON key');d[k]=v
    return d

def read(path):
    p=Path(path);need(p.stat().st_size<=64*1024*1024,'input byte limit')
    return json.loads(p.read_text(encoding='utf-8'),object_pairs_hook=unique_pairs)

def check(model,cert):
    need(type(model) is dict and set(model)==_MODEL_KEYS,'model schema')
    need(type(cert) is dict and set(cert)==_CERTIFICATE_KEYS,'certificate schema')
    c=model['config']; need(type(c) is dict and set(c)==_CONFIG_KEYS,'config schema')
    need(type(model['kernel']) is dict,'kernel encoding')
    need(type(cert['couplings']) is dict and type(cert['potentials']) is dict and
         type(cert['distances']) is dict,'certificate maps')
    need(type(cert['tree']) is list,'tree encoding')
    need(type(c['arrival_rates']) is list and type(c['initial_queues']) is list,
         'config sequences')
    need(type(c['scheduler']) is str and c['scheduler']=='public-history','scheduler scope')
    need(type(c['observe_overflow']) is bool,'observation mode')
    need(type(c['padding']) is str,'padding encoding')
    B=c['queue_capacity']; C=c['token_capacity']; H=c['horizon']; R=c['refill_period']
    need(all(type(v) is int for v in [B,C,H,R]),'integer dimensions')
    n=len(c['arrival_rates'])
    need(2<=n<=16 and 1<=B<=16 and 1<=C<=4 and 0<=H<=64 and 1<=R<=64,'dimension limit')
    need(len(c['initial_queues'])==n and all(type(q)is int and 0<=q<=B for q in c['initial_queues']),'initial states')
    need(all(type(x) is str and 0<=frac(x)<=1 for x in c['arrival_rates']) and
         0<=frac(c['padding'])<=1,'parameters')
    allowed={f'{a},{d}' for a,d in product(range(2),repeat=2)} if c['observe_overflow'] else {'0','1'}
    rows={}; expected={f'{s},{q},{a}' for s,q,a in product(range(n),range(B+1),range(2))}
    need(set(model['kernel'])==expected,'kernel coverage')
    for key,raw in model['kernel'].items():
        need(type(raw) is list,'kernel row encoding')
        row={}
        for entry in raw:
            need(type(entry) is list and len(entry)==3,'kernel entry encoding')
            y,q,p=entry
            need(type(y) is str and y in allowed and type(q)is int and 0<=q<=B,'kernel target')
            need((y,q) not in row,'duplicate transition')
            prob=frac(p);need(prob>0,'positive support');row[y,q]=prob
        need(sum(row.values())==1,'normalized kernel');rows[key]=row
    # Independent semantic expansion: integrate the cover coin immediately for
    # nonempty service, unlike the generator's Cartesian event enumeration.
    pad=frac(c['padding'])
    for s,q,a in product(range(n),range(B+1),range(2)):
        lam=frac(c['arrival_rates'][s]); expected_row={}
        for arrival,px in ((0,1-lam),(1,lam)):
            before=min(B,q+arrival); lost=int(q+arrival>B)
            if a==0:
                outcomes=((0,before,Fraction(1)),)
            elif before>0:
                outcomes=((1,before-1,Fraction(1)),)
            else:
                outcomes=((0,0,1-pad),(1,0,pad))
            for emission,after,pc in outcomes:
                y=f'{emission},{lost}' if c['observe_overflow'] else str(emission)
                if px*pc:
                    expected_row[y,after]=expected_row.get((y,after),0)+px*pc
        need(rows[f'{s},{q},{a}']==expected_row,'declared queue semantics')
    all_pairs=list(combinations(range(n),2))
    scope=cert.get('scope');need(scope in {'all-pairs','tree','ordered-chain'},'certificate scope')
    if scope=='all-pairs':
        pairs=all_pairs
    else:
        need(type(cert['tree']) is list and len(cert['tree'])==n-1,'tree size')
        pairs=[]
        for edge in cert['tree']:
            need(type(edge) is list and len(edge)==2 and all(type(x) is int for x in edge),'tree edge encoding')
            i,j=edge;need(0<=i<j<n and (i,j) not in pairs,'tree edge')
            pairs.append((i,j))
        pairs.sort()
    need(len(pairs)*(H+1)*(C+1)*(B+1)**2<=400000,'potential limit')
    if scope=='ordered-chain':
        rates=list(map(frac,c['arrival_rates']))
        need(rates==sorted(rates) and c['initial_queues']==sorted(c['initial_queues']),
             'given-index joint parameter order; checker does not relabel secrets')
        need(cert['tree']==[[i,i+1] for i in range(n-1)],'adjacent chain')
    gs={}
    expected={f'{i},{j},{q},{r},{a}' for i,j in pairs for q,r,a in product(range(B+1),range(B+1),range(2))}
    need(set(cert['couplings'])==expected,'coupling coverage')
    for key,raw in cert['couplings'].items():
        need(type(raw) is list,'coupling row encoding')
        i,j,q,r,a=map(int,key.split(','));left={};right={};g=[];seen=set()
        for entry in raw:
            need(type(entry) is list and len(entry)==5,'coupling entry encoding')
            yi,qi,yj,qj,p=entry
            need(type(yi) is str and type(yj) is str and yi in allowed and yj in allowed and
                 type(qi)is int and type(qj)is int and 0<=qi<=B and 0<=qj<=B,'coupling target')
            need((yi,qi,yj,qj) not in seen,'duplicate coupling entry');seen.add((yi,qi,yj,qj))
            v=frac(p);need(v>0,'positive coupling')
            left[yi,qi]=left.get((yi,qi),0)+v;right[yj,qj]=right.get((yj,qj),0)+v
            g.append((yi,qi,yj,qj,v))
        need(left==rows[f'{i},{q},{a}'] and right==rows[f'{j},{r},{a}'],'coupling marginals')
        if scope=='ordered-chain':
            li,lj=frac(c['arrival_rates'][i]),frac(c['arrival_rates'][j]);canonical={}
            # Analytic joint Bernoulli law; synthesis instead partitions [0,1].
            for xi,xj,px in ((0,0,1-lj),(0,1,lj-li),(1,1,li)):
                for cover,pc in ((0,1-pad),(1,pad)):
                    if not px*pc:continue
                    ui,uj=min(B,q+xi),min(B,r+xj)
                    ei,ej=int(a and (ui>0 or cover)),int(a and (uj>0 or cover))
                    ni,nj=ui-int(a and ui>0),uj-int(a and uj>0)
                    yi=f'{ei},{int(q+xi>B)}' if c['observe_overflow'] else str(ei)
                    yj=f'{ej},{int(r+xj>B)}' if c['observe_overflow'] else str(ej)
                    target=(yi,ni,yj,nj)
                    canonical[target]=canonical.get(target,0)+px*pc
            need({(yi,qi,yj,qj):p for yi,qi,yj,qj,p in g}==canonical,'canonical ordered coupling')
        gs[i,j,q,r,a]=g
    expected={f'{i},{j},{t},{b},{q},{r}' for i,j in pairs for t,b,q,r in product(range(H+1),range(C+1),range(B+1),range(B+1))}
    need(set(cert['potentials'])==expected,'potential coverage')
    vs={tuple(map(int,k.split(','))):frac(v) for k,v in cert['potentials'].items()}
    need(all(0<=v<=1 for v in vs.values()),'potential range')
    obligations=0;support_entries=0
    for i,j in pairs:
        for t,b,q,r in product(range(H+1),range(C+1),range(B+1),range(B+1)):
            v=vs[i,j,t,b,q,r]
            if t==H:
                need(v==0,'terminal potential');continue
            max_rhs=Fraction(0)
            for a in range(2 if b else 1):
                bn=min(C,b-a+int((t+1)%R==0))
                rhs=0
                for yi,qi,yj,qj,p in gs[i,j,q,r,a]:
                    rhs+=p*(1 if yi!=yj else vs[i,j,t+1,bn,qi,qj]);support_entries+=1
                need(v>=rhs,'history-safe Bellman inequality');obligations+=1
                max_rhs=max(max_rhs,rhs)
            if scope=='ordered-chain':need(v==max_rhs,'canonical Bellman equality')
    need(set(cert['distances'])=={f'{i},{j}' for i,j in pairs},'distance coverage')
    d={tuple(map(int,k.split(','))):frac(v) for k,v in cert['distances'].items()}
    for (i,j),x in d.items():
        initial_value=vs[i,j,0,C,c['initial_queues'][i],c['initial_queues'][j]]
        need(initial_value<=x<=1,'initial distance bound')
        if scope=='ordered-chain':need(initial_value==x,'canonical initial equality')
    tree=cert['tree'];need(len(tree)==n-1,'tree size');adj=[[] for _ in range(n)];seen=set()
    for e in tree:
        need(type(e)is list and len(e)==2 and all(type(v)is int for v in e),'tree edge encoding')
        i,j=e;need(0<=i<j<n and (i,j) not in seen,'tree edge');seen.add((i,j))
        adj[i].append(j);adj[j].append(i)
    reached={0};todo=[0]
    while todo:
        u=todo.pop()
        for v in adj[u]:
            if v not in reached:reached.add(v);todo.append(v)
    need(len(reached)==n,'connected tree')
    # Cycle property verifies minimum weight without rerunning producer's algorithm.
    for i,j in (all_pairs if scope=='all-pairs' else []):
        stack=[(i,-1,Fraction(0))];bottleneck=None
        while stack:
            u,parent,mx=stack.pop()
            if u==j:bottleneck=mx;break
            for v in adj[u]:
                if v!=parent:stack.append((v,u,max(mx,d[tuple(sorted((u,v)))])))
        need(bottleneck is not None and bottleneck<=d[i,j],'minimum tree cycle property')
    bound=1+sum(d[tuple(e)] for e in tree)
    need(frac(cert['capacity_bound'])==bound,'capacity arithmetic')
    return {'valid':True,'scope':scope,'optimality_checked':scope!='tree',
            'optimality_domain':{'all-pairs':'declared-dense-summary','ordered-chain':'canonical-dense-family-via-order','tree':'omitted-pairs-not-checked'}[scope],
            'capacity_bound':str(bound),'bellman_obligations':obligations,
            'coupling_entries':sum(len(g) for g in gs.values()),'weighted_support_visits':support_entries,
            'potential_entries':len(vs),'maximum_rational_bits':max(max(v.numerator.bit_length(),v.denominator.bit_length()) for v in vs.values())}

def main():
    p=argparse.ArgumentParser();p.add_argument('model');p.add_argument('certificate');a=p.parse_args()
    try:print(json.dumps(check(read(a.model),read(a.certificate)),sort_keys=True))
    except (InvalidCertificate,KeyError,TypeError,ValueError,IndexError,OSError,RecursionError) as e:
        print(json.dumps({'valid':False,'reason':str(e)}));raise SystemExit(2)
if __name__=='__main__':main()
