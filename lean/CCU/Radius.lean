/-
  Combinatorial core of the anchored-radius bound, `theory/main.tex`, Theorem 6.1(b)/(c)
  (credal Shapley-Folkman absorption, radius part).  One coordinate `k` at a time (all statements
  are for real numbers `a j = a_{jk}(p_j)`, `abar j = ā_{jk}`, ...; apply them for every `k` and
  divide by `w_k` to get the weighted sup-norm bound).

  * `first_term_*`  : `|A_{-i}(p) - Ā*_{-i}| ≤ Σ_{j≠i} r_j ≤ (N-1) σ_max` (support selection).
  * `decomp`        : the decomposition (eq:decomp) after Shapley-Folkman rounding.
  * `second_term_*` : `|A_{-i}(p) - Ā*_{-i}| ≤ Σ_{j∈J} s_j + r_i ≤ k♯ σ̄ + ρ̄` for `|J| ≤ k♯`.

  NOT formalised here: the Shapley-Folkman support bound `|J| ≤ d_L` itself is
  `CCU.shapleyFolkman` in `LeanTargets.lean`; the Hoeffding/union-bound third term needs
  probability and is not included; the LP vertex construction is not included.
-/
import Mathlib

open Finset

set_option linter.unusedSectionVars false
set_option linter.deprecated false

noncomputable section

namespace CCU
namespace Radius

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/-- `Ā_{-i} = Σ_j ā_j - ā_i` equals the sum of the others. -/
theorem sum_others (abar : ι → ℝ) (i : ι) :
    ∑ j, abar j - abar i = ∑ j ∈ univ.erase i, abar j := by
  rw [Finset.sum_erase_eq_sub (Finset.mem_univ i)]

/-- **Theorem 6.1(b), first term (exact).** If `|a_j - ā_j| ≤ r_j` for every `j`, then
`|Σ_{j≠i} a_j - (Σ_j ā_j - ā_i)| ≤ Σ_{j≠i} r_j`. -/
theorem first_term (a abar r : ι → ℝ) (hr : ∀ j, |a j - abar j| ≤ r j) (i : ι) :
    |∑ j ∈ univ.erase i, a j - (∑ j, abar j - abar i)| ≤ ∑ j ∈ univ.erase i, r j := by
  rw [sum_others, ← Finset.sum_sub_distrib]
  exact (Finset.abs_sum_le_sum_abs _ _).trans (Finset.sum_le_sum (fun j _ => hr j))

/-- **Theorem 6.1(c), the `N - 1` term.** If every spread is at most `σ`, then
`Σ_{j≠i} r_j ≤ (N - 1) σ`. -/
theorem first_term_card (r : ι → ℝ) (σ : ℝ) (hσ : ∀ j, r j ≤ σ) (i : ι) :
    ∑ j ∈ univ.erase i, r j ≤ ((Fintype.card ι : ℝ) - 1) * σ := by
  have h := Finset.sum_le_card_nsmul (univ.erase i) r σ (fun j _ => hσ j)
  rw [Finset.card_erase_of_mem (Finset.mem_univ i), Finset.card_univ, nsmul_eq_mul] at h
  have hc : 1 ≤ Fintype.card ι := Fintype.card_pos_iff.2 ⟨i⟩
  rw [Nat.cast_sub hc] at h
  simpa using h

/-- The two bounds combined: `|A_{-i}(p) - Ā*_{-i}| ≤ (N-1) σ` whenever `|a_j - ā_j| ≤ σ`. -/
theorem first_term_uniform (a abar : ι → ℝ) (σ : ℝ) (hr : ∀ j, |a j - abar j| ≤ σ) (i : ι) :
    |∑ j ∈ univ.erase i, a j - (∑ j, abar j - abar i)| ≤ ((Fintype.card ι : ℝ) - 1) * σ :=
  (first_term a abar (fun _ => σ) hr i).trans (first_term_card _ σ (fun _ => le_rfl) i)

/-- **Decomposition (eq:decomp).** If `a_j = y_j` off `J` and `Σ y = Σ ā` then
`Σ_{j≠i} a_j - (Σ ā - ā_i) = Σ_{j∈J}(a_j - y_j) - (a_i - ā_i)`. -/
theorem decomp (a abar y : ι → ℝ) (J : Finset ι) (hy : ∀ j ∉ J, a j = y j)
    (hsum : ∑ j, y j = ∑ j, abar j) (i : ι) :
    ∑ j ∈ univ.erase i, a j - (∑ j, abar j - abar i)
      = ∑ j ∈ J, (a j - y j) - (a i - abar i) := by
  have h1 : ∑ j ∈ univ.erase i, a j = ∑ j, a j - a i := by
    rw [Finset.sum_erase_eq_sub (Finset.mem_univ i)]
  have h2 : ∑ j, a j = ∑ j ∈ J, (a j - y j) + ∑ j, y j := by
    have : ∑ j, (a j - y j) = ∑ j ∈ J, (a j - y j) := by
      refine (Finset.sum_subset (Finset.subset_univ J) (fun j _ hj => ?_)).symm
      rw [hy j hj]; ring
    rw [← this, Finset.sum_sub_distrib]; ring
  rw [h1, h2, hsum]
  ring

/-- Two numbers in an interval differ by at most its length (`s_j = max - min` spread). -/
theorem abs_sub_le_spread {lo hi x y : ℝ} (hx : x ∈ Set.Icc lo hi) (hy : y ∈ Set.Icc lo hi) :
    |x - y| ≤ hi - lo := by
  rw [abs_le]
  constructor <;> linarith [hx.1, hx.2, hy.1, hy.2]

/-- **Theorem 6.1(b), second term (T8).** After Shapley-Folkman rounding (`a_j = y_j` for `j ∉ J`,
`Σ y = Σ ā`), with `|a_j - y_j| ≤ s_j` on `J` and `|a_i - ā_i| ≤ r_i`:
`|Σ_{j≠i} a_j - (Σ ā - ā_i)| ≤ Σ_{j∈J} s_j + r_i`. -/
theorem second_term (a abar y : ι → ℝ) (J : Finset ι) (hy : ∀ j ∉ J, a j = y j)
    (hsum : ∑ j, y j = ∑ j, abar j) (s : ι → ℝ) (hs : ∀ j ∈ J, |a j - y j| ≤ s j)
    (i : ι) (ri : ℝ) (hri : |a i - abar i| ≤ ri) :
    |∑ j ∈ univ.erase i, a j - (∑ j, abar j - abar i)| ≤ ∑ j ∈ J, s j + ri := by
  rw [decomp a abar y J hy hsum i]
  calc |∑ j ∈ J, (a j - y j) - (a i - abar i)|
      ≤ |∑ j ∈ J, (a j - y j)| + |a i - abar i| := abs_sub _ _
    _ ≤ ∑ j ∈ J, |a j - y j| + ri :=
        add_le_add (Finset.abs_sum_le_sum_abs _ _) hri
    _ ≤ ∑ j ∈ J, s j + ri := by
        have := Finset.sum_le_sum hs
        linarith

/-- **Theorem 6.1(b), second term, uniform form.** With `|J| ≤ k♯`, spreads `≤ σ̄`, `r_i ≤ ρ̄`:
`|Σ_{j≠i} a_j - (Σ ā - ā_i)| ≤ k♯ σ̄ + ρ̄` (per coordinate, i.e. `k♯ σ̄ w_k + ρ̄ w_k` after
scaling). -/
theorem second_term_uniform (a abar y : ι → ℝ) (J : Finset ι) (hy : ∀ j ∉ J, a j = y j)
    (hsum : ∑ j, y j = ∑ j, abar j) (sig rho : ℝ) (hsig : 0 ≤ sig)
    (hs : ∀ j ∈ J, |a j - y j| ≤ sig) (i : ι) (hri : |a i - abar i| ≤ rho) {k : ℕ}
    (hJ : J.card ≤ k) :
    |∑ j ∈ univ.erase i, a j - (∑ j, abar j - abar i)| ≤ (k : ℝ) * sig + rho := by
  have h := second_term a abar y J hy hsum (fun _ => sig) hs i rho hri
  have h2 : ∑ j ∈ J, sig = J.card * sig := by simp
  have h3 : (J.card : ℝ) * sig ≤ k * sig :=
    mul_le_mul_of_nonneg_right (by exact_mod_cast hJ) hsig
  linarith

end Radius
end CCU

end
