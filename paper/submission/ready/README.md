# Submission package (resubmission of OMEGA-D-26-03236): Omega, article type "VSI: Omega55: Smart Cities" (Editorial Manager)

Paths are relative to `paper/submission/ready/`. Upload slot names are the usual Editorial Manager labels; adjust them to the labels shown in the system.

## Files to upload (headline files first)

| File | Purpose | Editorial Manager slot |
|---|---|---|
| `manuscript_anonymous.pdf` | blinded main manuscript, 34 pages including abstract, figures, tables and references (Omega limit: 35); A4, single column, 11 pt, 1.5 line spacing, no line numbers; no author, affiliation, e-mail, ORCID or repository name; PDF author metadata set to "Anonymous" | Manuscript (blinded) |
| `anonymous_upload.zip` (unzipped copy in `anonymous_upload/`) | blinded LaTeX source of the main manuscript: one `main.tex`, two PNG figures, nothing else; compiles with `pdflatex` twice, no BibTeX | LaTeX source files for the blinded manuscript (if requested) |
| `supplement.pdf` | blinded Supplementary Material, 50 pages (same A4 paper and 11 pt type, single line spacing, since the page limit and the spacing rule apply to the article); no author information | Supplementary material (PDF) |
| `supplement_upload.zip` (unzipped copy in `supplement_upload/`) | blinded LaTeX source of the Supplementary Material: one `supplement.tex`, seven PNG figures; compiles with `pdflatex` twice | Supplementary material (LaTeX source, if requested) |
| `title_page.docx` (and `title_page.pdf`) | title page with author details: title, author, affiliation, corresponding author, ORCID, abstract, keywords, word count, data and code availability with the repository URL, competing-interest and funding statements, CRediT statement | Title page (with author details) |
| `credit_statement.docx` | CRediT authorship contribution statement (single author, all roles) | CRediT statement or author statement |
| `declaration_of_interest.docx` | declaration of interest and funding statement | Declaration of interest |
| `highlights.docx` (and `highlights.txt`) | five highlights, each at most 85 characters | Highlights |
| `graphical_abstract.png` (and `.pdf`) | 3120 x 1260 px, white background; left: three-layer schematic, right: DIP's share of the best grid point's gain and of its routing calls in the three ten-seed cities (from `results/summary_seeds10_ci.csv`); script `make_graphical_abstract.py` | Graphical abstract |
| `cover_letter.docx` (also `.md`, `.pdf`) | cover letter to the Guest Editors: states that this is based on the previously rejected paper OMEGA-D-26-03236 (decision reject & resubmit) and gives the point-by-point response (page limit, format, writing); insert the date | Cover letter |
| `figures_300dpi/` with `figures_table.md` | the two main-manuscript figures and the seven supplement figures as PNG, all at least 300 dpi at printed width, with a table of file, pixel size and effective dpi | Figures, if the system asks for separate figure files |

## Reference copies, not to be uploaded

| File | Purpose |
|---|---|
| `reference_not_for_upload/manuscript_with_author_REFERENCE_ONLY.pdf` | manuscript with the author block |
| `reference_upload_with_author.zip` (unzipped copy in `reference_upload_with_author/`) | the same flat source with the author block |
| `reference_not_for_upload/supplement_with_author_REFERENCE_ONLY.pdf`, `reference_supplement_upload_with_author.zip` (and folder) | the Supplementary Material with the author block |

## How the flattened sources were generated

`paper/submission/flatten.py OUTDIR {anon|titled} [main|supplement] [HIRES_FIGURE_DIR]` reads the finished build of `paper/main.tex` or `paper/supplement.tex` (`.bbl`, `.aux`) and writes one `.tex` plus PNG files (high-resolution figures from `paper/submission/hires/`). It inlines `frontmatter.tex` and all tables, replaces every number macro of `tables/macros.tex` by its literal value, inlines the compiled bibliography as a `thebibliography` environment, renders the TikZ schematic to PNG, copies the figures under flat names, and removes `adjustbox`, `xurl`, `orcidlink`, `tikz` and `microtype` (an `\shrinkbox` command replaces `adjustbox`). The anonymous variant also removes author, e-mail and address, replaces the repository sentence by a neutral one and sets the PDF author to "Anonymous". `build_ready.py` compiles both documents, runs `flatten.py` for the four variants (anonymous and with author, main and supplement), zips them and recompiles every zip in a fresh directory with plain `pdflatex` (twice); `make_ready_docs.py` builds the Word files, the title page (with page and word counts), the cover letter (page counts filled in) and the figure table; `verify_ready.py` checks the page limit, the page size and fonts, the fresh-directory compilation, the anonymity and the wording. Run the three scripts in this order after any edit of `paper/main.tex`, `paper/supplement.tex` or the tables. Cross-references from the main text to the Supplementary Material are written as text ("Supplementary Material, Section S3"), because the two documents are compiled separately; the section numbers S1 to S12 are fixed by the order of the sections in `paper/supplement.tex`. The figures were regenerated at 300 dpi from the scripts in `experiments/` in a scratch copy (stored in `paper/submission/hires/`), so the repository's `figures/` folder is unchanged.

## Remaining manual steps for the author

1. Run a novelty search in Scopus and Web of Science for the three components (probability-box labelling for routing, leader pricing from best-response cuts, credal absorption) and adjust the novelty statements if needed.
2. Generative-AI declaration: Elsevier's policy on the use of generative AI in the writing process asks authors to disclose such use in a statement placed before the reference list, and does not require a statement if none was used. No declaration has been added to any file; whether one applies is the author's decision.
3. Read Dabia et al. (2013), Ioachim et al. (1998) and Pessoa et al. (2015) in full; the manuscript states in Sections 4.1, 7.1 and 8 how far they were read and that no code based on them was run; revise those statements after reading.
4. Check the reference formatting against the journal's Guide for Authors (the source uses `elsarticle-num-names`; the inlined bibliography copies its output).
5. Choose the article type `VSI: Omega55: Smart Cities` in Editorial Manager and enter the Guest Editor information from the cover letter.
6. Insert the date in the cover letter; confirm the CRediT roles, the word count (approximate, from the PDF text) and the abstract length limit (the abstract has about 250 words).
7. Confirm with the editorial office that the Supplementary Material may be set at single line spacing, and decide whether to enter the previous manuscript number OMEGA-D-26-03236 in an Editorial Manager field as well as in the cover letter.
8. Select reviewers from the areas in `paper/submission/suggested_reviewer_areas.md`.
