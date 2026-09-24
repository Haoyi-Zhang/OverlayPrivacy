"""One scientific case in a fresh, resource-bounded process."""
import argparse,json,resource,time
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path
from producer import make,sparsify,hierarchy_witness
from checker import check,read
from oracle import capacity


def write(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n');tmp.replace(path)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--case',required=True);parser.add_argument('--scope',choices=('all-pairs','ordered-chain'),required=True)
    parser.add_argument('--repeat',type=int,default=0);args=parser.parse_args()
    # One child, no spawned workers. Address-space and CPU caps also bound failure.
    resource.setrlimit(resource.RLIMIT_AS,(3500*1024**2,3500*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(40,40))
    start=time.process_time();wall=time.perf_counter()
    startup_peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    model=read(args.root/'inputs'/f'{args.case}.json');c=model['config'];n=len(c['arrival_rates'])
    t=time.process_time();certificate=make(model,args.scope);generation=time.process_time()-t
    t=time.process_time();checked=check(model,certificate);checking=time.process_time()-t
    encoded=json.dumps(certificate,sort_keys=True,separators=(',',':'))+'\n'
    r=dict(case=args.case,scope=args.scope,repeat=args.repeat,config=c,**{k:v for k,v in checked.items() if k!='scope'},
           generation_cpu_seconds=generation,checking_cpu_seconds=checking,certificate_bytes=len(encoded.encode()))
    if args.repeat==0:
        path=args.root/'results'/'certificates'/f'{args.case}-{args.scope}.json'
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(encoded)
    if args.scope=='all-pairs' and args.repeat==0:
        distances={tuple(map(int,k.split(','))):F(v) for k,v in certificate['distances'].items()}
        r['best_star_bound']=str(1+min(sum(distances[tuple(sorted((root,j)))] for j in range(n) if root!=j) for root in range(n)))
        sparse=sparsify(certificate);r['tree_only_check']=check(model,sparse)['valid']
        if not c['observe_overflow']:
            H=c['horizon'];N=min(H,c['token_capacity']+(H-1)//c['refill_period']) if H else 0
            r['reservation_limit']=N;r['uniform_cover_bound']=str(1+(n-1)*(1-F(c['padding'])**N))
            assert F(r['capacity_bound'])<=F(r['uniform_cover_bound'])
        witness=hierarchy_witness(n,distances)
        assert all(sum(row)==1 for row in witness)
        assert sum(map(max,zip(*witness)))==F(r['capacity_bound'])
        assert all(sum(abs(x-y) for x,y in zip(witness[i],witness[j]))/2<=distances[i,j] for i,j in combinations(range(n),2))
        r['summary_witness_columns']=len(witness[0]);r['summary_witness_verified']=True
        ordered=list(map(F,c['arrival_rates']))==sorted(map(F,c['arrival_rates'])) and c['initial_queues']==sorted(c['initial_queues'])
        r['joint_order']=ordered
        r['chain_bound']=str(1+sum(distances[i,i+1] for i in range(n-1)))
        if ordered:
            assert all(distances[k,l]<=distances[i,j] for i,j in combinations(range(n),2) for k in range(i,j) for l in range(k+1,j+1))
            assert r['chain_bound']==r['capacity_bound'];r['interval_dominance_verified']=True
        if c['horizon']<=4:
            t=time.process_time();exact,details=capacity(model)
            r.update(exact_capacity=str(exact),**details)
            assert exact<=F(r['capacity_bound'])
            paird={};pairnodes=0
            for i,j in combinations(range(n),2):
                val,info=capacity(model,[i,j]);paird[i,j]=val-1;pairnodes+=info['oracle_nodes']
                assert val-1<=distances[i,j]
            # Separate scalar pair-oracle summary: each pair may use a different
            # worst public scheduler, so it is a valid conservative uniform bound.
            from producer import minimum_tree
            tree=minimum_tree(n,paird)
            r['exact_pair_summary_bound']=str(1+sum(paird[tuple(e)] for e in tree))
            assert exact<=F(r['exact_pair_summary_bound'])<=F(r['capacity_bound'])
            r['pair_oracle_nodes']=pairnodes;r['oracle_cpu_seconds']=time.process_time()-t
    r['worker_cpu_seconds']=time.process_time()-start;r['worker_wall_seconds']=time.perf_counter()-wall
    r['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    r['startup_peak_rss_kib']=startup_peak
    suffix='' if args.repeat==0 else f'-repeat{args.repeat}'
    write(args.root/'results'/'campaign'/f'{args.case}-{args.scope}{suffix}.json',r)

if __name__=='__main__':main()
