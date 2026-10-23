# ZMC: Zone-Market Clearing

## Problem solved

D1 affine carrier game (main.tex, Example 2.2 under D1; costs instead of profits). Carrier i picks a plan p from a
huge finite set through an NP-hard routing oracle. It contributes a_i(p) in R^d_{>=0} (d = 2Z: deliveries and
vehicle-hours per zone) and pays

    J_i(p; sigma_-i) = c_i(p) + <a_i(p), M A_-i>,   M = diag(b_z, gamma c_z) > 0,

with charges inside c_i. The Gamma-maximin credal problem is the same game with a surcharge (main.tex, Lemma 3.6),
so it is covered. **Output: an exact pure Nash equilibrium of good potential value (a "good" equilibrium, not
just any), computed with few routing solves, at a cost per round that does not grow with Z.**

## Structural facts the method is derived from (proofs in theory.tex)

Let ctilde_i = c_i - 1/2 ||a_i||_M^2, Phi = sum ctilde_i + 1/2 ||A||_M^2 (exact potential),
V_i(lam) = min_p ctilde_i(p) + <lam, a_i(p)> (one pricing call; a_i(answer) is a supergradient), and
G(lam) = sum_i V_i(lam) - 1/2 lam' M^-1 lam (the price dual of the convexified potential).

1. **Clearing identity (Theorem 2).** For a common price lam and pricing-optimal plans sigma_i in O_i(lam), with
   clearing error e = M^-1 lam - A(sigma):
   - Phi(sigma) - G(lam) = 1/2 ||e||_M^2, so Phi(sigma) - min Phi <= 1/2 ||e||_M^2;
   - Nash regret of carrier i <= 1/2 ||e restricted to i's zones||_M^2;
   - sigma_i is an exact best response to the anchor m_i = M^-1 lam - a_i(sigma_i), so it is E-admissible at
     credal width max over i's zones of |e_k|/w_k. **The own-contribution term of the Shapley-Folkman/absorption
     bounds cancels exactly**;
   - e = 0 if and only if the convexification is tight at a pure profile. In that case sigma is the global
     potential minimiser.

   Consequence: finding a good pure equilibrium amounts to finding ONE price vector at which the carriers' pricing
   answers clear every zone (supply line lam_k/M_k against demand A_k).
2. **Diagonal monotonicity (Theorem 6).** Concavity of V makes the total response antitone. Along its own
   coordinate, the sign of the residual s_k = A_k(lam) - lam_k/M_k at any query localises the optimal price
   coordinate lam*_k up to M_k kappa_k. Here kappa_k is the cross-zone variation: how much other zones' prices can
   move the response in zone k at a fixed own price. kappa = 0 for separable plan sets (Proposition 5); the floor is
   genuine otherwise (Example 9, complementary zones).
3. **Dimension-free rate (Corollary 7).** One oracle round gives one signed sample for **all d one-dimensional
   problems at once**. T rounds (N*T calls, parallel within a round) give
   |lam_k - lam*_k| <= M_k Amax_k 2^{-ceil(T/2)} + M_k kappa_k for every k, independent of d.
4. **Charges (Proposition 12).** Charges translate the supply line. The equilibrium gross price is 1-Lipschitz in
   the charges (M^-1 norm), and convexified aggregates respond monotonically. Brackets and plan pools warm-start
   the next charge evaluation of the leader.

## Pseudo-code

    l <- 0 ; u <- M * Amax ; lam <- (l+u)/2 ; pools Q_i <- {} ; samples S <- {}
    for t = 0..T-1:
        for i in parallel: sigma_i <- argmin_p ctilde_i(p) + <lam, a_i(p)>      # N routing solves
        Q_i <- Q_i + {sigma_i} ; A <- sum_i a_i(sigma_i) ; s <- A - lam / M
        for every k: if s_k > 0: l_k <- lam_k ; if s_k < 0: u_k <- lam_k ; if s_k = 0: l_k = u_k <- lam_k
        S <- S + {(lam, A)}
        if t odd: lam <- (l+u)/2                                                 # safeguard (rate)
        else: for every k: fit a decreasing isotonic piecewise-linear rhat_k to {(lam_k, A_k)} in S;
              lam_k <- crossing of rhat_k with x -> x/M_k, clipped to [l_k, u_k]   # secant (speed)
    sigma_price <- pricing profile with the smallest 1/2||e||_M^2 (= smallest Phi)
    sigma_round <- restricted master over Q (no oracle) + derandomised rounding (main.tex eq. 8.1)
    sigma <- better of the two ; best-response polish until no carrier improves
    return sigma          # exact pure NE; Phi(sigma) <= Phibar* + 1/2 min_t ||e^t||_M^2 (Theorem 10)

Defaults used in the prototypes: T = 8, all oracles exact.

## Why this is not a known method (closest prior art)

| neighbour | what it does | difference |
|---|---|---|
| Dantzig-Wolfe / column generation / simplicial decomposition; bundle methods (Briant et al. 2008 compare them on VRP); Kelley | refine a cutting-plane (full concave) model of V_i where it is wrong | That is idea (a) taken literally, so it is known. Its round count grows with d (here 58 calls at Z = 30, 797 at Z = 250). ZMC keeps only d one-dimensional monotone models and is d-independent. |
| Frank-Wolfe on the relaxation + Shapley-Folkman rounding (main.tex Sect. 8; Liu-Oudjane-Wan MOR 2023; Bonnans et al. 2023) | O(1/eps) rounds | ZMC is geometric per coordinate up to the floor, and beats FW at equal budget in 17/20 synthetic instances. |
| SPAR (Powell, Ruszczynski, Topaloglu MOR 2004) | learns separable piecewise-linear concave value functions from stochastic slopes, with projection steps | a learning scheme for stochastic programs, with convergence for separable objectives; no game, no common-price/anchor identity, no sign-bracket invariant with a cross-variation floor |
| diagonal variable-metric bundle (Karmitsa-Gaudioso-Joki 2019) | diagonal second-order model inside a bundle method | needs bundle machinery and descent tests; no coordinatewise bracket guarantee; dimension-dependent theory |
| Walrasian equilibrium via market potential minimisation with demand oracles (Paes Leme-Wong 2017); coordinate tatonnement in Fisher markets | price search with aggregate demand oracles | Paes Leme-Wong use cutting planes (O~(n) queries under gross substitutes, dimension-dependent). Our supply side is linear and diagonal, and no gross-substitutes assumption is made: the cross-effects are paid as the floor M_k kappa_k. Tatonnement has no bracket and no rate without gross substitutes. |
| Minimal-regret Walras equilibria (Duguet-Harks-Schmidt-Schwarz 2025) | regret of price-allocation pairs tied to duality and integrality gaps | the closest conceptual neighbour of Theorem 2(a),(b). It is in combinatorial markets with fixed supply; our game has a potential with own-term cancellation, credal anchors and the converse (e). |
| Sample generation / double oracle for integer-programming games (Carvalho-Lodi-Pedroso 2022) | restricted game + best-response columns | ZMC queries one common price, not per-carrier best responses to a restricted equilibrium |

The individual tools (bisection, regula falsi, isotonic regression, rounding, BR polish) are textbook. The claim
is limited to: (i) the clearing identity with own-term cancellation and its converse, (ii) the sign-bracket
invariant with the cross-variation floor, and (iii) the method they define, which is d-independent per round and
gives better pure equilibria per oracle call than FW/CG once Z is large. Searches were run on 2026-10-23 (web,
snippet level; queries listed in the final report). They do not replace a Scopus or Web of Science check.

## Limits (stated plainly)

- **Floor.** Accuracy stops at M_k kappa_k. In the prototypes the convexified dual stalls near 1e-3 relative gap, where CG converges to 0. This was harmless for pure equilibria, whose rounding gap is about 1e-2.
- **No a priori bound on the pure clearing error.** Theorem 10 bounds quality by min_t ||e^t||, which is observed, not predicted. Near lam*, kinks force mixing and an irreducible Shapley-Folkman-scale error.
- **D1 only** (plus Gamma-maximin via the surcharge). There is no D2 version.
- **Fixed cost.** T*N calls are spent even on easy games. When the game is nearly trivial, BR is cheaper (E3, strong-fleet case: 6 calls against 54).
- **Real maps.** On real maps with the zone-level proxy oracle, ZMC is clearly better only on the largest map (Berlin, 593 zones). On six of nine maps all methods, BR included, are within a few percent.
- **Oracle.** The routing oracle in the prototypes is an exact DP proxy with one fleet constraint, not a street-level VRP.
