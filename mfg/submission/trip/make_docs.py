#!/usr/bin/env python3
"""TRIP package, part 2: highlights, cover letter, declarations, CRediT, title page (full author data), data statement,
suggested reviewers, README. Adapted from ../make_ready_docs.py and ../build_anon.py. Run after build_trip.py."""
import os, re, shutil, subprocess, sys, zipfile
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from trip_config import *
from build_trip import pages
from docx import Document
from docx.shared import Pt

CREDIT_DANG = ('Quang-Vinh Dang: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Resources, '
          'Data curation, Writing - original draft, Writing - review & editing, Visualization, Project administration.')
CREDIT = CREDIT_DANG + ' Dat Le: Conceptualization, Writing - original draft. Minh-Ngoc Dinh: Supervision, Writing - review & editing.'
DOI_ = 'The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.'
FUND = 'This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.'
ZEN = f'Zenodo DOI: {ZENODO_DOI}' if ZENODO_DOI else 'Zenodo DOI: to be added'
DATA = (f'Code, instances, result files and the Lean development are available at {GITHUB} (folder mfg); the city data are the '
        f'processed data of the companion paper. {ZEN}.')
AI = ('During the preparation of this work the authors used Claude (Anthropic) to support the writing of the manuscript. After using this tool, '
      'the authors reviewed and edited the content as needed and take full responsibility for the content of the published article.')
AUTHORS = [('Quang-Vinh Dang', 'British University Vietnam, Hung Yen, Vietnam', 'vinh.dq4@buv.edu.vn', '0000-0002-3877-8024'),
           ('Dat Le', 'Department of Science, Technology, and International Projects, Ho Chi Minh City University of Economics and Finance, Ho Chi Minh City, 700000, Vietnam', 'datla@uef.edu.vn', '0009-0005-5038-8570'),
           ('Minh-Ngoc Dinh (corresponding author)', 'Millennia Education, Ho Chi Minh City, Vietnam', 'minh.dinh@maeducation.com', '0000-0003-4026-6068')]
MAIN_PAGES = pages(f'{H}/manuscript.pdf')
flat = zipfile.ZipFile(f'{H}/latex_source.zip').read('main.tex').decode()
NREFS = flat.count('\\bibitem')
src = open(f'{MFG}/paper/main.tex').read()
title = re.sub(r'\s+', ' ', re.search(r'\\title\{(.*?)\}\n', src, re.S).group(1).replace('\\\\', ' ')).strip()

def newdoc():
    d = Document(); d.styles['Normal'].font.name = 'Times New Roman'; d.styles['Normal'].font.size = Pt(12); return d
def md_runs(p, text):
    for i, part in enumerate(re.split(r'\*\*', text)):
        r = p.add_run(re.sub(r'\*([^*]+)\*', r'\1', part)); r.bold = (i % 2 == 1)
def to_pdf(docx):
    subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', os.path.dirname(docx), docx], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

hl = [l.strip() for l in open(f'{H}/templates/highlights.txt') if l.strip()]
assert 3 <= len(hl) <= 5 and all(len(x) <= 85 for x in hl)
open(f'{H}/highlights.txt', 'w').write('\n'.join(hl) + '\n')
d = newdoc(); d.add_paragraph().add_run('Highlights').bold = True
for x in hl: d.add_paragraph(x, style='List Bullet')
d.save(f'{H}/highlights.docx')

letter = open(f'{H}/templates/cover_letter.md').read().replace('{MAIN_PAGES}', str(MAIN_PAGES)).replace('{NREFS}', str(NREFS))
open(f'{H}/cover_letter.md', 'w').write(letter)
d = newdoc()
for blk in letter.strip().split('\n\n'):
    for line in blk.split('\n'):
        md_runs(d.add_paragraph(), re.sub(r'^- ', '', line).rstrip())
d.save(f'{H}/cover_letter.docx'); to_pdf(f'{H}/cover_letter.docx')

d = newdoc(); d.add_paragraph().add_run('Declaration of competing interest').bold = True; d.add_paragraph(DOI_)
d.add_paragraph().add_run('Funding').bold = True; d.add_paragraph(FUND); d.save(f'{H}/declaration_of_interest.docx')
d = newdoc(); d.add_paragraph().add_run('CRediT authorship contribution statement').bold = True; d.add_paragraph(CREDIT_DANG); d.add_paragraph('Dat Le: Conceptualization, Writing - original draft.'); d.add_paragraph('Minh-Ngoc Dinh: Supervision, Writing - review & editing.'); d.save(f'{H}/credit_statement.docx')
open(f'{H}/data_availability_statement.txt', 'w').write(DATA + '\n')
shutil.copy(f'{H}/templates/suggested_reviewers.md', f'{H}/suggested_reviewers.md')

# separate title page (anonymous manuscript carries none of this)
abstract = re.sub(r'\s+', ' ', re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', flat, re.S).group(1)).strip()
abstract = re.sub(r'\$([^$]*)\$', lambda m: m.group(1).replace('\\tfrac', '').replace('^{', '^').replace('}', ''), abstract).replace('\\,', ' ').replace('~', ' ').replace('{}', '')
kw = [k.strip() for k in re.search(r'\\begin\{keyword\}(.*?)\\end\{keyword\}', flat, re.S).group(1).split('\\sep')]
d = newdoc(); d.add_paragraph().add_run('Title page').bold = True
def head(t): d.add_paragraph().add_run(t).bold = True
head('Title'); d.add_paragraph(title)
head('Authors')
for n, aff, em, orc in AUTHORS:
    d.add_paragraph(f'{n}. {aff}. E-mail: {em}. ORCID: {orc}.')
head('Corresponding author'); d.add_paragraph('Minh-Ngoc Dinh, Millennia Education, Ho Chi Minh City, Vietnam, minh.dinh@maeducation.com. (Submitting author: Quang-Vinh Dang.)')
head('Keywords'); d.add_paragraph('; '.join(kw))
head('Author contributions (CRediT)'); d.add_paragraph(CREDIT)
head('Declaration of competing interest'); d.add_paragraph(DOI_)
head('Funding'); d.add_paragraph(FUND)
head('Data availability'); d.add_paragraph(DATA)
head('Declaration of generative AI and AI-assisted technologies in the manuscript preparation process'); d.add_paragraph(AI)
head('Related manuscript'); d.add_paragraph('A companion paper by the first author is under review at another journal and is cited in the manuscript as Anonymous (2026) in the anonymous version and as Dang (2026) in the non-anonymous version. An earlier version of this manuscript was assessed at initial review by another Transportation Research journal and was not advanced to full review.')
d.save(f'{H}/title_page.docx'); to_pdf(f'{H}/title_page.docx')

readme = f'''# TRIP submission package (Transportation Research Interdisciplinary Perspectives)

Corresponding author: Minh-Ngoc Dinh; submitting author: Quang-Vinh Dang.\n\nRequirements applied: Guide for Authors for TRIP as pasted by the author, read 2026-11-19. Single anonymized review: upload the
ANONYMOUS manuscript as the main file and the title page separately. The manuscript is {MAIN_PAGES} pages (A4, 11 pt); no page limit is stated.

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
'''
open(f'{H}/README.md', 'w').write(readme)
print('pages', MAIN_PAGES, 'refs', NREFS)
