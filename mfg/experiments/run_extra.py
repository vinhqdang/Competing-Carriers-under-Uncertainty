"""E4-E7: Gamma-maximin surcharge, belief-width scaling, ARP paths, the Cournot-corrected flat rule and solver cost.

Resumable per output file (a finished file is not recomputed; partial files are rebuilt by key).
  PYTHONPATH=mfg/src python3 mfg/experiments/run_extra.py [gamma|width|paths|flat|cost]   (default: all)
Outputs in mfg/results/: gamma.csv, width.csv, arp_paths.csv, flat_rule.csv, solver_cost.csv.
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
from mfgcc import theory as th
from mfgcc.leader import arp_fixed_point, knorm_inv, social_optimum, welfare
from mfgcc.qp import frank_wolfe, solve

RES = Path(__file__).resolve().parents[1] / "results"
KG = [1, 4, 16, 64, 256]
DELTAS = [0.25, 0.5, 1.0, 2.0, 4.0]


def mnorm(x, m):
    return float(np.sqrt(np.sum(m * x * x)))


def append(path, fields, row):
    new = not path.exists()
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fields)
        if new:
            w.writeheader()
        w.writerow(row)


def keys(path, cols):
    if not path.exists():
        return set()
    with open(path) as fh:
        return {tuple(r[c] for c in cols) for r in csv.DictReader(fh)}


# ---------------------------------------------------------------- Gamma-maximin
GF = ["city", "seed", "k", "delta", "w_med", "dev_W_m", "bound_W", "dev_N_m", "wloss_gamma", "wloss_bound",
      "SW_opt", "toll_shift_kinv", "toll_shift_bound", "rho"]


def gamma_job(args):
    c, seed = args
    path = RES / "gamma.csv"
    if (c, str(seed)) in {(a, b) for a, b in keys(path, ["city", "seed"])}:
        return
    g = C.build(c, seed)
    m, kap = g.m, g.kappa
    rho = float((kap / m).max())
    w = np.full(g.d, float(np.median(np.concatenate([B["lots"] for B in g.base]))))
    rows = []
    for k in KG:
        bl = g.blocks(k)
        QW, QN = solve(bl, m, own=False).Q, solve(bl, m, own=True).Q
        so = social_optimum(bl, m, kap)
        sw_opt = welfare(bl, so, m, kap)
        uW = kap * so.Q
        for dl in DELTAS:
            sur = dl * m * w
            QWg, QNg = solve(bl, m, own=False, u=sur).Q, solve(bl, m, own=True, u=sur).Q
            uG, _ = arp_fixed_point(bl, m, kap, own=False, surcharge=sur)
            eqG = solve(bl, m, own=False, u=uG + sur)
            rows.append(dict(city=c, seed=seed, k=k, delta=dl, w_med=w[0], dev_W_m=mnorm(QWg - QW, m),
                             bound_W=dl * mnorm(w, m), dev_N_m=mnorm(QNg - QN, m),
                             wloss_gamma=sw_opt - welfare(bl, eqG, m, kap),
                             wloss_bound=0.5 * dl ** 2 * float(np.sum((m * w) ** 2 / (m + kap))), SW_opt=sw_opt,
                             toll_shift_kinv=knorm_inv(uG - uW, kap),
                             toll_shift_bound=np.sqrt(rho) * float(np.sqrt(np.sum(sur ** 2 / m))) / (1 - rho),
                             rho=rho))
    for r in rows:
        append(path, GF, r)
    print("gamma", c, seed, flush=True)


# ---------------------------------------------------------------- width scaling (algebra on the Omega bound)
WF = ["city", "seed", "k", "N", "d", "sigma_max", "width_bound", "width_rel", "term"]


def width_rows():
    path = RES / "width.csv"
    if path.exists():
        return
    for c in C.CITIES:
        g = C.build(c, 0)
        Qm = float(solve(g.blocks(1), g.m, own=False).Q.mean())
        for k in [1, 2, 4, 8, 16, 32, 64, 128, 256, 1024, 4096]:
            N = len(g.base) * k
            # largest range of one carrier's contribution in one coordinate (unit weights, deliveries):
            # the whole per-carrier budget on the column with the largest delivery per vehicle-hour there
            smax = max(float((B["L"].multiply(1.0 / B["w"][None, :])).max()) * B["B"] / k for B in g.base)
            terms = [N - 1, g.d + 1, 1 + np.sqrt(g.d * np.log(2 * g.d) / 2)]
            j = int(np.argmin(terms))
            append(path, WF, dict(city=c, seed=0, k=k, N=N, d=g.d, sigma_max=smax, width_bound=smax * terms[j],
                                  width_rel=smax * terms[j] / Qm, term=["N-1", "d+1", "sqrt"][j]))
    print("width done", flush=True)


# ---------------------------------------------------------------- ARP paths
PF = ["city", "kappa_scale", "k", "own", "round", "dist_kinv", "step_ratio", "rho"]


def paths_rows():
    path = RES / "arp_paths.csv"
    if path.exists():
        return
    for c in ("Cairo", "Paris", "NewYork"):
        for ks in (1.0, 10.0):
            g = C.build(c, 0, kappa_scale=ks)
            m, kap = g.m, g.kappa
            rho = float((kap / m).max())
            for k in (1, 16, 256):
                bl = g.blocks(k)
                for own in (True, False):
                    ustar, _ = arp_fixed_point(bl, m, kap, own=own)
                    u = np.zeros(g.d)
                    prev = knorm_inv(u - ustar, kap)
                    append(path, PF, dict(city=c, kappa_scale=ks, k=k, own=own, round=0, dist_kinv=prev,
                                          step_ratio=np.nan, rho=rho))
                    for t in range(1, 9):
                        u = kap * solve(bl, m, own=own, u=u).Q
                        dist = knorm_inv(u - ustar, kap)
                        append(path, PF, dict(city=c, kappa_scale=ks, k=k, own=own, round=t, dist_kinv=dist,
                                              step_ratio=dist / prev if prev > 1e-12 else np.nan, rho=rho))
                        prev = dist
    print("paths done", flush=True)


# ---------------------------------------------------------------- Cournot-corrected flat rule (Omega's rule, splittable form)
FF = ["city", "seed", "kappa_scale", "k", "rounds", "resid", "dist_to_pigou_kinv", "pigou_kinv", "SW_opt", "SW_N0",
      "SW_flat", "SW_obs", "gain_flat", "gain_obs"]


def flat_job(args):
    c, seed, ks = args
    path = RES / "flat_rule.csv"
    if (c, str(seed), str(float(ks))) in {(a, b, x) for a, b, x in keys(path, ["city", "seed", "kappa_scale"])}:
        return
    g = C.build(c, seed, kappa_scale=ks)
    m, kap = g.m, g.kappa
    rows = []
    for k in [1, 2, 4, 8, 16, 32, 64, 128, 256]:
        bl = g.blocks(k)
        so = social_optimum(bl, m, kap)
        sw_opt = welfare(bl, so, m, kap)
        uW = kap * so.Q
        s0 = solve(bl, m, own=True)
        _, fp = arp_fixed_point(bl, m, kap, own=True)
        u = np.zeros(g.d)
        resid = np.inf
        t = 0
        for t in range(1, 61):
            sol = solve(bl, m, own=True, u=u)
            # active carriers per coordinate: k replicas of every segment with a positive contribution there
            nact = k * np.sum([a > 1e-6 * max(1.0, a.max()) for a in sol.a], axis=0)
            mean_lot = np.where(nact > 0, sol.Q / np.maximum(nact, 1), 0.0)
            target = kap * sol.Q - m * mean_lot
            unew = 0.5 * u + 0.5 * target
            resid = float(np.abs(unew - u).max())
            u = unew
            if resid < 1e-7 * max(1.0, float(np.abs(uW).max())):
                break
        sol = solve(bl, m, own=True, u=u)
        rows.append(dict(city=c, seed=seed, kappa_scale=ks, k=k, rounds=t, resid=resid,
                         dist_to_pigou_kinv=knorm_inv(u - uW, kap), pigou_kinv=knorm_inv(uW, kap), SW_opt=sw_opt,
                         SW_N0=welfare(bl, s0, m, kap), SW_flat=welfare(bl, sol, m, kap),
                         SW_obs=welfare(bl, fp, m, kap),
                         gain_flat=(welfare(bl, sol, m, kap) - welfare(bl, s0, m, kap)) / sw_opt,
                         gain_obs=(welfare(bl, fp, m, kap) - welfare(bl, s0, m, kap)) / sw_opt))
    for r in rows:
        append(path, FF, r)
    print("flat", c, seed, ks, flush=True)


# ---------------------------------------------------------------- solver cost (Frank-Wolfe learning dynamics)
SF = ["city", "mode", "k", "N", "eq", "iters", "rel_gap", "time_s", "clarabel_time_s"]


def cost_rows():
    path = RES / "solver_cost.csv"
    if path.exists():
        return
    for c in ("Cairo", "Paris"):
        g = C.build(c, 0)
        m = g.m
        rng = np.random.default_rng(5)
        for mode, ks in (("replica", [1, 4, 16, 64, 256]), ("hetero", [1, 2, 4, 8])):
            for k in ks:
                bl = g.blocks(k, mode, rng)
                for own, eqn in ((True, "nash"), (False, "wardrop")):
                    t0 = time.time()
                    ref = solve(bl, m, own=own)
                    tc = time.time() - t0
                    scale = max(abs(ref.obj), 1.0)
                    t0 = time.time()
                    tr = []
                    fw = frank_wolfe(bl, m, own=own, iters=3000, tol=1e-4 * scale, trace=tr)
                    append(path, SF, dict(city=c, mode=mode, k=k, N=len(g.base) * k, eq=eqn, iters=fw.iters,
                                          rel_gap=fw.gap / scale, time_s=time.time() - t0, clarabel_time_s=tc))
    print("cost done", flush=True)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    nproc = int(os.environ.get("NPROC", "3"))
    RES.mkdir(parents=True, exist_ok=True)
    if which in ("gamma", "all"):
        with Pool(nproc) as p:
            list(p.imap_unordered(gamma_job, [(c, s) for s in range(3) for c in C.CITIES]))
    if which in ("width", "all"):
        width_rows()
    if which in ("paths", "all"):
        paths_rows()
    if which in ("flat", "all"):
        with Pool(nproc) as p:
            list(p.imap_unordered(flat_job, [(c, s, ks) for ks in (1.0, 10.0) for s in range(3) for c in C.CITIES]))
    if which in ("cost", "all"):
        cost_rows()
