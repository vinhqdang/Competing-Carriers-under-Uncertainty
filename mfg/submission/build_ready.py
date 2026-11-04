#!/usr/bin/env python3
"""Builds the TeX/PDF part of mfg/submission/package/ from mfg/paper/main.tex.

1. compiles mfg/paper (pdflatex, bibtex, pdflatex x2) to obtain main.bbl;
2. flattens it into one .tex plus PNG figures (flatten.py) and zips them flat (latex_source.zip);
3. compiles the zip from a fresh directory with plain pdflatex, twice, and copies the result to manuscript.pdf;
4. copies the figures as separate files Figure_1.png ... (300 dpi) and Figure_1.pdf ... (vector) into package/figures/.

Run make_ready_docs.py afterwards (cover letter, highlights, declarations), then verify_ready.py.
"""
import os, re, shutil, subprocess, sys, tempfile, zipfile

H = os.path.dirname(os.path.abspath(__file__)); MFG = os.path.dirname(H); P = f'{MFG}/paper'; R = f'{H}/package'
sys.path.insert(0, H)
import flatten

def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def zip_dir(folder, zpath):
    if os.path.exists(zpath): os.remove(zpath)
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(folder)): z.write(f'{folder}/{f}', f)

def fresh_compile(zpath, name='main'):
    td = tempfile.TemporaryDirectory()
    with zipfile.ZipFile(zpath) as z: z.extractall(td.name)
    for _ in range(2): run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', f'{name}.tex'], td.name)
    return td, open(f'{td.name}/{name}.log', errors='replace').read()

if __name__ == '__main__':
    os.makedirs(f'{R}/figures', exist_ok=True)
    run(['pdflatex', '-interaction=nonstopmode', 'main.tex'], P); run(['bibtex', 'main'], P)
    run(['pdflatex', '-interaction=nonstopmode', 'main.tex'], P); run(['pdflatex', '-interaction=nonstopmode', 'main.tex'], P)
    work = tempfile.mkdtemp()
    names = flatten.build(f'{work}/latex_source')
    zip_dir(f'{work}/latex_source', f'{R}/latex_source.zip')
    td, log = fresh_compile(f'{R}/latex_source.zip')
    ok = os.path.exists(f'{td.name}/main.pdf')
    pages = re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', f'{td.name}/main.pdf'], capture_output=True, text=True).stdout).group(1) if ok else '?'
    print(f'latex_source.zip: compiled={ok} errors={len(re.findall(chr(10)+"!", log))} undefined={log.count("undefined")} pages={pages}')
    if ok: shutil.copy(f'{td.name}/main.pdf', f'{R}/manuscript.pdf')
    td.cleanup()
    for k, old in enumerate(names, 1):
        shutil.copy(f'{work}/latex_source/Figure_{k}.png', f'{R}/figures/Figure_{k}.png')
        shutil.copy(f'{H}/figures_src/{old[:-4]}.pdf', f'{R}/figures/Figure_{k}.pdf')
    shutil.rmtree(work)
