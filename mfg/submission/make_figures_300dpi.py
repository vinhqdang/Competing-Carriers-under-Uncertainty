#!/usr/bin/env python3
"""Re-render the twelve manuscript figures at 300 dpi (PNG) and as vector PDF into mfg/submission/figures_src/.

The three analysis scripts (mfg/experiments/analyze*.py) are run unchanged except for the savefig calls, in a temporary
copy of the results directory, so nothing in mfg/ is overwritten. The script checks that the regenerated number macros and
tables are byte-identical to those in mfg/paper (i.e. the figures show exactly the published numbers).

Run: PYTHONPATH=mfg/src python3 mfg/submission/make_figures_300dpi.py
"""
import os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__)); MFG = os.path.dirname(HERE)
with tempfile.TemporaryDirectory() as td:
    for d in ('experiments', 'paper', 'figures'): os.makedirs(f'{td}/{d}')
    shutil.copytree(f'{MFG}/results', f'{td}/results', ignore=shutil.ignore_patterns('geo'))
    for s in ('analyze.py', 'analyze_ext.py', 'analyze_stake.py'):
        t = open(f'{MFG}/experiments/{s}').read()
        t = re.sub(r'fig\.savefig\(FIG / "(mfg_[a-z_]+)\.png", dpi=150\)', r'fig.savefig(FIG / "\1.png", dpi=300); fig.savefig(FIG / "\1.pdf")', t)
        open(f'{td}/experiments/{s}', 'w').write(t)
        env = dict(os.environ, PYTHONPATH=f'{MFG}/src')
        subprocess.run([sys.executable, f'{td}/experiments/{s}'], check=True, env=env, stdout=subprocess.DEVNULL)
    for f in os.listdir(f'{td}/paper'):
        assert open(f'{td}/paper/{f}').read() == open(f'{MFG}/paper/{f}').read(), f'{f} differs from mfg/paper'
    os.makedirs(f'{HERE}/figures_src', exist_ok=True)
    for f in os.listdir(f'{td}/figures'): shutil.copy(f'{td}/figures/{f}', f'{HERE}/figures_src/{f}')
print('figures written; numbers and tables identical to mfg/paper')
