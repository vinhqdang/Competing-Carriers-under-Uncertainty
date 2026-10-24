# Progress: branch-and-price for BRL

Resume after a restart (all commands skip finished work; at most 2 cores):

```
export OMP_NUM_THREADS=1
python experiments/run_bp.py verify                       # results/bp_verify.csv
python experiments/run_bp.py metro London Paris Berlin NewYork Bombay --tl 1800 &
python experiments/run_bp.py metro BuenosAires Cairo Moscow NewDelhi --tl 1800 &
python experiments/run_bp.py game London Paris Berlin --tl 20
python experiments/run_bp.py summary
```

Status: ALL DONE (2026-10-24). 800/800 exact vs enumeration; nine metro instances proven optimal; game rerun for London, Paris, Berlin.

Checklist
- [x] kernel `allow` argument added to `ccu.brl.espprc` (backward compatible)
- [x] src/ccu/bp.py (arc branching, best-bound, ng enlargement, Lagrangian bound, restricted-master MILP)
- [x] tests/test_bp.py (exact vs complete enumeration, forbidden-arc pricing, pool oracle)
- [x] 740 random formulations checked against enumeration in scratch runs (0 failures, 33 where price-and-branch is suboptimal)
- [x] results/bp_verify.csv (run_bp.py verify)
- [x] metro, 9 cities (results/bp_metro_<city>.json)
- [x] game oracle London/Paris/Berlin (results/bp_game_<city>.csv)
- [x] summary_bp*.csv, figures/bp_gap.png, docs/EXPERIMENTS.md section

Log
- 2026-10-24 01:13:18 metro London: root 51.0386 P&B 52.2686 B&P 51.3767 lb 51.3767 optimal nodes 691 91s | heur pbox 52.0349 saa 51.3767
- 2026-10-24 01:27:16 metro BuenosAires: root 47.2921 P&B 49.6464 B&P 48.1287 lb 48.1287 optimal nodes 11907 930s | heur pbox 49.3008 saa 49.4526
- 2026-10-24 01:38:27 metro Paris: root 37.7317 P&B 38.3177 B&P 38.2454 lb 38.2454 optimal nodes 9101 1509s | heur pbox 38.3170 saa 38.2855
- 2026-10-24 01:39:24 metro Berlin: root 51.8535 P&B 52.2285 B&P 52.0639 lb 52.0639 optimal nodes 365 57s | heur pbox 52.7746 saa 52.5479
- 2026-10-24 01:39:34 metro NewYork: root 46.0988 P&B 46.0988 B&P 46.0988 lb 46.0988 optimal nodes 1 10s | heur pbox 51.2296 saa 51.7054
- 2026-10-24 01:57:20 metro Cairo: root 38.8106 P&B 40.6548 B&P 40.6548 lb 39.0129 time_limit nodes 1448 1803s | heur pbox 40.4195 saa 40.4195
- (v1 without fleet-size rows: London/BA/Paris/Berlin/NY optimal, Cairo hit 1800 s limit with gap 4%; v1 JSONs kept in results/bp_v1/. Fleet-size rows + branching added -> rerun all nine as v2 below)
- 2026-10-24 02:00:05 metro London: root 51.0386 P&B 52.2712 B&P 51.3767 lb 51.3767 optimal nodes 59 21s | heur pbox 52.0349 saa 51.3767
- 2026-10-24 02:02:30 metro BuenosAires: root 47.2921 P&B 50.4628 B&P 48.1287 lb 48.1287 optimal nodes 1659 166s | heur pbox 49.3008 saa 49.4526
- 2026-10-24 02:02:35 metro Cairo: root 40.3903 P&B 40.4195 B&P 40.4195 lb 40.4195 optimal nodes 215 5s | heur pbox 40.4195 saa 40.4195
- 2026-10-24 02:12:00 metro Paris: root 37.7317 P&B 38.2524 B&P 38.2454 lb 38.2454 optimal nodes 4305 715s | heur pbox 38.3170 saa 38.2855
- 2026-10-24 02:12:06 metro Berlin: root 51.8535 P&B 52.7448 B&P 52.0639 lb 52.0639 optimal nodes 3 6s | heur pbox 52.7746 saa 52.5479
- 2026-10-24 02:12:15 metro NewYork: root 46.0988 P&B 46.0988 B&P 46.0988 lb 46.0988 optimal nodes 1 8s | heur pbox 51.2296 saa 51.7054
- 2026-10-24 02:12:18 metro Bombay: root 53.8151 P&B 53.9076 B&P 53.9076 lb 53.9076 optimal nodes 177 4s | heur pbox 54.0807 saa 54.0807
- 2026-10-24 02:20:18 metro Moscow: root 42.0093 P&B 44.1063 B&P 43.1669 lb 43.1669 optimal nodes 7487 1063s | heur pbox 43.6458 saa 43.7389
- 2026-10-24 02:20:20 metro NewDelhi: root 63.0258 P&B 64.3730 B&P 63.1835 lb 63.1835 optimal nodes 65 2s | heur pbox 63.1835 saa 63.1835
- 2026-10-24 02:20:36 game London: welfare 631.7779 (P&B 631.7780) served 0.1989 (0.1989) regret 0.00e+00 calls 49 time 3s (P&B 1s) bp optimal 55/55
- 2026-10-24 02:22:30 verify done (800 instances, 117s this call): bp exact 800/800, price-and-branch suboptimal 39
- 2026-10-24 02:23:34 game Paris: welfare 5718.1686 (P&B 5706.4300) served 0.8869 (0.8801) regret 0.00e+00 calls 50 time 88s (P&B 9s) bp optimal 54/56
- 2026-10-24 02:25:15 game Berlin: welfare 8401.3476 (P&B 8446.1900) served 0.8767 (0.8841) regret 0.00e+00 calls 59 time 43s (P&B 13s) bp optimal 69/69
- 2026-10-24 02:25:32 game London: welfare 631.7779 (P&B 631.7780) served 0.1989 (0.1989) regret 0.00e+00 calls 49 time 3s (P&B 1s) bp optimal 55/55
- 2026-10-24 02:25:53 metro_ng22 NewDelhi: root 63.0258 P&B 63.1835 B&P 63.1835 lb 63.1835 optimal nodes 49 2s | heur pbox 63.1835 saa 63.1835
- 2026-10-24 02:25:58 metro_ng22 Cairo: root 40.3903 P&B 40.4195 B&P 40.4195 lb 40.4195 optimal nodes 121 5s | heur pbox 40.4195 saa 40.4195
- 2026-10-24 02:26:03 metro_ng22 Bombay: root 53.8151 P&B 53.9076 B&P 53.9076 lb 53.9076 optimal nodes 205 5s | heur pbox 54.0807 saa 54.0807
- 2026-10-24 02:26:31 metro_ng22 Berlin: root 51.8613 P&B 52.3324 B&P 52.0639 lb 52.0639 label_overflow nodes 3 28s | heur pbox 52.7746 saa 52.5479
- 2026-10-24 02:27:45 metro_ng22 London: root 51.0386 P&B 51.3932 B&P 51.3767 lb 51.3767 label_overflow nodes 61 74s | heur pbox 52.0349 saa 51.3767
- 2026-10-24 02:30:05 game Paris: welfare 5718.1686 (P&B 5706.4300) served 0.8869 (0.8801) regret 0.00e+00 calls 50 time 84s (P&B 9s) bp optimal 54/56
- 2026-10-24 02:33:18 game Berlin: welfare 8401.3476 (P&B 8446.1900) served 0.8767 (0.8841) regret 0.00e+00 calls 59 time 42s (P&B 13s) bp optimal 69/69
- 2026-10-24 02:39:34 game Paris: welfare 5718.1686 (P&B 5706.4300) served 0.8869 (0.8801) regret 0.00e+00 calls 50 time 85s (P&B 9s) bp optimal 56/56
