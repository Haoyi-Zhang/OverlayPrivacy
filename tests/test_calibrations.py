"""Exact analytic calibration checks added after the frozen campaign.

These validate proved special cases and continuity inequalities. They are not
additional workload samples or evidence of model-to-deployment conformance.
All scientific checks are explicit so ``python -O`` cannot remove them.
"""
from __future__ import annotations

import argparse
import json
import random
import resource
import sys
import time
from fractions import Fraction as F
from itertools import combinations_with_replacement
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from campaign import base  # noqa: E402
from checker import check  # noqa: E402
from model import kernel  # noqa: E402
from oracle import capacity  # noqa: E402
from producer import make  # noqa: E402


class CalibrationFailure(RuntimeError):
    """Raised when a calibration obligation is false or malformed."""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise CalibrationFailure(message)


def cap(rows):
    return sum(max(col) for col in zip(*rows))


def tv(left, right):
    return sum(abs(a - b) for a, b in zip(left, right)) / 2


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _one_slot_grid(
    capacity_fn: Callable = capacity,
    checker_fn: Callable = check,
) -> int:
    count = 0
    for m in (2, 3, 4):
        for rates in combinations_with_replacement([F(k, 4) for k in range(5)], m):
            for padding in [F(k, 4) for k in range(5)]:
                config = base(m=m, B=1, H=1)
                config.update(
                    arrival_rates=list(map(str, rates)),
                    padding=str(padding),
                )
                model = kernel(config)
                expected = 1 + (1 - padding) * (rates[-1] - rates[0])
                actual, _ = capacity_fn(model)
                verified = checker_fn(model, make(model, "ordered-chain"))
                certified = F(verified["capacity_bound"])
                need(
                    actual == expected,
                    f"one-slot scalar mismatch for m={m}, rates={rates}, "
                    f"padding={padding}: actual={actual}, expected={expected}",
                )
                need(
                    certified == expected,
                    f"one-slot certificate mismatch for m={m}, rates={rates}, "
                    f"padding={padding}: certified={certified}, expected={expected}",
                )
                count += 1
    return count


def _continuity_grid() -> int:
    rng = random.Random(229501)
    count = 0
    for m in range(2, 8):
        for columns in range(2, 8):
            for _ in range(3):

                def distribution():
                    row = [rng.randrange(9) for _ in range(columns)]
                    if not sum(row):
                        row[0] = 1
                    total = sum(row)
                    return [F(x, total) for x in row]

                left = [distribution() for _ in range(m)]
                right = [distribution() for _ in range(m)]
                error = sum(tv(a, b) for a, b in zip(left, right))
                need(
                    cap(right) <= min(F(m), cap(left) + error),
                    f"whole-row continuity inequality failed for m={m}, columns={columns}",
                )
                count += 1
    return count


def _retained_rate_bounds(data_root: Path) -> int:
    """Check every eligible retained dense record under ``data_root``."""
    count = 0
    campaign = data_root / "results" / "campaign"
    if not campaign.exists():
        return count
    for path in sorted(campaign.glob("*-all-pairs.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        need(type(record) is dict, f"{path}: record must be an object")
        need("config" in record and "capacity_bound" in record, f"{path}: missing scientific fields")
        config = record["config"]
        need(type(config) is dict, f"{path}: config must be an object")
        initial = config.get("initial_queues")
        raw_rates = config.get("arrival_rates")
        need(type(initial) is list and type(raw_rates) is list, f"{path}: malformed rate-bound inputs")
        if len(set(initial)) != 1:
            continue
        rates = list(map(F, raw_rates))
        if rates != sorted(rates):
            continue
        horizon = config["horizon"]
        labels = len(rates)
        rate_bound = 1 + sum(1 - (1 - (upper - lower)) ** horizon for lower, upper in zip(rates, rates[1:]))
        certificate = F(record["capacity_bound"])
        need(
            certificate <= min(F(labels), rate_bound),
            f"{path}: retained capacity bound {certificate} exceeds rate bound {rate_bound}",
        )
        linear_bound = 1 + horizon * (rates[-1] - rates[0])
        need(
            rate_bound <= linear_bound,
            f"{path}: derived rate bound {rate_bound} exceeds linear bound {linear_bound}",
        )
        count += 1
    return count


def run_calibrations(
    data_root: Path = ROOT,
    report_path: Path | None = None,
    capacity_fn: Callable = capacity,
    checker_fn: Callable = check,
) -> dict:
    """Run all calibrations and write a success report only after all pass."""
    data_root = Path(data_root).resolve()
    report_path = Path(report_path) if report_path is not None else data_root / "results" / "calibrations.json"
    report_path = report_path.resolve()
    report_path.unlink(missing_ok=True)

    started = time.process_time()
    one_slot = _one_slot_grid(capacity_fn=capacity_fn, checker_fn=checker_fn)
    continuity = _continuity_grid()
    eligible = _retained_rate_bounds(data_root)
    need(one_slot == 600, f"expected 600 one-slot cases, found {one_slot}")
    need(continuity == 108, f"expected 108 continuity cases, found {continuity}")

    report = {
        "successful": True,
        "one_slot_cases": one_slot,
        "continuity_cases": continuity,
        "continuity_seed": 229501,
        "eligible_retained_rate_cases": eligible,
        "cpu_seconds": time.process_time() - started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "status": (
            "Post-campaign validation of proved analytic calibrations; "
            "not a workload extension."
        ),
    }
    _atomic_write_json(report_path, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=ROOT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    print(json.dumps(run_calibrations(args.data_root, args.report), indent=2))


if __name__ == "__main__":
    main()
