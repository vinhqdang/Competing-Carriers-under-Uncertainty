/-
  Budget-resource labelling (BRL), `theory/new_algorithm_B/theory.tex`.

  * Theorem 1 (`thm:main`, eq. (budget)), common-level-grid form (Corollary `cor:grid`):
    for a comonotone sum on a finite grid of levels,
    `Σ_l w_l (Σ_a x_{a,l} - θ)⁺ = min { Σ_a Σ_l w_l (x_{a,l} - d_a)⁺ : Σ_a d_a ≤ θ }`.
    (Finitely many arcs, convex piecewise-linear arc costs, one budget.)
  * Lemma `lem:infconv`: concatenation is inf-convolution (split of the budget between two partial
    paths), for arbitrary arc cost functions whose budget-constrained minima are attained.
  * Lemma `lem:window`: completion window `D* ≤ min{S_p(1), θ - C_min}`.
  * Theorem `thm:fdom`: functional dominance on the window implies completion dominance.
  * Proposition `prop:compare`: (a) quantile-vector dominance implies functional dominance;
    (c) the two counter-examples.
  The measure-theoretic parts (the p-box, upper previsions, quantile functions) are NOT formalised:
  everything is stated on the finite level grid, where the upper prevision is the weighted sum.
-/
import Mathlib

open Finset

namespace CCU
namespace BRL

/-- Positive part `x⁺`. -/
def pos (x : ℝ) : ℝ := max x 0

theorem pos_nonneg (x : ℝ) : 0 ≤ pos x := le_max_right _ _
theorem le_pos (x : ℝ) : x ≤ pos x := le_max_left _ _
theorem pos_mono {x y : ℝ} (h : x ≤ y) : pos x ≤ pos y := max_le_max h le_rfl

section Budget

variable {A Λ : Type*} [Fintype A] [Fintype Λ]

/-- Step 1 of the proof of Theorem 1: for `Σ d ≤ θ`,
`(Σ x - θ)⁺ ≤ (Σ (x - d))⁺ ≤ Σ (x_a - d_a)⁺`. -/
theorem pos_sum_le (xs ds : A → ℝ) (θ : ℝ) (hd : ∑ a, ds a ≤ θ) :
    pos (∑ a, xs a - θ) ≤ ∑ a, pos (xs a - ds a) := by
  have h1 : ∑ a, xs a - θ ≤ ∑ a, (xs a - ds a) := by
    rw [Finset.sum_sub_distrib]; linarith
  have h2 : pos (∑ a, xs a - θ) ≤ pos (∑ a, (xs a - ds a)) := pos_mono h1
  have h3 : pos (∑ a, (xs a - ds a)) ≤ ∑ a, pos (xs a - ds a) :=
    max_le (Finset.sum_le_sum (fun a _ => le_pos _)) (Finset.sum_nonneg (fun a _ => pos_nonneg _))
  exact h2.trans h3

/-- `Σ_l w_l (Σ_a x_{a,l} - θ)⁺`: the stop-loss transform of the comonotone sum. -/
def stopLoss (w : Λ → ℝ) (x : A → Λ → ℝ) (θ : ℝ) : ℝ := ∑ l, w l * pos (∑ a, x a l - θ)

/-- `Σ_a Σ_l w_l (x_{a,l} - d_a)⁺ = Σ_a π̄_a(d_a)`: separable arc costs of the budget split `d`. -/
def splitCost (w : Λ → ℝ) (x : A → Λ → ℝ) (d : A → ℝ) : ℝ :=
  ∑ a, ∑ l, w l * pos (x a l - d a)

theorem splitCost_eq (w : Λ → ℝ) (x : A → Λ → ℝ) (d : A → ℝ) :
    splitCost w x d = ∑ l, w l * ∑ a, pos (x a l - d a) := by
  unfold splitCost
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl (fun l _ => by rw [Finset.mul_sum])

/-- Weak inequality (Step 2): `stopLoss ≤ splitCost` for every `d` with `Σ d ≤ θ`. -/
theorem stopLoss_le_splitCost {w : Λ → ℝ} (hw : ∀ l, 0 ≤ w l) (x : A → Λ → ℝ) (θ : ℝ)
    (d : A → ℝ) (hd : ∑ a, d a ≤ θ) : stopLoss w x θ ≤ splitCost w x d := by
  rw [splitCost_eq]
  exact Finset.sum_le_sum (fun l _ =>
    mul_le_mul_of_nonneg_left (pos_sum_le (fun a => x a l) d θ hd) (hw l))

/-- Per-level equality (Step 3). -/
theorem level_eq (xl d : A → ℝ) (θ : ℝ)
    (h : ((∀ a, xl a ≤ d a) ∧ ∑ a, xl a ≤ θ) ∨ ((∀ a, d a ≤ xl a) ∧ ∑ a, d a = θ)) :
    ∑ a, pos (xl a - d a) = pos (∑ a, xl a - θ) := by
  rcases h with ⟨h1, h2⟩ | ⟨h1, h2⟩
  · have : ∀ a, pos (xl a - d a) = 0 := fun a => max_eq_right (by linarith [h1 a])
    simp only [this, Finset.sum_const_zero]
    exact (max_eq_right (by linarith)).symm
  · have h3 : ∀ a, pos (xl a - d a) = xl a - d a := fun a => max_eq_left (by linarith [h1 a])
    simp only [h3]
    rw [Finset.sum_sub_distrib, h2]
    have : 0 ≤ ∑ a, xl a - θ := by
      rw [← h2, ← Finset.sum_sub_distrib]
      exact Finset.sum_nonneg (fun a _ => by linarith [h1 a])
    exact (max_eq_left this).symm

theorem splitCost_eq_stopLoss_of_levels {w : Λ → ℝ} {x : A → Λ → ℝ} {θ : ℝ} {d : A → ℝ}
    (h : ∀ l, ((∀ a, x a l ≤ d a) ∧ ∑ a, x a l ≤ θ) ∨ ((∀ a, d a ≤ x a l) ∧ ∑ a, d a = θ)) :
    splitCost w x d = stopLoss w x θ := by
  rw [splitCost_eq]
  exact Finset.sum_congr rfl (fun l _ => by rw [level_eq (fun a => x a l) d θ (h l)])

variable [LinearOrder Λ]

/-- Attainment (Step 3): on a common grid of levels with arc values nondecreasing in the level,
there is a budget split `d` with `Σ d ≤ θ` attaining the stop-loss. -/
theorem exists_split [Nonempty A] [Nonempty Λ] (w : Λ → ℝ) (x : A → Λ → ℝ)
    (hmono : ∀ a, Monotone (x a)) (θ : ℝ) :
    ∃ d : A → ℝ, ∑ a, d a ≤ θ ∧ splitCost w x d = stopLoss w x θ := by
  classical
  have hS : Monotone (fun l => ∑ a, x a l) :=
    fun l l' h => Finset.sum_le_sum (fun a _ => hmono a h)
  by_cases hHi : ∃ l, θ < ∑ a, x a l
  · by_cases hLo : ∃ l, ∑ a, x a l ≤ θ
    · -- case C: interpolate between the last level below θ and the first level above θ
      obtain ⟨l₀, hl₀⟩ := hLo
      obtain ⟨l₁, hl₁⟩ := hHi
      let Lo : Finset Λ := univ.filter (fun l => ∑ a, x a l ≤ θ)
      let Hi : Finset Λ := univ.filter (fun l => θ < ∑ a, x a l)
      have hLoNe : Lo.Nonempty := ⟨l₀, by simp [Lo, hl₀]⟩
      have hHiNe : Hi.Nonempty := ⟨l₁, by simp [Hi, hl₁]⟩
      set lo := Lo.max' hLoNe with hlo
      set hi := Hi.min' hHiNe with hhi
      have hlo_mem : ∑ a, x a lo ≤ θ := by
        have := Finset.max'_mem Lo hLoNe
        simpa [Lo] using this
      have hhi_mem : θ < ∑ a, x a hi := by
        have := Finset.min'_mem Hi hHiNe
        simpa [Hi] using this
      have hle_lo : ∀ l, ∑ a, x a l ≤ θ → l ≤ lo := fun l hl =>
        Finset.le_max' Lo l (by simp [Lo, hl])
      have hle_hi : ∀ l, θ < ∑ a, x a l → hi ≤ l := fun l hl =>
        Finset.min'_le Hi l (by simp [Hi, hl])
      have hlohi : lo ≤ hi := by
        by_contra hc
        push_neg at hc
        have := hS hc.le
        simp only at this
        linarith
      have hgap : 0 < ∑ a, x a hi - ∑ a, x a lo := by linarith
      set t : ℝ := (θ - ∑ a, x a lo) / (∑ a, x a hi - ∑ a, x a lo) with ht
      have ht0 : 0 ≤ t := div_nonneg (by linarith) hgap.le
      have ht1 : t ≤ 1 := by
        rw [ht, div_le_one hgap]; linarith
      refine ⟨fun a => x a lo + t * (x a hi - x a lo), ?_, ?_⟩
      · have : ∑ a, (x a lo + t * (x a hi - x a lo)) = θ := by
          rw [Finset.sum_add_distrib, ← Finset.mul_sum, Finset.sum_sub_distrib, ht]
          field_simp
          ring
        exact this.le
      · have hsum : ∑ a, (x a lo + t * (x a hi - x a lo)) = θ := by
          rw [Finset.sum_add_distrib, ← Finset.mul_sum, Finset.sum_sub_distrib, ht]
          field_simp
          ring
        refine splitCost_eq_stopLoss_of_levels (fun l => ?_)
        by_cases hl : ∑ a, x a l ≤ θ
        · left
          refine ⟨fun a => ?_, hl⟩
          have h1 : x a l ≤ x a lo := hmono a (hle_lo l hl)
          have h2 : x a lo ≤ x a hi := hmono a hlohi
          nlinarith
        · right
          push_neg at hl
          refine ⟨fun a => ?_, hsum⟩
          have h1 : x a hi ≤ x a l := hmono a (hle_hi l hl)
          have h2 : x a lo ≤ x a hi := hmono a hlohi
          nlinarith
    · -- case B: every level exceeds θ; shift the lowest level down to the budget
      push_neg at hLo
      let bot := (univ : Finset Λ).min' Finset.univ_nonempty
      have hbot : ∀ l, bot ≤ l := fun l => Finset.min'_le _ l (Finset.mem_univ l)
      have hcard : (0 : ℝ) < Fintype.card A := by exact_mod_cast Fintype.card_pos
      set c : ℝ := (∑ a, x a bot - θ) / Fintype.card A with hc
      have hc0 : 0 ≤ c := div_nonneg (by linarith [hLo bot]) hcard.le
      have hsum : ∑ a, (x a bot - c) = θ := by
        rw [Finset.sum_sub_distrib, Finset.sum_const, Finset.card_univ, nsmul_eq_mul, hc]
        field_simp
        ring
      refine ⟨fun a => x a bot - c, hsum.le, ?_⟩
      refine splitCost_eq_stopLoss_of_levels (fun l => Or.inr ⟨fun a => ?_, hsum⟩)
      have := hmono a (hbot l)
      linarith
  · -- case A: the sum never exceeds θ; every level is covered by the top level
    push_neg at hHi
    let top := (univ : Finset Λ).max' Finset.univ_nonempty
    have htop : ∀ l, l ≤ top := fun l => Finset.le_max' _ l (Finset.mem_univ l)
    refine ⟨fun a => x a top, hHi top, ?_⟩
    exact splitCost_eq_stopLoss_of_levels (fun l => Or.inl ⟨fun a => hmono a (htop l), hHi l⟩)

/-- **Theorem 1, budget decomposition (`thm:main`, eq. (budget)), finite-grid form.**
The stop-loss transform of the comonotone sum is the *minimum* of the separable arc costs over
all budget splits `Σ_a d_a ≤ θ`, and the minimum is attained. -/
theorem budget_identity [Nonempty A] [Nonempty Λ] {w : Λ → ℝ} (hw : ∀ l, 0 ≤ w l)
    (x : A → Λ → ℝ) (hmono : ∀ a, Monotone (x a)) (θ : ℝ) :
    IsLeast {y | ∃ d : A → ℝ, ∑ a, d a ≤ θ ∧ y = splitCost w x d} (stopLoss w x θ) := by
  refine ⟨?_, ?_⟩
  · obtain ⟨d, hd, he⟩ := exists_split w x hmono θ
    exact ⟨d, hd, he.symm⟩
  · rintro y ⟨d, hd, rfl⟩
    exact stopLoss_le_splitCost hw x θ d hd

/-- The `Σ_l w_l = 1` form with the loss `φ(T) = c₀ + γT + ρ (T - θ)⁺` (`κ = 1`):
`Σ_l w_l φ(S_l) = c₀ + γ Σ_a μ_a + ρ · min_d Σ_a π̄_a(d_a)`. -/
theorem upper_prevision_grid [Nonempty A] [Nonempty Λ] {w : Λ → ℝ} (hw : ∀ l, 0 ≤ w l)
    (hw1 : ∑ l, w l = 1) (x : A → Λ → ℝ) (hmono : ∀ a, Monotone (x a)) (c₀ γ ρ θ : ℝ)
    (hρ : 0 ≤ ρ) :
    IsLeast {y | ∃ d : A → ℝ, ∑ a, d a ≤ θ ∧
        y = c₀ + γ * ∑ a, ∑ l, w l * x a l + ρ * splitCost w x d}
      (∑ l, w l * (c₀ + γ * ∑ a, x a l + ρ * pos (∑ a, x a l - θ))) := by
  have heq : ∑ l, w l * (c₀ + γ * ∑ a, x a l + ρ * pos (∑ a, x a l - θ))
      = c₀ + γ * ∑ a, ∑ l, w l * x a l + ρ * stopLoss w x θ := by
    have h1 : ∑ l, w l * (c₀ + γ * ∑ a, x a l + ρ * pos (∑ a, x a l - θ))
        = c₀ * ∑ l, w l + γ * ∑ l, w l * ∑ a, x a l + ρ * stopLoss w x θ := by
      unfold stopLoss
      rw [Finset.mul_sum, Finset.mul_sum, Finset.mul_sum, ← Finset.sum_add_distrib,
        ← Finset.sum_add_distrib]
      exact Finset.sum_congr rfl (fun l _ => by ring)
    have h2 : ∑ a, ∑ l, w l * x a l = ∑ l, w l * ∑ a, x a l := by
      rw [Finset.sum_comm]
      exact Finset.sum_congr rfl (fun l _ => by rw [Finset.mul_sum])
    rw [h1, hw1, h2]; ring
  rw [heq]
  obtain ⟨⟨d₀, hd₀, he₀⟩, hlb⟩ := budget_identity hw x hmono θ
  refine ⟨⟨d₀, hd₀, ?_⟩, ?_⟩
  · rw [← he₀]
  · rintro y ⟨d, hd, rfl⟩
    have := hlb ⟨d, hd, rfl⟩
    nlinarith

end Budget

/-! ## Lemma `lem:infconv`: concatenation is inf-convolution -/

section InfConv

variable {A₁ A₂ : Type*} [Fintype A₁] [Fintype A₂]

/-- Splitting the arcs of a path into two partial paths `A₁ ⊕ A₂`: if `f₁ D`, `f₂ D` are the minimal
separable costs of the two parts under the budgets `D`, then the minimal cost of the whole path under
the budget `θ` is `min_D f₁(D) + f₂(θ - D)`. Valid for arbitrary arc cost functions for which the
two partial minima are attained (as they are for the convex piecewise-linear costs of the paper). -/
theorem infconv_split (c₁ : A₁ → ℝ → ℝ) (c₂ : A₂ → ℝ → ℝ) (f₁ f₂ : ℝ → ℝ)
    (h₁ : ∀ D, IsLeast {y | ∃ d : A₁ → ℝ, ∑ a, d a ≤ D ∧ y = ∑ a, c₁ a (d a)} (f₁ D))
    (h₂ : ∀ D, IsLeast {y | ∃ d : A₂ → ℝ, ∑ a, d a ≤ D ∧ y = ∑ a, c₂ a (d a)} (f₂ D))
    (θ v : ℝ) :
    IsLeast {y | ∃ d : A₁ ⊕ A₂ → ℝ, ∑ a, d a ≤ θ ∧ y = ∑ a, Sum.elim c₁ c₂ a (d a)} v
      ↔ IsLeast (Set.range fun D => f₁ D + f₂ (θ - D)) v := by
  have hsub : ∀ D, f₁ D + f₂ (θ - D) ∈
      {y | ∃ d : A₁ ⊕ A₂ → ℝ, ∑ a, d a ≤ θ ∧ y = ∑ a, Sum.elim c₁ c₂ a (d a)} := by
    intro D
    obtain ⟨d₁, hd₁, he₁⟩ := (h₁ D).1
    obtain ⟨d₂, hd₂, he₂⟩ := (h₂ (θ - D)).1
    refine ⟨Sum.elim d₁ d₂, ?_, ?_⟩
    · rw [Fintype.sum_sum_type]; simp only [Sum.elim_inl, Sum.elim_inr]; linarith
    · rw [Fintype.sum_sum_type]; simp only [Sum.elim_inl, Sum.elim_inr]
      rw [he₁, he₂]
  have hlow : ∀ y ∈ {y | ∃ d : A₁ ⊕ A₂ → ℝ, ∑ a, d a ≤ θ ∧
      y = ∑ a, Sum.elim c₁ c₂ a (d a)}, ∃ D, f₁ D + f₂ (θ - D) ≤ y := by
    rintro y ⟨d, hd, rfl⟩
    refine ⟨∑ a, d (Sum.inl a), ?_⟩
    rw [Fintype.sum_sum_type] at hd ⊢
    simp only [Sum.elim_inl, Sum.elim_inr]
    have e1 := (h₁ (∑ a, d (Sum.inl a))).2 ⟨fun a => d (Sum.inl a), le_rfl, rfl⟩
    have e2 := (h₂ (θ - ∑ a, d (Sum.inl a))).2
      ⟨fun a => d (Sum.inr a), by linarith, rfl⟩
    linarith
  constructor
  · rintro ⟨hv, hvl⟩
    obtain ⟨D, hD⟩ := hlow v hv
    have hvD : v = f₁ D + f₂ (θ - D) := le_antisymm (hvl (hsub D)) hD
    refine ⟨⟨D, hvD.symm⟩, ?_⟩
    rintro y ⟨D', rfl⟩
    exact hvl (hsub D')
  · rintro ⟨⟨D, rfl⟩, hvl⟩
    refine ⟨hsub D, ?_⟩
    intro y hy
    obtain ⟨D', hD'⟩ := hlow y hy
    exact (hvl ⟨D', rfl⟩).trans hD'

end InfConv

/-! ## Lemma `lem:window` and Theorem `thm:fdom` -/

section Window

/-- **Lemma `lem:window` (completion window).**
`fp` is the cost function of the partial path `p` (slope in `[-ρ, 0]`, constant from `s1p = S_p(1)`
on), `fq` that of a completion `q` (nonincreasing, slope exactly `-ρ` below `s0q = S_q(0⁺)`).
For every budget split `D₀` there is a split `D* ≤ min{s1p, θ - s0q}` that is at least as good. -/
theorem completion_window {fp fq : ℝ → ℝ} {ρ θ s0q s1p : ℝ}
    (hp_slope : ∀ D D', D ≤ D' → fp D - fp D' ≤ ρ * (D' - D))
    (hp_const : ∀ D, s1p ≤ D → fp D = fp s1p)
    (hq_anti : ∀ x x', x ≤ x' → fq x' ≤ fq x)
    (hq_lin : ∀ x, x ≤ s0q → fq x = fq s0q + ρ * (s0q - x)) (D₀ : ℝ) :
    ∃ Ds, Ds ≤ θ - s0q ∧ Ds ≤ s1p ∧ fp Ds + fq (θ - Ds) ≤ fp D₀ + fq (θ - D₀) := by
  set c := θ - s0q with hc
  -- step (i): on `D > θ - s0q` the objective is nondecreasing
  have step1 : fp (min D₀ c) + fq (θ - min D₀ c) ≤ fp D₀ + fq (θ - D₀) := by
    rcases le_total D₀ c with h | h
    · rw [min_eq_left h]
    · rw [min_eq_right h]
      have e1 := hp_slope c D₀ h
      have e2 := hq_lin (θ - D₀) (by linarith)
      have e3 : θ - c = s0q := by rw [hc]; ring
      rw [e3]
      linarith
  set D₁ := min D₀ c with hD₁
  -- step (ii): above `S_p(1)` the first term is constant and the second nonincreasing
  have step2 : fp (min D₁ s1p) + fq (θ - min D₁ s1p) ≤ fp D₁ + fq (θ - D₁) := by
    rcases le_total D₁ s1p with h | h
    · rw [min_eq_left h]
    · rw [min_eq_right h]
      have e1 := hp_const D₁ h
      have e2 := hq_anti (θ - D₁) (θ - s1p) (by linarith)
      linarith
  refine ⟨min D₁ s1p, ?_, min_le_right _ _, step2.trans step1⟩
  exact (min_le_left _ _).trans (min_le_right _ _)

/-- Window form with `C_min ≤ S_q(0⁺)`: the minimiser may be taken `≤ h(p) = min{S_p(1), θ - C_min}`. -/
theorem completion_window' {fp fq : ℝ → ℝ} {ρ θ s0q s1p Cmin : ℝ}
    (hC : Cmin ≤ s0q)
    (hp_slope : ∀ D D', D ≤ D' → fp D - fp D' ≤ ρ * (D' - D))
    (hp_const : ∀ D, s1p ≤ D → fp D = fp s1p)
    (hq_anti : ∀ x x', x ≤ x' → fq x' ≤ fq x)
    (hq_lin : ∀ x, x ≤ s0q → fq x = fq s0q + ρ * (s0q - x)) (D₀ : ℝ) :
    ∃ Ds, Ds ≤ min s1p (θ - Cmin) ∧ fp Ds + fq (θ - Ds) ≤ fp D₀ + fq (θ - D₀) := by
  obtain ⟨Ds, h1, h2, h3⟩ := completion_window (θ := θ) hp_slope hp_const hq_anti hq_lin D₀
  exact ⟨Ds, le_min h2 (by linarith), h3⟩

/-- The comparison `g ≤ 0` of two labels on the window `J(p₂) = [λ, h]`, `λ = min{S_{p₂}(0⁺), h}`,
extends to all `D ≤ h`: below `λ` the difference is nondecreasing. -/
theorem dominance_below_window {f₁ f₂ : ℝ → ℝ} {ρ s0₂ h π₁ π₂ : ℝ}
    (hf₁ : ∀ D D', D ≤ D' → f₁ D - f₁ D' ≤ ρ * (D' - D))
    (hf₂ : ∀ D, D ≤ s0₂ → f₂ D = f₂ s0₂ + ρ * (s0₂ - D))
    (hdom : ∀ D, min s0₂ h ≤ D → D ≤ h → (f₁ D - π₁) - (f₂ D - π₂) ≤ 0) :
    ∀ D, D ≤ h → (f₁ D - π₁) - (f₂ D - π₂) ≤ 0 := by
  intro D hD
  by_cases hin : min s0₂ h ≤ D
  · exact hdom D hin hD
  · push_neg at hin
    have hDs : D ≤ s0₂ := by
      have := min_le_left s0₂ h
      linarith
    have hl := hdom (min s0₂ h) le_rfl (min_le_right _ _)
    have hls : min s0₂ h ≤ s0₂ := min_le_left _ _
    have e1 := hf₁ D (min s0₂ h) hin.le
    have e2 := hf₂ D hDs
    have e3 := hf₂ (min s0₂ h) hls
    linarith

/-- **Theorem `thm:fdom` (functional dominance is valid).**  Let `p₂` be a label with cost function
`f₂` (slope `≥ -ρ`, constant from `s1₂`, slope `-ρ` below `s0₂`), `p₁` a label with `f₁` of slope
`≥ -ρ`, and `fq` the cost function of a completion (nonincreasing, slope `-ρ` below `s0q ≥ Cmin`).
Let `h = min{s1₂, θ - Cmin}`.  If `f₁ - π₁ ≤ f₂ - π₂` on `J(p₂) = [min{s0₂,h}, h]`, then the
concatenation values `v_i = min_D f_i(D) + fq(θ - D)` satisfy `v₁ - π₁ ≤ v₂ - π₂`. -/
theorem functional_dominance_valid {f₁ f₂ fq : ℝ → ℝ}
    {ρ θ s0q s1₂ s0₂ Cmin π₁ π₂ v₁ v₂ : ℝ}
    (hC : Cmin ≤ s0q)
    (hf₁ : ∀ D D', D ≤ D' → f₁ D - f₁ D' ≤ ρ * (D' - D))
    (hf₂ : ∀ D D', D ≤ D' → f₂ D - f₂ D' ≤ ρ * (D' - D))
    (hf₂c : ∀ D, s1₂ ≤ D → f₂ D = f₂ s1₂)
    (hf₂l : ∀ D, D ≤ s0₂ → f₂ D = f₂ s0₂ + ρ * (s0₂ - D))
    (hq_anti : ∀ x x', x ≤ x' → fq x' ≤ fq x)
    (hq_lin : ∀ x, x ≤ s0q → fq x = fq s0q + ρ * (s0q - x))
    (hdom : ∀ D, min s0₂ (min s1₂ (θ - Cmin)) ≤ D → D ≤ min s1₂ (θ - Cmin) →
      (f₁ D - π₁) - (f₂ D - π₂) ≤ 0)
    (hv₁ : ∀ D, v₁ ≤ f₁ D + fq (θ - D))
    (hv₂ : (∃ D₀, v₂ = f₂ D₀ + fq (θ - D₀)) ∧ ∀ D, v₂ ≤ f₂ D + fq (θ - D)) :
    v₁ - π₁ ≤ v₂ - π₂ := by
  obtain ⟨⟨D₀, hD₀⟩, hmin⟩ := hv₂
  obtain ⟨Ds, hDs, hle⟩ := completion_window' (θ := θ) hC hf₂ hf₂c hq_anti hq_lin D₀
  have hv2eq : v₂ = f₂ Ds + fq (θ - Ds) := le_antisymm (hmin Ds) (by linarith)
  have hg := dominance_below_window hf₁ hf₂l hdom Ds hDs
  have := hv₁ Ds
  linarith

end Window

/-! ## Proposition `prop:compare` -/

section Compare

variable {Λ : Type*} [Fintype Λ]

/-- Label cost function `f_S(D) = γ Σ_l w_l S_l + ρ Σ_l w_l (S_l - D)⁺`. -/
def fcost (w : Λ → ℝ) (γ ρ : ℝ) (S : Λ → ℝ) (D : ℝ) : ℝ :=
  γ * ∑ l, w l * S l + ρ * ∑ l, w l * pos (S l - D)

/-- **Proposition `prop:compare`(a).** Quantile-vector dominance `S₁ ≤ S₂` (with `π₁ ≥ π₂`)
implies `g ≤ 0` everywhere, hence functional dominance. -/
theorem fcost_mono {w : Λ → ℝ} (hw : ∀ l, 0 ≤ w l) {γ ρ : ℝ} (hγ : 0 ≤ γ) (hρ : 0 ≤ ρ)
    {S₁ S₂ : Λ → ℝ} (h : ∀ l, S₁ l ≤ S₂ l) (D : ℝ) :
    fcost w γ ρ S₁ D ≤ fcost w γ ρ S₂ D := by
  unfold fcost
  have h1 : ∑ l, w l * S₁ l ≤ ∑ l, w l * S₂ l :=
    Finset.sum_le_sum (fun l _ => mul_le_mul_of_nonneg_left (h l) (hw l))
  have h2 : ∑ l, w l * pos (S₁ l - D) ≤ ∑ l, w l * pos (S₂ l - D) :=
    Finset.sum_le_sum (fun l _ => mul_le_mul_of_nonneg_left (pos_mono (by linarith [h l])) (hw l))
  nlinarith [mul_le_mul_of_nonneg_left h1 hγ, mul_le_mul_of_nonneg_left h2 hρ]

theorem quantile_dominance_g_nonpos {w : Λ → ℝ} (hw : ∀ l, 0 ≤ w l) {γ ρ : ℝ} (hγ : 0 ≤ γ)
    (hρ : 0 ≤ ρ) {S₁ S₂ : Λ → ℝ} (h : ∀ l, S₁ l ≤ S₂ l) {π₁ π₂ : ℝ} (hπ : π₂ ≤ π₁)
    (D : ℝ) : (fcost w γ ρ S₁ D - π₁) - (fcost w γ ρ S₂ D - π₂) ≤ 0 := by
  have := fcost_mono hw hγ hρ h D
  linarith

/-- Two levels with weights `1/2`, `γ = 0`, `ρ = 1`, as in the proof of `prop:compare`(c). -/
noncomputable def f2 (S : Fin 2 → ℝ) (D : ℝ) : ℝ := fcost (fun _ => (1 : ℝ) / 2) 0 1 S D

/-- **Proposition `prop:compare`(c), first example.** `S₁ = (1,1)`, `S₂ = (0, 2.2)`:
`f₁ ≤ f₂` on all of `ℝ`, although `S₁,₁ = 1 > 0 = S₂,₁`. -/
theorem compare_example_one (D : ℝ) : f2 ![1, 1] D ≤ f2 ![0, 2.2] D := by
  unfold f2 fcost pos
  simp only [Fin.sum_univ_two, Matrix.cons_val_zero, Matrix.cons_val_one]
  simp only [max_def]
  split_ifs <;> norm_num <;> linarith

/-- First example: the strict inequality in the first coordinate that defeats vector dominance. -/
theorem compare_example_one_not_vector : ¬ (∀ l, (![1, 1] : Fin 2 → ℝ) l ≤ ![0, 2.2] l) := by
  intro h
  have := h 0
  simp at this
  norm_num at this

/-- **Proposition `prop:compare`(c), second example.** `S₁ = (0.5, 2.5)`, `S₂ = (1.5, 1.6)`,
window `J(p₂) = {0.5}`: `f₁(0.5) = 1 < 1.05 = f₂(0.5)` (so `p₂` is pruned), but
`f₁(2) = 0.25 > 0 = f₂(2)` (no dominance on the whole line). -/
theorem compare_example_two :
    f2 ![0.5, 2.5] 0.5 = 1 ∧ f2 ![1.5, 1.6] 0.5 = 1.05 ∧
    f2 ![0.5, 2.5] 2 = 0.25 ∧ f2 ![1.5, 1.6] 2 = 0 := by
  unfold f2 fcost pos
  simp only [Fin.sum_univ_two, Matrix.cons_val_zero, Matrix.cons_val_one]
  refine ⟨?_, ?_, ?_, ?_⟩ <;> norm_num [max_def]

end Compare

end BRL
end CCU
