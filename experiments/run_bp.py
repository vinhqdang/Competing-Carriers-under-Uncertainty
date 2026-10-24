"""Branch-and-price for BRL: verification, nine metro instances, integrated game oracle, summaries and figure.

  python experiments/run_bp.py verify [--seeds 0 400]            exact check against complete enumeration -> results/bp_verify.csv
  python experiments/run_bp.py metro CITY [CITY ...] [--tl 1800]  one JSON per city in results/bp_metro_<city>.json
  python experiments/run_bp.py game CITY [--tl 20]                integrated ZMC + BRL game with the exact integer step -> results/bp_game_<city>.csv
  python experiments/run_bp.py summary                            results/bp_metro.csv, summary_bp*.csv, figures/bp_gap.png

Every command is resumable: finished seeds / cities are skipped (use --force), files are written atomically.
Use at most 2 cores: `OMP_NUM_THREADS=1` is set below.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "theory/new_algorithm_B"))
RES = ROOT / "results"
FIG = ROOT / "figures"
RES.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

from ccu import bp, brl  # noqa: E402

CITIES = ["NewDelhi", "Cairo", "Moscow", "BuenosAires", "NewYork", "Bombay", "London", "Paris", "Berlin"]


def atomic_csv(path: Path, rows) -> None:
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    pd.DataFrame(rows).to_csv(tmp, index=False, float_format="%.8g")
    os.replace(tmp, path)


def atomic_json(path: Path, obj) -> None:
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(obj, default=float, indent=1))
    os.replace(tmp, path)


def progress(line: str) -> None:
    """Append one line to results/PROGRESS_bp.md (the log section)."""
    p = RES / "PROGRESS_bp.md"
    with open(p, "a") as fh:
        fh.write(f"- {time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")


# ---------------------------------------------------------------------------------------------------------------
# 1. verification against complete enumeration
# ---------------------------------------------------------------------------------------------------------------


def _prototype():
    spec = importlib.util.spec_from_file_location("brl_prototype_run", ROOT / "theory/new_algorithm_B/prototype.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def verify(lo: int, hi: int, force: bool = False) -> None:
    pr = _prototype()
    path = RES / "bp_verify.csv"
    rows = [] if force or not path.exists() else pd.read_csv(path).to_dict("records")
    done = {(int(r["seed"]), r["kind"]) for r in rows}
    t00 = time.time()
    for seed in range(lo, hi):
        rng = np.random.default_rng(1000 + seed)
        n = int(rng.integers(7, 11))
        cap = int(rng.integers(2, 6))
        Tfrac = float(rng.uniform(0.3, 1.2))
        P = pr.random_pricing(np.random.default_rng(seed), n, K=4, cap=cap, Tfrac=Tfrac)
        loss = brl.Loss(P.loss.gamma, P.loss.rho, P.loss.Tmax, P.loss.fixed)
        inst = brl.RoutingInstance(n, P.tau, P.svc, P.dem, P.cap, P.Qk, P.w, loss)
        single = np.array([inst.route_cost((j,)) for j in range(1, n + 1)])
        for part in (True, False):
            kind = "partition" if part else "packing"
            kap = (None if seed % 2 == 0 else np.concatenate([[0.0], rng.uniform(-50, 50, n)])) if part else \
                np.concatenate([[0.0], -rng.uniform(0.6, 2.2, n) * single])
            if (seed, kind) in done:
                continue
            ng_size = int(rng.integers(3, 6))
            exact, _ = bp.exact_by_enumeration(inst, kap, part)
            if not part:
                exact = min(exact, 0.0)
            r = bp.solve_bp(inst, kap, partition=part, ng_size=ng_size, time_limit=120)
            ok = r.status == "optimal" and abs(r.value - exact) < 1e-6 * max(1.0, abs(exact)) and r.lb <= exact + 1e-6
            rows.append(dict(seed=seed, kind=kind, n=n, cap=cap, Tfrac=Tfrac, ng=ng_size, exact=exact, bp=r.value, lb=r.lb,
                             root_lp=r.root_lp, price_and_branch=r.pb_value, nodes=r.nodes, status=r.status,
                             bp_ok=bool(ok), pb_suboptimal=bool(r.pb_value > exact + 1e-7 * max(1.0, abs(exact))),
                             pb_gap_pct=100 * (r.pb_value - exact) / max(1.0, abs(exact)), time=r.time))
        if seed % 20 == 19 or seed == hi - 1:
            atomic_csv(path, rows)
            print(f"verify seeds <= {seed}: {len(rows)} rows, failures {sum(not r['bp_ok'] for r in rows)}", flush=True)
    atomic_csv(path, rows)
    df = pd.DataFrame(rows)
    agg = df.groupby("kind").agg(instances=("seed", "count"), bp_exact=("bp_ok", "sum"), pb_suboptimal=("pb_suboptimal", "sum"),
                                 max_pb_gap_pct=("pb_gap_pct", "max"), mean_nodes=("nodes", "mean"), max_nodes=("nodes", "max"))
    agg.loc["all"] = [len(df), df.bp_ok.sum(), df.pb_suboptimal.sum(), df.pb_gap_pct.max(), df.nodes.mean(), df.nodes.max()]
    agg.reset_index().to_csv(RES / "summary_bp_verify.csv", index=False, float_format="%.6g")
    print(agg)
    progress(f"verify done ({len(df)} instances, {time.time() - t00:.0f}s this call): bp exact {int(df.bp_ok.sum())}/{len(df)}, "
             f"price-and-branch suboptimal {int(df.pb_suboptimal.sum())}")


# ---------------------------------------------------------------------------------------------------------------
# 2. nine metro instances
# ---------------------------------------------------------------------------------------------------------------


def metro(city: str, tl: float, node_limit: int, ng_size: int, force: bool = False) -> None:
    out = RES / f"bp_metro_{city}.json"
    if out.exists() and not force:
        print(city, "already done", flush=True)
        return
    import real_instances as ri

    P, true, meta = ri.build(city)
    cost = ri.make_costs(P, true, eps_w=0.05)
    loss = brl.Loss(P.loss.gamma, P.loss.rho, P.loss.Tmax, P.loss.fixed)
    inst = brl.RoutingInstance(P.n, P.tau, P.svc, P.dem, P.cap, P.Qk, P.w, loss)
    # heuristics exactly as in real_instances.testE (same rng stream): cached
    hpath = RES / f"bp_heur_{city}.json"
    if hpath.exists():
        sols = json.loads(hpath.read_text())
    else:
        rng = np.random.default_rng(0)
        sols, htime = {}, {}
        for model in ("pbox", "saa", "wass"):
            t0 = time.perf_counter()
            sols[model], _ = ri.heuristic(P, cost, model, rng)
            htime[model] = time.perf_counter() - t0
        sols["time"] = htime
        atomic_json(hpath, sols)
    print(city, "heuristics ready", flush=True)
    log = lambda m: print(city, m, flush=True)  # noqa: E731
    res = bp.solve_bp(inst, None, partition=True, ng_size=ng_size, time_limit=tl, node_limit=node_limit, gap_tol=1e-6,
                      mip_every=8, mip_time=10.0, log=log)
    plans = {"heur_pbox": sols["pbox"], "heur_saa": sols["saa"], "heur_wass": sols["wass"],
             "price_and_branch": [list(r) for r in res.pb_routes], "branch_and_price": [list(r) for r in res.routes]}
    ev = {k: {m: sum(cost(tuple(r), m) for r in v) for m in ("pbox", "indep_pbox", "saa", "true")} for k, v in plans.items()}
    # check that every plan is a partition of the customers
    for k, v in plans.items():
        seen = sorted(j for r in v for j in r)
        assert seen == list(range(1, P.n + 1)), (city, k)
    pub = {}
    ep = ROOT / "theory/new_algorithm_B/results_E.json"
    if ep.exists():
        for row in json.loads(ep.read_text()):
            if row["city"] == city:
                pub = dict(published_lp=row["cg"]["lp_bound"], published_pb=row["cg"]["ub"])
    rec = dict(city=city, n=P.n, ng_size=ng_size, tl=tl, root_lp=res.root_lp, root_lp_final=res.root_lp_final,
               pb_value=res.pb_value, bp_value=res.value, bp_lb=res.lb, gap_abs=res.gap, gap_rel=res.rel_gap,
               status=res.status, bound_valid=res.bound_valid, nodes=res.nodes, nodes_open=res.nodes_open,
               time=res.time, root_time=res.root_time, pricing_time=res.pricing_time, n_pricing=res.n_pricing,
               n_cols=res.n_cols, max_labels=res.max_labels, ng_aug=res.ng_aug, notes=res.notes,
               heur_time=sols.get("time"), plans=plans, eval=ev, meta=meta, **pub)
    atomic_json(out, rec)
    e = ev
    msg = (f"{city}: root {res.root_lp:.4f} P&B {res.pb_value:.4f} B&P {res.value:.4f} lb {res.lb:.4f} {res.status} "
           f"nodes {res.nodes} {res.time:.0f}s | heur pbox {e['heur_pbox']['pbox']:.4f} saa {e['heur_saa']['pbox']:.4f}")
    print(msg, flush=True)
    progress("metro " + msg)


# ---------------------------------------------------------------------------------------------------------------
# 3. integrated game
# ---------------------------------------------------------------------------------------------------------------


def game(city: str, tl: float, seed: int = 0, rounds: int = 8, ncust: int = 22, force: bool = False) -> None:
    from ccu import zmc_brl as zb

    sys.path.insert(0, str(ROOT / "experiments"))
    from common import scalars, solve_ne  # noqa: E402

    out = RES / f"bp_game_{city}.csv"
    if out.exists() and not force:
        print(city, "game already done", flush=True)
        return
    g = zb.build_city_game(city, n_cust=ncust, seed=seed)
    g.bp_time = tl
    t0 = time.perf_counter()
    o = solve_ne(g, rounds=rounds, certify="fresh")
    wall = time.perf_counter() - t0
    row = dict(city=city, seed=seed, bp_time_limit=tl, **o["row"], wall_s=wall, bp_calls=g.bp_calls, bp_optimal=g.bp_optimal,
               bp_timeouts=g.bp_timeouts, bp_nodes=g.bp_nodes, bp_max_gap=g.bp_max_gap, bp_total_time=g.bp_time_used)
    old = pd.read_csv(RES / f"E1_{city}.csv")
    old = old[(old.scenario == "base") & (old.seed == seed)].iloc[0]
    for k in ("welfare", "social_cost", "deliveries", "served_share", "vehicles", "vehicle_hours", "routing_cost",
              "profit_total", "phi", "calls", "converged", "time_s", "max_regret", "eta_cert", "lp_gap_max"):
        row[f"pb_{k}"] = old[k]
    row["profile_routes"] = json.dumps([sorted(p.routes) for p in o["profile"]])
    atomic_csv(out, [row])
    msg = (f"game {city}: welfare {row['welfare']:.4f} (P&B {old['welfare']:.4f}) served {row['served_share']:.4f} "
           f"({old['served_share']:.4f}) regret {row.get('max_regret', float('nan')):.2e} calls {row['calls']} "
           f"time {row['time_s']:.0f}s (P&B {old['time_s']:.0f}s) bp optimal {g.bp_optimal}/{g.bp_calls}")
    print(msg, flush=True)
    progress(msg)


# ---------------------------------------------------------------------------------------------------------------
# 4. summaries and figure
# ---------------------------------------------------------------------------------------------------------------


def summary() -> None:
    rows = []
    for city in CITIES:
        p = RES / f"bp_metro_{city}.json"
        if not p.exists():
            continue
        r = json.loads(p.read_text())
        e = r["eval"]
        sa, bpv = e["heur_saa"], e["branch_and_price"]
        best_h = min(e[k]["pbox"] for k in ("heur_pbox", "heur_saa", "heur_wass"))
        rows.append(dict(
            city=city, root_lp=r["root_lp"], root_lp_final=r["root_lp_final"], price_and_branch=r["pb_value"],
            published_price_and_branch=r.get("published_pb"), branch_and_price=r["bp_value"], bp_lower_bound=r["bp_lb"],
            gap_abs=r["gap_abs"], gap_rel_pct=100 * r["gap_rel"], status=r["status"], nodes=r["nodes"], nodes_open=r["nodes_open"],
            time_s=r["time"], root_time_s=r["root_time"], pricing_time_s=r["pricing_time"], columns=r["n_cols"], ng_enlargements=r["ng_aug"],
            root_gap_pct=100 * (r["bp_value"] - r["root_lp"]) / r["bp_value"],
            pb_gap_to_bp_pct=100 * (r["pb_value"] - r["bp_value"]) / r["bp_value"],
            heur_pbox_plan_pbox=e["heur_pbox"]["pbox"], heur_saa_plan_pbox=sa["pbox"], heur_wass_plan_pbox=e["heur_wass"]["pbox"],
            bp_plan_pbox=bpv["pbox"], bp_vs_saa_pbox_pct=100 * (bpv["pbox"] - sa["pbox"]) / sa["pbox"],
            bp_vs_best_heur_pbox_pct=100 * (bpv["pbox"] - best_h) / best_h,
            pb_vs_saa_pbox_pct=100 * (e["price_and_branch"]["pbox"] - sa["pbox"]) / sa["pbox"],
            saa_plan_true=sa["true"], bp_plan_true=bpv["true"], bp_vs_saa_true_pct=100 * (bpv["true"] - sa["true"]) / sa["true"],
            saa_plan_saa=sa["saa"], bp_plan_saa=bpv["saa"], bp_plan_indep=bpv["indep_pbox"],
            pbox_to_true_pct=100 * (bpv["pbox"] - bpv["true"]) / bpv["true"],
            same_plan_as_saa=sorted(map(sorted, r["plans"]["branch_and_price"])) == sorted(map(sorted, r["plans"]["heur_saa"])),
        ))
    if rows:
        atomic_csv(RES / "bp_metro.csv", rows)
        atomic_csv(RES / "summary_bp.csv", rows)
    grows = []
    for city in CITIES:
        p = RES / f"bp_game_{city}.csv"
        if p.exists():
            grows.append(pd.read_csv(p).iloc[0].to_dict())
    if grows:
        g = pd.DataFrame(grows)
        keep = ["city", "welfare", "pb_welfare", "social_cost", "pb_social_cost", "deliveries", "pb_deliveries", "served_share",
                "pb_served_share", "vehicles", "pb_vehicles", "vehicle_hours", "pb_vehicle_hours", "routing_cost", "pb_routing_cost",
                "phi", "pb_phi", "max_regret", "pb_max_regret", "converged", "pb_converged", "calls", "pb_calls", "time_s", "pb_time_s",
                "bp_calls", "bp_optimal", "bp_timeouts", "bp_nodes", "bp_max_gap", "bp_total_time", "bp_time_limit"]
        g = g[[c for c in keep if c in g.columns]].copy()
        g["welfare_change"] = g.welfare - g.pb_welfare
        g["welfare_change_pct"] = 100 * g.welfare_change / g.pb_welfare.abs()
        g["runtime_ratio"] = g.time_s / g.pb_time_s
        atomic_csv(RES / "summary_bp_game.csv", g.to_dict("records"))
    if rows:
        _figure(pd.DataFrame(rows))
    print(pd.DataFrame(rows).T if rows else "no metro results yet")


def _figure(df: pd.DataFrame) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = {"NewDelhi": "New Delhi", "BuenosAires": "Buenos Aires", "NewYork": "New York", "Bombay": "Mumbai"}
    lab = [names.get(c, c) for c in df.city]
    x = np.arange(len(df))
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.0))
    w = 0.27
    root = 100 * (df.branch_and_price - df.root_lp) / df.branch_and_price
    pb = 100 * (df.price_and_branch - df.branch_and_price) / df.branch_and_price
    gap = 100 * df.gap_abs / df.branch_and_price.abs()
    ax[0].bar(x - w, root, w, color="#6b7a8f", label="root LP bound to B&P value")
    ax[0].bar(x, pb, w, color="#c1666b", label="price-and-branch above B&P value")
    ax[0].bar(x + w, gap, w, color="#2f7d6d", label="remaining B&P gap")
    ax[0].set_xticks(x, lab, rotation=40, ha="right")
    ax[0].set_ylabel("percent of B&P value")
    ax[0].set_title("Gaps")
    ax[0].legend(frameon=False, fontsize=8)
    ax[1].bar(x - w / 2, df.root_time_s, w, color="#6b7a8f", label="root column generation")
    ax[1].bar(x + w / 2, df.time_s, w, color="#2f7d6d", label="full branch-and-price")
    for i, s in enumerate(df.status):
        if s != "optimal":
            ax[1].text(x[i] + w / 2, df.time_s.iloc[i], "limit", ha="center", va="bottom", fontsize=8, color="#c1666b")
    ax[1].set_yscale("log")
    ax[1].set_xticks(x, lab, rotation=40, ha="right")
    ax[1].set_ylabel("seconds (log)")
    ax[1].set_title("Time")
    ax[1].legend(frameon=False, fontsize=8)
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "bp_gap.png", dpi=160)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("verify")
    a.add_argument("--seeds", type=int, nargs=2, default=[0, 400])
    a.add_argument("--force", action="store_true")
    a = sub.add_parser("metro")
    a.add_argument("cities", nargs="+")
    a.add_argument("--tl", type=float, default=1800.0)
    a.add_argument("--nodes", type=int, default=10**7)
    a.add_argument("--ng", type=int, default=8)
    a.add_argument("--force", action="store_true")
    a = sub.add_parser("game")
    a.add_argument("cities", nargs="+")
    a.add_argument("--tl", type=float, default=20.0)
    a.add_argument("--seed", type=int, default=0)
    a.add_argument("--force", action="store_true")
    sub.add_parser("summary")
    ns = ap.parse_args()
    if ns.cmd == "verify":
        verify(*ns.seeds, force=ns.force)
    elif ns.cmd == "metro":
        for c in ns.cities:
            metro(c, ns.tl, ns.nodes, ns.ng, ns.force)
    elif ns.cmd == "game":
        for c in ns.cities:
            game(c, ns.tl, ns.seed, force=ns.force)
    else:
        summary()


if __name__ == "__main__":
    main()
