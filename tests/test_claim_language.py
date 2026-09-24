#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re, unittest
ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT.parent/'paper'
class ClaimLanguageTests(unittest.TestCase):
    def test_no_unsupported_absolute_priority_language(self):
        patterns=[r'for the first time',r'the first (?:method|work|paper|result|framework|certificate|approach|system)\b',r'the only (?:method|work|paper|result|framework|certificate|approach|system)\b',r'unprecedented',r'guarantee(?:s|d)? acceptance']
        hits=[]
        for p in PAPER.glob('*.tex'):
            text=re.sub(r'(?m)%.*$','',p.read_text(encoding='utf-8'))
            for pat in patterns:
                hits.extend((p.name,text[:m.start()].count('\n')+1,m.group(0)) for m in re.finditer(pat,text,re.I))
        self.assertEqual([],hits)
if __name__=='__main__': unittest.main(verbosity=2)
