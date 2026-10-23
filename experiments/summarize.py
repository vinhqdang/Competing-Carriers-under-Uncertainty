"""Aggregate the per-city result files into results/summary_*.csv and results/tables.md (markdown for the docs)."""
import glob

import numpy as np
import pandas as pd

from common import RES, zb

CITIES = zb.CITIES


def load(prefix, cities=CITIES, seeds=None):
    """all result files of one experiment: <prefix>_<city>.csv (seed 0) and <prefix>_<city>_s<k>.csv; adds a seed column.
    Only complete files (full grid / all kinds) are read, so a partial run never leaks into the tables."""
    full = {"E2": 63, "E3": 10, "E4": 12}
    out = []
    for c in cities:
        for f in [RES / f"{prefix}_{c}.csv"] + sorted(RES.glob(f"{prefix}_{c}_s[0-9]*.csv")):
            if not f.exists():
                continue
            d = pd.read_csv(f)
            if prefix in full and len(d) != full[prefix]:
                print("skipping incomplete", f.name, len(d))
                continue
            if "seed" not in d.columns:
                d["seed"] = int(f.stem.rsplit("_s", 1)[1]) if "_s" in f.stem.split(c)[-1] else 0
            if seeds is None or d.seed.iloc[0] in seeds:
                out.append(d)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def agg(df, by, cols):
    """mean / sd (ddof 1) / min / max over seeds of the columns `cols`, grouped by `by`; n = number of seeds"""
    g = df.groupby(by, sort=False)
    out = g.size().rename("n_seeds").to_frame()
    for c in cols:
        out[c + "_mean"] = g[c].mean()
        out[c + "_sd"] = g[c].std(ddof=1)
        out[c + "_min"] = g[c].min()
        out[c + "_max"] = g[c].max()
    return out.reset_index()


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
    cfgs = ["none", "congestion_only", "delivery_only", "both"]
    e2 = load("E2")
    if len(e2):
        rows = []
        for (c, sd), d in e2.groupby(["city", "seed"]):
            none = d[d.config == "none"].iloc[0]
            for obj in ("main", "broad"):
                col = "social_cost" if obj == "main" else "social_cost_broad"
                for cfg in cfgs:
                    cand = d[d.config.isin([cfg, "none"])]
                    b = cand.loc[cand[col].idxmin()]
                    gain = none[col] - b[col]
                    rows.append(dict(city=c, seed=sd, objective=obj, config=cfg, theta=b.theta, s_over_fee=b.sfrac,
                                     social_cost=b.social_cost, social_cost_broad=b.social_cost_broad,
                                     gain=gain, gain_pct_of_abs=100 * gain / max(abs(none[col]), 1e-9),
                                     profit=b.profit_total, revenue=b.revenue, served_share=b.served_share,
                                     slowdown_pct=100 * b.mean_slowdown, gini_access=b.gini_access,
                                     gini_price=b.gini_price, calls=b.calls, max_regret=d.max_regret.max(),
                                     all_converged=bool(d.converged.all())))
        s = pd.DataFrame(rows)
        s.to_csv(RES / "summary_E2.csv", index=False, float_format="%.6g")
        nseed = s.groupby("city").seed.nunique().min()
        # three-seed aggregate of the gains and of the share captured by the per-delivery instrument alone
        sm = s[s.objective == "main"].pivot(index=["city", "seed"], columns="config", values="gain_pct_of_abs").reset_index()
        sm["share_delivery_alone"] = np.where(sm["both"] > 0.5, sm["delivery_only"] / sm["both"].where(sm["both"] > 0), np.nan)
        sm["share_delivery_alone_raw"] = sm["delivery_only"] / sm["both"].where(sm["both"] > 1e-9)
        sb_ = s[(s.objective == "main") & (s.config == "delivery_only")].set_index(["city", "seed"])
        sm["delivery_best_s_over_fee"] = [sb_.loc[(c, k), "s_over_fee"] for c, k in zip(sm.city, sm.seed)]
        sm["delivery_best_is_subsidy"] = sm.delivery_best_s_over_fee < 0
        sm.to_csv(RES / "summary_E2_by_seed.csv", index=False, float_format="%.6g")
        a2 = agg(sm, "city", ["none", "congestion_only", "delivery_only", "both", "share_delivery_alone_raw"])
        a2 = a2.set_index("city").reindex([c for c in CITIES if c in set(a2.city)]).reset_index()
        a2.to_csv(RES / "summary_E2_agg.csv", index=False, float_format="%.6g")
        for obj in ("main", "broad"):
            d = s[s.objective == obj]
            p = d.pivot_table(index="city", columns="config", values="gain_pct_of_abs", aggfunc=lambda x: f"{x.mean():.3g} ({x.std(ddof=1):.2g}; {x.min():.3g}..{x.max():.3g})")[cfgs]
            p = p.reindex([c for c in CITIES if c in p.index]).reset_index()
            T.append(f"## E2 gain of the leader's best charge vs no charge, objective={obj}: mean (sd; min..max) over {nseed} seeds, percent of |SC|\n" + md(p))
        t = []
        for c in CITIES:
            d = sm[sm.city == c]
            if d.empty:
                continue
            both = d["both"]
            t.append(dict(city=c, both_mean=both.mean(), both_min=both.min(), both_max=both.max(),
                          share_by_seed=" / ".join("n/a" if not np.isfinite(v) else f"{v:.2f}" for v in d.share_delivery_alone_raw),
                          share_mean=d.share_delivery_alone_raw.mean(), share_sd=d.share_delivery_alone_raw.std(ddof=1),
                          cong_only_max=d.congestion_only.max(), best_s_by_seed=" / ".join(f"{v:g}" for v in d.delivery_best_s_over_fee)))
        T.append("## E2 share of the two-instrument gain captured by the per-delivery instrument alone (per seed order 0 / 1 / 2)\n" + md(pd.DataFrame(t)))
        sbt = s[(s.objective == "main") & (s.config == "both")]
        pb = agg(sbt, "city", ["theta", "s_over_fee", "gain_pct_of_abs", "served_share", "revenue"])
        T.append("## E2 best point with both instruments (main objective), over seeds\n" + md(pb))
        s2 = s[(s.objective == "broad") & (s.config == "both")][["city", "seed", "theta", "s_over_fee", "gain_pct_of_abs", "profit", "revenue", "served_share", "slowdown_pct", "gini_access", "gini_price"]]
        T.append("## E2 best point with both instruments (broad objective incl. background delay), per seed\n" + md(s2))
        ex = s.groupby("city").agg(max_regret_grid=("max_regret", "max"), all_converged=("all_converged", "min")).reset_index()
        cert = pd.concat([pd.read_csv(f).assign(seed=0 if "_s" not in f.stem else int(f.stem.rsplit("_s", 1)[1])) for f in sorted(RES.glob("E2cert_*.csv"))], ignore_index=True)
        ex = ex.merge(cert.groupby("city").agg(max_regret_fresh_best_point=("regret_fresh", "max")).reset_index(), on="city", how="left")
        ex.to_csv(RES / "summary_E2_exactness.csv", index=False, float_format="%.6g")
        T.append("## E2 equilibrium exactness over all seeds (max regret vs oracle in the grid; fresh-pool regret at the best point)\n" + md(ex))
    # ------------------------------------------------ E3
    e3 = load("E3")
    if len(e3):
        rows = []
        for (c, sd), d in e3.groupby(["city", "seed"]):
            d = d.set_index("kind")
            so = d.loc["SO_main"]
            ne = d[d.index.str.startswith("NE_") & ~d.index.str.contains("priced")]
            wne = ne.welfare
            r = dict(city=c, seed=sd, W_SO=so.welfare, W_SO_bound=-so.phi_relaxed, W_NE_zmc=d.loc["NE_zmc"].welfare,
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
            r["max_regret_ne"] = float(ne.max_regret.max())
            rows.append(r)
        s = pd.DataFrame(rows)
        s.to_csv(RES / "summary_E3.csv", index=False, float_format="%.6g")  # one row per city and seed
        a3 = agg(s, "city", ["W_SO", "W_NE_zmc", "PoA_zmc", "PoS", "PoA", "PoA_priced", "rel_gap_unpriced_pct", "rel_gap_priced_pct",
                             "n_ne_distinct", "gap_broad_unpriced_pct_of_W", "gap_broad_priced_pct_of_W"])
        a3 = a3.set_index("city").reindex([c for c in CITIES if c in set(a3.city)]).reset_index()
        a3.to_csv(RES / "summary_E3_agg.csv", index=False, float_format="%.6g")
        f = lambda x: f"{x.mean():.3g} ({x.std(ddof=1):.2g}; {x.min():.3g}..{x.max():.3g})"
        p = s.groupby("city").agg(PoA_zmc=("PoA_zmc", f), PoS=("PoS", f), PoA_worst_NE=("PoA", f), PoA_priced=("PoA_priced", f),
                                  priced_gap_pct=("rel_gap_priced_pct", f), max_regret_ne=("max_regret_ne", "max"))
        p = p.reindex([c for c in CITIES if c in p.index]).reset_index()
        T.append(f"## E3 price of anarchy / stability over seeds: mean (sd; min..max) (PoA = W_SO / W_NE, main objective; priced_gap = % of W_SO)\n" + md(p))
        T.append("## E3 per city and seed (welfare ratios; SO = convexified-CG + rounding, upper bound W_SO_bound)\n" + md(s))
    # ------------------------------------------------ E4
    e4 = load("E4")
    if len(e4):
        rows = []
        for (c, sd, kind), d in e4.groupby(["city", "seed", "kind"]):
            key = "eps" if kind == "pbox" else "delta"
            d = d.sort_values(key)
            r0 = d.iloc[0]
            for _, r in d.iterrows():
                rows.append(dict(city=c, seed=sd, kind=kind, eps=r.eps, delta=r.delta, L=r.L, served_share=r.served_share,
                                 deliveries=r.deliveries,
                                 d_deliveries_pct=100 * (r.deliveries / max(r0.deliveries, 1e-9) - 1),
                                 d_vehicle_hours_pct=100 * (r.vehicle_hours / max(r0.vehicle_hours, 1e-9) - 1),
                                 slowdown_pct=100 * r.mean_slowdown, welfare=r.welfare,
                                 d_welfare_pct=100 * (r.welfare / r0.welfare - 1), routing_cost=r.routing_cost,
                                 converged=r.converged, max_regret=r.max_regret, calls=r.calls))
        s = pd.DataFrame(rows)
        s.to_csv(RES / "summary_E4.csv", index=False, float_format="%.6g")  # one row per city, seed, width
        s["eps"] = s.eps.round(4)
        s["delta"] = s.delta.round(4)
        a4 = pd.concat([agg(s[s.kind == "pbox"], ["city", "kind", "eps"], ["served_share", "d_deliveries_pct", "d_welfare_pct", "welfare"]),
                        agg(s[s.kind == "gamma"], ["city", "kind", "delta"], ["served_share", "d_deliveries_pct", "d_welfare_pct", "welfare"])])
        a4.to_csv(RES / "summary_E4_agg.csv", index=False, float_format="%.6g")
        f = lambda x: f"{x.mean():.3g} ({x.std(ddof=1):.2g}; {x.min():.3g}..{x.max():.3g})"
        for kind, key, lab in (("pbox", "eps", "widest p-box vs eps=0"), ("gamma", "delta", "widest surcharge vs delta=0")):
            d = s[s.kind == kind]
            last = d[d[key] == d[key].max()]
            p = last.groupby("city").agg(width=(key, "max"), served_share=("served_share", f), d_deliveries_pct=("d_deliveries_pct", f),
                                         d_welfare_pct=("d_welfare_pct", f))
            p = p.reindex([c for c in CITIES if c in p.index]).reset_index()
            T.append(f"## E4 {lab}: mean (sd; min..max) over seeds\n" + md(p))
        # monotonicity of deliveries in the width, per city and seed
        mono = []
        for (c, sd, kind), d in s.groupby(["city", "seed", "kind"]):
            key = "eps" if kind == "pbox" else "delta"
            v = d.sort_values(key).deliveries.to_numpy()
            mono.append(dict(city=c, seed=sd, kind=kind, monotone=bool((np.diff(v) <= 1e-9 * max(v.max(), 1)).all()),
                             max_increase=float(np.maximum(np.diff(v), 0).max())))
        mono = pd.DataFrame(mono)
        mono.to_csv(RES / "summary_E4_monotone.csv", index=False, float_format="%.6g")
        ex = s.groupby("city").agg(all_converged=("converged", "min"), max_regret=("max_regret", "max")).reset_index()
        T.append("## E4 equilibrium exactness over all seeds and widths\n" + md(ex))
        pm = mono.pivot_table(index="city", columns="kind", values="monotone", aggfunc=lambda x: f"{int(x.sum())}/{len(x)}").reset_index()
        T.append("## E4 seeds in which deliveries fall monotonically with the width\n" + md(pm))
    # ------------------------------------------------ do the conclusions of docs/EXPERIMENTS.md hold in every seed?
    pe2, pe3 = RES / "summary_E2_by_seed.csv", RES / "summary_E3.csv"
    if pe2.exists() and pe3.exists():
        a, b = pd.read_csv(pe2), pd.read_csv(pe3)
        rows = []
        for c in CITIES:
            d, e = a[a.city == c].sort_values("seed"), b[b.city == c].sort_values("seed")
            if d.empty or e.empty:
                continue
            mat = d["both"] >= 0.5  # the second instrument is judged only where the leader's gain is at least 0.5% of |SC|
            c1 = [("n/a" if not m else ("yes" if sh >= 0.5 else "NO")) for m, sh in zip(mat, d.share_delivery_alone_raw)]
            c2 = d.congestion_only.max()
            poa = e.PoA_zmc.to_numpy()
            poaw = e.PoA.to_numpy()
            rows.append(dict(city=c, C1_delivery_alone_ge_half_by_seed=" / ".join(c1), C1_flips=int(sum(x == "NO" for x in c1)),
                             C2_congestion_only_max_pct=c2, C2_holds_lt_1p7=bool(c2 < 1.7),
                             C3_PoA_zmc_by_seed=" / ".join(f"{v:.2f}" for v in poa), C3_PoA_worstNE_by_seed=" / ".join(f"{v:.2f}" for v in poaw),
                             C3_large_ge_1p10_seeds=int((poa >= 1.10).sum()), C3_worstNE_ge_1p10_seeds=int((poaw >= 1.10).sum())))
        cc = pd.DataFrame(rows)
        cc.to_csv(RES / "summary_conclusions.csv", index=False, float_format="%.6g")
        T.append("## Conclusions by seed. C1: per-delivery instrument alone captures >= half of the two-instrument gain (n/a where that gain < 0.5% of |SC|); "
                 "C2: congestion charge alone gains < 1.7% of |SC|; C3: PoA >= 1.10 (ZMC equilibrium, and worst equilibrium found)\n" + md(cc))
    # ------------------------------------------------ one headline table per city (mean +- sd over seeds)
    need = [RES / f for f in ("summary_E2_by_seed.csv", "summary_E3.csv", "summary_E4.csv")]
    if all(p.exists() for p in need):
        a, b, c4 = (pd.read_csv(p) for p in need)
        ms = lambda x: f"{x.mean():.3g} +- {x.std(ddof=1):.2g}"
        rows = []
        for c in CITIES:
            d, e = a[a.city == c], b[b.city == c]
            w = c4[(c4.city == c) & (c4.kind == "pbox")]
            w = w[w.eps == w.eps.max()]
            if d.empty or e.empty:
                continue
            rows.append(dict(city=c, seeds=len(d), gain_cong_only=ms(d.congestion_only), gain_delivery_only=ms(d.delivery_only), gain_both=ms(d["both"]),
                             share_delivery=ms(d.share_delivery_alone_raw), PoA=ms(e.PoA_zmc), PoA_worst=ms(e.PoA), PoS=ms(e.PoS),
                             priced_gap_pct=ms(e.rel_gap_priced_pct), pbox_d_deliv_pct=ms(w.d_deliveries_pct), pbox_d_welfare_pct=ms(w.d_welfare_pct)))
        h = pd.DataFrame(rows)
        h.to_csv(RES / "summary_headline.csv", index=False)
        T.append("## Headline, mean +- sd over seeds (gains in % of |SC|, main objective; priced_gap = (W_SO - W_priced)/W_SO in %; pbox = widest p-box vs eps=0)\n" + md(h))
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
