"""Exact-oracle (branch-and-price) re-run of E1 (base + sensitivity), one result file per city/seed, and the assembly of
the per-seed parts into the usual results/E1_<city>.csv.  E2/E3 (run_leader.py) and E4 (run_imprecision.py) are run through
the same switch (environment variables CCU_BP_TIME / CCU_BP_RETRY, read by build_city_game) by run_exact.sh.

  python experiments/run_exact.py e1 CITY SEED        results/exact_parts/E1_<city>_s<seed>.csv (+ zones/trace parts for seed 0)
  python experiments/run_exact.py e1sens CITY         results/exact_parts/E1sens_<city>.csv (resumable per scenario)
  python experiments/run_exact.py assemble [--keep-old-sens]   merge the parts into results/E1_<city>.csv, zones_<city>.csv, E1_trace_<city>.csv
All writes are atomic; finished parts are skipped.
"""
import os
import sys

os.environ.setdefault("CCU_BP_TIME", "20")
os.environ.setdefault("CCU_BP_RETRY", "120")

import numpy as np
import pandas as pd

from common import RES, read_rows, solve_ne, write_csv, zb

PARTS = RES / "exact_parts"
PARTS.mkdir(exist_ok=True)
NCUST, ROUNDS = 22, 8


def e1(city, seed):
    p = PARTS / f"E1_{city}_s{seed}.csv"
    if p.exists():
        print(city, seed, "E1 part exists", flush=True)
        return
    g = zb.build_city_game(city, n_cust=NCUST, seed=seed)
    o = solve_ne(g, rounds=ROUNDS, certify="fresh")
    row = dict(city=city, scenario="base", param="", level="base", value=np.nan, seed=seed, N=g.N, Z=g.Z, d_eff=g.meta["d_eff"],
               overlap=g.meta["overlap"], L=g.meta["L"], **o["row"])
    if seed == 0:
        ev = o["eval"]
        z = pd.DataFrame(dict(zone=np.arange(g.Z), q=ev["q_z"], X=ev["X_z"], price=ev["price_z"], slowdown=ev["slow_z"], access=ev["access_z"]))
        z.to_csv(PARTS / f"zones_{city}.csv", index=False, float_format="%.5g")
        write_csv(PARTS / f"E1_trace_{city}.csv", [dict(city=city, **t) for t in o["result"]["trace"]])
    write_csv(p, [row])  # last: its existence marks the part as finished
    print(city, "E1 seed", seed, {k: round(v, 3) for k, v in o["row"].items() if isinstance(v, float)}, flush=True)


def e1sens(city):
    p = PARTS / f"E1sens_{city}.csv"
    rows = read_rows(p)
    done = {(r["param"], r["level"]) for r in rows}
    ranges = zb.load_ranges()
    name = zb.WIDE_NAME.get(city, city)
    for par in zb.WEAK_PARAMS:
        lo, base, hi = ranges[par][name]
        for level, val in (("low", lo), ("high", hi)):
            if abs(val - base) < 1e-12 or (par, level) in done:
                continue
            g = zb.build_city_game(city, n_cust=NCUST, seed=0, overrides={par: float(val)})
            o = solve_ne(g, rounds=ROUNDS, certify="oracle")
            rows.append(dict(city=city, scenario="sens", param=par, level=level, value=val, seed=0, N=g.N, Z=g.Z, d_eff=g.meta["d_eff"],
                             overlap=g.meta["overlap"], L=g.meta["L"], **o["row"]))
            write_csv(p, rows)
            print(city, par, level, round(o["row"]["served_share"], 3), flush=True)
    if not p.exists():
        write_csv(p, [])
    (PARTS / f"E1sens_{city}.done").write_text("done\n")


def assemble(keep_old_sens):
    for city in zb.CITIES:
        base = [pd.read_csv(PARTS / f"E1_{city}_s{s}.csv") for s in (0, 1, 2) if (PARTS / f"E1_{city}_s{s}.csv").exists()]
        if len(base) < 3:
            print(city, "E1 incomplete, not assembled", flush=True)
            continue
        parts = base
        sp = PARTS / f"E1sens_{city}.csv"
        if (PARTS / f"E1sens_{city}.done").exists() and sp.stat().st_size > 5:
            parts.append(pd.read_csv(sp))
        elif keep_old_sens:  # price-and-branch sensitivity rows, flagged
            old = pd.read_csv(RES / "pb_old" / f"E1_{city}.csv")
            old = old[old.scenario == "sens"].copy()
            old["oracle"] = "pb"
            parts.append(old)
        d = pd.concat(parts, ignore_index=True)
        d.to_csv(RES / f"E1_{city}.csv.tmp", index=False, float_format="%.6g")
        os.replace(RES / f"E1_{city}.csv.tmp", RES / f"E1_{city}.csv")
        for nm in ("zones", "E1_trace"):
            f = PARTS / f"{nm}_{city}.csv"
            if f.exists():
                tmp = RES / f"{nm}_{city}.csv.tmp"
                tmp.write_bytes(f.read_bytes())
                os.replace(tmp, RES / f"{nm}_{city}.csv")
        print(city, "assembled", len(d), "rows", flush=True)


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "e1":
        e1(sys.argv[2], int(sys.argv[3]))
    elif c == "e1sens":
        e1sens(sys.argv[2])
    elif c == "assemble":
        assemble("--keep-old-sens" in sys.argv)
