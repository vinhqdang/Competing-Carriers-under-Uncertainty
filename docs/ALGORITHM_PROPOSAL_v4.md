# Algorithm Proposal v4: Credal Threshold Sweep (CTS)

Status: design document (v4). It replaces the CCI recommendation of v3 (ALGORITHM_PROPOSAL.md).

**Status labels on claims.**
- **[proof known]**: elementary or standard; the outline below is complete.
- **[to prove]**: the outline is complete, but a rigorous write-up is still needed and there is a stated risk.
- **[numerically checked]**: reserved for claims verified by the Stage-1 brute force. None carries it yet. Claims planned for that check are marked **[to check numerically]**.

---

## 1. Attack on CCI (v3)

| CCI component | Status | Prior art |
|---|---|---|
| Ellipsoid in instrument space driven by best-response queries; cut from an observed better response | Published | Bhaskar, Ligett, Schulman, Swamy (FOCS 2014; GEB 2019); Roth, Ullman, Wu (2016) |
| Implementable set is a polyhedron in the tolls | Published | Fleischer, Jain, Mahdian (2004); Harks et al. (2015); Paccagnan et al. (2019) |
| Infeasibility certificate from the volume bound | Textbook | Grötschel, Lovász, Schrijver |
| Vertex reduction (Lemma 2 of v3) | Convexity; reduction to extreme points for choice functions | Troffaes (2009) |
| "Criterion-free" implementation | Immediate from the nesting of decision criteria | Troffaes (2007) |
| Comonotone worst case; IDM Choquet sum | Published | Puccetti, Rüschendorf; Walley |
| Gamma-maximin acting as a surcharge | Known | Aghassi, Bertsimas (2006); Crespi, Radi, Rocca (2025) |
| ALEH aggregate DP; E-admissibility as an LP | Published | Soundy, Irfan, Chan (UAI 2025); Jansen, Schollmeyer, Augustin |

The only sub-step that is arguably new is querying at credal extreme points. It is also CCI's weakest point. It costs 4^Z queries per round (about 10^150 for Z = 250), the ellipsoid in d = 500 dimensions needs about 10^6 rounds, and IMPLEMENTS is unsound with heuristic oracles.

## 2. Candidates and why CTS was chosen

**(a) Certified Credal Bracketing.** A decomposition-function iteration [L, U] ← [d(L, U), d(U, L)] on zone aggregate boxes, with certified oracle bounds. This is the Roy–Sabarwal / Milgrom–Roberts bracket plus mixed-monotone embeddings (Coogan; Guo–Lakshmikantham) plus credal widening. It needs single crossing, which plan-level routing does not have. Monaco–Sabarwal show that equilibrium sets in mixed games are unordered. Verdict: incremental. Kept as a diagnostic only.

**(b) Revealed-Imprecision Leader.** The smallest imprecision that rationalizes the observed pairs (θ_t, σ_t) is an LP: Rochet's cyclical monotonicity, with p_t as a variable inside the credal box. This is too close to Varian (1985, minimal data perturbation for GARP), to MEU revealed-preference tests (Chambers, Echenique; Polisson, Quah, Renou) and to robust Stackelberg learning (Gan et al.). Dropped.

**(c) Aggregate-space column generation.** This is Cut-and-Play (Carvalho, Dragotto, Lodi, Sankaranarayanan, Oper. Res. 2025), ZERO Regrets (Dragotto, Scatamacchia, IJOC 2023) and the sample generation method (Carvalho, Lodi, Pedroso). Rejected.

**(d) Credal Threshold Sweep (chosen).** The continuation idea of seed (d) is unnecessary. The equilibrium sets are nested in the imprecision width δ, so the entire family {ICNE_C(δ)} for δ ≥ 0 is the family of sublevel sets of one function, the **admission threshold** Φ_C. In Regime A, Φ_C and its dual, the **robustness radius**, are closed-form distances between a box and a polyhedral cell in a two-dimensional price plane per zone. A city-scale product theorem makes the computation exact for Z ≈ 250. One pass gives:

- the equilibrium aggregates for all δ;
- the PoA and PoS curves;
- the existence threshold δ_0;
- the instruments that maximize robustness.

---

## 3. Formal model

Zones z ∈ [Z], carriers i ∈ [N], city instruments θ.

**A1 (finite options, zone-separable surrogate).** Carrier i chooses σ_iz = (q, k, τ) from a finite set O_iz that contains 0: deliveries, vehicles, and exposure in vehicle-hours. Its payoff is Σ_z U_iz. At plan level (Stage 1), σ is the signature of a routing plan and the payoff depends on the plan only through σ.

**A2 (affine demand).** P_z(Q) = a_z − b_z Q, with b_z > 0.

**A3 (additive congestion).** The time cost of exposure is γ τ (ξ_z + c_z n_z), with c_z > 0. Under D1, n_z = Σ_j τ_jz (exposure). Under D2, n_z = Σ_j k_jz (vehicle count). There is no overtime penalty. Write x for the congestion variable: x = τ under D1 and x = k under D2.

**A4 (credal sets).** M_i(δ) is the set of all laws of (ξ, ω_{-i}), where ω_{-i,z} = (Q_{-i,z}, n_{-i,z}), satisfying:

- E ξ_z ∈ [μ̲_z, μ̄_z] (DKW p-box means; width κ_z = μ̄_z − μ̲_z);
- E ω_{-i} ∈ ω̂_{-i} ± δ w, with weights w = (w_Q, w_n) > 0.

Means are not clipped at 0. A remark treats clipping.

**A5 (consistency).** ω̂_{-i} is the rivals' realised aggregate at the profile (equilibrium in beliefs, Lo 1996).

**A6 (instruments).** θ_z = (s_z, t_z): a per-delivery charge s_z on q (s_z < 0 is a subsidy) and a congestion charge t_z on x. The city-uniform variant sets θ_z = θ for every z.

**Payoff.**

  U_iz(σ; m, μ, θ) = c_iz(σ) − ⟨ψ(σ), θ_z⟩ − ⟨φ(σ), p⟩, with p = (b_z m^Q, γ(μ + c_z m^n)).

Here c_iz(σ) = (a_z − b_z q) q − f k − γ c_z τ x is the known part (own revenue, fleet cost, own congestion), φ(σ) = (q, τ) and ψ(σ) = (q, x).

**Welfare.** W = Σ_z [∫_0^{Q_z} P_z − Σ_i F_iz − γ μ^true_z T_z − γ c_z T_z X_z], where F_iz is the fleet cost, T_z = Σ_i τ_iz and X_z = Σ_i x_iz. Transfers cancel.

**Definition 1 (credal image).** K_iz(δ) = p̂_iz + K0_z + δ B_z, where:

- p̂_iz = (b_z Q̂_{-i,z}, γ c_z n̂_{-i,z});
- K0_z = {0} × [γ μ̲_z, γ μ̄_z];
- B_z = [−b_z w_Q, b_z w_Q] × [−γ c_z w_n, γ c_z w_n].

Support functions: h_B(v) = b_z w_Q |v_1| + γ c_z w_n |v_2|, and h_{K0}(v) = γ max(μ̲ v_2, μ̄ v_2).

**Definition 2 (admissibility).** For a box K, σ is C-admissible as follows.

| Criterion | Condition |
|---|---|
| E (E-admissible) | ∃ p ∈ K with σ ∈ argmax U(·; p) |
| M (maximal) | ∄ σ' with U(σ'; p) > U(σ; p) for all p ∈ K |
| ID (not interval-dominated) | max_{p∈K} U(σ; p) ≥ max_{σ'} min_{p∈K} U(σ'; p) |
| Γ (Gamma-maximin) | σ ∈ argmax_σ min_{p∈K} U(σ; p) |

**Definition 3 (ICNE).** σ ∈ ICNE_C(δ, θ) if every σ_i is C-admissible against K_i(δ) evaluated at the realised rival aggregates.

**Definition 4 (threshold and radius).** A_i^C(σ) = inf{δ ≥ 0 : σ_i is C-admissible against K_i(δ)}, with inf ∅ = ∞. The profile threshold is Φ_C(σ) = max_i A_i^C(σ). The robustness radius is R_i(σ; θ) = sup{δ : K_i(δ) ⊆ cell_i(σ_i)}, where cell_i(σ) = {p : σ ∈ argmax U_i(·; p)}.

**Definition 5 (existence threshold).** δ_0^C = min_σ Φ_C(σ).

**Definition 6 (robust PoA and PoS).** With W* = max W:

- PoA_C(δ) = W* / min{W(σ) : σ ∈ ICNE_C(δ)};
- PoS_C(δ) = W* / max{W(σ) : σ ∈ ICNE_C(δ)}.

**Definition 7 (robust implementability).** δ*(σ̂) = sup{δ : ∃ θ ∈ Θ with K_i(δ; θ) ⊆ cell_i(σ̂_i) for all i}. When the sup is over an empty set, δ* is defined by the LP of Theorem 5 and is negative.

---

## 4. Theory

### 4.1 Structural lemmas

**Lemma 1 (credal–price reduction) [proof known].** Under A1–A5, for every P ∈ M_i(δ), E_P U_i(σ) = U_i(σ; p(P)) with p(P) ∈ K_i(δ). The map P ↦ p(P) is onto K_i(δ). Hence each criterion of Definition 2 applied to the credal set M_i(δ) equals the same criterion applied to the box K_i(δ).
*Proof.* Under A3 the payoff is affine in (ξ, ω) (additive congestion, so there is no ξ·n product). Linearity of expectation gives the identity. The Dirac measure at any admissible mean vector belongs to M_i(δ), which gives surjectivity. Each criterion quantifies over P only through E_P U, so it transfers. ∎

**Lemma 2 (cells) [proof known].** V_i(p) = max_σ U_i(σ; p) is convex and piecewise linear. The cells cell_i(σ) are closed convex polygons, possibly empty, that cover the plane and form the regular subdivision induced by the lifted points (φ(σ), c_i(σ) − ⟨ψ(σ), θ⟩). Instruments act on the cells by translation: under an exposure charge, cell_i(σ; θ) = cell_i(σ; 0) − θ.
*Proof.* Each cell is an intersection of |O_i| half-planes. Covering holds because a maximizer always exists. The translation identity holds because θ enters U exactly as p does on the coordinates (q, τ). ∎

**Lemma 3 (nesting) [proof known].** For δ ≤ δ', the C-admissible sets satisfy Adm_C(δ) ⊆ Adm_C(δ') for C ∈ {E, M, ID}. This fails for Γ.
*Proof.*
- E: a witness p ∈ K(δ) also lies in K(δ').
- M: "dominates on all of K(δ')" implies "dominates on all of K(δ)".
- ID: the upper value of σ rises and every lower value falls as K grows.
- Γ counterexample: take φ(A) = (1, 0), φ(B) = (0, 1), equal known parts, p̂_1 < p̂_2 and w_1 > w_2. A is Γ-optimal at δ = 0, and B is Γ-optimal once δ > (p̂_2 − p̂_1)/(w_1 − w_2). ∎

**Lemma 4 (closed-form thresholds) [proof known].** Fix σ and the rival aggregate. Let Δφ = φ(σ) − φ(σ'), and let N(σ, σ') = U(σ; p̂) − U(σ'; p̂) with the ξ-coordinate of p̂ set to 0.

- (R) σ is optimal for all p ∈ K(δ) iff N − h_{K0}(Δφ) − δ h_B(Δφ) ≥ 0 for all σ'. Hence R(σ) = min over σ' with h_B > 0 of [N − h_{K0}(Δφ)] / h_B(Δφ).
- (M) σ is maximal iff N + h_{K0}(−Δφ) + δ h_B(Δφ) ≥ 0 for all σ'. Hence A^M(σ) = max(0, max over σ' with h_B > 0 of −[N + h_{K0}(−Δφ)] / h_B(Δφ)). It equals ∞ if some σ' with h_B(Δφ) = 0 has N + h_{K0}(−Δφ) < 0.
- (E) A^E(σ) = min{δ ≥ 0 : ∃ p, p ∈ p̂ + K0 + δB, U(σ; p) ≥ U(σ'; p) for all σ'}. This is an LP in 3 variables with |O| + 4 constraints, solvable in O(|O|) time (Megiddo 1984). Equivalently, it is the B-gauge distance from the box p̂ + K0 to the cell.
- (ID) A^ID(σ) is the smallest root of ℓ(δ) − r(δ) = 0. Here ℓ(δ) = U(σ; p̂) + h_{K0}(−φ(σ)) + δ h_B(φ(σ)) is increasing and linear, and r(δ) = max_{σ'}[U(σ'; p̂) − h_{K0}(φ(σ')) − δ h_B(φ(σ'))] is convex, piecewise linear and nonincreasing. The root is found in O(|O| log |O|) from the upper envelope.

*Proof.* Use min_{p∈K} ⟨−Δφ, p⟩ = −h_K(Δφ) and the Minkowski additivity h_{p̂+K0+δB} = ⟨·, p̂⟩ + h_{K0} + δ h_B. For M, "for all σ' there exists p with U(σ) ≥ U(σ')" is equivalent to "for all σ', max_p[U(σ) − U(σ')] ≥ 0". Each condition is then linear in δ, so the threshold is the stated ratio. ∎

**Lemma 5 (zone product) [proof known].** Under A1 with product images K_i = ∏_z K_iz:

- A_i^C(σ) = max_z A_iz^C(σ_z) for C ∈ {E, M};
- R_i = min_z R_iz.

ID does not factor: city-level ID-admissibility is Σ_z (ℓ_z − r_z)(δ) ≥ 0, which is a one-dimensional merge of piecewise-linear functions.
*Proof.*
- E: optimality of a separable objective at a product point holds iff it holds in every zone.
- M and R: the condition "for all σ', Σ_z g_z(σ'_z) ≥ 0" is equivalent to "for every z, min_{σ'_z} g_z ≥ 0", because the term σ'_z = σ_z contributes g_z = 0.
- ID compares a sum of zone maxima with a sum of zone maxima of lower values, so it does not factor. ∎

### 4.2 Existence and structure of ICNE

**Theorem 1 (existence and structure).**

- (a) [proof known] Under D1, the game with mean μ̂ and δ = 0 is an exact potential game with

  Ψ = Σ_{i,z} [c_iz(σ_iz) − s_z q − (t_z + γ μ̂_z) τ] − Σ_z Σ_{i<j} (b_z q_i q_j + γ c_z τ_i τ_j).

  *Proof:* carrier i's interaction terms are −b q_i Q_{-i} − γ c τ_i T_{-i}, which are symmetric bilinear forms, so unilateral differences of U_i and Ψ coincide (Monderer–Shapley). A finite potential game has a pure equilibrium. ∎
- (b) [proof known] Under D1, ICNE_C(δ) ≠ ∅ for every δ ≥ 0 and every C ∈ {E, M, ID, Γ}.
  - *E, M, ID:* a Nash equilibrium σ° of the μ̂-game makes each σ°_i optimal at p̂_i(σ°) + (0, γ μ̂) ∈ K_i(δ), by A5. So σ° ∈ ICNE_E, which is contained in ICNE_M and ICNE_ID.
  - *Γ:* since φ ≥ 0, the worst case in K is the upper corner, so the Γ-game is the precise game with μ = μ̄ and surcharges b δ w_Q on q and γ c δ w_n on τ. It is still a potential game. ∎
- (c) [proof known] Under D2, a pure Nash equilibrium need not exist, and δ_0^E > 0 is possible. **Proposition 1.** One zone, N = 2, U_i = c_i(σ_i) − α τ_i k_{-i}, with α = 1:

  | Option | k | τ | c |
  |---|---|---|---|
  | A1 (carrier 1) | 1 | 4 | c_1(B1) + 6 |
  | B1 (carrier 1) | 3 | 1 | c_1(B1) |
  | X (carrier 2) | 1 | 1 | c_2(X) |
  | Y (carrier 2) | 3 | 4 | c_2(X) + 6 |

  Carrier 1 prefers A1 iff k_2 < 2. Carrier 2 prefers Y iff k_1 < 2. The best responses cycle (A1, X) → (A1, Y) → (B1, Y) → (B1, X) → (A1, X), so no pure equilibrium exists. In every profile one carrier must believe the rival's count is off by at least 1, so δ_0^E = 1/w_n. *Realization:* the c-values are attained through q via a q − b q², and the realization is to be numerically checked.
- (d) [proof known] δ_0^C ≤ δ̄ := max_i max_{ω, ω'} ‖ω − ω'‖_{∞, 1/w} < ∞ for E, M and ID. *Proof:* fix a rival belief ω° and set σ_i ∈ BR_i(ω°). At the resulting profile, ω° lies within δ̄ of every realised ω̂_{-i}. ∎
- (e) [proof known] ICNE_C(δ) = {σ : Φ_C(σ) ≤ δ}. The sets are nested (Lemma 3), and ICNE_E ⊆ ICNE_M ⊆ ICNE_ID. At δ = 0 with κ = 0, ICNE_E is the Nash set. As δ → ∞ it tends to ∏_i {σ : cell_i(σ) ≠ ∅}.

**Proposition 2 (weak NP-hardness of existence) [to prove].** Deciding δ_0^E = 0, which is existence of a pure equilibrium under D2 with N part of the input and binary-encoded quantities, is NP-hard. The planned route is a reduction from Partition that encodes the item weights in k and τ, following Dunkel and Schulz (2008). CTS decides it in pseudo-polynomial time. *Risk:* the gadget must respect the sign structure of A3.

### 4.3 Correctness and termination of CTS

**Theorem 2 (exact sweep) [proof known].** For C ∈ {E, M, R} under Lemma 5, and for ID through the merge, the CTS output (Section 5) satisfies:

- (i) for every δ ∈ [0, δ_max], the computed aggregate sets equal {A : ∃ σ ∈ ICNE_C(δ) with aggregate A};
- (ii) the computed W_min(δ) and W_max(δ) are exact;
- (iii) W_min and W_max are step functions with at most Σ_z Σ_i |O_iz| breakpoints;
- (iv) CTS terminates.

*Proof.*
- Thresholds are exact by Lemma 4.
- In a zone, fix the final aggregate A. This includes T_z under D2, where welfare needs it. Profiles with aggregate A correspond to sequences (σ_1, …, σ_N) with Σ σ_i = A. Carrier i's threshold depends only on (σ_i, A − σ_i), because A5 fixes ω̂ = A − σ_i.
- The label (θ, W) = (max_{j≤i} A_j, Σ_{j≤i} w_j) + Ω_z(A) extends monotonically: max and + are isotone. So pruning to the Pareto front in (θ↓, W↓), and separately in (θ↓, W↑), loses no completion that is optimal for any δ. This is the standard bicriteria DP exchange argument.
- The staircase min{W : θ ≤ δ} is then exact.
- Lemma 5 assembles the city: the sets are products, δ_0 = max_z δ_{0,z}, and W_min = Σ_z W_{min,z} because welfare is zone-additive.
- Every loop is over finite sets. ∎

**Theorem 3 (complexity and oracle calls) [proof known, except (c) to prove].**

- (a) *Surrogate (Stage 2).* Per zone the cost is O(N L log L + N |Λ_z| L log L + |Λ_z|² N L' F). Here L = max_i |O_iz|, Λ_z is the aggregate lattice, L' is the number of options that survive pruning (A^C ≤ δ_max), and F is the size of the Pareto front. Since F ≤ N L' and the bound is linear in Z, the zones run in parallel. No routing oracle is called after calibration. The E-thresholds use the precomputed cell polygon, and the distance query from a box to a convex polygon costs O(log L).
- (b) *Plan level (Stage 1).*
  - A^E by Kelley cutting planes on V_i terminates within |Σ_i| exact-oracle calls, where Σ_i is the set of distinct signatures. Each call either certifies or returns a signature that violates the current LP solution, so it is new.
  - A^M and R are fractional combinatorial problems, max or min of f(σ')/h_B(Δφ(σ')). Dinkelbach's method uses one oracle call per iteration, on the objective f − λ h_B with zone-separable |·| penalties (a loss-augmented oracle). It terminates finitely, with λ strictly monotone over a finite set.
  - With the ellipsoid method instead, A^E needs O(d² log(R/ε)) calls for ε-accuracy.
- (c) [to prove] For linear integer data, the Dinkelbach iteration count is O(p² log² p), where p is the number of binary plan variables. The route is to adapt Radzik (1992) after linearizing |·| with split variables.

### 4.4 The leader

**Theorem 4 (maximal-robustness LP; criterion-free implementation) [proof known].**

- (a) δ*(σ̂) is the optimal value of the LP

  max_{θ ∈ Θ, δ} δ s.t. N_i(σ̂_i, σ'; θ) − h_{K0}(Δφ) − δ h_B(Δφ) ≥ 0 for all i and all σ' ∈ O_i.

  The constraints are linear because N is affine in θ (Lemma 2) and K is Minkowski-linear in δ.
- (b) If 0 ≤ δ ≤ δ*, then at the optimal θ*, σ̂ ∈ ICNE_C(δ, θ*) for all four criteria. Moreover σ̂_i is optimal against every belief in M_i(δ).
- (c) At plan level, separation is the loss-augmented oracle max_{σ'} [U(σ'; p̂(θ)) + h_{K0}(φ̂ − φ(σ')) + δ h_B(φ̂ − φ(σ'))]. The cutting-plane method terminates within Σ_i |Σ_i| cuts.
- (d) With zone-specific instruments, the LP splits into Z LPs with 3 variables each. With city-uniform instruments it is a single LP with 3 variables and Σ_z N |O_z| constraints.

*Proof.*
- (a) follows from Lemma 4(R) and Lemma 1.
- (b): robust optimality gives U(σ̂; p) ≥ U(σ'; p) for every p ∈ K. That implies E-admissibility, maximality, absence of interval domination, and Γ-optimality, since min_p U(σ̂) ≥ min_p U(σ').
- (c) is finite-constraint cutting-plane LP.
- (d) follows from Lemma 5. ∎

### 4.5 Tightness and impossibility

**Theorem 5 (hardness of exact implementation at plan level) [proof known].** Deciding R_i(σ̂) ≥ 0, A_i^E(σ̂) = 0 or δ*(σ̂) ≥ 0 is coNP-hard, already for N = 1, κ = 0 and Θ = {θ_0}.
*Proof.* With K a single point, each question asks "is the given routing plan optimal?". For the TSP, which is a special case (one vehicle, q fixed, f = 0), tour-optimality verification is coNP-complete (Papadimitriou and Steiglitz). Each problem is a restriction of the general one. ∎
*Consequence:* CTS is exact only on the surrogate and on Stage-1 instances. Claim 8 gives certified brackets otherwise.

**Theorem 6 (one instrument is not enough; two are not always enough).** Take the continuous model in one zone under D1. Carrier i chooses q_i, with exposure τ_i(q_i) smooth, increasing and convex, its profit is strictly concave, and the efficient profile q* is interior.

- (a) [proof known] q* is a precise Nash equilibrium under uniform (s, t) iff s + t τ_i'(q_i*) = r_i for all i, where r_i := −b q_i* + γ c τ_i'(q_i*)(T* − τ_i*). Equivalently, the points (τ_i', r_i) are collinear.
  - With t ≥ 0 alone (s = 0), it is implementable iff r_i/τ_i' is the same nonnegative constant for every i. This fails whenever the Cournot wedge dominates, b q_i* > γ c τ_i' T_{-i}*.
  - With s alone, it is implementable iff r_i is the same for every i.
  - So for N = 2 and τ_1' ≠ τ_2', two instruments suffice and one fails generically. For N ≥ 3 even two fail generically.

  *Proof:* match carrier i's first-order condition P + P'q_i − s − C_i' − τ_i'(t + γ(μ + cT)) − γ c τ_i τ_i' = 0 with the efficiency condition P = C_i' + γ τ_i'(μ + 2cT). Strict concavity makes the first-order conditions sufficient. ∎
- (b) [proof known] In this continuous model, δ*(q*) ≤ 0 for every κ ≥ 0, with equality only if κ = 0. *Proof:* with one decision and two price coordinates, the set of p at which q_i* is optimal is the line given by the first-order condition, p_q + τ_i'(q_i*) p_τ = const. A line contains no box B of positive width. It contains the vertical segment K0 only if τ_i' = 0, which is excluded. ∎ **Indivisibility (integer k, the option grid) is what creates positive robustness.**
- (c) [proof known] In the discrete model, δ*(σ̂) ≤ min_i ρ_i, where ρ_i = sup{δ : some translate of K0 + δB lies inside cell_i(σ̂_i)} is the B-inradius. Equality holds for N = 1 with two instruments under an exposure charge, since θ translates freely in the plane (Lemma 2). With a single instrument the translation is restricted to one axis, and the inequality can be strict.

**Proposition 3 (query lower bound) [proof known].** At plan level, with access only to the best-response oracle, any deterministic algorithm that decides A^E(σ) ≤ δ to precision ε in a one-dimensional price family needs at least log₂(R/ε) queries. *Proof:* an adversary keeps the cell boundary consistent with both answers, as in binary search. ∎ The extension to Ω(d log(R/ε)) is [to prove].

### 4.6 Comparative statics in the imprecision width

**Theorem 7.**

- (a) [proof known] Q̲_z(δ) and n̲_z(δ) are nonincreasing in δ, and Q̄_z(δ) and n̄_z(δ) are nondecreasing. W_min is nonincreasing and W_max nondecreasing. PoA_C(δ) is nondecreasing and PoS_C(δ) nonincreasing. *Proof:* nesting (Lemma 3, Theorem 1(e)). ∎
- (b) [proof known] *Ambiguity acts as a tax (Γ, D1).* Let σ(δ) maximize Ψ_δ = Ψ_{μ̄} − δ L, where L(σ) = Σ_z (b_z w_Q Q_z + γ c_z w_n T_z), the Γ-potential of Theorem 1(b). Then L(σ(δ')) ≤ L(σ(δ)) for δ' > δ.
  *Proof:* add Ψ_δ(σ(δ)) ≥ Ψ_δ(σ(δ')) and Ψ_{δ'}(σ(δ')) ≥ Ψ_{δ'}(σ(δ)) to get (δ' − δ)(L(σ(δ)) − L(σ(δ'))) ≥ 0. ∎ Only the weighted aggregate L is monotone; Q and T separately need not be.
- (c) [proof known] *Closed form for the symmetric continuous benchmark* (τ = h q, D1, interior). Let β = b + γ c h² and ω = b w_Q + γ c h w_n. Then the set of ICNE_E aggregates is exactly

  [Q* − N(δ ω + γ h κ/2)/((N+1)β), Q* + N(δ ω + γ h κ/2)/((N+1)β)],

  and Γ selects the lower endpoint.
  *Proof:* E-admissible responses are q_i = (a' − β Q_{-i} + e_i)/(2β), with e_i ∈ [−δω − γhκ/2, δω + γhκ/2] free. Summing over i gives (N+1) β Q = N a' + Σ e_i, and every e in the box is attained. ∎
  *Prediction:* the interval width grows linearly in δ with slope 2Nω/((N+1)β), and steeper congestion (a larger β) shrinks it.

### 4.7 Robust PoA and PoS

**Lemma 6 (imprecise equilibria are approximate equilibria) [proof known].** Assume μ^true ∈ [μ̲, μ̄]. If σ ∈ ICNE_E(δ) ∪ ICNE_M(δ), then σ is an ε-Nash equilibrium of the true-mean game with

  ε_i ≤ κ γ D_i^τ + δ D_i^B, where D_i^τ = max_{σ'} Σ_z |Δτ_z| and D_i^B = max_{σ'} h_B(Δφ).

*Proof:* take the witness p ∈ K (E), or the pairwise witness p_{σ'} (M). Then U(σ'; p_t) − U(σ; p_t) ≤ ⟨Δφ, p − p_t⟩ ≤ h_{(K0 − γμ_t e_2) + δB}(Δφ). ∎

**Theorem 8 (robust PoA via smoothness transfer).**

- (a) [proof known, conditional] Suppose the true-mean game is (λ, μ)-smooth for welfare, that is, Σ_i U_i(σ*_i, σ_{-i}) ≥ λ W(σ*) − μ W(σ) for all σ. Suppose also that W ≥ Σ_i U_i, which holds when consumer surplus and charge revenue are nonnegative. Then for C ∈ {E, M},

  PoA_C(δ) ≤ (1 + μ) / (λ − E(δ)/W*), where E(δ) = Σ_i (κ γ D_i^τ + δ D_i^B).

  *Proof:* W(σ) ≥ Σ_i U_i(σ) ≥ Σ_i [U_i(σ*_i, σ_{-i}) − ε_i] ≥ λ W* − μ W(σ) − E(δ). ∎
- (b) [to prove] Smoothness constants for Regime A. The target is to combine linear-Cournot efficiency (Johari–Tsitsiklis: ratio ≥ 2/3 for convex costs) with affine congestion (Christodoulou–Koutsoupias) under arbitrary private routing costs. *Risk:* arbitrary private costs may destroy smoothness. The fallback is to report only the instance-exact PoA from Theorem 2.

**Theorem 9 (PoS bound via the potential, D1) [proof known].** Let σ^Ψ maximize Ψ_{μ̂}, with zero charges. Then for every δ ≥ 0, σ^Ψ ∈ ICNE_C(δ) for C ∈ {E, M, ID}, and

  W(σ^Ψ) ≥ W* − Σ_z [(b_z/2) Σ_i q*_iz² + (γ c_z/2)(1 − 1/N) T_z(σ^Ψ)²].

*Proof:*
1. Expand both functions: W − Ψ = Σ_z [(b/2) Σ_i q_i² − (γ c/2)(T² − Σ_i τ_i²)].
2. Using Σ_i τ_i² ≥ T²/N, W(σ^Ψ) ≥ Ψ(σ^Ψ) − Σ_z (γc/2)(1 − 1/N) T_Ψ².
3. Ψ(σ^Ψ) ≥ Ψ(σ*).
4. Ψ(σ*) = W* − Σ_z (b/2) Σ_i q*_i² + Σ_z (γc/2)(T*² − Σ_i τ*_i²) ≥ W* − Σ_z (b/2) Σ_i q*_i². ∎

### 4.8 Inexact oracles and the surrogate

**Theorem 10 (certified brackets) [proof known].** At plan level with a heuristic oracle:

- every cut comes from a real plan, so the computed A^E is a lower bound, the computed R is an upper bound, and "not maximal" is exact;
- with a relaxation bound Ū ≥ V (a column-generation lower bound on routing cost), the reverse bounds hold for ε-admissibility, where ε is the duality gap.

So each threshold is output as an interval [A_lo, A_hi(ε)].

**Proposition 4 (surrogate transfer) [proof known].** If |U^true − U^surrogate| ≤ η uniformly, then ICNE_C^true(δ) ⊆ ICNE_C^{surrogate, 2η}(δ), where 2η means 2η-admissibility, and conversely. *Proof:* an optimal option in one model is 2η-optimal in the other. ∎

---

## 5. Algorithm

```
CTS(cities, θ, C, δ_max):
 for each zone z (in parallel):
  for i: O_iz <- option grid from surrogate; cells_iz <- regular subdivision (2-D hull, Lemma 2)
  for A in Λ_z, i, σ ∈ O_iz with σ ≤ A:
      A_iz(σ,A) <- Lemma 4 formula for C at p̂(A−σ), K0, B;  prune if > δ_max
  for A in Λ_z:                                   # bottleneck–Pareto DP (Thm 2)
      F <- {(0, thr=0, W=0)}
      for i = 1..N: F <- ParetoFront{(S+σ, max(thr, A_iz(σ,A)), W+w_iz(σ))}
      Front_z(A) <- staircase δ ↦ (min W, max W) over labels with S = A, plus Ω_z(A)
 δ_0 <- max_z min_A minthr_z(A);  W_min(δ), W_max(δ) <- Σ_z merged staircases   (Lemma 5)
 return Front, δ_0, W_min, W_max, PoA_C(·), PoS_C(·)

LeaderLP(σ̂, Θ): solve LP of Thm 4 (explicit constraints in the surrogate;
                 loss-augmented cutting planes at plan level); return θ*, δ*;
                 then audit: CTS(θ*) gives the full ICNE set at θ* (strong-implementation check)
```

---

## 6. Not claimed, novelty and residual risk

**Not claimed:**
- novelty of the cell geometry (Baldwin–Klemperer tropical demand; stability radii, Chakravarti–Wagelmans 1998);
- novelty of loss-augmented cutting planes (structured max-margin learning) or of Dinkelbach's method;
- exactness outside Regime A (overtime penalties, multiplicative BPR, fleet caps across zones), where thresholds are approximated on a grid and fleet caps add a heuristic outer loop over shadow prices;
- strong implementation;
- smoothness constants (Theorem 8(b)).

**Plausibly new:**
1. Imprecise equilibrium families represented as sublevel sets of an admission threshold. This makes the δ-indexed PoA and PoS curves exactly computable. The closest work: ε-PoA for approximate equilibria (Christodoulou, Koutsoupias, Spirakis 2011), which perturbs utilities and gives worst-case bounds; and robust games with an uncertainty level (Crespi, Radi, Rocca 2025), which treats Γ only and has no algorithm.
2. Closed-form maximality and robustness thresholds over combinatorial option sets (Lemma 4), with Dinkelbach at plan level. Existing work on maximality uses pairwise LPs over explicit option lists (Troffaes; Nakharutai, Troffaes, Caiado 2019).
3. The existence threshold δ_0 as an exact instability index for non-potential congestion–Cournot games (Proposition 1).
4. A leader LP that maximizes belief-robustness uniformly over criteria, with the result that indivisibility is what creates robustness (Theorem 6(b, c)).
5. The zone-product theorem that makes items 1–4 exact for Z ≈ 250.

**Residual risk: medium.** The primitives are known. A referee may call items 1 and 4 "stability radius for games". The closest work to check in full text before submission:
- Emelichev et al. on stability radii of equilibria under ℓ∞ payoff perturbation (cooperative and multicriteria finite games);
- Cui, Yu, Pinson, Paccagnan (IJCAI 2025, the incenter in inverse game theory: robustness over utility parameters, not beliefs);
- Stauber (JET 2011, qualitative robustness to ambiguity, with no radius and no algorithm).

None of the searches found an admission threshold or robustness radius over credal sets, or δ-indexed PoA curves.

---

## 7. Empirical program on the six metro maps

**Instances.** New Delhi (120 zones), Cairo (42), Moscow (160), Buenos Aires (208), New York (234) and Mumbai (143). The inputs are the processed files in data/processed/<city>/.

**Data.**
- `zones.csv`: GHSL 2025 population, area and `lane_km_major`.
- `travel_time_matrix.npy`: free-flow zone-to-zone travel times.
- `pois.csv` and `depot_score`: OSM warehouses and industrial land for depots, and shops for B2B demand.

**Calibration (documented in data/README with source URLs).**
- *Parcel volumes:* web-sourced national parcels per capita per year (postal regulators, parcel-shipping indices), scaled by zone population plus a shop-density term. Carrier market shares come from web-sourced reports. N = 3–5 carriers, with depots at the zones of highest depot_score.
- *Demand slope b_z:* from a web-sourced delivery price and an elasticity range. The elasticity range is a sensitivity axis.
- *Traffic:* web-sourced city congestion indices (average and peak extra travel time) fix the level of ξ and the slope c_z. The constant c_z ∝ 1/lane_km_major is calibrated so that the delay at baseline volume matches the index. Daily ξ samples come from the published peak/off-peak spread. The p-box comes from DKW at n days, and κ is reported.
- *BHH surrogate:* L_iz(q, k) = 2 r̄_iz k + α_z √(A_z q). α_z is fitted by sampling q ∈ {5, …, 120} customers from the GHSL cells and shop points of each zone and solving the CVRPs (the in-repo heuristic, checked with HGS/PyVRP). The held-out error gives η (Proposition 4).

**Stage 1 (N = 2–3, Z = 2, |S_i| ≤ 7, plan level).** Brute force over all plans, all profiles and a dense belief grid. This assigns [numerically checked] to Lemmas 1–5, Theorems 1, 2 and 4, Proposition 1's realization, the Theorem 10 brackets and Theorem 5's instances (optimality-verification cost).

**Stage 2 and Stage 3.** Surrogate CTS on all six cities, with δ from 0 to δ̄, κ from DKW, D1 and D2, and one or two instruments, zone-specific or city-uniform.

**Theorem-to-experiment map**

| Claim | Prediction | Measurement |
|---|---|---|
| Lemma 1, Lemma 4 | Box thresholds equal brute force over beliefs | Maximum absolute error on Stage 1 (must be 0) |
| Lemma 5, Thm 2 | City sweep equals the product of zone sweeps; staircases are exact | Stage 1 enumeration against the DP; Stage 2 consistency for random zone pairs computed jointly |
| Thm 3(a) | Wall time linear in Z; zero oracle calls after calibration | Time against Z across the six cities; calibration CVRP counts |
| Thm 3(b), Thm 4(c), Prop 3 | Oracle calls ≤ number of signatures; logarithmic in 1/ε | Calls for Kelley, Dinkelbach and ellipsoid against CCI's 4^Z vertex queries and against ALEH rerun on a δ-grid |
| Thm 1(a, b) | ICNE ≠ ∅ under D1 for all δ | Fraction of zones with δ_0 = 0 under D1 (must be 1) |
| Thm 1(c), Prop 1–2 | δ_0 > 0 occurs under D2 | Distribution of δ_0 over zones; frequency of fleet arms races; DP time as N grows |
| Thm 5, Thm 10 | Exact plan-level certification is hard; brackets are valid | Widths of [A_lo, A_hi] against the duality gap; whether exact values fall inside the brackets |
| Thm 6(a) | One instrument fails when the Cournot wedge dominates; two fail when (τ', r) are not collinear | δ* and the welfare gap for t only, s only and (s, t); collinearity residual against N |
| Thm 6(b, c) | Robustness comes from indivisibility; δ* ≤ inradius, with equality when one carrier has two instruments | δ* against the vehicle grid (k integer against a finer grid); the δ*/ρ ratio; zone-specific against city-uniform |
| Thm 7(a) | Intervals and PoA monotone in δ | Curves of [Q̲, Q̄], [n̲, n̄] and PoA/PoS against δ for E, M and ID |
| Thm 7(b) | The Γ-weighted aggregate L falls with δ | L(σ^Γ(δ)) per city |
| Thm 7(c) | Interval slope ≈ 2Nω/((N+1)β) | Regression of the surrogate interval width on δ, compared with the formula, per zone |
| Lemma 6, Thm 8–9 | PoA(δ) ≤ the bound; PoS ≤ the potential bound | Instance-exact PoA/PoS from CTS against the bounds; slack against δ and κ |
| Prop 4 | Equilibrium sets agree up to 2η | Stage-1-sized zone samples solved at plan level against the surrogate |
| Fairness | Burden and robustness differ by zone | Population-weighted Gini of welfare loss, charges and δ*; lowest decile of zones |
| Out of sample | Realised aggregates fall inside the intervals at level 1 − β | Coverage over held-out ξ days |

## Sources checked for novelty

- Bhaskar et al.: https://ar5iv.arxiv.org/html/1408.1429
- Cut-and-Play: https://arxiv.org/html/2111.05726v4
- ZERO Regrets: https://arxiv.org/pdf/2111.06382
- Inverse game theory, incenter (IJCAI 2025): https://object.cloud.sdsc.edu/v1/AUTH_da4962d3368042ac8337e2dfdd3e7bf3/ml-papers-txt/IJCAI/2025/inverse_game_theory_an_incenterbased_approach__789ce6aa.txt
- Bertsimas, Gupta, Paschalidis: https://dspace.mit.edu/entities/publication/1d178a99-3b41-4fab-9a65-daf33cc260a8
- Suboptimality loss: https://arxiv.org/pdf/2609.23200
- Emelichev et al.: https://www.mathnet.ru/eng/basm105 ; https://www.mathnet.ru/eng/dm1045
- Chakravarti, Wagelmans: https://repub.eur.nl/pub/1403
- Berthold, Heller, Seidel: https://arxiv.org/pdf/2105.09588
- Ghobadi et al., robust inverse optimization: https://uwspace.uwaterloo.ca/items/4df4d472-dc03-4a4a-9083-cdd8b2e9a90e
- Stauber: https://ideas.repec.org/a/eee/jetheo/v146y2011i1p248-274.html
- Crespi, Radi, Rocca: https://arxiv.org/pdf/2002.00225
- Christodoulou, Koutsoupias, Spirakis: https://arxiv.org/pdf/0804.3160
- Liu: https://studiesinlogic.sysu.edu.cn/en/node/112
- Nakharutai, Troffaes, Caiado: https://arxiv.org/pdf/1906.12215
- Troffaes, finite approximations: https://ar5iv.labs.arxiv.org/html/1203.0919
- Monaco, Sabarwal: https://kuwpaper.ku.edu/2014Papers/201403.pdf
- Roy, Sabarwal: https://papers.ssrn.com/abstract=3683187
- Strategic heterogeneity: https://ideas.repec.org/a/spr/joecth/v67y2019i3d10.1007_s00199-017-1092-6.html
- Mixed-monotone decomposition: https://arxiv.org/pdf/2103.08638 ; https://coogan.ece.gatech.edu/papers/abate2021interconnected.html
- Baldwin, Klemperer: https://www.nuff.ox.ac.uk/economics/papers/2015/demandtypesrevised2016.pdf
- Echenique, revealed preference: https://eml.berkeley.edu/~fechenique/published/chapterRP.pdf
- Gan et al., robust Stackelberg equilibrium: https://par.nsf.gov/servlets/purl/10466723
- Structured Stackelberg learning: https://arxiv.org/abs/2504.09006v1
- Monderer, Tennenholtz: https://arxiv.org/pdf/1107.0022
- Chiu, Ferguson: https://arxiv.org/html/2505.11791v1
- Robust Wardrop tolls: https://optimization-online.org/2024/07/a-toll-setting-problem-with-robust-wardrop-equilibrium-conditions-under-budgeted-uncertainty/
- Continuous approximation review: https://researchportal.bath.ac.uk/en/publications/continuous-approximation-models-in-freight-distribution-managemen/
- Ghosal, Wiesemann: https://optimization-online.org/2018/08/6759/
- Boff, Werlang: https://repositorio.fgv.br/items/7223d034-3b2c-40e2-ad8b-3d52944acfaf
