# Design: Regulator-Led Stackelberg Game among Competing Carriers with Wasserstein-Robust Routing

Target: Omega 55th Anniversary Special Issue, *Data-Driven Optimization for Smart Cities*
(topics: DRO, learning-augmented optimization, last-mile routing, public-private coordination).

## 1. Research question

When N carriers share scarce urban micro-hub capacity and each routes under travel-time
ambiguity estimated from its own data, how much efficiency is lost at equilibrium, how much
of it can a city recover with a posted hub price, and how does the carriers' ambiguity
radius change both answers?

Gaps addressed (survey Section 8.2): G1 (routing-level equilibrium under stochasticity),
G2 (Stackelberg leader above interacting followers), G4 (efficiency bounds for tour-based
games), G5 (data-driven robustness in a game), G6 (multi-carrier instances, exploitability).

## 2. Model (v1)

**Players.** Leader (city) and carriers i = 1..N. Carrier i has a depot, a customer set
S_i (each customer j has demand 1 parcel), and a homogeneous fleet of capacity Q.

**Hubs.** Zones z = 1..Z with capacity scale C_z. Customer j has a nearest hub z(j).

**Carrier plan pi_i = (D_i, R_i).**
- D_i subset of S_i: parcels diverted to hubs (customer collects). Diverted parcel j costs
  the carrier a_ij = eta * dist(depot_i, hub z(j)) (amortised bulk line-haul) plus
  theta * dist(j, z(j)) (customer inconvenience compensation).
- R_i: a CVRP solution (routes with load <= Q) serving S_i minus D_i by doorstep delivery.
- Hub usage u_iz = |{j in D_i : z(j) = z}|; load L_z = sum_i u_iz.

**Travel-time uncertainty.** The city is divided into K sectors. Travel time of an arc in
sector k is t_arc * xi_k, with xi in R^K a congestion multiplier vector. Carrier i has S_i^data
samples xi^1..xi^S (empirical distribution P_i). For route r let tau_rk be its base travel
time spent in sector k (arc assigned to the sector of its midpoint) plus service time.
Route duration is T_r(xi) = sum_k tau_rk xi_k.

**Route loss.** l_r(xi) = f + gamma * T_r(xi) + rho * max(0, T_r(xi) - T_max)
(fixed vehicle cost, driving cost, lateness/overtime penalty past shift length T_max).
Convex, piecewise linear in xi.

**Ambiguity.** Carrier i hedges against the type-1 Wasserstein ball of radius eps_i around
P_i with ground norm ||.||_1 on R^K. For convex piecewise-linear losses and support R^K
(Mohajerin Esfahani & Kuhn 2018, Thm 6.3):

    sup_{Q in ball} E_Q[l_r] = E_{P_i}[l_r] + eps_i * (gamma + rho) * max_k tau_rk .

This is a closed-form route cost, so the carrier's best response remains an ordinary
deterministic CVRP-style problem. The support relaxation to R^K makes it conservative.
The sum over routes of a plan gives c_i(pi; eps_i); the Lipschitz term is per route.

**Congestion externality.** A parcel at hub z is processed with delay proportional to the
hub's load. Carrier i's cost for plan pi_i given others' plans:

    J_i(pi_i, pi_-i) = c_i(pi_i; eps_i) + sum_j in D_i a_ij
                       + sum_z [ p_z * u_iz + (beta_z / C_z) * u_iz * L_z ] .

p_z >= 0 is the leader's posted hub price (zone-specific, per parcel).

## 3. Game, equilibrium, leader

**Follower game (given p).** Finite game with cost J_i. It is an **exact potential game**:

    Phi(pi) = sum_i [c_i + sum_j a_ij + p.u_i] + sum_z (beta_z / (2 C_z)) (L_z^2 + sum_i u_iz^2)

(verified algebraically: switching u -> u' changes J_i and Phi by the same
(u'-u)(L+u') term). Consequences: best-response dynamics with exact best responses converge
to a pure Nash equilibrium; with heuristic best responses we obtain an eps-Nash equilibrium
and report **exploitability** (NashConv) = sum_i [J_i(pi) - min_pi_i' J_i(pi_i', pi_-i)],
the minimum being taken over the best response found, so it is a lower bound on true
exploitability when the oracle is heuristic (we also compute it with an independent
multi-start oracle).

**Social cost** (true expected cost, evaluated on P_true, not on the ambiguity ball):

    SC(pi) = sum_i [ E_true[ routing loss ] + diversion costs ] + sum_z (beta_z / C_z) L_z^2
             + phi * (total vehicle-time) ,

transfers p.u cancel. phi is a per-time externality (emissions, noise).

**Leader.** min over p in [0, p_max]^Z of SC(NE(p)), a nested problem with Z <= 4 variables,
solved by coordinate/Nelder-Mead search with warm-started best-response dynamics.
With non-uniform carriers the leader does not observe eps_i or costs, only usage and total
cost, so the information structure is realistic.

**Benchmarks.**
1. Unpriced Nash equilibrium (p = 0).
2. Priced Nash equilibrium at the leader's optimum p*.
3. Centralised social optimum over joint plans (best found by potential descent on SC from
   many starts; exact enumeration on tiny instances for validation).
4. Pigouvian price p_z^Pig = (beta_z / C_z) * L_z^*, closed form (marginal external cost).

**Metrics.** Price of anarchy PoA(p) = SC(worst found NE) / SC(optimum);
price of stability from best found NE; exploitability; Gini fairness of carrier cost
relative to stand-alone; out-of-sample disappointment (DR cost minus realised cost on fresh
samples); sensitivity to eps_i, N, capacity tightness, overlap.

## 4. Theory targets (to prove or refute; do not claim before proved)

- **P1 (existence).** Pure Nash equilibrium exists for every p (finite potential game).
- **P2 (PoA bound).** Unpriced game satisfies PoA <= (3+sqrt5)/2 against the social
  optimum. Sketch: weighted affine congestion game with additive player-private costs
  (the private routing/diversion terms enter with coefficient 1 <= lambda in the
  (lambda,mu)-smoothness inequality). To be written carefully.
- **P3 (Pigouvian implementation).** With separable costs and quadratic congestion, the
  posted price p* = (beta/C) L* makes the potential equal to SC up to the sum of u^2
  term, so minimisers of Phi implement near-optimal SC; exact when carriers are atomic
  with unit-size marginal contribution. Quantify the gap.
- **P4 (ambiguity).** Per-route robust cost is increasing and linear in eps; study how
  carrier hedging shifts the diversion volume and the leader's p*. Empirical first.

## 5. Learning layer (Stage 2)

1. Neural / learned warm-start for the best response (diversion mask predictor).
2. Decision-focused learning of the sector congestion distribution from covariates
   (time of day, weather) instead of fitting then optimising.
3. Report exploitability of learned oracles vs exact oracle.

## 6. Data

- Synthetic city generator (v1): Euclidean grid with K sectors, hub locations, carriers'
  depots, customer clouds with controllable market share and spatial overlap, sampled
  sector multipliers (lognormal, common shocks plus sector noise).
- Real-data adapters (v2): Amazon Last Mile Routing Challenge (route stops, zone ids) and
  LaDe (Cainiao pickup/delivery). Customers split among N synthetic carriers by market
  share and overlap parameters. Documented as an instance-generation contribution (G6).

## 7. Repository layout

    src/ccu/instance.py     instance generator, distances, sector assignment
    src/ccu/robust.py       Wasserstein route cost (closed form) and scenario evaluation
    src/ccu/routing.py      CVRP heuristic (savings + local search) under DR cost
    src/ccu/carrier.py      plan, best response with diversion choice, costs J_i
    src/ccu/game.py         best-response dynamics, exploitability, social cost, benchmarks
    src/ccu/leader.py       price search, Pigouvian price
    experiments/            run scripts and result tables/figures
    tests/                  unit tests and brute-force validation on tiny instances
    paper/  survey/         manuscripts
