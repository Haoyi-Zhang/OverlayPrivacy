#!/usr/bin/env python3
"""Derive reviewer-facing tightness and structural-reduction statistics.

Only declared campaign fields are consumed. The extractor fails closed when the
frozen 73/71/40 coverage or exact arithmetic relationships change.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MetricsFailure(RuntimeError):
    pass


def need(condition: bool, message: str) -> None:
    if not condition:
        raise MetricsFailure(message)


def frac_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def quantile(values: list[float], q: float) -> float:
    need(bool(values), "quantile requires values")
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def load_main_records(root: Path) -> dict[tuple[str, str], dict]:
    records: dict[tuple[str, str], dict] = {}
    for path in sorted((root / "results" / "campaign").glob("*.json")):
        if "-repeat" in path.stem:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        need(type(payload) is dict, f"{path}: expected object")
        case = payload.get("case")
        scope = payload.get("scope")
        need(type(case) is str and scope in {"all-pairs", "ordered-chain"}, f"{path}: malformed identity")
        key = (case, scope)
        need(key not in records, f"{path}: duplicate main record {key}")
        need(payload.get("valid") is True, f"{path}: valid must be true")
        records[key] = payload
    need(sum(scope == "all-pairs" for _, scope in records) == 73, "expected 73 dense records")
    need(sum(scope == "ordered-chain" for _, scope in records) == 71, "expected 71 ordered records")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    records = load_main_records(root)

    exact_rows = []
    gaps: list[float] = []
    ratios: list[float] = []
    for (case, scope), record in sorted(records.items()):
        if scope != "all-pairs" or "exact_capacity" not in record:
            continue
        need("capacity_bound" in record, f"{case}: missing capacity_bound")
        exact = Fraction(record["exact_capacity"])
        bound = Fraction(record["capacity_bound"])
        need(bound >= exact >= 0, f"{case}: invalid exact/bound ordering")
        gap = bound - exact
        ratio = bound / exact if exact > 0 else None
        gaps.append(float(gap))
        if ratio is not None:
            ratios.append(float(ratio))
        exact_rows.append(
            {
                "model": case,
                "exact": frac_text(exact),
                "canonical_bound": frac_text(bound),
                "absolute_gap": frac_text(gap),
                "ratio": "" if ratio is None else str(float(ratio)),
                "source": f"results/campaign/{case}-all-pairs.json",
            }
        )
    need(len(exact_rows) == 40, f"expected 40 exact models, found {len(exact_rows)}")

    reductions = {}
    for field, label in (("bellman_obligations", "bellman_obligations"), ("potential_entries", "potentials")):
        values = []
        for case in sorted({case for case, scope in records if scope == "ordered-chain"}):
            dense = records[(case, "all-pairs")]
            ordered = records[(case, "ordered-chain")]
            need(type(dense.get(field)) is int and type(ordered.get(field)) is int, f"{case}: malformed {field}")
            need(dense[field] >= ordered[field] >= 0, f"{case}: invalid {field} reduction")
            if dense[field] == 0:
                need(ordered[field] == 0, f"{case}: zero dense {field} but nonzero ordered value")
                continue
            values.append((dense[field] - ordered[field]) / dense[field])
        expected_positive = 70 if field == "bellman_obligations" else 71
        need(len(values) == expected_positive, f"expected {expected_positive} positive-work {field} comparisons")
        reductions[label] = {
            "dense_field": field,
            "ordered_field": field,
            "models_with_positive_work": len(values),
            "zero_work_models": 71 - len(values),
            "minimum_reduction": min(values),
            "median_reduction": statistics.median(values),
            "maximum_reduction": max(values),
            "all_nonnegative": all(value >= 0 for value in values),
        }

    worst = max(exact_rows, key=lambda row: Fraction(row["absolute_gap"]))
    report = {
        "schema_version": 2,
        "source": "results/campaign/*-all-pairs.json and matching ordered-chain records",
        "selected_exact_field": "exact_capacity",
        "selected_bound_field": "capacity_bound",
        "exact_models": len(exact_rows),
        "tightness": {
            "exact_hits": sum(value == 0.0 for value in gaps),
            "absolute_gap": {
                "minimum": min(gaps),
                "q25": quantile(gaps, 0.25),
                "median": statistics.median(gaps),
                "q75": quantile(gaps, 0.75),
                "q90": quantile(gaps, 0.90),
                "maximum": max(gaps),
                "mean": statistics.fmean(gaps),
            },
            "bound_over_exact_ratio": {
                "minimum": min(ratios),
                "median": statistics.median(ratios),
                "q90": quantile(ratios, 0.90),
                "maximum": max(ratios),
                "mean": statistics.fmean(ratios),
            },
            "worst_absolute_gap_record": worst,
        },
        "structural_reduction": reductions,
        "interpretation": [
            "Tightness is evaluated only on tiny models where the complete public-history optimum is exactly enumerable.",
            "The ordered reduction compares two encodings of the same canonical certificate; it is not an empirical claim about all queueing models.",
            "Ratios omit exact value zero to avoid division by zero.",
        ],
    }

    verification = root / "results" / "verification"
    verification.mkdir(parents=True, exist_ok=True)
    output = verification / "reviewer-utility-tightness.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (verification / "reviewer-utility-tightness.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(exact_rows[0]))
        writer.writeheader()
        writer.writerows(exact_rows)

    generated = root / "paper-generated"
    generated.mkdir(exist_ok=True)
    tex = (
        "\\begin{tabular}{lr}\\hline\n"
        f"Tiny models with exact oracle & {len(exact_rows)} \\\\\n"
        f"Exact certificate hits & {report['tightness']['exact_hits']} \\\\\n"
        f"Median absolute gap & {report['tightness']['absolute_gap']['median']:.4f} \\\\\n"
        f"90th-percentile absolute gap & {report['tightness']['absolute_gap']['q90']:.4f} \\\\\n"
        f"Maximum absolute gap & {report['tightness']['absolute_gap']['maximum']:.4f} \\\\\n"
        f"Maximum bound/exact ratio & {report['tightness']['bound_over_exact_ratio']['maximum']:.4f} \\\\\n"
        "\\hline\\end{tabular}\n"
    )
    (generated / "reviewer-metrics.tex").write_text(tex, encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
