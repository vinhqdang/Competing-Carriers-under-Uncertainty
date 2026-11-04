"""Item 1: recovering the market-power subsidy by lump-sum fees, fixed number of carriers (E9).

For every (city, seed, k), k in {1, 4, 32, 256} (N = 6k), the Pigou-minus-market-power charge (mfgcc.stake.pm_charge)
and the Nash equilibrium under it are computed; mfgcc.fees.fee_table gives, for a flat fee, a fee in proportion to
the licensed fleet (vehicle-hours) and a profit-proportional benchmark, the fee per carrier, the share of carrier
profit it takes and whether every carrier keeps a nonnegative profit (and at least its no-charge profit).  The
row also records the welfare when the deficit is recovered ex post (T_i = -<u, Q>/N, not lump-sum: the carriers
then face u (1 - 1/N)).  Output mfg/results/fees.csv; resumable.
  PYTHONPATH=mfg/src python3 mfg/experiments/run_fees.py
"""
from __future__ import annotations

import csv
import os
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from mfgcc import city as C
from mfgcc.fees import carrier_profits, fee_table, own_rebate_charge
from mfgcc.leader import social_optimum
from mfgcc.qp import solve
from mfgcc.stake import decompose, pm_charge

OUT = Path(__file__).resolve().parents[1] / "results" / "fees.csv"
KREP = [1, 4, 32, 256]
SEEDS = range(5)
FIELDS = None


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
        return []
    g = C.build(c, seed)
    m, kap, b = g.m, g.kappa, g.b
    rows = []
    for k in todo:
        bl = g.blocks(k)
        N = len(bl) * k
        so = social_optimum(bl, m, kap)
        s0 = solve(bl, m, own=True)
        pi0 = carrier_profits(bl, s0, m)
        u, s, res = pm_charge(bl, m, kap, so)
        ft = fee_table(bl, s, m, u, pi0=pi0)
        dec, dec0 = decompose(bl, s, b, kap, u), decompose(bl, s0, b, kap)
        # ex post recovery of the realised deficit: an own rebate of u/N per delivery
        s_ep = solve(bl, m, own=True, u=own_rebate_charge(u, N))
        sw_ep = decompose(bl, s_ep, b, kap)["SW"]
        row = dict(city=c, seed=seed, k=k, N=N, resid=res, SW_opt=decompose(bl, so, b, kap)["SW"], SW=dec["SW"],
                   SW0=dec0["SW"], Pi=dec["Pi"], Pi0=dec0["Pi"], Pi_op=dec["Pi_op"], CC=dec["CC"],
                   pi0_min=float(pi0.min()), SW_expost=sw_ep, neg_share=float(np.mean(u < -1e-12)))
        row.update({kk: (float(v) if not isinstance(v, bool) else int(v)) for kk, v in ft.items()})
        rows.append(row)
        print("fees", c, seed, k, f"R={ft['R']:.0f} share={ft['flat_share']:.2f} ok={ft['flat_ok']}", flush=True)
    return rows


def write(rows):
    new = not OUT.exists()
    with open(OUT, "a", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0].keys()))
        if new:
            w.writeheader()
        for r in rows:
            w.writerow(r)


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with Pool(int(os.environ.get("NPROC", "4"))) as pool:
        for rows in pool.imap_unordered(job, [(c, s) for s in SEEDS for c in C.CITIES]):
            if rows:
                write(rows)
