"""Compare full deterministic scientific payloads; timings are not identities."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MEASURED={'generation_cpu_seconds','checking_cpu_seconds','oracle_cpu_seconds',
    'peak_rss_kib','startup_peak_rss_kib','process_cpu_seconds','process_wall_seconds',
    'worker_cpu_seconds','worker_wall_seconds'}

def compare(expected: Path,actual: Path) -> dict:
    if expected.resolve()==actual.resolve():
        raise ValueError('The fresh output and retained reference must differ.')
    counts={}
    for folder in ['inputs','results/certificates','results/campaign']:
        e={p.name:p for p in (expected/folder).glob('*.json')}
        a={p.name:p for p in (actual/folder).glob('*.json')}
        if e.keys()!=a.keys():raise ValueError(f'{folder}: missing or extra files')
        for name in sorted(e):
            left,right=json.loads(e[name].read_text()),json.loads(a[name].read_text())
            if folder=='results/campaign':
                left={k:v for k,v in left.items() if k not in MEASURED}
                right={k:v for k,v in right.items() if k not in MEASURED}
            if left!=right:raise ValueError(f'{folder}/{name}: scientific mismatch')
            if folder!='results/campaign' and e[name].read_bytes()!=a[name].read_bytes():
                raise ValueError(f'{folder}/{name}: deterministic encoding mismatch')
        counts[folder]=len(e)
    if counts!={'inputs':74,'results/certificates':144,'results/campaign':174}:
        raise ValueError('Unexpected campaign size')
    measured=json.loads((actual/'results/tables/summary.json').read_text())
    report={'successful':True,'exact_payload_counts':counts,
            'excluded_measurement_fields':sorted(MEASURED),
            'fresh_retained_process_cpu_seconds':measured['retained_process_cpu_seconds'],
            'fresh_max_rss_kib':measured['max_rss_kib'],
            'interpretation':'Clean-extraction reproduction by the same executor; not independent human validation.'}
    target=actual/'results/reproduction.json';target.write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected',type=Path,default=ROOT)
    parser.add_argument('--actual',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(compare(args.expected,args.actual),indent=2))
