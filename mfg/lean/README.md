# Lean 4 cores of the mean-field paper

Separate Lake project that reuses the Mathlib checkout and build of `lean/` (`packagesDir = "../../lean/.lake/packages"`,
same toolchain and manifest); nothing in `lean/` is changed.  Build: `cd mfg/lean && lake build` (about 30 s once
`lean/` has been built).  `MFG/Core.lean` has no `sorry`; `#print axioms` on every theorem reports only
`propext`, `Classical.choice`, `Quot.sound`.

| Paper (mfg/paper/main.tex) | Lean name (`MFG.`) | What is checked | Status |
|---|---|---|---|
| Thm 6 (zone-separable), equality case | `symmetric_closed_form` | `q = α/(m(N+1))` solves the FOC, `Q^N = N/(N+1) Q^W`, gap = one carrier's quantity | full (algebra) |
| Thm 4(a) | `sqrt_bound` | from the per-carrier optimality inequalities: `‖A^W-A^N‖² ≤ Σ⟪a^W_i-a^N_i,a^N_i⟫ ≤ ¼Σ‖a^W_i‖²` in any real inner-product space | core (the inequalities themselves come from Lemma 1, not formalised) |
| Thm 6 | `revealed_lower`, `revealed_upper`, `sandwich` | revealed-preference steps and the sandwich `Q^W - s ≤ Q^N ≤ Q^W` | core (the reduction to best-response sets is not formalised) |
| Thm 12 (perturbation form) | `fixed_point_perturbation` | `ρ`-contraction `T`, fixed point of `T'` with `d(T'x',Tx') ≤ ε` ⇒ `d(x',x) ≤ ε/(1-ρ)` | full (metric spaces) |
| Prop 11(a) | `arp_contraction` | weighted-norm chain `‖κΔQ‖_{κ⁻¹} ≤ ρ‖Δu‖_{κ⁻¹}` from nonexpansiveness | core |
| Prop 5 | `tight_family` | Nash type totals solve `(G+I/n)T = α`; `‖ΔA‖² = 1/(8n)+(2n-1)/(8n³) ≥ 1/(8n)` | full (algebra of the example) |
| Thm 13(b) | `welfare_fixed_point` | loss ≤ difference of own terms | core (one line) |
| Prop 15(d) | `gamma_welfare` | `Σ(-σx - c x²/2) ≤ Σσ²/(2c)` | core |
| Prop 18 | `d2_det`, `d2_weights_iff`, `d2_rank_one` | determinant of the symmetric part; weights symmetrise iff dwell ratios are zone-independent; rank one works | full (algebra) |
| Cor 16 | `width_scaling` | absorption width `≤ (d+1)s` | full (algebra on the Omega bound) |

Not formalised: existence of equilibria, first-order optimality (Lemma 1), Robinson's upper-Lipschitz theorem
(Thm 8), the Omega credal-absorption theorem used in Cor 16, the solvers.
