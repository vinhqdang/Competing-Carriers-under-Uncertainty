# Progress: "Why probability boxes" (ambiguity criteria, out-of-sample study and game re-run)

Resume after a restart (all commands skip finished work; one core):

```
export OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
nohup taskset -c 0 python experiments/run_ambiguity.py pipeline > results/logs/run_ambiguity.out 2>&1 &
```

Log
- 2026-10-26 07:12:02 validate: planner vs exact B&P on 9 instances, max gap 0.1049%, optimal in 8/9
- 2026-10-26 07:13:27 oracle plans done (36 rows)
- 2026-10-26 07:26:17 game London seed 0 pbox done (533s)
- 2026-10-26 07:28:08 game London seed 0 saa done (111s)
- 2026-10-26 07:30:43 game London seed 0 wass_th done (155s)
- 2026-10-26 07:31:28 run base: draw 0 complete for 9 cities, elapsed 18.0 min this call
- 2026-10-26 07:33:12 game London seed 0 wass_e0.5 done (149s)
- 2026-10-26 07:39:05 game London seed 1 pbox done (353s)
- 2026-10-26 07:40:19 game London seed 1 saa done (74s)
- 2026-10-26 07:42:06 game London seed 1 wass_th done (107s)
- 2026-10-26 07:44:12 game London seed 1 wass_e0.5 done (126s)
- 2026-10-26 07:48:17 game London seed 2 pbox done (245s)
- 2026-10-26 07:49:12 game London seed 2 saa done (56s)
- 2026-10-26 07:50:19 run base: draw 1 complete for 9 cities, elapsed 36.9 min this call
- 2026-10-26 07:50:38 game London seed 2 wass_th done (86s)
- 2026-10-26 07:52:20 game London seed 2 wass_e0.5 done (102s)
- 2026-10-26 07:56:28 game BuenosAires seed 0 pbox done (248s)
- 2026-10-26 07:57:52 game BuenosAires seed 0 saa done (84s)
- 2026-10-26 07:59:57 game BuenosAires seed 0 wass_th done (125s)
- 2026-10-26 08:02:13 game BuenosAires seed 0 wass_e0.5 done (136s)
- 2026-10-26 08:09:12 game BuenosAires seed 1 pbox done (419s)
- 2026-10-26 08:09:26 run base: draw 2 complete for 9 cities, elapsed 56.0 min this call
- 2026-10-26 08:10:09 game BuenosAires seed 1 saa done (57s)
- 2026-10-26 08:11:40 game BuenosAires seed 1 wass_th done (90s)
- 2026-10-26 08:13:27 game BuenosAires seed 1 wass_e0.5 done (107s)
- 2026-10-26 08:21:16 game BuenosAires seed 2 pbox done (469s)
- 2026-10-26 08:22:55 game BuenosAires seed 2 saa done (99s)
- 2026-10-26 08:25:17 game BuenosAires seed 2 wass_th done (142s)
- 2026-10-26 08:27:43 game BuenosAires seed 2 wass_e0.5 done (146s)
- 2026-10-26 08:28:51 game NewDelhi seed 0 pbox done (68s)
- 2026-10-26 08:29:40 run base: draw 3 complete for 9 cities, elapsed 76.2 min this call
- 2026-10-26 08:29:50 game NewDelhi seed 0 saa done (59s)
- 2026-10-26 08:31:03 game NewDelhi seed 0 wass_th done (73s)
- 2026-10-26 08:32:10 game NewDelhi seed 0 wass_e0.5 done (67s)
- 2026-10-26 08:35:32 game NewDelhi seed 1 pbox done (202s)
- 2026-10-26 08:36:41 game NewDelhi seed 1 saa done (69s)
- 2026-10-26 08:38:10 game NewDelhi seed 1 wass_th done (90s)
- 2026-10-26 08:39:14 game NewDelhi seed 1 wass_e0.5 done (64s)
- 2026-10-26 08:49:25 run base: draw 4 complete for 9 cities, elapsed 96.0 min this call
- 2026-10-26 08:49:50 game NewDelhi seed 2 pbox done (636s)
- 2026-10-26 08:51:00 game NewDelhi seed 2 saa done (70s)
- 2026-10-26 08:52:41 game NewDelhi seed 2 wass_th done (101s)
- 2026-10-26 08:53:57 game NewDelhi seed 2 wass_e0.5 done (76s)
- 2026-10-26 09:03:39 run base: draw 5 complete for 9 cities, elapsed 110.2 min this call
- 2026-10-26 09:16:36 run base: draw 6 complete for 9 cities, elapsed 123.2 min this call
- 2026-10-26 09:29:31 run base: draw 7 complete for 9 cities, elapsed 136.1 min this call
- 2026-10-26 09:41:56 run base: draw 8 complete for 9 cities, elapsed 148.5 min this call
- 2026-10-26 09:54:01 run base: draw 9 complete for 9 cities, elapsed 160.6 min this call
- 2026-10-26 10:05:51 run base: draw 10 complete for 9 cities, elapsed 172.4 min this call
- 2026-10-26 10:18:18 run base: draw 11 complete for 9 cities, elapsed 184.8 min this call
- 2026-10-26 10:30:19 run base: draw 12 complete for 9 cities, elapsed 196.9 min this call
- 2026-10-26 10:45:52 run base: draw 13 complete for 9 cities, elapsed 212.4 min this call
- 2026-10-26 10:58:46 run base: draw 14 complete for 9 cities, elapsed 225.3 min this call
- 2026-10-26 11:11:43 run base: draw 15 complete for 9 cities, elapsed 238.3 min this call
- 2026-10-26 11:24:34 run base: draw 16 complete for 9 cities, elapsed 251.1 min this call
- 2026-10-26 11:37:56 run base: draw 17 complete for 9 cities, elapsed 264.5 min this call
- 2026-10-26 11:50:55 run base: draw 18 complete for 9 cities, elapsed 277.5 min this call
- 2026-10-26 12:03:54 run base: draw 19 complete for 9 cities, elapsed 290.4 min this call
- 2026-10-26 12:07:51 shift sweep done (129600 rows)
- 2026-10-26 12:11:18 run heavy: draw 0 complete for 9 cities, elapsed 7.4 min this call
- 2026-10-26 12:17:47 run heavy: draw 1 complete for 9 cities, elapsed 13.9 min this call
- 2026-10-26 12:24:09 run heavy: draw 2 complete for 9 cities, elapsed 20.2 min this call
- 2026-10-26 12:30:44 run heavy: draw 3 complete for 9 cities, elapsed 26.8 min this call
- 2026-10-26 12:37:18 run heavy: draw 4 complete for 9 cities, elapsed 33.4 min this call
- 2026-10-26 12:43:57 run heavy: draw 5 complete for 9 cities, elapsed 40.0 min this call
- 2026-10-26 12:50:43 run heavy: draw 6 complete for 9 cities, elapsed 46.8 min this call
- 2026-10-26 12:57:25 run heavy: draw 7 complete for 9 cities, elapsed 53.5 min this call
- 2026-10-26 13:03:57 run heavy: draw 8 complete for 9 cities, elapsed 60.0 min this call
- 2026-10-26 13:12:30 run heavy: draw 9 complete for 9 cities, elapsed 68.6 min this call
- 2026-10-26 13:20:05 run heavy: draw 10 complete for 9 cities, elapsed 76.2 min this call
- 2026-10-26 13:26:25 run heavy: draw 11 complete for 9 cities, elapsed 82.5 min this call
- 2026-10-26 13:32:59 run heavy: draw 12 complete for 9 cities, elapsed 89.1 min this call
- 2026-10-26 13:39:14 run heavy: draw 13 complete for 9 cities, elapsed 95.3 min this call
- 2026-10-26 13:45:58 run heavy: draw 14 complete for 9 cities, elapsed 102.1 min this call
- 2026-10-26 13:52:33 run heavy: draw 15 complete for 9 cities, elapsed 108.6 min this call
- 2026-10-26 13:59:05 run heavy: draw 16 complete for 9 cities, elapsed 115.2 min this call
- 2026-10-26 14:05:26 run heavy: draw 17 complete for 9 cities, elapsed 121.5 min this call
- 2026-10-26 14:11:53 run heavy: draw 18 complete for 9 cities, elapsed 128.0 min this call
- 2026-10-26 14:18:30 run heavy: draw 19 complete for 9 cities, elapsed 134.6 min this call
- 2026-10-26 14:18:30 pipeline (validate, oracle, base, heavy) finished

Status: ALL DONE (2026-10-26). validate (8/9 optimal vs exact B&P, max gap 0.10%), oracle (36 plans), base run (9 cities x n 10/20/30/60 x 20 draws), heavy-tailed-training run (n 20/60 x 20 draws), shift sweep, game (3 cities x 3 seeds x 4 criteria), summary, figures, docs section "Why probability boxes", tests (171 passed).
