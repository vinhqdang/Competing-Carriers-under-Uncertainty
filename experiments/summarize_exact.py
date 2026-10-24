"""Exact-oracle bookkeeping and the old-vs-new comparison of the exact re-run.

  results/summary_exact_oracle.csv    one row per experiment, city, seed: oracle calls solved by branch-and-price, calls proven optimal,
                                      retries (120 s), calls unproven after the retry, largest remaining gap (USD of the oracle objective),
                                      and the regret of the returned profiles under the independent (fresh-pool) exact oracle
  results/exact_vs_pb_comparison.csv  per city: old (price-and-branch, results/pb_old) vs new (exact) values of the headline quantities,
                                      mean over seeds 0-2 (the by-seed version is exact_vs_pb_comparison_by_seed.csv)
"""
import numpy as np
import pandas as pd

from common import RES, read_rows, rpath, zb

CITIES, SEEDS = zb.CITIES, (0, 1, 2)
PARTS = RES / "exact_parts"
OLD = RES / "pb_old"


def oracle_stats():
    rows = []

    def add(exp, c, s, d, cols=("bp_calls", "bp_optimal", "bp_retried", "bp_unproven", "bp_max_gap"), prefix="", extra=None):
        d = d[d.get("oracle", "exact") == "exact"] if "oracle" in d.columns else d.iloc[0:0]
        if d.empty:
            return
        r = dict(experiment=exp, city=c, seed=s, rows_exact=len(d))
        pre = prefix or "bp_"

        def col(k):  # bp_calls / bpfresh_calls etc.
            return pre + k

        for k in ("calls", "optimal", "retried", "unproven"):
            r["bp_" + k] = int(d[col(k)].fillna(0).sum()) if col(k) in d else 0
        r["bp_max_gap"] = float(d[col("max_gap")].max()) if col("max_gap") in d else 0.0
        r["bp_invalid_bound"] = int(d["bp_invalid_bound"].sum()) if "bp_invalid_bound" in d else 0
        r.update(extra or {})
        rows.append(r)

    for c in CITIES:
        for s in SEEDS:
            p = PARTS / f"E1_{c}_s{s}.csv"
            if p.exists():
                d = pd.read_csv(p)
                add("E1", c, s, d, extra=dict(max_regret_fresh=float(d.max_regret.max()), max_regret_lp_bound=float(d.max_regret_lp.max())))
            for exp in ("E2", "E3", "E4"):
                d = pd.DataFrame(read_rows(rpath(exp, c, s)))
                if d.empty:
                    continue
                ex = dict()
                if exp == "E3":
                    f = d[d.get("oracle", "exact") == "exact"]
                    ex["max_regret_fresh"] = float(f.max_regret_fresh.max()) if "max_regret_fresh" in f else np.nan
                    add("E3_fresh_verification", c, s, d, prefix="bpfresh_", extra=dict(max_regret_fresh=ex["max_regret_fresh"]))
                add(exp, c, s, d, extra=({"max_regret_pooled": float(d.max_regret.max())} if "max_regret" in d else None))
            d = pd.DataFrame(read_rows(rpath("E2cert", c, s)))
            if len(d):
                add("E2cert_fresh", c, s, d, extra=dict(max_regret_fresh=float(d.regret_fresh.max()), max_regret_lp_bound=float(d.regret_lp.max())))
    out = pd.DataFrame(rows)
    if len(out):
        out["frac_optimal"] = out.bp_optimal / out.bp_calls.where(out.bp_calls > 0)
        out.to_csv(RES / "summary_exact_oracle.csv", index=False, float_format="%.6g")
        tot = out.groupby("experiment")[["bp_calls", "bp_optimal", "bp_retried", "bp_unproven"]].sum()
        tot["frac_optimal"] = tot.bp_optimal / tot.bp_calls
        tot["max_gap_usd"] = out.groupby("experiment").bp_max_gap.max()
        print(tot.to_string())
    return out


def comparison():
    def ld(base, name):
        f = base / name
        return pd.read_csv(f) if f.exists() else pd.DataFrame()

    rows = []
    for tag, base in (("old", OLD), ("new", RES)):
        e1 = ld(base, "summary_E1.csv")  # means over seeds per city only; rebuild by seed from E1 files
        parts = []
        for c in CITIES:
            f = base / f"E1_{c}.csv"
            if f.exists():
                d = pd.read_csv(f)
                parts.append(d[d.scenario == "base"])
        b = pd.concat(parts) if parts else pd.DataFrame()
        b = b.assign(slowdown_pct=100 * b.mean_slowdown) if len(b) else b
        e2, e3, e4 = ld(base, "summary_E2_by_seed.csv"), ld(base, "summary_E3.csv"), ld(base, "summary_E4.csv")
        for c in CITIES:
            for s in SEEDS:
                r = dict(version=tag, city=c, seed=s)
                x = b[(b.city == c) & (b.seed == s)] if len(b) else b
                if len(x):
                    x = x.iloc[0]
                    r.update(E1_welfare=x.welfare, E1_served_share=x.served_share, E1_slowdown_pct=x.slowdown_pct, E1_vehicles=x.vehicles)
                if len(e2):
                    x = e2[(e2.city == c) & (e2.seed == s)]
                    if len(x):
                        x = x.iloc[0]
                        r.update(E2_gain_both_pct=x["both"], E2_gain_delivery_only_pct=x.delivery_only, E2_gain_congestion_only_pct=x.congestion_only,
                                 E2_share_delivery_alone=x.share_delivery_alone_raw, E2_best_s_over_fee_delivery=x.delivery_best_s_over_fee)
                if len(e3):
                    x = e3[(e3.city == c) & (e3.seed == s)]
                    if len(x):
                        x = x.iloc[0]
                        r.update(E3_PoA_zmc=x.PoA_zmc, E3_PoS=x.PoS, E3_PoA_worst=x.PoA, E3_priced_gap_pct=x.rel_gap_priced_pct,
                                 E3_unpriced_gap_pct=x.rel_gap_unpriced_pct, E3_W_SO=x.W_SO, E3_n_ne=x.n_ne_distinct)
                if len(e4):
                    for kind in ("pbox", "gamma"):
                        x = e4[(e4.city == c) & (e4.seed == s) & (e4.kind == kind)]
                        if len(x):
                            key = "eps" if kind == "pbox" else "delta"
                            x = x[x[key] == x[key].max()].iloc[0]
                            r[f"E4_{kind}_widest_d_deliveries_pct"] = x.d_deliveries_pct
                            r[f"E4_{kind}_widest_d_welfare_pct"] = x.d_welfare_pct
                rows.append(r)
    allr = pd.DataFrame(rows)
    num = [c for c in allr.columns if c not in ("version", "city", "seed")]
    old = allr[allr.version == "old"].set_index(["city", "seed"])[num]
    new = allr[allr.version == "new"].set_index(["city", "seed"])[num]
    by_seed = old.join(new, lsuffix="_old", rsuffix="_new").reset_index()
    by_seed = by_seed[[c for c in by_seed.columns if not (c.endswith("_new") and by_seed[c].isna().all())]]
    by_seed.to_csv(RES / "exact_vs_pb_comparison_by_seed.csv", index=False, float_format="%.6g")
    old = old.where(new.reindex(old.index).notna())  # same seeds on both sides: the old mean only over the seeds that were re-run
    om = old.groupby("city").mean().reindex(CITIES)
    nm = new.groupby("city").mean().reindex(CITIES)
    nseeds = new.notna().groupby("city").sum().reindex(CITIES)
    out = pd.DataFrame(index=CITIES)
    for c in num:
        out[c + "_old"] = om[c]
        out[c + "_new"] = nm[c]
    for c in ("E1_welfare", "E2_gain_both_pct", "E3_PoA_zmc", "E4_pbox_widest_d_deliveries_pct"):
        out["n_seeds_" + c.split("_")[0]] = nseeds[c]
    out.index.name = "city"
    out.reset_index().to_csv(RES / "exact_vs_pb_comparison.csv", index=False, float_format="%.6g")
    return out, by_seed


if __name__ == "__main__":
    oracle_stats()
    comparison()
