# Algorithm Proposal v4: Credal Threshold Sweep

Status: design document (v4). It replaces the CCI recommendation of v3 (ALGORITHM_PROPOSAL.md). The model of v3 Section 1 is kept. Every theorem below is a target with a proof route, not a proved result.

## 1. Attack on CCI (v3)

| CCI component | Status | Prior art |
|---|---|---|
| Ellipsoid in instrument space driven by equilibrium or best-response queries; cut from an observed better response | Published | Bhaskar, Ligett, Schulman, Swamy (FOCS 2014; GEB 2019); revealed-preference Stackelberg learning (Roth, Ullman, Wu 2016) |
| Implementable set is a polyhedron in the tolls | Published | Toll LPs (Fleischer, Jain, Mahdian 2004; Harks et al. 2015; Paccagnan et al. 2019) |
| Infeasibility certificate from the volume bound | Textbook | Grötschel, Lovász, Schrijver |
| Lemma 2 (vertex reduction) | Textbook convexity; for choice functions, the reduction to extreme points is in Troffaes (2009) | |
| "Criterion-free": optimal for every belief implies admissible under every criterion | Immediate from the standard nesting of criteria | Troffaes (2007) |
| Lemma 1 (comonotone worst case; IDM Choquet sum) | Published; v3 already said so | Puccetti, Rüschendorf; Walley |
| Gamma-maximin acting as a self-imposed surcharge | Known in robust games | Aghassi, Bertsimas (2006); Crespi, Radi, Rocca (Comput. Econ. 2025, robust Cournot) |
| ALEH aggregate DP; E-admissibility as an LP | Published | Soundy, Irfan, Chan (UAI 2025); Jansen, Schollmeyer, Augustin |

**Only sub-step that is arguably new:** posing the queries at credal extreme points. It is also CCI's weakest point. It needs 4^Z queries per round under a box of rival means, which is about 10^150 for Z = 250. An ellipsoid in d = 2Z = 500 dimensions needs on the order of 10^6 rounds. With heuristic oracles, IMPLEMENTS is unsound, as v3 admits. Verdict: CCI is a recombination, and it does not scale to the real maps.

## 2. Structural observation used throughout

**Regime A.** P_z affine. Additive congestion: travel time is base · (xi_z + c_z n_z), where n_z is the exposure (D1) or the vehicle count (D2). Cost γ per vehicle-hour, no overtime penalty. Credal sets: a p-box over xi, and a box of means [ω̂ − δ, ω̂ + δ] over the rivals' (Q_{-i,z}, n_{-i,z}) (consistent beliefs in the sense of Lo 1996). The exogenous and strategic layers are independent.

Under Regime A, carrier i's expected payoff for a plan with signature σ is

  U_i(σ; p) = c_i^0(σ) − ⟨φ(σ), p⟩ − ⟨ψ(σ), θ⟩.

Here φ(σ) = (q_z, τ_z)_z are the features exposed to uncertainty. c_i^0 contains everything known: own-quantity revenue, vehicle cost, and own-congestion terms. ψ(σ) = (q_z, x_z)_z are the charged features, and θ = (s, t) are the city's instruments. The **effective price** is p_z = (b_z m^Q_z, γ(μ_z + c_z m^n_z)), where m and μ are the believed means. A credal set therefore enters only through its image

  K_i(δ) = p̂_i(ω̂) + K^0_i + δ·B_i,

where K^0_i is the box of p-box means of xi and B_i = diag(b, γc)·[−1, 1]^{2Z}. This image is a box, it is nested in δ, and it is Minkowski-linear in δ. Write cell_i(σ) = {p : σ ∈ argmax U_i(·; p)}. This is a closed convex polyhedral cell of the regular subdivision of the convex piecewise-linear function V_i(p) = max_σ U_i(σ; p).

This observation is elementary. The three candidates below are different uses of it.

## 3. Three candidate mechanisms

### Candidate 1: Certified Credal Bracketing (CCB), from seed (a), narrowed

**Mechanism.** In each zone, maintain a box [L, U] of aggregate vectors (Q_z, n_z) that contains every ICNE aggregate. Each sweep replaces it by [d(L, U), d(U, L)]. Here d is a decomposition function of the imprecise best-response map: d is increasing in its first argument, decreasing in its second, and d(x, x) contains BR(x ⊕ K(δ)). For one carrier, d evaluates the lowest and highest E-admissible q and k over the box. Under a single-crossing property this is attained at two corners of the box. With an NP-hard oracle, each corner value is replaced by certified bounds: a primal plan, and a relaxation (column-generation) dual bound that prunes options which cannot be optimal anywhere in the box.

```
CCB(δ): [L,U] <- a priori bounds
repeat: L' <- Σ_i lowBR_i(U, δ, gap); U' <- Σ_i highBR_i(L, δ, gap)
        if [L',U'] = [L,U] (tolerance): return [L,U]; else [L,U] <- [L',U'] ∩ [L,U]
```

**Claims.** (C1.1) Soundness: every ICNE_E(δ) aggregate stays inside [L, U], for any oracle whose bounds are valid. Route: if x* is a fixed point with x* in [L, U], then d(L, U) ≤ d(x*, x*) ∋ x* ≤ d(U, L). (C1.2) The boxes are nested and converge finitely on a lattice. (C1.3) The equilibrium is unique, up to δ, when L = U.

**Complexity.** 2N oracle calls per zone per sweep. Zones are independent in the surrogate.

**Prior art.** The alternating bracket is Roy and Sabarwal (games with strategic substitutes) and Milgrom and Roberts (1990). Mixed monotone operators go back to Guo and Lakshmikantham (1987), and decomposition functions to Coogan, Abate and Yang. Monaco and Sabarwal show that equilibrium sets of mixed games are unordered. No search found decomposition functions applied to game equilibria.

**Verdict.** The novelty is incremental: an existing iteration plus credal widening plus oracle gaps. The required single-crossing property fails for plan-level routing, and the fleet-complementarity premise is itself a conjecture (v3, S3). This candidate is kept only as a diagnostic.

### Candidate 2: Revealed-Imprecision Leader (RIL), from seed (b), redesigned

**Mechanism.** The city observes rounds (θ_t, σ_t). By Section 2, σ_t is E-admissible if and only if σ_t is optimal at some p_t in K(δ; θ_t). Quasilinear rationalization (Rochet's cyclical monotonicity) with p_t as a variable is *linear*: there must exist v_t with v_s − v_t ≤ ⟨φ(σ_s) − φ(σ_t), p_t⟩ for all s and t. So

  δ̂ = min δ s.t. ∃ v, p_t ∈ K(δ; θ_t)

is a single LP: the smallest imprecision that rationalizes the data. The admissible responses to a new θ form a predicted set (another LP), and the leader picks θ to maximize worst-case welfare over that set.

**Claims.** (C2.1) δ̂ is exact and monotone in the data. (C2.2) Consistency: if the true credal width is δ_0, then δ̂ ≤ δ_0. (C2.3) Each query either shrinks the predicted set or yields an implementing θ, which gives a halving-type bound on the number of rounds.

**Prior art.** Varian (1985), on the minimal data perturbation needed to satisfy GARP, is the same min-perturbation LP idea. Other close work: Rochet (1987); revealed-preference tests for maxmin expected utility (Chambers, Echenique and coauthors; Polisson, Quah, Renou 2020); Roth, Ullman, Wu (2016); Gan et al. (robust Stackelberg equilibrium with δ-suboptimal followers); Balcan, Fragkia, Harris (2025). **Verdict:** too close to Varian 1985 plus Afriat-type LPs. Dropped as the main candidate.

### Candidate 3 (rejected without development): aggregate-space column generation (seed c)

A master problem over convex hulls of per-player plans, with columns priced by a best-response integer program, is Cut-and-Play (Carvalho, Dragotto, Lodi, Sankaranarayanan, Oper. Res. 2025). Optimizing over pure equilibria with equilibrium inequalities is ZERO Regrets (Dragotto, Scatamacchia, IJOC 2023), and the sample generation method is Carvalho, Lodi, Pedroso. Exact plan-level PoA bounds for Z ≈ 250 are not credible in any case.

### Candidate 4: Credal Threshold Sweep (CTS), from seed (d); chosen

**Central idea.** Seed (d) proposed continuation in the imprecision width. Continuation is unnecessary. For E-admissibility, maximality and interval dominance, the admissible sets are nested in δ, so the whole family {ICNE_C(δ)} for δ ≥ 0 is the family of sublevel sets of one function of the profile. CTS computes that function, the **admission threshold**

  Φ_C(σ) = max_i A_i^C(σ_i; σ_{-i}), with A_i^C = inf{δ : σ_i is C-admissible against K_i(δ)},

together with its dual, the **robustness radius**

  R_i(σ̂_i; θ) = sup{δ : K_i(δ; θ) ⊆ cell_i(σ̂_i)}.

In Regime A both are distances between a box and a polyhedral cell in effective-price space. CTS returns, in one pass:

- for every δ at once, the exact equilibrium aggregate sets;
- the welfare envelope [W_min(δ), W_max(δ)], which gives PoA(δ) and PoS(δ);
- the existence threshold δ_0 = min_σ Φ_E(σ);
- for the leader, instruments that maximize the robustness radius of a target.

The function Φ_C is new as a computational object, and the city-scale decomposition (Claim 3) has no counterpart in CCI or ALEH.

## 4. Final algorithm: Credal Threshold Sweep (CTS)

### 4.1 Problem solved

*Input:* N carriers, Z zones. In stage 1 these are plan oracles; in stage 2, per-zone option sets with surrogate payoffs. Also: p-box bounds on xi, the instruments θ, a criterion C ∈ {E, M, ID}, and optionally a target σ̂.

*Output:*

1. Φ_C on every profile, implicitly, through per-zone threshold tables.
2. For all δ ≥ 0: the ICNE_C(δ) aggregate set and [W_min(δ), W_max(δ)], as exact step functions.
3. δ_0, the smallest imprecision at which an equilibrium exists. δ_0 > 0 is possible under D2.
4. The leader's value δ*(σ̂) = max_θ min_i R_i(σ̂_i; θ), with its maximizing θ.

### 4.2 Algorithm

```
CTS(instance, θ, C, δ_max):
  # Phase 1: cells (per carrier i, zone z)
  for i, z: build option set O_iz = {(q,k,τ)} (surrogate) and the lifted points
            (φ(σ), c0(σ)); cells_iz <- regular subdivision of V_iz in the
            2-D uncertain price plane (p_q, p_τ)          # convex hull, O(L log L)
  # Phase 2: thresholds
  for z, for aggregate A in lattice Λ_z, for i, for σ in O_iz with σ ≤ A:
        ω <- A − σ                                         # rival aggregate
        A_iz(σ, A) <- ThresholdC(cells_iz, σ, p̂(ω, θ), K0, B)    # Lemma 2
        drop σ if A_iz > δ_max                             # pruning
  # Phase 3: bottleneck–Pareto aggregate DP (per zone)
  for z, for final A in Λ_z:
        F_0 <- {(partial=0, thr=0, W=0)}
        for i = 1..N: F_i <- ParetoMin over (thr, W) and ParetoMax over (thr, W) of
             {(partial+σ, max(thr, A_iz(σ,A)), W+w_iz(σ)) : (partial,thr,W) ∈ F_{i−1}}
        keep labels with partial = A; add aggregate welfare term w_z(A)
        Front_z(A) <- staircase δ ↦ (min W, max W) over labels with thr ≤ δ
  # Phase 4: city assembly (Claim 3)
  δ_0 <- max_z min_A minthr_z(A);   W_min(δ) <- Σ_z min_A Front_z(A).min(δ);  same for max
  return Front, δ_0, W_min(·), W_max(·)

LeaderRadius(σ̂, Θ):        # Claim 5; LP in (θ, δ)
  cuts <- ∅
  loop: (θ, δ) <- argmax δ s.t. θ ∈ Θ, cuts
        for i: σ' <- argmax_σ [U_i(σ; p̂_i(θ)) + h_{K0+δB}(φ(σ̂_i) − φ(σ))]   # loss-augmented oracle
               if violated: cuts += {Δc − ⟨Δφ, p̂_i(θ)⟩ − h_{K0}(Δφ) − δ·h_B(Δφ) ≥ 0}
        if no cut: return (θ, δ)
```

`ThresholdC` is a closed-form geometric test in the plane (Lemma 2):

- **E:** the weighted ℓ∞ gap between the box p̂ + K0 and the cell.
- **M:** the smallest δ such that, for every vertex-adjacent rival option σ', some point of the box weakly prefers σ.
- **ID:** compare σ's upper value with the best lower value. This needs one evaluation of the support function h.

At plan level (stage 1) the cells are implicit. ThresholdC then runs Kelley cutting planes on V_i, with one oracle call per cut.

### 4.3 Claims to be proved

**Claim 1 (credal–price reduction).** Under Regime A, σ_i is E-admissible against the credal set if and only if cell_i(σ_i) ∩ K_i(δ) ≠ ∅. It is robustly optimal (optimal for every belief) if and only if K_i(δ) ⊆ cell_i(σ_i).
*Sketch:* the payoff is affine in (ξ, ω), so expectations depend only on means; the image of the credal set's means under the affine map is K_i(δ); independence makes the bilinear term separate.

**Claim 2 (criteria without vertex enumeration).** Let K be any box (more generally, a product polytope).
- (a) σ is maximal if and only if max_{σ'} [c^0(σ') − c^0(σ) − h_K(φ(σ') − φ(σ))] ≤ 0.
- (b) σ is not interval-dominated if and only if c^0(σ) − min_{p∈K} ⟨φ(σ), p⟩ ≥ max_{σ'} [c^0(σ') − h_K(φ(σ'))].
- (c) Gamma-maximin is max_σ [c^0(σ) − h_K(φ(σ))].
- (d) E-admissibility is an LP over p with implicit constraints. Kelley's method terminates within |Σ_i| cuts, and the ellipsoid method needs O(d² log(R/ε)) oracle calls.

Here h_K is zone-separable and piecewise linear, so (a)–(c) each need one oracle call with zone-separable convex penalties. CCI needs 4^Z.
*Sketch:* (a) "for all σ' there exists p with Δ ≤ 0" is the same as "for all σ', min_p Δ ≤ 0", and min_p of a linear function over K is minus the support function. (b) and (c) follow by direct substitution.

**Claim 3 (city decomposition).** If the surrogate payoffs are zone-separable (vehicles dedicated to a zone; stem and fixed costs per vehicle) and K_i is a product over zones, then:
- A_i^C(σ) = max_z A_iz^C(σ_z) for C ∈ {E, M};
- ICNE_C(δ) = ∏_z ICNE_{C,z}(δ);
- δ_0 = max_z δ_{0,z};
- W_min(δ) = Σ_z W_{min,z}(δ), and likewise for W_max.

*Sketch:* with a separable objective and a product credal image, optimality at p is equivalent to optimality in each zone at p_z. For maximality, use the separability of h_K. Interval dominance is not separable (the max over σ' couples the zones), so it is assembled by a one-dimensional merge, and this is stated as a limitation.

**Claim 4 (exact sweep).** For C ∈ {E, M, ID}:
- A^C is well defined and lower semicontinuous, because K(δ) is nested and compact.
- Phase 3 returns the exact ICNE_C(δ) aggregate set and [W_min, W_max](δ) for every δ ≤ δ_max.
- These are step functions with at most N·Σ_z |O_z| breakpoints.
- W_min is nonincreasing and W_max nondecreasing in δ.
- Gamma-maximin admissible sets are *not* nested, so Γ is handled on a δ-grid. A two-option counterexample will be included.

*Complexity per zone:* O(N L log L + |Λ_z|·N·L + |Λ_z|²·N·L'·F). Here L' is the number of options that survive pruning and F is the length of the Pareto front (at most the number of distinct thresholds). Over zones the total is linear in Z and runs in parallel.
*Sketch:* the DP is an aggregative decomposition, as in Soundy et al. The label (max threshold, sum of welfare) is a bottleneck–sum bi-criterion, which is monotone under extension, so Pareto pruning is exact.

**Claim 5 (leader's maximal-robustness LP).** The value δ*(σ̂) = max_θ min_i R_i(σ̂_i; θ) is the optimum of an LP in (θ, δ). Its constraints are Δc − ⟨Δφ, p̂_i(θ)⟩ − h_{K0}(Δφ) − δ·h_B(Δφ) ≥ 0, one for each i and σ'. The constraints are linear because K is Minkowski-linear in δ and p̂ is affine in θ.
- Separation is the loss-augmented oracle in LeaderRadius, with one call per carrier.
- The method terminates finitely because the set of signatures is finite.
- δ* < 0 measures the nominal implementation gap, which is the v3 quantity ε*.
- At the returned θ, the target is an ICNE under every criterion for every δ' ≤ δ*.

*Sketch:* Claim 1, plus the support function of a Minkowski sum, plus the finite-constraint cutting-plane LP.

**Claim 6 (soundness with heuristic oracles; stage 1).** Every cut comes from a concrete plan, so:
- computed E-thresholds are lower bounds;
- computed robustness radii are upper bounds;
- a "not maximal" verdict is exact.

With a relaxation bound Ū_i ≥ V_i (column-generation lower bound on routing cost), the reverse bounds hold for ε-admissibility, with ε equal to the duality gap. So each threshold is returned as a certified interval [A_lo, A_hi(ε)].

**Claim 7 (surrogate transfer).** If the surrogate payoff error is at most η uniformly, then exact-model ICNE_E(δ) ⊆ surrogate ICNE_E^{2η}(δ) (2η-admissibility), and conversely. This is stated as an η-relaxation only.

### 4.4 Explicitly not claimed

- Novelty of the regular-subdivision geometry. Price-space cells of quasilinear demand are Baldwin and Klemperer's tropical geometry, and stability radii of combinatorial optima go back to Chakravarti and Wagelmans (1998).
- Novelty of the loss-augmented cutting plane. It is structured max-margin learning (Tsochantaridis et al.; Ratliff et al.). The robustness-radius LP is close in spirit to the incenter in inverse game theory (Cui, Yu, Pinson, Paccagnan, IJCAI 2025) and to inverse robust optimization (Berthold, Heller, Seidel).
- Exactness outside Regime A. Under overtime penalties, multiplicative BPR or carrier-level fleet caps, cells are no longer polyhedral, separability breaks, and CTS becomes a grid method with η-bounds. Fleet caps add a carrier-specific shadow price on the k feature, and the outer search over it is heuristic.
- Strong implementation. Claim 5 is weak implementation. The audit of the other equilibria comes from the sweep at the returned θ.
- Plan-level exactness at city scale. That holds only on stage-1 instances.
- PoA bounds in the (λ, μ)-smoothness sense. The PoA here is instance-exact, not worst-case.

### 4.5 What is plausibly new

1. Imprecise equilibrium families treated as sublevel sets of an admission threshold. This yields δ-indexed PoA and PoS curves computed exactly. The closest work: ε-PoA curves for approximate equilibria (Christodoulou, Koutsoupias, Spirakis 2011), which perturb utilities rather than beliefs and give worst-case bounds rather than instance computation; and uncertainty-level sensitivity in robust games (Crespi, Radi, Rocca 2025), which covers only Gamma and has no algorithm.
2. Claim 2(a): maximality over a combinatorial option set with one oracle call through the support function. The imprecise-probability literature uses pairwise LPs over finite option lists (Troffaes; Nakharutai, Troffaes, Caiado 2019; Jansen et al.).
3. The existence threshold δ_0 as an exactly computable instability index for non-potential (D2) congestion–Cournot games.
4. The leader LP that chooses instruments to maximize the belief-robustness radius of a target, uniformly over criteria.
5. The product decomposition that makes items 1–4 exact for Z ≈ 250.

**Residual risk: medium.** Each primitive is known (distance to a cell, Pareto DP, max-margin cutting planes). The contribution is the threshold representation and what it makes computable. A referee may call items 1 and 4 "stability-radius analysis for games". The defence is that the perturbations are restricted to the credal (belief) manifold, which makes them an imprecise-probability solution concept with policy meaning, together with the exact city-scale computation. No search found an admission threshold or robustness radius for imprecise or ambiguous equilibria, nor any δ-indexed PoA curve. Stauber (JET 2011) defines robustness to ambiguity qualitatively, with no radius and no algorithm. The closest risk is the Emelichev school (stability radius of equilibria under ℓ∞ payoff perturbation). Their papers concern cooperative or multicriteria finite games with matrix perturbations, not belief boxes, aggregates or instruments, but the full texts should be checked before submission.

## 5. Staged implementation plan

**Stage 1: exactness on tiny instances** (N = 2–3, Z = 2, |S_i| ≤ 7, plan level).
- `credal_price.py`: features φ, effective prices, the box K(δ), support functions.
- `threshold.py`: Kelley LP for E (scipy `linprog`), single-call tests for M and ID (Claim 2), heuristic and exact oracles.
- `sweep.py`: the Phase-3 DP on enumerated plans.
- `leader_lp.py`: the Claim 5 cutting-plane LP.

Brute-force verification:
- (i) enumerate all plans and profiles, and check C-admissibility on a dense grid of beliefs; Claims 1 and 2 must match on 200+ random cases, under both D1 and D2;
- (ii) the sweep's step functions must equal per-δ enumeration;
- (iii) δ*(σ̂) must equal brute-force maximization over a θ-grid refined by LP;
- (iv) Claim 6 brackets must contain the exact values;
- (v) find D2 instances with δ_0 > 0 and certify them.

**Stage 2: zone-level model on the five maps** (Z ≈ 40–230).
- *Surrogate.* For each zone z and carrier i, use the route length L_iz(q, k) ≈ 2 r̄_iz k + α_z √(A_z q) (Beardwood–Halton–Hammersley, Daganzo). Here r̄_iz is the network distance from the depot to the zone, taken from the travel-time matrix.
- *Calibration.* α_z is calibrated by sampling q customers from the GHSL population inside z (q ∈ {5, …, 120}, 30 samples), solving the CVRPs with the existing heuristic (HGS or PyVRP for checks), and fitting by least squares. Validation is on held-out samples, and the fitted error gives η (Claim 7).
- *Congestion.* c_z ∝ 1/(lane-km in z). τ = L/v_free + s_0·q. The options are (q, k) on a grid with capacity and free-flow shift constraints.
- *Data-driven ξ-box.* DKW p-box means from the travel-time samples available per zone (time-of-day matrices). If no samples are available, the box is a declared assumption.
- *Implementation.* NumPy and Numba for the per-zone DP. Zones run in parallel.

**Stage 3: experiments.**
1. Cost: oracle calls and wall time against (a) CCI with vertex queries, (b) ALEH rerun on a δ-grid, (c) best-response dynamics with a grid leader. Measure the speed-up from one sweep against per-δ recomputation.
2. Certified gaps: the widths of [A_lo, A_hi] at stage 1; surrogate η at stage 2.
3. PoA(δ) and PoS(δ) curves per city, and the aggregate intervals [Q̲_z, Q̄_z] and [n̲_z, n̄_z] as functions of δ, for E, M and ID.
4. Imprecision width: δ swept from 0 to full ignorance; DKW sample size n; δ_0 and the frequency of fleet arms races under D2.
5. One instrument against two: δ*(σ̂) and W at the optimum, for the congestion charge alone, charge plus delivery charge, and a city-uniform against a zone-specific charge (the Buchanan two-wedge effect).
6. Fairness: the distribution over zones of the robustness radius, of the welfare loss and of the charge burden, weighted by population (Gini and the lowest decile of zones).
7. Out-of-sample: coverage of the p-box (1 − β), and how often realised aggregates fall inside the predicted ICNE intervals.

## Sources checked for novelty

- Bhaskar, Ligett, Schulman, Swamy: https://ar5iv.arxiv.org/html/1408.1429 ; https://ideas.repec.org/a/eee/gamebe/v118y2019icp533-569.html
- Cut-and-Play: https://arxiv.org/html/2111.05726v4
- ZERO Regrets: https://arxiv.org/pdf/2111.06382
- Inverse game theory, incenter (IJCAI 2025): https://object.cloud.sdsc.edu/v1/AUTH_da4962d3368042ac8337e2dfdd3e7bf3/ml-papers-txt/IJCAI/2025/inverse_game_theory_an_incenterbased_approach__789ce6aa.txt
- Bertsimas, Gupta, Paschalidis, inverse equilibrium: https://www.mit.edu/~dbertsim/papers/Optimization/Data-driven%20estimation%20in%20equilibrium%20using%20inverse%20optimization.pdf
- Suboptimality loss for imperfect equilibria: https://arxiv.org/pdf/2609.23200
- Emelichev et al., stability radius in games: https://www.mathnet.ru/eng/basm105 ; https://www.mathnet.ru/eng/dm1045
- Chakravarti, Wagelmans, stability radii: https://repub.eur.nl/pub/1403
- Inverse robust optimization (Berthold, Heller, Seidel): https://arxiv.org/pdf/2105.09588
- Robust inverse optimization (Ghobadi et al.): https://uwspace.uwaterloo.ca/items/4df4d472-dc03-4a4a-9083-cdd8b2e9a90e
- Stauber, Knightian games and robustness to ambiguity: https://ideas.repec.org/a/eee/jetheo/v146y2011i1p248-274.html
- Crespi, Radi, Rocca, robust games: https://arxiv.org/pdf/2002.00225
- Christodoulou, Koutsoupias, Spirakis, approximate-equilibrium PoA: https://arxiv.org/pdf/0804.3160
- Liu, rationalizability with imprecise probabilities: https://studiesinlogic.sysu.edu.cn/en/node/112
- Nakharutai, Troffaes, Caiado; Troffaes finite approximations: https://arxiv.org/pdf/1906.12215 ; https://ar5iv.labs.arxiv.org/html/1203.0919
- Monaco, Sabarwal; Roy, Sabarwal: https://kuwpaper.ku.edu/2014Papers/201403.pdf ; https://papers.ssrn.com/abstract=3683187
- Barthel, Hoffmann, strategic heterogeneity: https://ideas.repec.org/a/spr/joecth/v67y2019i3d10.1007_s00199-017-1092-6.html
- Mixed-monotone decomposition functions: https://arxiv.org/pdf/2103.08638 ; https://coogan.ece.gatech.edu/papers/abate2021interconnected.html
- Baldwin, Klemperer, tropical demand: https://www.nuff.ox.ac.uk/economics/papers/2015/demandtypesrevised2016.pdf
- Revealed preference and MEU tests: https://eml.berkeley.edu/~fechenique/published/chapterRP.pdf ; https://ideas.repec.org:443/p/eca/wpaper/2013-310013.html
- Robust Stackelberg equilibrium (Gan et al.): https://par.nsf.gov/servlets/purl/10466723
- Structured Stackelberg learning: https://arxiv.org/abs/2504.09006v1
- Monderer, Tennenholtz, k-implementation: https://arxiv.org/pdf/1107.0022
- Tolls under misspecification (Chiu, Ferguson): https://arxiv.org/html/2505.11791v1
- Toll setting with robust Wardrop equilibria: https://optimization-online.org/2024/07/a-toll-setting-problem-with-robust-wardrop-equilibrium-conditions-under-budgeted-uncertainty/
- Continuous approximation in freight: https://researchportal.bath.ac.uk/en/publications/continuous-approximation-models-in-freight-distribution-managemen/
- Distributionally robust CVRP (Ghosal, Wiesemann): https://optimization-online.org/2018/08/6759/
- Cournot under Knightian uncertainty (Boff, Werlang): https://repositorio.fgv.br/items/7223d034-3b2c-40e2-ad8b-3d52944acfaf
