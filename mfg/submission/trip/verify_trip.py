#!/usr/bin/env python3
"""Checks of the TRIP package (adapted from ../verify_ready.py): format, fresh-directory compilation of both upload ZIPs,
TRIP file rules, anonymity of the anonymous variant, and wording scans (the generative-AI declaration is allowed only in its section)."""
import os, re, subprocess, sys, zipfile
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from trip_config import *
import build_trip
from docx import Document
from PIL import Image
R = H; ok = True; DOI = '10.5281/zenodo.24357664'
def check(name, cond, detail=''):
    global ok; ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + name + (f': {detail}' if detail else ''))
def pdftext(p): return subprocess.run(['pdftotext', p, '-'], capture_output=True, text=True).stdout
def info(p): return subprocess.run(['pdfinfo', p], capture_output=True, text=True).stdout
def pg(p): return int(re.search(r'Pages:\s+(\d+)', info(p)).group(1))

for variant, sfx in (('author-named', ''), ('anonymous', '_anonymous')):
    print(f'== {variant} manuscript PDF and LaTeX ZIP ==')
    pdf = f'{R}/manuscript{sfx}.pdf'; inf = info(pdf); pages = pg(pdf)
    check('page count (no journal limit; target 34-40)', 34 <= pages <= 40, pages)
    check('A4 page size', 'A4' in inf)
    fonts = subprocess.run(['pdffonts', pdf], capture_output=True, text=True).stdout.split('\n')[2:]
    bad = [l for l in fonts if l.strip() and l.split()[-5] != 'yes']
    check('all fonts embedded', not bad, bad or 'none')
    txt = pdftext(pdf); check('no unresolved references (??)', '??' not in txt)
    z = zipfile.ZipFile(f'{R}/latex_source{sfx}.zip'); names = z.namelist(); src = z.read('main.tex').decode()
    check('exactly one .tex, others PNG, flat', sum(n.endswith('.tex') for n in names) == 1 and all('/' not in n and n.endswith(('.tex', '.png')) for n in names), f'{len(names)} files')
    forb = [k for k in ('\\input{', '\\include{', 'tikz', '\\bibliography{', '\\graphicspath', '../', 'orcidlink') if k in src]
    check('no \\input / tikz / .bib / external paths', not forb, forb or 'none')
    check('bibliography inlined', '\\begin{thebibliography}' in src)
    td, log = build_trip.fresh_compile(f'{R}/latex_source{sfx}.zip')
    check('fresh pdflatex x2: no errors', len(re.findall(r'^!', log, re.M)) == 0)
    check('no undefined references/citations', 'undefined' not in log)
    check('compiled page count equals manuscript PDF', pg(f'{td.name}/main.pdf') == pages); td.cleanup()
    used = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', src)
    check('every figure file is in the ZIP', all(u in names for u in used), len(used))
    if sfx:
        pat = re.compile(r'Quang|Dang|buv\.edu|British University|Hung Yen|0000-0002|github|vinhqdang|zenodo|' + DOI.replace('.', r'\.') + r'|CRediT', re.I)
        for nm, t in (('anonymous PDF', txt), ('anonymous main.tex', src)):
            m = set(x.group(0) for x in pat.finditer(t)); check(f'{nm}: no author, affiliation, ORCID, e-mail, repository, DOI or CRediT', not m, sorted(m) or 'none')
        check('anonymous: self-citation is Anonymous (2026)', 'Anonymous (2026)' in txt)
        check('anonymous: repository link withheld statement', 'withheld during peer review' in src)
        check('anonymous PDF metadata has no author', not re.search(r'Author:[ \t]+\S', inf), 'none')
    else:
        check('author block present', 'Quang-Vinh Dang' in txt and 'British University Vietnam' in txt)
        check('companion paper cited as Dang (2026a), under review', 'Dang (2026a)' in txt and 'under review' in txt.replace('\n', ' '))
        check('Zenodo DOI and [dataset] reference present', DOI in txt and '[dataset]' in txt and 'github.com/vinhqdang' in src)
        check('CRediT section present', 'CRediT authorship contribution statement' in src)

print('== TRIP file rules (author-named source = anonymous source apart from the author parts) ==')
src = zipfile.ZipFile(f'{R}/latex_source_anonymous.zip').read('main.tex').decode()
ab = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', src, re.S).group(1)
t = re.sub(r'\$[^$]*\$', 'MATH', ab); words = len(t.replace('\\,', '').replace('\\ ', ' ').split())
check('abstract <= 250 words', words <= 250, words)
kw = [k.strip() for k in re.search(r'\\begin\{keyword\}(.*?)\\end\{keyword\}', src, re.S).group(1).split('\\sep')]
check('keywords 1-7, none built with "and"/"of"', 1 <= len(kw) <= 7 and not any(re.search(r'\b(and|of)\b', k) for k in kw), kw)
hl = [l.rstrip('\n') for l in open(f'{R}/highlights.txt') if l.strip()]
check('highlights 3-5, each <= 85 chars', 3 <= len(hl) <= 5 and all(len(x) <= 85 for x in hl), [len(x) for x in hl])
check('highlights docx present', os.path.exists(f'{R}/highlights.docx'))
w, h = Image.open(f'{R}/graphical_abstract.png').size
check('graphical abstract >= 1328 px wide, longest side horizontal', w >= 1328 and w > h, f'{w}x{h}')
check('graphical abstract PDF present', os.path.exists(f'{R}/graphical_abstract.pdf'))
n = len(re.findall(r'\\includegraphics', src)); small = []
for k in range(1, n + 1):
    if Image.open(f'{R}/figures/Figure_{k}.png').size[0] < 1063: small.append(k)
    assert os.path.exists(f'{R}/figures/Figure_{k}.pdf')
check('Figure_k files: PNG >= 1063 px wide and vector PDF', not small, small or f'{n} figures')
vert = re.findall(r'\\begin\{tabular\}\{([^}]*)\}', src)
check('tables: no vertical rules, no shading', not any('|' in v for v in vert) and 'rowcolor' not in src and 'cellcolor' not in src, len(vert))
sec = re.findall(r'\\section\*?\{([^}]*)\}', src)
check('Acknowledgement-type declarations before references (AI declaration last section)', sec[-1].startswith('Declaration of generative AI'), sec[-3:])
check('implications subsection present', 'Implications for planners and operators' in src)

print('== title page and declarations ==')
tp = '\n'.join(p.text for p in Document(f'{R}/title_page.docx').paragraphs)
for k in ('British University Vietnam, Hung Yen, Vietnam', 'vinh.dq4@buv.edu.vn', '0000-0002-3877-8024', 'CRediT', 'competing', 'Funding', DOI, 'github.com/vinhqdang', 'Claude'):
    check(f'title_page.docx contains {k}', k.lower() in tp.lower())
check('title_page.pdf exists', os.path.exists(f'{R}/title_page.pdf'))
for f in ('declaration_of_interest.docx', 'credit_statement.docx', 'cover_letter.docx', 'cover_letter.pdf', 'cover_letter.md', 'README.md', 'ZENODO_STEPS.md', 'suggested_reviewers.md'): check(f'{f} exists', os.path.exists(f'{R}/{f}'))
check('data statement contains DOI and GitHub', DOI in open(f'{R}/data_availability_statement.txt').read() and 'github.com' in open(f'{R}/data_availability_statement.txt').read())

print('== Zenodo deposit ==')
zp = f'{R}/zenodo/mfg_carriers_replication_v1.zip'
check('zenodo zip exists and is sound', os.path.exists(zp) and zipfile.ZipFile(zp).testzip() is None, f'{os.path.getsize(zp)/1e6:.1f} MB')
zn = zipfile.ZipFile(zp).namelist()
check('zenodo zip: no caches, hidden folders, raw data or pois.csv', not [x for x in zn if re.search(r'__pycache__|\.lake|/\.|raw|pois\.csv|results/geo', x)])
check('zenodo zip: licence, notice, README', all(any(x.endswith('/' + f) for x in zn) for f in ('LICENSE', 'LICENSE-DATA', 'NOTICE', 'README.md')))
import json; meta = json.load(open(f'{R}/zenodo/.zenodo.json'))
check('.zenodo.json: creator ORCID and no DOI field', meta['creators'][0]['orcid'] == '0000-0002-3877-8024' and 'doi' not in meta)
inzip = zipfile.ZipFile(zp).read('mfg_carriers_replication_v1/mfg/paper/main.tex').decode()
check('zenodo zip carries the final paper sources', open(f'{MFG}/paper/main.tex').read() == inzip)

print('== wording scans (AI / venue names) ==')
bad = re.compile(r'(?<![A-Za-z\\])AI(?![A-Za-z])|\bLLMs?\b|certif\w*|\bclau' + r'de\b|anthro' + r'pic|chatgpt|generative|copilot|\bGPT|\bOmega\b|\bmemo\b', re.I)
DECL = re.compile(r'Declaration of generative AI.*?(?=\\bibliographystyle|\\begin\{thebibliography\}|References)', re.S)
files = {'manuscript.pdf': DECL.sub('', pdftext(f'{R}/manuscript.pdf')), 'manuscript_anonymous.pdf': DECL.sub('', pdftext(f'{R}/manuscript_anonymous.pdf')),
         'main.tex': DECL.sub('', zipfile.ZipFile(f'{R}/latex_source.zip').read('main.tex').decode()), 'main_anon.tex': DECL.sub('', src)}
for p in ('highlights.txt', 'cover_letter.md', 'data_availability_statement.txt', 'suggested_reviewers.md', 'README.md', 'ZENODO_STEPS.md'): files[p] = open(f'{R}/{p}').read()
files['cover_letter.pdf'] = pdftext(f'{R}/cover_letter.pdf')
for p in ('highlights.docx', 'cover_letter.docx', 'declaration_of_interest.docx', 'credit_statement.docx'): files[p] = '\n'.join(x.text for x in Document(f'{R}/{p}').paragraphs)
tp_noai = re.sub(r'Declaration of generative AI.*?(?=Related manuscript)', '', tp, flags=re.S); files['title_page.docx (outside AI section)'] = tp_noai
for p, s in files.items():
    m = [x.group(0) for x in bad.finditer(s) if not (x.group(0).lower() == 'ai' and x.group(0) != 'AI')]
    check(f'{p} clean', not m, m or '')
check('AI declaration present in both manuscripts', 'Claude' in zipfile.ZipFile(f'{R}/latex_source.zip').read('main.tex').decode() and 'Claude' in zipfile.ZipFile(f'{R}/latex_source_anonymous.zip').read('main.tex').decode())
check('cover letter date left as DATE_TO_FILL', 'DATE_TO_FILL' in files['cover_letter.md'])
print('OVERALL', 'PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
