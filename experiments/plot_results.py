"""Curves and overview figures from results/summary_*.csv and the per-city result files.

  python experiments/plot_results.py   -> figures/E2_*.png, E3_poa.png, E4_imprecision.png, E5_scaling.png,
                                           E6_checks.png, overview_summary.png, verify_methods.png
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import FIG, RES, zb  # noqa: E402

CITIES = zb.CITIES
LAB = {"NewDelhi": "New Delhi", "BuenosAires": "Buenos Aires", "NewYork": "New York", "Bombay": "Mumbai"}
# validated categorical palette (colour-blind safe), one colour per city
PAL = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1", "#ff9da7", "#9c755f"]
CC = {c: PAL[i] for i, c in enumerate(CITIES)}


def nm(c):
    return LAB.get(c, c)


def style():
    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25,
                         "font.size": 9, "axes.titlesize": 10, "figure.dpi": 110})


def rd(p):
    f = RES / p
    return pd.read_csv(f) if f.exists() else pd.DataFrame()


def seeds_of(c, prefix):
    """result files of one experiment and city over all seeds (seed 0 keeps the unsuffixed name)"""
    fs = [RES / f"{prefix}_{c}.csv"] + sorted(RES.glob(f"{prefix}_{c}_s[0-9]*.csv"))
    out = []
    for f in fs:
        if f.exists():
            d = pd.read_csv(f)
            d["seed"] = int(f.stem.rsplit("_s", 1)[1]) if f.stem != f"{prefix}_{c}" else 0
            out.append(d)
    return out


def mean_sd(d, by, col):
    """mean, sd (ddof 1) and min/max over seeds of `col` per value of `by`"""
    g = d.groupby(by)[col]
    return pd.DataFrame(dict(m=g.mean(), sd=g.std(ddof=1).fillna(0), lo=g.min(), hi=g.max()))


def e2_heat():
    e2 = pd.concat([x for c in CITIES for x in seeds_of(c, "E2") if len(x) == 63], ignore_index=True)
    if e2.empty:
        return
    if "oracle" in e2.columns:  # reduced exact grid: leave the price-and-branch points blank
        e2 = e2[e2.oracle.fillna("exact") != "pb"]
    fig, axs = plt.subplots(3, 3, figsize=(13, 10), constrained_layout=True)
    for ax, c in zip(axs.ravel(), CITIES):
        d = e2[e2.city == c]
        if d.empty:
            ax.axis("off")
            continue
        gs = []
        for _, dd in d.groupby("seed"):
            none = dd[dd.config == "none"].iloc[0]
            gs.append(dd.assign(g=100 * (none.social_cost - dd.social_cost) / max(abs(none.social_cost), 1e-9)))
        d = pd.concat(gs)
        p = d.pivot_table(index="theta", columns="sfrac", values="g", aggfunc="mean").sort_index()
        im = ax.imshow(p.values, origin="lower", aspect="auto", cmap="RdBu", vmin=-max(np.nanmax(abs(p.values)), 1e-6), vmax=max(np.nanmax(abs(p.values)), 1e-6))
        ax.set_xticks(range(len(p.columns)), [f"{x:g}" for x in p.columns], fontsize=7)
        ax.set_yticks(range(len(p.index)), [f"{x:g}" for x in p.index], fontsize=7)
        ax.set_title(f"{nm(c)} (max {np.nanmax(p.values):.2f}%, {d.seed.nunique()} seeds)")
        ax.grid(False)
        ax.set_xlabel("per-delivery charge s / fee")
        ax.set_ylabel("congestion theta")
        fig.colorbar(im, ax=ax, fraction=0.05)
    fig.suptitle("E2: reduction of the social cost (% of |SC|, main objective, mean over seeds) over the (theta, s) grid; red = worse than no charge")
    fig.savefig(FIG / "E2_grid.png")
    plt.close(fig)
    s = rd("summary_E2.csv")
    if s.empty:
        return
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.2), constrained_layout=True)
    cfgs = ["congestion_only", "delivery_only", "both"]
    for ax, obj, tt in zip(axs, ["main", "broad"], ["main objective (carrier costs + consumer surplus)",
                                                     "broad objective (adds background-traffic delay)"]):
        d = s[s.objective == obj]
        x = np.arange(len(CITIES))
        for k, cfg in enumerate(cfgs):
            ms = mean_sd(d[d.config == cfg], "city", "gain_pct_of_abs").reindex(CITIES)
            xs = x + (k - 1) * 0.27
            ax.bar(xs, ms.m, 0.27, yerr=ms.sd, capsize=2, label=cfg.replace("_", " "), color=["#4e79a7", "#f28e2b", "#59a14f"][k])
            ax.plot(xs, ms.lo, "_", color="k", ms=4)
            ax.plot(xs, ms.hi, "_", color="k", ms=4)
        ax.set_xticks(x, [nm(c) for c in CITIES], rotation=30, ha="right")
        ax.set_ylabel("gain vs no charge (% of |social cost|), mean, sd bars, min/max ticks")
        ax.set_title(tt)
        ax.legend(frameon=False)
    fig.savefig(FIG / "E2_instruments.png")
    plt.close(fig)


def e3():
    s = rd("summary_E3.csv")
    if s.empty:
        return
    cs = [c for c in CITIES if c in set(s.city)]
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.2), constrained_layout=True)
    x = np.arange(len(cs))
    for ax, cols, labs, cl in ((axs[0], ("PoA", "PoS", "PoA_priced"), ("PoA (worst NE found)", "PoS (best NE found)", "priced NE (best charge pair)"),
                                ("#e15759", "#f28e2b", "#4e79a7")),
                               (axs[1], ("gap_broad_unpriced_pct_of_W", "gap_broad_priced_pct_of_W"), ("unpriced NE", "priced NE (broad-optimal charges)"),
                                ("#e15759", "#4e79a7"))):
        w = 0.8 / len(cols)
        for k, (col, lab, colr) in enumerate(zip(cols, labs, cl)):
            t = s.assign(v=100 * (s[col] - 1) if ax is axs[0] else s[col])
            ms = mean_sd(t, "city", "v").reindex(cs)
            xs = x + (k - (len(cols) - 1) / 2) * w
            ax.bar(xs, ms.m, w, yerr=ms.sd, capsize=2, label=lab, color=colr)
            ax.plot(xs, ms.lo, "_", color="k", ms=4)
            ax.plot(xs, ms.hi, "_", color="k", ms=4)
        ax.set_xticks(x, [nm(c) for c in cs], rotation=30, ha="right")
        ax.legend(frameon=False)
    axs[0].set_ylabel("W_SO / W_NE - 1  (%), mean over seeds, sd bars, min/max ticks")
    axs[0].set_title("E3: welfare loss vs the rounded convexified social optimum (main objective)")
    axs[1].set_ylabel("(Wb_SO - Wb_NE) as % of unpriced welfare")
    axs[1].set_title("same, broad objective (incl. background-traffic delay)")
    fig.savefig(FIG / "E3_poa.png")
    plt.close(fig)


def e4():
    s = rd("summary_E4.csv")
    if s.empty:
        return
    fig, axs = plt.subplots(2, 3, figsize=(15, 7.5), constrained_layout=True)
    pb = s[s.kind == "pbox"]
    ga = s[s.kind == "gamma"]
    def band(ax, d, key, col, c, label=None):
        d = d.assign(**{key: d[key].round(4)})
        ms = mean_sd(d, key, col).sort_index()
        ax.plot(ms.index, ms.m, "o-", color=CC[c], label=label, ms=3)
        ax.fill_between(ms.index, ms.lo, ms.hi, color=CC[c], alpha=0.18, lw=0)

    for c in CITIES:
        d = pb[pb.city == c]
        band(axs[0, 0], d, "eps", "d_deliveries_pct", c, nm(c))
        band(axs[0, 1], d, "eps", "d_vehicle_hours_pct", c)
        band(axs[0, 2], d, "eps", "d_welfare_pct", c)
        d = ga[ga.city == c]
        band(axs[1, 0], d, "delta", "d_deliveries_pct", c)
        band(axs[1, 1], d, "delta", "d_vehicle_hours_pct", c)
        band(axs[1, 2], d, "delta", "slowdown_pct", c)
    for ax, t, yl in zip(axs.ravel(), ["deliveries", "vehicle-hours (congestion)", "welfare", "deliveries", "vehicle-hours (congestion)", "mean slowdown"],
                         ["% vs eps = 0", "% vs eps = 0", "% vs eps = 0", "% vs delta = 0", "% vs delta = 0", "% (level)"]):
        ax.set_title(t)
        ax.set_ylabel(yl)
    for ax in axs[0]:
        ax.set_xlabel("p-box half-width eps (DKW band of the travel-time laws)")
    for ax in axs[1]:
        ax.set_xlabel("credal width delta (Gamma-maximin surcharge)")
    axs[0, 0].legend(frameon=False, fontsize=7, ncol=2)
    fig.suptitle("E4: imprecision (line = mean over seeds, band = min..max). Top: DKW p-box width. Bottom: Gamma-maximin surcharge on rivals' aggregates")
    fig.savefig(FIG / "E4_imprecision.png")
    plt.close(fig)


def e5():
    s = rd("summary_E5_calls_vs_Z.csv")
    vm = rd("summary_verify_methods.csv")
    if s.empty:
        return
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.3), constrained_layout=True)
    for m, col, mk in [("ZMC8", "#4e79a7", "o"), ("BR", "#e15759", "s"), ("FW8", "#f28e2b", "^"), ("CG8", "#59a14f", "v"), ("CG(conv)", "#9c755f", "D")]:
        d = vm[vm.method == m].sort_values("Z")
        axs[0].plot(d.Z, d.calls, mk + "-", color=col, label=m, ms=5)
        axs[1].plot(d.d_eff, d.calls, mk + "-", color=col, ms=5)
    for ax, xl in zip(axs[:2], ["number of zones Z", "active coordinates d_eff / 2 (zones with demand)"]):
        ax.set_xlabel(xl)
        ax.set_ylabel("oracle calls per equilibrium")
        ax.set_yscale("log")
    axs[0].set_xscale("log")
    axs[0].legend(frameon=False, ncol=2)
    axs[0].set_title("E5: calls vs Z (nine cities, 22 customer zones per carrier)")
    axs[1].set_title("same, versus number of active zones")
    for m, col, mk in [("ZMC8", "#4e79a7", "o"), ("BR", "#e15759", "s"), ("FW8", "#f28e2b", "^"), ("CG8", "#59a14f", "v"), ("CG(conv)", "#9c755f", "D")]:
        d = vm[vm.method == m].sort_values("Z")
        axs[2].plot(d.Z, 100 * d.gap_rel, mk, color=col, label=m, ms=6)
    axs[2].set_xscale("log")
    axs[2].set_yscale("symlog", linthresh=0.01)
    axs[2].set_xlabel("number of zones Z")
    axs[2].set_ylabel("potential gap to convexified CG optimum (%)")
    axs[2].set_title("quality of the returned pure equilibrium")
    fig.savefig(FIG / "E5_scaling.png")
    plt.close(fig)


def e6():
    e = pd.concat([rd(f"E6_{c}.csv") for c in CITIES], ignore_index=True)
    if e.empty:
        return
    z = e[e.kind == "zmc_round"]
    b = e[e.kind == "bisect_bracket"]
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2), constrained_layout=True)
    for c in CITIES:
        d = z[z.city == c]
        axs[0].plot(d["round"], d.err2 / d.err2.iloc[0], "o-", color=CC[c], ms=3, label=nm(c))
        axs[1].plot(d["round"], np.maximum(d.width_max, 1e-4), "o-", color=CC[c], ms=3)
        d = b[b.city == c]
        axs[2].plot(d["round"], d.err_max, "o-", color=CC[c], ms=3)
    axs[0].set_title("clearing error ||e||_M^2 per ZMC round (relative to round 1)")
    axs[0].set_yscale("log")
    axs[1].set_title("max relative bracket width (secant mode)")
    axs[1].set_yscale("log")
    r = np.arange(1, 13)
    axs[1].plot(r, 2.0 ** (-np.ceil(r / 2)), "k--", label="2^-ceil(T/2)")
    axs[1].set_ylim(1e-4, 1.5)
    axs[2].set_title("bisection: max |lam_t - lam_ref| / (M Amax)")
    axs[2].plot(r, 2.0 ** (-np.ceil(r / 2)), "k--", label="Cor. 7 bound 2^-ceil(T/2)")
    axs[2].set_yscale("log")
    axs[2].legend(frameon=False)
    for ax in axs:
        ax.set_xlabel("round T")
    axs[0].legend(frameon=False, fontsize=7, ncol=2)
    fig.savefig(FIG / "E6_checks.png")
    plt.close(fig)


def overview():
    e1 = rd("summary_E1.csv")
    s2 = rd("summary_E2.csv")
    s3 = rd("summary_E3.csv")
    if e1.empty:
        return
    fig, axs = plt.subplots(2, 3, figsize=(16, 8), constrained_layout=True)
    x = np.arange(len(e1))
    cl = [nm(c) for c in e1.city]
    axs[0, 0].bar(x, 100 * e1.served_share, yerr=100 * e1.served_sd, capsize=2, color=[CC[c] for c in e1.city])
    axs[0, 0].set_title("unpriced NE: share of customer demand served (%)")
    axs[0, 1].bar(x, e1.slowdown_pct, color=[CC[c] for c in e1.city])
    axs[0, 1].set_title("unpriced NE: mean added slowdown (%)")
    axs[0, 2].bar(x, e1.welfare, yerr=e1.welfare_sd, capsize=2, color=[CC[c] for c in e1.city])
    axs[0, 2].set_title("unpriced NE: welfare (USD/day of the modelled slice)")
    if len(s2):
        d = s2[s2.objective == "main"]
        for k, cfg in enumerate(["congestion_only", "delivery_only", "both"]):
            ms = mean_sd(d[d.config == cfg], "city", "gain_pct_of_abs").reindex(e1.city)
            axs[1, 0].bar(x + (k - 1) * 0.27, ms.m, 0.27, yerr=ms.sd, capsize=2, label=cfg.replace("_", " "))
        axs[1, 0].legend(frameon=False, fontsize=8)
        axs[1, 0].set_title("leader's gain vs no charge (% of |SC|, mean, sd bars)")
    if len(s3):
        for off, col, lab, colr in ((-0.2, "PoA", "PoA", "#e15759"), (0.2, "PoA_priced", "priced", "#4e79a7")):
            ms = mean_sd(s3.assign(v=100 * (s3[col] - 1)), "city", "v").reindex(e1.city)
            axs[1, 1].bar(x + off, ms.m, 0.4, yerr=ms.sd, capsize=2, label=lab, color=colr)
        axs[1, 1].legend(frameon=False)
        axs[1, 1].set_title("welfare loss vs social optimum (%)")
    axs[1, 2].bar(x, e1.calls, color=[CC[c] for c in e1.city])
    axs[1, 2].set_title("ZMC oracle calls per equilibrium")
    for ax in axs.ravel():
        ax.set_xticks(x, cl, rotation=35, ha="right")
    fig.suptitle("Nine cities: unpriced equilibrium, leader's instruments, price of anarchy, effort")
    fig.savefig(FIG / "overview_summary.png")
    plt.close(fig)


if __name__ == "__main__":
    style()
    for f in (e2_heat, e3, e4, e5, e6, overview):
        try:
            f()
        except Exception as ex:  # a missing city must not stop the other figures
            print(f.__name__, "failed:", repr(ex))
