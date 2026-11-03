"""E1-E3: finite-N vs mean-field gap, toll convergence, PoA and leader gain on the nine cities.

Resumable: every finished (city, seed, mode, amp, kappa_scale, k) row is appended to mfg/results/gap.csv and
skipped on a rerun.  Usage:
  PYTHONPATH=mfg/src python3 mfg/experiments/run_gap.py main        # replicas, amp=1, seeds 0-4, k=1..256
  PYTHONPATH=mfg/src python3 mfg/experiments/run_gap.py hetero      # heterogeneous splits, seeds 0-2, k=1..16
  PYTHONPATH=mfg/src python3 mfg/experiments/run_gap.py profile     # amp in {0,0.5,1.5}, seeds 0-2
  PYTHONPATH=mfg/src python3 mfg/experiments/run_gap.py kappa       # kappa_scale 10, seeds 0-2
"""
from __future__ import annotations

import csv
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from mfgcc import city as C
from mfgcc.leader import arp_fixed_point, knorm, knorm_inv, social_optimum, welfare
from mfgcc.qp import solve

OUT = Path(__file__).resolve().parents[1] / "results" / "gap.csv"
KREP = [1, 2, 4, 8, 16, 32, 64, 128, 256]
KHET = [1, 2, 4, 8, 16]
FIELDS = ["city", "seed", "mode", "amp", "kappa_scale", "k", "N", "d", "rho", "QW_total", "QN_total", "gap_inf",
          "gap_m", "QW_m", "s", "ratio", "sqrt_bound", "err_inf", "toll_W_kinv", "toll_gap_kinv", "eps_k",
          "toll_bound", "SW_opt", "SW_N0", "SW_W0", "SW_Nfp", "poa_N", "poa_W", "gain_N", "gain_W", "wloss_fp",
          "wloss_bound", "solver_gap_N", "solver_gap_W", "t_N", "t_W"]


def done_keys():
    if not OUT.exists():
        return set()
    with open(OUT) as fh:
        return {(r["city"], r["seed"], r["mode"], r["amp"], r["kappa_scale"], r["k"]) for r in csv.DictReader(fh)}


def key(cityname, seed, mode, amp, ks, k):
    return (cityname, str(seed), mode, str(float(amp)), str(float(ks)), str(k))


def mnorm(x, m):
    return float(np.sqrt(np.sum(m * x * x)))


def run_job(args):
    cityname, seed, mode, amp, ks, klist = args
    done = done_keys()
    todo = [k for k in klist if key(cityname, seed, mode, amp, ks, k) not in done]
    if not todo:
        return 0
    g = C.build(cityname, seed, amp=amp, kappa_scale=ks)
    m, kap = g.m, g.kappa
    rho = float((kap / m).max())
    rows = []
    rng = np.random.default_rng([seed, 99])
    cache = {}
    for k in klist:
        bl = g.blocks(k, mode, rng)  # draw in order of klist so heterogeneous splits are reproducible
        if k not in todo:
            continue
        t0 = time.time()
        sN = solve(bl, m, own=True)
        tN = time.time() - t0
        t0 = time.time()
        if mode == "replica" and "W" in cache:
            sW = cache["W"]
        else:
            sW = solve(bl, m, own=False)
            if mode == "replica":
                cache["W"] = sW
        tW = time.time() - t0
        counts = [B.count for B in bl]
        s = max(float((a / c).max()) for a, c in zip(sN.a, counts))
        dQ = sN.Q - sW.Q
        sqrt_bound = 0.5 * np.sqrt(sum(float((a / c) @ (m * (a / c))) * c for a, c in zip(sW.a, counts)))
        err = np.sqrt(2 * max(sN.gap, 0) / m.min()) + np.sqrt(2 * max(sW.gap, 0) / m.min())
        row = dict(city=cityname, seed=seed, mode=mode, amp=float(amp), kappa_scale=float(ks), k=k, N=len(g.base) * k,
                   d=g.d, rho=rho, QW_total=float(sW.Q.sum()), QN_total=float(sN.Q.sum()),
                   gap_inf=float(np.abs(dQ).max()), gap_m=mnorm(dQ, m), QW_m=mnorm(sW.Q, m), s=s,
                   ratio=float(np.abs(dQ).max()) / s, sqrt_bound=sqrt_bound, err_inf=float(err),
                   solver_gap_N=sN.gap, solver_gap_W=sW.gap, t_N=tN, t_W=tW)
        if mode == "replica":
            if "SO" not in cache:
                cache["SO"] = social_optimum(bl, m, kap)
            so = cache["SO"]
            uW = kap * so.Q
            uN, fpN = arp_fixed_point(bl, m, kap, own=True)
            QWu = solve(bl, m, own=False, u=uN).Q
            eps = knorm(fpN.Q - QWu, kap)
            sw_opt = welfare(bl, so, m, kap)
            sw_n0, sw_w0, sw_fp = welfare(bl, sN, m, kap), welfare(bl, sW, m, kap), welfare(bl, fpN, m, kap)
            row.update(toll_W_kinv=knorm_inv(uW, kap), toll_gap_kinv=knorm_inv(uN - uW, kap), eps_k=eps,
                       toll_bound=eps / (1 - rho), SW_opt=sw_opt, SW_N0=sw_n0, SW_W0=sw_w0, SW_Nfp=sw_fp,
                       poa_N=sw_opt / sw_n0, poa_W=sw_opt / sw_w0, gain_N=(sw_fp - sw_n0) / sw_opt,
                       gain_W=(sw_opt - sw_w0) / sw_opt, wloss_fp=sw_opt - sw_fp,
                       wloss_bound=0.5 * sum(float((a / c) @ (m * (a / c))) * c for a, c in zip(so.a, counts)))
        rows.append(row)
        with open(OUT, "a", newline="") as fh:
            csv.DictWriter(fh, FIELDS).writerow(row)
        print(cityname, seed, mode, amp, ks, k, f"ratio={row['ratio']:.3f}", f"tN={tN:.1f}", flush=True)
    return len(rows)


def jobs(which):
    out = []
    if which == "main":
        for seed in range(5):
            for c in C.CITIES:
                out.append((c, seed, "replica", 1.0, 1.0, KREP))
    elif which == "hetero":
        for seed in range(3):
            for c in C.CITIES:
                out.append((c, seed, "hetero", 1.0, 1.0, KHET))
    elif which == "profile":
        for seed in range(3):
            for amp in (0.0, 0.5, 1.5):
                for c in C.CITIES:
                    out.append((c, seed, "replica", amp, 1.0, KREP))
    elif which == "kappa":
        for seed in range(3):
            for c in C.CITIES:
                out.append((c, seed, "replica", 1.0, 10.0, KREP))
    return out


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "main"
    nproc = int(os.environ.get("NPROC", "3"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not OUT.exists():
        with open(OUT, "w", newline="") as fh:
            csv.DictWriter(fh, FIELDS).writeheader()
    with Pool(nproc) as pool:
        for _ in pool.imap_unordered(run_job, jobs(which)):
            pass
