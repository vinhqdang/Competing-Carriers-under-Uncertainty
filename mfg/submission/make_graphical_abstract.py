"""Graphical abstract for the mean-field paper (rate against N; who gains and who loses).
Data: mfg/results/gap.csv and mfg/results/summary_stake_who_pooled.csv (no new results).
Run: python3 mfg/submission/make_graphical_abstract.py   -> submission/graphical_abstract.{png,pdf}"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(os.path.dirname(HERE), "results")
g = pd.read_csv(os.path.join(RES, "gap.csv"))
g = g[(g["mode"] == "replica") & (g.amp == 1.0) & (g.kappa_scale == 1.0)] if "replica" in set(g["mode"]) else g[(g.amp == 1.0) & (g.kappa_scale == 1.0)]
rel = (g.gap_m / g.QW_m).groupby(g.N).median()
w = pd.read_csv(os.path.join(RES, "summary_stake_who_pooled.csv"))

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7})
BLUE, RED, GREY, GREEN = "#1f5f99", "#c0392b", "#555555", "#2e7d32"
fig = plt.figure(figsize=(5.4, 2.2), dpi=600, facecolor="white")   # 13.7 x 5.6 cm, 3240 px wide

# left: rate
ax = fig.add_axes([0.105, 0.20, 0.27, 0.52])
N = np.array([6, 1536.0])
ax.loglog(rel.index, rel.values, "-o", ms=2.5, lw=1.2, color=BLUE, label="cities, median")
ax.loglog(N, 0.5 * (N / 6) ** -1.0, "k--", lw=0.8, label=r"$N^{-1}$")
ax.loglog(N, 0.5 * (N / 6) ** -0.5, "k:", lw=0.9, label=r"$N^{-1/2}$ (worst case)")
ax.set_xlabel("number of carriers $N$", fontsize=6.8)
ax.set_ylabel("relative gap to limit", fontsize=6.8)
ax.tick_params(labelsize=6.3, length=2)
ax.legend(fontsize=5.8, frameon=False, loc="lower left")
for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.text(0.02, 0.92, "1  Rate: gap against N", fontsize=8.2, fontweight="bold", color=BLUE)
fig.text(0.02, 0.885, "about one carrier's delivery; the worst case\n(square root) needs plans that couple zones", fontsize=5.6, color=GREY, va="top", linespacing=1.1)

# right: who gains, who loses (Pigou minus market power); two panels with own scales
def panel(rect, n, title, ylim):
    a = fig.add_axes(rect)
    r = w[(w.rule == "pm") & (w.N == n)].iloc[0]
    vals = [r.dPi, r.dCS, r.R, r.dSW]
    cols = [RED, GREEN, GREY, BLUE]
    a.bar(range(4), vals, color=cols, width=0.65)
    a.axhline(0, color="k", lw=0.6)
    a.set_xticks(range(4)); a.set_xticklabels(["carriers", "buyers", "city", "welfare"], fontsize=5.4, rotation=25)
    a.set_ylim(*ylim); a.tick_params(labelsize=6.0, length=2)
    for i, v in enumerate(vals):
        a.text(i, v + (0.04 * (ylim[1] - ylim[0]) if v >= 0 else -0.04 * (ylim[1] - ylim[0])), f"{v:+.0f}" if abs(v) >= 10 else f"{v:+.1f}",
               ha="center", va="bottom" if v >= 0 else "top", fontsize=5.8)
    a.set_title(title, fontsize=6.6, pad=2)
    for s in ("top", "right"): a.spines[s].set_visible(False)
    return a
a1 = panel([0.50, 0.20, 0.22, 0.50], 6, "6 carriers", (-230, 190))
a1.set_ylabel("% of no-charge welfare", fontsize=6.4)
panel([0.78, 0.20, 0.21, 0.50], 1536, "1536 carriers", (-2.5, 4.0))
fig.text(0.47, 0.92, "2  Who gains, who loses", fontsize=8.2, fontweight="bold", color=BLUE)
fig.text(0.47, 0.885, "market-power-corrected charge: with few carriers a subsidy\nthat carriers and buyers gain and the city pays", fontsize=5.6, color=GREY, va="top", linespacing=1.1)
fig.text(0.02, 0.015, "Many small carriers: mean-field limit of urban delivery under zone-time charges. Nine cities, five seeds, stylised hourly profile.", fontsize=5.4, color=GREY)
for ext in ("png", "pdf"):
    fig.savefig(os.path.join(HERE, f"graphical_abstract.{ext}"), facecolor="white")
