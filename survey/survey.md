# Competing Carriers under Uncertainty: A Survey of Non-Cooperative, Stochastic and Data-Driven Vehicle Routing for Urban Last-Mile Delivery

The intersection this survey targets, in which several competing carriers or delivery platforms act as strategic players, routing is modelled explicitly, demand and travel times are stochastic, and data-driven or learning-based methods are used, has almost no peer-reviewed work: the closest anchors are Figliozzi, Mahmassani and Jaillet's sequential-auction work from the 2000s and recent single-leader bilevel last-mile models, and none of these combines all four elements.

## TL;DR

- **Where the gap is.** Peer-reviewed work splits into four streams that rarely meet: (i) single-decision-maker stochastic and dynamic VRP, which is mature, including DRO and RL; (ii) cooperative multi-carrier VRP, which is mature (auctions, request exchange, cost sharing); (iii) platform-competition economics, rich for ride-hailing but abstracting routing into queues; (iv) single-leader Stackelberg or bilevel last-mile models, recent and deterministic. Only the 2003–2007 sequential-auction work of Figliozzi, Mahmassani and Jaillet combines competition among carriers, routing and dynamics, and it assumes deterministic travel times and uses no learning.
- **Evidence is uneven.** Ride-hailing supplies most evidence on platform competition, multi-homing, mean-field games and multi-agent RL. Parcel and last-mile delivery supplies most evidence on routing fidelity, crowdsourced delivery and public datasets. Results should not be carried across without saying so. Peer-reviewed models of competing parcel carriers are stylized: shared collection points, locker placement, first-mile sharing.
- **Recommended contribution.** A regulator-led Stackelberg game: the city or a platform prices micro-hub or curb access; below it, N carriers play a generalized Nash game coupled by shared capacity, each solving a stochastic routing problem with data-driven (Wasserstein) ambiguity. Compute equilibria with best-response learning and decision-focused learning, and evaluate with price of anarchy, exploitability, social cost and fairness on multi-carrier instances built from Amazon and LaDe data.

## 1. Introduction, scope and search methodology

### 1.1 Motivation and scope

Urban last-mile delivery is increasingly shaped by several firms operating in the same space: parcel integrators, retailer fleets, crowdsourced platforms and on-demand meal or grocery platforms. They serve overlapping customers, compete for a shared and partly multi-homing courier workforce, and use scarce common infrastructure such as curb space, loading zones, lockers and micro-hubs. Classical VRP theory assumes one decision-maker and one fleet. Collaborative routing lets carriers share requests but still assumes they want to cooperate. Neither captures the non-cooperative case, where each carrier's routing, acceptance and pricing decisions change its rivals' costs and revenues.

The survey covers models in which (a) two or more carriers or platforms affect each other strategically, (b) at least one decision is routing, dispatching or order acceptance, or is explicitly linked to routing costs, and (c) uncertainty or dynamics is modelled, or the work is a methodological building block for such models. Foundational work before 2015 is covered selectively and 2015–2026 intensively.

### 1.2 Search methodology and transparency statement

We searched publisher platforms (ScienceDirect, INFORMS PubsOnline, SpringerLink, Wiley, ACM DL), Crossref, RePEc/IDEAS and arXiv, and followed citation chains from anchor papers, using keyword families on competition (e.g., "competing carriers", "generalized Nash", "Stackelberg", "bilevel", "price of anarchy", "multi-homing"), routing (e.g., "last-mile", "crowdshipping", "parcel locker", "curb") and uncertainty and learning (e.g., "distributionally robust", "approximate dynamic programming", "reinforcement learning", "mean field"). We then checked records against publisher pages or Crossref metadata. Inclusion required peer-reviewed articles in OR/MS, transportation or ML venues with a direct link to competition, routing, uncertainty or learning. Industry reports, blogs and vendor material are excluded; arXiv items are labelled as preprints and not used for core claims.

**Limitations.** This is a structured, citation-chained narrative review, not a PRISMA systematic review, so we do not report screening counts; for the manuscript, re-run a documented Scopus/Web of Science query for 2015–2026 and report PRISMA counts. Each reference in Section 10 carries a flag: **[V]** record confirmed against a publisher page, Crossref or an index during this review; **[P]** existence and key fields confirmed, some fields from domain knowledge; **[U]** not re-verified here, so all fields must be checked and DOIs are omitted rather than guessed.

## 2. A taxonomy of multi-carrier routing

**Axis 1: decision architecture.**
1. *Centralized (merged-fleet) planning.* One planner optimizes all requests jointly. This is the system optimum, the denominator of the price of anarchy, and the upper bound reported in collaborative-routing studies (Gansterer & Hartl, 2018).
2. *Cooperative, decentralized planning.* Carriers keep autonomy but exchange requests through auctions or trades and share gains via cost-allocation rules (Gansterer & Hartl, 2018, 2020; Guajardo & Rönnqvist, 2016; Cleophas et al., 2019). Incentive compatibility and stability (core, Shapley value) are central.
3. *Non-cooperative planning.* Carriers optimize their own objectives. Interaction runs through (a) competition for customers via prices, bids or service promises; (b) competition for couriers who may multi-home; and (c) congestion or capacity externalities on roads, curbs, lockers and hubs. Solution concepts are Nash, generalized Nash or Wardrop equilibria; Stackelberg equilibria when a platform or regulator moves first; and learning or evolutionary dynamics under bounded rationality.

**Axis 2: who leads.** No leader (simultaneous Nash); a platform leading self-interested carriers (Cerulli et al., 2024); a public authority leading the market (Catalano & Migliore, 2014; curb-management models); or multi-level structures.

**Axis 3: routing fidelity.** (i) stylized or aggregate (queues, continuous approximations); (ii) network-flow or assignment level; (iii) full VRP or TSP with profits per player. Game-theoretic work mostly sits at (i)–(ii); stochastic routing mostly at (iii) with one player. The target gap is non-cooperative architecture with level (iii) fidelity and stochasticity.

## 3. Stochastic and dynamic VRP foundations

### 3.1 Sources of uncertainty and modelling paradigms

Standard taxonomies cover uncertain demands, customer presence, and travel and service times (Gendreau, Laporte & Séguin, 1996; Gendreau, Jabali & Rei, 2016; Oyola, Arntzen & Woodruff, 2018). Dynamic VRPs are reviewed by Pillac et al. (2013), Psaraftis, Wen and Kontovas (2016) and Ritzinger, Puchinger and Hartl (2016). Four paradigms dominate:

1. **A priori and two-stage stochastic programming with recourse.** Routes are fixed first and recourse (depot returns, skipped customers) follows realization; classics are Bertsimas (1992) and Laporte, Louveaux and Mercure (1992), with Florio, Hartl and Minner (2020) as exact state of the art.
2. **Chance constraints.** Capacity or time-window feasibility must hold with high probability.
3. **Robust and distributionally robust optimization (DRO).** Gounaris, Wiesemann and Floudas (2013) studied the robust CVRP under demand uncertainty. Ghosal and Wiesemann (2020) showed that a distributionally robust chance-constrained CVRP can be solved with standard branch-and-cut whenever the ambiguity set is subadditive; under marginal moment ambiguity it reduces to a deterministic CVRP with altered demands, with runtimes often comparable to the deterministic CVRP. Ghosal, Ho and Wiesemann (2024) unify the CVRP under risk and ambiguity. For travel times, Zhang et al. (2021) introduced a service fulfilment risk index combining lateness probability and magnitude; under Wasserstein ambiguity it is evaluated in closed form, solved by branch-and-cut and a metaheuristic, and reduces overfitting. Jaillet, Qi and Sim (2016) give a related lateness-index framework.
4. **MDPs and approximate dynamic programming (ADP).** Ulmer et al. (2020) give a canonical MDP framework for route-based decisions; Soeffker, Ulmer and Mattfeld (2022) organize the field through prescriptive analytics. ADP has been developed for multi-period routing (Ulmer, Soeffker & Mattfeld, 2018), customer acceptance (Ulmer & Thomas, 2020), offline–online approximation (Ulmer et al., 2019) and same-day delivery with drones (Chen, Ulmer & Thomas, 2022).

### 3.2 Demand management and pricing coupled with routing

Many last-mile decisions are demand-side: which orders to accept and which time slots to offer at what price. Choice-based time-slot management (Agatz et al., 2011; Yang et al., 2016) and dynamic pricing for same-day delivery (Ulmer, 2020) are single-firm counterparts of the competitive problems in Section 4, where competition often acts through these levers rather than through routes.

### 3.3 Implications for competitive models

First, DRO formulations that keep the deterministic combinatorial structure (Ghosal & Wiesemann, 2020) are attractive *best-response oracles* in equilibrium computation, because each best response remains an ordinary VRP solve. Second, the MDP/ADP framework extends naturally to a *stochastic (Markov) game* by indexing state and action by player; we found no peer-reviewed paper that does this for competing parcel carriers.

## 4. Game-theoretic models of competing carriers and platforms

### 4.1 Competition for requests: sequential auctions and the VRPCE

Figliozzi, Mahmassani and Jaillet developed a framework for carrier strategies in auction-based marketplaces (2003), assessed dynamic routing technologies under sequential auctions (2004), studied auction settings (2005), derived an opportunity-cost expression whose impact depends on the competitive setting (2006), and introduced the Vehicle Routing Problem in a Competitive Environment (VRPCE), extending the TSP with profits to a dynamic competitive auction environment and pricing requests by opportunity costs from one-step look-ahead (2007). This is still the only stream combining inter-carrier competition, routing-level costs and dynamic arrivals. Its limits are a truckload pickup-and-delivery setting, deterministic travel times, and simulation rather than equilibrium computation.

### 4.2 Nash and generalized Nash formulations among carriers

Peer-reviewed models in which competing carriers each solve a VRP and the outcome is a Nash equilibrium are scarce. Isolated two-distributor bimatrix or bargaining models and "vehicle routing games" with strong equilibria appear in lower-tier or regional journals; they are deterministic and very small, so we do not treat them as core evidence. Flow-level generalized Nash games among forwarders exist (e.g., an EJOR paper on the non-cooperative transportation problem as a linear generalized Nash game, not fully verified) but are deterministic and omit routing.

Network economics supplies the theory a routing-level model needs: oligopolistic atomic-splittable routing (Orda, Rom & Shimkin, 1993; Cominetti, Correa & Stier-Moses, 2009) and price competition among congestible providers (Acemoglu & Ozdaglar, 2007). The key move for parcel carriers is to treat shared curb, hub or road capacity as *coupling constraints*, giving a generalized Nash equilibrium problem (GNEP; Facchinei & Kanzow, 2010) whose variational equilibria share a common shadow price on the resource, which a regulator can set as Stackelberg leader.

### 4.3 Stackelberg and bilevel models: platforms, regulators and consolidation

- **Platform leads, carriers follow.** Cerulli, Archetti, Fernández and Ljubić (2024) model a peer-to-peer last-mile platform that assigns requests, and optionally sets compensation, anticipating that each carrier solves its own profitable tour problem; they give single-level and projected reformulations and branch-and-cut. A carrier alliance with profit sharing, as in an urban consolidation centre (UCC), collapses to a single-level problem, which shows that the bilevel structure is what captures non-cooperation. The model is deterministic and followers do not interact, so it is not a Stackelberg–Nash game.
- **Crowdsourced delivery with strategic couriers.** Bilevel or menu-based acceptance models include Mofidi and Pazour (2019), Horner, Pazour and Mitchell (2021) and Ausseil, Pazour and Ulmer (2022). Stochastic crowd supply is studied by Gdowska, Viana and Pedroso (2018) and by Torres, Gendreau and Rei (2022) with two-stage stochastic programming and time windows.
- **Public authority leads.** Catalano and Migliore (2014) cast logistics-terminal design as a Stackelberg game with a system-optimal designer above a carrier equilibrium, finding that public co-investment should be high and consolidation concentrated at few terminals. A 2025 TR-B paper frames outsourcing of first and last legs to third-party carriers as a Stackelberg game solved by bilevel MINLP.
- **Curb access.** Xu and Sun (2024, Transportation Science 58(6)) find that pricing strategies for metered parking to general parkers are more efficient and flexible than other interventions, and that when curb parking pricing is optimally calibrated, the necessity for dedicated delivery bays diminishes. Liu, Ma and Qian (2023) optimize curbside pricing for ride-hailing pick-ups. These are the most direct foundations for a *curb-pricing leader*, but neither embeds competing carriers with routing-level responses.

### 4.4 Competition for couriers and customers (mostly ride-hailing)

The richest equilibrium evidence on competing platforms is from ride-hailing and on-demand services:
- **Single-platform foundations:** Taylor (2018), Bai et al. (2019) and Benjaafar et al. (2022) model self-scheduling supply and delay-sensitive customers.
- **Two competing platforms:** Bernstein, DeCroix and Keskin (2021, MSOM 23(5)) find that although individual drivers may have an incentive to multi-home, all players are worse off when all drivers multi-home, and they propose an incentive mechanism to discourage multi-homing. A 2026 TR-E paper adds a "pooling effect": multi-homing mirrors merger-like matching efficiency but triggers price and wage competition.
- **Two-sided theory:** Bakos and Halaburda (2020) analyse multi-homing on both sides.
- **Food delivery:** a TR-E (2023) equilibrium model of food-delivery and ride-sourcing platforms sharing one driver pool characterizes competitive and collaborative regimes and regulations such as commission caps.

These models use queues or aggregate matching, with no vehicle routing. They supply the *market layer* (prices, wages, multi-homing). We found no peer-reviewed model of competing *parcel* platforms with multi-homing couriers *and* explicit routing.

### 4.5 Shared infrastructure: lockers, collection points, first-mile sharing

- Li, Huang, Yue and Wang (2024, TR-E) model two competing express companies, one of which owns a collection-delivery-point network and decides whether and how to share it.
- An EJOR paper (c. 2020; not fully verified) asks whether two competing couriers with partially substitutable doorstep collection should form a common first-mile platform.
- Mercurio, Schlicher, Rohmer and Van Woensel (IJPE, 2026) study joint locker placement as a cooperative game; stable allocations always exist for a class of networks and are possible in most instances.
- Lyu and Teo (2022, MSOM) study Singapore's open-access Locker Alliance.

All are stylized and mostly deterministic, with routing only as reduced-form cost.

### 4.6 Congestion and potential games, and price of anarchy

Selfish-routing theory (Wardrop, 1952; Rosenthal, 1973; Monderer & Shapley, 1996; Roughgarden & Tardos, 2002; Correa, Schulz & Stier-Moses, 2004) gives worst-case bounds, e.g. a price of anarchy of 4/3 for nonatomic routing with affine latencies. A fleet operator, however, is an *atomic* player choosing tours, not paths. Tour-based games are generally not potential games, may lack pure equilibria, and fall outside known PoA bounds. We found no peer-reviewed PoA analysis for competing multi-stop delivery fleets.

### 4.7 Mean-field games, auctions and evolutionary games

Mean-field games and mean-field MARL are used for *within-platform* driver populations in ride-hailing (Li et al., 2019; Laurière et al., 2022) and suit large courier crowds, but competition among a few carriers is an oligopoly needing finite-player equilibria, possibly with a nested mean-field courier population. Auctions are mature in cooperative settings (Section 5) and truckload spot markets (Section 4.1). We found no peer-reviewed evolutionary-game model of competing last-mile carriers with routing in the target venues.

## 5. Cooperative multi-carrier VRP as a benchmark

- **Surveys.** Gansterer and Hartl (2018) classify collaborative VRP into centralized planning, decentralized planning without auctions, and auction-based planning; their 2020 survey of shared resources classifies roughly 40 recent studies by level of information sharing. Guajardo and Rönnqvist (2016) survey cost allocation; Cleophas et al. (2019) review collaborative urban transportation.
- **Auction-based exchange.** Request evaluation and bundling (Gansterer & Hartl, 2016), the value of information (Gansterer, Hartl & Savelsbergh, 2020) and frontiers of auction-based collaboration (Gansterer & Hartl, 2020, Omega 94); earlier work by Krajewska et al. (2008), Berger and Bierwirth (2010) and Wang and Kopfer (2014).
- **Incentive compatibility.** Lane-exchange mechanisms (Özener, Ergun & Savelsbergh, 2011) and truthful, budget-balanced bundle double auctions (Xu, Huang & Cheng, 2017) address misreporting, the natural bridge to non-cooperative analysis.
- **Scale and dynamics.** Los et al. (2020, TR-E) quantify the value of information sharing; Los et al. (2020, ICCL) report system-wide savings of up to 79% for 1,000 carriers on Dutch platform data; Los et al. (2025, Annals of OR) develop decentralized multi-agent combinatorial-auction methods for large dynamic pickup and delivery; Los et al. (2022) study strategic bidding.

These savings bound from above what collaboration could recover. They are not a price of anarchy, because baseline carriers plan independently but do not compete for the same customers.

## 6. Data-driven and learning-based methods

### 6.1 Neural combinatorial optimization

Attention and pointer policies (Vinyals et al., 2015; Nazari et al., 2018; Kool, van Hoof & Welling, 2019; Kwon et al., 2020) learn construction heuristics for static VRPs; Bengio, Lodi and Prouvost (2021) survey ML for combinatorial optimization. In competition, their value is as **fast approximate best-response oracles**: fictitious play or best-response dynamics need many solves, and amortized neural solvers make this tractable, but approximation error becomes *exploitability* that must be measured (Section 7).

### 6.2 Reinforcement learning for stochastic dynamic routing

Hildebrandt, Thomas and Ulmer (2023) argue that RL for stochastic dynamic VRPs is most promising when combined with combinatorial structure, because route-based action spaces are combinatorial. Hildebrandt et al. (2026, Networks) learn to shape the reward or decision space of a mixed-integer program rather than replace it. Baty et al. (2024) embed combinatorial optimization layers for the dynamic VRPTW, and Parmentier (2022) learns approximations by classic OR problems. These optimization-in-the-loop architectures are natural single-agent blocks for multi-agent extensions.

### 6.3 Multi-agent RL and learning in games

Peer-reviewed fleet MARL concentrates on ride-hailing dispatch and repositioning, mostly within one platform (e.g., Li et al., 2019). Competitive multi-operator RL for pricing and rebalancing and strategic dispatching equilibria in multi-regional ride-hailing appear only as arXiv preprints (2603.05000; 2609.09493). We found no peer-reviewed MARL study of *competing parcel carriers* with routing-level actions.

### 6.4 Decision-focused and contextual learning, and DRO

Predict-then-optimize and decision-focused learning (Bertsimas & Kallus, 2020; Elmachtoub & Grigas, 2022) and Wasserstein DRO (Mohajerin Esfahani & Kuhn, 2018; Kuhn, Shafiee & Wiesemann, 2025) are established; routing-specific DRO includes Zhang et al. (2021) and Ghosal and Wiesemann (2020). Recent Omega papers apply DRO to adjacent urban problems: emergency resource allocation and routing with distributionally robust chance constraints (Wang et al., 2023), data-driven robust ferry-vehicle management at airports (Omega 133), target-oriented DRO for micromobility battery swapping (Jin et al., 2026) and two-stage DRO for drone-supported relief (Gao et al., 2026); a TR-E (2026) paper treats mixed drone–courier fleets. In crowdsourced delivery, prescriptive ML for courier scheduling (Behrendt, Savelsbergh & Wang, 2023) and robust workforce management (Operations Research, 2023.0125) are close relatives. None adds competition. We found no peer-reviewed distributionally robust *game* for routing.

### 6.5 Simulation and digital twins

Agent-based simulation dominates evaluation in the competitive-auction (Figliozzi et al.) and large-scale collaboration (Los et al.) streams. We found no peer-reviewed "digital twin" of a multi-carrier urban delivery market; the term should be defined operationally if used.

## 7. Datasets, benchmarks and evaluation metrics

**Datasets.**
- **Amazon Last Mile Routing Research Challenge** (Merchán et al., 2024, Transportation Science 58(1):8–11): the first large public dataset of real operational routes, comprising a training set of 6,112 and an evaluation set of 3,072 historical routes driven by Amazon delivery drivers in 2018 across five major US metropolitan areas; single-carrier.
- **LaDe** (Wu et al., 2024, KDD; arXiv 2306.10675): Cainiao pickup and delivery data covering 10,677k packages of 21k couriers over 6 months of real-world operation in several Chinese cities, with trajectories and road networks; single-company.
- A Meituan food-delivery dataset for an INFORMS TSL challenge (2025) appeared only in a preprint's references and was not verified.

*Implication:* **no public dataset records competing carriers serving the same territory.** Multi-carrier instances must be built, e.g. by splitting Amazon or LaDe demand among N synthetic carriers with market-share and overlap parameters, and documented as a methodological contribution.

**Metrics.**
1. *Price of anarchy and stability:* worst or best equilibrium social cost divided by the merged-fleet optimum.
2. *Exploitability (NashConv):* total gain from unilateral best responses, essential for approximately learned equilibria.
3. *Social cost decomposition:* carrier costs, service level (lateness, slot availability), externalities (vehicle-km, curb occupancy, emissions).
4. *Fairness:* across carriers (profit relative to stand-alone), couriers (earnings and multi-homing welfare, as in Benjaafar et al., 2022, and Alnaggar et al., 2024) and neighbourhoods (spatial equity of lockers and hubs).
5. *Out-of-sample robustness* under distribution shift, the motivation for DRO.

## 8. Synthesis

### 8.1 Comparison of key papers

| Reference | Competition model | Uncertainty | Routing fidelity | Solution method | Data | Key finding / limitation |
|---|---|---|---|---|---|---|
| Figliozzi, Mahmassani & Jaillet (2004–2007) | Sequential auctions among carriers | Dynamic arrivals; deterministic travel times | Truckload PDP / TSP with profits | Opportunity-cost pricing; simulation | Synthetic | Only routing-level competitive dynamic model; truckload, no learning |
| Cerulli et al. (2024), TS 58(5) | Stackelberg: platform leads independent carriers | None | Profitable tour per carrier | Bilevel MILP, branch-and-cut | Synthetic | Ignoring carrier reactions misestimates profit; followers do not interact |
| Catalano & Migliore (2014) | Stackelberg: public designer leads carrier equilibrium | Demand scenarios | Network/terminal | Bilevel heuristic | Case study | High public share, few consolidation terminals |
| Li, Huang, Yue & Wang (2024), TR-E 183 | Duopoly sharing collection points | Not established | Reduced-form | Analytical game | None | When sharing infrastructure with a rival pays |
| Mercurio et al. (2026), IJPE | Cooperative locker-placement game | Deterministic | Reduced-form | Cooperative game theory | Generated instances | Stable allocations exist for a network class and most instances |
| Bernstein, DeCroix & Keskin (2021), MSOM 23(5) | Price Nash, two platforms; multi-homing | Congestion effects | None (queues) | Equilibrium analysis | None | All players worse off when all drivers multi-home (ride-hailing) |
| Ghosal & Wiesemann (2020), OR 68(3) | Single carrier | Demand ambiguity (moments) | Full CVRP | DR chance constraints, branch-and-cut | Benchmarks | DRO preserves CVRP structure; usable as best-response oracle |
| Zhang et al. (2021), OR 69(2) | Single carrier | Travel-time ambiguity (Wasserstein) | Full VRPTW | Branch-and-cut, metaheuristic | Data-driven simulation | Risk index cuts lateness and overfitting |
| Los et al. (2020–2025) | Cooperative auctions, MAS | Dynamic orders | Full PDP | Combinatorial auctions, MAS | Dutch platform data | Up to 79% savings; benchmark, not PoA |
| Merchán et al. (2024), TS 58(1) | n/a | Real operations | Real routes | Dataset | Amazon 2018 | Single-carrier; needs synthetic splitting |

### 8.2 Research gaps

1. **G1 – No routing-level equilibrium model of competing parcel carriers under stochasticity.** We found no paper computing Nash or generalized Nash equilibria among N carriers each solving a stochastic VRP while competing for customers or sharing capacity.
2. **G2 – No Stackelberg–GNEP model with a public leader.** Regulator models treat followers as aggregate or independent; bilevel last-mile models (Cerulli et al., 2024) have a platform leader and non-interacting followers.
3. **G3 – Ride-hailing to parcel transfer is unvalidated.** Multi-homing results come from queue-based ride-hailing models and are untested for couriers with multi-stop, capacitated, time-windowed routes.
4. **G4 – No efficiency theory for tour-based games.** PoA and price of stability for atomic tour-based delivery games lack bounds and systematic estimates.
5. **G5 – Data-driven robustness in games.** DRO is mature for single-carrier routing, but distributionally robust or learning-augmented equilibrium computation for routing games is absent.
6. **G6 – Benchmarks.** No public multi-carrier dataset or protocol exists, and exploitability is not reported in routing.

### 8.3 Positioning statement for the Omega manuscript

*A regulator-led, data-driven Stackelberg game in which a city authority or neutral platform sets access prices or capacities for micro-hubs and curb zones; N competing carriers respond in a generalized Nash equilibrium coupled by those capacities; and each carrier's best response is a Wasserstein-distributionally robust stochastic routing problem estimated from operational data. Equilibria are computed by learning-augmented best-response dynamics with neural or combinatorial-optimization-layer oracles and certified by exploitability bounds; performance is reported as price of anarchy, social cost and fairness on multi-carrier instances constructed from public last-mile data.* This addresses G1, G2, G5 and G6 and matches the special issue's topics: DRO, learning-augmented optimization, urban logistics, platform operations, public–private coordination and multistakeholder decision-making.

## 9. Future directions

1. **Variational-equilibrium pricing of shared capacity:** use the GNEP coupling multiplier as a curb or hub price and study when a leader can implement the merged-fleet optimum.
2. **Distributionally robust routing games:** existence and uniqueness under Wasserstein hedging, and how the ambiguity radius shifts the PoA.
3. **Learning equilibria with combinatorial oracles:** fictitious play or policy-space response oracles with neural VRP solvers, reporting exploitability.
4. **Courier multi-homing with routing:** nest a mean-field courier population under N parcel platforms and test whether ride-hailing welfare results carry over.
5. **Competition through time slots and promises:** extend choice-based slot management to oligopoly.
6. **Benchmarks:** release multi-carrier instance generators on Amazon and LaDe data.

## 10. Consolidated reference list

Flags: [V] verified; [P] partially verified; [U] not re-verified, check all fields and retrieve DOI.

**Competition, auctions, games and platforms**
1. Figliozzi, M.A., Mahmassani, H.S., Jaillet, P. (2003). Framework for study of carrier strategies in auction-based transportation marketplace. Transportation Research Record 1854, 162–170. [V]
2. Figliozzi, M.A., Mahmassani, H.S., Jaillet, P. (2004). Competitive performance assessment of dynamic vehicle routing technologies using sequential auctions. Transportation Research Record 1882, 10–18. [V]
3. Figliozzi, M.A., Mahmassani, H.S., Jaillet, P. (2005). Impacts of auction settings on the performance of truckload transportation marketplaces. Transportation Research Record 1906. [P]
4. Figliozzi, M.A., Mahmassani, H.S., Jaillet, P. (2006). Quantifying opportunity costs in sequential transportation auctions for truckload acquisition. Transportation Research Record 1964. https://doi.org/10.1177/0361198106196400127 [V]
5. Figliozzi, M.A., Mahmassani, H.S., Jaillet, P. (2007). Pricing in dynamic vehicle routing problems. Transportation Science 41(3), 302–318. [P]
6. Figliozzi, M.A., Mahmassani, H.S., Jaillet, P. (2008). Repeated auction games and learning dynamics in electronic logistics marketplaces. Springer chapter. https://link.springer.com/chapter/10.1007/978-3-540-75261-5_7 [P]
7. Cerulli, M., Archetti, C., Fernández, E., Ljubić, I. (2024). A bilevel approach for compensation and routing decisions in last-mile delivery. Transportation Science 58(5), 1076–1100. https://doi.org/10.1287/trsc.2023.0129 [V]
8. Catalano, M., Migliore, M. (2014). A Stackelberg-game approach to support the design of logistic terminals. Journal of Transport Geography 41. [P]
9. (Authors to verify) (2025). The multi-commodity flow problem with outsourcing decisions. Transportation Research Part B. [P]
10. Xu, Z., Sun, X. (2024). Economic analysis of on-street parking with urban delivery. Transportation Science 58(6), 1300–1318. https://doi.org/10.1287/trsc.2024.0569 [P]
11. Liu, J., Ma, W., Qian, S. (2023). Optimal curbside pricing for managing ride-hailing pick-ups and drop-offs. Transportation Research Part C 146, 103960. [P]
12. Dey, S.S., Pérez, B.O., Richards, L., et al. (2019). Demystifying urban curbside freight management: Strategic incremental approach from Washington, D.C. Transportation Research Record. https://doi.org/10.1177/0361198119863773 [V]
13. (Authors to verify) (2026). Commercial Vehicle Load Zone programs in US cities. Transportation Research Part A 211, 105122. [P]
14. Li, L., Huang, M., Yue, X., Wang, X. (2024). The strategic analysis of collection delivery points network sharing in last-mile logistics market. Transportation Research Part E 183, 103423. https://doi.org/10.1016/j.tre.2024.103423 [V]
15. (Authors to verify) (c. 2020). When and how to share first-mile parcel collection service. European Journal of Operational Research. [P]
16. Mercurio, F., Schlicher, L., Rohmer, S.U.K., Van Woensel, T. (2026). Collaboration in parcel locker networks—A cooperative game for the joint placement of lockers. International Journal of Production Economics. [P]
17. Lyu, G., Teo, C.-P. (2022). Last mile innovation: The case of the Locker Alliance network. Manufacturing & Service Operations Management 24(5). [U]
18. Taylor, T.A. (2018). On-demand service platforms. Manufacturing & Service Operations Management 20(4), 704–720. https://doi.org/10.1287/msom.2017.0678 [V]
19. Bai, J., So, K.C., Tang, C.S., Chen, X., Wang, H. (2019). Coordinating supply and demand on an on-demand service platform with impatient customers. Manufacturing & Service Operations Management 21(3), 556–570. https://doi.org/10.1287/msom.2018.0707 [V]
20. Benjaafar, S., Ding, J.-Y., Kong, G., Taylor, T. (2022). Labor welfare in on-demand service platforms. Manufacturing & Service Operations Management 24(1), 110–124. https://doi.org/10.1287/msom.2020.0964 [V]
21. Bernstein, F., DeCroix, G.A., Keskin, N.B. (2021). Competition between two-sided platforms under demand and supply congestion effects. Manufacturing & Service Operations Management 23(5), 1043–1061. https://doi.org/10.1287/msom.2020.0866 [P]
22. Bakos, Y., Halaburda, H. (2020). Platform competition with multihoming on both sides: Subsidize or not? Management Science 66(12), 5599–5607. [P]
23. (Authors to verify) (2026). Platform competition and driver multi-homing in ride-hailing markets. Transportation Research Part E. [P]
24. (Authors to verify) (2023). An economic analysis of on-demand food delivery platforms: Impacts of regulations and integration with ride-sourcing platforms. Transportation Research Part E 171, 103019. [P]
25. Di, X., Ban, X.J. (2019). A unified equilibrium framework of new shared mobility systems. Transportation Research Part B 129, 50–78. [P]
26. Mofidi, S.S., Pazour, J.A. (2019). When is it beneficial to provide freelance suppliers with choice? Transportation Research Part B 126, 1–23. [U]
27. Horner, H., Pazour, J., Mitchell, J.E. (2021). Optimizing driver menus under stochastic selection behavior for ridesharing and crowdsourced delivery. Transportation Research Part E 153, 102419. [U]
28. Ausseil, R., Pazour, J.A., Ulmer, M.W. (2022). Supplier menus for dynamic matching in peer-to-peer transportation platforms. Transportation Science 56(5), 1304–1326. [U]
29. Orda, A., Rom, R., Shimkin, N. (1993). Competitive routing in multiuser communication networks. IEEE/ACM Transactions on Networking 1(5), 510–521. [P]
30. Cominetti, R., Correa, J.R., Stier-Moses, N.E. (2009). The impact of oligopolistic competition in networks. Operations Research 57(6), 1421–1437. [U]
31. Acemoglu, D., Ozdaglar, A. (2007). Competition and efficiency in congested markets. Mathematics of Operations Research 32(1), 1–31. [U]
32. Roughgarden, T., Tardos, É. (2002). How bad is selfish routing? Journal of the ACM 49(2), 236–259. [U]
33. Correa, J.R., Schulz, A.S., Stier-Moses, N.E. (2004). Selfish routing in capacitated networks. Mathematics of Operations Research 29(4), 961–976. [U]
34. Wardrop, J.G. (1952). Some theoretical aspects of road traffic research. Proceedings of the Institution of Civil Engineers 1(3), 325–378. [U]
35. Rosenthal, R.W. (1973). A class of games possessing pure-strategy Nash equilibria. International Journal of Game Theory 2, 65–67. [U]
36. Monderer, D., Shapley, L.S. (1996). Potential games. Games and Economic Behavior 14(1), 124–143. [U]
37. Facchinei, F., Kanzow, C. (2010). Generalized Nash equilibrium problems. Annals of Operations Research 175, 177–211. [U]
38. Li, M., Qin, Z., Jiao, Y., et al. (2019). Efficient ridesharing order dispatching with mean field multi-agent reinforcement learning. Proceedings of WWW 2019, 983–994. https://doi.org/10.1145/3308558.3313433 [V]
39. Laurière, M., Perrin, S., Girgin, S., et al. (2022). Scalable deep reinforcement learning algorithms for mean field games. Proceedings of ICML 2022, PMLR, 12078–12095. [P]

**Collaborative / cooperative multi-carrier routing**

40. Gansterer, M., Hartl, R.F. (2018). Collaborative vehicle routing: A survey. European Journal of Operational Research 268(1), 1–12. https://doi.org/10.1016/j.ejor.2017.10.023 [V]
41. Gansterer, M., Hartl, R.F. (2020). Shared resources in collaborative vehicle routing. TOP 28(1), 1–20. [P]
42. Gansterer, M., Hartl, R.F. (2020). Pushing frontiers in auction-based transport collaborations. Omega 94, 102042. [P]
43. Gansterer, M., Hartl, R.F. (2016). Request evaluation strategies for carriers in auction-based collaborations. OR Spectrum 38, 3–23. [U]
44. Gansterer, M., Hartl, R.F., Savelsbergh, M. (2020). The value of information in auction-based carrier collaborations. International Journal of Production Economics 221, 107485. [U]
45. Guajardo, M., Rönnqvist, M. (2016). A review on cost allocation methods in collaborative transportation. International Transactions in Operational Research 23(3), 371–392. https://doi.org/10.1111/itor.12205 [P]
46. Cleophas, C., Cottrill, C., Ehmke, J.F., Tierney, K. (2019). Collaborative urban transportation: Recent advances in theory and practice. European Journal of Operational Research 273(3), 801–816. [U]
47. Krajewska, M.A., Kopfer, H., Laporte, G., Ropke, S., Zaccour, G. (2008). Horizontal cooperation among freight carriers: Request allocation and profit sharing. Journal of the Operational Research Society 59(11), 1483–1491. [U]
48. Berger, S., Bierwirth, C. (2010). Solutions to the request reassignment problem in collaborative carrier networks. Transportation Research Part E 46(5), 627–638. [U]
49. Wang, X., Kopfer, H. (2014). Collaborative transportation planning of less-than-truckload freight. OR Spectrum 36, 357–380. [U]
50. Özener, O.Ö., Ergun, Ö., Savelsbergh, M. (2011). Lane-exchange mechanisms for truckload carrier collaboration. Transportation Science 45(1), 1–17. [U]
51. Xu, S.X., Huang, G.Q., Cheng, M. (2017). Truthful, budget-balanced bundle double auctions for carrier collaboration. Transportation Science 51(4), 1365–1386. [U]
52. Los, J., Schulte, F., Spaan, M.T.J., Negenborn, R.R. (2020). The value of information sharing for platform-based collaborative vehicle routing. Transportation Research Part E 141, 102011. [V]
53. Los, J., Schulte, F., Gansterer, M., Hartl, R.F., Spaan, M.T.J., Negenborn, R.R. (2020). Decentralized combinatorial auctions for dynamic and large-scale collaborative vehicle routing. ICCL 2020, LNCS, Springer, 215–230. https://doi.org/10.1007/978-3-030-59747-4_14 [V]
54. Los, J., Schulte, F., Spaan, M.T.J., Negenborn, R.R. (2022). Strategic bidding in decentralized collaborative vehicle routing. LDIC 2022, Springer. https://doi.org/10.1007/978-3-031-05359-7_21 [V]
55. Los, J., Schulte, F., Gansterer, M., Hartl, R.F., Spaan, M.T.J., Negenborn, R.R. (2025). Large-scale collaborative vehicle routing. Annals of Operations Research 350(1), 201–233. [V]

**Stochastic, dynamic and robust VRP; crowdsourced delivery**

56. Gendreau, M., Laporte, G., Séguin, R. (1996). Stochastic vehicle routing. European Journal of Operational Research 88(1), 3–12. [U]
57. Gendreau, M., Jabali, O., Rei, W. (2016). Future research directions in stochastic vehicle routing. Transportation Science 50(4), 1163–1173. https://doi.org/10.1287/trsc.2016.0709 [P]
58. Oyola, J., Arntzen, H., Woodruff, D.L. (2018). The stochastic vehicle routing problem, a literature review, part I: Models. EURO Journal on Transportation and Logistics 7(3), 193–221. https://doi.org/10.1007/s13676-016-0100-5 [P]
59. Pillac, V., Gendreau, M., Guéret, C., Medaglia, A.L. (2013). A review of dynamic vehicle routing problems. European Journal of Operational Research 225(1), 1–11. [U]
60. Psaraftis, H.N., Wen, M., Kontovas, C.A. (2016). Dynamic vehicle routing problems: Three decades and counting. Networks 67(1), 3–31. [P]
61. Ritzinger, U., Puchinger, J., Hartl, R.F. (2016). A survey on dynamic and stochastic vehicle routing problems. International Journal of Production Research 54(1), 215–231. [P]
62. Bertsimas, D.J. (1992). A vehicle routing problem with stochastic demand. Operations Research 40(3), 574–585. [U]
63. Laporte, G., Louveaux, F., Mercure, H. (1992). The vehicle routing problem with stochastic travel times. Transportation Science 26(3), 161–170. [U]
64. Florio, A.M., Hartl, R.F., Minner, S. (2020). New exact algorithm for the vehicle routing problem with stochastic demands. Transportation Science 54(4), 1073–1090. [U]
65. Gounaris, C.E., Wiesemann, W., Floudas, C.A. (2013). The robust capacitated vehicle routing problem under demand uncertainty. Operations Research 61(3), 677–693. [P]
66. Ghosal, S., Wiesemann, W. (2020). The distributionally robust chance-constrained vehicle routing problem. Operations Research 68(3), 716–732. https://doi.org/10.1287/opre.2019.1924 [V]
67. Ghosal, S., Ho, C.P., Wiesemann, W. (2024). A unifying framework for the capacitated vehicle routing problem under risk and ambiguity. Operations Research 72(2), 425–443. [P]
68. Zhang, Y., Zhang, Z., Lim, A., Sim, M. (2021). Robust data-driven vehicle routing with time windows. Operations Research 69(2), 469–485. https://doi.org/10.1287/opre.2020.2043 [V; co-authors after first author P]
69. Jaillet, P., Qi, J., Sim, M. (2016). Routing optimization under uncertainty. Operations Research 64(1), 186–200. [U]
70. Wang, W., Yang, K., Yang, L., Gao, Z. (2023). Distributionally robust chance-constrained programming for multi-period emergency resource allocation and vehicle routing in disaster response operations. Omega, 102915. https://doi.org/10.1016/j.omega.2023.102915 [P; volume to check]
71. Ulmer, M.W., Goodson, J.C., Mattfeld, D.C., Thomas, B.W. (2020). On modeling stochastic dynamic vehicle routing problems. EURO Journal on Transportation and Logistics 9(2), 100008. https://doi.org/10.1016/j.ejtl.2020.100008 [P]
72. Soeffker, N., Ulmer, M.W., Mattfeld, D.C. (2022). Stochastic dynamic vehicle routing in the light of prescriptive analytics: A review. European Journal of Operational Research 298(3), 801–820. https://doi.org/10.1016/j.ejor.2021.07.014 [V]
73. Ulmer, M.W., Soeffker, N., Mattfeld, D.C. (2018). Value function approximation for dynamic multi-period vehicle routing. European Journal of Operational Research 269, 883–899. [P]
74. Ulmer, M.W., Goodson, J.C., Mattfeld, D.C., Hennig, M. (2019). Offline–online approximate dynamic programming for dynamic vehicle routing with stochastic requests. Transportation Science 53, 185–202. [P]
75. Ulmer, M.W., Thomas, B.W. (2020). Meso-parametric value function approximation for dynamic customer acceptances in delivery routing. European Journal of Operational Research 285, 183–195. [P]
76. Chen, X., Ulmer, M.W., Thomas, B.W. (2022). Deep Q-learning for same-day delivery with vehicles and drones. European Journal of Operational Research 298, 939–952. [P]
77. Ulmer, M.W. (2020). Dynamic pricing and routing for same-day delivery. Transportation Science 54(4), 1016–1033. [U]
78. Agatz, N., Campbell, A., Fleischmann, M., Savelsbergh, M. (2011). Time slot management in attended home delivery. Transportation Science 45(3), 435–449. [U]
79. Yang, X., Strauss, A.K., Currie, C.S.M., Eglese, R. (2016). Choice-based demand management and vehicle routing in e-fulfillment. Transportation Science 50(2), 473–488. [U]
80. Bertsimas, D., Jaillet, P., Martin, S. (2019). Online vehicle routing: The edge of optimization in large-scale applications. Operations Research 67(1). https://doi.org/10.1287/opre.2018.1763 [P]
81. Archetti, C., Savelsbergh, M., Speranza, M.G. (2016). The vehicle routing problem with occasional drivers. European Journal of Operational Research 254(2), 472–480. https://doi.org/10.1016/j.ejor.2016.03.049 [V]
82. Arslan, A.M., Agatz, N., Kroon, L., Zuidwijk, R. (2019). Crowdsourced delivery—A dynamic pickup and delivery problem with ad hoc drivers. Transportation Science 53(1), 222–235. [P]
83. Gdowska, K., Viana, A., Pedroso, J.P. (2018). Stochastic last-mile delivery with crowdshipping. Transportation Research Procedia 30, 90–100. [P]
84. Torres, F., Gendreau, M., Rei, W. (2022). Vehicle routing with stochastic supply of crowd vehicles and time windows. Transportation Science 56(3). https://doi.org/10.1287/trsc.2021.1101 [P]
85. Voigt, S., Kuhn, H. (2022). Crowdsourced logistics: The pickup and delivery problem with transshipments and occasional drivers. Networks 79(3). [P]
86. Alnaggar, A., Gzara, F., Bookbinder, J.H. (2021). Crowdsourced delivery: A review of platforms and academic literature. Omega 98, 102139. https://doi.org/10.1016/j.omega.2019.102139 [V]
87. Alnaggar, A., Gzara, F., Bookbinder, J.H. (2024). Compensation guarantees in crowdsourced delivery: Impact on platform and driver welfare. Omega 122, 102965. https://doi.org/10.1016/j.omega.2023.102965 [V]
88. Alnaggar, A., Bhatt, S. (2026). Fleet size planning in crowdsourced delivery: Balancing service level and driver utilization. Omega 139. [P]
89. Di Puglia Pugliese, L., Ferone, D., Festa, P., Guerriero, F. (2023). The crowd-shipping with penalty cost function and uncertain travel times. Omega 115, 102776. [P; DOI and middle authors to check]
90. Mancini, S., Gansterer, M. (2022). Bundle generation for last-mile delivery with occasional drivers. Omega 108, 102582. https://doi.org/10.1016/j.omega.2021.102582 [V]
91. (Authors to verify) (2025). Dynamic assignment of delivery order bundles to in-store customers. Omega 133, 103246. [U]
92. Cosmi, M., et al. (2025). Courier assignment in meal delivery via integer programming: A case study in Rome. Omega. [U]
93. Behrendt, A., Savelsbergh, M., Wang, H. (2023). A prescriptive machine learning method for courier scheduling on crowdsourced delivery platforms. Transportation Science 57(4). [U]
94. (Authors to verify) (2024/2025). Robust workforce management with crowdsourced delivery. Operations Research. https://doi.org/10.1287/opre.2023.0125 [P]

**Learning, DRO and data**

95. Vinyals, O., Fortunato, M., Jaitly, N. (2015). Pointer networks. Advances in NeurIPS 28. [U]
96. Nazari, M., Oroojlooy, A., Snyder, L., Takáč, M. (2018). Reinforcement learning for solving the vehicle routing problem. Advances in NeurIPS 31. [U]
97. Kool, W., van Hoof, H., Welling, M. (2019). Attention, learn to solve routing problems! ICLR 2019. [U]
98. Kwon, Y.-D., Choo, J., Kim, B., et al. (2020). POMO: Policy optimization with multiple optima for reinforcement learning. Advances in NeurIPS 33. [U]
99. Bengio, Y., Lodi, A., Prouvost, A. (2021). Machine learning for combinatorial optimization: A methodological tour d'horizon. European Journal of Operational Research 290(2), 405–421. [U]
100. Hildebrandt, F.D., Thomas, B.W., Ulmer, M.W. (2023). Opportunities for reinforcement learning in stochastic dynamic vehicle routing. Computers & Operations Research 150, 106071. [V]
101. Hildebrandt, F.D., Bode, A., Ulmer, M.W., Mattfeld, D.C. (2026). Shaping decision models for stochastic dynamic optimization problems via reinforcement learning. Networks 88. https://doi.org/10.1002/net.70039 [P]
102. Baty, L., Jungel, K., Klein, P.S., Parmentier, A., Schiffer, M. (2024). Combinatorial optimization-enriched machine learning to solve the dynamic vehicle routing problem with time windows. Transportation Science 58(4). [U]
103. Parmentier, A. (2022). Learning to approximate industrial problems by operations research classic problems. Operations Research 70(1), 606–623. [P]
104. Bertsimas, D., Kallus, N. (2020). From predictive to prescriptive analytics. Management Science 66(3), 1025–1044. [U]
105. Elmachtoub, A.N., Grigas, P. (2022). Smart "predict, then optimize". Management Science 68(1), 9–26. [U]
106. Mohajerin Esfahani, P., Kuhn, D. (2018). Data-driven distributionally robust optimization using the Wasserstein metric. Mathematical Programming 171, 115–166. [U]
107. Kuhn, D., Shafiee, S., Wiesemann, W. (2025). Distributionally robust optimization. Acta Numerica 34. [U]
108. Jin, et al. (2026). Target-oriented distributionally robust optimization for battery swapping in shared micromobility systems. Omega. [U]
109. Gao, P., et al. (2026). Two-stage distributionally robust optimization approach for drone-supported facility location and post-disaster relief distribution. Omega 139. [P]
110. (Authors to verify) (2025). Data-driven robust two-stage ferry vehicle management at airports. Omega 133. [P]
111. (Authors to verify) (2026). Data-driven optimization of a mixed fleet of drones and human couriers for on-demand delivery under uncertainty. Transportation Research Part E. [P]
112. Merchán, D., Arora, J., Pachon, J., Konduri, K., Winkenbach, M., Parks, S., Noszek, J. (2024). 2021 Amazon Last Mile Routing Research Challenge: Data set. Transportation Science 58(1), 8–11. https://doi.org/10.1287/trsc.2022.1173 [V]
113. Wu, L., Wen, H., Hu, H., et al. (2024). LaDe: The first comprehensive last-mile express dataset from industry. Proceedings of the 30th ACM SIGKDD Conference. https://doi.org/10.1145/3637528.3671548 [V]

**Preprints (context only):** P1 arXiv:2209.07618 (differentiable bilevel programming for Stackelberg congestion games); P2 arXiv:2603.05000 (competitive multi-operator RL for pricing and rebalancing); P3 arXiv:2609.09493 (strategic dispatching equilibrium in multi-regional ride-hailing); P4 arXiv:2203.15412 (stochastic generalized Nash model of ride-hailing competition; title to check).

## Must-read papers

Figliozzi, Mahmassani & Jaillet (2007, TS); Cerulli et al. (2024, TS 58(5)); Gansterer & Hartl (2018, EJOR 268(1)); Los et al. (2025, Annals of OR 350(1)); Ghosal & Wiesemann (2020, OR 68(3)); Zhang et al. (2021, OR 69(2)); Soeffker, Ulmer & Mattfeld (2022, EJOR 298(3)) with Ulmer et al. (2020, EURO JTL); Hildebrandt, Thomas & Ulmer (2023, C&OR 150); Bernstein, DeCroix & Keskin (2021, MSOM) with Benjaafar et al. (2022, MSOM) for ride-hailing evidence; Li, Huang, Yue & Wang (2024, TR-E 183); Alnaggar, Gzara & Bookbinder (2021, Omega 98); Merchán et al. (2024, TS 58(1)) with Wu et al. (2024, KDD).
