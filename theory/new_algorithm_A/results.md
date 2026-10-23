# Prototype results (direction A: Zone-Market Clearing, ZMC)

Code: `core.py` (model and exact DP oracle), `baselines.py` (BR, FW+rounding, CG+rounding), `ssd.py` (ZMC),
`prototype.py` (experiments E1 to E5), raw numbers in `results.json`, logs in `e2e4.log` and `e3e5.log`.
`test_oracle.py` checks the DP oracle against brute force (it passes).

## Setup

- **Game.** D1 affine game with `d = 2Z` coordinates (deliveries q_z, vehicle-hours tau_z) and `M = diag(b, gamma c)`. Plans choose integer deliveries per zone. Vehicle visits are `ceil(q/cap)`, and a fleet term `F * ceil(sum_z visits / R)` couples the zones, so plan sets are **not** separable. Own Cournot and congestion terms are included.
- **Oracle.** An exact dynamic programme over zones (state = total visits). Every call is counted, including the calls of the best-response (BR) polish and of the final verification round of BR dynamics.
- **Quality measure.** The potential gap `Phi(sigma) - Phibar*` of the returned **exact pure Nash equilibrium**. `Phibar*` is the convexified optimum from column generation run to convergence; it is a lower bound on every pure potential value. Lower is better. All methods end with the same BR polish, so every returned profile is an exact pure NE (verified).
- **Methods.**
  - `BR`: sequential best responses from the empty profile.
  - `BRms`: multi-start BR with the same budget as ZMC.
  - `FW8`, `CG8`: Frank-Wolfe / column generation on the convexified potential with 8 rounds, then rounding (restricted master plus derandomised rounding, as in main.tex Sect. 8) and BR polish.
  - `ZMC`: 8 rounds, then the same rounding and polish.
  - `CGfull`: column generation to convergence, then rounding and polish (quality reference).

## E1: tiny instances, exact enumeration (30 instances; N = 3-4, up to 262k profiles each)

| method | mean calls | reaches global potential minimum | mean excess over global min |
|---|---|---|---|
| BR | 7.6 | 70% | 0.32 |
| ZMC (6 rounds) | 23.5 | 97% | 6e-5 |
| FW (6 rounds) | 23.4 | 97% | 6e-5 |
| CG (to convergence) | 16.1 | 93% | 3e-4 |

On tiny instances ZMC and FW are equally good. BR is cheapest but lands in a worse equilibrium in 30% of cases. Nothing distinguishes ZMC from the baselines here; dimension is too small.

## E2: scaling in Z, equal budget (5 seeds each). Entries: mean calls / mean potential gap

| N | Z | BR | BRms | FW8 | CG8 | **ZMC** | CGfull | ZMC best of {FW8, CG8, BRms} |
|---|---|---|---|---|---|---|---|---|
| 4 | 30 | 12 / 5.33 | 45 / 3.22 | 38 / 3.64 | 39 / 3.20 | 39 / **2.77** | 58 / 2.69 | 4/5 |
| 5 | 60 | 21 / 15.79 | 56 / 11.84 | 50 / 7.78 | 51 / 7.80 | 49 / **6.90** | 159 / 6.13 | 4/5 |
| 6 | 120 | 28 / 50.16 | 70 / 38.38 | 61 / 21.38 | 63 / 27.49 | 60 / **17.14** | 365 / 14.21 | 4/5 |
| 6 | 250 | 26 / 91.47 | 71 / 80.15 | 64 / 47.92 | 67 / 55.45 | 60 / **33.44** | 797 / 27.80 | 5/5 |

- ZMC's call count is flat in Z: 8 rounds of N calls plus a short polish. CG to convergence grows from 58 to 797 calls.
- At equal budget, ZMC has the smallest gap in 17 of 20 instances. Its advantage over FW and CG grows with Z: at Z = 250 its gap is 30% below FW and 40% below CG.
- ZMC stays 10-20% above full CG, which uses 4 to 13 times more calls.
- BR is the cheapest method by far, but its equilibria have a 2.5 to 3.5 times larger gap. Multi-start BR does not close it.
- Failures: in 3 of 20 instances FW8 or CG8 beat ZMC (e.g. N = 5, Z = 60, seed 2: ZMC 8.29, FW 5.77, CG 5.54).

## Convexified-dual accuracy per round (relative gap of G, N = 5-6, Z = 60/250)

All variants (free secant, bracketed secant, pure bisection) reach 1e-2 in about 5 rounds whatever Z is, then stall at about 1e-3 (bisection about 2e-3). This is the cross-variation floor `M_k kappa_k` of Theorem 6. Column generation reaches 1e-3 after 40-170 calls and goes to 0. **ZMC is not a solver for the convexified problem to high accuracy.** It is useful because the pure-equilibrium problem has a much larger irreducible rounding gap (about 1% of |Phi| here), so precision beyond the floor is wasted.

## E3: stress tests (N = 6, Z = 120, 4 seeds). Entries: mean calls / mean gap

| case | empirical kappa (relative) | BR | FW8 | CG8 | ZMC | CGfull |
|---|---|---|---|---|---|---|
| local supports | 0.24 | 27 / 48.5 | 61 / 19.9 | 63 / 26.1 | 60 / **16.4** | 360 / 13.6 |
| random (non-local) supports | 0.23 | 24 / 47.5 | 62 / 22.1 | 64 / 22.3 | 61 / **15.1** | 361 / 13.2 |
| very strong fleet coupling (4F, R = 1) | 0.08 | **6** / 0.44 | 54 / 0.44 | 27 / 0.44 | 54 / 0.44 | 27 / 0.44 |

- The empirical cross-variation is far from 0, yet ZMC still works. The floor of Theorem 6 is a worst-case bound.
- Honest failure: in the degenerate strong-fleet case carriers serve almost nothing, all methods find the same equilibrium, and **BR wins**: 6 calls against 54 for ZMC. ZMC has a fixed cost of T*N calls that is wasted when the game is easy.

## E4: separable case (kappa = 0, deliveries-only market, no fleet term). Relative dual gap every 3 rounds

| Z | bisection, rounds 1, 4, ..., 28 | secant |
|---|---|---|
| 20 | 1e-1, 6e-3, 2e-4, 7e-6, 2e-6, 3e-7, 3e-8, 3e-9, 3e-10, 4e-11 | ... 7e-10 |
| 80 | 1e-1, 5e-3, 2e-4, 9e-6, 2e-6, 2e-7, 5e-8, 5e-9, 6e-10, 6e-11 | ... 2e-9 |
| 320 | 1e-1, 7e-3, 3e-4, 2e-5, 2e-6, 4e-7, 5e-8, 5e-9, 8e-10, 1e-10 | ... 3e-9 |

The geometric, Z-independent convergence predicted by Corollary 7 is observed exactly; the curves for Z = 20, 80 and 320 coincide. Pure bisection is faster than the secant variant in the tail.

## E5: nine real city maps (zone-level proxy oracle; potential gap relative to |Phibar*|; one seed)

| city | N | Z | BR | BRms | FW8 | CG8 | ZMC | CGfull |
|---|---|---|---|---|---|---|---|---|
| Cairo | 4 | 42 | 14 / 4.37e-3 | 46 / 4.35e-3 | 44 / 4.00e-3 | 44 / 3.76e-3 | 41 / **3.75e-3** | 174 / 3.54e-3 |
| New Delhi | 5 | 120 | 7 / 5.27e-1 | 49 / **5.16e-1** | 48 / 5.24e-1 | 47 / 5.27e-1 | 49 / 5.25e-1 | 1229 / 4.98e-1 |
| Mumbai | 5 | 143 | 20 / 7.54e-2 | 56 / **6.29e-2** | 52 / 6.77e-2 | 51 / 6.95e-2 | 49 / 7.04e-2 | 725 / 5.41e-2 |
| Moscow | 5 | 160 | 15 / 6.52e-2 | 57 / **6.48e-2** | 50 / 6.54e-2 | 50 / 6.59e-2 | 52 / 6.55e-2 | 1510 / 6.24e-2 |
| Buenos Aires | 4 | 208 | 18 / 4.06e-3 | 49 / 4.06e-3 | 42 / 3.96e-3 | 44 / 3.77e-3 | 40 / **3.44e-3** | 736 / 2.76e-3 |
| Paris | 5 | 198 | 25 / **3.31e-2** | 74 / 3.31e-2 | 52 / 3.39e-2 | 52 / 3.68e-2 | 57 / 3.48e-2 | 1510 / 3.15e-2 |
| New York | 4 | 234 | 16 / **4.33e-2** | 47 / 4.33e-2 | 40 / 4.34e-2 | 40 / 4.34e-2 | 43 / 4.39e-2 | 1208 / 4.18e-2 |
| London | 5 | 348 | 7 / 5.02e-1 | 50 / 5.02e-1 | 50 / 5.08e-1 | 52 / **4.99e-1** | 50 / 5.06e-1 | 1508 / 4.84e-1 |
| Berlin | 6 | 593 | 41 / 1.19e-2 | 74 / 1.02e-2 | 68 / 9.21e-3 | 70 / 9.48e-3 | 63 / **6.16e-3** | 1811 / 5.66e-3 |

- ZMC is clearly better only on Berlin, the largest map (d = 1186): a 33% smaller gap than FW8 at fewer calls, and within 9% of full CG, which needs 29 times more calls. It is also best on Cairo and Buenos Aires.
- On the other six maps the differences between all methods are within a few percent, and BR (7-25 calls) is as good as anything. The calibrated proxy games are only mildly nonconvex there, so BR's equilibrium is already near the best one. In New Delhi and London the relative gap is about 0.5 because `|Phibar*|` is small (profits and costs nearly cancel); the absolute differences are small.
- CG to convergence costs 700-1800 calls on the city maps, against about 50 for ZMC.
- Caveat: the city oracle is a zone-level proxy (exact DP with one fleet constraint per carrier), not a street-level VRP. The real routing oracle in `src/ccu/` uses a different model (hub diversion) and was not wired in.

## What did not work or was discarded

1. **Free secant without brackets** (`mode='free'`). Similar on average, but it has no guarantee and showed early overshoot (round-2 gap above round 1). It was replaced by the bracketed version, which carries the theorem.
2. **Learning a full concave surrogate of V_i** (a cutting-plane model refined only where it is wrong). This is exactly column generation / the Kelley-type restricted master. It is known, and it is the dimension-dependent baseline. Discarded as a contribution.
3. **Using the pricing answers at the best price directly as the pure profile.** Their potential gap was 2-5 times larger than after rounding and polish (early scratch runs). The clearing error at the best price is dominated by coordinates where the convexified optimum mixes. The final method therefore keeps rounding and polish.
4. **ZMC as a high-accuracy solver for the convexified game.** It stalls near 1e-3 relative gap on non-separable instances (floor `M_k kappa_k`); use CG or bundle methods for that.
5. **D2 (vehicle-count congestion).** No version: the common-price/anchor argument (Theorem 2(b),(c)) needs exposure = contribution.
