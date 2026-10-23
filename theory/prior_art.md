# Prior-art check

Searches were run on 2026-10-23 with a general web search engine plus fetches of arXiv abstract and HTML pages. They were snippet-level, except where a full-text read is noted. They do not replace a Scopus or Web of Science search, which should be run before submission.

## Queries run

1. `Approximate Nash equilibria in large nonconvex aggregative games Shapley-Folkman Liu Oudjane Wan`
2. `Bonnans Liu Oudjane Pfeiffer Wan large-scale nonconvex optimization randomization gap estimation Frank-Wolfe Shapley-Folkman`
3. `Shapley-Folkman lemma pure strategy approximate equilibrium finite games many players Starr existence nonconvex`
4. `ambiguity guarantees existence of pure strategy equilibrium games imprecise beliefs E-admissibility equilibrium existence`
5. `kernel digraph NP-complete reduction pure Nash equilibrium existence polymatrix game two actions`
6. `equilibrium in beliefs ambiguity set radius around actual play pure equilibrium exists epsilon equilibrium equivalence game theory`
7. `Nash equilibrium E-admissible imprecise probabilities game credal set "E-admissible" equilibrium`
8. `Azrieli Shmaya Lipschitz games pure approximate equilibrium existence; Kalai large games purification`
9. `Shapley-Folkman ambiguity robust game equilibrium nonconvex "Shapley-Folkman" uncertainty set beliefs`
10. `Udell Boyd bounding duality gap separable problems linear constraints Shapley-Folkman Aubin Ekeland`
11. `Nash equilibrium carriers vehicle routing game column generation pricing problem integer programming games competition last-mile`
12. `Carvalho Lodi Pedroso computing equilibria integer programming games sample generation method EJOR`
13. `Apt Simon Wojtczak coordination games directed graphs polymatrix win-loss pure Nash equilibrium NP-complete`

Fetched pages: arXiv 2011.12604 (abstract and the ar5iv full text, first 100k characters), arXiv 2601.19003 (abstract) and arXiv 2604.23669 (abstract). Papers checked in the earlier referee report (`docs/NOVELTY_AND_PROOF_REVIEW.md`) are not repeated here, except where they matter.

## Papers found and their relevance

| Paper | URL | Relevance |
|---|---|---|
| Liu, Oudjane, Wan, *Approximate Nash equilibria in large nonconvex aggregative games*, MOR 48(3) 2023 | https://arxiv.org/abs/2011.12604 ; https://pubsonline.informs.org/doi/10.1287/moor.2022.1321 | **Contains the candidate core.** Convexified game (each player's cost replaced by its convex envelope over generators), existence of a PNE of the convexified game via Kakutani/Rosen, and Shapley–Folkman on the generator sets. Lemma 5.6: every generator point is a best reply to the convexified rivals. The ε-PNE has ε = 2H((√q+1)MΔ/n)^γ (aggregate = average; rescaled to the sum, this is N-independent). There is also a randomized version and a gradient-proximal algorithm with O(n³) iterations for O(1/n)-PNE. No ambiguity or credal sets. |
| Bonnans, Liu, Oudjane, Pfeiffer, Wan, *Large-scale nonconvex optimization: randomization, gap estimation, numerical resolution*, SIOPT 2023 | https://arxiv.org/abs/2204.02366 | Frank–Wolfe on the randomized (relaxed) aggregative problem, with the LMO decomposed into N independent subproblems, stochastic recovery and an O(1/N) gap. This is the optimization analogue of our D1 branch. |
| Udell, Boyd, *Bounding duality gap for separable problems with linear constraints*, COAP 2016 | https://arxiv.org/abs/1410.4158 | Convexify, solve, randomized rounding; the gap is bounded by the number of active constraints. Aubin–Ekeland (1976) is the origin. Covers Corollary 8.6 (shared capacities). |
| Dubois-Taine, d'Aspremont, *Frank–Wolfe meets Shapley–Folkman* | https://arxiv.org/abs/2406.18282 | Constructs primal solutions meeting the Shapley–Folkman gap bound via FW. Close to our Sparsify step. |
| Dey, Xu, *Asymptotically tight Lagrangian dual … improved error bound of Shapley–Folkman*, 2026 | https://arxiv.org/abs/2601.19003 | Refined Shapley–Folkman error; vanishing nonconvexity under smoothness. Relevant only to the open problem of improving the d-dependence. |
| Starr, *Quasi-equilibria in markets with non-convex preferences*, Econometrica 1969 | https://econweb.ucsd.edu/~rstarr/SFarticle.pdf | Origin of the Shapley–Folkman–Starr approximation in economies. |
| Azrieli, Shmaya, *Lipschitz games*, MOR 2013 | https://arxiv.org/abs/1107.1520 | Pure ε-equilibria in Lipschitz games, ε → 0 with N. Probabilistic method. |
| Goldberg, Katzman, *PPAD-complete pure approximate Nash equilibria in Lipschitz games* | https://arxiv.org/abs/2207.09962 | Finding pure approximate equilibria is PPAD-complete even for Lipschitz polymatrix games. Motivates Conjecture 7.7. |
| Kalai, *Large robust games*, Econometrica 2004 | (classical) | Self-purification in large anonymous games. |
| Apt, Simon, Wojtczak, *Coordination games on weighted directed graphs*, MOR 47(2) 2022 | https://arxiv.org/abs/1910.02693 | NP-completeness of pure-NE existence on unweighted directed graphs, hence strong NP-hardness for polymatrix games. Theorem 7.3's hardness is therefore of a known kind. |
| Carvalho, Lodi, Pedroso, *Computing equilibria for integer programming games*, EJOR 2022 | https://arxiv.org/abs/2012.07082 | Complexity of deciding NE existence in IPGs, and a sample-generation algorithm (finite games: exact NE; Lipschitz: approximate). Our D2 relaxation (double oracle) is of this type. |
| Carvalho, Dragotto, Lodi, Sankaranarayanan, Cut-and-Play | https://arxiv.org/abs/2111.05726 | Cutting-plane computation of equilibria in IPGs. Not new on our side. |
| Dragotto, Scatamacchia, ZERO Regrets, IJOC 2023 | https://arxiv.org/abs/2111.06382 | Pure NE selection via integer programming. |
| Feik, Lanzetti, Bolognani, Dörfler, Paccagnan, *Strategically robust aggregative games* | https://arxiv.org/abs/2604.23669 | Convex aggregative games with an optimal-transport ambiguity ball around the aggregate. Existence of a pure strategically robust Wardrop equilibrium (convex case only); PoA against the radius. No nonconvex or discrete strategy sets, no Shapley–Folkman, no E-admissibility (abstract-level check). |
| Christodoulou, Koutsoupias, Spirakis, ε-equilibria in congestion games | https://arxiv.org/abs/0804.3160 | PoA and PoS of ε-equilibria as functions of ε. Our Lemma 10.1 plus Prop. 10.2 is a transfer to this framework. |
| Crespi, Radi, Rocca, *Insights on the theory of robust games* | https://arxiv.org/abs/2002.00225 | Robust-optimization equilibria are ε-Nash of the nominal game, the converse direction of absorption. |
| Beauchêne, *Solution concepts for games with ambiguous payoffs*, Theory Decis. 2016 | https://ideas.repec.org/a/kap/theord/v80y2016i2p245-269.html | Nash, Crawford equilibrium in beliefs and *pure equilibrium in beliefs*. Necessary and sufficient conditions for existence and equivalence. **Closest conceptual neighbour of Theorem 6.1** (pure equilibria made possible by belief ambiguity). Abstract-level check only: no aggregative structure, width bound or Shapley–Folkman visible. **Read in full before submission.** |
| Lo 1996 (equilibrium in beliefs under uncertainty); Klibanoff 1996; Marinacci 2000 (ambiguous games); Dow–Werlang 1994 | (classical) | Equilibrium notions with ambiguous beliefs about opponents. Beliefs contain the actual play: our consistency assumption A4. |
| CSEF working papers on equilibria with ambiguous belief correspondences (e.g. wp397, wp425, wp618) | https://www.csef.it/WP/wp397.pdf | Existence under imprecision-averse or -loving attitudes with convexity of belief correspondences. Convex strategy settings. |
| Liu (ISIPTA 2011), Nau (ISIPTA 2011), Nakharutai–Troffaes–Caiado | https://isipta11.sipta.org/proceedings/papers/s012.pdf ; https://arxiv.org/abs/1906.12215 | Imprecise probabilities in games and the computation of E-admissible and maximal options. No aggregative or existence-threshold results. |
| Chvátal 1973; Fraenkel 1981 (kernels NP-complete; planar, degree ≤ 3) | (classical) | Source problem for Theorem 7.3. |
| Chen–Deng–Teng 2009; Daskalakis–Goldberg–Papadimitriou 2009 | (classical) | PPAD-completeness used in Prop. 7.6. |
| Competitive VRP / carrier games | (query 11) | Nothing found combining carrier routing games, column generation and imprecise beliefs. Absence of search hits is weak evidence. |

## Verdict per claimed result

| Result (main.tex) | Verdict | Reason | Narrowest defensible claim |
|---|---|---|---|
| Candidate core: Shapley–Folkman rounding gives an N-independent ε-NE (Cor. 6.2, Thm 6.1(b) second and third terms without credal sets) | **KNOWN** | Liu–Oudjane–Wan 2023 (incl. the own-term "+1" and the best-reply property of generators); Starr 1969; Rashid 1983; Carmona–Podczeck 2009 | None. Cite LOW23 and present Cor. 6.2 as a restatement. **Pivot executed.** |
| Lemma 3.3 (credal → mean box, clipped), Lemmas 3.4–3.6 | KNOWN / elementary | Support-function algebra; Troffaes 2007; Aghassi–Bertsimas 2006 for the Γ surcharge | Technical lemmas only. |
| Prop. 5.2 (relaxed = mixed equilibrium under affine coupling) | KNOWN / elementary | Linearity of expectation | — |
| **Thm 6.1 (credal absorption: exact pure ICNE_E/M/ID for δ ≥ δ̂, N-uniform width bound)** | **PLAUSIBLY NEW** (as a statement); ingredients classical | No source found giving a belief width, uniform in N, that guarantees pure E-admissible or maximal equilibria in finite nonconvex aggregative games. Closest: Beauchêne 2016 (pure equilibrium in beliefs, qualitative), LOW23 (precise ε-NE), Crespi et al. (converse direction). Risk: a referee may call it "LOW23 plus the observation that an ε-gap can be moved into the belief set". The proof of (a) is a few lines. | "For finite aggregative games with affine coupling, belief imprecision of width σ_max·min{N−1, d+1, 1+√(d ln 2d /2)} guarantees a pure E-admissible (hence maximal and ID) equilibrium, computable from any mixed equilibrium; the bound is attained." |
| Prop. 7.1 (tightness of the support-selection bound) | PLAUSIBLY NEW but minor | Example | Part of the Thm 6.1 package. |
| Prop. 7.2 (d-linear ε lower bound) | INCREMENTAL | Standard product construction; such lower bounds for Shapley–Folkman-type approximations are folklore | Part of the package. |
| Thm 7.3 (strong NP-completeness of ICNE_C(δ) ≠ ∅ under D2, all four criteria, all δ < 1/(2Δ⁺+1)) and Cor. 7.4 (inapproximability of δ_0) | **INCREMENTAL** | Pure-NE existence is NP-complete in polymatrix and graphical games (Apt–Simon–Wojtczak; Gottlob–Greco–Scarcello). Our reduction is a direct kernel encoding. New aspects: rank-one bilinear D2 structure, credal criteria, a width interval, and the inapproximability corollary for the existence threshold. | "Deciding whether imprecise equilibria exist is strongly NP-complete under vehicle-count congestion for every width below an explicit constant, while under exposure-based congestion they always exist." |
| Prop. 7.6 (PPAD-hardness of the D2 relaxation) | KNOWN technique | Bimatrix embedding | Remark-level. |
| Thm 8.1–8.2 (D1: FW + LP sparsification + conditional-expectation rounding; certified η) | **INCREMENTAL** | Aubin–Ekeland; Udell–Boyd; Bonnans et al. 2023; Dubois-Taine–d'Aspremont | "Explicit, certifiable constants for the Cournot–congestion potential, extended to Γ-maximin via the surcharge game." |
| Thm 8.5 (certificates) | KNOWN technique | LP and cutting planes | — |
| Algorithm RSRC as a whole | **INCREMENTAL** | Each phase is known: relaxation (FW or double oracle), sparsification (Shapley–Folkman vertex), rounding, certification. Its output certificate (exact δ_cert of imprecise equilibrium) is the new element. | "An algorithm whose output carries an exact imprecise-equilibrium width certificate, with an a priori N-uniform guarantee." Do **not** call it a new algorithm in the methods sense. |
| Prop. 9.1 (monotone curves), Ex. 3.7 (Γ not nested) | KNOWN / elementary | Nesting; CKS 2011 analogue | — |
| Prop. 9.3 (symmetric benchmark, corrected sign rule) | INCREMENTAL | Linear algebra | Application result. |
| Lemma 10.1, Prop. 10.2–10.3 | INCREMENTAL / conditional | CKS 2011; Roughgarden smoothness; potential PoS | Application result. |

## Overall verdict

- The Starr-type rounding theorem for aggregative games with nonconvex strategy sets **already exists** (LOW23, MOR 2023), with essentially the bound proposed, including the own-term. Its optimization counterpart with Frank–Wolfe also exists (Bonnans et al. 2023; Udell–Boyd 2016). The candidate core does **not** survive as a novelty claim. Moreover, for the city instances (N = 4–5 ≤ d = 2Z), the Shapley–Folkman step does not bind.
- The pivot: under imprecise beliefs, the rounding error is absorbed into the belief width. This yields exact pure imprecise equilibria and an N-uniform existence threshold bound (Thm 6.1) that is attained. The contrasts are with Γ-maximin, where it fails, with D2, where existence below an explicit width is strongly NP-complete, and with D1, where existence holds at every width. Together these form a coherent theory-first package. **Its novelty is moderate.** The most likely referee objection is that Thm 6.1(a) is a short observation layered on LOW23. The answer is that the paper's content is the full picture (absorption bound, tightness, complexity phase split, failure for Γ, certificates), not any single deep lemma.
- **Before submission:** read Beauchêne 2016 in full, check the full text of Feik et al. 2026, and search Scopus for "pure equilibrium" AND (ambiguity OR "imprecise probabilit*") AND (aggregative OR congestion).
