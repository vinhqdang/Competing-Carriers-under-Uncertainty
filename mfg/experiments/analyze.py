"""Figures and summary tables for the mean-field study (run after run_all.sh).

  PYTHONPATH=mfg/src python3 mfg/experiments/analyze.py
Writes mfg/figures/*.png, mfg/results/summary_*.csv and mfg/paper/numbers.tex (macros used by the manuscript).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from mfgcc import theory as th  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES, FIG, PAP = ROOT / "results", ROOT / "figures", ROOT / "paper"
FIG.mkdir(exist_ok=True)
CITY_ORDER = ["NewDelhi", "Cairo", "Moscow", "BuenosAires", "NewYork", "Bombay", "London", "Paris", "Berlin"]
LABEL = {"NewDelhi": "New Delhi", "BuenosAires": "Buenos Aires", "NewYork": "New York", "Bombay": "Mumbai"}
CMAP = plt.get_cmap("tab10")
COL = {c: CMAP(i) for i, c in enumerate(CITY_ORDER)}
macros: dict[str, str] = {}


def lab(c):
    return LABEL.get(c, c)


def macro(name, val, fmt="{:.2f}"):
    macros[name] = fmt.format(val) if not isinstance(val, str) else val


def slope_ci(df, ycol, kmin=4):
    """Per (city, seed) OLS slope of log y on log N over k >= kmin; mean and t-interval over seeds per city."""
    rows = []
    for (c, s), g in df[df.k >= kmin].groupby(["city", "seed"]):
        g = g[g[ycol] > 0]
        if len(g) >= 3:
            b = np.polyfit(np.log(g.N), np.log(g[ycol]), 1)[0]
            rows.append(dict(city=c, seed=s, slope=b))
    sl = pd.DataFrame(rows)
    out = []
    from scipy import stats
    for c, g in sl.groupby("city"):
        n = len(g)
        mu = g.slope.mean()
        hw = stats.t.ppf(0.975, n - 1) * g.slope.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
        out.append(dict(city=c, n_seeds=n, slope=mu, lo=mu - hw, hi=mu + hw))
    allm = sl.slope.mean()
    n = len(sl)
    hw = stats.t.ppf(0.975, n - 1) * sl.slope.std(ddof=1) / np.sqrt(n)
    out.append(dict(city="all", n_seeds=n, slope=allm, lo=allm - hw, hi=allm + hw))
    return pd.DataFrame(out), sl


def fig_gap(d, dh):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    ax = axes[0]
    for c in CITY_ORDER:
        g = d[d.city == c].groupby("N")[["gap_m", "QW_m"]].median()
        ax.loglog(g.index, g.gap_m / g.QW_m, "-o", ms=3, color=COL[c], label=lab(c))
    N = np.array([6, 1536])
    ax.loglog(N, 0.5 * (N / 6.0) ** -1.0, "k--", lw=0.8, label="slope -1")
    ax.loglog(N, 0.5 * (N / 6.0) ** -0.5, "k:", lw=0.8, label="slope -1/2")
    ax.set_xlabel("number of carriers N (6 segments, k replicas each)")
    ax.set_ylabel(r"$\|Q^N-Q^W\|_m\,/\,\|Q^W\|_m$ (median of 5 seeds)")
    ax.set_title("Replica splits, stylised hourly profile")
    ax.legend(fontsize=7, ncol=2)
    ax = axes[1]
    for c in CITY_ORDER:
        g = d[d.city == c].groupby("N")["ratio"].median()
        ax.semilogx(g.index, g.values, "-o", ms=3, color=COL[c])
        if dh is not None and len(dh):
            h = dh[dh.city == c].groupby("N")["ratio"].median()
            ax.semilogx(h.index, h.values, "x", ms=5, color=COL[c])
    ax.axhline(1.0, color="k", lw=0.6, ls="--")
    ax.set_xlabel("N")
    ax.set_ylabel(r"$\max_k|Q^N_k-Q^W_k|\,/\,s_N$")
    ax.set_title("Gap / largest carrier delivery (o replicas, x heterogeneous)")
    fig.tight_layout()
    fig.savefig(FIG / "mfg_gap.png", dpi=150)
    plt.close(fig)


def fig_tight():
    ns = np.unique(np.round(np.logspace(np.log10(2), 5, 40)).astype(int))
    g1 = [th.tight_family(n)["gap"] for n in ns]
    b1 = [th.tight_family(n)["bound"] for n in ns]
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    ax.loglog(ns, b1, "k-", lw=1, label=r"bound $\frac{1}{2}(\sum_i\|a_i^W\|^2)^{1/2}$ (Thm 4)")
    ax.loglog(ns, g1, "o", ms=3, color=CMAP(0), label=r"gap, $1-\cos\varphi_n=1/n$ (Prop 5)")
    for phi, mk in ((0.5, "s"), (0.2, "^"), (0.05, "v")):
        gp = [th.tight_family(n, phi=phi)["gap"] for n in ns]
        ax.loglog(ns, gp, mk, ms=3, label=fr"gap, fixed $\varphi={phi}$")
    ax.loglog(ns, 1 / ns, "k:", lw=0.8, label=r"$\bar s=1/n$")
    ax.set_xlabel("carriers per type n")
    ax.set_ylabel(r"$\|A^N-A^W\|_2$")
    ax.set_title("Two-zone family: the order n^(-1/2) is attained")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "mfg_tight.png", dpi=150)
    plt.close(fig)


def fig_toll_poa(d, dk):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    ax = axes[0]
    for df, ls, name in ((d, "-", r"$\kappa$ calibrated"), (dk, "--", r"$\kappa\times10$")):
        if df is None or not len(df):
            continue
        for c in CITY_ORDER:
            g = df[df.city == c].groupby("N")[["toll_gap_kinv", "toll_W_kinv"]].median()
            ax.loglog(g.index, g.toll_gap_kinv / g.toll_W_kinv, ls, color=COL[c], lw=1,
                      label=lab(c) if ls == "-" else None)
    ax.set_xlabel("N")
    ax.set_ylabel(r"$\|u^*_N-u^*_W\|_{\kappa^{-1}}/\|u^*_W\|_{\kappa^{-1}}$")
    ax.set_title("Observation-only charge vs Pigou charge\n(solid: calibrated, dashed: congestion x10)")
    ax.legend(fontsize=6, ncol=2)
    ax = axes[1]
    for c in CITY_ORDER:
        g = d[d.city == c].groupby("N")[["poa_N", "poa_W"]].median()
        ax.loglog(g.index, g.poa_N - 1, "-o", ms=3, color=COL[c])
        ax.axhline(float(g.poa_W.iloc[0] - 1), color=COL[c], lw=0.6, ls=":")
    ax.set_xlabel("N")
    ax.set_ylabel("PoA - 1 (welfare)")
    ax.set_title("Price of anarchy (dotted: mean-field value)")
    ax = axes[2]
    for df, ls in ((d, "-"), (dk, "--")):
        if df is None or not len(df):
            continue
        for c in CITY_ORDER:
            g = df[df.city == c].groupby("N")[["gain_N", "gain_W"]].median()
            ax.semilogx(g.index, 100 * g.gain_N, ls, color=COL[c], lw=1)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("N")
    ax.set_ylabel("gain of the observation-only charge (% of optimal welfare)")
    ax.set_title("Leader gain (solid: calibrated, dashed: congestion x10)")
    fig.tight_layout()
    fig.savefig(FIG / "mfg_toll_poa.png", dpi=150)
    plt.close(fig)


def fig_profile(dall):
    dp = dall[(dall["mode"] == "replica") & (dall.kappa_scale == 1.0) & (dall.seed <= 2)]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    amps = sorted(dp.amp.unique())
    ax = axes[0]
    w = 0.8 / len(amps)
    for j, a in enumerate(amps):
        g = dp[(dp.amp == a) & (dp.k == 1)].groupby("city")["poa_N"].median().reindex(CITY_ORDER)
        ax.bar(np.arange(len(CITY_ORDER)) + j * w, 100 * (g.values - 1), width=w, label=f"amp={a}")
    ax.set_xticks(np.arange(len(CITY_ORDER)) + 0.4)
    ax.set_xticklabels([lab(c) for c in CITY_ORDER], rotation=40, fontsize=7)
    ax.set_ylabel("PoA - 1 at N = 6 (%)")
    ax.set_title("Effect of the stylised hourly profile (amp = 0: flat)")
    ax.legend(fontsize=7)
    ax = axes[1]
    sl = []
    for a in amps:
        s, _ = slope_ci(dp[dp.amp == a], "gap_m")
        s["amp"] = a
        sl.append(s)
    sl = pd.concat(sl)
    for j, a in enumerate(amps):
        g = sl[(sl.amp == a) & (sl.city != "all")].set_index("city").reindex(CITY_ORDER)
        ax.errorbar(np.arange(len(CITY_ORDER)) + j * w, g.slope, yerr=[g.slope - g.lo, g.hi - g.slope], fmt="o",
                    ms=3, label=f"amp={a}")
    ax.axhline(-1, color="k", lw=0.6, ls="--")
    ax.axhline(-0.5, color="k", lw=0.6, ls=":")
    ax.set_xticks(np.arange(len(CITY_ORDER)) + 0.4)
    ax.set_xticklabels([lab(c) for c in CITY_ORDER], rotation=40, fontsize=7)
    ax.set_ylabel("log-log slope of the gap in N (95% CI, 3 seeds)")
    ax.set_title("Convergence rate under different profiles")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "mfg_profile.png", dpi=150)
    plt.close(fig)
    sl.to_csv(RES / "summary_slopes_profile.csv", index=False)
    return sl


def fig_gamma():
    p = RES / "gamma.csv"
    if not p.exists():
        return None
    g = pd.read_csv(p)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    ax = axes[0]
    for c in CITY_ORDER:
        h = g[(g.city == c) & (g.k == 256)].groupby("delta")[["dev_W_m", "bound_W", "dev_N_m"]].median()
        ax.plot(h.index, h.dev_W_m / h.bound_W, "-o", ms=3, color=COL[c], label=lab(c))
    ax.axhline(1, color="k", lw=0.6, ls="--")
    ax.set_xlabel(r"belief width $\delta$ (in median lots)")
    ax.set_ylabel(r"$\|Q^{W,\delta}-Q^W\|_m\,/\,\delta\|w\|_m$")
    ax.set_title("Gamma-maximin shift of the mean-field aggregate (bound = 1)")
    ax.legend(fontsize=6, ncol=2)
    ax = axes[1]
    for c in CITY_ORDER:
        h = g[(g.city == c) & (g.k == 256)].groupby("delta")[["wloss_gamma", "wloss_bound", "SW_opt"]].median()
        ax.loglog(h.index, 100 * h.wloss_gamma / h.SW_opt, "-o", ms=3, color=COL[c])
        ax.loglog(h.index, 100 * h.wloss_bound / h.SW_opt, ":", color=COL[c], lw=0.8)
    ax.set_xlabel(r"$\delta$")
    ax.set_ylabel("welfare loss of ARP under cautious carriers (% of optimum)")
    ax.set_title("Loss (solid) and the bound of Prop. 15(d) (dotted)")
    fig.tight_layout()
    fig.savefig(FIG / "mfg_gamma.png", dpi=150)
    plt.close(fig)
    return g


def fig_width():
    p = RES / "width.csv"
    if not p.exists():
        return None
    w = pd.read_csv(p)
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for c in CITY_ORDER:
        h = w[w.city == c]
        ax.loglog(h.N, h.width_rel, "-o", ms=3, color=COL[c], label=lab(c))
    ax.set_xlabel("N")
    ax.set_ylabel("absorption width bound / mean coordinate demand")
    ax.set_title("Belief width needed for E-admissible rounding (Cor. 16)")
    ax.legend(fontsize=6, ncol=2)
    fig.tight_layout()
    fig.savefig(FIG / "mfg_width.png", dpi=150)
    plt.close(fig)
    return w


def fig_paths_flat():
    out = {}
    p = RES / "arp_paths.csv"
    f = RES / "flat_rule.csv"
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    if p.exists():
        a = pd.read_csv(p)
        ax = axes[0]
        for (c, ks, k, own), h in a.groupby(["city", "kappa_scale", "k", "own"]):
            if not own or k not in (1, 256):
                continue
            ax.semilogy(h["round"], h.dist_kinv / h.dist_kinv.iloc[0], "-o" if ks == 1 else "--s", ms=3,
                        color=COL[c], label=f"{lab(c)}, kappa x{int(ks)}, N={6 * k}")
        ax.set_xlabel("round")
        ax.set_ylabel(r"$\|u^t-u^*_N\|_{\kappa^{-1}}$ (relative)")
        ax.set_title("Observation-only rule, Nash carriers")
        ax.legend(fontsize=6)
        out["paths"] = a
    if f.exists():
        fl = pd.read_csv(f)
        ax = axes[1]
        for ks, ls in ((1.0, "-"), (10.0, "--")):
            h = fl[fl.kappa_scale == ks].groupby("k")[["gain_flat", "gain_obs"]].median()
            ax.semilogx(6 * h.index, 100 * h.gain_flat, ls + "o", ms=3, color=CMAP(3),
                        label=f"Omega flat rule (subsidy), kappa x{int(ks)}")
            ax.semilogx(6 * h.index, 100 * h.gain_obs, ls + "s", ms=3, color=CMAP(0),
                        label=f"observation-only Pigou, kappa x{int(ks)}")
        ax.axhline(0, color="k", lw=0.5)
        ax.set_xlabel("N")
        ax.set_ylabel("welfare gain (% of optimum), median over cities and seeds")
        ax.set_title("Which observation-only rule, by market size")
        ax.legend(fontsize=6)
        out["flat"] = fl
    fig.tight_layout()
    fig.savefig(FIG / "mfg_arp.png", dpi=150)
    plt.close(fig)
    return out


def fig_cost():
    p = RES / "solver_cost.csv"
    if not p.exists():
        return None
    s = pd.read_csv(p)
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for (mode, eq), h in s.groupby(["mode", "eq"]):
        h = h.groupby("N")[["time_s", "clarabel_time_s"]].median()
        ax.loglog(h.index, h.clarabel_time_s, "-o", ms=3, label=f"interior point, {mode}, {eq}")
        ax.loglog(h.index, h.time_s, "--s", ms=3, label=f"Frank-Wolfe, {mode}, {eq}")
    ax.set_xlabel("N")
    ax.set_ylabel("seconds (median of two cities)")
    ax.set_title("Cost of one equilibrium solve")
    ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(FIG / "mfg_cost.png", dpi=150)
    plt.close(fig)
    return s


def main():
    dall = pd.read_csv(RES / "gap.csv")
    d = dall[(dall["mode"] == "replica") & (dall.amp == 1.0) & (dall.kappa_scale == 1.0)]
    dk = dall[(dall["mode"] == "replica") & (dall.amp == 1.0) & (dall.kappa_scale == 10.0)]
    dh = dall[dall["mode"] == "hetero"]
    fig_gap(d, dh)
    fig_tight()
    fig_toll_poa(d, dk)
    slp = fig_profile(dall)
    gam = fig_gamma()
    wid = fig_width()
    pf = fig_paths_flat()
    cost = fig_cost()
    # ---- summaries
    s_gap, sl = slope_ci(d, "gap_m")
    s_gap.to_csv(RES / "summary_slopes_gap.csv", index=False)
    s_toll, _ = slope_ci(d, "toll_gap_kinv")
    s_toll.to_csv(RES / "summary_slopes_toll.csv", index=False)
    s_tollk, _ = slope_ci(dk, "toll_gap_kinv") if len(dk) else (None, None)
    a = s_gap[s_gap.city == "all"].iloc[0]
    macro("SlopeGap", a.slope)
    macro("SlopeGapLo", a.lo)
    macro("SlopeGapHi", a.hi)
    pc = s_gap[s_gap.city != "all"]
    macro("SlopeGapCityMin", pc.slope.min())
    macro("SlopeGapCityMax", pc.slope.max())
    a = s_toll[s_toll.city == "all"].iloc[0]
    macro("SlopeToll", a.slope)
    macro("SlopeTollLo", a.lo)
    macro("SlopeTollHi", a.hi)
    if s_tollk is not None:
        a = s_tollk[s_tollk.city == "all"].iloc[0]
        macro("SlopeTollK", a.slope)
        macro("SlopeTollKLo", a.lo)
        macro("SlopeTollKHi", a.hi)
    # slope of the gap against the share s itself (O(s) means slope one)
    rows_s = []
    for (c_, sd), g_ in d[d.k >= 4].groupby(["city", "seed"]):
        rows_s.append(np.polyfit(np.log(g_.s), np.log(g_.gap_inf), 1)[0])
    rows_s = np.array(rows_s)
    from scipy import stats as _st
    hw = _st.t.ppf(0.975, len(rows_s) - 1) * rows_s.std(ddof=1) / np.sqrt(len(rows_s))
    macro("SlopeS", rows_s.mean())
    macro("SlopeSLo", rows_s.mean() - hw)
    macro("SlopeSHi", rows_s.mean() + hw)
    rows_s = []
    for (c_, sd), g_ in d[d.k >= 4].groupby(["city", "seed"]):
        rows_s.append(np.polyfit(np.log(g_.N), np.log(g_.s), 1)[0])
    macro("SlopeSN", float(np.mean(rows_s)))
    macro("RatioMed", d.ratio.median())
    macro("RatioMax", d.ratio.max())
    macro("RatioMin", d.ratio.min())
    macro("RatioMaxBig", d[d.k >= 16].ratio.max())
    macro("SqrtOK", f"{int((d.gap_m <= d.sqrt_bound * (1 + 1e-9)).sum())}/{len(d)}", "{}")
    macro("SqrtRatioMax", (d.gap_m / d.sqrt_bound).max())
    macro("TollOK", f"{int((d.toll_gap_kinv <= d.toll_bound + 1e-9).sum())}/{len(d)}", "{}")
    macro("WelfOK", f"{int((d.wloss_fp <= d.wloss_bound + 1e-6).sum())}/{len(d)}", "{}")
    macro("WlossRatioMax", (d.wloss_fp / d.wloss_bound).max(), "{:.3f}")
    macro("RhoMin", d.rho.min(), "{:.3f}")
    macro("RhoMax", d.rho.max(), "{:.3f}")
    if len(dk):
        macro("RhoKMin", dk.rho.min(), "{:.3f}")
        macro("RhoKMax", dk.rho.max(), "{:.3f}")
    macro("ErrMax", (d.err_inf / d.gap_inf).max(), "{:.3f}")
    g6 = d[d.k == 1]
    macro("PoaSixMed", 100 * (g6.poa_N.median() - 1), "{:.1f}")
    macro("PoaSixMin", 100 * (g6.poa_N.min() - 1), "{:.1f}")
    macro("PoaSixMax", 100 * (g6.poa_N.max() - 1), "{:.1f}")
    gb = d[d.k == 256]
    macro("PoaBigMed", 100 * (gb.poa_N.median() - 1), "{:.3f}")
    macro("PoaWMed", 100 * (d.poa_W.median() - 1), "{:.3f}")
    macro("PoaWMax", 100 * (d.poa_W.max() - 1), "{:.3f}")
    macro("GainSixMed", 100 * g6.gain_N.median(), "{:.2f}")
    macro("GainBigMed", 100 * gb.gain_N.median(), "{:.3f}")
    macro("GainWMed", 100 * d.gain_W.median(), "{:.3f}")
    if len(dk):
        macro("GainKSixMed", 100 * dk[dk.k == 1].gain_N.median(), "{:.2f}")
        macro("GainKBigMed", 100 * dk[dk.k == 256].gain_N.median(), "{:.2f}")
        macro("GainKWMed", 100 * dk.gain_W.median(), "{:.2f}")
        macro("PoaKWMed", 100 * (dk.poa_W.median() - 1), "{:.2f}")
        # first N at which the observation-only gain is positive for every city/seed
        pos = dk.groupby("k").gain_N.min()
        macro("GainKPosN", 6 * int(pos[pos > 0].index.min()) if (pos > 0).any() else float("nan"), "{}")
    pos = d.groupby("k").gain_N.min()
    macro("GainPosN", 6 * int(pos[pos > 0].index.min()) if (pos > 0).any() else "none", "{}")
    if len(dh):
        s_h, _ = slope_ci(dh, "gap_m", kmin=2)
        s_h.to_csv(RES / "summary_slopes_hetero.csv", index=False)
        a = s_h[s_h.city == "all"].iloc[0]
        macro("SlopeHet", a.slope)
        macro("SlopeHetLo", a.lo)
        macro("SlopeHetHi", a.hi)
        macro("RatioHetMax", dh.ratio.max())
        macro("RatioHetMed", dh.ratio.median())
        macro("HetErrMax", (dh.err_inf / dh.gap_inf).max(), "{:.3f}")
        macro("HetSqrtOK", f"{int((dh.gap_m <= dh.sqrt_bound * (1 + 1e-9)).sum())}/{len(dh)}", "{}")
    if slp is not None:
        for a_ in sorted(slp.amp.unique()):
            r = slp[(slp.amp == a_) & (slp.city == "all")].iloc[0]
            tag = {0.0: "Zero", 0.5: "Half", 1.0: "One", 1.5: "OneHalf"}[a_]
            macro(f"SlopeAmp{tag}", r.slope)
        dp = dall[(dall["mode"] == "replica") & (dall.kappa_scale == 1.0) & (dall.seed <= 2) & (dall.k == 1)]
        for a_ in sorted(dp.amp.unique()):
            tag = {0.0: "Zero", 0.5: "Half", 1.0: "One", 1.5: "OneHalf"}[a_]
            macro(f"PoaAmp{tag}", 100 * (dp[dp.amp == a_].poa_N.median() - 1), "{:.1f}")
    if gam is not None:
        macro("GamDevMax", (gam.dev_W_m / gam.bound_W).max(), "{:.3f}")
        macro("GamDevMed", (gam.dev_W_m / gam.bound_W).median(), "{:.3f}")
        macro("GamLossOK", f"{int((gam.wloss_gamma <= gam.wloss_bound + 1e-6).sum())}/{len(gam)}", "{}")
        macro("GamLossRatioMed", (gam.wloss_gamma / gam.wloss_bound).median(), "{:.3f}")
        h = gam[gam.delta == 1.0]
        macro("GamLossOneMed", 100 * (h.wloss_gamma / h.SW_opt).median(), "{:.2f}")
        h = gam[gam.delta == 4.0]
        macro("GamLossFourMed", 100 * (h.wloss_gamma / h.SW_opt).median(), "{:.2f}")
        macro("GamTollOK", f"{int((gam.toll_shift_kinv <= gam.toll_shift_bound + 1e-9).sum())}/{len(gam)}", "{}")
    if wid is not None:
        macro("WidthSixMed", wid[wid.k == 1].width_rel.median(), "{:.2f}")
        macro("WidthBigMed", wid[wid.k == 4096].width_rel.median(), "{:.3f}")
        macro("Dmin", int(wid.d.min()), "{}")
        macro("Dmax", int(wid.d.max()), "{}")
    if "paths" in pf:
        a_ = pf["paths"]
        a_ = a_[(a_["round"] >= 1) & np.isfinite(a_.step_ratio) & (a_.dist_kinv > 1e-9)]
        macro("PathRatioMax", (a_.step_ratio / a_.rho).max(), "{:.3f}")
    if "flat" in pf:
        fl = pf["flat"]
        for ks, tag in ((1.0, ""), (10.0, "K")):
            h = fl[fl.kappa_scale == ks]
            if len(h):
                macro(f"Flat{tag}SixMed", 100 * h[h.k == 1].gain_flat.median(), "{:.2f}")
                macro(f"Flat{tag}BigMed", 100 * h[h.k == 256].gain_flat.median(), "{:.3f}")
                macro(f"Obs{tag}SixMed", 100 * h[h.k == 1].gain_obs.median(), "{:.2f}")
                macro(f"Flat{tag}DistBig", (h[h.k == 256].dist_to_pigou_kinv / h[h.k == 256].pigou_kinv).median(),
                      "{:.3f}")
    if cost is not None:
        c = cost
        macro("FWItersW", int(c[(c.eq == "wardrop")].iters.median()), "{}")
        macro("FWItersN", int(c[(c.eq == "nash")].iters.median()), "{}")
    macro("NRows", len(d), "{}")
    macro("NRowsHet", len(dh), "{}")
    macro("NRowsK", len(dk), "{}")
    with open(PAP / "numbers.tex", "w") as fh:
        fh.write("% generated by mfg/experiments/analyze.py; do not edit\n")
        for k_, v in sorted(macros.items()):
            fh.write(f"\\newcommand{{\\{k_}}}{{{v}}}\n")
    # per-city table
    rows = []
    for c in CITY_ORDER:
        g = d[d.city == c]
        r = s_gap[s_gap.city == c].iloc[0]
        rows.append(dict(city=lab(c), d=int(g.d.median()), rho=g.rho.median(), slope=r.slope, lo=r.lo, hi=r.hi,
                         ratio_med=g.ratio.median(), ratio_max=g.ratio.max(),
                         poa6=100 * (g[g.k == 1].poa_N.median() - 1), poaW=100 * (g.poa_W.median() - 1),
                         toll6=(g[g.k == 1].toll_gap_kinv / g[g.k == 1].toll_W_kinv).median(),
                         toll1536=(g[g.k == 256].toll_gap_kinv / g[g.k == 256].toll_W_kinv).median()))
    tab = pd.DataFrame(rows)
    tab.to_csv(RES / "summary_cities.csv", index=False)
    with open(PAP / "table_cities.tex", "w") as fh:
        fh.write("% generated by mfg/experiments/analyze.py\n")
        for r in rows:
            fh.write(f"{r['city']} & {r['d']} & {r['rho']:.3f} & {r['slope']:.2f} [{r['lo']:.2f}, {r['hi']:.2f}] & "
                     f"{r['ratio_med']:.2f} & {r['ratio_max']:.2f} & {r['poa6']:.1f} & {r['poaW']:.3f} & "
                     f"{r['toll6']:.3f} & {r['toll1536']:.4f}\\\\\n")
    print("\n".join(f"{k_} = {v}" for k_, v in sorted(macros.items())))


if __name__ == "__main__":
    main()
