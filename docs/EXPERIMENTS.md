# Game-theoretic experiments: ZMC with a BRL carrier oracle on nine city maps

All numbers come from the files in `results/` (CSV per experiment and city; `results/tables.md` holds every table of
this page in machine-generated form). Figures are in `figures/`. Seeds are fixed (`seed 0` for the leader, E3, E4, E6,
seeds 0-2 for E1). Everything here is a **model of a representative slice of each city**, calibrated from
`data/parameters/`; it is not a forecast.

## 1. What was built

| file | content |
|---|---|
| `src/ccu/brl.py` | numba port of the exact BRL pricer (functional dominance, ng-routes) of `theory/new_algorithm_B`; column generation + packing MILP (price-and-branch) over a persistent route pool. Tested against the prototype and against enumeration (`tests/test_brl.py`). |
| `src/ccu/zmc.py` | ZMC (bracketed secant on the zone clearing residual), restricted master, derandomised rounding, best-response polish, and the baselines BR, Frank-Wolfe+rounding, column generation, ported from `theory/new_algorithm_A`. |
| `src/ccu/zmc_brl.py` | the integration: `RoutingGame` (carrier oracle = BRL column generation at a common zone price vector, returns plan, p-box cost and contribution `x_i(p)` in R^{2Z}), city calibration `build_city_game`, tiny games and exhaustive enumeration, social-cost variant, metrics. |
| `tests/test_brl.py`, `tests/test_zmc_brl.py` | 17 tests (pricing = prototype; CG vs enumeration; ZMC equilibrium = exhaustive NE; independent-oracle regret = 0; clearing identity; city smoke test). 59 tests pass. |
| `experiments/` | `run_equilibria.py` (E1, sensitivity), `run_leader.py` (E2, E3), `run_imprecision.py` (E4), `run_verification.py` (verification, E5, E6), `run_city.sh`, `summarize.py`, `plot_equilibria.py`, `plot_results.py`. |

### The carrier oracle

At a price vector lambda (per-zone prices on deliveries and on vehicle-hours) carrier i solves
`min_p ctilde_i(p) + <lambda, a_i(p)>` over plans = sets of node-disjoint routes from its depot over its 22 customer
zones (all-or-nothing lots). Every served zone adds an additive node cost (prize `-alpha d`, own Cournot and congestion
terms, charges, `lambda`), and each route costs the BRL upper expectation of the loss `fixed + gamma T + rho (T - Tmax)^+`
under DKW p-boxes for 9 sector multipliers with unknown dependence (comonotone worst case). The oracle is column
generation with exact BRL pricing to LP convergence, then an integer packing over the generated elementary columns
(reduced-cost fixing, HiGHS). It returns the plan, its p-box route cost, its aggregate contribution `a_i(p) = (q_z, tau_z)`,
and the LP value, a lower bound on the oracle objective. Route costs do not depend on prices, so the column pool of a carrier
is reused across all calls (warm start across ZMC rounds and across the leader's charges).

### Approximations (honest list)

* **A1 all-or-nothing lots.** A carrier serves a customer zone fully or not at all; lot size `d_iz` is 10-50% of
  `drops_per_vehicle_per_day`, proportional to the zone's parcels (population x parcels per capita x market share).
  The Cournot game is therefore lumpy.
* **A2 price-and-branch, not branch-and-price.** The integer step runs on generated columns only. LP value is a lower
  bound, and the largest observed oracle gap (integer value minus LP value) per game is recorded as `lp_gap_max`
  (up to about 20 USD on plans worth hundreds to thousands). Pricing calls (`rho=1`) use a 0.5% MIP gap and 4 s limit;
  best responses use gap 1e-7 and 20 s. "Exact NE" below means exact with respect to this oracle, certified by an
  independent fresh-pool oracle (elementary routes, empty pool) and bracketed by the LP bound (`max_regret_lp`).
* **A3 congestion exposure** `tau_iz = d_iz x 0.6 x shift / drops` is the in-zone time of the lot. The inter-zone driving is
  priced only through the p-box route loss (it creates no externality). Hours are proportional to deliveries, so within a
  zone a congestion charge on hours and a delivery charge are collinear instruments.
* **A4 linear congestion** (D1): cost `gamma tau (xi + c_z X_z)`; `xi` lives inside the p-box.
* **A5 oracle exactness at scale** is not proven; at the 40 tiny games it matches enumeration exactly.

### Calibration (conventions reused; **NEW** = assumption introduced here)

| item | rule |
|---|---|
| zones, travel times, depot score, lane-km | `data/processed/<city>` (all zones; Z = 42..593) |
| carriers N, fee, wage, fuel, drops, shift, van capacity, TomTom, BPR | `city_parameters_wide.csv` |
| market shares | Paris (La Poste 50%, Amazon 15%, Mondial Relay 14%) and Berlin (DHL 42%, Amazon 17.5%, 4 others 10%) from `city_parameters.csv`; **equal shares elsewhere** (no data) |
| depots | `geo.select_depot_sites` (depot score, min separation 3 km, seeded) |
| customer zones | **NEW** 22 per carrier, sampled with weight `pop x exp(-t/t40)` around the depot (gravity), so carriers overlap (overlap column of `E1_*.csv`: 34-93% of served zones are shared) |
| p-box, sectors, loss | as `real_instances.py` (9 k-means sectors, lognormal law with TomTom mean and peak, DKW alpha=0.05); **NEW** 30 observed days instead of 60 (speed); loss in USD: fixed `2 gamma_h`, `gamma_h` per hour, `3 gamma_h` per overtime hour, deadline = shift |
| vehicle-hour cost `gamma_h` | wage + fuel price x burn; **NEW** burn 3 L/h for vans, 1 L/h when van capacity <= 60 |
| inverse demand | `alpha = 1.5 fee`, `b = alpha/(2 Q_full)` (convention of `core.py`) |
| congestion slope `c_z` | BPR: `v0 = (cong/0.15)^(1/4)`, slope `0.15 x 4 x v0^3`; capacity `lane_km x 1000 veh/h / v_ff`; **NEW** PCE 1.5, operating hours = shift, and a *representative-slice* multiplicity `m_z` = real delivery vehicle-hours (population x parcels per capita x hours per drop) / modelled hours, so that the modelled slice feels the congestion of the full city |
| social cost | main.tex W: consumer surplus minus own congestion cost minus route losses (charges are transfers) |
| "broad" social cost (**proxy, NEW**) | adds background-traffic delay: pop x vehicles/1000 x 1 h/day x value of time (= wage) x slowdown / m_z |
| delivery fee unit | a "drop" is one parcel |

The slice's economics are in real units (USD, parcels); only the congestion coupling is scaled by `m_z`.


## 2. Tables of the verification runs

Verification (a), tiny games with exhaustive enumeration:

| method | instances | mean_calls | is_ne_enum | max_regret_fresh | hits_global | hits_best_ne | mean_excess_over_global |
|---|---|---|---|---|---|---|---|
| ZMC6 | 40 | 17.5 | 1 | 0 | 1 | 1 | 0 |
| BR | 40 | 4.85 | 1 | 0 | 0.875 | 0.875 | 0.932 |
| FW6 | 40 | 16.7 | 1 | 0 | 0.95 | 0.95 | 0.0671 |
| CG | 40 | 11.1 | 1 | 0 | 0.975 | 0.975 | 0.0203 |

Verification (c) and E5: calls and relative potential gap to the convexified CG optimum (22 customer zones):

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
## 3. Verification before scale

* **(a) Tiny games vs exhaustive enumeration** (40 games, N = 2-3, 3-4 customer zones, up to 4096 profiles; `results/verify_tiny.csv`):
  the integrated ZMC+BRL profile is a pure NE of the enumerated game in 40/40 cases, reaches the global potential
  minimum in 40/40, and has regret 0 under an independent fresh-pool oracle. For reference BR reaches the global minimum
  in 35/40, Frank-Wolfe+rounding in 38/40, column generation in 39/40 (table above). The instances are small, so this
  supports correctness more than it separates the methods.
* **(b) Exactness at city scale.** Every base profile of E1 (27 profiles) and the leader's best point in every city
  (`E2cert_*.csv`) has regret <= 2.3e-13 against the independent fresh-pool oracle. This needed a repair loop: the first
  pass found regrets of 0.2-7 USD (0.1% of profit) in Cairo, Moscow, New York and Paris because the pooled price-and-branch
  oracle missed integer plans that the fresh oracle found. The fresh oracle's columns are now injected into the pool and the
  profile re-polished (at most 3 times); all final profiles pass. A bug in the first version (a stale answer cache after the
  injection) caused part of the early failures. The LP-bound-certified regret (`max_regret_lp`, a valid upper bound on what an
  exact solver could gain) is 0.0-19 USD per carrier.
* **(c) Methods on all nine cities** (`summary_E5_calls_vs_Z.csv`, 22 customer zones, one seed). Calls and relative
  potential gap to the convexified column-generation optimum (see the table above): ZMC8 uses 36-65 calls (about 9-11 per
  carrier, flat in Z). Its gap equals FW8 and CG8 to three digits in 5 of 9 cities and is within 0.005 elsewhere. **BR needs only 8-17 calls and is as good in 5 cities (Cairo, Moscow, New York, Paris, Berlin; slightly better than ZMC in Berlin, 0.0232 against 0.0243); it is worse in New Delhi (gap 0.138 against 0.102), Mumbai (0.046 against 0.020), Buenos Aires (0.179 against 0.163) and London (0.20 against 0.18).** ZMC therefore shows no
  quality advantage on these games, in contrast to the synthetic Z = 250 instances of `theory/new_algorithm_A/results.md`. Reasons we can
  see: only 32-89 coordinates are active (customer zones), the games are mildly nonconvex, and carriers couple through few shared
  zones.

## 4. Results

### E1 unpriced Cournot-Nash equilibrium (3 seeds; sensitivity in the next two tables)

Base calibration; ZMC (8 rounds + polish); every profile exact w.r.t. the oracle. `served_share` = deliveries / customer demand,
`slowdown_pct` = added mean travel-time slowdown caused by delivery vehicles (X-weighted), welfare = main.tex W (USD/day of the slice),
`eta_rel` = certified potential gap (potential of the returned profile minus the best LP-certified dual bound, relative to |potential|).

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

Reading: carriers serve most customer demand in Cairo, Moscow, New York, Paris, Berlin (84-100%), and only 18-45% in London, New
Delhi, Buenos Aires and Mumbai, where fee per parcel is low against the vehicle-hour cost or the shift is short (London 7.3 h). Added slowdown is
0.8-4.6% except Moscow (18%), New York (7.8%), London (6.7%). Seed-to-seed served-share spread is at most 0.03, welfare spread (sd/mean) 2-18%. `eta_rel` is
below 1% in Cairo, Moscow, New York, 3.5-4.3% in Berlin and Paris, and 7-46% in the low-service cities, where the potential is close to zero and the
dual bound is loose; so a small certified potential gap holds only in the first group.

Sensitivity (low/high of the five weakest parameters from SOURCES.md; one seed; welfare change in % and served share in pp).
Fee, drops per vehicle and the number of carriers dominate; parcels per capita hardly matters because lot sizes are relative:

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

Served share (pp):

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

### E2 the city leader's charges

Grid: congestion multiplier theta in {0, .5, 1, 2, 4, 8, 16} x per-delivery charge `s/fee` in {-.6, -.4, -.2, -.1, 0, .1, .2, .4, .6}
(63 warm-started ZMC equilibria per city, `E2_<city>.csv`). `t_z = theta gc_z X_z^NE` per vehicle-hour. Configurations: none; congestion only
(`s = 0`); delivery only (`theta = 0`); both. Gain = reduction of the social cost relative to no charge, in percent of |SC|, best point on the grid
(the leader may choose no charge). Figures: `figures/E2_grid.png`, `figures/E2_instruments.png`.

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

Best point with both instruments (main objective):

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

**Answer (main objective).** One instrument is *almost* enough, and it is the per-delivery one, with a subsidy (`s < 0`, 10-40% of the
fee). Delivery-only captures 100% of the gain in Buenos Aires, 87% in London, 57% in New Delhi, 98% in Paris and 79% in Berlin; the congestion
charge alone gains less than 1.7% of |SC| anywhere. Adding the congestion charge on top helps where the unpriced equilibrium
under-delivers *and* congestion differs across zones (London 47.5 -> 54.6%, New Delhi 7.0 -> 12.2%, Mumbai 0.09 -> 2.0%), and is irrelevant where service is complete
(Cairo, Moscow, New York: best gain below 0.5%). Mechanism: the model has a fixed-cost/market-power under-provision (subsidy corrects it) and a small congestion externality (3-8% slowdown on carriers' own hours),
and the two instruments are collinear within a zone (A3), so the second one only adds spatial differentiation. The subsidy costs the city
(negative revenue, e.g. London -1,470 USD/day for a welfare gain of about 54% of 570); charges are transfers in the welfare definition, so this
fiscal cost is *not* in the social cost. Zone-level fairness: the best subsidy points have Gini of delivery access 0-0.61 (access still unequal in London,
Mumbai, New Delhi where only about half is served) against much lower price Gini (0.015-0.09); see `summary_E2.csv`.

With the **broad objective (a proxy: background-traffic delay)** the leader's best response in New Delhi, Mumbai and London is to *shut deliveries down*
(gain 100%, served share 0), and in Paris to cut service by 96% (Buenos Aires: by 37%). This is an artifact of the proxy: delay cost per delivery vehicle-hour exceeds the
carriers' surplus when the slice is scaled by `m_z`. We report it but do not draw policy conclusions from the broad objective.

Broad objective, gain (% of |SC|):

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

Best point (broad objective):

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

### E3 price of anarchy and stability

Social optimum = convexified optimum by column generation (to convergence, up to 40 iterations) plus derandomised rounding and coordinate polish
(`W_SO`, pure and feasible) with the relaxation value as an upper bound (`W_SO_bound`). NE set: ZMC, BR from empty, from full service, and from 3 random
price vectors (2-6 distinct equilibria per city), so PoA/PoS are *empirical* (worst/best equilibrium found), not exact. PoA = W_SO / W_NE (main objective;
all welfares are positive). `PoA_priced` uses the leader's best (theta, s) point.

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

**Answer.** Price of anarchy is 1.00-1.03 in the high-service cities (Moscow, New York, Paris, Berlin, Cairo) and large where service is partial:
London 1.57 (worst NE found 1.61), Buenos Aires 1.35, New Delhi 1.15, Mumbai 1.02 (1.11 worst). PoS is within 0.05 of PoA (the equilibria found differ little in welfare), so
the loss comes from the equilibrium concept, not from equilibrium selection. The leader's priced equilibrium is within 0-2.4% of the
rounded social optimum in every city (PoA_priced 1.00-1.02). The relaxation bound is 1-20% above the pure optimum (London 1,200 against 991), so the
true PoA could be larger than reported by that margin. Caveat: all of this is for the lumpy, all-or-nothing lots (A1).

### E4 imprecision

(i) **p-box width.** DKW confidence alpha in {2 (eps = 0), 0.5, 0.2, 0.05, 0.005, 1e-4}, eps = 0 to 0.41 with 30 observed days. Wider bands raise route loss
(BRL upper expectation) and cut service: at eps = 0.41, deliveries fall by 2% (Moscow, New York), 7-8% (Paris, Berlin), 23% (Mumbai), 55-56% (New Delhi, Buenos
Aires, London), and welfare by 10-70%. Cairo is unaffected in deliveries (-0%) with welfare -2.8%. Deliveries and vehicle-hours move together because hours are proportional to
deliveries, so the congestion effect equals the delivery effect (a limitation of A3). Existence/exactness: a pure equilibrium was found, converged, and passed the oracle regret check at every width
(max regret 0).
(ii) **Credal width via the Gamma-maximin surcharge** (`sur = delta M_k w_k`, w = unpriced equilibrium aggregate, delta in {0, .05, .1, .2, .4, .8}).
Deliveries and vehicle-hours fall monotonically in delta in eight of nine cities; Buenos Aires shows one non-monotone step (see the E4 file), which is a violation of the monotone comparative statics expected from Lemma 3.6 for a *single* equilibrium found by ZMC (the game has several equilibria, so the equilibrium reached can switch); at delta = 0.8 deliveries fall by 31% (Cairo) to 100%
(London, which stops) and welfare by 22-100%. The slowdown level falls with delivery volume (e.g. Moscow 17.6% -> 9.0%). Ambiguity acts like a tax and *reduces* congestion at the cost of welfare.

Widest p-box (eps = 0.41) vs eps = 0:

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

Widest surcharge (delta = 0.8) vs 0:

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

### E5 scaling

Table in Section 3(c) and `figures/E5_scaling.png`: ZMC calls per equilibrium are 36-65 (9-11 per carrier) for Z = 42 to 593, with no visible trend in Z; the
number of active coordinates is 32-89 because carriers serve 22 zones each. Z itself costs nothing beyond numpy vectors, but **the effective dimension is not Z**, so this does not test dimension independence
as hard as the synthetic E2 of `theory/new_algorithm_A`. Column generation to convergence needs 16-143 calls, BR 8-17.

### E6 theory-to-experiment checks (`E6_<city>.csv`, `figures/E6_checks.png`)

* **Clearing identity** `Phi(sigma) - G(lambda) = 1/2 ||M^-1 lambda - A||_M^2`: residual below 3.4e-12 in every round of every city (an algebraic identity, confirms the code).
* **Theorem 2 bound** `Phi(sigma^t) - Phi_bar* <= 1/2 ||e^t||_M^2` with Phi_bar* the CG restricted-master value: holds in 100% of rounds in 8 cities and 7/8 in Cairo (one violation,
  within the oracle's integrality gap: Phi_bar* from an inexact oracle is not a strict lower bound).
* **Brackets.** No coordinate bracket became inverted in any city (the cross-variation floor never produced contradictory signs). In bisection mode the normalised distance to the 14-round reference is
  4e-3 at T = 8 against the Corollary 7 bound 2^-4 = 0.0625, and 100% of coordinates are within the bound at T = 4 and T = 8. In secant mode the maximum relative bracket width after 8 rounds is 0.0435,
  the same in all cities, i.e. it follows pure halving on the *last* active coordinate.
  This check is weak (the bound is loose for bisection), it supports consistency, not tightness.
* **Certified gap (H6 of verification_plan.md).** `eta_rel < 1%` in 5 cities, 3.5-4.3% in Berlin and Paris, 7-46% in the low-service cities (E1 table). Hypothesis "below 1%" is *not* met in general.
* **Monotone comparative statics in delta (H7)**: hold in 8 of 9 cities for the Gamma-maximin sweep, one step violated in Buenos Aires (equilibrium selection); H1-H4, H8-H9 (credal certification, sub-fleets, credal-radius hypotheses) were not run: they need the RSRC
  certification of `main.tex`, which is not part of this integration.

## 5. Figures

`figures/eq_<city>.png` (zone price and added slowdown on the real zone rectangles, grey = no delivery; only the carriers' customer zones are active, 32-89 per city),
`figures/overview_equilibria.png` (price/fee, nine cities), `figures/overview_slowdown.png`, `figures/overview_summary.png` (service, slowdown, welfare, leader gains, PoA, calls),
`figures/E2_grid.png`, `figures/E2_instruments.png`, `figures/E3_poa.png`, `figures/E4_imprecision.png`, `figures/E5_scaling.png`, `figures/E6_checks.png`.

## 6. Limitations and what did not work

* **Proxy components.** All-or-nothing lots; sampled customer zones (22 per carrier, gravity around the depot) rather than whole-city demand; equal market shares in seven cities; hours proportional to deliveries
  (so congestion and deliveries cannot be separated); the representative-slice scaling `m_z`; the broad objective (background delay, value of time = wage, 1 h per vehicle-day, PCE 1.5) is a pure proxy and drives degenerate "shut down" optima.
* **Weak parameters.** Most inputs are flagged weak(C) in SOURCES.md (country-level parcel rates, wage, drops, van capacity, fee). Results move by tens of percent over their ranges (E1 sensitivity), the sign of "charge or
  subsidy" depends on the fee-to-cost ratio. Moscow's congestion is a 2020 value. Parcels per capita barely matters by construction.
* **Oracle is not exact.** Price-and-branch with a pooled column set; gaps up to about 20 USD; certified by LP bounds and an independent oracle, not by a proof. Cairo's MILPs are slowest (about 1 s per call, E2 for Cairo took 36 minutes).
* **ZMC has no measurable advantage here.** BR is cheaper and as good in most cities; the potential gap of ZMC, FW and CG coincide in most cities. The Z-independence claim cannot be stressed because only 32-89 coordinates are active.
* **Search is a grid.** The leader's optimum is a grid optimum (63 points); several optima sit at the grid edge in the broad objective; no continuous refinement.
* **PoA/PoS are empirical** (equilibria found from 5 starts); the social optimum is a rounded convexified optimum, not proven.
* **Reduced or skipped.** 30 observed days instead of 60; 22 customer zones as asked; E2-E4 use a single seed (E1 uses three); the credal/RSRC hypotheses H1-H4, H8, H9 were skipped; no full branch-and-price; Cairo E1, E2, E4 were re-run after the container restart.
  The first E1 pass had a stale-cache bug (fixed, those cities re-run). An earlier import error in `run_imprecision.py` (New Delhi) was fixed and re-run.
* The fiscal cost of subsidies is not part of the social cost (transfers), as in main.tex.

## 7. Reproduce

```
pip install numba
python -m pytest -q                                  # 59 tests
cd experiments
python run_verification.py tiny
for c in NewDelhi Cairo Moscow BuenosAires NewYork Bombay London Paris Berlin; do
  python run_equilibria.py $c --seeds 0 1 2          # E1, sensitivity, zone files
  ./run_city.sh $c                                   # verification (c), E6, E2/E3, E4
done
python summarize.py; python plot_equilibria.py; python plot_results.py
```
All scripts take `--seed` / `--ncust` where relevant (`run_equilibria.py --seeds`, `run_leader.py --seed`), default seed 0, 22 customer zones.
Run time: about 2-3 hours on 4 cores (Cairo dominates). Packages: numpy, scipy (HiGHS), pandas, matplotlib, numba.


## Appendix: E6 table

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

