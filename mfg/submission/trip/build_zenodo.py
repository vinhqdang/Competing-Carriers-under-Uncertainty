#!/usr/bin/env python3
"""Builds mfg/submission/trip/zenodo/mfg_carriers_replication_v1.zip (Zenodo deposit) and copies .zenodo.json next to it.
Run from anywhere: python3 mfg/submission/trip/build_zenodo.py"""
import os, shutil, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
OUT = f'{HERE}/zenodo'; ROOT = 'mfg_carriers_replication_v1'
DOCS = f'{HERE}/deposit_docs'
SKIP_DIRS = {'__pycache__', '.pytest_cache', '.lake', 'geo', 'submission'}
SKIP_EXT = {'.aux', '.log', '.out', '.blg', '.spl', '.pyc', '.pdf', '.synctex.gz'}
def walk(rel, include=None, skip_names=()):
    base = f'{REPO}/{rel}'
    for d, dirs, files in os.walk(base):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not x.startswith('.'))
        for f in sorted(files):
            if f.startswith('.') or f in skip_names or os.path.splitext(f)[1] in SKIP_EXT: continue
            if f == 'main.bbl' and False: continue
            yield os.path.join(d, f), os.path.relpath(os.path.join(d, f), REPO)
os.makedirs(OUT, exist_ok=True)
zp = f'{OUT}/{ROOT}.zip'
if os.path.exists(zp): os.remove(zp)
n = 0
with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for rel in ('mfg', 'src', 'data/parameters', 'data/processed'):
        for p, r in walk(rel, skip_names=('pois.csv',)):
            z.write(p, f'{ROOT}/{r}'); n += 1
    for f in sorted(os.listdir(DOCS)): z.write(f'{DOCS}/{f}', f'{ROOT}/{f}'); n += 1
    z.write(f'{REPO}/data/README.md', f'{ROOT}/data/README.md')
for f in ('README.md', 'NOTICE', 'LICENSE', 'LICENSE-DATA'): shutil.copy(f'{DOCS}/{f}', f'{OUT}/{f}')
print(zp, n, 'files', round(os.path.getsize(zp) / 1e6, 1), 'MB')
