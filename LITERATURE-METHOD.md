# Literature-search and citation method

## Purpose

The search supports contribution positioning and detects close prior work. It
cannot prove priority or novelty. Editorial and reviewer judgment remains
necessary.

## Search date and scope

The final freshness pass is dated 2026-09-20. It covers work on low-latency
anonymous communication and traffic analysis, website fingerprinting and
linkability, finite-state or queue-based privacy analysis, coupling and total
variation certificates, maximal/guessing leakage, and tree-based aggregation of
pairwise statistical distances.

## Discovery queries

The retained machine search uses combinations of:

- `anonymous communication traffic analysis queue timing linkability`;
- `website fingerprinting complete history defense leakage`;
- `total variation coupling certificate privacy leakage`;
- `minimum spanning tree pairwise total variation capacity`;
- `ordered adjacent pair certificate monotone coupling`;
- the exact title and author names of every close candidate.

Discovery records are deduplicated by normalized DOI, official publication URL,
and normalized title. Preprints and formal versions are linked rather than
silently counted as separate works.

## Evidence levels

- `full_text_calibration`: the full paper was read for model, threat, theorem,
  evidence, and limitation comparison.
- `metadata_only`: title, authors, venue, year, pages, and DOI/official URL were
  checked, but no substantive claim in the paper relies on an unread result.
- `candidate_screen`: an automated search hit retained for audit; it is not a
  cited source until manually screened and, where relevant, read.

The 12 same-journal, 5 influential, and 5 adjacent/theory calibrations are
separately identified in `reference_audit.csv`. The remaining citations are not
misrepresented as full-text calibrations.

## Inclusion and exclusion

A work is included in the close-comparison set when it shares at least two of
the following: complete-history observations, adaptive scheduling, finite queue
semantics, externally checkable privacy witnesses, worst-case multi-secret
capacity, or lossless ordered pair reduction. Work sharing only a general tool
(e.g., total variation or MSTs) is background rather than a direct predecessor.
Survey and system papers are used for context, not as theorem substitutes.

## Claims discipline

The paper avoids absolute phrases such as “the first method” or “the only
framework.” The positive contribution is stated as a specific conjunction of
model, certificate, envelope, and ordered representation. The artifact's
`novelty-claim-audit.json` enforces this language boundary, while the literature
freshness report lists remaining uncertainty.
