/-
  Statement skeletons for the machine-checking targets listed in `lean_targets.md`.
  Every `sorry` marks a proof obligation; the statements themselves type-check
  against the Mathlib revision pinned in `../lean/lake-manifest.json`.
  Compile from the `lean/` directory with:  lake env lean ../theory/LeanTargets.lean
-/
import Mathlib

open Finset BigOperators Pointwise

namespace CCU

/-! ## Model: a finite bilinear aggregative game -/

/-- Finite aggregative game with `N` players and `d` aggregate coordinates.
`a i p` is the contribution of plan `p` to the aggregate, `φ i p` its exposure,
`π i p` its private profit, and `M` the (diagonal) coupling. -/
structure AggGame (N d : ℕ) where
  P : Fin N → Type
  fin : ∀ i, Fintype (P i)
  dec : ∀ i, DecidableEq (P i)
  ne : ∀ i, Nonempty (P i)
  a : ∀ i, P i → (Fin d → ℝ)
  φ : ∀ i, P i → (Fin d → ℝ)
  π : ∀ i, P i → ℝ
  M : Fin d → ℝ

variable {N d : ℕ}

/-- Expected payoff of plan `p` when the mean rival aggregate is `m` (affine coupling). -/
def AggGame.u (G : AggGame N d) (i : Fin N) (p : G.P i) (m : Fin d → ℝ) : ℝ :=
  G.π i p - ∑ z, G.φ i p z * G.M z * m z

/-- Realised rival aggregate at a pure profile. -/
def AggGame.rival (G : AggGame N d) (σ : ∀ i, G.P i) (i : Fin N) : Fin d → ℝ :=
  ∑ j ∈ univ.erase i, G.a j (σ j)

/-- Clipped weighted box of half-width `δ` around `c`. -/
def InBox (w : Fin d → ℝ) (δ : ℝ) (c m : Fin d → ℝ) : Prop :=
  ∀ z, 0 ≤ m z ∧ |m z - c z| ≤ δ * w z

def EAdm (G : AggGame N d) (w : Fin d → ℝ) (δ : ℝ) (i : Fin N) (c : Fin d → ℝ)
    (p : G.P i) : Prop :=
  ∃ m, InBox w δ c m ∧ ∀ q, G.u i q m ≤ G.u i p m

def MaxAdm (G : AggGame N d) (w : Fin d → ℝ) (δ : ℝ) (i : Fin N) (c : Fin d → ℝ)
    (p : G.P i) : Prop :=
  ∀ q, ∃ m, InBox w δ c m ∧ G.u i q m ≤ G.u i p m

def ICNE_E (G : AggGame N d) (w : Fin d → ℝ) (δ : ℝ) (σ : ∀ i, G.P i) : Prop :=
  ∀ i, EAdm G w δ i (G.rival σ i) (σ i)

/-! ## T1. Nesting of criteria and monotonicity in the width -/

theorem eAdm_imp_maxAdm (G : AggGame N d) (w : Fin d → ℝ) (δ : ℝ) (i : Fin N)
    (c : Fin d → ℝ) (p : G.P i) (h : EAdm G w δ i c p) : MaxAdm G w δ i c p := by
  obtain ⟨m, hm, hopt⟩ := h
  exact fun q => ⟨m, hm, hopt q⟩

theorem inBox_mono {w : Fin d → ℝ} (hw : ∀ z, 0 ≤ w z) {δ δ' : ℝ} (hδ : δ ≤ δ')
    {c m : Fin d → ℝ} (h : InBox w δ c m) : InBox w δ' c m := by
  intro z
  obtain ⟨h0, h1⟩ := h z
  exact ⟨h0, h1.trans (mul_le_mul_of_nonneg_right hδ (hw z))⟩

theorem icneE_mono (G : AggGame N d) {w : Fin d → ℝ} (hw : ∀ z, 0 ≤ w z) {δ δ' : ℝ}
    (hδ : δ ≤ δ') (σ : ∀ i, G.P i) (h : ICNE_E G w δ σ) : ICNE_E G w δ' σ := by
  intro i
  obtain ⟨m, hm, hopt⟩ := h i
  exact ⟨m, inBox_mono hw hδ hm, hopt⟩

/-! ## T2. Credal absorption (the elementary core of Theorem 6.1(a)) -/

theorem absorption (G : AggGame N d) (w : Fin d → ℝ) (δ : ℝ) (σ : ∀ i, G.P i)
    (anchor : Fin N → (Fin d → ℝ))
    (hbr : ∀ i q, G.u i q (anchor i) ≤ G.u i (σ i) (anchor i))
    (hnn : ∀ i z, 0 ≤ anchor i z)
    (hclose : ∀ i z, |anchor i z - G.rival σ i z| ≤ δ * w z) :
    ICNE_E G w δ σ :=
  fun i => ⟨anchor i, fun z => ⟨hnn i z, hclose i z⟩, fun q => hbr i q⟩

/-! ## T3. Shapley–Folkman lemma (finite sets, finite-dimensional real space) -/

theorem shapleyFolkman {ι E : Type*} [Fintype ι] [DecidableEq E] [AddCommGroup E]
    [Module ℝ E] [FiniteDimensional ℝ E]
    (S : ι → Finset E) (x : E) (hx : x ∈ ∑ i, convexHull ℝ (S i : Set E)) :
    ∃ y : ι → E, (∀ i, y i ∈ convexHull ℝ (S i : Set E)) ∧ ∑ i, y i = x ∧
      (univ.filter (fun i => y i ∉ S i)).card ≤ Module.finrank ℝ E := by
  sorry

/-! ## T4. Exact potential identity under D1 (φ = a) -/

/-- Potential of the D1 game: `Σ π̃_i − ½‖A‖²_M` with `π̃_i = π_i + ½‖a_i‖²_M`. -/
noncomputable def potential (G : AggGame N d) (σ : ∀ i, G.P i) : ℝ :=
  (∑ i, (G.π i (σ i) + (1 / 2) * ∑ z, G.M z * G.a i (σ i) z ^ 2))
    - (1 / 2) * ∑ z, G.M z * (∑ i, G.a i (σ i) z) ^ 2

theorem potential_identity (G : AggGame N d) (hD1 : ∀ i p, G.φ i p = G.a i p)
    (σ : ∀ i, G.P i) (i : Fin N) (q : G.P i) :
    potential G (Function.update σ i q) - potential G σ
      = G.u i q (G.rival σ i) - G.u i (σ i) (G.rival σ i) := by
  sorry

/-! ## T5. Kernel reduction (Theorem 7.3, combinatorial core) -/

/-- Gain of playing `in` rather than `out` in the kernel game, scaled by `2(Δ⁻+1)`
so that all data are integers: `2(Δ⁻+1)·(1 − 2·#out-nbrs-in) − #in-nbrs-in`. -/
def kernelGain {n : ℕ} (adj : Fin n → Fin n → Prop) [DecidableRel adj] (Δin : ℕ)
    (S : Finset (Fin n)) (i : Fin n) : ℤ :=
  2 * ((Δin : ℤ) + 1) * (1 - 2 * ((S.filter (fun j => adj i j)).card : ℤ))
    - ((S.filter (fun h => adj h i)).card : ℤ)

def IsKernel {n : ℕ} (adj : Fin n → Fin n → Prop) [DecidableRel adj]
    (S : Finset (Fin n)) : Prop :=
  (∀ i ∈ S, ∀ j ∈ S, ¬ adj i j) ∧ (∀ i ∉ S, ∃ j ∈ S, adj i j)

theorem pne_iff_kernel {n : ℕ} (adj : Fin n → Fin n → Prop) [DecidableRel adj]
    (Δin : ℕ) (hΔ : ∀ i, (univ.filter (fun h => adj h i)).card ≤ Δin)
    (S : Finset (Fin n)) :
    ((∀ i ∈ S, 0 ≤ kernelGain adj Δin S i) ∧ (∀ i ∉ S, kernelGain adj Δin S i ≤ 0))
      ↔ IsKernel adj S := by
  have hh : ∀ i, ((S.filter (fun h => adj h i)).card : ℤ) ≤ Δin := fun i => by
    have := (Finset.card_le_card (Finset.filter_subset_filter (fun h => adj h i)
      (Finset.subset_univ S))).trans (hΔ i)
    exact_mod_cast this
  have hpos : ∀ i, 0 ≤ kernelGain adj Δin S i ↔ ∀ j ∈ S, ¬ adj i j := by
    intro i
    have h0 := hh i
    have hnn : (0:ℤ) ≤ ((S.filter (fun h => adj h i)).card : ℤ) := by positivity
    unfold kernelGain
    constructor
    · intro hg j hj hadj
      have hmem : j ∈ S.filter (fun j => adj i j) := Finset.mem_filter.mpr ⟨hj, hadj⟩
      have : (1:ℤ) ≤ ((S.filter (fun j => adj i j)).card : ℤ) := by
        exact_mod_cast Finset.card_pos.mpr ⟨j, hmem⟩
      nlinarith
    · intro hno
      have : S.filter (fun j => adj i j) = ∅ :=
        Finset.filter_eq_empty_iff.mpr (fun j hj => hno j hj)
      rw [this, Finset.card_empty]; push_cast; nlinarith
  have hneg : ∀ i, kernelGain adj Δin S i ≤ 0 ↔ ∃ j ∈ S, adj i j := by
    intro i
    have h0 := hh i
    have hnn : (0:ℤ) ≤ ((S.filter (fun h => adj h i)).card : ℤ) := by positivity
    unfold kernelGain
    constructor
    · intro hg
      by_contra hno
      push Not at hno
      have : S.filter (fun j => adj i j) = ∅ :=
        Finset.filter_eq_empty_iff.mpr (fun j hj => hno j hj)
      rw [this, Finset.card_empty] at hg; push_cast at hg; nlinarith
    · rintro ⟨j, hj, hadj⟩
      have hmem : j ∈ S.filter (fun j => adj i j) := Finset.mem_filter.mpr ⟨hj, hadj⟩
      have : (1:ℤ) ≤ ((S.filter (fun j => adj i j)).card : ℤ) := by
        exact_mod_cast Finset.card_pos.mpr ⟨j, hmem⟩
      nlinarith
  constructor
  · rintro ⟨h1, h2⟩
    exact ⟨fun i hi j hj => (hpos i).1 (h1 i hi) j hj, fun i hi => (hneg i).1 (h2 i hi)⟩
  · rintro ⟨h1, h2⟩
    exact ⟨fun i hi => (hpos i).2 (h1 i hi), fun i hi => (hneg i).2 (h2 i hi)⟩

/-! ## T6. Tight two-carrier example (Proposition 7.1): every pure profile needs width ≥ 1 -/

/-- Payoff difference `u(A1) − u(B1) = 6 − 3·n₂`, with `n₂` the believed rival vehicles. -/
def gain1 (n : ℝ) : ℝ := 6 - 3 * n

theorem tight_example_lower (k2 : ℝ) (hk : k2 = 1 ∨ k2 = 3) (δ : ℝ)
    (h : ∃ n, 0 ≤ n ∧ |n - k2| ≤ δ ∧ (if k2 = 1 then gain1 n ≤ 0 else 0 ≤ gain1 n)) :
    1 ≤ δ := by
  obtain ⟨n, _, habs, hg⟩ := h
  rcases hk with rfl | rfl
  · simp only [ite_true, gain1] at hg
    have := le_abs_self (n - 1)
    linarith
  · have h31 : (3 : ℝ) ≠ 1 := by norm_num
    simp only [h31, ite_false, gain1] at hg
    have := neg_abs_le (n - 3)
    linarith

/-! ## T7. Product-of-cycles lower bound (Proposition 7.2) -/

/-- Regret of the two players in one zone of the cycle game; `s = true` means carrier 1
plays A1, `t = true` means carrier 2 plays Y. -/
def zoneRegret : Bool → Bool → (ℕ × ℕ)
  | true,  false => (0, 3)   -- (A, X)
  | true,  true  => (3, 0)   -- (A, Y)
  | false, true  => (0, 3)   -- (B, Y)
  | false, false => (3, 0)   -- (B, X)

theorem cycle_product_lower (Z : ℕ) (s t : Fin Z → Bool) :
    3 * ((Z + 1) / 2) ≤
      max (∑ z, (zoneRegret (s z) (t z)).1) (∑ z, (zoneRegret (s z) (t z)).2) := by
  have key : ∀ z, ∃ k : ℕ, k ≤ 1 ∧ (zoneRegret (s z) (t z)).1 = 3 * k ∧
      (zoneRegret (s z) (t z)).2 = 3 * (1 - k) := by
    intro z
    cases s z <;> cases t z <;> simp [zoneRegret]
  choose k hk1 hk2 hk3 using key
  have e1 : ∑ z, (zoneRegret (s z) (t z)).1 = 3 * ∑ z, k z := by
    rw [Finset.mul_sum]; exact Finset.sum_congr rfl (fun z _ => hk2 z)
  have e2 : ∑ z, (zoneRegret (s z) (t z)).2 = 3 * ∑ z, (1 - k z) := by
    rw [Finset.mul_sum]; exact Finset.sum_congr rfl (fun z _ => hk3 z)
  have e3 : ∑ z, k z + ∑ z, (1 - k z) = Z := by
    rw [← Finset.sum_add_distrib]
    have : ∀ z ∈ (univ : Finset (Fin Z)), k z + (1 - k z) = 1 := fun z _ => by
      have := hk1 z; omega
    rw [Finset.sum_congr rfl this]; simp
  rw [e1, e2]
  omega

end CCU
