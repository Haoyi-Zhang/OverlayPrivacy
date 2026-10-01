"""Validate the complete frozen campaign and write exact CSV/scalar summaries.

All scientific checks are explicit and remain active under ``python -O``. The
three derived success files are removed before validation and committed only
after every retained main and repetition record passes.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import statistics
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGGREGATE_RATIONAL_FIELDS = (
    "capacity_bound",
    "best_star_bound",
    "chain_bound",
    "uniform_cover_bound",
    "exact_capacity",
    "exact_pair_summary_bound",
)


class SummaryValidationError(RuntimeError):
    """Raised when a retained campaign record violates a scientific invariant."""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise SummaryValidationError(message)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _csv_text(rows: list[dict]) -> str:
    need(bool(rows), "cannot write an empty CSV summary")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def _fraction_bits(raw: str) -> tuple[int, int]:
    value = F(raw)
    return abs(value.numerator).bit_length(), value.denominator.bit_length()


def _aggregate_complexity(main_records: list[dict]) -> dict:
    observations = []
    for record in main_records:
        for field in AGGREGATE_RATIONAL_FIELDS:
            if field not in record:
                continue
            numerator_bits, denominator_bits = _fraction_bits(record[field])
            observations.append(
                {
                    "case": record["case"],
                    "scope": record["scope"],
                    "field": field,
                    "value": record[field],
                    "numerator_bits": numerator_bits,
                    "denominator_bits": denominator_bits,
                }
            )
    need(bool(observations), "no aggregate rational fields found")

    maximum_numerator = max(item["numerator_bits"] for item in observations)
    maximum_denominator = max(item["denominator_bits"] for item in observations)

    def field_summary(field: str) -> dict:
        selected = [item for item in observations if item["field"] == field]
        need(bool(selected), f"aggregate field {field} is absent")
        maximum = max(item["numerator_bits"] for item in selected)
        witnesses = [
            {key: item[key] for key in ("case", "scope", "value")}
            for item in selected
            if item["numerator_bits"] == maximum
        ]
        return {
            "records": len(selected),
            "maximum_numerator_bits": maximum,
            "numerator_witnesses": witnesses,
            "maximum_denominator_bits": max(item["denominator_bits"] for item in selected),
        }

    return {
        "field_set": list(AGGREGATE_RATIONAL_FIELDS),
        "records": len(observations),
        "maximum_numerator_bits": maximum_numerator,
        "maximum_denominator_bits": maximum_denominator,
        "maximum_numerator_witnesses": [
            {key: item[key] for key in ("case", "scope", "field", "value")}
            for item in observations
            if item["numerator_bits"] == maximum_numerator
        ],
        "maximum_denominator_witnesses": [
            {key: item[key] for key in ("case", "scope", "field", "value")}
            for item in observations
            if item["denominator_bits"] == maximum_denominator
        ],
        "capacity_bound": field_summary("capacity_bound"),
        "best_star_bound": field_summary("best_star_bound"),
    }


def summarize(root: Path) -> dict:
    root = Path(root).resolve()
    tables = root / "results" / "tables"
    output_paths = [
        tables / "campaign.csv",
        tables / "repetitions.csv",
        tables / "summary.json",
    ]
    for path in output_paths:
        path.unlink(missing_ok=True)

    plan_path = root / "inputs" / "selection.json"
    need(plan_path.is_file(), f"missing selection metadata: {plan_path}")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    need(type(plan) is list, "selection metadata must be a list")

    rows: list[dict] = []
    main_records: list[dict] = []
    tiny: list[dict] = []
    main_by_key: dict[tuple[str, str], dict] = {}
    ordered_equalities = []

    for item in plan:
        need(type(item) is dict, "selection entry must be an object")
        name = item["case"]
        dense = None
        scopes = ["all-pairs"] + (["ordered-chain"] if item["ordered"] else [])
        for scope in scopes:
            path = root / "results" / "campaign" / f"{name}-{scope}.json"
            need(path.is_file(), f"missing main record: {path}")
            record = json.loads(path.read_text(encoding="utf-8"))
            main_records.append(record)
            main_by_key[name, scope] = record

            need(record.get("valid") is True, f"{path}: valid is not true")
            need(record.get("case") == name, f"{path}: case identifier mismatch")
            need(record.get("scope") == scope, f"{path}: scope mismatch")
            need(record.get("config") == item["config"], f"{path}: config differs from selection metadata")
            need(record.get("repeat") == 0, f"{path}: main record repeat must be zero")

            config = record["config"]
            labels = len(config["arrival_rates"])
            pairs = labels * (labels - 1) // 2 if scope == "all-pairs" else labels - 1
            expected_potentials = (
                pairs
                * (config["horizon"] + 1)
                * (config["token_capacity"] + 1)
                * (config["queue_capacity"] + 1) ** 2
            )
            expected_obligations = (
                pairs
                * config["horizon"]
                * (1 + 2 * config["token_capacity"])
                * (config["queue_capacity"] + 1) ** 2
            )
            need(
                record.get("potential_entries") == expected_potentials,
                f"{path}: potential count mismatch",
            )
            need(
                record.get("bellman_obligations") == expected_obligations,
                f"{path}: Bellman-obligation count mismatch",
            )

            if scope == "all-pairs":
                dense = record
            else:
                need(dense is not None, f"{path}: ordered record lacks dense predecessor")
                equal = record["capacity_bound"] == dense["capacity_bound"]
                ordered_equalities.append(equal)
                need(equal, f"{path}: ordered and dense canonical bounds differ")

            if item["tiny_oracle"] and scope == "all-pairs":
                for field in ("exact_capacity", "exact_pair_summary_bound", "capacity_bound"):
                    need(field in record, f"{path}: missing {field}")
                need(
                    F(record["exact_capacity"])
                    <= F(record["exact_pair_summary_bound"])
                    <= F(record["capacity_bound"]),
                    f"{path}: exact, pair-summary, and canonical layers are not ordered",
                )
                tiny.append(record)

            rows.append(
                {
                    "case": name,
                    "group": item["group"],
                    "scope": scope,
                    "m": labels,
                    "B": config["queue_capacity"],
                    "H": config["horizon"],
                    "R": config["refill_period"],
                    "C": config["token_capacity"],
                    "padding": config["padding"],
                    "overflow": config["observe_overflow"],
                    "bound": record["capacity_bound"],
                    "bound_decimal": f"{float(F(record['capacity_bound'])):.9f}",
                    "exact": record.get("exact_capacity", ""),
                    "exact_pair_bound": record.get("exact_pair_summary_bound", ""),
                    "best_star": record.get("best_star_bound", ""),
                    "uniform_cover": record.get("uniform_cover_bound", ""),
                    "obligations": record["bellman_obligations"],
                    "potentials": record["potential_entries"],
                    "support_visits": record["weighted_support_visits"],
                    "max_potential_value_bits": record["maximum_rational_bits"],
                    "bytes": record["certificate_bytes"],
                    "generation_cpu": record["generation_cpu_seconds"],
                    "checking_cpu": record["checking_cpu_seconds"],
                    "peak_rss_kib": record["peak_rss_kib"],
                }
            )

    need(len(plan) == 73, f"expected 73 models, found {len(plan)}")
    need(len(main_records) == 144, f"expected 144 main records, found {len(main_records)}")
    need(len(tiny) == 40, f"expected 40 tiny-oracle records, found {len(tiny)}")
    need(len(ordered_equalities) == 71, f"expected 71 ordered comparisons, found {len(ordered_equalities)}")
    need(all(ordered_equalities), "not all ordered bounds equal their dense counterparts")

    repeats = []
    all_records = list(main_records)
    repeat_count = 0
    for case in ("S018", "S027", "S036"):
        for scope in ("all-pairs", "ordered-chain"):
            repeat_records = []
            main_record = main_by_key[case, scope]
            for repeat in range(1, 6):
                path = root / "results" / "campaign" / f"{case}-{scope}-repeat{repeat}.json"
                need(path.is_file(), f"missing repetition record: {path}")
                record = json.loads(path.read_text(encoding="utf-8"))
                need(record.get("valid") is True, f"{path}: valid is not true")
                need(record.get("case") == case, f"{path}: case identifier mismatch")
                need(record.get("scope") == scope, f"{path}: scope mismatch")
                need(record.get("repeat") == repeat, f"{path}: repeat index mismatch")
                need(record.get("config") == main_record["config"], f"{path}: config differs from main record")
                need(
                    record.get("capacity_bound") == main_record["capacity_bound"],
                    f"{path}: repeated capacity bound differs from main record",
                )
                repeat_records.append(record)
            need(
                len({record["capacity_bound"] for record in repeat_records}) == 1,
                f"{case}/{scope}: repetition bounds are not identical",
            )
            all_records.extend(repeat_records)
            repeat_count += len(repeat_records)
            values = [
                record["generation_cpu_seconds"] + record["checking_cpu_seconds"]
                for record in repeat_records
            ]
            repeats.append(
                {
                    "case": case,
                    "m": len(repeat_records[0]["config"]["arrival_rates"]),
                    "scope": scope,
                    "median_cpu": statistics.median(values),
                    "min_cpu": min(values),
                    "max_cpu": max(values),
                    "median_generation": statistics.median(
                        record["generation_cpu_seconds"] for record in repeat_records
                    ),
                    "median_checking": statistics.median(
                        record["checking_cpu_seconds"] for record in repeat_records
                    ),
                    "min_rss_kib": min(record["peak_rss_kib"] for record in repeat_records),
                    "max_rss_kib": max(record["peak_rss_kib"] for record in repeat_records),
                    "bytes": repeat_records[0]["certificate_bytes"],
                }
            )
    need(repeat_count == 30, f"expected 30 repetition records, found {repeat_count}")

    aggregate_complexity = _aggregate_complexity(main_records)
    potential_bits = max(record["maximum_rational_bits"] for record in main_records)
    need(potential_bits == 82, f"expected maximum potential-value width 82, found {potential_bits}")
    need(
        aggregate_complexity["capacity_bound"]["maximum_numerator_bits"] == 83,
        "capacity-bound numerator-width regression",
    )
    need(
        aggregate_complexity["best_star_bound"]["maximum_numerator_bits"] == 84,
        "best-star numerator-width regression",
    )

    summary = {
        "successful": True,
        "models": len(plan),
        "dense": 73,
        "ordered": 71,
        "ordered_index_convention": "supplied label indices; no automatic relabeling",
        "oracle_models": len(tiny),
        "repetition_runs": repeat_count,
        "all_ordered_bounds_equal": True,
        "all_oracles_below_bounds": True,
        "maximum_oracle_nodes": max(record["oracle_nodes"] for record in tiny),
        "maximum_potential_value_bits": potential_bits,
        "aggregate_rational_complexity": aggregate_complexity,
        "max_rss_kib": max(record["peak_rss_kib"] for record in all_records),
        "retained_process_cpu_seconds": sum(
            record.get("process_cpu_seconds", record["worker_cpu_seconds"])
            for record in all_records
        ),
        "process_cpu_fallback_records": [
            record["case"] + "-" + record["scope"]
            for record in all_records
            if "process_cpu_seconds" not in record
        ],
        "exact_equals_certificate": sum(
            F(record["exact_capacity"]) == F(record["capacity_bound"])
            for record in tiny
        ),
        "median_absolute_gap": statistics.median(
            float(F(record["capacity_bound"]) - F(record["exact_capacity"]))
            for record in tiny
        ),
        "maximum_absolute_gap": max(
            float(F(record["capacity_bound"]) - F(record["exact_capacity"]))
            for record in tiny
        ),
        "maximum_gap_case": max(
            tiny,
            key=lambda record: F(record["capacity_bound"]) - F(record["exact_capacity"]),
        )["case"],
        "maximum_relative_bound_ratio": max(
            float(F(record["capacity_bound"]) / F(record["exact_capacity"]))
            for record in tiny
        ),
        "note": (
            "Exact finite validation, not deployment evidence. Potential-value bit width "
            "is distinct from aggregate-result numerator and denominator widths. RSS is "
            "an unadjusted process high-water mark including startup. CPU excludes "
            "discarded intake/pilot attempts; resource accounting documents allowance separately."
        ),
    }

    # All scientific validation has passed; commit the three derived outputs.
    _atomic_write_text(tables / "campaign.csv", _csv_text(rows))
    _atomic_write_text(tables / "repetitions.csv", _csv_text(repeats))
    _atomic_write_text(tables / "summary.json", json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(summarize(args.root), indent=2))
