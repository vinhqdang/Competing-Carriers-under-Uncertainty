## E1 base (mean over 3 seeds)
| city | N | Z | d_eff | served_share | served_sd | deliveries | vehicles | vehicle_hours | mean_price | slowdown_pct | profit_total | welfare | welfare_sd | calls | max_regret | max_regret_lp | eta_rel | conv |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NewDelhi | 5 | 120 | 64.7 | 0.259 | 0.0107 | 328 | 10 | 49.1 | 0.803 | 4.18 | 44.7 | 82.7 | 7.01 | 47.7 | 0 | 7.11e-15 | 0.119 | 1 |
| Cairo | 4 | 42 | 33 | 1 | 0 | 994 | 27.7 | 125 | 0.885 | 3.61 | 626 | 1.07e+03 | 20.4 | 39 | 0 | 0.00201 | -0.000244 | 1 |
| Moscow | 5 | 160 | 72.7 | 0.99 | 0.0035 | 2.36e+03 | 37.7 | 170 | 2.76 | 17.6 | 3.52e+03 | 6.76e+03 | 154 | 46.7 | 2.27e-13 | 1.24 | 0.00357 | 1 |
| BuenosAires | 4 | 208 | 64.7 | 0.359 | 0.0328 | 605 | 9 | 43.6 | 0.941 | 0.775 | 112 | 272 | 18.8 | 39.3 | 0 | 2.13e-14 | 0.243 | 1 |
| NewYork | 4 | 234 | 62.7 | 0.989 | 0.00249 | 2.67e+03 | 27.3 | 112 | 6.82 | 7.75 | 1.09e+04 | 2e+04 | 1.44e+03 | 38.7 | 9.09e-13 | 4.84 | 0.00497 | 1 |
| Bombay | 5 | 143 | 52.7 | 0.448 | 0.0163 | 554 | 15 | 83.1 | 0.751 | 4.59 | 73.8 | 153 | 10 | 47.3 | 1.42e-14 | 1.78e-14 | 0.0464 | 1 |
| London | 5 | 348 | 87.7 | 0.182 | 0.0292 | 408 | 6.67 | 24.8 | 4.67 | 6.68 | 233 | 570 | 101 | 48.3 | 1.14e-13 | 1.14e-13 | 0.438 | 1 |
| Paris | 5 | 198 | 69 | 0.847 | 0.0352 | 1.46e+03 | 21.7 | 105 | 4.66 | 4.99 | 2.11e+03 | 5.33e+03 | 437 | 49.7 | 0 | 0.759 | 0.0387 | 1 |
| Berlin | 6 | 593 | 79 | 0.889 | 0.0121 | 3.18e+03 | 28.7 | 127 | 3.36 | 3.68 | 3.48e+03 | 8.62e+03 | 256 | 58 | 0 | 0.9 | 0.0294 | 1 |

## E1 sensitivity: change of welfare (%) over low/high of each weak parameter
| city | delivery_fee_usd | driver_wage_usd_per_hour | drops_per_vehicle_per_day | n_major_carriers | parcels_per_capita_per_day |
|---|---|---|---|---|---|
| Berlin | -59..24 | -5..3 | -83..4 | -3..-3 | 0..1 |
| Bombay | -45..202 | -38..24 | -72..168 | -18..29 | -5..1 |
| BuenosAires | -59..449 | -48..-48 | -87..474 | -13..72 | 4..6 |
| Cairo | 19..19 | -6..2 | -31..59 | -26..23 | -0..-0 |
| London | -95..363 | -3..34 | -95..789 | -26..107 | -2..4 |
| Moscow | -75..48 | -26..6 | -43..105 | -62..20 | -0..1 |
| NewDelhi | -58..317 | -53..43 | -90..286 | -38..53 | -9..0 |
| NewYork | -41..55 | -8..1 | -57..9 | -27..23 | -0..0 |
| Paris | -58..82 | -4..10 | -56..148 | -16..27 | -0..1 |

## E1 sensitivity: change of served share (pp)
| city | delivery_fee_usd | driver_wage_usd_per_hour | drops_per_vehicle_per_day | n_major_carriers | parcels_per_capita_per_day |
|---|---|---|---|---|---|
| Berlin | -22..2 | -1..2 | -52..2 | 3..3 | 1..1 |
| Bombay | -11..30 | -11..6 | -17..20 | -2..3 | 0..1 |
| BuenosAires | -7..48 | -7..-7 | -22..49 | 5..9 | 3..4 |
| Cairo | 0..0 | 0..0 | 0..0 | 0..0 | 0..0 |
| London | -17..27 | 0..5 | -17..52 | -3..10 | 0..2 |
| Moscow | -21..1 | -5..0 | -3..1 | -1..-0 | 0..0 |
| NewDelhi | -11..27 | -11..8 | -19..21 | -6..6 | -0..0 |
| NewYork | -3..1 | -1..0 | -9..0 | -0..0 | -0..0 |
| Paris | -17..5 | -1..3 | -14..8 | -2..-1 | -1..-0 |

## E2 gain of the leader's best charge vs no charge, objective=main: mean (sd; min..max) over 1 seeds, percent of |SC|
| city | none | congestion_only | delivery_only | both |
|---|---|---|---|---|
| Cairo | 0 (0; 0..0) | 0 (0; 0..0) | 0 (0; 0..0) | 0 (0; 0..0) |
| BuenosAires | 0 (0; 0..0) | 3.52 (4.2; 0.532..6.51) | 33.3 (8.6; 27.2..39.4) | 33.3 (8.6; 27.2..39.4) |
| London | 0 (nan; 0..0) | 1.34 (nan; 1.34..1.34) | 50 (nan; 50..50) | 54.6 (nan; 54.6..54.6) |
| Paris | 0 (0; 0..0) | 0.0412 (0.071; 0..0.124) | 3.47 (1.1; 2.77..4.72) | 3.57 (1; 2.77..4.72) |

## E2 gain of the leader's best charge vs no charge, objective=broad: mean (sd; min..max) over 1 seeds, percent of |SC|
| city | none | congestion_only | delivery_only | both |
|---|---|---|---|---|
| Cairo | 0 (0; 0..0) | 0 (0; 0..0) | 2.06 (1.8; 0..3.26) | 4.59 (2.6; 2.47..7.5) |
| BuenosAires | 0 (0; 0..0) | 2.91 (1.6; 1.79..4.02) | 0 (0; 0..0) | 2.86 (2.5; 1.09..4.62) |
| London | 0 (nan; 0..0) | 100 (nan; 100..100) | 100 (nan; 100..100) | 100 (nan; 100..100) |
| Paris | 0 (0; 0..0) | 37.7 (6.4; 31.7..44.5) | 74.2 (1.7; 72.3..75.6) | 99.1 (0.98; 98.1..100) |

## E2 share of the two-instrument gain captured by the per-delivery instrument alone (per seed order 0 / 1 / 2)
| city | both_mean | both_min | both_max | share_by_seed | share_mean | share_sd | cong_only_max | best_s_by_seed |
|---|---|---|---|---|---|---|---|---|
| Cairo | 0 | 0 | 0 | n/a / n/a / n/a | nan | nan | 0 | 0 / 0 / -0.6 |
| BuenosAires | 33.3 | 27.2 | 39.4 | 1.00 / 1.00 | 1 | 0 | 6.51 | -0.4 / -0.4 |
| London | 54.6 | 54.6 | 54.6 | 0.92 | 0.916 | nan | 1.34 | -0.4 |
| Paris | 3.57 | 2.77 | 4.72 | 1.00 / 0.91 / 1.00 | 0.97 | 0.0521 | 0.124 | -0.4 / -0.4 / -0.6 |

## E2 best point with both instruments (main objective), over seeds
| city | n_seeds | theta_mean | theta_sd | theta_min | theta_max | s_over_fee_mean | s_over_fee_sd | s_over_fee_min | s_over_fee_max | gain_pct_of_abs_mean | gain_pct_of_abs_sd | gain_pct_of_abs_min | gain_pct_of_abs_max | served_share_mean | served_share_sd | served_share_min | served_share_max | revenue_mean | revenue_sd | revenue_min | revenue_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BuenosAires | 2 | 0.5 | 0 | 0.5 | 0.5 | -0.4 | 0 | -0.4 | -0.4 | 33.3 | 8.64 | 27.2 | 39.4 | 0.786 | 0.00986 | 0.779 | 0.793 | -506 | 30.7 | -528 | -484 |
| Cairo | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| London | 1 | 8 | nan | 8 | 8 | -0.4 | nan | -0.4 | -0.4 | 54.6 | nan | 54.6 | 54.6 | 0.538 | nan | 0.538 | 0.538 | -1.47e+03 | nan | -1.47e+03 | -1.47e+03 |
| Paris | 3 | 5.5 | 4.33 | 0.5 | 8 | -0.333 | 0.115 | -0.4 | -0.2 | 3.57 | 1.02 | 2.77 | 4.72 | 0.948 | 0.0507 | 0.891 | 0.988 | -2.71e+03 | 1.69e+03 | -4.16e+03 | -849 |

## E2 best point with both instruments (broad objective incl. background delay), per seed
| city | seed | theta | s_over_fee | gain_pct_of_abs | profit | revenue | served_share | slowdown_pct | gini_access | gini_price |
|---|---|---|---|---|---|---|---|---|---|---|
| BuenosAires | 0 | 4 | 0.1 | 4.62 | 63.4 | 54 | 0.291 | 0.66 | 0.776 | 0.0504 |
| BuenosAires | 2 | 8 | 0.1 | 1.09 | 89.8 | 58 | 0.302 | 0.586 | 0.803 | 0.0308 |
| Cairo | 0 | 4 | 0.6 | 2.47 | 113 | 497 | 0.689 | 2.72 | 0.257 | 0.0418 |
| Cairo | 1 | 16 | 0.6 | 7.5 | 74.9 | 537 | 0.673 | 2.64 | 0.309 | 0.0421 |
| Cairo | 2 | 16 | 0.6 | 3.81 | 81 | 500 | 0.652 | 2.47 | 0.331 | 0.0427 |
| London | 0 | 0.5 | 0.6 | 100 | 0 | 0 | 0 | 0 | nan | nan |
| Paris | 0 | 16 | 0.6 | 99.3 | 19 | 341 | 0.04 | 1.12 | 0.957 | 0.00498 |
| Paris | 1 | 16 | 0.6 | 100 | 0 | 0 | 0 | 0 | nan | nan |
| Paris | 2 | 16 | 0.6 | 98.1 | 41.7 | 724 | 0.0848 | 1.1 | 0.903 | 0.0121 |

## E2 equilibrium exactness over all seeds (max regret vs oracle in the grid; fresh-pool regret at the best point)
| city | max_regret_grid | all_converged | max_regret_fresh_best_point |
|---|---|---|---|
| BuenosAires | 0 | True | 5.68e-14 |
| Cairo | 0 | True | 0 |
| London | 0 | True | 1.14e-13 |
| Paris | 2.27e-13 | True | 0 |

## E3 price of anarchy / stability over seeds: mean (sd; min..max) (PoA = W_SO / W_NE, main objective; priced_gap = % of W_SO)
| city | PoA_zmc | PoS | PoA_worst_NE | PoA_priced | priced_gap_pct | max_regret_ne |
|---|---|---|---|---|---|---|
| Cairo | 1 (0; 1..1) | 1 (0; 1..1) | 1 (0; 1..1) | 1 (0; 1..1) | 0 (0; 0..0) | 0 |
| BuenosAires | 1.36 (0.096; 1.29..1.43) | 1.3 (0.034; 1.27..1.32) | 1.37 (0.086; 1.31..1.43) | 1.02 (0.006; 1.02..1.03) | 2.06 (0.57; 1.65..2.46) | 0 |
| London | 1.57 (nan; 1.57..1.57) | 1.52 (nan; 1.52..1.52) | 1.61 (nan; 1.61..1.61) | 1.01 (nan; 1.01..1.01) | 1.42 (nan; 1.42..1.42) | 0 |
| Paris | 1.04 (0.015; 1.03..1.05) | 1.04 (0.017; 1.03..1.05) | 1.04 (0.015; 1.03..1.05) | 1 (0.0013; 1..1) | 0.139 (0.13; 0.0475..0.23) | 0 |

## E3 per city and seed (welfare ratios; SO = convexified-CG + rounding, upper bound W_SO_bound)
| city | seed | W_SO | W_SO_bound | W_NE_zmc | W_NE_best | W_NE_worst | n_ne_distinct | W_priced | PoA_zmc | PoS | PoA_priced | PoA | rel_gap_unpriced_pct | rel_gap_priced_pct | Wb_SO | Wb_NE | Wb_priced | gap_broad_unpriced_usd | gap_broad_priced_usd | gap_broad_unpriced_pct_of_W | gap_broad_priced_pct_of_W | max_regret_ne |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BuenosAires | 0 | 361 | 380 | 252 | 273 | 252 | 6 | 352 | 1.43 | 1.32 | 1.03 | 1.43 | 30 | 2.46 | 90.5 | 60.1 | 62.9 | 30.4 | 27.6 | 12.1 | 11 | 0 |
| BuenosAires | 2 | 374 | 394 | 289 | 294 | 286 | 3 | 368 | 1.29 | 1.27 | 1.02 | 1.31 | 22.7 | 1.65 | 122 | 110 | 111 | 12.6 | 11.4 | 4.35 | 3.93 | 0 |
| Cairo | 0 | 1.07e+03 | 1.07e+03 | 1.07e+03 | 1.07e+03 | 1.07e+03 | 3 | 1.07e+03 | 1 | 1 | 1 | 1 | 0 | 0 | 331 | 207 | 212 | 124 | 119 | 11.6 | 11.1 | 0 |
| Cairo | 1 | 1.09e+03 | 1.09e+03 | 1.09e+03 | 1.09e+03 | 1.09e+03 | 2 | 1.09e+03 | 1 | 1 | 1 | 1 | 0 | 0 | 329 | 200 | 216 | 128 | 113 | 11.8 | 10.4 | 0 |
| Cairo | 2 | 1.05e+03 | 1.05e+03 | 1.05e+03 | 1.05e+03 | 1.05e+03 | 2 | 1.05e+03 | 1 | 1 | 1 | 1 | 0 | 0 | 329 | 214 | 222 | 115 | 107 | 11 | 10.2 | 0 |
| London | 0 | 991 | 1.2e+03 | 632 | 650 | 615 | 6 | 976 | 1.57 | 1.52 | 1.01 | 1.61 | 36.2 | 1.42 | 0 | -1.28e+03 | 0 | 1.28e+03 | 0 | 203 | 0 | 0 |
| Paris | 0 | 5.88e+03 | 5.9e+03 | 5.72e+03 | 5.73e+03 | 5.72e+03 | 3 | 5.88e+03 | 1.03 | 1.03 | 1 | 1.03 | 2.74 | 0.0475 | 264 | -5e+03 | -37.4 | 5.27e+03 | 302 | 92.1 | 5.28 | 0 |
| Paris | 2 | 5.69e+03 | 5.74e+03 | 5.42e+03 | 5.42e+03 | 5.42e+03 | 3 | 5.68e+03 | 1.05 | 1.05 | 1 | 1.05 | 4.73 | 0.23 | 172 | -5.15e+03 | -99.9 | 5.32e+03 | 272 | 98.1 | 5.02 | 0 |

## Conclusions by seed. C1: per-delivery instrument alone captures >= half of the two-instrument gain (n/a where that gain < 0.5% of |SC|); C2: congestion charge alone gains < 1.7% of |SC|; C3: PoA >= 1.10 (ZMC equilibrium, and worst equilibrium found)
| city | C1_delivery_alone_ge_half_by_seed | C1_flips | C2_congestion_only_max_pct | C2_holds_lt_1p7 | C3_PoA_zmc_by_seed | C3_PoA_worstNE_by_seed | C3_large_ge_1p10_seeds | C3_worstNE_ge_1p10_seeds |
|---|---|---|---|---|---|---|---|---|
| Cairo | n/a / n/a / n/a | 0 | 0 | True | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0 | 0 |
| BuenosAires | yes / yes | 0 | 6.51 | False | 1.43 / 1.29 | 1.43 / 1.31 | 2 | 2 |
| London | yes | 0 | 1.34 | True | 1.57 | 1.61 | 1 | 1 |
| Paris | yes / yes / yes | 0 | 0.124 | True | 1.03 / 1.05 | 1.03 / 1.05 | 0 | 0 |

## Headline, mean +- sd over seeds (gains in % of |SC|, main objective; priced_gap = (W_SO - W_priced)/W_SO in %; pbox = widest p-box vs eps=0)
| city | seeds | gain_cong_only | gain_delivery_only | gain_both | share_delivery | PoA | PoA_worst | PoS | priced_gap_pct | pbox_d_deliv_pct | pbox_d_welfare_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Cairo | 3 | 0 +- 0 | 0 +- 0 | 0 +- 0 | nan +- nan | 1 +- 0 | 1 +- 0 | 1 +- 0 | 0 +- 0 | 0 +- 0 | -2.75 +- 0.042 |
| BuenosAires | 2 | 3.52 +- 4.2 | 33.3 +- 8.6 | 33.3 +- 8.6 | 1 +- 0 | 1.36 +- 0.096 | 1.37 +- 0.086 | 1.3 +- 0.034 | 2.06 +- 0.57 | -53 +- 6.5 | -53 +- 7.3 |
| London | 1 | 1.34 +- nan | 50 +- nan | 54.6 +- nan | 0.916 +- nan | 1.57 +- nan | 1.61 +- nan | 1.52 +- nan | 1.42 +- nan | -63.4 +- 13 | -73.9 +- 7.4 |
| Paris | 3 | 0.0412 +- 0.071 | 3.47 +- 1.1 | 3.57 +- 1 | 0.97 +- 0.052 | 1.04 +- 0.015 | 1.04 +- 0.015 | 1.04 +- 0.017 | 0.139 +- 0.13 | -9.16 +- 3.1 | -17 +- 1.2 |

## Verification (c) and E5: calls and relative potential gap (vs convexified CG optimum)
| city | N | Z | d_eff | calls_BR | calls_CG(conv) | calls_CG8 | calls_FW8 | calls_ZMC8 | gap_BR | gap_CG(conv) | gap_CG8 | gap_FW8 | gap_ZMC8 | zmc_calls_per_carrier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NewDelhi | 5 | 120 | 64 | 14 | 65 | 50 | 45 | 45 | 0.138 | 0.102 | 0.102 | 0.102 | 0.102 | 9 |
| Cairo | 4 | 42 | 32 | 8 | 16 | 16 | 24 | 36 | 1.05e-07 | 1.05e-07 | 1.05e-07 | 1.05e-07 | 1.05e-07 | 9 |
| Moscow | 5 | 160 | 71 | 12 | 60 | 45 | 45 | 45 | 0.0022 | 0.0022 | 0.0022 | 0.0022 | 0.0022 | 9 |
| BuenosAires | 4 | 208 | 62 | 10 | 91 | 40 | 37 | 39 | 0.179 | 0.16 | 0.16 | 0.166 | 0.163 | 9.75 |
| NewYork | 4 | 234 | 64 | 8 | 76 | 36 | 36 | 36 | 0.00451 | 0.00437 | 0.00437 | 0.00437 | 0.00451 | 9 |
| Bombay | 5 | 143 | 55 | 14 | 60 | 48 | 48 | 48 | 0.046 | 0.0198 | 0.0198 | 0.0198 | 0.0198 | 9.6 |
| London | 5 | 348 | 89 | 15 | 70 | 50 | 49 | 49 | 0.2 | 0.18 | 0.18 | 0.18 | 0.18 | 9.8 |
| Paris | 5 | 198 | 68 | 13 | 108 | 50 | 50 | 50 | 0.0274 | 0.0274 | 0.0274 | 0.0274 | 0.0278 | 10 |
| Berlin | 6 | 593 | 82 | 17 | 143 | 59 | 59 | 65 | 0.0232 | 0.0246 | 0.0246 | 0.0232 | 0.0243 | 10.8 |

## Verification (a) tiny games, exhaustive enumeration
| method | instances | mean_calls | is_ne_enum | max_regret_fresh | hits_global | hits_best_ne | mean_excess_over_global |
|---|---|---|---|---|---|---|---|
| ZMC6 | 40 | 17.5 | 1 | 0 | 1 | 1 | 0 |
| BR | 40 | 4.85 | 1 | 0 | 0.875 | 0.875 | 0.932 |
| FW6 | 40 | 16.7 | 1 | 0 | 0.95 | 0.95 | 0.0671 |
| CG | 40 | 11.1 | 1 | 0 | 0.975 | 0.975 | 0.0203 |

## E6 theory checks (clearing identity, Theorem 2 bound, brackets)
| city | max_abs_identity_resid | thm2_bound_holds_frac | inverted_brackets_max | n_act | width_after_8 | width_med_after_8 | frac_within_T4 | frac_within_T8 | err_max_T8 | bound_T8 | inverted_T12 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Berlin | 1.82e-12 | 1 | 0 | 164 | 0.0435 | 0.00297 | 1 | 1 | 0.00385 | 0.0625 | 0 |
| Bombay | 4.26e-14 | 1 | 0 | 110 | 0.0435 | 0 | 1 | 1 | 0.00385 | 0.0625 | 0 |
| BuenosAires | 5.68e-14 | 1 | 0 | 124 | 0.0435 | 0.00415 | 1 | 1 | 0.00385 | 0.0625 | 0 |
| Cairo | 1.59e-13 | 0.875 | 0 | 64 | 0.0435 | 0 | 1 | 1 | 0.00385 | 0.0625 | 0 |
| London | 1.14e-13 | 1 | 0 | 178 | 0.0435 | 0 | 1 | 1 | 0.00385 | 0.0625 | 0 |
| Moscow | 8.1e-13 | 1 | 0 | 142 | 0.0435 | 0 | 1 | 1 | 0.00385 | 0.0625 | 0 |
| NewDelhi | 2.84e-14 | 1 | 0 | 128 | 0.0435 | 0 | 1 | 1 | 0.00385 | 0.0625 | 0 |
| NewYork | 3.35e-12 | 1 | 0 | 128 | 0.0435 | 0 | 1 | 1 | 0.00385 | 0.0625 | 0 |
| Paris | 1.48e-12 | 1 | 0 | 136 | 0.0415 | 0.00441 | 1 | 1 | 0.00385 | 0.0625 | 0 |
