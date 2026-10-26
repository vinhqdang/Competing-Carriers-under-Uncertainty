/-
  Aggregate-response pricing (ARP), `theory/new_algorithm_D/theory.tex`.

  * Theorem 1 (`thm:resolvent`, inequality (lip)): the equilibrium response
    `Q(u) = argmin_Q F(Q) + ⟨u,Q⟩` of a `‖·‖_m`-strongly convex `F` over a convex set satisfies
    `‖Q(u₁) - Q(u₂)‖_m ≤ ‖u₁ - u₂‖_{m⁻¹}`  (we prove the strong-monotonicity inequality, then (lip)).
  * Theorem 3 (`thm:rate`): the plain step (`θ = 1`) contracts at `ρ = max κ/m` in the
    `κ⁻¹`-norm; the damped step `0 < θ ≤ 2/(2+ρ)` contracts at `(1-θ)`, which is at most the paper's
    `sqrt(1 - 2θ(1+ρ)/(2+ρ))`; at `θ = 2/(2+ρ)` the ratio is `ρ/(2+ρ)`.
    The rate statements are proved for an arbitrary response map satisfying the strong-monotonicity
    inequality (hence for the non-diagonal case too), not only for the diagonal case.
  Norms are kept squared (`nk2`); the unsquared forms are given as corollaries.
-/
import Mathlib
import CCU.SegmentLimit

open Finset

namespace CCU
namespace ARP

variable {Z : Type*} [Fintype Z]

/-! ## Weighted quantities -/

/-- `‖v‖²_{κ⁻¹} = Σ_z v_z² / κ_z`. -/
noncomputable def nk2 (κ : Z → ℝ) (v : Z → ℝ) : ℝ := ∑ z, (κ z)⁻¹ * v z ^ 2

theorem nk2_nonneg {κ : Z → ℝ} (hκ : ∀ z, 0 < κ z) (v : Z → ℝ) : 0 ≤ nk2 κ v :=
  Finset.sum_nonneg (fun z _ => mul_nonneg (inv_nonneg.2 (hκ z).le) (sq_nonneg _))

/-- Strong monotonicity of the response `Q : u ↦ Q(u)` (consequence of `F` being `1`-strongly
convex in `‖·‖_m`): `⟨u₂ - u₁, Q(u₁) - Q(u₂)⟩ ≥ ‖Q(u₁) - Q(u₂)‖²_m`. -/
def StrongMono (m : Z → ℝ) (Qf : (Z → ℝ) → (Z → ℝ)) : Prop :=
  ∀ u₁ u₂, ∑ z, m z * (Qf u₁ z - Qf u₂ z) ^ 2 ≤ ∑ z, (u₂ z - u₁ z) * (Qf u₁ z - Qf u₂ z)

/-- **Inequality (lip) of Theorem 1**, squared:
`Σ m_z (Q₁ - Q₂)_z² ≤ Σ (u₁ - u₂)_z² / m_z`. -/
theorem lip_of_strongMono {m : Z → ℝ} (hm : ∀ z, 0 < m z) {Qf : (Z → ℝ) → (Z → ℝ)}
    (h : StrongMono m Qf) (u₁ u₂ : Z → ℝ) :
    ∑ z, m z * (Qf u₁ z - Qf u₂ z) ^ 2 ≤ ∑ z, (m z)⁻¹ * (u₁ z - u₂ z) ^ 2 := by
  have hpt : ∀ z, (u₂ z - u₁ z) * (Qf u₁ z - Qf u₂ z)
      ≤ (m z)⁻¹ * (u₁ z - u₂ z) ^ 2 / 2 + m z * (Qf u₁ z - Qf u₂ z) ^ 2 / 2 := by
    intro z
    have hz := hm z
    have : (u₂ z - u₁ z) * (Qf u₁ z - Qf u₂ z)
        = (m z)⁻¹ * (u₁ z - u₂ z) ^ 2 / 2 + m z * (Qf u₁ z - Qf u₂ z) ^ 2 / 2
          - (m z)⁻¹ / 2 * (m z * (Qf u₁ z - Qf u₂ z) + (u₂ z - u₁ z)) ^ 2 := by
      field_simp
      ring
    rw [this]
    have : 0 ≤ (m z)⁻¹ / 2 * (m z * (Qf u₁ z - Qf u₂ z) + (u₂ z - u₁ z)) ^ 2 :=
      mul_nonneg (by positivity) (sq_nonneg _)
    linarith
  have h1 := h u₁ u₂
  have h2 := Finset.sum_le_sum (fun z (_ : z ∈ (univ : Finset Z)) => hpt z)
  rw [Finset.sum_add_distrib, ← Finset.sum_div, ← Finset.sum_div] at h2
  linarith

/-- With `κ ≤ ρ m` (i.e. `1/m ≤ ρ/κ`): `‖u‖²_{m⁻¹} ≤ ρ ‖u‖²_{κ⁻¹}`. -/
theorem nm_le_rho_nk {m κ : Z → ℝ} (hm : ∀ z, 0 < m z) (hκ : ∀ z, 0 < κ z) {ρ : ℝ}
    (hρ : ∀ z, κ z ≤ ρ * m z) (v : Z → ℝ) :
    ∑ z, (m z)⁻¹ * v z ^ 2 ≤ ρ * nk2 κ v := by
  unfold nk2
  rw [Finset.mul_sum]
  refine Finset.sum_le_sum (fun z _ => ?_)
  have h1 : (m z)⁻¹ ≤ ρ * (κ z)⁻¹ := by
    rw [inv_eq_one_div, mul_one_div, div_le_div_iff₀ (hm z) (hκ z)]
    linarith [hρ z]
  nlinarith [sq_nonneg (v z)]

/-! ## Theorem 3 -/

/-- The tangent map `T(u) = κ ⊙ Q(u) - c` (with `c = (m/2) d̄`). -/
def Tmap (κ c : Z → ℝ) (Qf : (Z → ℝ) → (Z → ℝ)) (u : Z → ℝ) : Z → ℝ :=
  fun z => κ z * Qf u z - c z

/-- The damped rule `u⁺ = (1 - θ) u + θ T(u)`. -/
def Tdamp (θ : ℝ) (κ c : Z → ℝ) (Qf : (Z → ℝ) → (Z → ℝ)) (u : Z → ℝ) : Z → ℝ :=
  fun z => (1 - θ) * u z + θ * Tmap κ c Qf u z

/-- **Theorem 3(a) (plain step).** With `m = b + κ`, `κ ≤ ρ m`, `ρ ≥ 0` and a strongly monotone
response: `‖T u₁ - T u₂‖²_{κ⁻¹} ≤ ρ² ‖u₁ - u₂‖²_{κ⁻¹}`. -/
theorem plain_contraction_sq {b κ c : Z → ℝ} (hb : ∀ z, 0 < b z) (hκ : ∀ z, 0 < κ z)
    {ρ : ℝ} (hρ0 : 0 ≤ ρ) (hρ : ∀ z, κ z ≤ ρ * (b z + κ z)) {Qf : (Z → ℝ) → (Z → ℝ)}
    (h : StrongMono (fun z => b z + κ z) Qf) (u₁ u₂ : Z → ℝ) :
    nk2 κ (fun z => Tmap κ c Qf u₁ z - Tmap κ c Qf u₂ z)
      ≤ ρ ^ 2 * nk2 κ (fun z => u₁ z - u₂ z) := by
  have hm : ∀ z, 0 < b z + κ z := fun z => by linarith [hb z, hκ z]
  have hpt : ∀ z, (κ z)⁻¹ * (Tmap κ c Qf u₁ z - Tmap κ c Qf u₂ z) ^ 2
      = κ z * (Qf u₁ z - Qf u₂ z) ^ 2 := by
    intro z
    have := (hκ z).ne'
    simp only [Tmap]
    field_simp
    ring
  have h1 : nk2 κ (fun z => Tmap κ c Qf u₁ z - Tmap κ c Qf u₂ z)
      = ∑ z, κ z * (Qf u₁ z - Qf u₂ z) ^ 2 := by
    unfold nk2
    exact Finset.sum_congr rfl (fun z _ => hpt z)
  have h2 : ∑ z, κ z * (Qf u₁ z - Qf u₂ z) ^ 2
      ≤ ρ * ∑ z, (b z + κ z) * (Qf u₁ z - Qf u₂ z) ^ 2 := by
    rw [Finset.mul_sum]
    refine Finset.sum_le_sum (fun z _ => ?_)
    have := mul_le_mul_of_nonneg_right (hρ z) (sq_nonneg (Qf u₁ z - Qf u₂ z))
    linarith
  have h3 := lip_of_strongMono hm h u₁ u₂
  have h4 := nm_le_rho_nk hm hκ hρ (fun z => u₁ z - u₂ z)
  rw [h1]
  calc ∑ z, κ z * (Qf u₁ z - Qf u₂ z) ^ 2
      ≤ ρ * ∑ z, (b z + κ z) * (Qf u₁ z - Qf u₂ z) ^ 2 := h2
    _ ≤ ρ * ∑ z, (b z + κ z)⁻¹ * (u₁ z - u₂ z) ^ 2 := mul_le_mul_of_nonneg_left h3 hρ0
    _ ≤ ρ * (ρ * nk2 κ (fun z => u₁ z - u₂ z)) := mul_le_mul_of_nonneg_left h4 hρ0
    _ = ρ ^ 2 * nk2 κ (fun z => u₁ z - u₂ z) := by ring

/-- **Theorem 3(b) (damped step).** For `0 < θ` with `θ (2 + ρ) ≤ 2`:
`‖T_θ u₁ - T_θ u₂‖²_{κ⁻¹} ≤ (1 - θ)² ‖u₁ - u₂‖²_{κ⁻¹}`. -/
theorem damped_contraction_sq {b κ c : Z → ℝ} (hb : ∀ z, 0 < b z) (hκ : ∀ z, 0 < κ z)
    {ρ : ℝ} (hρ0 : 0 ≤ ρ) (hρ : ∀ z, κ z ≤ ρ * (b z + κ z)) {Qf : (Z → ℝ) → (Z → ℝ)}
    (h : StrongMono (fun z => b z + κ z) Qf) {θ : ℝ} (hθ0 : 0 < θ) (hθ : θ * (2 + ρ) ≤ 2)
    (u₁ u₂ : Z → ℝ) :
    nk2 κ (fun z => Tdamp θ κ c Qf u₁ z - Tdamp θ κ c Qf u₂ z)
      ≤ (1 - θ) ^ 2 * nk2 κ (fun z => u₁ z - u₂ z) := by
  have hm : ∀ z, 0 < b z + κ z := fun z => by linarith [hb z, hκ z]
  have hθ1 : θ ≤ 1 := by nlinarith
  have hpt : ∀ z, (κ z)⁻¹ * (Tdamp θ κ c Qf u₁ z - Tdamp θ κ c Qf u₂ z) ^ 2
      = (1 - θ) ^ 2 * ((κ z)⁻¹ * (u₁ z - u₂ z) ^ 2)
        + 2 * θ * (1 - θ) * ((u₁ z - u₂ z) * (Qf u₁ z - Qf u₂ z))
        + θ ^ 2 * (κ z * (Qf u₁ z - Qf u₂ z) ^ 2) := by
    intro z
    have := (hκ z).ne'
    simp only [Tdamp, Tmap]
    field_simp
    ring
  have h1 : nk2 κ (fun z => Tdamp θ κ c Qf u₁ z - Tdamp θ κ c Qf u₂ z)
      = (1 - θ) ^ 2 * nk2 κ (fun z => u₁ z - u₂ z)
        + 2 * θ * (1 - θ) * ∑ z, (u₁ z - u₂ z) * (Qf u₁ z - Qf u₂ z)
        + θ ^ 2 * ∑ z, κ z * (Qf u₁ z - Qf u₂ z) ^ 2 := by
    unfold nk2
    rw [Finset.sum_congr rfl (fun z _ => hpt z), Finset.sum_add_distrib, Finset.sum_add_distrib,
      ← Finset.mul_sum, ← Finset.mul_sum, ← Finset.mul_sum]
  -- strong monotonicity: Σ e w ≤ - Σ m w²
  have hH : ∑ z, (u₁ z - u₂ z) * (Qf u₁ z - Qf u₂ z)
      ≤ - ∑ z, (b z + κ z) * (Qf u₁ z - Qf u₂ z) ^ 2 := by
    have := h u₁ u₂
    have e : ∑ z, (u₂ z - u₁ z) * (Qf u₁ z - Qf u₂ z)
        = - ∑ z, (u₁ z - u₂ z) * (Qf u₁ z - Qf u₂ z) := by
      rw [← Finset.sum_neg_distrib]
      exact Finset.sum_congr rfl (fun z _ => by ring)
    linarith
  have hcoef : ∑ z, κ z * (Qf u₁ z - Qf u₂ z) ^ 2 * θ
      ≤ ∑ z, 2 * (1 - θ) * ((b z + κ z) * (Qf u₁ z - Qf u₂ z) ^ 2) := by
    refine Finset.sum_le_sum (fun z _ => ?_)
    have e1 : θ * (κ z) ≤ θ * (ρ * (b z + κ z)) := mul_le_mul_of_nonneg_left (hρ z) hθ0.le
    have e2 : 0 ≤ (b z + κ z) * (2 - θ * (2 + ρ)) :=
      mul_nonneg (hm z).le (sub_nonneg.2 hθ)
    have e3 : 0 ≤ (Qf u₁ z - Qf u₂ z) ^ 2 := sq_nonneg _
    nlinarith [mul_nonneg e3 e2, mul_nonneg e3 (mul_nonneg hθ0.le (hm z).le),
      mul_le_mul_of_nonneg_left e1 e3]
  have hS : θ * ∑ z, κ z * (Qf u₁ z - Qf u₂ z) ^ 2
      ≤ 2 * (1 - θ) * ∑ z, (b z + κ z) * (Qf u₁ z - Qf u₂ z) ^ 2 := by
    have : ∑ z, κ z * (Qf u₁ z - Qf u₂ z) ^ 2 * θ = θ * ∑ z, κ z * (Qf u₁ z - Qf u₂ z) ^ 2 := by
      rw [Finset.mul_sum]
      exact Finset.sum_congr rfl (fun z _ => by ring)
    rw [← this]
    rw [← Finset.mul_sum] at hcoef
    exact hcoef
  rw [h1]
  have hθ' : 0 ≤ 2 * θ * (1 - θ) := by nlinarith
  nlinarith [mul_le_mul_of_nonneg_left hH hθ', mul_le_mul_of_nonneg_left hS hθ0.le]

/-- The damped factor `(1-θ)²` is at most the paper's `1 - 2θ(1+ρ)/(2+ρ)`. -/
theorem damped_factor_le {ρ θ : ℝ} (hρ0 : 0 ≤ ρ) (hθ0 : 0 < θ) (hθ : θ * (2 + ρ) ≤ 2) :
    (1 - θ) ^ 2 ≤ 1 - 2 * θ * (1 + ρ) / (2 + ρ) := by
  have hpos : 0 < 2 + ρ := by linarith
  have : 1 - 2 * θ * (1 + ρ) / (2 + ρ) - (1 - θ) ^ 2 = θ * (2 - θ * (2 + ρ)) / (2 + ρ) := by
    field_simp
    ring
  have h2 : 0 ≤ θ * (2 - θ * (2 + ρ)) / (2 + ρ) :=
    div_nonneg (mul_nonneg hθ0.le (sub_nonneg.2 hθ)) hpos.le
  linarith

/-- At `θ = 2/(2+ρ)` the damped ratio is `ρ/(2+ρ)`. -/
theorem damped_ratio_opt {ρ : ℝ} (hρ0 : 0 ≤ ρ) : 1 - 2 / (2 + ρ) = ρ / (2 + ρ) := by
  have : (2 + ρ) ≠ 0 := by positivity
  field_simp
  ring

/-! ### Norm form and iteration -/

/-- `‖v‖_{κ⁻¹}`. -/
noncomputable def nk (κ : Z → ℝ) (v : Z → ℝ) : ℝ := Real.sqrt (nk2 κ v)

theorem nk_le_of_sq {κ : Z → ℝ} {v w : Z → ℝ} {λ' : ℝ} (hλ : 0 ≤ λ')
    (h : nk2 κ v ≤ λ' ^ 2 * nk2 κ w) : nk κ v ≤ λ' * nk κ w := by
  unfold nk
  calc Real.sqrt (nk2 κ v) ≤ Real.sqrt (λ' ^ 2 * nk2 κ w) := Real.sqrt_le_sqrt h
    _ = λ' * Real.sqrt (nk2 κ w) := by
      rw [Real.sqrt_mul (sq_nonneg λ'), Real.sqrt_sq hλ]

/-- **Theorem 3(a), norm form:** `‖u⁺ - u*⁺‖ ≤ ρ ‖u - u*‖` for the plain step. -/
theorem plain_contraction {b κ c : Z → ℝ} (hb : ∀ z, 0 < b z) (hκ : ∀ z, 0 < κ z)
    {ρ : ℝ} (hρ0 : 0 ≤ ρ) (hρ : ∀ z, κ z ≤ ρ * (b z + κ z)) {Qf : (Z → ℝ) → (Z → ℝ)}
    (h : StrongMono (fun z => b z + κ z) Qf) (u₁ u₂ : Z → ℝ) :
    nk κ (fun z => Tmap κ c Qf u₁ z - Tmap κ c Qf u₂ z) ≤ ρ * nk κ (fun z => u₁ z - u₂ z) :=
  nk_le_of_sq hρ0 (plain_contraction_sq hb hκ hρ0 hρ h u₁ u₂)

/-- **Theorem 3(b), norm form** (ratio `1 - θ`; at `θ = 2/(2+ρ)` it is `ρ/(2+ρ)`). -/
theorem damped_contraction {b κ c : Z → ℝ} (hb : ∀ z, 0 < b z) (hκ : ∀ z, 0 < κ z)
    {ρ : ℝ} (hρ0 : 0 ≤ ρ) (hρ : ∀ z, κ z ≤ ρ * (b z + κ z)) {Qf : (Z → ℝ) → (Z → ℝ)}
    (h : StrongMono (fun z => b z + κ z) Qf) {θ : ℝ} (hθ0 : 0 < θ) (hθ : θ * (2 + ρ) ≤ 2)
    (u₁ u₂ : Z → ℝ) :
    nk κ (fun z => Tdamp θ κ c Qf u₁ z - Tdamp θ κ c Qf u₂ z)
      ≤ (1 - θ) * nk κ (fun z => u₁ z - u₂ z) :=
  nk_le_of_sq (by nlinarith) (damped_contraction_sq hb hκ hρ0 hρ h hθ0 hθ u₁ u₂)

/-- The paper's form of the damped rate: `‖·‖ ≤ sqrt(1 - 2θ(1+ρ)/(2+ρ)) ‖·‖`. -/
theorem damped_contraction_paper {b κ c : Z → ℝ} (hb : ∀ z, 0 < b z) (hκ : ∀ z, 0 < κ z)
    {ρ : ℝ} (hρ0 : 0 ≤ ρ) (hρ : ∀ z, κ z ≤ ρ * (b z + κ z)) {Qf : (Z → ℝ) → (Z → ℝ)}
    (h : StrongMono (fun z => b z + κ z) Qf) {θ : ℝ} (hθ0 : 0 < θ) (hθ : θ * (2 + ρ) ≤ 2)
    (u₁ u₂ : Z → ℝ) :
    nk κ (fun z => Tdamp θ κ c Qf u₁ z - Tdamp θ κ c Qf u₂ z)
      ≤ Real.sqrt (1 - 2 * θ * (1 + ρ) / (2 + ρ)) * nk κ (fun z => u₁ z - u₂ z) := by
  have h1 := damped_contraction_sq hb hκ hρ0 hρ h hθ0 hθ u₁ u₂
  have h2 := damped_factor_le hρ0 hθ0 hθ
  have h3 : nk2 κ (fun z => Tdamp θ κ c Qf u₁ z - Tdamp θ κ c Qf u₂ z)
      ≤ (Real.sqrt (1 - 2 * θ * (1 + ρ) / (2 + ρ))) ^ 2 * nk2 κ (fun z => u₁ z - u₂ z) := by
    rw [Real.sq_sqrt (le_trans (sq_nonneg _) h2)]
    exact h1.trans (mul_le_mul_of_nonneg_right h2 (nk2_nonneg hκ _))
  exact nk_le_of_sq (Real.sqrt_nonneg _) h3

/-- Iteration of a contraction with a fixed point: `‖u_t - u*‖ ≤ λ^t ‖u₀ - u*‖`. -/
theorem iterate_bound {κ : Z → ℝ} (f : (Z → ℝ) → (Z → ℝ)) (ustar : Z → ℝ) {λ' : ℝ}
    (hλ : 0 ≤ λ')
    (hcontr : ∀ a b, nk κ (fun z => f a z - f b z) ≤ λ' * nk κ (fun z => a z - b z))
    (hfix : f ustar = ustar) (u : ℕ → (Z → ℝ)) (hstep : ∀ t, u (t + 1) = f (u t)) :
    ∀ t, nk κ (fun z => u t z - ustar z) ≤ λ' ^ t * nk κ (fun z => u 0 z - ustar z) := by
  intro t
  induction t with
  | zero => simp
  | succ t ih =>
    have e : (fun z => u (t + 1) z - ustar z) = fun z => f (u t) z - f ustar z := by
      funext z
      rw [hstep t, hfix]
    rw [e]
    calc nk κ (fun z => f (u t) z - f ustar z)
        ≤ λ' * nk κ (fun z => u t z - ustar z) := hcontr _ _
      _ ≤ λ' * (λ' ^ t * nk κ (fun z => u 0 z - ustar z)) :=
          mul_le_mul_of_nonneg_left ih hλ
      _ = λ' ^ (t + 1) * nk κ (fun z => u 0 z - ustar z) := by ring

/-- A fixed point of `T` is a fixed point of every damped step. -/
theorem damp_fixed {κ c : Z → ℝ} {Qf : (Z → ℝ) → (Z → ℝ)} {ustar : Z → ℝ} (θ : ℝ)
    (h : Tmap κ c Qf ustar = ustar) : Tdamp θ κ c Qf ustar = ustar := by
  funext z
  simp only [Tdamp]
  rw [h]
  ring

/-- **Theorem 3, rounds.** Plain rule: after `t` rounds the charge is within `ρ^t ‖u⁰ - u*‖`. -/
theorem plain_rounds {b κ c : Z → ℝ} (hb : ∀ z, 0 < b z) (hκ : ∀ z, 0 < κ z)
    {ρ : ℝ} (hρ0 : 0 ≤ ρ) (hρ : ∀ z, κ z ≤ ρ * (b z + κ z)) {Qf : (Z → ℝ) → (Z → ℝ)}
    (h : StrongMono (fun z => b z + κ z) Qf) (ustar : Z → ℝ) (hfix : Tmap κ c Qf ustar = ustar)
    (u : ℕ → (Z → ℝ)) (hstep : ∀ t, u (t + 1) = Tmap κ c Qf (u t)) :
    ∀ t, nk κ (fun z => u t z - ustar z) ≤ ρ ^ t * nk κ (fun z => u 0 z - ustar z) :=
  iterate_bound (κ := κ) (Tmap κ c Qf) ustar hρ0 (plain_contraction hb hκ hρ0 hρ h) hfix u hstep

/-- **Theorem 3, rounds.** Damped rule with `θ = 2/(2+ρ)`: ratio `ρ/(2+ρ)` per round. -/
theorem damped_rounds {b κ c : Z → ℝ} (hb : ∀ z, 0 < b z) (hκ : ∀ z, 0 < κ z)
    {ρ : ℝ} (hρ0 : 0 ≤ ρ) (hρ : ∀ z, κ z ≤ ρ * (b z + κ z)) {Qf : (Z → ℝ) → (Z → ℝ)}
    (h : StrongMono (fun z => b z + κ z) Qf) (ustar : Z → ℝ) (hfix : Tmap κ c Qf ustar = ustar)
    (u : ℕ → (Z → ℝ)) (hstep : ∀ t, u (t + 1) = Tdamp (2 / (2 + ρ)) κ c Qf (u t)) :
    ∀ t, nk κ (fun z => u t z - ustar z)
      ≤ (ρ / (2 + ρ)) ^ t * nk κ (fun z => u 0 z - ustar z) := by
  have hpos : 0 < 2 + ρ := by linarith
  have hθ0 : 0 < 2 / (2 + ρ) := by positivity
  have hθ : 2 / (2 + ρ) * (2 + ρ) ≤ 2 := by
    rw [div_mul_cancel₀ _ hpos.ne']
  have hc := damped_contraction hb hκ hρ0 hρ h hθ0 hθ
  rw [damped_ratio_opt hρ0] at hc
  exact iterate_bound (κ := κ) (Tdamp (2 / (2 + ρ)) κ c Qf) ustar (by positivity) hc
    (damp_fixed _ hfix) u hstep

/-- **Theorem 3, last claim (squared).** `‖Q(u) - Q(u')‖²_m ≤ ρ ‖u - u'‖²_{κ⁻¹}`
(so the aggregate is within `√ρ ρ^t ‖u⁰ - u*‖` of `Q^∞` in `‖·‖_m`). -/
theorem aggregate_bound {b κ : Z → ℝ} (hb : ∀ z, 0 < b z) (hκ : ∀ z, 0 < κ z)
    {ρ : ℝ} (hρ : ∀ z, κ z ≤ ρ * (b z + κ z)) {Qf : (Z → ℝ) → (Z → ℝ)}
    (h : StrongMono (fun z => b z + κ z) Qf) (u₁ u₂ : Z → ℝ) :
    ∑ z, (b z + κ z) * (Qf u₁ z - Qf u₂ z) ^ 2 ≤ ρ * nk2 κ (fun z => u₁ z - u₂ z) := by
  have hm : ∀ z, 0 < b z + κ z := fun z => by linarith [hb z, hκ z]
  exact (lip_of_strongMono hm h u₁ u₂).trans (nm_le_rho_nk hm hκ hρ _)

/-! ## Theorem 1 from strong convexity -/

/-- Segment expansion of a weighted square sum. -/
theorem wsq_seg (m : Z → ℝ) (Q₁ Q₂ : Z → ℝ) (t : ℝ) :
    ∑ z, m z * ((1 - t) * Q₁ z + t * Q₂ z) ^ 2
      = (1 - t) ^ 2 * ∑ z, m z * Q₁ z ^ 2 + 2 * ((1 - t) * t) * ∑ z, m z * (Q₁ z * Q₂ z)
        + t ^ 2 * ∑ z, m z * Q₂ z ^ 2 := by
  rw [Finset.mul_sum, Finset.mul_sum, Finset.mul_sum, ← Finset.sum_add_distrib,
    ← Finset.sum_add_distrib]
  exact Finset.sum_congr rfl (fun z _ => by ring)

theorem ip_seg (u Q₁ Q₂ : Z → ℝ) (t : ℝ) :
    ∑ z, u z * ((1 - t) * Q₁ z + t * Q₂ z)
      = (1 - t) * ∑ z, u z * Q₁ z + t * ∑ z, u z * Q₂ z := by
  rw [Finset.mul_sum, Finset.mul_sum, ← Finset.sum_add_distrib]
  exact Finset.sum_congr rfl (fun z _ => by ring)

/-- **Theorem 1 (core).** If `F - ½‖·‖²_m` is convex on the convex set `𝒬` and `Q₁` minimises
`F + ⟨u,·⟩` on `𝒬`, then for every `Q₂ ∈ 𝒬`:
`F(Q₁) + ⟨u,Q₁⟩ + ½ ‖Q₂ - Q₁‖²_m ≤ F(Q₂) + ⟨u,Q₂⟩`. -/
theorem strong_convex_growth {𝒬 : Set (Z → ℝ)} (h𝒬 : Convex ℝ 𝒬) {m : Z → ℝ}
    (hm : ∀ z, 0 ≤ m z) (F : (Z → ℝ) → ℝ)
    (hF : ConvexOn ℝ 𝒬 (fun Q => F Q - (1 / 2) * ∑ z, m z * Q z ^ 2)) (u : Z → ℝ)
    {Q₁ Q₂ : Z → ℝ} (hQ₁ : Q₁ ∈ 𝒬) (hQ₂ : Q₂ ∈ 𝒬)
    (hmin : ∀ Q ∈ 𝒬, F Q₁ + ∑ z, u z * Q₁ z ≤ F Q + ∑ z, u z * Q z) :
    F Q₁ + ∑ z, u z * Q₁ z + (1 / 2) * ∑ z, m z * (Q₂ z - Q₁ z) ^ 2
      ≤ F Q₂ + ∑ z, u z * Q₂ z := by
  have hD : ∑ z, m z * (Q₂ z - Q₁ z) ^ 2
      = ∑ z, m z * Q₁ z ^ 2 - 2 * ∑ z, m z * (Q₁ z * Q₂ z) + ∑ z, m z * Q₂ z ^ 2 := by
    rw [Finset.mul_sum, ← Finset.sum_sub_distrib, ← Finset.sum_add_distrib]
    exact Finset.sum_congr rfl (fun z _ => by ring)
  have hDnn : 0 ≤ ∑ z, m z * (Q₂ z - Q₁ z) ^ 2 :=
    Finset.sum_nonneg (fun z _ => mul_nonneg (hm z) (sq_nonneg _))
  have key : 0 ≤ ((F Q₂ + ∑ z, u z * Q₂ z) - (F Q₁ + ∑ z, u z * Q₁ z)
      - (1 / 2) * ∑ z, m z * (Q₂ z - Q₁ z) ^ 2) := by
    refine nonneg_of_forall_small (B := (1 / 2) * ∑ z, m z * (Q₂ z - Q₁ z) ^ 2)
      (by linarith) (fun t ht0 ht1 => ?_)
    have hmem : (1 - t) • Q₁ + t • Q₂ ∈ 𝒬 := h𝒬 hQ₁ hQ₂ (by linarith) ht0.le (by ring)
    have hc := hF.2 hQ₁ hQ₂ (a := 1 - t) (b := t) (by linarith) ht0.le (by ring)
    have hm' := hmin _ hmem
    have e1 : ∀ z, ((1 - t) • Q₁ + t • Q₂) z = (1 - t) * Q₁ z + t * Q₂ z := fun z => by
      simp
    simp only [e1, smul_eq_mul, wsq_seg, ip_seg] at hc hm'
    rw [hD]
    nlinarith
  linarith

/-- **Theorem 1 ⇒ strong monotonicity.** If every `Q(u)` minimises `F + ⟨u,·⟩` over `𝒬`
(`F - ½‖·‖²_m` convex), then `Q` is strongly monotone, hence satisfies (lip). -/
theorem strongMono_of_strongConvex {𝒬 : Set (Z → ℝ)} (h𝒬 : Convex ℝ 𝒬) {m : Z → ℝ}
    (hm : ∀ z, 0 ≤ m z) (F : (Z → ℝ) → ℝ)
    (hF : ConvexOn ℝ 𝒬 (fun Q => F Q - (1 / 2) * ∑ z, m z * Q z ^ 2))
    (Qf : (Z → ℝ) → (Z → ℝ)) (hmem : ∀ u, Qf u ∈ 𝒬)
    (hmin : ∀ u, ∀ Q ∈ 𝒬, F (Qf u) + ∑ z, u z * Qf u z ≤ F Q + ∑ z, u z * Q z) :
    StrongMono m Qf := by
  intro u₁ u₂
  have h1 := strong_convex_growth h𝒬 hm F hF u₁ (hmem u₁) (hmem u₂) (hmin u₁)
  have h2 := strong_convex_growth h𝒬 hm F hF u₂ (hmem u₂) (hmem u₁) (hmin u₂)
  have e : ∑ z, (u₂ z - u₁ z) * (Qf u₁ z - Qf u₂ z)
      = ∑ z, u₁ z * Qf u₂ z + ∑ z, u₂ z * Qf u₁ z
        - ∑ z, u₁ z * Qf u₁ z - ∑ z, u₂ z * Qf u₂ z := by
    simp only [← Finset.sum_add_distrib, ← Finset.sum_sub_distrib]
    exact Finset.sum_congr rfl (fun z _ => by ring)
  have e2 : ∑ z, m z * (Qf u₂ z - Qf u₁ z) ^ 2 = ∑ z, m z * (Qf u₁ z - Qf u₂ z) ^ 2 :=
    Finset.sum_congr rfl (fun z _ => by ring)
  rw [e2] at h1
  rw [e]
  linarith

end ARP
end CCU
