# Progress: exact-oracle (branch-and-price) re-run of E1-E4

Resume after a restart (all commands skip finished work; 3 processes):

```
nohup experiments/run_exact.sh > results/logs/run_exact.out 2>&1 &
```

Updated 2026-10-24 10:51:05. x = finished, . = missing (E1 / E2 / E3 / E4 per seed; sens = E1 sensitivity).

| city | s0 | s1 | s2 | E1 sens |
|---|---|---|---|---|
| NewDelhi | x/x/x/x | ./x/x/x | ./x/x/x | . |
| Cairo | x/x/x/x | x/x/x/x | x/x/x/x | . |
| Moscow | ./x/x/x | ./x/x/x | ./x/x/x | . |
| BuenosAires | ./x/x/x | ./x/x/x | ./x/x/x | . |
| NewYork | ./x/x/x | ./x/x/x | ./x/x/x | . |
| Bombay | ./x/x/x | ./x/x/x | ./x/x/x | . |
| London | x/x/x/x | ./x/x/x | ./x/x/x | . |
| Paris | x/x/x/x | ./x/x/x | x/x/x/x | . |
| Berlin | ./x/x/x | ./x/x/x | ./x/x/x | . |

88 of 108 city/seed/experiment results complete (E2/E3/E4 files are only counted when they were produced after the old ones were moved to results/pb_old).

## Log
