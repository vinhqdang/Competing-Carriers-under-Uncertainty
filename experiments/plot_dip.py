"""Figures of the DIP experiments.

figures/dip_calls_vs_gain.png : per city, the grid's best gain so far against oracle calls spent (exact E2 rows, in the
                                order they were solved; one line per seed) and DIP (one marker per seed).
figures/dip_charges_<city>.png: zone map (real zone rectangles) of DIP's implementing charge u_z / fee, seed 0; zones
                                without lots in grey.
Usage: python experiments/plot_dip.py
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm  # noqa: E402

from common import FIG, RES, rpath  # noqa: E402
from plot_cities import load_city, projector, to_km  # noqa: E402

CITIES = ["London", "BuenosAires", "NewDelhi", "Paris", "Berlin", "Bombay", "Cairo", "Moscow", "NewYork"]
LABEL = {"BuenosAires": "Buenos Aires", "NewDelhi": "New Delhi", "Bombay": "Mumbai", "NewYork": "New York"}
GRID_C, DIP_C = "#2a78d6", "#eb6834"
INK, MUTED, GRIDLINE = "#0b0b0b", "#52514e", "#e4e3df"
DIV = LinearSegmentedColormap.from_list("div", ["#2a78d6", "#e9e8e4", "#eb6834"])
MARK = {0: "o", 1: "s", 2: "^"}


def grid_curve(city, seed):
    f = rpath("E2", city, seed)
    if not f.exists():
        f = RES / "pb_old" / f.name  # seed without an exact E2 run
    if not f.exists():
        return None
    d = pd.read_csv(f)
    if "oracle" in d:
        d = d[d.oracle == "exact"]
    base = float(d[(d.theta == 0) & (d.sfrac == 0)].social_cost.iloc[0])
    calls = np.cumsum(d.calls.to_numpy())
    best = np.minimum.accumulate(d.social_cost.to_numpy())
    return calls, 100 * (base - best) / abs(base), base


LS = {0: "-", 1: "--", 2: ":"}


def calls_vs_gain(dipd):
    from matplotlib.ticker import LogLocator, NullFormatter
    fig, axes = plt.subplots(3, 3, figsize=(11, 9.5))
    for ax, city in zip(axes.ravel(), CITIES):
        any_gain = False
        for seed in (0, 1, 2):
            gc = grid_curve(city, seed)
            r = dipd[(dipd.city == city) & (dipd.seed == seed)]
            if gc is None or not len(r):
                continue
            r = r.iloc[0]
            gbest = gc[1][-1]
            if gbest <= 1e-9:
                continue
            any_gain = True
            ax.step(gc[0], 100 * gc[1] / gbest, where="post", color=GRID_C, lw=2, ls=LS[seed], label=f"grid, seed {seed}")
            g = 100 * (r.grid_sc0 - r.dip_sc) / abs(r.grid_sc0)
            ax.plot(r.dip_calls, 100 * g / gbest, MARK[seed], ms=8, color=DIP_C, mec="white", mew=1.5, label=f"DIP, seed {seed}")
        if not any_gain:
            ax.text(0.5, 0.5, "no seed with a positive grid gain\n(unpriced equilibrium = social optimum)", ha="center",
                    va="center", transform=ax.transAxes, color=MUTED, fontsize=9)
        ax.set_xscale("log")
        if not any_gain:
            ax.set_xlim(20, 3000)
        ax.xaxis.set_major_locator(LogLocator(base=10))
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.axhline(100, color=MUTED, lw=0.8)
        ax.set_ylim(-60, 340) if city == "Bombay" else ax.set_ylim(-60, 150)
        ax.set_title(LABEL.get(city, city), color=INK, fontsize=11, loc="left")
        ax.grid(True, color=GRIDLINE, lw=0.8)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(colors=MUTED, labelsize=8)
    for ax in axes[-1]:
        ax.set_xlabel("routing-oracle calls (log)", color=MUTED)
    for ax in axes[:, 0]:
        ax.set_ylabel("gain, % of the grid's best gain", color=MUTED)
    h, l = [], []
    for ax in axes.ravel():
        for hh, ll in zip(*ax.get_legend_handles_labels()):
            if ll not in l:
                h.append(hh)
                l.append(ll)
    order = sorted(range(len(l)), key=lambda k: (l[k].split(",")[0] != "grid", l[k]))
    fig.legend([h[k] for k in order], [l[k] for k in order], loc="lower center", ncol=6, frameon=False, fontsize=9)
    fig.suptitle("Social-cost gain of the leader against routing-oracle calls: grid search (best so far, exact E2 rows in solve order)\n"
                 "vs dual implementation pricing (one point per run). 100% = best grid point. Mumbai, Paris, Berlin, Cairo, Moscow, New York:\n"
                 "reduced exact grids (7-17 points; Berlin, Moscow, New York seed 2: price-and-branch 63-point grid)",
                 fontsize=10, color=INK)
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    fig.savefig(FIG / "dip_calls_vs_gain.png", dpi=150)
    plt.close(fig)


def charges_map(city, seed=0):
    f = rpath("dip_charges", city, seed)
    if not f.exists():
        return
    ch = pd.read_csv(f)
    data = load_city(city)
    from ccu import zmc_brl as zb
    fee = zb.load_wide(city)["delivery_fee_usd"]
    tr, _, _ = projector(data)
    b = data["bounds"]
    w, s, e, n = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    xs, ys = to_km(tr, np.column_stack([w, e, e, w]).ravel(), np.column_stack([s, s, n, n]).ravel())
    verts = np.stack([xs, ys], axis=-1).reshape(-1, 4, 2)
    act = ch.active.to_numpy(bool)
    v = ch.u.to_numpy() / fee
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.6))
    vmax = max(np.abs(v[act]).max(), 1e-3)
    norm = TwoSlopeNorm(vcenter=0.0, vmin=-vmax, vmax=vmax)
    for ax, (vals, title) in zip(axs, [(v, "implementing charge u_z / fee (per-delivery equivalent)"),
                                       (ch.t.to_numpy(), "congestion charge t_z, USD per vehicle-hour")]):
        ax.add_collection(PolyCollection(verts[~act], facecolors="#d6d5d0", edgecolors="none"))
        if ax is axs[0]:
            pc = PolyCollection(verts[act], array=vals[act], cmap=DIV, norm=norm, edgecolors="white", linewidths=0.3)
        else:
            pc = PolyCollection(verts[act], array=vals[act], cmap=LinearSegmentedColormap.from_list("seq", ["#e9f1fb", "#0d3b75"]),
                                edgecolors="white", linewidths=0.3)
        ax.add_collection(pc)
        ax.autoscale()
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=10, color=INK, loc="left")
        ax.set_xlabel("km", color=MUTED)
        ax.tick_params(colors=MUTED, labelsize=8)
        cb = fig.colorbar(pc, ax=ax, shrink=0.8)
        cb.ax.tick_params(labelsize=8, colors=MUTED)
    r = pd.read_csv(rpath("dip", city, seed)).iloc[0]
    fig.suptitle(f"{LABEL.get(city, city)}, seed {seed}: DIP charges (uniform per-delivery s = {r.dip_s_over_fee:+.2f} fee; "
                 f"grey: zones without lots)", fontsize=11, color=INK)
    fig.tight_layout()
    fig.savefig(FIG / f"dip_charges_{city}.png", dpi=140)
    plt.close(fig)


def main():
    d = pd.read_csv(RES / "summary_dip.csv")
    calls_vs_gain(d)
    for c in CITIES:
        charges_map(c, 0)


if __name__ == "__main__":
    main()
