# Progress: "Why probability boxes" (ambiguity criteria, out-of-sample study and game re-run)

Resume after a restart (all commands skip finished work; one core):

```
export OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
nohup taskset -c 0 python experiments/run_ambiguity.py pipeline > results/logs/run_ambiguity.out 2>&1 &
```

Log
- 2026-10-26 07:12:02 validate: planner vs exact B&P on 9 instances, max gap 0.1049%, optimal in 8/9
- 2026-10-26 07:13:27 oracle plans done (36 rows)
