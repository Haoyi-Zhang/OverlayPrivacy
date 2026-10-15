# Reproducibility guide

## Scope

The reproducibility target is equality of deterministic scientific payloads:
model inputs, exact rational certificate fields, Bellman obligations, trees,
exact-oracle values, and summary statistics. CPU time, wall-clock time, and
resident memory are recorded but excluded from byte-for-byte equality.

## Minimal verification

```sh
python3 -B src/checker.py inputs/Q014.json \
  results/certificates/Q014-ordered-chain.json
python3 -B -O src/checker.py inputs/Q014.json \
  results/certificates/Q014-ordered-chain.json
```

These checker calls only read retained inputs. Full tests and derived-data tools
write reports; use a writable disposable checkout when preserving reference files:

```sh
python3 -B tests/run_all.py
python3 -B tests/run_all.py --optimized
python3 -B src/reviewer_metrics.py
python3 -B src/model_coverage.py
python3 -B src/numeric_complexity.py
```

Tests refresh JSON reports under `results/`; the three extractors rewrite
their reports under `results/verification/`, and the metrics extractor also
writes `paper-generated/reviewer-metrics.tex`. They do not rerun campaign timing.

The optimized-mode pass is intentional: native Python `assert` statements are
removed under `-O`, so the calibration, worker, and summary acceptance paths use
explicit fail-closed checks. `tests/test_fail_closed_validation.py` verifies in
both modes that a wrong exact scalar, a copied rate-bound violation, and a corrupt
campaign record exit nonzero and do not leave a success report or committed
scientific output. `tests/run_all.py` returns the first failing status and stops;
it does not implement a best-effort shell loop that could hide a failure.

The tiny-oracle cross-check is algorithmically distinct, not source-independent:
both solvers share the declared `model.kernel`. The comparison entry calls the
production scalar oracle, while static checks prevent the direct policy-table
enumeration functions from reusing that recursion, its memo table, or any
certificate/tree algorithm. The retained result is checked by required fields,
zero failures/errors, exact coverage counts, and a fresh scientific-payload
recomputation. No source/result checksum or snapshot fingerprint is promised.

## Full campaign

```sh
set -eu
work=$(mktemp -d "${TMPDIR:-/tmp}/linkability-reproduction.XXXXXX")
python3 -B src/campaign.py --out "$work" --start 0 --stop 73
python3 -B src/campaign.py --out "$work" --repeats
python3 -B src/summarize.py --root "$work"
python3 -B tests/compare_reproduction.py --actual "$work"
```

Run in a fresh extraction of the delivered repository. Set `PYTHONHASHSEED` to
any fixed integer when investigating iteration-order sensitivity; the supplied
hash-seed test compares two distinct values.

## Paper build

From the sibling `paper/` directory in the complete project:

```sh
make clean
make all
```

The final gate requires a 12-page US-Letter main PDF, resolved references,
embedded fonts, and no overfull boxes. The supplement is a separate PDF.

## Trust and limitations

A successful rerun is same-artifact computational reproduction, not independent
scientific replication. The general theorem remains a human proof, and mapping
a real deployment to the finite model is a separate obligation. Ordered-mode
eligibility is evaluated in the supplied label index; the checker does not search
for a relabeling. Environment-dependent CPU, wall-time, and RSS measurements are
kept separate from deterministic scientific payloads.
