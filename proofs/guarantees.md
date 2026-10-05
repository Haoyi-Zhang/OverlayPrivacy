# Defensive certificate guarantees

These are mathematical proofs over the finite model below, not a mechanized proof,
not a deployment claim, and not evidence about real traffic. All probabilities and
certificate entries in the implementation are rational. The definitions allow real
probabilities; the proofs do not depend on a bounded denominator.

## 1. Model and observable transcript

A fixed secret s belongs to {0,...,m-1}. Its initial queue is q_s in {0,...,B};
its independent slot-arrival coins have parameter lambda_s. B is the queue capacity.
The public token state starts at C. At time t=0,...,H-1 a common behavioral scheduler
chooses a in {0,1} from the public history only, with a=1 permitted only when b>0.
An arrival x is then drawn. Write u=min(B,q+x) and l=1[q+x>B]. If a=1, one real
packet is served when u>0; otherwise a cover packet is emitted with probability p.
Thus e=a*1[u>0 or k=1] and q'=u-a*1[u>0], with k~Bernoulli(p). If a=0 then e=0.
The observation is either y=e or y=(e,l), fixed for the entire experiment. The
public token transition is b'=min(C,b-a+1[(t+1) mod R=0]). A reservation consumes
one token irrespective of emission, queue occupancy, real/cover status, or loss.

The transcript Z is the entire sequence (a_0,y_0,...,a_{H-1},y_{H-1}); time and
horizon are public. Real/cover tags, payloads, intermediate queue lengths, timing
within a slot, arrival events, and overflow in emission-only mode are not observed.
No claim covers an implementation that exposes one of these omitted observations.
A scheduler is one common map pi_t(a|history), not a separate map for each secret.
Its fresh action randomization is conditionally independent of the hidden secret
and model randomness given that history. Arrivals and cover coins are fresh and
independent across slots. The queue is one aggregate bottleneck abstraction, not
a full network topology, traffic trace, or operational anonymous service.

For fixed pi let P_s^pi(z) be the channel row. Define
C(P)=sum_z max_s P_s(z), TV(P,Q)=(1/2)sum_z|P(z)-Q(z)|.
Then 1<=C(P)<=m. For a prior rho, Bayes vulnerability is
V(rho,P)=sum_z max_s rho_s P_s(z). Direct comparison of each summand gives
V(rho,P)<=||rho||_infinity C(P). Uniform rho attains V/(max rho)=C(P).
Thus log_2 C is the familiar prior-free maximal-leakage/min-entropy-capacity
quantity on the full declared input support; it is not a new privacy metric.
It is not a pointwise posterior bound or differential-privacy guarantee.

## 2. History-safe pairwise potentials

For each certified pair i<j, each hidden state pair (q,r), each t,b and each common
legal action a, provide a joint one-step law gamma on (y_i,q_i',y_j,q_j') whose
marginals are the declared kernels. The implementation's gamma does not depend on
t,b, but the soundness argument would also allow that dependence. Provide
v_ij(t,b,q,r) in [0,1], with v_ij(H,b,q,r)=0, satisfying, for every legal a,

v_ij(t,b,q,r) >= sum_gamma gamma *
  (1[y_i != y_j] + 1[y_i=y_j] v_ij(t+1,b',q_i',q_j')).                 (A)

Finally d_ij must be at least v_ij(0,C,q_i,q_j) and at most 1.

**Theorem 1 (whole-history bound).** Every common public-history scheduler obeys
TV(P_i^pi,P_j^pi)<=d_ij for every certified pair.

**Proof.** While the two histories agree, sample a single action according to the
common pi; it is legal in both executions because the public token histories agree.
Draw the paired transition according to gamma. At the first unequal observation,
charge one and retain that charge forever. After that first mismatch, complete the
two runs using any valid conditional marginals; no subsequent coupling is required.
Before the first mismatch, define D_t=0, afterward D_t=1. The process
D_t+(1-D_t)v_ij(t,b_t,q_t,r_t) is a supermartingale by (A), after averaging over the
shared action. At H it equals D_H. Consequently Pr(D_H=1)<=v_ij(0,C,q_i,q_j).
A completed coupling has each execution's correct marginal distribution. Equality
of histories until H implies equality of the full transcript including actions.
The coupling inequality TV(P_i^pi,P_j^pi)<=Pr(Z_i!=Z_j) proves the result. This
argument works for every pi, regardless of history length or randomized choices.
It never resets a mismatch merely because the queues later coalesce. QED.

**Non-claims.** Local potentials can relax scheduler observability, so equality in
(A) need not produce the true worst public-scheduler total variation. A marginal
per-slot bound without history conditioning cannot replace (A). Matching final
queue distributions cannot replace matching transcripts.

## 3. Tree aggregation and the exact summary-only envelope

Let d_ij in [0,1] be symmetric declared upper bounds, whether or not they satisfy
the triangle inequality. Uncertified entries can always be filled with 1. A tree
has vertices {0,...,m-1}; w(T)=sum_{ij in T}d_ij.

**Lemma 2 (tree bound).** If TV(P_i,P_j)<=d_ij on a spanning tree T, then
C(P)<=1+w(T).

**Proof.** Root the tree at r and orient its edges outward. For any output z, choose
a maximizer k. Telescoping on the r-to-k path, replacing increments by their
positive parts, and then including the remaining nonnegative edge terms yields
max_i P_i(z)<=P_r(z)+sum_(parent,child)(P_child(z)-P_parent(z))_+.
Sum over z. The root sums to 1, and each positive-part difference sums to total
variation because both rows normalize. QED.

This is a specialization of classical tree/union-bound reasoning, not a claim to
have invented the minimum-spanning-tree union bound.

**Theorem 3 (summary sharpness).** Over all finite channels with m rows that satisfy
TV(P_i,P_j)<=d_ij for every pair, the largest possible C(P) is exactly
1+min_T w(T). The maximizing channel can be chosen with at most 2m-1 positive
columns. This theorem concerns upper-bound summaries, not equality-constrained TV
matrices or a fixed queue model.

**Proof.** Lemma 2 proves the upper bound. For t in [0,1), form the graph containing
all edges with d_ij<=t. For each component U that appears over any interval of t,
let w_U be the total length of time that it is a component. Define one output
column per positive w_U, with P_i(U)=w_U when i belongs to U and 0 otherwise.
At every t each i belongs to exactly one component, so every row sums to 1.
For i!=j let u_ij be the first threshold at which they are connected. Equivalently,
u_ij=min_{paths i to j} max_{edge on path} d_edge. Their columns agree after that
threshold and are disjoint before it. Therefore TV(P_i,P_j)=u_ij<=d_ij, including
thresholds 0 and 1. Let k(t) be the number of components. Then
C(P)=sum_U w_U=integral_0^1 k(t)dt.
For a minimum spanning tree T, its edges of weight <=t connect exactly the same
components as the full threshold graph: otherwise a path using only edges <=t
would connect two T-components, and the T-path between them would have an edge
>t; exchanging the heavier edge contradicts minimality. A forest on m vertices
with e edges has m-e components, so
integral_0^1 k(t)dt = m-sum_(e in T)(1-d_e)=1+sum_(e in T)d_e.
The threshold components only merge. Distinct components form a laminar forest;
there are at most m singleton leaves and m-1 strict merges, hence at most 2m-1
positive columns. Zero-length intervals and tied edges add no columns. QED.

For a retained tree alone, filling all other bounds with 1 shows that 1+w(T) is
sharp for that tree-only interface. A generic sparse certificate cannot claim to
match the best bound from an omitted dense matrix. Dense-first sparsification
reduces package/check size but does not retrospectively reduce synthesis work.
The ordered reduction below is a distinct result that reduces synthesis too.

The threshold witness is not asserted to optimize Bayes vulnerability for every
fixed prior. For example rho=(3/10,1/10,3/5), d_01=1/5,d_12=3/5,d_02=4/5 admits
columns supported on {0},{0,1},{2},{1,2},{0,1,2} of weights 1/5,3/5,3/5,1/5,1/5.
The normalized resulting rows give V=21/25, whereas the threshold witness gives
V=4/5. Both have C=9/5. These are exact witnesses, not a claim to a fixed-prior
optimum, and they specify no estimator or operational traffic strategy.

## 4. Lossless adjacent-pair reduction under ordered grand coupling

Assume lambda_0<=...<=lambda_{m-1} and q_0<=...<=q_{m-1}; all other parameters and
the observation mode are common. At every slot use a single fresh U~Uniform[0,1]
and K~Bernoulli(p) across the family. Set X_s=1[U<lambda_s]. This explicitly
constructs one grand coupling; the result does not assume that arbitrary chosen
pairwise monotone couplings admit a joint realization.

Let v^can be the unique backward solution of (A) with equality to the maximum
over legal actions, for the fixed canonical pair coupling. Let d^can_ij be its
initial value. Equivalently this is the first-observation-disagreement probability
maximized in a fully observed finite pair-state control problem. It is a
conservative intermediate certificate quantity, not the original public-history
channel capacity or its exact pairwise TV.

**Lemma 4 (pathwise order).** Until, and even after, observations first differ, all
queues and both observation coordinates remain ordered under common actions.

**Proof.** If q_i<=q_j and X_i<=X_j, then q_i+X_i<=q_j+X_j. Clipping to B and
subtracting one iff a=1 and the clipped queue is positive preserve this order.
The emission predicate a*1[u>0 or K=1] is monotone in u, and overflow 1[q+X>B]
is monotone in q+X. Induction proves the claim. If two outer observations are
equal, every intermediate observation is equal to them, coordinate by coordinate.
In emission-only mode use just the emission coordinate. QED.

**Lemma 5 (nested-interval dominance).** For i<=k<l<=j,
d^can_kl<=d^can_ij.

**Proof.** Choose an optimal deterministic Markov control for the inner pair (k,l),
which exists by finite backward induction. Run queues i,k,l,j with the same fresh
coins and the same actions, using this inner control even after the outer histories
have separated. The resulting inner process has its canonical pair law and attains
d^can_kl. By Lemma 4, an inner disagreement at any time implies an outer disagreement
at that time; hence the inner first-mismatch event is contained in the outer one.
It remains to upper-bound the outer mismatch probability under actions that may
observe inner states. Condition on the enlarged filtration containing the entire
grand-coupled past, not merely the outer pair. The next U,K are independent of this
filtration. Conditional on the current outer states and chosen legal action, their
outer transition has exactly the canonical outer kernel. Therefore the Bellman
inequality for the outer value function remains valid under this enlarged
filtration. The stopped supermartingale used in Theorem 1 bounds the outer mismatch
probability by d^can_ij. Combining the two inequalities proves the lemma. Crucially,
we did not pretend that the inner controller is a function of the outer state, or
that it is an allowed public-history scheduler. QED.

**Theorem 6 (lossless ordered reduction).** The adjacent chain (0,1),...,(m-2,m-1)
is a minimum spanning tree of the entire dense canonical matrix d^can. For every
allowed public-history scheduler pi,

C(P^pi)<=1+sum_{r=0}^{m-2} d^can_(r,r+1)
       =1+min_T sum_(ij in T)d^can_ij.

**Proof.** Lemma 5 implies d^can_ij>=max_{i<=r<j}d^can_(r,r+1). For each non-chain
edge, its weight is at least the maximum edge weight on the unique chain path.
This cycle property suffices for chain minimality: starting from any tree, add a
missing chain edge, then exchange it with an edge crossing its chain cut; every
such crossing edge spans that chain edge and has at least its weight. Each exchange
retains a tree, does not increase total weight, and increases the number of chain
edges. Iteration produces the chain. Theorem 1 and Lemma 2 give the privacy bound.
QED.

Only m-1 canonical pair syntheses/checks are needed. With equal state grids, their
potential and Bellman obligation counts are exactly 2/m of the dense m(m-1)/2
counts. Support work need not have this ratio when pair support sizes differ. More
precisely, potential entries per pair are (H+1)(C+1)(B+1)^2 and Bellman obligations
per pair are H(1+2C)(B+1)^2. Total support work also depends on coincident rates,
zero probabilities, and observation mode; do not infer an exact support ratio when
these differ across selected pairs. Rational arithmetic complexity additionally
depends on bit lengths. Generality is over the declared model, not over all
traffic shapers, arrival processes, hidden schedulers, or unbounded horizons.

Both rate order and initial-queue order matter. For H=1,lambda=(0,0,0),q=(0,1,0),
B=C=1,p=0 and no refill, the dense canonical distances are (d01,d12,d02)=(1,1,0).
The adjacent chain yields 3 while the dense minimum gives 2. Ordered mode rejects
this model. An arbitrary inflated adjacent upper bound may still be sound but need
not equal the omitted dense canonical result: canonical couplings, Bellman
equalities, initial equalities, and the joint order are all checked for the
lossless claim. Dense mode supports any valid couplings/potential upper bounds and
claims minimum only relative to its actually supplied summary matrix.

## 5. Cover baseline and exact tiny scalar oracle

In emission-only mode at most N=min(H,C+floor((H-1)/R)) reservations occur for H>0
(and N=0 for H=0). This follows by counting initial tokens and refills before the
last slot; it is also attainable by spending available tokens. On the event that
the first N reservation cover coins are all 1, every reserved slot emits for every
secret, so the coupled observation histories agree. These coins can be sampled
lazily at successive reservations; the reservation choice precedes each fresh coin.
Therefore TV<=1-p^N and C<=1+(m-1)(1-p^N). This is a conservative baseline; it
ignores queue dynamics. Overflow observations invalidate this reasoning. Full
padding p=1 certifies C=1 for emission-only mode, but not for emission-plus-overflow.

For an exact tiny oracle let M_s(q) be unnormalized probability mass of reaching a
public history with queue q under secret s. Start from point masses of total 1 per
secret. At H return max_s sum_q M_s(q). At earlier nodes choose one common legal
a, propagate all M_s through each observation branch y, and sum recursively over
y. Maximize that sum over a. Backward induction over the finite history tree proves
that this scalar is sup_pi sum_z max_s P_s^pi(z). Action randomization cannot improve
it: since actions are observed, a randomized root action is a convex combination
of the deterministic branch values. The same argument holds at every history.
This oracle uses no coupling, tree or certificate potentials, but is exponential
in the worst case. It has a fixed node cap in the artifact and is used only for
tiny owned models. It returns scalar values and node counts, never an action
policy, estimator, trace-linking procedure or target-specific operational output.

## 6. Checker trust boundary

The checker independently expands the declared queue kernel, checks nonnegative
normalized marginals, exact rational coupling marginals, all potential obligations,
initial bounds, and a connected tree. Dense minimum is verified by the cycle
property rather than by rerunning the producer's Kruskal algorithm. Ordered mode
also checks the parameter order, analytic canonical Bernoulli coupling, exact
Bellman equalities and adjacent tree. The marginal and order checks have different
code paths from synthesis. The checker does not import the producer, kernel
generator or oracle. This is implementation separation, not a proof assistant,
independent human review, or a verified compiler. Its acceptance establishes only
the mathematical obligations implemented over its declared finite semantics.
Deployment conformance, omitted observations, honest scheduling, liveness, workload
realism, and the correctness of the mathematical checker implementation remain
outside its acceptance result.


## 7. Analytic calibrations added after the frozen campaign

These are supporting derivations, not additional novelty claims or new workload
coverage. They are stated and proved in the main manuscript as well.

### 7.1 One slot, equal empty queues

Let H=1, B,C>=1, and all initial queues be zero. With emission-only observation,
a reservation emits Bernoulli(theta_s), theta_s=p+(1-p)lambda_s. Its capacity is
max_s theta_s + max_s(1-theta_s) = 1+(1-p)(lambda_max-lambda_min).
Idle yields one. Because the action is observed, a randomized root action gives
a convex combination of these capacities and cannot improve the reservation.
Under the shared coins, the canonical pair mismatch probability is
(1-p)|lambda_j-lambda_i|. There is no continuation at H, so this is the canonical
pair value; adjacent differences telescope. This proves equality of the exact
scalar and canonical bound for this entire special-case family.

### 7.2 Equal initial queues and rate continuity

For a pair with equal initial queues, the probability that its shared-uniform
arrival indicators differ in a given slot is Delta=|lambda_j-lambda_i|. The event
that they never differ has probability (1-Delta)^H, independently of how common
legal actions depend on past states. On that event, an induction gives identical
queues and all declared observations. Therefore d_can_ij <= 1-(1-Delta)^H, even
for the state-aware canonical control relaxation. With ordered rates and all
initial queues equal, the chain theorem gives
C <= 1+sum_r [1-(1-Delta_(r,r+1))^H] <= 1+H(lambda_max-lambda_min).
The last inequality follows from 1-(1-x)^H<=Hx and telescoping. Cap the bound at m.
The same argument applies to both admitted observation modes, but not to unequal
initial queues. It is a conservative analytic calibration, not a padding optimum.

### 7.3 Whole-row perturbation

For two finite channels P,R on the same labels/alphabet and row errors
TV(R_s,P_s)<=eta_s, pointwise max_s R_s(z) <= max_s P_s(z)
+sum_s(R_s(z)-P_s(z))_+. Summation gives C(R)<=C(P)+sum_s eta_s, also bounded by m.
A scheduler-uniform bound requires this whole-row assumption for every scheduler
in the same class. No one-slot frequency check establishes it. No deployment eta
is supplied or inferred in this project.

### 7.4 Rational bit growth

If D is a common multiple of the denominators of all arrival and cover parameters,
canonical transition probabilities admit denominator D^2. With h remaining slots,
backward values admit denominator D^(2h), by induction: multiply by the transition,
sum over outcomes, and select a maximizing action. Values are between zero and
one, so numerator and denominator bit lengths in this representation are
O(h log D); reducing a fraction cannot increase them. The explicit-state count
is polynomial in numerical B,C,H, not necessarily in their binary encoding length.
Arbitrary general-scope coupling inputs remain subject to separate parser limits.

## Ordered minimum-tree lemma: exact cut condition

The graph-theoretic step in the ordered reduction is stronger than a triangle
inequality.  Write the ordered secrets as \(0,\ldots,m-1\), let
\(a_k=w(k,k+1)\), and suppose every edge \((i,j)\) crossing the adjacent cut
\(\{0,\ldots,k\}\mid\{k+1,\ldots,m-1\}\) obeys

\[
  w(i,j)\ge a_k \qquad (i\le k<j).
\]

Equivalently, \(w(i,j)\ge\max_{i\le k<j}a_k\).  For each cut, the adjacent
edge \((k,k+1)\) is therefore a minimum-weight crossing edge.  The MST cut
property permits that edge in a minimum tree.  Applying the argument to every
ordered cut gives all \(m-1\) adjacent edges; together they are already a
spanning tree, so the adjacent chain is an MST.  Ties may make the MST
nonunique, but do not change its weight.

For the queue-specific canonical weights, Lemma 5 proves this cut condition
through nested-interval dominance under shared coins and the enlarged filtration.
The threshold-component construction instead proves the upper-summary envelope
in Section 3; metricity alone does not supply the ordered cut condition.
For example, the three-point metric
\(w(0,1)=w(1,2)=2\), \(w(0,2)=1\) satisfies all triangle inequalities, while
the adjacent chain weighs 4 and an MST weighs 3.  The executable exhaustive
check in `tests/test_threshold_mst_lemma.py` covers small integer threshold
patterns and includes this counterexample as a regression test.

## Why the finite exact oracle may enumerate deterministic policies

For a finite secret-to-history channel \(K\), the uniform-prior multiplicative
guessing capacity used here is
\[
  C(K)=\sum_y \max_s K(y\mid s).
\]
It is convex in \(K\): for \(0\le\lambda\le1\), the pointwise maximum is
convex, hence
\(C(\lambda K_0+(1-\lambda)K_1)\le
\lambda C(K_0)+(1-\lambda)C(K_1)\).

A finite behavioral scheduler is a product of action simplices, one simplex for
each public-history decision node.  With every other local rule fixed, the
induced channel is affine in the action distribution at one node.  Convexity
therefore implies that replacing that distribution by some vertex of its
simplex does not decrease the objective.  Repeating this finite operation over
all nodes yields a deterministic public-history policy with objective at least
that of the original randomized scheduler.  Thus an optimum is attained among
the deterministic policies enumerated by the tiny-model oracle.  This argument
is about existence of an optimal deterministic policy; it does not say that
all randomized policies are equivalent.

`tests/test_randomized_policy_dominance.py` exercises the convexity inequality
on exact-rational finite channels.  The proof above, rather than the test, is
what justifies deterministic enumeration.
