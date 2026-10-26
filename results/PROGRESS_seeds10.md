# Progress: ten-seed extension (seeds 3..9 added to 0..2), exact oracle

Resume after a restart (every job is resumable and writes atomically; finished work is skipped; 2 cores):

```
nohup python experiments/run_seeds10_queue.py > results/logs/seeds10_queue.out 2>&1 &
```

Updated 2026-10-26 07:08:36. Cells: core / arp / grid per seed, x = finished, . = missing, - = not scheduled (seeds 0-2: ARP exists for London, Buenos Aires, New Delhi, Mumbai; E1-E3, DIP and the grid of seeds 0-2 are the earlier runs).

| city | s3 | s4 | s5 | s6 | s7 | s8 | s9 | arp s0 s1 s2 |
|---|---|---|---|---|---|---|---|---|
| NewDelhi | x/./. | ././. | ././. | ././. | ././. | ././. | ././. | existing |
| Cairo | ././. | ././. | ././. | ././. | ././. | ././. | ././. | . . . |
| Moscow | ././. | ././. | ././. | ././. | ././. | ././. | ././. | . . . |
| BuenosAires | ././. | ././. | ././. | ././. | ././. | ././. | ././. | existing |
| NewYork | ././. | ././. | ././. | ././. | ././. | ././. | ././. | . . . |
| Bombay | ././. | ././. | ././. | ././. | ././. | ././. | ././. | existing |
| London | x/x/x | ././. | ././. | ././. | ././. | ././. | ././. | existing |
| Paris | ././. | ././. | ././. | ././. | ././. | ././. | ././. | . . . |
| Berlin | ././. | ././. | ././. | ././. | ././. | ././. | ././. | . . . |

4 of 204 scheduled results complete.

## Log
- 2026-10-26 07:07 started the queue (2 cores, scheduler deadline for new jobs 16:47). Design: experiments/run_seeds10.py (phases core | arp | grid), experiments/run_seeds10_queue.py; parts in results/seeds10_parts/. London seed 3 was run by hand before the queue (core 28 s, ARP 19 s, full grid 112 s).
