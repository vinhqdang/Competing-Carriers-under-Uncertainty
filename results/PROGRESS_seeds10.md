# Progress: ten-seed extension (seeds 3..9 added to 0..2), exact oracle

Resume after a restart (every job is resumable and writes atomically; finished work is skipped; 2 cores):

```
nohup python experiments/run_seeds10_queue.py > results/logs/seeds10_queue.out 2>&1 &
```

Updated 2026-10-26 14:20:46. Cells: core / arp / grid per seed, x = finished, . = missing, - = not scheduled (seeds 0-2: ARP exists for London, Buenos Aires, New Delhi, Mumbai; E1-E3, DIP and the grid of seeds 0-2 are the earlier runs).

| city | s3 | s4 | s5 | s6 | s7 | s8 | s9 | arp s0 s1 s2 |
|---|---|---|---|---|---|---|---|---|
| NewDelhi | x/x/x | x/x/x | x/x/x | x/x/x | x/x/x | x/x/x | x/x/. | existing |
| Cairo | x/./. | x/./. | x/./. | x/./. | ././. | ././. | ././. | . . . |
| Moscow | x/./. | x/./. | x/./. | x/./. | ././. | ././. | ././. | . . . |
| BuenosAires | x/x/x | x/x/x | x/x/x | x/x/x | x/x/x | x/x/x | x/./. | existing |
| NewYork | x/./. | x/./. | x/./. | x/./. | ././. | ././. | ././. | . . . |
| Bombay | x/./. | x/./. | x/./. | x/./. | ././. | ././. | ././. | existing |
| London | x/x/x | x/x/x | x/x/x | x/x/x | x/x/x | x/x/x | x/./. | existing |
| Paris | x/./. | x/./. | x/./. | x/./. | ././. | ././. | ././. | . . . |
| Berlin | x/./. | x/./. | x/./. | x/./. | ././. | ././. | ././. | . . . |

82 of 204 scheduled results complete.

## Log
- 2026-10-26 07:07 started the queue (2 cores, scheduler deadline for new jobs 16:47). Design: experiments/run_seeds10.py (phases core | arp | grid), experiments/run_seeds10_queue.py; parts in results/seeds10_parts/. London seed 3 was run by hand before the queue (core 28 s, ARP 19 s, full grid 112 s).
- 2026-10-26 10:32 rescheduled (S10_ORDER=light_first): the core phase runs at about 7 jobs/hour (DIP stage of Paris, Moscow, Bombay, Cairo takes 15-30 min), so the cheap work of New Delhi / Buenos Aires / London (full grid, ARP) was moved before the remaining heavy core jobs to protect the headline grid. The first scheduler was stopped (its running jobs continued) and a second one started: results/logs/seeds10_queue2.out. Restart command: S10_ORDER=light_first nohup python experiments/run_seeds10_queue.py --deadline 'YYYY-mm-dd HH:MM' > results/logs/seeds10_queue2.out 2>&1 &
- 2026-10-26 12:30 third scheduler start (results/logs/seeds10_queue3.out): full-grid cities' grid+ARP for all seeds before the remaining heavy core jobs (time budget); heavy-city ARP and coarse grids will be cut first.
