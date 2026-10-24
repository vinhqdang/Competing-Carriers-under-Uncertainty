"""E2 (the city leader's charges) and E3 (price of anarchy / stability) for one city.

Usage:  python experiments/run_leader.py CITY [--ncust 22] [--seed 0]
Seed s changes depots, customer zones, sector clustering and the observed days (build_city_game(seed=s)) and the random
starts of E3.  Resumable: the grid file is rewritten atomically after every point and finished points are skipped; the
best/cert/E3 files are written atomically once; a finished city/seed is skipped.  Seed 0 files keep the historical names,
seed s > 0 files carry the suffix _s<seed>.
Instruments: per-zone congestion charge  t_z = theta * gc_z * X_z^NE  on vehicle-hours (theta times the marginal
congestion externality at the unpriced equilibrium) and a uniform per-delivery charge/subsidy s = sfrac * fee.
The leader's search is a grid (theta x sfrac) of warm-started ZMC equilibria.
Writes results/E2_<city>.csv (every grid point), results/E2best_<city>.csv (best point per configuration and
objective), results/E3_<city>.csv (social optimum, equilibria found, priced equilibrium).
"""
import argparse
import time

import numpy as np

from common import RES, read_rows, rpath, scalars, solve_ne, write_csv, zb, zmc

THETAS = [0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
SFRACS = [-0.6, -0.4, -0.2, -0.1, 0.0, 0.1, 0.2, 0.4, 0.6]


N_E3 = 10  # SO_main, SO_broad, NE_zmc, 5 more NE starts, 2 priced equilibria


def config(theta, sfrac):
    if theta == 0 and sfrac == 0:
        return "none"
    if sfrac == 0:
        return "congestion_only"
    if theta == 0:
        return "delivery_only"
    return "both"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("city")
    ap.add_argument("--ncust", type=int, default=22)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    p_e2, p_best, p_cert, p_e3 = (rpath(k, a.city, a.seed) for k in ("E2", "E2best", "E2cert", "E3"))
    old = read_rows(p_e2)
    ngrid = len(THETAS) * len(SFRACS)
    if len(old) == ngrid and p_best.exists() and p_cert.exists() and len(read_rows(p_e3)) == N_E3:
        print(a.city, a.seed, "E2/E3 already complete, skipping", flush=True)
        return
    g = zb.build_city_game(a.city, n_cust=a.ncust, seed=a.seed)
    fee = g.meta["params"]["delivery_fee_usd"]
    Z = g.Z
    t0 = time.perf_counter()
    base = solve_ne(g, rounds=8, certify="oracle")
    Xne = base["eval"]["X_z"]
    ext = g.gc * Xne  # marginal congestion externality (USD per vehicle-hour) at the unpriced equilibrium
    rows = old
    done = {(float(r["theta"]), float(r["sfrac"])) for r in rows}
    lam0_base = base["result"]["lam"]
    lam = lam0_base
    order = []
    for k, th in enumerate(THETAS):
        ss = SFRACS if k % 2 == 0 else SFRACS[::-1]
        order += [(th, s) for s in ss]
    results = {}
    def point(th, sf):
        """equilibrium at a grid point (re-solved from the base warm start when the point was finished before a restart)"""
        if (th, sf) not in results:
            toll = np.zeros(2 * Z)
            toll[:Z] = sf * fee
            toll[Z:] = th * ext
            g.set_charges(toll=toll)
            results[(th, sf)] = base if (th == 0 and sf == 0) else solve_ne(g, rounds=6, lam0=lam0_base, certify="oracle")
        return results[(th, sf)]

    for th, sf in order:
        if (th, sf) in done:
            continue
        toll = np.zeros(2 * Z)
        toll[:Z] = sf * fee
        toll[Z:] = th * ext
        g.set_charges(toll=toll)
        if th == 0 and sf == 0:
            o = base
        else:
            o = solve_ne(g, rounds=6, lam0=lam, certify="oracle")
        lam = o["result"]["lam"]
        results[(th, sf)] = o
        r = dict(city=a.city, seed=a.seed, config=config(th, sf), theta=th, sfrac=sf, s_usd=sf * fee, N=g.N, Z=Z, **o["row"])
        r["revenue"] = r.pop("charges")
        rows.append(r)
        print(a.city, a.seed, th, sf, round(r["social_cost"], 1), round(r["social_cost_broad"], 1), r["calls"], round(time.perf_counter() - t0), flush=True)
        write_csv(p_e2, rows)
    g.set_charges()
    # best point per configuration and objective (the leader may always choose "none")
    best = []
    for obj in ("social_cost", "social_cost_broad"):
        for cfg in ("none", "congestion_only", "delivery_only", "both"):
            cand = [r for r in rows if r["config"] in (cfg, "none")]
            b = min(cand, key=lambda r: r[obj])
            best.append(dict(city=a.city, seed=a.seed, objective=obj, config=cfg, **{k: v for k, v in b.items() if k not in ("city", "config", "seed")},
                             chosen_config=b["config"]))
    write_csv(p_best, best)
    # fresh independent certification of the best "both" point (main objective)
    bb = [b for b in best if b["objective"] == "social_cost" and b["config"] == "both"][0]
    if not p_cert.exists():
        toll = np.zeros(2 * Z)
        toll[:Z] = bb["sfrac"] * fee
        toll[Z:] = bb["theta"] * ext
        g.set_charges(toll=toll)
        oc = solve_ne(g, rounds=6, lam0=lam0_base, certify="fresh")
        cert = dict(city=a.city, seed=a.seed, theta=bb["theta"], sfrac=bb["sfrac"], regret_fresh=oc["row"]["max_regret"],
                    regret_lp=oc["row"]["max_regret_lp"], social_cost=oc["row"]["social_cost"],
                    **{k: v for k, v in oc["row"].items() if k.startswith("bp_") or k == "oracle"})
        write_csv(p_cert, [cert])
    g.set_charges()

    # ---------------------------------------------------------------- E3
    e3 = []

    last = dict(g._st)

    def stamp(r, prefix="bp_"):
        """exact-oracle calls (solved, optimal, unproven after the retry) since the previous stamp"""
        if g.bp_time:
            st = g._st
            n = st["calls"] - last["calls"]
            r[prefix + "calls"], r[prefix + "optimal"] = n, st["optimal"] - last["optimal"]
            r[prefix + "unproven"] = st["timeouts"] - last["timeouts"]
            r[prefix + "retried"] = st["retried"] - last["retried"]
            r[prefix + "max_gap"] = st["max_gap"]  # running maximum over this city/seed run
            r["oracle"] = "exact"
            last.update(st)

    def fresh_regret(r, prof):
        """independent exact verification of a profile: fresh elementary pool, no shared columns"""
        if g.bp_time:
            r["max_regret_fresh"] = float(g.regrets(prof, count=False, fresh=True).max())
            stamp(r, "bpfresh_")

    def add(kind, prof, extra=None, game=None):
        ev = g.evaluate(prof)
        r = dict(city=a.city, seed=a.seed, kind=kind, **scalars(ev))
        r.update(extra or {})
        e3.append(r)
        stamp(r)
        return r

    for broad in (False, True):
        so = g.so_variant(broad)
        cg = zmc.run_cg(so, iters=40)
        relaxed = zmc.relaxed_value(so, cg["pools"], cg["weights"])
        add("SO_broad" if broad else "SO_main", cg["profile"],
            dict(phi_pure=so.potential(cg["profile"]), phi_relaxed=relaxed, calls=cg["calls"], converged=cg["converged"],
                 cg_iters=len(cg["hist"]), cg_last_gap=cg["hist"][-1][1]))
    # equilibria of the unpriced game: ZMC, BR from the empty profile, from full service, from random prices
    r_ne = add("NE_zmc", base["profile"], dict(phi_pure=base["row"]["phi"], calls=base["row"]["calls"], max_regret=base["row"]["max_regret"]))
    fresh_regret(r_ne, base["profile"])
    rng = np.random.default_rng(a.seed + 7)
    Amax = sum(g.full_a(i) for i in range(g.N))
    starts = {"NE_br_empty": None,
              "NE_full_service": [g.oracle(i, -1e3 * np.ones(g.d), rho=1.0, count=False) for i in range(g.N)]}
    for k in range(3):
        u = rng.uniform(0.0, 1.0, g.d)
        starts[f"NE_random{k}"] = [g.oracle(i, u * g.M * Amax, rho=1.0, count=False) for i in range(g.N)]
    seen = {tuple(p.key() for p in base["profile"])}
    for name, init in starts.items():
        r = zmc.run_br(g, init=init)
        reg = g.regrets(r["profile"], count=False)
        key = tuple(p.key() for p in r["profile"])
        add(name, r["profile"], dict(phi_pure=g.potential(r["profile"]), calls=r["calls"], converged=r["converged"],
                                     max_regret=float(reg.max()), distinct=key not in seen))
        seen.add(key)
    # priced equilibria at the leader's best points (main and broad objective, both instruments)
    for obj in ("social_cost", "social_cost_broad"):
        b = [x for x in best if x["objective"] == obj and x["config"] == "both"][0]
        toll = np.zeros(2 * Z)
        toll[:Z] = b["sfrac"] * fee
        toll[Z:] = b["theta"] * ext
        g.set_charges(toll=toll)
        o = point(b["theta"], b["sfrac"])
        r_pr = add("NE_priced_main" if obj == "social_cost" else "NE_priced_broad", o["profile"],
                   dict(theta=b["theta"], sfrac=b["sfrac"], phi_pure=o["row"]["phi"], max_regret=o["row"]["max_regret"]))
        fresh_regret(r_pr, o["profile"])
    g.set_charges()
    write_csv(p_e3, e3)  # E3 is written once, atomically (it takes minutes, not hours)
    print(a.city, a.seed, "done", round(time.perf_counter() - t0), flush=True)


if __name__ == "__main__":
    main()
