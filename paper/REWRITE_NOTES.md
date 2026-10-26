# Rewrite notes

Source files: `paper/main.tex` (new), `paper/frontmatter.tex` (title, author, abstract, keywords: the only template-dependent block), `paper/highlights.txt`, `paper/graphical_abstract_notes.md`, `paper/make_tables.py`, `paper/tables/`. The old manuscript is untouched in `paper/old/main_v1_59pages.tex`.

## Result

- Class `elsarticle` (preprint, 12 pt). No class-specific macros in the body; `\journal{}` was removed. To re-template, replace the preamble and `frontmatter.tex`; `\citep/\citet` need natbib, the tables use `booktabs` and `adjustbox`.
- Main text through the conclusion: about 35 pages (the declarations end at the top of page 36); references pp. 36-42; appendices A-F pp. 43-62 (62 pages in all). Compiled with pdflatex + bibtex until no undefined reference or citation; the log has no overfull box.
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
- The wording "certificate/certified" was removed from the text.

## References

Verified against Crossref (DOI records) or the arXiv abstract page on 2026-10-26: Yang-Meng-Lee 2004 (TR-B 38(6)), Sandholm 2002 (REStud 69(3)), Maheshwari et al. arXiv 2204.05507 = CDC 2022 (doi 10.1109/CDC51059.2022.9992685), Maheshwari et al. arXiv 2405.16716 = IEEE TAC 71(6), 2026 (found by title search in Crossref), Wolpert-Tumer 2001 (Adv. Complex Syst.), Marden-Wierman 2013, Beauchene 2016 (doi 10.1007/s11238-015-9502-3), Feik et al. arXiv 2604.23669, Masiha et al. arXiv 2602.23277, Duguet et al. arXiv 2511.09021, Liu-Oudjane-Wan arXiv 2011.12604. A script check of every DOI in `references.bib` against Crossref titles found no mismatch (the GHS-POP DOI is a DataCite DOI and is not in Crossref). Not in Crossref and not re-verified: Buchanan 1969 and Barnett 1980 (American Economic Review, classical), Chvatal 1973 (technical report), the ICML papers (McMahan et al., Jaggi). Wolpert-Tumer 1999 (arXiv cs/9908014) exists but is not cited.

## The author must still check

1. Competing-interest and funding statements are placeholders. The Elsevier generative-AI declaration is the author's decision; no such statement is in the text.
2. Read in full: Beauchene 2016, Feik et al. 2026, Ghosal-Ho-Wiesemann 2024 (and its e-companion), Masiha et al. 2026, Liu-Ma-Ma 2026 (not cited in the text; check whether it should be), and Maheshwari et al. (both versions) against the ARP claims.
3. Scopus / Web of Science novelty search (all searches so far were web and index searches, snippet level).
4. Grade-C parameters (fees, wages, drops, van capacities, market shares) in `data/parameters/SOURCES.md`; they drive the sign and size of the leader's gains.
5. Lean: the text states that the file compiles with no `sorry` (the file contains the word only in a comment). Lean was not available in this environment and was not rebuilt; run `lake build` in `lean/` before submission.
6. The experiments behind Table E5, the ZMC checks, the theory tests and the tiny-game verification still use the price-and-branch oracle; re-run them with the exact oracle if the journal requires it. The grid for six cities is a reduced exact grid.
7. The wording "ARP reaches X% of the grid" compares against the best grid point, which is a two-parameter family; consider reporting gains against the social optimum instead.
8. The venue memo (`docs/VENUES.md`) was not used; the abstract and keywords can be shortened or reordered for the chosen journal. The title block and `\journal` line are the only template-bound parts.
9. The CTS referee review in `docs/NOVELTY_AND_PROOF_REVIEW.md` concerns an abandoned method and was not used.
