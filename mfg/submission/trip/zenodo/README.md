# Replication package: many small carriers, mean-field limit of competitive urban delivery under zone-time charges


Replication package for the manuscript of the same title (Quang-Vinh Dang, Dat Le and Minh-Ngoc Dinh).
Archive date: 2026-11-19. Source repository: https://github.com/vinhqdang/Competing-Carriers-under-Uncertainty (folder `mfg`).

## Contents

| Path | What |
|---|---|
| `mfg/src/mfgcc/` | package: instances on the time-expanded zone graph, quadratic-program solvers, leader rules, fees, entry, externalities |
| `mfg/tests/` | 38 tests (`pytest`; one is skipped until `run_extern.py` has built the path cache in `mfg/results/geo/`) |
| `mfg/experiments/` | resumable experiment drivers (`run_*.py`, `run_all.sh`) and the analysis scripts (`analyze*.py`) |
| `mfg/results/` | all result CSVs (raw per-instance rows and `summary_*.csv`) and run logs |
| `mfg/figures/` | the figures of the paper |
| `mfg/paper/` | LaTeX sources of the manuscript, the generated number macros (`numbers*.tex`) and tables |
| `mfg/theory/` | LaTeX sections with the statements and proofs |
| `mfg/checks/` | brute-force numerical checks of the bounds, with output |
| `mfg/lean/` | Lean 4 sources of the machine-checked algebraic cores (no Mathlib copy; see below) |
| `src/ccu/` | the earlier package of the companion work that `mfgcc` reuses (nine-city loader, depot selection) |
| `data/processed/<City>/` | derived zone tables, road graphs and travel-time matrices for nine cities (ODbL, see `NOTICE`); the point-of-interest lists (`pois.csv`) and raw extracts are NOT included |
| `data/parameters/` | calibration parameter tables with sources and quality grades (A/B/C) |

## Setup and tests

    python3 -m pip install -r requirements.txt     # Python 3.11 or newer; tested with 3.13
    PYTHONPATH=mfg/src python3 -m pytest mfg/tests -q       # expected: 37 passed, 1 skipped

(`osmium` and `rasterio` are imported by `src/ccu/geo.py` only to read raw files; they are needed to import the module but no raw
file is used here.)

## Regenerate the key tables and figures from the stored results

    PYTHONPATH=mfg/src python3 mfg/experiments/analyze.py        # gap, charge, welfare: mfg/paper/numbers.tex, table_cities.tex, figures
    PYTHONPATH=mfg/src python3 mfg/experiments/analyze_stake.py  # who gains and who loses: numbers_stake.tex, tables
    PYTHONPATH=mfg/src python3 mfg/experiments/analyze_ext.py    # fees, entry, externalities: numbers_ext.tex, tables

The analysis scripts read `mfg/results/*.csv` and overwrite the generated macro and table files in `mfg/paper/` and the figures in
`mfg/figures/`; with the stored results the numbers in the paper are reproduced. (Fig. 1 of the paper onward are produced by these
three scripts.)

## Re-run the experiments (long)

    PYTHONPATH=mfg/src bash mfg/experiments/run_all.sh           # resumable; writes mfg/results/*.csv
    for s in stake fees entry extern ident uniform; do PYTHONPATH=mfg/src python3 mfg/experiments/run_$s.py; done   # later sections (resumable)

The external-cost run caches fastest-path distances in `mfg/results/geo/` (rebuilt on demand from `data/processed`; not archived).
Theory checks: `PYTHONPATH=mfg/src python3 mfg/checks/theory_checks.py out.txt` (compare with `mfg/checks/theory_checks.out`).

## Lean

`mfg/lean` is a Lake project whose `lakefile.toml` expects a built Mathlib checkout at `../../lean/.lake/packages`. That checkout is
not archived. To check the files, create a Lake project that depends on Mathlib at the version in `lake-manifest.json` and copy
`MFG/Core.lean` into it; `lake build` then compiles it (no `sorry`).

## Licences

- Code (`mfg/src`, `mfg/tests`, `mfg/experiments`, `mfg/checks`, `mfg/lean`, `src/`): MIT, file `LICENSE`.
- Results, figures, parameter tables, paper sources (`mfg/results`, `mfg/figures`, `mfg/paper`, `mfg/theory`, `data/parameters`):
  CC BY 4.0, file `LICENSE-DATA`.
- `data/processed/`: derived from OpenStreetMap (c) OpenStreetMap contributors, Open Database Licence 1.0, and from GHSL GHS-POP
  R2023A (CC BY 4.0). These files stay under the ODbL; attribution and share-alike are described in `NOTICE`.

## How to cite

Cite the manuscript and this archive (Zenodo DOI: to be added).
