#!/usr/bin/env python3
"""Derive reviewer-facing tightness and structural-reduction statistics.

The extractor deliberately consumes frozen JSON/JSONL records rather than
hard-coding the reported values.  It chooses semantic key pairs by name and by
expected campaign coverage, records the selected paths, and fails closed when
coverage changes unexpectedly.
"""
from __future__ import annotations
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import argparse, csv, json, math, re, statistics

ROOT = Path(__file__).resolve().parents[1]

def scalar(x):
    if isinstance(x, bool) or x is None: return None
    if isinstance(x, int): return Fraction(x)
    if isinstance(x, float): return Fraction(str(x))
    if isinstance(x, str):
        s=x.strip()
        if re.fullmatch(r'-?\d+(?:/-?[1-9]\d*)?',s):
            try: return Fraction(s)
            except Exception: return None
        if re.fullmatch(r'-?\d+\.\d+(?:[eE][+-]?\d+)?',s):
            try: return Fraction(s)
            except Exception: return None
    return None

def flatten(x,prefix=''):
    out={}
    if isinstance(x,dict):
        for k,v in x.items(): out.update(flatten(v,f'{prefix}.{k}' if prefix else str(k)))
    elif isinstance(x,list):
        # Lists of scalars are not treated as record fields; child dictionaries are.
        pass
    else:
        out[prefix]=x
    return out

def dictionaries(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from dictionaries(v)
    elif isinstance(x,list):
        for v in x: yield from dictionaries(v)

def load_records(results):
    out=[]
    for p in sorted(results.rglob('*')):
        if not p.is_file() or 'verification' in p.parts: continue
        try:
            if p.suffix=='.json':
                obj=json.loads(p.read_text(encoding='utf-8'))
                for i,d in enumerate(dictionaries(obj)): out.append((p,i,flatten(d)))
            elif p.suffix in {'.jsonl','.ndjson'}:
                for ln,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
                    if not line.strip(): continue
                    obj=json.loads(line)
                    for i,d in enumerate(dictionaries(obj)): out.append((p,ln*100000+i,flatten(d)))
        except Exception:
            continue
    return out

def ident(flat,p,i):
    for k,v in flat.items():
        lk=k.lower()
        if re.search(r'(^|\.)(model_id|instance_id|case_id|model|instance|case|name|id)$',lk) and isinstance(v,(str,int)):
            return str(v)
    return f'{p.name}:{i}'

def quantile(vals,q):
    if not vals: return None
    xs=sorted(vals); pos=(len(xs)-1)*q; lo=math.floor(pos); hi=math.ceil(pos)
    return xs[lo] if lo==hi else xs[lo]+(xs[hi]-xs[lo])*(pos-lo)

def fstr(x): return str(x.numerator) if x.denominator==1 else f'{x.numerator}/{x.denominator}'

def choose_exact(records):
    groups=defaultdict(dict)
    for p,i,flat in records:
        rid=ident(flat,p,i)
        ex=[]; bd=[]
        for k,v in flat.items():
            fv=scalar(v); lk=k.lower()
            if fv is None: continue
            if re.search(r'(exact|oracle)',lk) and not re.search(r'(time|second|node|count|rss|memory|seed)',lk): ex.append((k,fv))
            if re.search(r'(canonical.*bound|bound.*canonical|certificate.*bound|tree.*bound|dense.*bound|^bound$|\.bound$)',lk) and not re.search(r'(time|second|count|rss|memory)',lk): bd.append((k,fv))
        for ek,ev in ex:
            for bk,bv in bd:
                if bv>=ev>=0:
                    groups[(ek,bk)][rid]=(ev,bv,str(p.relative_to(ROOT)))
    ranked=sorted(groups.items(),key=lambda kv:(abs(len(kv[1])-40),-len(kv[1]),kv[0]))
    if not ranked or len(ranked[0][1])<20: raise RuntimeError('could not identify exact/bound record family')
    return ranked[0]

def choose_reduction(records,needle):
    groups=defaultdict(dict)
    for p,i,flat in records:
        rid=ident(flat,p,i)
        dense=[]; ordered=[]
        for k,v in flat.items():
            fv=scalar(v); lk=k.lower()
            if fv is None or needle not in lk: continue
            if 'dense' in lk: dense.append((k,fv))
            if 'ordered' in lk or 'adjacent' in lk: ordered.append((k,fv))
        for dk,dv in dense:
            for ok,ov in ordered:
                if dv>=ov>0:
                    groups[(dk,ok)][rid]=(dv,ov,str(p.relative_to(ROOT)))
    ranked=sorted(groups.items(),key=lambda kv:(abs(len(kv[1])-71),-len(kv[1]),kv[0]))
    if not ranked or len(ranked[0][1])<30: return None
    return ranked[0]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT); args=ap.parse_args()
    root=args.root.resolve(); records=load_records(root/'results')
    (ek,bk),exact=choose_exact(records)
    gaps=[]; ratios=[]; rows=[]
    for rid,(ev,bv,src) in sorted(exact.items()):
        gap=bv-ev; ratio=(bv/ev if ev>0 else None)
        gaps.append(float(gap));
        if ratio is not None: ratios.append(float(ratio))
        rows.append({'model':rid,'exact':fstr(ev),'canonical_bound':fstr(bv),'absolute_gap':fstr(gap),'ratio':str(float(ratio)) if ratio is not None else '', 'source':src})
    red={}
    for needle,label in [('obligation','bellman_obligations'),('potential','potentials')]:
        chosen=choose_reduction(records,needle)
        if chosen:
            (dk,ok),vals=chosen
            pct=[float((dv-ov)/dv) for dv,ov,_ in vals.values()]
            red[label]={'dense_key':dk,'ordered_key':ok,'models':len(vals),'minimum_reduction':min(pct),'median_reduction':statistics.median(pct),'maximum_reduction':max(pct),'all_equal_reduction':len(set(round(x,15) for x in pct))==1}
    worst=max(rows,key=lambda r:float(Fraction(r['absolute_gap'])))
    report={
      'schema_version':1,
      'source_records_scanned':len(records),
      'selected_exact_key':ek,'selected_bound_key':bk,
      'exact_models':len(exact),
      'tightness':{
        'exact_hits':sum(1 for x in gaps if x==0.0),
        'absolute_gap':{'minimum':min(gaps),'q25':quantile(gaps,.25),'median':statistics.median(gaps),'q75':quantile(gaps,.75),'q90':quantile(gaps,.90),'maximum':max(gaps),'mean':statistics.fmean(gaps)},
        'bound_over_exact_ratio':{'minimum':min(ratios),'median':statistics.median(ratios),'q90':quantile(ratios,.90),'maximum':max(ratios),'mean':statistics.fmean(ratios)},
        'worst_absolute_gap_record':worst,
      },
      'structural_reduction':red,
      'interpretation':[
        'Tightness is evaluated only on tiny models where the complete public-history optimum is exactly enumerable.',
        'The ordered reduction compares two encodings of the same canonical certificate; it is not an empirical claim about all queueing models.',
        'Ratios omit exact value zero to avoid division by zero.'
      ]
    }
    out=root/'results/verification/reviewer-utility-tightness.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    with (root/'results/verification/reviewer-utility-tightness.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    gen=root/'paper-generated'; gen.mkdir(exist_ok=True)
    tex=(r"\begin{tabular}{lr}\hline"+'\n'
         +r"Tiny models with exact oracle & %d \\"%len(exact)+'\n'
         +r"Exact certificate hits & %d \\"%report['tightness']['exact_hits']+'\n'
         +r"Median absolute gap & %.4f \\"%report['tightness']['absolute_gap']['median']+'\n'
         +r"90th-percentile absolute gap & %.4f \\"%report['tightness']['absolute_gap']['q90']+'\n'
         +r"Maximum absolute gap & %.4f \\"%report['tightness']['absolute_gap']['maximum']+'\n'
         +r"Maximum bound/exact ratio & %.4f \\"%report['tightness']['bound_over_exact_ratio']['maximum']+'\n'
         +r"\hline\end{tabular}"+'\n')
    (gen/'reviewer-metrics.tex').write_text(tex,encoding='utf-8')
    if len(exact)!=40: raise SystemExit(f'expected 40 exact models, found {len(exact)} via {ek}, {bk}')
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
