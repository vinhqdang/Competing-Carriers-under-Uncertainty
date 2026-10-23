# Referee Report on ALGORITHM_PROPOSAL_v4 (Credal Threshold Sweep, CTS)

Scope: docs/ALGORITHM_PROPOSAL_v4.md, read against DESIGN.md and ALGORITHM_PROPOSAL.md. Part A audits novelty with web searches (snippet-level; full texts were not all retrieved, so "ALREADY KNOWN" verdicts marked (abstract) need a full-text check). Part B audits the mathematics. Quick numeric checks were run in a scratch directory outside the repository.

## Summary verdict

CTS is a competent assembly of known parts. Its individual theorems are mostly correct and elementary. As a "new algorithm", the claim is weak. The closed forms of Lemma 4 are support-function algebra, and the sweep of Theorem 2 is a bottleneck-Pareto dynamic program. Both are textbook. What I could not find in the literature is the specific package: imprecision-width-indexed PoA/PoS curves for E-admissible and maximal equilibria in a Cournot-congestion game, computed exactly. That is a defensible contribution of model plus analysis, not of algorithm. A referee would write: "The algorithm is a parametric (sensitivity) analysis of a finite game with a box-shaped belief set. All steps reduce to LP duality and a knapsack-style DP. The novelty lies in the application, not the method."

There is also a mathematical error that undercuts the headline "exact" claim: the ID criterion does not factor across zones, so Theorem 2 is false for ID (B-3).

---

## A. Novelty audit

### (i) Threshold / critical-imprecision / robustness-radius representation, with PoA/PoS curves

Closest work:
- Christodoulou, Koutsoupias, Spirakis, "On the performance of approximate equilibria in congestion games" (https://arxiv.org/abs/0804.3160). The ε-equilibrium sets are nested in ε, and PoA(ε) and PoS(ε) are bounded as functions of ε. This is the same family-of-sublevel-sets idea, with ε as a utility-slack parameter.
- Feik, Lanzetti, Bolognani, Dörfler, Paccagnan, "Strategically Robust Aggregative Games" (https://arxiv.org/abs/2604.23669). Agents protect against an ambiguity ball of radius ε around the aggregate. ε interpolates between Wardrop and security strategies, and PoA is reported to reach 1 in some settings. This is the most dangerous recent neighbour: aggregative games, an ambiguity radius, PoA as a function of the radius. It uses an optimal-transport ball and a Γ-type (worst-case) rule, not E-admissibility or maximality.
- Crespi, Radi, Rocca, "Insights on the Theory of Robust Games" (https://arxiv.org/abs/2002.00225). The uncertainty level runs from 0 to 1, robust equilibria are ε-Nash of the nominal game, and sensitivity to the level is discussed.
- Routing games under uncertainty (https://arxiv.org/abs/1411.4943). PoA is analysed as a function of the amount of uncertainty (affine costs: 4/3, then 1, then rising).
- Stauber, "Knightian games and robustness to ambiguity", JET 2011 (https://ideas.repec.org/a/eee/jetheo/v146y2011i1p248-274.html). Qualitative robustness, no radius.
- Emelichev, Karelkina and co-authors, stability radius of Nash/Pareto situations under l_p payoff perturbation (https://www.mathnet.ru/eng/basm105, https://www.mathnet.ru/eng/dm1045). Radius formulas exist for finite games (abstract).

New in CTS: the pairing of E/M/ID admissibility over credal boxes with exact δ-indexed W_min/W_max and PoA/PoS in a combinatorial game. The nesting itself is trivial (Lemma 3).

Verdict: **INCREMENTAL.** The "threshold = sublevel-set parameter" idea is the ε-equilibrium family relabelled. Article 6's "None of the searches found..." claim is true only for the exact combination, and a referee will cite Christodoulou et al. and Feik et al.

### (ii) Cournot / aggregative games with congestion externalities solved in closed form by zone decomposition

Closest work:
- Harks and Klimm, aggregative location games (https://www3.math.tu-berlin.de/disco/research/publications/pdf/HarksKlimm2015.pdf).
- Harks and Timmermans, Cournot with affine prices as atomic splittable congestion games, Math. Programming 2022 (https://academicnewsletter.sufe.edu.cn/info/396887).
- Willis and Punzo, coupled Cournot-congestion layers (https://arxiv.org/abs/2406.19079).
- Johari and Tsitsiklis, Cournot efficiency.

Zone separability under additive congestion is a modelling assumption, and the "zone-product theorem" is the statement that a separable objective over a product set is optimized coordinate-wise. I found no closed form for Cournot-congestion equilibria in a regime decomposition, but the one that exists (Theorem 7(c)) is linear algebra on a symmetric affine game.

Verdict: **INCREMENTAL** (zone product: ALREADY KNOWN as a mathematical fact; its use for exactness at Z≈250 is a modelling convenience).

### (iii) Robust toll / charge implementation under ambiguity with certificates

Closest work:
- Robust Wardrop tolls under budgeted uncertainty (https://optimization-online.org/2024/07/a-toll-setting-problem-with-robust-wardrop-equilibrium-conditions-under-budgeted-uncertainty/).
- Robust and stochastic congestion pricing: Wang, Gardner, Waller (https://trid.trb.org/view/1241252); two-stage robust toll design (https://hub.hku.hk/handle/10722/150605); Chung, Friesz, Yao, Liu (https://pure.psu.edu/en/publications/dynamic-congestion-pricing-with-demand-uncertainty-a-robust-optim/).
- Gan et al., robust Stackelberg equilibrium (https://par.nsf.gov/servlets/purl/10466723).
- Berthold, Heller, Seidel, inverse robustness (https://arxiv.org/abs/2105.09588): maximizes the considered uncertainty set under an objective. This is structurally Theorem 4's LP.
- Cui, Yu, Pinson, Paccagnan, incenter-based inverse game theory (IJCAI 2025): maximizes the margin by which a target equilibrium stays an equilibrium, which is Theorem 4 with utility parameters in place of beliefs.

Theorem 4's LP (max δ s.t. robust optimality constraints linear in (θ, δ)) is a Chebyshev-centre / maximum-margin LP.

Verdict: **ALREADY KNOWN** structurally (incenter / inverse robustness); **INCREMENTAL** because the margin is over beliefs in a credal box. The "robust to all four criteria" statement (Theorem 4(b)) is immediate from robust-optimality dominating every criterion.

### (iv) Stability radius of equilibria under belief perturbation

Closest work: Emelichev et al. (above), Stauber 2011, the Cui et al. incenter, Chakravarti and Wagelmans (https://repub.eur.nl/pub/1403), Berthold et al. The δ-ball of Definition 4 is an l∞ (weighted) stability radius of an equilibrium whose perturbation acts through the price coordinates. Lemma 4's formula, min over σ' of [slack / dual norm of Δφ], is the standard stability-radius formula for linear optimization under l∞ cost perturbation. The proposal itself concedes this in Section 6.

Verdict: **ALREADY KNOWN** for the radius concept and the formula; **PLAUSIBLY NEW** only in applying it jointly to E-admissibility and maximality sets (rather than the optimal set) with a common δ over players.

### (v) Application to urban freight or last-mile with imprecise probabilities

Searches (last-mile, parcel, carriers, Cournot, congestion, ambiguity, imprecise probability) found only deterministic or stochastic carrier games (e.g. Deng, Fang, Lim on consolidation centres; Friesz et al. on urban freight pricing at https://pure.psu.edu/en/publications/dynamic-pricing-in-an-urban-freight-environment/; the AAMAS 2022 last-mile congestion paper at https://ifaamas.csc.liv.ac.uk/Proceedings/aamas2022/pdfs/p1473.pdf). Nothing with credal sets. The closest imprecise-probability game papers are Liu (https://studiesinlogic.sysu.edu.cn/en/node/112), Nakharutai, Troffaes, Caiado (https://arxiv.org/abs/1906.12215) and the ISIPTA decision-tree work, none about freight.

Verdict: **PLAUSIBLY NEW** (application niche). Absence of search hits is weak evidence; run a Scopus/Web of Science search before asserting.

### Overall novelty verdict

CTS as written is not a new algorithm in the sense an OR journal would accept for a methods paper. The recognised building blocks are: ε-equilibrium families (Christodoulou et al.), stability radii and inverse robustness (Emelichev; Berthold et al.), incenter/maximum-margin LP (Cui et al.), support-function algebra for credal-box optimality (Troffaes, Jansen et al.), and bottleneck-Pareto DP. The objection in a referee's words: "Computing, for a finite game with box-shaped beliefs, the smallest box under which each profile is rationalizable is parametric analysis. The authors present a bookkeeping device as an algorithm."

### Narrowest defensible claim

"We characterize, and compute exactly on separable instances, the nested family of imprecise-equilibrium sets of a Cournot-congestion game indexed by belief imprecision, together with the induced PoA/PoS curves, and show where exactness breaks (ID, fleet coupling, D2, plan-level)." Present it as an analysis framework with an exact solver on a stated class, not as a new algorithm. Drop "novel algorithm" language and state the neighbours (Christodoulou et al.; Feik et al.; Cui et al.) up front.

### Changes that would genuinely strengthen novelty

1. Prove something that the generic-parametric view does not give. A real candidate is the D2 existence-threshold result: a computed δ_0 as an instability index for non-potential games, with a proved complexity separation (D1 polynomial, D2 NP-hard via Partition). That is outside the stability-radius literature. Finish Proposition 2 rigorously.
2. Give a tight, non-trivial PoA(δ) bound for Regime A (Theorem 8(b)), for example by proving smoothness for linear Cournot plus affine congestion. A closed-form curve beats an algorithm for "new".
3. Treat the coupled case (fleet cap) with a proved Lagrangian-product theorem and a gap bound. That is where the zone-product claim would become non-trivial.
4. Compare with a direct competitor: run the Feik et al. strategically robust equilibrium on the same instances and show where E/M-admissibility differs qualitatively.

---

## B. Mathematical audit

Numeric checks done: (1) the Theorem 7(c) width against brute force over the eight corner belief combinations (three random instances agree to 1e-15); (2) the shrinking-with-congestion claim; (3) an interval-dominance counterexample for zone factoring; (4) hand verification of the Proposition 1 best-response cycle, of the PoS expansion in Theorem 9, and of the Theorem 6(a) first-order conditions.

| # | Claim | Status | Notes |
|---|---|---|---|
| 1 | Lemma 1 (credal-price reduction) | FIXABLE | Needs ω̂ − δw ≥ 0 so that Dirac mean vectors are feasible, otherwise beliefs include negative quantities. The δ→∞ limit in Theorem 1(e) uses unbounded negative beliefs. With clipping, K is no longer p̂ + K0 + δB. It becomes a box clipped at 0, and the thresholds in Lemma 4 are piecewise-linear in δ, not simple ratios. State this as a hypothesis ("δ ≤ min ω̂/w"), or make the clipped box the base case. |
| 2 | Lemma 2 (cells are translated by θ) | WRONG under D2 | Translation cell(σ;θ) = cell(σ;0) − θ needs ψ = φ, which holds only under D1 (x = τ). Under D2, ψ = (q, k) ≠ φ = (q, τ), so θ shifts the lifted points, not the cells. Cells remain a regular subdivision, but without the translation property. Theorem 6(c)'s equality case and Lemma 2's "instruments act by translation" must be restricted to D1. |
| 3 | Lemma 3 (nesting E, M, ID; Γ fails) | SOUND | Γ counterexample verified: A and B cross at δ = (p̂₂ − p̂₁)/(w₁ − w₂). ICNE_E ⊆ ICNE_M ⊆ ICNE_ID also holds (non-strict ID). |
| 4 | Lemma 4(R), (M), (ID), (E) | SOUND with two caveats | Support-function algebra checked, including the ID envelope and monotonicity. (a) The ratio form needs h_B > 0, and σ' with Δφ = 0 need the separate condition N ≥ 0 (handled for M, omitted for R). (b) The O(log L) box-to-polygon distance query needs preprocessing that is not described; use O(L) or cite. |
| 5 | Lemma 5 zone product (E, M, R) | FIXABLE | Valid only if O_i = ∏_z O_iz and the credal set is a product. Any per-carrier fleet cap Σ_z k_iz ≤ K_i, or a budget, breaks the option product, so max_z and min_z formulas fail. Say so in the statement, not only in Section 6. Integer problems also have a Lagrangian duality gap. |
| 6 | Lemma 5, ID remark and Theorem 2 for ID | WRONG | ID condition is Σ_z(ℓ_z − r_z)(δ) ≥ 0, so a carrier's zone choices are coupled. Counterexample: two zones, one carrier, p̂ = 1.5, half-width 1 (K = [0.5, 2.5]). Zone 1 options X (c = 0, φ = 0) and Y (c = 0.5, φ = 0): X is strictly dominated. Zone 2 options T (c = 2, φ = 1) and R (c = 0.4, φ = 0): T has interval [−0.5, 1.5], R has 0.4. Joint profile (X, T): upper value 1.5 ≥ Σ best lower values 0.5 + 0.4 = 0.9, so it is ID-admissible, but zone 1 alone is not. The city set is not a product, so W_min = Σ_z W_min,z fails and "ID through the merge" does not give an exact DP. Fix: restrict Theorem 2 to E and M, or make ID a joint two-level DP over the carrier's total slack (a knapsack over zones, pseudo-polynomial). |
| 7 | Theorem 1(a) exact potential, D1 | SOUND, with a scope note | Potential verified by direct expansion (symmetric bilinear interaction terms). Requires carriers to share b_z, c_z, an individual (not shared) fleet constraint, and μ̂ common to all. A shared depot or fleet cap across carriers is a generalized Nash game and breaks the potential property. |
| 8 | Theorem 1(b) | SOUND | Needs μ̂ ∈ [μ̲, μ̄]. The Γ potential with upper-corner surcharge is correct for φ ≥ 0. |
| 9 | Theorem 1(c) / Proposition 1 | SOUND (realization open) | Best-response cycle verified; each profile has exactly one deviator; δ_0^E = 1/w_n holds with closed credal boxes. Realization through q is unchecked and also adds the b q_i Q_{-i} interaction, which may break the cycle. |
| 10 | Theorem 1(d) | SOUND | |
| 11 | Theorem 1(e) | FIXABLE | The δ → ∞ limit needs the clipping assumption of item 1. |
| 12 | Proposition 2 (NP-hardness, D2) | PLAUSIBLE, unproven | Dunkel and Schulz concerns weighted congestion games, whose payoff structure differs from this rank-one bilinear coupling τ_i·K_{-i}. The risk is larger than stated: reduce from a graphical two-action game with this interaction, or prove it directly. |
| 13 | Theorem 2 (i), (ii) (E, M) | SOUND, conditional | Correct under Lemma 5. W includes γμ^true T: μ^true is unspecified inside [μ̲, μ̄]. PoA and PoS depend on it, so report curves per μ^true or fix μ̂. |
| 14 | Theorem 2 (iii) breakpoint count Σ_z Σ_i |O_iz| | WRONG | Thresholds A_iz(σ, A) depend on A through p̂(A − σ), so there are up to N·L·|Λ_z| distinct values per zone, not N·L. The same error is in Theorem 3(a) (F ≤ N L'). Replace with N L' |Λ_z|, or note that A enters only by translation of the box. |
| 15 | Theorem 3(a) complexity | FIXABLE | Aggregate lattice Λ_z is a product over (Q, K, T) and can be huge. |Λ_z|² is pseudo-polynomial only. Also, the cell-polygon query is per (i, z), so state the preprocessing. |
| 16 | Theorem 3(b) Kelley, ≤ |Σ_i| calls | SOUND but vacuous | The bound is exponential. In 3 variables, a centre-of-gravity or ellipsoid method gives O(log(R/ε)) calls and is the useful statement. Requires an exact oracle, which Theorem 5 shows is NP-hard. |
| 17 | Theorem 3(b) Dinkelbach, one oracle call per iteration | FIXABLE | The subproblem min f(σ') − λ h_B(Δφ(σ')) rewards the absolute value |Δq|, |Δτ_z|, i.e. it maximizes a convex function. It is not a best-response oracle. It needs sign-pattern binaries (two per zone, big-M) inside the routing model, or 2^{2Z} oracle calls. The same applies to the loss-augmented separation in Theorem 4(c). State that the oracle must be a modified routing model. Σ' with Δφ = 0 are a separate oracle call. |
| 18 | Theorem 3(c) Radzik O(p² log² p) | UNPROVEN | Radzik's bound is for linear fractional 0-1 programs. After linearizing |·|, the denominator is not linear in the 0-1 variables without extra sign variables, so "adapt Radzik" hides the real work. Treat as an open claim or drop. |
| 19 | Theorem 4(a), (b) | SOUND, with an edge case | If some σ' has the same φ as σ̂ but a better known part (e.g. a dominated fleet option), no δ is feasible. The LP is infeasible, not "negative". Definition 7's "δ* negative via the LP" should say −∞ in that case. |
| 20 | Theorem 4(d) | SOUND under zone-specific instruments, D1 or D2 | Correct per Lemma 5, subject to item 5. |
| 21 | Theorem 5 (coNP-hardness) | SOUND, weak | Valid (tour-optimality verification, Papadimitriou–Steiglitz), but it is hardness of the routing oracle at N = 1, not of the credal or game structure. A referee will call it a restatement of routing hardness. Strengthen with a hardness result that persists when the routing oracle is free (for example, hardness in N or Z). |
| 22 | Theorem 6(a) | SOUND | First-order and efficiency conditions re-derived: r_i = −b q_i* + γ c τ_i'(T* − τ_i*). Collinearity statement is right. The "Cournot wedge dominates" condition should read: for every i, r_i < 0 (a negative t is required). |
| 23 | Theorem 6(b) | FIXABLE | δ* ≤ 0 with equality only if κ = 0 is correct, but for κ > 0 the sup is over an empty set, so δ* = −∞ in the set definition and negative only by LP convention. Say "no positive robustness". |
| 24 | Theorem 6(c) | SOUND under D1 | See item 2 for D2. |
| 25 | Proposition 3 | SOUND for the one-dimensional case | The Ω(d log) extension is open. |
| 26 | Theorem 7(a) | SOUND | Needs W > 0 for PoA. |
| 27 | Theorem 7(b) | SOUND, as a selection statement | σ(δ) is a global potential maximizer. Γ-equilibria include local maximizers. The statement does not hold for all Γ-equilibria. |
| 28 | Theorem 7(c) slope 2Nω/((N+1)β) and interval | SOUND | Confirmed numerically (match 1e-15). Hidden assumptions: μ̂ is the midpoint of [μ̲, μ̄]; interior q_i (non-negativity); the center is the μ̂-Nash aggregate (the notation Q* clashes with the efficient Q*). |
| 29 | Theorem 7(c) prediction "larger β shrinks the interval" | WRONG as stated | The slope is 2N/(N+1) · ω/β with ω/β = (b w_Q + γ c h w_n)/(b + γ c h²). As c grows this moves monotonically from w_Q to w_n/h. It shrinks only if w_n < h·w_Q. Counterexample: b = g = h = 1, w_Q = 0.1, w_n = 1: ω/β = 0.10, 0.55, 0.85, 0.98 for c = 0, 1, 5, 50. The interval widens with congestion. |
| 30 | Lemma 6 | SOUND | |
| 31 | Theorem 8(a) | SOUND, conditional | W = Σ U_i + CS, so W ≥ Σ U_i if P ≥ 0, with zero charges. The smoothness hypothesis is the whole content. |
| 32 | Theorem 9 PoS bound | SOUND | W − Ψ = Σ_z[(b/2)Σq² − (γc/2)(T² − Στ²)] verified by expansion. Needs μ^true = μ̂; otherwise add γ|μ̂ − μ^true|·|T* − T_Ψ|. |
| 33 | Theorem 10, Proposition 4 | SOUND | |
| 34 | Robustness-radius positivity, indivisibility ("indivisibility creates robustness") | SOUND in the continuous model | The claim is relative to the best-response set being a line; it is a statement about generic strict concavity, not about integrality as such. Say "discreteness gives fat cells". |

## Top five issues the author must resolve

1. **Zone factorization fails for ID (and for any coupled carrier problem).** Theorem 2 is false for ID. Restrict to E and M, or build a joint DP; state product hypotheses in Lemma 5. State also that fleet or budget coupling breaks the product (item 5).
2. **Novelty is overstated.** The sublevel-set family is the ε-equilibrium family; the radius formula is a stability radius; the leader LP is the incenter/inverse-robustness LP. Retitle as an analysis framework, cite Christodoulou et al., Feik et al. (2026), Cui et al., Berthold et al., and restrict the novelty claim to the credal-box E/M family, exact PoA/PoS curves and the D2 existence threshold.
3. **Oracle claims at plan level are not correct as written.** The Dinkelbach and loss-augmented subproblems maximize convex absolute-value terms; the "one best-response call per iteration" and the O(p² log² p) claims need sign variables and a real proof. Kelley's "≤ |Σ_i|" is vacuous.
4. **D1 and D2 mixed in lemmas.** Lemma 2 (translation) and Theorem 6(c) hold only for D1; the potential and existence results are D1; D2 is where the non-trivial results live and where Proposition 2 is still unproven. Reorganize around that split.
5. **Counting and prediction errors.** Breakpoint and front-size bounds ignore the dependence on A (item 14), and the "steeper congestion shrinks the interval" prediction is false unless w_n < h·w_Q (item 29), so the empirical table row for Theorem 7(c) would test a wrong hypothesis. Also fix the clipping assumption behind Lemma 1 and the δ → ∞ limit, and the dependence of PoA/PoS on the unspecified μ^true.
