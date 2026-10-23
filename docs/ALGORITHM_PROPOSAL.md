# Algorithm Proposal: Imprecise Cournot-Nash Competition of Carriers under Traffic Congestion, and Criterion-Free Toll Implementation by Credal Cuts

Status: design document (v3). It supersedes the hub-capacity coupling in DESIGN.md. The game is now coupled by **price** and **traffic** in each zone. Nothing below is claimed as proved until written out in full. Every theorem is labelled a target and comes with its proof route and its main risk.

## 0. Summary

N carriers compete à la Cournot in each city zone z. Each carrier chooses how many deliveries to serve (q_iz) and which vehicles and routes to deploy. Two aggregates couple the carriers. (a) The **revenue per delivery** P_z(Q_z) falls with the total quantity Q_z. (b) **Traffic**: arc times in zone z are base · xi_z · g_z(n_z), where g_z rises with the total vehicle density n_z. Each vehicle therefore completes fewer stops per hour, and serving the same volume takes more vehicles. Underneath every quantity choice is an NP-hard routing problem. Carriers hold **credal sets** on two layers: over the exogenous traffic factor xi (data-driven: p-boxes or the imprecise Dirichlet model, IDM) and over their rivals' aggregates (Q_{-i}, n_{-i}). The city has per-zone instruments: a congestion charge on vehicle exposure, a per-delivery charge or subsidy, or a quota. The result is a set-valued **imprecise Cournot-Nash equilibrium (ICNE)**.

The proposed method is **Credal Cut Implementation (CCI)**, an ellipsoid mechanism in the low-dimensional instrument space. In each round it queries carriers only at the **extreme points of their credal sets**. It ends in one of two ways: (i) instruments under which a target profile is optimal for every belief in every carrier's credal set, and hence an equilibrium under Gamma-maximin, maximality, E-admissibility and interval dominance alike; or (ii) a checkable certificate that no such instruments exist. The number of rounds is polynomial in the number of instruments and does not depend on the exponential plan space. The city never sees costs, routes, data or credal sets.

A companion exact procedure, the **Aggregate-Lattice Equilibrium Hull (ALEH)**, computes the full ICNE set, the interval of equilibrium aggregates and the interval-valued price of anarchy (PoA) on small instances.

## 1. Model

**Strategies.** Carrier i has a depot, a candidate customer set S_i partitioned by zone, a fleet with capacity Q and shift length T_max, and per-vehicle cost f. A plan pi_i consists of the customers it serves (giving q_iz) and capacitated routes (giving k_iz, the vehicles active in z, and tau_iz, the free-flow vehicle-hours in z). Its **signature** is sigma_i = (q_i, k_i, tau_i) in R^{3Z}.

**Traffic.** The travel time of an arc in zone z is t_arc · xi_z · g_z(n_z), with g_z increasing. Two density definitions are carried along because they behave differently:
- **D1 (exposure):** n_z = sum_j tau_jz, the vehicle-hours in the zone.
- **D2 (count):** n_z = sum_j k_jz, the number of vehicles.

**Payoff.** pi_i ↦ sum_z [P_z(Q_z) - s_z] q_iz - f·sum_z k_iz - t·(k_i or tau_i) - Cost_i(pi_i; xi, n). Here Cost_i = sum_r [gamma T_r + rho (T_r - T_max)^+] and T_r = sum_z tau_rz xi_z g_z(n_z). The city's instruments are a congestion charge t_z and a per-delivery charge s_z (negative s_z is a subsidy). Both enter linearly, through the low-dimensional vectors k_i (or tau_i) and q_i. Welfare W = sum_z ∫_0^{Q_z} P_z - total true expected cost; transfers cancel.

**Two regimes.**
- **R1 (affine):** P_z(Q) = a_z - b_z Q, g_z affine, rho = 0, and density D1. The payoff then depends on the plan only through sigma_i, and it is affine in (Q_{-i}, n_{-i}) and in E[xi].
- **R2 (general):** shift penalty, BPR-type g, or density D2.

**Layer 1: credal set over the exogenous factor xi (data-driven).** There are two constructions. (i) Per-zone DKW/Kolmogorov-Smirnov p-boxes [F̂ ± e_n], with e_n = sqrt(ln(2Z/beta)/2n), on a physical support [0, xi_max], and unknown dependence across zones. (ii) An IDM over the n observed daily scenario vectors with parameter s. Its extreme points put mass s/(n+s) on a single scenario. The upper prevision is (sum_b V_b + s·max_b V_b)/(n+s), a sorted-sum Choquet integral of a 2-monotone capacity. A Wasserstein ball is admissible but is only one more construction.

**Lemma 1 (exogenous layer stays tractable).** (a) Under p-boxes with unknown dependence, for every *fixed* plan, the upper prevision equals the expectation under one plan-independent measure P*. P* is the comonotone coupling of the stochastically largest marginals. The reason is that the plan cost is increasing and supermodular in xi, being a sum of increasing convex functions of nonnegative linear forms (Lorentz/Tchen; Puccetti-Rüschendorf). (b) Under the IDM, the upper prevision is the closed-form Choquet sum above. In both cases the best-response oracle remains a scenario-CVRP, and with probability >= 1-beta the upper prevision bounds the true expected cost of every plan at once. This part is known in risk aggregation and is used here, not claimed.

**Layer 2: credal set over rivals.** Carrier i holds a finitely generated credal set M_i over rival states omega = (Q_{-i}, n_{-i}). Examples are probability intervals or the IDM built on past observed aggregates, or a box of means [w - delta_i, w + delta_i] around the realised rival state (consistent beliefs in the sense of Lo 1996). In R1 only the mean of omega matters, so M_i reduces to a box with 2^{2Z} corners.

**Decision criteria and ICNE.** For a criterion C in {Gamma-maximin, maximality, E-admissibility, interval dominance}, a profile is an ICNE_C(delta) if each pi_i is C-admissible against M_i(delta). These sets are nested in the usual way: Nash ⊆ E ⊆ maximal ⊆ interval-dominance, and Gamma ⊆ maximal. All of them grow with delta. The natural outputs are the **interval of equilibrium aggregates** [Q̲_z, Q̄_z] × [n̲_z, n̄_z] and the interval-valued PoA/PoS (minimum and maximum welfare over the ICNE set).

**Structure.**
- (S1) *Existence in R1.* Linear-demand Cournot is an exact potential game (Monderer-Shapley 1996), and so is weighted affine congestion with exposure density (Fotakis-Kontogiannis-Spirakis 2005). Their sum is an exact potential game over the finite plan set, so a **pure ICNE exists despite the nonconvex, NP-hard V_i**. Under Gamma-maximin on rivals the worst case is the corner (high Q_{-i}, high n_{-i}). This adds private linear surcharges b_z·delta^Q·q_iz + gamma·xi̅_z·c1_z·delta^n·tau_iz to each carrier's cost, so the potential is preserved. In other words, ambiguity about rivals acts as a **self-imposed quantity tax and congestion charge** (target theorem T-S1: Gamma-ICNE aggregates are weakly lower than Nash aggregates when Z = 1).
- (S2) *R2 can fail to have a pure equilibrium.* With count density D2, the cost weight is tau_i but the congestion counts k_j, so the game is player-specific and not a potential game, and pure Nash equilibria may not exist. Because ICNE_E(delta) grows with delta, the **minimal imprecision delta\* that makes ICNE non-empty** is a well-defined instability index. It can be computed by ALEH.
- (S3) *Mixed monotonicity.* Quantities are strategic substitutes, because higher Q_{-i} lowers price. Fleets are plausibly strategic complements, because higher n_{-i} slows traffic, lowers throughput and so requires more vehicles: a **fleet arms race**. The game is therefore not supermodular, and lattice methods do not apply. Whether the congestion charge removes the complementarity is an empirical question (target T-S3).
- (S4) *Two wedges, one instrument is not enough.* Cournot withholding means Q is too low, while the congestion externality means n is too high. A congestion charge alone lowers n but also lowers Q (Buchanan 1969). Hence both instruments (t, s) are used, and with heterogeneous carriers even these are uniform, so they are second-best.

## 2. Hard problems

**P1 (Equilibrium hull).** *Input:* plan oracles, instruments (t, s), credal widths delta, criterion C. *Output:* the ICNE_C set, the aggregate interval, and the minimum and maximum welfare over it, which gives the PoA/PoS interval. *Why existing methods fail:* best-response dynamics finds one equilibrium (in R1) or may cycle (in R2), so a "worst found NE" is not a PoA. E-admissibility is an existential condition over a continuum of beliefs combined with a universal condition over exponentially many plans. Joint enumeration of plan profiles is doubly exponential.

**P2 (Criterion-free robust implementation).** *Input:* a target plan profile π̂ (for example the best welfare profile found), an instrument box Θ ⊂ R^{d} with d = Z or 2Z, and query access to each carrier's best response under a given belief. Costs, routes, data, credal sets and criteria are not observed. *Output:* θ = (t, s) in Θ such that every π̂_i is optimal for every P in M_i, or a certificate that none exists. *Why hard:* this is a bilevel problem with NP-hard followers, semi-infinite over beliefs, with follower objectives unknown to the leader. Bilevel MILP and value-function methods need the follower model explicitly. Grid search costs (1/eps)^d equilibrium computations and cannot certify infeasibility.

**P3 (Second-best instruments).** max over θ of the minimum welfare over ICNE_C(delta, θ). This is a pessimistic Stackelberg problem over a set-valued equilibrium. It is attacked with P2 (instruments for candidate targets) and P1 (worst equilibrium at those instruments), and is exact only on small instances.

## 3. Key lemma

**Lemma 2 (vertex reduction).** Fix i, θ and a target plan π̂_i. Let R_i(P) = max_pi E_P[payoff_i(pi)] - E_P[payoff_i(π̂_i)] for P in M_i. R_i is convex in P: a maximum of linear functions minus a linear function. So π̂_i is optimal for all P in M_i if and only if it is optimal at every extreme point of M_i. *Proof:* a convex function attains its maximum over a polytope at a vertex. ∎

Consequences:
- (i) Optimality for every belief implies C-admissibility for all four criteria. The leader therefore needs no assumption about which criterion carriers use.
- (ii) Lemma 2 needs **plan-level targets** in R2. In R1, signature-level targets suffice, because the payoff depends on the plan only through sigma. With quantity-only targets in R2, the target's own value is a minimum over plans, the regret is a difference of concave functions, and the lemma fails. This is an honest limitation.
- (iii) **Instrument linearity:** for each deviation pi, the condition "π̂_i is weakly better than pi at extreme point P" reads (σ̂_i - σ_pi)_{instr}·θ <= c_i(pi, P), where the left-hand vector is (k or tau, q) and c_i is a constant. The **implementable set Π(π̂) is a polyhedron in R^d**. In R1 its facets are indexed by signatures, so there are finitely many.

## 4. Candidate algorithms

### A. Credal Cut Implementation (CCI), recommended

**Mechanism.** CCI runs the central-cut ellipsoid method in instrument space R^d. At the centre θ^t, for each carrier and each extreme point P of M_i, the carrier answers one question: "at instruments θ^t and belief P, is there a plan better than π̂_i by more than eps? If so, report its instrument-relevant vector (k or tau, q)." The leader adds the cut (σ̂_i - σ_v)_{instr}·(θ - θ^t) >= 0, oriented so that θ^t lies on the infeasible side. The cut is valid without knowing any cost, because every point of Π(π̂) weakly prefers the target and θ^t does not. What makes this more than toll learning is that the queries are posed at **credal extreme points** (Lemma 2), which gives robustness to the carriers' beliefs and independence from their decision criteria, with atomic NP-hard followers and two coupled aggregates.

```
CCI(π̂, Θ, {M_i}, eps):
  E <- ball containing Θ; cuts <- []
  loop
    θ <- centre(E)
    if θ ∉ Θ: box cut; continue
    violated <- none
    for i = 1..N, for P in ext(M_i):            # 2^{2Z} corners in R1; IDM vertices in R2
        v <- BestResponse_i(θ, P)               # carrier's own scenario-CVRP (Lemma 1 inside)
        if gain_i(v vs π̂_i | θ, P) > eps: violated <- (i, P, v); break
    if violated is none: return IMPLEMENTS(θ)
    E <- update(E, halfspace from violated); cuts.append(violated)
    if vol(E) < vol(ball(eps / 2D)): return CERTIFICATE(cuts)
```

**Full-information variant (simulation and evaluation).** If carriers also report payoffs, the cuts become deep cuts. The LP max {m : cuts with margin m} then gives the **implementation gap** eps*(π̂) = min_θ max_{i,P} R_i(P; θ). With an exact oracle it terminates finitely in R1, because signatures are finite.

**Target theorems.**
- *T-A1 (query complexity).* Suppose some θ* has zero robust regret and the ball of radius eps/(2D) around it lies inside Θ, where D bounds the instrument-relevant differences ||σ̂_i - σ_v||. Then CCI returns an eps-robust implementation within O(d^2 log(R_Θ D / eps)) rounds, each with at most sum_i |ext(M_i)| oracle calls. *Route:* every point of that ball has regret at most eps/2 under all cuts, combined with the ellipsoid volume-reduction argument, as in Bhaskar et al. (2019).
- *T-A2 (criterion-free equilibrium).* Under the output θ, π̂ is an ICNE_C for all four criteria and a Nash equilibrium for every rival state in the support of M_i. *Route:* Lemma 2.
- *T-A3 (soundness with heuristic oracles).* Each cut is generated by a plan that really is better than the target, because the carrier's gain compares two concrete plans. A CERTIFICATE is therefore exact even when the oracle is heuristic. IMPLEMENTS holds only relative to the oracle, and on small instances it is re-checked with an exact oracle.
- *T-A4 (information).* The city observes only instrument-relevant vectors (vehicles or vehicle-hours, and deliveries per zone).

**Complexity.** The total number of oracle calls is O(N |ext| d^2 log(1/eps)). For Z = 2 in R1, d = 4 and |ext| = 16.

**Closest prior art and what is new.**
- Bhaskar, Ligett, Schulman & Swamy (FOCS 2014; GEB 2019): ellipsoid tolls that induce a target flow from equilibrium queries in **nonatomic** routing games. The ellipsoid-plus-queries mechanism is theirs.
- New here: atomic Cournot competitors whose strategies are NP-hard routing plans; two coupled aggregates (price and traffic) and two instruments; queries at credal extreme points, which give implementation that is robust and criterion-free; certificates of non-implementability as a first-class output, since non-implementability is generic here (S4, discreteness, uniform instruments).
- Atomic toll implementability (Fotakis-Spirakis 2008; Harks-Kleinert-Klimm-Möhring 2015; Paccagnan et al. 2019; Stoll 2021) assumes resource-based strategies, full information and no ambiguity.
- Cournot under ambiguity (Radi-Gardini 2023; Schlag-Zapechelnyuk; the Bonn and Heidelberg working papers) has no routing, no congestion and no implementation.
- Imprecise-probability solution concepts (Liu: E- and maximality rationalizability; Dow-Werlang; Eichberger-Kelsey; Klibanoff; Lo) are not computational and use small matrix games.
- No work was found that combines credal sets or p-boxes with vehicle routing; the only related routing work uses belief functions or fuzzy times. No ambiguity-averse equilibrium in congestion or routing games was found either. Novelty is claimed only for the combination listed, not for the ellipsoid idea or Lemma 1.

### B. Aggregate-Lattice Equilibrium Hull (ALEH), exact companion for P1

**Mechanism.** The game is aggregative: carrier i's admissibility depends on the others only through omega = (Q, n) minus its own contribution. For each candidate aggregate (Q, n) on a lattice Lambda (integer Q; n integer under D2, discretised under D1), compute A_i(Q, n), the signatures of carrier i that are C-admissible against M_i(omega_{-i}). E-admissibility is an LP in P ("there exists P in M_i under which σ is optimal against all known σ'"), and maximality and interval dominance are LP or sorting checks. An aggregate (Q, n) is in equilibrium if and only if it lies in A_1 ⊕ ... ⊕ A_N. This is checked by a dynamic program over carriers on partial aggregates, which also carries the minimum and maximum welfare. Signatures are generated lazily with an exact small-CVRP oracle and pruned using Lagrangian bounds.

**Target theorem T-B1.** Given all signatures, ALEH outputs ICNE_C, the aggregate interval, the exact PoA/PoS interval and delta\* (S2) with O(N |Lambda|^2 max_i |Σ_i|) arithmetic and LP work. This is polynomial for fixed Z and bounded quantities.

**Prior art.** Soundy, Irfan & Chan (UAI 2025) compute pure Nash equilibria in additive aggregate games with a bounded aggregate space, so the aggregate dynamic program is not new. New: E-admissible and maximal equilibria via LPs in belief space, with private costs given by routing value functions. **Role:** an exact baseline and the source of PoA intervals. It is limited to tiny instances (N <= 3, Z = 2, |S_i| <= 7).

### C. Credal fictitious play with the IDM (not recommended)

Carriers update IDM credal sets on rival aggregates (width s/(t+s)) and play Gamma-maximin replies. In R1 each stage is a potential game with vanishing surcharges, so convergence is plausible; in R2 it may cycle. **Prior art:** Quaeghebeur & De Cooman (ISIPTA 2003) already study IDM-based learning in games. The marginal novelty is thin and the convergence risk is high.

## 5. Recommendation: CCI, verified by ALEH

**Why CCI.** It is one mechanism with its own guarantees (T-A1 to T-A4), and it uses each part of the setting: the Cournot and aggregative interface (low-dimensional linear instruments), imprecise probabilities (vertex reduction, criterion-free implementation, data-driven credal sets), NP-hard followers (oracle-only access), and a leader with limited information (it sees signatures only).

**Risks and fallbacks.**
1. *Exact robust implementation may usually be infeasible*, because of the two wedges, uniform instruments and discreteness. Fallback: report eps*(π̂) and run CCI on the eps-relaxed set. The second-best loop ranks targets from the welfare-search pool and returns the best one that is implementable. Low implementability is then a policy finding in itself.
2. *R2 needs plan-level targets* (Lemma 2(ii)). These are well defined analytically, since the city computes target plans in simulation, but they are stronger than needed. Fallback: state the R2 results for plan targets and give the main results in R1.
3. *Weak implementation.* Other equilibria may exist at θ. ALEH reports the worst ICNE and the PoA interval.
4. *Many extreme points* (2^{2Z}). Fallback: query the most-violated vertex first and check all vertices only before returning IMPLEMENTS. Correctness is unaffected; only the round cost changes.
5. *Novelty attack ("this is Bhaskar et al.").* Lemma 2 with criterion-free implementation, atomic NP-hard Cournot followers, and the certificates have to carry the paper, and the text says so openly.

**Minimal implementable v1** (R1, Z = 2, about 300 lines). It reuses the small CVRP heuristic and exact enumeration for small n.
- Extend the instance to zone demand curves (a_z, b_z), a congestion function g_z, and plan signatures (q, k, tau) with optional customers (prize-collecting).
- `credal.py`: DKW p-box and IDM over xi, and the upper prevision (Lemma 1); rival-state boxes and their corners.
- `implement.py`: the central-cut ellipsoid in R^4 (t, s) with box cuts, a query wrapper calling the best response at (θ, corner), the IMPLEMENTS/CERTIFICATE outcome, and an LP for eps*(π̂) (scipy `linprog`).
- `hull.py`: ALEH with full signature tables on tiny instances.

**Validation plan.**
- *Correctness, with exact baselines on N = 2-3, Z = 2, |S_i| <= 7:*
  - Enumerate every plan and solve Π(π̂) exactly by LP. Check that CCI's verdict agrees on 100+ random (instance, target, delta, s) cases.
  - Verify Lemma 2 against a dense grid of beliefs.
  - Verify ALEH's ICNE sets by enumerating profiles.
  - Verify the potential function (S1) numerically in R1 and look for best-response cycles in R2.
  - Check the IDM and p-box upper previsions by LP over the credal set.
- *Value over the v1 stack (best-response dynamics with a grid or Nelder-Mead leader):*
  1. VRP oracle calls needed to reach eps-implementation, CCI against a grid as eps shrinks and d grows (2 to 6).
  2. The share of grid instruments that look implementing at realised aggregates but fail at a credal vertex, which v1 cannot detect.
  3. The certified non-implementability rate and eps*(π̂) for the welfare-optimal target, with the charge only versus charge plus subsidy (S4), as a function of delta, sample size n and IDM s.
  4. Exact PoA/PoS intervals and aggregate intervals from ALEH, compared with v1's "worst found NE".
  5. delta\* and the frequency of fleet arms races under D2.
  6. Out-of-sample coverage of the upper prevision against 1-beta.

## Sources consulted for novelty checks

- [Bhaskar, Ligett, Schulman, Swamy, Achieving target equilibria in network routing games without knowing the latency functions](https://ar5iv.arxiv.org/html/1408.1429)
- [Harks, Kleinert, Klimm, Möhring, Computing network tolls with support constraints](https://page.math.tu-berlin.de/~moehring/adm3/adm3-2015/ComputingNetworkTolls.pdf)
- [Paccagnan et al., Optimal taxes in atomic congestion games](https://arxiv.org/pdf/1911.09806)
- [Stoll, Tolls for atomic congestion games](https://uwspace.uwaterloo.ca/handle/10012/16835)
- [Fotakis, Spirakis, Cost-balancing tolls for atomic network congestion games](https://projecteuclid.org/euclid.im/1265033169)
- [Soundy, Irfan, Chan, Pure and strong Nash equilibrium computation in compactly representable aggregate games](https://proceedings.mlr.press/v286/soundy25a.html)
- [Quaeghebeur, De Cooman, Learning in games using the imprecise Dirichlet model](https://isipta03.sipta.org/proc/papers/034.pdf)
- [Liu, Rationalizability with imprecise probabilities](https://studiesinlogic.sysu.edu.cn/en/node/112)
- [Radi, Gardini, Ambiguity aversion as a route to randomness in a duopoly game](https://arxiv.org/pdf/2311.11366)
- [Schlag, Zapechelnyuk, Compromise, don't optimize](https://ar5iv.labs.arxiv.org/html/2003.02539)
- [Bonn working paper on pessimism in Cournot oligopoly](https://www.wiwi.uni-bonn.de/bgsepapers/old%20series/bonedp/bgse23_2003.pdf)
- [Extremal dependence concepts (supermodular/comonotone bounds)](https://arxiv.org/pdf/1512.03232)
- [Routing in an uncertain world (risk-averse equilibria)](https://arxiv.org/pdf/2201.02985)
- [Robust scenario approach for VRP with uncertain travel times](https://pubsonline.informs.org/doi/fpi/10.1287/trsc.2013.0476)
- [VRPTW with evidential travel times](https://www.cepadues.com/nos-articles/950/)
