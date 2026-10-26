/-
  Dual implementation pricing (DIP), `theory/new_algorithm_C/theory.tex`.

  * Proposition 1 : two instruments collapse to one number per zone.
  * Lemma 2       : exact potential-welfare identity with the lot-asymmetry term
                    (pure lumpy game, finite player and zone sets, all of ℝ).
  * Theorem 5     : exact implementation of the (convexified) social optimum under
                    symmetric lots (`thm:convex`), over an abstract convex feasible set.
  * Theorem 7     : the charges that make a target an equilibrium form a polyhedron;
                    one best response separates (`thm:cut`, parts (a) and the counting of (b)).

  Notation (as in the paper):  κ_z = g_z r²,  m_z = b_z + κ_z,  m^S_z = b_z + 2 κ_z.
-/
import Mathlib
import CCU.SegmentLimit

open Finset

namespace CCU
namespace DIP

variable {ι Z : Type*} [Fintype ι] [Fintype Z]

/-! ## Notation -/

/-- `κ_z = g_z r²`: congestion slope in delivery units. -/
def kap (g : Z → ℝ) (r : ℝ) (z : Z) : ℝ := g z * r ^ 2
/-- `m_z = b_z + κ_z`: the slope the carriers face. -/
def mC (b g : Z → ℝ) (r : ℝ) (z : Z) : ℝ := b z + kap g r z
/-- `m^S_z = b_z + 2 κ_z`: the social slope. -/
def mS (b g : Z → ℝ) (r : ℝ) (z : Z) : ℝ := b z + 2 * kap g r z

/-- Zone aggregate `Q_z = Σ_i q_{iz}`. -/
def Qagg (q : ι → Z → ℝ) (z : Z) : ℝ := ∑ i, q i z

/-! ## Proposition 1 (two instruments, one number per zone) -/

/-- (a) a per-delivery charge `s` and a per-vehicle-hour charge `t` (vehicle-hours `r·q`)
cost `⟨u, q⟩` with `u = s + r t`. -/
theorem instr_a (s t u : Z → ℝ) (r : ℝ) (hu : ∀ z, u z = s z + r * t z) (q : Z → ℝ) :
    ∑ z, (s z * q z + t z * (r * q z)) = ∑ z, u z * q z :=
  Finset.sum_congr rfl (fun z _ => by rw [hu z]; ring)

/-- (b) every `u` is realised by a uniform per-delivery charge `s = min_{z ∈ Z₊} u_z`
and non-negative congestion charges `t_z = (u_z - s)/r` on the zones `Z₊` with a lot. -/
theorem instr_b {r : ℝ} (hr : 0 < r) (u : Z → ℝ) (Zp : Finset Z) (hne : Zp.Nonempty) :
    ∃ s : ℝ, ∃ t : Z → ℝ, (∀ z ∈ Zp, 0 ≤ t z ∧ s + r * t z = u z) ∧ (∃ z ∈ Zp, s = u z) := by
  obtain ⟨z0, hz0, hmin⟩ := Finset.exists_min_image Zp u hne
  refine ⟨u z0, fun z => (u z - u z0) / r, fun z hz => ⟨?_, ?_⟩, ⟨z0, hz0, rfl⟩⟩
  · exact div_nonneg (sub_nonneg.2 (hmin z hz)) hr.le
  · field_simp
    ring

/-! ## Lemma 2 (identity) in the pure lumpy game -/

variable (α b g : Z → ℝ) (r : ℝ)

/-- The carriers' exact potential `Φ_u` at a profile with routing costs `R_i`, deliveries `q_{iz}`. -/
def Phi (u : Z → ℝ) (R : ι → ℝ) (q : ι → Z → ℝ) : ℝ :=
  ∑ i, R i + ∑ z, (-α z * Qagg q z + mC b g r z / 2 * (Qagg q z ^ 2 + ∑ i, q i z ^ 2)
    + u z * Qagg q z)

/-- Social cost `SC = Σ R_i + Σ_z [-α_z Q_z + b_z/2 Q_z² + g_z X_z²]`, `X_z = Σ_i r q_{iz}`. -/
def SC (R : ι → ℝ) (q : ι → Z → ℝ) : ℝ :=
  ∑ i, R i + ∑ z, (-α z * Qagg q z + b z / 2 * Qagg q z ^ 2 + g z * (∑ i, r * q i z) ^ 2)

/-- Lot-asymmetry term `L(σ) = Σ_{i,z} (m_z/2)(d_{iz} - d̄_z) q_{iz}`. -/
def Lasym (d : ι → Z → ℝ) (dbar : Z → ℝ) (q : ι → Z → ℝ) : ℝ :=
  ∑ i, ∑ z, mC b g r z / 2 * (d i z - dbar z) * q i z

/-- **Lemma 2 (DIP, `lem:identity`).**  For lumpy lots (`q_{iz}² = d_{iz} q_{iz}`), any
`Q°, d̄` and `u = κ Q° - (m/2) d̄ + v`:
`Φ_u = SC - Σ κ/2 (Q - Q°)² + L + ⟨v, Q⟩ + Σ κ/2 (Q°)²`.
Full statement of the paper, for arbitrary finite `ι`, `Z`. -/
theorem potential_welfare_identity (d : ι → Z → ℝ) (R : ι → ℝ) (q : ι → Z → ℝ)
    (hl : ∀ i z, q i z ^ 2 = d i z * q i z) (Qo dbar v u : Z → ℝ)
    (hu : ∀ z, u z = kap g r z * Qo z - mC b g r z / 2 * dbar z + v z) :
    Phi α b g r u R q
      = SC α b g r R q - ∑ z, kap g r z / 2 * (Qagg q z - Qo z) ^ 2
        + Lasym b g r d dbar q + ∑ z, v z * Qagg q z + ∑ z, kap g r z / 2 * Qo z ^ 2 := by
  have hX : ∀ z, ∑ i, r * q i z = r * Qagg q z := fun z => (Finset.mul_sum _ _ _).symm
  have hsq : ∀ z, ∑ i, q i z ^ 2 = ∑ i, d i z * q i z :=
    fun z => Finset.sum_congr rfl (fun i _ => hl i z)
  have hL : ∀ z, ∑ i, mC b g r z / 2 * (d i z - dbar z) * q i z
      = mC b g r z / 2 * ∑ i, d i z * q i z - mC b g r z / 2 * dbar z * Qagg q z := by
    intro z
    rw [Finset.mul_sum, Qagg, Finset.mul_sum, ← Finset.sum_sub_distrib]
    exact Finset.sum_congr rfl (fun i _ => by ring)
  have hz : ∀ z, (-α z * Qagg q z + mC b g r z / 2 * (Qagg q z ^ 2 + ∑ i, q i z ^ 2)
        + u z * Qagg q z)
      = (-α z * Qagg q z + b z / 2 * Qagg q z ^ 2 + g z * (∑ i, r * q i z) ^ 2)
        - kap g r z / 2 * (Qagg q z - Qo z) ^ 2
        + ∑ i, mC b g r z / 2 * (d i z - dbar z) * q i z
        + v z * Qagg q z + kap g r z / 2 * Qo z ^ 2 := by
    intro z
    rw [hsq z, hX z, hL z, hu z]
    simp only [mC, kap]
    ring
  have hLc : ∑ i, ∑ z, mC b g r z / 2 * (d i z - dbar z) * q i z
      = ∑ z, ∑ i, mC b g r z / 2 * (d i z - dbar z) * q i z := Finset.sum_comm
  unfold Phi SC Lasym
  rw [hLc, Finset.sum_congr rfl (fun z _ => hz z)]
  simp only [Finset.sum_add_distrib, Finset.sum_sub_distrib]
  ring

/-- Corollary used in the paper: with `u = κ Q° - (m/2) d̄` (`v = 0`) the potential is the social
cost minus a concave quadratic in the aggregate plus the lot-asymmetry term. -/
theorem potential_welfare_tangent (d : ι → Z → ℝ) (R : ι → ℝ) (q : ι → Z → ℝ)
    (hl : ∀ i z, q i z ^ 2 = d i z * q i z) (Qo dbar : Z → ℝ) :
    Phi α b g r (fun z => kap g r z * Qo z - mC b g r z / 2 * dbar z) R q
      = SC α b g r R q - ∑ z, kap g r z / 2 * (Qagg q z - Qo z) ^ 2
        + Lasym b g r d dbar q + ∑ z, kap g r z / 2 * Qo z ^ 2 := by
  have := potential_welfare_identity α b g r d R q hl Qo dbar (fun _ => 0)
    (fun z => kap g r z * Qo z - mC b g r z / 2 * dbar z) (fun z => by simp)
  simpa using this

/-! ## The convexified game and Theorem 5 -/

section Convexified

variable {V : Type*} [AddCommGroup V] [Module ℝ V]

/-- Aggregate of the (linear) delivery maps `q̄_{iz}` at a point `x` of the feasible set. -/
def Qb (qb : ι → Z → V →ₗ[ℝ] ℝ) (x : V) (z : Z) : ℝ := ∑ i, qb i z x

/-- Convexified potential `Φ̄_u`. `Rl x` is the expected routing cost. -/
def PhiB (d : ι → Z → ℝ) (u : Z → ℝ) (Rl : V →ₗ[ℝ] ℝ) (qb : ι → Z → V →ₗ[ℝ] ℝ) (x : V) : ℝ :=
  Rl x + ∑ z, ((-α z + u z) * Qb qb x z + mC b g r z / 2 * ∑ i, d i z * qb i z x
    + mC b g r z / 2 * Qb qb x z ^ 2)

/-- Convexified social cost `SC̄`. -/
def SCB (Rl : V →ₗ[ℝ] ℝ) (qb : ι → Z → V →ₗ[ℝ] ℝ) (x : V) : ℝ :=
  Rl x + ∑ z, (-α z * Qb qb x z + mS b g r z / 2 * Qb qb x z ^ 2)

/-- Lot asymmetry of the convexified game. -/
def LB (d : ι → Z → ℝ) (dbar : Z → ℝ) (qb : ι → Z → V →ₗ[ℝ] ℝ) (x : V) : ℝ :=
  ∑ i, ∑ z, mC b g r z / 2 * (d i z - dbar z) * qb i z x

/-- The identity of Lemma 2 for `Φ̄_u` and `SC̄` (no lumpiness needed: same algebra). -/
theorem potential_welfare_identity_convexified (d : ι → Z → ℝ) (Rl : V →ₗ[ℝ] ℝ)
    (qb : ι → Z → V →ₗ[ℝ] ℝ) (x : V) (Qo dbar v u : Z → ℝ)
    (hu : ∀ z, u z = kap g r z * Qo z - mC b g r z / 2 * dbar z + v z) :
    PhiB α b g r d u Rl qb x
      = SCB α b g r Rl qb x - ∑ z, kap g r z / 2 * (Qb qb x z - Qo z) ^ 2
        + LB b g r d dbar qb x + ∑ z, v z * Qb qb x z + ∑ z, kap g r z / 2 * Qo z ^ 2 := by
  have hL : ∀ z, ∑ i, mC b g r z / 2 * (d i z - dbar z) * qb i z x
      = mC b g r z / 2 * ∑ i, d i z * qb i z x - mC b g r z / 2 * dbar z * Qb qb x z := by
    intro z
    rw [Finset.mul_sum, Qb, Finset.mul_sum, ← Finset.sum_sub_distrib]
    exact Finset.sum_congr rfl (fun i _ => by ring)
  have hz : ∀ z, ((-α z + u z) * Qb qb x z + mC b g r z / 2 * ∑ i, d i z * qb i z x
        + mC b g r z / 2 * Qb qb x z ^ 2)
      = (-α z * Qb qb x z + mS b g r z / 2 * Qb qb x z ^ 2)
        - kap g r z / 2 * (Qb qb x z - Qo z) ^ 2
        + ∑ i, mC b g r z / 2 * (d i z - dbar z) * qb i z x
        + v z * Qb qb x z + kap g r z / 2 * Qo z ^ 2 := by
    intro z
    rw [hL z, hu z]
    simp only [mC, mS, kap]
    ring
  have hLc : ∑ i, ∑ z, mC b g r z / 2 * (d i z - dbar z) * qb i z x
      = ∑ z, ∑ i, mC b g r z / 2 * (d i z - dbar z) * qb i z x := Finset.sum_comm
  unfold PhiB SCB LB
  rw [hLc, Finset.sum_congr rfl (fun z _ => hz z)]
  simp only [Finset.sum_add_distrib, Finset.sum_sub_distrib]
  ring

/-- Linear coefficient of `SC̄(x) - SC̄(x*)` in the direction `x - x*`. -/
def Acoef (Rl : V →ₗ[ℝ] ℝ) (qb : ι → Z → V →ₗ[ℝ] ℝ) (xs x : V) : ℝ :=
  (Rl x - Rl xs) + ∑ z, (-α z + mS b g r z * Qb qb xs z) * (Qb qb x z - Qb qb xs z)

/-- Quadratic coefficient. -/
def Bcoef (qb : ι → Z → V →ₗ[ℝ] ℝ) (xs x : V) : ℝ :=
  ∑ z, mS b g r z / 2 * (Qb qb x z - Qb qb xs z) ^ 2

theorem scb_sub (Rl : V →ₗ[ℝ] ℝ) (qb : ι → Z → V →ₗ[ℝ] ℝ) (xs x : V) :
    SCB α b g r Rl qb x - SCB α b g r Rl qb xs
      = Acoef α b g r Rl qb xs x + Bcoef b g r qb xs x := by
  have hz : ∀ z, (-α z * Qb qb x z + mS b g r z / 2 * Qb qb x z ^ 2)
      - (-α z * Qb qb xs z + mS b g r z / 2 * Qb qb xs z ^ 2)
      = (-α z + mS b g r z * Qb qb xs z) * (Qb qb x z - Qb qb xs z)
        + mS b g r z / 2 * (Qb qb x z - Qb qb xs z) ^ 2 := fun z => by ring
  have h1 : SCB α b g r Rl qb x - SCB α b g r Rl qb xs
      = (Rl x - Rl xs) + ∑ z, ((-α z * Qb qb x z + mS b g r z / 2 * Qb qb x z ^ 2)
        - (-α z * Qb qb xs z + mS b g r z / 2 * Qb qb xs z ^ 2)) := by
    simp only [SCB, Finset.sum_sub_distrib]
    ring
  rw [h1, Finset.sum_congr rfl (fun z _ => hz z), Finset.sum_add_distrib]
  simp only [Acoef, Bcoef]
  ring

theorem Qb_seg (qb : ι → Z → V →ₗ[ℝ] ℝ) (xs x : V) (t : ℝ) (z : Z) :
    Qb qb (xs + t • (x - xs)) z = Qb qb xs z + t * (Qb qb x z - Qb qb xs z) := by
  simp only [Qb, map_add, map_smul, map_sub, smul_eq_mul, Finset.sum_add_distrib,
    ← Finset.mul_sum, Finset.sum_sub_distrib]

theorem A_seg (Rl : V →ₗ[ℝ] ℝ) (qb : ι → Z → V →ₗ[ℝ] ℝ) (xs x : V) (t : ℝ) :
    Acoef α b g r Rl qb xs (xs + t • (x - xs)) = t * Acoef α b g r Rl qb xs x := by
  simp only [Acoef, Qb_seg, map_add, map_smul, map_sub, smul_eq_mul, Finset.mul_sum]
  rw [mul_add, Finset.mul_sum]
  congr 1
  · ring
  · exact Finset.sum_congr rfl (fun z _ => by ring)

theorem B_seg (qb : ι → Z → V →ₗ[ℝ] ℝ) (xs x : V) (t : ℝ) :
    Bcoef b g r qb xs (xs + t • (x - xs)) = t ^ 2 * Bcoef b g r qb xs x := by
  simp only [Bcoef, Qb_seg, Finset.mul_sum]
  exact Finset.sum_congr rfl (fun z _ => by ring)

/-- **Theorem 5 (DIP, `thm:convex`; exact implementation under symmetric lots).**
Let `C` be a convex feasible set (the paper's `∏ Δ(𝒫_i)`, with `q̄`, `R̄` linear in `x`),
`x*` a minimiser of `SC̄` on `C`, lots symmetric within zones
(`d_{iz} = d̄_z` or carrier `i` never serves `z`), and `u = κ Q̄* - (m/2) d̄` the tangent charge.
Then (a) `x*` minimises `Φ̄_u` on `C` (it is a convexified equilibrium) and (b) every
minimiser `x^u` of `Φ̄_u` has aggregate `Q̄*` and social cost `SC̄(x*)`. -/
theorem exact_implementation_symmetric
    (hb : ∀ z, 0 < b z) (hg : ∀ z, 0 ≤ g z)
    (d : ι → Z → ℝ) (Rl : V →ₗ[ℝ] ℝ) (qb : ι → Z → V →ₗ[ℝ] ℝ)
    (C : Set V) (hC : Convex ℝ C) (xs : V) (hxs : xs ∈ C)
    (hopt : ∀ x ∈ C, SCB α b g r Rl qb xs ≤ SCB α b g r Rl qb x)
    (dbar : Z → ℝ) (hsym : ∀ i z, d i z = dbar z ∨ ∀ x ∈ C, qb i z x = 0)
    (u : Z → ℝ) (hu : ∀ z, u z = kap g r z * Qb qb xs z - mC b g r z / 2 * dbar z) :
    (∀ x ∈ C, PhiB α b g r d u Rl qb xs ≤ PhiB α b g r d u Rl qb x) ∧
    (∀ xu ∈ C, (∀ x ∈ C, PhiB α b g r d u Rl qb xu ≤ PhiB α b g r d u Rl qb x) →
      (∀ z, Qb qb xu z = Qb qb xs z) ∧ SCB α b g r Rl qb xu = SCB α b g r Rl qb xs) := by
  have hκ : ∀ z, 0 ≤ kap g r z := fun z => mul_nonneg (hg z) (sq_nonneg r)
  have hmS : ∀ z, 0 ≤ mS b g r z := fun z => by
    have := hκ z; have := hb z; simp only [mS]; linarith
  -- the asymmetry term vanishes on `C`
  have hL0 : ∀ x ∈ C, LB b g r d dbar qb x = 0 := by
    intro x hx
    unfold LB
    refine Finset.sum_eq_zero (fun i _ => Finset.sum_eq_zero (fun z _ => ?_))
    rcases hsym i z with h | h
    · rw [h]; ring
    · rw [h x hx]; ring
  have hid : ∀ x ∈ C, PhiB α b g r d u Rl qb x
      = SCB α b g r Rl qb x - ∑ z, kap g r z / 2 * (Qb qb x z - Qb qb xs z) ^ 2
        + ∑ z, kap g r z / 2 * Qb qb xs z ^ 2 := by
    intro x hx
    have := potential_welfare_identity_convexified α b g r d Rl qb x (Qb qb xs) dbar
      (fun _ => 0) u (fun z => by simp [hu z])
    rw [this, hL0 x hx]
    simp
  -- first-order optimality: A ≥ 0
  have hB : ∀ x, 0 ≤ Bcoef b g r qb xs x := fun x =>
    Finset.sum_nonneg (fun z _ => mul_nonneg (div_nonneg (hmS z) (by norm_num)) (sq_nonneg _))
  have hA : ∀ x ∈ C, 0 ≤ Acoef α b g r Rl qb xs x := by
    intro x hx
    refine nonneg_of_forall_small (hB x) (fun t ht0 ht1 => ?_)
    have hmem : xs + t • (x - xs) ∈ C := hC.add_smul_sub_mem hxs hx ⟨ht0.le, ht1⟩
    have h1 := hopt _ hmem
    have h2 := scb_sub α b g r Rl qb xs (xs + t • (x - xs))
    rw [A_seg, B_seg] at h2
    linarith
  -- difference of the potentials
  have hdiff : ∀ x ∈ C, PhiB α b g r d u Rl qb x - PhiB α b g r d u Rl qb xs
      = Acoef α b g r Rl qb xs x
        + ∑ z, (b z + kap g r z) / 2 * (Qb qb x z - Qb qb xs z) ^ 2 := by
    intro x hx
    rw [hid x hx, hid xs hxs]
    have h2 := scb_sub α b g r Rl qb xs x
    have h3 : ∑ z, kap g r z / 2 * (Qb qb xs z - Qb qb xs z) ^ 2 = 0 := by simp
    have h4 : Bcoef b g r qb xs x - ∑ z, kap g r z / 2 * (Qb qb x z - Qb qb xs z) ^ 2
        = ∑ z, (b z + kap g r z) / 2 * (Qb qb x z - Qb qb xs z) ^ 2 := by
      unfold Bcoef
      rw [← Finset.sum_sub_distrib]
      exact Finset.sum_congr rfl (fun z _ => by simp only [mS]; ring)
    linarith
  refine ⟨fun x hx => ?_, fun xu hxu hmin => ?_⟩
  · have := hdiff x hx
    have h5 : 0 ≤ ∑ z, (b z + kap g r z) / 2 * (Qb qb x z - Qb qb xs z) ^ 2 :=
      Finset.sum_nonneg (fun z _ => mul_nonneg
        (div_nonneg (by have := hκ z; have := hb z; linarith) (by norm_num)) (sq_nonneg _))
    linarith [hA x hx]
  · have h1 := hdiff xu hxu
    have h2 := hmin xs hxs
    have hA0 := hA xu hxu
    have h5 : 0 ≤ ∑ z, (b z + kap g r z) / 2 * (Qb qb xu z - Qb qb xs z) ^ 2 :=
      Finset.sum_nonneg (fun z _ => mul_nonneg
        (div_nonneg (by have := hκ z; have := hb z; linarith) (by norm_num)) (sq_nonneg _))
    have hsum0 : ∑ z, (b z + kap g r z) / 2 * (Qb qb xu z - Qb qb xs z) ^ 2 = 0 := by linarith
    have hz0 := (Finset.sum_eq_zero_iff_of_nonneg (fun z _ => mul_nonneg
        (div_nonneg (by have := hκ z; have := hb z; linarith) (by norm_num)) (sq_nonneg _))).1 hsum0
    have hQ : ∀ z, Qb qb xu z = Qb qb xs z := by
      intro z
      have hz := hz0 z (Finset.mem_univ z)
      have hpos : 0 < (b z + kap g r z) / 2 := by
        have := hκ z; have := hb z; positivity
      have : (Qb qb xu z - Qb qb xs z) ^ 2 = 0 := by
        rcases mul_eq_zero.1 hz with h | h
        · exact absurd h hpos.ne'
        · exact h
      have := pow_eq_zero_iff (two_ne_zero) |>.1 this
      linarith
    refine ⟨hQ, ?_⟩
    have hBz : Bcoef b g r qb xs xu = 0 := by
      unfold Bcoef
      exact Finset.sum_eq_zero (fun z _ => by rw [hQ z]; ring)
    have h6 := scb_sub α b g r Rl qb xs xu
    have hA00 : Acoef α b g r Rl qb xs xu = 0 := by linarith
    linarith

end Convexified

/-! ## Theorem 7 (implementation polyhedron and best-response cuts) -/

section Polyhedron

variable {P : ι → Type*} [DecidableEq ι]

/-- Carrier `i`'s cost of plan `p` under charge `u` against the target `σ*`:
`J^u_i(p;σ*_{-i}) = c_i(p) + ⟨u, q_i(p)⟩` (Proposition 1(a)); `c i p = J^0_i(p;σ*_{-i})`. -/
def Jc (c : ∀ i, P i → ℝ) (q : ∀ i, P i → Z → ℝ) (u : Z → ℝ) (i : ι) (p : P i) : ℝ :=
  c i p + ∑ z, u z * q i p z

/-- The constraint `(i,p)` of the toll polyhedron `P(σ*)`:
`⟨q_i(p) - q_i(σ*_i), u⟩ ≥ J⁰_i(σ*_i) - J⁰_i(p)`. -/
def Sat (c : ∀ i, P i → ℝ) (q : ∀ i, P i → Z → ℝ) (σ : ∀ i, P i) (i : ι) (p : P i)
    (u : Z → ℝ) : Prop :=
  c i (σ i) - c i p ≤ ∑ z, (q i p z - q i (σ i) z) * u z

/-- The toll polyhedron `P(σ*)` (without the box `𝒰`). -/
def Poly (c : ∀ i, P i → ℝ) (q : ∀ i, P i → Z → ℝ) (σ : ∀ i, P i) : Set (Z → ℝ) :=
  {u | ∀ i p, Sat c q σ i p u}

/-- Constraint `(i,p)` holds iff `p` is not strictly better than `σ*_i` under `u`. -/
theorem sat_iff (c : ∀ i, P i → ℝ) (q : ∀ i, P i → Z → ℝ) (σ : ∀ i, P i) (i : ι) (p : P i)
    (u : Z → ℝ) : Sat c q σ i p u ↔ Jc c q u i (σ i) ≤ Jc c q u i p := by
  unfold Sat Jc
  have : ∑ z, (q i p z - q i (σ i) z) * u z
      = ∑ z, u z * q i p z - ∑ z, u z * q i (σ i) z := by
    rw [← Finset.sum_sub_distrib]
    exact Finset.sum_congr rfl (fun z _ => by ring)
  rw [this]
  constructor <;> intro h <;> linarith

/-- **Theorem 7(a), polyhedron.** `u ∈ P(σ*)` iff `σ*` is a pure equilibrium under `u`. -/
theorem mem_poly_iff (c : ∀ i, P i → ℝ) (q : ∀ i, P i → Z → ℝ) (σ : ∀ i, P i) (u : Z → ℝ) :
    u ∈ Poly c q σ ↔ ∀ i p, Jc c q u i (σ i) ≤ Jc c q u i p :=
  forall_congr' (fun i => forall_congr' (fun p => sat_iff c q σ i p u))

/-- Violation of the constraint `(i,p)` at `u`. -/
def viol (c : ∀ i, P i → ℝ) (q : ∀ i, P i → Z → ℝ) (σ : ∀ i, P i) (i : ι) (p : P i)
    (u : Z → ℝ) : ℝ :=
  Jc c q u i (σ i) - Jc c q u i p

/-- **Theorem 7(a), separation.** If `b` is a best response of carrier `i` to `σ*_{-i}` under `u`,
then (1) all of `i`'s constraints hold iff `b` is not strictly improving, (2) if `b` improves,
constraint `(i,b)` is violated and (3) it is the most violated constraint of carrier `i`. -/
theorem separation (c : ∀ i, P i → ℝ) (q : ∀ i, P i → Z → ℝ) (σ : ∀ i, P i) (u : Z → ℝ)
    (i : ι) (bi : P i) (hb : ∀ p, Jc c q u i bi ≤ Jc c q u i p) :
    ((∀ p, Sat c q σ i p u) ↔ ¬ (Jc c q u i bi < Jc c q u i (σ i))) ∧
    (Jc c q u i bi < Jc c q u i (σ i) → ¬ Sat c q σ i bi u) ∧
    (∀ p, viol c q σ i p u ≤ viol c q σ i bi u) := by
  refine ⟨?_, ?_, fun p => ?_⟩
  · constructor
    · intro h hlt
      have := (sat_iff c q σ i bi u).1 (h bi)
      linarith
    · intro h p
      rw [sat_iff]
      have := hb (σ i)
      have := hb p
      by_contra hc
      push_neg at hc
      exact h (by linarith)
  · intro hlt hs
    have := (sat_iff c q σ i bi u).1 hs
    linarith
  · unfold viol
    have := hb p
    linarith

/-- **Theorem 7(b), counting.** If every round `k` adds a cut `c k` that the current charge
`u k` violates while `u k` satisfies all earlier cuts, the cuts are pairwise distinct; hence at most
`|Idx|` rounds add a cut. -/
theorem cuts_injective {Idx U : Type*} (sat : Idx → U → Prop) (c : ℕ → Idx) (u : ℕ → U)
    (hviol : ∀ k, ¬ sat (c k) (u k)) (hprev : ∀ j k, j < k → sat (c j) (u k)) :
    Function.Injective c := by
  intro j k hjk
  by_contra hne
  rcases lt_or_gt_of_ne hne with h | h
  · exact hviol k (hjk ▸ hprev j k h)
  · exact hviol j (hjk ▸ hprev k j h)

theorem rounds_le_card {Idx U : Type*} [Fintype Idx] (sat : Idx → U → Prop) (c : ℕ → Idx)
    (u : ℕ → U) (hviol : ∀ k, ¬ sat (c k) (u k)) (hprev : ∀ j k, j < k → sat (c j) (u k))
    (n : ℕ) : n ≤ Fintype.card Idx := by
  have hinj := cuts_injective sat c u hviol hprev
  have : Function.Injective (fun k : Fin n => c k) := fun a b h => Fin.ext (hinj h)
  simpa using Fintype.card_le_of_injective _ this

/-- The index set of non-trivial constraints has `Σ_i (|𝒫_i| - 1)` elements, the bound of
Theorem 7(b) (plus one final round with no cut). -/
theorem card_nontrivial [∀ i, Fintype (P i)] [∀ i, DecidableEq (P i)] (σ : ∀ i, P i) :
    Fintype.card (Σ i, {p : P i // p ≠ σ i}) = ∑ i, (Fintype.card (P i) - 1) := by
  rw [Fintype.card_sigma]
  refine Finset.sum_congr rfl (fun i _ => ?_)
  rw [Fintype.card_subtype_compl, Fintype.card_subtype_eq]
  rfl

end Polyhedron

end DIP
end CCU
