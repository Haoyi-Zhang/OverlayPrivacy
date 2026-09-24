# Reproducibility guide

## Scope

The reproducibility target is equality of deterministic scientific payloads:
model inputs, exact rational certificate fields, Bellman obligations, trees,
exact-oracle values, and summary statistics. CPU time, wall-clock time, and
resident memory are recorded but excluded from byte-for-byte equality.

## Minimal verification

```sh
python3 -m compileall -q src tests
for t in tests/test_*.py; do python3 "$t"; done
for t in tests/test_*.py; do python3 -O "$t"; done
python3 src/checker.py inputs/Q014.json \
  results/certificates/Q014-ordered-chain.json
python3 src/reviewer_metrics.py
python3 src/model_coverage.py
python3 src/numeric_complexity.py
```

The optimized-mode pass is intentional: native Python `assert` statements are
removed under `-O`, so scientific validation uses explicit fail-closed checks.

## Full campaign

```sh
rm -rf /tmp/linkability-reproduction
python3 src/campaign.py --out /tmp/linkability-reproduction --start 0 --stop 73
python3 src/campaign.py --out /tmp/linkability-reproduction --repeats
python3 src/summarize.py --root /tmp/linkability-reproduction
python3 tests/compare_reproduction.py --actual /tmp/linkability-reproduction
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
a real deployment to the finite model is a separate obligation.
