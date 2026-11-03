/-
Machine-checked algebraic cores of the mean-field paper (mfg/paper/main.tex).

Every statement below is a finite or algebraic core of a result of the paper; the analytic parts (existence,
variational inequalities from optimality, Robinson's upper-Lipschitz theorem, the Omega credal theorem) are not
formalised.  The file has no `sorry`.  Check: `cd lean && lake env lean ../mfg/lean/MFG/Core.lean`.
-/
import Mathlib.Analysis.InnerProductSpace.Basic
import Mathlib.Topology.MetricSpace.Lipschitz
import Mathlib.Algebra.Order.Chebyshev
import Mathlib.Tactic

open Finset BigOperators

namespace MFG

/-! ## 1. Symmetric one-zone closed form (paper, Section 3, Theorem `thm:sep`, equality case) -/

/-- With `N` identical carriers, linear profit `α` per delivery and slope `m`, the per-carrier Nash quantity
`q = α / (m (N+1))` satisfies the first-order condition `α - m (N q) - m q = 0`; the Nash aggregate is
`N/(N+1)` of the Wardrop aggregate `α/m`, and the gap equals one carrier's quantity. -/
theorem symmetric_closed_form (α m : ℝ) (N : ℕ) (hm : 0 < m) :
    let q := α / (m * (N + 1))
    α - m * (N * q) - m * q = 0 ∧ N * q = (N / (N + 1)) * (α / m) ∧ α / m - N * q = q := by
  intro q
  have hN : (N : ℝ) + 1 ≠ 0 := by positivity
  have hm' : m ≠ 0 := ne_of_gt hm
  refine ⟨?_, ?_, ?_⟩ <;> simp only [q] <;> field_simp <;> ring

/-! ## 2. The summed variational-inequality bound (Theorem `thm:sqrt`(a)) -/

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

local notation "⟪" x ", " y "⟫" => @inner ℝ E _ x y

/-- Algebraic core of the general bound: if every carrier's Nash and Wardrop optimality conditions give
`⟪aW i - aN i, AW⟫ - ⟪aW i - aN i, AN⟫ ≤ ⟪aW i - aN i, aN i⟫`, then
`‖AW - AN‖² ≤ Σ ⟪aW i - aN i, aN i⟫ ≤ (1/4) Σ ‖aW i‖²`.  (`E` carries the `M`-inner product.) -/
theorem sqrt_bound {N : ℕ} (aN aW : Fin N → E)
    (h : ∀ i, ⟪aW i - aN i, ∑ j, aW j⟫ - ⟪aW i - aN i, ∑ j, aN j⟫ ≤ ⟪aW i - aN i, aN i⟫) :
    ‖(∑ j, aW j) - ∑ j, aN j‖ ^ 2 ≤ ∑ i, ⟪aW i - aN i, aN i⟫ ∧
      ∑ i, ⟪aW i - aN i, aN i⟫ ≤ (1 / 4) * ∑ i, ‖aW i‖ ^ 2 := by
  constructor
  · have hD : (∑ j, aW j) - ∑ j, aN j = ∑ i, (aW i - aN i) := by rw [Finset.sum_sub_distrib]
    calc ‖(∑ j, aW j) - ∑ j, aN j‖ ^ 2
        = ⟪(∑ j, aW j) - ∑ j, aN j, (∑ j, aW j) - ∑ j, aN j⟫ := (real_inner_self_eq_norm_sq _).symm
      _ = ⟪∑ i, (aW i - aN i), (∑ j, aW j) - ∑ j, aN j⟫ := by nth_rewrite 1 [hD]; rfl
      _ = ∑ i, ⟪aW i - aN i, (∑ j, aW j) - ∑ j, aN j⟫ := sum_inner _ _ _
      _ = ∑ i, (⟪aW i - aN i, ∑ j, aW j⟫ - ⟪aW i - aN i, ∑ j, aN j⟫) := by
          simp only [inner_sub_right]
      _ ≤ ∑ i, ⟪aW i - aN i, aN i⟫ := Finset.sum_le_sum (fun i _ => h i)
  · rw [Finset.mul_sum]
    apply Finset.sum_le_sum
    intro i _
    have h0 : 0 ≤ ‖aN i - (1 / 2 : ℝ) • aW i‖ ^ 2 := by positivity
    rw [← real_inner_self_eq_norm_sq] at h0
    simp only [inner_sub_left, inner_sub_right, inner_smul_left, inner_smul_right,
      real_inner_comm (aW i) (aN i), real_inner_self_eq_norm_sq] at h0 ⊢
    simp at h0
    linarith [h0]

/-! ## 3. One-zone sandwich (Theorem `thm:sep`) -/

/-- Revealed preference: if `x` beats a smaller `y` at price `p'`, it beats `y` strictly at every lower price. -/
theorem revealed_lower (f : ℝ → ℝ) {x y p p' : ℝ} (hxy : y < x) (hp : p < p')
    (h : f y - p' * y ≤ f x - p' * x) : f y - p * y < f x - p * x := by
  nlinarith

/-- Revealed preference, upper side. -/
theorem revealed_upper (f : ℝ → ℝ) {x y p p' : ℝ} (hxy : x < y) (hp : p' < p)
    (h : f y - p' * y ≤ f x - p' * x) : f y - p * y < f x - p * x := by
  nlinarith

/-- The sandwich step: if a lower Wardrop price forces every Wardrop quantity above the Nash quantity, and a
Wardrop price above `m (Q^N + s)` forces every Wardrop quantity below it, then `Q^W - s ≤ Q^N ≤ Q^W`. -/
theorem sandwich {N : ℕ} (qN qW : Fin N → ℝ) (m s : ℝ) (hm : 0 < m) (hs : 0 ≤ s)
    (H1 : m * (∑ i, qW i) < m * (∑ i, qN i) → ∀ i, qN i ≤ qW i)
    (H2 : m * ((∑ i, qN i) + s) < m * (∑ i, qW i) → ∀ i, qW i ≤ qN i) :
    (∑ i, qW i) - s ≤ ∑ i, qN i ∧ ∑ i, qN i ≤ ∑ i, qW i := by
  constructor
  · by_contra hc
    rw [not_le] at hc
    have : m * ((∑ i, qN i) + s) < m * (∑ i, qW i) := by
      apply mul_lt_mul_of_pos_left _ hm; linarith
    have := Finset.sum_le_sum (fun i (_ : i ∈ Finset.univ) => H2 this i)
    linarith
  · by_contra hc
    rw [not_le] at hc
    have : m * (∑ i, qW i) < m * (∑ i, qN i) := mul_lt_mul_of_pos_left hc hm
    have := Finset.sum_le_sum (fun i (_ : i ∈ Finset.univ) => H1 this i)
    linarith

/-! ## 4. Contraction perturbation (Theorem `thm:toll`, perturbation form) -/

/-- If `T` is a `ρ`-contraction with fixed point `x`, and `x'` is a fixed point of some other map `T'` with
`dist (T' x') (T x') ≤ ε`, then `dist x' x ≤ ε / (1 - ρ)`. -/
theorem fixed_point_perturbation {X : Type*} [MetricSpace X] (T T' : X → X) (ρ ε : ℝ) (hρ : ρ < 1)
    (hT : ∀ a b, dist (T a) (T b) ≤ ρ * dist a b) (x x' : X) (hx : T x = x) (hx' : T' x' = x')
    (hε : dist (T' x') (T x') ≤ ε) : dist x' x ≤ ε / (1 - ρ) := by
  have h1 : dist x' x ≤ ε + ρ * dist x' x := by
    calc dist x' x = dist (T' x') (T x) := by rw [hx, hx']
      _ ≤ dist (T' x') (T x') + dist (T x') (T x) := dist_triangle _ _ _
      _ ≤ ε + ρ * dist x' x := add_le_add hε (hT x' x)
  rw [le_div_iff₀ (by linarith)]
  linarith

/-! ## 5. Contraction ratio of the observation-only rule (Proposition `prop:arp`(a)) -/

/-- Weighted-norm algebra: if `κ_k ≤ ρ m_k` (`0 < κ_k`, `0 < m_k`) and the response is nonexpansive,
`Σ m_k ΔQ_k² ≤ Σ Δu_k² / m_k`, then the rule `u ↦ κ Q(u)` contracts:
`Σ (κ_k ΔQ_k)² / κ_k ≤ ρ² Σ Δu_k² / κ_k`. -/
theorem arp_contraction {d : ℕ} (κ m dQ du : Fin d → ℝ) (ρ : ℝ) (hρ : 0 ≤ ρ)
    (hκ : ∀ k, 0 < κ k) (hm : ∀ k, 0 < m k) (hr : ∀ k, κ k ≤ ρ * m k)
    (hprox : ∑ k, m k * dQ k ^ 2 ≤ ∑ k, du k ^ 2 / m k) :
    ∑ k, (κ k * dQ k) ^ 2 / κ k ≤ ρ ^ 2 * ∑ k, du k ^ 2 / κ k := by
  have e1 : ∀ k, (κ k * dQ k) ^ 2 / κ k = κ k * dQ k ^ 2 := by
    intro k; have := (hκ k).ne'; field_simp
  have s1 : ∑ k, (κ k * dQ k) ^ 2 / κ k ≤ ρ * ∑ k, m k * dQ k ^ 2 := by
    rw [Finset.mul_sum]; apply Finset.sum_le_sum; intro k _
    rw [e1]; have := sq_nonneg (dQ k); nlinarith [hr k]
  have s2 : ∑ k, du k ^ 2 / m k ≤ ρ * ∑ k, du k ^ 2 / κ k := by
    rw [Finset.mul_sum]; apply Finset.sum_le_sum; intro k _
    have hk := hκ k; have hmk := hm k
    rw [div_le_iff₀ hmk, mul_assoc, mul_comm (du k ^ 2 / κ k) (m k), ← mul_assoc]
    have : du k ^ 2 = (du k ^ 2 / κ k) * κ k := by field_simp
    calc du k ^ 2 = (du k ^ 2 / κ k) * κ k := this
      _ ≤ (du k ^ 2 / κ k) * (ρ * m k) := by
          apply mul_le_mul_of_nonneg_left (hr k); positivity
      _ = ρ * m k * (du k ^ 2 / κ k) := by ring
  calc ∑ k, (κ k * dQ k) ^ 2 / κ k ≤ ρ * ∑ k, m k * dQ k ^ 2 := s1
    _ ≤ ρ * ∑ k, du k ^ 2 / m k := mul_le_mul_of_nonneg_left hprox hρ
    _ ≤ ρ * (ρ * ∑ k, du k ^ 2 / κ k) := mul_le_mul_of_nonneg_left s2 hρ
    _ = ρ ^ 2 * ∑ k, du k ^ 2 / κ k := by ring

/-! ## 6. The tightness family (Proposition `prop:tight`) -/

/-- Two zones, `M = I`, `1 - cos φ = 1/n`.  With `c = 1 - 1/n`, `s² = 1 - c²`, the Nash type totals
`T = (3/4 - 1/(4n), 1/4 - 1/(4n))` solve `(G + I/n) T = (1, c)`, `G = [[1, c], [c, 1]]`, and the aggregate gap
`ΔA = (ΔT₁ + c ΔT₂, s ΔT₂)` with `ΔT = T - (1, 0)` has squared norm `1/(8n) + (2n-1)/(8n³) ≥ 1/(8n)`. -/
theorem tight_family (n s : ℝ) (hn : 1 ≤ n) (hs : s ^ 2 = 1 - (1 - 1 / n) ^ 2) :
    let c := 1 - 1 / n
    let T1 := 3 / 4 - 1 / (4 * n)
    let T2 := 1 / 4 - 1 / (4 * n)
    (1 + 1 / n) * T1 + c * T2 = 1 ∧ c * T1 + (1 + 1 / n) * T2 = c ∧
      ((T1 - 1) + c * T2) ^ 2 + (s * T2) ^ 2 = 1 / (8 * n) + (2 * n - 1) / (8 * n ^ 3) ∧
      1 / (8 * n) ≤ ((T1 - 1) + c * T2) ^ 2 + (s * T2) ^ 2 := by
  intro c T1 T2
  have hn0 : n ≠ 0 := by positivity
  have e3 : ((T1 - 1) + c * T2) ^ 2 + (s * T2) ^ 2 = 1 / (8 * n) + (2 * n - 1) / (8 * n ^ 3) := by
    have : (s * T2) ^ 2 = s ^ 2 * T2 ^ 2 := by ring
    rw [this, hs]; simp only [c, T1, T2]; field_simp; ring
  refine ⟨?_, ?_, e3, ?_⟩
  · simp only [c, T1, T2]; field_simp; ring
  · simp only [c, T1, T2]; field_simp; ring
  · rw [e3]
    have : 0 ≤ (2 * n - 1) / (8 * n ^ 3) := by
      apply div_nonneg (by linarith) (by positivity)
    linarith

/-! ## 7. Welfare bounds (Theorem `thm:welfare`, Proposition `prop:gamma`) -/

/-- If the finite-game equilibrium maximises `SW - ½Σ‖a‖²` (observation-only fixed point), its welfare loss is
at most the optimum's own term minus its own. -/
theorem welfare_fixed_point (SWopt SWN ownOpt ownN : ℝ)
    (h : SWopt - ownOpt / 2 ≤ SWN - ownN / 2) : SWopt - SWN ≤ ownOpt / 2 - ownN / 2 := by
  linarith

/-- Coordinatewise maximisation behind the Gamma-maximin welfare bound:
`-σ x - ½ c x² ≤ σ² / (2c)` for `c > 0`, summed over coordinates. -/
theorem gamma_welfare {d : ℕ} (σ c x : Fin d → ℝ) (hc : ∀ k, 0 < c k) :
    ∑ k, (-(σ k * x k) - c k * x k ^ 2 / 2) ≤ ∑ k, σ k ^ 2 / (2 * c k) := by
  apply Finset.sum_le_sum; intro k _
  have hk := hc k
  rw [le_div_iff₀ (by positivity)]
  nlinarith [sq_nonneg (c k * x k + σ k)]

/-! ## 8. Vehicle-count congestion (Proposition `prop:d2`) -/

/-- Two types in one zone with dwell times `h₁, h₂`: the coupling matrix `g [[1/h₁, 1/h₂], [1/h₁, 1/h₂]]` has a
symmetric part with determinant `-g² (1/h₁ - 1/h₂)² / 4`, negative unless `h₁ = h₂` (monotonicity fails). -/
theorem d2_det (g h1 h2 : ℝ) :
    let a := g / h1
    let b := g / h2
    a * b - ((a + b) / 2) ^ 2 = -(g ^ 2 * (1 / h1 - 1 / h2) ^ 2) / 4 := by
  intro a b; simp only [a, b]; ring

/-- Per-type weights `w` symmetrise the coupling of every zone (`w a / h b z = w b / h a z`) iff the dwell-time
ratio of every pair of types is the same in all zones (rank one). -/
theorem d2_weights_iff {Θ Z : Type*} (h : Θ → Z → ℝ) (w : Θ → ℝ) (hh : ∀ a z, 0 < h a z)
    (hw : ∀ a, 0 < w a) :
    (∀ a b z, w a / h b z = w b / h a z) ↔ (∀ a b z, h a z / h b z = w b / w a) := by
  constructor
  · intro H a b z
    have := H a b z
    have h1 := (hh a z).ne'; have h2 := (hh b z).ne'; have h3 := (hw a).ne'; have h4 := (hw b).ne'
    field_simp at this ⊢; linarith
  · intro H a b z
    have := H a b z
    have h1 := (hh a z).ne'; have h2 := (hh b z).ne'; have h3 := (hw a).ne'; have h4 := (hw b).ne'
    field_simp at this ⊢; linarith

/-- Rank-one dwell times `h a z = η a * ζ z` with weights `1/η` give a symmetric weighted coupling. -/
theorem d2_rank_one {Θ Z : Type*} (η : Θ → ℝ) (ζ : Z → ℝ) (hη : ∀ a, 0 < η a) (hζ : ∀ z, 0 < ζ z) :
    ∀ a b z, (1 / η a) / (η b * ζ z) = (1 / η b) / (η a * ζ z) := by
  intro a b z
  have := (hη a).ne'; have := (hη b).ne'; have := (hζ z).ne'
  field_simp

/-! ## 9. Belief-width scaling (Corollary `cor:width`) -/

/-- With per-carrier contribution ranges at most `s` (in units of the weights), the uniform absorption width of
the Omega theorem, `σ_max · min{N-1, d+1, ·}`, is at most `(d+1) s`, which tends to zero with `s`. -/
theorem width_scaling (σmax s : ℝ) (N d : ℕ) (t3 : ℝ) (hσ : σmax ≤ s) (h0 : 0 ≤ σmax) :
    σmax * min (min ((N : ℝ) - 1) ((d : ℝ) + 1)) t3 ≤ ((d : ℝ) + 1) * s := by
  have hd : (0 : ℝ) ≤ (d : ℝ) + 1 := by positivity
  calc σmax * min (min ((N : ℝ) - 1) ((d : ℝ) + 1)) t3 ≤ σmax * ((d : ℝ) + 1) := by
        apply mul_le_mul_of_nonneg_left _ h0
        exact le_trans (min_le_left _ _) (min_le_right _ _)
    _ ≤ s * ((d : ℝ) + 1) := mul_le_mul_of_nonneg_right hσ hd
    _ = ((d : ℝ) + 1) * s := by ring

end MFG
