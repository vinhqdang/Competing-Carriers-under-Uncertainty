# Results: Budget-Resource Labelling (BRL)

All numbers come from `prototype.py`, `real_instances.py` and the drivers listed below. They were run on 2026-10-23 on 4 CPU cores in pure Python (numpy/scipy, HiGHS through scipy). Raw data: `results_raw.json` (tests A, B, C, D, F), `results_D.jsonl`, `results_D_loose.json`, `results_D_highdual.json`, `results_realC.json`, `results_E.json`.

## Bug found and fixed during testing (stated for honesty)

The first metro run had an error. `espprc` added the fixed route cost `c0` to reduced costs that already contained it (`cost_profile` includes `c0`), so every reduced cost was overstated by `c0 = 2`. Column generation therefore stopped early, and its "exact" bound sat *above* a feasible plan found by the SAA heuristic (Berlin: 52.775 > 52.548). That contradiction exposed the bug.

Tests C and D were unaffected: enumeration had the same constant shift, and dominance is invariant to constants. Test E was rerun after the fix and now carries a safety check: the minimum reduced cost of every route in every heuristic plan at the final duals (column "min rc known" below) must be >= 0. It is >= 0 in all nine cities.

## Test A: upper expectation formula vs brute force over all joint laws

An LP over all joint pmfs on the product support grid, subject to the p-box constraints on every marginal CDF, maximises `E phi(sum X)`. It is compared with the comonotone formula `int phi(sum Qbar_a(u)) du`.

| Check | Instances | Max relative error |
|---|---|---|
| 2-3 arcs, 4-5 support points, random p-boxes, random kink | 40 | 4.5e-14 |
| Factor model: G with 2 atoms, conditional p-boxes, unknown dependence given G (Thm 7.1) | 20 | 2.5e-14 |

For scale, the comonotone worst case exceeds the value under *independent* worst marginals by 4.5% on average (max 14.1%).

## Test B: budget identity and integrality (Thm 2.1, eq. (2))

60 random routes (2-6 arcs, 3-8 levels, integer quantiles):

| Check | Max absolute error |
|---|---|
| LP `min sum_a c_a(d_a) s.t. sum d_a <= Tmax` vs formula | 1.4e-14 |
| Integer-budget DP vs formula | 1.4e-14 |

## Test C: exactness of BRL pricing against complete enumeration

| Family | Instances | BRL = enumeration | Pointwise = enumeration |
|---|---|---|---|
| Random Euclidean, n = 6-8, K = 4 (test C) | 12 | 12 | 12 |
| Random, n = 6-9, deadline fraction 0.3-2.0, K in {1, 4, 9}, dual scale 0.5-2 (stress) | 40 | 40 | 40 |
| Real metro sub-instances, 9 customer zones, all 9 cities, CG duals x {1.0, 1.3} | 18 | 18 | 18 |

Labels kept (end of run): random n=9 instances, enumeration 79,209 paths, pointwise about 2,400, BRL 12-50. On the real 9-zone instances the gain is small: BRL 460-680 labels vs pointwise 610-800. Here capacity binds after about 4 customers and windows are wide.

## Test D: pricing scaling (random Euclidean, K = 9 sectors, L = 33 levels, capacity 6 stops)

Time in seconds; (labels kept); TO = hit the time limit (60 s). "deterministic mean" is the risk-neutral ESPPRC (rho = 0) on the same instance, for reference. "scenario" is the precise-probability SAA objective with the 40 data days as scenarios, so it optimises a different objective.

| n | deterministic mean | **BRL (functional)** | sector (tau, K=9) | quantile-vector (L=33) | SAA scenarios (S=40) |
|---|---|---|---|---|---|
| 10 | 0.005 (19) | **0.004 (16)** | TO | 2.2 (4,946) | 5.4 (7,904) |
| 10 | 0.017 (36) | **0.008 (16)** | TO | 2.2 (4,391) | 4.7 (7,715) |
| 15 | 0.17 (264) | **0.019 (48)** | TO | TO | TO |
| 15 | 0.03 (69) | **0.010 (24)** | TO | TO | TO |
| 20 | 0.39 (714) | **0.049 (97)** | TO | TO | TO |
| 20 | 1.44 (1,730) | **0.047 (89)** | TO | TO | TO |
| 25 | 0.46 (650) | **0.059 (94)** | TO | TO | TO |
| 25 | 0.49 (693) | **0.065 (109)** | TO | TO | TO |

Whenever a competing rule finished, its minimum reduced cost equalled BRL's.

Loose deadlines (`results_D_loose.json`, deadline 1.5-5x a typical route, 60 s limit). BRL takes 0.015-2.0 s (43-2,417 labels). Pointwise takes 17.6-25.1 s for n = 12 and times out for n >= 16. At its time limit the pointwise incumbent was wrong twice (n=20: 11.51 vs the true 5.16, and -49.9 vs -73.8).

Large duals (`results_D_highdual.json`, duals x 2.5, 120 s limit, many negative routes):

| n | deterministic mean | BRL | pointwise |
|---|---|---|---|
| 12 | 0.55 (1,371) | 0.015 (48) | 16.6 (14,616) |
| 16 | 4.9 (7,349) | 0.018 (50) | TO |
| 20 | 67.9 (43,692) | 0.16 (255) | TO |
| 25 | TO | 1.8 (2,349) | TO (incumbent -138.1 vs BRL -265.5) |

The robust pricing is *faster* than the risk-neutral one here. The reason is that once a partial path is certain to be late at every level, its window collapses to a point and comparisons become scalar (Remark 3.7 of `theory.tex`). This is a property of the instances (deadline pressure), not a general complexity claim.

## Test F: is one risk level enough? (fixed-u sweep vs exact)

Exact robust VRP: set partitioning over all elementary routes with exact robust costs (n = 10, capacity 4, deadline fraction 0.5-1.3, rho in {3, 10, 30}). Competitor: for every grid level u, solve the VRP with additive arc costs `gamma*mubar_a + rho*H_a(u)` exactly, evaluate each solution under the exact robust cost and keep the best. The bound is the max over u.

| | Value |
|---|---|
| Instances where the best fixed-u plan is suboptimal | **9 / 20** |
| Max suboptimality of the best fixed-u plan | **6.42%** |
| Common-u bound gap: median / max | 6.9% / 22.1% |

An earlier run with n = 8, capacity 3, rho = 3: fixed-u was optimal in 10/10, with bound gap 0-8%. So the sweep is a good heuristic on small, mildly penalised instances. It is not exact, and it cannot certify optimality.

## Test E: nine metro instances (column generation with BRL pricing)

Setup (assumptions; see the docstring of `real_instances.py`):
- Free-flow zone-to-zone times from `data/processed/<City>/travel_time_matrix.npy`; depot = highest `depot_score`.
- 22 customer zones sampled by population, 6-15 drops each, 3 min per drop; capacity = `drops_per_vehicle_per_day`; shift = `shift_hours`.
- 9 sectors from k-means. The true sector multipliers are lognormal with a common factor: mean 1 + TomTom all-day congestion, 95% quantile 1 + TomTom peak-hour congestion. Moscow's congestion is imputed as the mean of the other cities, because its value is missing in `city_parameters.csv`.
- The carrier observes 60 days and uses DKW p-boxes (alpha = 0.05), with a support cap of 1 + 2 x peak, giving L = 51 levels.
- Loss in driver-hours: 2 per route + 1 per hour + 3 per hour of overtime.
- Pricing: BRL with ng-routes (|N| = 8); integer plan by price-and-branch (HiGHS MILP on the generated elementary columns, no branching).
- Baselines: Clarke-Wright + relocate/2-opt/swap descent (a routing.py-style heuristic) optimising (i) the p-box worst case, (ii) SAA over the 60 days, (iii) the Wasserstein closed form of `src/ccu/robust.py` (eps = 0.05).

| City | CG iters | cols | CG time (s) | max labels | LP bound | P&B plan | gap % | heur p-box | heur SAA | heur Wass | min rc known |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Berlin | 27 | 1026 | 255 | 3162 | 51.854 | 52.666 | 1.54 | 52.775 | **52.548** | 52.940 | 0.000 |
| Mumbai | 13 | 419 | 20 | 1684 | 53.340 | 54.081 | 1.37 | 54.081 | 54.081 | 54.081 | 0.000 |
| Buenos Aires | 23 | 874 | 150 | 2865 | 47.292 | **48.371** | 2.23 | 49.301 | 49.453 | 49.472 | 0.000 |
| Cairo | 13 | 448 | 36 | 2017 | 38.811 | 40.419 | 3.98 | 40.419 | 40.419 | 40.433 | 0.000 |
| London | 32 | 1176 | 250 | 3464 | 51.039 | 52.035 | 1.91 | 52.035 | **51.377** | 52.446 | 0.000 |
| Moscow* | 27 | 1007 | 149 | 2575 | 42.009 | 43.646 | 3.75 | 43.646 | 43.739 | 43.739 | 0.000 |
| New Delhi | 15 | 464 | 13 | 1136 | 63.026 | 63.183 | 0.25 | 63.183 | 63.183 | 63.184 | 0.000 |
| New York | 70 | 2337 | 680 | 3365 | 46.099 | **46.099** | **0.00** | 51.230 | 51.705 | 51.230 | 0.791 |
| Paris | 29 | 1092 | 304 | 2981 | 37.732 | 38.317 | 1.53 | 38.317 | **38.285** | 38.743 | 0.000 |

(*) Moscow congestion is imputed. All plans are evaluated under the p-box worst case.

Reading the table honestly:
- **BRL column generation converged with exact pricing in all 9 cities.** The LP bound lies below every plan found by any method (checked), so the gap column is a valid optimality gap for the robust objective (the add-on).
- **Better solutions than the heuristics:** New York, 46.10 vs 51.23 (-10.0%, proved optimal since gap 0), and Buenos Aires, 48.37 vs 49.30 (-1.9%). Equal to the best heuristic in 5 cities.
- **Not better:** in Berlin, London and Paris the SAA-optimised heuristic plan has a *lower* p-box cost than our price-and-branch plan (by 0.2%, 1.3% and 0.1%). Price-and-branch without branching is not an exact integer method. A full branch-and-price (branching on arcs, same BRL pricing) would be needed to close the 0.25-4% gaps; it is not implemented.
- Runtime: 13-680 s per city in pure Python. Pricing takes over 99% of the time.

Model conservatism (same plans under other laws; this concerns the *model*, not the algorithm):

| City | Plan | p-box worst case | Independent worst marginals | SAA (60 days) | True law (20,000 draws) |
|---|---|---|---|---|---|
| Berlin | BRL-CG | 52.67 | 49.93 | 39.90 | 38.81 |
| Buenos Aires | BRL-CG | 48.37 | 45.18 | 38.19 | 37.31 |
| Buenos Aires | heur SAA | 49.45 | 44.83 | 35.69 | 34.77 |
| New York | BRL-CG | 46.10 | 43.76 | 36.90 | 36.09 |
| New York | heur p-box / Wass | 51.23 | 49.33 | 35.79 | 33.85 |
| Paris | BRL-CG | 38.32 | 35.78 | 32.09 | 31.66 |

The p-box worst case is 21-36% above the true expected cost. Most of this comes from the DKW band with n = 60 and the support cap (independent worst marginals already sit 13-29% above the truth); unknown dependence adds 5-7%. A plan that is optimal for the robust objective can be worse under the true law: New York, +6.6%; Buenos Aires, +7.3% vs the SAA plan. Users who care about the expected cost under a well-estimated law should not use this criterion. BRL is the right tool when the p-box / unknown-dependence criterion is the one wanted, for example in the credal-equilibrium model of `main.tex`.

## Reproduce

```
cd theory/new_algorithm_B
python prototype.py A B C D F        # tests A-D, F  -> results_raw.json, results_D.jsonl
python -c "import real_instances as ri, json; json.dump(ri.testE(), open('results_E.json','w'), default=float)"
python extra_checks.py               # loose deadlines, large duals, real 9-zone exactness -> results_D_loose.json, results_D_highdual.json, results_realC.json
```
