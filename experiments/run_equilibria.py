"""E1 (unpriced Cournot-Nash equilibrium, base + sensitivity) and E5 data (oracle calls vs Z) for one city.

Usage:  python experiments/run_equilibria.py CITY [--seeds 0 1 2] [--ncust 22] [--rounds 8]
Writes results/E1_<city>.csv (rows: base seeds and low/high sensitivity of the five weakest parameters),
results/zones_<city>.csv (zone-level equilibrium, first seed) and results/E1_trace_<city>.csv (ZMC rounds).
"""
import argparse

import numpy as np
import pandas as pd

from common import RES, solve_ne, write_csv, zb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("city")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--ncust", type=int, default=22)
    ap.add_argument("--rounds", type=int, default=8)
    a = ap.parse_args()
    rows, traces = [], []
    ranges = zb.load_ranges()
    name = zb.WIDE_NAME.get(a.city, a.city)
    for seed in a.seeds:
        g = zb.build_city_game(a.city, n_cust=a.ncust, seed=seed)
        o = solve_ne(g, rounds=a.rounds, certify="fresh")
        row = dict(city=a.city, scenario="base", param="", level="base", value=np.nan, seed=seed, N=g.N, Z=g.Z,
                   d_eff=g.meta["d_eff"], overlap=g.meta["overlap"], L=g.meta["L"], **o["row"])
        rows.append(row)
        print(a.city, "base seed", seed, {k: round(v, 3) for k, v in o["row"].items() if isinstance(v, float)}, flush=True)
        if seed == a.seeds[0]:
            ev = o["eval"]
            z = pd.DataFrame(dict(zone=np.arange(g.Z), q=ev["q_z"], X=ev["X_z"], price=ev["price_z"], slowdown=ev["slow_z"],
                                  access=ev["access_z"]))
            z.to_csv(RES / f"zones_{a.city}.csv", index=False, float_format="%.5g")
            for t in o["result"]["trace"]:
                traces.append(dict(city=a.city, **t))
        write_csv(RES / f"E1_{a.city}.csv", rows)
    seed = a.seeds[0]
    for par in zb.WEAK_PARAMS:
        lo, base, hi = ranges[par][name]
        for level, val in (("low", lo), ("high", hi)):
            if abs(val - base) < 1e-12:
                continue
            g = zb.build_city_game(a.city, n_cust=a.ncust, seed=seed, overrides={par: float(val)})
            o = solve_ne(g, rounds=a.rounds, certify="oracle")
            rows.append(dict(city=a.city, scenario="sens", param=par, level=level, value=val, seed=seed, N=g.N, Z=g.Z,
                             d_eff=g.meta["d_eff"], overlap=g.meta["overlap"], L=g.meta["L"], **o["row"]))
            print(a.city, par, level, val, round(o["row"]["served_share"], 3), round(o["row"]["social_cost"], 1), flush=True)
            write_csv(RES / f"E1_{a.city}.csv", rows)
    write_csv(RES / f"E1_trace_{a.city}.csv", traces)


if __name__ == "__main__":
    main()
