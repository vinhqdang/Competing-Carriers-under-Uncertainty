"""Tiny games with exhaustive enumeration: DIP against the exact leader optimum over all zone charges.

For every pure profile sigma the set of zone charges u (per-delivery equivalent) that make sigma a pure Nash equilibrium
is a polyhedron (finitely many linear inequalities, all enumerated here).  The exact optimistic leader optimum over
u in [-alpha, alpha]^Z is the smallest social cost among profiles whose polyhedron is non-empty; the same with u
restricted to the grid family (s + r theta ext_z, theta >= 0) and to a uniform per-delivery charge.  The 63-point grid
of experiments/run_leader.py is evaluated by enumeration of the equilibrium set at each point.

Usage: python experiments/dip_tiny.py [--n 30]      -> results/dip_tiny.csv (resumable per instance)
"""
import argparse
import itertools
import time

import numpy as np
from scipy.optimize import linprog

from common import RES, read_rows, write_csv, zb, zmc  # noqa: F401
from ccu import dip

THETAS = [0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
SFRACS = [-0.6, -0.4, -0.2, -0.1, 0.0, 0.1, 0.2, 0.4, 0.6]


def enum(g):
    """plans per carrier at zero charges: list of (q, a, c0) with c0 the plan cost without charges."""
    g.set_charges()
    _, _, plans = zb.enumerate_game(g)
    out = []
    for i in range(g.N):
        out.append([(p.q.copy(), p.a.copy(), float(p.c), p) for _, p in plans[i]])
    return out


def profile_tables(g, P):
    """Arrays over all pure profiles: SC, Q (deliveries per zone), and per carrier / alternative the NE constraint data."""
    N, Z = g.N, g.Z
    M = g.M
    shape = [len(p) for p in P]
    idxs = list(itertools.product(*[range(s) for s in shape]))
    SC = np.empty(len(idxs))
    Phi0 = np.empty(len(idxs))
    for n, idx in enumerate(idxs):
        prof = [P[i][k][3] for i, k in enumerate(idx)]
        SC[n] = dip.social_cost(g, prof)
        Phi0[n] = g.potential(prof)
    return idxs, SC, Phi0


def constraints(g, P, idx):
    """NE of profile idx under u  <=>  G u >= h  (rows: carrier i, alternative k != idx_i)."""
    M = g.M
    A = sum(P[i][k][1] for i, k in enumerate(idx))
    G, h = [], []
    for i, k in enumerate(idx):
        Am = A - P[i][k][1]
        qk, ak, ck, _ = P[i][k]
        Jk = ck + float(ak @ (M * Am))
        for j, (qj, aj, cj, _) in enumerate(P[i]):
            if j == k:
                continue
            Jj = cj + float(aj @ (M * Am))
            G.append(qj - qk)
            h.append(Jk - Jj)
    return np.array(G), np.array(h)


def feasible(G, h, B, lo, hi, ylo=None, yhi=None):
    """exists y with G B y >= h, lo <= B y <= hi (and optional bounds on y)?  returns y or None."""
    k = B.shape[1]
    A_ub = np.vstack([-(G @ B), B, -B])
    b_ub = np.concatenate([-h, hi, -lo])
    bounds = [(ylo[j] if ylo is not None else None, yhi[j] if yhi is not None else None) for j in range(k)]
    res = linprog(np.zeros(k), A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")
    return res.x if res.status == 0 else None


_CACHE = {}


def all_constraints(g, P, idxs):
    key = id(P)
    if key not in _CACHE:
        _CACHE.clear()
        GH = [constraints(g, P, idx) for idx in idxs]
        _CACHE[key] = (np.array([x[0] for x in GH]), np.array([x[1] for x in GH]))
    return _CACHE[key]


def ne_set(g, P, idxs, u):
    """indices (into idxs) of the pure NE under charges u."""
    G, h = all_constraints(g, P, idxs)
    ok = np.all(G @ u >= h - 1e-9, axis=1)
    return list(np.flatnonzero(ok))


def leader_opt(g, P, idxs, SC, B, lo, hi, ylo=None, yhi=None):
    order = np.argsort(SC)
    GA, HA = all_constraints(g, P, idxs)
    for n in order:
        G, h = GA[n], HA[n]
        y = feasible(G, h, B, lo, hi, ylo, yhi)
        if y is not None:
            return float(SC[n]), B @ y
    return np.nan, None


def make(seed, N, Z, n_cust, gcx):
    g = zb.make_tiny_game(N=N, Z=Z, n_cust=n_cust, seed=seed)
    g.gc = g.gc * gcx  # congestion strength (gcx = 1: make_tiny_game default, where congestion is negligible)
    return g


def run_instance(seed, N, Z, n_cust, gcx=1.0):
    g = make(seed, N, Z, n_cust, gcx)
    P = enum(g)
    idxs, SC, Phi0 = profile_tables(g, P)
    act = dip.active_zones(g)
    lo, hi = np.where(act, -g.alpha, 0.0), np.where(act, g.alpha, 0.0)
    # unpriced equilibrium: potential minimiser (a pure NE), and the full NE set
    ne0 = ne_set(g, P, idxs, np.zeros(Z))
    n_unpr = min(ne0, key=lambda n: Phi0[n])
    sc_ne = float(SC[n_unpr])
    sc_ne_worst = float(max(SC[n] for n in ne0))
    sc_so = float(SC.min())
    prof0 = [P[i][k][3] for i, k in enumerate(idxs[n_unpr])]
    X0 = sum(p.a[Z:] for p in prof0)
    ext = g.gc * X0
    t0 = time.perf_counter()
    # exact leader optima
    Bz = np.eye(Z)[:, act]
    opt_zone, _ = leader_opt(g, P, idxs, SC, Bz, lo, hi)
    Bf, _ = dip.grid_family(g, ext)
    opt_fam, _ = leader_opt(g, P, idxs, SC, Bf, lo, hi, ylo=[None, 0.0], yhi=[None, None])
    Bu = act[:, None].astype(float)
    opt_unif, _ = leader_opt(g, P, idxs, SC, Bu, lo, hi)
    t_exact = time.perf_counter() - t0
    # 63-point grid (fee = alpha / 1.5), equilibrium selected as potential minimiser; also best / worst NE
    fee = float(g.alpha[0]) / 1.5
    r = dip.lot_ratio(g)
    grid_sel, grid_best = np.inf, np.inf
    grid_calls = 0
    for th in THETAS:
        for sf in SFRACS:
            u = np.where(act, sf * fee + r * th * ext, 0.0)
            ne = ne_set(g, P, idxs, u)
            # potential under u: Phi0 + u.Q
            Qs = None
            phis = []
            for n in ne:
                Q = sum(P[i][k][0] for i, k in enumerate(idxs[n]))
                phis.append(Phi0[n] + float(u @ Q))
            sel = ne[int(np.argmin(phis))]
            grid_sel = min(grid_sel, SC[sel])
            grid_best = min(grid_best, min(SC[n] for n in ne))
            # oracle calls the grid spends with ZMC at this point
            gg = make(seed, N, Z, n_cust, gcx)
            _, _, toll = dip.instruments(gg, u)
            gg.set_charges(toll=toll)
            grid_calls += zmc.run_zmc(gg, rounds=6)["calls"]
    # DIP with the game's own oracle (column generation target)
    gd = make(seed, N, Z, n_cust, gcx)
    out = dip.dip(gd, so_iters=40)
    u = out["u"]
    ne_u = ne_set(g, P, idxs, u)
    key = lambda prof: tuple(np.round(np.concatenate([p.q for p in prof]), 9))
    pk = key(out["profile"])
    is_ne = any(key([P[i][k][3] for i, k in enumerate(idxs[n])]) == pk for n in ne_u)
    phis = []
    for n in ne_u:
        Q = sum(P[i][k][0] for i, k in enumerate(idxs[n]))
        phis.append(Phi0[n] + float(u @ Q))
    sc_dip_sel = float(SC[ne_u[int(np.argmin(phis))]]) if ne_u else np.nan
    sc_dip_worst = float(max(SC[n] for n in ne_u)) if ne_u else np.nan
    # DIP with the exact SO as target (oracle-free check of the implementation step)
    ge = make(seed, N, Z, n_cust, gcx)
    n_so = int(np.argmin(SC))
    # rebuild target plans through the oracle's pool: a plan with the same served set and minimal route cost
    tgt = []
    for i, k in enumerate(idxs[n_so]):
        q = P[i][k][0]
        cr = ge.carriers[i]
        served = [j + 1 for j, z in enumerate(cr.zones) if q[z] > 0]
        best = zb.brl.enumerate_best_routes(cr.inst)
        # partition of the served set into routes with minimal cost (small n: brute force over set partitions)
        tgt.append(_best_partition_plan(ge, i, served, best))
    oe = dip.dip(ge, target=tgt, target_info=dict(so_calls=0))
    row = dict(seed=seed, N=N, Z=Z, n_cust=n_cust, gcx=gcx, n_profiles=len(idxs), n_ne0=len(ne0),
               sc_ne=sc_ne, sc_ne_worst=sc_ne_worst, sc_so=sc_so,
               opt_zone=opt_zone, opt_family=opt_fam, opt_uniform=opt_unif, grid_selected=grid_sel, grid_best_ne=grid_best,
               grid_calls=grid_calls, dip1_sc=out["first"]["sc"], dip1_calls=out["first"]["calls"], dip_sc=out["sc"], dip_status=out["status"], dip_rounds=out["rounds"],
               dip_calls=out["calls"], dip_calls_so=out["calls_so"], dip_is_ne=bool(is_ne), dip_sc_target=out["sc_target"],
               dip_sel_sc=sc_dip_sel, dip_worst_sc=sc_dip_worst, dip_n_ne=len(ne_u),
               dipx_sc=oe["sc"], dipx_status=oe["status"], dipx_rounds=oe["rounds"], dipx_calls=oe["calls"],
               t_exact=t_exact)
    return row


def _best_partition_plan(g, i, served, best):
    """plan of carrier i serving exactly `served` (node ids) with minimal route loss (partition DP over subsets)."""
    from functools import lru_cache
    served = tuple(sorted(served))
    if not served:
        return g.empty_plan(i)
    cost = {fs: v for fs, v in best.items()}

    @lru_cache(None)
    def f(S):
        if not S:
            return 0.0, ()
        first = S[0]
        bestv, bestr = np.inf, None
        rest = S[1:]
        for m in range(1 << len(rest)):
            sub = (first,) + tuple(x for j, x in enumerate(rest) if m >> j & 1)
            fs = frozenset(sub)
            if fs not in cost:
                continue
            rem = tuple(x for x in S if x not in fs)
            v, rr = f(rem)
            if cost[fs][0] + v < bestv:
                bestv, bestr = cost[fs][0] + v, (cost[fs][1],) + rr
        return bestv, bestr

    v, routes = f(served)
    cr = g.carriers[i]
    zr = [tuple(int(cr.zones[j - 1]) for j in r) for r in routes]
    for r in routes:
        cr.pool._add(tuple(r))
    return g.plan_from_routes(i, zr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    a = ap.parse_args()
    path = RES / "dip_tiny.csv"
    rows = read_rows(path)
    done = {(int(r["seed"]), int(r["N"]), int(r["n_cust"]), float(r["gcx"])) for r in rows}
    configs = [(3, 6, 3, 1.0), (3, 6, 4, 1.0), (4, 5, 3, 1.0), (3, 5, 4, 20.0), (4, 5, 3, 20.0), (3, 5, 4, 60.0), (4, 5, 4, 60.0)]
    for seed in range(a.n):
        for N, Z, nc, gcx in configs:
            if (seed, N, nc, gcx) in done:
                continue
            r = run_instance(seed, N, Z, nc, gcx)
            rows.append(r)
            write_csv(path, rows)
            print(seed, N, Z, nc, r["dip_status"], round(r["sc_ne"], 2), round(r["opt_zone"], 2), round(r["dip_sc"], 2),
                  round(r["grid_selected"], 2), r["dip_calls"], r["grid_calls"], flush=True)


if __name__ == "__main__":
    main()
