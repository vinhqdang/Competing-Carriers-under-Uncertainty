#!/usr/bin/env python3
"""TRIP package, part 1: compiles mfg/paper, flattens it (../flatten.py), builds latex_source.zip, manuscript.pdf, the
anonymous variant (latex_source_anonymous.zip, manuscript_anonymous.pdf) and the separate figure files in figures/.
Adapted from ../build_ready.py and ../build_anon.py. Then run make_docs.py and verify_trip.py."""
import os, re, shutil, subprocess, sys, tempfile, zipfile
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); sys.path.insert(0, os.path.dirname(H))
from trip_config import *
import flatten

def run(cmd, cwd): return subprocess.run(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def zip_dir(folder, zpath):
    if os.path.exists(zpath): os.remove(zpath)
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(folder)): z.write(f'{folder}/{f}', f)
def fresh_compile(zpath, name='main'):
    td = tempfile.TemporaryDirectory()
    with zipfile.ZipFile(zpath) as z: z.extractall(td.name)
    for _ in range(2): run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', f'{name}.tex'], td.name)
    return td, open(f'{td.name}/{name}.log', errors='replace').read()
def pages(pdf): return int(re.search(r'Pages:\s+(\d+)', subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout).group(1))

if __name__ == '__main__':
    P = f'{MFG}/paper'; os.makedirs(f'{H}/figures', exist_ok=True)
    run(['pdflatex', '-interaction=nonstopmode', 'main.tex'], P); run(['bibtex', 'main'], P)
    run(['pdflatex', '-interaction=nonstopmode', 'main.tex'], P); run(['pdflatex', '-interaction=nonstopmode', 'main.tex'], P)
    for anon in (False, True):
        sfx = '_anonymous' if anon else ''
        work = tempfile.mkdtemp()
        names = flatten.build(f'{work}/src', figdir=f'{SUB}/figures_src', anon=anon)
        zip_dir(f'{work}/src', f'{H}/latex_source{sfx}.zip')
        td, log = fresh_compile(f'{H}/latex_source{sfx}.zip')
        ok = os.path.exists(f'{td.name}/main.pdf')
        print(f'latex_source{sfx}.zip: compiled={ok} errors={len(re.findall(chr(10)+"!", log))} undefined={log.count("undefined")} pages={pages(td.name + "/main.pdf") if ok else "?"}')
        if ok: shutil.copy(f'{td.name}/main.pdf', f'{H}/manuscript{sfx}.pdf')
        td.cleanup()
        if not anon:
            for k, old in enumerate(names, 1):
                shutil.copy(f'{work}/src/Figure_{k}.png', f'{H}/figures/Figure_{k}.png')
                shutil.copy(f'{SUB}/figures_src/{old[:-4]}.pdf', f'{H}/figures/Figure_{k}.pdf')
        shutil.rmtree(work)
