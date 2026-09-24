#!/usr/bin/env python3
"""Static and record-level checks for the independent tiny-model semantics path."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "tests" / "test_oracle_bruteforce.py"
RECORD = ROOT / "results" / "oracle-bruteforce.json"

class SemanticIndependenceTests(unittest.TestCase):
    def test_reference_oracle_does_not_import_production_implementation(self) -> None:
        tree = ast.parse(ORACLE.read_text(encoding="utf-8"), filename=str(ORACLE))
        forbidden = []
        dynamic = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".", 1)[0]
                    if top in {"src", "checker", "campaign", "summarize"}:
                        forbidden.append((node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.split(".", 1)[0] in {"src", "checker", "campaign", "summarize"}:
                    forbidden.append((node.lineno, module))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"__import__", "eval", "exec"}:
                dynamic.append((node.lineno, node.func.id))
        self.assertEqual([], forbidden, f"production imports found: {forbidden}")
        self.assertEqual([], dynamic, f"dynamic loading found: {dynamic}")

    def test_reference_record_is_machine_readable_and_nonempty(self) -> None:
        payload = json.loads(RECORD.read_text(encoding="utf-8"))
        self.assertTrue(payload)
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(64, len(hashlib.sha256(encoded).hexdigest()))

if __name__ == "__main__":
    unittest.main(verbosity=2)
