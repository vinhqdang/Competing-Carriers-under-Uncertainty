/-
  Small real-analysis helper shared by the convexified-game files:
  a quadratic that is nonnegative on `(0,1]` has a nonnegative linear coefficient
  (first-order optimality along a segment).
-/
import Mathlib

namespace CCU

/-- If `t * A + t^2 * B ≥ 0` for all `t ∈ (0,1]` and `B ≥ 0`, then `A ≥ 0`. -/
theorem nonneg_of_forall_small {A B : ℝ} (hB : 0 ≤ B)
    (h : ∀ t : ℝ, 0 < t → t ≤ 1 → 0 ≤ t * A + t ^ 2 * B) : 0 ≤ A := by
  by_contra hA
  push_neg at hA
  have hden : 0 < 2 * (B + 1) := by linarith
  set t : ℝ := min 1 (-A / (2 * (B + 1))) with ht
  have hpos : 0 < t := lt_min one_pos (div_pos (by linarith) hden)
  have h1 : t ≤ 1 := min_le_left _ _
  have h2 : t ≤ -A / (2 * (B + 1)) := min_le_right _ _
  have h3 : t * (2 * (B + 1)) ≤ -A := by rwa [le_div_iff₀ hden] at h2
  have h0 := h t hpos h1
  have h4 : 0 ≤ A + t * B := by
    by_contra hc
    push_neg at hc
    nlinarith [mul_pos hpos (neg_pos.2 hc)]
  nlinarith

end CCU
