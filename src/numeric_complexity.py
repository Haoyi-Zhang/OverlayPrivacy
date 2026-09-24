#!/usr/bin/env python3
from __future__ import annotations
from fractions import Fraction
from pathlib import Path
import json,re,statistics
ROOT=Path(__file__).resolve().parents[1]
PAT=re.compile(r'^-?\d+(?:/[1-9]\d*)?$')
def walk(x,path=''):
 if isinstance(x,dict):
  for k,v in x.items(): yield from walk(v,f'{path}.{k}' if path else str(k))
 elif isinstance(x,list):
  for i,v in enumerate(x): yield from walk(v,f'{path}[{i}]')
 elif isinstance(x,str) and PAT.fullmatch(x.strip()):
  try: yield path,Fraction(x)
  except Exception: return
 elif isinstance(x,int) and not isinstance(x,bool): yield path,Fraction(x)
def main():
 rows=[]
 for p in sorted((ROOT/'results').rglob('*.json')):
  if 'verification' in p.parts: continue
  try: obj=json.loads(p.read_text(encoding='utf-8'))
  except Exception: continue
  for path,x in walk(obj):
   rows.append({'file':str(p.relative_to(ROOT)),'path':path,'numerator_bits':abs(x.numerator).bit_length(),'denominator_bits':x.denominator.bit_length()})
 if not rows: raise SystemExit('no exact rational values found')
 nb=[r['numerator_bits'] for r in rows]; db=[r['denominator_bits'] for r in rows]
 worst_num=max(rows,key=lambda r:r['numerator_bits']); worst_den=max(rows,key=lambda r:r['denominator_bits'])
 report={'exact_rational_values':len(rows),'numerator_bits':{'median':statistics.median(nb),'maximum':max(nb),'q90':sorted(nb)[int(.9*(len(nb)-1))]},'denominator_bits':{'median':statistics.median(db),'maximum':max(db),'q90':sorted(db)[int(.9*(len(db)-1))]},'worst_numerator':worst_num,'worst_denominator':worst_den,'interpretation':['Scientific comparisons use exact integers and fractions; timing and memory remain machine dependent.','Bit length, not decimal digit count, is the relevant arithmetic-size indicator.']}
 (ROOT/'results/verification/numeric-complexity.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
 print(json.dumps(report,indent=2))
if __name__=='__main__': main()
