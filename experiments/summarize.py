"""Aggregate the per-city result files into results/summary_*.csv and results/tables.md (markdown for the docs)."""
import glob

import numpy as np
import pandas as pd

from common import RES, zb

CITIES = zb.CITIES


def load(prefix, cities=CITIES):
    fs = [RES / f"{prefix}_{c}.csv" for c in cities if (RES / f"{prefix}_{c}.csv").exists()]
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else pd.DataFrame()


def md(df, floatfmt="{:.3g}"):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(floatfmt.format(v) if isinstance(v, (float, np.floating)) else str(v) for v in r) + " |")
    return "\n".join(out)


def main():
    T = []
    # ------------------------------------------------ E1
    e1 = load("E1")
    if len(e1):
        base = e1[e1.scenario == "base"]
        g = base.groupby("city")
        s = g.agg(N=("N", "first"), Z=("Z", "first"), d_eff=("d_eff", "mean"), served_share=("served_share", "mean"),
                  served_sd=("served_share", "std"), deliveries=("deliveries", "mean"), vehicles=("vehicles", "mean"),
                  vehicle_hours=("vehicle_hours", "mean"), mean_price=("mean_price", "mean"),
                  slowdown_pct=("mean_slowdown", lambda x: 100 * x.mean()), profit_total=("profit_total", "mean"),
                  welfare=("welfare", "mean"), welfare_sd=("welfare", "std"), calls=("calls", "mean"),
                  max_regret=("max_regret", "max"), max_regret_lp=("max_regret_lp", "max"), eta_rel=("eta_rel", "mean"),
                  conv=("converged", "mean")).reindex([c for c in CITIES if c in g.groups]).reset_index()
        s.to_csv(RES / "summary_E1.csv", index=False, float_format="%.6g")
        T.append("## E1 base (mean over 3 seeds)\n" + md(s))
        sens = e1[e1.scenario == "sens"].copy()
        if len(sens):
            b0 = base[base.seed == 0].set_index("city")
            sens["d_served_pp"] = 100 * (sens.served_share.values - b0.loc[sens.city, "served_share"].values)
            sens["d_welfare_pct"] = 100 * (sens.welfare.values / b0.loc[sens.city, "welfare"].values - 1)
            sens["d_slowdown_pct"] = 100 * (sens.mean_slowdown.values / b0.loc[sens.city, "mean_slowdown"].values - 1)
            sens[["city", "param", "level", "value", "N", "served_share", "welfare", "mean_slowdown", "d_served_pp",
                  "d_welfare_pct", "d_slowdown_pct", "calls", "converged", "max_regret"]].to_csv(
                RES / "summary_E1_sensitivity.csv", index=False, float_format="%.6g")
            piv = sens.pivot_table(index="city", columns="param", values="d_welfare_pct", aggfunc=lambda x: f"{x.min():.0f}..{x.max():.0f}")
            T.append("## E1 sensitivity: change of welfare (%) over low/high of each weak parameter\n" + md(piv.reset_index()))
            piv2 = sens.pivot_table(index="city", columns="param", values="d_served_pp", aggfunc=lambda x: f"{x.min():.0f}..{x.max():.0f}")
            T.append("## E1 sensitivity: change of served share (pp)\n" + md(piv2.reset_index()))
    # ------------------------------------------------ E2
    e2 = load("E2")
    if len(e2):
        rows = []
        for c, d in e2.groupby("city"):
            none = d[d.config == "none"].iloc[0]
            for obj, W in (("main", "welfare"), ("broad", "social_cost_broad")):
                col = "social_cost" if obj == "main" else "social_cost_broad"
                for cfg in ("none", "congestion_only", "delivery_only", "both"):
                    cand = d[d.config.isin([cfg, "none"])]
                    b = cand.loc[cand[col].idxmin()]
                    gain = none[col] - b[col]
                    rows.append(dict(city=c, objective=obj, config=cfg, theta=b.theta, s_over_fee=b.sfrac,
                                     social_cost=b.social_cost, social_cost_broad=b.social_cost_broad,
                                     gain=gain, gain_pct_of_abs=100 * gain / max(abs(none[col]), 1e-9),
                                     profit=b.profit_total, revenue=b.revenue, served_share=b.served_share,
                                     slowdown_pct=100 * b.mean_slowdown, gini_access=b.gini_access,
                                     gini_price=b.gini_price, calls=b.calls))
        s = pd.DataFrame(rows)
        s.to_csv(RES / "summary_E2.csv", index=False, float_format="%.6g")
        for obj in ("main", "broad"):
            p = s[s.objective == obj].pivot(index="city", columns="config", values="gain_pct_of_abs")[["none", "congestion_only", "delivery_only", "both"]]
            p = p.reindex([c for c in CITIES if c in p.index]).reset_index()
            T.append(f"## E2 gain of the leader's best charge vs no charge, objective={obj} (percent of |SC|)\n" + md(p))
        sb = s[(s.objective == "main") & (s.config == "both")][["city", "theta", "s_over_fee", "gain_pct_of_abs", "profit", "revenue", "served_share", "slowdown_pct", "gini_access", "gini_price"]]
        T.append("## E2 best point with both instruments (main objective)\n" + md(sb))
        s2 = s[(s.objective == "broad") & (s.config == "both")][["city", "theta", "s_over_fee", "gain_pct_of_abs", "profit", "revenue", "served_share", "slowdown_pct", "gini_access", "gini_price"]]
        T.append("## E2 best point with both instruments (broad objective incl. background delay)\n" + md(s2))
    # ------------------------------------------------ E3
    e3 = load("E3")
    if len(e3):
        rows = []
        for c, d in e3.groupby("city"):
            d = d.set_index("kind")
            so = d.loc["SO_main"]
            ne = d[d.index.str.startswith("NE_") & ~d.index.str.contains("priced")]
            wne = ne.welfare
            r = dict(city=c, W_SO=so.welfare, W_SO_bound=-so.phi_relaxed, W_NE_zmc=d.loc["NE_zmc"].welfare,
                     W_NE_best=wne.max(), W_NE_worst=wne.min(), n_ne_distinct=int(1 + ne.distinct.fillna(False).sum()),
                     W_priced=d.loc["NE_priced_main"].welfare if "NE_priced_main" in d.index else np.nan)
            for k in ("zmc", "best", "worst", "priced"):
                w = r[f"W_NE_{k}"] if k != "priced" else r["W_priced"]
                r[f"PoA_{k}" if k != "best" else "PoS"] = r["W_SO"] / w if w > 0 else np.nan
            r["PoA"] = r.pop("PoA_worst")
            r["rel_gap_unpriced_pct"] = 100 * (r["W_SO"] - r["W_NE_zmc"]) / abs(r["W_SO"])
            r["rel_gap_priced_pct"] = 100 * (r["W_SO"] - r["W_priced"]) / abs(r["W_SO"])
            sb = d.loc["SO_broad"]
            r["Wb_SO"] = sb.welfare - sb.bg_delay_cost
            r["Wb_NE"] = d.loc["NE_zmc"].welfare - d.loc["NE_zmc"].bg_delay_cost
            r["Wb_priced"] = d.loc["NE_priced_broad"].welfare - d.loc["NE_priced_broad"].bg_delay_cost
            r["gap_broad_unpriced_usd"] = r["Wb_SO"] - r["Wb_NE"]
            r["gap_broad_priced_usd"] = r["Wb_SO"] - r["Wb_priced"]
            r["gap_broad_unpriced_pct_of_W"] = 100 * r["gap_broad_unpriced_usd"] / abs(r["W_NE_zmc"])
            r["gap_broad_priced_pct_of_W"] = 100 * r["gap_broad_priced_usd"] / abs(r["W_NE_zmc"])
            rows.append(r)
        s = pd.DataFrame(rows).set_index("city").reindex([c for c in CITIES if c in set(e3.city)]).reset_index()
        s.to_csv(RES / "summary_E3.csv", index=False, float_format="%.6g")
        T.append("## E3 price of anarchy / stability (welfare ratios; SO = convexified-CG + rounding, upper bound W_SO_bound)\n" + md(s))
    # ------------------------------------------------ E4
    e4 = load("E4")
    if len(e4):
        rows = []
        for (c, kind), d in e4.groupby(["city", "kind"]):
            key = "eps" if kind == "pbox" else "delta"
            d = d.sort_values(key)
            r0 = d.iloc[0]
            for _, r in d.iterrows():
                rows.append(dict(city=c, kind=kind, eps=r.eps, delta=r.delta, L=r.L, served_share=r.served_share,
                                 d_deliveries_pct=100 * (r.deliveries / max(r0.deliveries, 1e-9) - 1),
                                 d_vehicle_hours_pct=100 * (r.vehicle_hours / max(r0.vehicle_hours, 1e-9) - 1),
                                 slowdown_pct=100 * r.mean_slowdown, welfare=r.welfare,
                                 d_welfare_pct=100 * (r.welfare / r0.welfare - 1), routing_cost=r.routing_cost,
                                 converged=r.converged, max_regret=r.max_regret, calls=r.calls))
        s = pd.DataFrame(rows)
        s.to_csv(RES / "summary_E4.csv", index=False, float_format="%.6g")
        last = s[s.kind == "pbox"].sort_values("eps").groupby("city").tail(1)
        last_g = s[s.kind == "gamma"].sort_values("delta").groupby("city").tail(1)
        T.append("## E4 widest p-box vs eps=0 (change in %)\n" + md(last[["city", "eps", "L", "served_share", "d_deliveries_pct", "d_vehicle_hours_pct", "d_welfare_pct", "routing_cost", "converged", "max_regret"]]))
        T.append("## E4 widest Gamma-maximin surcharge delta vs delta=0\n" + md(last_g[["city", "delta", "served_share", "d_deliveries_pct", "d_vehicle_hours_pct", "slowdown_pct", "d_welfare_pct", "converged", "max_regret"]]))
    # ------------------------------------------------ verification / E5 / E6
    vm = load("verify_methods")
    if len(vm):
        vm.to_csv(RES / "summary_verify_methods.csv", index=False, float_format="%.6g")
        p = vm.pivot(index="city", columns="method", values="gap_rel")
        pc = vm.pivot(index="city", columns="method", values="calls")
        meta = vm[vm.method == "ZMC8"].set_index("city")[["N", "Z", "d_eff"]]
        out = meta.join(pc.add_prefix("calls_")).join(p.add_prefix("gap_")).reindex([c for c in CITIES if c in meta.index]).reset_index()
        out["zmc_calls_per_carrier"] = out["calls_ZMC8"] / out["N"]
        out.to_csv(RES / "summary_E5_calls_vs_Z.csv", index=False, float_format="%.6g")
        T.append("## Verification (c) and E5: calls and relative potential gap (vs convexified CG optimum)\n" + md(out))
    vt = RES / "verify_tiny.csv"
    if vt.exists():
        d = pd.read_csv(vt)
        rows = []
        for m in ("ZMC6", "BR", "FW6", "CG"):
            rows.append(dict(method=m, instances=len(d), mean_calls=d[f"{m}_calls"].mean(), is_ne_enum=d[f"{m}_is_ne_enum"].mean(),
                             max_regret_fresh=d[f"{m}_regret_fresh"].max(), hits_global=d[f"{m}_hits_global"].mean(),
                             hits_best_ne=d[f"{m}_hits_best_ne"].mean(),
                             mean_excess_over_global=(d[f"{m}_phi"] - d.global_min).mean()))
        s = pd.DataFrame(rows)
        s.to_csv(RES / "summary_verify_tiny.csv", index=False, float_format="%.6g")
        T.append("## Verification (a) tiny games, exhaustive enumeration\n" + md(s))
    e6 = load("E6")
    if len(e6):
        z = e6[e6.kind == "zmc_round"]
        b = e6[e6.kind == "bisect_bracket"]
        rows = []
        for c, d in z.groupby("city"):
            rows.append(dict(city=c, max_abs_identity_resid=d.identity_resid.abs().max(), thm2_bound_holds_frac=d.thm2_bound_holds.mean(),
                             inverted_brackets_max=d.n_inverted.max(), n_act=d.n_act.iloc[0], width_after_8=d.width_max.iloc[-1],
                             width_med_after_8=d.width_med.iloc[-1]))
        s = pd.DataFrame(rows)
        bb = b.groupby("city").apply(lambda d: pd.Series(dict(frac_within_T4=d[d["round"] == 4].frac_within.iloc[0],
                                                              frac_within_T8=d[d["round"] == 8].frac_within.iloc[0],
                                                              err_max_T8=d[d["round"] == 8].err_max.iloc[0],
                                                              bound_T8=d[d["round"] == 8].bound.iloc[0],
                                                              inverted_T12=d[d["round"] == 12].n_inverted.iloc[0])), include_groups=False).reset_index()
        s = s.merge(bb, on="city")
        s.to_csv(RES / "summary_E6.csv", index=False, float_format="%.6g")
        T.append("## E6 theory checks (clearing identity, Theorem 2 bound, brackets)\n" + md(s))
    (RES / "tables.md").write_text("\n\n".join(T) + "\n")
    print("\n\n".join(T))


if __name__ == "__main__":
    main()
