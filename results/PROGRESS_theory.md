# Progress: theory-to-experiment checks

Code: src/ccu/credal.py (thresholds E/M/ID/Gamma, anchored bounds, relaxed-equilibrium search), src/ccu/d2game.py
(vehicle-count variant, tiny enumeration), experiments/run_theory_checks.py, experiments/run_theory.sh.
Resumable: every stage of one (city, seed) is cached in results/theory_cache/<city>_s<seed>.json; rerun the same command
after a container restart (finished stages are skipped).

## Commands
- all nine cities x seeds 0,1,2 (absorption + Gamma), 2 cores:  nohup experiments/run_theory.sh > results/logs/run_theory.out 2>&1 &
- D2 tiny / gadgets:  python experiments/run_theory_checks.py d2tiny
- D2 on cities:  KIND=d2city SEEDS="0 1 2" experiments/run_theory.sh   (or d2city CITY --seeds ...)
- assemble CSVs, summary, figures:  python experiments/run_theory_checks.py report

## Status (updated by hand)
- 2026-10-24 01:20  absorption/Gamma runs for all 27 (city, seed) launched (run_theory.sh). D2 + report code pending.
- 2026-10-24 03:30 absorption + Gamma complete for all 27 (city, seed) (cache has rows_agg, rows_type_median, gamma_rows); d2tiny complete
  (theory_D2_{prop71,kernels,random_explicit,tiny}.csv). D2 city runs restarted after container restart (per-(city,seed) files
  theory_D2_<City>_s<seed>.csv; finished scales are skipped). Remaining: report, docs section, final pytest.
- 2026-10-24 03:40 ALL DONE: D2 city runs complete (9 files), report written (summary_theory.csv, figures), docs/EXPERIMENTS.md section added, 97 tests pass.
