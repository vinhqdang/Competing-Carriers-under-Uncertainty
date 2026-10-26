"""Ten-seed extension of the exact-oracle study: seeds 3..9 for the nine cities (seeds 0..2 are the existing runs).

Usage:  python experiments/run_seeds10.py CITY SEED PHASE          PHASE = core | arp | grid
Every phase is resumable (stages are stored atomically in results/seeds10_parts/<phase>_<city>_s<seed>.json and skipped on restart).
All runs use the exact oracle (branch-and-price, CCU_BP_TIME = 20 s per call, retry 120 s for best responses, as in the E1-E4 re-run).

  core  E1  unpriced equilibrium (ZMC, certified against an independent fresh-pool exact oracle)
        DIP social optimum (column generation + rounding = the E3 'SO_main' solve, then the multi-start polish), the dual
            implementation prices, priced equilibrium, regrets (pooled and fresh); SO_main of E3 is the first target of DIP
        NE  the five further equilibria of E3 (best response from the empty profile, from full service, from 3 random prices)
            for PoS and the worst-equilibrium PoA
  arp   flat ARP (plain, successive averages if it cycles), marginal tariff + best responses, marginal tariff + solver
        (run_arp.run with the stages, the base equilibrium is taken from core)
  grid  the leader's two-parameter grid (theta x s/fee), exact oracle at every evaluated point.
        New Delhi, Buenos Aires, London: the full 63-point grid.  Other cities: a fixed coarse exact set of 14 points:
        the unpriced equilibrium, 4 per-delivery points s/fee in {-.6,-.4,-.2,-.1} (theta = 0), 5 congestion points
        theta in {1,2,4,8,16} (s = 0), and the 4 'both' points nearest to the projection of DIP's zone charges on the grid's
        family.  Gains from the coarse set are LOWER BOUNDS of the 63-point grid gains.
        The best 'both' point is certified with the fresh-pool exact oracle (the priced equilibrium of E3).
"""
import argparse
import fcntl
import json
import os
import sys
import time

os.environ.setdefault("CCU_BP_TIME", "20")
os.environ.setdefault("CCU_BP_RETRY", "120")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("NUMBA_NUM_THREADS", "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import RES, scalars, solve_ne, write_csv, zb, zmc  # noqa: E402
from ccu import dip  # noqa: E402

PARTS = RES / "seeds10_parts"
PARTS.mkdir(exist_ok=True)
NCUST = 22
THETAS = [0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]
SFRACS = [-0.6, -0.4, -0.2, -0.1, 0.0, 0.1, 0.2, 0.4, 0.6]
FULL_GRID_CITIES = ("NewDelhi", "BuenosAires", "London")
COARSE_DELIVERY = [-0.6, -0.4, -0.2, -0.1]
COARSE_CONG = [1.0, 2.0, 4.0, 8.0, 16.0]


def jdump(path, obj):
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(obj, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else (bool(x) if isinstance(x, np.bool_) else float(x))))
    os.replace(tmp, path)


def jload(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def routes_of(prof):
    return [[list(map(int, r)) for r in p.routes] for p in prof]


def plans_from(g, routes):
    return [g.plan_from_routes(i, [tuple(r) for r in rs]) for i, rs in enumerate(routes)]


def stamp(g, st0):
    st = g._st
    return dict(bp_calls=st["calls"] - st0["calls"], bp_optimal=st["optimal"] - st0["optimal"], bp_unproven=st["timeouts"] - st0["timeouts"],
                bp_retried=st["retried"] - st0["retried"], bp_max_gap=st["max_gap"])


def config(theta, sfrac):
    if theta == 0 and sfrac == 0:
        return "none"
    if sfrac == 0:
        return "congestion_only"
    if theta == 0:
        return "delivery_only"
    return "both"


# ------------------------------------------------------------------------------------------------ core
def core(city, seed):
    part = PARTS / f"core_{city}_s{seed}.json"
    P = jload(part)
    if P.get("done"):
        print(city, seed, "core done", flush=True)
        return
    t_all = time.perf_counter()
    g = zb.build_city_game(city, n_cust=NCUST, seed=seed)
    Z = g.Z
    # ---- E1
    if "e1" not in P:
        st0 = dict(g._st)
        o = solve_ne(g, rounds=8, certify="fresh")
        row = dict(city=city, seed=seed, N=g.N, Z=Z, d_eff=g.meta["d_eff"], overlap=g.meta["overlap"], L=g.meta["L"], **o["row"])
        P["e1"] = dict(row=row, lam=o["result"]["lam"], routes=routes_of(o["profile"]), X=o["eval"]["X_z"], fee=g.meta["params"]["delivery_fee_usd"])
        jdump(part, P)
        print(city, seed, "E1", {k: round(v, 3) for k, v in o["row"].items() if isinstance(v, float)}, flush=True)
    base = plans_from(g, P["e1"]["routes"])
    # ---- DIP (its social target is the E3 SO_main solve)
    if "dip" not in P:
        g.set_charges()
        st0 = dict(g._st)
        t0 = time.perf_counter()
        log = []
        o = dip.dip(g, so_iters=40, log=log)
        stp = stamp(g, st0)
        _, _, toll_ = dip.instruments(g, o["u"])
        g.set_charges(toll=toll_)
        ev = g.evaluate(o["profile"])
        g.set_charges()
        first_target_sc = o["first"]["sc_target"]
        so_row = dict(scalars(g.evaluate(o["first"]["target"])))
        P["dip"] = dict(u=o["u"], u_tan=o["u_tan"], s=o["s"], t=o["t"], status=o["status"], rounds=o["rounds"], n_cuts=o["n_cuts"],
                        converged=o["converged"], sc=o["sc"], sc_target=o["sc_target"], first_sc=o["first"]["sc"],
                        first_sc_target=first_target_sc, first_status=o["first"]["status"], first_calls=o["first"]["calls"],
                        calls=o["calls"], calls_so=o["calls_so"], calls_implement=o["calls_implement"], calls_restarts=o["calls_restarts"],
                        so_relaxed=o["so_relaxed"], so_pure=o["so_pure"], welfare=ev["welfare"], served_share=ev["served_share"],
                        revenue=ev["charges"], profit=ev["profit_total"], time_s=time.perf_counter() - t0,
                        loss_bound=o["loss_bound"], routes=routes_of(o["profile"]), target_routes=routes_of(o["target"]),
                        so_main_row=so_row, **stp)
        g.set_charges()
        jdump(part, P)
        print(city, seed, "DIP", o["status"], o["rounds"], "sc", round(o["sc"], 2), "target", round(o["sc_target"], 2),
              "calls", o["calls"], round(time.perf_counter() - t0), flush=True)
    D = P["dip"]
    u = np.array(D["u"])
    # ---- verification of the priced profile (not counted as method calls)
    if "verify" not in P:
        _, _, toll = dip.instruments(g, u)
        g.set_charges(toll=toll)
        prof = plans_from(g, D["routes"])  # plan costs embed the charges in force when they are built
        st0 = dict(g._st)
        t0 = time.perf_counter()
        reg = g.regrets(prof, count=False)
        regf = g.regrets(prof, count=False, fresh=True)
        P["verify"] = dict(max_regret=float(reg.max()), max_regret_fresh=float(regf.max()), max_regret_fresh_lb=float(np.nanmax(g._last_regret_lp)),
                           time_s=time.perf_counter() - t0, **stamp(g, st0))
        g.set_charges()
        jdump(part, P)
        print(city, seed, "verify", P["verify"]["max_regret"], P["verify"]["max_regret_fresh"], flush=True)
    # ---- further equilibria (E3)
    if "ne" not in P:
        g.set_charges()
        st0 = dict(g._st)
        t0 = time.perf_counter()
        rows = []

        def add(kind, prof, extra=None):
            ev = g.evaluate(prof)
            rows.append(dict(city=city, seed=seed, kind=kind, **scalars(ev), **(extra or {})))

        add("NE_zmc", base, dict(phi_pure=P["e1"]["row"]["phi"], max_regret=P["e1"]["row"]["max_regret"], distinct=False))
        rng = np.random.default_rng(seed + 7)
        Amax = sum(g.full_a(i) for i in range(g.N))
        starts = {"NE_br_empty": None, "NE_full_service": [g.oracle(i, -1e3 * np.ones(g.d), rho=1.0, count=False) for i in range(g.N)]}
        for k in range(3):
            uu = rng.uniform(0.0, 1.0, g.d)
            starts[f"NE_random{k}"] = [g.oracle(i, uu * g.M * Amax, rho=1.0, count=False) for i in range(g.N)]
        seen = {tuple(p.key() for p in base)}
        for name, init in starts.items():
            r = zmc.run_br(g, init=init)
            reg = g.regrets(r["profile"], count=False)
            key = tuple(p.key() for p in r["profile"])
            add(name, r["profile"], dict(phi_pure=g.potential(r["profile"]), calls=r["calls"], converged=r["converged"],
                                         max_regret=float(reg.max()), distinct=key not in seen))
            seen.add(key)
        P["ne"] = dict(rows=rows, time_s=time.perf_counter() - t0, **stamp(g, st0))
        jdump(part, P)
        print(city, seed, "NE starts", len(rows), "calls", P["ne"]["bp_calls"], round(P["ne"]["time_s"]), flush=True)
    P["time_s"] = sum(P[k].get("time_s", 0) for k in ("dip", "verify", "ne")) + P["e1"]["row"]["time_s"]
    P["done"] = True
    jdump(part, P)
    print(city, seed, "core finished", round(time.perf_counter() - t_all), flush=True)


# ------------------------------------------------------------------------------------------------ arp
def arp_phase(city, seed):
    import run_arp

    run_arp.rpath = lambda prefix, c, s=0: PARTS / f"{prefix}_{c}_s{s}.csv"
    cp = jload(PARTS / f"core_{city}_s{seed}.json")

    def dip_reference(c, s):
        if cp.get("done"):
            e1, D = cp["e1"]["row"], cp["dip"]
            return dict(grid_sc0=e1["social_cost"], e3_so_sc=cp["dip"]["first_sc_target"], dip_sc=D["sc"], dip_calls=D["calls"],
                        dip_time_s=D["time_s"], dip_revenue=D["revenue"], dip_s_over_fee=D["s"] / cp["e1"]["fee"])
        d = pd.read_csv(RES / "summary_dip.csv")
        r = d[(d.city == c) & (d.seed == s)]
        return r.iloc[0].to_dict() if len(r) else {}

    run_arp.dip_reference = dip_reference
    run_arp.PARTS = PARTS / "arp"
    run_arp.PARTS.mkdir(exist_ok=True)
    ap = run_arp.PARTS / f"{city}_s{seed}.json"
    if cp.get("done") and not ap.exists():  # the unpriced equilibrium of core is the ARP status quo
        e1 = cp["e1"]
        jdump(ap, dict(base=dict(sc=e1["row"]["social_cost"], calls=e1["row"]["calls"], time_s=e1["row"]["time_s"], routes=e1["routes"],
                                 served_share=e1["row"]["served_share"], bp_calls=e1["row"].get("bp_calls", 0),
                                 bp_optimal=e1["row"].get("bp_optimal", 0), bp_unproven=e1["row"].get("bp_unproven", 0))))
    run_arp.run(city, seed, NCUST)


# ------------------------------------------------------------------------------------------------ grid
def coarse_points(g, cp):
    """Fixed coarse exact set (without the unpriced equilibrium, which is E1): see the module docstring."""
    fee = cp["e1"]["fee"]
    ext = g.gc * np.array(cp["e1"]["X"])
    B, ufix = dip.grid_family(g, ext)
    act = dip.active_zones(g)
    y = np.linalg.lstsq(B[act], np.array(cp["dip"]["u"])[act], rcond=None)[0]
    s_frac, theta = float(y[0] / fee), float(y[1])
    tc = float(np.clip(np.log2(max(theta, 0.25) / 0.5), 0.0, 5.0))  # index of theta in THETAS[1:]
    sc = float(np.interp(np.clip(s_frac, -0.6, 0.6), SFRACS, np.arange(len(SFRACS))))
    both = [(t, s) for t in THETAS[1:] for s in SFRACS if s != 0.0]
    dist = lambda p: (np.log2(p[0] / 0.5) - tc) ** 2 + (SFRACS.index(p[1]) - sc) ** 2
    near = sorted(both, key=dist)[:4]
    pts = [(0.0, s) for s in COARSE_DELIVERY] + [(t, 0.0) for t in COARSE_CONG] + near
    return pts, dict(dip_proj_theta=theta, dip_proj_sfrac=s_frac)


def grid_phase(city, seed):
    cpart = PARTS / f"core_{city}_s{seed}.json"
    cp = jload(cpart)
    if not cp.get("done"):
        print(city, seed, "core not finished, grid skipped", flush=True)
        return
    part = PARTS / f"grid_{city}_s{seed}.json"
    P = jload(part)
    if P.get("done"):
        print(city, seed, "grid done", flush=True)
        return
    g = zb.build_city_game(city, n_cust=NCUST, seed=seed)
    Z, fee = g.Z, cp["e1"]["fee"]
    ext = g.gc * np.array(cp["e1"]["X"])
    lam0 = np.array(cp["e1"]["lam"])
    full = city in FULL_GRID_CITIES
    if full:
        order = []
        for k, th in enumerate(THETAS):
            ss = SFRACS if k % 2 == 0 else SFRACS[::-1]
            order += [(th, s) for s in ss]
        order = [p for p in order if p != (0.0, 0.0)]
        info = {}
    else:
        order, info = coarse_points(g, cp)
        # evaluation order: the DIP-near 'both' points first, then the one-instrument axes
        order = order[-4:] + order[:-4]
    P.setdefault("rows", [])
    P["mode"] = "full" if full else "coarse"
    P.update(info)
    done = {(float(r["theta"]), float(r["sfrac"])) for r in P["rows"]}
    e1row = cp["e1"]["row"]
    if (0.0, 0.0) not in done:  # the unpriced equilibrium of E1 is the (0, 0) point
        r0 = {k: v for k, v in e1row.items() if k not in ("city", "seed", "N", "Z")}
        P["rows"].append(dict(city=city, seed=seed, config="none", theta=0.0, sfrac=0.0, s_usd=0.0, revenue=e1row["charges"], **r0))
        done.add((0.0, 0.0))
    lam = lam0
    t0 = time.perf_counter()
    for th, sf in order:
        if (th, sf) in done:
            continue
        toll = np.zeros(2 * Z)
        toll[:Z] = sf * fee
        toll[Z:] = th * ext
        g.set_charges(toll=toll)
        o = solve_ne(g, rounds=6, lam0=lam, certify="oracle")
        lam = o["result"]["lam"]
        r = dict(city=city, seed=seed, config=config(th, sf), theta=th, sfrac=sf, s_usd=sf * fee, N=g.N, Z=Z, **o["row"])
        r["revenue"] = r.pop("charges")
        P["rows"].append(r)
        done.add((th, sf))
        jdump(part, P)
        print(city, seed, th, sf, round(r["social_cost"], 2), r["calls"], round(time.perf_counter() - t0), flush=True)
    g.set_charges()
    if "cert" not in P:
        both = [r for r in P["rows"] if r["config"] in ("both", "none")]
        b = min(both, key=lambda r: r["social_cost"])
        if b["config"] == "both":
            toll = np.zeros(2 * Z)
            toll[:Z] = b["sfrac"] * fee
            toll[Z:] = b["theta"] * ext
            g.set_charges(toll=toll)
            oc = solve_ne(g, rounds=6, lam0=lam0, certify="fresh")
            P["cert"] = dict(theta=b["theta"], sfrac=b["sfrac"], regret_fresh=oc["row"]["max_regret"], regret_lp=oc["row"]["max_regret_lp"],
                             social_cost=oc["row"]["social_cost"], calls=oc["row"]["calls"],
                             **{k: v for k, v in oc["row"].items() if k.startswith("bp_")})
            g.set_charges()
        else:
            P["cert"] = dict(theta=0.0, sfrac=0.0, regret_fresh=float(e1row["max_regret"]), regret_lp=float(e1row["max_regret_lp"]),
                             social_cost=e1row["social_cost"], calls=0)
        jdump(part, P)
        print(city, seed, "cert", P["cert"]["theta"], P["cert"]["sfrac"], P["cert"]["regret_fresh"], flush=True)
    P["done"] = True
    jdump(part, P)
    print(city, seed, "grid finished", len(P["rows"]), "points", round(time.perf_counter() - t0), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("city")
    ap.add_argument("seed", type=int)
    ap.add_argument("phase", choices=["core", "arp", "grid"])
    a = ap.parse_args()
    lock = open(PARTS / f".lock_{a.phase}_{a.city}_s{a.seed}", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print(a.city, a.seed, a.phase, "already running elsewhere", flush=True)
        return
    {"core": core, "arp": arp_phase, "grid": grid_phase}[a.phase](a.city, a.seed)


if __name__ == "__main__":
    main()
