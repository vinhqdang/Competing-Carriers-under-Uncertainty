# Machine-checked core (Lean 4 + Mathlib)

Build: `cd lean && lake build CCU` (toolchain `leanprover/lean4:v4.36.0-rc1`, Mathlib pinned in
`lake-manifest.json`). No file imported by `CCU.lean` contains `sorry`. `#print axioms` on every
theorem listed below reports only `propext`, `Classical.choice`, `Quot.sound` (or no axiom).
A cold first build takes about 8 minutes (Mathlib loads from disk); the project itself builds in
about 1 minute once Mathlib is cached.

"Full" means the paper's statement for arbitrary finite index sets, over `ℝ`. "Core" means a finite or
algebraic part of the paper's theorem; the missing part is stated in the last column.

## `CCU/LeanTargets.lean` (earlier work)

| Paper | Lean name | Status |
|---|---|---|
| main.tex Lemma 3.4 (E ⊆ M), Lemma 3.5 | `eAdm_imp_maxAdm`, `inBox_mono`, `icneE_mono` | full (E vs maximal, monotone in width) |
| main.tex Thm 6.1(a) | `absorption` | core (pure-profile absorption step) |
| main.tex Thm 4.1 | `shapleyFolkman` | full (finite sets) |
| main.tex Prop 7.5 | `potential_identity` | full (exact potential, D1) |
| main.tex Thm 7.3 | `pne_iff_kernel` | core (kernel equivalence; no NP-hardness) |
| main.tex Prop 7.1, 7.2 | `tight_example_lower`, `cycle_product_lower` | core (counting/lower-bound arithmetic) |

## `CCU/DIP.lean` (theory/new_algorithm_C)

| Paper | Lean name (`CCU.DIP.`) | Statement | Status |
|---|---|---|---|
| Prop 1(a) | `instr_a` | `Σ_z (s_z q_z + t_z (r q_z)) = ⟨u,q⟩`, `u = s + r t` | full |
| Prop 1(b) | `instr_b` | uniform `s = min_{Z₊} u`, `t_z = (u_z - s)/r ≥ 0` realise any `u` | full |
| Lemma 2 | `potential_welfare_identity` | `Φ_u = SC − Σ κ/2 (Q−Q°)² + L + ⟨v,Q⟩ + Σ κ/2 Q°²` for lumpy lots, finite `ι`, `Z`, `u = κQ° − (m/2)d̄ + v` | full |
| Lemma 2 (v = 0) | `potential_welfare_tangent` | tangent-charge form | full |
| Sec. 3 (convexified identity) | `potential_welfare_identity_convexified` | same identity for `Φ̄_u`, `SC̄`, no lumpiness needed | full |
| Thm 5 (`thm:convex`) | `exact_implementation_symmetric` | symmetric lots: `x*` (minimiser of `SC̄` on a convex set `C`) minimises `Φ̄_u` for `u = κQ̄* − (m/2)d̄`, and every minimiser has aggregate `Q̄*` and cost `SC̄(x*)` | full, over an abstract convex set `C` of a real vector space with linear delivery maps (the paper's `∏ Δ(𝒫_i)` is an instance); needs `b>0`, `g≥0` |
| Thm 7(a) (`thm:cut`) | `mem_poly_iff`, `sat_iff`, `separation` | `u ∈ P(σ*)` iff `σ*` is a pure equilibrium under `u`; a best response `b_i` separates and is the most violated constraint | full (without the box `𝒰`) |
| Thm 7(b) | `cuts_injective`, `rounds_le_card`, `card_nontrivial` | cuts are pairwise distinct, so at most `Σ_i (|𝒫_i|−1)` rounds add a cut | core (counting). Not formalised: the LP step, the ε-shrunken polyhedron, 7(c) (classical centre-of-gravity bound) |

Not formalised from DIP: Thm 6 (asymmetric lots, `thm:asym`, the `(1+ρ)E` bound), Props `pers`, `opt`,
`credal`, the existence of equilibria.

## `CCU/MarginalTariff.lean` (theory/new_algorithm_D, Thm 9 `thm:mct`)

| Part | Lean name (`CCU.MT.`) | Status |
|---|---|---|
| (a) `J^T_i = SC(p,σ_{-i}) − SC(∅_i,σ_{-i})`, SC exact potential | `tariff_cost_eq_social`, `tariff_exact_potential` | full |
| (b) NE = unilateral social optima; every social optimum is NE (PoS 1) | `isNE_iff`, `socialOpt_isNE` | full |
| (b) improvement dynamics lower SC, cannot cycle, reach an equilibrium | `step_lowers_SC`, `no_infinite_improvement`, `reaches_NE` | full for improvement steps (best-response steps are a special case) |
| (c) cost linear in own deliveries | `tariff_cost_linear` | full |
| (d) tariff identity and revenue formula | `tariff_eq_flat`, `tariff_revenue` | full |

Adaptations: `SC` uses D's form with `m^S = b + 2κ` (equal to C's `b/2 Q² + g X²` with `κ = g r²`;
the equivalence is the `hX` step in `DIP.potential_welfare_identity`). The empty plan `∅_i` need not lie in
`𝒫_i`, so (a) compares with the hypothetical contribution `(Σ_{j≠i}R_j, Q_{-i})`.

## `CCU/ARP.lean` (theory/new_algorithm_D, Thm 1 and Thm 3)

| Paper | Lean name (`CCU.ARP.`) | Status |
|---|---|---|
| Thm 1, inequality (lip) | `strong_convex_growth`, `strongMono_of_strongConvex`, `lip_of_strongMono` | core: for `F − ½‖·‖²_m` convex on a convex set, the argmin response satisfies `⟨u₂−u₁,Q₁−Q₂⟩ ≥ ‖Q₁−Q₂‖²_m` and `‖Q₁−Q₂‖²_m ≤ ‖u₁−u₂‖²_{m⁻¹}`. Not formalised: conjugate `F*`, differentiability, `Q(u) = ∇F*(−u)`, the prox form |
| Thm 3(a) plain step | `plain_contraction_sq`, `plain_contraction`, `plain_rounds` | full from the strong-monotonicity hypothesis `StrongMono` (any `Z`, non-diagonal): ratio `ρ` in the `κ⁻¹`-norm, and `ρ^t` after `t` rounds |
| Thm 3(b) damped step | `damped_contraction_sq`, `damped_contraction`, `damped_factor_le`, `damped_contraction_paper`, `damped_ratio_opt`, `damped_rounds` | full from `StrongMono`: ratio `(1−θ)` for `0<θ≤2/(2+ρ)`, which is ≤ the paper's `√(1−2θ(1+ρ)/(2+ρ))` (`damped_contraction_paper`); at `θ=2/(2+ρ)` ratio `ρ/(2+ρ)` |
| Thm 3, aggregate claim | `aggregate_bound` | full (squared form, `‖ΔQ‖²_m ≤ ρ‖Δu‖²_{κ⁻¹}`) |

Adaptations: the contraction theorems take the response map `Q` as an abstract function satisfying
`StrongMono` (which `strongMono_of_strongConvex` derives from Thm 1's hypotheses) instead of the polytope
construction of `F`. The rate for the damped step proved here, `1−θ`, is sharper than the paper's and
implies it. The fixed point `u*` is a hypothesis (`Tmap u* = u*`); existence and the dual
characterisation (Thm 2) are not formalised.

## `CCU/BRL.lean` (theory/new_algorithm_B)

| Paper | Lean name (`CCU.BRL.`) | Status |
|---|---|---|
| Thm 1 eq. (budget) + Cor `cor:grid` | `stopLoss_le_splitCost`, `exists_split`, `budget_identity`, `upper_prevision_grid` | core: finite level grid, arcs `a`, nondecreasing values `x_{a,l}`, weights `w_l ≥ 0`; `Σ_l w_l(Σ_a x_{a,l}−θ)⁺ = min_{Σ d ≤ θ} Σ_a Σ_l w_l (x_{a,l}−d_a)⁺`, minimum attained; and the `c₀+γT+ρ(T−θ)⁺` form. Not formalised: p-boxes, upper previsions as suprema over credal sets, quantile functions, integrality (Step 5) |
| Lemma `lem:infconv` | `infconv_split` | full for arbitrary arc costs whose partial minima are attained: budget split between two partial paths is `min_D f₁(D)+f₂(θ−D)` |
| Lemma `lem:window` | `completion_window`, `completion_window'` | core: abstract slope conditions on `f_p`, `f_q` (slope ≥ −ρ, constant above `S_p(1)`, slope `−ρ` below `S_q(0⁺)`, `f_q` nonincreasing), minimiser may be taken `≤ min{S_p(1), θ−C_min}`. The conditions are hypotheses, not derived from the grid definition of `f_p` |
| Thm `thm:fdom` | `dominance_below_window`, `functional_dominance_valid` | core, same abstract hypotheses: functional dominance on `J(p₂)` implies `v₁−π₁ ≤ v₂−π₂` |
| Prop `prop:compare`(a), (c) | `fcost_mono`, `quantile_dominance_g_nonpos`, `compare_example_one`, `compare_example_one_not_vector`, `compare_example_two` | (a) full; (c) both numerical counter-examples |

## `CCU/Radius.lean` (theory/main.tex Thm 6.1(b),(c))

| Paper | Lean name (`CCU.Radius.`) | Status |
|---|---|---|
| (b) first term | `first_term` | core, per coordinate: `|A_{-i}−Ā*_{-i}| ≤ Σ_{j≠i} r_j` |
| (c) the `N−1` term | `first_term_card`, `first_term_uniform` | `Σ_{j≠i} r_j ≤ (N−1)σ` |
| (b) decomposition (eq:decomp) | `decomp` | full, per coordinate |
| (b) second term (T8) | `second_term`, `second_term_uniform`, `abs_sub_le_spread` | core: `≤ Σ_{j∈J} s_j + r_i ≤ k♯σ̄ + ρ̄` given the rounding data (`|J| ≤ k♯`). The support bound `|J| ≤ d_L` is `shapleyFolkman` (LeanTargets); the LP vertex is not formalised |

Not formalised: the Hoeffding third term, the construction by linear programming, `min{...}` over the three
bounds.

## Helper

`CCU/SegmentLimit.lean`: `nonneg_of_forall_small` (a quadratic `tA + t²B ≥ 0` on `(0,1]` has `A ≥ 0`).
