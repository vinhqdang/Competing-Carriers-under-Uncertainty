"""Stakeholder study, part 1: welfare decomposition and exposure under three charge rules (E8).

For every (city, seed, k) of the main study (nine cities, seeds 0-4, replicas k = 1, 2, 4, ..., 256, N = 6k) the
Nash equilibrium is computed under: no charge (none), the observation-only fixed point (obs), the Pigou-minus-
market-power charge (pm; mfgcc.stake.pm_charge) and, as a reference, the social optimum with the Pigou charge
(opt).  Output: mfg/results/stake.csv (one row per instance and rule).  Resumable: finished (city, seed, k) skipped.
  PYTHONPATH=mfg/src python3 mfg/experiments/run_stake.py
"""
from __future__ import annotations

import csv
import os
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from mfgcc import city as C
from mfgcc.leader import arp_fixed_point, social_optimum
from mfgcc.qp import solve
from mfgcc.stake import decompose, exposure_metrics, pm_charge

OUT = Path(__file__).resolve().parents[1] / "results" / "stake.csv"
KREP = [1, 2, 4, 8, 16, 32, 64, 128, 256]
SEEDS = range(5)
FIELDS = ["city", "seed", "k", "N", "rule", "SW", "CS", "Pi_op", "CC", "R", "Pi", "SW_opt", "resid", "neg_share",
          "Q_total", "n_zones", "pop_cov", "veh_hours", "exp_mean_min", "gini_zone", "gini_zh", "d10d1",
          "peak_hour_min", "corr_rel_dens", "corr_share_dens", "dens_mass_shift"]


def done():
    if not OUT.exists():
        return set()
    with open(OUT) as fh:
        return {(r["city"], r["seed"], r["k"]) for r in csv.DictReader(fh)}


def job(args):
    c, seed = args
    d = done()
    todo = [k for k in KREP if (c, str(seed), str(k)) not in d]
    if not todo:
        return 0
    g = C.build(c, seed)
    m, kap, b = g.m, g.kappa, g.b
    for k in todo:
        bl = g.blocks(k)
        so = social_optimum(bl, m, kap)
        s0 = solve(bl, m, own=True)
        uo, _ = arp_fixed_point(bl, m, kap, own=True)
        so_obs = solve(bl, m, own=True, u=uo)
        upm, s_pm, res = pm_charge(bl, m, kap, so)
        u_opt = kap * so.Q
        sw_opt = decompose(bl, so, b, kap)["SW"]
        rules = [("none", s0, np.zeros(g.d), 0.0), ("obs", so_obs, uo, 0.0), ("pm", s_pm, upm, res),
                 ("opt", so, u_opt, 0.0)]
        rows = []
        for name, sol, u, rs in rules:
            row = dict(city=c, seed=seed, k=k, N=len(g.base) * k, rule=name, SW_opt=sw_opt, resid=rs,
                       neg_share=float(np.mean(u < -1e-12)), Q_total=float(sol.Q.sum()))
            row.update(decompose(bl, sol, b, kap, u))
            row.update(exposure_metrics(g, sol.Q, None if name == "none" else s0.Q))
            rows.append(row)
        with open(OUT, "a", newline="") as fh:
            w = csv.DictWriter(fh, FIELDS)
            for r in rows:
                w.writerow(r)
        print("stake", c, seed, k, f"pm_resid={res:.1e}", flush=True)
    return len(todo)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not OUT.exists():
        with open(OUT, "w", newline="") as fh:
            csv.DictWriter(fh, FIELDS).writeheader()
    with Pool(int(os.environ.get("NPROC", "4"))) as pool:
        list(pool.imap_unordered(job, [(c, s) for s in SEEDS for c in C.CITIES]))
