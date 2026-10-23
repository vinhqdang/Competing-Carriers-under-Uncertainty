"""E2 (the city leader's charges) and E3 (price of anarchy / stability) for one city.

Usage:  python experiments/run_leader.py CITY [--ncust 22] [--seed 0]
Instruments: per-zone congestion charge  t_z = theta * gc_z * X_z^NE  on vehicle-hours (theta times the marginal
congestion externality at the unpriced equilibrium) and a uniform per-delivery charge/subsidy s = sfrac * fee.
The leader's search is a grid (theta x sfrac) of warm-started ZMC equilibria.
Writes results/E2_<city>.csv (every grid point), results/E2best_<city>.csv (best point per configuration and
objective), results/E3_<city>.csv (social optimum, equilibria found, priced equilibrium).
"""
import argparse
import time

import numpy as np

from common import RES, scalars, solve_ne, write_csv, zb, zmc

THETAS = [0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
SFRACS = [-0.6, -0.4, -0.2, -0.1, 0.0, 0.1, 0.2, 0.4, 0.6]


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
    g = zb.build_city_game(a.city, n_cust=a.ncust, seed=a.seed)
    fee = g.meta["params"]["delivery_fee_usd"]
    Z = g.Z
    t0 = time.perf_counter()
    base = solve_ne(g, rounds=8, certify="oracle")
    Xne = base["eval"]["X_z"]
    ext = g.gc * Xne  # marginal congestion externality (USD per vehicle-hour) at the unpriced equilibrium
    rows = []
    lam = base["result"]["lam"]
    order = []
    for k, th in enumerate(THETAS):
        ss = SFRACS if k % 2 == 0 else SFRACS[::-1]
        order += [(th, s) for s in ss]
    results = {}
    for th, sf in order:
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
        r = dict(city=a.city, config=config(th, sf), theta=th, sfrac=sf, s_usd=sf * fee, N=g.N, Z=Z, **o["row"])
        r["revenue"] = r.pop("charges")
        rows.append(r)
        print(a.city, th, sf, round(r["social_cost"], 1), round(r["social_cost_broad"], 1), r["calls"], round(time.perf_counter() - t0), flush=True)
        write_csv(RES / f"E2_{a.city}.csv", rows)
    g.set_charges()
    # best point per configuration and objective (the leader may always choose "none")
    best = []
    for obj in ("social_cost", "social_cost_broad"):
        for cfg in ("none", "congestion_only", "delivery_only", "both"):
            cand = [r for r in rows if r["config"] in (cfg, "none")]
            b = min(cand, key=lambda r: r[obj])
            best.append(dict(city=a.city, objective=obj, config=cfg, **{k: v for k, v in b.items() if k not in ("city", "config")},
                             chosen_config=b["config"]))
    write_csv(RES / f"E2best_{a.city}.csv", best)
    # fresh independent certification of the best "both" point (main objective)
    bb = [b for b in best if b["objective"] == "social_cost" and b["config"] == "both"][0]
    toll = np.zeros(2 * Z)
    toll[:Z] = bb["sfrac"] * fee
    toll[Z:] = bb["theta"] * ext
    g.set_charges(toll=toll)
    oc = solve_ne(g, rounds=6, lam0=lam, certify="fresh")
    cert = dict(city=a.city, theta=bb["theta"], sfrac=bb["sfrac"], regret_fresh=oc["row"]["max_regret"],
                regret_lp=oc["row"]["max_regret_lp"], social_cost=oc["row"]["social_cost"])
    write_csv(RES / f"E2cert_{a.city}.csv", [cert])
    g.set_charges()

    # ---------------------------------------------------------------- E3
    e3 = []

    def add(kind, prof, extra=None, game=None):
        ev = g.evaluate(prof)
        r = dict(city=a.city, kind=kind, **scalars(ev))
        r.update(extra or {})
        e3.append(r)
        write_csv(RES / f"E3_{a.city}.csv", e3)
        return r

    for broad in (False, True):
        so = g.so_variant(broad)
        cg = zmc.run_cg(so, iters=40)
        relaxed = zmc.relaxed_value(so, cg["pools"], cg["weights"])
        add("SO_broad" if broad else "SO_main", cg["profile"],
            dict(phi_pure=so.potential(cg["profile"]), phi_relaxed=relaxed, calls=cg["calls"], converged=cg["converged"],
                 cg_iters=len(cg["hist"]), cg_last_gap=cg["hist"][-1][1]))
    # equilibria of the unpriced game: ZMC, BR from the empty profile, from full service, from random prices
    add("NE_zmc", base["profile"], dict(phi_pure=base["row"]["phi"], calls=base["row"]["calls"], max_regret=base["row"]["max_regret"]))
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
        o = results[(b["theta"], b["sfrac"])]
        add("NE_priced_main" if obj == "social_cost" else "NE_priced_broad", o["profile"],
            dict(theta=b["theta"], sfrac=b["sfrac"], phi_pure=o["row"]["phi"], max_regret=o["row"]["max_regret"]))
    g.set_charges()
    print(a.city, "done", round(time.perf_counter() - t0), flush=True)


if __name__ == "__main__":
    main()
