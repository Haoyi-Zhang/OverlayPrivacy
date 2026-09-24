# Final Internal Audit

## Scope

This record describes the final internal checks performed on the mathematical
argument, executable artifact, bibliography provenance, and publication packet.
It is evidence of same-executor checking, not independent peer review, formal
proof-assistant verification, or a guarantee that an external system conforms to
the finite queue model.

## Corrections made during the final audit

- The manuscript now uses the supplied `IEEEtran.cls` with the valid
  `letterpaper,journal` option pair. The matched template's literal
  `lettersize` token is not recognized by the supplied class; `letterpaper`
  preserves its intended page size without an unused-option warning.
- The bibliography now uses the supplied, unmodified `IEEEtranS.bst`. The
  previously added `IEEEtran.bst` was removed.
- Bibliographic corrections include David L. Chaum's name, the final PriFi
  record, the Dissent in Numbers page range, Jean-Pierre Smith as QCSD's first
  author, the TCS journal record for van Breugel--Worrell, the author list for
  Vlasman et al., and the peer-reviewed 2025 ISIT record for Makur--Singh.
- Canonical identifiers were corrected for the Mittal CCS paper and the Luo
  TDSC paper. Conference/journal or event/publication-year distinctions for
  Tarzan, Hintz, Hopper, PriFi, and the Alvim ICALP chapter are recorded instead
  of silently merging versions.
- The standalone checker now enforces exact model/configuration/certificate
  schemas, canonical reduced rational strings, and explicit list/entry shapes.
  Unknown fields, duplicate keys, decimals, unreduced fractions, signed zero,
  leading zeros, whitespace variants, and malformed rows are rejected rather
  than silently normalized or ignored.
- A 2026 freshness scan replaced two weaker bibliography entries with the current
  ACM Computing Surveys website-fingerprinting survey and the CSL behavioural-
  distance lower-bound-witness paper. The survey and CSL records remain
  `metadata_only`; two relevant 2026 preprints are recorded only as boundary
  evidence, not promoted to peer-reviewed support.

## Bibliography evidence

`reference_audit.csv` has one row for each of the manuscript's 69 references and
one unique canonical DOI or official publication page per row. The retained
calibration claim is exactly 22 full-text papers: 12 TDSC papers, five influential
field papers, and five adjacent-venue or theory papers. The other 47 records are
explicitly marked `metadata_only`; no full-text reading claim is made for them.
The current-source decision trail is retained in
`results/verification/literature-freshness-2026-09-19.md`.

`tests/test_reference_audit.py` checks the inventory, canonical identifiers,
calibration counts, material corrections, and—when the test is run inside the
full project—exact agreement with `paper/references.bib` and the citation keys in
`paper/main.tex`. It is not a live resolver, does not test the scholarly validity
of a cited conclusion, and cannot guarantee that a publisher's own metadata is
error-free.

## Executable checks

The final validation command set is:

```sh
python3 -m compileall -q src tests
python3 tests/test_certificates.py
python3 tests/test_calibrations.py
python3 tests/test_oracle_bruteforce.py
python3 tests/test_reference_audit.py
python3 src/checker.py inputs/Q014.json results/certificates/Q014-ordered-chain.json
python3 src/summarize.py
```

The certificate suite exercises 15 test methods, 854 exhaustive three-label
summary matrices, 140 fixed-seed summaries, 280 fixed-seed finite channels,
32 basic packet/schema mutations, five ordered-specific mutations, and semantic negative controls. The analytic suite checks 600
one-slot instances, 108 continuity instances, and all 70 eligible retained
rate-bound cases.

The additional brute-force oracle test directly simulates exact secret-to-history
channels for every enumerated deterministic public-history policy without reusing
the scalar dynamic-program recursion. It agrees on 192 exhaustive two-slot
model cases and 16 deeper cases, covering 4,832 policy tables in aggregate. Only
scalar optima and aggregate counts are retained; no optimizing scheduler is
stored or exposed.

The complete campaign is reproducible from an empty output directory. The
final retained comparison covers 74 input files, 144 certificate encodings, and
174 main or repetition records, all of whose deterministic scientific payloads
match. Only an explicit allowlist of CPU-time and RSS fields is excluded. That
run recorded 194.044708 process CPU seconds and 158,676 KiB peak RSS. One
Q018 parent-timing record was intentionally refreshed after a parent timeout; its
deterministic scientific payload was unchanged. This same-environment clean
reproduction is useful fault-detection evidence, not an independent implementation.

## Mathematical and empirical boundary

The general guarantees remain handwritten proofs. Finite tests can refute an
implementation or modeling mistake on the exercised cases but cannot establish a
general theorem. The exact tiny-model recursion is capped and does not emit an
operational linking policy. The 73-model campaign consists of constructed finite
models; it is not a sample of deployed anonymous networks, and timings are not
portable performance claims.

The ordered result is lossless only relative to the dense canonical certificate
family under a common order of arrival rates and initial queues, the declared
shared-coin grand coupling, exact canonical backward values, and the specified
finite observation/scheduler semantics. It does not state that the canonical
bound equals exact leakage for every model.

## Publication-packet boundary

The compiled main paper is required to remain exactly 12 letter-size,
double-column pages including references, with a separate supplement. Both PDFs
must be rebuilt from the delivered sources and visually inspected after any
change. The packet is an internal draft. Before external use, the named authors
must recheck current venue rules, every material theorem and citation, authorship,
AI-use disclosure, originality, and the eventual repository link. No acceptance,
submission, public upload, or independent review is represented here.
