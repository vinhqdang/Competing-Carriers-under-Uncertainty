# Submission record

- Journal: Omega (Elsevier), special issue "Data-Driven Optimization for Smart Cities" (VSI: Omega55: Smart Cities)
- Submitted: 2026-10-28 (deadline 2027-08-31)
- Manuscript: 70 pages, single author
- Files uploaded: see paper/submission/ready/README.md
- Source state: repository `main` at the commit that adds this note

## Open items after submission
- Novelty search on Scopus / Web of Science
- Read Dabia 2013, Ioachim 1998, Pessoa 2015
- Decide on generative-AI declaration under Elsevier policy if requested
- Vector versions of figures before acceptance; Figure 5 is 314 dpi
- Release the public repository link on acceptance (withheld during review)
- Manuscript ID and review status: add here when the system assigns them

## Outcome (Ms. No. OMEGA-D-26-03236)
- Decision: reject and resubmit, on Writing and Formatting grounds only; no scientific review comments were given.
- Reason: the Guide for Authors caps the article at 35 pages including abstract, figures, tables, main text and references; ours is 70. Format required: A4 or letter, single column, 11pt, 1.5 line spacing, no line numbers.
- Allowed: non-essential material (long empirical descriptions, full data and detailed results, very technical or repetitive proofs) goes to Supplementary Materials. Case/data descriptions and other proofs are normally expected in appendices of the main manuscript.
- Resubmission requires: the cover letter must state that this is based on a previously rejected paper (OMEGA-D-26-03236) whose decision was "reject & resubmit", plus a response to the evaluation comments.

## Resubmission package (2026-10-28)
- Based on OMEGA-D-26-03236 (reject & resubmit; Writing and Formatting only). Package in `paper/submission/ready/`, built by `build_ready.py`, `make_ready_docs.py`, `verify_ready.py`.
- Main manuscript: 34 pages including abstract, figures, tables and references (previously 70; limit 35); `elsarticle` preprint, A4, single column, 11 pt, 1.5 line spacing, no line numbers. Reference list reduced from 109 to the 58 works cited in the main text.
- Supplementary Material (`paper/supplement.tex`, separate PDF and single-file zip): 50 pages, single line spacing. Holds the full model, complete theorem statements, all proofs, the extended data description and parameter tables, extended results and per-city tables, the ZMC negative result, criterion-robustness and BRL benchmark details, and the Lean description. The main text cites it as "Supplementary Material, Section S1" to "S12".
- Uploads: `manuscript_anonymous.pdf`, `anonymous_upload.zip`, `supplement.pdf`, `supplement_upload.zip`, title page, cover letter (states the previous manuscript number and decision and gives the point-by-point response), highlights, CRediT, declaration of interest, graphical abstract.

## Resubmission (2026-10-29)
- Resubmitted to Omega, special issue "Data-Driven Optimization for Smart Cities"; based on rejected OMEGA-D-26-03236 (decision "reject & resubmit").
- Package: 34-page main manuscript (A4, 11pt, 1.5 spacing, single column), 50-page Supplementary Material, cover letter dated 29 October 2026.
- New manuscript number: NOT YET RECORDED (author has not supplied it); add here.
- Open: supplement is single-spaced; confirm with the editorial office whether 1.5 spacing applies to it. Abstract is about 252 words.

## Mean-field paper submitted to Transportation Research Part B
- Title: Many small carriers: the mean-field limit of competitive urban delivery under zone-time charges
- Journal: Transportation Research Part B: Methodological (Elsevier); review model: single anonymized.
- Package: mfg/submission/package/ (manuscript 36-37 pages, anonymous variant and separate title page, highlights, graphical abstract, declarations incl. generative-AI declaration, cover letter).
- Manuscript number: NOT YET RECORDED (author has not supplied it); add here.
- Related manuscript: the Omega paper (OMEGA resubmission of 2026-10-29), cited in the TR-B paper as under review.
- Open: references have no DOIs; repository has no archival DOI (consider Zenodo); three figures are 1950 px wide (below the 2244 px full-page minimum).

## Outcome at Transportation Research Part B (2026-11-19)
- Decision: not advanced to full review (initial-review stage), signed by the Senior Associate Editor, Yafeng Yin.
- Reason given: the contributions are approximation bounds for a class of aggregative games; the paper does not sufficiently show their significance for transportation research or new insight on delivery operations and policy; the numerical studies are stylised and give limited extra support. Not a quality judgement on the mathematics.
- Editor suggestions: a venue closer to the theoretical focus; since the paper builds on the companion paper and reuses its model and application setting, the journal handling that work (Omega), subject to its scope.
- Status: free to submit elsewhere; no revision requested.

## Mean-field paper submitted to Transportation Research Interdisciplinary Perspectives (TRIP)
- Title: Many small carriers: the mean-field limit of competitive urban delivery under zone-time charges
- Authors: Quang-Vinh Dang, Dat Le, Minh-Ngoc Dinh (corresponding author); submitted by Dang.
- Journal: Transportation Research Interdisciplinary Perspectives (Elsevier, open access, single anonymized review).
- Earlier attempt: Transportation Research Part B declined at initial review (fit and transport significance), 2026-11-19.
- Package: mfg/submission/trip/ (author-named and anonymous manuscripts, one-.tex ZIPs, title page, CRediT, declarations, highlights, graphical abstract, cover letter).
- Data: Zenodo DOI 10.5281/zenodo.24357664 (reserved; publish after uploading the final ZIP if not already done). Code licence differs between the Zenodo ZIP (MIT) and the GitHub repository (Apache-2.0); to be aligned.
- Manuscript number: NOT YET RECORDED (author has not supplied it); add here.
- Related manuscript: the Omega paper (resubmitted 2026-10-29), cited as under review.
- Open: APC for open access if accepted; references have no DOIs; suggested reviewers have no names; generative-AI declaration is in the manuscript (plural, covers writing support).
