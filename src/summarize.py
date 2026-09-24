"""Validate the complete frozen campaign and write exact CSV/scalar summaries."""
import argparse,csv,json,statistics
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def summarize(root):
    plan=json.loads((root/'inputs/selection.json').read_text());rows=[];records=[];tiny=[]
    for item in plan:
        name=item['case'];base=None
        for scope in ['all-pairs']+(['ordered-chain'] if item['ordered'] else []):
            r=json.loads((root/f'results/campaign/{name}-{scope}.json').read_text());records.append(r)
            assert r['valid'] and r['config']==item['config'] and r['repeat']==0
            c=r['config'];m=len(c['arrival_rates']);pairs=m*(m-1)//2 if scope=='all-pairs' else m-1
            assert r['potential_entries']==pairs*(c['horizon']+1)*(c['token_capacity']+1)*(c['queue_capacity']+1)**2
            assert r['bellman_obligations']==pairs*c['horizon']*(1+2*c['token_capacity'])*(c['queue_capacity']+1)**2
            if scope=='all-pairs':base=r
            else:assert r['capacity_bound']==base['capacity_bound']
            if item['tiny_oracle'] and scope=='all-pairs':
                assert F(r['exact_capacity'])<=F(r['exact_pair_summary_bound'])<=F(r['capacity_bound'])
                tiny.append(r)
            rows.append(dict(case=name,group=item['group'],scope=scope,m=m,B=c['queue_capacity'],H=c['horizon'],R=c['refill_period'],C=c['token_capacity'],padding=c['padding'],overflow=c['observe_overflow'],bound=r['capacity_bound'],bound_decimal=f"{float(F(r['capacity_bound'])):.9f}",exact=r.get('exact_capacity',''),exact_pair_bound=r.get('exact_pair_summary_bound',''),best_star=r.get('best_star_bound',''),uniform_cover=r.get('uniform_cover_bound',''),obligations=r['bellman_obligations'],potentials=r['potential_entries'],support_visits=r['weighted_support_visits'],bits=r['maximum_rational_bits'],bytes=r['certificate_bytes'],generation_cpu=r['generation_cpu_seconds'],checking_cpu=r['checking_cpu_seconds'],peak_rss_kib=r['peak_rss_kib']))
    assert len(plan)==73 and len(records)==144 and len(tiny)==40
    write_csv(root/'results/tables/campaign.csv',rows)
    repeats=[]
    for case in ['S018','S027','S036']:
        for scope in ['all-pairs','ordered-chain']:
            rs=[json.loads((root/f'results/campaign/{case}-{scope}-repeat{k}.json').read_text()) for k in range(1,6)]
            records.extend(rs);assert len(set(r['capacity_bound'] for r in rs))==1
            vals=[r['generation_cpu_seconds']+r['checking_cpu_seconds'] for r in rs]
            repeats.append(dict(case=case,m=len(rs[0]['config']['arrival_rates']),scope=scope,median_cpu=statistics.median(vals),min_cpu=min(vals),max_cpu=max(vals),median_generation=statistics.median(r['generation_cpu_seconds'] for r in rs),median_checking=statistics.median(r['checking_cpu_seconds'] for r in rs),min_rss_kib=min(r['peak_rss_kib'] for r in rs),max_rss_kib=max(r['peak_rss_kib'] for r in rs),bytes=rs[0]['certificate_bytes']))
    write_csv(root/'results/tables/repetitions.csv',repeats)
    summary=dict(models=len(plan),dense=73,ordered=71,oracle_models=len(tiny),repetition_runs=30,
        all_ordered_bounds_equal=True,all_oracles_below_bounds=True,
        maximum_oracle_nodes=max(r['oracle_nodes'] for r in tiny),
        maximum_potential_bits=max(r['maximum_rational_bits'] for r in records),
        max_rss_kib=max(r['peak_rss_kib'] for r in records),
        retained_process_cpu_seconds=sum(r.get('process_cpu_seconds',r['worker_cpu_seconds']) for r in records),
        process_cpu_fallback_records=[r['case']+'-'+r['scope'] for r in records if 'process_cpu_seconds' not in r],
        exact_equals_certificate=sum(F(r['exact_capacity'])==F(r['capacity_bound']) for r in tiny),
        median_absolute_gap=statistics.median(float(F(r['capacity_bound'])-F(r['exact_capacity'])) for r in tiny),
        maximum_absolute_gap=max(float(F(r['capacity_bound'])-F(r['exact_capacity'])) for r in tiny),
        maximum_gap_case=max(tiny,key=lambda r:F(r['capacity_bound'])-F(r['exact_capacity']))['case'],
        maximum_relative_bound_ratio=max(float(F(r['capacity_bound'])/F(r['exact_capacity'])) for r in tiny),
        note='Exact finite validation, not deployment evidence. RSS is unadjusted process high-water mark including startup. CPU excludes discarded intake/pilot attempts; resource accounting documents allowance separately.')
    (root/'results/tables/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);a=p.parse_args();print(json.dumps(summarize(a.root),indent=2))
