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

Checklist
- [x] kernel `allow` argument added to `ccu.brl.espprc` (backward compatible)
- [x] src/ccu/bp.py (arc branching, best-bound, ng enlargement, Lagrangian bound, restricted-master MILP)
- [x] tests/test_bp.py (exact vs complete enumeration, forbidden-arc pricing, pool oracle)
- [x] 740 random formulations checked against enumeration in scratch runs (0 failures, 33 where price-and-branch is suboptimal)
- [ ] results/bp_verify.csv (run_bp.py verify)
- [ ] metro, 9 cities (results/bp_metro_<city>.json)
- [ ] game oracle London/Paris/Berlin (results/bp_game_<city>.csv)
- [ ] summary_bp*.csv, figures/bp_gap.png, docs/EXPERIMENTS.md section

Log
- 2026-10-24 01:13:18 metro London: root 51.0386 P&B 52.2686 B&P 51.3767 lb 51.3767 optimal nodes 691 91s | heur pbox 52.0349 saa 51.3767
