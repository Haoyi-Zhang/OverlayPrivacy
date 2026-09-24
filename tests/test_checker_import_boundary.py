#!/usr/bin/env python3
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
CHECKER=ROOT/'src/checker.py'
class CheckerImportBoundaryTests(unittest.TestCase):
    def test_checker_does_not_import_producer_entry_points(self):
        tree=ast.parse(CHECKER.read_text(encoding='utf-8'),filename=str(CHECKER))
        imported=[]
        for n in ast.walk(tree):
            if isinstance(n,ast.Import): imported.extend(a.name for a in n.names)
            elif isinstance(n,ast.ImportFrom): imported.append(n.module or '')
        bad=[x for x in imported if any(tok in x.lower() for tok in ('campaign','generator','synthes','producer'))]
        self.assertEqual([],bad)
    def test_checker_source_hash_is_recordable(self):
        self.assertEqual(64,len(hashlib.sha256(CHECKER.read_bytes()).hexdigest()))
if __name__=='__main__': unittest.main(verbosity=2)
