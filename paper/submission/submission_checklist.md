# Submission checklist: Omega special issue

**Call:** Omega 55th Anniversary Special Issue "Data-Driven Optimization for Smart Cities"
**Article type to select in Editorial Manager:** `VSI: Omega55: Smart Cities`
**System:** https://submit.elsevier.com/OMEGA
**Deadline:** 31 August 2027
**Guest Editors:** Kai Pan (lead), Ilke Bakir, Hao Fu, Jorge A. Sefair, Duygu Tas, Ming Zhao
**Manuscript (resubmission, OMEGA-D-26-03236):** `paper/main.tex` (class `elsarticle`, preprint, 11 pt, A4, single column, 1.5 line spacing via `setspace`, no line numbers), compiled `paper/main.pdf`: 34 pages including abstract, figures, tables and references; Supplementary Material `paper/supplement.tex`, 50 pages. The upload package is in `paper/submission/ready/` (see its README).

## 1. Files for upload

| File | Content | Status |
|---|---|---|
| `paper/main.pdf` and sources (`main.tex`, `frontmatter.tex`, `tables/`, `references.bib`, `../figures/`) | manuscript | compiled, no undefined references or citations |
| `paper/highlights.txt` | 5 highlights, 71-83 characters each, no numbers | ready (Elsevier: 3-5 bullets, at most 85 characters each, uploaded as a separate file) |
| `paper/graphical_abstract_notes.md` | recipe for the graphical abstract | the image itself still has to be made (optional for Elsevier; the call may welcome it) |
| `paper/submission/cover_letter.md` | cover letter to the Guest Editors | ready; insert the date |
| `paper/submission/suggested_reviewer_areas.md` | eight areas for the reviewer-suggestion fields | the author must pick names |
| `paper/submission/anticipated_objections.md` | internal memo, not for upload | for the author's preparation |

## 2. Requirements and status

| Item | Status |
|---|---|
| Article type | select `VSI: Omega55: Smart Cities` |
| Title | present (frontmatter) |
| Author, affiliation, e-mail, ORCID | present: Quang-Vinh Dang, British University Vietnam, Hung Yen, Vietnam; vinh.dq4@buv.edu.vn; ORCID 0000-0002-3877-8024 |
| Abstract | 242 words (check the limit stated in Omega's Guide for Authors) |
| Keywords | six: urban logistics; bilevel optimization; vehicle routing; imprecise probabilities; congestion games; city charges |
| Highlights | present (see above) |
| Graphical abstract | to be made from `paper/graphical_abstract_notes.md`; Elsevier asks for at least 531 x 1328 pixels (height x width), readable at about 5 x 13 cm, in TIFF, EPS, PDF or Office format (re-check on the submission site) |
| Declaration of competing interest | in the manuscript: "no competing financial interests or personal relationships". Elsevier may also ask for it as a separate form or file at submission |
| Funding | in the manuscript: "no specific grant from any funding agency in the public, commercial or not-for-profit sectors" |
| Data and code availability | in the manuscript, with https://github.com/vinhqdang/Competing-Carriers-under-Uncertainty. Consider a DOI-bearing archive (for example a tagged release deposited in a repository) so the link is persistent, and check whether Omega asks for a separate data statement or data link in Editorial Manager |
| Author contribution statement | not in the manuscript. Elsevier journals commonly ask for a CRediT author statement; the author decides the roles to list |
| Acknowledgements | none in the manuscript; add if applicable |
| Reference style | the manuscript uses `elsarticle-num-names` (numbered, author names in the text via natbib). `\citep` and `\citet` are already used throughout, so switching to an author-year style needs only the `.bst` file (and the class option) if Omega requires it. Check the current Guide for Authors |
| Reference accuracy | all DOIs were checked against Crossref (see `REWRITE_NOTES.md`); not in Crossref and not re-verified: Buchanan 1969, Barnett 1980, Chvatal 1973, the ICML papers. Four neighbours were read from reference lists or abstracts only (Section 9) |
| Figure resolution | the figures are PNG rasters: effective resolution at printed size is about 220-320 dpi (E2 instruments about 220, E4 imprecision about 250, ARP calls about 250, DIP calls and equilibria map about 315). Figure 1 is vector (TikZ). Elsevier asks for at least 300 dpi for halftones and 1000 dpi for line art in production; regenerate the plots as PDF or EPS from the plotting scripts before acceptance. This is not a barrier at first submission |
| Length | Omega limit: 35 pages including abstract, figures, tables, main text and references. The main manuscript has 34; long proofs, extended data descriptions, full tables and further experiments are in the separate Supplementary Material |
| Template line | the class prints "Preprint submitted to Elsevier" on page 1; fine for review, remove or change when the final template is used |
| Anonymity | Omega uses single-anonymised review as a rule (check the Guide); the manuscript carries the author's name and a GitHub link containing the user name |

## 3. Items the author must still do

1. **Scopus / Web of Science novelty search.** All searches so far were web and index searches at snippet level (Section 9 says so). A database search on the closest topics (leader pricing above routing games, probability-box or credal routing, best-response cuts for implementation) is outstanding.
2. **Reading the remaining neighbours.** Dabia et al. (2013), Ioachim et al. (1998) and Pessoa et al. (2015) were read in part or at abstract level. They matter for the BRL claims: the window dominance is claimed for this loss, not as the idea of comparing cost functions (Ioachim), and it was not compared with function-label or resource-extension labelling code (Dabia, Irnich), while robust resource-constrained pricing by labelling is known for budgeted uncertainty (Pessoa). Also still to read in full, from `REWRITE_NOTES.md`: Ghosal--Ho--Wiesemann (journal version and e-companion), Feik et al., Masiha et al., Maheshwari et al. (both versions) and Lanzetti et al., against the ARP and absorption claims. Section 9 records the reading depth; update it after reading.
3. **Declaration on the use of generative AI tools.** Whether to include a declaration is the author's decision and nothing in the manuscript, cover letter or notes makes a statement either way. For reference, Elsevier's policy page (summarised in `docs/VENUES.md`, section on author declarations, as read on 2026-10-26) says, in outline: authors who used generative AI or AI-assisted tools in preparing the manuscript are asked to disclose this in a separate statement placed before the references, with a stated heading; the statement is published; basic spelling and grammar checks and reference managers without a generative function are exempt from disclosure; such tools cannot be listed as authors; the authors remain responsible for the content; and the policy has separate rules for images. Re-read the current page and the Omega Guide for Authors, then decide.
4. **Lean.** Appendix G states that `lake build CCU` succeeds. Lean was not available when the text was last edited; run `lake build CCU` in `lean/` and confirm before submission.
5. **Grade-C parameters** (fees, wages, drops, van capacities, market shares) in `data/parameters/SOURCES.md` drive the size and sign of the leader's gains. Improve any that can be improved cheaply, or keep the wording in Sections 6, 8.1 and 9.
6. **Experiments still on the price-and-branch oracle** (engine comparison, ZMC checks, theory tests, tiny-game verification): decide whether to re-run them with the exact oracle (Section 9 states the current status).
7. **Reviewer suggestions.** Pick names from `suggested_reviewer_areas.md`; decide whether to list opposed reviewers.
8. **Preprint.** If a preprint is posted before submission, say so in the cover letter and check Omega's policy. Nothing in the cover letter currently refers to one.
9. **Cover letter.** Insert the date; the letter states that the manuscript is original, unpublished and not under review elsewhere, which only the author can confirm.
10. **Final read of the PDF** for the abstract word limit, the "Preprint submitted to Elsevier" line, and the figure files, then upload the highlights and graphical abstract in the dedicated Editorial Manager slots.

## 4. How the manuscript meets the call

- Topics: urban logistics and vehicle routing (Sections 3, 4.1-4.2, 7.1); robust optimisation under data uncertainty (probability boxes with unknown dependence; Sections 4.1, 7.2, 7.6); public--private coordination (city leader above carriers; Sections 3.3, 4.4, 4.5, 8); platform-type competition (Cournot carriers; Section 7.4).
- Method-driven contribution: three algorithms with proofs, a theory section and a computational study on nine cities, with the novelty level of each part stated (Section 1).
- Transferable insights: Section 8 (managerial and smart-city implications), stated with its limits.
- Not in the paper, and not claimed anywhere: machine learning, learning-augmented optimisation, digital twins, real-time decisions, human-in-the-loop experiments. Section 8.2 and the cover letter say so; the author may want to prepare an answer if the editors ask (see objection 9 in `anticipated_objections.md`).
