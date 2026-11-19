# TRIP submission package (Transportation Research Interdisciplinary Perspectives)

Corresponding author: Minh-Ngoc Dinh; submitting author: Quang-Vinh Dang.

Requirements applied: Guide for Authors for TRIP as pasted by the author, read 2026-11-19. Single anonymized review: upload the
ANONYMOUS manuscript as the main file and the title page separately. The manuscript is 38 pages (A4, 11 pt); no page limit is stated.

| Upload slot | File |
|---|---|
| Manuscript, editable source (anonymous) | `latex_source_anonymous.zip` (one `main.tex` plus `Figure_k.png`; plain pdflatex, run twice) |
| Manuscript, reading copy (anonymous) | `manuscript_anonymous.pdf` (a PDF is not accepted as the source file) |
| Title page (authors, addresses, ORCIDs, corresponding author, CRediT, declarations, data, tool-use statement) | `title_page.docx` (and `title_page.pdf`) |
| Figures, one file each | `figures/Figure_1.png` ... (300 dpi) and `figures/Figure_1.pdf` ... (vector) |
| Highlights (3 to 5, at most 85 characters) | `highlights.docx`, `highlights.txt` |
| Graphical abstract | `graphical_abstract.pdf`, `graphical_abstract.png` (3240 x 1320 px) |
| Declaration of competing interest | `declaration_of_interest.docx` (also fill in the online tool: nothing to declare) |
| CRediT statement | `credit_statement.docx` (in the non-anonymous manuscript and on the title page) |
| Cover letter | `cover_letter.docx`, `.pdf`, `.md` (date left as DATE_TO_FILL) |
| Research data (Option C, required) | Zenodo deposit in `zenodo/` (see `ZENODO_STEPS.md`); data statement in `data_availability_statement.txt` |
| Suggested reviewers (areas only) | `suggested_reviewers.md` |
| Non-anonymous copies (for the editor, or if the system asks for them) | `manuscript.pdf`, `latex_source.zip` (author names included) |

## Rebuild and checks

    python3 mfg/submission/trip/build_trip.py        # compile paper, flatten, zips, PDFs, figure files
    python3 mfg/submission/trip/make_graphical_abstract.py
    python3 mfg/submission/trip/make_docs.py         # highlights, cover letter, declarations, title page
    python3 mfg/submission/trip/build_zenodo.py      # Zenodo archive
    python3 mfg/submission/trip/verify_ready.py       # all checks, ends with OVERALL PASS

## Decisions for the author

1. Zenodo: create the deposit (`ZENODO_STEPS.md`), then set `ZENODO_DOI` in `trip_config.py` and run `make_docs.py` to put the DOI into the title page and data statement; it is never written into the anonymous manuscript.
2. Licence: the deposit uses MIT for code, CC BY 4.0 for results, and ODbL 1.0 for the derived OpenStreetMap city files; the GitHub repository is Apache-2.0.
3. The publisher's tool-use declaration section is present in both manuscript versions and on the title page, unchanged from the earlier package.
4. Names of suggested reviewers, and the DATE_TO_FILL in the cover letter.
5. Whether the cover letter should name the earlier journal (it does not).
6. References: DOIs not added (not verifiable here); five arXiv items are marked as preprints.
