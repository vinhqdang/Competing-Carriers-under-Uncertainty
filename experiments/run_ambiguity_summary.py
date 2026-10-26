"""Tables and figures of the 'Why probability boxes' study (see experiments/run_ambiguity.py).

Reads results/ambiguity_parts/plans_<regime>_<city>.csv, results/ambiguity_oracle.csv, results/ambiguity_game_<city>.csv and
writes results/ambiguity_*.csv, results/ambiguity_summary.md and figures/ambiguity_*.png.

Conventions
  regret          expected cost of the plan on the test law minus the best known plan for that law (the oracle plan optimised
                  on the test law, or any plan found in any run if that is cheaper), in percent of the best known cost
  disappointment  criterion value of the plan minus its realised expected cost on the true law (positive = conservative)
  tail            CVaR_0.95 of the daily total cost of the plan (percent above the best known plan's value for that law)
  unit of replication   the training draw: every table averages over the nine cities first and takes the sd over the 20 draws
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
RES = ROOT / "results"
FIG = ROOT / "figures"
PARTS = RES / "ambiguity_parts"

MAIN = ["saa", "wass_cv", "wass_th", "wass_fg", "cvar80", "cvar90", "pbox_ud_80", "pbox_ud_90", "pbox_ud_95", "pbox_ud_99",
        "pbox_ud_emp", "pbox_ind_80", "pbox_ind_95", "pbox_ind_emp"]
PBOX_UD = ["pbox_ud_80", "pbox_ud_90", "pbox_ud_95", "pbox_ud_99"]
METRICS = ["exp", "cvar95", "p_ot_day", "p_ot_route", "ot_h", "ot_h_cond", "drive_h", "sd"]
MARGIN_PP = 0.5  # non-inferiority margin (percentage points of the best known cost)


def load_plans() -> pd.DataFrame:
    fs = sorted(PARTS.glob("plans_*_*.csv"))
    if not fs:
        raise SystemExit("no results yet")
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)


def best_known(df: pd.DataFrame, orc: pd.DataFrame) -> dict:
    """{(city, law): cost of the best known plan for that law}."""
    out = {(r.city, r.law): r.exp for r in orc.itertuples()}
    for law in ("true", "shift20", "shift40", "heavy"):
        col = f"{law}_exp"
        if col not in df.columns:
            continue
        m = df.dropna(subset=[col]).groupby("city")[col].min()
        for c, v in m.items():
            out[(c, law)] = min(out.get((c, law), np.inf), float(v))
    return out


def add_regrets(df: pd.DataFrame, bk: dict) -> pd.DataFrame:
    df = df.copy()
    for law in ("true", "shift20", "shift40", "heavy"):
        if f"{law}_exp" not in df.columns:
            continue
        ref = df.city.map(lambda c: bk.get((c, law), np.nan))
        df[f"{law}_regret"] = df[f"{law}_exp"] - ref
        df[f"{law}_regret_pct"] = 100 * df[f"{law}_regret"] / ref
        if f"{law}_cvar95" in df.columns:
            # tail relative to the best known *expected* cost keeps units comparable across cities
            df[f"{law}_cvar95_pct"] = 100 * (df[f"{law}_cvar95"] - ref) / ref
    df["disappointment"] = df["crit_value"] - df["true_exp"] if "true_exp" in df.columns else np.nan
    df["disappointment_pct"] = 100 * df["disappointment"] / df["true_exp"] if "true_exp" in df.columns else np.nan
    return df


def draw_level(df: pd.DataFrame, cols: list[str], law_prefix: str) -> pd.DataFrame:
    """Average over cities first: one row per (regime, criterion, n, draw)."""
    keys = ["regime", "criterion", "n", "draw"]
    return df.groupby(keys)[cols].mean().reset_index()


def by_n_table(df: pd.DataFrame, regime: str, law: str) -> pd.DataFrame:
    d = df[(df.regime == regime) & df[f"{law}_exp"].notna()]
    cols = [f"{law}_{m}" for m in METRICS if f"{law}_{m}" in d.columns] + [f"{law}_regret", f"{law}_regret_pct", f"{law}_cvar95_pct"]
    if law == "true":
        cols += ["disappointment", "disappointment_pct", "crit_value", "n_routes"]
    dl = d.groupby(["criterion", "n", "draw"])[cols].mean().reset_index()
    g = dl.groupby(["criterion", "n"])[cols]
    mean = g.mean().add_suffix("_mean")
    sd = g.std(ddof=1).add_suffix("_sd")
    out = pd.concat([mean, sd], axis=1).reset_index()
    out.insert(0, "law", law)
    out.insert(0, "regime", regime)
    out["n_draws"] = g.size().values
    return out


def paired(df: pd.DataFrame, regime: str, law: str, ref: str, test: list[str]) -> pd.DataFrame:
    """Paired difference of the regret (pp) of each test criterion against `ref`, per n: draw-level mean over cities."""
    d = df[(df.regime == regime) & df[f"{law}_exp"].notna()]
    pv = d.groupby(["criterion", "n", "draw"])[f"{law}_regret_pct"].mean().unstack("criterion")
    rows = []
    for n in sorted(pv.index.get_level_values("n").unique()):
        sub = pv.xs(n, level="n")
        if ref not in sub:
            continue
        for t in test:
            if t not in sub:
                continue
            x = (sub[t] - sub[ref]).dropna()
            if len(x) < 3:
                continue
            m, s = x.mean(), x.std(ddof=1)
            se = s / np.sqrt(len(x))
            from scipy import stats

            tc = stats.t.ppf(0.975, len(x) - 1)
            lo, hi = m - tc * se, m + tc * se
            # city-draw pairs: share of (city, draw) cells where the test criterion has the lower regret
            cc = d[d.n == n].pivot_table(index=["city", "draw"], columns="criterion", values=f"{law}_regret_pct")
            win = float((cc[t] < cc[ref] - 1e-9).mean()) if t in cc and ref in cc else np.nan
            tie = float(((cc[t] - cc[ref]).abs() <= 1e-9).mean()) if t in cc and ref in cc else np.nan
            rows.append(dict(regime=regime, law=law, ref=ref, criterion=t, n=n, diff_pp=m, ci_lo=lo, ci_hi=hi, n_draws=len(x),
                             win_share=win, tie_share=tie, wins=bool(hi < 0), competitive=bool(hi <= MARGIN_PP), loses=bool(lo > MARGIN_PP)))
    return pd.DataFrame(rows)


def city_table(df: pd.DataFrame, regime: str, law: str) -> pd.DataFrame:
    d = df[(df.regime == regime) & df[f"{law}_exp"].notna()]
    cols = [f"{law}_exp", f"{law}_regret_pct", f"{law}_cvar95", f"{law}_p_ot_day", f"{law}_ot_h", "disappointment_pct" if law == "true" else f"{law}_sd"]
    g = d.groupby(["city", "criterion", "n"])[cols]
    out = pd.concat([g.mean().add_suffix("_mean"), g.std(ddof=1).add_suffix("_sd")], axis=1).reset_index()
    out.insert(0, "law", law)
    out.insert(0, "regime", regime)
    return out


def md_table(df: pd.DataFrame, floatfmt: str = "{:.2f}") -> str:
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in df.itertuples(index=False):
        cells = []
        for v in r:
            if isinstance(v, (float, np.floating)):
                cells.append("" if np.isnan(v) else floatfmt.format(v))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def compact(tab: pd.DataFrame, metric: str, crits=MAIN, ns=(10, 20, 30, 60), sd=True) -> pd.DataFrame:
    """criterion x n table 'mean (sd)' of one metric from by_n_table output."""
    t = tab.set_index(["criterion", "n"])
    rows = []
    for c in crits:
        row = {"criterion": c}
        for n in ns:
            if (c, n) in t.index and f"{metric}_mean" in t.columns:
                m = t.loc[(c, n), f"{metric}_mean"]
                s = t.loc[(c, n), f"{metric}_sd"]
                row[f"n={n}"] = f"{m:.2f} ({s:.2f})" if sd else f"{m:.2f}"
        if len(row) > 1:
            rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------------------------------
# game
# ---------------------------------------------------------------------------------------------------------------


def game_tables():
    fs = sorted(RES.glob("ambiguity_game_*.csv"))
    if not fs:
        return None, None
    g = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    rows = []
    for (city, seed, crit), d in g.groupby(["city", "seed", "criterion"]):
        k = d.set_index("kind")
        if "SO_main" not in k.index or "NE_zmc" not in k.index:
            continue
        ne = k.loc["NE_zmc"]
        so = k.loc["SO_main"]
        eq = k.loc[[x for x in k.index if str(x).startswith("NE_")]]
        rows.append(dict(city=city, seed=seed, criterion=crit, eps=ne["eps"], served_share=ne.served_share, vehicles=ne.vehicles,
                         welfare_model=ne.welfare, welfare_true=ne.welfare_true, routing_cost_model=ne.routing_cost,
                         routing_cost_true=ne.routing_cost_true, so_served_share=so.served_share, so_welfare_model=so.welfare,
                         so_welfare_true=so.welfare_true,
                         poa_model=so.welfare / ne.welfare if ne.welfare > 0 else np.nan,
                         poa_true=so.welfare_true / ne.welfare_true if ne.welfare_true > 0 else np.nan,
                         poa_worst_model=so.welfare / eq.welfare.min() if eq.welfare.min() > 0 else np.nan,
                         poa_worst_true=so.welfare_true / eq.welfare_true.min() if eq.welfare_true.min() > 0 else np.nan,
                         curse_pct=100 * (ne.routing_cost - ne.routing_cost_true) / max(ne.routing_cost_true, 1e-9),
                         max_regret=ne.max_regret, converged=bool(ne.converged)))
    by_seed = pd.DataFrame(rows)
    num = [c for c in by_seed.columns if c not in ("city", "seed", "criterion", "converged")]
    gg = by_seed.groupby(["city", "criterion"])[num]
    agg = pd.concat([gg.mean(), gg.std(ddof=1).add_suffix("_sd")[[f"{c}_sd" for c in ("served_share", "welfare_true", "poa_model", "poa_true")]]], axis=1).reset_index()
    agg["n_seeds"] = gg.size().values
    return by_seed, agg


# ---------------------------------------------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------------------------------------------

COL = {"saa": "#222222", "wass_cv": "#0072B2", "wass_th": "#56B4E9", "wass_fg": "#7fb8d9", "cvar80": "#009E73", "cvar90": "#006b4d",
       "pbox_ud_80": "#F0A8C0", "pbox_ud_90": "#E58AB0", "pbox_ud_95": "#CC79A7", "pbox_ud_99": "#9c4a7c", "pbox_ud_emp": "#D55E00",
       "pbox_ind_80": "#E69F00", "pbox_ind_95": "#c27d00", "pbox_ind_emp": "#b0a060"}
LABEL = {"saa": "SAA", "wass_cv": "Wasserstein (CV)", "wass_th": "Wasserstein (theory)", "wass_fg": "Wasserstein (FG rate)",
         "cvar80": "CVaR 0.8", "cvar90": "CVaR 0.9", "pbox_ud_80": "p-box UD 0.80", "pbox_ud_90": "p-box UD 0.90",
         "pbox_ud_95": "p-box UD 0.95", "pbox_ud_99": "p-box UD 0.99", "pbox_ud_emp": "comonotone, no band",
         "pbox_ind_80": "p-box indep 0.80", "pbox_ind_95": "p-box indep 0.95", "pbox_ind_emp": "independent, no band"}


def figures(df: pd.DataFrame, tabs: dict, pairs: pd.DataFrame, gagg: pd.DataFrame | None):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
    crit_plot = ["saa", "wass_cv", "wass_th", "cvar90", "pbox_ud_80", "pbox_ud_95", "pbox_ud_99", "pbox_ud_emp", "pbox_ind_95"]
    # 1. regret and tail vs n, base law
    t = tabs[("base", "true")]
    fig, ax = plt.subplots(1, 3, figsize=(11, 3.3))
    for c in crit_plot:
        s = t[t.criterion == c].sort_values("n")
        if s.empty:
            continue
        ax[0].errorbar(s.n, s.true_regret_pct_mean, yerr=s.true_regret_pct_sd, color=COL[c], marker="o", ms=3, lw=1.2, capsize=2, label=LABEL[c])
        ax[1].plot(s.n, s.true_cvar95_pct_mean, color=COL[c], marker="o", ms=3, lw=1.2)
        ax[2].plot(s.n, s.disappointment_pct_mean, color=COL[c], marker="o", ms=3, lw=1.2)
    ax[0].set_title("regret of expected cost (% of best known)")
    ax[1].set_title("upper tail: CVaR 0.95 (% over best mean)")
    ax[2].set_title("disappointment (% of realised cost)")
    for a in ax:
        a.set_xlabel("training days n")
        a.set_xscale("log")
        a.set_xticks([10, 20, 30, 60])
        a.set_xticklabels([10, 20, 30, 60])
        a.minorticks_off()
    ax[2].axhline(0, color="grey", lw=0.6)
    ax[0].legend(fontsize=6, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "ambiguity_regret_vs_n.png", dpi=170)
    plt.close(fig)
    # 2. misspecification: regret by law at n = 20 and 60
    laws = [("base", "true", "true law"), ("base", "shift20", "shift +0.2"), ("base", "shift40", "shift +0.4"), ("base", "heavy", "train light, test heavy"),
            ("heavy", "heavy", "train and test heavy")]
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.3), sharey=True)
    for k, n in enumerate((20, 60)):
        w = 0.8 / len(crit_plot)
        for j, c in enumerate(crit_plot):
            ys, xs = [], []
            for i, (reg, law, _) in enumerate(laws):
                tt = tabs.get((reg, law))
                if tt is None:
                    continue
                s = tt[(tt.criterion == c) & (tt.n == n)]
                if len(s):
                    ys.append(s[f"{law}_regret_pct_mean"].iloc[0])
                    xs.append(i + (j - len(crit_plot) / 2) * w)
            ax[k].bar(xs, ys, width=w, color=COL[c], label=LABEL[c])
        ax[k].set_xticks(range(len(laws)))
        ax[k].set_xticklabels([l[2] for l in laws], rotation=12)
        ax[k].set_title(f"n = {n} training days")
    ax[0].set_ylabel("regret vs best known plan for that law (%)")
    ax[1].legend(fontsize=6, frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(FIG / "ambiguity_misspec.png", dpi=170)
    plt.close(fig)
    # 3. expected cost vs tail trade-off at n = 30, base law
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
    for k, n in enumerate((20, 60)):
        s = t[t.n == n]
        for c in MAIN:
            r = s[s.criterion == c]
            if r.empty:
                continue
            ax[k].scatter(r.true_regret_pct_mean, r.true_cvar95_pct_mean, color=COL[c], s=22)
            ax[k].annotate(LABEL[c], (r.true_regret_pct_mean.iloc[0], r.true_cvar95_pct_mean.iloc[0]), fontsize=5.5, xytext=(2, 2), textcoords="offset points")
        ax[k].set_xlabel("regret of expected cost (%)")
        ax[k].set_ylabel("CVaR 0.95 of daily cost (% over best known mean)")
        ax[k].set_title(f"n = {n}")
    fig.tight_layout()
    fig.savefig(FIG / "ambiguity_tradeoff.png", dpi=170)
    plt.close(fig)
    # 4. paired difference of p-box vs SAA by n (base, true law)
    pr = pairs[(pairs.regime == "base") & (pairs.law == "true") & (pairs.ref == "saa")]
    if len(pr):
        fig, ax = plt.subplots(1, 1, figsize=(5.2, 3.4))
        for c in ["pbox_ud_80", "pbox_ud_95", "pbox_ud_99", "pbox_ud_emp", "pbox_ind_95", "wass_cv", "cvar90"]:
            s = pr[pr.criterion == c].sort_values("n")
            if s.empty:
                continue
            ax.errorbar(s.n, s.diff_pp, yerr=[s.diff_pp - s.ci_lo, s.ci_hi - s.diff_pp], color=COL[c], marker="o", ms=3, capsize=2, lw=1, label=LABEL[c])
        ax.axhline(0, color="grey", lw=0.6)
        ax.set_xscale("log")
        ax.set_xticks([10, 20, 30, 60])
        ax.set_xticklabels([10, 20, 30, 60])
        ax.minorticks_off()
        ax.set_xlabel("training days n")
        ax.set_ylabel("regret minus SAA regret (pp), 95% CI over draws")
        ax.legend(fontsize=6, frameon=False)
        fig.tight_layout()
        fig.savefig(FIG / "ambiguity_paired_vs_saa.png", dpi=170)
        plt.close(fig)
    # 5. game
    if gagg is not None and len(gagg):
        crits = [c for c in ["pbox", "saa", "wass_th", "wass_e0.5"] if c in set(gagg.criterion)]
        cities = list(gagg.city.unique())
        fig, ax = plt.subplots(1, 3, figsize=(11, 3.2))
        w = 0.8 / len(crits)
        cc = {"pbox": "#CC79A7", "saa": "#222222", "wass_th": "#56B4E9", "wass_e0.5": "#0072B2"}
        for j, c in enumerate(crits):
            s = gagg[gagg.criterion == c].set_index("city").reindex(cities)
            x = np.arange(len(cities)) + (j - len(crits) / 2 + 0.5) * w
            ax[0].bar(x, s.served_share, width=w, color=cc[c], label=c)
            ax[1].bar(x, s.welfare_true, width=w, color=cc[c])
            ax[2].bar(x, s.poa_true, width=w, color=cc[c])
        for a, tl in zip(ax, ["served share at the unpriced equilibrium", "welfare at the equilibrium, routing cost under the true law", "price of anarchy (true-law welfare)"]):
            a.set_xticks(range(len(cities)))
            a.set_xticklabels(cities)
            a.set_title(tl, fontsize=7)
        ax[2].axhline(1, color="grey", lw=0.6)
        ax[0].legend(fontsize=6, frameon=False)
        fig.tight_layout()
        fig.savefig(FIG / "ambiguity_game.png", dpi=170)
        plt.close(fig)


# ---------------------------------------------------------------------------------------------------------------
# shift sweep (stored plans re-evaluated under a common congestion shock)
# ---------------------------------------------------------------------------------------------------------------


def shift_summary():
    f = RES / "ambiguity_shift_sweep.csv"
    if not f.exists():
        return None
    from scipy import stats

    d = pd.read_csv(f)
    ref = d[d.criterion == "saa"].rename(columns={"exp": "exp0", "cvar95": "cvar0"})[["city", "n", "draw", "delta", "exp0", "cvar0"]]
    m = d.merge(ref, on=["city", "n", "draw", "delta"])
    m["d_exp_pct"] = 100 * (m.exp - m.exp0) / m.exp0
    m["d_cvar_pct"] = 100 * (m.cvar95 - m.cvar0) / m.cvar0
    dl = m.groupby(["criterion", "n", "delta", "draw"])[["d_exp_pct", "d_cvar_pct"]].mean().reset_index()
    rows = []
    for (c, n, de), g in dl.groupby(["criterion", "n", "delta"]):
        row = dict(criterion=c, n=n, delta=de)
        for k in ("d_exp_pct", "d_cvar_pct"):
            x = g[k].to_numpy()
            se = x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 2 else np.nan
            tc = stats.t.ppf(0.975, len(x) - 1) if len(x) > 2 else np.nan
            row[k] = x.mean()
            row[k + "_lo"] = x.mean() - tc * se
            row[k + "_hi"] = x.mean() + tc * se
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(RES / "ambiguity_shift_summary.csv", index=False, float_format="%.5g")
    return out


def shift_figure(sh):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(2, 2, figsize=(9, 5.6), sharex=True)
    for j, n in enumerate((20, 60)):
        for c in ["wass_cv", "cvar90", "pbox_ud_80", "pbox_ud_95", "pbox_ud_99", "pbox_ud_emp", "pbox_ind_95"]:
            s = sh[(sh.criterion == c) & (sh.n == n)].sort_values("delta")
            if s.empty:
                continue
            ax[0, j].plot(s.delta, s.d_exp_pct, color=COL[c], marker="o", ms=3, lw=1.2, label=LABEL[c])
            ax[1, j].plot(s.delta, s.d_cvar_pct, color=COL[c], marker="o", ms=3, lw=1.2)
        ax[0, j].axhline(0, color="grey", lw=0.6)
        ax[1, j].axhline(0, color="grey", lw=0.6)
        ax[0, j].set_title(f"n = {n} training days")
        ax[1, j].set_xlabel("common congestion shock added at test time (multiplier units)")
    ax[0, 0].set_ylabel("expected cost vs SAA plan (%)")
    ax[1, 0].set_ylabel("CVaR 0.95 of daily cost vs SAA plan (%)")
    ax[0, 0].legend(fontsize=6, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "ambiguity_shift_sweep.png", dpi=170)
    plt.close(fig)


def main():
    plans = load_plans()
    orc = pd.read_csv(RES / "ambiguity_oracle.csv") if (RES / "ambiguity_oracle.csv").exists() else pd.DataFrame(columns=["city", "law", "exp"])
    bk = best_known(plans, orc)
    df = add_regrets(plans, bk)
    df.to_csv(RES / "ambiguity_plans.csv", index=False, float_format="%.7g")
    tabs, allt = {}, []
    for regime, law in [("base", "true"), ("base", "shift20"), ("base", "shift40"), ("base", "heavy"), ("heavy", "heavy")]:
        if ((df.regime == regime) & df[f"{law}_exp"].notna()).any():
            tabs[(regime, law)] = by_n_table(df, regime, law)
            allt.append(tabs[(regime, law)])
    pd.concat(allt, ignore_index=True).to_csv(RES / "ambiguity_summary_by_n.csv", index=False, float_format="%.6g")
    cts = [city_table(df, regime, law) for (regime, law) in tabs]
    pd.concat(cts, ignore_index=True).to_csv(RES / "ambiguity_summary_by_city.csv", index=False, float_format="%.6g")
    pairs = []
    test = [c for c in MAIN if c != "saa"]
    for (regime, law) in tabs:
        for ref in ("saa", "wass_cv"):
            pairs.append(paired(df, regime, law, ref, [c for c in test if c != ref]))
    pairs = pd.concat(pairs, ignore_index=True)
    pairs.to_csv(RES / "ambiguity_paired.csv", index=False, float_format="%.6g")
    by_seed, gagg = game_tables()
    if by_seed is not None:
        by_seed.to_csv(RES / "ambiguity_game_by_seed.csv", index=False, float_format="%.6g")
        gagg.to_csv(RES / "ambiguity_game_summary.csv", index=False, float_format="%.6g")
    figures(df, tabs, pairs, gagg)
    sh = shift_summary()
    if sh is not None:
        shift_figure(sh)
    write_md(df, tabs, pairs, gagg, by_seed, sh)
    print("summary written", len(df), "plan rows")


def first_n(pr: pd.DataFrame, flag: str) -> dict:
    """Smallest n at which `flag` holds and keeps holding for all larger n, per criterion."""
    out = {}
    for c, d in pr.groupby("criterion"):
        d = d.sort_values("n")
        ok = d[flag].to_numpy()
        ns = d.n.to_numpy()
        res = None
        for i in range(len(ok)):
            if ok[i:].all():
                res = int(ns[i])
                break
        out[c] = res if res is not None else "never (in the grid)"
    return out


def write_md(df, tabs, pairs, gagg, by_seed, sh=None):
    L = []
    nd = df[df.regime == "base"].draw.nunique()
    L.append("# Why probability boxes: out-of-sample comparison of ambiguity criteria (generated by experiments/run_ambiguity_summary.py)\n")
    L.append(f"Nine metro instances (22 customer zones, seed 0 of the BRL study), {nd} training draws per n, criteria planned with the same local-search + "
             "set-partitioning heuristic, 20000 held-out days per instance. Means over the nine cities, sd over draws (city-averaged). "
             "Regret and tail are in percent of the cost of the best known plan for the test law.\n")
    t = tabs[("base", "true")]
    for metric, title in [("true_regret_pct", "Regret of the expected cost on the true law (%), mean (sd over draws)"),
                          ("true_cvar95_pct", "Upper tail: CVaR 0.95 of the daily plan cost, % over the best known expected cost"),
                          ("true_p_ot_day", "Probability that at least one route runs overtime on a day"),
                          ("true_ot_h", "Expected overtime hours per day (sum over routes)"),
                          ("disappointment_pct", "Disappointment: criterion value minus realised expected cost, % of realised cost")]:
        L.append(f"### {title}\n")
        L.append(md_table(compact(t, metric)) + "\n")
    for ref in ("saa", "wass_cv"):
        pr = pairs[(pairs.regime == "base") & (pairs.law == "true") & (pairs.ref == ref)]
        L.append(f"### Paired regret difference against {ref} (pp, 95% CI over draws), true law\n")
        if len(pr):
            pv = pr[pr.criterion.isin(PBOX_UD + ["pbox_ud_emp", "pbox_ind_80", "pbox_ind_95", "pbox_ind_emp", "wass_cv", "wass_th", "cvar80", "cvar90"] )].copy()
            pv["cell"] = pv.apply(lambda r: f"{r.diff_pp:+.2f} [{r.ci_lo:+.2f}, {r.ci_hi:+.2f}]", axis=1)
            L.append(md_table(pv.pivot(index="criterion", columns="n", values="cell").reset_index().fillna("")) + "\n")
        fn = first_n(pr[pr.criterion.isin(PBOX_UD)], "competitive")
        fw = first_n(pr[pr.criterion.isin(PBOX_UD)], "wins")
        L.append(f"Smallest n from which the p-box is non-inferior to {ref} (95% CI upper end <= {MARGIN_PP} pp): {fn}. Smallest n from which it is better (CI upper end < 0): {fw}.\n")
    for (regime, law), tt in tabs.items():
        if (regime, law) == ("base", "true"):
            continue
        name = {"shift20": "common congestion shock +0.2 at test time (training days from the true law)", "shift40": "common congestion shock +0.4 at test time",
                "heavy": "heavy-tailed test days (Student-t, 3 df)" + (", light-tailed training days" if regime == "base" else ", heavy-tailed training days")}[law]
        L.append(f"### Misspecification: {name}; regret (%), mean (sd)\n")
        L.append(md_table(compact(tt, f"{law}_regret_pct")) + "\n")
        L.append(f"Tail (CVaR 0.95, % over best known expected cost):\n")
        L.append(md_table(compact(tt, f"{law}_cvar95_pct", sd=False)) + "\n")
    L.append("### Per city, n = 60, true law: regret (%) and probability of overtime (mean over draws)\n")
    ct = pd.read_csv(RES / "ambiguity_summary_by_city.csv")
    cc = ct[(ct.regime == "base") & (ct.law == "true") & (ct.n == 60) & ct.criterion.isin(["saa", "wass_cv", "cvar90", "pbox_ud_80", "pbox_ud_95", "pbox_ud_99", "pbox_ud_emp", "pbox_ind_95"])]
    L.append(md_table(cc.pivot(index="criterion", columns="city", values="true_regret_pct_mean").reset_index()) + "\n")
    L.append(md_table(cc.pivot(index="criterion", columns="city", values="true_p_ot_day_mean").reset_index(), "{:.3f}") + "\n")
    if sh is not None:
        for n in (20, 60):
            for k, ttl in (("d_exp_pct", "expected cost"), ("d_cvar_pct", "CVaR 0.95 of the daily cost")):
                s2 = sh[(sh.n == n) & sh.criterion.isin(["wass_cv", "cvar90", "pbox_ud_80", "pbox_ud_95", "pbox_ud_99", "pbox_ud_emp", "pbox_ind_95"])]
                pv = s2.pivot(index="criterion", columns="delta", values=k).reset_index()
                L.append(f"### Shift sweep, n = {n}: {ttl} of the plan relative to the SAA plan (%, negative = better than SAA), shock delta in columns\n")
                L.append(md_table(pv) + "\n")
    if gagg is not None:
        L.append("### Game: unpriced equilibrium and price of anarchy with other carrier criteria (mean over seeds)\n")
        cols = ["city", "criterion", "n_seeds", "served_share", "vehicles", "welfare_model", "welfare_true", "routing_cost_model", "routing_cost_true", "curse_pct", "so_served_share", "poa_model", "poa_true", "poa_worst_true", "max_regret"]
        L.append(md_table(gagg[[c for c in cols if c in gagg.columns]], "{:.3f}") + "\n")
    (RES / "ambiguity_summary.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()
