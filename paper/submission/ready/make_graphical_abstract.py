"""Graphical abstract: three-layer schematic (left) and DIP vs. the best grid point (right).
Data: results/summary_seeds10_ci.csv (ten seeds, the three full-grid cities). No new results.
Run: python3 paper/submission/ready/make_graphical_abstract.py"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
d = pd.read_csv(os.path.join(REPO, "results", "summary_seeds10_ci.csv"))
cities = [("NewDelhi", "New Delhi"), ("BuenosAires", "Buenos Aires"), ("London", "London")]

def get(city, q):
    r = d[(d.city == city) & (d.quantity == q)].iloc[0]
    return r["mean"], r["ci_lo"], r["ci_hi"]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7})
BLUE, RED, GREY = "#1f5f99", "#c0392b", "#555555"
fig = plt.figure(figsize=(5.2, 2.1), dpi=600, facecolor="white")   # 13.2 x 5.3 cm
axl = fig.add_axes([0.0, 0.0, 0.52, 1.0]); axl.set_xlim(0, 1); axl.set_ylim(0, 1); axl.axis("off")
layers = [("1  Carriers' routing", "BRL: exact robust best\nresponses (probability boxes)", 0.70),
          ("2  Carriers' game", "competition and congestion;\nequilibrium of the carriers", 0.37),
          ("3  City's charges", "DIP / ARP: zone charges\nwithout equilibrium search", 0.04)]
for title, sub, y in layers:
    axl.add_patch(FancyBboxPatch((0.04, y), 0.92, 0.26, boxstyle="round,pad=0.005,rounding_size=0.02",
                                 fc="#f2f6fb", ec=BLUE, lw=1.0))
    axl.text(0.08, y + 0.205, title, fontsize=8, fontweight="bold", color=BLUE, va="center")
    axl.text(0.08, y + 0.095, sub, fontsize=7, color="black", va="center", linespacing=1.15)
for y0, y1 in ((0.70, 0.63), (0.37, 0.30)):
    axl.add_patch(FancyArrowPatch((0.5, y0), (0.5, y1), arrowstyle="-|>", mutation_scale=9, lw=1.2, color=GREY))

axr = fig.add_axes([0.66, 0.30, 0.32, 0.52])
w = 0.34
for k, (c, name) in enumerate(cities):
    g, glo, ghi = get(c, "dip_vs_grid_gain"); s, slo, shi = get(c, "dip_calls_share63")
    axr.bar(k - w / 2, g * 100, w, color=BLUE, yerr=[[(g - glo) * 100], [(ghi - g) * 100]], error_kw=dict(lw=0.7, capsize=1.5))
    axr.bar(k + w / 2, s * 100, w, color=RED, yerr=[[(s - slo) * 100], [(shi - s) * 100]], error_kw=dict(lw=0.7, capsize=1.5))
    axr.text(k - w / 2, g * 100 + 14, f"{g*100:.0f}", ha="center", fontsize=6.5, color=BLUE)
    axr.text(k + w / 2, s * 100 + 14, f"{s*100:.1f}", ha="center", fontsize=6.5, color=RED)
axr.axhline(100, color="k", lw=0.7, ls="--")
axr.set_xticks(range(3)); axr.set_xticklabels([n.replace(' ','\n') for _, n in cities], fontsize=6.5)
axr.set_ylim(0, 150); axr.set_ylabel("% of best grid point", fontsize=7)
axr.tick_params(labelsize=6.8, length=2)
for s_ in ("top", "right"): axr.spines[s_].set_visible(False)
fig.text(0.60, 0.93, "DIP: gain", color=BLUE, fontsize=7.5, fontweight="bold")
fig.text(0.74, 0.93, "and routing calls", color=RED, fontsize=7.5, fontweight="bold")
fig.text(0.60, 0.005, "Dashed line: best grid point (100). Ten seeds per\ncity; bars: mean, whiskers: bootstrap 95% CI.", fontsize=5.8, color=GREY, linespacing=1.2)
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(HERE, f"graphical_abstract.{ext}"), facecolor="white")
