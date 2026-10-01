#!/usr/bin/env python3
"""Recompute rational bit widths from explicit scientific field sets.

The 82-bit quantity reported for Bellman potentials is deliberately separated
from aggregate result fields such as capacity and best-star bounds.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGGREGATE_FIELDS = (
    "capacity_bound",
    "best_star_bound",
    "chain_bound",
    "uniform_cover_bound",
    "exact_capacity",
    "exact_pair_summary_bound",
)


class ComplexityValidationError(RuntimeError):
    pass


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ComplexityValidationError(message)


def bits(raw: str) -> tuple[int, int, int]:
    value = Fraction(raw)
    numerator = abs(value.numerator).bit_length()
    denominator = value.denominator.bit_length()
    return numerator, denominator, max(numerator, denominator)


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def main(root: Path = ROOT) -> dict:
    root = Path(root).resolve()
    certificate_dir = root / "results" / "certificates"
    campaign_dir = root / "results" / "campaign"

    certificate_files = sorted(certificate_dir.glob("*.json"))
    need(len(certificate_files) == 144, f"expected 144 certificate files, found {len(certificate_files)}")

    potential_observations = []
    per_certificate_maximum = {}
    for path in certificate_files:
        packet = json.loads(path.read_text(encoding="utf-8"))
        potentials = packet.get("potentials")
        need(type(potentials) is dict and potentials, f"{path}: missing potential map")
        local_maximum = 0
        for key, raw in potentials.items():
            numerator, denominator, maximum = bits(raw)
            local_maximum = max(local_maximum, maximum)
            potential_observations.append(
                {
                    "file": str(path.relative_to(root)),
                    "path": f"potentials.{key}",
                    "value": raw,
                    "numerator_bits": numerator,
                    "denominator_bits": denominator,
                    "value_bits": maximum,
                }
            )
        per_certificate_maximum[path.stem] = local_maximum

    main_files = sorted(
        path
        for path in campaign_dir.glob("*.json")
        if "-repeat" not in path.name
    )
    need(len(main_files) == 144, f"expected 144 main campaign records, found {len(main_files)}")

    aggregate_observations = []
    consistency_checked = 0
    for path in main_files:
        record = json.loads(path.read_text(encoding="utf-8"))
        key = path.stem
        need(key in per_certificate_maximum, f"{path}: matching certificate is absent")
        need(
            record.get("maximum_rational_bits") == per_certificate_maximum[key],
            f"{path}: maximum_rational_bits does not match certificate potentials",
        )
        consistency_checked += 1
        for field in AGGREGATE_FIELDS:
            if field not in record:
                continue
            numerator, denominator, maximum = bits(record[field])
            aggregate_observations.append(
                {
                    "case": record["case"],
                    "scope": record["scope"],
                    "file": str(path.relative_to(root)),
                    "field": field,
                    "value": record[field],
                    "numerator_bits": numerator,
                    "denominator_bits": denominator,
                    "value_bits": maximum,
                }
            )

    need(potential_observations, "no potential values found")
    need(aggregate_observations, "no aggregate scientific values found")

    potential_maximum = max(item["value_bits"] for item in potential_observations)
    potential_numerator_maximum = max(item["numerator_bits"] for item in potential_observations)
    potential_denominator_maximum = max(item["denominator_bits"] for item in potential_observations)
    potential_witnesses = [
        item for item in potential_observations if item["value_bits"] == potential_maximum
    ]

    aggregate_numerator_maximum = max(item["numerator_bits"] for item in aggregate_observations)
    aggregate_denominator_maximum = max(item["denominator_bits"] for item in aggregate_observations)

    by_field = {}
    for field in AGGREGATE_FIELDS:
        selected = [item for item in aggregate_observations if item["field"] == field]
        need(selected, f"aggregate field {field} is absent")
        maximum_numerator = max(item["numerator_bits"] for item in selected)
        maximum_denominator = max(item["denominator_bits"] for item in selected)
        by_field[field] = {
            "records": len(selected),
            "maximum_numerator_bits": maximum_numerator,
            "maximum_denominator_bits": maximum_denominator,
            "numerator_witnesses": [
                {
                    key: item[key]
                    for key in ("case", "scope", "file", "value")
                }
                for item in selected
                if item["numerator_bits"] == maximum_numerator
            ],
            "denominator_witnesses": [
                {
                    key: item[key]
                    for key in ("case", "scope", "file", "value")
                }
                for item in selected
                if item["denominator_bits"] == maximum_denominator
            ],
        }

    named_checks = {
        "S030_capacity_bound_numerator_bits": bits(
            json.loads((campaign_dir / "S030-all-pairs.json").read_text())["capacity_bound"]
        )[0],
        "S033_best_star_bound_numerator_bits": bits(
            json.loads((campaign_dir / "S033-all-pairs.json").read_text())["best_star_bound"]
        )[0],
        "S036_best_star_bound_numerator_bits": bits(
            json.loads((campaign_dir / "S036-all-pairs.json").read_text())["best_star_bound"]
        )[0],
    }

    need(potential_maximum == 82, f"expected 82-bit potential maximum, found {potential_maximum}")
    need(named_checks["S030_capacity_bound_numerator_bits"] == 83, "S030 capacity numerator is not 83 bits")
    need(named_checks["S033_best_star_bound_numerator_bits"] == 84, "S033 best-star numerator is not 84 bits")
    need(named_checks["S036_best_star_bound_numerator_bits"] == 84, "S036 best-star numerator is not 84 bits")

    report = {
        "schema_version": 2,
        "potential_values": {
            "field_set": "results/certificates/*.json -> potentials[*]",
            "values": len(potential_observations),
            "maximum_value_bits": potential_maximum,
            "maximum_numerator_bits": potential_numerator_maximum,
            "maximum_denominator_bits": potential_denominator_maximum,
            "maximum_witness_count": len(potential_witnesses),
            "maximum_witnesses_first_ten": potential_witnesses[:10],
        },
        "aggregate_result_fields": {
            "field_set": list(AGGREGATE_FIELDS),
            "values": len(aggregate_observations),
            "maximum_numerator_bits": aggregate_numerator_maximum,
            "maximum_denominator_bits": aggregate_denominator_maximum,
            "maximum_numerator_witnesses": [
                {
                    key: item[key]
                    for key in ("case", "scope", "file", "field", "value")
                }
                for item in aggregate_observations
                if item["numerator_bits"] == aggregate_numerator_maximum
            ],
            "maximum_denominator_witnesses": [
                {
                    key: item[key]
                    for key in ("case", "scope", "file", "field", "value")
                }
                for item in aggregate_observations
                if item["denominator_bits"] == aggregate_denominator_maximum
            ],
            "by_field": by_field,
        },
        "campaign_record_consistency": {
            "records_checked": consistency_checked,
            "maximum_rational_bits_definition": "maximum bit width among that certificate's potential values",
            "all_match": True,
        },
        "named_checks": named_checks,
        "interpretation": [
            "The 82-bit statement applies only to Bellman potential values.",
            "Aggregated result fields can be wider: the maximum numerator is 84 bits and the maximum denominator is 82 bits.",
            "Timing and resident memory are environment measurements and are not part of this exact-arithmetic inventory.",
        ],
    }
    target = root / "results" / "verification" / "numeric-complexity.json"
    _atomic_write_json(target, report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return report


if __name__ == "__main__":
    main()
