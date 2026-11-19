"""Graphical abstract for the TRIP version: three panels (rate, few carriers, free entry and through traffic).
Data: mfg/results/gap.csv, summary_stake_who_pooled.csv and the number macros of mfg/paper (no new results).
Run: python3 mfg/submission/trip/make_graphical_abstract.py -> trip/graphical_abstract.{png,pdf} (3240 x 1320 px)."""
import os, re
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); MFG = os.path.dirname(os.path.dirname(HERE)); RES = f"{MFG}/results"
mac = {}
for f in ("numbers_ext.tex", "numbers.tex"):
    for m in re.finditer(r"\\newcommand\{\\(\w+)\}\{([^}]*)\}", open(f"{MFG}/paper/{f}").read()): mac[m.group(1)] = float(m.group(2)) if re.fullmatch(r"-?[\d.]+", m.group(2)) else m.group(2)
g = pd.read_csv(f"{RES}/gap.csv")
g = g[(g["mode"] == "replica") & (g.amp == 1.0) & (g.kappa_scale == 1.0)] if "replica" in set(g["mode"]) else g[(g.amp == 1.0) & (g.kappa_scale == 1.0)]
rel = (g.gap_m / g.QW_m).groupby(g.N).median()
w = pd.read_csv(f"{RES}/summary_stake_who_pooled.csv")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7})
BLUE, RED, GREY, GREEN = "#1f5f99", "#c0392b", "#555555", "#2e7d32"
fig = plt.figure(figsize=(5.4, 2.2), dpi=600, facecolor="white")
def title(x, t, sub):
    fig.text(x, 0.93, t, fontsize=7.6, fontweight="bold", color=BLUE)
    fig.text(x, 0.885, sub, fontsize=5.4, color=GREY, va="top", linespacing=1.1)
# 1: many carriers
ax = fig.add_axes([0.105, 0.22, 0.21, 0.50]); N = np.array([6, 1536.0])
ax.loglog(rel.index, rel.values, "-o", ms=2.5, lw=1.2, color=BLUE, label="cities")
ax.loglog(N, 0.5 * (N / 6) ** -1.0, "k--", lw=0.8, label=r"$N^{-1}$")
ax.loglog(N, 0.5 * (N / 6) ** -0.5, "k:", lw=0.9, label=r"$N^{-1/2}$ worst")
ax.set_xlabel("number of carriers $N$", fontsize=6.3); ax.set_ylabel("relative gap to limit", fontsize=6.3)
ax.tick_params(labelsize=6, length=2); ax.legend(fontsize=5.4, frameon=False, loc="lower left")
for s in ("top", "right"): ax.spines[s].set_visible(False)
title(0.015, "1  Many small carriers", "an observation-only charge is enough;\nthe gap falls like N$^{-0.88}$ on nine cities")
# 2: few carriers
a = fig.add_axes([0.44, 0.22, 0.20, 0.50]); r = w[(w.rule == "pm") & (w.N == 6)].iloc[0]
vals = [r.dPi, r.dCS, r.R, r.dSW]; a.bar(range(4), vals, color=[RED, GREEN, GREY, BLUE], width=0.65); a.axhline(0, color="k", lw=0.6)
a.set_xticks(range(4)); a.set_xticklabels(["carriers", "buyers", "city", "welfare"], fontsize=5.4, rotation=25)
a.set_ylim(-230, 190); a.tick_params(labelsize=6, length=2); a.set_ylabel("% of no-charge welfare", fontsize=6.0)
for i, v in enumerate(vals): a.text(i, v + (8 if v >= 0 else -8), f"{v:+.0f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=5.6)
for s in ("top", "right"): a.spines[s].set_visible(False)
title(0.39, "2  Few carriers", "efficient charge = subsidy the city pays;\nthe plain charge lowers welfare")
# 3: free entry + through traffic
b = fig.add_axes([0.76, 0.22, 0.22, 0.50]); x = np.arange(3)
sub = [mac["EntSixPmdSW"], mac["EntTwentyFourPmdSW"], mac["EntOneNinetyTwoPmdSW"]]; lim = [mac["EntSixMwGain"], mac["EntTwentyFourMwGain"], mac["EntOneNinetyTwoMwGain"]]
b.bar(x - 0.2, sub, 0.38, color=RED, label="subsidy rule"); b.bar(x + 0.2, lim, 0.38, color=GREEN, label="entry limited")
b.axhline(0, color="k", lw=0.6); b.set_xticks(x); b.set_xticklabels(["6", "24", "192"], fontsize=6); b.set_xlabel("carriers without charge, $N_0$", fontsize=6.0)
b.set_ylabel("welfare net of fixed costs, %", fontsize=6.0); b.tick_params(labelsize=6, length=2); b.legend(fontsize=5.4, frameon=False, loc="lower right")
for s in ("top", "right"): b.spines[s].set_visible(False)
title(0.70, "3  Free entry", f"the subsidy draws entrants; through\ntraffic delay is {mac['ExtRatioKQ']:.0f} times in-zone delay")
fig.text(0.015, 0.02, "Many small carriers: competitive urban delivery under zone-time charges. Nine cities, five seeds, stylised hourly profile.", fontsize=5.2, color=GREY)
for ext in ("png", "pdf"): fig.savefig(f"{HERE}/graphical_abstract.{ext}", facecolor="white")
