#!/usr/bin/env python3
from __future__ import annotations
import ast
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
    def test_checker_has_no_dynamic_import_escape(self):
        tree=ast.parse(CHECKER.read_text(encoding='utf-8'),filename=str(CHECKER))
        dynamic=[]
        for n in ast.walk(tree):
            if not isinstance(n,ast.Call):
                continue
            if isinstance(n.func,ast.Name) and n.func.id=='__import__':
                dynamic.append(('__import__',n.lineno))
            if isinstance(n.func,ast.Attribute) and n.func.attr=='import_module':
                dynamic.append(('import_module',n.lineno))
        self.assertEqual([],dynamic)
if __name__=='__main__': unittest.main(verbosity=2)
