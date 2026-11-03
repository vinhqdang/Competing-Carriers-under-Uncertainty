"""Stakeholder study, part 3: N identical carriers, welfare-optimal charge = Pigou minus a market-power term (E7).

One segment (n_types = 1) split into N identical carriers.  For every city, seed and N the script computes the social
optimum Q^opt, the closed-form charge u*_N = (kappa - m/N) Q^opt and checks that the Nash equilibrium under u*_N has
aggregate Q^opt and welfare SW^opt; it also reports the welfare loss of no charge and of the pure Pigou charge
kappa Q^opt, the fraction of zone-hours in which u*_N is a subsidy, and the deviation of the Nash/Wardrop aggregate
ratio from the Cournot value N/(N+1).   Output: mfg/results/ident.csv (resumable).
  PYTHONPATH=mfg/src python3 mfg/experiments/run_ident.py
"""
from __future__ import annotations

import csv
import os
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from mfgcc import city as C
from mfgcc.leader import social_optimum, welfare
from mfgcc.qp import solve
from mfgcc.stake import identical_optimal_charge

OUT = Path(__file__).resolve().parents[1] / "results" / "ident.csv"
NS = [1, 2, 3, 6, 12, 24, 48, 96, 192, 384, 768, 1536]
F = ["city", "seed", "N", "d", "q_err", "sw_err", "loss_none", "loss_pigou", "loss_ustar", "sub_share",
     "ratio_QN_QW", "cournot", "ratio_dev", "ustar_over_pigou", "market_power_rel", "frac_kappa_gt_m_over_N"]


def job(a):
    c, seed = a
    if OUT.exists():
        with open(OUT) as fh:
            if any(r["city"] == c and r["seed"] == str(seed) for r in csv.DictReader(fh)):
                return
    g = C.build(c, seed, n_types=1)
    m, kap = g.m, g.kappa
    rows = []
    for N in NS:
        bl = g.blocks(N)
        so = social_optimum(bl, m, kap)
        swo = welfare(bl, so, m, kap)
        ust = identical_optimal_charge(m, kap, so.Q, N)
        nash = solve(bl, m, own=True, u=ust)
        n0 = solve(bl, m, own=True)
        npig = solve(bl, m, own=True, u=kap * so.Q)
        QW = solve(bl, m, own=False).Q
        ratio = float(n0.Q.sum() / QW.sum())
        pig = kap * so.Q
        rows.append(dict(city=c, seed=seed, N=N, d=g.d,
                         q_err=float(np.sqrt(np.sum(m * (nash.Q - so.Q) ** 2) / np.sum(m * so.Q ** 2))),
                         sw_err=abs(welfare(bl, nash, m, kap) - swo) / swo,
                         loss_none=(swo - welfare(bl, n0, m, kap)) / swo,
                         loss_pigou=(swo - welfare(bl, npig, m, kap)) / swo,
                         loss_ustar=(swo - welfare(bl, nash, m, kap)) / swo, sub_share=float(np.mean(ust < 0)),
                         ratio_QN_QW=ratio, cournot=N / (N + 1), ratio_dev=ratio / (N / (N + 1)) - 1,
                         ustar_over_pigou=float(ust.sum() / pig.sum()),
                         market_power_rel=float(np.sum(m * so.Q / N) / pig.sum()),
                         frac_kappa_gt_m_over_N=float(np.mean(kap > m / N))))
    with open(OUT, "a", newline="") as fh:
        w = csv.DictWriter(fh, F)
        if fh.tell() == 0:
            w.writeheader()
        for r in rows:
            w.writerow(r)
    print("ident", c, seed, flush=True)


if __name__ == "__main__":
    with Pool(int(os.environ.get("NPROC", "4"))) as p:
        list(p.imap_unordered(job, [(c, s) for s in range(3) for c in C.CITIES]))
