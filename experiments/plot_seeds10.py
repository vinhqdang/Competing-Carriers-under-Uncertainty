"""Forest plots of the headline quantities over ten seeds: mean and bootstrap 95% CI per city (filled), mean of seeds 0-2 (open marker),
individual seeds (small grey dots).  Cities marked * have a reduced exact grid: every grid-derived value is a lower bound.
Writes figures/seeds10_forest_gain.png, seeds10_forest_poa.png, seeds10_forest_dip_arp.png, seeds10_forest_so_share.png."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIG, RES
from summarize_seeds10 import CITIES, FULL, OLD, boot_ci, boot_ratio_ci

BLUE, GREY, RED = "#2a6fb0", "#8a8f98", "#c0392b"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6})
NAMES = {"NewDelhi": "New Delhi", "BuenosAires": "Buenos Aires", "NewYork": "New York", "Bombay": "Mumbai"}


def lab(c):
    return NAMES.get(c, c) + ("" if c in FULL else " *")


def panel(ax, runs, col, title, thr=None, xlabel="", cities=CITIES, ratio=None, offset=0.0, color=BLUE, show_seeds=True, label=None):
    ys = np.arange(len(cities))[::-1]
    for y, c in zip(ys, cities):
        d = runs[runs.city == c]
        if ratio:
            num, den = d[ratio[0]].values, d[ratio[1]].values
            if np.nanmean(den) < 0.5:
                continue
            m, lo, hi = boot_ratio_ci(num, den)
            m3, _, _ = boot_ratio_ci(d[d.seed.isin(OLD)][ratio[0]].values, d[d.seed.isin(OLD)][ratio[1]].values)
            pts = d[ratio[0]].values / np.where(d[ratio[1]].values > 0.5, d[ratio[1]].values, np.nan)
        else:
            x = d[col].astype(float).values
            x = x[np.isfinite(x)]
            if len(x) == 0:
                continue
            m, (lo, hi) = x.mean(), boot_ci(x)
            m3 = d[d.seed.isin(OLD)][col].astype(float).mean()
            pts = x
        if show_seeds:
            ax.plot(pts, np.full(len(pts), y + offset), ".", color=GREY, ms=3, alpha=0.7, zorder=1)
        ax.plot([lo, hi], [y + offset] * 2, "-", color=color, lw=2, zorder=2)
        ax.plot([m], [y + offset], "o", color=color, ms=6, zorder=3, label=label if y == ys[0] else None)
        if np.isfinite(m3):
            ax.plot([m3], [y + offset], "o", mfc="white", mec=color, ms=5, zorder=3)
    if thr is not None:
        ax.axvline(thr, color=RED, ls="--", lw=1)
    ax.set_yticks(ys)
    ax.set_yticklabels([lab(c) for c in cities])
    ax.set_title(title, fontsize=9.5, loc="left")
    ax.set_xlabel(xlabel)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=150)
    plt.close(fig)
    print("wrote", name)


def main():
    runs = pd.read_csv(RES / "seeds10_runs.csv")
    n = runs.groupby("city").seed.nunique().min()
    cap = ("filled: mean with bootstrap 95% CI over all seeds; open: mean of seeds 0-2; dots: seeds. Grid quantities: 10 seeds for New Delhi, Buenos Aires, London; "
           "seeds 0-2 only (reduced exact grid, lower bound) for the cities marked *. Equilibrium/DIP quantities: 8-10 seeds.")
    fig, ax = plt.subplots(1, 3, figsize=(13, 4.2))
    panel(ax[0], runs, "gain_congestion_only_pct", "Congestion-only gain (threshold 1.7%)", 1.7, "% of |SC|")
    panel(ax[1], runs, None, "Delivery-only share of the combined gain (ratio of means)", 0.5, "share", ratio=("gain_delivery_only_pct", "gain_both_pct"))
    panel(ax[2], runs, "gain_both_pct", "Two-instrument gain", None, "% of |SC|")
    ax[1].set_yticklabels([]); ax[2].set_yticklabels([])
    fig.text(0.01, 0.005, cap, fontsize=7.5, color="#555")
    save(fig, "seeds10_forest_gain.png")

    fig, ax = plt.subplots(1, 4, figsize=(15, 4.2))
    panel(ax[0], runs, "poa_zmc", "PoA, ZMC equilibrium (large above 1.10)", 1.10, "PoA")
    panel(ax[1], runs, "poa_worst", "PoA, worst equilibrium found", 1.10, "PoA")
    panel(ax[2], runs, "gap_unpriced_pct", "Unpriced gap to social optimum", None, "% of W_SO")
    panel(ax[3], runs, "priced_gap_pct", "Priced gap, grid-best point (upper bound if *)", 7.5, "% of W_SO")
    for a in ax[1:]:
        a.set_yticklabels([])
    fig.text(0.01, 0.005, cap, fontsize=7.5, color="#555")
    save(fig, "seeds10_forest_poa.png")

    fig, ax = plt.subplots(1, 4, figsize=(15, 4.2))
    panel(ax[0], runs, "dip_vs_grid_gain", "DIP gain / best grid gain (>= 1: DIP better)", 1.0, "ratio")
    panel(ax[1], runs, "dip_calls_share63", "DIP calls / calls of a 63-point grid", 0.10, "share")
    panel(ax[2], runs, "arp_vs_dip_gain", "ARP flat gain / DIP gain", 1.0, "ratio")
    panel(ax[3], runs, "mct_br_vs_dip_gain", "Marginal tariff + best responses / DIP gain", 1.0, "ratio")
    for a in ax[1:]:
        a.set_yticklabels([])
    fig.text(0.01, 0.005, cap, fontsize=7.5, color="#555")
    save(fig, "seeds10_forest_dip_arp.png")

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    cs = [c for c in CITIES if runs[runs.city == c].so_gap_pct_of_abs.mean() >= 2]  # cities where the unpriced equilibrium is far from the optimum
    panel(ax[0], runs, "so_share_grid", "Grid-best (blue), congestion-only (grey)", 1.0, "gain share vs social optimum", cities=cs, offset=0.12, label="grid-best two-parameter")
    panel(ax[0], runs, "so_share_grid_cong", "", None, "", cities=cs, offset=-0.18, color="#555", show_seeds=False, label="congestion-only")
    ax[0].legend(loc="lower right", fontsize=7)
    panel(ax[1], runs, "so_share_dip", "DIP (blue), ARP flat (orange), tariff + BR (green)", 1.0, "gain share vs social optimum", cities=cs, offset=0.2, label="DIP")
    panel(ax[1], runs, "so_share_arp", "", None, "", cities=cs, offset=0.0, color="#d98a1f", show_seeds=False, label="ARP flat")
    panel(ax[1], runs, "so_share_mct_br", "", None, "", cities=cs, offset=-0.2, color="#2e8b57", show_seeds=False, label="tariff + BR")
    ax[1].legend(loc="lower right", fontsize=7)
    fig.text(0.01, 0.005, "gain share = (SC unpriced - SC method) / (SC unpriced - SC social optimum); " + "cities with social-optimum gap >= 2% only; ARP: 10 seeds in New Delhi, Buenos Aires, London", fontsize=7, color="#555")
    save(fig, "seeds10_forest_so_share.png")


if __name__ == "__main__":
    main()
