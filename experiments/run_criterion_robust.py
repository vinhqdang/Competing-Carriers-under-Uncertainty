"""Robustness of the game and policy results to the carriers' ambiguity criterion.

Usage
  python experiments/run_criterion_robust.py run [--cities C ...] [--seeds 0 1 2] [--criteria saa wass_cv wass_th pbox]
                                                 [--stages ne so dip grid imprec]
  python experiments/run_criterion_robust.py summary      (results/criterion_*.csv, summary_criterion.csv, figures)

Criteria (the carriers' route cost; the same 30 observed days as the published runs)
  pbox     the paper's DKW p-box with unknown dependence.  Here with the price-and-branch oracle (no CCU_BP_TIME), flagged
           oracle = 'pb'; the published exact-oracle numbers (E1/E2/E3, DIP) are the reference for the model cost.
  saa      expected cost on the 30 observed days.
  wass_cv  type-1 Wasserstein ball, radius chosen by 3-fold cross-validation, one radius per carrier (grid EPS_GRID, score = held-out SAA
           cost of the carrier's full-service plan).  If every carrier selects 0 the game is the SAA game and the SAA result is re-used.
  wass_th  radius sigma sqrt(2 ln(1/0.05)/n) of `ccu.ambiguity.wass_radius`.
SAA and Wasserstein carriers use `ccu.ambiguity_game.HeurPool`: a heuristic carrier oracle without a certificate; every equilibrium
is verified against an independent fresh pool of the same oracle, not against an exact one.

Per (city, seed, criterion) a unit is stored in results/criterion_parts/<city>_s<seed>_<criterion>.json (atomic writes, every stage
resumable).  Stages
  ne      unpriced equilibria (ZMC with fresh-pool certification, best-response dynamics from the empty profile and from full
          service); served share, welfare under the carriers' cost (model) and under the true law, slowdown.
  so      social optimum of the same carriers (column generation + rounding + polish, as in E3); PoA, PoS.
  dip     the leader's charges by dual implementation pricing (src/ccu/dip.py); the priced profile is verified under a fresh pool.
  grid    coarse leader grid (about 17 points) on London, Buenos Aires, New Delhi: (0,0), delivery-only axis, congestion-only axis,
          two-instrument points around the best delivery-only subsidy and DIP's subsidy.  Same family as E2:
          u_z = sfrac * fee + theta * gc_z * X_z^NE (X^NE = unpriced equilibrium).
  imprec  Gamma-maximin width delta in {0.2, 0.8} of the rivals' aggregate (as E4), unpriced equilibrium (focus cities).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("NUMBA_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FIG, RES, solve_ne, write_csv, zb, zmc  # noqa: E402
from ccu import ambiguity as amb  # noqa: E402
from ccu import dip  # noqa: E402
from ccu.ambiguity_game import HeurPool  # noqa: E402

PARTS = RES / "criterion_parts"
CITIES = ["London", "BuenosAires", "NewDelhi", "Bombay", "Paris", "Berlin", "Moscow", "NewYork", "Cairo"]
FOCUS = ["London", "BuenosAires", "NewDelhi"]
LOW_SERVICE = set(FOCUS)
CRITERIA = ["saa", "wass_th", "wass_cv", "pbox"]
EPS_GRID = [0.0, 0.05, 0.25, 1.0]  # coarse subset of the metro study's grid (0, .02, .05, .1, .25, .5, 1): one pool solve costs 5-10 s
STAGES = ["ne", "so", "dip", "grid", "imprec"]
THETAS_AX = [1.0, 4.0, 16.0]
SFRAC_AX = [-0.6, -0.4, -0.2, -0.1, -0.05, 0.2]
SFRAC_GRID = [-0.6, -0.4, -0.2, -0.1, -0.05, 0.0, 0.1, 0.2, 0.4, 0.6]
DELTAS = [0.2, 0.8]
NCUST = 22


# ------------------------------------------------------------------------------------------------ io
def jdump(path: Path, obj) -> None:
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(obj, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else float(x)))
    os.replace(tmp, path)


def part_path(city, seed, crit) -> Path:
    return PARTS / f"{city}_s{seed}_{crit}.json"


def load_part(city, seed, crit) -> dict:
    p = part_path(city, seed, crit)
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def log(msg: str) -> None:
    line = f"- {time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(RES / "PROGRESS_criterion_robust.md", "a") as fh:
        fh.write(line + "\n")


# ------------------------------------------------------------------------------------------------ games
def cv_radii(g, seed: int, folds: int = 3) -> tuple[list[float], list[list[float]]]:
    """One cross-validated Wasserstein radius per carrier.  Score of a radius: plan the carrier's full-service routes on the
    training folds with the radius, evaluate the plan by the SAA expected cost on the held-out fold (ties: smaller radius)."""
    eps_sel, scores = [], []
    for i, cr in enumerate(g.carriers):
        days = cr.pool.days
        n = len(days)
        rng = np.random.default_rng([seed, i, 31])
        perm = rng.permutation(n)
        parts = np.array_split(perm, folds)
        kap = np.concatenate([[0.0], -1e3 * np.ones(cr.inst.n)])  # full service
        sc = np.zeros(len(EPS_GRID))
        for te in parts:
            tr = np.setdiff1d(perm, te)
            test = amb.make_saa(cr.inst.loss, days[te])
            for ie, e in enumerate(EPS_GRID):
                pool = HeurPool(cr.inst, days[tr], "wass", eps=e, ng_size=8)
                res = pool.solve(kap, integer=True, mip_gap=5e-3, mip_time=4.0)
                tot = 0.0
                for r in res.routes:
                    tau, svc = pool._vec(tuple(r))
                    tot += float(test.fn(tau, svc))
                sc[ie] += tot * len(te)
        sc /= n
        eps_sel.append(float(EPS_GRID[int(np.argmin(sc - 1e-9 * np.arange(len(sc))))]))
        scores.append([float(v) for v in sc])
    return eps_sel, scores


def build(city: str, seed: int, crit: str, eps_cv=None):
    if crit == "pbox":
        os.environ.pop("CCU_BP_TIME", None)
        return zb.build_city_game(city, n_cust=NCUST, seed=seed, criterion="pbox")
    if crit == "saa":
        return zb.build_city_game(city, n_cust=NCUST, seed=seed, criterion="saa")
    if crit == "wass_th":
        return zb.build_city_game(city, n_cust=NCUST, seed=seed, criterion="wass", eps=None)
    if crit == "wass_cv":
        g = zb.build_city_game(city, n_cust=NCUST, seed=seed, criterion="saa")
        if eps_cv is None:
            eps_cv, _ = cv_radii(g, seed)
        for cr, e in zip(g.carriers, eps_cv):
            if e > 0:
                cr.pool = HeurPool(cr.inst, cr.pool.days, "wass", eps=float(e), ng_size=8)
        g.meta["criterion"] = "wass_cv"
        g._cache = {}
        return g
    raise ValueError(crit)


TRUE = ("routing_cost_true", "welfare_true", "social_cost_true")
KEEP = ["deliveries", "demand", "served_share", "vehicles", "vehicle_hours", "mean_price", "mean_slowdown", "max_slowdown",
        "profit_total", "charges", "social_cost", "welfare", "consumer_surplus", "congestion_cost", "routing_cost", "gini_access"]


def metrics(ev: dict) -> dict:
    out = {k: float(ev[k]) for k in KEEP}
    out["vehicles"] = int(ev["vehicles"])
    out.update({k: float(ev[k]) for k in TRUE})
    return out


def routes_of(prof):
    return [[list(map(int, r)) for r in p.routes] for p in prof]


def plans_from(g, routes):
    return [g.plan_from_routes(i, [tuple(r) for r in rs]) for i, rs in enumerate(routes)]


def stat(g, st0):
    return dict(calls=g.calls)


# ------------------------------------------------------------------------------------------------ stages
def stage_ne(g, P):
    t0 = time.perf_counter()
    o = solve_ne(g, rounds=8, certify="fresh")
    ev = o["eval"]
    ne = dict(metrics(ev), max_regret=float(o["row"]["max_regret"]), converged=bool(o["row"]["converged"]), calls=int(o["row"]["calls"]),
              X=ev["X_z"], q=ev["q_z"], lam=o["result"]["lam"], routes=routes_of(o["profile"]), kind="NE_zmc")
    eqs = [ne]
    starts = {"NE_br_empty": None,
              "NE_full_service": [g.oracle(i, -1e3 * np.ones(g.d), rho=1.0, count=False) for i in range(g.N)]}
    for kind, init in starts.items():
        r = zmc.run_br(g, init=init)
        reg = g.regrets(r["profile"], count=False)
        e = metrics(g.evaluate(r["profile"]))
        eqs.append(dict(e, max_regret=float(reg.max()), converged=bool(r["converged"]), calls=int(r["calls"]), kind=kind))
    P["ne"] = dict(eqs=eqs, time_s=time.perf_counter() - t0)


def stage_so(g, P):
    t0 = time.perf_counter()
    so = g.so_variant(False)
    cg = zmc.run_cg(so, iters=40)
    ev = g.evaluate(cg["profile"])
    P["so"] = dict(metrics(ev), calls=int(cg["calls"]), converged=bool(cg["converged"]), cg_last_gap=float(cg["hist"][-1][1]),
                   time_s=time.perf_counter() - t0, routes=routes_of(cg["profile"]))


def stage_dip(g, P, city, seed, crit):
    t0 = time.perf_counter()
    c0 = g.calls
    lg: list = []
    o = dip.dip(g, so_iters=40, log=lg)
    prof = plans_from(g, routes_of(o["profile"]))  # re-priced under the returned charges (set on g by dip)
    ev = g.evaluate(prof)
    t_dip = time.perf_counter() - t0
    # independent verification: fresh elementary pool of the same oracle, no shared columns
    u = np.array(o["u"])
    dip._set_u(g, u)
    reg = g.regrets(prof, count=False)
    regf = g.regrets(prof, count=False, fresh=True)
    tgt = plans_from(g, routes_of(o["target"]))
    regt = g.regrets(tgt, count=False, fresh=True)
    # shape of the charges
    fee = g.meta["params"]["delivery_fee_usd"]
    act = dip.active_zones(g)
    D = dip.lots(g)
    nz = (D > 0).sum(0)
    x = np.where(act, fee / np.maximum(nz, 1), 0.0)[act]
    uu = u[act]
    slope = float((uu * x).sum() / (x * x).sum())
    corr = float(np.corrcoef(uu, x)[0, 1]) if len(uu) > 2 and np.std(uu) > 0 and np.std(x) > 0 else float("nan")
    Qn = np.array(o["Qstar"])[act]
    P["dip"] = dict(metrics(ev), status=o["status"], rounds=int(o["rounds"]), n_cuts=int(o["n_cuts"]), converged=bool(o["converged"]),
                    sc_model=float(o["sc"]), sc_target=float(o["sc_target"]), calls=int(o["calls"]), calls_so=int(o["calls_so"]),
                    calls_implement=int(o["calls_implement"]), time_s=t_dip, loss_bound=float(o["loss_bound"]),
                    s=float(o["s"]), s_over_fee=float(o["s"] / fee), t_max=float(np.max(o["t"])),
                    u_mean_over_fee=float(uu.mean() / fee), u_q_weighted_over_fee=float((uu * Qn).sum() / max(Qn.sum(), 1e-12) / fee),
                    u_min_over_fee=float(uu.min() / fee), u_max_over_fee=float(uu.max() / fee), n_active=int(act.sum()),
                    slope_fee_over_nz=slope, corr_fee_over_nz=corr,
                    verify_regret_pooled=float(reg.max()), verify_regret_fresh=float(regf.max()), verify_target_fresh=float(regt.max()),
                    u=u, routes=routes_of(prof), target_routes=routes_of(o["target"]),
                    nz=nz.astype(int), fee=float(fee))
    g.set_charges()
    zones = pd.read_csv(zb.ROOT / "data/processed" / city / "zones.csv")
    ch = pd.DataFrame(dict(zone_id=zones.zone_id, active=act, n_z=nz, u=u, u_over_fee=u / fee, fee_over_nz=fee / np.maximum(nz, 1)))
    write_csv(RES / f"criterion_dip_charges_{city}_s{seed}_{crit}.csv", ch.to_dict("records"))


def stage_imprec(g, P):
    base = P["ne"]["eqs"][0]
    A = None
    prof = plans_from(g, base["routes"])
    A = sum(p.a for p in prof)
    pos = A[A > 1e-9]
    w = np.where(A > 1e-9, A, np.median(pos) if len(pos) else 1.0)
    lam = np.array(base["lam"])
    rows = []
    for de in DELTAS:
        g.set_charges(sur=de * g.M * w)
        o = solve_ne(g, rounds=6, lam0=lam, certify="oracle")
        rows.append(dict(metrics(o["eval"]), delta=de, max_regret=float(o["row"]["max_regret"]), calls=int(o["row"]["calls"])))
    g.set_charges()
    P["imprec"] = rows


def grid_points(P) -> list[tuple[float, float]]:
    """Deterministic list of the coarse-grid points, in evaluation order (the two-instrument points depend on earlier ones)."""
    pts = [(0.0, 0.0)] + [(0.0, s) for s in SFRAC_AX] + [(t, 0.0) for t in THETAS_AX]
    G = P.get("grid", {})
    fee = P["dip"]["fee"] if "dip" in P else None
    if not all(f"0.0|{s}" in G for s in SFRAC_AX):
        return pts
    base = P["ne"]["eqs"][0]["social_cost_true"]
    dl = {s: G[f"0.0|{s}"]["social_cost_true"] for s in SFRAC_AX}
    s_star = min(dl, key=lambda s: dl[s])
    sd = P["dip"]["s_over_fee"] if "dip" in P else s_star
    snap = min(SFRAC_GRID, key=lambda s: abs(s - sd))
    ss = []
    for s in (s_star, snap):
        if s != 0.0 and s not in ss:
            ss.append(s)
    if len(ss) < 2:  # second subsidy level: the next grid value towards zero (a milder subsidy)
        k = SFRAC_GRID.index(ss[0]) if ss else SFRAC_GRID.index(-0.2)
        ss.append(SFRAC_GRID[min(k + 1, len(SFRAC_GRID) - 1)] if SFRAC_GRID[min(k + 1, len(SFRAC_GRID) - 1)] != 0.0 else SFRAC_GRID[k - 1])
    return pts + [(t, s) for s in ss for t in THETAS_AX]


def stage_grid(g, P, path: Path, city, seed, crit):
    fee = g.meta["params"]["delivery_fee_usd"]
    Z = g.Z
    base = P["ne"]["eqs"][0]
    ext = g.gc * np.array(base["X"])
    lam0 = np.array(base["lam"])
    G = P.setdefault("grid", {})
    G.setdefault("0.0|0.0", dict(base, theta=0.0, sfrac=0.0, kind="NE_zmc"))
    t0 = time.perf_counter()
    while True:
        pts = grid_points(P)
        todo = [p for p in pts if f"{p[0]}|{p[1]}" not in G]
        if not todo:
            break
        th, sf = todo[0]
        toll = np.zeros(2 * Z)
        toll[:Z] = sf * fee
        toll[Z:] = th * ext
        g.set_charges(toll=toll)
        o = solve_ne(g, rounds=6, lam0=lam0, certify="oracle")
        G[f"{th}|{sf}"] = dict(metrics(o["eval"]), theta=th, sfrac=sf, max_regret=float(o["row"]["max_regret"]), calls=int(o["row"]["calls"]),
                               converged=bool(o["row"]["converged"]))
        g.set_charges()
        jdump(path, P)
        log(f"grid {city} s{seed} {crit} theta={th} sfrac={sf} sc_true={G[f'{th}|{sf}']['social_cost_true']:.2f} "
            f"served={G[f'{th}|{sf}']['served_share']:.3f} ({time.perf_counter() - t0:.0f}s)")
    # independent fresh-pool certification of the best two-instrument/any point (true-law objective)
    if "gridcert" not in P:
        best = min(G.values(), key=lambda r: r["social_cost_true"])
        th, sf = best["theta"], best["sfrac"]
        toll = np.zeros(2 * Z)
        toll[:Z] = sf * fee
        toll[Z:] = th * ext
        g.set_charges(toll=toll)
        o = solve_ne(g, rounds=6, lam0=lam0, certify="fresh")
        P["gridcert"] = dict(theta=th, sfrac=sf, max_regret_fresh=float(o["row"]["max_regret"]),
                             social_cost_true=float(o["eval"]["social_cost_true"]), social_cost=float(o["eval"]["social_cost"]))
        g.set_charges()
    P["grid_calls"] = int(sum(r["calls"] for k, r in G.items() if k != "0.0|0.0"))
    P["grid_n"] = len(G)
    jdump(path, P)


# ------------------------------------------------------------------------------------------------ driver
def run_unit(city, seed, crit, stages):
    path = part_path(city, seed, crit)
    P = load_part(city, seed, crit)
    need = [s for s in stages if (s in ("ne", "so", "dip", "imprec") and s not in P) or
            (s == "grid" and city in LOW_SERVICE and "gridcert" not in P)]
    if crit == "wass_cv" and "eps_cv" not in P and need:
        pass
    if not need:
        return
    t0 = time.perf_counter()
    if crit == "wass_cv":
        if "eps_cv" not in P:
            g0 = zb.build_city_game(city, n_cust=NCUST, seed=seed, criterion="saa")
            e, sc = cv_radii(g0, seed)
            P["eps_cv"], P["cv_scores"] = e, sc
            jdump(path, P)
            log(f"cv {city} s{seed}: radii {e}")
        if all(e == 0.0 for e in P["eps_cv"]):  # identical to the SAA game
            S = load_part(city, seed, "saa")
            if all(s in S for s in need if s != "grid") and ("grid" not in need or "gridcert" in S):
                P.update({k: v for k, v in S.items() if k not in ("eps_cv", "cv_scores")})
                P["same_as_saa"] = True
                jdump(path, P)
                return
            log(f"wass_cv {city} s{seed}: SAA unit not finished, deferred")
            return
        g = build(city, seed, crit, eps_cv=P["eps_cv"])
    else:
        g = build(city, seed, crit)
    for st in STAGES:
        if st not in stages:
            continue
        if st == "ne" and "ne" not in P:
            stage_ne(g, P)
        elif st == "so" and "so" not in P:
            stage_so(g, P)
        elif st == "dip" and "dip" not in P:
            stage_dip(g, P, city, seed, crit)
        elif st == "imprec" and "imprec" not in P and city in LOW_SERVICE and "ne" in P:
            stage_imprec(g, P)
        elif st == "grid" and city in LOW_SERVICE and "gridcert" not in P and "ne" in P and "dip" in P:
            stage_grid(g, P, path, city, seed, crit)
        else:
            continue
        jdump(path, P)
        e = P.get("ne", {}).get("eqs", [{}])[0]
        log(f"{city} s{seed} {crit} stage {st} done: served={e.get('served_share', float('nan')):.3f} "
            f"({time.perf_counter() - t0:.0f}s)")


def cmd_run(a):
    PARTS.mkdir(exist_ok=True)
    import fcntl
    lock = open(PARTS / ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another run_criterion_robust job holds the lock", flush=True)
        return
    # stage-major order: all cheap stages everywhere first, then the policy stages, then the grid
    waves = [(["ne", "so"], a.cities), (["dip"], a.cities), (["grid", "imprec"], [c for c in a.cities if c in LOW_SERVICE])]
    waves = [([s for s in ws if s in a.stages], cs) for ws, cs in waves]
    for crit in a.criteria:
        for ws, cs in waves:
            if not ws:
                continue
            for seed in a.seeds:
                for city in cs:
                    try:
                        run_unit(city, seed, crit, ws)
                    except Exception as e:  # keep the queue alive; the unit is retried on the next invocation
                        import traceback
                        traceback.print_exc()
                        log(f"ERROR {city} s{seed} {crit} {ws}: {type(e).__name__}: {e}")
    # a wass_cv unit deferred for lack of its SAA unit: second pass
    for ws, cs in waves:
        for seed in a.seeds:
            for city in cs:
                if "wass_cv" in a.criteria and ws:
                    run_unit(city, seed, "wass_cv", ws)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "summary"])
    ap.add_argument("--cities", nargs="*", default=CITIES)
    ap.add_argument("--seeds", type=int, nargs="*", default=[0, 1, 2])
    ap.add_argument("--criteria", nargs="*", default=CRITERIA)
    ap.add_argument("--stages", nargs="*", default=STAGES)
    a = ap.parse_args(argv)
    if a.cmd == "run":
        cmd_run(a)
    else:
        from criterion_summary import summarize
        summarize()


if __name__ == "__main__":
    main()
