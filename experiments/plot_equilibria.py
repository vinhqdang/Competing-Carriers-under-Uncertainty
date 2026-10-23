"""Equilibrium maps: zone price and travel-time slowdown of the unpriced equilibrium on the real zone rectangles
(style of experiments/plot_cities.py).  Needs results/zones_<city>.csv from run_equilibria.py.

  python experiments/plot_equilibria.py [city ...]   -> figures/eq_<city>.png and figures/overview_equilibria.png
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402

from common import FIG, RES, zb  # noqa: E402
from plot_cities import BG, FG, load_city, projector, to_km  # noqa: E402

IDLE = "#1f2638"


def rects(data, tr):
    b = data["bounds"]
    w, s, e, n = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    xs, ys = to_km(tr, np.column_stack([w, e, e, w]).ravel(), np.column_stack([s, s, n, n]).ravel())
    return np.stack([xs, ys], axis=-1).reshape(-1, 4, 2)


def draw(ax, verts, vals, cmap, norm, title, data):
    ax.add_collection(PolyCollection(verts, facecolors=IDLE, edgecolors="none"))
    m = np.isfinite(vals)
    pc = PolyCollection(verts[m], array=vals[m], cmap=cmap, norm=norm, edgecolors="none")
    ax.add_collection(pc)
    ax.set_xlim(verts[..., 0].min(), verts[..., 0].max())
    ax.set_ylim(verts[..., 1].min(), verts[..., 1].max())
    ax.set_aspect("equal", adjustable="box")
    ax.set_facecolor(BG)
    ax.tick_params(colors=FG, labelsize=7)
    for sp in ax.spines.values():
        sp.set_color("#3a4150")
    ax.set_title(title, color=FG, fontsize=9)
    return pc


def cbar(fig, pc, ax, label):
    cb = fig.colorbar(pc, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label(label, color=FG, fontsize=8)
    cb.ax.tick_params(colors=FG, labelsize=7)
    cb.outline.set_edgecolor("#3a4150")


def main(cities):
    FIG.mkdir(exist_ok=True)
    allp, alls = {}, {}
    for c in cities:
        f = RES / f"zones_{c}.csv"
        if not f.exists():
            continue
        z = pd.read_csv(f)
        data = load_city(c)
        tr, _, _ = projector(data)[0], None, None
        verts = rects(data, tr)
        fee = zb.load_wide(c)["delivery_fee_usd"]
        price = np.where(z.q > 0, z.price, np.nan)
        slow = np.where(z.X > 0, 100 * z.slowdown, np.nan)
        fig, axes = plt.subplots(1, 2, figsize=(13, 6), dpi=110, facecolor=BG)
        pc1 = draw(axes[0], verts, price, plt.get_cmap("viridis"), Normalize(np.nanmin(price), np.nanmax(price)),
                   f"{data['meta']['display_name']}: zone price per delivery (USD), grey = no delivery", data)
        cbar(fig, pc1, axes[0], "USD per delivery")
        pc2 = draw(axes[1], verts, slow, plt.get_cmap("magma"), Normalize(0, np.nanmax(slow)),
                   "added travel-time slowdown from delivery vehicles (%)", data)
        cbar(fig, pc2, axes[1], "percent")
        fig.tight_layout()
        fig.savefig(FIG / f"eq_{c}.png", facecolor=BG)
        plt.close(fig)
        allp[c] = (verts, price / fee, data)
        alls[c] = (verts, slow, data)
    if len(allp) == 9:
        for name, store, cmap, label, fname, norm in [
                ("price / fee", allp, "viridis", "zone price divided by the city's delivery fee", "overview_equilibria.png", None),
                ("slowdown", alls, "magma", "added slowdown (%)", "overview_slowdown.png", None)]:
            vmin = np.nanmin([np.nanmin(v[1]) for v in store.values()])
            vmax = np.nanmax([np.nanmax(v[1]) for v in store.values()])
            fig, axs = plt.subplots(3, 3, figsize=(16, 15), dpi=100, facecolor=BG)
            for ax, c in zip(axs.ravel(), zb.CITIES):
                verts, vals, data = store[c]
                pc = draw(ax, verts, vals, plt.get_cmap(cmap), Normalize(max(vmin, 0) if name == "slowdown" else vmin, vmax),
                          data["meta"]["display_name"], data)
            cax = fig.add_axes([0.93, 0.15, 0.012, 0.7])
            cb = fig.colorbar(pc, cax=cax)
            cb.set_label(label, color=FG)
            cb.ax.tick_params(colors=FG)
            fig.subplots_adjust(left=0.03, right=0.91, top=0.96, bottom=0.03, wspace=0.12, hspace=0.12)
            fig.savefig(FIG / fname, facecolor=BG)
            plt.close(fig)


if __name__ == "__main__":
    main(sys.argv[1:] or zb.CITIES)
