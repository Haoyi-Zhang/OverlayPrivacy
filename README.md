# Worst-case linkability certificates

This standalone exact-rational artifact supports the internal research manuscript
*Worst-Case Linkability Certificates for Finite Rate-Limited Overlays*. It studies
an owned finite reservation-charged queue abstraction. It is not a deployed
privacy system, a traffic-analysis tool, or a source of operational linkage
policies. The ordered theorem preserves the dense **canonical certificate bound**;
it does not compute exact disclosure for every queue or prove conformance of a
real network implementation.

No captured traffic, personal data, live service, GPU, external compute, model
API, solver, or third-party implementation is required. Python's standard library
is sufficient.

## Repository map and trust boundary

- `proofs/guarantees.md` contains the complete handwritten mathematical arguments.
- `src/model.py` expands the declared queue semantics.
- `src/producer.py` synthesizes exact rational couplings, potentials, and trees.
- `src/checker.py` reconstructs the model and checks exact obligations without
  importing the producer, campaign driver, or oracle.
- `src/oracle.py` computes exact scalar public-history capacity for bounded tiny
  models and emits no policy, estimator, or linking procedure.
- `inputs/selection.json` freezes the 73-model campaign.
- `results/certificates/` contains 144 checked certificate encodings.
- `results/campaign/` contains 144 main records and 30 timing repetitions.
- `results/tables/` contains summaries derived from retained records.
- `results/verification/` records the completed clean reproduction.
- `claim_evidence_ledger.csv` maps every material manuscript claim to proof,
  executable evidence, raw results, display location, maturity, and recheck.
- `external_resources.csv` records scholarly and workflow provenance; no cited
  paper or publisher asset is redistributed or needed by the code.
- `reference_audit.csv` records the 69 cited works, one unique canonical DOI or
  official publication page per work, and an explicit split between 22 full-text
  calibration papers and 47 metadata-only records.

Implementation separation can expose disagreements between code paths, but it is
not proof-assistant mechanization, a verified compiler, or independent human
review. Exact arithmetic removes numerical tolerances, not every possible semantic
or implementation error. The checker accepts only exact declared schemas and
canonical reduced rational strings, rejects duplicate keys and unknown fields,
and bounds input size and rational bit width. These parser checks harden the
certificate interface but do not establish that another system conforms to the
finite model.

## Requirements and resource limits

Use Python 3 on a Unix-like platform providing the standard-library `resource`
module. No dependency installation is required. Scientific acceptance paths use
explicit fail-closed checks rather than native Python `assert`, and the retained
suite is required to pass both ordinary execution and `python -O`.

Scientific workers run one at a time. Each child has a 40 CPU-second limit, a
44-second parent wall timeout, and a 3500 MiB address-space cap. The surrounding
campaign ceiling is four CPUs and 4 GiB RAM with no swap, but the commands do not
request four concurrent workers. The largest retained main-run high-water mark is
158,676 KiB (about 155 MiB).

## Validate retained evidence

Run these commands from the repository root:

```sh
python3 -m compileall -q src tests
python3 tests/run_all.py
python3 tests/run_all.py --optimized
python3 src/checker.py inputs/Q014.json results/certificates/Q014-ordered-chain.json
python3 -O src/checker.py inputs/Q014.json results/certificates/Q014-ordered-chain.json
python3 src/summarize.py
```

Expected scientific outcomes:

- `test_certificates.py`: 15 methods; 854 exhaustive pair-summary matrices,
  140 fixed-seed summaries, 280 finite channels, 32 basic packet/schema
  mutations, five ordered-specific mutations, and semantic controls all pass.
- `test_calibrations.py`: 600 one-slot cases, 108 whole-row continuity cases,
  and all 70 eligible retained rate-bound cases pass.
- `test_oracle_bruteforce.py`: an algorithmically separate direct-channel simulator agrees
  with the scalar dynamic program on 192 exhaustive two-slot model cases and 16
  deeper cases, covering 4,832 deterministic policy tables in aggregate. It
  retains scalar optima and counts, never an optimizing policy. Both paths share
  the declared `model.kernel`; the reference enumeration does not reuse the
  production recursion, memo table, or certificate/tree algorithms.
- `test_fail_closed_validation.py`: under ordinary and optimized interpreters,
  a wrong exact scalar, a copied rate-bound violation, and a corrupt campaign
  record all exit nonzero and leave no success report or committed scientific
  output; the test runner also propagates the first nonzero status and does not
  continue to later tests.
- `test_reference_audit.py`: 69 unique canonical records pass structural checks;
  the full-text calibration split is exactly 12 same-venue, five influential,
  and five adjacent/theory papers, with 47 remaining records marked metadata-only.
- the Q014 checker invocation reports `valid: true` and exact bound `1028/625`;
  invalid certificates exit with status 2;
- the summary verifies 73 models, 144 main certificates, 71 ordered/dense exact
  equalities, 40 full-secret oracles, 10 exact canonical cases, and all retained
  structural counts.

The test commands refresh `results/tests.json`, `results/calibrations.json`,
`results/oracle-bruteforce.json`, and `results/reference-audit.json`. Their wall
time, CPU time, and resident-memory fields may vary; exact scientific counts,
rational values, and recomputed histograms must not. The semantic metadata makes
no snapshot-fingerprint promise: the retained oracle record is accepted only
when required fields, zero failures/errors, exact coverage counts, and a fresh
scientific-payload recomputation agree. The reference test validates retained
provenance and manuscript consistency when `paper/` is present; it is not a
live-Web resolver and does not claim that metadata-only references were read in
full.

## Reproduce all scientific results

Use an empty writable directory outside the repository:

```sh
set -eu
python3 src/campaign.py --out /tmp/linkability-reproduction --start 0 --stop 73
python3 src/campaign.py --out /tmp/linkability-reproduction --repeats
python3 src/summarize.py --root /tmp/linkability-reproduction
python3 tests/compare_reproduction.py --actual /tmp/linkability-reproduction
```

For short execution windows, split the first command into deterministic intervals,
for example `[0,5)`, `[5,10)`, through `[70,73)`, using `--start` and `--stop`.
Repetition work can be split into `[44,45)`, `[53,54)`, and `[62,63)` for the
three measured scaling cases. This is resumable execution of the same frozen
selection, not subsampling. Results are written atomically; a failed or timed-out
child is not counted as success. Use `--overwrite` only to replace a chosen record
intentionally.

The completed clean run regenerated and compared:

- 74 input files, including selection metadata;
- 144 full certificate encodings;
- 174 scientific campaign and repetition records.

`tests/compare_reproduction.py` compares deterministic scientific payloads and
encodings while excluding only an explicit allowlist of CPU-time and RSS fields.
It writes `results/reproduction.json` under the fresh output root. The retained
verification report is `results/verification/clean-reproduction.json`. The final
retained clean run matched all 74 input, 144 certificate, and 174 result records,
recording 122.390209 process CPU seconds and 158,740 KiB peak RSS. Same-executor
clean reproduction is reproducibility evidence, not independent validation.

## Bibliography provenance boundary

The manuscript bibliography is relevance-first rather than quota-filled. Each of
its 69 records has a unique canonical DOI or official publication page in
`reference_audit.csv`. Twenty-two papers were used for the recorded full-text
calibration matrix (12 TDSC, five influential field papers, and five adjacent or
theory papers). The other 47 records were checked at the publication-metadata
level and are explicitly labeled `metadata_only`; neither this README nor the
audit represents them as full-text reads. Corrections made during the final audit
include the Mittal CCS DOI, the Luo TDSC DOI, the journal form of van Breugel--
Worrell, the final PriFi record, and the peer-reviewed ISIT form of Makur--Singh.
A 2026 freshness scan also adds the current ACM website-fingerprinting survey and
the CSL lower-bound-witness paper while recording two related preprints only as
novelty-boundary evidence in `results/verification/literature-freshness-2026-09-19.md`.

Canonical identifiers make the audit inspectable, but metadata can still be
wrong at a publisher or catalog. Human authors should re-open the cited records
before external submission, especially where conference and journal versions
coexist.

## Main results and interpretation

All 71 models whose rates and initial queues are jointly nondecreasing in their
supplied label index have identical adjacent and dense canonical bounds as reduced
rational numbers. The checker does not search for a relabeling. Frozen A004 and
A005 are dense-only under that convention, although permutation `(0,2,1)` jointly
sorts each; regenerated relabeled adjacent and dense bounds both equal `2`.
Forty tiny models have exact full-history
oracles; every exact result is below both certificate layers and ten canonical
bounds are exact. Across these 40 models, the median absolute canonical gap is
0.0792, the maximum is 0.7872 (Q010), and the maximum bound-to-exact ratio is
approximately 1.397.

At the largest tested grid (`m=16`, `B=4`, `H=16`), dense certificates retain
102,000 potentials and check 144,000 Bellman obligations. Ordered certificates
retain 12,750 potentials and check 18,000 obligations, an exact 87.5% structural
reduction, while returning the same fraction. Their retained encodings occupy
4,279,838 and 542,618 bytes. Five fresh-process repetitions give dense/ordered
median generation-plus-check CPU times of 2.824/0.383 seconds for this case.
Timing is environment-specific; the pair-count reduction and equality of the
canonical bounds are the theorem-backed claims.

The largest numerator or denominator among certificate **potential values** is
82 bits. This does not bound every aggregate: S030's capacity-bound numerator is
83 bits, and the best-star numerators for S033 and S036 are 84 bits. The explicit
field inventory is `results/verification/numeric-complexity.json`.

The summary-envelope theorem is sharp over arbitrary channels constrained only by
pairwise TV **upper bounds**. It is not a claim that the witness is a queue channel,
that every constraint is tight, or that the result optimizes a fixed-prior decision
problem. The tiny oracle, exact-pair tree, and canonical certificate are separate
layers and can differ.

Observation mode, action-before-fresh-randomness timing, common public-history
scheduling, iid arrivals, reservation-charged tokens, and finite horizon are
binding. Ordered equivalence additionally requires one common order of rates and
initial queues, the explicit grand coupling, and exact canonical backward values.
The generic `tree` scope makes no equivalence claim about omitted pairs.

## Licensing, provenance, and AI disclosure

The MIT license applies to this repository's original code, documentation, proofs,
and constructed inputs. It does not apply to cited papers, IEEE template assets,
or publisher material. External resources are cited or recorded by stable URL and
are not incorporated into the runtime artifact.

ChatGPT (GPT-5.6 Sol Pro) was used substantively in the research formulation,
literature synthesis, proofs, implementation, constructed experiments, figures,
supplement, and writing; its role was not limited to copy editing. No independent
human validation is asserted. The named human authors must verify the science,
authorship, disclosures, originality, and applicable publication policies before
any external use. The source repository is [available here](https://github.com/Haoyi-Zhang/worst-case-linkability-certificates-for-finite-rate-limited-overlays-artifact).
