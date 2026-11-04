#!/usr/bin/env python3
"""Flatten mfg/paper/main.tex into ONE .tex file plus PNG figures (for Elsevier's upload system).

Usage: python3 mfg/submission/flatten.py OUTDIR [FIGDIR]
Requires a finished build of mfg/paper (main.bbl is read). It inlines the theory files, stake.tex, ext.tex, the tables
and the shared macros, expands every number macro of numbers*.tex to its literal value, inlines the compiled bibliography
(thebibliography), renames the figures Figure_1.png, Figure_2.png, ... in order of appearance (300 dpi versions from FIGDIR,
default mfg/submission/figures_src) and drops the non-standard orcidlink package.
"""
import os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MFG = os.path.dirname(HERE)
PAPER = f'{MFG}/paper'

def balanced(s, i):
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
        val, _ = balanced(txt, mo.end()); m[mo.group(1)] = val
    return m

def resolve(m):
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

def anonymise(main):
    """Author-free manuscript: no name, affiliation, e-mail, ORCID, repository link, CRediT; self-citation anonymised."""
    main = re.sub(r'\\author\{[^}]*\}\n\\ead\{[^}]*\}\n\\address\{[^}]*\}\n', '', main)
    main = re.sub(r'\\section\*\{CRediT authorship contribution statement\}.*?(?=\\section\*\{Declaration of competing)', '', main, flags=re.S)
    main = re.sub(r'(\\section\*\{Data availability\}\n).*?\n', r'\1Code, instances, result files and the Lean development are available in a public repository. The link is withheld during peer review and will be provided to the editor on request and on acceptance.\n', main, count=1)
    main = re.sub(r'\\bibitem\[\{Dang\(2026\)\}\]\{Omega2026\}.*?(?=\\bibitem|\\end\{thebibliography\})', lambda m: '\\bibitem[{Anonymous(2026)}]{Omega2026}\n\\bibinfo{author}{Anonymous}, \\bibinfo{year}{2026}.\n\\newblock \\bibinfo{title}{Manuscript under review}.\n\n', main, flags=re.S)
    return main

def build(out, figdir=None, anon=False):
    figdir = figdir or f'{HERE}/figures_src'
    if os.path.exists(out): shutil.rmtree(out)
    os.makedirs(out)
    main = open(f'{PAPER}/main.tex').read()
    macros = {}
    for f in ('numbers', 'numbers_stake', 'numbers_ext'):
        macros.update(parse_macros(open(f'{PAPER}/{f}.tex').read()))
    macros = resolve(macros)
    for f in ('numbers', 'numbers_stake', 'numbers_ext'):
        main = main.replace('\\input{%s.tex}\n' % f, '')
    main = main.replace('\\input{../theory/macros.tex}', open(f'{MFG}/theory/macros.tex').read())
    def inl(mo):
        p = mo.group(1)
        p = f'{MFG}/theory/{os.path.basename(p)}' if p.startswith('../theory/') else f'{PAPER}/{p}'
        if not p.endswith('.tex'): p += '.tex'
        return open(p).read()
    for _ in range(3):
        main = re.sub(r'\\input\{([^}]+)\}', inl, main)
    main = main.replace('\\usepackage{orcidlink}\n', '').replace('\\graphicspath{{../figures/}}\n', '')
    main = re.sub(r'\\,\\orcidlink\{[^}]*\}', '', main)
    main = main.replace('\\address{British University Vietnam, Hung Yen, Vietnam}', '\\address{British University Vietnam, Hung Yen, Vietnam. ORCID: 0000-0002-3877-8024}')
    bbl = open(f'{PAPER}/main.bbl').read()
    main = main.replace('\\bibliographystyle{elsarticle-harv}\n', '').replace('\\bibliography{references}', bbl)
    if anon:
        main = anonymise(main)
    main = strip_comments(main)
    main, pat = expand(main, macros)
    assert not pat.search(main)
    # figures in order of appearance
    names = []
    for mo in re.finditer(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', main):
        if mo.group(1) not in names: names.append(mo.group(1))
    for k, old in enumerate(names, 1):
        new = f'Figure_{k}.png'
        main = main.replace('{%s}' % old, '{%s}' % new)
        src = f'{figdir}/{old}'
        if not os.path.exists(src): src = f'{MFG}/figures/{old}'
        shutil.copy(src, f'{out}/{new}')
    assert '../' not in main and 'graphicspath' not in main and '\\input{' not in main
    open(f'{out}/main.tex', 'w').write(main + '\n')
    return names

if __name__ == '__main__':
    print(build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
