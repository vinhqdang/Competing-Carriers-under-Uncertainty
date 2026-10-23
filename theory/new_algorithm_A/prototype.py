"""Prototype experiments for the Zone-Market Clearing (ZMC) method.

Run:  python3 prototype.py [E1 E2 E3 E4 E5]      (default: all; writes results.json next to this file)

E1  tiny instances, exact enumeration of all pure profiles (global potential minimum, set of pure NE)
E2  scaling in the number of zones at equal oracle budget (ZMC vs FW vs CG vs BR vs multi-start BR) + full CG reference
E3  stress tests: non-local supports, strong fleet coupling; empirical cross-variation kappa
E4  separable case (kappa = 0): ZMC price error vs rounds, independent of Z (Theorem 2)
E5  nine real city maps (zone-level proxy oracle)
"""
from __future__ import annotations

import itertools
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baselines import _restricted_master, _round_support, br_dynamics, column_generation, frank_wolfe  # noqa: E402
from core import make_city_game, make_game  # noqa: E402
from ssd import zmc  # noqa: E402

OUT = {}


def relaxed_value(g, pools, weights):
    M = g.M
    A = sum(sum(w * p.a for w, p in zip(weights[i], pools[i])) for i in range(g.N))
    return sum(sum(w * g.ctilde(p) for w, p in zip(weights[i], pools[i])) for i in range(g.N)) + 0.5 * A @ (M * A)


def round_pools(g, P):
    """Oracle-free: restricted master over the collected plans, then derandomised rounding."""
    W = [[1.0 if j == 0 else 0.0 for j in range(len(P[i]))] for i in range(g.N)]
    W = _restricted_master(g, P, W, iters=3000)
    return _round_support(g, P, W)


def run_zmc(g, rounds, mode="secant"):
    g.calls = 0
    best, pools = zmc(g, rounds=rounds, mode=mode)
    P = [list(pools[i].values()) for i in range(g.N)]
    start = min([best[2], round_pools(g, P)], key=g.potential)
    prof, ok = br_dynamics(g, init=start)
    return prof, g.calls, ok, best


def run_fw(g, iters):
    g.calls = 0
    pf, _, (P, W) = frank_wolfe(g, iters=iters)
    start = min([pf, round_pools(g, P)], key=g.potential)
    prof, ok = br_dynamics(g, init=start)
    return prof, g.calls, ok


def run_cg(g, iters):
    g.calls = 0
    pc, h, (P, W) = column_generation(g, max_iter=iters)
    prof, ok = br_dynamics(g, init=pc)
    return prof, g.calls, ok, (P, W)


def run_br(g):
    g.calls = 0
    prof, ok = br_dynamics(g)
    return prof, g.calls, ok


def run_brms(g, budget, seed):
    rng = np.random.default_rng(1000 + seed)
    g.calls = 0
    best = None
    first = True
    while g.calls < budget:
        init = None if first else [g.make_plan(i, np.floor(rng.random(g.Z) * (g.carriers[i].D + 1)))
                                   for i in range(g.N)]
        first = False
        prof, ok = br_dynamics(g, init=init)
        if best is None or g.potential(prof) < g.potential(best):
            best = prof
    return best, g.calls


# ------------------------------------------------------------------------------------------------ E1
def all_plans(g, i):
    cr = g.carriers[i]
    rngs = [range(int(cr.D[z]) + 1) if z in cr.S else [0] for z in range(g.Z)]
    return [g.make_plan(i, np.array(q)) for q in itertools.product(*rngs)]


def enumerate_game(g):
    plans = [all_plans(g, i) for i in range(g.N)]
    a = [np.array([p.a for p in pl]) for pl in plans]
    ct = [np.array([g.ctilde(p) for p in pl]) for pl in plans]
    shape = [len(pl) for pl in plans]
    M = g.M
    A = np.zeros(shape + [g.d])
    C = np.zeros(shape)
    for i in range(g.N):
        sh = [1] * g.N
        sh[i] = shape[i]
        A = A + a[i].reshape(sh + [g.d])
        C = C + ct[i].reshape(sh)
    Phi = C + 0.5 * np.einsum("...k,k,...k->...", A, M, A)
    ne = np.ones(shape, dtype=bool)
    for i in range(g.N):
        ne &= Phi <= Phi.min(axis=i, keepdims=True) + 1e-9
    return Phi, ne


def E1():
    rows = []
    for (N, Z, Dmax, sup) in [(3, 3, 3, 1.0), (4, 3, 2, 1.0), (3, 4, 2, 1.0)]:
        for seed in range(10):
            g = make_game(N=N, Z=Z, seed=seed, Dmax=Dmax, support=sup)
            Phi, ne = enumerate_game(g)
            gmin = float(Phi.min())
            ne_vals = Phi[ne]
            r = dict(N=N, Z=Z, seed=seed, profiles=int(Phi.size), n_ne=int(ne.sum()),
                     global_min=gmin, best_ne=float(ne_vals.min()), worst_ne=float(ne_vals.max()))
            for name, fn in [("BR", lambda: run_br(g)), ("ZMC6", lambda: run_zmc(g, 6)),
                             ("FW6", lambda: run_fw(g, 6)), ("CG", lambda: run_cg(g, 200))]:
                out = fn()
                prof, calls = out[0], out[1]
                v = g.potential(prof)
                r[name] = dict(calls=calls, phi=v, is_ne=bool(g.regrets(prof).max() < 1e-7),
                               hits_global=bool(abs(v - gmin) < 1e-7))
            rows.append(r)
    summ = {}
    for name in ["BR", "ZMC6", "FW6", "CG"]:
        summ[name] = dict(
            mean_calls=float(np.mean([r[name]["calls"] for r in rows])),
            frac_global=float(np.mean([r[name]["hits_global"] for r in rows])),
            frac_ne=float(np.mean([r[name]["is_ne"] for r in rows])),
            mean_excess_over_global=float(np.mean([r[name]["phi"] - r["global_min"] for r in rows])),
        )
    OUT["E1"] = dict(rows=rows, summary=summ)
    print("E1", json.dumps(summ, indent=1))


# ------------------------------------------------------------------------------------------------ E2
def E2(sizes=((4, 30), (5, 60), (6, 120), (6, 250)), seeds=5, budget_rounds=8):
    rows = []
    for (N, Z) in sizes:
        for seed in range(seeds):
            g = make_game(N=N, Z=Z, seed=seed)
            t0 = time.time()
            prof_ref, c_ref, _, (P, W) = run_cg(g, 600)
            star = relaxed_value(g, P, W)  # convexified optimum = lower bound on every pure potential value
            r = dict(N=N, Z=Z, seed=seed, relaxed_opt=star,
                     CGfull=dict(calls=c_ref, gap=g.potential(prof_ref) - star))
            prof, c, _ = run_br(g)
            r["BR"] = dict(calls=c, gap=g.potential(prof) - star)
            prof, c, _, _ = run_zmc(g, budget_rounds)
            r["ZMC"] = dict(calls=c, gap=g.potential(prof) - star)
            budget = c
            prof, c, _ = run_fw(g, budget_rounds)
            r["FW"] = dict(calls=c, gap=g.potential(prof) - star)
            prof, c, _, _ = run_cg(g, budget_rounds)
            r["CG"] = dict(calls=c, gap=g.potential(prof) - star)
            prof, c = run_brms(g, budget, seed)
            r["BRms"] = dict(calls=c, gap=g.potential(prof) - star)
            rows.append(r)
            print("E2", N, Z, seed, {k: (round(v["calls"]), round(v["gap"], 2)) for k, v in r.items()
                                     if isinstance(v, dict)}, f"{time.time() - t0:.0f}s", flush=True)
    OUT["E2"] = rows


# ------------------------------------------------------------------------------------------------ E3
def kappa_estimate(g, lam, trials=20, rng=None):
    """Empirical cross-variation: max_k |A_k(lam) - A_k(lam')| over random lam' with lam'_k = lam_k, divided by
    the total demand range of coordinate k; reported as the mean over k of the max over trials."""
    rng = rng or np.random.default_rng(0)
    base = sum(g.oracle(i, lam, rho=1.0, count=False).a for i in range(g.N))
    Amax = sum(g.make_plan(i, c.D).a for i, c in enumerate(g.carriers))
    out = np.zeros(g.d)
    for _ in range(trials):
        k = rng.integers(g.d)
        lp = lam * np.exp(0.3 * rng.standard_normal(g.d))
        lp[k] = lam[k]
        A2 = sum(g.oracle(i, lp, rho=1.0, count=False).a for i in range(g.N))
        out[k] = max(out[k], abs(A2[k] - base[k]) / max(Amax[k], 1e-9))
    nz = out[out > 0]
    return float(nz.mean()) if len(nz) else 0.0


def E3(seeds=4):
    rows = []
    cases = [("local", dict(local=True)), ("nonlocal", dict(local=False)),
             ("fleet-strong", dict(local=True))]
    for name, kw in cases:
        for seed in range(seeds):
            g = make_game(N=6, Z=120, seed=seed, **kw)
            if name == "fleet-strong":
                for c in g.carriers:
                    c.F *= 4
                    c.R = 1
            prof_ref, c_ref, _, (P, W) = run_cg(g, 600)
            star = relaxed_value(g, P, W)
            lam_star = g.M * sum(sum(w * p.a for w, p in zip(W[i], P[i])) for i in range(g.N))
            r = dict(case=name, seed=seed, kappa=kappa_estimate(g, lam_star),
                     CGfull=dict(calls=c_ref, gap=g.potential(prof_ref) - star))
            prof, c, _ = run_br(g)
            r["BR"] = dict(calls=c, gap=g.potential(prof) - star)
            prof, c, _, _ = run_zmc(g, 8)
            r["ZMC"] = dict(calls=c, gap=g.potential(prof) - star)
            prof, c, _ = run_fw(g, 8)
            r["FW"] = dict(calls=c, gap=g.potential(prof) - star)
            prof, c, _, _ = run_cg(g, 8)
            r["CG"] = dict(calls=c, gap=g.potential(prof) - star)
            rows.append(r)
            print("E3", name, seed, round(r["kappa"], 3), {k: (round(v["calls"]), round(v["gap"], 2))
                                                         for k, v in r.items() if isinstance(v, dict)}, flush=True)
    OUT["E3"] = rows


# ------------------------------------------------------------------------------------------------ E4
def E4(seeds=3):
    """kappa = 0: deliveries-only market (no congestion coordinate coupling) and no fleet term."""
    rows = []
    for Z in (20, 80, 320):
        for seed in range(seeds):
            g = make_game(N=5, Z=Z, seed=seed)
            g.gc[:] = 1e-9  # congestion coordinate inert; its price bracket collapses to ~0
            g.gmu[:] = 0.0
            for c in g.carriers:
                c.F = 0.0
                c.kap[:] = 0.0
                c.t[:] = 0.0
                c.s[:] = 0.0
            g._cache.clear()
            _, _, _, (P, W) = run_cg(g, 800)
            star = relaxed_value(g, P, W)
            for mode in ("bisect", "secant"):
                g.calls = 0
                H = []
                zmc(g, rounds=30, hist=H, mode=mode)
                gaps = [max(0.0, (star - G) / abs(star)) for _, G, _, _ in H]
                rows.append(dict(Z=Z, seed=seed, mode=mode, rel_dual_gap=gaps))
            print("E4", Z, seed, "bisect", " ".join(f"{x:.0e}" for x in rows[-2]["rel_dual_gap"][::3]),
                  "| secant", " ".join(f"{x:.0e}" for x in rows[-1]["rel_dual_gap"][::3]), flush=True)
    OUT["E4"] = rows


# ------------------------------------------------------------------------------------------------ E5
def E5(cities=("Cairo", "NewDelhi", "Bombay", "Moscow", "BuenosAires", "Paris", "NewYork", "London", "Berlin")):
    rows = []
    for city in cities:
        g = make_city_game(city, seed=0)
        t0 = time.time()
        prof_ref, c_ref, _, (P, W) = run_cg(g, 300)
        star = relaxed_value(g, P, W)
        scale = abs(star)
        r = dict(city=city, N=g.N, Z=g.Z, relaxed_opt=star, CGfull=dict(calls=c_ref, gap=(g.potential(prof_ref) - star) / scale))
        prof, c, _ = run_br(g)
        r["BR"] = dict(calls=c, gap=(g.potential(prof) - star) / scale)
        prof, c, _, _ = run_zmc(g, 8)
        r["ZMC"] = dict(calls=c, gap=(g.potential(prof) - star) / scale)
        budget = c
        prof, c, _ = run_fw(g, 8)
        r["FW"] = dict(calls=c, gap=(g.potential(prof) - star) / scale)
        prof, c, _, _ = run_cg(g, 8)
        r["CG"] = dict(calls=c, gap=(g.potential(prof) - star) / scale)
        prof, c = run_brms(g, budget, 0)
        r["BRms"] = dict(calls=c, gap=(g.potential(prof) - star) / scale)
        rows.append(r)
        print("E5", city, g.N, g.Z, {k: (round(v["calls"]), f"{v['gap']:.2e}") for k, v in r.items()
                                     if isinstance(v, dict)}, f"{time.time() - t0:.0f}s", flush=True)
    OUT["E5"] = rows


if __name__ == "__main__":
    which = sys.argv[1:] or ["E1", "E2", "E3", "E4", "E5"]
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")
    if os.path.exists(path):
        OUT.update(json.load(open(path)))
    for w in which:
        globals()[w]()
        json.dump(OUT, open(path, "w"), indent=1, default=float)
