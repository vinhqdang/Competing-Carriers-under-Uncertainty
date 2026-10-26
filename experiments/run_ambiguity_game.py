"""E1 / E3 of the game with other carrier criteria (SAA, Wasserstein ball) on London, Buenos Aires and New Delhi.

  python experiments/run_ambiguity.py game [CITY ...] [--seeds 0 1 2]

Per (city, seed, criterion): the unpriced ZMC equilibrium (E1), two further equilibria (best-response dynamics from the empty
profile and from full service) and the social-cost optimum of the same carriers (E3).  Criteria: "pbox" (the paper's model, exact
branch-and-price oracle as in the published E1/E3 runs), "saa", "wass_th" (theory radius at the 30 observed days) and "wass_e0.5".
Results: results/ambiguity_game_<city>.csv (one row per criterion, seed and profile kind).  Resumable.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
from common import RES, scalars, solve_ne, write_csv, zb, zmc  # noqa: E402

GAME_CITIES = ["London", "BuenosAires", "NewDelhi"]
CRITERIA = {"pbox": dict(criterion="pbox"), "saa": dict(criterion="saa"), "wass_th": dict(criterion="wass", eps=None),
            "wass_e0.5": dict(criterion="wass", eps=0.5)}


def true_scalars(ev: dict) -> dict:
    return {k: float(ev[k]) for k in ("routing_cost_true", "welfare_true", "social_cost_true")}


def one(city: str, seed: int, name: str) -> list[dict]:
    kw = CRITERIA[name]
    t0 = time.perf_counter()
    g = zb.build_city_game(city, n_cust=22, seed=seed, **kw)
    if kw["criterion"] == "pbox":
        g.bp_time, g.bp_retry = 20.0, 120.0
    eps_used = g.carriers[0].pool.eps if hasattr(g.carriers[0].pool, "eps") else 0.0
    rows = []

    def add(kind, prof, extra=None):
        ev = g.evaluate(prof)
        r = dict(city=city, seed=seed, criterion=name, kind=kind, eps=eps_used, N=g.N, Z=g.Z, **scalars(ev), **true_scalars(ev))
        r["vehicles"] = int(ev["vehicles"])
        r.update(extra or {})
        rows.append(r)
        return r

    o = solve_ne(g, rounds=8, certify="fresh")
    prof_ne = o["profile"]
    add("NE_zmc", prof_ne, dict(max_regret=o["row"]["max_regret"], converged=o["row"]["converged"], calls=o["row"]["calls"],
                                phi=o["row"]["phi"], oracle=o["row"]["oracle"]))
    starts = {"NE_br_empty": None,
              "NE_full_service": [g.oracle(i, -1e3 * np.ones(g.d), rho=1.0, count=False) for i in range(g.N)]}
    for kind, init in starts.items():
        r = zmc.run_br(g, init=init)
        reg = g.regrets(r["profile"], count=False)
        add(kind, r["profile"], dict(max_regret=float(reg.max()), converged=r["converged"], calls=r["calls"], phi=g.potential(r["profile"])))
    so = g.so_variant(False)
    cg = zmc.run_cg(so, iters=40)
    add("SO_main", cg["profile"], dict(converged=cg["converged"], calls=cg["calls"], phi=so.potential(cg["profile"]),
                                       cg_last_gap=cg["hist"][-1][1]))
    for r in rows:
        r["time_s"] = time.perf_counter() - t0
    return rows


def main(argv):
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("cities", nargs="*", default=GAME_CITIES)
    ap.add_argument("--seeds", type=int, nargs="*", default=[0, 1, 2])
    ap.add_argument("--criteria", nargs="*", default=list(CRITERIA))
    a = ap.parse_args(argv)
    for city in a.cities:
        path = RES / f"ambiguity_game_{city}.csv"
        rows = pd.read_csv(path).to_dict("records") if path.exists() else []
        done = {(int(r["seed"]), r["criterion"]) for r in rows}
        for seed in a.seeds:
            for name in a.criteria:
                if (seed, name) in done:
                    continue
                t0 = time.perf_counter()
                new = one(city, seed, name)
                rows.extend(new)
                write_csv(path, rows)
                ne = new[0]
                print(f"{city} seed {seed} {name}: served {ne['served_share']:.3f} welfare {ne['welfare']:.1f} true {ne['welfare_true']:.1f} "
                      f"regret {ne['max_regret']:.2g} {time.perf_counter() - t0:.0f}s", flush=True)
                with open(RES / "PROGRESS_ambiguity.md", "a") as fh:
                    fh.write(f"- {time.strftime('%Y-%m-%d %H:%M:%S')} game {city} seed {seed} {name} done ({time.perf_counter() - t0:.0f}s)\n")
