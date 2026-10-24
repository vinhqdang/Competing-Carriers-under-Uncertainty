# Progress: exact-oracle (branch-and-price) re-run of E1-E4

Resume after a restart (all commands skip finished work; 3 processes):

```
nohup experiments/run_exact.sh > results/logs/run_exact.out 2>&1 &
```

Updated 2026-10-24 13:59:29. x = finished, . = missing (E1 / E2 / E3 / E4 per seed; sens = E1 sensitivity).

| city | s0 | s1 | s2 | E1 sens |
|---|---|---|---|---|
| NewDelhi | x/././. | x/././. | x/././. | . |
| Cairo | x/x/x/. | x/x/x/. | x/x/x/. | . |
| Moscow | x/././. | x/././. | x/././. | . |
| BuenosAires | x/x/x/. | x/././. | x/x/x/. | . |
| NewYork | x/././. | x/././. | x/././. | . |
| Bombay | x/././. | x/././. | x/././. | . |
| London | x/x/x/. | x/././. | x/././. | . |
| Paris | x/x/x/. | x/x/./. | x/x/x/. | . |
| Berlin | x/././. | x/././. | x/././. | . |

44 of 108 city/seed/experiment results complete (E2/E3/E4 files are only counted when they were produced after the old ones were moved to results/pb_old).

## Log
- 2026-10-24 10:34 started: old results copied to results/pb_old (E1-E4, summaries, tables.md; figures to figures/pb_old); E2/E3/E4 files removed from results/ so that the scripts recompute them; E1 written per city/seed to results/exact_parts and assembled by `run_exact.py assemble`.
- 2026-10-24 11:30 E1 base finished for 26/27 city-seeds (Moscow s2 still running); the leader phase (E2+E3) started. Reduced E2 grid and reduced E4 for Cairo, Paris, Berlin, NewYork, Moscow (see docs), full for the rest.
- Resume: `PHASES="leader imprecision e1sens" nohup experiments/run_exact.sh > results/logs/run_exact.out 2>&1 &` (plus `python experiments/run_exact.py e1 CITY SEED` for any missing E1 part), then `python experiments/run_exact.py assemble --keep-old-sens`.
