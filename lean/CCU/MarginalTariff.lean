/-
  Marginal tariff, `theory/new_algorithm_D/theory.tex`, Theorem 9 (`thm:mct`).

  Pure lumpy city game with finite player set `ι`, zone set `Z`, finite plan sets `P i`.
  Every carrier pays in every zone `T_z(q, Q) = κ_z q (Q - q) - (b_z/2) q²`.

  (a) `J^T_i(p;σ_{-i}) = SC(p,σ_{-i}) - SC(∅_i,σ_{-i})`: social cost is an exact potential;
  (b) pure equilibria = profiles no single carrier can improve socially; every social optimum
      is an equilibrium; best-response (improvement) dynamics strictly decrease `SC` and cannot
      cycle, so they stop after finitely many steps;
  (c) the cost is linear in the carrier's own service indicators;
  (d) the tariff identity and the revenue formula.

  Note on `∅_i`: the paper's empty plan (serve nobody, routing cost 0) need not belong to `P i`;
  we state (a) against the hypothetical contribution `(Σ_{j≠i} R_j, Q_{-i})`, which is what
  `SC(∅_i, σ_{-i})` is.
-/
import Mathlib

open Finset

namespace CCU
namespace MT

variable {ι Z : Type*} [Fintype ι] [DecidableEq ι] [Fintype Z]
variable {P : ι → Type*}

/-- Parameters: `b` demand slope, `κ = g r²` congestion slope (in delivery units), `α` intercept. -/
structure Par (Z : Type*) where
  α : Z → ℝ
  b : Z → ℝ
  κ : Z → ℝ

namespace Par
variable (π : Par Z)
/-- `m_z = b_z + κ_z`. -/
def m (z : Z) : ℝ := π.b z + π.κ z
/-- `m^S_z = b_z + 2 κ_z`. -/
def mS (z : Z) : ℝ := π.b z + 2 * π.κ z
end Par

/-- The tariff `T_z(q_{iz}, Q_z) = κ_z q (Q - q) - (b_z/2) q²`. -/
def tariff (π : Par Z) (z : Z) (q Q : ℝ) : ℝ := π.κ z * q * (Q - q) - π.b z / 2 * q ^ 2

/-- Social cost from aggregated data: routing total `Rs` and zone aggregates `Q`:
`Rs + Σ_z [-α_z Q_z + (m^S_z/2) Q_z²]` (D's form; `= Σ R + Σ[-αQ + b/2 Q² + g X²]`
since `κ = g r²`, see `CCU.DIP.SC`). -/
def SCof (π : Par Z) (Rs : ℝ) (Q : Z → ℝ) : ℝ := Rs + ∑ z, (-π.α z * Q z + π.mS z / 2 * Q z ^ 2)

/-- Delivery data of the game: `q i p z`, routing cost `R i p`, lot size `d i z`. -/
structure Game (ι Z : Type*) (P : ι → Type*) where
  q : ∀ i, P i → Z → ℝ
  R : ∀ i, P i → ℝ
  d : ι → Z → ℝ

variable (π : Par Z) (G : Game ι Z P)

/-- Zone aggregate at a profile. -/
def Qtot (σ : ∀ i, P i) (z : Z) : ℝ := ∑ i, G.q i (σ i) z

/-- Rivals' aggregate `Q_{-i,z}`. -/
def Qm (σ : ∀ i, P i) (i : ι) (z : Z) : ℝ := ∑ j ∈ univ.erase i, G.q j (σ j) z

/-- Social cost of a profile. -/
def SCp (σ : ∀ i, P i) : ℝ := SCof π (∑ i, G.R i (σ i)) (Qtot G σ)

/-- Carrier `i`'s cost of plan `p` against `σ_{-i}` under the tariff (no other charge). -/
def Jtar (i : ι) (p : P i) (σ : ∀ i, P i) : ℝ :=
  G.R i p + ∑ z, (G.q i p z * (-π.α z + π.m z * (G.d i z + Qm G σ i z))
    + tariff π z (G.q i p z) (G.q i p z + Qm G σ i z))

/-- Lumpy lots: `q_{iz}(p)² = d_{iz} q_{iz}(p)` (since `q ∈ {0, d}`). -/
def Lumpy : Prop := ∀ i (p : P i) z, G.q i p z ^ 2 = G.d i z * G.q i p z

theorem Qtot_update (σ : ∀ i, P i) (i : ι) (p : P i) (z : Z) :
    Qtot G (Function.update σ i p) z = G.q i p z + Qm G σ i z := by
  unfold Qtot Qm
  rw [← Finset.sum_erase_add _ _ (Finset.mem_univ i), Function.update_self, add_comm]
  congr 1
  refine Finset.sum_congr rfl (fun j hj => ?_)
  rw [Function.update_of_ne (Finset.ne_of_mem_erase hj)]

theorem Rsum_update (σ : ∀ i, P i) (i : ι) (p : P i) :
    ∑ j, G.R j (Function.update σ i p j)
      = G.R i p + ∑ j ∈ univ.erase i, G.R j (σ j) := by
  rw [← Finset.sum_erase_add _ _ (Finset.mem_univ i), Function.update_self, add_comm]
  congr 1
  refine Finset.sum_congr rfl (fun j hj => ?_)
  rw [Function.update_of_ne (Finset.ne_of_mem_erase hj)]

/-- **Theorem 9(a) (`thm:mct`).**
`J^T_i(p;σ_{-i}) = SC(p,σ_{-i}) - SC(∅_i,σ_{-i})`. -/
theorem tariff_cost_eq_social (hl : Lumpy G) (σ : ∀ i, P i) (i : ι) (p : P i) :
    Jtar π G i p σ
      = SCp π G (Function.update σ i p)
        - SCof π (∑ j ∈ univ.erase i, G.R j (σ j)) (Qm G σ i) := by
  unfold Jtar SCp SCof
  rw [Rsum_update]
  simp only [Qtot_update]
  have hz : ∀ z, G.q i p z * (-π.α z + π.m z * (G.d i z + Qm G σ i z))
      + tariff π z (G.q i p z) (G.q i p z + Qm G σ i z)
      = (-π.α z * (G.q i p z + Qm G σ i z) + π.mS z / 2 * (G.q i p z + Qm G σ i z) ^ 2)
        - (-π.α z * Qm G σ i z + π.mS z / 2 * Qm G σ i z ^ 2) := by
    intro z
    have h := hl i p z
    simp only [tariff, Par.m, Par.mS]
    linear_combination (-(π.b z + π.κ z)) * h
  rw [Finset.sum_congr rfl (fun z _ => hz z), Finset.sum_sub_distrib]
  ring

/-- **Theorem 9(c).** Given the rivals the tariff cost is linear in the carrier's own deliveries:
`J^T_i(p) = R_i(p) + Σ_z q_{iz}(p)(-α_z + (m^S_z/2) d_{iz} + m^S_z Q_{-i,z})`. -/
theorem tariff_cost_linear (hl : Lumpy G) (σ : ∀ i, P i) (i : ι) (p : P i) :
    Jtar π G i p σ
      = G.R i p + ∑ z, G.q i p z * (-π.α z + π.mS z / 2 * G.d i z + π.mS z * Qm G σ i z) := by
  unfold Jtar
  congr 1
  refine Finset.sum_congr rfl (fun z _ => ?_)
  have h := hl i p z
  simp only [tariff, Par.m, Par.mS]
  linear_combination (-(π.b z + π.κ z)) * h

/-- Exact potential: unilateral cost differences equal unilateral social-cost differences. -/
theorem tariff_exact_potential (hl : Lumpy G) (σ : ∀ i, P i) (i : ι) (p p' : P i) :
    Jtar π G i p σ - Jtar π G i p' σ
      = SCp π G (Function.update σ i p) - SCp π G (Function.update σ i p') := by
  rw [tariff_cost_eq_social π G hl, tariff_cost_eq_social π G hl]
  ring

/-- Pure Nash equilibrium of the tariff game. -/
def IsNE (σ : ∀ i, P i) : Prop := ∀ i (p : P i), Jtar π G i (σ i) σ ≤ Jtar π G i p σ

/-- Unilateral social optimum: no single carrier can lower `SC` by changing its plan. -/
def IsUnilateralOpt (σ : ∀ i, P i) : Prop :=
  ∀ i (p : P i), SCp π G σ ≤ SCp π G (Function.update σ i p)

/-- **Theorem 9(b).** The pure equilibria are exactly the unilateral social optima. -/
theorem isNE_iff (hl : Lumpy G) (σ : ∀ i, P i) : IsNE π G σ ↔ IsUnilateralOpt π G σ := by
  unfold IsNE IsUnilateralOpt
  refine forall_congr' (fun i => forall_congr' (fun p => ?_))
  have := tariff_exact_potential π G hl σ i (σ i) p
  rw [Function.update_eq_self] at this
  constructor <;> intro h <;> linarith

/-- **Theorem 9(b), price of stability 1.** Every social optimum is a pure equilibrium. -/
theorem socialOpt_isNE (hl : Lumpy G) (σ : ∀ i, P i)
    (hopt : ∀ τ : ∀ i, P i, SCp π G σ ≤ SCp π G τ) : IsNE π G σ :=
  (isNE_iff π G hl σ).2 (fun i p => hopt _)

/-- An improvement step of the tariff game: carrier `i` strictly lowers its own cost
(in particular every best-response step with an improvement is one). -/
def Step (σ τ : ∀ i, P i) : Prop :=
  ∃ i (p : P i), τ = Function.update σ i p ∧ Jtar π G i p σ < Jtar π G i (σ i) σ

/-- **Theorem 9(b), dynamics, monotonicity.** Every improvement step strictly lowers `SC`. -/
theorem step_lowers_SC (hl : Lumpy G) {σ τ : ∀ i, P i} (h : Step π G σ τ) :
    SCp π G τ < SCp π G σ := by
  obtain ⟨i, p, rfl, hlt⟩ := h
  have := tariff_exact_potential π G hl σ i p (σ i)
  rw [Function.update_eq_self] at this
  linarith

/-- **Theorem 9(b), dynamics, termination.** There is no infinite improvement sequence
(finite plan sets): best-response dynamics stop after finitely many steps. -/
theorem no_infinite_improvement [∀ i, Finite (P i)] (hl : Lumpy G) :
    ¬ ∃ f : ℕ → (∀ i, P i), ∀ n, Step π G (f n) (f (n + 1)) := by
  rintro ⟨f, hf⟩
  have hlt : ∀ n, SCp π G (f (n + 1)) < SCp π G (f n) := fun n => step_lowers_SC π G hl (hf n)
  have hanti : StrictAnti (fun n => SCp π G (f n)) := strictAnti_nat_of_succ_lt hlt
  have hinj : Function.Injective f := fun a b hab => hanti.injective (by simp [hab])
  exact not_injective_infinite_finite f hinj

/-- Every profile with no improving unilateral move is a pure equilibrium (so a dynamics that
stops, stops at an equilibrium) and the dynamics from any start reaches one. -/
theorem reaches_NE [∀ i, Finite (P i)] (hl : Lumpy G) (σ : ∀ i, P i) :
    ∃ τ, Relation.ReflTransGen (Step π G) σ τ ∧ IsNE π G τ := by
  haveI : Finite (∀ i, P i) := Pi.finite
  let r : (∀ i, P i) → (∀ i, P i) → Prop := fun a b => SCp π G a < SCp π G b
  haveI : IsTrans _ r := ⟨fun a b c h1 h2 => lt_trans h1 h2⟩
  haveI : IsIrrefl _ r := ⟨fun a h => lt_irrefl _ h⟩
  have hwf : WellFounded r := Finite.wellFounded_of_trans_of_irrefl r
  induction σ using hwf.induction with
  | _ σ ih =>
    by_cases hne : IsNE π G σ
    · exact ⟨σ, Relation.ReflTransGen.refl, hne⟩
    · unfold IsNE at hne
      push_neg at hne
      obtain ⟨i, p, hp⟩ := hne
      have hstep : Step π G σ (Function.update σ i p) := ⟨i, p, rfl, hp⟩
      obtain ⟨τ, hτ, hτne⟩ := ih _ (step_lowers_SC π G hl hstep)
      exact ⟨τ, Relation.ReflTransGen.head hstep hτ, hτne⟩

/-- **Theorem 9(d), identity.** If `q = d` then
`T_z(d,Q) = d(κ Q - (m/2) d) - (κ/2) d²`. -/
theorem tariff_eq_flat (z : Z) (dd Q : ℝ) :
    tariff π z dd Q = dd * (π.κ z * Q - π.m z / 2 * dd) - π.κ z / 2 * dd ^ 2 := by
  simp only [tariff, Par.m]
  ring

/-- **Theorem 9(d), revenue.** `Σ_i T_z(q_{iz},Q_z) = κ_z Q_z² - (κ_z + b_z/2) Σ_i q_{iz}²`. -/
theorem tariff_revenue (z : Z) (qz : ι → ℝ) :
    ∑ i, tariff π z (qz i) (∑ j, qz j)
      = π.κ z * (∑ j, qz j) ^ 2 - (π.κ z + π.b z / 2) * ∑ i, qz i ^ 2 := by
  simp only [tariff]
  have : ∀ i, π.κ z * qz i * (∑ j, qz j - qz i) - π.b z / 2 * qz i ^ 2
      = π.κ z * (qz i * ∑ j, qz j) - (π.κ z + π.b z / 2) * qz i ^ 2 := fun i => by ring
  rw [Finset.sum_congr rfl (fun i _ => this i), Finset.sum_sub_distrib, ← Finset.mul_sum,
    ← Finset.mul_sum, ← Finset.sum_mul]
  ring

end MT
end CCU
