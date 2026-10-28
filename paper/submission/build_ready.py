#!/usr/bin/env python3
"""Builds the TeX/PDF part of paper/submission/ready/ from paper/main.tex and paper/supplement.tex.

1. compiles both documents in paper/ (pdflatex, bibtex, pdflatex x2) to obtain the .bbl and .aux files;
2. flattens each into one .tex plus PNG figures, in an anonymous and a titled (author) variant (flatten.py);
3. zips every variant (flat zip, no folders) and compiles it from a fresh directory with plain pdflatex, twice;
4. copies the resulting PDFs: manuscript_anonymous.pdf, supplement.pdf (anonymous) and the two reference PDFs with author.

Run make_ready_docs.py afterwards (cover letter, title page, ...), then verify_ready.py.
"""
import os, shutil, subprocess, sys, tempfile, zipfile

H = os.path.dirname(os.path.abspath(__file__)); P = os.path.dirname(H); R = f'{H}/ready'
sys.path.insert(0, H)
import flatten

def run(cmd, cwd, **kw):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kw)

def compile_source(name):
    run(['pdflatex', '-interaction=nonstopmode', f'{name}.tex'], P)
    run(['bibtex', name], P)
    run(['pdflatex', '-interaction=nonstopmode', f'{name}.tex'], P)
    run(['pdflatex', '-interaction=nonstopmode', f'{name}.tex'], P)

def zip_dir(folder, zpath):
    if os.path.exists(zpath): os.remove(zpath)
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(folder)): z.write(f'{folder}/{f}', f)

def fresh_compile(zpath, name):
    """unzip into a fresh directory, run pdflatex twice, return (pdf path in temp dir, log text, tempdir object)"""
    td = tempfile.TemporaryDirectory()
    with zipfile.ZipFile(zpath) as z: z.extractall(td.name)
    for _ in range(2): run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', f'{name}.tex'], td.name)
    log = open(f'{td.name}/{name}.log', errors='replace').read()
    return td, log

if __name__ == '__main__':
    os.makedirs(R, exist_ok=True)
    for n in ('main', 'supplement'): compile_source(n)
    plan = [  # (doc, mode, folder, zip, pdf destination)
        ('main', 'anon', 'anonymous_upload', 'anonymous_upload.zip', 'manuscript_anonymous.pdf'),
        ('supplement', 'anon', 'supplement_upload', 'supplement_upload.zip', 'supplement.pdf'),
        ('main', 'titled', 'reference_upload_with_author', 'reference_upload_with_author.zip', 'reference_not_for_upload/manuscript_with_author_REFERENCE_ONLY.pdf'),
        ('supplement', 'titled', 'reference_supplement_upload_with_author', 'reference_supplement_upload_with_author.zip', 'reference_not_for_upload/supplement_with_author_REFERENCE_ONLY.pdf'),
    ]
    os.makedirs(f'{R}/reference_not_for_upload', exist_ok=True)
    for doc, mode, folder, zname, pdf in plan:
        flatten.build(f'{R}/{folder}', mode, doc)
        zip_dir(f'{R}/{folder}', f'{R}/{zname}')
        td, log = fresh_compile(f'{R}/{zname}', doc)
        ok = os.path.exists(f'{td.name}/{doc}.pdf')
        errs = log.count('\n!'); undef = log.count('undefined')
        pages = subprocess.run(['pdfinfo', f'{td.name}/{doc}.pdf'], capture_output=True, text=True).stdout
        pages = [l for l in pages.split('\n') if l.startswith('Pages')]
        print(f'{zname}: compiled={ok} errors={errs} undefined={undef} {pages}')
        if ok: shutil.copy(f'{td.name}/{doc}.pdf', f'{R}/{pdf}')
        td.cleanup()
