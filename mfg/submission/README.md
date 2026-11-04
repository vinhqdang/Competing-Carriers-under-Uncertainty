# Submission package: Transportation Research Part B

Requirements read and applied: `TRB_requirements.md` (source: Guide for Authors pasted by the author, read 2026-11-04).
Review model: single anonymized (author name stays in the manuscript). No page limit is stated; the manuscript is 36 pages
(A4, single column, 11 pt). Everything to upload is in `package/`.

| Upload slot (Editorial Manager) | File |
|---|---|
| Manuscript (editable LaTeX source) | `package/latex_source.zip` (one `main.tex` plus `Figure_1.png` ... `Figure_12.png`; compiles with plain pdflatex, run twice) |
| Manuscript (reading copy, if a PDF is also accepted) | `package/manuscript.pdf` (a PDF is not an acceptable source file) |
| Figure files, one per figure | `package/figures/Figure_1.png` ... `Figure_12.png` (300 dpi) and `Figure_1.pdf` ... (vector) |
| Highlights (editable) | `package/highlights.docx`, `package/highlights.txt` |
| Graphical abstract | `package/graphical_abstract.pdf`, `package/graphical_abstract.png` (3240 x 1320 px) |
| Declaration of competing interest | `package/declaration_of_interest.docx` (tool field: "I have nothing to declare") |
| CRediT statement | `package/credit_statement.docx` (also in the manuscript) |
| Cover letter | `package/cover_letter.docx`, `.pdf`, `.md` (date left as DATE_TO_FILL) |
| Data statement (also in the manuscript) | `package/data_availability_statement.txt` |
| Suggested reviewers (areas only) | `package/suggested_reviewers.md` |

Not in the package: a title page and an anonymous manuscript (not needed for single-anonymized review); a generative-AI
statement (see `AI_STATEMENT_TO_DECIDE.md`).

## Rebuild and checks

    PYTHONPATH=mfg/src python3 mfg/submission/make_figures_300dpi.py   # 300 dpi PNG and vector PDF figures (identical numbers)
    python3 mfg/submission/make_graphical_abstract.py
    python3 mfg/submission/build_ready.py && python3 mfg/submission/make_ready_docs.py
    python3 mfg/submission/verify_ready.py                             # all checks, ends with OVERALL PASS

## Decisions for the author

1. Generative-AI statement: Elsevier requires one if such tools were used in preparing the manuscript; none is written. Wording template in `AI_STATEMENT_TO_DECIDE.md`.
2. Related-submission disclosure: the cover letter says only that a companion paper by the author is under review and cited as Dang (2026); the venue is not named. Name it if the editorial system asks.
3. Data: the repository is on GitHub, which has no DOI. The guide encourages depositing and citing data; consider a Zenodo deposit and add its DOI.
4. References: DOIs were not added (not verifiable here); add them if wanted. Five arXiv items are marked as preprints.
5. Suggested reviewers: areas only; add names you can vouch for.
6. Check the DATE_TO_FILL placeholder in the cover letter.
