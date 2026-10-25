# DIP: results

All numbers from `results/summary_dip.csv` (per city/seed rows `results/dip_<city>[_s<seed>].csv`, stages in
`results/dip_parts/`), `results/dip_tiny.csv`; tables printed by `experiments/dip_report.py`. Exact oracle everywhere
(branch-and-price, 20 s per call, 120 s retry, as in the exact E2 run). Seeds 0, 1, 2; nine cities; 27 runs.

## Headline

* **Full-grid cities (London, Buenos Aires, New Delhi; 63-point exact grid known), 9 runs:** DIP reaches **104% to 135%
  of the grid-optimal social-cost gain (mean 115%)** with **4.9% to 9.4% of the grid's oracle calls (mean 6.6%)**.
  The target (95% of the gain with at most 10% of the calls) is met in all 9 runs.
* **All 27 runs:** gain share at least 0.999 of the best grid point evaluated (New York seeds 0 and 1: 0.999, i.e. equal
  within 0.07 USD); calls at most 9.4% of a 63-point grid (for the six reduced-grid cities the comparison is against
  63 x the mean calls per exact point, because only 7-17 exact points exist; against the reduced exact grid alone DIP
  uses 8-31% of its calls, Mumbai being the highest).
* In every run the social target was implemented **exactly**: the cutting-plane loop ended with a charge under which the
  target is a pure Nash equilibrium (fresh-pool exact oracle regret <= 9e-13 USD in all 27 runs). The tangent charge
  alone already implemented it in 18 of 27 runs; the others needed 2-3 rounds (at most 4 cuts).
* The priced equilibrium therefore has the social cost of the column-generation social optimum: PoA of the priced
  equilibrium = 1.000 (London seed 2, Mumbai: 0.995-0.997, i.e. slightly better than the E3 benchmark, thanks to the
  multi-start target). The grid's best point has PoA 1.01-1.08 in the full-grid cities.
* Wall-clock: median 0.22 of the grid's time over the exact-grid runs; but one exact full-grid run is slower
  (London seed 0: 247 s against 157 s; the social pricing calls of column generation are harder branch-and-price
  instances than the warm-started equilibrium calls of a grid). Seed-2 runs of Berlin, Moscow and New York are compared
  with price-and-branch grids, so their times are not comparable.

## Per city and seed

`dip_gain_share` = (SC0 - SC_DIP)/(SC0 - SC_grid best), SC0 = unpriced equilibrium of E2. `dip1_*` = DIP without the
multi-start target improvement (column-generation target only). `dip_calls` counts every oracle query of the method
(social column generation and polish, multi-start, all best responses of the cutting plane), with the same counter as the
E2 `calls` column; the verification by a fresh oracle is not counted (as for the grid's best point). `grid_calls` sums
the exact E2 rows; `dip_calls_share_63` divides by 63 x mean calls per exact grid point. `grid_oracle = pb`: the exact
E2 run of that seed does not exist (Berlin, Moscow, New York seed 2); the 63-point price-and-branch grid is used.

| city | seed | grid_oracle | grid_points | dip_status | dip_rounds | grid_gain_usd | dip_gain_usd | dip_gain_share | dip1_gain_share | dip_calls | dip1_calls | grid_calls | dip_calls_share | dip_calls_share_63 | dip_time_s | grid_time_s | W_dip | W_grid | PoA_unpriced | PoA_grid | PoA_dip | verify_max_regret_fresh |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| London | 0 | exact | 63 | exact | 3 | 345 | 359 | 1.04 | 1.04 | 170 | 130 | 2376 | 0.0715 | 0.0715 | 247 | 157 | 991 | 976 | 1.57 | 1.01 | 1 | 0 |
| London | 1 | exact | 63 | exact | 3 | 216 | 283 | 1.31 | 1.31 | 221 | 186 | 2356 | 0.0938 | 0.0938 | 93.9 | 207 | 908 | 840 | 1.45 | 1.08 | 1 | 0 |
| London | 2 | exact | 63 | exact | 3 | 409 | 433 | 1.06 | 1.05 | 206 | 160 | 2378 | 0.0866 | 0.0866 | 88.3 | 155 | 887 | 863 | 1.94 | 1.02 | 0.995 | 2.84e-14 |
| BuenosAires | 0 | exact | 63 | exact | 1 | 99.4 | 108 | 1.09 | 1.09 | 121 | 96 | 1921 | 0.063 | 0.063 | 65.3 | 299 | 361 | 352 | 1.43 | 1.03 | 1 | 0 |
| BuenosAires | 1 | exact | 63 | exact | 1 | 109 | 114 | 1.05 | 1.05 | 122 | 96 | 1950 | 0.0626 | 0.0626 | 168 | 1.73e+03 | 390 | 385 | 1.42 | 1.01 | 1 | 0 |
| BuenosAires | 2 | exact | 63 | exact | 1 | 78.7 | 84.9 | 1.08 | 1.08 | 105 | 82 | 1943 | 0.054 | 0.054 | 117 | 178 | 374 | 368 | 1.29 | 1.02 | 1 | 0 |
| NewDelhi | 0 | exact | 63 | exact | 2 | 9.08 | 11.1 | 1.23 | 1.23 | 134 | 99 | 2404 | 0.0557 | 0.0557 | 19.7 | 352 | 85.8 | 83.7 | 1.15 | 1.02 | 1 | 1.42e-14 |
| NewDelhi | 1 | exact | 63 | exact | 1 | 14.9 | 20.1 | 1.35 | 1.35 | 119 | 85 | 2418 | 0.0492 | 0.0492 | 61.7 | 353 | 106 | 101 | 1.23 | 1.05 | 1 | 0 |
| NewDelhi | 2 | exact | 63 | exact | 2 | 12.2 | 13.8 | 1.14 | 1.14 | 132 | 103 | 2419 | 0.0546 | 0.0546 | 239 | 1.11e+03 | 101 | 99.7 | 1.16 | 1.02 | 1 | 2.84e-14 |
| Bombay | 0 | exact | 15 | exact | 1 | 1.16 | 3.77 | 3.25 | 2.93 | 139 | 89 | 586 | 0.237 | 0.0565 | 148 | 1.63e+03 | 148 | 146 | 1.02 | 1.02 | 0.997 | 0 |
| Bombay | 1 | exact | 14 | exact | 2 | 5.42 | 6.51 | 1.2 | 1.11 | 169 | 120 | 544 | 0.311 | 0.069 | 193 | 1.08e+03 | 170 | 169 | 1.04 | 1 | 0.997 | 2.84e-14 |
| Bombay | 2 | exact | 14 | exact | 2 | 4.91 | 6.29 | 1.28 | 1.12 | 141 | 95 | 537 | 0.263 | 0.0583 | 376 | 660 | 156 | 155 | 1.04 | 1 | 0.995 | 1.42e-14 |
| Paris | 0 | exact | 14 | exact | 3 | 158 | 161 | 1.02 | 1.02 | 119 | 85 | 542 | 0.22 | 0.0488 | 1.25e+03 | 1.7e+03 | 5.88e+03 | 5.88e+03 | 1.03 | 1 | 1 | 2.27e-13 |
| Paris | 1 | exact | 13 | exact | 1 | 156 | 166 | 1.06 | 1.06 | 116 | 80 | 503 | 0.231 | 0.0476 | 858 | 3.02e+03 | 5.02e+03 | 5.01e+03 | 1.03 | 1 | 1 | 1.14e-13 |
| Paris | 2 | exact | 13 | exact | 2 | 256 | 269 | 1.05 | 1.05 | 109 | 75 | 508 | 0.215 | 0.0443 | 484 | 604 | 5.69e+03 | 5.68e+03 | 1.05 | 1 | 1 | 0 |
| Berlin | 0 | exact | 13 | exact | 1 | 164 | 168 | 1.03 | 1.03 | 104 | 69 | 622 | 0.167 | 0.0345 | 195 | 503 | 8.57e+03 | 8.56e+03 | 1.02 | 1 | 1 | 9.09e-13 |
| Berlin | 1 | exact | 13 | exact | 1 | 136 | 141 | 1.03 | 1.03 | 94 | 62 | 614 | 0.153 | 0.0316 | 174 | 1.31e+03 | 8.69e+03 | 8.69e+03 | 1.02 | 1 | 1 | 0 |
| Berlin | 2 | pb | 63 | exact | 1 | 216 | 244 | 1.13 | 1.13 | 123 | 86 | 2977 | 0.0413 | 0.0413 | 182 | 373 | 9.14e+03 | 9.11e+03 | 1.03 | 1 | 1 | 0 |
| Cairo | 0 | exact | 13 | exact | 1 | 0 | 0 | n/a | n/a | 44 | 20 | 391 | 0.113 | 0.0232 | 258 | 2.72e+03 | 1.07e+03 | 1.07e+03 | 1 | 1 | 1 | 0 |
| Cairo | 1 | exact | 17 | exact | 1 | 0 | 0 | n/a | n/a | 44 | 20 | 519 | 0.0848 | 0.0229 | 98.2 | 2.19e+03 | 1.09e+03 | 1.09e+03 | 1 | 1 | 1 | 0 |
| Cairo | 2 | exact | 13 | exact | 1 | 0 | 0 | n/a | n/a | 45 | 23 | 388 | 0.116 | 0.0239 | 464 | 2.94e+03 | 1.05e+03 | 1.05e+03 | 1 | 1 | 1 | 0 |
| Moscow | 0 | exact | 12 | exact | 1 | 8.46 | 9.28 | 1.1 | 1.1 | 61 | 30 | 454 | 0.134 | 0.0256 | 8.94 | 139 | 6.74e+03 | 6.74e+03 | 1 | 1 | 1 | 0 |
| Moscow | 1 | exact | 10 | exact | 1 | 9.08 | 9.08 | 1 | 1 | 50 | 30 | 380 | 0.132 | 0.0209 | 174 | 628 | 6.93e+03 | 6.93e+03 | 1 | 1 | 1 | 0 |
| Moscow | 2 | pb | 63 | exact | 1 | 25.7 | 25.7 | 1 | 1 | 70 | 40 | 2404 | 0.0291 | 0.0291 | 344 | 91 | 6.64e+03 | 6.64e+03 | 1 | 1 | 1 | 0 |
| NewYork | 0 | exact | 7 | exact | 1 | 69.8 | 69.8 | 0.999 | 0.999 | 50 | 30 | 212 | 0.236 | 0.0262 | 18.9 | 54.8 | 21466 | 21466 | 1 | 1 | 1 | 0 |
| NewYork | 1 | exact | 7 | exact | 1 | 85.1 | 85.1 | 0.999 | 0.999 | 50 | 30 | 213 | 0.235 | 0.0261 | 21.9 | 384 | 18604 | 18604 | 1 | 1 | 1 | 9.09e-13 |
| NewYork | 2 | pb | 63 | exact | 1 | 56.1 | 58.1 | 1.04 | 1.04 | 56 | 32 | 1908 | 0.0294 | 0.0294 | 858 | 105 | 20147 | 20145 | 1 | 1 | 1 | 0 |

## Variants, instruments, credal check

* `fam_*`: DIP restricted to the grid's own two-parameter family `u = s + r theta gc X^NE`. The polyhedron is empty in
  most runs (2 parameters cannot reproduce a zone vector), the fallback is used; `fam_theta` often lies outside the
  grid (theta up to 49), and the restricted method still matches or beats the grid in 17 of 24 runs with a gain and reaches
  95% of it in 19 (mean share 1.00; worst Mumbai seed 0, 0.50). The extra gain of full DIP comes mostly from the zone-differentiated charge.
* `sel_*`: the equilibrium that the grid's own protocol (ZMC warm-started from the unpriced prices) selects under DIP's
  charges. Same profile in 21 of 27 runs; in all 27 its gain is at least 0.999 of the grid's.
* `dip_s_over_fee`: the uniform per-delivery part is a subsidy of 0.37-0.50 fee; `dip_t_max` the largest zone congestion
  charge (USD per vehicle-hour). The city pays the subsidy (`dip_revenue` < 0), as at the grid's best points.
* `credal*`: Gamma-maximin width delta in {0.2, 0.8} with the weights of E4. Charges `u(delta) = u - s_hat(delta)`
  (Theorem 12) make the same target an exact equilibrium in all 27 runs at both widths (regret <= 9e-13) with zero
  further optimisation, so the social cost is unchanged; `credal0.8_unpriced_sc` is the unpriced delta = 0.8
  equilibrium of E4 (London seed 0: 0, service collapses). Caveat: at delta = 0.8 the uniform subsidy reaches
  1-3.6 fee, i.e. above the demand intercept; the charge is a transfer in the welfare accounting, but such a subsidy is
  not a realistic policy.

| city | seed | fam_status | fam_gain_share | fam_s_over_fee | fam_theta | sel_same | sel_gain_share | dip_s_over_fee | dip_t_max | dip_revenue | dip_served_share | credal0.2_regret | credal0.8_regret | credal0.8_sc | credal0.8_unpriced_sc | credal0.8_s_over_fee |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| London | 0 | empty | 1.03 | -0.363 | 11 | False | 1.03 | -0.408 | 21.9 | -1.13e+03 | 0.507 | 0 | 0 | -991 | 0 | -1.76 |
| London | 1 | empty | 1.16 | -0.313 | 4.34 | False | 1.3 | -0.418 | 21.8 | -965 | 0.401 | 0 | 0 | -908 | -100 | -1.74 |
| London | 2 | empty | 1.05 | -0.356 | 10.2 | False | 1.04 | -0.418 | 24.2 | -1.14e+03 | 0.482 | 0 | 0 | -887 | -111 | -1.85 |
| BuenosAires | 0 | empty | 1.09 | -0.342 | 41.7 | True | 1.09 | -0.386 | 4.03 | -275 | 0.723 | 0 | 0 | -361 | -111 | -1.63 |
| BuenosAires | 1 | empty | 1.03 | -0.266 | 20.6 | True | 1.05 | -0.381 | 3.54 | -308 | 0.667 | 0 | 0 | -390 | -131 | -0.977 |
| BuenosAires | 2 | empty | 1.06 | -0.353 | 48.8 | True | 1.08 | -0.422 | 4.1 | -245 | 0.732 | 0 | 0 | -374 | -128 | -2.53 |
| NewDelhi | 0 | empty | 1.02 | -0.314 | 7.72 | False | 1.2 | -0.463 | 1.91 | -66.2 | 0.412 | 0 | 0 | -85.8 | -26 | -2.1 |
| NewDelhi | 1 | empty | 1.25 | -0.314 | 6.83 | True | 1.35 | -0.448 | 1.82 | -75.1 | 0.446 | 0 | 0 | -106 | -43.3 | -1.94 |
| NewDelhi | 2 | empty | 0.92 | -0.33 | 9.91 | True | 1.14 | -0.498 | 2.08 | -53.5 | 0.403 | 0 | 0 | -101 | -53.6 | -3.61 |
| Bombay | 0 | empty | 0.504 | -0.298 | 5.45 | False | 2.93 | -0.472 | 1.89 | -50.1 | 0.491 | 0 | 0 | -148 | -74.6 | -2.64 |
| Bombay | 1 | empty | 0.871 | -0.187 | 2.93 | True | 1.2 | -0.412 | 1.63 | -54.8 | 0.577 | 0 | 0 | -170 | -97.2 | -1.97 |
| Bombay | 2 | empty | 0.874 | -0.121 | 2.43 | False | 1.12 | -0.408 | 1.64 | -55.6 | 0.563 | 0 | 0 | -156 | -82.6 | -2.58 |
| Paris | 0 | empty | 0.993 | -0.339 | 8.75 | True | 1.02 | -0.379 | 27.6 | -1.82e+03 | 0.945 | 0 | 0 | -5.88e+03 | -2.06e+03 | -1.11 |
| Paris | 1 | empty | 0.92 | -0.348 | 9.24 | True | 1.06 | -0.382 | 26.4 | -1.82e+03 | 0.921 | 0 | 4.55e-13 | -5.02e+03 | -1.8e+03 | -1.12 |
| Paris | 2 | empty | 1.03 | -0.353 | 11.3 | True | 1.05 | -0.38 | 27 | -1.67e+03 | 0.952 | 0 | 0 | -5.69e+03 | -2.47e+03 | -1.12 |
| Berlin | 0 | empty | 1.02 | -0.307 | 20.1 | True | 1.03 | -0.38 | 34.2 | -2.77e+03 | 0.947 | 4.55e-13 | 9.09e-13 | -8.57e+03 | -3.24e+03 | -1.04 |
| Berlin | 1 | empty | 0.996 | -0.34 | 11.2 | True | 1.03 | -0.381 | 34.2 | -2.68e+03 | 0.939 | 2.27e-13 | 2.27e-13 | -8.69e+03 | -3.57e+03 | -1.02 |
| Berlin | 2 | empty | 1.13 | -0.355 | 12.5 | True | 1.13 | -0.379 | 34.8 | -2.92e+03 | 0.963 | 0 | 0 | -9.14e+03 | n/a | -2.07 |
| Cairo | 0 | exact | n/a | -0.253 | 30.2 | True | n/a | -0.375 | 2.7 | -133 | 1 | 0 | 0 | -1.07e+03 | -826 | -0.975 |
| Cairo | 1 | exact | n/a | -0.278 | 35.1 | True | n/a | -0.375 | 2.7 | -135 | 1 | 0 | 0 | -1.09e+03 | -846 | -0.976 |
| Cairo | 2 | exact | n/a | -0.285 | 36.7 | True | n/a | -0.375 | 2.69 | -137 | 1 | 0 | 0 | -1.05e+03 | n/a | -0.975 |
| Moscow | 0 | exact | 1.1 | -0.233 | 2.36 | True | 1.1 | -0.372 | 15.4 | -1.85e+03 | 0.997 | 0 | 0 | -6.74e+03 | -3.2e+03 | -1.17 |
| Moscow | 1 | exact | 1 | -0.332 | 1.53 | True | 1 | -0.372 | 15.4 | -2.04e+03 | 1 | 4.55e-13 | 0 | -6.93e+03 | -2.72e+03 | -1.06 |
| Moscow | 2 | exact | 1 | -0.346 | 3.61 | True | 1 | -0.373 | 15.2 | -1.74e+03 | 0.997 | 0 | 0 | -6.64e+03 | n/a | -1.51 |
| NewYork | 0 | exact | 0.999 | -0.4 | 13.5 | True | 0.999 | -0.374 | 62.8 | -5.98e+03 | 1 | 9.09e-13 | 0 | -21466 | -9.71e+03 | -1.04 |
| NewYork | 1 | exact | 0.999 | -0.352 | 5.59 | True | 0.999 | -0.375 | 55.9 | -5.69e+03 | 1 | 0 | 0 | -18604 | -7.19e+03 | -0.982 |
| NewYork | 2 | exact | 1.04 | -0.363 | 7.67 | True | 1.04 | -0.374 | 56.1 | -5.11e+03 | 1 | 0 | 0 | -20147 | n/a | -0.981 |

## Per city

and seed

| city | seed | grid_oracle | grid_points | dip_status | dip_rounds | grid_gain_usd | dip_gain_usd | dip_gain_share | dip1_gain_share | dip_calls | dip1_calls | grid_calls | dip_calls_share | dip_calls_share_63 | dip_time_s | grid_time_s | W_dip | W_grid | PoA_unpriced | PoA_grid | PoA_dip | verify_max_regret_fresh |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| London | 0 | exact | 63 | exact | 3 | 345 | 359 | 1.04 | 1.04 | 170 | 130 | 2376 | 0.0715 | 0.0715 | 247 | 157 | 991 | 976 | 1.57 | 1.01 | 1 | 0 |
| London | 1 | exact | 63 | exact | 3 | 216 | 283 | 1.31 | 1.31 | 221 | 186 | 2356 | 0.0938 | 0.0938 | 93.9 | 207 | 908 | 840 | 1.45 | 1.08 | 1 | 0 |
| London | 2 | exact | 63 | exact | 3 | 409 | 433 | 1.06 | 1.05 | 206 | 160 | 2378 | 0.0866 | 0.0866 | 88.3 | 155 | 887 | 863 | 1.94 | 1.02 | 0.995 | 2.84e-14 |
| BuenosAires | 0 | exact | 63 | exact | 1 | 99.4 | 108 | 1.09 | 1.09 | 121 | 96 | 1921 | 0.063 | 0.063 | 65.3 | 299 | 361 | 352 | 1.43 | 1.03 | 1 | 0 |
| BuenosAires | 1 | exact | 63 | exact | 1 | 109 | 114 | 1.05 | 1.05 | 122 | 96 | 1950 | 0.0626 | 0.0626 | 168 | 1.73e+03 | 390 | 385 | 1.42 | 1.01 | 1 | 0 |
| BuenosAires | 2 | exact | 63 | exact | 1 | 78.7 | 84.9 | 1.08 | 1.08 | 105 | 82 | 1943 | 0.054 | 0.054 | 117 | 178 | 374 | 368 | 1.29 | 1.02 | 1 | 0 |
| NewDelhi | 0 | exact | 63 | exact | 2 | 9.08 | 11.1 | 1.23 | 1.23 | 134 | 99 | 2404 | 0.0557 | 0.0557 | 19.7 | 352 | 85.8 | 83.7 | 1.15 | 1.02 | 1 | 1.42e-14 |
| NewDelhi | 1 | exact | 63 | exact | 1 | 14.9 | 20.1 | 1.35 | 1.35 | 119 | 85 | 2418 | 0.0492 | 0.0492 | 61.7 | 353 | 106 | 101 | 1.23 | 1.05 | 1 | 0 |
| NewDelhi | 2 | exact | 63 | exact | 2 | 12.2 | 13.8 | 1.14 | 1.14 | 132 | 103 | 2419 | 0.0546 | 0.0546 | 239 | 1.11e+03 | 101 | 99.7 | 1.16 | 1.02 | 1 | 2.84e-14 |
| Bombay | 0 | exact | 15 | exact | 1 | 1.16 | 3.77 | 3.25 | 2.93 | 139 | 89 | 586 | 0.237 | 0.0565 | 148 | 1.63e+03 | 148 | 146 | 1.02 | 1.02 | 0.997 | 0 |
| Bombay | 1 | exact | 14 | exact | 2 | 5.42 | 6.51 | 1.2 | 1.11 | 169 | 120 | 544 | 0.311 | 0.069 | 193 | 1.08e+03 | 170 | 169 | 1.04 | 1 | 0.997 | 2.84e-14 |
| Bombay | 2 | exact | 14 | exact | 2 | 4.91 | 6.29 | 1.28 | 1.12 | 141 | 95 | 537 | 0.263 | 0.0583 | 376 | 660 | 156 | 155 | 1.04 | 1 | 0.995 | 1.42e-14 |
| Paris | 0 | exact | 14 | exact | 3 | 158 | 161 | 1.02 | 1.02 | 119 | 85 | 542 | 0.22 | 0.0488 | 1.25e+03 | 1.7e+03 | 5.88e+03 | 5.88e+03 | 1.03 | 1 | 1 | 2.27e-13 |
| Paris | 1 | exact | 13 | exact | 1 | 156 | 166 | 1.06 | 1.06 | 116 | 80 | 503 | 0.231 | 0.0476 | 858 | 3.02e+03 | 5.02e+03 | 5.01e+03 | 1.03 | 1 | 1 | 1.14e-13 |
| Paris | 2 | exact | 13 | exact | 2 | 256 | 269 | 1.05 | 1.05 | 109 | 75 | 508 | 0.215 | 0.0443 | 484 | 604 | 5.69e+03 | 5.68e+03 | 1.05 | 1 | 1 | 0 |
| Berlin | 0 | exact | 13 | exact | 1 | 164 | 168 | 1.03 | 1.03 | 104 | 69 | 622 | 0.167 | 0.0345 | 195 | 503 | 8.57e+03 | 8.56e+03 | 1.02 | 1 | 1 | 9.09e-13 |
| Berlin | 1 | exact | 13 | exact | 1 | 136 | 141 | 1.03 | 1.03 | 94 | 62 | 614 | 0.153 | 0.0316 | 174 | 1.31e+03 | 8.69e+03 | 8.69e+03 | 1.02 | 1 | 1 | 0 |
| Berlin | 2 | pb | 63 | exact | 1 | 216 | 244 | 1.13 | 1.13 | 123 | 86 | 2977 | 0.0413 | 0.0413 | 182 | 373 | 9.14e+03 | 9.11e+03 | 1.03 | 1 | 1 | 0 |
| Cairo | 0 | exact | 13 | exact | 1 | 0 | 0 | n/a | n/a | 44 | 20 | 391 | 0.113 | 0.0232 | 258 | 2.72e+03 | 1.07e+03 | 1.07e+03 | 1 | 1 | 1 | 0 |
| Cairo | 1 | exact | 17 | exact | 1 | 0 | 0 | n/a | n/a | 44 | 20 | 519 | 0.0848 | 0.0229 | 98.2 | 2.19e+03 | 1.09e+03 | 1.09e+03 | 1 | 1 | 1 | 0 |
| Cairo | 2 | exact | 13 | exact | 1 | 0 | 0 | n/a | n/a | 45 | 23 | 388 | 0.116 | 0.0239 | 464 | 2.94e+03 | 1.05e+03 | 1.05e+03 | 1 | 1 | 1 | 0 |
| Moscow | 0 | exact | 12 | exact | 1 | 8.46 | 9.28 | 1.1 | 1.1 | 61 | 30 | 454 | 0.134 | 0.0256 | 8.94 | 139 | 6.74e+03 | 6.74e+03 | 1 | 1 | 1 | 0 |
| Moscow | 1 | exact | 10 | exact | 1 | 9.08 | 9.08 | 1 | 1 | 50 | 30 | 380 | 0.132 | 0.0209 | 174 | 628 | 6.93e+03 | 6.93e+03 | 1 | 1 | 1 | 0 |
| Moscow | 2 | pb | 63 | exact | 1 | 25.7 | 25.7 | 1 | 1 | 70 | 40 | 2404 | 0.0291 | 0.0291 | 344 | 91 | 6.64e+03 | 6.64e+03 | 1 | 1 | 1 | 0 |
| NewYork | 0 | exact | 7 | exact | 1 | 69.8 | 69.8 | 0.999 | 0.999 | 50 | 30 | 212 | 0.236 | 0.0262 | 18.9 | 54.8 | 21466 | 21466 | 1 | 1 | 1 | 0 |
| NewYork | 1 | exact | 7 | exact | 1 | 85.1 | 85.1 | 0.999 | 0.999 | 50 | 30 | 213 | 0.235 | 0.0261 | 21.9 | 384 | 18604 | 18604 | 1 | 1 | 1 | 9.09e-13 |
| NewYork | 2 | pb | 63 | exact | 1 | 56.1 | 58.1 | 1.04 | 1.04 | 56 | 32 | 1908 | 0.0294 | 0.0294 | 858 | 105 | 20147 | 20145 | 1 | 1 | 1 | 0 |

## Why the uniform subsidy is about -0.2 to -0.4 fee (Proposition 13)

DIP's zone charges follow the competitor-count rule u_z ~ -0.375 fee / n_z (n_z carriers with a lot in zone z):
seed 0, correlation of the tangent charge with -0.375/n_z: London 0.983, Buenos Aires 1.000, New Delhi 0.985; mean
charge by n_z (fee units) London -0.378 / -0.172 / -0.106 (n = 1, 2, 3), Buenos Aires -0.375 / -0.185 / -0.122 / -0.09,
New Delhi -0.383 / -0.182 / -0.125 / -0.084 / -0.047. Congestion is a small correction (median kappa/b 0.005-0.04).
The grid's best uniform subsidies (-0.2 to -0.4 fee) are averages of this zone pattern.

## Tiny games, exhaustive enumeration (`experiments/dip_tiny.py`)

210 random games (N = 3-4 carriers, 3-4 customer zones each, 5-6 zones, congestion strength x1/x20/x60), every pure
profile enumerated. `opt_zone` is the **exact** optimistic leader optimum over all zone charges u in [-alpha, alpha]^Z
(smallest social cost among profiles whose implementation polyhedron is non-empty, by LP on all enumerated
constraints); `family`/`uniform`: the same restricted to the grid family / to a uniform charge; `grid`: the 63-point
grid with the potential-minimising equilibrium at each point. Shares are of the exact optimal gain (instances with a
positive gain).

| N | n_cust | congestion_x | instances | with_gain | dip_exact | dip_hits_opt | dip_share | dip1_share | dipx_hits_opt | grid_share | family_opt_share | uniform_opt_share | dip_calls | grid_calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 3 | 1 | 30 | 23 | 1 | 0.967 | 0.99 | 0.99 | 1 | 0.789 | 0.923 | 0.862 | 32.1 | 1.33e+03 |
| 3 | 4 | 1 | 30 | 26 | 1 | 1 | 1 | 1 | 1 | 0.882 | 0.978 | 0.964 | 32.3 | 1.33e+03 |
| 3 | 4 | 20 | 30 | 18 | 1 | 0.9 | 0.938 | 0.882 | 1 | 0.667 | 0.943 | 0.832 | 36.1 | 1.33e+03 |
| 3 | 4 | 60 | 30 | 19 | 1 | 0.9 | 0.936 | 0.898 | 1 | 0.877 | 1 | 0.912 | 36.9 | 1.33e+03 |
| 4 | 3 | 1 | 30 | 17 | 1 | 0.967 | 0.997 | 0.997 | 1 | 0.867 | 0.977 | 0.939 | 42.1 | 1.77e+03 |
| 4 | 3 | 20 | 30 | 12 | 1 | 0.967 | 1 | 1 | 1 | 0.942 | 0.952 | 0.804 | 42.7 | 1.77e+03 |
| 4 | 4 | 60 | 30 | 21 | 1 | 0.833 | 0.922 | 0.91 | 1 | 0.806 | 1 | 0.94 | 49.2 | 1.77e+03 |

* DIP implemented its target exactly in 210/210 games and hit the exact leader optimum in 93%; mean share of the
  optimal gain 0.969 (without restarts 0.954), the grid 0.829, with 32-49 oracle calls against 1,300-1,800.
* With the exact social optimum as target (`dipx`), the leader optimum was reached in **210/210** games: every miss of
  DIP is a miss of the social solver, never of the implementation step (Proposition 8).
* Selection: under DIP's charges the equilibrium is unique in 35% of the games (unpriced: 44%); the
  potential-minimising equilibrium coincides with (or beats) the target in 82%; the worst equilibrium under DIP's charges
  can be much worse (mean share -2.8). DIP is an optimistic-selection method, like the grid with ZMC selection.

## Failures and limits observed

* No city run fell below 95% of the grid gain. In the tiny games DIP got less than 95% of the optimal gain in 10 of 136
  games with a gain (less than half in 3, zero in 1); all of these are target quality (column-generation rounding plus
  multi-start), not implementation.
* The 10%-of-calls target is not met against the *reduced* exact grids (Mumbai 24-31%, Paris 21-23%, New York 24%):
  those grids only have 7-17 exact points chosen by a price-and-branch screening whose calls are not counted.
  Against a 63-point grid all runs are below 9.4%.
* Wall-clock is not uniformly better (London seed 0).
* The grid-family variant fails in Mumbai seed 0 (share 0.50): two parameters cannot express the zone pattern there.
