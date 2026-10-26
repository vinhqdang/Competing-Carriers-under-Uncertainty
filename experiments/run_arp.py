"""Aggregate-response pricing on the real city games with the exact oracle, compared with DIP and the E2 leader grid.

Usage:  python experiments/run_arp.py CITY [--seed 0] [--ncust 22]
        python experiments/run_arp.py summary          (results/summary_arp.csv from the per-city files)
Environment: CCU_BP_TIME / CCU_BP_RETRY as for the exact E2 and DIP runs (default here 20 / 120 s: the same exact oracle).

Per city and seed (resumable: every stage is stored in results/arp_parts/<city>_s<seed>.json and skipped on restart;
the final row goes to results/arp_<city>[_s<seed>].csv):
  stage 'base'      unpriced equilibrium (ZMC, the E1/E2 protocol): the status quo the city observes first.
  stage 'arp'       flat ARP (plain), the city posting zone charges from (Q_z, n_z) only, carriers best-responding
                    day to day from the previous profile; then 'arp_msa' (successive averages) if the plain run cycles.
  stage 'mct_br'    marginal tariff + carriers' best responses from the status quo (observation-only).
  stage 'mct_so'    marginal tariff + potential-minimising solver (ZMC on the social-cost potential = E3's SO solve).
  stage 'verify'    regrets of the final profiles against the pooled and a fresh exact oracle (not counted as calls).
References: results/summary_dip.csv (DIP, grid, E3 social optimum of the same city and seed).
"""
import argparse
import json
import os
import time

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import RES, read_rows, rpath, solve_ne, write_csv, zb, zmc  # noqa: E402,F401
from ccu import arp, dip  # noqa: E402

PARTS = RES / "arp_parts"
PARTS.mkdir(exist_ok=True)
os.environ.setdefault("CCU_BP_TIME", "20")
os.environ.setdefault("CCU_BP_RETRY", "120")


def jdump(path, obj):
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(obj, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else float(x)))
    os.replace(tmp, path)


def routes_of(prof):
    return [[list(map(int, r)) for r in p.routes] for p in prof]


def plans_from(g, routes):
    return [g.plan_from_routes(i, [tuple(r) for r in rs]) for i, rs in enumerate(routes)]


def stamp(g, st0):
    st = g._st
    return dict(bp_calls=st["calls"] - st0["calls"], bp_optimal=st["optimal"] - st0["optimal"], bp_unproven=st["timeouts"] - st0["timeouts"])


def dip_reference(city, seed):
    d = pd.read_csv(RES / "summary_dip.csv")
    r = d[(d.city == city) & (d.seed == seed)]
    return r.iloc[0].to_dict() if len(r) else {}


def run(city, seed, ncust):
    part = PARTS / f"{city}_s{seed}.json"
    P = json.loads(part.read_text()) if part.exists() else {}
    out_csv = rpath("arp", city, seed)
    if P.get("done") and out_csv.exists():
        print(city, seed, "done, skipping", flush=True)
        return
    g = zb.build_city_game(city, n_cust=ncust, seed=seed)
    ref = dip_reference(city, seed)
    t_all = time.perf_counter()
    # ------------------------------------------------------------------ base
    if "base" not in P:
        g.set_charges()
        c0, st0, t0 = g.calls, dict(g._st), time.perf_counter()
        b = solve_ne(g, rounds=8)
        P["base"] = dict(sc=b["row"]["social_cost"], calls=g.calls - c0, time_s=time.perf_counter() - t0,
                         routes=routes_of(b["profile"]), served_share=b["row"]["served_share"], **stamp(g, st0))
        jdump(part, P)
        print(city, seed, "base", round(P["base"]["sc"], 2), "grid base", round(ref.get("grid_sc0", np.nan), 2), flush=True)
    base = plans_from(g, P["base"]["routes"])
    # ------------------------------------------------------------------ flat ARP
    for stage, theta in (("arp", "plain"), ("arp_msa", "msa")):
        if stage in P:
            continue
        if stage == "arp_msa" and P["arp"]["status"] == "fixed_point":
            P[stage] = dict(skipped=True)
            jdump(part, P)
            continue
        g.set_charges()
        st0, t0 = dict(g._st), time.perf_counter()
        o = arp.arp(g, base, theta=theta, max_rounds=10)
        ev = g.evaluate(o["profile"])
        P[stage] = dict(sc=o["sc"], status=o["status"], rounds=o["rounds"], calls=o["calls"], best_sc=o["best_sc"],
                        best_round=o["best_round"], sc_path=o["sc_path"], u=o["u"], Q=o["Q"], n=o["n"], rho=o["rho"],
                        step_rel=[h["step_rel"] for h in o["hist"]], welfare=ev["welfare"], served_share=ev["served_share"],
                        revenue=ev["charges"], profit=ev["profit_total"], s=dip.instruments(g, o["u"])[0],
                        t_max=float(np.max(dip.instruments(g, o["u"])[1])), routes=routes_of(o["profile"]),
                        time_s=time.perf_counter() - t0, **stamp(g, st0))
        jdump(part, P)
        print(city, seed, stage, o["status"], o["rounds"], "sc", round(o["sc"], 2), "path", [round(x, 1) for x in o["sc_path"]],
              "calls", o["calls"], "dip", round(ref.get("dip_sc", np.nan), 2), round(time.perf_counter() - t0), flush=True)
    # ------------------------------------------------------------------ marginal tariff, BR from the status quo
    if "mct_br" not in P:
        g.set_charges()
        st0, t0 = dict(g._st), time.perf_counter()
        o = arp.arp_marginal(g, base)
        ev = g.evaluate(o["profile"])
        P["mct_br"] = dict(sc=o["sc"], calls=o["calls"], monotone=o["monotone"], converged=o["converged"], sc_path=o["sc_path"],
                           payments=o["payments"], welfare=ev["welfare"], served_share=ev["served_share"],
                           routes=routes_of(o["profile"]), time_s=time.perf_counter() - t0, **stamp(g, st0))
        jdump(part, P)
        print(city, seed, "mct_br", "sc", round(o["sc"], 2), "monotone", o["monotone"], "calls", o["calls"], round(time.perf_counter() - t0), flush=True)
    # ------------------------------------------------------------------ marginal tariff, potential-minimising solver
    if "mct_so" not in P:
        g.set_charges()
        so = g.so_variant(False)
        st0, t0, c0 = dict(g._st), time.perf_counter(), so.calls
        r = zmc.run_zmc(so, rounds=8)
        prof = plans_from(g, routes_of(r["profile"]))
        ev = g.evaluate(prof)
        mg = arp.MarginalTariffGame(g)
        P["mct_so"] = dict(sc=dip.social_cost(g, prof), calls=so.calls - c0, converged=bool(r["converged"]), payments=mg.payments(prof),
                           welfare=ev["welfare"], served_share=ev["served_share"], routes=routes_of(prof),
                           time_s=time.perf_counter() - t0, **stamp(g, st0))
        jdump(part, P)
        print(city, seed, "mct_so", "sc", round(P["mct_so"]["sc"], 2), "calls", P["mct_so"]["calls"], "e3 SO", round(ref.get("e3_so_sc", np.nan), 2), flush=True)
    # ------------------------------------------------------------------ verify
    if "verify" not in P:
        V = {}
        st0, t0 = dict(g._st), time.perf_counter()
        for stage in ("arp", "arp_msa"):
            if P[stage].get("skipped"):
                continue
            _, _, toll = dip.instruments(g, np.array(P[stage]["u"]))
            g.set_charges(toll=toll)
            prof = plans_from(g, P[stage]["routes"])
            V[stage] = dict(max_regret=float(g.regrets(prof, count=False).max()),
                            max_regret_fresh=float(g.regrets(prof, count=False, fresh=True).max()))
        g.set_charges()
        mg = arp.MarginalTariffGame(g)
        for stage in ("mct_br", "mct_so"):
            prof = plans_from(g, P[stage]["routes"])
            V[stage] = dict(max_regret=float(mg.regrets(prof).max()))
        V["time_s"] = time.perf_counter() - t0
        V.update(stamp(g, st0))
        P["verify"] = V
        jdump(part, P)
        print(city, seed, "verify", {k: v for k, v in V.items() if isinstance(v, dict)}, flush=True)
    # ------------------------------------------------------------------ row
    B, A, AM, MB, MS, V = P["base"], P["arp"], P["arp_msa"], P["mct_br"], P["mct_so"], P["verify"]
    sc0 = ref.get("grid_sc0", B["sc"])
    gain_grid = ref.get("grid_sc0", np.nan) - ref.get("grid_sc_best", np.nan)
    share = lambda sc: (sc0 - sc) / gain_grid if gain_grid > 1e-9 else np.nan
    fee = g.meta["params"]["delivery_fee_usd"]
    row = dict(city=city, seed=seed, N=g.N, Z=g.Z, rho=A["rho"], base_sc=B["sc"], base_calls=B["calls"], grid_sc0=sc0,
               grid_sc_best=ref.get("grid_sc_best", np.nan), grid_calls=ref.get("grid_calls", np.nan), grid_calls_63=ref.get("grid_calls_63", np.nan),
               e3_so_sc=ref.get("e3_so_sc", np.nan), dip_sc=ref.get("dip_sc", np.nan), dip_calls=ref.get("dip_calls", np.nan),
               dip_time_s=ref.get("dip_time_s", np.nan), dip_gain_share=ref.get("dip_gain_share", np.nan), dip_revenue=ref.get("dip_revenue", np.nan),
               dip_s_over_fee=ref.get("dip_s_over_fee", np.nan),
               arp_status=A["status"], arp_rounds=A["rounds"], arp_sc=A["sc"], arp_best_sc=A["best_sc"], arp_calls=A["calls"], arp_time_s=A["time_s"],
               arp_gain_share=share(A["sc"]), arp_best_gain_share=share(A["best_sc"]), arp_revenue=A["revenue"], arp_served_share=A["served_share"],
               arp_s_over_fee=A["s"] / fee, arp_t_max=A["t_max"], arp_sc_path=";".join("%.6g" % x for x in A["sc_path"]),
               arp_step_rel=";".join("%.3g" % x for x in A["step_rel"]), arp_bp_unproven=A["bp_unproven"],
               arp_msa_status=AM.get("status", "skipped"), arp_msa_rounds=AM.get("rounds", np.nan), arp_msa_sc=AM.get("sc", np.nan),
               arp_msa_calls=AM.get("calls", np.nan), arp_msa_gain_share=share(AM["sc"]) if "sc" in AM else np.nan,
               mct_br_sc=MB["sc"], mct_br_calls=MB["calls"], mct_br_monotone=MB["monotone"], mct_br_gain_share=share(MB["sc"]),
               mct_br_payments=MB["payments"], mct_br_served_share=MB["served_share"],
               mct_so_sc=MS["sc"], mct_so_calls=MS["calls"], mct_so_gain_share=share(MS["sc"]), mct_so_payments=MS["payments"],
               mct_so_served_share=MS["served_share"],
               arp_calls_share_dip=A["calls"] / ref["dip_calls"] if ref.get("dip_calls") else np.nan,
               arp_calls_share_63=A["calls"] / ref["grid_calls_63"] if ref.get("grid_calls_63") else np.nan,
               poa_arp=A["sc"] / ref["e3_so_sc"] if ref.get("e3_so_sc") else np.nan,
               poa_mct_br=MB["sc"] / ref["e3_so_sc"] if ref.get("e3_so_sc") else np.nan,
               poa_mct_so=MS["sc"] / ref["e3_so_sc"] if ref.get("e3_so_sc") else np.nan,
               verify_arp_regret=V.get("arp", {}).get("max_regret", np.nan), verify_arp_regret_fresh=V.get("arp", {}).get("max_regret_fresh", np.nan),
               verify_arp_msa_regret_fresh=V.get("arp_msa", {}).get("max_regret_fresh", np.nan),
               verify_mct_br_regret=V["mct_br"]["max_regret"], verify_mct_so_regret=V["mct_so"]["max_regret"],
               time_s=time.perf_counter() - t_all)
    write_csv(out_csv, [row])
    # zone charges
    zones = pd.read_csv(zb.ROOT / "data/processed" / city / "zones.csv")
    kappa, m, _ = dip.curvatures(g)
    ch = pd.DataFrame(dict(zone_id=zones.zone_id, active=dip.active_zones(g), u_arp=A["u"], Q_arp=A["Q"], n_arp=A["n"], kappa=kappa, b=g.b))
    write_csv(rpath("arp_charges", city, seed), ch.to_dict("records"))
    P["done"] = True
    jdump(part, P)
    print(city, seed, "finished", round(time.perf_counter() - t_all), flush=True)


def summary():
    rows = []
    for f in sorted(RES.glob("arp_*.csv")):
        if f.name.startswith(("arp_charges", "arp_tiny", "arp_parts")):
            continue
        rows += read_rows(f)
    if not rows:
        return
    d = pd.DataFrame(rows).sort_values(["city", "seed"])
    write_csv(RES / "summary_arp.csv", d.to_dict("records"))
    cols = ["city", "seed", "rho", "arp_status", "arp_rounds", "arp_gain_share", "arp_best_gain_share", "mct_br_gain_share", "mct_so_gain_share",
            "dip_gain_share", "arp_calls", "mct_br_calls", "mct_so_calls", "dip_calls", "grid_calls"]
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
