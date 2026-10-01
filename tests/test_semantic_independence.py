#!/usr/bin/env python3
"""Checks for the algorithmically distinct tiny-model comparison path.

The direct enumerator and production dynamic program share ``model.kernel``.
The comparison entry may call ``oracle.capacity`` to obtain the value under
test, but the direct enumeration functions may not reuse that recursion or any
certificate/tree implementation.
"""
from __future__ import annotations

import ast
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE_SOURCE = ROOT / "tests" / "test_oracle_bruteforce.py"
RETAINED_RECORD = ROOT / "results" / "oracle-bruteforce.json"
METADATA = ROOT / "results" / "verification" / "semantic-triangulation.json"
REFERENCE_FUNCTIONS = {
    "_rows",
    "enumerate_policy_tables",
    "channel_for_policy",
    "channel_capacity",
    "brute_capacity",
}
REQUIRED_COVERAGE = {
    "test_methods": 2,
    "two_slot_cases": 192,
    "two_slot_policy_tables": 2976,
    "deeper_cases": 16,
    "deeper_policy_tables": 1856,
}
SCIENTIFIC_FIELDS = (
    "schema_version",
    "successful",
    "test_methods",
    "failures",
    "errors",
    "two_slot_cases",
    "two_slot_policy_tables",
    "two_slot_optimum_sum",
    "two_slot_value_histogram",
    "deeper_cases",
    "deeper_policy_tables",
    "deeper_optimum_sum",
    "deeper_value_histogram",
    "retained_output",
)


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _histogram_total(histogram: dict[str, int]) -> int:
    return sum(histogram.values())


def _histogram_sum(histogram: dict[str, int]) -> F:
    return sum((F(value) * count for value, count in histogram.items()), F(0))


def validate_record(payload: dict) -> dict:
    """Validate required scientific coverage and separate environment fields."""
    _need(type(payload) is dict, "record must be a JSON object")
    missing = [field for field in SCIENTIFIC_FIELDS if field not in payload]
    _need(not missing, f"record is missing required fields: {missing}")
    _need(payload["schema_version"] == 2, "unexpected record schema")
    _need(payload["successful"] is True, "successful must be true")
    _need(type(payload["failures"]) is int and payload["failures"] == 0, "failures must be zero")
    _need(type(payload["errors"]) is int and payload["errors"] == 0, "errors must be zero")
    for field, expected in REQUIRED_COVERAGE.items():
        _need(type(payload[field]) is int, f"{field} must be an integer")
        _need(payload[field] == expected, f"{field} must equal {expected}")

    for prefix in ("two_slot", "deeper"):
        histogram = payload[f"{prefix}_value_histogram"]
        _need(type(histogram) is dict and histogram, f"{prefix} histogram must be nonempty")
        for value, count in histogram.items():
            F(value)
            _need(type(count) is int and count > 0, f"{prefix} histogram counts must be positive integers")
        _need(
            _histogram_total(histogram) == payload[f"{prefix}_cases"],
            f"{prefix} histogram coverage does not match case count",
        )
        _need(
            _histogram_sum(histogram) == F(payload[f"{prefix}_optimum_sum"]),
            f"{prefix} optimum sum does not match histogram",
        )

    _need(
        payload["retained_output"]
        == "scalar optima summaries and aggregate counts only; no optimizing policy",
        "unexpected retained-output declaration",
    )
    environment = payload.get("environment_measurements")
    _need(type(environment) is dict, "environment_measurements must be separate")
    _need(
        type(environment.get("cpu_seconds")) in (int, float)
        and environment["cpu_seconds"] >= 0,
        "cpu_seconds must be a nonnegative environment measurement",
    )
    _need(
        type(environment.get("peak_rss_kib")) is int
        and environment["peak_rss_kib"] > 0,
        "peak_rss_kib must be a positive environment measurement",
    )
    return {field: payload[field] for field in SCIENTIFIC_FIELDS}


class SemanticPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.fresh_path = Path(cls.temporary.name) / "oracle-bruteforce.json"
        subprocess.run(
            [
                sys.executable,
                str(REFERENCE_SOURCE),
                "--output",
                str(cls.fresh_path),
            ],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls.retained = json.loads(RETAINED_RECORD.read_text(encoding="utf-8"))
        cls.fresh = json.loads(cls.fresh_path.read_text(encoding="utf-8"))
        cls.metadata = json.loads(METADATA.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_reference_functions_do_not_reuse_tested_recursion_or_certificates(self) -> None:
        tree = ast.parse(REFERENCE_SOURCE.read_text(encoding="utf-8"), filename=str(REFERENCE_SOURCE))
        functions = {
            node.name: node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertTrue(REFERENCE_FUNCTIONS <= functions.keys())

        globally_forbidden_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in {"producer", "checker", "campaign", "summarize"}:
                        globally_forbidden_imports.append((node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.split(".", 1)[0] in {"producer", "checker", "campaign", "summarize"}:
                    globally_forbidden_imports.append((node.lineno, module))
        self.assertEqual([], globally_forbidden_imports)

        forbidden_reference_uses = []
        for name in sorted(REFERENCE_FUNCTIONS):
            for node in ast.walk(functions[name]):
                if isinstance(node, ast.ImportFrom) and (node.module or "").split(".", 1)[0] == "oracle":
                    forbidden_reference_uses.append((name, node.lineno, "oracle import"))
                elif isinstance(node, ast.Import) and any(
                    alias.name.split(".", 1)[0] == "oracle" for alias in node.names
                ):
                    forbidden_reference_uses.append((name, node.lineno, "oracle import"))
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {
                    "capacity",
                    "production_capacity",
                    "make",
                    "check",
                    "minimum_tree",
                }:
                    forbidden_reference_uses.append((name, node.lineno, node.func.id))
        self.assertEqual([], forbidden_reference_uses)

        comparison = functions.get("production_capacity")
        self.assertIsNotNone(comparison)
        oracle_imports = [
            node
            for node in ast.walk(comparison)
            if isinstance(node, ast.ImportFrom) and node.module == "oracle"
        ]
        self.assertEqual(1, len(oracle_imports), "comparison boundary must import oracle.capacity exactly once")

    def test_metadata_states_shared_dependencies_without_hash_fingerprints(self) -> None:
        self.assertEqual(2, self.metadata["schema_version"])
        self.assertEqual(
            "algorithmically distinct paths with a shared declared one-step kernel",
            self.metadata["claim_level"],
        )
        shared = {
            (item["path"], item["symbol"], item["used_by"])
            for item in self.metadata["shared_dependencies"]
        }
        self.assertIn(("src/model.py", "kernel", "both paths"), shared)
        self.assertIn(("src/oracle.py", "capacity", "comparison entry only"), shared)
        self.assertEqual(REQUIRED_COVERAGE, self.metadata["required_coverage"])
        self.assertEqual(
            ["cpu_seconds", "peak_rss_kib"],
            self.metadata["environment_measurements"],
        )
        self.assertFalse(any("sha256" in key.lower() or "hash" in key.lower() for key in self.metadata))
        self.assertIn("no source or result hash", self.metadata["snapshot_policy"].lower())

    def test_retained_record_is_valid_and_matches_fresh_scientific_payload(self) -> None:
        retained_science = validate_record(self.retained)
        fresh_science = validate_record(self.fresh)
        self.assertEqual(retained_science, fresh_science)
        self.assertNotEqual(
            self.retained["environment_measurements"],
            {},
            "environment measurements must be present but are not equality identities",
        )

    def test_false_or_incomplete_records_are_rejected(self) -> None:
        mutations = []

        changed = copy.deepcopy(self.retained)
        changed["successful"] = False
        mutations.append(("successful=false", changed))

        changed = copy.deepcopy(self.retained)
        changed["failures"] = 1
        mutations.append(("nonzero failures", changed))

        changed = copy.deepcopy(self.retained)
        changed["errors"] = 1
        mutations.append(("nonzero errors", changed))

        changed = copy.deepcopy(self.retained)
        changed["two_slot_cases"] -= 1
        mutations.append(("wrong scientific count", changed))

        changed = copy.deepcopy(self.retained)
        changed["two_slot_optimum_sum"] = "0"
        mutations.append(("wrong scientific scalar", changed))

        changed = copy.deepcopy(self.retained)
        changed.pop("deeper_policy_tables")
        mutations.append(("missing required coverage", changed))

        for name, payload in mutations:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validate_record(payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
