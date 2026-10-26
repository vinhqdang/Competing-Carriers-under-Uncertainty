"""Tables and figures of the criterion-robustness study (see run_criterion_robust.py).

Reads results/criterion_parts/*.json; writes results/criterion_unpriced.csv, criterion_dip.csv, criterion_grid.csv,
criterion_claims.csv, criterion_imprecision.csv, criterion_pbox_check.csv, summary_criterion.csv and figures/criterion_*.png.

Conventions
  PoA   = welfare(social optimum) / welfare(unpriced equilibrium), computed with the carriers' own route cost ('model') and with the
          true-law expected route cost ('true'); PoS uses the best of the (up to three) equilibria found.
  gain  = 100 (SC0 - SC) / |SC0|, SC the social cost (= -welfare) of the priced equilibrium, SC0 that of the unpriced equilibrium of
          the same game; 'true' re-prices the carriers' routes with the true law, 'model' uses the carriers' criterion.
  seed spread: sd over seeds 0, 1, 2 (ddof = 1).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
FIG = ROOT / "figures"
PARTS = RES / "criterion_parts"
CITIES = ["London", "BuenosAires", "NewDelhi", "Bombay", "Paris", "Berlin", "Moscow", "NewYork", "Cairo"]
FOCUS = ["London", "BuenosAires", "NewDelhi"]
FULL = ["Moscow", "NewYork", "Cairo"]
CRIT = ["pbox", "saa", "wass_cv", "wass_th"]
LABEL = {"pbox": "p-box", "saa": "SAA", "wass_cv": "Wasserstein (CV radius)", "wass_th": "Wasserstein (theory radius)"}
COL = {"pbox": "#4c78a8", "saa": "#f58518", "wass_cv": "#54a24b", "wass_th": "#b279a2"}
SD = lambda x: float(np.std(x, ddof=1)) if len(x) > 1 else float("nan")  # noqa: E731


def load() -> dict:
    out = {}
    for f in sorted(PARTS.glob("*_s*_*.json")):
        stem = f.stem
        city, rest = stem.split("_s", 1)
        seed, crit = rest.split("_", 1)
        try:
            out[(city, int(seed), crit)] = json.loads(f.read_text())
        except Exception:
            pass
    return out


def unpriced_rows(U) -> pd.DataFrame:
    rows = []
    for (city, seed, crit), P in U.items():
        if "ne" not in P:
            continue
        e = P["ne"]["eqs"]
        ne = e[0]
        r = dict(city=city, seed=seed, criterion=crit, eps_cv=";".join(f"{x:g}" for x in P["eps_cv"]) if "eps_cv" in P else "",
                 same_as_saa=bool(P.get("same_as_saa", False)))
        for k in ("served_share", "vehicles", "vehicle_hours", "mean_slowdown", "max_slowdown", "welfare", "welfare_true", "routing_cost",
                  "routing_cost_true", "profit_total", "max_regret", "calls", "gini_access"):
            r[k] = ne[k]
        r["max_regret_all_equilibria"] = max(x["max_regret"] for x in e)
        r["n_eq_distinct_welfare_true"] = len({round(x["welfare_true"], 3) for x in e})
        r["eq_welfare_true_min"] = min(x["welfare_true"] for x in e)
        r["eq_welfare_true_max"] = max(x["welfare_true"] for x in e)
        if "so" in P:
            so = P["so"]
            r.update(so_served_share=so["served_share"], so_welfare=so["welfare"], so_welfare_true=so["welfare_true"],
                     so_vehicles=so["vehicles"], so_slowdown=so["mean_slowdown"])
            wm = max(x["welfare"] for x in e)
            wt = max(x["welfare_true"] for x in e)
            r["poa_model"] = so["welfare"] / ne["welfare"] if ne["welfare"] > 0 else np.nan
            r["poa_true"] = so["welfare_true"] / ne["welfare_true"] if ne["welfare_true"] > 0 else np.nan
            r["pos_model"] = so["welfare"] / wm if wm > 0 else np.nan
            r["pos_true"] = so["welfare_true"] / wt if wt > 0 else np.nan
            r["poa_worst_true"] = so["welfare_true"] / min(x["welfare_true"] for x in e) if min(x["welfare_true"] for x in e) > 0 else np.nan
            r["curse_pct"] = 100 * (ne["routing_cost"] - ne["routing_cost_true"]) / ne["routing_cost_true"] if ne["routing_cost_true"] else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


def dip_rows(U) -> pd.DataFrame:
    rows = []
    for (city, seed, crit), P in U.items():
        if "dip" not in P or "ne" not in P:
            continue
        d, ne = P["dip"], P["ne"]["eqs"][0]
        sc0m, sc0t = ne["social_cost"], ne["social_cost_true"]
        g = P.get("grid", {})
        r = dict(city=city, seed=seed, criterion=crit, status=d["status"], rounds=d["rounds"], n_cuts=d["n_cuts"], calls=d["calls"],
                 calls_so=d["calls_so"], time_s=d["time_s"], served_share=d["served_share"], served_unpriced=ne["served_share"],
                 mean_slowdown=d["mean_slowdown"], slowdown_unpriced=ne["mean_slowdown"],
                 gain_model_pct=100 * (sc0m - d["sc_model"]) / abs(sc0m) if sc0m else np.nan,
                 gain_true_pct=100 * (sc0t - d["social_cost_true"]) / abs(sc0t) if sc0t else np.nan,
                 s_over_fee=d["s_over_fee"], u_mean_over_fee=d["u_mean_over_fee"], u_q_weighted_over_fee=d["u_q_weighted_over_fee"],
                 u_min_over_fee=d["u_min_over_fee"], u_max_over_fee=d["u_max_over_fee"], t_max=d["t_max"],
                 slope_fee_over_nz=d["slope_fee_over_nz"], corr_fee_over_nz=d["corr_fee_over_nz"], n_active=d["n_active"],
                 verify_regret_pooled=d["verify_regret_pooled"], verify_regret_fresh=d["verify_regret_fresh"],
                 verify_target_fresh=d["verify_target_fresh"], loss_bound=d["loss_bound"], welfare_true_dip=d["welfare_true"],
                 welfare_true_unpriced=ne["welfare_true"])
        if "so" in P:
            r["poa_dip_true"] = d["social_cost_true"] / (-P["so"]["welfare_true"]) if P["so"]["welfare_true"] else np.nan
            r["poa_dip_model"] = d["sc_model"] / (-P["so"]["welfare"]) if P["so"]["welfare"] else np.nan
        if g and "gridcert" in P:
            gb = min(g.values(), key=lambda x: x["social_cost_true"])
            r["grid_gain_true_pct"] = 100 * (sc0t - gb["social_cost_true"]) / abs(sc0t)
            r["grid_calls"] = P["grid_calls"]
            r["grid_points"] = P["grid_n"]
            r["grid_calls_per_point"] = P["grid_calls"] / max(P["grid_n"] - 1, 1)
            r["dip_gain_share_of_grid"] = r["gain_true_pct"] / r["grid_gain_true_pct"] if r["grid_gain_true_pct"] > 1e-9 else np.nan
            r["dip_calls_share_grid"] = d["calls"] / P["grid_calls"] if P["grid_calls"] else np.nan
            r["dip_calls_share_63"] = d["calls"] / (63 * r["grid_calls_per_point"]) if r["grid_calls_per_point"] else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


def grid_rows(U) -> pd.DataFrame:
    rows = []
    for (city, seed, crit), P in U.items():
        if "grid" not in P or "ne" not in P:
            continue
        ne = P["ne"]["eqs"][0]
        for k, v in P["grid"].items():
            th, sf = float(v["theta"]), float(v["sfrac"])
            cfg = "none" if th == 0 and sf == 0 else "congestion_only" if sf == 0 else "delivery_only" if th == 0 else "both"
            rows.append(dict(city=city, seed=seed, criterion=crit, config=cfg, theta=th, sfrac=sf, served_share=v["served_share"],
                             mean_slowdown=v["mean_slowdown"], vehicles=v["vehicles"], social_cost=v["social_cost"],
                             social_cost_true=v["social_cost_true"], max_regret=v.get("max_regret", np.nan), calls=v.get("calls", np.nan),
                             gain_true_pct=100 * (ne["social_cost_true"] - v["social_cost_true"]) / abs(ne["social_cost_true"]),
                             gain_model_pct=100 * (ne["social_cost"] - v["social_cost"]) / abs(ne["social_cost"])))
    return pd.DataFrame(rows)


def claims_rows(grid: pd.DataFrame, dp: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (city, seed, crit), g in grid.groupby(["city", "seed", "criterion"]):
        best = g.loc[g.gain_true_pct.idxmax()]
        dl, cg, bt = g[g.config == "delivery_only"], g[g.config == "congestion_only"], g[g.config == "both"]
        bd = dl.loc[dl.gain_true_pct.idxmax()] if len(dl) else None
        gain_all = max(best.gain_true_pct, 0.0)
        gdl = max(float(bd.gain_true_pct), 0.0) if bd is not None else np.nan
        gcg = max(float(cg.gain_true_pct.max()), 0.0) if len(cg) else np.nan
        d = dp[(dp.city == city) & (dp.seed == seed) & (dp.criterion == crit)]
        r = dict(city=city, seed=seed, criterion=crit, grid_points=len(g), gain_best_pct=gain_all, best_config=best.config,
                 best_theta=best.theta, best_sfrac=best.sfrac, gain_delivery_only_pct=gdl, best_sfrac_delivery_only=float(bd.sfrac) if bd is not None else np.nan,
                 gain_congestion_only_pct=gcg, best_theta_congestion_only=float(cg.loc[cg.gain_true_pct.idxmax()].theta) if len(cg) else np.nan,
                 gain_both_best_pct=float(bt.gain_true_pct.max()) if len(bt) else np.nan,
                 delivery_share=gdl / gain_all if gain_all > 1e-9 else np.nan,
                 congestion_share=gcg / gain_all if gain_all > 1e-9 else np.nan,
                 subsidy_dominates=bool(gdl >= gcg and (gdl / gain_all >= 0.5 if gain_all > 1e-9 else True)),
                 best_delivery_is_subsidy=bool(bd is not None and bd.sfrac < 0 and bd.gain_true_pct > 0))
        if len(d):
            d = d.iloc[0]
            r.update(dip_gain_true_pct=d.gain_true_pct, dip_ge_grid=bool(d.gain_true_pct >= gain_all - 1e-6 * max(abs(gain_all), 1.0)),
                     dip_gain_share_of_grid=d.dip_gain_share_of_grid, dip_calls_share_grid=d.dip_calls_share_grid,
                     dip_calls_share_63=d.dip_calls_share_63, dip_s_over_fee=d.s_over_fee, dip_u_q_weighted_over_fee=d.u_q_weighted_over_fee)
        rows.append(r)
    return pd.DataFrame(rows)


def agg(df: pd.DataFrame, keys, cols) -> pd.DataFrame:
    g = df.groupby(keys)
    m = g[cols].mean()
    s = g[cols].agg(SD).add_suffix("_sd")
    n = g.size().rename("n_seeds")
    return pd.concat([n, m, s], axis=1).reset_index()


def pbox_check(U) -> pd.DataFrame:
    """Price-and-branch p-box runs of this study against the published exact-oracle E1 / E3 numbers (model cost)."""
    rows = []
    for (city, seed, crit), P in U.items():
        if crit != "pbox" or "ne" not in P:
            continue
        f = RES / (f"E1_{city}.csv")
        e1 = pd.read_csv(f)
        e1 = e1[(e1.scenario == "base") & (e1.seed == seed)]
        f3 = RES / (f"E3_{city}.csv" if seed == 0 else f"E3_{city}_s{seed}.csv")
        r = dict(city=city, seed=seed, welfare_here=P["ne"]["eqs"][0]["welfare"], served_here=P["ne"]["eqs"][0]["served_share"])
        if len(e1):
            r.update(welfare_published=float(e1.welfare.iloc[0]), served_published=float(e1.served_share.iloc[0]))
        if "so" in P:
            r["so_welfare_here"] = P["so"]["welfare"]
            if f3.exists():
                e3 = pd.read_csv(f3)
                so = e3[e3.kind == "SO_main"]
                if len(so):
                    r["so_welfare_published"] = float(-so.social_cost.iloc[0])
        rows.append(r)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------------ figures
def bars(ax, tab, value, sd, cities, crits, ylabel, title, hline=None):
    import matplotlib.pyplot as plt  # noqa: F401
    x = np.arange(len(cities))
    w = 0.8 / len(crits)
    for j, c in enumerate(crits):
        t = tab[tab.criterion == c].set_index("city").reindex(cities)
        ax.bar(x + (j - (len(crits) - 1) / 2) * w, t[value], w, yerr=t[sd] if sd in t else None, color=COL[c], label=LABEL[c],
               capsize=2, error_kw=dict(lw=0.8))
    if hline is not None:
        ax.axhline(hline, color="grey", lw=0.8, ls=":")
    ax.set_xticks(x)
    ax.set_xticklabels(cities, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)


def figures(un: pd.DataFrame, dp: pd.DataFrame, cl: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    crits = [c for c in CRIT if c in set(un.criterion)]
    cities = [c for c in CITIES if c in set(un.city)]
    ua = agg(un, ["city", "criterion"], ["served_share", "poa_true", "poa_model", "mean_slowdown"])
    for name, val, yl, title, hl in [("served", "served_share", "served share at the unpriced equilibrium", "Served share", None),
                                     ("poa", "poa_true", "PoA (true-law cost)", "Price of anarchy", 1.0)]:
        fig, ax = plt.subplots(figsize=(8.5, 3.6), constrained_layout=True)
        bars(ax, ua, val, val + "_sd", cities, crits, yl, title + " by carrier criterion (bars: mean, whiskers: sd over seeds 0-2)", hl)
        ax.legend(fontsize=8, frameon=False, ncol=2)
        fig.savefig(FIG / f"criterion_{name}.png", dpi=150)
        plt.close(fig)
    if len(dp):
        da = agg(dp, ["city", "criterion"], ["u_q_weighted_over_fee", "s_over_fee", "gain_true_pct"])
        fig, ax = plt.subplots(1, 2, figsize=(11, 3.6), constrained_layout=True)
        bars(ax[0], da, "u_q_weighted_over_fee", "u_q_weighted_over_fee_sd", cities, crits,
             "DIP per-delivery charge u / fee (delivery-weighted mean)", "Optimal subsidy (negative = subsidy), DIP", 0.0)
        ax[0].legend(fontsize=8, frameon=False, ncol=2)
        bars(ax[1], da, "gain_true_pct", "gain_true_pct_sd", cities, crits, "leader's gain, % of |SC| (true-law cost)",
             "Gain from DIP charges", 0.0)
        fig.savefig(FIG / "criterion_subsidy.png", dpi=150)
        plt.close(fig)
    if len(cl):
        ca = agg(cl, ["city", "criterion"], ["delivery_share", "gain_delivery_only_pct", "gain_congestion_only_pct", "best_sfrac_delivery_only"])
        fig, ax = plt.subplots(1, 3, figsize=(11, 3.4), constrained_layout=True)
        bars(ax[0], ca, "gain_delivery_only_pct", "gain_delivery_only_pct_sd", FOCUS, [c for c in crits if c != "pbox" or True],
             "gain, % of |SC|", "Best delivery-only point", 0.0)
        bars(ax[1], ca, "gain_congestion_only_pct", "gain_congestion_only_pct_sd", FOCUS, crits, "gain, % of |SC|", "Best congestion-only point", 0.0)
        bars(ax[2], ca, "best_sfrac_delivery_only", "best_sfrac_delivery_only_sd", FOCUS, crits, "subsidy / fee", "Best delivery-only charge", 0.0)
        ax[0].legend(fontsize=7, frameon=False)
        fig.savefig(FIG / "criterion_grid_claims.png", dpi=150)
        plt.close(fig)


# ------------------------------------------------------------------------------------------------ main
def summarize() -> None:
    U = load()
    if not U:
        print("no results yet")
        return
    un, dp, gr = unpriced_rows(U), dip_rows(U), grid_rows(U)
    cl = claims_rows(gr, dp) if len(gr) else pd.DataFrame()
    for name, df in [("unpriced", un), ("dip", dp), ("grid", gr), ("claims", cl)]:
        if len(df):
            df.sort_values([c for c in ("city", "criterion", "seed", "theta", "sfrac") if c in df]).to_csv(RES / f"criterion_{name}.csv", index=False, float_format="%.6g")
    pc = pbox_check(U)
    if len(pc):
        pc.to_csv(RES / "criterion_pbox_check.csv", index=False, float_format="%.6g")
    im = []
    for (city, seed, crit), P in U.items():
        for r in P.get("imprec", []):
            im.append(dict(city=city, seed=seed, criterion=crit, **{k: r[k] for k in ("delta", "served_share", "welfare", "welfare_true", "vehicles", "mean_slowdown", "max_regret")}))
    if im:
        pd.DataFrame(im).sort_values(["city", "criterion", "seed", "delta"]).to_csv(RES / "criterion_imprecision.csv", index=False, float_format="%.6g")
    # summary: one row per (city, criterion) with mean and sd over seeds
    cols_un = [c for c in ("served_share", "mean_slowdown", "vehicles", "welfare", "welfare_true", "poa_model", "poa_true", "pos_model", "pos_true",
                           "so_served_share", "max_regret") if c in un]
    s = agg(un, ["city", "criterion"], cols_un)
    if len(dp):
        cols_dp = [c for c in ("gain_model_pct", "gain_true_pct", "s_over_fee", "u_mean_over_fee", "u_q_weighted_over_fee", "slope_fee_over_nz",
                               "corr_fee_over_nz", "calls", "poa_dip_true", "verify_regret_fresh", "verify_target_fresh") if c in dp]
        d = agg(dp, ["city", "criterion"], cols_dp).drop(columns="n_seeds").rename(columns={c: "dip_" + c for c in cols_dp} | {c + "_sd": "dip_" + c + "_sd" for c in cols_dp})
        s = s.merge(d, on=["city", "criterion"], how="left")
    if len(cl):
        cols_cl = ["gain_best_pct", "gain_delivery_only_pct", "gain_congestion_only_pct", "delivery_share", "congestion_share",
                   "best_sfrac_delivery_only", "dip_gain_share_of_grid", "dip_calls_share_grid", "dip_calls_share_63"]
        cols_cl = [c for c in cols_cl if c in cl]
        c2 = agg(cl, ["city", "criterion"], cols_cl).drop(columns="n_seeds")
        c2["subsidy_dominates_seeds"] = cl.groupby(["city", "criterion"]).subsidy_dominates.sum().values
        c2["dip_ge_grid_seeds"] = cl.groupby(["city", "criterion"]).dip_ge_grid.sum().values if "dip_ge_grid" in cl else np.nan
        c2 = c2.rename(columns={c: "grid_" + c for c in c2.columns if c not in ("city", "criterion")})
        s = s.merge(c2, on=["city", "criterion"], how="left")
    s["order"] = s.city.map({c: i for i, c in enumerate(CITIES)})
    s["corder"] = s.criterion.map({c: i for i, c in enumerate(CRIT)})
    s = s.sort_values(["order", "corder"]).drop(columns=["order", "corder"])
    s.to_csv(RES / "summary_criterion.csv", index=False, float_format="%.6g")
    figures(un, dp, cl)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print(s[["city", "criterion", "n_seeds", "served_share", "poa_true", "poa_model", "dip_gain_true_pct", "dip_u_q_weighted_over_fee"]].round(3).to_string(index=False))


if __name__ == "__main__":
    summarize()
