"""Stakeholder study, part 2: one city-wide charge versus zone-hour charges, and mis-specified charges (E9, E10).

uniform.csv  best single per-delivery charge u (same in every zone-hour; scalar optimised over a grid refined by a
             bounded search) under Nash (k = 1..256 replicas per segment, N = 6k) and under Wardrop (N = infinity),
             with the welfare of no charge, of the Pigou-minus-market-power zone-hour charge (pm) and of the optimum.
misspec.csv  charge (1 + eps) * u_ref with eps in {-25, -10, +10, +25}%: Wardrop with u_ref = kappa Q^opt (Pigou) and
             measured loss against the bounds of Theorem 13(a); Nash (N = 6, 24, 192, 1536) with u_ref = pm charge.
Resumable per (city, seed).   PYTHONPATH=mfg/src python3 mfg/experiments/run_uniform.py
"""
from __future__ import annotations

import csv
import os
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

from mfgcc import city as C
from mfgcc.leader import social_optimum, welfare
from mfgcc.qp import solve
from mfgcc.stake import n_active, pm_charge

RES = Path(__file__).resolve().parents[1] / "results"
KREP = [1, 2, 4, 8, 16, 32, 64, 128, 256]
KMIS = [1, 4, 32, 256]
EPS = [-0.25, -0.10, 0.10, 0.25]
UF = ["city", "seed", "k", "N", "u_star", "u_pigou_mean", "SW_opt", "SW_none", "SW_uniform", "SW_pm", "loss_none",
      "loss_uniform", "loss_pm", "frac_uniform", "frac_pm", "u_over_scale", "solver"]
MF = ["city", "seed", "kind", "k", "N", "eps", "loss", "bound_loose", "bound_tight", "sw_opt"]


def append(path, fields, rows):
    new = not path.exists()
    with open(path, "a", newline="") as fh:
        w = csv.DictWriter(fh, fields)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def seen(path):
    if not path.exists():
        return set()
    with open(path) as fh:
        return {(r["city"], r["seed"]) for r in csv.DictReader(fh)}


def best_uniform(bl, m, own, lo, hi):
    f = lambda x: -welfare(bl, solve(bl, m, own=own, u=np.full(len(m), x)), m, KAP)
    grid = np.linspace(lo, hi, 13)
    vals = [f(x) for x in grid]
    i = int(np.argmin(vals))
    a, b = grid[max(i - 1, 0)], grid[min(i + 1, len(grid) - 1)]
    r = minimize_scalar(f, bounds=(a, b), method="bounded", options=dict(xatol=1e-6 * (hi - lo)))
    return (r.x, -r.fun) if r.fun < vals[i] else (grid[i], -vals[i])


def job_uniform(args):
    global KAP
    c, seed = args
    if (c, str(seed)) in seen(RES / "uniform.csv"):
        return
    g = C.build(c, seed)
    m, kap, b = g.m, g.kappa, g.b
    KAP = kap
    rows = []
    for k in KREP + [None]:
        own = k is not None
        bl = g.blocks(k or 1)
        so = social_optimum(bl, m, kap)
        swo = welfare(bl, so, m, kap)
        scale = float(np.max(kap * so.Q)) * 1.5 + float(np.max(m * so.Q / np.maximum(n_active(bl, so), 1)))
        s0 = welfare(bl, solve(bl, m, own=own), m, kap)
        u, sw = best_uniform(bl, m, own, -scale, scale)
        if own:
            upm, spm, _ = pm_charge(bl, m, kap, so)
            swpm = welfare(bl, spm, m, kap)
        else:
            upm, swpm = kap * so.Q, swo
        gain = swpm - s0
        rows.append(dict(city=c, seed=seed, k=k if own else "inf", N=len(g.base) * k if own else "inf",
                         u_star=u, u_pigou_mean=float(np.mean(kap * so.Q)), SW_opt=swo, SW_none=s0, SW_uniform=sw,
                         SW_pm=swpm, loss_none=(swo - s0) / swo, loss_uniform=(swo - sw) / swo,
                         loss_pm=(swo - swpm) / swo, frac_uniform=(sw - s0) / gain if abs(gain) > 1e-12 else np.nan,
                         frac_pm=1.0, u_over_scale=u / scale, solver="nash" if own else "wardrop"))
    append(RES / "uniform.csv", UF, rows)
    print("uniform", c, seed, flush=True)


def job_misspec(args):
    c, seed = args
    if (c, str(seed)) in seen(RES / "misspec.csv"):
        return
    g = C.build(c, seed)
    m, kap, b = g.m, g.kappa, g.b
    rows = []
    bl = g.blocks(1)
    so = social_optimum(bl, m, kap)
    swo = welfare(bl, so, m, kap)
    pig = kap * so.Q
    for e in EPS:
        v = (1 + e) * pig
        sol = solve(bl, m, own=False, u=v)
        loss = swo - welfare(bl, sol, m, kap)
        dq = so.Q - sol.Q
        tight = float(np.dot(v - pig, dq) - 0.5 * np.sum(b * dq * dq))
        loose = 0.5 * float(np.sum((v - pig) ** 2 / b))
        rows.append(dict(city=c, seed=seed, kind="wardrop", k="inf", N="inf", eps=e, loss=loss, bound_loose=loose,
                         bound_tight=tight, sw_opt=swo))
    for k in KMIS:
        bl = g.blocks(k)
        so = social_optimum(bl, m, kap)
        swo = welfare(bl, so, m, kap)
        upm, _, _ = pm_charge(bl, m, kap, so)
        for e in EPS:
            sol = solve(bl, m, own=True, u=(1 + e) * upm)
            rows.append(dict(city=c, seed=seed, kind="nash_pm", k=k, N=len(g.base) * k, eps=e,
                             loss=swo - welfare(bl, sol, m, kap), bound_loose=np.nan, bound_tight=np.nan,
                             sw_opt=swo))
    append(RES / "misspec.csv", MF, rows)
    print("misspec", c, seed, flush=True)


def run(a):
    job_uniform(a)
    job_misspec(a)


if __name__ == "__main__":
    RES.mkdir(parents=True, exist_ok=True)
    with Pool(int(os.environ.get("NPROC", "4"))) as p:
        list(p.imap_unordered(run, [(c, s) for s in range(5) for c in C.CITIES]))
