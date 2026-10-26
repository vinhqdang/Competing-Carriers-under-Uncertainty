"""Why probability boxes: out-of-sample comparison of ambiguity criteria (SAA, Wasserstein, CVaR, p-box) and the game
re-run with other carrier criteria.  Everything is resumable; files are written atomically; one CPU core.

  python experiments/run_ambiguity.py validate                 planner vs exact branch-and-price (results/ambiguity_validation.csv)
  python experiments/run_ambiguity.py oracle                   oracle plans on every test law (results/ambiguity_oracle.csv)
  python experiments/run_ambiguity.py run [--regime base|heavy] [--draws 20] [--ns 10 20 30 60] [--cities ...]
  python experiments/run_ambiguity.py game [CITY ...]          E1 / E3 with SAA and Wasserstein carriers (results/ambiguity_game_*.csv)
  python experiments/run_ambiguity.py summary                  tables (results/ambiguity_*.csv, summary) and figures/ambiguity_*.png

Design: docs/EXPERIMENTS.md, section "Why probability boxes".
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
RES = ROOT / "results"
FIG = ROOT / "figures"
PARTS = RES / "ambiguity_parts"
for _d in (RES, FIG, PARTS):
    _d.mkdir(exist_ok=True)

from ccu import ambiguity as A  # noqa: E402

SEED = 20261026
REGIMES = {"base": 0, "heavy": 1}
LAW_NAMES = {"base": ["true", "shift20", "shift40", "heavy"], "heavy": ["heavy"]}
N_TRAIN_MAX = 60


def atomic_csv(path: Path, df: pd.DataFrame) -> None:
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    df.to_csv(tmp, index=False, float_format="%.8g")
    os.replace(tmp, path)


def progress(line: str) -> None:
    with open(RES / "PROGRESS_ambiguity.md", "a") as fh:
        fh.write(f"- {time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")


def test_laws(M: A.Metro, regime: str) -> dict:
    """Held-out days of each test law (the instance's own 20000 true-law days; the heavy law has 20000 own days)."""
    ci = A.CITIES.index(M.name)
    laws = {}
    for nm in LAW_NAMES[regime]:
        if nm == "true":
            laws[nm] = A.TestLaw(nm, M.true)
        elif nm == "shift20":
            laws[nm] = A.TestLaw(nm, M.true, 0.2)
        elif nm == "shift40":
            laws[nm] = A.TestLaw(nm, M.true, 0.4)
        elif nm == "heavy":
            laws[nm] = A.TestLaw(nm, M.sample(np.random.default_rng([SEED, 99, ci]), 20000, "heavy"))
    return laws


# ---------------------------------------------------------------------------------------------------------------
# validate: planner against the exact branch-and-price of the BRL metro study
# ---------------------------------------------------------------------------------------------------------------


def validate() -> None:
    out = RES / "ambiguity_validation.csv"
    rows = []
    for city in A.CITIES:
        M = A.load_metro(city)
        d = json.loads((RES / f"bp_metro_{city}.json").read_text())
        w, Q = A.pbox_levels(M.own_days, 0.05, M.xmax)
        crit = A.make_pbox_ud(M.loss, w, Q, "pbox_ud_95")
        pl = A.Planner(M)
        t0 = time.perf_counter()
        sol, v = pl.plan(crit, np.random.default_rng(0))
        dt = time.perf_counter() - t0
        sol_ls, v_ls = A.Planner(M).search(crit, np.random.default_rng(0))
        saa = A.make_saa(M.loss, M.own_days)
        plS = A.Planner(M)
        solS, vS = plS.plan(saa, np.random.default_rng(0))
        rows.append(dict(city=city, bp_status=d["status"], bp_value=d["bp_value"], planner_value=v, gap_pct=100 * (v / d["bp_value"] - 1),
                         search_only_value=v_ls, search_only_gap_pct=100 * (v_ls / d["bp_value"] - 1), planner_time_s=dt,
                         bp_time_s=d["time"], saa_value=vS, saa_study_heuristic=d["eval"]["heur_saa"]["saa"]))
        print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    atomic_csv(out, df)
    progress(f"validate: planner vs exact B&P on 9 instances, max gap {df.gap_pct.max():.4f}%, optimal in {(df.gap_pct.abs() < 1e-7).sum()}/9")


# ---------------------------------------------------------------------------------------------------------------
# oracle plans
# ---------------------------------------------------------------------------------------------------------------


def oracle(cities) -> None:
    out = RES / "ambiguity_oracle.csv"
    rows = [] if not out.exists() else pd.read_csv(out).to_dict("records")
    done = {(r["city"], r["law"]) for r in rows}
    for city in cities:
        M = A.load_metro(city)
        laws = test_laws(M, "base")
        for ln, law in laws.items():
            if (city, ln) in done:
                continue
            t0 = time.perf_counter()
            Xs = law.Z[:5000] + law.shift
            pl = A.Planner(M)
            crit = A.make_saa(M.loss, Xs, "oracle")
            sol, v = pl.plan(crit, np.random.default_rng(SEED), starts=6, ils=40, nseed=8)
            row = dict(city=city, law=ln, plan=";".join("-".join(map(str, r)) for r in sol), n_routes=len(sol), time=time.perf_counter() - t0)
            for k, x in A.plan_metrics(M, pl, sol, law).items():
                row[k] = x
            rows.append(row)
            atomic_csv(out, pd.DataFrame(rows))
            print(city, ln, round(row["exp"], 4), f"{row['time']:.0f}s", flush=True)
    progress(f"oracle plans done ({len(rows)} rows)")


# ---------------------------------------------------------------------------------------------------------------
# main experiment
# ---------------------------------------------------------------------------------------------------------------


def part_path(regime: str, city: str) -> Path:
    return PARTS / f"plans_{regime}_{city}.csv"


def run(regime: str, cities, ns, draws, d0: int = 0) -> None:
    Ms = {c: A.load_metro(c) for c in cities}
    laws = {c: test_laws(Ms[c], regime) for c in cities}
    rows = {c: ([] if not part_path(regime, c).exists() else pd.read_csv(part_path(regime, c)).to_dict("records")) for c in cities}
    done = {c: {(int(r["n"]), int(r["draw"])) for r in rows[c]} for c in cities}
    t00 = time.time()
    for k in range(d0, draws):
        for c in cities:
            M = Ms[c]
            ci = A.CITIES.index(c)
            todo = [n for n in ns if (n, k) not in done[c]]
            if not todo:
                continue
            days_all = M.sample(np.random.default_rng([SEED, ci, REGIMES[regime], k]), N_TRAIN_MAX, "base" if regime == "base" else "heavy")
            for n in todo:
                t0 = time.perf_counter()
                rng = np.random.default_rng([SEED, ci, REGIMES[regime], k, n])
                blk = A.run_block(M, laws[c], days_all[:n], rng)
                for r in blk:
                    r.update(city=c, regime=regime, n=n, draw=k)
                rows[c].extend(blk)
                done[c].add((n, k))
                atomic_csv(part_path(regime, c), pd.DataFrame(rows[c]))
                print(f"{regime} draw {k} {c} n={n}: {time.perf_counter() - t0:.1f}s (elapsed {(time.time() - t00) / 60:.1f} min)", flush=True)
        progress(f"run {regime}: draw {k} complete for {len(cities)} cities, elapsed {(time.time() - t00) / 60:.1f} min this call")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["validate", "oracle", "run", "game", "summary", "pipeline"])
    ap.add_argument("rest", nargs="*")
    ap.add_argument("--regime", default="base", choices=list(REGIMES))
    ap.add_argument("--draws", type=int, default=20)
    ap.add_argument("--draw0", type=int, default=0)
    ap.add_argument("--ns", type=int, nargs="*", default=[10, 20, 30, 60])
    ap.add_argument("--cities", nargs="*", default=A.CITIES)
    a, extra = ap.parse_known_args()
    if a.cmd == "validate":
        validate()
    elif a.cmd == "oracle":
        oracle(a.cities)
    elif a.cmd == "run":
        run(a.regime, a.cities, a.ns, a.draws, a.draw0)
    elif a.cmd == "pipeline":  # everything of the metro study, resumable
        validate() if not (RES / "ambiguity_validation.csv").exists() else None
        oracle(a.cities)
        run("base", a.cities, a.ns, a.draws, a.draw0)
        run("heavy", a.cities, [20, 60], a.draws, a.draw0)
        progress("pipeline (validate, oracle, base, heavy) finished")
    elif a.cmd == "game":
        from run_ambiguity_game import main as gmain  # noqa: WPS433

        gmain(a.rest + extra)
    elif a.cmd == "summary":
        from run_ambiguity_summary import main as smain  # noqa: WPS433

        smain()


if __name__ == "__main__":
    main()
