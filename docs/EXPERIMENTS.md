# Game-theoretic experiments: ZMC with a BRL carrier oracle on nine city maps

> **Update 2026-10-24.** The files in `results/` and `figures/` now come from the **exact (branch-and-price) oracle**, see the section "Exact oracle re-run" (after "Branch-and-price for BRL").
> The tables and numbers of Sections 4 and 4a below were written for the price-and-branch run (kept in `results/pb_old/`, `figures/pb_old/`) and are not updated; where the two differ, the exact re-run is the one to quote.

All numbers come from the files in `results/` (CSV per experiment and city; `results/tables.md` holds every table of
this page in machine-generated form). Figures are in `figures/`. Seeds are fixed: E1, E2, E3 and E4 were run for seeds 0, 1 and 2 (seed s changes the depots, the
customer-zone sampling, the sector clustering and the 30 observed days; section 4a), E6 and the sensitivity runs use seed 0 only. Tables headed "seed 0" below are the first
run; the three-seed tables follow them and are the ones to quote. Everything here is a **model of a representative slice of each city**, calibrated from
`data/parameters/`; it is not a forecast.

## 1. What was built

| file | content |
|---|---|
| `src/ccu/brl.py` | numba port of the exact BRL pricer (functional dominance, ng-routes) of `theory/new_algorithm_B`; column generation + packing MILP (price-and-branch) over a persistent route pool. Tested against the prototype and against enumeration (`tests/test_brl.py`). |
| `src/ccu/zmc.py` | ZMC (bracketed secant on the zone clearing residual), restricted master, derandomised rounding, best-response polish, and the baselines BR, Frank-Wolfe+rounding, column generation, ported from `theory/new_algorithm_A`. |
| `src/ccu/zmc_brl.py` | the integration: `RoutingGame` (carrier oracle = BRL column generation at a common zone price vector, returns plan, p-box cost and contribution `x_i(p)` in R^{2Z}), city calibration `build_city_game`, tiny games and exhaustive enumeration, social-cost variant, metrics. |
| `tests/test_brl.py`, `tests/test_zmc_brl.py` | 17 tests (pricing = prototype; CG vs enumeration; ZMC equilibrium = exhaustive NE; independent-oracle regret = 0; clearing identity; city smoke test). 59 tests pass. |
| `experiments/` | `run_equilibria.py` (E1, sensitivity), `run_leader.py` (E2, E3), `run_imprecision.py` (E4), `run_verification.py` (verification, E5, E6), `run_city.sh`, `run_seeds.sh` + `run_job.sh` + `progress.py` (E2-E4 for further seeds, 4 parallel jobs, resumable), `summarize.py`, `plot_equilibria.py`, `plot_results.py`. |

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
* **A2 price-and-branch, not branch-and-price (superseded: the final results use branch-and-price, see "Exact oracle re-run").** The integer step runs on generated columns only. LP value is a lower
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

**E2 over three seeds (0, 1, 2).** The tables above are seed 0. Gain of the best charge vs no charge, percent of |SC|, mean (sd; min..max) over seeds (`summary_E2.csv` per seed, `summary_E2_by_seed.csv`, `summary_E2_agg.csv`):

| city | none | congestion_only | delivery_only | both |
|---|---|---|---|---|
| NewDelhi | 0 (0; 0..0) | 0 (0; 0..0) | 11 (5.2; 6.99..16.9) | 14.5 (2.6; 12.2..17.4) |
| Cairo | 0 (0; 0..0) | 0.107 (0.052; 0.0488..0.146) | 0.0352 (0.037; 0..0.0743) | 0.107 (0.052; 0.0488..0.146) |
| Moscow | 0 (0; 0..0) | 0.00414 (0.0072; 0..0.0124) | 0.204 (0.16; 0.0977..0.383) | 0.219 (0.15; 0.126..0.389) |
| BuenosAires | 0 (0; 0..0) | 1.25 (0.71; 0.428..1.67) | 33.4 (5.7; 28.6..39.7) | 33.4 (5.7; 28.6..39.7) |
| NewYork | 0 (0; 0..0) | 0.0458 (0.052; 0.00864..0.105) | 0.367 (0.095; 0.263..0.448) | 0.393 (0.1; 0.279..0.468) |
| Bombay | 0 (0; 0..0) | 0 (0; 0..0) | 1.97 (1.7; 0.0852..3.25) | 2.87 (0.74; 2.02..3.31) |
| London | 0 (0; 0..0) | 0.446 (0.77; 0..1.34) | 47.9 (17; 30.8..65.6) | 58.5 (26; 34.5..86.4) |
| Paris | 0 (0; 0..0) | 0.548 (0.25; 0.368..0.833) | 3.62 (1.3; 2.83..5.12) | 3.77 (1.2; 2.91..5.19) |
| Berlin | 0 (0; 0..0) | 0.0334 (0.057; 0..0.0997) | 1.6 (0.64; 1.08..2.31) | 1.73 (0.6; 1.37..2.43) |

Share of the two-instrument gain captured by the per-delivery instrument alone (`delivery_only / both`, seeds in order 0 / 1 / 2; meaningless where the gain is below 0.5%: Cairo, Moscow, New York):

| city | both_mean | both_min | both_max | share_by_seed | share_mean | share_sd | cong_only_max | best_s_by_seed |
|---|---|---|---|---|---|---|---|---|
| NewDelhi | 14.5 | 12.2 | 17.4 | 0.57 / 0.97 / 0.65 | 0.731 | 0.212 | 0 | -0.2 / -0.2 / -0.2 |
| Cairo | 0.107 | 0.0488 | 0.146 | 0.58 / 0.64 / 0.00 | 0.407 | 0.354 | 0.146 | 0.2 / 0.1 / -0.6 |
| Moscow | 0.219 | 0.126 | 0.389 | 0.78 / 0.91 / 0.99 | 0.893 | 0.106 | 0.0124 | -0.6 / -0.6 / -0.4 |
| BuenosAires | 33.4 | 28.6 | 39.7 | 1.00 / 1.00 / 1.00 | 1 | 0 | 1.67 | -0.4 / -0.2 / -0.4 |
| NewYork | 0.393 | 0.279 | 0.468 | 0.90 / 0.96 / 0.94 | 0.934 | 0.027 | 0.105 | -0.6 / -0.6 / -0.4 |
| Bombay | 2.87 | 2.02 | 3.31 | 0.04 / 0.98 / 0.79 | 0.605 | 0.497 | 0 | -0.1 / -0.2 / -0.2 |
| London | 58.5 | 34.5 | 86.4 | 0.87 / 0.89 / 0.76 | 0.841 | 0.0713 | 1.34 | -0.4 / -0.2 / -0.4 |
| Paris | 3.77 | 2.91 | 5.19 | 0.97 / 0.90 / 0.99 | 0.954 | 0.0453 | 0.833 | -0.4 / -0.4 / -0.6 |
| Berlin | 1.73 | 1.37 | 2.43 | 0.79 / 1.00 / 0.95 | 0.913 | 0.111 | 0.0997 | -0.4 / -0.2 / -0.2 |

Best point with both instruments, over seeds:

| city | n_seeds | theta_mean | theta_sd | theta_min | theta_max | s_over_fee_mean | s_over_fee_sd | s_over_fee_min | s_over_fee_max | gain_pct_of_abs_mean | gain_pct_of_abs_sd | gain_pct_of_abs_min | gain_pct_of_abs_max | served_share_mean | served_share_sd | served_share_min | served_share_max | revenue_mean | revenue_sd | revenue_min | revenue_max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Berlin | 3 | 5.5 | 4.33 | 0.5 | 8 | -0.267 | 0.115 | -0.4 | -0.2 | 1.73 | 0.598 | 1.37 | 2.43 | 0.941 | 0.0223 | 0.927 | 0.966 | -3.32e+03 | 1.72e+03 | -5.24e+03 | -1.92e+03 |
| Bombay | 3 | 4.67 | 3.06 | 2 | 8 | -0.2 | 0 | -0.2 | -0.2 | 2.87 | 0.735 | 2.02 | 3.31 | 0.559 | 0.0356 | 0.521 | 0.592 | -54.7 | 30 | -83.9 | -23.9 |
| BuenosAires | 3 | 0.5 | 0 | 0.5 | 0.5 | -0.333 | 0.115 | -0.4 | -0.2 | 33.4 | 5.74 | 28.6 | 39.7 | 0.74 | 0.0808 | 0.647 | 0.793 | -413 | 163 | -528 | -226 |
| Cairo | 3 | 6 | 3.46 | 2 | 8 | 0.2 | 0 | 0.2 | 0.2 | 0.107 | 0.0516 | 0.0488 | 0.146 | 1 | 0 | 1 | 1 | 263 | 20.8 | 240 | 279 |
| London | 3 | 9.33 | 6.11 | 4 | 16 | -0.4 | 0 | -0.4 | -0.4 | 58.5 | 26.2 | 34.5 | 86.4 | 0.496 | 0.0891 | 0.394 | 0.556 | -1.44e+03 | 625 | -2.06e+03 | -808 |
| Moscow | 3 | 1 | 0.866 | 0.5 | 2 | -0.3 | 0.173 | -0.4 | -0.1 | 0.219 | 0.147 | 0.126 | 0.389 | 0.999 | 0.00172 | 0.997 | 1 | -2.41e+03 | 1.45e+03 | -3.37e+03 | -747 |
| NewDelhi | 3 | 2.67 | 1.15 | 2 | 4 | -0.2 | 0 | -0.2 | -0.2 | 14.5 | 2.64 | 12.2 | 17.4 | 0.39 | 0.0277 | 0.362 | 0.417 | -54.7 | 8.14 | -63.9 | -48.2 |
| NewYork | 3 | 4 | 3.46 | 2 | 8 | -0.2 | 0.173 | -0.4 | -0.1 | 0.393 | 0.1 | 0.279 | 0.468 | 1 | 0 | 1 | 1 | -4.02e+03 | 3.52e+03 | -8.09e+03 | -1.89e+03 |
| Paris | 3 | 5.5 | 4.33 | 0.5 | 8 | -0.333 | 0.115 | -0.4 | -0.2 | 3.77 | 1.24 | 2.91 | 5.19 | 0.948 | 0.0507 | 0.891 | 0.988 | -2.71e+03 | 1.69e+03 | -4.16e+03 | -849 |

Equilibrium exactness over all 63 grid points of every seed (regret against the pooled oracle; against the independent fresh-pool oracle at the best point; every equilibrium converged):

| city | max_regret_grid | all_converged | max_regret_fresh_best_point |
|---|---|---|---|
| Berlin | 4.55e-13 | True | 4.55e-13 |
| Bombay | 1.42e-14 | True | 0 |
| BuenosAires | 2.84e-14 | True | 2.84e-14 |
| Cairo | 0 | True | 0 |
| London | 5.68e-14 | True | 2.27e-13 |
| Moscow | 0 | True | 0 |
| NewDelhi | 2.84e-14 | True | 2.84e-14 |
| NewYork | 0 | True | 0 |
| Paris | 2.27e-13 | True | 0 |

Figure `figures/E2_instruments.png` shows mean, sd bars and min/max ticks; `figures/E2_grid.png` the mean gain over the (theta, s) grid.

With the **broad objective (a proxy: background-traffic delay)** the leader's best response in New Delhi, Mumbai and London is to *shut deliveries down*
(gain 100%, served share 0), and in Paris to cut service by 96% (Buenos Aires: by 37%). This is an artifact of the proxy: delay cost per delivery vehicle-hour exceeds the
carriers' surplus when the slice is scaled by `m_z`. We report it but do not draw policy conclusions from the broad objective.

Broad objective, gain (% of |SC|), seed 0 (three-seed table in section 4a):

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

**E3 over three seeds** (`summary_E3.csv` per seed and city, `summary_E3_agg.csv`; mean (sd; min..max); the tables above are seed 0; priced_gap = (W_SO - W_priced)/W_SO in percent):

| city | PoA_zmc | PoS | PoA_worst_NE | PoA_priced | priced_gap_pct | max_regret_ne |
|---|---|---|---|---|---|---|
| NewDelhi | 1.18 (0.046; 1.15..1.23) | 1.17 (0.056; 1.12..1.23) | 1.2 (0.045; 1.15..1.24) | 1.03 (0.018; 1.02..1.05) | 2.95 (1.7; 1.58..4.86) | 0 |
| Cairo | 1 (0.00052; 1..1) | 1 (0.00023; 1..1) | 1 (0.00052; 1..1) | 1 (7.6e-05; 1..1) | -0.00122 (0.0076; -0.0094..0.00574) | 0 |
| Moscow | 1 (0.0014; 1..1) | 1 (0.0015; 1..1) | 1 (0.0014; 1..1) | 1 (6.4e-05; 1..1) | 0.00487 (0.0064; 0..0.0122) | 0 |
| BuenosAires | 1.36 (0.055; 1.31..1.42) | 1.33 (0.07; 1.27..1.41) | 1.4 (0.12; 1.31..1.54) | 1.02 (0.0055; 1.01..1.02) | 1.78 (0.53; 1.31..2.36) | 0 |
| NewYork | 1 (0.001; 1..1) | 1 (0.001; 1..1) | 1 (0.001; 1..1) | 1 (0; 1..1) | 0 (0; 0..0) | 4.55e-13 |
| Bombay | 1.03 (0.0076; 1.02..1.04) | 1.03 (0.0076; 1.02..1.04) | 1.08 (0.033; 1.04..1.11) | 1 (0.00032; 1..1) | 0.356 (0.031; 0.333..0.392) | 0 |
| London | 1.66 (0.26; 1.45..1.94) | 1.63 (0.28; 1.42..1.94) | 1.75 (0.2; 1.61..1.98) | 1.05 (0.033; 1.01..1.08) | 4.33 (3; 1.42..7.43) | 2.84e-14 |
| Paris | 1.04 (0.013; 1.03..1.05) | 1.03 (0.018; 1.02..1.05) | 1.04 (0.013; 1.03..1.05) | 1 (0.00083; 1..1) | 0.165 (0.082; 0.0721..0.23) | 0 |
| Berlin | 1.02 (0.0071; 1.01..1.03) | 1.02 (0.0027; 1.01..1.02) | 1.02 (0.0057; 1.02..1.03) | 1 (0.0014; 1..1) | 0.197 (0.14; 0.0476..0.313) | 0 |

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

**E4 over three seeds** (`summary_E4.csv`, `summary_E4_agg.csv`, `summary_E4_monotone.csv`; the tables above are seed 0). Widest p-box vs eps = 0, mean (sd; min..max):

| city | width | served_share | d_deliveries_pct | d_welfare_pct |
|---|---|---|---|---|
| NewDelhi | 0.406 | 0.206 (0.027; 0.191..0.238) | -53.5 (4.3; -57.2..-48.7) | -60.1 (2.4; -62..-57.4) |
| Cairo | 0.406 | 1 (0; 1..1) | 0 (0; 0..0) | -2.75 (0.042; -2.8..-2.71) |
| Moscow | 0.406 | 0.986 (0.0057; 0.979..0.99) | -1.35 (0.63; -2.07..-0.951) | -10.5 (0.61; -11.1..-9.84) |
| BuenosAires | 0.406 | 0.297 (0.045; 0.258..0.346) | -53 (6.5; -57.2..-45.5) | -53 (7.3; -57.3..-44.6) |
| NewYork | 0.406 | 0.974 (0.0048; 0.97..0.979) | -2.62 (0.48; -2.98..-2.08) | -10.8 (0.43; -11.1..-10.3) |
| Bombay | 0.406 | 0.402 (0.02; 0.379..0.416) | -28.8 (7.3; -36.9..-22.8) | -30.8 (1.4; -31.9..-29.2) |
| London | 0.406 | 0.118 (0.039; 0.074..0.147) | -63.4 (13; -78.2..-55.7) | -73.9 (7.4; -82.4..-69.6) |
| Paris | 0.406 | 0.836 (0.028; 0.818..0.868) | -9.16 (3.1; -12.7..-6.94) | -17 (1.2; -18.1..-15.8) |
| Berlin | 0.406 | 0.861 (0.012; 0.852..0.874) | -7.47 (1.4; -8.7..-6.02) | -17.3 (0.94; -18.1..-16.2) |

Widest surcharge vs delta = 0:

| city | width | served_share | d_deliveries_pct | d_welfare_pct |
|---|---|---|---|---|
| NewDelhi | 0.8 | 0.0983 (0.036; 0.0609..0.132) | -62.2 (13; -75.5..-49.1) | -51.2 (13; -65.2..-38.7) |
| Cairo | 0.8 | 0.682 (0.0071; 0.675..0.689) | -31.8 (0.71; -32.5..-31.1) | -23.1 (0.73; -23.8..-22.3) |
| Moscow | 0.8 | 0.367 (0.036; 0.326..0.388) | -63 (3.7; -67.2..-60.7) | -54.4 (5; -60.1..-51) |
| BuenosAires | 0.8 | 0.126 (0.007; 0.121..0.134) | -65.6 (2; -67.9..-64.1) | -54.8 (2.8; -57.9..-52.4) |
| NewYork | 0.8 | 0.359 (0.067; 0.295..0.429) | -63.7 (6.9; -70.2..-56.5) | -55.1 (7.5; -62.2..-47.3) |
| Bombay | 0.8 | 0.183 (0.02; 0.165..0.205) | -59.3 (3.2; -61.7..-55.6) | -44.9 (3.9; -48.3..-40.7) |
| London | 0.8 | 0.0177 (0.015; 0..0.0276) | -89.5 (9.5; -100..-81.4) | -86.5 (12; -100..-75.6) |
| Paris | 0.8 | 0.236 (0.049; 0.183..0.281) | -72.1 (5.7; -77.7..-66.3) | -61.1 (7.4; -68.2..-53.5) |
| Berlin | 0.8 | 0.255 (0.011; 0.248..0.268) | -71.4 (0.98; -72..-70.3) | -59.8 (1.2; -60.7..-58.4) |

Exactness over all seeds and widths (all equilibria converged; max regret against the oracle):

| city | all_converged | max_regret |
|---|---|---|
| Berlin | True | 2.27e-13 |
| Bombay | True | 7.11e-15 |
| BuenosAires | True | 2.84e-14 |
| Cairo | True | 0 |
| London | True | 0 |
| Moscow | True | 5.68e-14 |
| NewDelhi | True | 0 |
| NewYork | True | 0 |
| Paris | True | 5.68e-14 |

Number of seeds in which deliveries fall monotonically with the width (a 1-delivery rise counts as non-monotone):

| city | gamma | pbox |
|---|---|---|
| Berlin | 3/3 | 3/3 |
| Bombay | 3/3 | 2/3 |
| BuenosAires | 1/3 | 2/3 |
| Cairo | 3/3 | 3/3 |
| London | 3/3 | 3/3 |
| Moscow | 3/3 | 1/3 |
| NewDelhi | 3/3 | 3/3 |
| NewYork | 3/3 | 3/3 |
| Paris | 2/3 | 1/3 |

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
* **Monotone comparative statics in delta (H7)**: hold in 8 of 9 cities for the Gamma-maximin sweep in seed 0, one step violated in Buenos Aires (equilibrium selection); over three seeds 7 cities are monotone in all seeds, Buenos Aires in 1 of 3 and Paris in 2 of 3 (section 4a); H1-H4, H8-H9 (credal certification, sub-fleets, credal-radius hypotheses) were not run: they need the RSRC
  certification of `main.tex`, which is not part of this integration.

## 4a. Robustness to the seed (E2, E3, E4 on seeds 0, 1, 2)

Seed s re-draws depots, the 22 customer zones per carrier, the k-means sectors and the 30 observed days (so also the DKW p-boxes); the calibration inputs are unchanged. Seed 0 is the
run reported first; seeds 1 and 2 were added with `experiments/run_seeds.sh`. Three seeds give an sd with two degrees of freedom: treat sd and min/max as a rough
indication of the spread, not as a confidence interval.

Headline per city, mean +- sd over three seeds (`summary_headline.csv`):

| city | seeds | gain_cong_only | gain_delivery_only | gain_both | share_delivery | PoA | PoA_worst | PoS | priced_gap_pct | pbox_d_deliv_pct | pbox_d_welfare_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NewDelhi | 3 | 0 +- 0 | 11 +- 5.2 | 14.5 +- 2.6 | 0.731 +- 0.21 | 1.18 +- 0.046 | 1.2 +- 0.045 | 1.17 +- 0.056 | 2.95 +- 1.7 | -53.5 +- 4.3 | -60.1 +- 2.4 |
| Cairo | 3 | 0.107 +- 0.052 | 0.0352 +- 0.037 | 0.107 +- 0.052 | 0.407 +- 0.35 | 1 +- 0.00052 | 1 +- 0.00052 | 1 +- 0.00023 | -0.00122 +- 0.0076 | 0 +- 0 | -2.75 +- 0.042 |
| Moscow | 3 | 0.00414 +- 0.0072 | 0.204 +- 0.16 | 0.219 +- 0.15 | 0.893 +- 0.11 | 1 +- 0.0014 | 1 +- 0.0014 | 1 +- 0.0015 | 0.00487 +- 0.0064 | -1.35 +- 0.63 | -10.5 +- 0.61 |
| BuenosAires | 3 | 1.25 +- 0.71 | 33.4 +- 5.7 | 33.4 +- 5.7 | 1 +- 0 | 1.36 +- 0.055 | 1.4 +- 0.12 | 1.33 +- 0.07 | 1.78 +- 0.53 | -53 +- 6.5 | -53 +- 7.3 |
| NewYork | 3 | 0.0458 +- 0.052 | 0.367 +- 0.095 | 0.393 +- 0.1 | 0.934 +- 0.027 | 1 +- 0.001 | 1 +- 0.001 | 1 +- 0.001 | 0 +- 0 | -2.62 +- 0.48 | -10.8 +- 0.43 |
| Bombay | 3 | 0 +- 0 | 1.97 +- 1.7 | 2.87 +- 0.74 | 0.605 +- 0.5 | 1.03 +- 0.0076 | 1.08 +- 0.033 | 1.03 +- 0.0076 | 0.356 +- 0.031 | -28.8 +- 7.3 | -30.8 +- 1.4 |
| London | 3 | 0.446 +- 0.77 | 47.9 +- 17 | 58.5 +- 26 | 0.841 +- 0.071 | 1.66 +- 0.26 | 1.75 +- 0.2 | 1.63 +- 0.28 | 4.33 +- 3 | -63.4 +- 13 | -73.9 +- 7.4 |
| Paris | 3 | 0.548 +- 0.25 | 3.62 +- 1.3 | 3.77 +- 1.2 | 0.954 +- 0.045 | 1.04 +- 0.013 | 1.04 +- 0.013 | 1.03 +- 0.018 | 0.165 +- 0.082 | -9.16 +- 3.1 | -17 +- 1.2 |
| Berlin | 3 | 0.0334 +- 0.057 | 1.6 +- 0.64 | 1.73 +- 0.6 | 0.913 +- 0.11 | 1.02 +- 0.0071 | 1.02 +- 0.0057 | 1.02 +- 0.0027 | 0.197 +- 0.14 | -7.47 +- 1.4 | -17.3 +- 0.94 |

Conclusion by seed (`summary_conclusions.csv`):

| city | C1_delivery_alone_ge_half_by_seed | C1_flips | C2_congestion_only_max_pct | C2_holds_lt_1p7 | C3_PoA_zmc_by_seed | C3_PoA_worstNE_by_seed | C3_large_ge_1p10_seeds | C3_worstNE_ge_1p10_seeds |
|---|---|---|---|---|---|---|---|---|
| NewDelhi | yes / yes / yes | 0 | 0 | True | 1.15 / 1.23 / 1.16 | 1.15 / 1.24 / 1.20 | 3 | 3 |
| Cairo | n/a / n/a / n/a | 0 | 0.146 | True | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0 | 0 |
| Moscow | n/a / n/a / n/a | 0 | 0.0124 | True | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0 | 0 |
| BuenosAires | yes / yes / yes | 0 | 1.67 | True | 1.35 / 1.42 / 1.31 | 1.35 / 1.54 / 1.31 | 3 | 3 |
| NewYork | n/a / n/a / n/a | 0 | 0.105 | True | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 0 | 0 |
| Bombay | NO / yes / yes | 1 | 0 | True | 1.02 / 1.04 / 1.04 | 1.11 / 1.08 / 1.04 | 0 | 1 |
| London | yes / yes / yes | 0 | 1.34 | True | 1.57 / 1.45 / 1.94 | 1.61 / 1.67 / 1.98 | 3 | 3 |
| Paris | yes / yes / yes | 0 | 0.833 | True | 1.03 / 1.03 / 1.05 | 1.03 / 1.03 / 1.05 | 0 | 0 |
| Berlin | yes / yes / yes | 0 | 0.0997 | True | 1.01 / 1.02 / 1.03 | 1.02 / 1.02 / 1.03 | 0 | 0 |

**Seed robustness of the conclusions of section 4.**

* *"One instrument captures most of the gain" (the per-delivery subsidy).* Holds in every city and seed where the leader's gain is material (at least 0.5% of |SC|):
  New Delhi (delivery-only share 0.57 / 0.97 / 0.65), Buenos Aires (1.00 in all seeds), London (0.87 / 0.89 / 0.76), Paris, Berlin (0.79-1.00). Cairo, Moscow, New York have gains below 0.5% in all seeds, so the share is not informative there.
  **Mumbai is the one case that flips with the seed.** In seed 0 the subsidy alone gives 0.09% against 2.0% with both instruments (share 0.04); in seeds 1 and 2 it is 98% and 79%. The earlier statement
  that adding the congestion charge helps in Mumbai (0.09 -> 2.0%) was a seed-0 result, and the three-seed answer for Mumbai is "mostly one instrument, but not reliably". The best per-delivery point is a subsidy (s < 0)
  in every seed where the gain is material; in Cairo (gain 0.05-0.15%) its sign changes with the seed. The earlier reading of the size of the second instrument's contribution
  in New Delhi (7.0 -> 12.2%) and London (47.5 -> 54.6%) also moves: New Delhi delivery-only 7.0-16.9%, both 12.2-17.4%; London delivery-only 30.8-65.6%, both 34.5-86.4%.
* *Congestion charge alone gains less than 1.7% of |SC|.* Holds in all 27 city-seed cases, but without much margin: the maximum is 1.67% (Buenos Aires, seed 0), then London 1.34% (seed 0); in Buenos Aires the three values are 0.43-1.67%.
  Seed 0 happened to be the largest in both cities, so the bound is a sample maximum and a fourth seed could exceed 1.7%.
* *PoA large only where service is partial (London, Buenos Aires, New Delhi).* Holds in every seed. PoA of the ZMC equilibrium: London 1.57 / 1.45 / 1.94, Buenos Aires 1.35 / 1.42 / 1.31, New Delhi 1.15 / 1.23 / 1.16; the other six cities are at most 1.05
  in every seed (Paris 1.05 in seed 2). The ordering London > Buenos Aires > New Delhi holds in each seed. Mumbai is borderline only for the *worst* equilibrium found (1.11 / 1.08 / 1.04), and the size of London's PoA (1.45-1.94) is not pinned down.
* *Priced equilibrium within 0-2.4% of the optimum* does **not** survive as stated. Over seeds the gap is at most 0.4% in six cities, but London reaches 7.4% (seed 1; PoA_priced 1.08) and New Delhi 4.9% (seed 1), Buenos Aires 2.4%. The leader's grid
  point is still far better than no charge (PoA 1.45-1.94 -> 1.01-1.08 in London), but "within 2.4% everywhere" has to be replaced by "within 7.4% everywhere, within 0.4% in six cities".
* *PoS within 0.05 of PoA, so the loss comes from the equilibrium concept and not from selection.* Mostly true (worst-NE PoA minus PoS is at most 0.05 in 23 of 27 games), but not in every seed: London seed 1 has PoS 1.42 against worst-NE 1.67 (seed 0: 1.52 against 1.61), Buenos Aires seed 1 1.41 against 1.54,
  Mumbai seed 0 1.02 against 1.11. In those games the equilibrium that is selected matters.
* *E4 (imprecision).* The grouping of cities holds in every seed: Cairo does not lose deliveries at the widest p-box (-2.75% welfare), Moscow and New York lose 1-3% of deliveries, Paris and Berlin 6-13%, Mumbai 23-37%, and New Delhi, Buenos Aires and London 45-78%; welfare loss 3-82%.
  The magnitudes in the three low-service cities vary a lot (London deliveries -55.7 / -56.2 / -78.2% in seeds 0 / 1 / 2). Deliveries are not always monotone in the width: 9 of 54 (city, seed, sweep) series have at least one rise,
  mostly of 1-4 deliveries, but also Paris p-box (28 and 31 deliveries, seeds 0 and 1), Moscow seed 2 p-box (17) and Buenos Aires (p-box seed 0, 20; Gamma seed 1, 65 deliveries, 33% -> 23% -> 33% across delta). So the monotone-in-delta property
  found in eight of nine cities for seed 0 holds in all three seeds for seven cities (Buenos Aires 1/3, Paris 2/3 seeds); it is a property of the single equilibrium reached, not of the game.
  Existence/exactness holds: every equilibrium of every seed converged, max regret 4.6e-13.
* *Broad objective (proxy).* Shutting deliveries down is the best response in New Delhi, Mumbai and London in all three seeds, and cuts service by 98-100% in Paris in all three; this is the artifact of the proxy discussed above. Buenos Aires is not robust (gain 55.4% in seed 0, 5.4% in seed 1, 0% in seed 2:
  the best point is "no charge"), and the smaller gains in Berlin, Cairo, Moscow (2-8%) move by a factor of about two between seeds.

**Which conclusions changed.** One flip (Mumbai, one instrument is enough: true in 2 of 3 seeds), one claim that no longer holds as written (priced equilibrium within 2.4% of the optimum), one weakened (PoS ~ PoA; monotone comparative statics in delta), and
the ranges around every magnitude (London's leader gain 34-86%, PoA 1.45-1.94). No qualitative conclusion about *which* cities have a large gain or a large PoA changed.

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
* **Seeds.** Seed variation covers the sampled slice of the city (depots, customer zones, observed days); it does not vary calibration inputs, so the spread understates total uncertainty.
* **Search is a grid.** The leader's optimum is a grid optimum (63 points); several optima sit at the grid edge in the broad objective; no continuous refinement.
* **PoA/PoS are empirical** (equilibria found from 5 starts); the social optimum is a rounded convexified optimum, not proven.
* **Reduced or skipped.** 30 observed days instead of 60; 22 customer zones as asked; E1-E4 use three seeds (the sd of three values is a rough guide; E5, E6, sensitivity and verification use one); the credal/RSRC hypotheses H1-H4, H8, H9 were skipped; no full branch-and-price (added later, see the last sections); Cairo E1, E2, E4 were re-run after the container restart.
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
Seeds 1 and 2 of E2, E3, E4 (about 30 minutes on 4 cores; resumable; status in `results/PROGRESS.md`, logs in `results/logs/`):
```
nohup experiments/run_seeds.sh > results/logs/run_seeds.out 2>&1 &     # 4 parallel jobs, Cairo first; rerun the same line after a restart
python experiments/summarize.py && python experiments/plot_results.py
# one job by hand: python experiments/run_leader.py London --seed 1 ; python experiments/run_imprecision.py London --seed 1
```
Result files: seed 0 `results/E2_<city>.csv`, seed s > 0 `results/E2_<city>_s<s>.csv` (same for `E2best`, `E2cert`, `E3`, `E4`); files are written atomically, finished files are skipped.
All scripts take `--seed` / `--ncust` where relevant (`run_equilibria.py --seeds`, `run_leader.py --seed`), default seed 0, 22 customer zones.
Run time: about 2-3 hours on 4 cores for the first seed (Cairo dominates), about 30 minutes wall-clock for the 36 E2/E3/E4 jobs of seeds 1 and 2. Packages: numpy, scipy (HiGHS), pandas, matplotlib, numba.


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



## Branch-and-price for BRL

Date: 2026-10-24. Code: `src/ccu/bp.py` (plus an arc mask and a fleet-size shift in `brl.espprc`), tests `tests/test_bp.py`, driver `experiments/run_bp.py`, results `results/bp_*.csv|json`, `results/summary_bp*.csv`, figure `figures/bp_gap.png`, progress and resume notes `results/PROGRESS_bp.md`.

**Why.** The BRL pricer is exact, but the integer step of Section 2 and of `theory/new_algorithm_B` is price-and-branch: column generation at the root, then an integer program over the generated columns. That plan can be worse than a heuristic optimised on the observed days (London, Paris and Berlin, 0.1-1.3%). `ccu.bp` makes the integer step exact.

**Method.**
* Master: set partitioning (metro study: every customer once) or prize-collecting set packing (game oracle), with a global column pool shared by all nodes; a column is usable at a node if all its arcs are allowed there.
* Node LP: column generation with the exact BRL labelling pricer, with the arc restrictions of the node and a return-time bound recomputed on the allowed arcs. Dominance is unchanged and stays valid, because the restrictions are local to the current node.
* Branching on the aggregated arc flow `f_ij` (including depot arcs). `f_ij = 0` deletes the arc. `f_ij = 1` deletes the other arcs leaving i and entering j and turns the row of i (or j if i is the depot) into an equality. The pricing problem does not change. Integral arc flows imply an integral plan, so no other branching is needed.
* Fleet size: with every customer served the number of routes is at least `ceil(total demand / capacity)`. This row is added at the root (partition mode), and a fractional number of routes is branched on (`sum x <= floor` / `>= ceil`) before any arc. The dual of this row is a constant added to every route's reduced cost (`fixed_shift`).
* ng-routes: a non-elementary column in an LP solution triggers an enlargement of the ng-sets along the cycle and the removal of the columns that became infeasible. Earlier bounds stay valid, since the relaxation only gets tighter.
* Bounds: node LP value, and during column generation the Lagrangian bound `z + n_max * min(0, min reduced cost)` for early pruning and for a bound that is valid at every moment. A bound is flagged invalid if a pricing call hit the label limit. Infeasible nodes are handled by big-M artificial columns, which only relax, so the bound stays valid.
* Upper bounds: integral nodes, and a restricted master MILP over the generated elementary columns at the root and every 8 nodes, with reduced-cost fixing from the root duals. No heuristic plan is used as warm start.
* Node selection: best bound. Stops at relative gap 1e-6 (`gap_tol`), a time limit or a node limit. The result carries the status `optimal`, `time_limit`, `node_limit` or `label_overflow`, the incumbent, the global bound and the remaining gap.
* Bound semantics: ng-routes are a relaxation of elementary routes, so the bound is valid for the elementary problem. The reported value is always the cost of a feasible elementary plan.

**Verification** (`python experiments/run_bp.py verify`, `results/bp_verify.csv`, `results/summary_bp_verify.csv`, plus `tests/test_bp.py`). 400 random Euclidean instances (n = 7-10, capacity 2-5, deadline fraction 0.3-1.2, ng-size 3-5, K = 4 sectors, DKW p-boxes from 40 samples), each solved as partition and as packing with random prizes and costs, against complete enumeration of all routes and an integer program over all customer subsets. Branch-and-price equals the enumerated optimum and its bound is below it in 800 of 800 cases (also in an earlier scratch run of 740 cases before the fleet-size rows were added). Price-and-branch (integer program over the root columns) is strictly suboptimal in 39 of the 800 (18 packing, 21 partition), by up to 7.3%. Mean 10.7 nodes, maximum 479.

**Nine metro instances** (`run_bp.py metro`, same `real_instances.build` calibration and seed 0, 22 customer zones, 60 observed days, L = 51, ng-size 8, partition, 1800 s limit, one core each, two jobs in parallel). Values are the p-box (robust) loss in driver-hours.

| City | root LP | root LP after ng enlargement | P&B (root columns, partition) | P&B (published pipeline) | B&P value | B&P bound | gap | nodes | time (s) | root CG (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| Berlin | 51.8535 | 51.8613 | 52.7448 | 52.6658 | 52.0639 | 52.0639 | 0 | 3 | 6 | 4.4 |
| Mumbai | 53.8151 | 53.8151 | 53.9076 | 54.0807 | 53.9076 | 53.9076 | 0 | 177 | 4 | 0.2 |
| Buenos Aires | 47.2921 | 47.2921 | 50.4628 | 48.3708 | 48.1287 | 48.1287 | 0 | 1659 | 166 | 2.8 |
| Cairo | 40.3903 | 40.3903 | 40.4195 | 40.4195 | 40.4195 | 40.4195 | 0 | 215 | 5 | 0.3 |
| London | 51.0386 | 51.0386 | 52.2712 | 52.0349 | 51.3767 | 51.3767 | 0 | 59 | 21 | 3.0 |
| Moscow* | 42.0093 | 42.0093 | 44.1063 | 43.6458 | 43.1669 | 43.1669 | 0 | 7487 | 1063 | 2.2 |
| New Delhi | 63.0258 | 63.0258 | 64.3730 | 63.1835 | 63.1835 | 63.1835 | 0 | 65 | 2 | 0.2 |
| New York | 46.0988 | 46.0988 | 46.0988 | 46.0988 | 46.0988 | 46.0988 | 0 | 1 | 8 | 8.2 |
| Paris | 37.7317 | 37.8402 | 38.2524 | 38.3170 | 38.2454 | 38.2454 | 0 | 4305 | 715 | 5.6 |

(*) Moscow congestion imputed. "P&B (published pipeline)" is the covering integer program with repair of `results.md` (`theory/new_algorithm_B/results_E.json`); "P&B (root columns, partition)" is the integer program over the columns that the root column generation of this implementation produced, with equality rows. The two are different heuristics, so neither dominates. All nine instances were solved to proven optimality (gap 0 up to 1e-6 relative). The total is 1989 s of one core. Moscow, Paris and Buenos Aires carry 98% of it.

Against the heuristics (all plans evaluated with the p-box worst case; "true" = the calibrated law, 20,000 draws):

| City | heur p-box | heur SAA | heur Wass. | B&P | B&P vs SAA (p-box) | SAA plan, true law | B&P plan, true law | B&P vs SAA (true) |
|---|---|---|---|---|---|---|---|---|
| Berlin | 52.7746 | 52.5479 | 52.9401 | 52.0639 | -0.92% | 38.746 | 41.369 | +6.77% |
| Mumbai | 54.0807 | 54.0807 | 54.0807 | 53.9076 | -0.32% | 48.039 | 47.890 | -0.31% |
| Buenos Aires | 49.3008 | 49.4526 | 49.4715 | 48.1287 | -2.68% | 34.770 | 37.216 | +7.03% |
| Cairo | 40.4195 | 40.4195 | 40.4335 | 40.4195 | 0 | 36.583 | 36.583 | 0 |
| London | 52.0349 | 51.3767 | 52.4455 | 51.3767 | 0 | 35.525 | 35.525 | 0 |
| Moscow* | 43.6458 | 43.7389 | 43.7389 | 43.1669 | -1.31% | 33.250 | 33.059 | -0.57% |
| New Delhi | 63.1835 | 63.1835 | 63.1836 | 63.1835 | 0 | 47.602 | 47.602 | 0 |
| New York | 51.2296 | 51.7054 | 51.2296 | 46.0988 | -10.84% | 34.443 | 36.089 | +4.78% |
| Paris | 38.3170 | 38.2855 | 38.7425 | 38.2454 | -0.10% | 31.661 | 31.653 | -0.03% |

Reading:
* The gap to the heuristics is closed and reversed. The SAA plan in London is in fact optimal for the robust objective (the exact method finds a plan with the same value, 51.3767, so the earlier 1.3% deficit came from price-and-branch, not from the model). In Berlin and Paris the exact plan is strictly better than the SAA plan (-0.92%, -0.10%). In Mumbai, Moscow and Buenos Aires it improves on the best heuristic by 0.32%, 1.10% and 2.38%. In New York it is the same proven optimum as before. In Cairo and New Delhi the best heuristic was already optimal.
* Under the calibrated true law the robust optimum is not better: it is 6.8% (Berlin), 7.0% (Buenos Aires) and 4.8% (New York) worse than the SAA plan and equal or slightly better elsewhere. This is the model conservatism of `results.md` (the p-box criterion is not the expected cost), not an algorithmic effect. A plan that is optimal for the robust criterion should not be read as the best plan under the true law.
* The published LP bounds are reproduced (e.g. London 51.039, Paris 37.732); the fleet-size row does not move them when the root solution already uses at least `ceil(demand/capacity)` routes, and it lifts Cairo from 38.811 to 40.390.
* Elementary cross-check (`--ng 22 --tag _ng22`, `results/bp_metro_<city>_ng22.json`): New Delhi, Cairo and Mumbai give the same optimum with elementary routes. For Berlin and London the elementary labelling hit the 200,000-label limit, so the run is not a certificate (status `label_overflow`), but the values (52.0639 and 51.3767) agree with the ng-8 optimum.

**What did not work first, honestly.** The first version had arc branching only. It solved London (91 s), Buenos Aires (930 s), Paris (1509 s), Berlin (57 s) and New York (10 s), but Cairo hit the 1800 s limit with value 40.6548 (worse than the heuristic 40.4195), bound 39.0129 and 4% gap after 1448 nodes. The reason is the fleet size: Cairo has demand 247 and capacity 40, so at least 7 routes are needed, while the LP uses 6.28 vehicles; each fractional vehicle saves a fixed cost and the arc branching had to repair this one arc at a time. Adding the fleet row and branching on the number of routes solved Cairo in 5 s (215 nodes) and reduced London from 91 s to 21 s, Buenos Aires from 930 s to 166 s, Paris from 1509 s to 715 s. The first-version JSON files are kept in `results/bp_v1/` (Bombay was stopped after 18 minutes, Moscow and New Delhi were not run with it). The table above is from the final version only.

Limits that remain: (i) the 22-zone instances are small, since capacity admits only 3-6 customers per route; larger instances would likely need cuts (subset-row, rounded capacity) and are untested; (ii) Moscow and Paris need 4,300-7,500 nodes (12-18 min); the BRL pricing takes about 64% of the time and the rest is the master LPs and python bookkeeping over up to 17,000 columns; (iii) the bound is for ng-routes with enlargement, so an optimality claim for the elementary problem relies on the enlargement (cycles are removed whenever they appear in a node solution, and the final plans are elementary and feasible); (iv) a pricing call that hits the label limit invalidates the bound (`bound_valid`); this did not happen with ng-size 8 (at most 11,159 labels kept, Berlin) but did with ng-size 22.

**Integrated game with the exact integer step** (`run_bp.py game London Paris Berlin --tl 20`, base instances seed 0, 22 customer zones, same `solve_ne(..., certify="fresh")` as E1; `RoutingGame.bp_time` switches the oracle to branch-and-price; per-call limit 20 s; pricing calls use the 5e-3 relative gap of the old pipeline, best responses 1e-8; `results/bp_game_<city>.csv`, `results/summary_bp_game.csv`). The old equilibrium was recomputed with price-and-branch (it reproduces `results/E1_<city>.csv`) and then tested with the exact oracle.

| City | welfare, exact (price-and-branch) | served share | oracle calls (B&P calls, optimal) | time, exact (P&B) | regret of the P&B equilibrium under the exact oracle | regret of the new equilibrium |
|---|---|---|---|---|---|---|
| London | 631.778 (631.778) | 0.1989 (0.1989) | 49 (55, 55) | 3 s (1 s) | 0 | 0 |
| Paris | 5718.17 (5706.43) | 0.8869 (0.8801) | 50 (56, 54; 56 with a 120 s limit) | 84 s (9 s) | 0.78, 1.61, 2.04 USD (carriers 3, 4, 5) | 0 |
| Berlin | 8401.35 (8446.19) | 0.8767 (0.8841) | 59 (69, 69) | 42 s (13 s) | 3.54 USD (carrier 2) | 0 |

* London: unchanged (welfare differs by 1e-4). The previous equilibrium is also exact.
* Paris and Berlin: the price-and-branch equilibrium is not an exact equilibrium. In Paris three carriers and in Berlin one carrier can gain 0.8-3.5 USD by a plan that the pooled MILP did not generate. The exact oracle leads to a different equilibrium: welfare +0.21% in Paris (5718.17 against 5706.43), -0.53% in Berlin (8401.35 against 8446.19). The sign differs, so this is a change of equilibrium (the game has several), not a systematic welfare gain. The ZMC potential improves in both cities (Paris -3902.1 against -3897.7, Berlin -5611.3 against -5601.6), and the certified gap of the dual bound shrinks (`eta_cert` 156 against 166, and 172 against 206); the largest oracle gap `lp_gap_max` drops from 16 and 21 USD to 2.1 and 0 USD.
* Time limits: in Paris 2 of 56 calls reached the 20 s limit (largest remaining gap 2.14 USD). With a 120 s limit all 56 calls are optimal, with the same equilibrium and welfare (`results/bp_game_Paris_tl120.csv`). The runtime is 3 times (London, Berlin) to 9 times (Paris) that of price-and-branch.
* Caveat: the new profile has regret 0 against the fresh exact oracle, which uses the same method. The result is therefore exact up to the 1e-8 gap and the time limits stated, and conditional on the correctness of the pricer (checked against enumeration in `tests/test_brl.py` and in the verification above). Only the three cities and seed 0 of the base case were rerun; the other six cities, the sensitivity scenarios, the leader and imprecision experiments (E2-E4) were not rerun with the exact oracle, and their numbers in this document still come from price-and-branch.

Bugs and issues found: (1) price-and-branch is suboptimal on 39 of 800 random formulations; (2) the published equilibria of Paris and Berlin carry exact-oracle regrets of up to 3.5 USD; (3) the first branch-and-price version stalled on Cairo, fixed by the fleet-size row; (4) with the covering formulation of `real_instances.column_generation` the repair step is not guaranteed to preserve optimality, so the published "P&B" column is only an upper bound; the partition formulation used here is what the heuristics optimise. No error was found in the BRL pricer itself.

Reproduce (about 33 minutes of one core for the metro runs, 5 min for the game, 3 min for verification; all resumable; the commands skip finished results):
```
export OMP_NUM_THREADS=1
python experiments/run_bp.py verify                                   # 800 formulations vs enumeration
python experiments/run_bp.py metro London Paris Berlin NewYork Bombay --tl 1800 &
python experiments/run_bp.py metro BuenosAires Cairo Moscow NewDelhi --tl 1800 &
python experiments/run_bp.py game London Paris Berlin --tl 20          # integrated oracle (add: Paris --tl 120 --tag _tl120)
python experiments/run_bp.py metro NewDelhi Cairo Bombay Berlin London --ng 22 --tag _ng22 --tl 900   # elementary cross-check
python experiments/run_bp.py summary                                   # results/summary_bp*.csv, figures/bp_gap.png
python -m pytest -q                                                    # 97 tests, 13 s
```


## Exact oracle re-run

Date: 2026-10-24. E1-E4 of Section 4 were first computed with the price-and-branch integer step (A2). After branch-and-price
(`ccu.bp`, previous section) became available, they were re-run with the exact integer step in the carrier oracle
(`RoutingGame.bp_time`). The **files in `results/` (and `figures/`) are now the exact ones**, under the usual names, so `summarize.py`,
`plot_results.py` and the paper tables read them unchanged (with two small filters, see below). The price-and-branch results are untouched in
`results/pb_old/` (all `E1-E4`, `zones`, `summary_*`, `tables.md`) and `figures/pb_old/`. The tables of Sections 4 and 4a above still quote the
price-and-branch numbers; `results/exact_vs_pb_comparison.csv` (mean over the seeds that were re-run) and
`results/exact_vs_pb_comparison_by_seed.csv` hold old and new side by side, the tables below are generated from them (`experiments/exact_report.py`).
`paper/` was not touched.

**Protocol.** Branch-and-price on the pool columns for every oracle call (pricing calls `rho = 1`, best responses `rho = 0`, regrets), limit 20 s per call.
Pricing calls keep the relative gap 5e-3 of the old pipeline (a call is "proven optimal" when it closes that gap), best responses 1e-8. Calls that
hit the limit are retried with 120 s (E1 and the E2/E3 runs of Cairo, Paris, Buenos Aires, London, New Delhi: every call; Mumbai, New York,
Moscow, Berlin and all of E4: best responses and regrets only, because a pricing call only steers the price search and a 120 s retry on every
pricing call made the 63-point grids unaffordable). Every call is counted (`bp_calls`, `bp_optimal`, `bp_retried`, `bp_unproven`, `bp_max_gap` in the result rows,
`results/summary_exact_oracle.csv` per experiment, city and seed); the remaining gap of an unproven call is the incumbent value minus the proven bound, in USD of the oracle objective.
Equilibria are verified as before: E1 and the E2 best point by an independent fresh-pool oracle (elementary routes, empty pool, branch-and-price), E2/E3/E4 grid
points by the pooled exact oracle; new in E3: the profiles `NE_zmc`, `NE_priced_main`, `NE_priced_broad` are also verified with a fresh exact oracle (`max_regret_fresh`).
The old (price-and-branch) equilibria were re-tested with the same fresh exact oracle in all 27 city/seeds (`results/exact_parts/oldreg_*.csv`, `experiments/run_old_regret.py`).

**What was reduced (the full re-run did not fit the budget of about 6 hours on 3 cores; one exact E1 solve costs 3-12 times the price-and-branch one, the 63-point grids and E3 dominate).**
Coverage per city and seed (E2: grid points solved with the exact oracle out of 63; E3: complete; E4: widths solved exactly out of 12):

| city | s0: E1 / E2 exact pts / E3 / E4 exact rows | s1: E1 / E2 exact pts / E3 / E4 exact rows | s2: E1 / E2 exact pts / E3 / E4 exact rows |
|---|---|---|---|
| New Delhi | x / 63/63 / x / 12/12 | x / 63/63 / x / 12/12 | x / 63/63 / x / 12/12 |
| Cairo | x / 13/63 / x / 6/12 | x / 17/63 / x / 6/12 | x / 13/63 / x / . |
| Moscow | x / 12/63 / x / 6/12 | x / 10/63 / x / 6/12 | x / . / . / . |
| Buenos Aires | x / 63/63 / x / 12/12 | x / 63/63 / x / 12/12 | x / 63/63 / x / 12/12 |
| New York | x / 7/63 / x / 6/12 | x / 7/63 / x / 6/12 | x / . / . / . |
| Mumbai | x / 15/63 / x / 12/12 | x / 14/63 / x / 12/12 | x / 14/63 / x / 12/12 |
| London | x / 63/63 / x / 12/12 | x / 63/63 / x / 12/12 | x / 63/63 / x / 12/12 |
| Paris | x / 14/63 / x / 6/12 | x / 13/63 / x / 6/12 | x / 13/63 / x / . |
| Berlin | x / 13/63 / x / 6/12 | x / 13/63 / x / 6/12 | x / . / . / . |

* **E1 base: all nine cities and three seeds, exact** (certified with the fresh exact oracle). The sensitivity scenarios (the `sens` rows of `E1_<city>.csv`) were **not** re-run: they keep their
  price-and-branch values and carry `oracle = pb`; `summarize.py` compares them with the price-and-branch base case of the same seed.
* **E3: exact for 24 of 27 city/seeds** (Cairo, Paris, Buenos Aires, London, New Delhi, Mumbai: three seeds; New York, Moscow, Berlin: seeds 0 and 1). Seed 2 of New York, Moscow and Berlin was not finished in time and is absent from the exact files
  (the new three-seed tables then average two seeds for these cities, `n_seeds` says so; the old values of their seed 2 are in `results/pb_old/`). In New York, Moscow and Berlin the SO benchmark of the *broad* objective (`SO_broad`) was computed with price-and-branch (`oracle = pb` in that row);
  everything else in E3 is exact.
* **E2 grid: complete 63-point exact grid for Buenos Aires, London and New Delhi; for Cairo, Paris, Berlin, New York, Moscow and Mumbai only a subset of the grid is exact**, chosen by screening with the price-and-branch grid of the same city and seed: the exact oracle is applied at (0, 0) and
  at the two best points of every (objective, configuration) among the three charge configurations (`CCU_E2_MODE=minimal`). The other grid points keep their price-and-branch row (`oracle = pb`, copied from `results/pb_old`).
  `summarize.py` and `plot_results.py` ignore the `pb` rows, so the best point of every configuration is the best *exact* point. The reported leader gains of these six cities are therefore **lower bounds** of the gain over the 63-point grid
  (the exact grid is a subset), and shares of delivery-only in the two-instrument gain can exceed 1 when the best two-instrument point was not among the exact points (Mumbai seed 1: 1.38). No local refinement was done (the first, abandoned, version also evaluated the grid neighbours of the best point, so Cairo, Paris, Mumbai, Moscow and Berlin seeds contain a few more exact points than the minimal set; the number of exact points is in the coverage table).
  The leader's best points, E2best, E2cert and the priced equilibria of E3 are all exact equilibria of the exact game.
* **E4: complete for New Delhi, Buenos Aires, London and Mumbai (12 widths, exact); for Cairo, Paris, Berlin, New York and Moscow six widths are exact (p-box alpha in {2, 0.05, 1e-4}, i.e. eps = 0, base, widest; credal delta in {0, 0.2, 0.8}) and the others keep price-and-branch rows (`oracle = pb`, ignored by `summarize.py`)**.
  Seeds: see the coverage table (a dot means the seed was not re-run exactly; it is then absent from the new tables).

**Oracle calls proven optimal.**

| experiment | bp_calls | bp_optimal | bp_retried | bp_unproven | proven_share | max_remaining_gap_usd |
|---|---|---|---|---|---|---|
| E1 | 1403 | 1385 | 55 | 18 | 0.987 | 4.84 |
| E2 | 24256 | 24205 | 189 | 51 | 0.998 | 3 |
| E2cert_fresh | 761 | 744 | 40 | 17 | 0.978 | 4.94 |
| E3 | 3694 | 3655 | 104 | 39 | 0.989 | 5.7 |
| E3_fresh_verification | 342 | 330 | 33 | 12 | 0.965 | 5.7 |
| E4 | 8135 | 8089 | 34 | 46 | 0.994 | 8.47 |

Over all experiments 38591 oracle calls were solved by branch-and-price, 38408 (99.53%) proven optimal (within the stated gap), 455 calls needed the 120 s retry, 183 (0.47%) remain unproven. In the calls that are not proven, the remaining gap (incumbent minus proven lower bound) is at most 8.5 USD
(plans worth 10^2-10^4 USD); the equilibria are verified against the incumbents of the verifying calls, so a profile can only be an exact equilibrium
up to the regret *bound* `max_regret_lp` (verifying call against its proven lower bound). That bound is zero for all but the following E1/E2cert profiles (largest bound 4.84 USD, New York seed 2 base case;
the same profile has regret 0 against the incumbent): Cairo seed 2 (E1, 0.00201 USD); Cairo seed 2 (E2 best point, 0.0221 USD); Moscow seed 2 (E1, 1.24 USD); NewYork seed 2 (E1, 4.84 USD); Paris seed 0 (E2 best point, 1.76 USD); Paris seed 1 (E1, 0.759 USD); Paris seed 1 (E2 best point, 2.64 USD); Berlin seed 1 (E2 best point, 1.72 USD); Berlin seed 2 (E1, 0.9 USD).

By city:

| city | bp_calls | bp_optimal | bp_unproven | proven_share | max_gap_usd |
|---|---|---|---|---|---|
| NewDelhi | 8759 | 8756 | 3 | 1 | 0.243 |
| Cairo | 1832 | 1792 | 40 | 0.978 | 0.573 |
| Moscow | 1496 | 1488 | 8 | 0.995 | 2.62 |
| BuenosAires | 7612 | 7612 | 0 | 1 | 0 |
| NewYork | 987 | 970 | 17 | 0.983 | 7.55 |
| Bombay | 4071 | 4025 | 46 | 0.989 | 0.821 |
| London | 8510 | 8510 | 0 | 1 | 0 |
| Paris | 3009 | 2966 | 43 | 0.986 | 8.47 |
| Berlin | 2315 | 2289 | 26 | 0.989 | 5.4 |

**Verification that the returned profiles are exact pure equilibria.** Regret against the *fresh* exact oracle (elementary routes, empty pool): E1 base, all 27 city/seeds: maximum 9e-13 USD (zero); E2 best "both" point (`E2cert`): 0 in all 24 certified city/seeds; E3 `NE_zmc` and priced profiles (`max_regret_fresh`): 0 in all
24 verified city/seeds. All grid points of E2, E3 and E4 have regret at most 3e-13 USD against the pooled exact oracle, and every ZMC solve converged (best-response polish).
For the price-and-branch equilibria the same test gives (regret, USD; seeds in which at least one carrier could gain):

| city | seeds | seeds_not_exact_eq | max_regret_usd |
|---|---|---|---|
| NewDelhi | 3 | 0 | 0 |
| Cairo | 3 | 3 | 0.819 |
| Moscow | 3 | 2 | 0.834 |
| BuenosAires | 3 | 0 | 0 |
| NewYork | 3 | 1 | 4.04 |
| Bombay | 3 | 0 | 0 |
| London | 3 | 0 | 1.14e-13 |
| Paris | 3 | 2 | 2.04 |
| Berlin | 3 | 2 | 3.54 |

So the old equilibria were already exact in New Delhi, Buenos Aires, Mumbai and London; in Cairo (3 of 3 seeds, up to 0.8 USD), Moscow (2 of 3, 0.8), New York (1 of 3, 4.0), Paris (2 of 3, 2.0) and Berlin (2 of 3, 3.5 USD) the old profile was not an exact equilibrium.
Several equilibria exist, and where the old one was exact the exact run can still select another one (Buenos Aires seed 0, see below), because the pricing calls and the best responses are solved by a different integer method and the ZMC trajectory differs.

**Old (price-and-branch) against new (exact).** Mean over the seeds that were re-run (same seeds on both sides).

| city | welfare | served_share | slowdown_pct |
|---|---|---|---|
| New Delhi | 82.7 -> 82.7 | 0.259 -> 0.259 | 4.18 -> 4.18 |
| Cairo | 1065.0 -> 1065.9 | 1.000 -> 1.000 | 3.61 -> 3.61 |
| Moscow | 6755.7 -> 6756.0 | 0.990 -> 0.990 | 17.57 -> 17.57 |
| Buenos Aires | 276.0 -> 272.3 | 0.367 -> 0.359 | 0.81 -> 0.77 |
| New York | 20001.5 -> 20002.8 | 0.989 -> 0.989 | 7.75 -> 7.75 |
| Mumbai | 152.8 -> 152.8 | 0.448 -> 0.448 | 4.59 -> 4.59 |
| London | 570.1 -> 570.1 | 0.182 -> 0.182 | 6.68 -> 6.68 |
| Paris | 5327.1 -> 5331.6 | 0.845 -> 0.847 | 4.98 -> 4.99 |
| Berlin | 8630.6 -> 8618.8 | 0.892 -> 0.889 | 3.67 -> 3.68 |

| city | both | delivery_only | congestion_only | share_delivery_alone |
|---|---|---|---|---|
| New Delhi | 14.51 -> 14.49 | 10.98 -> 10.32 | 0.00 -> 0.00 | 0.73 -> 0.68 |
| Cairo | 0.11 -> 0.00 | 0.04 -> 0.00 | 0.11 -> 0.00 | n/a -> n/a |
| Moscow | 0.13 -> 0.13 | 0.11 -> 0.13 | 0.01 -> 0.00 | 0.85 -> 1.00 |
| Buenos Aires | 33.35 -> 35.45 | 33.35 -> 35.45 | 1.25 -> 2.49 | 1.00 -> 1.00 |
| New York | 0.45 -> 0.39 | 0.42 -> 0.39 | 0.06 -> 0.00 | 0.93 -> 1.00 |
| Mumbai | 2.87 -> 2.16 | 1.97 -> 2.09 | 0.00 -> 0.00 | 0.61 -> 0.88 |
| London | 58.48 -> 59.72 | 47.95 -> 49.27 | 0.45 -> 0.45 | 0.84 -> 0.85 |
| Paris | 3.77 -> 3.57 | 3.62 -> 3.47 | 0.55 -> 0.04 | 0.95 -> 0.97 |
| Berlin | 1.39 -> 1.77 | 1.24 -> 1.70 | 0.00 -> 0.00 | 0.89 -> 0.96 |

| city | PoA_zmc | PoS | PoA_worst | priced_gap_pct | unpriced_gap_pct |
|---|---|---|---|---|---|
| New Delhi | 1.180 -> 1.180 | 1.172 -> 1.172 | 1.197 -> 1.197 | 2.95 -> 2.96 | 15.20 -> 15.20 |
| Cairo | 1.001 -> 1.000 | 1.000 -> 1.000 | 1.001 -> 1.000 | -0.00 -> 0.00 | 0.11 -> 0.00 |
| Moscow | 1.001 -> 1.001 | 1.001 -> 1.001 | 1.001 -> 1.001 | 0.01 -> 0.01 | 0.14 -> 0.13 |
| Buenos Aires | 1.358 -> 1.380 | 1.333 -> 1.334 | 1.399 -> 1.426 | 1.78 -> 1.81 | 26.26 -> 27.37 |
| New York | 1.004 -> 1.004 | 1.004 -> 1.004 | 1.004 -> 1.004 | 0.00 -> 0.00 | 0.45 -> 0.39 |
| Mumbai | 1.032 -> 1.032 | 1.032 -> 1.032 | 1.077 -> 1.077 | 0.36 -> 1.04 | 3.13 -> 3.13 |
| London | 1.655 -> 1.655 | 1.628 -> 1.628 | 1.752 -> 1.752 | 4.33 -> 3.69 | 38.65 -> 38.65 |
| Paris | 1.039 -> 1.037 | 1.029 -> 1.031 | 1.039 -> 1.037 | 0.16 -> 0.16 | 3.78 -> 3.59 |
| Berlin | 1.015 -> 1.018 | 1.015 -> 1.018 | 1.018 -> 1.018 | 0.14 -> 0.05 | 1.51 -> 1.79 |

| city | pbox_deliveries | pbox_welfare | gamma_deliveries |
|---|---|---|---|
| New Delhi | -53.5 -> -53.5 | -60.1 -> -60.4 | -62.2 -> -62.2 |
| Cairo | 0.0 -> 0.0 | -2.7 -> -2.8 | -31.4 -> -30.9 |
| Moscow | -1.5 -> -1.5 | -10.5 -> -10.5 | -64.1 -> -64.8 |
| Buenos Aires | -53.0 -> -52.3 | -53.0 -> -52.9 | -65.6 -> -64.9 |
| New York | -2.5 -> -2.5 | -10.7 -> -10.9 | -67.3 -> -66.2 |
| Mumbai | -28.8 -> -29.4 | -30.8 -> -30.3 | -59.3 -> -59.0 |
| London | -63.4 -> -64.8 | -73.9 -> -74.8 | -89.5 -> -89.5 |
| Paris | -7.4 -> -9.1 | -16.5 -> -17.0 | -75.0 -> -73.5 |
| Berlin | -6.9 -> -8.6 | -16.8 -> -17.6 | -71.1 -> -71.3 |

Gains are in percent of |social cost| of the unpriced equilibrium, main objective; PoA = W_SO / W_NE; priced gap = (W_SO - W_priced)/W_SO. By seed: `results/exact_vs_pb_comparison_by_seed.csv`.

**What did not change.**
* The E1 picture: welfare, served share and slowdown are the same to three digits in New Delhi, Mumbai and London and within 0.01% in Moscow and New York, within 0.1% in Cairo, Paris and Berlin, and 1.4% (welfare) / 0.8 pp (served share) lower in Buenos Aires (a different equilibrium).
* The PoA ordering **London (1.66) > Buenos Aires (1.38) > New Delhi (1.18)** and the ordering of all nine cities (Paris 1.04, Mumbai 1.03, Berlin 1.02, New York 1.00, Moscow 1.00, Cairo 1.00) are unchanged for PoA, PoS and the worst equilibrium found; London's PoA is identical to three digits.
  The exact SO benchmark is slightly higher than the price-and-branch one (up to +0.2%), the exact equilibria are slightly higher or lower, so PoA moves by at most 0.03.
* "Large PoA only where the leader's gain is large": London, Buenos Aires and New Delhi stay the only cities with PoA >= 1.10 and the only ones with leader gains above 10%.
* "Priced equilibria are within a few percent of the optimum": the largest single-seed priced gap is still London seed 1, 7.4% of W_SO (unchanged), the city means are 3.7% (London), 3.0% (New Delhi), 1.8% (Buenos Aires), 1.0% (Mumbai) and 0.2% or less elsewhere.
  The ordering of the cities by priced gap is unchanged; Mumbai's mean rises from 0.36% to 1.04% and London's falls from 4.33% to 3.69%.
* E4: deliveries and welfare fall with both kinds of imprecision in every city, with the same magnitudes (the widest-width effect changes by at most 2 percentage points), see the table.

**What flipped or moved.**
* **The "congestion charge alone gains less than 1.7%" bound fails in Buenos Aires seed 0: 6.5%** (old: 1.67%, so the old maximum was just below the bound). The reason is the baseline, not the charge: the exact unpriced equilibrium of Buenos Aires seed 0 is a worse one
  (social cost -252.2 against -266.7), while the best congestion-charge equilibrium is about the same (-268.6 against -271.1). Seeds 1 and 2: 0.4% and 0.5%. All other city/seeds stay below 1.7% (largest: London 1.34%, Paris 0.12%, Cairo 0). So "a congestion charge alone is nearly worthless" is true in eight of nine cities and, in Buenos Aires, depends on which unpriced equilibrium is selected.
* **Cairo: the leader's gain vanishes in the evaluated points** (old 0.05-0.15% for the congestion charge, now 0 in all seeds: with the exact oracle none of the 13-17 exact points beats no charge, so the tiny price-and-branch gains were artefacts of the integer step at those points). Paris' congestion-only gain falls from 0.55% to 0.04% (a lower bound, reduced grid); in the full-grid cities the congestion-only gains are unchanged (New Delhi 0, London 0.45%) or larger (Buenos Aires 1.25% -> 2.49%, see above).
* **Delivery-only share of the two-instrument gain** (the paper's statement that the per-delivery instrument alone captures about half or more): the by-seed statement "at least half in every seed" now fails in New Delhi seed 0 (0.57 -> 0.41; the delivery-only gain 7.0% -> 5.0% of |SC|) as well as in Mumbai seed 0 (0.04 -> 0.46, failing in both runs).
  Mumbai's three-seed mean share is 0.88 (was 0.61), but Mumbai is a reduced grid, where the two-instrument gain is a lower bound; in seed 1 the share exceeds 1 (1.38). The qualitative statement (delivery-only dominates; congestion-only is negligible) stands; the numbers for Mumbai should not be quoted to two digits.
* **Buenos Aires**: E1 welfare -1.4% (276.0 -> 272.3), leader gain 33.3% -> 35.4%, PoA 1.358 -> 1.380 (seed 0: 1.349 -> 1.429), all from the changed equilibrium of seed 0 (welfare -5.4%) and a small shift in seed 2.
* **Berlin**: E1 welfare -0.14%; seed-0 PoA 1.014 -> 1.020 (equilibrium welfare -0.53%, the equilibrium found by `run_bp.py game` earlier); Paris: welfare +0.09%, Cairo +0.09%.
* New York and Moscow: the equilibria differ in the second digit only; New York seed 2 base case has 6 unproven calls (gap bound 4.8 USD on a welfare of 20,000), see above.

**Caveats.** (1) The exact oracle is exact for the elementary problem with the proven bound only where the call is proven optimal; unproven calls are quantified above (largest gap 8.5 USD). (2) The reduced grids make the E2 gains of Cairo, Paris, Berlin, New York, Moscow and Mumbai lower bounds. (3) The equilibrium is not unique; PoS/PoA use the equilibria found from six starting points, as before.
(4) Two oracle protocols were used for the pricing calls (retry on all calls, or on best responses only, see Protocol); the equilibria and their verification are the same in both. (5) The E1 sensitivity and the E5/E6/verification runs of Section 4 were not re-run.
Run time: 6 h 25 min (10:34-16:59) wall-clock on 3 processes for E1, E2/E3, E4 and the 27 regret checks of the old equilibria (price-and-branch needed about 3 hours of one core in total for the same files, excluding the sensitivity runs).

**Reproduce** (all steps resumable; finished work is skipped; status in `results/PROGRESS_exact.md`; 3 processes):
```
export OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
nohup python experiments/run_exact_queue.py > results/logs/run_exact_queue.out 2>&1 &   # scheduler, priority order, 3 jobs at a time
#   one job by hand (BP time limit 20 s, retry 120 s; E2/E4 modes as in run_exact_job.sh):
#   experiments/run_exact_job.sh e1|leader|imprecision|oldreg CITY SEED
python experiments/run_exact.py assemble --keep-old-sens      # E1 parts -> results/E1_<city>.csv, zones, traces
python experiments/summarize.py && python experiments/summarize_exact.py && python experiments/plot_results.py && python experiments/plot_equilibria.py
python experiments/exact_report.py                            # the tables of this section
python -m pytest -q
```
The environment variables read by `build_city_game` and the scripts: `CCU_BP_TIME` (per-call limit, s; unset = price-and-branch), `CCU_BP_RETRY`, `CCU_E2_MODE` (`full` | `reduced` | `minimal`), `CCU_E4_MODE` (`full` | `reduced`), `CCU_E3_SO_BROAD` (`pb`).
Old results: `results/pb_old/`, `figures/pb_old/`. New code: `experiments/run_exact*.py|sh`, `run_old_regret.py`, `summarize_exact.py`, `exact_report.py`; changes in `run_leader.py`, `run_imprecision.py`, `common.py`, `zmc_brl.py` (counters, retry), `summarize.py` and `plot_results.py` (filters for the `oracle = pb` rows).

## Theory-to-experiment checks

Code: `src/ccu/credal.py` (E / maximal / interval-dominance thresholds, Gamma-maximin regret, anchored radius and the bounds of main.tex Thm 6.1, relaxed-equilibrium search), `src/ccu/d2game.py` (vehicle-count congestion game, tiny enumeration), `experiments/run_theory_checks.py`, `experiments/run_theory.sh`, `tests/test_credal.py`. Outputs: `results/theory_absorption_*.csv` (profile level, per city; `theory_absorption_summary.csv` per city/seed/anchor; `theory_absorption_equilibria.csv`), `results/theory_gamma_*.csv`, `results/theory_D2_*.csv`, `results/summary_theory.csv`, `figures/theory_absorption.png`, `figures/theory_D2.png`. Reproduce: `experiments/run_theory.sh` (absorption + Gamma, 9 cities x seeds 0-2, 2 jobs, resumable, about 1.5 h), `python experiments/run_theory_checks.py d2tiny` (2 min), `KIND=d2city CITIES="Cairo Paris Bombay" experiments/run_theory.sh`, `python experiments/run_theory_checks.py report`.

**Conventions.** Thresholds are exact up to the BRL oracle (price-and-branch): E by Kelley cuts on the LP (EthrLP), maximal and ID by bisection with one shifted-price oracle call. Because the oracle is exact only to a small gap, every threshold is relaxed by the observed inexactness (`eps`, largest improvement a known plan or the oracle offers at a certified equilibrium, up to 1.9 USD on plans worth 10^2-10^3); `eps = 0` gave infinite thresholds in a few cases. Belief weights: `agg` (E4 convention, w_k = realised aggregate), robustness `type_median`. The city game is D1 and the ZMC+BRL profile is an exact pure equilibrium, so its own threshold is 0 and its anchored bound is 0 (point-mass anchor): the absorption theorem is tight but empty there. Informative tests need non-trivial relaxed equilibria x*; they were built from pairs of distinct pure equilibria (best-response dynamics from perturbed starts, 4-9 per game) by solving the two-plan indifference system and verifying the result with the oracle (support plans optimal over all plans, B_j := supp). All profiles in the product of supports (at most 16 sampled with exact thresholds) are tested.

**Absorption (Thm 6.1), w = agg.** 14 of 27 games have a non-trivial relaxed equilibrium (43 anchors before de-duplication, 24 distinct; Cairo and Moscow none: everything is served, no conflicts). Per city (means over the seeds that have an anchor):

| city | N | Z | seeds with a mixed anchor | rho-bar | d_L | anchored bound | N-uniform bound | min delta-hat | max_p delta_E | max delta_E / bound | max delta_E / delta-hat |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Cairo | 4 | 42 | 0/3 | - | - | - | - | - | - | - | - |
| Bombay | 5 | 143 | 2/3 | 0.74 | 3.3 | 1.23 | 10.6 | 0.36 | 0.53 | 0.43 | 0.60 |
| Paris | 5 | 198 | 3/3 | 0.88 | 2.0 | 1.39 | 8.4 | 0.40 | 0.69 | 0.49 | 0.70 |
| NewDelhi | 5 | 120 | 3/3 | 1.02 | 2.7 | 1.61 | 10.7 | 0.56 | 0.64 | 0.41 | 0.60 |
| Moscow | 5 | 160 | 0/3 | - | - | - | - | - | - | - | - |
| BuenosAires | 4 | 208 | 1/3 | 0.96 | 2.0 | 1.76 | 8.8 | 0.24 | 0.83 | 0.47 | 0.48 |
| NewYork | 4 | 234 | 1/3 | 0.82 | 1.0 | 1.58 | 3.7 | 0.42 | 0.82 | 0.52 | 0.58 |
| London | 5 | 348 | 3/3 | 0.85 | 2.0 | 1.56 | 13.6 | 0.42 | 0.82 | 0.53 | 0.76 |
| Berlin | 6 | 593 | 1/3 | 0.94 | 2.0 | 0.94 | 8.0 | 0.28 | 0.41 | 0.44 | 0.74 |

Findings. (i) No violation anywhere: delta_E(p) <= delta-hat(p) for all 274 tested profiles (159 under the realised-aggregate weights, 115 under the second weighting), min_p delta-hat <= three-term bound, delta_0 <= N-uniform bound, order ID <= M <= E (both w modes). (ii) The bound is loose by about a factor 2 against the worst profile and 3-15 against the profile of the construction: max delta_E / anchored bound 0.28-0.60 (median 0.45), delta_E(p*) / bound median 0.015 (p* = argmin delta-hat), delta_E / delta-hat up to 0.76. The N-uniform bound is 5-30 times looser (ratio 0.03-0.22). (iii) The first term (N-1) rho-bar is the minimum in every anchor (k = min(N, d_L) = 1-4 so k sigma-bar + rho-bar is 2-9); the Shapley-Folkman and Hoeffding terms are irrelevant at N <= 6, as the theory says. (iv) Dependence: ratio vs N not significant (Spearman -0.18), mild increase with d (Spearman 0.46, p = 0.02, 24 points: exploratory); the N-uniform bound does not grow with d here because min{N-1, ...} = N-1. rho-bar is 0.5-1.1 because mixing carriers switch whole zone lots. (v) Maximal and E thresholds coincide in 99% of profiles; ID threshold is about 8% of E (median). (vi) The ZMC rounding before the best-response polish is E-admissible at a finite width in only 10 of 27 games (infinite: some carrier's plan is strictly dominated), so the polish step is what makes absorption apply.

**Gamma-maximin (Lemma 3.6).** The surcharge-game equilibrium (ZMC+BRL on charges delta M_k w_k, certified) differs from the precise equilibrium in all 108 (city, seed, delta) cases. The precise equilibrium is not Gamma-admissible (Gamma-regret column below), whereas the Gamma equilibrium is maximal at width delta (M threshold / delta = 0.76-0.99, never above 1: 106 of 108 finite, 2 Cairo cases infinite from oracle slack 0.02-0.17 USD) and its E threshold equals it (E_thr = M_thr). Gamma therefore drops service sharply (share of demand served, NE minus Gamma):

| city | served drop at delta=0.1 | 0.25 | 0.5 | 1.0 | Gamma-regret of the precise NE at delta=0.5 (USD) | M-threshold of Gamma-eq / delta at 1.0 |
|---|---|---|---|---|---|---|
| Cairo | 0.000 | 0.000 | 0.014 | 0.475 | 0.9 | 0.99 |
| Bombay | 0.049 | 0.102 | 0.159 | 0.335 | 14.2 | 0.92 |
| Paris | 0.036 | 0.139 | 0.428 | 0.739 | 374.8 | 0.96 |
| NewDelhi | 0.008 | 0.050 | 0.115 | 0.177 | 3.5 | 0.89 |
| Moscow | 0.002 | 0.012 | 0.237 | 0.732 | 43.2 | 0.97 |
| BuenosAires | 0.082 | 0.086 | 0.134 | 0.310 | 31.7 | 0.93 |
| NewYork | 0.009 | 0.025 | 0.127 | 0.710 | 134.8 | 0.98 |
| London | 0.033 | 0.061 | 0.098 | 0.172 | 62.5 | 0.76 |
| Berlin | 0.050 | 0.138 | 0.501 | 0.765 | 601.0 | 0.97 |

**D2 (vehicle-count congestion).** Gadgets (`theory_D2_prop71.csv`, `theory_D2_kernels.csv`, same threshold code through `ExplicitGame`): Prop 7.1 gives delta_0^E = delta_0^M = 1/w for w = 0.5, 1, 2 (2, 1, 0.5), no pure NE, ID threshold 0.6/w; Thm 7.3 kernel construction on 223 digraphs (n = 3 all, n = 4, 5 sampled): the sets ICNE_E, M, ID, Gamma at delta = 0 and 0.999/(2 Delta+ + 1) equal the kernel set in 223/223, delta_0 = 0 iff a kernel exists, otherwise delta_0 >= 1/(2 Delta+ + 1) (observed 0.27-0.63 vs 0.11-0.33). Random bilinear D2 games (N = 3): 6/400 have no pure NE (D1 control: 0/150), delta_0 in 0.03-0.46, always below the N-uniform bound (ratio <= 0.09); on 18 verified relaxed equilibria no violation, delta_E/delta-hat reaches 1.0 (tight). Routing-integrated D2 tiny games (N = 3-4, scales 1, 30, 1000, 540 game-scale runs (180 games, scales 1, 30, 1000), including shared-zone lots): a pure NE always exists (0 of 540 without), so delta_0 = 0; the Prop 7.1 pattern (few long vs many short vehicles with opposite exposures) cannot be generated by routing plans, because exposure is proportional to the service indicator and subsets add. Cities (Cairo, Mumbai, Paris, seeds 0-2, externality scale 1, 10, 100, 1000, 10^4, 4 best-response starts each, 40-pass budget): all 180 runs converge to a pure NE (0 cycles), 1-4 distinct equilibria. At scale 1 the D1 equilibrium is already a D2 equilibrium in 6/9 runs (regret otherwise 1.6 USD in Paris); from scale 10 it is not (regret 12-21 USD at 10), the carriers change plans, and best-response dynamics still converge. The measured E width of the D1 profile under D2 is 0 where it is an equilibrium and infinite otherwise (its deviation is rival-independent, i.e. dominance), while the ID width is 0.0004-0.7. Null result: D2 does not bite on city instances; non-existence needs adversarial plan menus, which the Thm 7.3 and Prop 7.1 gadgets provide.

Caveats: relaxed equilibria are found only for two-plan mixing (not all equilibria); the thresholds are exact only up to the oracle gap (eps above); the D2 calibration M_X = scale gc hbar is a new assumption; D2 city runs do not test Thm 6.1 because no cycle occurred.


## Dual implementation pricing

Date: 2026-10-25. A replacement for the leader's grid of E2 (`src/ccu/dip.py`, `experiments/run_dip.py`; method and proofs in
`theory/new_algorithm_C/{algorithm.md,theory.tex,results.md}`).

**Method.** (1) Compute the pure social optimum with the E3 machinery (column generation on the social-cost potential, rounding,
coordinate polish, plus a 3-start polish). (2) Because every lot's vehicle-hours are proportional to its deliveries (h = r d), the two
instruments act through one number per zone, u_z = s + r t_z; start from the tangent charge u_z = kappa_z Q*_z - (m_z/2) dbar_z
(congestion externality at the target minus a half-lot Cournot subsidy; kappa = gc r^2, m = b + kappa). (3) Ask every carrier for its
best response to the target under u (N oracle calls); each improving answer is a linear cut on u; an LP returns the charge closest to the
tangent that satisfies all cuts; repeat until no carrier wants to deviate. The target is then an exact pure equilibrium under u; no
equilibrium is ever solved for the leader's decision. (4) Post u as a uniform per-delivery subsidy s = min u plus zone congestion
charges t_z = (u_z - s)/r >= 0.

**Protocol.** Exact oracle (branch-and-price, 20 s, retry 120 s), `n_cust = 22`, seeds 0-2, nine cities (27 runs). Baseline: the exact
E2 grid of the same city and seed (seed 2 of Berlin, Moscow, New York: the price-and-branch grid in `results/pb_old`, flagged
`grid_oracle = pb`). Every oracle query of the method is counted with the counter of the E2 `calls` column; the fresh-oracle verification
is not counted (as for the grid's best point).

**Results** (`results/summary_dip.csv`, figure `figures/dip_calls_vs_gain.png`, zone maps `figures/dip_charges_<city>.png`):

| city | seeds | gain_share_mean | gain_share_min | calls_share_mean | calls_share_max | calls_share63_mean | time_share_mean | all_exact | PoA_dip_mean | PoA_grid_mean |
|---|---|---|---|---|---|---|---|---|---|---|
| London | 3 | 1.14 | 1.04 | 0.084 | 0.0938 | 0.084 | 0.867 | True | 0.998 | 1.04 |
| BuenosAires | 3 | 1.07 | 1.05 | 0.0599 | 0.063 | 0.0599 | 0.324 | True | 1 | 1.02 |
| NewDelhi | 3 | 1.24 | 1.14 | 0.0532 | 0.0557 | 0.0532 | 0.149 | True | 1 | 1.03 |
| Bombay | 3 | 1.91 | 1.2 | 0.27 | 0.311 | 0.0613 | 0.28 | True | 0.997 | 1.01 |
| Paris | 3 | 1.04 | 1.02 | 0.222 | 0.231 | 0.0469 | 0.607 | True | 1 | 1 |
| Berlin | 3 | 1.07 | 1.03 | 0.121 | 0.167 | 0.0358 | 0.26 | True | 1 | 1 |
| Cairo | 3 | n/a | n/a | 0.104 | 0.116 | 0.0233 | 0.0992 | True | 1 | 1 |
| Moscow | 3 | 1.03 | 1 | 0.0984 | 0.134 | 0.0252 | 0.17 | True | 1 | 1 |
| NewYork | 3 | 1.01 | 0.999 | 0.167 | 0.236 | 0.0272 | 0.201 | True | 1 | 1 |

`gain_share` = DIP gain / best grid gain (social cost, main objective); `calls_share` = DIP calls / calls of the exact grid points;
`calls_share63` = DIP calls / (63 x mean calls per exact grid point). Cairo: no charge improves on the unpriced equilibrium (grid and DIP gain 0).

* Full-grid cities (London, Buenos Aires, New Delhi, 9 runs): 104-135% of the grid-optimal gain (mean 115%) with 4.9-9.4% of its calls.
* All 27 runs: the target was implemented exactly (fresh exact oracle regret <= 9e-13 USD); 18 runs needed no cut at all (the tangent
  charge already implements the optimum), the others 2-3 rounds. The priced equilibrium has PoA 1.000 against the E3 social optimum
  (0.995-0.997 in four runs, where the multi-start target beats the E3 benchmark); the grid's best point has PoA 1.01-1.08 in the full-grid cities.
* The equilibrium selected by the grid's own protocol (ZMC from the unpriced prices) under DIP's charges is the target in 21 of 27 runs
  and never loses more than 0.1% of the grid gain.
* Restricting DIP to the grid's two-parameter family still matches the grid in most runs (mean share 1.00, worst 0.50 in Mumbai seed 0):
  the extra gain of full DIP comes from zone-differentiated charges.
* The zone charges follow u_z ~ -0.375 fee / n_z (n_z = number of carriers with a lot in the zone; correlation 0.98-1.00), which
  explains the grid's best uniform subsidies of -0.2 to -0.4 fee.
* Gamma-maximin imprecision: the implementing charge is shifted by the surcharge, u(delta) = u - s_hat(delta); for delta = 0.2 and 0.8
  the target stays an exact equilibrium in all 27 runs at no further optimisation cost (at delta = 0.8 the needed subsidy, 1-3.6 fee, is
  unrealistically large).
* Wall-clock: median 0.22 of the grid's, but not uniformly faster (London seed 0: 247 s against 157 s).
* Tiny games with exhaustive enumeration (210 games, `results/dip_tiny.csv`): DIP reaches the exact leader optimum over all zone charges in
  93% of games (mean 97% of the optimal gain; grid 83%) with 32-49 calls against 1,300-1,800; with the exact social optimum as target it
  reaches it in 100%, so every miss is a miss of the social solver.

**Limits.** Optimistic selection (other equilibria may coexist under the returned charges; in tiny games the worst one can be much worse);
quality bounded by the social solver; the closed forms need one hours-per-delivery ratio; against the reduced exact grids of Mumbai, Paris
and New York DIP uses 21-31% of their (screened) calls.

**Reproduce.**
```
export OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
nohup experiments/run_dip_queue.sh > results/logs/dip_queue.out 2>&1 &     # 27 runs, resumable (results/dip_parts/), DIP_PAR=2 jobs
python experiments/run_dip.py London --seed 0                              # one run by hand
python experiments/dip_tiny.py --n 30                                       # tiny games, exhaustive
python experiments/run_dip.py summary && python experiments/dip_report.py && python experiments/plot_dip.py
python -m pytest -q tests/test_dip.py
```
