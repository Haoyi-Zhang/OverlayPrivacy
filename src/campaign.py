"""Deterministic owned-input campaign; one bounded child at a time, no network I/O.

Run with --start/--stop for resumable chunks. Each result is written only after
its checks finish. --overwrite intentionally refreshes existing measurements.
"""
import argparse, json, os, subprocess, sys, resource, time
from fractions import Fraction as F
from pathlib import Path
from itertools import product
from model import kernel

ROOT=Path(__file__).resolve().parents[1]

def base(m=4, B=2, H=4):
    return dict(scheduler='public-history',queue_capacity=B,token_capacity=1,
        horizon=H,refill_period=2,padding='1/2',observe_overflow=False,
        arrival_rates=[str(F(i,m+1)) for i in range(1,m+1)],initial_queues=[0]*m)

def instances():
    cases=[]
    for k,(H,p,R) in enumerate(product((2,4,8),('0','1/2','1'),(1,2,4)),1):
        c=base(H=H);c.update(padding=p,refill_period=R);cases.append((f'Q{k:03d}',c,'queue-grid'))
    for k,(m,B,H) in enumerate(product((2,4,8,16),(1,2,4),(4,8,16)),1):
        c=base(m,B,H);c['padding']='3/4';cases.append((f'S{k:03d}',c,'scale-grid'))
    variants=[{'observe_overflow':True,'padding':'1'},
              {'observe_overflow':True},
              {'arrival_rates':['1/2']*4},
              {'arrival_rates':['0']*3,'initial_queues':[0,1,0],
               'queue_capacity':1,'horizon':1,'padding':'0'},
              {'arrival_rates':['0','1','0'],'initial_queues':[0]*3,
               'queue_capacity':1,'horizon':1,'padding':'0'},
              {'initial_queues':[0,0,1,2]},
              {'horizon':0},
              {'token_capacity':2},
              {'arrival_rates':['0','0','1/2','1']},
              {'observe_overflow':True,'padding':'0'}]
    for k,v in enumerate(variants,1):
        c=base();c.update(v);cases.append((f'A{k:03d}',c,'assumption-grid'))
    return cases

def ordered(c):
    """Frozen supplied-index criterion; this function does not search relabelings."""
    return list(map(F,c['arrival_rates']))==sorted(map(F,c['arrival_rates'])) and c['initial_queues']==sorted(c['initial_queues'])

def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n')
    tmp.replace(path)

def prepare(out):
    plan=[]
    for name,c,group in instances():
        write_json(out/'inputs'/f'{name}.json',kernel(c))
        plan.append(dict(case=name,group=group,ordered=ordered(c),tiny_oracle=c['horizon']<=4,config=c))
    write_json(out/'inputs'/'selection.json',plan)
    return plan

def worker(out,name,scope,rep,overwrite):
    suffix='' if rep==0 else f'-repeat{rep}'
    result=out/'results'/'campaign'/f'{name}-{scope}{suffix}.json'
    if result.exists() and not overwrite:return json.loads(result.read_text())
    env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1'}
    cmd=[sys.executable,str(ROOT/'src'/'worker.py'),'--root',str(out),'--case',name,'--scope',scope,'--repeat',str(rep)]
    before=resource.getrusage(resource.RUSAGE_CHILDREN); start=time.perf_counter()
    completed=subprocess.run(cmd,capture_output=True,text=True,timeout=44,env=env)
    after=resource.getrusage(resource.RUSAGE_CHILDREN); elapsed=time.perf_counter()-start
    if completed.returncode:
        raise RuntimeError(f'{name}/{scope}: {completed.stderr[-1500:]} {completed.stdout[-1500:]}')
    if not result.exists():raise RuntimeError('child omitted result')
    record=json.loads(result.read_text())
    record['process_cpu_seconds']=(after.ru_utime+after.ru_stime)-(before.ru_utime+before.ru_stime)
    record['process_wall_seconds']=elapsed
    write_json(result,record)
    return record

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,default=ROOT)
    p.add_argument('--start',type=int,default=0);p.add_argument('--stop',type=int)
    p.add_argument('--prepare-only',action='store_true');p.add_argument('--overwrite',action='store_true')
    p.add_argument('--repeats',action='store_true');a=p.parse_args();out=a.out.resolve()
    plan=prepare(out)
    if a.prepare_only:print(json.dumps({'prepared':len(plan)}));return
    chosen=plan[a.start:a.stop]
    for item in chosen:
        name=item['case'];scopes=['all-pairs']+(['ordered-chain'] if item['ordered'] else [])
        if a.repeats:
            if not(item['group']=='scale-grid' and item['config']['queue_capacity']==4 and item['config']['horizon']==16 and len(item['config']['arrival_rates']) in (4,8,16)):continue
            reps=range(1,6)
        else:reps=(0,)
        for rep in reps:
            for scope in (scopes if rep%2==0 else list(reversed(scopes))):
                r=worker(out,name,scope,rep,a.overwrite)
                print(json.dumps({k:r[k] for k in ('case','scope','repeat','capacity_bound','worker_cpu_seconds','peak_rss_kib')}),flush=True)

if __name__=='__main__':main()
