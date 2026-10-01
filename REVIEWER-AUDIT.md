# Reviewer-facing audit

This file records the strongest foreseeable objections that can be tested
inside the delivered finite project. It is an evidence map, not a claim that
acceptance or external peer review can be guaranteed.

## Claim boundary

The paper claims a complete-history certificate in a stated finite queue model,
a sharp envelope conditional on pairwise TV bounds, and an adjacent encoding
that preserves the same canonical tree value under explicit ordered
hypotheses. It does **not** claim that TV/coupling/MSTs are individually new,
that every anonymity deployment matches the abstraction, that every certificate
is exact leakage, or that triangle inequality alone proves the ordered result.

## High-risk objections and resolutions

1. **“The ordered theorem is only an empirical pattern.”** The proof is split
   into the monotone grand-coupling/threshold-component lemma and the MST cut
   argument. Exhaustive and constructed-model checks are falsification support,
   not the proof.
2. **“Triangle inequality cannot establish the advertised equality.”** Agreed;
   it supplies only a path upper bound. The paper now states explicitly that
   the threshold-component property of the canonical weights is essential.
3. **“The exact-oracle cross-check may share the same bug.”** The direct
   deterministic-policy enumerator follows a different algorithmic path, but it
   deliberately shares `model.kernel` with the production dynamic program. Its
   comparison entry may call the scalar oracle; the enumeration functions may
   not reuse the tested recursion, memo table, or certificate/tree code.
   Closed-form one-slot cases form a third bounded path. Declared shared
   dependencies, exact coverage, and fresh scientific-payload comparison are in
   `results/verification/semantic-triangulation.json`; no fingerprint is used as
   a substitute for validation.
4. **“The certificate may be too loose to be useful.”** Per-model gaps, ratios,
   quantiles, exact hits, and the worst case are generated from frozen records
   by `src/reviewer_metrics.py`; see
   `results/verification/reviewer-utility-tightness.{json,csv}`.
5. **“Python optimization silently removes validation.”** Native `assert`
   statements were removed from the calibration, worker, and summary acceptance
   paths and replaced by explicit fail-closed checks. In ordinary and optimized
   modes, `tests/test_fail_closed_validation.py` injects a wrong exact scalar, a
   copied rate-bound violation, and a corrupt campaign record; each must exit
   nonzero without a success report or committed scientific output. It also
   verifies that the documented test runner propagates and stops at failure.
6. **“References were padded or only superficially checked.”** Every cited key
   maps to the provenance ledger. Full-text calibration and metadata-only
   verification remain separate. The live metadata report is
   `results/verification/bibliography-live-check.json`.
7. **“The results depend on nondeterministic iteration order.”** Final
   verification runs under multiple `PYTHONHASHSEED` values and compares
   deterministic payloads; timing and RSS fields are explicitly excluded.
8. **“The artifact demonstrates a real deanonymization attack.”** It does not.
   Inputs are constructed, no live traffic is used, and operational policy
   tables are not released as a session-linking procedure.
9. **“The two dense-only controls show that no common secret order exists.”**
   They do not. Frozen A004 and A005 are unsorted only in their supplied index;
   permutation `(0,2,1)` jointly sorts each. Regenerated adjacent and dense
   bounds both equal 2. The 73/71 campaign count intentionally retains the
   supplied-index convention, and the checker does not auto-relabel.
10. **“The reported 82-bit maximum contradicts wider aggregate fractions.”**
    The 82-bit figure is limited to certificate potential values. Over the
    declared aggregate field set, S030's capacity numerator is 83 bits and the
    S033/S036 best-star numerators are 84 bits; the exact field inventory is in
    `results/verification/numeric-complexity.json`.

## Remaining limits that cannot honestly be eliminated internally

- No proof assistant has mechanically checked the general theorem.
- No external team has independently replicated the work.
- No real deployment has been shown to satisfy the finite model assumptions.
- Editorial suitability, novelty judgment, and acceptance remain decisions of
  independent reviewers and editors.

These are disclosure boundaries, not unfinished code tasks.
