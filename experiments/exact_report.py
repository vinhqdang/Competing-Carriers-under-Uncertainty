"""Markdown tables for the section 'Exact oracle re-run' of docs/EXPERIMENTS.md (reads results/exact_vs_pb_comparison*.csv,
results/summary_exact_oracle.csv, results/exact_parts/oldreg_*.csv).  Prints to stdout."""
import numpy as np
import pandas as pd

from common import RES, zb
from summarize import md

CITIES = zb.CITIES
NAME = {"NewDelhi": "New Delhi", "Bombay": "Mumbai", "BuenosAires": "Buenos Aires", "NewYork": "New York"}
f = lambda x: f"{x:.3g}" if np.isfinite(x) else "n/a"


def pair(d, col, fmt="{:.4g}"):
    return [("n/a" if not np.isfinite(a) else fmt.format(a)) + " -> " + ("n/a" if not np.isfinite(b) else fmt.format(b))
            for a, b in zip(d[col + "_old"], d[col + "_new"])]


def coverage():
    from common import read_rows, rpath
    rows = []
    for c in CITIES:
        r = dict(city=NAME.get(c, c))
        for sd in (0, 1, 2):
            e2 = pd.DataFrame(read_rows(rpath("E2", c, sd)))
            e3 = read_rows(rpath("E3", c, sd))
            e4 = pd.DataFrame(read_rows(rpath("E4", c, sd)))
            p1 = (RES / "exact_parts" / f"E1_{c}_s{sd}.csv").exists()
            a = "x" if p1 else "."
            if len(e2) == 63:
                b = f"{int((e2.get('oracle', 'exact') == 'exact').sum())}/63"
            else:
                b = f"partial {len(e2)}" if len(e2) else "."
            cc = "x" if len(e3) == 10 else "."
            if len(e4) == 12:
                d_ = f"{int((e4.get('oracle', 'exact') == 'exact').sum())}/12"
            else:
                d_ = "."
            r[f"s{sd}: E1 / E2 exact pts / E3 / E4 exact rows"] = f"{a} / {b} / {cc} / {d_}"
        rows.append(r)
    print("### Coverage of the exact re-run (E2: grid points evaluated with the exact oracle, the others keep price-and-branch rows flagged `oracle = pb`; E4: widths)\n" + md(pd.DataFrame(rows)) + "\n")


def main():
    coverage()
    d = pd.read_csv(RES / "exact_vs_pb_comparison.csv").set_index("city").reindex(CITIES)
    names = [NAME.get(c, c) for c in CITIES]
    t1 = pd.DataFrame(dict(city=names, welfare=pair(d, "E1_welfare", "{:.1f}"), served_share=pair(d, "E1_served_share", "{:.3f}"),
                           slowdown_pct=pair(d, "E1_slowdown_pct", "{:.2f}")))
    print("### E1 (mean over seeds 0-2; price-and-branch -> exact)\n" + md(t1) + "\n")
    t2 = pd.DataFrame(dict(city=names, both=pair(d, "E2_gain_both_pct", "{:.2f}"), delivery_only=pair(d, "E2_gain_delivery_only_pct", "{:.2f}"),
                           congestion_only=pair(d, "E2_gain_congestion_only_pct", "{:.2f}"), share_delivery_alone=pair(d, "E2_share_delivery_alone", "{:.2f}")))
    print("### E2 best leader gain (% of |SC|, main objective, mean over the seeds available) and share captured by delivery-only\n" + md(t2) + "\n")
    t3 = pd.DataFrame(dict(city=names, PoA_zmc=pair(d, "E3_PoA_zmc", "{:.3f}"), PoS=pair(d, "E3_PoS", "{:.3f}"), PoA_worst=pair(d, "E3_PoA_worst", "{:.3f}"),
                           priced_gap_pct=pair(d, "E3_priced_gap_pct", "{:.2f}"), unpriced_gap_pct=pair(d, "E3_unpriced_gap_pct", "{:.2f}")))
    print("### E3 (mean over seeds)\n" + md(t3) + "\n")
    t4 = pd.DataFrame(dict(city=names, pbox_deliveries=pair(d, "E4_pbox_widest_d_deliveries_pct", "{:.1f}"), pbox_welfare=pair(d, "E4_pbox_widest_d_welfare_pct", "{:.1f}"),
                           gamma_deliveries=pair(d, "E4_gamma_widest_d_deliveries_pct", "{:.1f}")))
    print("### E4 widest width vs width 0 (% change)\n" + md(t4) + "\n")
    s = pd.read_csv(RES / "summary_exact_oracle.csv")
    g = s.groupby(["experiment"])[["bp_calls", "bp_optimal", "bp_retried", "bp_unproven"]].sum()
    g["proven_share"] = g.bp_optimal / g.bp_calls
    g["max_remaining_gap_usd"] = s.groupby("experiment").bp_max_gap.max()
    print("### Oracle calls\n" + md(g.reset_index()) + "\n")
    c = s.groupby("city")[["bp_calls", "bp_optimal", "bp_unproven"]].sum().reindex(CITIES)
    c["proven_share"] = c.bp_optimal / c.bp_calls
    c["max_gap_usd"] = s.groupby("city").bp_max_gap.max().reindex(CITIES)
    print("### Oracle calls by city\n" + md(c.reset_index()) + "\n")
    import glob
    o = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(str(RES / "exact_parts" / "oldreg_*.csv")))])
    oc = o.groupby("city").agg(seeds=("seed", "count"), seeds_not_exact_eq=("n_carriers_with_regret", lambda x: int((x > 0).sum())),
                               max_regret_usd=("regret_exact_max", "max")).reindex(CITIES).reset_index()
    print("### Regret of the old price-and-branch equilibria under the exact oracle\n" + md(oc) + "\n")


if __name__ == "__main__":
    main()
