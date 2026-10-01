# Certificate trust boundary

## Verification objective

The certificate generator is untrusted for purposes of certificate acceptance.
The checker receives a finite model and a certificate, parses exact canonical
rationals, reconstructs the declared proof obligations, and accepts only when
all schema, Bellman, tree, and bound conditions it implements hold.

## Recomputed or rejected by the checker

- duplicate JSON keys, unknown fields, missing records, and malformed arrays;
- noncanonical integers or fractions, zero denominators, whitespace variants,
  decimals, negative zero, and unreduced rationals;
- model/certificate identifier and dimension mismatches;
- missing or duplicate state/pair potentials;
- Bellman inequalities for the declared model and scheduler action space;
- tree connectivity, edge membership, declared weight, and minimum-tree weight;
- ordered-mode eligibility and the ordered claim encoded by the certificate;
- the final rational upper-bound arithmetic.

Ordered-mode eligibility is deliberately a supplied-label-index check. The
checker does not search over secret permutations. Thus frozen A004 and A005 are
rejected in ordered scope even though `(0,2,1)` jointly sorts either case; tests
regenerate the relabeled forms and verify adjacent and dense bounds both equal 2.

The mutation suite contains positive controls plus targeted changes for each
class. Optimized Python execution is part of the regression suite so these
checks cannot be disabled by removal of native `assert` statements.

## Shared trusted base

“Separate checker” does not mean a separately developed or formally verified
program. The checker and producer still trust:

- CPython's JSON and arbitrary-precision integer implementation;
- the written finite-model semantics and any deliberately shared parser/data
  definitions identified in the import audit;
- the theorem connecting accepted local obligations to the advertised global
  bound;
- the input model supplied to both programs;
- the operating system and hardware.

The direct policy enumerator and production scalar dynamic program are
algorithmically distinct but share `src/model.py::kernel`, exact rational
arithmetic, and the written model. The comparison entry is allowed to call
`src/oracle.py::capacity` to obtain the value under test. Static checks prevent
the direct enumeration functions themselves from reusing that mass-state
recursion or memo table, and from importing certificate, tree, checker, campaign,
or summary algorithms. Closed-form calibrations provide a third bounded path.
These layers reduce common-code risk for tiny instances but do not remove common
specification risk or amount to an independent semantics implementation.

## Properties outside certificate checking

The checker does not establish that a real network matches the finite model,
that the theorem is novel, that a deployment is safe, that the certificate is
tight, or that the paper has passed peer review. Those questions require the
separate evidence and limitations recorded elsewhere in the artifact.
