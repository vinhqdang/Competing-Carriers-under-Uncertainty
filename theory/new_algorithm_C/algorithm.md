# DIP: dual implementation pricing

## Problem solved

The city (leader) sets charges for N carriers who play the D1 Cournot-congestion game of `theory/main.tex`
(`src/ccu/zmc_brl.py`), whose plans come from an NP-hard routing oracle (BRL branch-and-price). The leader minimises
the social cost of the equilibrium. Until now this was done by a grid over (theta, s) with one warm-started ZMC
equilibrium per point: 63 points and about 2,400 oracle calls per city and seed (E2).

DIP replaces the search by an implementation step: compute the profile the city wants (the social optimum), then
compute the charges under which that profile is an equilibrium, using the carriers' own routing oracle as the
separation oracle. No equilibrium is solved for the leader's decision.

## The method in ten lines

    1  sigma* <- pure social optimum: column generation on the social-cost potential (same oracle, social prices),
       derandomised rounding, coordinate polish                                        (the E3 routine, ~60-150 calls)
    2  Q* <- zone deliveries of sigma*;  kappa_z = gc_z r^2,  m_z = b_z + kappa_z,  dbar_z = mean lot in z
    3  u_ref <- kappa * Q* - (m/2) * dbar          (tangent charge: Pigou term minus a half-lot Cournot subsidy)
    4  u <- u_ref ; cuts <- {}
    5  repeat:  for every carrier i: b_i <- best response to sigma*_-i under u        (N oracle calls, no equilibrium)
    6           if no carrier gains: return u, sigma*                    (sigma* is an exact pure equilibrium under u)
    7           for every gaining carrier: add the cut <q_i(b_i) - q_i(sigma*_i), u> >= J0_i(sigma*_i) - J0_i(b_i) + eps
    8           u <- argmin ||u - u_ref||_1 over the cuts and the box  (LP);  if infeasible: break
    9  fallback (polyhedron empty): best-response dynamics from sigma* under the least-violating u and under u_ref; keep
       the better equilibrium (its loss is bounded by Theorem 9)
    10 instruments: uniform per-delivery charge s = min_z u_z, congestion charge t_z = (u_z - s)/r >= 0 per vehicle-hour

Code: `src/ccu/dip.py` (`dip`, `social_target`, `tangent_charge`, `implement`, `fallback`, `instruments`,
`surcharge_shift`, `grid_family`). Experiments: `experiments/run_dip.py`, `experiments/dip_tiny.py`.

## Why it works (proofs in theory.tex)

1. One instrument per zone (Prop. 1). Every lot has hours h = r d, so the charge per vehicle-hour and per delivery act
   on the same variable: only u_z = s_z + r t_z matters, and (uniform s, t_z >= 0) realises every u.
2. Identity (Lemma 2). Phi_u(sigma) = SC(sigma) - sum kappa/2 (Q - Q*)^2 + L(sigma) + <u - u_tan, Q> + const, with
   L(sigma) = sum (m/2)(d_iz - dbar_z) q_iz. Exact for pure and convexified profiles.
3. Symmetric lots, convexified game (Thm 5): the tangent charge implements the convexified optimum, and every
   convexified equilibrium is socially optimal. Asymmetric lots (Thm 4): loss <= (1 + rho) E with
   E = sum (m/2)|d_iz - dbar_z| d_iz and rho = max kappa/(b + kappa) < 1.
4. Pure game (Thm 7, Prop. 8): the charges that make sigma* an equilibrium form a polyhedron P(sigma*). A carrier's best
   response at sigma*_-i is its most violated constraint, so lines 5-8 terminate (finitely; O(k log) rounds with central
   cuts) with u in P(sigma*) or a proof that P(sigma*) is empty. The leader problem is the single-level problem
   min {SC(sigma) : P(sigma) non-empty}; when DIP ends in the loop, its only loss is the suboptimality of sigma*.
5. Credal imprecision (Thm 12): the Gamma-maximin surcharge translates the polyhedron, u(delta) = u(0) - s_hat(delta),
   so the charges for every width come from one run, and the welfare under ambiguity aversion is the same as without.
   For E-admissibility, maximality and interval dominance, u(0) already works at every width.
6. Two instruments (Prop. 13): a uniform subsidy is exact if the tangent charge is constant across zones; with the
   project's calibration the congestion-free tangent is -0.375 fee / n_z (n_z carriers in the zone), which is exactly
   the grid's optimum range s/fee in [-0.4, -0.2]. The congestion charge buys spatial differentiation, nothing else.

## What is classical and what is new

Classical: the tangent charge (Pigou-Cournot corrective tax, Buchanan 1969, Barnett 1980); personalised
marginal-contribution charges (Wolpert-Tumer; Marden-Wierman 2013); toll polyhedra (Bergendorff-Hearn-Ramana 1997,
Hearn-Ramana 1998; cost-balancing tolls for atomic games, Fotakis-Spirakis); finding target-implementing tolls with an
equilibrium oracle by the ellipsoid method (Bhaskar-Ligett-Schulman-Swamy, FOCS 2014 / GEB 2019); inverse optimisation
by cutting planes (Ahuja-Orlin 2001; Wang 2009; Bodur-Chan-Zhu 2022); best-response cutting planes for pure equilibria of
integer-programming games (Dragotto-Scatamacchia 2023; Duguet-Harks-Schmidt-Schwarz 2025).

New (modest): the exact potential-welfare identity of the lumpy Cournot-congestion game and the loss bounds it gives
(lot-asymmetry number E); the use of the carriers' NP-hard best responses *at the fixed target* as separation oracle
(Bhaskar et al. need an equilibrium per query, which is what costs the grid its calls); the surcharge translation; the
competitor-count rule. The point is practical: one social solve and a few best-response rounds instead of 63
equilibrium solves, with a better result because the instrument space is the full zone vector, not a 2-parameter family.

## Limits

- Result quality = quality of the social target (a column-generation heuristic for the pure optimum).
- Optimistic selection: the target is an exact equilibrium under the returned charges, not necessarily the unique one
  (the experiments also report what ZMC selects from the unpriced warm start).
- Needs D1, one hours-per-delivery ratio, affine demand and linear congestion for the closed forms; the polyhedron and
  the cutting plane work without the ratio (in R^{2Z}).
- When the polyhedron is empty, the fallback is a heuristic with an a posteriori bound only.
