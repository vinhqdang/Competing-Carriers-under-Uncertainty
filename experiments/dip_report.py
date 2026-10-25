"""Markdown tables of the DIP experiments (printed; pasted into theory/new_algorithm_C/results.md and docs/EXPERIMENTS.md).

Usage: python experiments/dip_report.py
"""
import numpy as np
import pandas as pd

from common import RES

ORDER = ["London", "BuenosAires", "NewDelhi", "Bombay", "Paris", "Berlin", "Cairo", "Moscow", "NewYork"]


def md(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, float):
                cells.append("n/a" if not np.isfinite(v) else (f"{v:.3g}" if abs(v) < 1e4 else f"{v:.0f}"))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main():
    d = pd.read_csv(RES / "summary_dip.csv")
    d["order"] = d.city.map({c: k for k, c in enumerate(ORDER)})
    d = d.sort_values(["order", "seed"])
    d["grid_gain_usd"] = d.grid_sc0 - d.grid_sc_best
    d["dip_gain_usd"] = d.grid_sc0 - d.dip_sc
    d["W_dip"] = -d.dip_sc
    d["W_grid"] = -d.grid_sc_best
    d["W_SO_E3"] = -d.e3_so_sc
    d["PoA_dip"] = d.e3_so_sc / d.dip_sc
    d["PoA_grid"] = d.e3_so_sc / d.grid_sc_best
    d["PoA_unpriced"] = d.e3_so_sc / d.grid_sc0
    t = d[["city", "seed", "grid_oracle", "grid_points", "dip_status", "dip_rounds", "grid_gain_usd", "dip_gain_usd", "dip_gain_share",
           "dip1_gain_share", "dip_calls", "dip1_calls", "grid_calls", "dip_calls_share", "dip_calls_share_63", "dip_time_s", "grid_time_s",
           "W_dip", "W_grid", "PoA_unpriced", "PoA_grid", "PoA_dip", "verify_max_regret_fresh"]].copy()
    print("## per city and seed\n")
    print(md(t))
    t2 = d[["city", "seed", "fam_status", "fam_gain_share", "fam_s_over_fee", "fam_theta", "sel_same", "sel_gain_share", "dip_s_over_fee",
            "dip_t_max", "dip_revenue", "dip_served_share", "credal0.2_regret", "credal0.8_regret", "credal0.8_sc", "credal0.8_unpriced_sc",
            "credal0.8_s_over_fee"]]
    print("\n## variants, instruments, credal\n")
    print(md(t2))
    a = d.groupby("city", sort=False).agg(seeds=("seed", "size"), gain_share_mean=("dip_gain_share", "mean"),
                                          gain_share_min=("dip_gain_share", "min"), calls_share_mean=("dip_calls_share", "mean"),
                                          calls_share_max=("dip_calls_share", "max"), calls_share63_mean=("dip_calls_share_63", "mean"),
                                          time_share_mean=("dip_time_share", "mean"), all_exact=("dip_status", lambda s: bool((s == "exact").all())),
                                          PoA_dip_mean=("PoA_dip", "mean"), PoA_grid_mean=("PoA_grid", "mean"))
    print("\n## per city\n")
    print(md(a.reset_index()))
    full = d[d.city.isin(["London", "BuenosAires", "NewDelhi"])]
    print("\nfull-grid cities: gain share min %.3f mean %.3f; calls share max %.4f mean %.4f; all exact %s"
          % (full.dip_gain_share.min(), full.dip_gain_share.mean(), full.dip_calls_share.max(), full.dip_calls_share.mean(),
             (full.dip_status == "exact").all()))
    print("all: gain share min %.3f; calls share (vs 63-point grid estimate) max %.4f; all exact %s; n=%d"
          % (d.dip_gain_share.min(), d.dip_calls_share_63.max(), (d.dip_status == "exact").all(), len(d)))
    # tiny games
    tt = pd.read_csv(RES / "dip_tiny.csv")
    g = tt.sc_ne - tt.opt_zone
    m = g > 1e-7
    rows = []
    for (N, nc, gx), x in tt.groupby(["N", "n_cust", "gcx"]):
        gg = (x.sc_ne - x.opt_zone)
        mm = gg > 1e-7
        sh = lambda k: ((x.sc_ne - x[k]) / gg)[mm]
        rows.append(dict(N=N, n_cust=nc, congestion_x=gx, instances=len(x), with_gain=int(mm.sum()),
                         dip_exact=float((x.dip_status == "exact").mean()), dip_hits_opt=float((x.dip_sc <= x.opt_zone + 1e-7).mean()),
                         dip_share=float(sh("dip_sc").mean()) if mm.any() else np.nan,
                         dip1_share=float(sh("dip1_sc").mean()) if mm.any() else np.nan,
                         dipx_hits_opt=float((x.dipx_sc <= x.opt_zone + 1e-7).mean()),
                         grid_share=float(sh("grid_selected").mean()) if mm.any() else np.nan,
                         family_opt_share=float(sh("opt_family").mean()) if mm.any() else np.nan,
                         uniform_opt_share=float(sh("opt_uniform").mean()) if mm.any() else np.nan,
                         dip_calls=float(x.dip_calls.mean()), grid_calls=float(x.grid_calls.mean())))
    print("\n## tiny games\n")
    print(md(pd.DataFrame(rows)))
    sh = lambda k: ((tt.sc_ne - tt[k]) / g)[m]
    print("\ntiny all: n=%d with gain %d; dip share mean %.3f min %.3f; dip1 %.3f; grid %.3f; dipx hits opt %.3f; dip worst-NE share %.3f"
          % (len(tt), m.sum(), sh("dip_sc").mean(), sh("dip_sc").min(), sh("dip1_sc").mean(), sh("grid_selected").mean(),
             (tt.dipx_sc <= tt.opt_zone + 1e-7).mean(), sh("dip_worst_sc").mean()))


if __name__ == "__main__":
    main()
