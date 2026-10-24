/-
  Statement skeletons for the machine-checking targets listed in `lean_targets.md`.
  All statements below are fully proved (no `sorry`); they check against the
  Mathlib revision pinned in `../lean/lake-manifest.json`.
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
  classical
  rcases isEmpty_or_nonempty ι with hι | hι
  · refine ⟨fun i => isEmptyElim i, fun i => isEmptyElim i, ?_, ?_⟩
    · simp only [univ_eq_empty, sum_empty]
      have : x ∈ (0 : Set E) := by simpa using hx
      exact (Set.mem_zero.1 this).symm
    · simp
  obtain ⟨y₀, hy₀, hsum⟩ := (Set.mem_fintype_sum _ _).1 hx
  set n : ℝ := (Fintype.card ι : ℝ) with hn_def
  have hn : 0 < n := by
    rw [hn_def]; exact_mod_cast Fintype.card_pos
  set T : Set (E × (ι → ℝ)) := ⋃ i, (S i : Set E) ×ˢ {(Pi.single i (1:ℝ) : ι → ℝ)} with hT
  have hmem : ((1 / n) • x, fun _ => 1 / n) ∈ convexHull ℝ T := by
    have h1 : ((1 / n) • x, fun _ => 1 / n)
        = ∑ i, (1 / n) • (y₀ i, (Pi.single i (1:ℝ) : ι → ℝ)) := by
      refine Prod.ext ?_ ?_
      · simp only [Prod.fst_sum, Prod.smul_fst, ← Finset.smul_sum, hsum]
      · funext j
        simp [Prod.snd_sum, Finset.sum_apply, Pi.single_apply]
    rw [h1]
    refine (convex_convexHull ℝ T).sum_mem (fun i _ => by positivity) ?_ ?_
    · rw [Finset.sum_const, Finset.card_univ, nsmul_eq_mul, ← hn_def]
      field_simp
    · intro i _
      have h2 : convexHull ℝ ((S i : Set E) ×ˢ {(Pi.single i (1:ℝ) : ι → ℝ)})
          = convexHull ℝ (S i : Set E) ×ˢ {(Pi.single i (1:ℝ) : ι → ℝ)} := by
        rw [convexHull_prod, convexHull_singleton]
      have h3 : (y₀ i, (Pi.single i (1:ℝ) : ι → ℝ)) ∈
          convexHull ℝ ((S i : Set E) ×ˢ {(Pi.single i (1:ℝ) : ι → ℝ)}) := by
        rw [h2]; exact ⟨hy₀ i, rfl⟩
      exact convexHull_mono (Set.subset_iUnion (fun i => (S i : Set E) ×ˢ
        {(Pi.single i (1:ℝ) : ι → ℝ)}) i) h3
  obtain ⟨κ, hκ, z, w, hz, haff, hw, hw1, hwz⟩ := eq_pos_convex_span_of_mem_convexHull hmem
  have hex : ∀ k, ∃ (i : ι) (s : E), s ∈ S i ∧ z k = (s, (Pi.single i (1:ℝ) : ι → ℝ)) := by
    intro k
    have := hz (Set.mem_range_self k)
    simp only [hT, Set.mem_iUnion, Set.mem_prod, Set.mem_singleton_iff] at this
    obtain ⟨i, hs, h2⟩ := this
    exact ⟨i, (z k).1, hs, Prod.ext rfl h2⟩
  choose idx pt hpt heq using hex
  set fib : ι → Finset κ := fun i => univ.filter (fun k => idx k = i) with hfib
  have hfst : ∑ k, w k • pt k = (1 / n) • x := by
    have := congrArg Prod.fst hwz
    simpa [Prod.fst_sum, heq] using this
  have hcoord : ∀ i, ∑ k ∈ fib i, w k = 1 / n := by
    intro i
    have := congrFun (congrArg Prod.snd hwz) i
    simp only [Prod.snd_sum, Finset.sum_apply, Prod.smul_snd, Pi.smul_apply, heq,
      Pi.single_apply, smul_eq_mul] at this
    rw [hfib, Finset.sum_filter, ← this]
    refine Finset.sum_congr rfl (fun k _ => ?_)
    by_cases h : idx k = i
    · simp [h]
    · simp [h, Ne.symm h]
  have hne : ∀ i, (fib i).Nonempty := by
    intro i
    by_contra hcon
    rw [Finset.not_nonempty_iff_eq_empty] at hcon
    have := hcoord i
    rw [hcon, Finset.sum_empty] at this
    have : (0:ℝ) < 1 / n := by positivity
    linarith
  have hmemfib : ∀ i, ∀ k ∈ fib i, pt k ∈ S i := by
    intro i k hk
    have : idx k = i := (Finset.mem_filter.1 hk).2
    rw [← this]; exact hpt k
  let y : ι → E := fun i => n • ∑ k ∈ fib i, w k • pt k
  have hy : ∀ i, y i = ∑ k ∈ fib i, (n * w k) • pt k := by
    intro i
    simp only [y, Finset.smul_sum, smul_smul]
  refine ⟨y, ?_, ?_, ?_⟩
  · intro i
    rw [hy i]
    refine (convex_convexHull ℝ (S i : Set E)).sum_mem (fun k _ => (mul_pos hn (hw k)).le) ?_
      (fun k hk => subset_convexHull ℝ _ (hmemfib i k hk))
    rw [← Finset.mul_sum, hcoord i]; field_simp
  · have : ∑ i, y i = n • ∑ k, w k • pt k := by
      simp only [y]
      rw [← Finset.smul_sum]
      congr 1
      exact Finset.sum_fiberwise univ idx (fun k => w k • pt k)
    rw [this, hfst, smul_smul]
    field_simp
    simp
  · -- counting
    have hlin : LinearIndependent ℝ z := by
      rw [Fintype.linearIndependent_iff]
      intro g hg
      have hs : ∑ k, g k = 0 := by
        have := congrArg (fun p : E × (ι → ℝ) => ∑ j, p.2 j) hg
        simp only [Prod.snd_sum, Prod.smul_snd, Finset.sum_apply, Pi.smul_apply, heq,
          smul_eq_mul, Prod.snd_zero, Pi.zero_apply, Finset.sum_const_zero] at this
        rw [Finset.sum_comm] at this
        simpa [Pi.single_apply] using this
      have := (affineIndependent_iff_of_fintype (k := ℝ) (p := z)).1 haff g hs
        (by rw [Finset.weightedVSub_eq_linear_combination _ hs]; exact hg)
      exact this
    have hcard : Fintype.card κ ≤ Module.finrank ℝ E + Fintype.card ι := by
      have := hlin.fintype_card_le_finrank
      rwa [Module.finrank_prod, Module.finrank_fintype_fun_eq_card] at this
    set B : Finset ι := univ.filter (fun i => 2 ≤ (fib i).card) with hB
    have hsub : univ.filter (fun i => y i ∉ S i) ⊆ B := by
      intro i hi
      rw [Finset.mem_filter] at hi ⊢
      refine ⟨hi.1, ?_⟩
      by_contra hlt
      push Not at hlt
      have h1 : (fib i).card = 1 := le_antisymm (by omega) (Finset.card_pos.2 (hne i))
      obtain ⟨k, hk⟩ := Finset.card_eq_one.1 h1
      apply hi.2
      have hw' : w k = 1 / n := by have := hcoord i; rwa [hk, Finset.sum_singleton] at this
      have : y i = pt k := by
        rw [hy i, hk, Finset.sum_singleton, hw', mul_one_div_cancel hn.ne', one_smul]
      rw [this]
      exact hmemfib i k (by rw [hk]; exact Finset.mem_singleton_self k)
    have hsumcard : Fintype.card κ = ∑ i, (fib i).card := by
      rw [← Finset.card_univ]
      exact Finset.card_eq_sum_card_fiberwise (fun _ _ => Finset.mem_univ _)
    have hB' : B.card = ∑ i, if 2 ≤ (fib i).card then 1 else 0 := Finset.card_filter _ _
    have : ∑ i : ι, (1 + (if 2 ≤ (fib i).card then 1 else 0)) ≤ ∑ i, (fib i).card := by
      refine Finset.sum_le_sum (fun i _ => ?_)
      have := Finset.card_pos.2 (hne i)
      split_ifs <;> omega
    rw [Finset.sum_add_distrib, ← hB', Finset.sum_const, Finset.card_univ, ← hsumcard] at this
    simp only [smul_eq_mul, mul_one] at this
    calc (univ.filter (fun i => y i ∉ S i)).card ≤ B.card := Finset.card_le_card hsub
      _ ≤ _ := by omega

/-! ## T4. Exact potential identity under D1 (φ = a) -/

/-- Potential of the D1 game: `Σ π̃_i − ½‖A‖²_M` with `π̃_i = π_i + ½‖a_i‖²_M`. -/
noncomputable def potential (G : AggGame N d) (σ : ∀ i, G.P i) : ℝ :=
  (∑ i, (G.π i (σ i) + (1 / 2) * ∑ z, G.M z * G.a i (σ i) z ^ 2))
    - (1 / 2) * ∑ z, G.M z * (∑ i, G.a i (σ i) z) ^ 2

theorem potential_identity (G : AggGame N d) (hD1 : ∀ i p, G.φ i p = G.a i p)
    (σ : ∀ i, G.P i) (i : Fin N) (q : G.P i) :
    potential G (Function.update σ i q) - potential G σ
      = G.u i q (G.rival σ i) - G.u i (σ i) (G.rival σ i) := by
  classical
  -- sum over all players of a function of the (updated) plan
  have hsum : ∀ F : ∀ j, G.P j → ℝ,
      ∑ j, F j (Function.update σ i q j) = ∑ j ∈ univ.erase i, F j (σ j) + F i q := by
    intro F
    rw [← Finset.sum_erase_add _ _ (Finset.mem_univ i), Function.update_self]
    congr 1
    refine Finset.sum_congr rfl (fun j hj => ?_)
    rw [Function.update_of_ne (Finset.ne_of_mem_erase hj)]
  have hsum' : ∀ F : ∀ j, G.P j → ℝ,
      ∑ j, F j (σ j) = ∑ j ∈ univ.erase i, F j (σ j) + F i (σ i) := fun F =>
    (Finset.sum_erase_add _ _ (Finset.mem_univ i)).symm
  set R : Fin d → ℝ := G.rival σ i with hR
  have hRz : ∀ z, R z = ∑ j ∈ univ.erase i, G.a j (σ j) z := fun z => by
    simp [hR, AggGame.rival, Finset.sum_apply]
  have hA : ∀ (p : G.P i) z, ∑ j, G.a j (Function.update σ i p j) z = R z + G.a i p z := by
    intro p z
    have := Finset.sum_erase_add (univ : Finset (Fin N))
      (fun j => G.a j (Function.update σ i p j) z) (Finset.mem_univ i)
    rw [← this, Function.update_self, hRz]
    congr 1
    refine Finset.sum_congr rfl (fun j hj => ?_)
    rw [Function.update_of_ne (Finset.ne_of_mem_erase hj)]
  have hA0 : ∀ z, ∑ j, G.a j (σ j) z = R z + G.a i (σ i) z := by
    intro z
    have := hA (σ i) z
    simpa using this
  have e : ∀ p : G.P i, ∑ z, G.M z * (R z + G.a i p z) ^ 2
      = ∑ z, G.M z * R z ^ 2 + 2 * ∑ z, G.M z * R z * G.a i p z
        + ∑ z, G.M z * G.a i p z ^ 2 := by
    intro p
    rw [Finset.mul_sum, ← Finset.sum_add_distrib, ← Finset.sum_add_distrib]
    exact Finset.sum_congr rfl (fun z _ => by ring)
  have hu : ∀ p : G.P i, G.u i p R = G.π i p - ∑ z, G.M z * R z * G.a i p z := by
    intro p
    simp only [AggGame.u, hD1]
    congr 1
    exact Finset.sum_congr rfl (fun z _ => by ring)
  unfold potential
  rw [hsum (fun j p => G.π j p + (1 / 2) * ∑ z, G.M z * G.a j p z ^ 2)]
  rw [hsum' (fun j p => G.π j p + (1 / 2) * ∑ z, G.M z * G.a j p z ^ 2)]
  simp only [hA, hA0, e, hu]
  ring

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
