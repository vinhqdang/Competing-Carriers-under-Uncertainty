"""Regret of the OLD (price-and-branch) E1 equilibria under the exact oracle, for every city and seed.

  python experiments/run_old_regret.py CITY SEED  ->  results/exact_parts/oldreg_<city>_s<seed>.csv
The price-and-branch equilibrium is recomputed (deterministic, reproduces results/pb_old/E1_<city>.csv), then every carrier's best response is
computed with the exact oracle on a fresh elementary pool (branch-and-price, 20 s limit, 120 s retry).
"""
import json
import os
import sys

os.environ.pop("CCU_BP_TIME", None)  # the equilibrium itself is the price-and-branch one

import numpy as np
import pandas as pd

from common import RES, solve_ne, write_csv, zb

city, seed = sys.argv[1], int(sys.argv[2])
out = RES / "exact_parts" / f"oldreg_{city}_s{seed}.csv"
if out.exists():
    sys.exit(0)
g = zb.build_city_game(city, n_cust=22, seed=seed)
o = solve_ne(g, rounds=8, certify="fresh")
old = pd.read_csv(RES / "pb_old" / f"E1_{city}.csv")
old = old[(old.scenario == "base") & (old.seed == seed)].iloc[0]
g.bp_time, g.bp_retry = 20.0, 120.0
reg = g.regrets(o["profile"], count=False, fresh=True)
st = g._st
write_csv(out, [dict(city=city, seed=seed, welfare_replay=o["row"]["welfare"], welfare_old_file=old.welfare, regret_pb_certified=o["row"]["max_regret"],
                     regret_exact_max=float(reg.max()), regret_exact_each=json.dumps([round(float(v), 4) for v in reg]),
                     n_carriers_with_regret=int((reg > 1e-6).sum()), bp_calls=st["calls"], bp_optimal=st["optimal"], bp_unproven=st["timeouts"])])
print(city, seed, "max exact regret of the price-and-branch equilibrium", float(reg.max()), flush=True)
