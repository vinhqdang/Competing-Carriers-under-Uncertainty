# ARP: results

All numbers from `results/summary_arp.csv` (per city/seed rows `results/arp_<city>[_s<seed>].csv`, stages in
`results/arp_parts/`), `results/arp_tiny.csv` (210 exhaustively enumerated games) and `results/arp_rates.csv`
(contraction constants). Run on 2026-10-26, exact oracle everywhere on the cities (branch-and-price, 20 s per call,
120 s retry, the protocol of the exact E2 and DIP runs), seeds 0, 1, 2, four cities (the three full-grid cities London,
Buenos Aires, New Delhi, and Mumbai). References: the exact E2 grid, DIP and the E3 social optimum of the same city and
seed (`results/summary_dip.csv`). Figures: `figures/arp_calls_vs_gain.png`, `figures/arp_paths.png`, `figures/arp_tiny.png`.

Methods compared (all leader methods; the carriers always best-respond with the exact oracle):

| method | city's information | city's computation |
|---|---|---|
| grid (E2) | carriers' oracle | 63 (or 7-17 exact) equilibrium solves |
| DIP | carriers' oracle | social solve + best-response cuts |
| **ARP flat** | zone aggregates (Q_z, n_z) after each posted charge | one formula per round |
| **ARP flat, msa** | same, successive-averages damping | same |
| **tariff + BR** (ARP-M) | own deliveries of the billed carrier and the zone total | none |
| **tariff + SO** | carriers' oracle (ZMC on the social-cost potential = the E3 solve) | one potential-minimising run |

`gain share` = (SC of the unpriced equilibrium - SC of the method) / (gain of the best exact grid point); `calls` = all
routing-oracle calls made by the simulated carriers while the method runs (the unpriced equilibrium, 40-60 calls, is the
common status quo and is not counted, as in DIP's `dip_calls`); the fresh-oracle verification is not counted.

## Headline (cities, 12 runs)

| city | seed | rho | ARP status / rounds | ARP | ARP msa | tariff+BR | tariff+SO | DIP | ARP calls | tariff+BR calls | tariff+SO calls | DIP calls | grid calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Mumbai | 0 | 0.20 | fixed point / 7 | 2.93 | - | 2.93 | 2.63 | 3.25 | 65 | 9 | 51 | 139 | 586 |
| Mumbai | 1 | 0.09 | fixed point / 3 | 1.11 | - | 1.13 | 1.08 | 1.20 | 30 | 10 | 50 | 169 | 544 |
| Mumbai | 2 | 0.20 | cycle / 5 | 1.28 | 1.27 | 1.11 | 1.18 | 1.28 | 47 | 10 | 49 | 141 | 537 |
| Buenos Aires | 0 | 0.03 | fixed point / 3 | 1.08 | - | 1.08 | 1.08 | 1.09 | 24 | 9 | 40 | 121 | 1921 |
| Buenos Aires | 1 | 0.02 | fixed point / 3 | 1.05 | - | 1.05 | 1.05 | 1.05 | 22 | 10 | 40 | 122 | 1950 |
| Buenos Aires | 2 | 0.11 | fixed point / 3 | 1.08 | - | 1.08 | 1.08 | 1.08 | 23 | 8 | 39 | 105 | 1943 |
| London | 0 | 0.10 | cycle / 5 | 1.02 | 1.03 | 1.04 | 1.00 | 1.04 | 51 | 14 | 49 | 170 | 2376 |
| London | 1 | 0.10 | cycle / 5 | 1.20 | 1.22 | 1.22 | 1.31 | 1.31 | 47 | 9 | 50 | 221 | 2356 |
| London | 2 | 0.10 | cycle / 7 | 1.03 | 1.01 | 1.05 | 1.01 | 1.06 | 67 | 11 | 50 | 206 | 2378 |
| New Delhi | 0 | 0.40 | cycle / 5 | 0.91 | 0.91 | 0.99 | 0.92 | 1.23 | 53 | 11 | 51 | 134 | 2404 |
| New Delhi | 1 | 0.19 | fixed point / 3 | 1.26 | - | 1.35 | 1.27 | 1.35 | 27 | 10 | 51 | 119 | 2418 |
| New Delhi | 2 | 0.40 | cycle / 6 | 1.05 | 1.05 | 1.03 | 1.14 | 1.14 | 60 | 9 | 48 | 132 | 2419 |
| **mean** | | | | **1.25** | | **1.25** | **1.23** | **1.34** | 43 | 10 | 47 | 148 | 1819 |

Reading:
* **From (Q_z, n_z) alone, ARP reaches 91-293% of the exact grid's gain (mean 1.25) in 3-7 posted charges and 22-67
  oracle calls of the carriers**, against DIP's 104-325% (mean 1.34) with 105-221 calls and the oracle. ARP equals DIP
  (within 2%) in 5 of 12 runs (all three Buenos Aires seeds, Mumbai seed 2, New Delhi seed 1), is 2-9% of the grid gain
  below it in London and Mumbai seeds 0-1, and misses in New Delhi seed 0 (0.91 against 1.23: a cycle between two
  equilibria, rho = 0.40, the largest of the sample).
* The flat iteration converged to an exact fixed point in 6 runs (3 rounds in 5 of them, 7 in Mumbai seed 0) and
  cycled between two charges in 6; the cycles are two-equilibrium cycles of the lumpy response (the convexified map
  contracts at rho). The successive-averages variant does not break them (0.91-1.27, same as plain). The contraction
  constants are as predicted: in all 12 runs the relative step `step_rel` falls from 1 to 0.4-0.7 in the first round and
  to below 0.1 or to the cycle amplitude in the second (`arp_step_rel` column).
* **The marginal tariff with the carriers' own best responses from the status quo (8-14 oracle calls, no city
  computation) reaches 99-293% of the grid's gain (mean 1.25)** and equals DIP within 2% in 6 of 12 runs; it never
  lowered the social cost along the way (`mct_br_monotone` true in all runs, as Theorem 8 says). With the E3 solver
  under the tariff (tariff+SO, 39-51 calls) the result is the E3 social optimum in London seed 1, New Delhi seed 2 and
  Buenos Aires (as DIP), and slightly worse elsewhere (the ZMC run from the standard start selects another local
  optimum of SC; DIP's multi-start polish is what makes the difference). The better of the two tariff variants averages
  1.28.
* Every returned profile is an exact pure equilibrium of the posted charges: fresh-oracle regret 0 (<= 1e-13 USD) for ARP
  in all 12 runs; tariff regret 0 in all 12 runs (both variants).
* Price of anarchy against the E3 social optimum: ARP 0.966-1.005 (mean 0.992), tariff+BR 0.975-1.001, DIP 0.995-1.000.
* Wall-clock: ARP 2-41 s against DIP 20-376 s (median ratio 0.04), because no social column generation is needed.
* Charges: ARP's uniform per-delivery part is -1.3 to -1.6 fee (DIP: -0.4 to -0.5 fee), its zone congestion charges
  correspondingly larger: the city-mean lot used for never-served zones spreads the zone charges more than DIP's
  customer-based mean lot. Net subsidies are similar (ARP -51 to -1233 USD, DIP -50 to -1145, tariff -56 to -1241).

## Tiny games, exhaustive enumeration (`results/arp_tiny.csv`, 210 games, 136 with a positive leader gain)

Same instances as DIP's tiny study (N = 3-4 carriers, 3-4 customer zones, congestion x1 / x20 / x60; rho median 0.01 /
0.24 / 0.52). `opt_zone` is the exact optimistic leader optimum over all zone charges. Shares of the exact optimal gain:

| method | information | mean share | median | hits the optimum | >= 95% | worse than unpriced | calls |
|---|---|---|---|---|---|---|---|
| ARP flat, plain | (Q, n) | 0.56 | 1.00 | 35% | 37% | 9 / 136 | 11.5 |
| ARP flat, optimal damping | (Q, n) | 0.59 | 1.00 | 37% | 39% | 11 | 30.2 |
| ARP flat, msa | (Q, n) | 0.64 | 1.00 | 37% | 39% | 8 | 39.8 |
| ARP flat, lots known | (Q, n) + lots | 0.63 | 1.00 | 35% | 37% | 15 | - |
| tariff + BR | own q, Q | 0.80 | 1.00 | 46% | 47% | 3 (*) | 4.8 |
| tariff + SO solve | oracle | 0.94 | 1.00 | 58% | 58% | 1 (*) | 24.2 |
| DIP | oracle | 0.97 | 1.00 | 60% | 60% | 0 | 38.8 |
| grid | oracle | 0.83 | 1.00 | 43% | 44% | 0 | 1518 |

(*) the tariff dynamics are monotone from their own start (the ZMC equilibrium); "worse than unpriced" compares with the
potential-minimising unpriced equilibrium of the enumeration, which differs from the ZMC start in these 3 (1) games.

* The flat rule reached a fixed point in 166 of 210 games (mean 2.3 rounds, at most 8) and cycled in 44, almost all at
  congestion x60 (rho about 0.5-0.7). By congestion level its mean share is 0.72 / 0.64 / 0.23 (x1 / x20 / x60); the
  tariff's 0.93 / 0.79 / 0.58; DIP's 1.00 / 0.96 / 0.93. The failures of the flat rule are of two kinds: (i) the subsidy
  for never-served zones (city-mean lot) attracts entry into zones that the optimum leaves unserved, and the carriers
  then settle in a worse local optimum (the fixed point is a unilateral social optimum, Theorem 4, but a worse one);
  (ii) two-charge cycles at strong congestion. Knowing the lots does not help (0.63): the limit is the information
  about which profile is socially good, which the aggregate does not carry (Theorem 6).
* Under the tariff the set of pure equilibria is exactly the set of unilateral social optima (checked in 210/210
  games: the best tariff equilibrium is the social optimum in every game, mean 3.9 equilibria against 2.4 unpriced),
  and the SC-descent from the status quo never increased SC. Its misses (54%) are local optima of SC.
* Worst equilibrium under the returned charges (share of the optimal gain, mean / median): unpriced -6.4 / -0.04,
  DIP -2.8 / 0.28, tariff -4.4 / 0.24, ARP -2.3 / 0.09. No method has a pessimistic guarantee; the tariff's equilibria
  are all unilateral social optima, which can still be poor.

## Contraction constants (`results/arp_rates.csv`, 48 convexified tiny games, rho from 0.006 to 0.81)

Random charge pairs and iterations from random starts, convexified responses computed exactly over all enumerated plans:
the Lipschitz bound of Theorem 1 (ratio <= 1; observed max 0.99), the plain-map ratio <= rho (Theorem 3a; observed max
0.84 rho), the damped step ratio <= rho/(2+rho) (Theorem 3b; observed max 1.001 of the bound, i.e. tight) hold in all
48 games. The plain step from a random start contracted at most at 0.81 (bound rho = 0.81 in that game).

## What did not work, honestly

* The flat rule is not better than DIP in solution quality; it is better in information (none about the carriers) and
  cost (a third of DIP's calls, 4% of its wall-clock), and equal to DIP in half of the city runs.
* Damping (optimal constant step, successive averages) helps the convexified rate but not the lumpy cycles, which are
  two-equilibrium cycles, not overshooting.
* The tariff removes the implementation problem but not the selection problem: with the carriers' own dynamics it
  stops at unilateral social optima; with a potential-minimising solver it reproduces E3's social optimum, which is
  DIP's target without DIP's cuts.
* Lot learning from jumps changed the tiny-game outcomes in a handful of instances only; the never-served zones remain a
  blind spot (Lemma 9c).

## Reproduce

```
export OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
ARP_PAR=3 experiments/run_arp_queue.sh London BuenosAires NewDelhi Bombay   # 12 runs, resumable (results/arp_parts/)
python experiments/run_arp.py London --seed 0                              # one run by hand (exact oracle by default)
python experiments/run_arp_tiny.py --n 30                                   # 210 tiny games, exhaustive
python experiments/run_arp_rates.py                                         # contraction constants
python experiments/run_arp.py summary && python experiments/plot_arp.py
python -m pytest -q tests/test_arp.py
```
About 10 minutes for the cities on 3 cores (the carriers' pools are warm after the base equilibrium), 25 minutes for the
tiny games, 3 minutes for the rates.
