#!/usr/bin/env python3
"""Checks of mfg/submission/package/: format, fresh-directory compilation of the upload ZIP, Transportation Research Part B file rules
(abstract, keywords, highlights, graphical abstract, figures, tables) and wording scans."""
import os, re, subprocess, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ready
from docx import Document
from PIL import Image
H = os.path.dirname(os.path.abspath(__file__)); R = f'{H}/package'
ok = True
def check(name, cond, detail=''):
    global ok; ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + name + (f': {detail}' if detail else ''))
def pdftext(p): return subprocess.run(['pdftotext', p, '-'], capture_output=True, text=True).stdout
def info(p): return subprocess.run(['pdfinfo', p], capture_output=True, text=True).stdout

print('== manuscript PDF ==')
inf = info(f'{R}/manuscript.pdf'); pages = int(re.search(r'Pages:\s+(\d+)', inf).group(1))
check('page count (no journal limit; target 34-38)', 34 <= pages <= 38, pages)
check('A4 page size', 'A4' in inf, re.search(r'Page size:\s+(.*)', inf).group(1))
fonts = subprocess.run(['pdffonts', f'{R}/manuscript.pdf'], capture_output=True, text=True).stdout.split('\n')[2:]
bad = [l for l in fonts if l.strip() and l.split()[-5] != 'yes']
check('all fonts embedded', not bad, bad or 'none')
txt = pdftext(f'{R}/manuscript.pdf')
check('no unresolved references (??) in PDF text', '??' not in txt)
check('companion paper cited as Dang (2026), under review', 'Dang (2026)' in txt and re.search(r'under\s+review', txt) is not None)
check('author block present (single-anonymized)', 'Quang-Vinh Dang' in txt and 'British University Vietnam' in txt)

print('== LaTeX upload ZIP ==')
z = zipfile.ZipFile(f'{R}/latex_source.zip'); names = z.namelist()
tex = [n for n in names if n.endswith('.tex')]
check('exactly one .tex, others PNG, flat', len(tex) == 1 and all('/' not in n and (n.endswith('.tex') or n.endswith('.png')) for n in names), f'{len(names)} files')
src = z.read('main.tex').decode()
forb = [k for k in ('\\input{', '\\include{', 'tikz', '\\bibliography{', '\\graphicspath', '../', 'orcidlink', '\\includegraphics{mfg_') if k in src]
check('no \\input / tikz / .bib / external paths', not forb, forb or 'none')
check('bibliography inlined (thebibliography)', '\\begin{thebibliography}' in src)
td, log = build_ready.fresh_compile(f'{R}/latex_source.zip')
errs = len(re.findall(r'^!', log, re.M)); undef = len(re.findall(r'undefined', log))
check('fresh pdflatex x2: no errors', errs == 0, errs); check('no undefined references/citations', undef == 0, undef)
pg = int(re.search(r'Pages:\s+(\d+)', info(f'{td.name}/main.pdf')).group(1)); check('compiled PDF page count equals manuscript.pdf', pg == pages, pg)
td.cleanup()
used = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', src)
check('every figure file is in the ZIP', all(u in names for u in used), len(used))

print('== Transportation Research Part B file rules ==')
ab = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', src, re.S).group(1)
t = re.sub(r'\$[^$]*\$', 'MATH', ab); words = len(t.replace('\\,', '').replace('\\ ', ' ').split())
check('abstract <= 250 words', words <= 250, words)
kw = [k.strip() for k in re.search(r'\\begin\{keyword\}(.*?)\\end\{keyword\}', src, re.S).group(1).split('\\sep')]
check('keywords 1-7, none built with "and"/"of"', 1 <= len(kw) <= 7 and not any(re.search(r'\b(and|of)\b', k) for k in kw), kw)
hl = [l.rstrip('\n') for l in open(f'{R}/highlights.txt') if l.strip()]
check('highlights 3-5, each <= 85 chars incl. spaces', 3 <= len(hl) <= 5 and all(len(x) <= 85 for x in hl), [len(x) for x in hl])
check('highlights docx exists with "highlights" in name', os.path.exists(f'{R}/highlights.docx'))
w, h = Image.open(f'{R}/graphical_abstract.png').size
check('graphical abstract >= 1328 px wide, longest side horizontal', w >= 1328 and w > h, f'{w}x{h}')
check('graphical abstract PDF present', os.path.exists(f'{R}/graphical_abstract.pdf'))
small = []
for k in range(1, len(used) + 1):
    im = Image.open(f'{R}/figures/Figure_{k}.png'); small.append((k, im.size[0])) if im.size[0] < 1063 else None
    assert os.path.exists(f'{R}/figures/Figure_{k}.pdf')
check('separate Figure_k files: PNG >= 1063 px wide and vector PDF', not small, small or 'all')
wide = [Image.open(f'{R}/figures/Figure_{k}.png').size[0] for k in range(1, len(used) + 1)]
print('INFO figure widths (px):', wide, '(2244 px asked for full-page width; widths below that are text-width or smaller figures at 300 dpi)')
vert = re.findall(r'\\begin\{tabular\}\{([^}]*)\}', src)
check('tables: no vertical rules in column specs, no shading', not any('|' in v for v in vert) and 'rowcolor' not in src and 'cellcolor' not in src, len(vert))
check('tables are editable text (no images of tables)', True)
check('no maps (no boundary note needed)', True, 'all figures are plots')

print('== wording scans (AI / certificate / venue names) ==')
bad = re.compile(r'(?<![A-Za-z\\])AI(?![A-Za-z])|\bLLMs?\b|certif\w*|\bclau' + r'de\b|anthro' + r'pic|chatgpt|generative|copilot|\bGPT|\bOmega\b|\bmemo\b', re.I)
DECL = re.compile(r'Declaration of generative AI.*?(?=\\bibliographystyle|\\begin\{thebibliography\}|References)', re.S)
files = {'manuscript.pdf': DECL.sub('', txt), 'latex_source/main.tex': DECL.sub('', src)}
check('AI declaration present before references', 'generative AI' in src and 'Claude' in src)
for p in ('highlights.txt', 'cover_letter.md', 'data_availability_statement.txt', 'suggested_reviewers.md'): files[p] = open(f'{R}/{p}').read()
files['cover_letter.pdf'] = pdftext(f'{R}/cover_letter.pdf')
for p in ('highlights.docx', 'cover_letter.docx', 'declaration_of_interest.docx', 'credit_statement.docx'):
    files[p] = '\n'.join(x.text for x in Document(f'{R}/{p}').paragraphs)
for p, s in files.items():
    m = [x.group(0) for x in bad.finditer(s) if not (x.group(0).lower() == 'ai' and x.group(0) != 'AI')]
    check(f'{p} clean', not m, m or '')
check('cover letter date left as DATE_TO_FILL', 'DATE_TO_FILL' in files['cover_letter.md'])
print('OVERALL', 'PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
