#!/usr/bin/env python3
"""Checks of paper/submission/ready/: anonymity of the blinded manuscript and upload folder, and wording checks."""
import os, re, subprocess, zipfile, tempfile, shutil, sys
from docx import Document
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ready')
ok = True
def pdftext(p): return subprocess.run(['pdftotext', p, '-'], capture_output=True, text=True).stdout
ID = ['Dang', 'Quang', 'Vinh', 'vinhqdang', 'BUV', 'British University', 'buv.edu', 'ORCID', '0000-0002-3877-8024', 'github.com/vinh', '/home/user', 'Hung Yen']
def hits(text, pats):
    return {p: len(re.findall(re.escape(p), text, re.I if p not in ('BUV',) else 0)) for p in pats if re.search(re.escape(p), text, re.I if p != 'BUV' else 0)}
print('== anonymity ==')
t = pdftext(f'{R}/manuscript_anonymous.pdf'); h = hits(t, ID); print('anonymous PDF text hits:', h or 'none'); ok &= not h
meta = subprocess.run(['pdfinfo', '-meta', f'{R}/manuscript_anonymous.pdf'], capture_output=True, text=True).stdout
info = subprocess.run(['pdfinfo', f'{R}/manuscript_anonymous.pdf'], capture_output=True, text=True).stdout
h = hits(meta + info, ID); print('anonymous PDF metadata hits:', h or 'none', '|', [l for l in info.split('\n') if l.startswith(('Author', 'Creator', 'Producer'))]); ok &= not h
for f in os.listdir(f'{R}/anonymous_upload'):
    p = f'{R}/anonymous_upload/{f}'
    data = open(p, 'rb').read().decode('latin-1')
    h = hits(data, ID); print(f'anonymous_upload/{f}:', h or 'none'); ok &= not h
z = zipfile.ZipFile(f'{R}/anonymous_upload.zip'); names = z.namelist()
print('anonymous zip:', names); ok &= sum(n.endswith('.tex') for n in names) == 1 and all(n.endswith(('.tex', '.png')) for n in names)
tex = open(f'{R}/anonymous_upload/main.tex').read()
print('comments / ../ / graphicspath in anonymous .tex:', len(re.findall(r'(?<!\\)%', tex)), '../' in tex, 'graphicspath' in tex)
print('== wording (AI / certificate) in manuscript, sources, highlights, letter, declarations, title page ==')
bad = re.compile(r'(?<![A-Za-z\\])AI(?![A-Za-z])|\bLLMs?\b|\bassistants?\b|certif\w*|\bclaude\b|anthropic|chatgpt|generative|copilot|\bGPT', re.I)
def case_ok(m, s):   # 'AI' only counts upper-case (math uses a_i)
    return not (m.group(0).lower() == 'ai' and m.group(0) != 'AI')
files = {}
for p in ('manuscript_anonymous.pdf', 'reference_not_for_upload/manuscript_with_author_REFERENCE_ONLY.pdf', 'title_page.pdf', 'cover_letter.pdf'):
    files[p] = pdftext(f'{R}/{p}')
for p in ('anonymous_upload/main.tex', 'reference_upload_with_author/main.tex', 'highlights.txt', 'cover_letter.md', 'README.md'):
    files[p] = open(f'{R}/{p}').read() if p != 'README.md' else ''
for p in ('highlights.docx', 'cover_letter.docx', 'declaration_of_interest.docx', 'title_page.docx', 'credit_statement.docx'):
    files[p] = '\n'.join(x.text for x in Document(f'{R}/{p}').paragraphs)
for p, s in files.items():
    m = [x.group(0) for x in bad.finditer(s) if case_ok(x, s)]
    print(f'{p}:', m or 'clean'); ok &= not m
print('OVERALL', 'PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
