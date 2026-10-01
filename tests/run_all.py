#!/usr/bin/env python3
"""Run every ``test_*.py`` script and propagate the first nonzero status."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_tests(tests: list[Path], optimized: bool = False, cwd: Path = ROOT) -> int:
    """Run ``tests`` in order and return the first nonzero status.

    Keeping this logic in a callable function lets the acceptance suite verify
    that a shell-like test loop cannot continue past, or hide, a failed test.
    """
    for test in tests:
        command = [sys.executable]
        if optimized:
            command.append("-O")
        command.append(str(test))
        print(f"==> {' '.join(command)}", flush=True)
        completed = subprocess.run(command, cwd=cwd)
        if completed.returncode != 0:
            return completed.returncode
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--optimized", action="store_true", help="run each test with python -O")
    args = parser.parse_args()

    tests = sorted((ROOT / "tests").glob("test_*.py"))
    if not tests:
        raise SystemExit("no test_*.py scripts found")
    raise SystemExit(run_tests(tests, optimized=args.optimized))


if __name__ == "__main__":
    main()
