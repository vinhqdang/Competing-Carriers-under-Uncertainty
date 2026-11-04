"""Tables, figures and macros for fees, free entry and further externalities (after run_fees.py, run_entry.py
[and SWEEP=1], run_extern.py).

  PYTHONPATH=mfg/src python3 mfg/experiments/analyze_ext.py
Writes mfg/results/summary_ext_*.csv, mfg/figures/mfg_entry.png, mfg/figures/mfg_extern.png,
mfg/paper/numbers_ext.tex and mfg/paper/table_{fees,entry,extern,extparams}.tex.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES, FIG, PAP = ROOT / "results", ROOT / "figures", ROOT / "paper"
CITY_ORDER = ["NewDelhi", "Cairo", "Moscow", "BuenosAires", "NewYork", "Bombay", "London", "Paris", "Berlin"]
LABEL = {"NewDelhi": "New Delhi", "BuenosAires": "Buenos Aires", "NewYork": "New York", "Bombay": "Mumbai"}
WORD = {6: "Six", 24: "TwentyFour", 192: "OneNinetyTwo", 1536: "Big"}
macros: dict[str, str] = {}


def macro(name, val, fmt="{:.2f}"):
    macros[name] = val if isinstance(val, str) else fmt.format(val)


def lab(c):
    return LABEL.get(c, c)


def med(x):
    return float(np.nanmedian(x))


# ------------------------------------------------------------------ Item 1: fees at a fixed number of carriers
def fees():
    d = pd.read_csv(RES / "fees.csv")
    d["def_pct"] = 100.0 * d.deficit / d.SW
    d["share_pct"] = 100.0 * d.flat_share
    d["ep_loss"] = 100.0 * (d.SW - d.SW_expost) / d.SW_opt
    d["kept_pct"] = 100.0 * (d.profit_total - d.deficit) / d.Pi0  # carriers' profit after the fee / no-charge profit
    n = d.groupby(["city", "seed"]).ngroups
    for N, w in WORD.items():
        x = d[d.N == N]
        macro(f"Fee{w}Def", med(x.def_pct), "{:.0f}" if N < 192 else "{:.1f}")
        macro(f"Fee{w}Share", med(x.share_pct), "{:.0f}")
        macro(f"Fee{w}ShareMin", float(x.share_pct.min()), "{:.0f}")
        macro(f"Fee{w}ShareMax", float(x.share_pct.max()), "{:.0f}")
        for s in ("flat", "fleet", "aggregate"):
            col = "aggregate_ok" if s == "aggregate" else f"{s}_ok"
            macro(f"Fee{w}{s.capitalize()}OK", f"{int(x[col].sum())}/{len(x)}")
        macro(f"Fee{w}Kept", med(x.kept_pct), "{:.0f}")
        macro(f"Fee{w}EpLoss", med(x.ep_loss), "{:.2f}")
        macro(f"Fee{w}Sub", med(100 * x.neg_share), "{:.0f}")
    macro("FeeInst", str(n))
    bad = sorted({lab(c) for c in d[(d.N == 6) & (d.aggregate_ok == 0)].city})
    macro("FeeAggFailCities", ", ".join(bad) if bad else "none")
    # city table: median share of profit; counts flat/fleet/aggregate participation out of 5 seeds
    rows = []
    for c in CITY_ORDER:
        cells = [lab(c)]
        for N in (6, 24, 192, 1536):
            x = d[(d.city == c) & (d.N == N)]
            if med(x.def_pct) <= 0:
                cells.append(r"\multicolumn{2}{c}{tax}")
                continue
            cells.append(f"{med(x.share_pct):.0f}")
            cells.append(f"{int(x.flat_ok.sum())}/{int(x.fleet_ok.sum())}/{int(x.aggregate_ok.sum())}")
        rows.append(" & ".join(cells) + r" \\")
    (PAP / "table_fees.tex").write_text("\n".join(rows)[:-3] + "\n")
    d.groupby(["city", "N"])[["def_pct", "share_pct", "flat_ok", "fleet_ok", "aggregate_ok", "kept_pct",
                               "ep_loss"]].median().to_csv(RES / "summary_ext_fees.csv")
    return d


# ------------------------------------------------------------------ Item 2: free entry
RULES = [("none", 1.0, "no charge"), ("obs", 1.0, "observation-only"), ("pm", 1.0, "Pigou minus market power"),
         ("pmfee", 1.0, "\\quad with recovery fee"), ("obs", 0.5, "$0.5\\,\\kappa Q$"), ("obs", 1.5, "$1.5\\,\\kappa Q$")]


def entry_frame(f):
    e = pd.read_csv(f)
    base = e[e.rule == "none"].set_index(["city", "seed", "k0"])
    idx = e.set_index(["city", "seed", "k0"]).index
    e["SW_none"] = base.SW.reindex(idx).to_numpy()
    e["N_none"] = base.N.reindex(idx).to_numpy()
    e["dSW"] = 100.0 * (e.SW - e.SW_none) / e.SW_none
    e["fb_pct"] = 100.0 * e.SW / e.SW_fb
    e["N_ratio"] = e.N / e.N_none
    e["R_pct"] = 100.0 * (e.R + e.fee_rev) / e.SW_none
    e["id_err"] = np.abs(e.SW - (e.CS + e.R + e.fee_rev)) / e.SW_none.abs()
    return e


def entry():
    e = entry_frame(RES / "entry.csv")
    sw = entry_frame(RES / "entry_sweep.csv") if (RES / "entry_sweep.csv").exists() else None
    macro("EntInst", str(e.groupby(["city", "seed"]).ngroups))
    macro("EntIdErr", f"{e.id_err.max():.0e}")
    macro("EntErrMax", f"{e.err.max():.0e}")
    macro("EntResidMax", f"{e[e.rule.isin(['pm', 'pmfee'])].resid.max():.0e}")
    rows = []
    for rule, th, name in RULES:
        cells = [name]
        for k0 in (1, 4, 32):
            x = e[(e.rule == rule) & (e.theta == th) & (e.k0 == k0)]
            cells += [f"{med(x.N):.1f}", f"{med(x.active):.0f}" if rule == "pmfee" else f"{med(x.active):.0f}",
                      f"{med(x.dSW):+.1f}" if rule != "none" else "0", f"{med(x.R_pct):+.1f}"]
            w = WORD[6 * k0]
            key = {"none": "None", "obs": "Obs", "pm": "Pm", "pmfee": "Pmfee"}[rule] + (
                "" if th == 1.0 else ("Half" if th == 0.5 else "OneHalf"))
            macro(f"Ent{w}{key}N", med(x.N), "{:.1f}")
            macro(f"Ent{w}{key}dSW", med(x.dSW), "{:+.1f}")
            macro(f"Ent{w}{key}dSWMin", float(x.dSW.min()), "{:+.1f}")
            macro(f"Ent{w}{key}dSWMax", float(x.dSW.max()), "{:+.1f}")
            macro(f"Ent{w}{key}Act", med(x.active), "{:.0f}")
            macro(f"Ent{w}{key}ActMin", float(x.active.min()), "{:.0f}")
            macro(f"Ent{w}{key}Closed", f"{int((x.active == 0).sum())}/{len(x)}")
            macro(f"Ent{w}{key}R", med(x.R_pct), "{:+.1f}")
            macro(f"Ent{w}{key}FB", med(x.fb_pct), "{:.1f}")
            macro(f"Ent{w}{key}Ratio", med(x.N_ratio), "{:.2f}")
            macro(f"Ent{w}{key}NInt", med(x.N_int), "{:.0f}")
            if rule == "obs" and th == 1.0:
                pm = e[(e.rule == "pm") & (e.k0 == k0)].set_index(["city", "seed"])
                ob = x.set_index(["city", "seed"])
                macro(f"Ent{w}ObsBeatsPm", f"{int((ob.SW >= pm.SW.reindex(ob.index) - 1e-9).sum())}/{len(ob)}")
                best = e[(e.rule == "obs") & (e.k0 == k0)].pivot_table(index=["city", "seed"], columns="theta",
                                                                        values="SW")
                macro(f"Ent{w}ObsBest", f"{int((best.idxmax(axis=1) == 1.0).sum())}/{len(best)}")
                nn = e[(e.rule == "none") & (e.k0 == k0)].set_index(["city", "seed"])
                macro(f"Ent{w}ObsBeatsNone", f"{int((ob.SW >= nn.SW.reindex(ob.index) - 1e-9).sum())}/{len(ob)}")
            if rule == "pmfee":
                nn = e[(e.rule == "none") & (e.k0 == k0)].set_index(["city", "seed"])
                pf = x.set_index(["city", "seed"])
                macro(f"Ent{w}PmfeeBeatsNone", f"{int((pf.SW > nn.SW.reindex(pf.index)).sum())}/{len(pf)}")
        rows.append(" & ".join(cells) + r" \\")
    (PAP / "table_entry.tex").write_text("\n".join(rows)[:-3] + "\n")
    # Mankiw-Whinston test
    mw = e[e.rule == "none"].copy()
    mw["mw_gain"] = 100.0 * (mw.SW_lam_best.astype(float) - mw.SW_lam1.astype(float)) / mw.SW_none
    for k0 in (1, 4, 32):
        x = mw[mw.k0 == k0]
        w = WORD[6 * k0]
        macro(f"Ent{w}LamBest", med(x.lam_best.astype(float)), "{:.2f}")
        macro(f"Ent{w}LamBestMax", float(x.lam_best.astype(float).max()), "{:.2f}")
        macro(f"Ent{w}MwGain", med(x.mw_gain), "{:.2f}")
        macro(f"Ent{w}NLam", med(x.N_lam_best.astype(float)), "{:.0f}")
        macro(f"Ent{w}MwExcess", f"{int((x.lam_best.astype(float) < 1.0).sum())}/{len(x)}")
    e.to_csv(RES / "summary_ext_entry.csv", index=False)
    # figure
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8))
    allE = pd.concat([e, sw]) if sw is not None else e
    col = {"none": "k", "obs": "tab:red", "pm": "tab:blue", "pmfee": "tab:green"}
    for rule, th, name in RULES[:4]:
        x = allE[(allE.rule == rule) & (allE.theta == th)].groupby("N0")
        n0 = np.array(sorted(x.groups))
        for ax, v in zip(axes, ("N", "dSW")):
            m_ = x[v].median().reindex(n0)
            lo, hi = x[v].quantile(0.25).reindex(n0), x[v].quantile(0.75).reindex(n0)
            ax.plot(n0, m_, "o-", color=col[rule], label=name.replace("\\quad ", "").replace("$", ""))
            ax.fill_between(n0, lo, hi, color=col[rule], alpha=0.15)
    axes[0].plot([6, 384], [6, 384], ":", color="grey", lw=0.8)
    axes[0].set(xscale="log", yscale="log", xlabel="calibration $N_0$ (fixed cost $F$ decreases to the right)",
                ylabel="free-entry number of carriers $N^*$")
    axes[1].set(xscale="log", xlabel="calibration $N_0$", ylabel="welfare net of fixed costs, % change vs no charge")
    axes[1].axhline(0, color="grey", lw=0.6)
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "mfg_entry.png", dpi=150)
    plt.close(fig)
    return e


# ------------------------------------------------------------------ Item 3: further externalities
def extern():
    d = pd.read_csv(RES / "extern.csv")
    d["N"] = pd.to_numeric(d["N"], errors="coerce")  # inf for the mean field
    key = ["city", "seed"]
    ref = d[(d.regime == "W") & (d.rule == "cong") & (d.variant == "base")].set_index(key).SW  # SW^opt (no ext.)
    d["SW_cong_opt"] = ref.reindex(d.set_index(key).index).to_numpy()
    d["loss_sw"] = 100.0 * (d.SW_ext_opt - d.SW_ext) / d.SW_cong_opt  # % of the congestion-only optimal welfare
    W = d[(d.regime == "W") & (d.variant == "base")]
    nb = W[W.rule == "none"].set_index(key)
    nb_per = nb[["air", "clim", "noise", "cong", "E"]].div(nb.Q_total, axis=0)
    macro("ExtInst", str(len(nb)))
    for c in ("air", "clim", "noise", "cong", "E"):
        macro(f"ExtPer{c.capitalize()}", med(nb_per[c]), "{:.3f}")
        macro(f"ExtPer{c.capitalize()}Min", nb_per[c].groupby("city").median().min(), "{:.3f}")
        macro(f"ExtPer{c.capitalize()}Max", nb_per[c].groupby("city").median().max(), "{:.3f}")
    macro("ExtKQ", med(nb.kQ_per_del), "{:.3f}")
    ratio = nb_per.E / nb.kQ_per_del
    macro("ExtRatioKQ", med(ratio), "{:.1f}")
    macro("ExtRatioKQMin", ratio.groupby("city").median().min(), "{:.1f}")
    macro("ExtRatioKQMax", ratio.groupby("city").median().max(), "{:.1f}")
    macro("ExtShareCong", med(100 * nb_per.cong / nb_per.E), "{:.0f}")
    macro("ExtShareFee", med(100 * nb_per.E / nb.fee), "{:.0f}")
    macro("ExtShareFeeMin", (100 * nb_per.E / nb.fee).groupby("city").median().min(), "{:.0f}")
    macro("ExtShareFeeMax", (100 * nb_per.E / nb.fee).groupby("city").median().max(), "{:.0f}")
    macro("ExtVkmDel", med(nb.vkm / nb.Q_total), "{:.2f}")
    macro("ExtVkmInShare", med(100 * nb.vkm_in / nb.vkm), "{:.0f}")
    piv = W.pivot_table(index=key, columns="rule", values="loss_sw")
    for r_, nm in (("none", "None"), ("cong", "Cong"), ("ext_ebar", "Ebar"), ("ext_match", "Match")):
        macro(f"ExtLoss{nm}", med(piv[r_]), "{:.2f}")
        macro(f"ExtLoss{nm}Max", float(piv[r_].max()), "{:.1f}")
    pivE = W.pivot_table(index=key, columns="rule", values="loss_pct")  # % of the extended optimum
    macro("ExtLossNoneExtPct", med(pivE["none"]), "{:.1f}")
    macro("ExtLossMatchExtPctMax", float(pivE["ext_match"].max()), "{:.2f}")
    gain_cong = piv["none"] - piv["cong"]
    gain_ext = piv["none"] - piv["ext_tour"]
    macro("ExtGainCongShare", med(100 * gain_cong / gain_ext), "{:.0f}")
    macro("ExtGainCongShareMax", float((100 * gain_cong / gain_ext).max()), "{:.0f}")
    # charge: per-delivery extended charge vs congestion-only Pigou
    up = W.pivot_table(index=key, columns="rule", values="u_per_del")
    macro("ExtChargeMatch", med(up["ext_match"]), "{:.2f}")
    macro("ExtChargeCong", med(up["cong"]), "{:.3f}")
    macro("ExtChargeRatio", med(up["ext_match"] / up["cong"]), "{:.0f}")
    macro("ExtChargeRatioMin", (up["ext_match"] / up["cong"]).groupby("city").median().min(), "{:.0f}")
    macro("ExtChargeRatioMax", (up["ext_match"] / up["cong"]).groupby("city").median().max(), "{:.0f}")
    qd = W.pivot_table(index=key, columns="rule", values="Q_total")
    vk = W.pivot_table(index=key, columns="rule", values="vkm")
    macro("ExtDQ", med(100 * (qd["ext_tour"] / qd["none"] - 1)), "{:+.0f}")
    macro("ExtDVkm", med(100 * (vk["ext_tour"] / vk["none"] - 1)), "{:+.0f}")
    macro("ExtDQMatch", med(100 * (qd["ext_match"] / qd["none"] - 1)), "{:+.0f}")
    macro("ExtDVkmMatch", med(100 * (vk["ext_match"] / vk["none"] - 1)), "{:+.0f}")
    macro("ExtEbarDQ", med(100 * (qd["ext_ebar"] / qd["ext_tour"] - 1)), "{:+.0f}")
    macro("ExtEbarDVkm", med(100 * (vk["ext_ebar"] / vk["ext_tour"] - 1)), "{:+.0f}")
    cpv = nb.cong / (nb.vkm - nb.vkm_in)
    macro("ExtCongPerVkm", med(cpv), "{:.2f}")
    macro("ExtCongPerVkmMin", cpv.groupby("city").median().min(), "{:.2f}")
    macro("ExtCongPerVkmMax", cpv.groupby("city").median().max(), "{:.2f}")
    eu = [c for c in ("London", "Paris", "Berlin")]
    macro("ExtCongPerVkmEU", f"{cpv.loc[eu].groupby('city').median().min():.2f}--{cpv.loc[eu].groupby('city').median().max():.2f}")
    macro("ExtDVkmPerDel", med(100 * ((vk["ext_tour"] / qd["ext_tour"]) / (vk["none"] / qd["none"]) - 1)),
          "{:+.0f}")
    # sensitivity
    for v, nm in (("eu", "Eu"), ("hi", "Hi"), ("nocong", "NoCong")):
        x = d[(d.regime == "W") & (d.variant == v)]
        px = x.pivot_table(index=key, columns="rule", values="loss_sw")
        macro(f"ExtSens{nm}None", med(px["none"]), "{:.2f}")
        macro(f"ExtSens{nm}Cong", med(px["cong"]), "{:.2f}")
        macro(f"ExtSens{nm}Match", med(px["ext_match"]), "{:.3f}")
        xb = x[x.rule == "none"]
        macro(f"ExtSens{nm}E", med(xb.E / xb.Q_total), "{:.3f}")
    # finite N
    F_ = d[(d.regime == "N") & (d.variant == "base")]
    pf = F_.pivot_table(index=key + ["N"], columns="rule", values="loss_sw").reset_index()
    for N, w in WORD.items():
        x = pf[pf.N == N]
        for r_, nm in (("none", "None"), ("pm_cong", "PmCong"), ("pm_ext_match", "PmMatch"),
                       ("pm_ext_tour", "PmTour")):
            macro(f"Ext{w}{nm}", med(x[r_]), "{:.2f}")
    # exposure
    ex = W.pivot_table(index=key, columns="rule", values=["exp_vkm_m", "exp_gini", "exp_d10d1",
                                                          "exp_through_share", "exp_air_usd_yr"])
    macro("ExpVkmNone", med(ex["exp_vkm_m"]["none"]), "{:.0f}")
    macro("ExpVkmNoneMin", ex["exp_vkm_m"]["none"].groupby("city").median().min(), "{:.0f}")
    macro("ExpVkmNoneMax", ex["exp_vkm_m"]["none"].groupby("city").median().max(), "{:.0f}")
    macro("ExpVkmDTour", med(100 * (ex["exp_vkm_m"]["ext_tour"] / ex["exp_vkm_m"]["none"] - 1)), "{:+.0f}")
    macro("ExpVkmDCong", med(100 * (ex["exp_vkm_m"]["cong"] / ex["exp_vkm_m"]["none"] - 1)), "{:+.1f}")
    macro("ExpGiniNone", med(ex["exp_gini"]["none"]), "{:.2f}")
    macro("ExpGiniTour", med(ex["exp_gini"]["ext_tour"]), "{:.2f}")
    macro("ExpGiniMatch", med(ex["exp_gini"]["ext_match"]), "{:.2f}")
    macro("ExpGiniDTour", med(ex["exp_gini"]["ext_tour"] - ex["exp_gini"]["none"]), "{:+.3f}")
    macro("ExpGiniUp", f"{int((ex['exp_gini']['ext_tour'] > ex['exp_gini']['none']).sum())}/{len(ex)}")
    macro("ExpDtenNone", med(ex["exp_d10d1"]["none"]), "{:.0f}")
    macro("ExpThroughNone", med(100 * ex["exp_through_share"]["none"]), "{:.0f}")
    macro("ExpThroughTour", med(100 * ex["exp_through_share"]["ext_tour"]), "{:.0f}")
    macro("ExpAirNone", med(ex["exp_air_usd_yr"]["none"]), "{:.2f}")
    macro("ExpAirMax", ex["exp_air_usd_yr"]["none"].groupby("city").median().max(), "{:.2f}")
    macro("ExpCorrCong", med(nb.exp_corr_cong), "{:.2f}")
    macro("ExpCorrCongMin", nb.exp_corr_cong.groupby("city").median().min(), "{:.2f}")
    macro("ExpCorrCongMax", nb.exp_corr_cong.groupby("city").median().max(), "{:.2f}")
    # city table
    rows = []
    for c in CITY_ORDER:
        x = nb_per.loc[c].median()
        b = nb.loc[c]
        pc = piv.loc[c].median()
        exc = ex.loc[c].median()
        cells = [lab(c), f"{x.air + x.clim:.3f}", f"{x.noise:.3f}", f"{x.cong:.3f}", f"{b.kQ_per_del.median():.3f}",
                 f"{100 * x.E / b.fee.median():.0f}", f"{pc['none']:.2f}", f"{pc['cong']:.2f}",
                 f"{pc['ext_match']:.2f}", f"{100 * (vk.loc[c]['ext_tour'] / vk.loc[c]['none'] - 1).median():+.0f}",
                 f"{exc['exp_vkm_m']['none']:.0f}", f"{exc['exp_gini']['none']:.2f}",
                 f"{exc['exp_gini']['ext_tour']:.2f}"]
        rows.append(" & ".join(cells) + r" \\")
    (PAP / "table_extern.tex").write_text("\n".join(rows)[:-3] + "\n")
    d.to_csv(RES / "summary_ext_extern.csv", index=False)
    # figure
    fig, axes = plt.subplots(1, 2, figsize=(12, 3.8), gridspec_kw=dict(width_ratios=[1.3, 1]))
    cities = CITY_ORDER
    xs = np.arange(len(cities))
    bottom = np.zeros(len(cities))
    for comp, cl, nm in (("air", "tab:brown", "air pollution"), ("clim", "tab:olive", "climate"),
                         ("noise", "tab:purple", "noise"), ("cong", "tab:orange", "through-traffic delay")):
        v = np.array([nb_per.loc[c][comp].median() for c in cities])
        axes[0].bar(xs, v, bottom=bottom, color=cl, label=nm)
        bottom += v
    kq = np.array([nb.loc[c].kQ_per_del.median() for c in cities])
    axes[0].plot(xs, kq, "k_", ms=18, mew=2, label=r"in-zone congestion charge $\kappa Q$")
    axes[0].set_xticks(xs, [lab(c) for c in cities], rotation=30, fontsize=8)
    axes[0].set(yscale="log", ylabel="USD per delivery (no charge, mean field)")
    axes[0].legend(fontsize=7)
    Ns = [6, 12, 24, 48, 96, 192, 384, 768, 1536]
    pf["Ni"] = pf.N.astype(int)
    for r_, cl, nm in (("none", "k", "no charge"), ("pm_cong", "tab:blue", "congestion only (Pigou minus m.p.)"),
                       ("pm_ext_match", "tab:red", "extended, per delivery"),
                       ("pm_ext_tour", "tab:green", "extended, per delivery and per tour")):
        g = pf.groupby("Ni")[r_]
        n_ = np.array(sorted(g.groups))
        axes[1].plot(n_, g.median().reindex(n_), "o-", color=cl, label=nm)
        axes[1].fill_between(n_, g.quantile(0.25).reindex(n_), g.quantile(0.75).reindex(n_), color=cl, alpha=0.15)
    _ = Ns
    axes[1].set(xscale="log", yscale="symlog", xlabel="number of carriers $N$",
                ylabel="loss vs extended optimum, % of $\\mathrm{SW}^{\\rm opt}$")
    axes[1].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "mfg_extern.png", dpi=150)
    plt.close(fig)
    return d


def main():
    fees()
    if (RES / "entry.csv").exists():
        entry()
    if (RES / "extern.csv").exists():
        extern()
    with open(PAP / "numbers_ext.tex", "w") as fh:
        fh.write("% generated by mfg/experiments/analyze_ext.py; do not edit\n")
        for k in sorted(macros):
            fh.write(f"\\newcommand{{\\{k}}}{{{macros[k]}}}\n")
    print(len(macros), "macros")


if __name__ == "__main__":
    main()
