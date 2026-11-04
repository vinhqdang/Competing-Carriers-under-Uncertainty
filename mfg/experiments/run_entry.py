"""Item 2: free entry (zero profit) under the charge rules (E10).

Fixed cost per carrier and day F_theta (segment theta), calibrated so that without a charge the free-entry number
of carriers lies between k0 and k0 + 1 per segment (mfgcc.fees.calibrate_F), k0 in {1, 4, 32} (N0 = 6, 24, 192);
SWEEP=1 runs the F sweep k0 in {2, 8, 16, 64} on seed 0.  For each calibration: free-entry equilibria under
none / obs / pm / pmfee and under the scaled observation-only rule u = theta kappa Q (theta in {0.5, 1.5}, the
second-best scan), and the Mankiw-Whinston test (welfare net of fixed costs when the no-charge free-entry counts
are scaled by lambda, conduct unchanged).  Output mfg/results/entry.csv (entry_sweep.csv); resumable per
(city, seed).
  PYTHONPATH=mfg/src python3 mfg/experiments/run_entry.py
"""
from __future__ import annotations

import csv
import os
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from mfgcc import city as C
from mfgcc.fees import calibrate_F, free_entry, planner_scale
from mfgcc.leader import social_optimum
from mfgcc.stake import decompose

SWEEP = os.environ.get("SWEEP", "0") == "1"
OUT = Path(__file__).resolve().parents[1] / "results" / ("entry_sweep.csv" if SWEEP else "entry.csv")
K0 = [2, 8, 16, 64] if SWEEP else [1, 4, 32]
SEEDS = range(1) if SWEEP else range(3)
RULES = [("none", 1.0), ("obs", 1.0), ("pm", 1.0), ("pmfee", 1.0), ("obs", 0.5), ("obs", 1.5)]
LAMS = np.round(np.concatenate([np.arange(0.02, 0.3, 0.02), np.arange(0.30, 1.201, 0.05)]), 2)
FIELDS = ["city", "seed", "k0", "N0", "rule", "theta", "N", "N_int", "active", "SW", "CS", "R", "fee_rev", "CC",
          "Pi", "fixed", "Q_total", "neg_share", "err", "resid", "iters", "F_mean", "SW_fb", "SW_opt",
          "lam_best", "SW_lam_best", "SW_lam1", "N_lam_best", "k"]


def done():
    if not OUT.exists():
        return set()
    with open(OUT) as fh:
        return {(r["city"], r["seed"]) for r in csv.DictReader(fh)}


def job(args):
    c, seed = args
    if (c, str(seed)) in done():
        return []
    g = C.build(c, seed)
    so = social_optimum(g.blocks(1), g.m, g.kappa)
    sw_opt = decompose(g.blocks(1), so, g.b, g.kappa)["SW"]
    rows = []
    for k0 in K0:
        F = calibrate_F(g, k0)
        sw_fb = sw_opt - float(F.sum())  # one carrier per segment, optimum implemented by subsidy and fee
        base = None
        for rule, th in RULES:
            r = free_entry(g, F, rule, theta=th, k_init=np.full(len(F), k0 + 0.5))
            row = dict(city=c, seed=seed, k0=k0, N0=6 * k0, rule=rule, theta=th, N=r["N"],
                       N_int=float(np.sum(np.floor(r["k"]))), active=r["active"], SW=r["SW"], CS=r["CS"], R=r["R"],
                       fee_rev=r["fee_rev"], CC=r["CC"], Pi=r["Pi"], fixed=r["fixed"], Q_total=r["Q_total"],
                       neg_share=r["neg_share"], err=r["err"], resid=r["resid"], iters=r["iters"],
                       F_mean=float(F.mean()), SW_fb=sw_fb, SW_opt=sw_opt, lam_best="", SW_lam_best="", SW_lam1="",
                       N_lam_best="", k=" ".join(f"{v:.6g}" for v in r["k"]))
            if rule == "none":
                base = r
                sc = planner_scale(g, F, r["k"], LAMS)
                j = int(np.argmax([v for _, v in sc]))
                row.update(lam_best=sc[j][0], SW_lam_best=sc[j][1], SW_lam1=dict(sc)[1.0],
                           N_lam_best=float(np.sum(np.maximum(sc[j][0] * r["k"], 1.0))))
            rows.append(row)
            print("entry", c, seed, k0, rule, th, f"N={r['N']:.2f} act={r['active']} err={r['err']:.1e}", flush=True)
    return rows


def write(rows):
    new = not OUT.exists()
    with open(OUT, "a", newline="") as fh:
        w = csv.DictWriter(fh, FIELDS)
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
