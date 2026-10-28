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
