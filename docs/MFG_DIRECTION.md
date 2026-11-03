# A mean-field direction after the Omega paper: decision memo

Date: 2026-11-03. Status: design memo, followed by execution of the plan (Section 6 below gives the status after execution). Nothing under `paper/`, `theory/`, `src/`, `lean/` or the submission folders was changed. The numerical sanity checks are in `mfg/checks/` (script and output file).

## 0. Recommendation in brief

1. Write one paper on the **many-small-carriers limit** of the Omega game: carriers whose fleet share s tends to 0, on a time-expanded zone graph, with a leader posting zone-time charges.
2. Core theorem to aim at: the aggregate of the finite-N Cournot-congestion equilibrium is within **O(s) = O(1/N)** of the mean-field (Wardrop-type) equilibrium, with an explicit constant, which improves the O(1/sqrt N) of Paccagnan et al. (2019) for this class. The leader's fixed-point charge then converges to the marginal-cost (Pigou) toll at rate O(s/(1-rho)), where rho is the contraction ratio of ARP in the Omega paper.
3. The constant is proved (equal to 1) when carriers' problems separate by zone; with cross-zone coupling it is open. The numerics show ratios up to 1.32, so the one-zone constant does not carry over unchanged.
4. Existence, uniqueness and toll implementation in the mean-field game are largely known (MDP congestion games, Calderone-Sastry 2017; Li et al. 2019, 2023). They go into the paper as lemmas, not as contributions.
5. Target: Transportation Science or Operations Research. Mathematics of OR is realistic only if the cross-zone O(s) constant is proved.

## 1. Is MFG a natural fit here?

**Partly.** It fits the vehicles and couriers. It does not fit the large parcel carriers of the Omega paper, and the memo should say this plainly.

*Where it fits.* Gig couriers, platform drivers and small parcel van operators are numerous. Each is negligible, and they interact only through zone-time aggregates: deliveries Q_{zt}, which set the price, and vehicle-hours X_{zt}, which set the congestion. That is the defining structure of a mean-field game. The coupling in the Omega paper is already aggregative and affine (`paper/main.tex`, eq. (1)). Its D1 regime is an exact potential game, and the nonatomic version of a potential game is a potential MFG.

*Where it does not fit.* (i) In the limit each agent is a price taker, so **the Cournot wedge vanishes**. With N symmetric carriers in one zone, Q^N = N/(N+1) Q^W exactly (check 1). The market-power subsidy term -(m/2) d-bar of the ARP/DIP charge disappears, and the corrective charge becomes the Pigou toll. A few large carriers (3 to 6 in a city) are better modelled as atomic or "major" players. (ii) A single courier's problem is a shortest-path or MDP problem on the zone graph, not an NP-hard multi-stop routing problem. The combinatorial layer of the Omega paper (BRL, branch-and-price) survives only if the mean-field agent is a small carrier with multi-stop tours. (iii) Our data are static: one travel-time matrix and no time-of-day demand (`data/processed/<City>/`: `zones.csv`, `travel_time_matrix.npy`, `major_graph.npz`, `pois.csv`, `meta.json`; between 42 zones for Cairo and 593 for Berlin).

**Proposed model (M).** Zones z in [Z], periods t in [T] (T = 4 to 12 time-of-day slots). Finitely many agent types theta (cargo bike, van, gig car; or a small carrier type), with mass mu_theta. An agent's state is s = (z, t, k), where k is the remaining load. Actions: deliver in z, wait, move to an adjacent zone, or return. Travel between zones takes a random whole number of periods, and its law lies in a p-box estimated from observations, as in the Omega paper. Per-period reward: (alpha_{zt} - b_{zt} Q_{zt} - u_{zt}) per delivery, minus gamma (xi_{zt} + c_{zt} X_{zt}) per vehicle-hour.

- **The mean field** is the vector of occupation measures rho_theta(s, a) of the types, the mass of type-theta agents in state s taking action a. Agents interact only through two linear functionals of it: the zone-time delivery density Q_{zt} and the vehicle-hour density X_{zt}. So the coupling variable is A = (Q, X) in R^d with d = 2ZT. The type distribution mu is exogenous.
- **Control and state.** Discrete time and finite state, as in Gomes-Mohr-Souza (2009 preprint; 2013 for continuous time). The control is a Markov policy on the time-expanded zone graph. Feasible occupation measures form a network-flow polytope, which makes the problem an MDP congestion game (Calderone-Sastry 2017). A continuous-time version on the graph (Gueant 2015; Camilli-Marchi 2016) adds nothing for our data.
- **Equilibrium.** A Wardrop-type MFG equilibrium: each type's occupation measure is optimal against A(rho), and rho reproduces A. Under D1 (congestion on vehicle-hours, exposure equal to contribution), the coupling F(A) = M A with M = diag(b, gamma c) is symmetric and positive semidefinite. So the game is a **potential MFG**: its equilibria maximise Phi(rho) = sum_theta <r_theta, rho_theta> + sum_{zt} [alpha Q - b Q^2/2 - gamma xi X - gamma c X^2/2] - <u, A(rho)> over the flow polytopes. The equilibrium aggregate is unique when b, c > 0. This is Lasry-Lions monotonicity in its discrete form (Gueant 2015 for graphs). Under D2 (congestion on vehicle counts), exposure and contribution differ and monotonicity can fail (Section 3C).
- **Leader.** A Stackelberg MFG with tolls u_{zt}. The social optimum maximises the same functional with gamma c X^2 in place of gamma c X^2/2, so the toll u_{zt} = gamma c_{zt} X^opt_{zt} per vehicle-hour implements it (Beckmann et al. 1956). This is mean-field control by a planner, decentralised by the toll.
- **Imprecise travel times.** Under Gamma-maximin with rectangular p-box sets, each agent solves a robust MDP (Iyengar 2005; Nilim-El Ghaoui 2005), which is a robust MFG (Langner-Neufeld-Park 2024; Liang et al. 2026). In the static Omega model the worst case sat at the upper corner (Lemma "Gamma-maximin surcharge"). **With time-of-day prices this can fail**: arriving later can be better when the price is higher later, so the worst-case law is no longer the upper p-box bound. Under E-admissibility the equilibrium becomes a set, indexed by the width delta.

## 2. Prior-art audit

Search done on 2026-11-03 with web search, arXiv abstract pages and one full text (Paccagnan et al., Section IV). "Read" means the abstract unless stated otherwise.

| Paper | Year | What it does | What remains open for us |
|---|---|---|---|
| Lasry-Lions, Huang-Malhame-Caines | 2006-07 | MFG foundations; monotonicity gives uniqueness | none (background) |
| Gomes-Mohr-Souza, discrete time and continuous time, finite state | 2009-13 | finite-state MFG; N to infinity convergence with a rate (2013) | the rate is for smooth Markov dynamics and does not cover lumpy plans or Cournot coupling |
| Gueant, MFG with congestion on graphs (AMO 72) | 2015 | existence and a uniqueness criterion for congestion on graphs | Cournot price coupling and a leader |
| Camilli-Marchi (SICON 2016); Al Saleh-Bakaryan-Gomes-Ribeiro (Port. Math. 2024) | 2016, 2024 | MFG on networks; first-order network MFG and Wardrop equilibrium | the link from MFG to Wardrop is already made, so we cannot claim it |
| Calderone-Sastry, MDP routing games (ICCPS) | 2017 | nonatomic agents choose MDP policies on a network; Wardrop equilibrium; potential; ride-sharing example | **closest model**: we add elastic (Cournot) demand, atomic carriers, the finite-N rate and imprecision |
| Li, Yu, Calderone, Ratliff, Acikmese (ACC 2019); Li et al. (Automatica 151, 2023) | 2019, 2023 | tolls enforce constraints in MDP congestion games; adaptive tolls with unknown costs; Manhattan Uber data | **closest leader result**: our ARP-in-MFG would be a variant; the new part is the instance-free rate rho and the finite-N toll error |
| Cabannes, Lauriere, Perolat et al., arXiv 2110.11943 | 2021 | N-player dynamic routing with congestion solved by its MFG; accurate beyond a few dozen vehicles (numerical) | no theorem on the N-gap; no prices or tolls |
| Haurie-Marcotte (Networks 15) | 1985 | Nash-Cournot equilibria converge to Wardrop as players split | qualitative; no rate |
| Paccagnan, Gentile, Parise, Kamgarpour, Lygeros (IEEE TAC 64), **full text of Section IV read** | 2019 | Thm 1(3): aggregate gap at most sqrt(2 R L2/(alpha M)), i.e. **O(1/sqrt M)**; convex strategy sets | **an O(1/M) gap with an explicit constant, and lumpy plans** |
| Jacquot-Wan, arXiv 1804.03081 | 2018 | atomic to nonatomic on parallel networks, with rate bounds | form of the rate not read; parallel links only |
| Cominetti, Scarsini, Schroder, Stier-Moses (MOR 48) | 2023 | unsplittable atomic games converge to Wardrop (mixed equilibria, Poisson limit); PoA convergence | random or mixed play; our object is pure lumpy plans with Cournot prices |
| Liu-Oudjane-Wan (MOR 48) | 2023 | Shapley-Folkman approximate pure equilibria in nonconvex aggregative games | the rounding step in our lumpy version; already used in the Omega paper |
| Chan-Sircar (AMO 71); Graber; Graber-Mouzouni | 2015- | Cournot and Bertrand MFG; epsilon-Nash for large N | no congestion network, no tolls, no routing |
| Huang (SICON 48) and the major-minor literature | 2010- | MFG with a major player | a major-minor model (a few big carriers plus gig couriers) is open for this application but harder |
| Aurell-Carmona-Dayanikli-Lauriere (SICON 60); Dayanikli-Lauriere (MOR 2024); Guo-Hu-Zhang (arXiv 2210.04110); Elie-Mastrolia-Possamai (MOR 44) | 2019-24 | Stackelberg MFG: incentives, single-level penalised reformulation, minimax sensitivity, principal with many agents | general machinery; none uses observation-only tolls with a rate |
| Sanjari-Bose-Basar, arXiv 2207.10611 | 2022 | incentive design with many followers; smooth mean-field incentives can fail to exist | warns that affine incentives in the limit need care; our tolls are prices on aggregates, which avoids it |
| Harks-Schedel (Math. Program. 203) | 2024 | multi-leader Stackelberg pricing with a continuum of congested followers | leaders are firms, not a city; static |
| Li-Dimakis-Courcoubetis, arXiv 2504.02346 and 2504.20774; Courcoubetis-Dimakis (AAMAS 2023) | 2023-25 | ride-hailing MFG with repositioning (KKT, uniqueness under a dispatch rule); couriers choosing zones, PoA under discounting | closest gig-courier application; no carriers, Cournot or tolls |
| Langner-Neufeld-Park, arXiv 2410.11652; Liang-Zhou-Zhuang-Zou, arXiv 2601.12226 | 2024, 2026 | discrete-time MFG with worst-case transition ambiguity; existence; finite-agent approximation | **robust MFG existence is known**; p-boxes, E-admissibility and the width-indexed equilibrium sets are not covered |
| Cardaliaguet-Hadikhanloo (COCV 2017); Lavigne-Pfeiffer (AMO 2023); Perolat et al. (AAMAS 2022); Cui-Koeppl (AISTATS 2021) | 2017-23 | fictitious play for potential MFG; conditional gradient with rates; online mirror descent under monotonicity; entropy regularisation | solvers exist; we would reuse them, not contribute one |
| Lacker (AAP 30); Cardaliaguet-Delarue-Lasry-Lions (book) | 2019-20 | closed-loop N-player convergence; master equation | diffusion settings; not our static or aggregative case |
| Beckmann-McGuire-Winsten; Roughgarden-Tardos; Roughgarden-Schoppmann (JET 156); Chau-Sim (ORL 2003) | 1956-2015 | Beckmann potential and marginal-cost tolls; nonatomic PoA 4/3; splittable PoA; PoA with elastic demand | known; PoA results transfer to the limit game as cited facts |
| Carlier-Jimenez-Santambrogio (SICON 47) | 2008 | continuous Wardrop equilibrium with congestion | background |

**What is already known.** Existence and uniqueness of the potential congestion MFG on a graph. Marginal-cost tolls implement the optimum. Tolls in MDP congestion games, including adaptive tolls with unknown costs and real ride-hail data. Robust MFG existence and finite-agent approximation. Nash-to-Wardrop convergence at O(1/sqrt N), and Nash-to-Wardrop convergence in general. Solvers. Ride-hailing and courier MFG models.

**What would be new, to my reading.** (a) An O(1/N) aggregate gap with an explicit, instance-free constant for Cournot-congestion games, first for zone-separable carriers and possibly in general. (b) The same gap for **lumpy, pure** plan profiles, combining it with Liu-Oudjane-Wan. (c) Convergence of the leader's observation-only fixed-point charge to the Pigou toll at rate O(s/(1-rho)). (d) The scaling of the credal absorption width with s: the N-free terms of the Omega theorem bind exactly in this regime. (e) The D2 contrast: in the finite game, pure existence is NP-complete; in the limit, existence is restored but monotonicity holds only for rank-one dwell times. Of these, (a) is the only piece a theory referee would call a result. The others are consequences, but useful ones.

## 3. Candidate research problems

### A. Robust Stackelberg tolls in the zone-time congestion MFG

*Statement attempt.* Model (M) under D1 with b, c > 0.
- (A1) An equilibrium exists and its aggregate is unique, for the precise game and for Gamma-maximin with p-box travel times, provided the robust per-agent value is concave in the aggregate.
- (A2) The toll u* = gamma c X^opt implements the optimum. Under E-admissible beliefs of width delta, every equilibrium under u* has an aggregate within delta ||w||_M of A^opt, and its welfare loss is O(delta), or O(delta^2) when the optimum is interior.
- (A3) The ARP update u <- (1-theta) u + theta kappa Q(u), which uses observed aggregates only, contracts at ratio rho = max kappa/(b+kappa). In the nonatomic case the convexification is exact, so this is the Omega theorem without the lot error.

*Proof idea.* Potential plus strong concavity in A (A1). The proximal-map identity of the Omega paper and nonexpansiveness (A2, A3).

*Likely true or false.* A1 is true but known in substance. The A2 bound is first order in general. With time-of-day prices, the corner property of Gamma-maximin can fail, so A1 for Gamma-maximin needs a monotonicity condition on prices over time.

*Difficulty:* low. *Novelty risk:* high (Li et al. 2019, 2023; Yang-Meng-Lee 2004; Calderone-Sastry 2017).

*Data.* The 9 cities with T = 1 work today. A time-of-day version needs delivery-demand and background-speed profiles by hour, which we do not have (see Section 5).

### B. Finite-N to mean field with an O(1/N) gap (recommended spine)

*Setting.* Affine D1 coupling with M = diag(b, gamma c) = diag(m) in delivery units. Carrier i has convexified plan set X_i, contributions a_i(x_i) in R^d and share s_i (largest contribution in any coordinate), with s = max s_i. Write A^N for the aggregate of a Nash equilibrium (carriers internalise their own effect on A) and A^W for the mean-field aggregate (price takers).

- (B1, known in form) ||A^N - A^W||_M^2 <= sum_i <a_i^N, M (a_i^W - a_i^N)>, so the gap is O(sqrt s). This is the Paccagnan et al. Thm 1(3) rate; the argument is the sum of the two variational inequalities.
- (B2, provable now) If each carrier's problem separates by zone, then for every z, every N and every instance, |Q^N_z - Q^W_z| <= max_i (largest lot of i in z) <= s.
  *Proof.* A Nash equilibrium is a Wardrop equilibrium of the game in which carrier i's unit cost in zone z rises by m_z q_iz^N, which lies in [0, m_z s]. In one zone, the Wardrop aggregate falls by at most delta/m when every cost rises by at most delta. The checks found no violation over 200 random instances (largest ratio 0.65).
  The symmetric closed form Q^N = N/(N+1) Q^W gives |Q^N - Q^W| = Q^W/(N+1), so the bound is attained in order.
- (B3, target) With cross-zone coupling (fleet budgets, tours spanning zones), ||Q^N - Q^W||_inf <= C s, with C independent of N.
  For exact replicas of a fixed instance (T base types, each split into N/T identical carriers), the Nash equilibrium is unique and symmetric. It is the Wardrop equilibrium of the T-type game with a type-level perturbation of size O(1/N) in fixed dimension. Robinson's (1981) upper-Lipschitz property of polyhedral multifunctions then gives O(1/N) **with an instance-dependent constant**.
  Whether C can be made instance-free, for example C <= 1 + something depending only on Z, is open.
  Numerics (check 3): over random instances with N <= 64 and Z <= 8, the ratio max_z |dQ_z|/s stays at or below 1.09 in the main run and reaches 1.32 at N = 256. For exact replicas the ratio settles as N grows; one instance gives 0.37, 0.49, 0.53, 0.55 for N = 4, 16, 64, 256. Under an O(sqrt s) gap it would grow like sqrt N, by a factor of 8 between N = 4 and N = 256. The evidence supports O(s) per instance. The worst-case constant is unknown and exceeds the one-zone value 1.
- (B4, lumpy plans) Pure equilibria of the lumpy game: combine B2/B3 with the Shapley-Folkman rounding. When contributions scale with s, at most d = 2ZT carriers remain fractional, so the extra error is at most d s. For the credal width, sigma_max is proportional to s, so the absorption threshold sigma_max min{N-1, d+1, 1 + sqrt(d ln(2d)/2)} is O(s d) and tends to 0. The N-free terms of the Omega theorem, which do not bind on the Omega city instances (N <= 6 < d), bind exactly when N > d. For Cairo (42 zones) with T = 4, that means N > 336 agents, which is plausible for gig couriers.
- (B5, the leader) The ARP fixed points satisfy ||u*_N - u*_W||_{kappa^-1} <= (||kappa (Q^N(u) - Q^W(u))|| + ||(m/2) d-bar||)/(1 - rho) = O(s/(1-rho)). The proof uses only the perturbation lemma for contractions and the Omega rate rho. The leader's gain and the PoA converge at O(s).

*Likely true or false.* B2 and B5 are true; B2 has a complete proof and B5 needs only the cited Omega theorem. B3 for replicas is true with an instance-dependent constant. Whether an instance-free constant exists is uncertain; a constant equal to 1 is false (ratio 1.32 observed). B4 is true, with the d-dependence probably loose.

*Difficulty.* B2, B4, B5: low to moderate. B3 with an explicit constant: hard, and the main research risk.

*Novelty risk:* medium. Paccagnan et al. have the sqrt rate, Haurie-Marcotte the qualitative limit, and Cominetti et al. explicit bounds for unsplittable mixed play. An O(1/N) result with constant 1 for zone-separable Cournot-congestion, plus the toll and credal corollaries, is narrower but, as far as I found, not in print.

*Data.* No new data are needed for T = 1. Replica experiment: split each city's carriers (existing E1/E2 instances) into k = 1, 2, 4, ..., 64 replicas with 1/k of the demand and fleet each. Compute the convexified Nash equilibrium with the existing D1 engine and the mean-field equilibrium by Frank-Wolfe on the potential. Plot ||A^N - A^W|| and ||u*_N - u*_W|| against s together with the bounds.

### C. Vehicle-count congestion (D2) in the mean-field limit

- (C1) The nonatomic D2 game always has an equilibrium: strategy sets are convex and the coupling is continuous (Kakutani). In the finite game, deciding whether a pure equilibrium exists is strongly NP-complete (Omega Thm "NP-completeness under D2"). The limit removes the existence problem.
- (C2) With types theta whose dwell time per vehicle in zone z is h_{theta z}, the coupling operator is monotone after a per-type reweighting, and the game is a weighted potential game, **if** h is rank one (h_{theta z} = h_theta g_z). With two types of different dwell times, the unweighted symmetric part is indefinite (check 4: eigenvalues -0.208 and 2.708), and the weight 1/h restores a positive semidefinite form. A rank-two h admits no per-type weight that symmetrises both zones.
- (C3, conjecture) For rank above one, multiple isolated equilibria exist on some instances, and computing an equilibrium of the resulting affine non-monotone variational inequality (a linear complementarity problem) is PPAD-hard in the number of types. Not checked; the reduction is not designed.

*Difficulty:* C1 and C2 low; C3 hard. *Novelty risk:* moderate for C2 (a weighted-potential argument is standard). C3 is the only substantive part.

*Data.* The fleet mix (vans against cargo bikes) and dwell times by zone are not in our data.

## 4. Recommendation and plan

**Direction:** Problem B as the spine, with A3 and C1-C2 as supporting sections. Working title: *Many small carriers: the mean-field limit of competitive urban delivery under zone tolls.* The claim is narrow and checkable: an O(1/N) equilibrium gap with an explicit constant, transferred to the city's charge and to the belief width. It also links the new paper to the Omega paper without repeating it.

**Plan.**
1. Fix model (M) with T = 1 first. Write B1 and B2 with full proofs and the symmetric closed form, and add A1 and A3 as lemmas with citations.
2. Attack B3: prove the replica case through Robinson's upper-Lipschitz property. Search numerically for families that push the ratio up (adversarial search over Z <= 4 with cross-zone budgets and tour-type contributions). Then try to prove or refute an instance-free bound of the form C(Z). Decision point after about four weeks: if no instance-free constant appears, state B3 for replicas and B2 as the sharp case.
3. Derive B4 and B5, plus PoA and leader-gain convergence. Add the Gamma-maximin surcharge in the limit and the width scaling.
4. Experiments on the 9 cities with T = 1: the replica sweep k <= 64, the toll gap, and the solver cost of finite-N against mean-field equilibria (the mean-field solve does not grow with N). Then T = 4 with a stated stylised hourly profile and a sensitivity analysis, labelled as stylised.
5. Section on D2 (C1, C2), with C3 stated as an open problem unless a reduction is found.
6. Lean cores (below), writing, submission.

**Lean-checkable cores** (finite or algebraic; the existing `lean/CCU` development is the base):
- symmetric Cournot-congestion closed form Q^N = N/(N+1) Q^W and the gap Q^W/(N+1);
- the summed variational-inequality bound of B1 in a finite-dimensional inner-product space;
- the one-zone cost-shift monotonicity behind B2: for a finite set of capacitated types with linear costs, raising each cost by at most delta lowers the Wardrop aggregate by at most delta/m;
- the contraction perturbation lemma (rho-contractions T, T' with sup-distance eps have fixed points within eps/(1-rho)) and its use in B5;
- the D2 algebra: indefiniteness of the symmetric part of 1 w^T for w not proportional to 1, and the weighted-potential identity under rank-one dwell times;
- the scaling of the credal width bound with s (algebra on the existing statement).

Not Lean-checkable at reasonable cost: existence through Kakutani (I do not know of a Kakutani theorem in Mathlib), Robinson's upper-Lipschitz theorem, robust MDP dynamic programming, and solver rates.

**Venues.** Transportation Science or Operations Research, for the model, theorems B2/B4/B5 and the 9-city study. Mathematics of OR, if B3 is proved with an instance-free constant. Dynamic Games and Applications, for a shorter theory note (B and C without the cities). SIAM J. Control Optim., only for a continuous-time version on the graph, which this plan does not include. TR Part B is a fallback for the toll results.

**Risks, stated plainly.**
1. The static T = 1 version is "Nash to Wardrop in an aggregative game". A referee may say it is not an MFG paper at all. The dynamic zone-time model is what makes it one, and that needs time-of-day data we lack.
2. B3 may have no instance-free constant. Then the main theorem is the zone-separable case (constant 1) plus an instance-dependent rate for replicas, which is still an improvement on O(1/sqrt N) but a smaller one.
3. The limit removes market power, which is the economic content of the Omega leader results. The paper must say that its limit fits gig couriers and small operators, not DHL or Amazon. A major-minor model is the faithful one, and it is not attempted.
4. Overlap with MDP congestion-game tolling (Li et al.) is large on the leader side. The new paper's leader claims must be limited to the rate and the finite-N toll error.
5. The new paper depends on the Omega paper's ARP theorem, which is under review. If that theorem changes in revision, B5 changes with it. Cite the Omega paper as a working paper, and check the blind-review rules of the target journal.
6. Literature coverage: most entries were read at abstract level, except Paccagnan et al. Section IV. The rate in Jacquot-Wan and the exact statements of Gomes-Mohr-Souza (2013) and Cominetti et al. need full-text reading before any claim of novelty is written.

**Decisions the author must make.**
1. Who is the mean-field agent: small multi-stop carriers (keeps routing and lumpy plans; recommended) or single couriers (cleaner MFG, loses the routing layer)?
2. Major-minor (a few big carriers plus a courier continuum) now, or as a later paper? Recommendation: later.
3. Time-of-day data: accept a stylised hourly profile for the first paper, or acquire hourly speeds and demand (for example a traffic-index provider or a city open-data portal; licence to be checked)?
4. How much of the imprecise-probability layer to keep. Recommendation: only the Gamma-maximin surcharge and the width scaling. A robust MFG existence theorem is not new.
5. Venue tier, which depends on the outcome of step 2.

## 5. Numerical sanity checks (run on 2026-11-03)

`python3 -I mfg/checks/finite_to_mf_gap.py`; output in `mfg/checks/finite_to_mf_gap.out`. These are continuous convexified instances solved by FISTA, with the accuracy of each solve bounded through the Frank-Wolfe gap (at most 2e-4 of s in all runs).

- Check 1: the symmetric closed form holds to 2e-16.
- Check 2: in one zone, the largest |Q^N - Q^W|/s is 0.65 (bound 1).
- Check 3: with cross-zone budgets, the largest ratio is 1.09 over N = 2 to 64, Z = 3 and 8 (main run), and 1.32 in a separate run at N = 256 (seed 1, random instances; a scratch run not included in the committed script). Exact replicas settle as N grows.
- Check 4: with two dwell times, the D2 coupling has an indefinite symmetric part.

None of this proves anything. The checks support the conjecture in B3 and show that its constant is not 1.

Data gaps for the dynamic model: no hourly demand or speed profiles, no counts of gig couriers or fleet mix per city, and no dwell times by vehicle type. The static instances (zones, populations, OSM travel times, POIs) are sufficient for T = 1.


## 6. Status after execution of the plan (2026-11-03)

Decisions taken with the memo's defaults: (1) mean-field agent = small multi-stop carriers (tours with up to three stops, fleet budgets); (2) major-minor model left for a later paper; (3) stylised hourly profile, graded (anchors A from TomTom peak values, shape C, Moscow peaks imputed C); (4) imprecise layer limited to the Gamma-maximin surcharge and the width scaling; (5) venue open. All new work is in `mfg/` (code `mfg/src/mfgcc`, tests `mfg/tests`, checks `mfg/checks`, theory `mfg/theory`, Lean `mfg/lean`, results `mfg/results`, figures `mfg/figures`, draft `mfg/paper/main.pdf`). Nothing in `paper/`, `theory/`, `src/ccu`, `lean/` was changed. Theorem numbers refer to `mfg/paper/main.tex`.

**Answer to the open question of Problem B3.** No instance-free O(s) constant exists once carriers' plans couple zones. Proposition 5 gives a two-zone family (two carrier types moving along directions at angle phi_n with 1 - cos phi_n = 1/n, linear profits, bounded data) whose gap is exactly sqrt(1/(8n) + (2n-1)/(8n^3)), i.e. 1/sqrt 2 times the general bound (1/2)(sum_i ||a_i^W||^2)^(1/2) of Theorem 4. The worst-case rate over bounded instances is therefore exactly of order s^(1/2) (the Paccagnan et al. order). For a fixed angle the rate is 1/n with constant 1/sin(phi): O(s) per instance, with a constant governed by the conditioning of the carrier types (Proposition 9: lambda_min(G+K)^(-1/2)). The memo's "C(Z)" guess is refuted for weighted budgets/tours; whether a C(Z) exists for unweighted fleet budgets (unimodular directions) is open.

| Result | Statement (short) | Status |
|---|---|---|
| Lemma 1-3 | linearisation; potentials and uniqueness; Nash = Wardrop with own surcharge M a_i; replica symmetry | proved (classical parts cited) |
| Thm 4(a) | gap <= (1/2)(sum ||a_i^W||^2)^(1/2) <= (1/2)(s <m,A^W>)^(1/2) | proved; constant 1/2 new, argument Paccagnan et al. |
| Thm 4(b) | same order for pure equilibria of lumpy plans | proved |
| Prop 5 | tightness family, ratio -> 1/sqrt 2; no instance-free O(s) constant | proved (closed form; Lean algebra) |
| Thm 6 | zone-separable: 0 <= Q^W - Q^N <= max_i q_i^N (convexified) or max lot (lumpy pure); equality for identical carriers | proved, sharp |
| Prop 7 | identical carriers, any coupling: ||dA||_m <= ||A^N||_m / N | proved |
| Thm 8 | replicas (polyhedral, linear profits): O(1/n), instance-dependent constant | proved via Robinson (1981) |
| Prop 9 | affine interior replicas: explicit constant lambda_min(G+K)^(-1/2) | proved |
| Lemma 10, Prop 11 | responses nonexpansive; observation-only rule contracts at rho = max kappa/m (Omega theorem restated); fixed point = kappa * aggregate of auxiliary game; Pigou in the limit | proved |
| Thm 12 | u_N* - u_W* = kappa (Q~_N - Q~_W): charge converges at the aggregate rate of an auxiliary game; separable: 0 <= u_W* - u_N* <= kappa s | proved |
| Thm 13, Cor 14 | welfare under any charge; observation-only fixed point loses <= (1/2) s <m,Q^opt> for every instance; PoA and leader gain converge | proved |
| Prop 15 | Gamma-maximin = common tax delta m w; prox shift <= delta ||w||_m; ARP over-corrects, loss <= (1/2) delta^2 ||m w||^2_{(m+kappa)^-1} | proved (part (a) from the Omega lemma) |
| Cor 16 | absorption width <= (d+1) s / w_min | algebra on the Omega theorem |
| Prop 17 | time-dependent charges can break the slow-corner property of p-boxes | proved (example) |
| Prop 18 | D2 limit: existence; weighted potential iff dwell times rank one; unweighted operator indefinite | proved |
| Conj 19 | D2 rank >= 2: multiplicity, PPAD-hardness | conjecture, not checked |
| Prop 20 | N identical carriers: optimal charge = Pigou minus (1/N) m Q^opt (subsidy for N < m/kappa) | proved; checked to 5e-9 on 324 city instances |

Every inequality was also checked by brute force on small random games (`mfg/checks/theory_checks.out`, all slacks nonnegative). Lean (`mfg/lean`, `lake build` passes, no sorry) checks the algebraic cores listed in `mfg/lean/README.md`.

**Experiments (nine cities, ten hourly periods, 6 segments split into k = 1..256 carriers, N <= 1536).**

| Question | Result |
|---|---|
| gap vs N (replicas, 5 seeds) | slope -0.88 [-0.90, -0.86] for N >= 24 (by city -0.93 to -0.77); against the share s_N slope 0.95 [0.92, 0.97]; gap / s_N median 0.98, range 0.35-1.86; general bound held in 405/405 |
| heterogeneous splits (3 seeds, N <= 96) | slope -0.79 [-0.83, -0.75], gap / s_N median 0.76, max 1.57; short range of N, read as consistent with O(s) only |
| charge | observation-only fixed point -> Pigou charge with slope -0.91 [-0.92, -0.89] (calibrated) and -0.90 (congestion x10) |
| PoA | Cournot loss 21.4% of optimal welfare at N = 6 (8.7-28.1%), 0.020% at N = 1536; mean-field PoA 0.026% (calibrated congestion is weak, rho 0.009-0.52) |
| leader gain (negative result) | the observation-only charge lowers welfare with few carriers (-0.45% at N = 6; -3.0% with congestion x10) and helps in every instance only from N = 192 (congestion x10); the Omega flat rule with subsidy gains 16.4% (10.5%) at N = 6 and meets the Pigou rule in the limit |
| hourly profile (amplitudes 0-1.5) | weak effect: PoA at N = 6 between 20.7% and 21.8%, slopes -0.86 to -0.90; conclusions are not artefacts of the profile, but the profile is stylised |
| Gamma-maximin | aggregate shift <= 0.97 of the bound; ARP under cautious carriers loses 1.2% (delta = 1 lot) to 11.9% (delta = 4 lots) of welfare, within the bound in 675/675 |
| width scaling (weak result) | the uniform absorption width falls from 481 to 0.7 times a zone-hour's mean demand between N = 6 and N = 24576: not a practically small width |
| stakeholder split (new) | Welfare = carrier profit + consumer surplus + congestion cost + revenue (exact). N=6: market-power rule +19.6% welfare, CS +69%, carriers +132%, revenue -182% (city pays); observation-only -0.5%. N=1536: revenue +3%, CS -1.1%, carrier profit -8%. Exposure Gini unchanged by charges (0.080), traffic share moves away from dense zones (rho -0.56); best single city-wide charge loses 3.41% vs 1.08% (zone-hour) at N=6; +-25% charge error costs <= 0.04% (bound held 180/180). Congestion is 3.6% of welfare: residents' burden is small (weak result) |
| solver | replica reduction makes N = 1536 as cheap as N = 6; plain Frank-Wolfe did not reach 1e-4 relative gap in 3000 rounds (0.3-1.3%); interior point used for all results |

**Honest novelty assessment.** The new pieces, to our reading of the literature listed in Section 2: the tightness family (no lower bound for the Nash-Wardrop distance was found in Paccagnan et al. 2019, Jacquot-Wan 2018 or Haurie-Marcotte 1985), the sharp constant-one zone-separable theorem (short and elementary), the exact identity for the finite-market observation-only charge and the instance-free O(s) welfare bound. Potentials, uniqueness, marginal-cost tolls, MDP congestion games, the contraction of the observation-only rule (Omega paper) and robust-MFG existence are known and are used as such. Paccagnan et al. (Thm 1(1)-(2)) already give O(1/N) under strong monotonicity in individual strategies; our replica results matter only because routing plans with linear costs lack it. The full texts of Gomes-Mohr-Souza (2013) and Cominetti et al. (2023) were still not read.

**Decisions for the author.** (i) Venue: with B3 answered negatively, MOR is less natural than Transportation Science / OR; a shorter theory note (Dynamic Games and Applications) is possible. (ii) Whether to pursue the open C(Z) question for unweighted budgets. (iii) Whether to acquire hourly data. (iv) Blind-review rules for citing the Omega paper. (v) Whether the economic message (observation-only charge harmful with few carriers) should lead the paper.

## References

Verified in this audit (title, authors and venue checked on the publisher, arXiv or an indexing page; content read at abstract level unless stated):

- Al Saleh, F., Bakaryan, T., Gomes, D., Ribeiro, R. de L. First-order mean-field games on networks and Wardrop equilibrium. Portugaliae Mathematica 81 (2024) 201-246. arXiv 2207.01397.
- Aurell, A., Carmona, R., Dayanikli, G., Lauriere, M. Optimal incentives to mitigate epidemics: a Stackelberg mean field game approach. SIAM J. Control Optim. 60(2) (2022) S294-S322.
- Cabannes, T., Lauriere, M., Perolat, J., et al. Solving N-player dynamic routing games with congestion: a mean field approach. arXiv 2110.11943 (2021).
- Calderone, D., Sastry, S. S. Markov decision process routing games. ICCPS 2017, 273-279.
- Camilli, F., Marchi, C. Stationary mean field games systems defined on networks. SIAM J. Control Optim. (2016). arXiv 1505.04953.
- Cardaliaguet, P., Hadikhanloo, S. Learning in mean field games: the fictitious play. ESAIM: COCV 23(2) (2017) 569-591.
- Carlier, G., Jimenez, C., Santambrogio, F. Optimal transportation with traffic congestion and Wardrop equilibria. SIAM J. Control Optim. 47(3) (2008) 1330-1350.
- Chan, P., Sircar, R. Bertrand and Cournot mean field games. Appl. Math. Optim. 71(3) (2015) 533-569.
- Chau, C. K., Sim, K. M. The price of anarchy for non-atomic congestion games with symmetric cost maps and elastic demands. Oper. Res. Lett. (2003).
- Cominetti, R., Scarsini, M., Schroder, M., Stier-Moses, N. Approximation and convergence of large atomic congestion games. Math. Oper. Res. 48(2) (2023) 784-811.
- Courcoubetis, C., Dimakis, A. Stationary equilibrium of mean field games with congestion-dependent sojourn times (extended abstract). AAMAS 2023. (Title and authors from the PDF metadata.)
- Dayanikli, G., Lauriere, M. A machine learning method for Stackelberg mean field games. Math. Oper. Res. (2024), doi 10.1287/moor.2023.0065.
- Elie, R., Mastrolia, T., Possamai, D. A tale of a principal and many, many agents. Math. Oper. Res. 44(2) (2019) 440-467.
- Gomes, D. A., Mohr, J., Souza, R. R. Discrete mean field games, arXiv 0903.1620 (2009); chapter "Discrete time, finite state space mean field games" in Dynamics, Games and Science I, Springer (2011). A journal version in J. Math. Pures Appl. (2010) is cited from memory and was **not verified**.
- Gomes, D. A., Mohr, J., Souza, R. R. Continuous time finite state mean field games. Appl. Math. Optim. 68 (2013) 99-143.
- Gueant, O. Existence and uniqueness result for mean field games with congestion effect on graphs. Appl. Math. Optim. 72(2) (2015). arXiv 1110.3442.
- Guo, X., Hu, A., Zhang, J. Optimization frameworks and sensitivity analysis of Stackelberg mean-field games. arXiv 2210.04110 (2022).
- Harks, T., Schedel, A. Stackelberg pricing games with congestion effects. Math. Program. 203(1) (2024) 763-799.
- Haurie, A., Marcotte, P. On the relationship between Nash-Cournot and Wardrop equilibria. Networks 15(3) (1985) 295-308.
- Huang, M. Large-population LQG games involving a major player: the Nash certainty equivalence principle. SIAM J. Control Optim. 48(5) (2010) 3318-3353.
- Jacquot, P., Wan, C. Routing game on parallel networks: the convergence of atomic to nonatomic. arXiv 1804.03081 (2018).
- Lacker, D. On the convergence of closed-loop Nash equilibria to the mean field game limit. Ann. Appl. Probab. 30(4) (2020) 1693-1761.
- Langner, J., Neufeld, A., Park, K. Markov-Nash equilibria in mean-field games under model uncertainty. arXiv 2410.11652 (2024).
- Lavigne, P., Pfeiffer, L. Generalized conditional gradient and learning in potential mean field games. Appl. Math. Optim. (2023). arXiv 2209.12772.
- Li, S. H. Q., Yu, Y., Calderone, D., Ratliff, L., Acikmese, B. Tolling for constraint satisfaction in Markov decision process congestion games. ACC 2019, 1238-1243. arXiv 1903.00747.
- Li, S. H. Q., Yu, Y., Miguel, N. I., Calderone, D., Ratliff, L. J., Acikmese, B. Adaptive constraint satisfaction for Markov decision process congestion games: application to transportation networks. Automatica 151 (2023) 110879.
- Li, Y., Dimakis, A., Courcoubetis, C. A. Repositioning, ride-matching, and abandonment in on-demand ride-hailing platforms: a mean field game approach. arXiv 2504.02346 (2025).
- Li, Y., Dimakis, A., Courcoubetis, C. A. On the effect of time preferences on the price of anarchy. arXiv 2504.20774 (2025).
- Liang, Z., Zhou, Z., Zhuang, Y., Zou, B. Mean-field games under model uncertainty. arXiv 2601.12226 (2026).
- Liu, M., Oudjane, N., Wan, C. Approximate Nash equilibria in large nonconvex aggregative games. Math. Oper. Res. 48(3) (2023). (Verified in docs/CLOSEST_WORK.md.)
- Masiha, S., et al. Zeroth-order Stackelberg control in combinatorial congestion games. arXiv 2602.23277 (2026). (Verified in docs/CLOSEST_WORK.md.)
- Paccagnan, D., Gentile, B., Parise, F., Kamgarpour, M., Lygeros, J. Nash and Wardrop equilibria in aggregative games with coupling constraints. IEEE Trans. Autom. Control 64(4) (2019) 1373-1388. Section IV read in full (arXiv 1702.08789v2).
- Perolat, J., Perrin, S., Elie, R., et al. Scaling mean field games by online mirror descent. AAMAS 2022. arXiv 2103.00623.
- Roughgarden, T., Schoppmann, F. Local smoothness and the price of anarchy in splittable congestion games. J. Econ. Theory 156 (2015) 317-342.
- Salhab, R., Malhame, R. P., Le Ny, J. A dynamic game model of collective choice in multiagent systems. IEEE Trans. Autom. Control 63(3) (2018).
- Sanjari, S., Bose, S., Basar, T. Incentive designs for Stackelberg games with a large number of followers and their mean-field limits. arXiv 2207.10611 (2022, rev. 2024).
- Cui, K., Koeppl, H. Approximately solving mean field games via entropy-regularized deep reinforcement learning. AISTATS 2021, PMLR 130.

Classical references cited from memory (bibliographic details not re-checked in this audit):

- Beckmann, M., McGuire, C. B., Winsten, C. B. Studies in the Economics of Transportation. Yale University Press, 1956.
- Cardaliaguet, P., Delarue, F., Lasry, J.-M., Lions, P.-L. The Master Equation and the Convergence Problem in Mean Field Games. Annals of Math. Studies 201, Princeton, 2019.
- Huang, M., Malhame, R. P., Caines, P. E. Large population stochastic dynamic games. Commun. Inf. Syst. 6(3) (2006) 221-252.
- Iyengar, G. Robust dynamic programming. Math. Oper. Res. 30(2) (2005) 257-280.
- Lasry, J.-M., Lions, P.-L. Mean field games. Jpn. J. Math. 2(1) (2007) 229-260.
- Nilim, A., El Ghaoui, L. Robust control of Markov decision processes with uncertain transition matrices. Oper. Res. 53(5) (2005) 780-798.
- Robinson, S. M. Some continuity properties of polyhedral multifunctions. Math. Program. Study 14 (1981) 206-214.
- Roughgarden, T., Tardos, E. How bad is selfish routing? J. ACM 49(2) (2002) 236-259.
- Yang, H., Meng, Q., Lee, D.-H. Trial-and-error implementation of marginal-cost pricing on networks in the absence of demand functions. Transp. Res. Part B 38(6) (2004) 477-493. (In the Omega bibliography.)
