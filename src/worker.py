"""One scientific case in a fresh, resource-bounded process.

Scientific obligations use explicit fail-closed checks so optimized Python cannot
remove them. Output files are committed only after every obligation succeeds.
"""
from __future__ import annotations

import argparse
import json
import resource
import time
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path

from checker import check, read
from oracle import capacity
from producer import hierarchy_witness, make, sparsify


class WorkerValidationError(RuntimeError):
    """Raised when a derived scientific obligation is not satisfied."""


def need(condition: bool, message: str) -> None:
    if not condition:
        raise WorkerValidationError(message)


def write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--scope", choices=("all-pairs", "ordered-chain"), required=True)
    parser.add_argument("--repeat", type=int, default=0)
    args = parser.parse_args()

    # One child, no spawned workers. Address-space and CPU caps also bound failure.
    resource.setrlimit(resource.RLIMIT_AS, (3500 * 1024**2, 3500 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (40, 40))
    start = time.process_time()
    wall = time.perf_counter()
    startup_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    model = read(args.root / "inputs" / f"{args.case}.json")
    config = model["config"]
    labels = len(config["arrival_rates"])

    tick = time.process_time()
    certificate = make(model, args.scope)
    generation = time.process_time() - tick
    tick = time.process_time()
    checked = check(model, certificate)
    checking = time.process_time() - tick
    need(checked.get("valid") is True, "checker did not return valid=true")

    encoded = json.dumps(certificate, sort_keys=True, separators=(",", ":")) + "\n"
    record = dict(
        case=args.case,
        scope=args.scope,
        repeat=args.repeat,
        config=config,
        **{key: value for key, value in checked.items() if key != "scope"},
        generation_cpu_seconds=generation,
        checking_cpu_seconds=checking,
        certificate_bytes=len(encoded.encode()),
    )

    if args.scope == "all-pairs" and args.repeat == 0:
        distances = {
            tuple(map(int, key.split(","))): F(value)
            for key, value in certificate["distances"].items()
        }
        record["best_star_bound"] = str(
            1
            + min(
                sum(
                    distances[tuple(sorted((root, other)))]
                    for other in range(labels)
                    if root != other
                )
                for root in range(labels)
            )
        )
        sparse = sparsify(certificate)
        record["tree_only_check"] = check(model, sparse)["valid"]
        need(record["tree_only_check"] is True, "tree-only sparse certificate failed validation")

        if not config["observe_overflow"]:
            horizon = config["horizon"]
            reservations = (
                min(
                    horizon,
                    config["token_capacity"]
                    + (horizon - 1) // config["refill_period"],
                )
                if horizon
                else 0
            )
            record["reservation_limit"] = reservations
            record["uniform_cover_bound"] = str(
                1 + (labels - 1) * (1 - F(config["padding"]) ** reservations)
            )
            need(
                F(record["capacity_bound"]) <= F(record["uniform_cover_bound"]),
                "canonical capacity bound exceeds the uniform-cover bound",
            )

        witness = hierarchy_witness(labels, distances)
        need(all(sum(row) == 1 for row in witness), "summary witness row is not normalized")
        need(
            sum(map(max, zip(*witness))) == F(record["capacity_bound"]),
            "summary witness does not attain the declared capacity bound",
        )
        need(
            all(
                sum(abs(x - y) for x, y in zip(witness[i], witness[j])) / 2
                <= distances[i, j]
                for i, j in combinations(range(labels), 2)
            ),
            "summary witness violates a pairwise total-variation constraint",
        )
        record["summary_witness_columns"] = len(witness[0])
        record["summary_witness_verified"] = True

        rates = list(map(F, config["arrival_rates"]))
        # This is deliberately the supplied label-index convention. The worker
        # and checker do not search for a relabeling of secrets.
        given_index_ordered = (
            rates == sorted(rates)
            and config["initial_queues"] == sorted(config["initial_queues"])
        )
        record["joint_order"] = given_index_ordered
        record["chain_bound"] = str(
            1 + sum(distances[i, i + 1] for i in range(labels - 1))
        )
        if given_index_ordered:
            need(
                all(
                    distances[k, ell] <= distances[i, j]
                    for i, j in combinations(range(labels), 2)
                    for k in range(i, j)
                    for ell in range(k + 1, j + 1)
                ),
                "ordered dense matrix violates nested interval dominance",
            )
            need(
                record["chain_bound"] == record["capacity_bound"],
                "ordered adjacent chain does not equal the dense canonical bound",
            )
            record["interval_dominance_verified"] = True

        if config["horizon"] <= 4:
            tick = time.process_time()
            exact, details = capacity(model)
            record.update(exact_capacity=str(exact), **details)
            need(
                exact <= F(record["capacity_bound"]),
                "exact full-secret capacity exceeds the canonical certificate",
            )
            pair_distances = {}
            pair_nodes = 0
            for i, j in combinations(range(labels), 2):
                value, info = capacity(model, [i, j])
                pair_distances[i, j] = value - 1
                pair_nodes += info["oracle_nodes"]
                need(
                    value - 1 <= distances[i, j],
                    f"exact pair ({i},{j}) exceeds its canonical pair distance",
                )
            # Separate scalar pair-oracle summary: each pair may use a different
            # worst public scheduler, so it is a valid conservative uniform bound.
            from producer import minimum_tree

            tree = minimum_tree(labels, pair_distances)
            record["exact_pair_summary_bound"] = str(
                1 + sum(pair_distances[tuple(edge)] for edge in tree)
            )
            need(
                exact
                <= F(record["exact_pair_summary_bound"])
                <= F(record["capacity_bound"]),
                "exact, exact-pair, and canonical layers are not ordered",
            )
            record["pair_oracle_nodes"] = pair_nodes
            record["oracle_cpu_seconds"] = time.process_time() - tick

    record["worker_cpu_seconds"] = time.process_time() - start
    record["worker_wall_seconds"] = time.perf_counter() - wall
    record["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    record["startup_peak_rss_kib"] = startup_peak

    # Commit outputs only after all scientific validation above succeeds.
    if args.repeat == 0:
        write_text(
            args.root / "results" / "certificates" / f"{args.case}-{args.scope}.json",
            encoded,
        )
    suffix = "" if args.repeat == 0 else f"-repeat{args.repeat}"
    write(
        args.root / "results" / "campaign" / f"{args.case}-{args.scope}{suffix}.json",
        record,
    )


if __name__ == "__main__":
    main()
