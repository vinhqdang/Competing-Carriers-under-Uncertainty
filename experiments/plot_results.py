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


def e2_heat():
    e2 = pd.concat([rd(f"E2_{c}.csv") for c in CITIES], ignore_index=True)
    if e2.empty:
        return
    fig, axs = plt.subplots(3, 3, figsize=(13, 10), constrained_layout=True)
    for ax, c in zip(axs.ravel(), CITIES):
        d = e2[e2.city == c]
        if d.empty:
            ax.axis("off")
            continue
        none = d[d.config == "none"].iloc[0]
        d = d.assign(g=100 * (none.social_cost - d.social_cost) / max(abs(none.social_cost), 1e-9))
        p = d.pivot(index="theta", columns="sfrac", values="g").sort_index()
        im = ax.imshow(p.values, origin="lower", aspect="auto", cmap="RdBu", vmin=-max(abs(p.values).max(), 1e-6), vmax=max(abs(p.values).max(), 1e-6))
        ax.set_xticks(range(len(p.columns)), [f"{x:g}" for x in p.columns], fontsize=7)
        ax.set_yticks(range(len(p.index)), [f"{x:g}" for x in p.index], fontsize=7)
        ax.set_title(f"{nm(c)} (max {p.values.max():.2f}%)")
        ax.grid(False)
        ax.set_xlabel("per-delivery charge s / fee")
        ax.set_ylabel("congestion theta")
        fig.colorbar(im, ax=ax, fraction=0.05)
    fig.suptitle("E2: reduction of the social cost (% of |SC|, main objective) over the (theta, s) grid; red = worse than no charge")
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
            v = [d[(d.city == c) & (d.config == cfg)].gain_pct_of_abs.values[0] if len(d[(d.city == c) & (d.config == cfg)]) else np.nan for c in CITIES]
            ax.bar(x + (k - 1) * 0.27, v, 0.27, label=cfg.replace("_", " "), color=["#4e79a7", "#f28e2b", "#59a14f"][k])
        ax.set_xticks(x, [nm(c) for c in CITIES], rotation=30, ha="right")
        ax.set_ylabel("gain vs no charge (% of |social cost|)")
        ax.set_title(tt)
        ax.legend(frameon=False)
    fig.savefig(FIG / "E2_instruments.png")
    plt.close(fig)


def e3():
    s = rd("summary_E3.csv")
    if s.empty:
        return
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.2), constrained_layout=True)
    x = np.arange(len(s))
    axs[0].bar(x - 0.27, 100 * (s.PoA - 1), 0.27, label="PoA (worst NE found)", color="#e15759")
    axs[0].bar(x, 100 * (s.PoS - 1), 0.27, label="PoS (best NE found)", color="#f28e2b")
    axs[0].bar(x + 0.27, 100 * (s.PoA_priced - 1), 0.27, label="priced NE (best charge pair)", color="#4e79a7")
    axs[0].set_xticks(x, [nm(c) for c in s.city], rotation=30, ha="right")
    axs[0].set_ylabel("W_SO / W_NE - 1  (%)")
    axs[0].set_title("E3: welfare loss vs the rounded convexified social optimum (main objective)")
    axs[0].legend(frameon=False)
    axs[1].bar(x - 0.2, s.gap_broad_unpriced_pct_of_W, 0.4, label="unpriced NE", color="#e15759")
    axs[1].bar(x + 0.2, s.gap_broad_priced_pct_of_W, 0.4, label="priced NE (broad-optimal charges)", color="#4e79a7")
    axs[1].set_xticks(x, [nm(c) for c in s.city], rotation=30, ha="right")
    axs[1].set_ylabel("(Wb_SO - Wb_NE) as % of unpriced welfare")
    axs[1].set_title("same, broad objective (incl. background-traffic delay)")
    axs[1].legend(frameon=False)
    fig.savefig(FIG / "E3_poa.png")
    plt.close(fig)


def e4():
    s = rd("summary_E4.csv")
    if s.empty:
        return
    fig, axs = plt.subplots(2, 3, figsize=(15, 7.5), constrained_layout=True)
    pb = s[s.kind == "pbox"]
    ga = s[s.kind == "gamma"]
    for c in CITIES:
        d = pb[pb.city == c].sort_values("eps")
        axs[0, 0].plot(d.eps, d.d_deliveries_pct, "o-", color=CC[c], label=nm(c), ms=3)
        axs[0, 1].plot(d.eps, d.d_vehicle_hours_pct, "o-", color=CC[c], ms=3)
        axs[0, 2].plot(d.eps, d.d_welfare_pct, "o-", color=CC[c], ms=3)
        d = ga[ga.city == c].sort_values("delta")
        axs[1, 0].plot(d.delta, d.d_deliveries_pct, "o-", color=CC[c], ms=3)
        axs[1, 1].plot(d.delta, d.d_vehicle_hours_pct, "o-", color=CC[c], ms=3)
        axs[1, 2].plot(d.delta, d.slowdown_pct, "o-", color=CC[c], ms=3)
    for ax, t, yl in zip(axs.ravel(), ["deliveries", "vehicle-hours (congestion)", "welfare", "deliveries", "vehicle-hours (congestion)", "mean slowdown"],
                         ["% vs eps = 0", "% vs eps = 0", "% vs eps = 0", "% vs delta = 0", "% vs delta = 0", "% (level)"]):
        ax.set_title(t)
        ax.set_ylabel(yl)
    for ax in axs[0]:
        ax.set_xlabel("p-box half-width eps (DKW band of the travel-time laws)")
    for ax in axs[1]:
        ax.set_xlabel("credal width delta (Gamma-maximin surcharge)")
    axs[0, 0].legend(frameon=False, fontsize=7, ncol=2)
    fig.suptitle("E4: imprecision. Top: DKW p-box width (route costs through BRL). Bottom: Gamma-maximin surcharge on rivals' aggregates")
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
    axs[0, 0].bar(x, 100 * e1.served_share, color=[CC[c] for c in e1.city])
    axs[0, 0].set_title("unpriced NE: share of customer demand served (%)")
    axs[0, 1].bar(x, e1.slowdown_pct, color=[CC[c] for c in e1.city])
    axs[0, 1].set_title("unpriced NE: mean added slowdown (%)")
    axs[0, 2].bar(x, e1.welfare, color=[CC[c] for c in e1.city])
    axs[0, 2].set_title("unpriced NE: welfare (USD/day of the modelled slice)")
    if len(s2):
        d = s2[s2.objective == "main"]
        for k, cfg in enumerate(["congestion_only", "delivery_only", "both"]):
            v = [d[(d.city == c) & (d.config == cfg)].gain_pct_of_abs.values[0] if len(d[(d.city == c) & (d.config == cfg)]) else np.nan for c in e1.city]
            axs[1, 0].bar(x + (k - 1) * 0.27, v, 0.27, label=cfg.replace("_", " "))
        axs[1, 0].legend(frameon=False, fontsize=8)
        axs[1, 0].set_title("leader's gain vs no charge (% of |SC|)")
    if len(s3):
        s3 = s3.set_index("city").reindex(e1.city)
        axs[1, 1].bar(x - 0.2, 100 * (s3.PoA.values - 1), 0.4, label="PoA", color="#e15759")
        axs[1, 1].bar(x + 0.2, 100 * (s3.PoA_priced.values - 1), 0.4, label="priced", color="#4e79a7")
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
