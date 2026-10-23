# Verification plan

There are two parts. Part A is an exact brute-force check of every theorem on tiny instances. Part B is a set of empirical hypotheses, derived from the theorems, for the nine city maps. Theorem numbers refer to `theory/main.tex`.

The script `theory/brute_force_checks.py` already implements tests A1, A2 (deterministic part), A6, A9, A10 and A11. Its output on 2026-10-23 had no violations (see the docstring). The other tests are specified here to be implemented.

## Conventions for Part A

- Exact arithmetic where it is cheap: `fractions.Fraction` for the examples and the kernel games, and LP solved with HiGHS (`scipy.optimize.linprog`, `method="highs"`) for random instances. Tolerance: `tol = 1e-7 · (1 + max|data|)` for LP-derived quantities. Every inequality "X ≤ Y" is checked as `X ≤ Y + tol`.
- Exact ground truth for δ-thresholds is computed per profile and player by the LP (eq. EthrLP), with variables (m, ξ, δ), clipping `m ≥ 0`, and the traffic box as bounds. Ground truth for maximality, ID and Γ uses the closed-form corner formulas for linear functions on boxes.
- `δ_0^C` is computed by enumerating all pure profiles (feasible because ∏|P_i| ≤ 4^4 = 256).

**Generator G(N, d, P, regime, seed).** Draw:
- `a_i(p) ∈ {0,…,S}^d` with `S = 3`;
- `φ_i(p) = a_i(p)` (D1) or independent in `{0,…,S}^d` (D2);
- `t_i(p) ∈ {0,…,2}^Z`;
- `π_i(p) ~ U[0,10]`;
- `M_k ~ U[0.5,1.5]`, `w_k ~ U[0.5,2]`;
- traffic box `[μ̂ − κ/2, μ̂ + κ/2]` with `κ ∈ {0, 0.5}`.

The ranges are N ∈ {2,3,4}, Z ∈ {1,2} (so d = 2Z ∈ {2,4}), and |P_i| ∈ {2,3,4}. Use 500 seeds per cell. A degenerate variant uses all-integer data to create ties.

**Generator CC (Cournot–congestion realisation).** Each carrier has 2–4 plans. A plan is a per-zone triple (q, n, τ) taken from a small grid (q ∈ {0, 10, 20}, n ∈ {0,1,2}, τ = n·U[2,8]), with routing cost `C_i(p) = f·n + v·τ`. Price and congestion parameters are scaled to the city calibration (Part B). This checks that the theorems hold on data shaped like the application, not only on random bilinear games.

## Part A: tests per statement

| Test | Statement | Quantity checked | Pass condition |
|---|---|---|---|
| A1 | Lemma 3.3 (reduction) | For random laws P (finite mixtures of 5 Dirac points with random means in the box), `E_P u_i(p)` against `ū_i(p; E_P m, E_P ξ)` | abs. error ≤ 1e-9 |
| A2 | Lemma 3.4, Lemma 3.5 | Sets Adm_E ⊆ Adm_M ⊆ Adm_ID and Adm_Γ ⊆ Adm_M per player, and `ICNE_C(δ) ⊆ ICNE_C(δ')` on a grid of 50 widths, for all profiles | set inclusion exact |
| A3 | Example 3.7 | `ICNE_Γ(0) = {A}` and `ICNE_Γ(2) = {B}` | exact (Fractions) |
| A4 | Lemma 3.6 | For random mixtures x: `min_k Σ x_p ū(p;k)` against `Σ x_p ū(p;k⁺)` when φ, t ≥ 0. Also, with signed φ, that the concavity gap is ≥ 0 | error ≤ 1e-9; gap ≥ −1e-9 |
| A5 | Prop. 5.2 | Mixed equilibria from support enumeration (N = 2) or from a polynomial-system solver (N = 3, `|P_i|` ≤ 3): `E_x[u_i(p, σ_{-i})]` against `ū_i(p; Ā_{-i}(x))`; support ⊆ B_i | error ≤ 1e-9 |
| A6 | **Thm 6.1(a)–(c)** | For every mixed NE x* (N = 2: all equilibria by support enumeration; N = 3: those found by the solver): (i) every p ∈ ∏B_j satisfies `max_i A_i^E(p) ≤ δ̂(p)`; (ii) `δ_0^E ≤ min_p δ̂(p) ≤` each of the three bounds; (iii) `δ_0^{ID} ≤ δ_0^M ≤ δ_0^E` | all inequalities within tol; 0 violations over ≥ 10⁴ equilibria |
| A7 | Thm 6.1(b), Hoeffding term | For N ∈ {10, 30, 100} (synthetic x*, B_j = supp): 1000 draws of the J-rounding. Record the empirical success frequency of `‖E‖_{w,∞} ≤ t` against `1 − 2d·exp(−2t²/(kσ̄²))` | empirical ≥ bound − 3·SE |
| A8 | Cor. 6.2 | For the rounded p and μ^t at the corners of Ξ: exact regret `max_{p'} ū_i(p') − ū_i(p_i)` against `δ̂ L_i + γ Σ κ_z T_iz` | regret ≤ bound |
| A9 | **Prop. 7.1** | `δ_0^E = δ_0^M = 1/w` for w ∈ {0.5, 1, 2}; no PNE; the unique mixed NE is (½, ½); `(N−1)ρ̄ = 1/w` | exact (Fractions) |
| A10 | **Prop. 7.2** | Z = 1…6: `min_profiles max_i ε_i = 3⌈Z/2⌉` and `δ̂·L_i ≤ 3Z` | exact |
| A11 | **Thm 7.3** | All digraphs on n ≤ 5 vertices (all labelled digraphs for n ≤ 4; 2000 random for n = 5, 6). For δ ∈ {0, 0.999/(2Δ⁺+1)} and C ∈ {E, M, ID, Γ}: `ICNE_C(δ)` = the set of kernels. Also check that for δ = 1.5/(2Δ⁺+1) the equality can fail, to show the threshold is not vacuous | exact set equality |
| A12 | Cor. 7.4 | On the A11 digraphs without a kernel: `δ_0^E ≥ 1/(2Δ⁺+1)` | exact |
| A13 | Prop. 7.5 | D1 instances: `Ψ` difference equals utility difference for all unilateral deviations; argmax Ψ ∈ ICNE_E(0) | error ≤ 1e-9 |
| A14 | Prop. 7.6 | Random bimatrix games 3×3: the embedded D2 game has payoffs equal to (R, C), and its mixed NE set equals the bimatrix NE set | exact |
| A15 | **Thm 8.1** | D1, N ∈ {2,3,4}: FW until g ≤ 1e-6; sparsify LP; conditional-expectation rounding. Check (a) `max_σ Ψ ≤ Ψ̄(x) + g(x)`; (c) `|J| ≤ min(N, d_L)` and `Ψ̄(x') ≥ Ψ̄(x)`; (d) `Ψ(p) ≥ Ψ̄(x') − ½ΣV_j`; (e) exact max regret ≤ η_cert; (g) the same on `G^Γ_δ` for δ ∈ {0.5, 1}, with Γ-regret computed from the lower values | all within tol |
| A16 | Thm 8.2 | Iterations to reach g ≤ η against `⌈6.75 (ΣD_i)²/η⌉` | iterations ≤ bound |
| A17 | Prop. 8.3, Thm 8.5 | Double oracle from singleton restricted sets: terminates with a mixed NE (checked against support enumeration). Cutting-plane E-threshold equals the explicit LP threshold; number of cuts ≤ |P_i| | exact / 1e-7 |
| A18 | Cor. 8.6 | With caps C_k set at the relaxed aggregate: `A_k(p) − C_k ≤ Σ_{j∈J} s_jk` | exact |
| A19 | Prop. 9.1 | `W_min`, `W_max`, `A_k`-extremes monotone in δ on a 200-point grid; number of breakpoints ≤ ∏|P_i| | exact |
| A20 | **Prop. 9.3** | Continuous symmetric benchmark. Compute the ICNE_E aggregate set by brute force: discretise e ∈ [−ℰ, ℰ]^N on a 21^N grid (N ≤ 3), and separately verify the endpoints by solving the FOC system. Compare with the closed form. Check the derivative sign rule on 1000 random parameter draws by finite differences. Include draws violating `a'' > (2N−1)ℰ` to show what fails | endpoints within 1e-9; sign rule 100% on valid draws |
| A21 | Lemma 10.1 | For all ICNE_C(δ) profiles: exact regret at μ^t against the stated bound, for C ∈ {E, M, ID} | regret ≤ bound |
| A22 | Prop. 10.3 | Generator CC under D1 with zero charges and μ^t = μ̂: `W(σ^Ψ) ≥ W* − B(σ^Ψ)` by enumeration; also for the RSRC output with η_cert | exact within tol |

Bolded tests (A6, A9, A10, A11, A15, A20) cover the headline claims. A failure in any of them blocks the corresponding statement. The proof would then have to be repaired before any empirical use.

## Part B: empirical hypotheses on the nine maps

### Data and instance construction

- Maps: Berlin (593 zones), Bombay/Mumbai (143), Buenos Aires (208), Cairo (42), London (348), Moscow (160), New Delhi (120), New York (234), Paris (198). Inputs are `data/processed/<city>/zones.csv` (pop, lane_km_major, n_shop, n_depot, depot_score) and `travel_time_matrix.npy` (seconds; median off-diagonal 21–35 min).
- Calibration rows exist in `data/parameters/city_parameters_wide.csv` for only six cities. Berlin, London and Paris have none. For these three, use the New York (London, Paris) or Moscow (Berlin) row as a labelled proxy, and report them separately as "uncalibrated".
- Demand: zone parcels/day = `pop_z × parcels_per_capita_per_day`, with an optional shop-density term ∝ `n_shop`. For example, New York gives about 2.2 M parcels/day, or about 9,500 per zone; New Delhi about 240 k/day, or about 2,000 per zone. Use N = `n_major_carriers` (4 or 5) with market shares from the calibration notes.
- Congestion: `c_z ∝ 1/lane_km_major_z`. Zones with `lane_km_major = 0` (Berlin 30, Mumbai 8, Buenos Aires 9, New York 5, Moscow 2) are merged into the nearest zone by travel time. Calibrate γc_z so that the baseline delay matches the TomTom index. The traffic box Ξ comes from the published peak/off-peak spread (κ), as in v4.
- Plan sets (the oracle): a carrier's plan is a per-zone option (q, n, τ) under a fleet cap Σ_z n_iz ≤ K_i, which keeps the plan set nonconvex and coupled across zones. Per-zone options come from the BHH surrogate `τ = 2 r̄ n + α_z √(area_z q)` on the drops/vehicle grid. Plan-level validation subsamples zones and solves the actual CVRPs (in-repo heuristic, PyVRP check).
  - The pricing oracle with zone prices (and, under D1, the concave quadratic term) is then a multiple-choice knapsack over zones. It is solved exactly by DP over the fleet budget, so `O_i` is exact on the surrogate.
  - The relaxation bound `U_i` is the LP relaxation of the knapsack (surrogate), or the column-generation bound (plan level).
- Weights: `w_k` is the city median of the rival aggregate in coordinate k. δ is therefore a *relative* imprecision of rivals' delivery and vehicle counts.

### Hypotheses

Each hypothesis states the theorem that predicts it, the measurement, and what would refute it.

**H1. Credal absorption radius is small relative to aggregates (Thm 6.1, D2).** Under D2, RSRC gives `δ_cert ≤ δ̂ ≤ (N−1)ρ̄`. Prediction: `δ_cert ≤ (N−1)·σ_max` in 100% of instances, and the median `δ_cert` is below 0.1, i.e. a 10% relative imprecision suffices for a pure E-admissible equilibrium. The order of magnitude comes from a vehicle spread of 1–3 per carrier-zone against rival totals of 40–100.
- Measurement: per city, the distribution of `δ_cert`, `δ̂` and the three bounds; the ratios `δ_cert/δ̂` and `δ̂/bound`.
- Practical caveat: for N ≥ 3 and many columns, an exact mixed NE of the restricted game may be out of reach (Prop. 7.6). Then use an ε-well-supported equilibrium (Remark 6.4), and report ε together with the bound. `δ_cert` from the LP (Thm 8.5) is exact for whatever profile is returned. Only the comparison with the a priori bound needs an exact x*.
- Refutation: any `δ_cert > δ̂`, which would be a bug or a theorem error.

**H2. Independence of N in the many-player regime (Thm 6.1(b)–(c)).** Split each carrier into m independent sub-fleets (m ∈ {1, 2, 5, 10, 50, 200}), so N' = mN ranges from 4 to about 1,000 couriers, with fixed d = 2Z. Per-courier spreads shrink with m. To isolate the N-effect, also run a second protocol that keeps per-courier spreads fixed by replicating couriers.
- Prediction: under fixed spreads, `δ_cert` plateaus once N' > d_L. The support-selection term grows linearly in N' while the Shapley–Folkman and Hoeffding terms stay flat. The crossover is at N' ≈ d_L (expected near 2Z, i.e. 84–1,186 by city).
- Measurement: `δ_cert` and |J| against N'. Check `|J| ≤ d_L`.
- Refutation: growth of `δ_cert` with N' beyond d_L under fixed spreads.

**H3. ε-Nash of the precise game (Cor. 6.2, Lemma 10.1).** Prediction: the measured exploitability (exact on the surrogate) satisfies `ε_i ≤ δ̂ L_i + γ Σ κ_z T_iz`. The ratio measured/bound is reported. On real data a ratio of 0.05–0.3 is expected, because the bound uses the worst-case alignment of rounding errors with exposure differences.
- Refutation: ratio > 1.

**H4. Complexity split D1/D2 (Prop. 7.5, Thm 7.3).**
- Under D1, RSRC returns η_cert, and exact enumeration on 2-zone subgames always finds a PNE (δ_0 = 0). Under D2, the same subgames (2–3 zones, explicit option menus, N = 4–5) show a positive fraction with δ_0 > 0.
- Measurement: the frequency of δ_0 > 0 by city under D2, its relation to vehicle-grid coarseness, and the wall time of the exact existence check as N grows. Exponential growth is consistent with, but does not prove, NP-hardness.
- Refutation: δ_0 > 0 under D1, which would be a bug.

**H5. Oracle calls (Thm 8.2).** Under D1, the number of FW oracle calls to reach `g ≤ ½ min(N,d) R²` is at most `N⌈6.75 (ΣD_i)²/η⌉`, and in practice far fewer.
- Measurement: calls against Z (across cities), against N (sub-fleet splitting), and the ratio to the bound. Compare with CTS's grid-over-δ re-solves and with best-response dynamics.
- Refutation: more calls than the bound with an exact oracle.

**H6. Certified potential gap and PoS (Thm 8.1, Prop. 10.3).**
- Prediction: `η_cert / |Ψ|` < 1% on the surrogate, and `W(p) ≥ W* − B − η_cert`, where W* comes from a centralised MIP on small instances and from an upper bound (the relaxation) on full cities. Also report the relaxation gap `Ψ̄* − Ψ(p)` against `½ΣV_j`.
- Refutation: `W(p) < W* − B − η_cert` on instances with exact W*.

**H7. Comparative statics in δ (Prop. 9.1, 9.3).**
- Prediction: the curves `[Q_min, Q_max](δ)`, `[X_min, X_max](δ)`, PoA_C(δ) and PoS_C(δ) are monotone for E, M and ID, and Γ curves can be non-monotone.
- On symmetric surrogate zones, the width slope matches `2Nℰ/((N+1)β)`, and stronger congestion widens the interval iff `δ b (w_n − h w_Q) > γ h² κ/2`. Test the sign rule across zones by regression of width on c_z with the sign of `δ b (w_n − h w_Q) − γh²κ/2` as moderator.
- Refutation: a sign mismatch on zones satisfying the interiority hypothesis.

**H8. Certificate tightness with heuristic oracles (Thm 8.5).** At plan level (CVRP heuristic plus column-generation bound), the exploitability bracket `[heuristic regret, UB regret]` has width ≤ the routing duality gap.
- Measurement: bracket widths against the gap; how often the exact value (small instances) falls inside the bracket, which must be 100%.

**H9. Imprecision substitutes for convexity, out of sample.** Draw held-out traffic days. The realised aggregates when carriers follow the RSRC profile fall inside the δ_cert-box of beliefs at the stated frequency, and E-admissibility of the plan persists for days with `μ^t ∈ Ξ`.
- Measurement: coverage and regret distribution.

### Reporting

- For every hypothesis: one table per city (calibrated six first, proxies separately), the distribution over seeds and instances, and the exact theorem bound alongside the measurement.
- A hypothesis is reported as *supported* only if no refutation event occurs. Ratio-type predictions (H1 median, H3 ratio, H6 percentage) are exploratory and labelled as such.
