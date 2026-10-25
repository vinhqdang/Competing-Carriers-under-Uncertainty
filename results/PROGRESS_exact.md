# Progress: exact-oracle (branch-and-price) re-run of E1-E4

Resume after a restart (all commands skip finished work; 3 processes):

```
nohup python experiments/run_exact_queue.py > results/logs/run_exact_queue.out 2>&1 &
```

Updated 2026-10-25 08:45:48. x = finished, . = missing (E1 / E2 / E3 / E4 per seed; sens = E1 sensitivity).

| city | s0 | s1 | s2 | E1 sens |
|---|---|---|---|---|
| NewDelhi | x/x/x/x | x/x/x/x | x/x/x/x | . |
| Cairo | x/x/x/x | x/x/x/x | x/x/x/. | . |
| Moscow | x/x/x/x | x/x/x/x | x/././x | . |
| BuenosAires | x/x/x/x | x/x/x/x | x/x/x/x | . |
| NewYork | x/x/x/x | x/x/x/x | x/././x | . |
| Bombay | x/x/x/x | x/x/x/x | x/x/x/x | . |
| London | x/x/x/x | x/x/x/x | x/x/x/x | . |
| Paris | x/x/x/x | x/x/x/x | x/x/x/x | . |
| Berlin | x/x/x/x | x/x/x/x | x/././x | . |

101 of 108 city/seed/experiment results complete (E2/E3/E4 files are only counted when they were produced after the old ones were moved to results/pb_old).

## Log
- 2026-10-24 10:34 started: old results copied to results/pb_old (E1-E4, summaries, tables.md; figures to figures/pb_old); E2/E3/E4 files removed from results/ so that the scripts recompute them; E1 written per city/seed to results/exact_parts and assembled by `run_exact.py assemble`.
- 2026-10-24 11:30 E1 base finished for 26/27 city-seeds (Moscow s2 still running); the leader phase (E2+E3) started. Reduced E2 grid and reduced E4 for Cairo, Paris, Berlin, NewYork, Moscow (see docs), full for the rest.
- 2026-10-24 16:59 stopped (time budget). E1 base 27/27 exact; E3 24/27 (New York, Moscow, Berlin seed 2 missing); E2 complete grid for Buenos Aires, London, New Delhi, reduced exact subset for the other six cities (24 city/seeds); E4: New Delhi, Buenos Aires, London, Mumbai all three seeds (12 widths), Cairo/Paris/Berlin/New York/Moscow seeds 0 and 1 with 6 exact widths (seed 2 missing); old-equilibrium regrets 27/27.
- Unfinished work (resumable with `python experiments/run_exact_queue.py`): E2/E3 seed 2 of New York, Moscow, Berlin (partial files in results/exact_parts/partial/, rerun `experiments/run_exact_job.sh leader CITY 2`); E4 seed 2 of Cairo, Paris, Berlin, New York, Moscow; E1 sensitivity (`run_exact.py e1sens CITY`).
- After finishing any of these: `python experiments/run_exact.py assemble --keep-old-sens; python experiments/summarize.py; python experiments/summarize_exact.py; python experiments/plot_results.py; python experiments/plot_equilibria.py`.
