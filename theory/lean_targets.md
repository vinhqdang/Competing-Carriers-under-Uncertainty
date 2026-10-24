# Lean 4 + Mathlib targets

The statement skeletons are in `theory/LeanTargets.lean`. They type-check against the Mathlib checkout in `lean/.lake/packages/mathlib` (toolchain `leanprover/lean4:v4.36.0-rc1`). To check them:

```
cd lean && PATH=$HOME/.elan/bin:$PATH lake env lean ../theory/LeanTargets.lean
```

The file compiles with no `sorry`. T1 to T7 are proved in the file (T3 and T4 included). `#print axioms` shows only `propext`, `Classical.choice` and `Quot.sound` for each theorem.

Common setup, from `LeanTargets.lean`:

```lean
structure AggGame (N d : ℕ) where
  P : Fin N → Type;  fin : ∀ i, Fintype (P i);  dec : ∀ i, DecidableEq (P i);  ne : ∀ i, Nonempty (P i)
  a : ∀ i, P i → (Fin d → ℝ)    -- contribution
  φ : ∀ i, P i → (Fin d → ℝ)    -- exposure
  π : ∀ i, P i → ℝ              -- private profit
  M : Fin d → ℝ                  -- diagonal coupling
def AggGame.u G i p m := G.π i p - ∑ z, G.φ i p z * G.M z * m z      -- payoff at mean belief m
def AggGame.rival G σ i := ∑ j ∈ univ.erase i, G.a j (σ j)
def InBox w δ c m := ∀ z, 0 ≤ m z ∧ |m z - c z| ≤ δ * w z           -- clipped box (A4)
def EAdm G w δ i c p := ∃ m, InBox w δ c m ∧ ∀ q, G.u i q m ≤ G.u i p m
def MaxAdm G w δ i c p := ∀ q, ∃ m, InBox w δ c m ∧ G.u i q m ≤ G.u i p m
def ICNE_E G w δ σ := ∀ i, EAdm G w δ i (G.rival σ i) (σ i)
```

Traffic is omitted from the Lean model. With a degenerate traffic box it is a constant shift of π. The general case adds a second box and changes nothing structural.

The targets are ordered by difficulty.

## T1. Criteria nesting and width monotonicity (Lemma 3.4 E⊆M, Lemma 3.5). Status: DONE

```lean
theorem eAdm_imp_maxAdm (h : EAdm G w δ i c p) : MaxAdm G w δ i c p
theorem inBox_mono (hw : ∀ z, 0 ≤ w z) (hδ : δ ≤ δ') (h : InBox w δ c m) : InBox w δ' c m
theorem icneE_mono (hw : ∀ z, 0 ≤ w z) (hδ : δ ≤ δ') (σ) (h : ICNE_E G w δ σ) : ICNE_E G w δ' σ
```

- Proof: unfold and use `mul_le_mul_of_nonneg_right`.
- Still to add (easy): M ⊆ ID, Γ ⊆ M, and monotonicity for M and ID. These are finite statements over `Finset.univ` with `Finset.exists_max_image`. The box is compact, so a min or max over it needs either `IsCompact.exists_isMinOn` on `Set.pi`/`Set.Icc` or, simpler, the coordinatewise corner formula for linear functions on boxes. That formula is a target of its own (T1b): `∀ m, InBox w δ c m → ∑ z, v z * m z ≤ ∑ z, v z * corner v z`.

## T2. Credal absorption, the core of Theorem 6.1(a). Status: DONE

```lean
theorem absorption (σ) (anchor : Fin N → (Fin d → ℝ))
    (hbr : ∀ i q, G.u i q (anchor i) ≤ G.u i (σ i) (anchor i))
    (hnn : ∀ i z, 0 ≤ anchor i z)
    (hclose : ∀ i z, |anchor i z - G.rival σ i z| ≤ δ * w z) : ICNE_E G w δ σ
```

- Proof: a term-mode witness.
- Next step (easy): connect it to mixed equilibria. If `x i : P i → ℝ` are distributions and every `p` in `supp (x i)` maximises `G.u i · (Σ_{j≠i} Σ_p x j p • G.a j p)`, then any selection `σ i ∈ supp (x i)` satisfies `hbr`. The proof is `Finset.sum_nonneg` plus nonnegativity of `a` for `hnn`.

## T3. Shapley–Folkman lemma, finite form (Theorem 4.1). Status: DONE

```lean
theorem shapleyFolkman {ι E : Type*} [Fintype ι] [DecidableEq E] [AddCommGroup E]
    [Module ℝ E] [FiniteDimensional ℝ E]
    (S : ι → Finset E) (x : E) (hx : x ∈ ∑ i, convexHull ℝ (S i : Set E)) :
    ∃ y : ι → E, (∀ i, y i ∈ convexHull ℝ (S i : Set E)) ∧ ∑ i, y i = x ∧
      (univ.filter (fun i => y i ∉ S i)).card ≤ Module.finrank ℝ E
```

Proof as formalised: lift to `E × (ι → ℝ)` with the points `(s, e_i)`, `s ∈ S i`. The point `(x/n, 1/n)` lies in their convex hull. Mathlib's Carathéodory (`eq_pos_convex_span_of_mem_convexHull`) gives affinely independent support points with positive weights. These lie in the hyperplane where the indicator coordinates sum to 1, so they are linearly independent and number at most `finrank E + n`. Every index `i` owns at least one support point, so at most `finrank E` indices own two or more. The remaining indices have `y i ∈ S i`. The earlier plan by minimal support is kept below for reference.

Original plan, by minimal support:

1. Use `convexHull_sum` (`Mathlib/Analysis/Convex/Combination.lean`) to turn `hx` into `x = ∑ i, y₀ i` with `y₀ i ∈ convexHull`. Then write each `y₀ i` with weights by `Finset.mem_convexHull` / `Finset.centerMass_mem_convexHull`, or by Carathéodory `eq_pos_convex_span_of_mem_convexHull`.
2. Among all weight families `λ : ∀ i, E → ℝ` (supported in `S i`, nonnegative, summing to 1, with `∑ i, ∑ s, λ i s • s = x`), choose one minimising the total support size. Use `Nat.find` or `WellFounded.min` on the measure `∑ i, (supp λ i).card`.
3. Suppose more than `finrank` players have support of size at least 2. Pick a base point `s⁰ i` per player. The vectors `s - s⁰ i` (one per non-base support point of those players) number more than `finrank`. `Module.exists_nontrivial_relation_of_finrank_lt_card` (`LinearAlgebra/Dimension/Finite.lean`) gives a nontrivial relation `∑ f e • e = 0`.
4. Move along the relation, compensating at the base points so that per-player weight sums stay 1, until some weight hits 0 (the standard Carathéodory step, cf. `Caratheodory.mem_convexHull_erase`). This reduces total support and contradicts minimality.

Difficulty: medium–hard, about 300–600 lines. Step 4 is the bulk: it mirrors `Mathlib.Analysis.Convex.Caratheodory` but over a product of simplices. Using `d_L` (the dimension of the span of differences) instead of `finrank` is a strengthening. Formalise it afterwards by working in the submodule `Submodule.span ℝ (⋃ i, S i - S i)`.

## T4. Exact potential identity under D1 (Proposition 7.5). Status: DONE

```lean
noncomputable def potential (G : AggGame N d) (σ) : ℝ :=
  (∑ i, (G.π i (σ i) + (1/2) * ∑ z, G.M z * G.a i (σ i) z ^ 2))
    - (1/2) * ∑ z, G.M z * (∑ i, G.a i (σ i) z) ^ 2
theorem potential_identity (hD1 : ∀ i p, G.φ i p = G.a i p) (σ) (i) (q : G.P i) :
    potential G (Function.update σ i q) - potential G σ
      = G.u i q (G.rival σ i) - G.u i (σ i) (G.rival σ i)
```

Proof strategy:
- Split each sum at `i` with `Finset.sum_erase_add` / `Finset.add_sum_erase`.
- Rewrite `Function.update_self` and `Function.update_of_ne` for `j ≠ i`. This is a dependent update, so use `Function.update_apply` with `dif_neg`.
- Set `R z = rival σ i z` and close with `ring_nf` after `Finset.sum_sub_distrib` / `Finset.mul_sum`.

Difficulty: easy–medium. The dependent-type bookkeeping of `Function.update` is the only friction.

## T5. Kernel reduction core (Theorem 7.3). Status: DONE

```lean
def kernelGain adj Δin S i : ℤ :=
  2 * (Δin + 1) * (1 - 2 * #(S.filter (adj i ·))) - #(S.filter (adj · i))
def IsKernel adj S := (∀ i ∈ S, ∀ j ∈ S, ¬ adj i j) ∧ (∀ i ∉ S, ∃ j ∈ S, adj i j)
theorem pne_iff_kernel (hΔ : ∀ i, #(univ.filter (adj · i)) ≤ Δin) (S) :
  ((∀ i ∈ S, 0 ≤ kernelGain adj Δin S i) ∧ (∀ i ∉ S, kernelGain adj Δin S i ≤ 0)) ↔ IsKernel adj S
```

- The gain is the payoff gap `D_i` of the paper multiplied by `2(Δ⁻+1)`, so all data are integers.
- Proof: `Finset.card_pos`, `Finset.filter_eq_empty_iff`, `Finset.card_le_card`, `nlinarith`.
- Still to add (medium): the robustness step. For `δ < 1/(2Δ⁺+1)`, the sign of the gain is constant on the box, so E, M, ID and Γ all coincide with the pure-Nash condition. This is real arithmetic on finite sums with `abs_sub_le` and `Finset.abs_sum_le_sum_abs`.
- Not realistic: the NP-completeness statement itself. Mathlib has no infrastructure for polynomial-time reductions; `Mathlib.Computability` covers Turing machines but not NP. Only the combinatorial core is a target.

## T6. Tight example (Proposition 7.1). Status: DONE (lower-bound core)

```lean
def gain1 (n : ℝ) : ℝ := 6 - 3 * n
theorem tight_example_lower (k2 : ℝ) (hk : k2 = 1 ∨ k2 = 3) (δ : ℝ)
    (h : ∃ n, 0 ≤ n ∧ |n - k2| ≤ δ ∧ (if k2 = 1 then gain1 n ≤ 0 else 0 ≤ gain1 n)) : 1 ≤ δ
```

- This says that playing against the strict best response requires width at least 1.
- Still to add (easy): instantiate `AggGame 2 1` with the four plans, and prove `¬ ICNE_E G 1 δ σ` for δ < 1 and all σ (four cases with `fin_cases`), plus `ICNE_E G 1 1 σ` for all σ.

## T7. Product-of-cycles lower bound (Proposition 7.2). Status: DONE (counting core)

```lean
def zoneRegret : Bool → Bool → ℕ × ℕ      -- (A,X)↦(0,3), (A,Y)↦(3,0), (B,Y)↦(0,3), (B,X)↦(3,0)
theorem cycle_product_lower (Z) (s t : Fin Z → Bool) :
    3 * ((Z + 1) / 2) ≤ max (∑ z, (zoneRegret (s z) (t z)).1) (∑ z, (zoneRegret (s z) (t z)).2)
```

- Proof: `choose`, `Finset.mul_sum`, `Finset.sum_add_distrib`, `omega`.
- Still to add (medium): derive the zone regrets from the game, i.e. regret of a product strategy = sum of zone regrets. Use `Finset.sum_le_sum` and `Fintype.piFinset` for the max over product plans.

## T8. Deterministic rounding bound (Theorem 6.1(b), second term, given T3). Status: to do. Realistic.

Statement: given `y`, `σ`, `J` with `G.a j (σ j) = y j` for `j ∉ J`, `∑ y = ∑ abar`, and coordinate bounds `|a j (σ j) z - y j z| ≤ s j z` and `|a i (σ i) z - abar i z| ≤ r i z`, then `|rival σ i z - (Abar - abar i) z| ≤ ∑ j ∈ J, s j z + r i z`.

Proof: the identity (eq:decomp) by `Finset.sum_erase_eq_sub`, `Finset.sum_sub_distrib` and `Finset.sum_subset`, then `abs_sub_le` and `Finset.abs_sum_le_sum_abs`. Easy–medium.

## T9. Relaxed equilibria = mixed equilibria under affinity (Proposition 5.2). Status: to do. Realistic.

Finite expectation over the product of PMFs: `∑_{σ₋ᵢ} (∏_{j≠i} x j (σ j)) * u i p (rival σ i) = u i p (Σ_{j≠i} abar j)`. Use `Finset.prod_univ_sum` / `Fintype.prod_sum` and linearity, or `PMF` with `PMF.integral_eq_sum`. Medium, mostly bookkeeping.

## T10. D1 rounding identity (Theorem 8.1(d)). Status: to do. Medium.

`E‖Ā + e‖²_M = ‖Ā‖²_M + ∑_{j∈J} V_j` for independent zero-mean finite random vectors, written as finite weighted sums over `Fintype.piFinset`. The cross terms vanish by `Finset.sum_mul_sum` and the zero-mean hypothesis. The method of conditional expectations is then an averaging argument: `Finset.exists_le_of_sum_le` / `Finset.exists_lt_of_sum_lt` on a weighted average.

## T11. Hoeffding step (Theorem 6.1(b), third term). Status: to do. Hard but feasible.

Mathlib has Hoeffding: `ProbabilityTheory.measure_sum_ge_le_of_iIndepFun` and `hasSubgaussianMGF_of_mem_Icc_of_integral_eq_zero` (`Mathlib/Probability/Moments/SubGaussian.lean`). The work is building the product probability space over the plan choices (`Measure.pi` on `Fin k → P j`), proving `iIndepFun` (`iIndepFun_pi`), the two-sided bound and a union bound over `Fin d` (`measure_iUnion_fintype_le`), and finally extracting a sample point from `μ(bad) < 1` (`exists_not_mem_of_measure_lt`-type lemma). Difficulty: hard; probably 400+ lines.

## T12. Symmetric benchmark (Proposition 9.3). Status: to do. Medium.

Algebra for the FOC characterisation and the sign of `∂_c(ℰ/β)`. The derivative can be avoided: compare `ℰ/β` at `c` and `c'` by cross-multiplication and `nlinarith`/`positivity`.

## Not realistic or out of scope

- Frank–Wolfe convergence (Theorem 8.2). This is continuous optimisation with curvature constants. Mathlib has no FW library, and the statement is classical.
- NP-completeness and PPAD-hardness (Theorem 7.3, Proposition 7.6). No complexity-class infrastructure.
- Existence of mixed equilibria (Nash). Mathlib has Brouwer only in special cases, and Kakutani is not available.

## Suggested order

1. T1, T2, T3, T4, T5, T6, T7: done.
2. T8 (about a week).
3. T9 and T10 (about a week).
4. T12, then T11.
