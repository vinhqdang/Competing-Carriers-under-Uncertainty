#!/usr/bin/env python3
"""Checks of paper/submission/ready/: format and page limit, fresh-directory compilation of both zips, anonymity of the blinded manuscript and supplement (PDF text, metadata, sources, zip contents) and wording checks."""
import os, re, subprocess, zipfile, tempfile, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ready
from docx import Document
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ready')
ok = True
def pdftext(p): return subprocess.run(['pdftotext', p, '-'], capture_output=True, text=True).stdout
ID = ['Dang', 'Quang', 'Vinh', 'vinhqdang', 'BUV', 'British University', 'buv.edu', 'ORCID', '0000-0002-3877-8024', 'github.com/vinh', '/home/user', 'Hung Yen']
def hits(text, pats):
    return {p: len(re.findall(re.escape(p), text, re.I if p not in ('BUV',) else 0)) for p in pats if re.search(re.escape(p), text, re.I if p != 'BUV' else 0)}
def info(p): return subprocess.run(['pdfinfo', p], capture_output=True, text=True).stdout
print('== format: page limit, page size, fonts ==')
mp = int(re.search(r'Pages:\s+(\d+)', info(f'{R}/manuscript_anonymous.pdf')).group(1))
sp = int(re.search(r'Pages:\s+(\d+)', info(f'{R}/supplement.pdf')).group(1))
print('main pages', mp, '(limit 35); supplement pages', sp); ok &= mp <= 35
for p in ('manuscript_anonymous.pdf', 'supplement.pdf'):
    ps = re.search(r'Page size:\s+(.*)', info(f'{R}/{p}')).group(1); print(p, 'page size:', ps); ok &= 'A4' in ps
    fonts = subprocess.run(['pdffonts', f'{R}/{p}'], capture_output=True, text=True).stdout.split('\n')[2:]
    notemb = [l for l in fonts if l.strip() and l.split()[-5] != 'yes']
    print(p, 'fonts not embedded:', notemb or 'none'); ok &= not notemb
src = open(f'{R}/anonymous_upload/main.tex').read()
pre = src.split('\\begin{document}')[0]
print('documentclass:', re.search(r'\\documentclass\[[^\]]*\]\{[^}]*\}', pre).group(0), '| stretch:', re.findall(r'\\setstretch\{[^}]*\}', pre), '| lineno:', 'lineno' in src or 'linenumbers' in src)
ok &= '[preprint,11pt]{elsarticle}' in pre and '\\setstretch{1.5}' in pre and 'lineno' not in src and 'twocolumn' not in src
print('== compile both zips in fresh directories (pdflatex twice) ==')
for z, n in (('anonymous_upload.zip', 'main'), ('supplement_upload.zip', 'supplement'), ('reference_upload_with_author.zip', 'main'), ('reference_supplement_upload_with_author.zip', 'supplement')):
    zf = zipfile.ZipFile(f'{R}/{z}'); names = zf.namelist()
    flat = all('/' not in x for x in names) and sum(x.endswith('.tex') for x in names) == 1 and all(x.endswith(('.tex', '.png')) for x in names)
    td, log = build_ready.fresh_compile(f'{R}/{z}', n)
    pg = int(re.search(r'Pages:\s+(\d+)', info(f'{td.name}/{n}.pdf')).group(1)) if os.path.exists(f'{td.name}/{n}.pdf') else -1
    errs = len(re.findall(r'^!', log, re.M)); undef = len(re.findall(r'undefined', log))
    tex = open(f'{td.name}/{n}.tex').read()
    bad = [k for k in ('\\input{', '\\include{', 'tikz', '\\bibliography{', '\\graphicspath', '../') if k in tex]
    print(f'{z}: flat={flat} pages={pg} errors={errs} undefined={undef} forbidden-constructs={bad or "none"}')
    ok &= flat and pg > 0 and errs == 0 and undef == 0 and not bad
    td.cleanup()
print('== anonymity ==')
for pdf in ('manuscript_anonymous.pdf', 'supplement.pdf'):
    t = pdftext(f'{R}/{pdf}'); h = hits(t, ID); print(f'{pdf} text hits:', h or 'none'); ok &= not h
    meta = subprocess.run(['pdfinfo', '-meta', f'{R}/{pdf}'], capture_output=True, text=True).stdout
    h = hits(meta + info(f'{R}/{pdf}'), ID); print(f'{pdf} metadata hits:', h or 'none', '|', [l for l in info(f"{R}/{pdf}").split('\n') if l.startswith(('Author', 'Creator', 'Producer', 'Title'))]); ok &= not h
    raw = open(f'{R}/{pdf}', 'rb').read().decode('latin-1'); h = hits(raw, [x for x in ID if x != 'Quang']); print(f'{pdf} raw-bytes hits:', h or 'none')
for folder, zname, main in (('anonymous_upload', 'anonymous_upload.zip', 'main'), ('supplement_upload', 'supplement_upload.zip', 'supplement')):
    for f in os.listdir(f'{R}/{folder}'):
        data = open(f'{R}/{folder}/{f}', 'rb').read().decode('latin-1')
        h = hits(data, ID); print(f'{folder}/{f}:', h or 'none'); ok &= not h
    z = zipfile.ZipFile(f'{R}/{zname}')
    for n in z.namelist():
        h = hits(z.read(n).decode('latin-1'), ID); ok &= not h
        if h: print('zip member', n, h)
    tex = open(f'{R}/{folder}/{main}.tex').read()
    print(f'comments / ../ / graphicspath in {main}.tex:', len(re.findall(r'(?<!\\)%', tex)), '../' in tex, 'graphicspath' in tex)
print('== wording (AI / certificate) in manuscript, sources, highlights, letter, declarations, title page ==')
bad = re.compile(r'(?<![A-Za-z\\])AI(?![A-Za-z])|\bLLMs?\b|\bassistants?\b|certif\w*|\bclau' + r'de\b|anthro' + r'pic|chatgpt|generative|copilot|\bGPT', re.I)
def case_ok(m, s):   # 'AI' only counts upper-case (math uses a_i)
    return not (m.group(0).lower() == 'ai' and m.group(0) != 'AI')
files = {}
for p in ('manuscript_anonymous.pdf', 'supplement.pdf', 'reference_not_for_upload/manuscript_with_author_REFERENCE_ONLY.pdf', 'reference_not_for_upload/supplement_with_author_REFERENCE_ONLY.pdf', 'title_page.pdf', 'cover_letter.pdf'):
    files[p] = pdftext(f'{R}/{p}')
for p in ('anonymous_upload/main.tex', 'supplement_upload/supplement.tex', 'reference_upload_with_author/main.tex', 'reference_supplement_upload_with_author/supplement.tex', 'highlights.txt', 'cover_letter.md', 'README.md'):
    files[p] = open(f'{R}/{p}').read() if p != 'README.md' else ''
for p in ('highlights.docx', 'cover_letter.docx', 'declaration_of_interest.docx', 'title_page.docx', 'credit_statement.docx'):
    files[p] = '\n'.join(x.text for x in Document(f'{R}/{p}').paragraphs)
for p, s in files.items():
    m = [x.group(0) for x in bad.finditer(s) if case_ok(x, s)]
    print(f'{p}:', m or 'clean'); ok &= not m
print('OVERALL', 'PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
