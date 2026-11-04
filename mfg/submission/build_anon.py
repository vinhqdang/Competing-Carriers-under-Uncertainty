#!/usr/bin/env python3
"""Anonymous manuscript (no author, affiliation, e-mail, ORCID, repository link, CRediT) and the separate title page.
Outputs in package/: latex_source_anonymous.zip, manuscript_anonymous.pdf, title_page.docx, title_page.pdf.
Run after build_ready.py (needs paper/main.bbl and the figures)."""
import os, re, shutil, subprocess, sys, tempfile
H = os.path.dirname(os.path.abspath(__file__)); MFG = os.path.dirname(H); R = f'{H}/package'
sys.path.insert(0, H)
import flatten, build_ready
from docx import Document
from docx.shared import Pt

work = tempfile.mkdtemp()
flatten.build(f'{work}/src', anon=True)
build_ready.zip_dir(f'{work}/src', f'{R}/latex_source_anonymous.zip')
td, log = build_ready.fresh_compile(f'{R}/latex_source_anonymous.zip')
ok = os.path.exists(f'{td.name}/main.pdf')
print('anonymous zip compiled', ok, 'errors', len(re.findall(chr(10) + '!', log)), 'undefined', log.count('undefined'))
if ok: shutil.copy(f'{td.name}/main.pdf', f'{R}/manuscript_anonymous.pdf')
td.cleanup(); shutil.rmtree(work)

src = open(f'{MFG}/paper/main.tex').read()
title = re.search(r'\\title\{(.*?)\}\n', src, re.S).group(1)
abstract = open(f'{R}/latex_source.zip', 'rb') and None
import zipfile
flat = zipfile.ZipFile(f'{R}/latex_source.zip').read('main.tex').decode()
abstract = re.sub(r'\s+', ' ', re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', flat, re.S).group(1)).strip()
abstract = abstract.replace('\\tfrac', '').replace('$', '').replace('\\,', ' ').replace('\\ ', ' ').replace('~', ' ')
kw = [k.strip() for k in re.search(r'\\begin\{keyword\}(.*?)\\end\{keyword\}', flat, re.S).group(1).split('\\sep')]
sys.path.insert(0, H)
CREDIT = ('Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Resources, Data curation, '
          'Writing - original draft, Writing - review & editing, Visualization, Project administration.')
d = Document(); d.styles['Normal'].font.name = 'Times New Roman'; d.styles['Normal'].font.size = Pt(12)
def head(t): d.add_paragraph().add_run(t).bold = True
d.add_paragraph().add_run('Title page').bold = True
head('Title'); d.add_paragraph(title.replace('\\\\', ' ').strip())
head('Author'); d.add_paragraph('Quang-Vinh Dang')
head('Affiliation'); d.add_paragraph('British University Vietnam, Hung Yen, Vietnam')
head('Corresponding author'); d.add_paragraph('Quang-Vinh Dang, vinh.dq4@buv.edu.vn')
head('ORCID'); d.add_paragraph('0000-0002-3877-8024')
head('Author contributions (CRediT)'); d.add_paragraph('Quang-Vinh Dang: ' + CREDIT)
head('Declaration of competing interest'); d.add_paragraph('The author declares that he has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.')
head('Funding'); d.add_paragraph('This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.')
head('Data availability'); d.add_paragraph('Code, instances, result files and the Lean development are available at https://github.com/vinhqdang/Competing-Carriers-under-Uncertainty (folder mfg); the city data are the processed data of the companion paper, which is under review.')
head('Declaration of generative AI and AI-assisted technologies in the manuscript preparation process')
d.add_paragraph('During the preparation of this work the author used Claude (Anthropic) to support the writing of the manuscript. After using this tool, the author reviewed and edited the content as needed and takes full responsibility for the content of the published article.')
head('Related manuscript'); d.add_paragraph('A companion paper by the same author is under review at another journal and is cited in the manuscript as Anonymous (2026).')
d.save(f'{R}/title_page.docx')
subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', R, f'{R}/title_page.docx'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print('title page written')
