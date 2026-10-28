#!/usr/bin/env python3
"""Flatten paper/main.tex into ONE .tex file plus PNG figures (for upload systems that cannot handle projects).

Usage: python3 paper/submission/flatten.py OUTDIR {anon|titled} [HIRES_FIGURE_DIR]

Requires a finished build of paper/main.tex (main.bbl and main.aux are read).
It inlines frontmatter.tex and all \\input tables, expands every number macro of
tables/macros.tex to its literal value, inlines the compiled bibliography, replaces the
TikZ schematic by a PNG, copies the figures under flat names, and drops non-standard packages.
"""
import re, os, sys, shutil, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.dirname(HERE)
REPO = os.path.dirname(PAPER)

def balanced(s, i):
    """s[i]=='{' -> (content, index after closing brace)"""
    assert s[i] == '{'
    d = 0
    for j in range(i, len(s)):
        c = s[j]
        if c == '\\': continue
        if c == '{' and s[j-1] != '\\': d += 1
        elif c == '}' and s[j-1] != '\\':
            d -= 1
            if d == 0: return s[i+1:j], j+1
    raise ValueError

def parse_macros(txt):
    m = {}
    for mo in re.finditer(r'\\newcommand\{\\([A-Za-z]+)\}', txt):
        val, _ = balanced(txt, mo.end())
        m[mo.group(1)] = val
    return m

def resolve(m):
    pat = None
    for _ in range(20):
        pat = re.compile(r'\\(' + '|'.join(sorted(m, key=len, reverse=True)) + r')(?![A-Za-z])')
        changed = False
        for k, v in m.items():
            nv = pat.sub(lambda x: m[x.group(1)], v)
            if nv != v: m[k] = nv; changed = True
        if not changed: break
    assert not any(pat.search(v) for v in m.values()), 'unresolved nested macros'
    return m

def expand(text, m):
    pat = re.compile(r'\\(' + '|'.join(sorted(m, key=len, reverse=True)) + r')(?![A-Za-z])(?:(\{\})|[ \t]+|[ \t]*\n(?![ \t]*\n))?')
    def rep(x):
        v = m[x.group(1)]
        if x.group(2) is not None and re.search(r'\\[A-Za-z]+$', v): return v + '{}'
        return v
    return pat.sub(rep, text), pat

def strip_comments(t):
    out = []
    for l in t.split('\n'):
        if re.match(r'\s*%', l): continue
        l = re.sub(r'(?<!\\)%.*$', '', l) if re.search(r'(?<!\\)%', l) else l
        out.append(l.rstrip())
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out))

def build(out, mode, hires=None):
    anon = mode == 'anon'
    hires = hires or os.path.join(REPO, 'figures')
    if os.path.exists(out): shutil.rmtree(out)
    os.makedirs(out)
    main = open(f'{PAPER}/main.tex').read()
    fm = open(f'{PAPER}/frontmatter.tex').read()
    macros = resolve(parse_macros(open(f'{PAPER}/tables/macros.tex').read()))
    # frontmatter
    if anon:
        for k in ('author', 'ead', 'address'):
            fm = re.sub(r'\\%s\{[^\n]*\n' % k, '', fm)
        fm = fm.replace('\\begin{frontmatter}', '\\begin{frontmatter}\n\\date{}', 1)
    else:
        fm = re.sub(r'\\orcidlink\{[^}]*\}', '', fm)
        fm = fm.replace(r'\author{Quang-Vinh Dang\,}', r'\author{Quang-Vinh Dang}')
        fm = fm.replace('British University Vietnam, Hung Yen, Vietnam}', 'British University Vietnam, Hung Yen, Vietnam. ORCID 0000-0002-3877-8024}')
    main = main.replace('\\input{frontmatter}', fm)
    main = main.replace('\\input{tables/macros}', '')
    # tables
    def tab(mo):
        return open(f'{PAPER}/tables/{mo.group(1)}.tex').read()
    main = re.sub(r'\\input\{tables/([A-Za-z0-9_]+)\}', tab, main)
    main = main.replace('\\adjustbox{max width=\\linewidth}{', '\\shrinkbox{')
    # preamble
    for pkg in (r'\usepackage[export]{adjustbox}', r'\usepackage{xurl}', r'\usepackage{orcidlink}', r'\usepackage{tikz}',
                r'\usetikzlibrary{arrows.meta,positioning}', r'\usepackage{microtype}', r'\graphicspath{{../figures/}}'):
        assert pkg in main, pkg
        main = main.replace(pkg + '\n', '')
    shrink = ('\\long\\def\\shrinkbox#1{\\sbox0{#1}\\ifdim\\wd0>\\linewidth\\resizebox{\\linewidth}{!}{\\usebox0}\\else\\usebox0\\fi}\n')
    main = main.replace('\\setlength{\\tabcolsep}{4pt}', shrink + '\\setlength{\\tabcolsep}{4pt}', 1)
    if anon:
        main = main.replace('\\hypersetup{hidelinks}', '\\hypersetup{hidelinks,pdfauthor={Anonymous},pdfcreator={},pdfproducer={}}')
        old = re.search(r'Code, processed data, parameter sources, result files, figures and the scripts that generate the tables and numbers of this paper are available at \\url\{[^}]+\}\.', main).group(0)
        main = main.replace(old, 'Code, processed data, parameter sources, result files, figures and the scripts that generate the tables and numbers of this paper are available in a public repository. The link is withheld during peer review and will be provided on acceptance, or to the editor on request.')
    # bibliography
    bbl = open(f'{PAPER}/main.bbl').read()
    main = main.replace('\\bibliographystyle{elsarticle-num-names}\n', '')
    main = main.replace('\\bibliography{references}', bbl)
    # macros
    main = strip_comments(main)
    main, pat = expand(main, macros)
    assert not pat.search(main)
    # tikz
    mo = re.search(r'\\resizebox\{\\textwidth\}\{!\}\{\s*(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\})\}', main, re.S)
    tikz = mo.group(1)
    aux = open(f'{PAPER}/main.aux').read()
    labels = dict(re.findall(r'\\newlabel\{([^}]+)\}\{\{([^}]*)\}', aux))
    tikz = re.sub(r'\\ref\{([^}]+)\}', lambda x: labels[x.group(1)], tikz)
    with tempfile.TemporaryDirectory() as td:
        open(f'{td}/t.tex', 'w').write('\\documentclass[12pt,border=3pt]{standalone}\n\\usepackage{amsmath,amssymb}\n\\usepackage{tikz}\n\\usetikzlibrary{arrows.meta,positioning}\n\\begin{document}\n' + tikz + '\n\\end{document}\n')
        subprocess.run(['pdflatex', '-interaction=nonstopmode', 't.tex'], cwd=td, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(['pdftoppm', '-r', '450', '-png', '-singlefile', 't.pdf', 'fig01_overview_schematic'], cwd=td, check=True)
        shutil.copy(f'{td}/fig01_overview_schematic.png', out)
    main = main.replace(mo.group(0), '\\includegraphics[width=\\textwidth]{fig01_overview_schematic.png}')
    # figures
    names = {'arp_calls_vs_gain.png': 'fig02_arp_calls_vs_gain.png', 'E4_imprecision.png': 'fig03_imprecision.png',
             'E2_instruments.png': 'fig04_instruments.png', 'overview_equilibria_light.png': 'fig05_equilibria_overview.png',
             'dip_calls_vs_gain.png': 'fig06_dip_calls_vs_gain.png', 'theory_absorption.png': 'fig07_theory_absorption.png',
             'theory_D2.png': 'fig08_theory_d2.png'}
    for old, new in names.items():
        assert '{%s}' % old in main, old
        main = main.replace('{%s}' % old, '{%s}' % new)
        src = os.path.join(hires, old)
        if not os.path.exists(src): src = os.path.join(REPO, 'figures', old)
        shutil.copy(src, f'{out}/{new}')
    open(f'{out}/main.tex', 'w').write(main + '\n')

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
