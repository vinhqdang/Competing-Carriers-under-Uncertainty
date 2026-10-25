"""Dual implementation pricing (DIP) on the real city games with the exact oracle, compared with the E2 leader grid.

Usage:  python experiments/run_dip.py CITY [--seed 0] [--ncust 22]
        python experiments/run_dip.py summary          (results/summary_dip.csv from the per-city files)
Environment: CCU_BP_TIME / CCU_BP_RETRY as for the exact E2 run (default here 20 / 120 s: the same exact oracle).

Per city and seed (resumable: every stage is stored in results/dip_parts/<city>_s<seed>.json and skipped on restart;
the final row goes to results/dip_<city>.csv):
  stage 'dip'     the method: social target (column generation on the social cost, rounding, coordinate polish),
                  tangent charge, cutting-plane implementation with best-response separation, priced equilibrium.
  stage 'verify'  regrets of the priced profile against the pooled and a fresh exact oracle (not counted as method calls,
                  like the fresh-oracle check of the grid's best point in E2).
  stage 'base'    unpriced equilibrium (ZMC, the E2 baseline protocol): needed only for the grid-family variant and the
                  credal check; its calls are reported separately.
  stage 'family'  DIP restricted to the grid's two-parameter family u_z = s + r theta gc_z X_z^NE.
  stage 'select'  equilibrium that the grid's protocol (ZMC from the unpriced prices) selects under DIP's charges.
  stage 'credal'  Gamma-maximin widths delta in {0.2, 0.8}: charges u(delta) = u - (sur_q + r sur_tau), regrets of the
                  target under (u(delta), sur(delta)) and the unpriced delta-equilibrium welfare from results/E4.
Zone charges: results/dip_charges_<city>[_s<seed>].csv.
"""
import argparse
import json
import os
import time

os.environ.setdefault("CCU_BP_TIME", "20")
os.environ.setdefault("CCU_BP_RETRY", "120")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import RES, read_rows, rpath, solve_ne, write_csv, zb, zmc  # noqa: E402,F401
from ccu import dip  # noqa: E402

PARTS = RES / "dip_parts"
PARTS.mkdir(exist_ok=True)
DELTAS = [0.2, 0.8]


def jdump(path, obj):
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(obj, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else float(x)))
    os.replace(tmp, path)


def routes_of(prof):
    return [[list(map(int, r)) for r in p.routes] for p in prof]


def plans_from(g, routes):
    return [g.plan_from_routes(i, [tuple(r) for r in rs]) for i, rs in enumerate(routes)]


def grid_reference(city, seed):
    """E2 (exact rows only): unpriced social cost, best grid social cost and point, calls and time of the exact grid."""
    f2, f3, src = rpath("E2", city, seed), rpath("E3", city, seed), "exact"
    if not f2.exists() or not f3.exists():  # seed not re-run with the exact oracle: price-and-branch grid (flagged)
        f2, f3, src = RES / "pb_old" / f2.name, RES / "pb_old" / f3.name, "pb"
    d = pd.read_csv(f2)
    if "oracle" in d and src == "exact":
        d = d[d.oracle == "exact"]
    base = d[(d.theta == 0) & (d.sfrac == 0)].iloc[0]
    b = d.loc[d.social_cost.idxmin()]
    e3 = pd.read_csv(f3)
    so = e3[e3.kind == "SO_main"].iloc[0]
    n = len(d)
    if "bp_calls" not in d:
        d = d.assign(bp_calls=np.nan)
    return dict(grid_oracle=src, grid_points=n, grid_sc0=float(base.social_cost), grid_sc_best=float(b.social_cost), grid_theta=float(b.theta),
                grid_sfrac=float(b.sfrac), grid_calls=int(d.calls.sum()), grid_bp_calls=int(d.bp_calls.sum()),
                grid_time_s=float(d.time_s.sum()), grid_calls_63=float(d.calls.mean() * 63), grid_bp_calls_63=float(d.bp_calls.mean() * 63),
                grid_served_best=float(b.served_share), e3_so_sc=float(so.social_cost), e3_so_calls=float(so.calls))


def stamp(g, st0):
    st = g._st
    return dict(bp_calls=st["calls"] - st0["calls"], bp_optimal=st["optimal"] - st0["optimal"], bp_unproven=st["timeouts"] - st0["timeouts"])


def run(city, seed, ncust):
    part = PARTS / f"{city}_s{seed}.json"
    P = json.loads(part.read_text()) if part.exists() else {}
    out_csv = rpath("dip", city, seed)
    if P.get("done") and out_csv.exists():
        print(city, seed, "done, skipping", flush=True)
        return
    g = zb.build_city_game(city, n_cust=ncust, seed=seed)
    Z = g.Z
    ref = grid_reference(city, seed)
    t_all = time.perf_counter()
    # ------------------------------------------------------------------ stage dip
    if "dip" not in P:
        st0 = dict(g._st)
        log = []
        t0 = time.perf_counter()
        o = dip.dip(g, so_iters=40, log=log)
        ev = g.evaluate(o["profile"])
        P["dip"] = dict(u=o["u"], u_tan=o["u_tan"], s=o["s"], t=o["t"], status=o["status"], rounds=o["rounds"],
                        n_cuts=o["n_cuts"], slack=o["slack"], converged=o["converged"], sc=o["sc"], sc_target=o["sc_target"],
                        welfare=ev["welfare"], served_share=ev["served_share"], mean_slowdown=ev["mean_slowdown"],
                        revenue=ev["charges"], profit=ev["profit_total"], loss_bound=o["loss_bound"],
                        first_sc=o["first"]["sc"], first_status=o["first"]["status"], first_rounds=o["first"]["rounds"],
                        first_calls=o["first"]["calls"], first_time_s=o["first"]["time_s"], calls_restarts=o["calls_restarts"],
                        calls=o["calls"], calls_so=o["calls_so"], calls_implement=o["calls_implement"],
                        so_relaxed=o["so_relaxed"], so_pure=o["so_pure"], time_s=time.perf_counter() - t0,
                        Qstar=o["Qstar"], q_priced=ev["q_z"], X_priced=ev["X_z"], log=log,
                        routes=routes_of(o["profile"]), target_routes=routes_of(o["target"]), **stamp(g, st0))
        jdump(part, P)
        print(city, seed, "dip", o["status"], o["rounds"], round(o["sc"], 2), "target", round(o["sc_target"], 2),
              "grid", round(ref["grid_sc_best"], 2), "calls", o["calls"], round(time.perf_counter() - t0), flush=True)
    D = P["dip"]
    u = np.array(D["u"])
    prof = plans_from(g, D["routes"])
    target = plans_from(g, D["target_routes"])
    # ------------------------------------------------------------------ stage verify
    if "verify" not in P:
        _, _, toll = dip.instruments(g, u)
        g.set_charges(toll=toll)
        st0 = dict(g._st)
        t0 = time.perf_counter()
        reg = g.regrets(prof, count=False)
        regf = g.regrets(prof, count=False, fresh=True)
        P["verify"] = dict(max_regret=float(reg.max()), max_regret_fresh=float(regf.max()),
                           max_regret_fresh_lb=float(np.nanmax(g._last_regret_lp)), time_s=time.perf_counter() - t0, **stamp(g, st0))
        jdump(part, P)
        print(city, seed, "verify", P["verify"]["max_regret"], P["verify"]["max_regret_fresh"], flush=True)
    # ------------------------------------------------------------------ stage base (unpriced equilibrium)
    if "base" not in P:
        g.set_charges()
        c0, st0, t0 = g.calls, dict(g._st), time.perf_counter()
        b = solve_ne(g, rounds=8)
        P["base"] = dict(sc=b["row"]["social_cost"], X=b["eval"]["X_z"], q=b["eval"]["q_z"], A=sum(p.a for p in b["profile"]),
                         lam=b["result"]["lam"], calls=g.calls - c0, time_s=time.perf_counter() - t0, **stamp(g, st0))
        jdump(part, P)
        print(city, seed, "base", round(P["base"]["sc"], 2), "E2 base", round(ref["grid_sc0"], 2), flush=True)
    Bs = P["base"]
    # ------------------------------------------------------------------ stage family (grid's two-parameter family)
    if "family" not in P:
        ext = g.gc * np.array(Bs["X"])
        B, ufix = dip.grid_family(g, ext)
        c0, st0, t0 = g.calls, dict(g._st), time.perf_counter()
        imp = dip.implement(g, target, np.array(D["u_tan"]), basis=B, ufix=ufix, max_rounds=12)
        uf, ok = imp["u"], True
        if imp["status"] != "exact":
            uf, pf, ok = dip.fallback(g, target, imp, np.array(D["u_tan"]), (B, ufix))
        else:
            pf = [g.plan_from_routes(i, p.routes) for i, p in enumerate(target)]
        ev = g.evaluate(pf)
        y = np.linalg.lstsq(B[dip.active_zones(g)], uf[dip.active_zones(g)], rcond=None)[0]
        fee = g.meta["params"]["delivery_fee_usd"]
        P["family"] = dict(status=imp["status"], rounds=imp["rounds"], sc=ev["social_cost"], s_over_fee=float(y[0] / fee), theta=float(y[1]),
                           calls_implement=g.calls - c0, converged=ok, time_s=time.perf_counter() - t0, **stamp(g, st0))
        jdump(part, P)
        print(city, seed, "family", imp["status"], round(ev["social_cost"], 2), round(y[0] / fee, 3), round(y[1], 3), flush=True)
    # ------------------------------------------------------------------ stage select (grid protocol under DIP's charges)
    if "select" not in P:
        _, _, toll = dip.instruments(g, u)
        g.set_charges(toll=toll)
        c0, st0, t0 = g.calls, dict(g._st), time.perf_counter()
        o = solve_ne(g, rounds=6, lam0=np.array(Bs["lam"]))
        P["select"] = dict(sc=o["row"]["social_cost"], same_as_dip=bool(abs(o["row"]["social_cost"] - D["sc"]) < 1e-6),
                           calls=g.calls - c0, time_s=time.perf_counter() - t0, **stamp(g, st0))
        jdump(part, P)
        print(city, seed, "select", round(o["row"]["social_cost"], 2), flush=True)
    # ------------------------------------------------------------------ stage credal
    if "credal" not in P:
        A = np.array(Bs["A"])
        pos = A[A > 1e-9]
        w = np.where(A > 1e-9, A, np.median(pos) if len(pos) else 1.0)  # weights of run_imprecision.py
        rows = []
        e4 = read_rows(rpath("E4", city, seed))
        for de in DELTAS:
            sur = de * g.M * w
            ud = dip.surcharge_shift(g, u, sur)
            _, _, toll = dip.instruments(g, ud)
            g.set_charges(toll=toll, sur=sur)
            c0, st0 = g.calls, dict(g._st)
            pr = [g.plan_from_routes(i, p.routes) for i, p in enumerate(prof)]
            reg = g.regrets(pr, count=True)
            ev = g.evaluate(pr)
            e4w = [r for r in e4 if r.get("kind") == "gamma" and abs(float(r["delta"]) - de) < 1e-9 and r.get("oracle", "exact") == "exact"]
            rows.append(dict(delta=de, max_regret=float(reg.max()), sc=ev["social_cost"], calls=g.calls - c0,
                             unpriced_sc_E4=float(e4w[0]["social_cost"]) if e4w else np.nan,
                             s_delta=float(dip.instruments(g, ud)[0]), **stamp(g, st0)))
            print(city, seed, "credal", de, rows[-1]["max_regret"], round(ev["social_cost"], 2), flush=True)
        g.set_charges()
        P["credal"] = rows
        jdump(part, P)
    # ------------------------------------------------------------------ outputs
    zones = pd.read_csv(zb.ROOT / "data/processed" / city / "zones.csv")
    act = dip.active_zones(g)
    kappa, m, mS = dip.curvatures(g)
    ch = pd.DataFrame(dict(zone_id=zones.zone_id, active=act, u=u, u_tangent=D["u_tan"], s=D["s"], t=D["t"],
                           Qstar=D["Qstar"], q_priced=D["q_priced"], q_unpriced=Bs["q"], kappa=kappa, b=g.b))
    write_csv(rpath("dip_charges", city, seed), ch.to_dict("records"))
    V, F, S, C = P["verify"], P["family"], P["select"], P["credal"]
    gain_grid = ref["grid_sc0"] - ref["grid_sc_best"]
    row = dict(city=city, seed=seed, N=g.N, Z=Z, **ref,
               dip1_sc=D["first_sc"], dip1_status=D["first_status"], dip1_rounds=D["first_rounds"], dip1_calls=D["first_calls"],
               dip1_time_s=D["first_time_s"], dip1_gain_share=(ref["grid_sc0"] - D["first_sc"]) / gain_grid if gain_grid > 1e-9 else np.nan,
               dip1_calls_share=D["first_calls"] / ref["grid_calls"], dip_calls_restarts=D["calls_restarts"], dip_loss_bound=D["loss_bound"],
               dip_status=D["status"], dip_rounds=D["rounds"], dip_n_cuts=D["n_cuts"], dip_sc=D["sc"], dip_sc_target=D["sc_target"],
               dip_welfare=D["welfare"], dip_served_share=D["served_share"], dip_revenue=D["revenue"], dip_profit=D["profit"],
               dip_s_over_fee=D["s"] / g.meta["params"]["delivery_fee_usd"], dip_t_max=float(np.max(D["t"])),
               dip_calls=D["calls"], dip_calls_so=D["calls_so"], dip_calls_implement=D["calls_implement"], dip_bp_calls=D["bp_calls"],
               dip_bp_unproven=D["bp_unproven"], dip_time_s=D["time_s"], dip_so_relaxed=D["so_relaxed"],
               dip_gain_share=(ref["grid_sc0"] - D["sc"]) / gain_grid if gain_grid > 1e-9 else np.nan,
               dip_gain_pct_abs=100 * (ref["grid_sc0"] - D["sc"]) / abs(ref["grid_sc0"]),
               grid_gain_pct_abs=100 * gain_grid / abs(ref["grid_sc0"]),
               dip_calls_share=D["calls"] / ref["grid_calls"], dip_calls_share_63=D["calls"] / ref["grid_calls_63"],
               dip_bp_share=D["bp_calls"] / ref["grid_bp_calls"] if ref["grid_bp_calls"] else np.nan,
               dip_time_share=D["time_s"] / ref["grid_time_s"] if ref["grid_oracle"] == "exact" else np.nan,
               poa_dip=D["sc"] / ref["e3_so_sc"], poa_grid=ref["grid_sc_best"] / ref["e3_so_sc"],
               poa_dip_own=D["sc"] / D["sc_target"],
               verify_max_regret=V["max_regret"], verify_max_regret_fresh=V["max_regret_fresh"],
               verify_max_regret_fresh_lb=V["max_regret_fresh_lb"],
               base_sc=Bs["sc"], base_calls=Bs["calls"],
               fam_status=F["status"], fam_sc=F["sc"], fam_s_over_fee=F["s_over_fee"], fam_theta=F["theta"], fam_calls_implement=F["calls_implement"],
               fam_gain_share=(ref["grid_sc0"] - F["sc"]) / gain_grid if gain_grid > 1e-9 else np.nan,
               sel_sc=S["sc"], sel_same=S["same_as_dip"], sel_calls=S["calls"],
               sel_gain_share=(ref["grid_sc0"] - S["sc"]) / gain_grid if gain_grid > 1e-9 else np.nan,
               **{f"credal{c['delta']}_regret": c["max_regret"] for c in C}, **{f"credal{c['delta']}_sc": c["sc"] for c in C},
               **{f"credal{c['delta']}_unpriced_sc": c["unpriced_sc_E4"] for c in C},
               **{f"credal{c['delta']}_s_over_fee": c["s_delta"] / g.meta["params"]["delivery_fee_usd"] for c in C})
    write_csv(out_csv, [row])
    P["done"] = True
    jdump(part, P)
    print(city, seed, "finished", round(time.perf_counter() - t_all), flush=True)


def summary():
    rows = []
    for f in sorted(RES.glob("dip_*.csv")):
        if f.name.startswith(("dip_charges", "dip_tiny")):
            continue
        rows += read_rows(f)
    if not rows:
        return
    d = pd.DataFrame(rows).sort_values(["city", "seed"])
    write_csv(RES / "summary_dip.csv", d.to_dict("records"))
    cols = ["city", "seed", "dip_status", "dip_gain_share", "dip_calls", "grid_calls", "dip_calls_share", "dip_calls_share_63",
            "poa_dip", "poa_grid", "fam_gain_share", "sel_gain_share"]
    print(d[cols].to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("city")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--ncust", type=int, default=22)
    a = ap.parse_args()
    if a.city == "summary":
        summary()
    else:
        import fcntl
        lock = open(PARTS / f".lock_{a.city}_s{a.seed}", "w")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print(a.city, a.seed, "already running elsewhere", flush=True)
            return
        run(a.city, a.seed, a.ncust)


if __name__ == "__main__":
    main()
