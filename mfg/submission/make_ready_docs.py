#!/usr/bin/env python3
"""Builds the Word/PDF/text files of mfg/submission/package/ (highlights, cover letter, declaration, CRediT, graphical abstract copy,
data statement) from the sources in mfg/submission/. Run after build_ready.py."""
import os, re, shutil, subprocess
from docx import Document
from docx.shared import Pt

H = os.path.dirname(os.path.abspath(__file__)); MFG = os.path.dirname(H); R = f'{H}/package'
CREDIT = ('Quang-Vinh Dang: Conceptualization, Methodology, Software, Validation, Formal analysis, Investigation, Resources, '
          'Data curation, Writing - original draft, Writing - review & editing, Visualization, Project administration.')
DOI_ = 'The author declares that he has no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.'
FUND = 'This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors.'
DATA = ('Code, instances, result files and the Lean development are available at '
        'https://github.com/vinhqdang/Competing-Carriers-under-Uncertainty (folder mfg); the city data are the processed data of the companion paper.')

def npages(pdf):
    return int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))
MAIN_PAGES = npages(f'{R}/manuscript.pdf')
NREFS = open(f'{MFG}/paper/main.bbl').read().count('\\bibitem')

def newdoc():
    d = Document(); d.styles['Normal'].font.name = 'Times New Roman'; d.styles['Normal'].font.size = Pt(12); return d
def md_runs(p, text):
    for i, part in enumerate(re.split(r'\*\*', text)):
        r = p.add_run(re.sub(r'\*([^*]+)\*', r'\1', part)); r.bold = (i % 2 == 1)
def to_pdf(docx):
    subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', os.path.dirname(docx), docx], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

hl = [l.strip() for l in open(f'{H}/highlights.txt') if l.strip()]
assert 3 <= len(hl) <= 5 and all(len(x) <= 85 for x in hl)
open(f'{R}/highlights.txt', 'w').write('\n'.join(hl) + '\n')
d = newdoc(); d.add_paragraph().add_run('Highlights').bold = True
for x in hl: d.add_paragraph(x, style='List Bullet')
d.save(f'{R}/highlights.docx')

letter = open(f'{H}/cover_letter.md').read().replace('{MAIN_PAGES}', str(MAIN_PAGES)).replace('{NREFS}', str(NREFS))
open(f'{R}/cover_letter.md', 'w').write(letter)
d = newdoc()
for blk in letter.strip().split('\n\n'):
    for line in blk.split('\n'):
        line = re.sub(r'^- ', '', line)
        md_runs(d.add_paragraph(), line.rstrip())
d.save(f'{R}/cover_letter.docx'); to_pdf(f'{R}/cover_letter.docx')

d = newdoc(); d.add_paragraph().add_run('Declaration of competing interest').bold = True; d.add_paragraph(DOI_)
d.add_paragraph().add_run('Funding').bold = True; d.add_paragraph(FUND); d.save(f'{R}/declaration_of_interest.docx')
d = newdoc(); d.add_paragraph().add_run('CRediT authorship contribution statement').bold = True; d.add_paragraph(CREDIT); d.save(f'{R}/credit_statement.docx')
open(f'{R}/data_availability_statement.txt', 'w').write(DATA + '\n')
for f in ('graphical_abstract.png', 'graphical_abstract.pdf', 'suggested_reviewers.md'): shutil.copy(f'{H}/{f}', f'{R}/{f}')
print('pages', MAIN_PAGES, 'refs', NREFS)
