#!/usr/bin/env python3
"""Reproducible Crossref candidate discovery; not a substitute for reading."""
from __future__ import annotations
from pathlib import Path
import json,re,time,urllib.parse,urllib.request
ROOT=Path(__file__).resolve().parents[1]
QUERIES=[
 'anonymous communication traffic analysis queue timing linkability',
 'website fingerprinting complete history defense leakage',
 'total variation coupling certificate privacy leakage',
 'minimum spanning tree pairwise total variation capacity',
 'ordered adjacent pair certificate monotone coupling',
]
UA='linkability-literature-audit/1.0 (mailto:research-audit@example.invalid)'
def get(url):
 req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=30) as r: return json.load(r)
def normdoi(s): return (s or '').strip().lower().removeprefix('https://doi.org/')
def main():
 records={}; errors=[]
 for q in QUERIES:
  url='https://api.crossref.org/works?'+urllib.parse.urlencode({'query.bibliographic':q,'filter':'from-pub-date:2022-01-01,until-pub-date:2026-12-31','rows':20,'select':'DOI,title,author,published-print,published-online,issued,publisher,container-title,type,URL,score'})
  try: items=get(url)['message']['items']
  except Exception as e: errors.append({'query':q,'error':repr(e)}); continue
  for it in items:
   doi=normdoi(it.get('DOI')); title=(it.get('title') or [''])[0].strip()
   key=doi or re.sub(r'\W+',' ',title.lower()).strip()
   if not key: continue
   date=it.get('published-print') or it.get('published-online') or it.get('issued') or {}
   year=((date.get('date-parts') or [[None]])[0] or [None])[0]
   rec={'title':title,'doi':doi or None,'year':year,'publisher':it.get('publisher'),'venue':(it.get('container-title') or [''])[0],'type':it.get('type'),'url':it.get('URL'),'crossref_score':it.get('score'),'queries':[],'evidence_level':'candidate_screen'}
   if key not in records: records[key]=rec
   records[key]['queries'].append(q)
  time.sleep(.25)
 out={'search_date':'2026-09-20','queries':QUERIES,'candidate_count':len(records),'candidates':sorted(records.values(),key=lambda x:(-(x.get('crossref_score') or 0),x.get('title') or '')),'errors':errors,'warning':'Automated candidates are not cited evidence until manually screened and, when substantively used, read in full.'}
 p=ROOT/'results/verification/literature-candidate-scan.json'; p.write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
 print(json.dumps({'candidates':len(records),'errors':len(errors)}))
if __name__=='__main__': main()
