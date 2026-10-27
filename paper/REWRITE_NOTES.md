# Rewrite notes

Source files: `paper/main.tex` (new), `paper/frontmatter.tex` (title, author, abstract, keywords: the only template-dependent block), `paper/highlights.txt`, `paper/graphical_abstract_notes.md`, `paper/make_tables.py`, `paper/tables/`. The old manuscript is untouched in `paper/old/main_v1_59pages.tex`.

## Result

- Class `elsarticle` (preprint, 12 pt). No class-specific macros in the body; `\journal{}` was removed. To re-template, replace the preamble and `frontmatter.tex`; `\citep/\citet` need natbib, the tables use `booktabs` and `adjustbox`.
- (First round, superseded by the update round below.) Main text about 35 pages. Compiled with pdflatex + bibtex until no undefined reference or citation; the log has no overfull box.
- Abstract 238 words, six keywords, five highlights of at most 75 characters, graphical-abstract note rewritten.
- Order: Introduction (three stacked difficulties, contributions with novelty levels, what is not new or claimed), Related work, Model, Algorithms (BRL, branch-and-price, engine, DIP, ARP), Equilibrium theory, Data, Computational study (research questions first), Managerial implications (one page), Limitations, Conclusion, availability, appendices (A equilibrium proofs, B BRL, C ZMC, D DIP, E ARP, F tables and figures).

## What changed

- Story: algorithm/optimisation first. The theory section moved after the algorithms and is no longer the headline. ZMC is a remark in Section 4.3 and Appendix C with its negative result (it did not beat plain best response on the city games).
- ARP added (Section 4.5, Appendix E, Section 7.4.2) with the city runs, tiny games and contraction constants; the marginal tariff theorem is stated as classical in mechanism.
- Every number in the text comes from `tables/macros.tex` or a generated table. `make_tables.py` gained `t_extra` (full-grid subsets, grid call counts, ARP step ratios, ARP-DIP gap). The ARP tables and macros of the earlier attempt were checked against `results/summary_arp.csv`, `arp_tiny.csv`, `arp_rates.csv` and kept. One error was found in `theory/new_algorithm_D/results.md`: its tiny-game "hits the optimum" column divides by all 210 games (35%, 37%, 60%) while the generated table correctly divides by the 136 games with a positive gain (54%, 92% for DIP); the paper uses the generated table.
- Symbol changes: contraction rate and the lot-asymmetry ratio are `\varrho`; congestion slope in delivery units is `\kappa` (was `\zeta` in the DIP notes); traffic-box widths are `\varpi` (were `\kappa`); the numbered approximations are S1-S5 (were A1-A5, which clashed with the assumption labels).
- Tables and figures moved to Appendix F to stay near 35 pages: city table, engine comparison (E5), equilibrium maps, E2 instrument figure, imprecision figure, coverage, parameters, sensitivity, broad-objective table, ZMC synthetic and tiny-game tables, ZMC checks, theory figures.

## Claims dropped or weakened

- Dropped: the literature-survey gap list (G1, G2, G5, G6); the "human-centred smart-city" paragraph; the "optional quality statement" section; the claim that DIP "beats" the grid without the caveat that DIP searches zone-specific charges (a richer family) than the two-parameter grid (the paper now gives the restricted-family comparison, mean 1.0, worst 0.50 in Mumbai seed 0 with a reduced grid).
- Weakened: the novelty statements for BRL (classical decomposition, new resource view and window dominance), DIP and ARP (classical principles; new parts listed narrowly), credal absorption (closely related to Liu-Oudjane-Wan), and the D1/D2 split (incremental to Apt et al.). The benchmark claim is now "released pipeline", not "first public instances". "Exact oracle covers all 27 city-seeds" is stated with the coverage limits: full 63-point grid only for New Delhi, Buenos Aires, London; reduced grids elsewhere; seed-2 DIP comparisons for Berlin, Moscow, New York use price-and-branch grids; E5, E6, the theory tests and tiny-game verification still use the old oracle.
- ARP statements are conditional: no claim about which equilibrium the carriers select; the pure-game neighbourhood bound holds for potential minimisers; ARP matches DIP in 5 of 12 runs and trails it by up to 32 points of the grid gain in the others; the Mumbai grid is a reduced one, so its shares are against a lower bound.
- Earlier selling-point wording about guarantees on computed solutions was removed from the text.

## References

Verified against Crossref (DOI records) or the arXiv abstract page on 2026-10-26: Yang-Meng-Lee 2004 (TR-B 38(6)), Sandholm 2002 (REStud 69(3)), Maheshwari et al. arXiv 2204.05507 = CDC 2022 (doi 10.1109/CDC51059.2022.9992685), Maheshwari et al. arXiv 2405.16716 = IEEE TAC 71(6), 2026 (found by title search in Crossref), Wolpert-Tumer 2001 (Adv. Complex Syst.), Marden-Wierman 2013, Beauchene 2016 (doi 10.1007/s11238-015-9502-3), Feik et al. arXiv 2604.23669, Masiha et al. arXiv 2602.23277, Duguet et al. arXiv 2511.09021, Liu-Oudjane-Wan arXiv 2011.12604. A script check of every DOI in `references.bib` against Crossref titles found no mismatch (the GHS-POP DOI is a DataCite DOI and is not in Crossref). Not in Crossref and not re-verified: Buchanan 1969 and Barnett 1980 (American Economic Review, classical), Chvatal 1973 (technical report), the ICML papers (McMahan et al., Jaggi). Wolpert-Tumer 1999 (arXiv cs/9908014) exists but is not cited.

## The author must still check

1. Declarations: competing interest and funding are set to "none" as stated by the author. Any further declaration the publisher asks for is the author's decision (see `paper/submission/submission_checklist.md`); none is in the text.
2. Read in full: Beauchene 2016, Feik et al. 2026, Ghosal-Ho-Wiesemann 2024 (and its e-companion), Masiha et al. 2026, Liu-Ma-Ma 2026 (not cited in the text; check whether it should be), and Maheshwari et al. (both versions) against the ARP claims.
3. Scopus / Web of Science novelty search (all searches so far were web and index searches, snippet level).
4. Grade-C parameters (fees, wages, drops, van capacities, market shares) in `data/parameters/SOURCES.md`; they drive the sign and size of the leader's gains.
5. Lean: the text states that the file compiles with no `sorry` (the file contains the word only in a comment). Lean was not available in this environment and was not rebuilt; run `lake build` in `lean/` before submission.
6. The experiments behind Table E5, the ZMC checks, the theory tests and the tiny-game verification still use the price-and-branch oracle; re-run them with the exact oracle if the journal requires it. The grid for six cities is a reduced exact grid.
7. The wording "ARP reaches X% of the grid" compares against the best grid point, which is a two-parameter family; consider reporting gains against the social optimum instead.
8. The venue memo (`docs/VENUES.md`) was not used; the abstract and keywords can be shortened or reordered for the chosen journal. The title block and `\journal` line are the only template-bound parts.
9. The CTS referee review in `docs/NOVELTY_AND_PROOF_REVIEW.md` concerns an abandoned method and was not used.


## Update round (closest-work edits, Lean, ten seeds, probability boxes, BRL benchmark, criterion robustness)

Page counts now: 67 pages in all; main text through the conclusion and declarations pp. 1-36; references pp. 37-43; appendices A-F pp. 44-67. Abstract 229 words. Compiled with pdflatex + bibtex, no undefined reference or citation, one 2.6 pt overfull box in the class's title-page footnote.

New generators in `make_tables.py`: `t_seeds10` (tab_seeds10, tab_seeds10b, about 90 `Ten*` macros, bootstrap CIs read from `summary_seeds10_ci.csv`), `t_ambiguity` (tab_ambig, `Amb*`), `t_brlbench` (tab_brl_labels, tab_brl_oos, tab_brl_scale, `Brl*`), `t_criterion` (tab_criterion, `Crit*`). Macro names cannot contain digits in TeX, so `macro()` now spells digits out (`AmbSaaRegTwoZero`).

### Changed claims and numbers
1. Credal absorption (intro, theory remark, conclusion, abstract, Lean text): no longer "bounded independently of the number of carriers" and no longer "the bound is attained". The text gives sigma_max min{N-1, d+1, 1+sqrt(d ln(2d)/2)}, says the N-free terms bind only for N > d (city instances: N <= 6, d >= 84, so (N-1) rho-bar applies and grows with N), that the N-1 term is attained at N = 2, and that the theorem is close to Liu-Oudjane-Wan (Lemma 5.6, Prop 2.4, Thm 2.7, Prop 2.8/Lemma 5.7) with part (a) following in two lines from their Lemma 5.6.
2. Citations: Duguet-Harks-Schmidt-Schwarz (arXiv 2506.02520) now carries best-response cuts; the Walras paper stays only as the neighbour of the clearing identity. Added Lanzetti et al. 2025, Han-Yang 2009, Ye-Yang-Tan 2015, Gottlob et al. 2005, Tchen 1980, Long-Qi-Zhang 2024, Monderer-Tennenholtz 2004, Caragiannis et al. 2010, Irnich 2008, Dabia et al. 2013, Duguet et al. 2025 (IPG), Carvalho et al. 2025. Maheshwari and Masiha descriptions corrected; Feik sentence rewritten; DIP separation step described as the Dragotto et al. inequality in charge space; BRL Thm "resource" described as immediate from the budget theorem; window dominance flagged as not compared with resource-extension or function-label dominance (Irnich 2008, Dabia et al. 2013). Search-limits sentence updated (Beauchene 2016 and Liu-Ma-Ma 2026 read at abstract level). `closest_work_additions.bib` was appended to `references.bib` (17 entries; 12 are cited; Slade, Yang-Xu-He-Meng, Wang-Yang, Chicoisne are in the bib but not cited).
3. Lean: the section now lists the seven modules, which results are full and which are cores, and what is not formalised (asymmetric-lot DIP bound, LP and epsilon parts, ARP existence/proximal form and pure-game theorems, p-boxes and BRL exactness, Hoeffding, LP vertex, NP-hardness, all computation). Lean was not rebuilt here.
4. Ten seeds replace three seeds in the main text for the equilibrium, grid, PoA and DIP/ARP statements (full 63-point grid and ARP for New Delhi, Buenos Aires, London; 9 seeds for the other cities with 3 seeds and a reduced grid for grid-derived quantities). Flipped: "congestion-only gain below 1.7% everywhere" (Buenos Aires 4 of 10 seeds, max 6.5%; London 2 of 10, max 5.4%; New Delhi 1 of 10, max 2.9%); "PoA ordering London > Buenos Aires > New Delhi in every seed" (7 of 10 seeds). Survives: congestion alone far below delivery-only (means 0.32-2.4% vs 12.1-39.8%); delivery share 0.81, 0.98, 0.82 (below one half once, New Delhi seed 0); Mumbai's share not established; PoA >= 1.10 only in London, Buenos Aires, New Delhi; priced gap at most 7.4%. DIP and ARP are now reported against the social optimum as well as the grid (grid 0.82/0.94/0.91, DIP 1.00/1.00/1.02, ARP 0.93/0.995/0.93 of the SO gain). The old "DIP reaches 104-135% of the grid" is kept only as a seeds 0-2 statement with the caveat about the richer charge family.
5. New Section 7.2 "Why probability boxes": the p-box loses in expected cost at every n <= 60 (regret 1.6-8.9% against 0.16-0.27% for SAA); the cost is the DKW band, not the unknown-dependence worst case; it buys lower overtime probability, lower CVaR_0.95 and an upper bound, and overtakes SAA under a common shock of about +0.5; Wasserstein with cross-validated radius reproduces SAA. The text says explicitly that p-boxes do not minimise expected cost.
6. BRL claims rewritten (abstract, intro, 4.1, 7.1, limitations, conclusion): advantage is proof speed and label counts at about 25 customers; label reductions on real data are 1.8-2.9x (no window) and 2.8-6.3x (quantile-vector) on metro instances and 1.6-14x / 2.7-23x on public instances; the earlier "10-100x" was removed from the text; BRL is 0.30-5.0% worse than SAA on held-out mean and 1.2-2.8% worse at the 95th percentile on the public instances, better only at N = 10 under a shifted law; exact B&P proven up to 40 zones for London and New York, not at 60 or 80, not on Augerat A-n32-k5. The public-instance study is described as an emulation.
7. New Section 7.6 "Robustness to the carriers' criterion" with a table: orderings and policy directions robust (delivery share, small congestion-only gain, PoA >= 1.10 only in three cities, -0.375 fee/n_z rule, DIP vs grid, subsidy sign); levels not (served share roughly doubles with SAA, true-cost PoA falls, PoA order of Buenos Aires and New Delhi flips, true-cost DIP gain halves, best uniform charge for the true-cost objective shrinks 58-69%). Stated in the abstract, the introduction's "what is not claimed", managerial section, limitations and conclusion. Research questions in Section 7 now include RQ2 (why p-boxes) and RQ6 (criterion robustness).
8. Housekeeping: coverage text rewritten (what still uses price-and-branch: engine comparison, ZMC checks, theory tests, tiny-game verification, DIP seed-2 comparisons for Berlin, Moscow, New York, the p-box reference runs of the criterion study, and the broad-objective social-optimum benchmark for New York, Moscow, Berlin). Tables moved to appendices to keep the main text near 36 pages: E1, grid (E2), PoA (E3), imprecision (E4), DIP per-run, metro B&P, tiny-game ARP, theory tests, scale table; figures: DIP, E2, E4, equilibrium maps.

### Unresolved inconsistencies and things to check
- `highlights.txt` contains hard-coded numbers ("6-8%", "7 of 10"); update by hand if the data change.
- A few narrative facts are typed, not generated: the list of instances proven at scale (taken from Table F.11), the "validated against branch-and-price" count (generated: `AmbValOptN`), the "40-60 calls" status-quo range, and the multiplier range 1.4-1.6 of the shock study.
- Small differences between the study documents and the generated numbers: Augerat proven cells 0 of 15 in `brl_bench_pub.csv` (the document says 0 of 18); best-charge shrinkage 58-69% computed (the document says 55-68%); delivery-share lower bound 0.88 computed (the document says 0.89).
- The out-of-sample study (Section 7.2) uses a heuristic planner (validated against branch-and-price in 9 instances, at most 0.10% above), the criterion study uses a heuristic oracle for SAA and Wasserstein carriers and price-and-branch for the p-box reference, a coarse 16-point grid and three seeds.
- Seeds 3-9 imprecision sweeps and the broad objective were not extended; ARP has ten seeds in three cities, five in Mumbai, none elsewhere.
- Table "ARP / SO" equals "ARP / DIP" in New Delhi and Buenos Aires because DIP's share is 1.00 there.
- Lean modules were not rebuilt in this environment; run `lake build CCU` before submission.


## Final editorial pass (writing quality and coherence; no result, theorem, proof, experiment or number source changed)

Page counts after this pass: 69 pages in all; main text through the conclusion pp. 1-35 (about 34.6 pages; declarations at the foot of p. 35 and top of p. 36); references pp. 36-43; appendices A-G pp. 44-69. Abstract 242 words, six keywords, five highlights of at most 83 characters, none with a number. Compiled with pdflatex + bibtex until no undefined reference or citation; one 2.6 pt overfull box in the class's title-page footnote (as before).

### Structural changes
- Introduction: contributions and scope tightened; new subsection 1.1 "Overview for the reader" (about 190 words) with Figure 1, a TikZ schematic of the three layers (carriers' routing, BRL -> carriers' game -> city's charges, DIP/ARP) and the section that addresses each. The introduction now says "in the convexified game" next to the instance-free rate of ARP, which is what Theorem 18 and the conclusion already said.
- Every algorithm subsection (4.1-4.5) and Section 5 now opens with an "In words" paragraph (what it does and why it works).
- Related work: reading-depth and search-limits statements moved out of the last paragraph and merged with the Limitations bullet "Evidence and novelty checks", so they are stated once. The Masiha description is no longer repeated in the DIP subsection.
- Section 4: repeated statements about ng-routes, column generation, price-and-branch and the Meilijson/Tchen attribution were merged; the DIP and BRL "Relation to prior work" paragraphs keep the attribution.
- Section 5: the tightness results (Propositions on the N-1 term and on the number of zones) and the efficiency results (transfer lemma, price of anarchy and stability propositions) moved to Appendix A.1, with one pointer paragraph at the end of 5.4; the Lean list moved to the new Appendix G (a three-sentence subsection 5.9 remains).
- Tables moved from the main text to Appendix F: BRL pricing on random instances (F.23), label counts (F.24), out-of-sample comparison on public instances (F.25), ARP city table (F.26). The text refers to them by label.
- Section 8 is now "Managerial and smart-city implications": 8.1 managerial (about 0.8 page), 8.2 relevance for data-driven smart-city logistics (about 0.6 page), linked to the call's themes (data-driven optimisation under data uncertainty, urban logistics, public-private coordination, implementable and human-centred decisions). 8.2 states that the study is an offline simulation: no machine learning, digital twin, real-time control or decision-maker experiment.
- Limitations: five bullets shortened; draft history removed. Conclusion rewritten as four short paragraphs (routing, charges, theory, cities).
- Abstract (242 words), keywords (urban logistics, bilevel optimization, vehicle routing, imprecise probabilities, congestion games, city charges), highlights and graphical-abstract note refreshed.

### Wording and notation
- Removed leftover wording from earlier drafts: "earlier statements of a ten- to hundred-fold reduction", "the three-seed statement/reading ... did not survive ten seeds" (results now stated positively), "several readings from the earlier three-seed analysis did not survive", "earlier price-and-branch" in three captions (now "price-and-branch").
- Notation: the model's charge per unit of congestion is now t_z (was theta_z, which clashed with the ARP damping theta); the transfer lemma's Theta_i is Upsilon_i (clashed with the overtime thresholds Theta_j); the slice multiplicity is varsigma_z (was m_z, which clashed with m_z = b_z + kappa_z); a notation sentence in Section 3 separates rho_j, bar rho and varrho and notes that t_z (charge) has no carrier index whereas t_i(p) is the traffic exposure.
- Claim strength, qualifiers that protect accuracy, attribution and all macros are unchanged; the qualifiers are stated where they matter instead of in several places.

### Not fixed (would need new work or the author's decision)
- Typed numbers outside the generated macros remain as listed in the update round above (status-quo "40-60 calls", multipliers 1.4-1.6, "37.5%" rule, "about 25 to 40 customers"). The highlights carry no number.
- The statement in Appendix G that `lake build CCU` succeeds was not re-verified here; Lean was not rebuilt.
- The elsarticle class prints "Preprint submitted to Elsevier" on the first page; remove it or switch template when the journal's template is chosen.
- Figures are PNG rasters of about 220-320 dpi at printed size; regenerate as vector files before acceptance.

### Submission package
`paper/submission/` holds `cover_letter.md`, `submission_checklist.md`, `suggested_reviewer_areas.md` and `anticipated_objections.md`.
