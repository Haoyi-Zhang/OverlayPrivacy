# Internal validation audit

## Scope and claim boundary

This audit covers the delivered finite, exact-rational theory artifact for
*Worst-Case Linkability Certificates for Finite Rate-Limited Overlays*. It
records same-executor checks of code, proofs, retained synthetic inputs,
scientific result files, bibliography provenance, and the compiled manuscript.
It is not independent peer review, proof-assistant verification, deployment
validation, or an acceptance prediction.

The ordered result preserves the dense **canonical certificate bound** under the
stated common-order, shared-coin, finite-history, and exact-value hypotheses. It
does not claim exact leakage for every queue model or conformance of a deployed
anonymous network.

## Fail-closed executable acceptance

All scientific acceptance paths in `tests/test_calibrations.py`, `src/worker.py`,
and `src/summarize.py` use explicit checks rather than native Python `assert`.
The documented test runner executes every `test_*.py` file in order and returns
the first nonzero status. Both required modes are exercised:

```sh
python3 -m compileall -q src tests
python3 tests/run_all.py
python3 tests/run_all.py --optimized
python3 src/checker.py inputs/Q014.json \
  results/certificates/Q014-ordered-chain.json
python3 -O src/checker.py inputs/Q014.json \
  results/certificates/Q014-ordered-chain.json
python3 src/summarize.py
```

`tests/test_fail_closed_validation.py` supplies micro-fixtures in ordinary and
optimized modes. A deliberately wrong exact scalar, a copied retained record
that violates the proved rate bound, and a corrupt campaign record must each
exit nonzero. The calibration and summary paths may not leave a successful
report, and the worker may not commit either a certificate or a campaign record.
A separate runner fixture verifies that a failed test stops the loop and that a
later test is not executed.

## Ordered-index convention

The frozen campaign evaluates ordered eligibility in the supplied secret-label
index. The checker does not search for a relabeling. This convention yields 73
dense results and 71 ordered results.

A004 and A005 are not counterexamples to existence of a common order. Their
supplied arrays are unsorted: A004 has queues `(0,1,0)` and A005 has rates
`(0,1,0)`. Permutation `(0,2,1)` jointly sorts each case. The regression suite
regenerates the relabeled models and verifies that the adjacent and dense bounds
both equal `2`. The original frozen inputs and the 73/71 supplied-index count are
retained unchanged.

## Numeric-complexity fields

`results/verification/numeric-complexity.json` inventories only declared
scientific fields. The campaign field historically named
`maximum_rational_bits` is recomputed from that certificate's Bellman potential
values; it is not an all-fields maximum.

- Maximum numerator or denominator width among all 457,555 retained potential
  values: 82 bits.
- S030 `capacity_bound` numerator: 83 bits.
- S033 and S036 `best_star_bound` numerators: 84 bits.
- Across the explicit aggregate field set (`capacity_bound`, `best_star_bound`,
  `chain_bound`, `uniform_cover_bound`, `exact_capacity`, and
  `exact_pair_summary_bound`), the maximum numerator width is 84 bits and the
  maximum denominator width is 82 bits.

The source program checks all 144 campaign `maximum_rational_bits` values against
the matching certificate potentials and rejects field drift.

## Tiny-oracle semantic cross-check

The production scalar dynamic program and direct deterministic-policy enumerator
are algorithmically distinct, but both deliberately share
`src/model.py::kernel`, the written finite semantics, and exact rational
arithmetic. The comparison entry may call `src/oracle.py::capacity` to obtain the
value under test. Static checks prevent the direct enumeration functions from
reusing the oracle's mass-state recursion or memo table and from calling
certificate, tree, checker, campaign, or summary algorithms.

The retained `results/oracle-bruteforce.json` is accepted only when all required
fields are present, `successful` is true, failures and errors are zero, the
coverage counts are exact, each histogram count and weighted sum is internally
consistent, and a fresh recomputation has the same scientific payload. CPU time
and peak RSS are separate environment measurements. Removing stale optional
fingerprints cancels only a snapshot-fingerprint promise; it does not remove the
fresh scientific validation.

The direct comparison covers 192 exhaustive two-slot configurations and 16
deeper configurations, totaling 4,832 deterministic public-history policy
tables. Every scalar optimum agrees with the production dynamic program. Only
scalar optima summaries and counts are retained; no optimizing policy is stored.

## Certificate, calibration, and model checks

The certificate suite retains 15 test methods, 32 basic packet/schema mutations,
five ordered-specific negative checks, 854 exhaustive upper-summary matrices,
140 fixed-seed summary matrices, and 280 fixed-seed finite channels. It also
contains the two explicit relabeling controls above.

The analytic suite checks 600 one-slot instances, 108 whole-row continuity
instances, and all 70 eligible retained rate-bound cases. The input-coverage
report verifies all 73 constructed model files, the 27/36/10 Q/S/A family split,
and 73 distinct canonical model encodings without publishing a checksum
manifest.

## Bibliography evidence

The manuscript contains 69 unique BibTeX records and cites every one. The
provenance ledger has one row per key and distinguishes 22 full-text writing
calibration papers (12 TDSC, five influential field papers, and five adjacent or
theory papers) from 47 metadata-only records. The executable audit checks keys,
identifiers, category counts, recorded material corrections, and agreement with
the manuscript when the complete project is present. It is not a live resolver
and cannot prove that every scholarly interpretation is correct.

## Reproduction and environment boundary

The full campaign regenerates 74 input files including selection metadata, 144
certificate encodings, and 174 principal or repetition records. Deterministic
scientific payloads are compared exactly. CPU time, wall time, startup RSS, and
process RSS are explicitly treated as environment-dependent measurements rather
than correctness fields.

A clean rerun by the same codebase is useful fault-detection evidence, not an
independent implementation or external replication. After the current repairs,
a fresh empty-directory run matched all 74 inputs, 144 certificate encodings,
and 174 result records. The retained report records 122.390209 process CPU
seconds and 158,740 KiB peak RSS; these environment measurements are not
scientific identity fields.

## Publication packet

The main manuscript must remain exactly 12 US-Letter IEEE double-column pages,
including references, with the supplement separate. The supplied class and
bibliography style remain unmodified. All figures retain their existing native
TikZ/PGFPlots design and underlying data; only text or local layout corrections
needed by these repairs are permitted. After any source change, both PDFs must
be rebuilt and every page rendered and inspected for unresolved references,
overfull material, clipping, overlap, and unreadable content.

The packet retains its substantive AI-use disclosure and all limitations. It
contains no fabricated repository URL, external submission claim, independent
review claim, or guarantee of acceptance.
