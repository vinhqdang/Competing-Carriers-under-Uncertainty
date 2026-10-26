"""Figures for aggregate-response pricing: figures/arp_calls_vs_gain.png, figures/arp_paths.png, figures/arp_tiny.png."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from common import FIG, RES  # noqa: E402

COL = {"arp": "#1f77b4", "mct_br": "#2ca02c", "mct_so": "#9467bd", "dip": "#d62728", "grid": "#7f7f7f"}


def calls_vs_gain():
    d = pd.read_csv(RES / "summary_arp.csv")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for key, lab, mk in (("arp", "ARP flat (Q, n only)", "o"), ("mct_br", "marginal tariff + carriers' BR (own q, Q)", "s"),
                         ("mct_so", "marginal tariff + SO solve", "^"), ("dip", "DIP (oracle)", "D")):
        ax.scatter(d[f"{key}_calls"], d[f"{key}_gain_share"], label=lab, color=COL[key], marker=mk, s=45, alpha=0.85)
    ax.scatter(d["grid_calls"], np.ones(len(d)), label="E2 grid (exact points)", color=COL["grid"], marker="x", s=45)
    ax.set_xscale("log")
    ax.set_xlabel("routing-oracle calls (log)")
    ax.set_ylabel("social-cost gain / best grid gain")
    ax.axhline(1.0, color="k", lw=0.5, ls="--")
    ax.legend(fontsize=8, loc="lower left")
    ax.set_title("Leader methods on four cities, three seeds, exact oracle")
    fig.tight_layout()
    fig.savefig(FIG / "arp_calls_vs_gain.png", dpi=150)


def paths():
    d = pd.read_csv(RES / "summary_arp.csv")
    cities = list(dict.fromkeys(d.city))
    fig, axes = plt.subplots(1, len(cities), figsize=(3.4 * len(cities), 3.4), sharey=False)
    for ax, city in zip(np.atleast_1d(axes), cities):
        sub = d[d.city == city]
        for _, r in sub.iterrows():
            p = [float(x) for x in str(r.arp_sc_path).split(";")]
            share = (r.grid_sc0 - np.array(p)) / (r.grid_sc0 - r.grid_sc_best)
            ax.plot(range(len(p)), share, "-o", ms=3, color=COL["arp"], alpha=0.8, label="ARP flat" if r.seed == 0 else None)
            ax.axhline(r.dip_gain_share, color=COL["dip"], lw=0.8, ls=":", label="DIP" if r.seed == 0 else None)
        ax.axhline(1.0, color="k", lw=0.5, ls="--")
        ax.set_title(city)
        ax.set_xlabel("posted charges (rounds)")
    np.atleast_1d(axes)[0].set_ylabel("gain share of the best grid point")
    np.atleast_1d(axes)[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "arp_paths.png", dpi=150)


def tiny():
    t = pd.read_csv(RES / "arp_tiny.csv")
    g = t.sc_ne - t.opt_zone
    ok = g > 1e-9
    fig, ax = plt.subplots(figsize=(7, 4))
    data, labels = [], []
    for c, lab in (("arp_plain_sc", "ARP flat"), ("arp_known_sc", "ARP flat, lots known"), ("mct_br_sc", "tariff + BR"),
                   ("mct_so_sc", "tariff + SO solve"), ("dip_sc", "DIP"), ("grid_selected", "grid")):
        s = ((t.sc_ne - t[c]) / g)[ok].clip(-1, 1.2)
        data.append(s.values)
        labels.append(f"{lab}\nmean {s.mean():.2f}")
    ax.boxplot(data, tick_labels=labels, showmeans=True)
    ax.set_ylabel("share of the exact optimal gain (clipped at -1)")
    ax.set_title(f"Tiny games with exhaustive enumeration ({int(ok.sum())} instances with a gain)")
    fig.tight_layout()
    fig.savefig(FIG / "arp_tiny.png", dpi=150)


if __name__ == "__main__":
    calls_vs_gain()
    paths()
    tiny()
    print("figures written")
