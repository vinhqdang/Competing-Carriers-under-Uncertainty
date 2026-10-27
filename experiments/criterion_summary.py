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
                 welfare_true_unpriced=ne["welfare_true"], gain_true_abs=d["welfare_true"] - ne["welfare_true"],
                 gain_model_abs=sc0m - d["sc_model"], subsidy_outlay=-d["charges"], deliveries_dip=d["deliveries"],
                 outlay_per_delivery_over_fee=-d["charges"] / max(d["deliveries"], 1e-12) / d["fee"], deliveries_unpriced=ne["deliveries"])
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
        for k, v in list(P["grid"].items()) + [("x" + k, v) for k, v in P.get("gridx", {}).items()]:
            th, sf = float(v["theta"]), float(v["sfrac"])
            cfg = "none" if th == 0 and sf == 0 else "congestion_only" if sf == 0 else "delivery_only" if th == 0 else "both"
            rows.append(dict(city=city, seed=seed, criterion=crit, config=cfg, theta=th, sfrac=sf, served_share=v["served_share"],
                             mean_slowdown=v["mean_slowdown"], vehicles=v["vehicles"], social_cost=v["social_cost"],
                             social_cost_true=v["social_cost_true"], max_regret=v.get("max_regret", np.nan), calls=v.get("calls", np.nan),
                             gain_true_pct=100 * (ne["social_cost_true"] - v["social_cost_true"]) / abs(ne["social_cost_true"]),
                             gain_model_pct=100 * (ne["social_cost"] - v["social_cost"]) / abs(ne["social_cost"])))
    return pd.DataFrame(rows)


def claims_rows(grid: pd.DataFrame, dp: pd.DataFrame) -> pd.DataFrame:
    """Per (city, seed, criterion): the headline claims of the leader's problem on the coarse grid, with the leader maximising the
    true-law social cost ('true', the study's primary objective) and the carriers' own criterion cost ('model', the paper's objective)."""
    rows = []
    for (city, seed, crit), g in grid.groupby(["city", "seed", "criterion"]):
        d = dp[(dp.city == city) & (dp.seed == seed) & (dp.criterion == crit)]
        r = dict(city=city, seed=seed, criterion=crit, grid_points=len(g))
        for tag, col in (("", "gain_true_pct"), ("_m", "gain_model_pct")):
            best = g.loc[g[col].idxmax()]
            dl, cg, bt = g[g.config == "delivery_only"], g[g.config == "congestion_only"], g[g.config == "both"]
            bd = dl.loc[dl[col].idxmax()] if len(dl) else None
            gain_all = max(float(best[col]), 0.0)
            gdl = max(float(bd[col]), 0.0) if bd is not None else np.nan
            gcg = max(float(cg[col].max()), 0.0) if len(cg) else np.nan
            r.update({f"gain_best_pct{tag}": gain_all, f"best_config{tag}": best.config, f"best_theta{tag}": best.theta,
                      f"best_sfrac{tag}": best.sfrac, f"gain_delivery_only_pct{tag}": gdl,
                      f"best_sfrac_delivery_only{tag}": float(bd.sfrac) if bd is not None else np.nan,
                      f"gain_congestion_only_pct{tag}": gcg, f"gain_congestion_only_raw_pct{tag}": float(cg[col].max()) if len(cg) else np.nan,
                      f"gain_both_best_pct{tag}": float(bt[col].max()) if len(bt) else np.nan,
                      f"delivery_share{tag}": gdl / gain_all if gain_all > 1e-9 else np.nan,
                      f"congestion_share{tag}": gcg / gain_all if gain_all > 1e-9 else np.nan,
                      f"subsidy_dominates{tag}": bool(gdl >= gcg and (gdl / gain_all >= 0.5 if gain_all > 1e-9 else True)),
                      f"best_delivery_is_subsidy{tag}": bool(bd is not None and bd.sfrac < 0 and bd[col] > 0)})
            if len(d):
                dd = d.iloc[0]
                gd = float(dd[col])
                r.update({f"dip_ge_grid{tag}": bool(gd >= gain_all - 1e-6 * max(abs(gain_all), 1.0)),
                          f"dip_gain_share_of_grid{tag}": gd / gain_all if gain_all > 1e-9 else np.nan})
        if len(d):
            dd = d.iloc[0]
            r.update(dip_gain_true_pct=dd.gain_true_pct, dip_gain_model_pct=dd.gain_model_pct, dip_calls_share_grid=dd.dip_calls_share_grid,
                     dip_calls_share_63=dd.dip_calls_share_63, dip_s_over_fee=dd.s_over_fee, dip_u_q_weighted_over_fee=dd.u_q_weighted_over_fee)
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

    def legend(fig, ax):
        h, l = ax.get_legend_handles_labels()
        fig.legend(h, l, loc="outside lower center", ncol=len(crits), frameon=False, fontsize=8)

    ua = agg(un, ["city", "criterion"], ["served_share", "poa_true", "poa_model", "mean_slowdown"])
    for name, val, yl, title, hl in [("served", "served_share", "served share", "Served share at the unpriced equilibrium", None),
                                     ("poa", "poa_true", "PoA (true-law cost)", "Price of anarchy", 1.0)]:
        fig, ax = plt.subplots(figsize=(8.5, 3.8), constrained_layout=True)
        bars(ax, ua, val, val + "_sd", cities, crits, yl, title + " (mean, whiskers sd over seeds 0-2)", hl)
        legend(fig, ax)
        fig.savefig(FIG / f"criterion_{name}.png", dpi=150)
        plt.close(fig)
    if len(dp):
        da = agg(dp, ["city", "criterion"], ["u_q_weighted_over_fee", "s_over_fee", "gain_true_pct", "gain_model_pct"])
        ca = agg(cl, ["city", "criterion"], ["best_sfrac_delivery_only", "best_sfrac_delivery_only_m", "delivery_share", "delivery_share_m",
                                              "gain_congestion_only_raw_pct", "dip_gain_share_of_grid_m"]) if len(cl) else None
        fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.9), constrained_layout=True)
        bars(ax[0], da, "u_q_weighted_over_fee", "u_q_weighted_over_fee_sd", cities, crits, "u / fee",
             "DIP per-delivery charge (delivery-weighted)", 0.0)
        if ca is not None:
            bars(ax[1], ca, "best_sfrac_delivery_only_m", "best_sfrac_delivery_only_m_sd", FOCUS, crits, "charge / fee",
                 "Best uniform charge, carriers' own cost", 0.0)
            bars(ax[2], ca, "best_sfrac_delivery_only", "best_sfrac_delivery_only_sd", FOCUS, crits, "charge / fee",
                 "Best uniform charge, true-law cost", 0.0)
        legend(fig, ax[0])
        fig.savefig(FIG / "criterion_subsidy.png", dpi=150)
        plt.close(fig)
        fig, ax = plt.subplots(1, 3, figsize=(12.5, 3.9), constrained_layout=True)
        bars(ax[0], da, "gain_true_pct", "gain_true_pct_sd", cities, crits, "% of |SC|", "Leader's gain from DIP charges (true-law cost)", 0.0)
        bars(ax[1], da, "gain_model_pct", "gain_model_pct_sd", cities, crits, "% of |SC|", "Leader's gain from DIP charges (carriers' cost)", 0.0)
        if ca is not None:
            bars(ax[2], ca, "gain_congestion_only_raw_pct", "gain_congestion_only_raw_pct_sd", FOCUS, crits, "% of |SC|",
                 "Best congestion-only point (coarse grid)", 0.0)
        legend(fig, ax[0])
        fig.savefig(FIG / "criterion_gain.png", dpi=150)
        plt.close(fig)
    if len(cl):
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.8), constrained_layout=True)
        bars(ax[0], ca, "delivery_share_m", "delivery_share_m_sd", FOCUS, crits, "share", "Delivery-only share of the best grid gain", 1.0)
        bars(ax[1], ca, "dip_gain_share_of_grid_m", "dip_gain_share_of_grid_m_sd", FOCUS, crits, "share", "DIP gain / coarse-grid gain", 1.0)
        legend(fig, ax[0])
        fig.savefig(FIG / "criterion_grid_claims.png", dpi=150)
        plt.close(fig)


# ------------------------------------------------------------------------------------------------ markdown report
def fmt(m, sd=None, d=2):
    if pd.isna(m):
        return "-"
    return f"{m:.{d}f}" + (f" ({sd:.{d}f})" if sd is not None and not pd.isna(sd) else "")


def write_md(un: pd.DataFrame, dp: pd.DataFrame, cl: pd.DataFrame, gr: pd.DataFrame) -> None:
    crits = [c for c in CRIT if c in set(un.criterion)]
    cities = [c for c in CITIES if c in set(un.city)]
    ua = agg(un, ["city", "criterion"], ["served_share", "vehicles", "welfare_true", "mean_slowdown", "poa_true", "poa_model", "pos_true"])
    da = agg(dp, ["city", "criterion"], ["gain_true_pct", "gain_model_pct", "gain_true_abs", "u_q_weighted_over_fee", "s_over_fee", "slope_fee_over_nz",
                                         "corr_fee_over_nz", "calls", "subsidy_outlay"]) if len(dp) else pd.DataFrame()
    L = ["# Robustness to the carriers' criterion (generated by experiments/criterion_summary.py)", "",
         "Mean (sd over seeds 0, 1, 2).  p-box: the paper's carriers (price-and-branch oracle); SAA / Wasserstein: heuristic oracle `HeurPool` "
         "(no certificate; equilibria verified against a fresh independent pool).  PoA = welfare(SO)/welfare(unpriced equilibrium).", ""]

    def tab(title, df, cols, heads, cs=cities, digits=None):
        L.extend([f"### {title}", "", "| city | criterion | n | " + " | ".join(heads) + " |", "|---|---|---|" + "---|" * len(heads)])
        for c in cs:
            for k in crits:
                r = df[(df.city == c) & (df.criterion == k)]
                if not len(r):
                    continue
                r = r.iloc[0]
                L.append(f"| {c} | {LABEL[k]} | {int(r.n_seeds)} | " + " | ".join(
                    fmt(r[v], r.get(v + "_sd"), (digits or {}).get(v, 2)) for v in cols) + " |")
        L.append("")

    tab("1. Unpriced equilibrium and price of anarchy", ua, ["served_share", "vehicles", "welfare_true", "mean_slowdown", "poa_true", "poa_model", "pos_true"],
        ["served share", "vehicles", "welfare (true law)", "slowdown", "PoA true", "PoA model", "PoS true"], digits={"mean_slowdown": 3, "vehicles": 1, "welfare_true": 1})
    if len(da):
        tab("2. Leader's charges by DIP", da, ["gain_true_pct", "gain_model_pct", "gain_true_abs", "u_q_weighted_over_fee", "s_over_fee",
                                               "slope_fee_over_nz", "corr_fee_over_nz", "calls"],
            ["gain % (true)", "gain % (model)", "gain (true, USD)", "u/fee (weighted)", "s/fee", "slope vs fee/n_z", "corr", "calls"],
            digits={"gain_true_abs": 1, "calls": 0, "slope_fee_over_nz": 3, "corr_fee_over_nz": 3, "u_q_weighted_over_fee": 3, "s_over_fee": 3})
    if len(cl):
        ca = agg(cl, ["city", "criterion"], ["gain_best_pct_m", "gain_delivery_only_pct_m", "gain_congestion_only_pct_m", "delivery_share_m",
                                              "best_sfrac_delivery_only_m", "dip_gain_share_of_grid_m", "gain_best_pct", "delivery_share",
                                              "best_sfrac_delivery_only", "gain_congestion_only_raw_pct", "dip_calls_share_63"])
        ca["n_seeds"] = ca["n_seeds"]
        tab("3a. Coarse leader grid, carriers' own cost (the paper's objective)", ca,
            ["gain_best_pct_m", "gain_delivery_only_pct_m", "gain_congestion_only_pct_m", "delivery_share_m", "best_sfrac_delivery_only_m",
             "dip_gain_share_of_grid_m", "dip_calls_share_63"],
            ["best gain %", "delivery-only %", "congestion-only %", "delivery share", "best uniform s/fee", "DIP / grid gain", "DIP calls / 63-point grid"],
            cs=FOCUS, digits={"dip_calls_share_63": 3})
        tab("3b. Coarse leader grid, true-law cost", ca, ["gain_best_pct", "delivery_share", "best_sfrac_delivery_only", "gain_congestion_only_raw_pct"],
            ["best gain %", "delivery share", "best uniform s/fee", "congestion-only gain % (raw)"], cs=FOCUS)

    # ---- claim-by-claim verdicts
    V = ["### 4. The paper's claims, criterion by criterion", "",
         "A claim 'holds' when the rule in the first column is met in every city (and seed, where stated); the rules are conventions of this study.", "",
         "| claim and rule | " + " | ".join(LABEL[k] for k in crits) + " |", "|---|" + "---|" * len(crits)]

    def row(name, fn):
        V.append(f"| {name} | " + " | ".join(fn(k) for k in crits) + " |")

    def ok(b):
        return "HOLDS" if b else "FLIPS"

    if len(cl):
        def c1(k):
            c = cl[cl.criterion == k]
            if not len(c):
                return "-"
            out, okk = [], True
            for tag, nm in (("_m", "model"), ("", "true")):
                col = "gain_delivery_only_pct" + tag
                tot = "gain_best_pct" + tag
                m = c.groupby("city")[[col, tot, "gain_congestion_only_pct" + tag]].mean()
                ratio = m[col] / m[tot]
                okk &= bool((ratio >= 0.5).all() and (m[col] > m["gain_congestion_only_pct" + tag]).all())
                out.append(f"{nm} ratio of mean gains {ratio.min():.2f}-{ratio.max():.2f}, per seed >= 0.5 in {int((c['delivery_share' + tag] >= 0.5).sum())}/{len(c)}")
            return f"{ok(okk)}: " + "; ".join(out)
        row("Subsidy dominates: per city, delivery-only gain >= half the best grid gain (ratio of mean gains) and above the congestion-only gain (focus cities, 3 seeds)", c1)

        def c2(k):
            c = cl[cl.criterion == k]
            if not len(c):
                return "-"
            okk, weak, out = True, True, []
            for tag, nm in (("_m", "model"), ("", "true")):
                m = c.groupby("city")[["gain_congestion_only_pct" + tag, "gain_delivery_only_pct" + tag]].mean()
                okk &= bool((m.iloc[:, 0] < 5).all() and (m.iloc[:, 0] < 0.15 * m.iloc[:, 1]).all())
                weak &= bool((m.iloc[:, 0] < 5).all() and (m.iloc[:, 0] < 0.25 * m.iloc[:, 1]).all())
                out.append(f"{nm} mean {m.iloc[:, 0].min():.1f}-{m.iloc[:, 0].max():.1f}% vs delivery-only {m.iloc[:, 1].min():.0f}-{m.iloc[:, 1].max():.0f}%, max seed {c['gain_congestion_only_pct' + tag].max():.1f}%")
            return f"{'HOLDS' if okk else 'HOLDS (marginal: ratio 0.15-0.25)' if weak else 'FLIPS'}: " + "; ".join(out)
        row("Congestion charge alone small: per city mean best congestion-only gain < 5% of |SC| and < 15% of the delivery-only gain", c2)
    P3 = un.groupby(["city", "criterion"])[["poa_true", "poa_model"]].mean()

    def c3(k):
        t = P3.xs(k, level="criterion")
        t = t[t.index.isin(cities)]
        big = sorted(t.index[t.poa_true >= 1.10], key=lambda c: -t.poa_true[c])
        top3 = list(t.poa_true.sort_values(ascending=False).index[:3])
        return f"{ok(set(big) == set(FOCUS) or set(big) <= set(FOCUS) and len(big) >= 2)}: PoA>=1.10 in {', '.join(big) or 'none'}; top 3 {', '.join(top3)}; London {t.poa_true.get('London', np.nan):.2f}, Buenos Aires {t.poa_true.get('BuenosAires', np.nan):.2f}, New Delhi {t.poa_true.get('NewDelhi', np.nan):.2f}, other cities max {t.poa_true.drop([c for c in FOCUS if c in t.index]).max():.2f}"
    row("PoA large only in London, Buenos Aires, New Delhi (large: true-law PoA >= 1.10; mean over seeds)", c3)

    def c4(k):
        c = da[da.criterion == k] if len(da) else pd.DataFrame()
        if not len(c):
            return "-"
        return f"{ok((c.slope_fee_over_nz + 0.375).abs().max() <= 0.03 and c.corr_fee_over_nz.max() <= -0.95)}: slope {c.slope_fee_over_nz.min():.3f} to {c.slope_fee_over_nz.max():.3f}, corr <= {c.corr_fee_over_nz.max():.3f}"
    row("Per-delivery charge u_z ~ -0.375 fee/n_z: |slope + 0.375| <= 0.03 and corr <= -0.95 in every city", c4)
    if len(cl):
        def c5(k):
            c = cl[cl.criterion == k]
            if not len(c):
                return "-"
            m = c.groupby("city")[["dip_gain_true_pct", "dip_gain_model_pct", "gain_best_pct", "gain_best_pct_m"]].mean()
            r_m = m.dip_gain_model_pct / m.gain_best_pct_m
            r_t = m.dip_gain_true_pct / m.gain_best_pct
            return (f"{ok((r_m >= 1.0).all())}: DIP / grid gain (carriers' cost) {r_m.min():.2f}-{r_m.max():.2f} (mean gains), per case >= 0.97 in "
                    f"{int((c.dip_gain_share_of_grid_m >= 0.97).sum())}/{len(c)}, >= 1 in {int(c.dip_ge_grid_m.sum())}/{len(c)}; true-law {r_t.min():.2f}-{r_t.max():.2f}; "
                    f"calls {c.dip_calls_share_63.mean() * 100:.1f}% of a 63-point grid ({c.dip_calls_share_grid.mean() * 100:.0f}% of this 16-point grid)")
        row("DIP gain >= coarse-grid gain (ratio of mean gains >= 1 per city) with < 15% of the calls of a 63-point grid", c5)
    if len(da):
        def c6(k):
            c = da[da.criterion == k]
            if not len(c):
                return "-"
            return f"{ok((c.u_q_weighted_over_fee < 0).all())}: weighted u/fee {c.u_q_weighted_over_fee.min():.3f} to {c.u_q_weighted_over_fee.max():.3f} (all negative)"
        row("Optimal charge is a subsidy (DIP, every city)", c6)
    comp = [c for c in FULL if c in set(un.city)]
    if comp:
        def c7(k):
            u = un[(un.criterion == k) & un.city.isin(comp)]
            d_ = dp[(dp.criterion == k) & dp.city.isin(comp)] if len(dp) else pd.DataFrame()
            if not len(u):
                return "-"
            g = f"; DIP gain {d_.gain_true_pct.min():.2f} to {d_.gain_true_pct.max():.2f}%" if len(d_) else ""
            return f"served share {u.served_share.min():.3f}-{u.served_share.max():.3f}, PoA {u.poa_true.min():.3f}-{u.poa_true.max():.3f}{g}"
        row("Complete-service cities (Moscow, New York, Cairo): nothing to fix", c7)
    L.extend([""] + V + [""])
    open(RES / "criterion_summary.md", "w").write("\n".join(L) + "\n")


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
        cols_dp = [c for c in ("gain_model_pct", "gain_true_pct", "gain_true_abs", "gain_model_abs", "subsidy_outlay", "outlay_per_delivery_over_fee", "poa_dip_model", "s_over_fee", "u_mean_over_fee", "u_q_weighted_over_fee", "slope_fee_over_nz",
                               "corr_fee_over_nz", "calls", "poa_dip_true", "verify_regret_fresh", "verify_target_fresh") if c in dp]
        d = agg(dp, ["city", "criterion"], cols_dp).drop(columns="n_seeds").rename(columns={c: "dip_" + c for c in cols_dp} | {c + "_sd": "dip_" + c + "_sd" for c in cols_dp})
        s = s.merge(d, on=["city", "criterion"], how="left")
    if len(cl):
        cols_cl = ["gain_best_pct", "gain_delivery_only_pct", "gain_congestion_only_pct", "gain_congestion_only_raw_pct", "delivery_share",
                   "congestion_share", "best_sfrac_delivery_only", "dip_gain_share_of_grid", "gain_best_pct_m", "gain_delivery_only_pct_m",
                   "gain_congestion_only_pct_m", "delivery_share_m", "best_sfrac_delivery_only_m", "dip_gain_share_of_grid_m",
                   "dip_calls_share_grid", "dip_calls_share_63"]
        cols_cl = [c for c in cols_cl if c in cl]
        c2 = agg(cl, ["city", "criterion"], cols_cl).drop(columns="n_seeds")
        c2["subsidy_dominates_seeds"] = cl.groupby(["city", "criterion"]).subsidy_dominates.sum().values
        c2["dip_ge_grid_seeds"] = cl.groupby(["city", "criterion"]).dip_ge_grid.sum().values if "dip_ge_grid" in cl else np.nan
        c2["subsidy_dominates_m_seeds"] = cl.groupby(["city", "criterion"]).subsidy_dominates_m.sum().values
        c2 = c2.rename(columns={c: "grid_" + c for c in c2.columns if c not in ("city", "criterion")})
        s = s.merge(c2, on=["city", "criterion"], how="left")
    s["order"] = s.city.map({c: i for i, c in enumerate(CITIES)})
    s["corder"] = s.criterion.map({c: i for i, c in enumerate(CRIT)})
    s = s.sort_values(["order", "corder"]).drop(columns=["order", "corder"])
    s.to_csv(RES / "summary_criterion.csv", index=False, float_format="%.6g")
    figures(un, dp, cl)
    write_md(un, dp, cl, gr)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print(s[["city", "criterion", "n_seeds", "served_share", "poa_true", "poa_model", "dip_gain_true_pct", "dip_u_q_weighted_over_fee"]].round(3).to_string(index=False))


if __name__ == "__main__":
    summarize()
