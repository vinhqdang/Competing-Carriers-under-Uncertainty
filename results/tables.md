## E1 base (mean over 3 seeds)
| city | N | Z | d_eff | served_share | served_sd | deliveries | vehicles | vehicle_hours | mean_price | slowdown_pct | profit_total | welfare | welfare_sd | calls | max_regret | max_regret_lp | eta_rel | conv |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NewDelhi | 5 | 120 | 64.7 | 0.259 | 0.0107 | 328 | 10 | 49.1 | 0.803 | 4.18 | 44.7 | 82.7 | 7.01 | 47.7 | 1.42e-14 | 0.43 | 0.134 | 1 |
| Cairo | 4 | 42 | 33 | 1 | 0 | 994 | 27.7 | 125 | 0.885 | 3.61 | 625 | 1.06e+03 | 20.7 | 43 | 0 | 1.49 | 0.00351 | 1 |
| Moscow | 5 | 160 | 72.7 | 0.99 | 0.0035 | 2.36e+03 | 37.7 | 170 | 2.76 | 17.6 | 3.52e+03 | 6.76e+03 | 154 | 48.3 | 2.27e-13 | 5.68 | 0.00582 | 1 |
| BuenosAires | 4 | 208 | 64.7 | 0.367 | 0.0213 | 620 | 9.33 | 44.7 | 0.932 | 0.806 | 109 | 276 | 9.81 | 39.7 | 0 | 1.14 | 0.241 | 1 |
| NewYork | 4 | 234 | 62.7 | 0.989 | 0.00249 | 2.67e+03 | 27.3 | 112 | 6.82 | 7.75 | 1.09e+04 | 2e+04 | 1.44e+03 | 41.7 | 0 | 19.1 | 0.0071 | 1 |
| Bombay | 5 | 143 | 52.7 | 0.448 | 0.0163 | 554 | 15 | 83.1 | 0.751 | 4.59 | 73.8 | 153 | 10 | 47.3 | 7.11e-15 | 1.71 | 0.0689 | 1 |
| London | 5 | 348 | 87.7 | 0.182 | 0.0292 | 408 | 6.67 | 24.8 | 4.67 | 6.68 | 233 | 570 | 101 | 48.3 | 1.14e-13 | 1.14e-13 | 0.457 | 1 |
| Paris | 5 | 198 | 69 | 0.845 | 0.0314 | 1.46e+03 | 21.7 | 105 | 4.67 | 4.98 | 2.13e+03 | 5.33e+03 | 432 | 55.3 | 0 | 11.1 | 0.0427 | 1 |
| Berlin | 6 | 593 | 79 | 0.892 | 0.00845 | 3.18e+03 | 28.7 | 127 | 3.37 | 3.67 | 3.48e+03 | 8.63e+03 | 233 | 60.7 | 2.27e-13 | 6.62 | 0.0351 | 1 |

## E1 sensitivity: change of welfare (%) over low/high of each weak parameter
| city | delivery_fee_usd | driver_wage_usd_per_hour | drops_per_vehicle_per_day | n_major_carriers | parcels_per_capita_per_day |
|---|---|---|---|---|---|
| Berlin | -59..24 | -6..2 | -83..4 | -3..-3 | -0..1 |
| Bombay | -45..202 | -38..24 | -72..168 | -18..29 | -5..1 |
| BuenosAires | -61..419 | -51..-51 | -87..443 | -18..63 | -1..0 |
| Cairo | 19..19 | -5..2 | -31..59 | -26..23 | -0..0 |
| London | -95..363 | -3..34 | -95..789 | -26..107 | -2..4 |
| Moscow | -75..48 | -26..6 | -43..105 | -62..20 | -0..1 |
| NewDelhi | -58..317 | -53..43 | -90..286 | -38..53 | -9..0 |
| NewYork | -41..55 | -8..1 | -57..9 | -27..23 | -0..0 |
| Paris | -58..83 | -4..10 | -56..148 | -16..27 | -0..1 |

## E1 sensitivity: change of served share (pp)
| city | delivery_fee_usd | driver_wage_usd_per_hour | drops_per_vehicle_per_day | n_major_carriers | parcels_per_capita_per_day |
|---|---|---|---|---|---|
| Berlin | -23..2 | -2..1 | -53..1 | 3..3 | -0..0 |
| Bombay | -11..30 | -11..6 | -17..20 | -2..3 | 0..1 |
| BuenosAires | -11..44 | -11..-11 | -26..45 | 1..5 | -1..0 |
| Cairo | 0..0 | 0..0 | 0..0 | 0..0 | 0..0 |
| London | -17..27 | 0..5 | -17..52 | -3..10 | 0..2 |
| Moscow | -21..1 | -5..0 | -3..1 | -1..-0 | 0..0 |
| NewDelhi | -11..27 | -11..8 | -19..21 | -6..6 | -0..0 |
| NewYork | -3..1 | -1..0 | -9..0 | -0..0 | -0..0 |
| Paris | -16..6 | -1..4 | -14..9 | -1..-1 | 0..0 |

## E2 gain of the leader's best charge vs no charge, objective=main (percent of |SC|)
| city | none | congestion_only | delivery_only | both |
|---|---|---|---|---|
| NewDelhi | 0 | 0 | 6.99 | 12.2 |
| Cairo | 0 | 0.128 | 0.0743 | 0.128 |
| Moscow | 0 | 0 | 0.0977 | 0.126 |
| BuenosAires | 0 | 1.67 | 31.7 | 31.7 |
| NewYork | 0 | 0.105 | 0.391 | 0.432 |
| Bombay | 0 | 0 | 0.0852 | 2.02 |
| London | 0 | 1.34 | 47.5 | 54.6 |
| Paris | 0 | 0.833 | 2.83 | 2.91 |
| Berlin | 0 | 0.000592 | 1.08 | 1.37 |

## E2 gain of the leader's best charge vs no charge, objective=broad (percent of |SC|)
| city | none | congestion_only | delivery_only | both |
|---|---|---|---|---|
| NewDelhi | 0 | 82.5 | 100 | 100 |
| Cairo | 0 | 0.664 | 6.02 | 4.34 |
| Moscow | 0 | 3.05 | 0 | 3.59 |
| BuenosAires | 0 | 46.3 | 43.6 | 55.4 |
| NewYork | 0 | 0.136 | 0.334 | 0.395 |
| Bombay | 0 | 64.8 | 100 | 100 |
| London | 0 | 100 | 100 | 100 |
| Paris | 0 | 32.6 | 72.8 | 99.2 |
| Berlin | 0 | 0.579 | 0 | 2.25 |

## E2 best point with both instruments (main objective)
| city | theta | s_over_fee | gain_pct_of_abs | profit | revenue | served_share | slowdown_pct | gini_access | gini_price |
|---|---|---|---|---|---|---|---|---|---|
| Berlin | 8 | -0.2 | 1.37 | 5.16e+03 | -1.92e+03 | 0.928 | 3.69 | 0.195 | 0.0146 |
| Bombay | 8 | -0.2 | 2.02 | 73.8 | -23.9 | 0.521 | 4.54 | 0.526 | 0.0505 |
| BuenosAires | 0.5 | -0.4 | 31.7 | 398 | -528 | 0.793 | 1.16 | 0.399 | 0.0593 |
| Cairo | 8 | 0.2 | 0.128 | 353 | 272 | 1 | 3.62 | 0 | 1.57e-17 |
| London | 8 | -0.4 | 54.6 | 907 | -1.47e+03 | 0.538 | 10.6 | 0.601 | 0.0853 |
| Moscow | 0.5 | -0.4 | 0.126 | 6.86e+03 | -3.37e+03 | 1 | 16.6 | 0 | 5.25e-18 |
| NewDelhi | 2 | -0.2 | 12.2 | 75 | -52.1 | 0.362 | 4.4 | 0.607 | 0.058 |
| NewYork | 2 | -0.1 | 0.432 | 1.37e+04 | -2.1e+03 | 1 | 8.41 | 0 | 4.07e-18 |
| Paris | 8 | -0.4 | 2.91 | 5.16e+03 | -3.13e+03 | 0.965 | 4.65 | 0.0997 | 0.0266 |

## E2 best point with both instruments (broad objective incl. background delay)
| city | theta | s_over_fee | gain_pct_of_abs | profit | revenue | served_share | slowdown_pct | gini_access | gini_price |
|---|---|---|---|---|---|---|---|---|---|
| Berlin | 1 | 0.2 | 2.25 | 1.33e+03 | 2.41e+03 | 0.747 | 3.35 | 0.484 | 0.0965 |
| Bombay | 0.5 | 0.6 | 100 | 0 | 0 | 0 | 0 | nan | nan |
| BuenosAires | 1 | 0.2 | 55.4 | 36 | 77.8 | 0.23 | 0.605 | 0.835 | 0.0548 |
| Cairo | 2 | 0.6 | 4.34 | 121 | 490 | 0.689 | 2.72 | 0.257 | 0.0418 |
| London | 0.5 | 0.6 | 100 | 0 | 0 | 0 | 0 | nan | nan |
| Moscow | 16 | -0.1 | 3.59 | 1.53e+03 | 1.92e+03 | 0.91 | 14.1 | 0.0826 | 0.0385 |
| NewDelhi | 0.5 | 0.6 | 100 | 0 | 0 | 0 | 0 | nan | nan |
| NewYork | 2 | -0.1 | 0.395 | 1.37e+04 | -2.1e+03 | 1 | 8.41 | 0 | 4.07e-18 |
| Paris | 16 | 0.6 | 99.2 | 19 | 341 | 0.04 | 1.12 | 0.957 | 0.00498 |

## E3 price of anarchy / stability (welfare ratios; SO = convexified-CG + rounding, upper bound W_SO_bound)
| city | W_SO | W_SO_bound | W_NE_zmc | W_NE_best | W_NE_worst | n_ne_distinct | W_priced | PoA_zmc | PoS | PoA_priced | PoA | rel_gap_unpriced_pct | rel_gap_priced_pct | Wb_SO | Wb_NE | Wb_priced | gap_broad_unpriced_usd | gap_broad_priced_usd | gap_broad_unpriced_pct_of_W | gap_broad_priced_pct_of_W |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NewDelhi | 85.8 | 95 | 74.6 | 76.3 | 74.5 | 5 | 83.7 | 1.15 | 1.12 | 1.02 | 1.15 | 13 | 2.41 | 0 | -1.21e+03 | 0 | 1.21e+03 | 0 | 1.62e+03 | 0 |
| Cairo | 1.06e+03 | 1.06e+03 | 1.06e+03 | 1.06e+03 | 1.06e+03 | 2 | 1.06e+03 | 1 | 1 | 1 | 1 | 0.118 | -0.0094 | 331 | 204 | 213 | 126 | 117 | 11.9 | 11 |
| Moscow | 6.74e+03 | 6.75e+03 | 6.73e+03 | 6.73e+03 | 6.73e+03 | 5 | 6.74e+03 | 1 | 1 | 1 | 1 | 0.138 | 0.0122 | 3.51e+03 | 3.37e+03 | 3.49e+03 | 135 | 14 | 2.01 | 0.208 |
| BuenosAires | 360 | 380 | 267 | 273 | 267 | 6 | 351 | 1.35 | 1.32 | 1.02 | 1.35 | 25.9 | 2.36 | 91.8 | 42.2 | 65.5 | 49.6 | 26.3 | 18.6 | 9.85 |
| NewYork | 2.15e+04 | 2.15e+04 | 2.14e+04 | 2.14e+04 | 2.14e+04 | 4 | 2.15e+04 | 1 | 1 | 1 | 1 | 0.43 | 0 | 1.44e+04 | 1.43e+04 | 1.43e+04 | 75.6 | 19 | 0.354 | 0.0888 |
| Bombay | 148 | 153 | 144 | 144 | 133 | 6 | 147 | 1.02 | 1.02 | 1 | 1.11 | 2.3 | 0.333 | 0 | -1.36e+03 | 0 | 1.36e+03 | 0 | 942 | 0 |
| London | 991 | 1.2e+03 | 632 | 650 | 615 | 5 | 976 | 1.57 | 1.52 | 1.01 | 1.61 | 36.2 | 1.42 | 0 | -1.28e+03 | 0 | 1.28e+03 | 0 | 203 | 0 |
| Paris | 5.88e+03 | 5.9e+03 | 5.71e+03 | 5.77e+03 | 5.71e+03 | 3 | 5.87e+03 | 1.03 | 1.02 | 1 | 1.03 | 2.9 | 0.0721 | 279 | -4.96e+03 | -37.4 | 5.24e+03 | 316 | 91.7 | 5.54 |
| Berlin | 8.57e+03 | 8.62e+03 | 8.45e+03 | 8.45e+03 | 8.4e+03 | 5 | 8.56e+03 | 1.01 | 1.01 | 1 | 1.02 | 1.4 | 0.0476 | 3.67e+03 | 3.41e+03 | 3.49e+03 | 259 | 182 | 3.07 | 2.16 |

## E4 widest p-box vs eps=0 (change in %)
| city | eps | L | served_share | d_deliveries_pct | d_vehicle_hours_pct | d_welfare_pct | routing_cost | converged | max_regret |
|---|---|---|---|---|---|---|---|---|---|
| Berlin | 0.406 | 19 | 0.857 | -7.68 | -7.68 | -17.5 | 7.1e+03 | True | 0 |
| BuenosAires | 0.406 | 19 | 0.288 | -56.4 | -56.4 | -57.2 | 406 | True | 0 |
| Bombay | 0.406 | 19 | 0.412 | -22.8 | -22.8 | -29.2 | 302 | True | 0 |
| London | 0.406 | 19 | 0.133 | -55.7 | -55.7 | -69.6 | 1.17e+03 | True | 0 |
| Cairo | 0.406 | 19 | 1 | 0 | 0 | -2.76 | 260 | True | 0 |
| Moscow | 0.406 | 19 | 0.979 | -2.07 | -2.07 | -11.1 | 2.93e+03 | True | 0 |
| NewDelhi | 0.406 | 19 | 0.191 | -54.5 | -54.5 | -61 | 158 | True | 0 |
| NewYork | 0.406 | 19 | 0.979 | -2.08 | -2.08 | -10.3 | 8.07e+03 | True | 0 |
| Paris | 0.406 | 19 | 0.868 | -6.94 | -6.94 | -15.8 | 5e+03 | True | 0 |

## E4 widest Gamma-maximin surcharge delta vs delta=0
| city | delta | served_share | d_deliveries_pct | d_vehicle_hours_pct | slowdown_pct | d_welfare_pct | converged | max_regret |
|---|---|---|---|---|---|---|---|---|
| Berlin | 0.8 | 0.248 | -72 | -72 | 1.89 | -60.7 | True | 1.14e-13 |
| BuenosAires | 0.8 | 0.121 | -67.9 | -67.9 | 0.544 | -57.9 | True | 0 |
| Bombay | 0.8 | 0.165 | -61.7 | -61.7 | 2.68 | -48.3 | True | 0 |
| London | 0.8 | 0 | -100 | -100 | 0 | -100 | True | 0 |
| Cairo | 0.8 | 0.689 | -31.1 | -31.1 | 2.72 | -22.3 | True | 0 |
| Moscow | 0.8 | 0.387 | -60.9 | -60.9 | 9.03 | -51.9 | True | 5.68e-14 |
| NewDelhi | 0.8 | 0.0609 | -75.5 | -75.5 | 3.78 | -65.2 | True | 0 |
| NewYork | 0.8 | 0.352 | -64.4 | -64.4 | 6.44 | -55.8 | True | 0 |
| Paris | 0.8 | 0.244 | -72.3 | -72.3 | 2.73 | -61.4 | True | 5.68e-14 |

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
