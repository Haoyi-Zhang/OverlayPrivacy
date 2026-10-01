#!/usr/bin/env python3
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]

def flatten(x,p=''):
 out={}
 if isinstance(x,dict):
  for k,v in x.items(): out.update(flatten(v,f'{p}.{k}' if p else str(k)))
 elif isinstance(x,list):
  if all(not isinstance(v,(dict,list)) for v in x): out[p]=x
  else:
   for i,v in enumerate(x): out.update(flatten(v,f'{p}[{i}]'))
 else: out[p]=x
 return out

def main():
 files=[]
 for p in sorted((ROOT/'inputs').glob('*.json')):
  if re.fullmatch(r'[AQS]\d{3}\.json',p.name): files.append(p)
 if len(files)!=73: raise SystemExit(f'expected 73 model inputs, found {len(files)}')
 inv=defaultdict(list); records=[]; canonical_encodings=[]
 for p in files:
  obj=json.loads(p.read_text(encoding='utf-8')); flat=flatten(obj)
  canonical_encodings.append(json.dumps(obj,sort_keys=True,separators=(',',':')))
  for k,v in flat.items():
   if isinstance(v,(str,int,float,bool)) and not isinstance(v,list): inv[k].append(v)
  records.append({'file':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'top_level_keys':sorted(obj) if isinstance(obj,dict) else []})
 fields={}
 for k,vals in sorted(inv.items()):
  if vals and all(isinstance(v,(int,float)) and not isinstance(v,bool) for v in vals): fields[k]={'count':len(vals),'minimum':min(vals),'maximum':max(vals),'unique_count':len(set(vals))}
  elif vals and all(isinstance(v,(str,bool)) for v in vals):
   u=sorted(set(map(str,vals))); fields[k]={'count':len(vals),'unique_count':len(u),'values':u if len(u)<=20 else u[:20]+['...']}
 report={'model_count':len(files),'unique_model_encodings':len(set(canonical_encodings)),'families':{'Q':sum(p.name.startswith('Q') for p in files),'S':sum(p.name.startswith('S') for p in files),'A':sum(p.name.startswith('A') for p in files)},'files':records,'scalar_field_inventory':fields,'interpretation':['These are deterministic constructed stress cases, not a random or representative sample of deployed networks.','Coverage inventories parameter values present in the frozen inputs; it does not establish external validity.','No checksum or snapshot manifest is part of this coverage report.']}
 out=ROOT/'results/verification/model-coverage.json'; out.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
 print(json.dumps({'models':len(files),'fields':len(fields)}))
if __name__=='__main__': main()
