"""Plot population zones and major roads per city, plus an overview figure.

Usage:
    python experiments/plot_cities.py [city ...]

Reads data/processed/<city>/ and writes figures/<city>_map.png and figures/overview.png.
Uses matplotlib only (no map tiles).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.collections import LineCollection, PolyCollection  # noqa: E402
from matplotlib.colors import LogNorm, to_rgba  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from pyproj import Transformer  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
FIG = ROOT / "figures"
CITIES = ["NewDelhi", "Cairo", "Moscow", "BuenosAires", "NewYork", "Bombay"]

BG = "#0b0f19"
FG = "#d9dee8"
CMAP = plt.get_cmap("magma")
# Road class code 0..4 = motorway, trunk, primary, secondary, tertiary; 5..9 = the same as links.
ROAD_STYLE = {
    0: ("#fff1a8", 0.9), 1: ("#ffe08a", 0.8), 2: ("#ffc9a0", 0.7),
    3: ("#cfe8f5", 0.55), 4: ("#c9ced8", 0.45),
}
LINK_ALPHA = 0.75
LINK_WIDTH_FACTOR = 0.8


def load_city(city):
    d = PROC / city
    meta = json.loads((d / "meta.json").read_text())
    zones = pd.read_csv(d / "zones.csv")
    bounds = np.load(d / "zone_bounds.npy")
    g = np.load(d / "major_graph.npz")
    density = zones["pop"].to_numpy() / zones["area_km2"].to_numpy()
    return {
        "city": city, "meta": meta, "zones": zones, "bounds": bounds,
        "segments": g["segments"], "code": g["road_class_code"], "density": density,
    }


def projector(data):
    z = data["zones"]
    w = z["pop"].to_numpy()
    lon0 = float(np.sum(z["lon"] * w) / w.sum())
    lat0 = float(np.sum(z["lat"] * w) / w.sum())
    crs = f"+proj=aeqd +lat_0={lat0:.6f} +lon_0={lon0:.6f} +datum=WGS84 +units=km +no_defs"
    tr = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    return tr, lon0, lat0


def to_km(tr, lon, lat):
    x, y = tr.transform(np.asarray(lon, dtype=np.float64), np.asarray(lat, dtype=np.float64))
    return np.asarray(x), np.asarray(y)


def draw_city(ax, data, norm, show_title=True):
    """Draw zones (log colour), major roads (thin, by class) and the extract frame on ax."""
    tr, lon0, lat0 = projector(data)
    b = data["bounds"]                                       # west, south, east, north
    w, s, e, n = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
    xs, ys = to_km(tr, np.column_stack([w, e, e, w]).ravel(), np.column_stack([s, s, n, n]).ravel())
    verts = np.stack([xs, ys], axis=-1).reshape(-1, 4, 2)
    zones_pc = PolyCollection(verts, array=data["density"], cmap=CMAP, norm=norm, edgecolors="none")
    ax.add_collection(zones_pc)

    seg = data["segments"].reshape(-1, 2)
    sx, sy = to_km(tr, seg[:, 0], seg[:, 1])
    xy = np.stack([sx, sy], axis=-1).reshape(-1, 2, 2)
    colours, widths = [], []
    for c in data["code"]:
        base = ROAD_STYLE[int(c) % 5]
        if c >= 5:
            colours.append(to_rgba(base[0], LINK_ALPHA))
            widths.append(base[1] * LINK_WIDTH_FACTOR)
        else:
            colours.append(to_rgba(base[0], 0.95))
            widths.append(base[1])
    ax.add_collection(LineCollection(xy, colors=colours, linewidths=widths))

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
    ax.axhline(0, color="#3a4150", lw=0.5, zorder=0)
    ax.axvline(0, color="#3a4150", lw=0.5, zorder=0)
    if show_title:
        ax.set_title(f"{data['meta']['display_name']}  |  {data['meta']['continent']}  |  "
                     f"population in extract {data['meta']['population_extract_total'] / 1e6:.2f} M  |  "
                     f"{data['meta']['zone_count']} zones", color=FG, fontsize=10)
    return zones_pc, (lon0, lat0)


def colourbar(fig, mappable, ax_or_axes, label):
    cb = fig.colorbar(mappable, ax=ax_or_axes, fraction=0.035, pad=0.02)
    cb.set_label(label, color=FG)
    cb.ax.tick_params(colors=FG, labelsize=8)
    cb.outline.set_edgecolor("#3a4150")
    return cb


def plot_city_maps(datasets, norm):
    FIG.mkdir(exist_ok=True)
    for data in datasets:
        fig, ax = plt.subplots(figsize=(8.5, 7.5), dpi=150, facecolor=BG)
        pc, _ = draw_city(ax, data, norm)
        colourbar(fig, pc, ax, "people per km$^2$ (log scale)")
        fig.savefig(FIG / f"{data['city']}_map.png", facecolor=BG)
        plt.close(fig)


def plot_overview(datasets, norm):
    FIG.mkdir(exist_ok=True)
    fig, axes = plt.subplots(2, 4, figsize=(22, 11.5), dpi=130, facecolor=BG)
    fig.subplots_adjust(left=0.04, right=0.92, top=0.95, bottom=0.07, wspace=0.25, hspace=0.25)
    flat = axes.ravel()
    last = None
    for ax, data in zip(flat[:6], datasets):
        pc, _ = draw_city(ax, data, norm)
        last = pc
    for ax in flat[:6]:
        ax.title.set_fontsize(8)
    ax_t = flat[6]
    ax_t.set_facecolor(BG)
    ax_t.axis("off")
    header = ["City", "Continent", "Pop (M)", "Zones", "Major km"]
    rows = []
    total_pop = 0.0
    total_zones = 0
    total_road = 0.0
    for data in datasets:
        m = data["meta"]
        pop = m["population_extract_total"]
        total_pop += pop
        total_zones += m["zone_count"]
        total_road += m["road_km_major_zones"]
        rows.append([m["display_name"], m["continent"], f"{pop / 1e6:.2f}",
                     f"{m['zone_count']}", f"{m['road_km_major_zones']:,.0f}"])
    rows.append(["Total", "", f"{total_pop / 1e6:.2f}", f"{total_zones}", f"{total_road:,.0f}"])
    table = ax_t.table(cellText=rows, colLabels=header, loc="center", cellLoc="center",
                       colWidths=[0.24, 0.24, 0.16, 0.14, 0.18])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.7)
    for (r, _c), cell in table.get_celld().items():
        cell.set_edgecolor("#3a4150")
        cell.set_facecolor("#1a2030" if r == 0 else (BG if r < len(rows) else "#20283a"))
        cell.get_text().set_color(FG)
        if r == len(rows):
            cell.get_text().set_fontweight("bold")
    ax_t.text(0.5, 0.92, "Population within extract bounds", transform=ax_t.transAxes,
              ha="center", color=FG, fontsize=10)
    ax_t.text(0.5, 0.06,
              "Population: GHSL GHS-POP R2023A, epoch 2025 (Pesaresi et al., JRC)\n"
              "Roads: OpenStreetMap contributors (ODbL), BBBike extracts",
              transform=ax_t.transAxes, ha="center", color=FG, fontsize=7.5)
    for ax in list(flat[len(datasets):6]) + [flat[7]]:
        ax.set_visible(False)
    sm = ScalarMappable(norm=norm, cmap=CMAP)
    sm.set_array([])
    cax = fig.add_axes([0.94, 0.12, 0.010, 0.76])
    cb = fig.colorbar(sm, cax=cax)
    cb.set_label("people per km$^2$ (log scale, shared across panels)", color=FG)
    cb.ax.tick_params(colors=FG, labelsize=8)
    cb.outline.set_edgecolor("#3a4150")
    fig.savefig(FIG / "overview.png", facecolor=BG)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cities", nargs="*", help=f"subset of {', '.join(CITIES)} (default: all)")
    args = parser.parse_args(argv)
    cities = args.cities or CITIES
    unknown = [c for c in cities if c not in CITIES]
    if unknown:
        parser.error(f"unknown city: {', '.join(unknown)}")

    datasets = [load_city(c) for c in CITIES]          # overview always needs all cities
    dens = np.concatenate([d["density"] for d in datasets])
    norm = LogNorm(vmin=max(float(dens.min()), 1.0), vmax=float(dens.max()))
    print(f"density colour scale: {norm.vmin:.1f} to {norm.vmax:.0f} people per km^2")

    selected = [d for d in datasets if d["city"] in cities]
    plot_city_maps(selected, norm)
    if set(cities) == set(CITIES):
        plot_overview(datasets, norm)
    print("wrote", ", ".join(f"{d['city']}_map.png" for d in selected))


if __name__ == "__main__":
    sys.exit(main())
