"""Numerical check of the contraction theorems on tiny games with all plans enumerated (convexified game).

For random charge pairs (u1, u2): the Lipschitz bound ||Q(u1)-Q(u2)||_m <= ||u1-u2||_{m^-1} (Theorem 1), the plain map
ratio ||T(u1)-T(u2)||_{k^-1} / ||u1-u2||_{k^-1} <= rho (Theorem 2a) and the damped map ratio <= rho/(2+rho) (Theorem 2b,
measured on the iteration from random starts against the fixed point).  Output: results/arp_rates.csv.
"""
import numpy as np

from common import RES, write_csv, zb
from ccu import arp, dip


def enum_plans(g):
    g.set_charges()
    _, _, plans = zb.enumerate_game(g)
    return [[p for _, p in pl] for pl in plans]


def main():
    rows = []
    rng = np.random.default_rng(0)
    for seed in range(12):
        for gcx in (1.0, 20.0, 60.0, 200.0):
            g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=seed)
            g.gc = g.gc * gcx
            plans = enum_plans(g)
            kappa, m, _ = dip.curvatures(g)
            act = dip.active_zones(g)
            rho = arp.contraction_ratio(g)
            D = dip.lots(g)
            has = D > 0
            dbar = np.where(has.any(0), D.sum(0) / np.maximum(has.sum(0), 1), 0.0)
            T = lambda u: np.where(act, kappa * arp.convexified_response(g, plans, u)[0] - 0.5 * m * dbar, 0.0)
            lip, ratio = [], []
            for _ in range(6):
                u1 = np.where(act, rng.normal(0, 3, g.Z), 0.0)
                u2 = np.where(act, rng.normal(0, 3, g.Z), 0.0)
                Q1, _ = arp.convexified_response(g, plans, u1)
                Q2, _ = arp.convexified_response(g, plans, u2)
                lip.append(np.sqrt(np.sum(m[act] * (Q1 - Q2)[act] ** 2)) / max(np.sqrt(np.sum((u1 - u2)[act] ** 2 / m[act])), 1e-12))
                ratio.append(arp.knorm(g, kappa * (Q1 - Q2)) / max(arp.knorm(g, u1 - u2), 1e-12))
            # fixed point by the plain iteration, then per-step ratios of plain and damped from random starts
            u = np.zeros(g.Z)
            for _ in range(60):
                un = T(u)
                if arp.knorm(g, un - u) <= 1e-9 * max(arp.knorm(g, un), 1e-12):
                    u = un
                    break
                u = un
            ustar = u
            th = 2.0 / (2.0 + rho)
            rp, rd = [], []
            for _ in range(3):
                u0 = np.where(act, ustar + rng.normal(0, 3, g.Z), 0.0)
                up, ud = u0.copy(), u0.copy()
                for _ in range(4):
                    e0 = arp.knorm(g, up - ustar)
                    up = T(up)
                    if e0 > 1e-7:
                        rp.append(arp.knorm(g, up - ustar) / e0)
                    e0 = arp.knorm(g, ud - ustar)
                    ud = (1 - th) * ud + th * T(ud)
                    if e0 > 1e-7:
                        rd.append(arp.knorm(g, ud - ustar) / e0)
            rows.append(dict(seed=seed, gcx=gcx, rho=rho, rho_damped=rho / (2 + rho), lipschitz_max=max(lip),
                             T_ratio_max=max(ratio), plain_step_ratio_max=max(rp) if rp else np.nan,
                             damped_step_ratio_max=max(rd) if rd else np.nan,
                             ok_lip=max(lip) <= 1 + 1e-3, ok_T=max(ratio) <= rho + 1e-3,
                             ok_plain=(max(rp) if rp else 0) <= rho + 1e-3, ok_damped=(max(rd) if rd else 0) <= rho / (2 + rho) + 1e-3))
            print(rows[-1], flush=True)
    write_csv(RES / "arp_rates.csv", rows)
    import pandas as pd
    d = pd.DataFrame(rows)
    print(d[["ok_lip", "ok_T", "ok_plain", "ok_damped"]].all())
    print(d[["rho", "T_ratio_max", "plain_step_ratio_max", "rho_damped", "damped_step_ratio_max"]].describe())


if __name__ == "__main__":
    main()
