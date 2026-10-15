# Worst-case linkability certificates

An exact-rational artifact for *Worst-Case Linkability Certificates for Finite Rate-Limited Overlays*. It studies constructed finite reservation-charged queues. The ordered theorem preserves the dense canonical certificate bound, not exact disclosure for every queue or conformance of a deployed network. No captured traffic, personal data, live service, operational linkage policy, solver, GPU, external compute, model API, or third-party implementation is needed.

## Requirements and read-only smoke check

Use Python 3.10+ and the standard library; there is no package installation. Full campaigns/tests require a Unix-like platform with the `resource` module. The standalone checker does not import that campaign machinery and reads its two input files without writing results:

```sh
python3 -B src/checker.py inputs/Q014.json results/certificates/Q014-ordered-chain.json
python3 -B -O src/checker.py inputs/Q014.json results/certificates/Q014-ordered-chain.json
```

Both report `valid: true` and exact bound `1028/625`; invalid certificates exit 2. The checker independently reconstructs queue semantics and exact Bellman/tree obligations without importing model, producer, or oracle code. It rejects duplicate keys, unknown fields, noncanonical rationals, oversized input, and excess rational bit width. These interface checks do not establish real-network conformance. Details are in `TRUST-BOUNDARY.md`.

## Tests and retained-data summaries

Run in a writable disposable checkout when preserving every retained report:

```sh
python3 -B tests/run_all.py
python3 -B tests/run_all.py --optimized
python3 -B src/summarize.py
```

The test runner executes every `test_*.py` script and stops at the first failure. Scientific acceptance checks remain active with `-O`. Tests refresh reports including `results/tests.json`, `results/calibrations.json`, `results/oracle-bruteforce.json`, and `results/reference-audit.json`; they are not read-only inspection commands. `src/summarize.py` validates all retained main/repetition records and rewrites three files under `results/tables/` only after success; it first removes the old derived success files so failure cannot leave a stale pass.

The retained certificate suite covers 854 exhaustive pair-summary matrices, 140 fixed-seed summaries, 280 finite channels, packet/schema mutations, and ordered controls. Calibrations cover 600 one-slot cases, 108 whole-row continuity cases, and 70 eligible rate-bound cases. A direct policy-table enumeration agrees with the scalar dynamic program on 192 two-slot and 16 deeper models (4,832 policy tables); both deliberately share `model.kernel`, not an independent semantics. Only scalar values/counts are retained, not optimizing policies. Fail-closed regressions exercise wrong scalars, rate violations, corrupted records, and test-runner failure propagation in both modes.

Six token-action regressions compare a test-local analytic recursion and check token/refill arithmetic; endpoint regressions cover zero horizon and rational widths. These do not add campaign models or establish a measured speedup. Synthesis reuses legal actions/token successors within one call, lazily at zero horizon; no cross-call cache is used. Historical native reports with 48 methods per mode remain their original records, not a rerun of later additions.

## Full isolated reproduction

Run from the artifact root. Create a fresh output directory outside it:

```sh
set -eu
work=$(mktemp -d "${TMPDIR:-/tmp}/linkability-reproduction.XXXXXX")
python3 -B src/campaign.py --out "$work" --start 0 --stop 73
python3 -B src/campaign.py --out "$work" --repeats
python3 -B src/summarize.py --root "$work"
python3 -B tests/compare_reproduction.py --actual "$work"
```

This regenerates 74 input files including selection metadata, 144 certificate encodings, and 174 main/repetition records. The comparison excludes only the explicit timing/RSS allowlist and writes `$work/results/reproduction.json`; inputs and certificate encodings also require exact bytes. It is same-artifact computational reproduction, not independent human validation.

For short windows, split main work into `[0,5)`, `[5,10)`, …, `[70,73)` with `--start/--stop`. Repetitions can be split into `[44,45)`, `[53,54)`, and `[62,63)`. These intervals cover the same frozen selection, not subsampling. Existing campaign records are reused unless `--overwrite` is explicitly requested. Results are committed atomically after checks; a failed child is not a pass. Do not run several drivers against the same output directory.

Workers run serially with 40 CPU seconds, a 44-second parent wall timeout, and 3500 MiB address-space cap per child. The configured campaign envelope is four CPUs/4 GiB/no swap, not four concurrent workers. The scientific workflow on Ubuntu 24.04 runs both test modes, the checker, and clean regeneration/comparison within a 900-second scientific-step budget, retaining raw output on failure or success. Material-integrity CI checks files/syntax, not scientific correctness.

## Inputs, results, and data consumers

`inputs/selection.json` freezes 73 models: 27 Q, 36 S, and 10 A cases. `results/certificates/` holds 144 encodings; `results/campaign/` holds 144 main records and 30 timing repetitions. `results/tables/` contains derived CSV/scalar summaries. `results/verification/` retains clean-reproduction, numeric-field, coverage, and provenance records.

`src/model.py` expands the finite semantics; `src/producer.py` synthesizes rational couplings, potentials, and trees. `src/oracle.py` computes bounded tiny-model scalar public-history capacity. `proofs/guarantees.md` contains the written arguments. Exact arithmetic removes rounding tolerance, not specification/implementation risk or the need for the general proof.

To refresh auxiliary reports from retained observations, use a disposable checkout:

```sh
python3 -B src/reviewer_metrics.py
python3 -B src/model_coverage.py
python3 -B src/numeric_complexity.py
```

The metrics extractor writes tightness JSON/CSV under `results/verification/` and `paper-generated/reviewer-metrics.tex`. Coverage/numeric extractors rewrite their corresponding verification reports. None reruns campaign timings. `REPRODUCIBILITY.md` gives the detailed workflow, including the separate full-project paper build.

## Results and assumptions

All 71 supplied-index ordered models have identical adjacent/dense canonical bounds as reduced fractions. The checker does not search for a relabeling: A004/A005 remain dense-only in the frozen convention, although permutation `(0,2,1)` jointly sorts either, and relabeled adjacent/dense bounds both equal `2`. Forty tiny models have exact full-history oracles; ten canonical bounds are exact. Their median absolute gap is 0.0792, maximum gap 0.7872 (Q010), and maximum bound/exact ratio about 1.397.

At `m=16, B=4, H=16`, dense/ordered encodings contain 102,000/12,750 potentials and 144,000/18,000 Bellman obligations: 87.5% fewer while retaining the same bound. Encoding sizes are 4,279,838/542,618 bytes. Five historical Linux x86-64/CPython 3.13.5 repetitions have median generation-plus-check CPU times of 2.824/0.383 seconds; the environment record is dated 2026-09-20. These are host-specific observations, not later-check timings or a deployment speed guarantee.

Potential values have at most 82 numerator/denominator bits. Aggregates can be wider: S030's capacity numerator is 83 bits and S033/S036 best-star numerators are 84; `results/verification/numeric-complexity.json` records the field distinction.

The envelope is sharp over arbitrary channels satisfying pairwise TV upper bounds; its witness need not be a queue channel or make every constraint tight. Tiny oracle, exact-pair summary, and canonical certificate are distinct layers. Binding premises include finite horizon, the observation alphabet, action before fresh randomness, common public-history scheduling, iid arrivals, and reservation-charged tokens. Ordered equivalence also needs a common rate/initial-queue order, the grand coupling, and exact canonical backward values. Generic `tree` scope claims no equivalence for omitted pairs.

The retained clean comparison matches all 74/144/174 files and records 122.390209 process CPU seconds/158,740 KiB peak RSS. `results/measurements/current-linux/` separately retains an Ubuntu run with 48 methods per mode and exact regeneration, 36.032003 process CPU seconds/80,664 KiB peak RSS. Historical plots are not relabelled with newer environments.

## Sources and licensing

`claim_evidence_ledger.csv` maps claims to proofs/results; `external_resources.csv` retains source/workflow provenance. `reference_audit.csv` has 69 canonical records, explicitly separating 22 recorded full-text calibration papers (12 same-venue, five influential, five adjacent/theory) from 47 metadata-only entries. A structural audit is not a live resolver or certification of every claim-bearing source body. Reading and version boundaries remain in `LITERATURE-METHOD.md` and retained source records; no scholarly PDFs are redistributed.

MIT (`LICENSE`, `licenses/README.md`) covers original code, documentation, proofs, and constructed data, not cited papers, IEEE template assets, or publisher material. The source repository is [OverlayPrivacy-code](https://github.com/Haoyi-Zhang/OverlayPrivacy-code).
