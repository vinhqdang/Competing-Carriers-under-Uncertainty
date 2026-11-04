"""Item 3: emissions, noise and through-traffic congestion added to the welfare accounting (E11).

For every (city, seed): external cost per tour from mfgcc.extern (base rates; sensitivity variants eu / hi / nocong
for the mean-field rules).  Mean field (Wardrop): no charge (none); congestion-only Pigou (cong, the paper's
optimum); extended optimum implemented by a per-tour distance charge E plus kappa Q per delivery (ext_tour);
per-delivery charge kappa Q' + e (e = external cost per delivery of the tours at the extended optimum, ext_ebar);
the per-delivery charge that matches the extended-optimum aggregate (ext_match).  Finite N = 6k, k in
{1, 4, 32, 256}: none, Pigou minus market power for congestion only (pm_cong), with the distance charge
(pm_ext_tour) and per delivery only, matching the extended aggregate (pm_ext_match).  Exposure: vehicle-km per
resident in every zone touched by the delivery traffic.  Output mfg/results/extern.csv; resumable per (city, seed).
  PYTHONPATH=mfg/src python3 mfg/experiments/run_extern.py
"""
from __future__ import annotations

import csv
import os
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from mfgcc import city as C
from mfgcc import extern as X
from mfgcc.leader import social_optimum, welfare
from mfgcc.qp import solve
from mfgcc.stake import decile_ratio, exposure_grid, pm_charge, spearman, wgini

OUT = Path(__file__).resolve().parents[1] / "results" / "extern.csv"
KREP = [1, 4, 32, 256]
SEEDS = range(5)
FIELDS = ["city", "seed", "regime", "N", "rule", "variant", "SW", "SW_ext", "SW_ext_opt", "loss_pct", "E", "air",
          "clim", "noise", "cong", "vkm", "vkm_in", "Q_total", "R_deliv", "R_tour", "kQ_per_del", "u_per_del",
          "ebar_per_del", "E_per_del", "kappa_cost", "fee", "resid", "exp_vkm_m", "exp_gini", "exp_d10d1",
          "exp_air_usd_yr", "exp_through_share", "exp_corr_cong", "n_touched", "veh_min_res"]


def done():
    if not OUT.exists():
        return set()
    with open(OUT) as fh:
        return {(r["city"], r["seed"]) for r in csv.DictReader(fh)}


def wardrop_match(bl, m, target, u0, rounds=40, theta=0.8):
    u = u0.copy()
    for _ in range(rounds):
        s = solve(bl, m, own=False, u=u)
        u = u + theta * m * (s.Q - target)
    s = solve(bl, m, own=False, u=u)
    return u, s, float(np.sqrt(np.sum(m * (s.Q - target) ** 2) / np.sum(m * target ** 2)))


class Exposure:
    """vkm per resident in the zones touched by the no-charge traffic (fixed reference set per instance)."""

    def __init__(self, g, ext, sol0):
        self.g, self.ext, self.mu = g, ext, X.real_scale(g)
        x0 = X.zone_vkm(g, sol0, ext, self.mu)
        pop = g.meta["pop_z"]
        self.t = (x0 > 0) & (pop > 0)
        self.cust = np.zeros(len(pop), bool)
        self.cust[np.unique(g.coords[:, 0])] = True

    def __call__(self, sol, air_rate):
        g, t = self.g, self.t
        x = X.zone_vkm(g, sol, self.ext, self.mu)
        pop = g.meta["pop_z"]
        e = x[t] / pop[t]
        zones, popc, _, E, _ = exposure_grid(g, sol.Q)
        vkm_c = x[zones] / popc
        return dict(exp_vkm_m=1000.0 * x[t].sum() / pop[t].sum(), exp_gini=wgini(e, pop[t]),
                    exp_d10d1=decile_ratio(e, pop[t]), exp_air_usd_yr=365.0 * air_rate * x[t].sum() / pop[t].sum(),
                    exp_through_share=float(x[t & ~self.cust].sum() / max(x[t].sum(), 1e-12)),
                    exp_corr_cong=spearman(E.sum(1), vkm_c), n_touched=int(t.sum()),
                    veh_min_res=float(60.0 * np.sum(popc * E.sum(1)) / popc.sum()))


def row_for(g, bl, sol, ext, u, tour_charge, opt_ext, variant, regime, N, rule, rt, expo=None, resid=0.0):
    m, kap = g.m, g.kappa
    ec = X.external_cost(sol, ext)
    sw = welfare(bl, sol, m, kap)
    Qt = float(sol.Q.sum())
    eb = X.per_delivery_external(bl, sol, ext)
    r = dict(city=g.city, seed=g.seed, regime=regime, N=N, rule=rule, variant=variant, SW=sw, SW_ext=sw - ec["E"],
             SW_ext_opt=opt_ext, loss_pct=100.0 * (opt_ext - (sw - ec["E"])) / opt_ext, Q_total=Qt,
             R_deliv=float(u @ sol.Q), R_tour=ec["E"] if tour_charge else 0.0, kQ_per_del=float(kap @ sol.Q ** 2) / Qt,
             u_per_del=float(u @ sol.Q) / Qt, ebar_per_del=float(eb @ sol.Q) / Qt, E_per_del=ec["E"] / Qt,
             kappa_cost=float(kap @ sol.Q ** 2), fee=g.meta["fee"], resid=resid)
    r.update({k: ec[k] for k in ("E", "air", "clim", "noise", "cong", "vkm", "vkm_in")})
    if expo is not None:
        r.update(expo(sol, rt["air"]))
    return r


def job(args):
    c, seed = args
    if (c, str(seed)) in done():
        return []
    g = C.build(c, seed)
    m, kap = g.m, g.kappa
    geo = X.zone_paths(c)
    rows = []
    bl = g.blocks(1)
    for variant in ("base", "eu", "hi", "nocong"):
        ext = X.tour_externalities(g, variant, geo)
        rt = X.rates(g, variant)
        ble = X.ext_blocks(g, 1, ext, True)
        so_e = social_optimum(ble, m, kap)
        opt = welfare(ble, so_e, m, kap)
        s0 = solve(bl, m, own=False)
        expo = Exposure(g, ext, s0) if variant == "base" else None
        so = social_optimum(bl, m, kap)
        ebar = X.per_delivery_external(ble, so_e, ext)
        u_eb = kap * so_e.Q + ebar
        s_eb = solve(bl, m, own=False, u=u_eb)
        u_mt, s_mt, res = wardrop_match(bl, m, so_e.Q, u_eb)
        for rule, sol, u, tc, rs in [("none", s0, np.zeros(g.d), False, 0.0), ("cong", so, kap * so.Q, False, 0.0),
                                     ("ext_tour", so_e, kap * so_e.Q, True, 0.0), ("ext_ebar", s_eb, u_eb, False, 0.0),
                                     ("ext_match", s_mt, u_mt, False, res)]:
            rows.append(row_for(g, bl, sol, ext, u, tc, opt, variant, "W", "inf", rule, rt, expo, rs))
        if variant != "base":
            continue
        for k in KREP:
            blk = g.blocks(k)
            blke = X.ext_blocks(g, k, ext, True)
            sok = social_optimum(blk, m, kap)
            soke = social_optimum(blke, m, kap)
            n0 = solve(blk, m, own=True)
            u1, s1, r1 = pm_charge(blk, m, kap, sok)
            u2, s2, r2 = pm_charge(blke, m, kap, soke)
            u3, s3, r3 = pm_charge(blk, m, kap, soke)
            N = 6 * k
            for rule, sol, u, tc, rs in [("none", n0, np.zeros(g.d), False, 0.0), ("pm_cong", s1, u1, False, r1),
                                         ("pm_ext_tour", s2, u2, True, r2), ("pm_ext_match", s3, u3, False, r3)]:
                rows.append(row_for(g, blk, sol, ext, u, tc, opt, variant, "N", N, rule, rt, expo, rs))
        print("extern", c, seed, flush=True)
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
