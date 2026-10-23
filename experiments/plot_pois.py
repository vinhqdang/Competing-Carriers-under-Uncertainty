"""Plot OpenStreetMap points of interest per city, plus an overview and a counts table.

Usage:
    python experiments/plot_pois.py [city ...]

Reads data/processed/<city>/ (zones, zone bounds, major graph, pois.csv, meta.json) and writes
figures/<city>_pois.png, figures/pois_overview.png (all six cities) and figures/poi_counts.png.
Uses matplotlib only (no map tiles). Projection, city loading and road styling come from plot_cities.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.collections import LineCollection, PolyCollection  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, LogNorm, to_rgba  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_cities import BG, CITIES, FG, FIG, LINK_WIDTH_FACTOR, PROC, ROAD_STYLE  # noqa: E402
from plot_cities import colourbar, load_city, projector, to_km  # noqa: E402

POI_CATEGORIES = ("shop", "market", "depot", "post_office", "locker", "wholesale")
# marker, colour, marker size, alpha. Shops are many and drawn as small translucent points.
POI_STYLE = {
    "shop": ("o", "#cfd8e3", 2.0, 0.28),
    "market": ("D", "#06d6a0", 20, 0.95),
    "depot": ("s", "#ef476f", 30, 0.95),
    "post_office": ("^", "#ffd166", 24, 0.95),
    "locker": ("P", "#c77dff", 30, 0.95),
    "wholesale": ("h", "#f77f00", 26, 0.95),
}
POI_LABEL = {
    "shop": "shop", "market": "market", "depot": "depot (warehouse, logistics, post depot)",
    "post_office": "post office", "locker": "parcel locker", "wholesale": "wholesale / trade",
}
ZONE_CMAP = LinearSegmentedColormap.from_list("zone_grey_blue", ["#121a2b", "#56698c"])
ROAD_WIDTH_FACTOR = 0.45
ROAD_ALPHA = 0.55
OSM_CREDIT = "POIs and roads: OpenStreetMap contributors (ODbL), BBBike extracts"
POP_CREDIT = "Population: GHSL GHS-POP R2023A, epoch 2025 (Pesaresi et al., JRC)"


def load_pois(city):
    d = PROC / city
    df = pd.read_csv(d / "pois.csv", usecols=["lon", "lat", "category"], dtype={"category": str},
                     keep_default_na=False)
    return df


def draw_city_pois(ax, data, pois, norm):
    """Population mesh (grey-blue by density), thin major roads, then POIs by category on top."""
    tr, _, _ = projector(data)
    b = data["bounds"]
    w, s, e, n = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    xs, ys = to_km(tr, np.column_stack([w, e, e, w]).ravel(), np.column_stack([s, s, n, n]).ravel())
    verts = np.stack([xs, ys], axis=-1).reshape(-1, 4, 2)
    ax.add_collection(PolyCollection(verts, array=data["density"], cmap=ZONE_CMAP, norm=norm,
                                     edgecolors="none"))

    seg = data["segments"].reshape(-1, 2)
    sx, sy = to_km(tr, seg[:, 0], seg[:, 1])
    xy = np.stack([sx, sy], axis=-1).reshape(-1, 2, 2)
    colours, widths = [], []
    for c in data["code"]:
        base = ROAD_STYLE[int(c) % 5]
        if c >= 5:
            colours.append(to_rgba(base[0], ROAD_ALPHA * LINK_WIDTH_FACTOR))
        else:
            colours.append(to_rgba(base[0], ROAD_ALPHA))
        widths.append(base[1] * ROAD_WIDTH_FACTOR)
    ax.add_collection(LineCollection(xy, colors=colours, linewidths=widths))

    px, py = to_km(tr, pois["lon"].to_numpy(), pois["lat"].to_numpy())
    cats = pois["category"].to_numpy()
    for cat in POI_CATEGORIES:
        m = cats == cat
        marker, colour, size, alpha = POI_STYLE[cat]
        ax.scatter(px[m], py[m], s=size, marker=marker, c=colour, alpha=alpha,
                   edgecolors="none" if cat == "shop" else "#0b0f19",
                   linewidths=0 if cat == "shop" else 0.4, zorder=3)

    m = data["meta"]["bbox"]
    bx, by = to_km(tr, [m["west"], m["east"], m["east"], m["west"]], [m["south"], m["south"], m["north"], m["north"]])
    ax.set_xlim(bx.min(), bx.max())
    ax.set_ylim(by.min(), by.max())
    ax.set_aspect("equal", adjustable="box")
    ax.set_facecolor(BG)
    ax.tick_params(colors=FG, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#3a4150")
    ax.set_xlabel("km east of city centre", color=FG, fontsize=9)
    ax.set_ylabel("km north of city centre", color=FG, fontsize=9)


def legend_handles(counts):
    handles = []
    for cat in POI_CATEGORIES:
        marker, colour, size, _ = POI_STYLE[cat]
        handles.append(Line2D([], [], linestyle="", marker=marker, markersize=max(4.0, size ** 0.5 * 1.1),
                              markerfacecolor=colour, markeredgecolor="#0b0f19" if cat != "shop" else colour,
                              label=f"{POI_LABEL[cat]}: {counts.get(cat, 0):,}"))
    return handles


def style_legend(leg):
    leg.get_frame().set_facecolor(BG)
    leg.get_frame().set_edgecolor("#3a4150")
    leg.get_frame().set_alpha(0.85)
    for t in leg.get_texts():
        t.set_color(FG)
        t.set_fontsize(7.5)


def plot_city_maps(datasets, norm):
    FIG.mkdir(exist_ok=True)
    for data in datasets:
        pois = load_pois(data["city"])
        meta = data["meta"]
        counts = pois["category"].value_counts().to_dict()
        fig, ax = plt.subplots(figsize=(8.5, 7.5), dpi=150, facecolor=BG)
        draw_city_pois(ax, data, pois, norm)
        ax.set_title(f"{meta['display_name']}  |  {meta['continent']}  |  {len(pois):,} OSM points of interest  |  "
                     f"{meta['poi_counts']['zones_with_depot']} of {meta['zone_count']} zones with a depot",
                     color=FG, fontsize=9.5)
        leg = ax.legend(handles=legend_handles(counts), loc="upper left", fontsize=7.5, framealpha=0.85,
                        title="OSM points (in extract)", title_fontsize=8)
        style_legend(leg)
        leg.get_title().set_color(FG)
        sm = ScalarMappable(norm=norm, cmap=ZONE_CMAP)
        sm.set_array([])
        colourbar(fig, sm, ax, "people per km$^2$ (log scale)")
        fig.text(0.01, 0.01, f"{POP_CREDIT}\n{OSM_CREDIT}", color=FG, fontsize=6.5, alpha=0.8)
        fig.savefig(FIG / f"{data['city']}_pois.png", facecolor=BG)
        plt.close(fig)


def plot_overview(datasets, norm):
    FIG.mkdir(exist_ok=True)
    fig, axes = plt.subplots(2, 3, figsize=(18, 11.5), dpi=110, facecolor=BG)
    fig.subplots_adjust(left=0.035, right=0.9, top=0.94, bottom=0.13, wspace=0.22, hspace=0.22)
    for ax, data in zip(axes.ravel(), datasets):
        pois = load_pois(data["city"])
        draw_city_pois(ax, data, pois, norm)
        ax.set_title(f"{data['meta']['display_name']}  |  {len(pois):,} POIs  |  "
                     f"{data['meta']['poi_counts']['zones_with_depot']} zones with a depot",
                     color=FG, fontsize=9)
    handles = [Line2D([], [], linestyle="", marker=POI_STYLE[c][0], markersize=max(4.0, POI_STYLE[c][2] ** 0.5 * 1.1),
                      markerfacecolor=POI_STYLE[c][1], markeredgecolor="#0b0f19" if c != "shop" else POI_STYLE[c][1],
                      label=POI_LABEL[c]) for c in POI_CATEGORIES]
    leg = fig.legend(handles=handles, loc="lower center", ncol=6, bbox_to_anchor=(0.47, 0.012), fontsize=9,
                     framealpha=0.85)
    style_legend(leg)
    for t in leg.get_texts():
        t.set_fontsize(9)
    sm = ScalarMappable(norm=norm, cmap=ZONE_CMAP)
    sm.set_array([])
    cax = fig.add_axes([0.925, 0.25, 0.010, 0.6])
    cb = fig.colorbar(sm, cax=cax)
    cb.set_label("people per km$^2$ (log scale, shared across panels)", color=FG)
    cb.ax.tick_params(colors=FG, labelsize=8)
    cb.outline.set_edgecolor("#3a4150")
    fig.text(0.035, 0.985, f"{POP_CREDIT}. {OSM_CREDIT}.", ha="left", va="top", color=FG, fontsize=7.5, alpha=0.8)
    fig.savefig(FIG / "pois_overview.png", facecolor=BG)
    plt.close(fig)


def plot_counts_table(datasets):
    FIG.mkdir(exist_ok=True)
    header = ["City", "POIs", *POI_CATEGORIES, "Zones", "Zones w/ depot", "Build (s)"]
    rows = []
    totals = {c: 0 for c in POI_CATEGORIES}
    tot_pois = tot_zones = tot_dep = 0
    tot_s = 0.0
    for data in datasets:
        m = data["meta"]
        ext = m["poi_counts"]["extract"]
        for c in POI_CATEGORIES:
            totals[c] += ext[c]
        tot_pois += m["poi_counts"]["extract_total"]
        tot_zones += m["zone_count"]
        tot_dep += m["poi_counts"]["zones_with_depot"]
        tot_s += m["poi_build_seconds"]
        rows.append([m["display_name"], f"{m['poi_counts']['extract_total']:,}",
                     *[f"{ext[c]:,}" for c in POI_CATEGORIES], f"{m['zone_count']}",
                     f"{m['poi_counts']['zones_with_depot']}", f"{m['poi_build_seconds']:.1f}"])
    rows.append(["Total", f"{tot_pois:,}", *[f"{totals[c]:,}" for c in POI_CATEGORIES], f"{tot_zones}",
                 f"{tot_dep}", f"{tot_s:.1f}"])

    fig, ax = plt.subplots(figsize=(13, 3.6), dpi=130, facecolor=BG)
    ax.set_facecolor(BG)
    ax.axis("off")
    table = ax.table(cellText=rows, colLabels=header, loc="center", cellLoc="center",
                     colWidths=[0.14, 0.08, 0.08, 0.08, 0.08, 0.1, 0.09, 0.1, 0.08, 0.1, 0.09])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.6)
    for (r, _c), cell in table.get_celld().items():
        cell.set_edgecolor("#3a4150")
        cell.set_facecolor("#1a2030" if r == 0 else (BG if r < len(rows) else "#20283a"))
        cell.get_text().set_color(FG)
        if r == len(rows):
            cell.get_text().set_fontweight("bold")
    ax.text(0.5, 0.95, "OpenStreetMap points of interest per city (counts in the extract; zone columns use populated zones)",
            transform=ax.transAxes, ha="center", color=FG, fontsize=10)
    ax.text(0.5, 0.02, "Counts reflect OSM tagging, not business census data. "
            "Source: OpenStreetMap contributors (ODbL), BBBike extracts, replication 2026-10-16T23:00:00Z.",
            transform=ax.transAxes, ha="center", color=FG, fontsize=7.5)
    fig.savefig(FIG / "poi_counts.png", facecolor=BG, bbox_inches="tight")
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cities", nargs="*", help=f"subset of {', '.join(CITIES)} (default: all)")
    args = parser.parse_args(argv)
    cities = args.cities or CITIES
    unknown = [c for c in cities if c not in CITIES]
    if unknown:
        parser.error(f"unknown city: {', '.join(unknown)}")

    datasets = [load_city(c) for c in CITIES]          # overview and shared colour scale need all cities
    dens = np.concatenate([d["density"] for d in datasets])
    norm = LogNorm(vmin=max(float(dens.min()), 1.0), vmax=float(dens.max()))
    print(f"density colour scale: {norm.vmin:.1f} to {norm.vmax:.0f} people per km^2")

    selected = [d for d in datasets if d["city"] in cities]
    plot_city_maps(selected, norm)
    if set(cities) == set(CITIES):
        plot_overview(datasets, norm)
        plot_counts_table(datasets)
    print("wrote", ", ".join(f"{d['city']}_pois.png" for d in selected))


if __name__ == "__main__":
    sys.exit(main())
