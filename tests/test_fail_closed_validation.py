#!/usr/bin/env python3
"""Acceptance tests for fail-closed scientific validation under normal and -O modes."""
from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _interpreters():
    return (("normal", []), ("optimized", ["-O"]))


class FailClosedValidationTests(unittest.TestCase):
    def test_native_assert_is_absent_from_scientific_acceptance_paths(self):
        files = [
            ROOT / "tests" / "test_calibrations.py",
            ROOT / "src" / "worker.py",
            ROOT / "src" / "summarize.py",
        ]
        found = []
        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assert):
                    found.append((str(path.relative_to(ROOT)), node.lineno))
        self.assertEqual([], found)

    def test_wrong_one_slot_scalar_exits_nonzero_without_success_report(self):
        for label, optimize in _interpreters():
            with self.subTest(mode=label), tempfile.TemporaryDirectory() as folder:
                root = Path(folder) / "data"
                report = root / "results" / "calibrations.json"
                code = textwrap.dedent(
                    f"""
                    import sys
                    from fractions import Fraction as F
                    from pathlib import Path
                    sys.path.insert(0, {str(ROOT / 'tests')!r})
                    import test_calibrations as calibration
                    original = calibration.capacity
                    def wrong_scalar(model, *args, **kwargs):
                        value, details = original(model, *args, **kwargs)
                        return value + F(1, 7), details
                    calibration.run_calibrations(
                        data_root=Path({str(root)!r}),
                        report_path=Path({str(report)!r}),
                        capacity_fn=wrong_scalar,
                    )
                    """
                )
                completed = subprocess.run(
                    [sys.executable, *optimize, "-c", code],
                    cwd=ROOT,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.assertNotEqual(0, completed.returncode)
                self.assertFalse(report.exists())

    def test_worker_wrong_scalar_exits_nonzero_without_scientific_outputs(self):
        """A bad exact scalar must fail before the worker commits either file."""
        source = ROOT / "inputs" / "A003.json"
        for label, optimize in _interpreters():
            with self.subTest(mode=label), tempfile.TemporaryDirectory() as folder:
                root = Path(folder) / "data"
                (root / "inputs").mkdir(parents=True)
                shutil.copy2(source, root / "inputs" / source.name)
                code = textwrap.dedent(
                    f"""
                    import sys
                    from fractions import Fraction as F
                    sys.path.insert(0, {str(ROOT / 'src')!r})
                    import worker
                    original = worker.capacity
                    def wrong_scalar(model, *args, **kwargs):
                        value, details = original(model, *args, **kwargs)
                        return value + F(1, 7), details
                    worker.capacity = wrong_scalar
                    sys.argv = [
                        'worker.py', '--root', {str(root)!r}, '--case', 'A003',
                        '--scope', 'all-pairs'
                    ]
                    worker.main()
                    """
                )
                completed = subprocess.run(
                    [sys.executable, *optimize, "-c", code],
                    cwd=ROOT,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.assertNotEqual(0, completed.returncode)
                self.assertFalse(
                    (root / "results" / "certificates" / "A003-all-pairs.json").exists()
                )
                self.assertFalse(
                    (root / "results" / "campaign" / "A003-all-pairs.json").exists()
                )

    def test_rate_bound_violation_copy_exits_nonzero_without_success_report(self):
        source = ROOT / "results" / "campaign" / "A003-all-pairs.json"
        retained = json.loads(source.read_text(encoding="utf-8"))
        self.assertEqual("1", retained["capacity_bound"])
        for label, optimize in _interpreters():
            with self.subTest(mode=label), tempfile.TemporaryDirectory() as folder:
                root = Path(folder) / "data"
                campaign = root / "results" / "campaign"
                campaign.mkdir(parents=True)
                corrupted = dict(retained)
                corrupted["capacity_bound"] = "2"
                (campaign / source.name).write_text(
                    json.dumps(corrupted, sort_keys=True, separators=(",", ":")) + "\n",
                    encoding="utf-8",
                )
                report = root / "results" / "calibrations.json"
                completed = subprocess.run(
                    [
                        sys.executable,
                        *optimize,
                        str(ROOT / "tests" / "test_calibrations.py"),
                        "--data-root",
                        str(root),
                        "--report",
                        str(report),
                    ],
                    cwd=ROOT,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.assertNotEqual(0, completed.returncode)
                self.assertFalse(report.exists())

    def test_corrupt_campaign_record_makes_summarize_fail_without_outputs(self):
        for label, optimize in _interpreters():
            with self.subTest(mode=label), tempfile.TemporaryDirectory() as folder:
                root = Path(folder) / "data"
                (root / "inputs").mkdir(parents=True)
                shutil.copy2(ROOT / "inputs" / "selection.json", root / "inputs" / "selection.json")
                shutil.copytree(ROOT / "results" / "campaign", root / "results" / "campaign")
                target = root / "results" / "campaign" / "Q001-all-pairs.json"
                record = json.loads(target.read_text(encoding="utf-8"))
                record["valid"] = False
                target.write_text(json.dumps(record) + "\n", encoding="utf-8")
                completed = subprocess.run(
                    [
                        sys.executable,
                        *optimize,
                        str(ROOT / "src" / "summarize.py"),
                        "--root",
                        str(root),
                    ],
                    cwd=ROOT,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.assertNotEqual(0, completed.returncode)
                tables = root / "results" / "tables"
                self.assertFalse((tables / "summary.json").exists())
                self.assertFalse((tables / "campaign.csv").exists())
                self.assertFalse((tables / "repetitions.csv").exists())

    def test_test_runner_propagates_failure_and_stops(self):
        """The documented loop must return failure and skip later tests."""
        sys.path.insert(0, str(ROOT / "tests"))
        try:
            import run_all
        finally:
            sys.path.pop(0)
        for label, optimize in _interpreters():
            with self.subTest(mode=label), tempfile.TemporaryDirectory() as folder:
                folder_path = Path(folder)
                ok = folder_path / "test_00_ok.py"
                bad = folder_path / "test_01_bad.py"
                late = folder_path / "test_02_late.py"
                marker = folder_path / "late-ran"
                ok.write_text("raise SystemExit(0)\n", encoding="utf-8")
                bad.write_text("raise SystemExit(7)\n", encoding="utf-8")
                late.write_text(
                    f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n",
                    encoding="utf-8",
                )
                status = run_all.run_tests(
                    [ok, bad, late], optimized=bool(optimize), cwd=folder_path
                )
                self.assertEqual(7, status)
                self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
