"""E4: imprecision.  (i) p-box width: DKW confidence sweep (alpha) of the travel-time bands used by BRL;
(ii) credal width delta of the rivals' aggregates: Gamma-maximin surcharge delta * M_k * w_k (main.tex Lemma 3.6).

Usage:  python experiments/run_imprecision.py CITY [--ncust 22] [--seed 0]
Writes results/E4_<city>.csv (seed 0) or E4_<city>_s<seed>.csv (kind = 'pbox' or 'gamma').
Resumable: finished widths/deltas are read back and skipped, the file is rewritten atomically after every row.
Seed s changes depots, customer zones, sectors and the observed days.
"""
import argparse
import os

import numpy as np

from common import RES, read_rows, rpath, solve_ne, write_csv, zb  # noqa: E402  (common adds src to the path)
from ccu import brl  # noqa: E402

ALPHAS = [2.0, 0.5, 0.2, 0.05, 0.005, 1e-4]  # alpha >= 2: eps = 0 (empirical law, no band)
DELTAS = [0.0, 0.05, 0.1, 0.2, 0.4, 0.8]


# reduced exact run (heavy cities, CCU_E4_MODE=reduced): exact oracle for the widths below only, the other widths keep their
# price-and-branch rows from results/pb_old (column oracle = 'pb'; summarize.py and plot_results.py skip them)
RED_ALPHAS = [2.0, 0.05, 1e-4]
RED_DELTAS = [0.0, 0.2, 0.8]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("city")
    ap.add_argument("--ncust", type=int, default=22)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    path = rpath("E4", a.city, a.seed)
    rows = read_rows(path)
    reduced = os.environ.get("CCU_E4_MODE", "full") == "reduced" and bool(os.environ.get("CCU_BP_TIME"))
    if not reduced and any(r.get("oracle") == "pb" for r in rows):  # upgrade of a reduced run
        rows = [r for r in rows if r.get("oracle") != "pb"]
    if len(rows) == len(ALPHAS) + len(DELTAS):
        print(a.city, a.seed, "E4 already complete, skipping", flush=True)
        return
    done_p = {float(r["alpha"]) for r in rows if r["kind"] == "pbox"}
    done_g = {float(r["delta"]) for r in rows if r["kind"] == "gamma"}
    for al in ALPHAS:
        if al in done_p or (reduced and al not in RED_ALPHAS):
            continue
        g = zb.build_city_game(a.city, n_cust=a.ncust, seed=a.seed, alpha_dkw=al)
        o = solve_ne(g, rounds=8, certify="oracle")
        eps = brl.dkw_eps(g.meta["ndays"], al)
        rows.append(dict(city=a.city, seed=a.seed, kind="pbox", alpha=al, eps=eps, delta=0.0, N=g.N, Z=g.Z, L=g.meta["L"], **o["row"]))
        print(a.city, a.seed, "pbox", al, round(eps, 3), round(o["row"]["served_share"], 3), round(o["row"]["social_cost"], 1), flush=True)
        write_csv(path, rows)
    g = zb.build_city_game(a.city, n_cust=a.ncust, seed=a.seed)
    o0 = solve_ne(g, rounds=8, certify="oracle")
    A = sum(p.a for p in o0["profile"])
    pos = A[A > 1e-9]
    w = np.where(A > 1e-9, A, np.median(pos) if len(pos) else 1.0)  # weights: relative imprecision of the rival aggregate
    lam = o0["result"]["lam"]
    for de in DELTAS:
        if de in done_g or (reduced and de not in RED_DELTAS):
            continue
        g.set_charges(sur=de * g.M * w)
        o = o0 if de == 0 else solve_ne(g, rounds=6, lam0=lam, certify="oracle")
        lam = o["result"]["lam"]
        rows.append(dict(city=a.city, seed=a.seed, kind="gamma", alpha=0.05, eps=brl.dkw_eps(g.meta["ndays"], 0.05), delta=de, N=g.N,
                         Z=g.Z, L=g.meta["L"], **o["row"]))
        print(a.city, a.seed, "gamma", de, round(o["row"]["served_share"], 3), round(o["row"]["vehicle_hours"], 2), flush=True)
        write_csv(path, rows)
    if reduced:
        pb = read_rows(RES / "pb_old" / path.name)
        have = {(r["kind"], float(r["alpha"]) if r["kind"] == "pbox" else float(r["delta"])) for r in rows}
        for r in pb:
            if (r["kind"], float(r["alpha"]) if r["kind"] == "pbox" else float(r["delta"])) not in have:
                rows.append(dict(r, oracle="pb"))
        write_csv(path, rows)


if __name__ == "__main__":
    main()
