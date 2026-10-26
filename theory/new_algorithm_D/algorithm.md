# ARP: aggregate-response pricing

The city's zone charges from observed zone aggregates alone. Problem, method, theory pointers, prior art and limits.
Proofs: `theory.tex` (pdf alongside). Numbers: `results.md`. Code: `src/ccu/arp.py`, tests `tests/test_arp.py`,
experiments `experiments/run_arp.py` (cities), `run_arp_tiny.py` (exhaustive tiny games), `run_arp_rates.py`
(contraction constants), `plot_arp.py`.

## Problem

The city of the D1 Cournot-congestion game (`theory/main.tex`; `src/ccu/zmc_brl.py`) sets per-delivery and congestion
charges for N = 4..6 carriers whose plans come from an NP-hard robust routing oracle (BRL branch-and-price). The project's
leader methods need the carriers' private information: the 63-point grid solves 63 equilibria with the carriers' oracle,
DIP (`theory/new_algorithm_C`) computes the social optimum with the carriers' oracle and then runs best-response cuts
with it. A real city cannot run the carriers' routing problems. It can post charges and observe what the market does:
per zone, the deliveries Q_z and the number n_z of active carriers.

ARP asks: how much of the leader's gain is reachable from (Q_z, n_z) alone, with what guarantee, and in how many rounds?

## The method in ten lines

    Flat rule (ARP), the city posts a per-delivery-equivalent charge u in R^Z and observes the equilibrium aggregates
      1  u <- 0 ;  observe (Q, n) of the unpriced equilibrium
      2  repeat
      3     dbar_z <- mean lot learned in z (Q_z when n_z = 1; |jump of Q_z| when n_z changes by one), else Q_z / n_z,
               else the city-wide mean observed lot                                           (Lemma 9)
      4     u_z <- (1 - theta_z) u_z + theta_z [ kappa_z Q_z - (m_z / 2) dbar_z ]          (theta = 1 plain; 2m/(2m+kappa) damped)
      5     post u (uniform per-delivery charge min_z u_z plus zone congestion charges (u_z - min u)/r, as in DIP)
      6     carriers best-respond day to day from their current plans until nobody moves; observe (Q, n)
      7  until u = kappa Q - (m/2) dbar (fixed point), or the posted charge and the market state repeat (cycle)
    Marginal tariff (ARP-M), the limit of re-tangenting at every transaction, no iteration
      8  bill carrier i in zone z:  T_z(q_i, Q) = kappa_z q_i (Q_z - q_i) - (b_z / 2) q_i^2   (own deliveries, zone total)
      9  the carriers' game then has the social cost as exact potential: every social optimum is an equilibrium and the
            carriers' own best responses from the status quo never raise the social cost                 (Theorem 8)
     10 optional: the potential-minimising solver of E3 (ZMC on the social-cost potential) gives the DIP target, which
            under the tariff is an equilibrium without any implementation step

kappa_z = g_z r^2 (congestion slope in delivery units), m_z = b_z + kappa_z; both are city parameters.

## The theory in one paragraph

Convexify the carriers' plan sets. The equilibrium aggregate under the charge u is the proximal map of the carriers'
aggregate value function: Q(u) = argmin_Q F(Q) + <u, Q> = grad F*(-u), with F strongly convex (Theorem 1). The city's
problem min SC-bar is the Fenchel dual problem min_u D(u) = F*(-u) + g*(u), whose gradient (u + m dbar/2)/kappa - Q(u)
is exactly what the city observes (Theorem 2). Line 4 is gradient descent on D in the kappa^{-1}-metric: the plain step
contracts at ratio rho = max_z kappa_z/(b_z + kappa_z) < 1, the damped step 2/(2+rho) at ratio rho/(2+rho) (Theorem 3);
the ratios depend on nothing but rho, not on Z, N, lots, routing costs or p-boxes. The fixed point is the exact
minimiser of SC-bar plus DIP's lot-asymmetry term (zero for symmetric lots). In the pure game, every fixed point is a
unilateral social optimum up to lot asymmetry (Theorem 4), the iteration stays within sup ||e^t||_kappa/(1-rho) of the
convexified fixed point, e^t the lumpiness of the observed equilibrium (Theorem 5), and the response map identifies F up
to a constant, so the convexified optimum is all that any observation-only scheme can target (Theorem 6, with an example
where the pure optimum is not identified). A Gamma-maximin surcharge of the carriers only shifts the fixed point and
needs no knowledge of delta (Proposition 7); under E-admissibility of width delta a pure target is implemented exactly
once the charge is within the surcharge band of an implementing charge, after at most log(.)/log(1/rho) rounds
(Proposition 8). Under the marginal tariff the social cost is the exact potential (Theorem 8).

## Why it is not DIP, and what it costs

DIP: oracle access, a computed target, cutting planes; implements the target exactly; 100-220 oracle calls per city.
ARP: no oracle, no target, no lots, no plans; the carriers do the computing; 20-70 of their oracle calls (two to seven
posted charges) for the flat rule and 8-14 for the tariff; the fixed point is a convexified optimum up to lot asymmetry
and the pure equilibrium the carriers select. On the city games ARP reaches 91-293% of the grid's gain (DIP: 104-325%),
equal to DIP in 5 of 12 runs; the marginal tariff with the carriers' own best responses reaches 99-293% with about ten
calls, and with the E3 solver it reproduces DIP's target. In adversarial tiny games (exhaustive enumeration) the flat
rule cycles or lands in a worse local optimum in about one instance in six, which DIP, with the oracle, avoids.

## Closest prior art and novelty verdict

| item | status |
|---|---|
| Charge the externality at the observed state and iterate (trial-and-error marginal-cost pricing): Yang, Meng, Lee TR-B 2004; Han, Yang 2008; Ye, Yang, Tan TR-B 2015; Xu, Meng, Huang TR-C 2016; Zhou et al. 2015 | **known** (nonatomic, MSA, no rate) |
| Adaptive incentive design, two time scales, atomic Cournot with continuous strategies, fixed points socially optimal: Maheshwari, Kulkarni, Wu, Sastry 2022 (arXiv 2204.05507), 2024 (2405.16716); Kulkarni's thesis 2022 | **known** (closest neighbour of the principle) |
| Learning optimal taxes from equilibrium feedback, nonatomic congestion: Cui, Fazel, Du NeurIPS 2024 | known |
| Linear convergence of projection descent in Stackelberg aggregative games under strong monotonicity: Li, Li, Li, Chen IEEE TAC 2025 | known, continuous strategies, leader knows responses |
| Marginal-contribution tariffs, welfare as potential: Wolpert-Tumer 1999; Sandholm REStud 2002, JET 2007; Marden-Wierman 2013; "The game of marginal utilities" arXiv 2608.10373 | **known** |
| Pigou-Cournot corrective tax with market-power subsidy: Buchanan 1969, Barnett 1980 | known |
| Response map = proximal map of the aggregate value function; leader's dual with observable gradient; instance-free ratios rho and rho/(2+rho) in a lumpy routing game | new as far as found |
| Fixed-point unilateral social optimality up to lot asymmetry; neighbourhood bound through the rounding gap; identification limit with example | new as far as found |
| Credal absorption of the leader's search error (E-admissibility); surcharge shift of the fixed point | new as far as found |
| Lumpy form of the marginal tariff and the observation that it makes DIP's implementation step unnecessary | new in this project; the mechanism is classical |

**Verdict: incremental.** The central step (set the charge to the externality at the observed aggregate) is classical
and its atomic-Cournot version exists (Maheshwari et al.). What is new is the theory in the lumpy, NP-hard, credal
setting: the proximal identity and the dimension-free, instance-free rates, the fixed-point and identification results
and the credal absorption. The author's usefulness test is met in the sense of information and cost (no oracle, a
fifth of DIP's calls, a tenth to a fiftieth of its wall-clock), not in the sense of solution quality, where DIP with
the oracle remains better in the adversarial cases.

Queries run (2026-10-26, web search, snippet level; abstracts of 2204.05507, 2110.08879, 2512.17157 fetched):
"trial-and-error marginal cost pricing Yang Meng Lee convergence Lagrangian dual subgradient observed link flows";
"iterative Pigouvian tax Cournot oligopoly regulator observes aggregate output only convergence contraction";
"adaptive congestion pricing atomic players aggregative game unknown costs feedback toll update converges social optimum";
"trial-and-error congestion pricing linear convergence rate strongly convex dual equilibrium response proximal map";
"Sandholm evolutionary implementation congestion pricing potential equals welfare dynamic Pigouvian pricing atomic";
"regulator learns Pigouvian tax from observed equilibrium quantity proximal resolvent convex conjugate aggregative game";
"trial-and-error toll discrete strategies integer players step function response cycle fixed point lumpy";
"incentive design aggregative games two time-scale tolls best response integer nonconvex strategy sets Cournot learning";
"pessimistic Stackelberg toll design worst-case equilibrium atomic congestion game integer programming";
"equilibrium response map proximal resolvent Fenchel dual leader Stackelberg aggregative game tax observed aggregate";
"Pigouvian tax iteration Cournot oligopoly fixed point tax equals marginal damage at observed output contraction rate";
"marginal contribution pricing potential game welfare potential atomic Cournot congestion all-or-nothing discrete".
Absence of hits is weak evidence; a Scopus/Web of Science pass is still needed before any submission.

## Candidates killed on the way (stage 1 of the mandate)

1. Scale by budget discretisation of the BRL labels (FPTAS-type): known technique (Hassin 1992), and the scale
   bottleneck of the project is the integer master, not the pricing.
2. Scale by zone/sector decomposition with BRL subproblems: cluster-first region partitioning (Haimovich-Rinnooy Kan
   1985) and split-delivery direct-load decompositions (Dror-Trudeau; Archetti et al.) are known.
3. Parametric labelling in the imprecision width: for Gamma-maximin the surcharge is linear in the node prices
   (bi-criteria/parametric ESPPRC, known); for the DKW width the route cost is concave in epsilon with an explicit
   derivative, but the family computation is a parametric analysis, which the referee report rejected for CTS.
4. Credal-inertia best-response dynamics with a switch-count bound: epsilon-Nash dynamics (Chien-Sinclair) in disguise.
5. Exact joint branch-and-price for the pure social optimum (subset convexification of the lumpy aggregate plus BRL
   pricing): an assembly of Dantzig-Wolfe, Meyer's integer representation and B&P; stronger but not new.
6. Pessimistic (worst-equilibrium) charge design: PoA-optimal tolls (Paccagnan et al.) and cost-balancing tolls
   (Fotakis-Spirakis) cover the principle; the exact bilevel is a heavy MIP without new theory.
7. Observation-only charges (this document): principle known, theory new; kept as the strongest true result.

## Limits

- Equilibrium selection: the carriers choose the pure equilibrium; all guarantees for the pure game are conditional
  (fixed point reached; potential-minimising selection for Theorem 5). The flat rule can cycle (lumpy response) and can
  settle in a worse local optimum than the status quo (3 of 210 tiny games); the tariff cannot.
- Unserved zones give no lot information; the subsidy there is a guess bounded by E (Theorem 2(c)).
- The tariff requires billing on own deliveries and the zone total (ex post, per day); its net cost to the city is
  comparable to DIP's subsidy.
- The convexified theory needs D1, one hours-per-delivery ratio, affine demand, linear congestion (as DIP).
- No worst-equilibrium guarantee: under the tariff every equilibrium is a unilateral social optimum, which can still be
  far from the optimum (tiny games: worst-equilibrium share -4.5 on average).
