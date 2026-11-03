"""Tables, figures and macros of the stakeholder study (run after run_stake.py, run_uniform.py, run_ident.py).

  PYTHONPATH=mfg/src python3 mfg/experiments/analyze_stake.py
Writes mfg/results/summary_stake_*.csv, mfg/figures/mfg_stake_*.png, mfg/paper/numbers_stake.tex and the table
fragments mfg/paper/table_stake_*.tex.
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
NT = [6, 24, 192, 1536]
macros: dict[str, str] = {}


def macro(name, val, fmt="{:.2f}"):
    macros[name] = val if isinstance(val, str) else fmt.format(val)


def lab(c):
    return LABEL.get(c, c)


def q(x, p):
    return float(np.nanpercentile(x, p))


# ------------------------------------------------------------------ who gains
def deltas(s):
    base = s[s.rule == "none"].set_index(["city", "seed", "k"])
    out = []
    for rule in ("obs", "pm", "opt"):
        r = s[s.rule == rule].set_index(["city", "seed", "k"])
        z = pd.DataFrame(index=r.index)
        sw0 = base.SW.loc[r.index]
        z["rule"] = rule
        z["N"] = r.N
        for t in ("Pi", "CS", "CC", "R", "SW"):
            z["d" + t] = 100.0 * (r[t] - (base[t].loc[r.index] if t != "R" else 0.0)) / sw0
        z["R"] = z["dR"]
        z["dPiop"] = 100.0 * (r.Pi_op - base.Pi_op.loc[r.index]) / sw0
        z["R_share"] = 100.0 * r.R / r.SW
        z["R_pct_sw0"] = 100.0 * r.R / sw0
        z["SW0"] = sw0
        out.append(z.reset_index())
    return pd.concat(out)


def sg(v, nd=1):
    v = round(float(v), nd)
    return f"{0.0:.{nd}f}" if v == 0 else f"{v:+.{nd}f}"


def tex_who(dl):
    lines = []
    for N in NT:
        for rule, nm in (("obs", "observation-only"), ("pm", "Pigou minus market power")):
            x = dl[(dl.N == N) & (dl.rule == rule)]
            f = lambda c: sg(x[c].median())
            lines.append(f"{N if rule == 'obs' else ''} & {nm} & {f('dPi')} & {f('dCS')} & {f('dCC')} & {f('R')} & "
                         f"{f('dSW')} & {sg(x.R_share.median())} \\\\")
        if N != NT[-1]:
            lines.append("\\addlinespace")
    return "\n".join(lines)


def fig_who(dl):
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.6), sharex=True)
    terms = [("dPi", "carrier profit (net of charge)"), ("dCS", "consumer surplus"), ("dCC", "congestion cost"),
             ("R", "charge revenue")]
    for ax, (t, ttl) in zip(axes, terms):
        for rule, col, nm in (("pm", "tab:blue", "Pigou minus market power"), ("obs", "tab:red", "observation-only")):
            g = dl[dl.rule == rule].groupby("N")[t]
            med, lo, hi = g.median(), g.quantile(0.25), g.quantile(0.75)
            ax.semilogx(med.index, med.values, "-o", ms=3, color=col, label=nm)
            ax.fill_between(med.index, lo.values, hi.values, color=col, alpha=0.15, lw=0)
        ax.axhline(0, color="k", lw=0.5)
        ax.set_title(ttl, fontsize=9)
        ax.set_xlabel("N")
    axes[0].set_ylabel("change vs no charge\n(% of welfare, no charge)")
    axes[0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "mfg_stake_who.png", dpi=150)
    plt.close(fig)


# ------------------------------------------------------------------ exposure
def exposure_summary(s):
    rows = []
    for (N, rule), x in s.groupby(["N", "rule"]):
        rows.append(dict(N=N, rule=rule, exp_mean_min=x.exp_mean_min.median(), gini_zone=x.gini_zone.median(),
                         gini_zh=x.gini_zh.median(), d10d1=x.d10d1.median(),
                         corr_share_dens=x.corr_share_dens.median(), corr_rel_dens=x.corr_rel_dens.median(),
                         dens_mass_shift=x.dens_mass_shift.median(), veh_hours=x.veh_hours.median()))
    return pd.DataFrame(rows)


def exposure_changes(s):
    base = s[s.rule == "none"].set_index(["city", "seed", "k"])
    out = []
    for rule in ("obs", "pm"):
        r = s[s.rule == rule].set_index(["city", "seed", "k"])
        z = pd.DataFrame(index=r.index)
        z["rule"], z["N"] = rule, r.N
        z["d_gini_zone"] = r.gini_zone - base.gini_zone.loc[r.index]
        z["d_gini_zh"] = r.gini_zh - base.gini_zh.loc[r.index]
        z["d_d10d1"] = r.d10d1 - base.d10d1.loc[r.index]
        z["d_exp_rel"] = 100 * (r.exp_mean_min / base.exp_mean_min.loc[r.index] - 1)
        z["corr_share_dens"] = r.corr_share_dens
        z["dens_mass_shift"] = r.dens_mass_shift
        out.append(z.reset_index())
    return pd.concat(out)


def tex_exposure(s, ec):
    lines = []
    for N in (6, 1536):
        for rule, nm in (("none", "no charge"), ("obs", "observation-only"), ("pm", "Pigou minus market power")):
            x = s[(s.N == N) & (s.rule == rule)]
            cs = "--" if rule == "none" else f"{x.corr_share_dens.median():+.2f}"
            lines.append(f"{N if rule == 'none' else ''} & {nm} & {x.exp_mean_min.median():.3f} & "
                         f"{x.gini_zone.median():.3f} & {x.gini_zh.median():.3f} & {x.d10d1.median():.2f} & {cs} \\\\")
        if N == 6:
            lines.append("\\addlinespace")
    return "\n".join(lines)


def fig_second(s, uni, mis):
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.8))
    ax = axes[0]
    for rule, col, nm in (("none", "0.4", "no charge"), ("obs", "tab:red", "observation-only"),
                          ("pm", "tab:blue", "Pigou minus market power")):
        g = s[s.rule == rule].groupby("N").gini_zone.median()
        ax.semilogx(g.index, g.values, "-o", ms=3, color=col, label=nm)
    ax.set_xlabel("N")
    ax.set_ylabel("Gini of daily exposure across residents")
    ax.set_title("Exposure inequality (vehicle-hours per resident)", fontsize=9)
    ax.legend(fontsize=7)
    ax = axes[1]
    un = uni[uni.solver == "nash"].copy()
    un["N"] = un.N.astype(int)
    for col, c, nm, ls in (("loss_none", "0.4", "no charge", "-"), ("loss_uniform", "tab:green", "one city-wide charge", "-"),
                           ("loss_pm", "tab:blue", "zone-hour charges", "-")):
        g = un.groupby("N")[col].median() * 100
        ax.loglog(g.index, g.values, ls + "o", ms=3, color=c, label=nm)
    ax.set_xlabel("N")
    ax.set_ylabel("welfare loss (% of optimum)")
    ax.set_title("City-wide versus zone-hour charge", fontsize=9)
    ax.legend(fontsize=7)
    ax = axes[2]
    w = mis[mis.kind == "wardrop"].copy()
    for e, mk in zip(sorted(w.eps.unique()), "vsos^"):
        pass
    xs = np.array(sorted(w.eps.unique()))
    meas = [100 * (w[w.eps == e].loss / w[w.eps == e].sw_opt).median() for e in xs]
    loose = [100 * (w[w.eps == e].bound_loose / w[w.eps == e].sw_opt).median() for e in xs]
    tight = [100 * (w[w.eps == e].bound_tight / w[w.eps == e].sw_opt).median() for e in xs]
    ax.semilogy(100 * xs, loose, "--s", color="tab:orange", ms=4, label=r"bound $\frac{1}{2}\Vert v-\kappa Q^{\mathrm{opt}}\Vert^2_{b^{-1}}$")
    ax.semilogy(100 * xs, tight, ":^", color="tab:purple", ms=4, label="first inequality of Thm 13(a)")
    ax.semilogy(100 * xs, meas, "-o", color="tab:blue", ms=4, label="measured (mean field)")
    ax.set_xlabel("error of the charge (%)")
    ax.set_ylabel("welfare loss (% of optimum)")
    ax.set_title("Mis-specified Pigou charge", fontsize=9)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG / "mfg_stake_equity.png", dpi=150)
    plt.close(fig)


def main():
    s = pd.read_csv(RES / "stake.csv")
    # exact decomposition check (all rules)
    chk = (s.CS + s.Pi + s.R - s.SW).abs() / s.SW.abs()
    macro("StakeIdErr", chk.max(), "{:.1e}")
    macro("StakeRows", str(int(s.groupby(["city", "seed", "k"]).ngroups)))
    dl = deltas(s)
    dl.to_csv(RES / "summary_stake_deltas.csv", index=False)
    city_tab = (dl[dl.N.isin(NT)].groupby(["city", "rule", "N"])[["dPi", "dCS", "dCC", "R", "dSW", "R_share"]]
                .median().reset_index())
    city_tab.to_csv(RES / "summary_stake_who_city.csv", index=False)
    pool = dl[dl.N.isin(NT)].groupby(["rule", "N"])[["dPi", "dCS", "dCC", "R", "dSW", "R_share"]].median()
    pool.to_csv(RES / "summary_stake_who_pooled.csv")
    (PAP / "table_stake_who.tex").write_text(tex_who(dl) + "\n")
    fig_who(dl)
    TAG = {6: "Six", 24: "TwentyFour", 192: "OneNinetyTwo", 1536: "Big"}
    for N in NT:
        for rule in ("obs", "pm"):
            x = dl[(dl.N == N) & (dl.rule == rule)]
            tag = f"{TAG[N]}{rule.capitalize()}"
            for t in ("dPi", "dPiop", "dCS", "dCC", "R", "dSW", "R_share"):
                macro(f"W{tag}{t.replace('_', '')}", x[t].median(), "{:.1f}")
            macro(f"W{tag}PiMin", x.groupby("city").dPi.median().min(), "{:.1f}")
            macro(f"W{tag}PiMax", x.groupby("city").dPi.median().max(), "{:.1f}")
            macro(f"W{tag}CSMin", x.groupby("city").dCS.median().min(), "{:.1f}")
            macro(f"W{tag}CSMax", x.groupby("city").dCS.median().max(), "{:.1f}")
    # abs levels at N = 6
    for N in (6, 1536):
        b = s[(s.N == N) & (s.rule == "none")]
        tag = "Six" if N == 6 else "Big"
        macro(f"L{tag}CSshare", 100 * (b.CS / b.SW).median(), "{:.0f}")
        macro(f"L{tag}CCshare", 100 * (b.CC / b.SW).median(), "{:.1f}")
        macro(f"L{tag}CCshareMax", 100 * (b.CC / b.SW).max(), "{:.1f}")
        macro(f"L{tag}PiShare", 100 * (b.Pi / b.SW).median(), "{:.0f}")
    pm6 = dl[(dl.N == 6) & (dl.rule == "pm")]
    macro("PmNegShare", 100 * s[(s.N == 6) & (s.rule == "pm")].neg_share.median(), "{:.0f}")
    macro("PmNegShareBig", 100 * s[(s.N == 1536) & (s.rule == "pm")].neg_share.median(), "{:.0f}")
    macro("PmResidMax", s[s.rule == "pm"].resid.max(), "{:.3f}")
    macro("PmResidMed", s[s.rule == "pm"].resid.median(), "{:.4f}")
    macro("PmSubsidyInst", f"{int((pm6.R < 0).sum())}/{len(pm6)}", "{}")
    pm_loss = 100 * (s[s.rule == "pm"].set_index(["city", "seed", "k"]).eval("(SW_opt - SW)/SW_opt"))
    for N in (6, 1536):
        x = 100 * (s[(s.rule == "pm") & (s.N == N)].eval("(SW_opt - SW)/SW_opt"))
        macro(f"PmLoss{'Six' if N == 6 else 'Big'}", x.median(), "{:.2f}")
        y = 100 * (s[(s.rule == "none") & (s.N == N)].eval("(SW_opt - SW)/SW_opt"))
        macro(f"NoLoss{'Six' if N == 6 else 'Big'}", y.median(), "{:.2f}")
        z = 100 * (s[(s.rule == "obs") & (s.N == N)].eval("(SW_opt - SW)/SW_opt"))
        macro(f"ObsLoss{'Six' if N == 6 else 'Big'}", z.median(), "{:.2f}")
    # ---- exposure
    ex = exposure_summary(s)
    ex.to_csv(RES / "summary_stake_exposure.csv", index=False)
    ec = exposure_changes(s)
    ec.to_csv(RES / "summary_stake_exposure_changes.csv", index=False)
    (PAP / "table_stake_exposure.tex").write_text(tex_exposure(s, ec) + "\n")
    for N in (6, 1536):
        tag = "Six" if N == 6 else "Big"
        b = s[(s.N == N) & (s.rule == "none")]
        macro(f"Exp{tag}Mean", b.exp_mean_min.median(), "{:.3f}")
        macro(f"Exp{tag}GiniNone", b.gini_zone.median(), "{:.3f}")
        macro(f"Exp{tag}D10None", b.d10d1.median(), "{:.2f}")
        for rule in ("obs", "pm"):
            x = ec[(ec.N == N) & (ec.rule == rule)]
            r = rule.capitalize()
            macro(f"Exp{tag}{r}dGini", x.d_gini_zone.median(), "{:+.3f}")
            macro(f"Exp{tag}{r}dGiniMin", x.d_gini_zone.quantile(0.1), "{:+.3f}")
            macro(f"Exp{tag}{r}dGiniMax", x.d_gini_zone.quantile(0.9), "{:+.3f}")
            macro(f"Exp{tag}{r}dExp", x.d_exp_rel.median(), "{:+.1f}")
            macro(f"Exp{tag}{r}Corr", x.corr_share_dens.median(), "{:+.2f}")
            macro(f"Exp{tag}{r}CorrMin", x.corr_share_dens.quantile(0.1), "{:+.2f}")
            macro(f"Exp{tag}{r}CorrMax", x.corr_share_dens.quantile(0.9), "{:+.2f}")
            macro(f"Exp{tag}{r}Shift", x.dens_mass_shift.median(), "{:+.3f}")
            macro(f"Exp{tag}{r}dD10", x.d_d10d1.median(), "{:+.2f}")
            macro(f"Exp{tag}{r}CorrNeg", f"{int((x.corr_share_dens < 0).sum())}/{x.corr_share_dens.notna().sum()}", "{}")
    # ---- uniform and misspecification
    uni = pd.read_csv(RES / "uniform.csv")
    mis = pd.read_csv(RES / "misspec.csv")
    un = uni[uni.solver == "nash"].copy()
    un["N"] = un.N.astype(int)
    summ = un.groupby("N")[["loss_none", "loss_uniform", "loss_pm", "frac_uniform"]].median()
    summ.to_csv(RES / "summary_stake_uniform.csv")
    for N in (6, 1536):
        tag = "Six" if N == 6 else "Big"
        x = un[un.N == N]
        macro(f"Un{tag}None", 100 * x.loss_none.median(), "{:.2f}")
        macro(f"Un{tag}Uni", 100 * x.loss_uniform.median(), "{:.2f}")
        macro(f"Un{tag}Pm", 100 * x.loss_pm.median(), "{:.2f}")
        macro(f"Un{tag}Frac", 100 * x.frac_uniform.median(), "{:.0f}")
        macro(f"Un{tag}FracMin", 100 * x.frac_uniform.min(), "{:.0f}")
        macro(f"Un{tag}FracMax", 100 * x.frac_uniform.max(), "{:.0f}")
        macro(f"Un{tag}Ustar", x.u_over_scale.median(), "{:.2f}")
    uw = uni[uni.solver == "wardrop"]
    macro("UnWNone", 100 * uw.loss_none.median(), "{:.3f}")
    macro("UnWUni", 100 * uw.loss_uniform.median(), "{:.3f}")
    macro("UnWFrac", 100 * uw.frac_uniform.median(), "{:.0f}")
    macro("UnWFracMin", 100 * uw.frac_uniform.min(), "{:.0f}")
    macro("UnWFracMax", 100 * uw.frac_uniform.max(), "{:.0f}")
    macro("UnWUniMax", 100 * uw.loss_uniform.max(), "{:.3f}")
    # mis-specification
    w = mis[mis.kind == "wardrop"].copy()
    w["lossp"] = 100 * w.loss / w.sw_opt
    w["ratio_loose"] = w.loss / w.bound_loose
    w["ratio_tight"] = w.loss / w.bound_tight
    tab = w.groupby("eps")[["lossp", "ratio_loose", "ratio_tight"]].median()
    tab["loose_pct"] = 100 * w.assign(v=w.bound_loose / w.sw_opt).groupby("eps").v.median()
    tab["max_ratio_loose"] = w.groupby("eps").ratio_loose.max()
    tab["max_ratio_tight"] = w.groupby("eps").ratio_tight.max()
    tab.to_csv(RES / "summary_stake_misspec_wardrop.csv")
    macro("MisHeld", f"{int((w.loss <= w.bound_loose * (1 + 1e-6) + 1e-9).sum())}/{len(w)}", "{}")
    macro("MisHeldTight", f"{int((np.abs(w.loss - w.bound_tight) <= 1e-5 * w.sw_opt).sum())}/{len(w)}", "{}")
    for e, nm in ((0.1, "Ten"), (0.25, "TwentyFive")):
        a = w[np.isclose(w.eps.abs(), e)]
        macro(f"Mis{nm}Loss", a.lossp.median(), "{:.4f}")
        macro(f"Mis{nm}LossMax", a.lossp.max(), "{:.4f}")
        macro(f"Mis{nm}Ratio", a.ratio_loose.median(), "{:.2f}")
        macro(f"Mis{nm}RatioMax", a.ratio_loose.max(), "{:.2f}")
        macro(f"Mis{nm}RatioMin", a.ratio_loose.min(), "{:.2f}")
    mn = mis[mis.kind == "nash_pm"].copy()
    mn["lossp"] = 100 * mn.loss / mn.sw_opt
    mn["N"] = mn.N.astype(int)
    mt = mn.groupby(["N", "eps"]).lossp.median().unstack()
    mt.to_csv(RES / "summary_stake_misspec_nash.csv")
    for N in (6, 1536):
        for e, nm in ((0.1, "Ten"), (0.25, "TwentyFive")):
            a = mn[(mn.N == N) & np.isclose(mn.eps.abs(), e)]
            macro(f"MisN{'Six' if N == 6 else 'Big'}{nm}", a.lossp.median(), "{:.3f}")
    # ---- identical carriers
    idn = pd.read_csv(RES / "ident.csv")
    macro("IdQErr", idn.q_err.max(), "{:.1e}")
    macro("IdSWErr", idn.sw_err.max(), "{:.1e}")
    macro("IdRatioDevMed", 100 * idn.ratio_dev.abs().median(), "{:.1f}")
    macro("IdRatioDevMax", 100 * idn.ratio_dev.abs().max(), "{:.1f}")
    macro("IdRows", str(len(idn)))
    sub = idn.groupby("N")[["sub_share", "loss_none", "loss_pigou", "loss_ustar", "ustar_over_pigou", "market_power_rel",
                            "ratio_dev"]].median()
    sub.to_csv(RES / "summary_stake_ident.csv")
    nm_ = {1: "One", 6: "Six", 24: "TwentyFour", 192: "OneNinetyTwo", 1536: "Big"}
    for N in (1, 6, 24, 192, 1536):
        r = idn[idn.N == N]
        macro(f"Id{nm_[N]}Sub", 100 * r.sub_share.median(), "{:.0f}")
        macro(f"Id{nm_[N]}None", 100 * r.loss_none.median(), "{:.2f}")
        macro(f"Id{nm_[N]}Pig", 100 * r.loss_pigou.median(), "{:.2f}")
        macro(f"Id{nm_[N]}Ratio", r.ustar_over_pigou.median(), "{:.2f}")
    fig_second(s, uni, mis)
    with open(PAP / "numbers_stake.tex", "w") as fh:
        fh.write("% generated by mfg/experiments/analyze_stake.py; do not edit\n")
        for k in sorted(macros):
            fh.write("\\newcommand{\\%s}{%s}\n" % (k, macros[k]))
    print(len(macros), "macros")


if __name__ == "__main__":
    main()
