"""BRL benchmark on public instances and scale study.

  python experiments/run_brl_bench.py pub      [--tl 90] [--reps 2]     A: five criteria on Solomon / Augerat data
  python experiments/run_brl_bench.py polish   [--tl 15]                 A: local-search polish of every arm's plan (stronger baselines)
  python experiments/run_brl_bench.py labels   [--tl-cg 240]            B: root CG + label counts of the three dominance rules
  python experiments/run_brl_bench.py devices  [--tl-cg 200]            B: scale-up devices at the root
  python experiments/run_brl_bench.py bpscale  [--tl 1800]              B: full branch-and-price as the instance grows
  python experiments/run_brl_bench.py summary                           CSV files and figures

Every stage is resumable: one JSON per job in results/brl_bench/<stage>/, finished jobs are skipped (--force redoes).
One core: OMP/NUMBA threads are fixed to 1.  `--only SUBSTR` restricts a stage to job ids containing SUBSTR.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_v] = "1"

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import brl_bench_lib as L  # noqa: E402
from ccu import brl_variants as bv  # noqa: E402

ROOT = L.ROOT
RES = ROOT / "results"
JOBS = RES / "brl_bench"
FIG = ROOT / "figures"
for d in (RES, JOBS, FIG):
    d.mkdir(exist_ok=True)

CITIES = ["NewDelhi", "Cairo", "Moscow", "BuenosAires", "NewYork", "Bombay", "London", "Paris", "Berlin"]

# public instances of study A: (instance, reps)
PUB_SMALL = ["solomon25/R101", "solomon25/R105", "solomon25/RC101", "solomon25/RC105", "solomon25/C101",
             "augerat_A/A-n32-k5", "augerat_A/A-n34-k5"]
PUB_LARGE = ["solomon50/R101", "solomon50/RC101", "augerat_A/A-n45-k6"]
ARMS = ["brl", "det", "saa", "wass", "cvar"]
NS = [10, 30, 60]


def atomic_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(obj, default=float, indent=1))
    os.replace(tmp, path)


def progress(line: str) -> None:
    with open(RES / "PROGRESS_brl_bench.md", "a") as fh:
        fh.write(f"- {time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")


def run_jobs(stage: str, jobs, args) -> None:
    """jobs: list of (job id, callable returning a dict).  Skips finished ones."""
    todo = [(j, f) for j, f in jobs if (args.force or not (JOBS / stage / f"{j}.json").exists())
            and (not args.only or args.only in j)]
    progress(f"stage {stage}: {len(jobs) - len(todo)} of {len(jobs)} jobs already done, {len(todo)} to run")
    for k, (jid, fn) in enumerate(todo):
        t0 = time.time()
        try:
            out = fn()
        except Exception as e:  # keep the queue alive; the failure is recorded
            out = {"error": f"{type(e).__name__}: {e}"}
            progress(f"{stage}/{jid} FAILED {out['error']}")
        out["job"] = jid
        out["wall_job"] = time.time() - t0
        atomic_json(JOBS / stage / f"{jid}.json", out)
        print(f"[{stage} {k + 1}/{len(todo)}] {jid} {time.time() - t0:.0f}s {out.get('status', out.get('error', ''))}", flush=True)
        if (k + 1) % 5 == 0 or k == len(todo) - 1:
            progress(f"stage {stage}: {k + 1}/{len(todo)} jobs run in this call, last {jid} ({time.time() - t0:.0f}s)")


# ---------------------------------------------------------------------------------------------------------------
# stage pub
# ---------------------------------------------------------------------------------------------------------------


def pub_job(inst: str, N: int, rep: int, arm: str, tl: float):
    def fn():
        spec = L.public_spec(inst)
        train, test = L.make_days(spec, rep)
        crit = L.criteria_instances(spec, train[:N])
        vi = crit[arm]
        heur = 0 if arm == "brl" else 20
        r, b = bv.solve_variant(vi, mode="window" if arm == "brl" else "qv", time_limit=tl, heur_first=heur)
        out = dict(inst=inst, n=spec.n, N=N, rep=rep, arm=arm, tl=tl, L=int(vi.arcS.shape[2]) if arm != "brl" else int(vi.Qk.shape[1]),
                   status=r.status, value=r.value, lb=r.lb if r.bound_valid else None, bound_valid=bool(r.bound_valid),
                   proven=bool(r.status == "optimal" and r.bound_valid),
                   rel_gap=(r.rel_gap if (r.bound_valid and math.isfinite(r.value)) else None), nodes=r.nodes,
                   time=r.time, root_time=r.root_time, pricing_time=r.pricing_time, n_pricing=r.n_pricing, max_labels=r.max_labels,
                   created=b.created, ncmp=b.ncmp, n_cols=r.n_cols, ng_aug=r.ng_aug, routes=[list(x) for x in r.routes])
        out.update(L.evaluate_plan(spec, r.routes, test))
        out.update(L.plan_costs(crit, r.routes))
        return out
    return fn


def stage_pub(args):
    jobs = []
    combos = []
    for rep in range(args.reps):
        for inst in PUB_SMALL:
            combos.append((inst, rep))
    for inst in PUB_LARGE:
        combos.append((inst, 0))
    combos.sort(key=lambda t: t[1])  # all rep-0 cells first
    for inst, rep in combos:
        for N in NS:
            for arm in ARMS:
                jid = f"{inst.replace('/', '_')}_N{N}_r{rep}_{arm}"
                jobs.append((jid, pub_job(inst, N, rep, arm, args.tl)))
    run_jobs("pub", jobs, args)


def polish_job(inst: str, N: int, rep: int, arm: str, tl: float):
    """Local search (relocate / swap / 2-opt) under the criterion of `arm`, started from the best plan of any arm of the
    cell under that criterion.  The result is a stronger baseline than the pricing heuristic of the time-limited arms."""
    def fn():
        spec = L.public_spec(inst)
        train, test = L.make_days(spec, rep)
        crit = L.criteria_instances(spec, train[:N])
        starts = []
        for a in ARMS:
            p = JOBS / "pub" / f"{inst.replace('/', '_')}_N{N}_r{rep}_{a}.json"
            starts.append(json.loads(p.read_text())["routes"])
        vi = crit[arm]
        vals = [sum(vi.route_cost(tuple(r)) for r in rt) for rt in starts]
        k = int(np.argmin(vals))
        routes, val = L.local_search(vi, [tuple(r) for r in starts[k]], tlim=tl)
        out = dict(inst=inst, n=spec.n, N=N, rep=rep, arm=arm + "_ls", start_value=vals[k], value=val, status="polished",
                   routes=[list(x) for x in routes], tl=tl)
        out.update(L.evaluate_plan(spec, routes, test))
        out.update(L.plan_costs(crit, routes))
        return out
    return fn


def stage_polish(args):
    jobs = []
    for inst, rep in sorted({(i, r) for i in PUB_SMALL for r in range(args.reps)} | {(i, 0) for i in PUB_LARGE}, key=lambda t: t[1]):
        for N in NS:
            if not all((JOBS / "pub" / f"{inst.replace('/', '_')}_N{N}_r{rep}_{a}.json").exists() for a in ARMS):
                continue
            for arm in ARMS:
                jobs.append((f"{inst.replace('/', '_')}_N{N}_r{rep}_{arm}_ls", polish_job(inst, N, rep, arm, args.tl)))
    run_jobs("polish", jobs, args)


def shift_job(src: str, stem: str):
    """Evaluate a stored plan on days from a SHIFTED law (congestion excess x1.5, volatility x1.25): a stress test of what
    the plan does when the training days understate the future.  No re-solving."""
    def fn():
        d = json.loads((JOBS / src / f"{stem}.json").read_text())
        spec = L.public_spec(d["inst"])
        law = spec.law
        shifted = L.Law(1 + (law.m - 1) * 1.5, law.sc * 1.25, law.ss * 1.25, law.xmax)
        h = sum((i + 1) * ord(c) for i, c in enumerate(spec.name)) % 100_000
        test = shifted.draw(np.random.default_rng([h, d["rep"], 3]), 2000)
        ev = L.evaluate_plan(spec, [tuple(r) for r in d["routes"]], test)
        out = dict(inst=d["inst"], N=d["N"], rep=d["rep"], arm=d["arm"], src=src, status="shift")
        out.update({"shift_" + k: v for k, v in ev.items()})
        return out
    return fn


def stage_shift(args):
    jobs = []
    for src in ("pub", "polish"):
        for p in sorted((JOBS / src).glob("*.json")):
            jobs.append((f"{src}_{p.stem}", shift_job(src, p.stem)))
    run_jobs("shift", jobs, args)


# ---------------------------------------------------------------------------------------------------------------
# instances of the scale study
# ---------------------------------------------------------------------------------------------------------------

_cache: dict = {}


def scale_instance(name: str, n: int):
    """('metro/London', 40) or ('solomon100/R101', 100) -> (spec, p-box RoutingInstance)."""
    key = (name, n)
    if key in _cache:
        return _cache[key]
    if name.startswith("metro/"):
        spec, days, _ = L.metro_spec(name[6:], n)
        inst = brl_inst_from_metro(spec)
    else:
        spec = L.public_spec(name, None if name.startswith("solomon") else n)
        train, _ = L.make_days(spec, 0)
        inst = L.pbox_instance(spec, train[:60])
    _cache.clear()
    _cache[key] = (spec, inst)
    return spec, inst


def brl_inst_from_metro(spec):
    from ccu import brl
    return brl.RoutingInstance(spec.n, spec.tau, spec.svc, spec.dem, spec.cap, spec.meta["Qk"], spec.meta["w"], spec.loss)


SCALE_N = [22, 30, 40, 60, 80]
PUBLIC_SCALE = [("solomon25/R101", 25), ("solomon50/R101", 50), ("solomon100/R101", 100),
                ("solomon25/RC101", 25), ("solomon50/RC101", 50), ("solomon100/RC101", 100),
                ("solomon25/C101", 25), ("solomon50/C101", 50), ("solomon100/C101", 100),
                ("augerat_A/A-n32-k5", 31), ("augerat_A/A-n45-k6", 44), ("augerat_A/A-n60-k9", 59), ("augerat_A/A-n80-k10", 79)]


def scale_cells():
    cells = [(f"metro/{c}", n) for n in SCALE_N for c in CITIES] + PUBLIC_SCALE
    return sorted(cells, key=lambda t: (t[1], t[0]))


def jid_of(name, n, extra=""):
    return f"{name.replace('/', '_')}_n{n}{extra}"


# ---------------------------------------------------------------------------------------------------------------
# stage labels: root column generation (exact BRL, ng-8) and label counts of the three dominance rules
# ---------------------------------------------------------------------------------------------------------------


def labels_job(name: str, n: int, tl_cg: float, cap_cmp: float, cap_created: float):
    def fn():
        spec, inst = scale_instance(name, n)
        cg = bv.root_cg(inst, mode="window", ng_size=8, time_limit=tl_cg)
        duals = np.array(cg["duals"])
        ng = bv.ng_masks_py(inst, 8)
        out = dict(name=name, n=spec.n, L=int(inst.Qk.shape[1]), cap=spec.cap, mean_dem=float(spec.dem[1:].mean()),
                   cg_status=cg["status"], cg_iters=cg["iters"], cg_time=cg["time"], cg_price_time=cg["price_time"],
                   cg_lp=cg["lp"], cg_lb=cg["lb"], cg_cols=cg["cols"], cg_max_kept=cg["max_kept"], cg_created=cg["created"],
                   cg_overflow=cg["overflow"], tl_cg=tl_cg)
        for mode in ("window", "nowin", "qv"):
            b, cols, st = bv.price(inst, duals, mode=mode, ng=ng, max_cols=40, max_created=int(cap_created), max_cmp=int(cap_cmp))
            out.update({f"{mode}_best": b, f"{mode}_created": st["created"], f"{mode}_kept": st["kept"], f"{mode}_ncmp": st["ncmp"],
                        f"{mode}_time": st["time"], f"{mode}_overflow": st["overflow"]})
        out["status"] = cg["status"]
        return out
    return fn


def stage_labels(args):
    jobs = [(jid_of(nm, n), labels_job(nm, n, args.tl_cg, args.cap_cmp, args.cap_created)) for nm, n in scale_cells()]
    run_jobs("labels", jobs, args)


# ---------------------------------------------------------------------------------------------------------------
# stage devices: scale-up devices at the root
# ---------------------------------------------------------------------------------------------------------------

DEVICES = {
    "base_ng8": dict(ng_size=8),
    "ng4": dict(ng_size=4),
    "dssr2": dict(ng_size=2, dssr=True),
    "heur5": dict(ng_size=8, heur_first=5),
    "lbprune": dict(ng_size=8, lbprune=True),
    "combo": dict(ng_size=2, dssr=True, heur_first=5, lbprune=True),
}
DEVICE_CELLS = [("metro/London", 22), ("metro/London", 40), ("metro/NewYork", 30), ("metro/Cairo", 40), ("metro/Berlin", 30),
                ("metro/BuenosAires", 40), ("solomon25/R101", 25), ("solomon50/R101", 50), ("solomon25/RC101", 25),
                ("augerat_A/A-n45-k6", 44)]


def devices_job(name: str, n: int, cfg: str, tl_cg: float):
    def fn():
        spec, inst = scale_instance(name, n)
        cg = bv.root_cg(inst, mode="window", time_limit=tl_cg, **DEVICES[cfg])
        cg.pop("duals")
        cg.update(name=name, n=spec.n, cfg=cfg, tl_cg=tl_cg)
        return cg
    return fn


def stage_devices(args):
    jobs = [(jid_of(nm, n, f"_{c}"), devices_job(nm, n, c, args.tl_cg)) for nm, n in DEVICE_CELLS for c in DEVICES]
    run_jobs("devices", jobs, args)


# ---------------------------------------------------------------------------------------------------------------
# stage bpscale: full branch-and-price
# ---------------------------------------------------------------------------------------------------------------

BP_CONFIGS = {"exact": dict(ng_size=8), "devices": dict(ng_size=4, heur_first=5, lbprune=True)}
BP_CELLS = [("metro/London", n) for n in (30, 40, 60, 80)] + [("metro/NewYork", n) for n in (30, 40)] + \
    [("metro/Cairo", n) for n in (30, 40)] + [("metro/NewDelhi", 60)] + [("solomon25/R101", 25), ("augerat_A/A-n32-k5", 31), ("augerat_A/A-n60-k9", 59)]


def bp_job(name: str, n: int, cfg: str, tl: float):
    def fn():
        spec, inst = scale_instance(name, n)
        r, b = bv.solve_variant(inst, mode="window", time_limit=tl, **BP_CONFIGS[cfg])
        return dict(name=name, n=spec.n, cfg=cfg, tl=tl, status=r.status, value=r.value, lb=r.lb if r.bound_valid else None,
                    bound_valid=bool(r.bound_valid), rel_gap=r.rel_gap if (r.bound_valid and math.isfinite(r.value)) else None,
                    root_lp=r.root_lp, pb_value=r.pb_value, nodes=r.nodes, time=r.time, root_time=r.root_time,
                    pricing_time=r.pricing_time, heur_time=b.t_heur, n_pricing=r.n_pricing, n_exact=b.n_exact, n_heur=b.n_heur,
                    max_labels=r.max_labels, created=b.created, ng_aug=r.ng_aug, n_cols=r.n_cols, nodes_open=r.nodes_open,
                    routes=[list(x) for x in r.routes])
    return fn


def stage_bpscale(args):
    jobs = []
    for nm, n in sorted(BP_CELLS, key=lambda t: t[1]):
        for cfg in BP_CONFIGS:
            jobs.append((jid_of(nm, n, f"_{cfg}"), bp_job(nm, n, cfg, args.tl)))
    run_jobs("bpscale", jobs, args)


# ---------------------------------------------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------------------------------------------


def load(stage: str) -> pd.DataFrame:
    rows = []
    for p in sorted((JOBS / stage).glob("*.json")):
        d = json.loads(p.read_text())
        if "error" in d:
            continue
        d.pop("routes", None)
        d.pop("duals", None)
        rows.append(d)
    return pd.DataFrame(rows)


def summary(args):
    import summarize_brl_bench as S
    S.main()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["pub", "polish", "shift", "labels", "devices", "bpscale", "summary"])
    ap.add_argument("--tl", type=float, default=None)
    ap.add_argument("--tl-cg", type=float, default=None)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--cap-cmp", type=float, default=3e8)
    ap.add_argument("--cap-created", type=float, default=3e7)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    if args.stage == "pub":
        args.tl = 90.0 if args.tl is None else args.tl
        stage_pub(args)
    elif args.stage == "shift":
        stage_shift(args)
    elif args.stage == "polish":
        args.tl = 15.0 if args.tl is None else args.tl
        stage_polish(args)
    elif args.stage == "labels":
        args.tl_cg = 240.0 if args.tl_cg is None else args.tl_cg
        stage_labels(args)
    elif args.stage == "devices":
        args.tl_cg = 200.0 if args.tl_cg is None else args.tl_cg
        stage_devices(args)
    elif args.stage == "bpscale":
        args.tl = 1800.0 if args.tl is None else args.tl
        stage_bpscale(args)
    else:
        summary(args)


if __name__ == "__main__":
    main()
