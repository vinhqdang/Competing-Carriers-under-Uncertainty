"""Verification before scale (tasks 2a, 2c) and theory-to-experiment checks (E6).

  python experiments/run_verification.py tiny            -> results/verify_tiny.csv   (exhaustive enumeration, 2a)
  python experiments/run_verification.py city CITY       -> results/verify_methods_<city>.csv (2c),
                                                            results/E6_<city>.csv (clearing error, brackets)
(2b, exact pure NE w.r.t. an independent oracle, is the column max_regret of every E1/E2/E4 row.)
"""
import sys
import time

import numpy as np

from common import RES, write_csv, zb, zmc


def tiny():
    rows = []
    cfgs = [(2, 5, 3), (3, 6, 3), (3, 6, 4), (2, 6, 4)]
    for (N, Z, nc) in cfgs:
        for seed in range(10):
            g = zb.make_tiny_game(N=N, Z=Z, n_cust=nc, seed=1000 * nc + 100 * N + seed)
            Phi, ne, plans = zb.enumerate_game(g)
            gmin, nemin, nemax = float(Phi.min()), float(Phi[ne].min()), float(Phi[ne].max())

            def locate(prof):
                idx = []
                for i, p in enumerate(prof):
                    idx.append(next(k for k, (_, pl) in enumerate(plans[i]) if np.allclose(pl.a, p.a)))
                return tuple(idx)

            row = dict(N=N, Z=Z, n_cust=nc, seed=seed, profiles=int(Phi.size), n_ne=int(ne.sum()), global_min=gmin,
                       best_ne=nemin, worst_ne=nemax)
            for name, fn in [("ZMC6", lambda: zmc.run_zmc(g, rounds=6)), ("BR", lambda: zmc.run_br(g)),
                             ("FW6", lambda: zmc.run_fw(g, iters=6)), ("CG", lambda: zmc.run_cg(g, iters=60))]:
                r = fn()
                prof = r["profile"]
                v = g.potential(prof)
                idx = locate(prof)
                row[f"{name}_calls"] = r["calls"]
                row[f"{name}_phi"] = v
                row[f"{name}_is_ne_enum"] = bool(ne[idx])
                row[f"{name}_regret_fresh"] = float(g.regrets(prof, fresh=True).max())
                row[f"{name}_hits_global"] = bool(abs(v - gmin) < 1e-7)
                row[f"{name}_hits_best_ne"] = bool(abs(v - nemin) < 1e-7)
            rows.append(row)
            print(row["N"], row["Z"], row["n_cust"], seed, {k: v for k, v in row.items() if k.startswith("ZMC")}, flush=True)
    write_csv(RES / "verify_tiny.csv", rows)


def city(c, ncust=22):
    g = zb.build_city_game(c, n_cust=ncust, seed=0)
    rows = []
    t0 = time.perf_counter()
    zm = zmc.run_zmc(g, rounds=8)
    t_zmc = time.perf_counter() - t0
    t0 = time.perf_counter()
    cg = zmc.run_cg(g, iters=40)
    t_cg = time.perf_counter() - t0
    phibar = zmc.relaxed_value(g, cg["pools"], cg["weights"])  # convexified optimum (approx., restricted master after CG)
    res = {"ZMC8": (zm, t_zmc), "CG(conv)": (cg, t_cg)}
    for name, fn in [("BR", lambda: zmc.run_br(g)), ("FW8", lambda: zmc.run_fw(g, iters=8)),
                     ("CG8", lambda: zmc.run_cg(g, iters=8))]:
        t0 = time.perf_counter()
        res[name] = (fn(), time.perf_counter() - t0)
    best_dual = max([t["G"] for t in zm["trace"]])
    for name, (r, tm) in res.items():
        prof = r["profile"]
        phi = g.potential(prof)
        reg = g.regrets(prof, fresh=False)
        rows.append(dict(city=c, method=name, N=g.N, Z=g.Z, d_eff=g.meta["d_eff"], calls=r["calls"], phi=phi,
                         phibar_cg=phibar, gap=phi - phibar, gap_rel=(phi - phibar) / abs(phibar),
                         best_dual_zmc=best_dual, max_regret=float(reg.max()), converged=bool(r["converged"]), time_s=tm,
                         welfare=g.evaluate(prof)["welfare"]))
        print(c, name, r["calls"], round(phi, 2), round((phi - phibar) / abs(phibar), 5), flush=True)
    write_csv(RES / f"verify_methods_{c}.csv", rows)
    # ---------------- E6 checks
    e6 = []
    for t in zm["trace"]:
        e6.append(dict(city=c, kind="zmc_round", round=t["round"], calls=t["calls"], G=t["G"], G_lb=t["G_lb"], phi=t["phi"],
                       err2=t["err2"], identity_resid=t["phi"] - t["G"] - 0.5 * t["err2"], width_max=t["width_max"],
                       width_med=t["width_med"], n_inverted=t["n_inverted"], n_act=t["n_act"],
                       thm2_bound_holds=bool(t["phi"] - phibar <= 0.5 * t["err2"] + 1e-6)))
    h = []
    best, pools, tr = zmc.zmc(g, rounds=14, mode="bisect", hist=h)
    Amax = sum(g.full_a(i) for i in range(g.N))
    act = Amax > 0
    scale = (g.M * Amax)[act]
    ref = h[-1][2][act]
    for t in range(1, 13):
        lam = h[t - 1][2][act]
        err = np.abs(lam - ref) / scale
        bound = 2.0 ** (-np.ceil(t / 2))
        e6.append(dict(city=c, kind="bisect_bracket", round=t, err_max=float(err.max()), err_med=float(np.median(err)),
                       bound=bound, frac_within=float(np.mean(err <= bound + 1e-12)), n_inverted=tr[t - 1]["n_inverted"],
                       width_max=tr[t - 1]["width_max"], n_act=int(act.sum())))
    write_csv(RES / f"E6_{c}.csv", e6)


if __name__ == "__main__":
    if sys.argv[1] == "tiny":
        tiny()
    else:
        city(sys.argv[2])
