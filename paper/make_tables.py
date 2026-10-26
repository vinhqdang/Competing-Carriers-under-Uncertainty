"""Generate the LaTeX tables and number macros of the manuscript from the result files.

Run from any directory:  python paper/make_tables.py
Inputs : results/summary_*.csv, results/arp_*.csv, data/parameters/city_parameters_wide.csv, data/processed/<city>/meta.json,
         theory/new_algorithm_A/results.json (ZMC prototype), theory/new_algorithm_B/*.json(l) (BRL prototype).
Outputs: paper/tables/*.tex (one table body per file) and paper/tables/macros.tex (numbers quoted in the text).

When a summary file carries a column `<c>_sd` (seed standard deviation) next to a displayed column `<c>`,
the table shows `mean (sd)`. Re-run this script after the summaries change, then recompile the paper.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
OUT = ROOT / "paper" / "tables"
OUT.mkdir(parents=True, exist_ok=True)

ORDER = ["NewDelhi", "Cairo", "Moscow", "BuenosAires", "NewYork", "Bombay", "London", "Paris", "Berlin"]
NAME = {"NewDelhi": "New Delhi", "Cairo": "Cairo", "Moscow": "Moscow", "BuenosAires": "Buenos Aires",
        "NewYork": "New York", "Bombay": "Mumbai", "London": "London", "Paris": "Paris", "Berlin": "Berlin"}
WIDE_KEY = {"New Delhi": "NewDelhi", "Cairo": "Cairo", "Moscow": "Moscow", "Buenos Aires": "BuenosAires",
            "New York": "NewYork", "Mumbai": "Bombay", "London": "London", "Paris": "Paris", "Berlin": "Berlin"}

MACROS = {}


def macro(name, value):
    MACROS[name] = value


def fmt(v, sig=3, pct=False):
    """Compact number formatting for tables (no scientific notation unless tiny)."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "--"
    if isinstance(v, (bool, np.bool_)):
        return "yes" if v else "no"
    if isinstance(v, str):
        return v
    v = float(v)
    if v == 0:
        return "0"
    a = abs(v)
    if a < 1e-3:
        e = int(math.floor(math.log10(a)))
        return f"${v / 10 ** e:.1f}\\cdot10^{{{e}}}$"
    if a >= 1000:
        return f"{v:,.0f}".replace(",", "\\,")
    d = max(0, sig - 1 - int(math.floor(math.log10(a))))
    s = f"{v:.{d}f}"
    return s


def cell(row, col, df, sig=3):
    s = fmt(row[col], sig)
    sd = f"{col}_sd"
    if sd in df.columns and not pd.isna(row[sd]):
        s += f" ({fmt(row[sd], 2)})"
    return s


def order(df, col="city"):
    df = df[df[col].isin(ORDER)].copy()
    df["_o"] = df[col].map({c: i for i, c in enumerate(ORDER)})
    return df.sort_values("_o").drop(columns="_o")


def write_table(fname, header, rows, align):
    lines = ["\\begin{tabular}{" + align + "}", "\\toprule", " & ".join(header) + " \\\\", "\\midrule"]
    lines += [" & ".join(r) + " \\\\" for r in rows]
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / fname).write_text("\n".join(lines) + "\n")


def read(name):
    p = RES / name
    return pd.read_csv(p) if p.exists() else None


# ---------------------------------------------------------------- data and calibration
def t_params():
    w = pd.read_csv(ROOT / "data/parameters/city_parameters_wide.csv")
    cols = [("parcels_per_capita_per_day", "parcels/cap./day", 3), ("tomtom_congestion_pct", "cong.\\ \\%", 3),
            ("drops_per_vehicle_per_day", "drops/veh.", 3), ("shift_hours", "shift h", 2),
            ("van_capacity_parcels", "van cap.", 3), ("delivery_fee_usd", "fee USD", 3),
            ("driver_wage_usd_per_hour", "wage USD/h", 3), ("fuel_usd_per_litre", "fuel USD/L", 3),
            ("n_major_carriers", "$N$", 1), ("vehicles_per_1000_people", "veh./1000", 3)]
    w["key"] = w.city.map(WIDE_KEY)
    w = order(w, "key")
    rows = [[NAME[r.key]] + [fmt(r[c], s) for c, _, s in cols] for _, r in w.iterrows()]
    write_table("tab_params.tex", ["City"] + [h for _, h, _ in cols], rows, "l" + "r" * len(cols))


def t_cities():
    w = pd.read_csv(ROOT / "data/parameters/city_parameters_wide.csv")
    w["key"] = w.city.map(WIDE_KEY)
    w = w.set_index("key")
    rows, zs = [], []
    for c in ORDER:
        p = ROOT / "data/processed" / c / "meta.json"
        if not p.exists():
            continue
        m = json.loads(p.read_text())
        zs.append(m["zone_count"])
        rows.append([NAME[c], str(m["zone_count"]), fmt(m["population_zones_total"] / 1e6, 3),
                     fmt(m["road_km_major_zones"], 3), fmt(m["lane_km_major_zones"], 3),
                     str(m["graph_nodes"]).replace("000", "\\,000") if False else fmt(m["graph_nodes"], 3),
                     str(int(w.loc[c, "n_major_carriers"]))])
    write_table("tab_cities.tex", ["City", "$Z$", "pop.\\ (M)", "major road km", "lane-km", "graph nodes", "$N$"],
                rows, "lrrrrrr")
    macro("Zmin", str(min(zs)))
    macro("Zmax", str(max(zs)))
    macro("NCities", str(len(zs)))


# ---------------------------------------------------------------- E1
def t_e1():
    d = read("summary_E1.csv")
    if d is None:
        return
    d = order(d)
    cols = [("N", 1), ("Z", 3), ("served_share", 2), ("slowdown_pct", 2), ("mean_price", 3), ("vehicle_hours", 3),
            ("welfare", 3), ("calls", 2), ("max_regret_lp", 2), ("eta_rel", 2)]
    rows = []
    for _, r in d.iterrows():
        row = [NAME[r.city]]
        for c, s in cols:
            if c == "served_share":
                v = fmt(r[c], 2)
                if "served_sd" in d.columns:
                    v += f" ({fmt(r['served_sd'], 1)})"
                row.append(v)
            elif c == "welfare":
                v = fmt(r[c], 3)
                if "welfare_sd" in d.columns:
                    v += f" ({fmt(r['welfare_sd'], 2)})"
                row.append(v)
            else:
                row.append(cell(r, c, d, s))
        rows.append(row)
    write_table("tab_e1.tex", ["City", "$N$", "$Z$", "served", "slowdown \\%", "price", "veh.-h", "welfare",
                               "calls", "regret$^{\\rm LP}$", "$\\eta_{\\rm rel}$"], rows, "l" + "r" * len(cols))
    hi = d[d.served_share >= 0.8]
    lo = d[d.served_share < 0.8]
    macro("EoneHighCities", ", ".join(NAME[c] for c in hi.city))
    macro("EoneLowCities", ", ".join(NAME[c] for c in lo.city))
    macro("EoneServedHighMin", fmt(100 * hi.served_share.min(), 2))
    macro("EoneServedLowMin", fmt(100 * lo.served_share.min(), 2))
    macro("EoneServedLowMax", fmt(100 * lo.served_share.max(), 2))
    macro("EoneSlowMin", fmt(d.slowdown_pct.min(), 2))
    macro("EoneSlowMax", fmt(d.slowdown_pct.max(), 3))
    macro("EoneSlowMaxCity", NAME[d.loc[d.slowdown_pct.idxmax(), "city"]])
    macro("EoneRegretMax", fmt(d.max_regret.max()))
    macro("EoneRegretLPMax", fmt(d.max_regret_lp.max(), 2))
    macro("EoneEtaMin", fmt(100 * d.eta_rel.min(), 2))
    macro("EoneEtaMax", fmt(100 * d.eta_rel.max(), 2))
    macro("EoneCallsMin", fmt(d.calls.min(), 2))
    macro("EoneCallsMax", fmt(d.calls.max(), 2))
    macro("EoneEtaBelowOne", str(int((d.eta_rel < 0.01).sum())))


def t_sens():
    s = read("summary_E1_sensitivity.csv")
    if s is None:
        return
    params = [("delivery_fee_usd", "fee"), ("driver_wage_usd_per_hour", "wage"), ("drops_per_vehicle_per_day", "drops"),
              ("n_major_carriers", "$N$"), ("parcels_per_capita_per_day", "parcels")]
    rows = []
    for c in ORDER:
        x = s[s.city == c]
        if not len(x):
            continue
        row = [NAME[c]]
        for p, _ in params:
            y = x[x.param == p].d_welfare_pct
            row.append(f"{y.min():.0f} to {y.max():.0f}" if len(y) else "--")
        rows.append(row)
    write_table("tab_sens.tex", ["City"] + [h for _, h in params], rows, "lrrrrr")


# ---------------------------------------------------------------- E2 (per-seed summaries)
def seeds_note(df, key):
    n = int(df["seed"].nunique()) if "seed" in df.columns else 1
    macro(key, f"{n} seed{'s' if n > 1 else ''}")
    return n


def mrange(x, sig=3):
    """'mean (min--max)' over seeds, or the single value."""
    x = pd.Series(x).dropna()
    if not len(x):
        return "--"
    if len(x) == 1:
        return fmt(x.iloc[0], sig)
    if x.min() == x.max():
        return fmt(x.iloc[0], sig)
    return f"{fmt(x.mean(), sig)} [{fmt(x.min(), 2)}, {fmt(x.max(), 2)}]"


def byseed(x, sig=3):
    x = pd.Series(x).dropna()
    return " / ".join(fmt(v, sig) for v in x) if len(x) else "--"


def reduced_cities(exp, full):
    d = read("summary_exact_oracle.csv")
    if d is None:
        return set()
    e = d[d.experiment == exp]
    return {c for c, g in e.groupby("city") if (g.rows_exact < full).any()}


MATERIAL = 0.5  # leader gain (% of |SC|) below which the delivery-only share is not informative


def t_e2():
    s = read("summary_E2.csv")
    if s is None:
        return
    if "seed" not in s.columns:
        s["seed"] = 0
    n = seeds_note(s, "EtwoSeeds")
    macro("NSeeds", str(n))
    macro("NCases", str(len(set(zip(s.city, s.seed)))))
    red2 = reduced_cities("E2", 63)
    for obj, fname in (("main", "tab_e2.tex"), ("broad", "tab_e2broad.tex")):
        x = s[s.objective == obj]
        rows = []
        for c in ORDER:
            y = x[x.city == c]
            if not len(y):
                continue
            g = {cfg: y[y.config == cfg].sort_values("seed") for cfg in ("congestion_only", "delivery_only", "both")}
            b = g["both"]
            share = (g["delivery_only"].gain_pct_of_abs.values / np.where(b.gain_pct_of_abs.values > 0, b.gain_pct_of_abs.values, np.nan))
            row = [NAME[c] + ("$^\\dagger$" if c in red2 else ""), mrange(g["congestion_only"].gain_pct_of_abs), mrange(g["delivery_only"].gain_pct_of_abs),
                   mrange(b.gain_pct_of_abs)]
            if obj == "main":
                mat = b.gain_pct_of_abs.values >= MATERIAL
                row.append(byseed([v if m else np.nan for v, m in zip(share, mat)], 2) if mat.any() else "--")
                row += [f"{int((b.s_over_fee < 0).sum())}/{len(b)}", mrange(b.served_share, 2), mrange(b.revenue, 3)]
            else:
                row += [byseed(b.gain_pct_of_abs, 3), mrange(b.served_share, 2)]
            rows.append(row)
        if obj == "main":
            write_table(fname, ["City", "cong.\\ only", "deliv.\\ only", "both", "deliv.\\ share by seed",
                                "subsidy", "served", "revenue"], rows, "lrrrrrrr")
        else:
            write_table(fname, ["City", "cong.\\ only", "deliv.\\ only", "both", "both by seed", "served"], rows, "lrrrrr")
    m = s[s.objective == "main"]
    piv = m.pivot_table(index=["city", "seed"], columns="config", values="gain_pct_of_abs").reset_index()
    i = piv.congestion_only.idxmax()
    macro("EtwoCongMax", fmt(piv.congestion_only.max(), 3))
    macro("EtwoCongMaxCase", f"{NAME[piv.loc[i, 'city']]}, seed {int(piv.loc[i, 'seed'])}")
    rest = piv.drop(index=i)
    j = rest.congestion_only.idxmax()
    macro("EtwoCongSecond", fmt(rest.congestion_only.max(), 3))
    macro("EtwoCongSecondCase", f"{NAME[rest.loc[j, 'city']]}, seed {int(rest.loc[j, 'seed'])}")
    macro("EtwoCongBelowN", str(int((piv.congestion_only < 1.7).sum())))
    zba = piv[piv.city == "BuenosAires"].sort_values("seed")
    macro("EtwoCongBA", " / ".join(fmt(v, 2) for v in zba.congestion_only))
    macro("EtwoBothMax", fmt(piv.both.max(), 3))
    mat = piv[piv.both >= MATERIAL].copy()
    mat["share"] = mat.delivery_only / mat.both
    macro("EtwoMaterialN", str(len(mat)))
    macro("EtwoShareGeHalfN", str(int((mat.share >= 0.5).sum())))
    bad = mat[mat.share < 0.5]
    macro("EtwoShareLowCases", ", ".join(f"{NAME[r.city]} seed {int(r.seed)} ({fmt(r.share, 2)})" for _, r in bad.iterrows()) or "none")
    parts = []
    for c in ORDER:
        z = mat[mat.city == c]
        if len(z):
            parts.append(f"{NAME[c]} {fmt(z.share.min(), 2)}--{fmt(z.share.max(), 2)}" if len(z) > 1 else f"{NAME[c]} {fmt(z.share.iloc[0], 2)}")
    macro("EtwoShareRanges", ", ".join(parts))
    fparts = []
    for c in ORDER:
        z = mat[(mat.city == c) & (~mat.city.isin(red2))]
        if len(z):
            lo_, hi_ = fmt(z.share.min(), 2), fmt(z.share.max(), 2)
            fparts.append(f"{NAME[c]} {lo_}" + (f"--{hi_}" if lo_ != hi_ else " in every seed"))
    macro("EtwoShareFullRanges", ", ".join(fparts))
    macro("EtwoShareAboveOne", ", ".join(f"{NAME[r.city]} seed {int(r.seed)}" for _, r in mat[mat.share > 1.0001].iterrows()) or "none")
    mb = mat[mat.city == "Bombay"].sort_values("seed")
    macro("EtwoMumbaiShares", " / ".join(fmt(v, 2) for v in mb.share))
    small = [c for c in ORDER if c in set(piv.city) and (piv[piv.city == c].both < MATERIAL).all()]
    macro("EtwoSmallCities", ", ".join(NAME[c] for c in small))
    macro("EtwoSmallMax", fmt(piv[piv.city.isin(small)].both.max(), 2) if small else "--")
    for c, key in (("London", "London"), ("NewDelhi", "Delhi"), ("BuenosAires", "BA")):
        z = piv[piv.city == c]
        macro(f"Etwo{key}BothMin", fmt(z.both.min(), 3))
        macro(f"Etwo{key}BothMax", fmt(z.both.max(), 3))
        macro(f"Etwo{key}DelMin", fmt(z.delivery_only.min(), 3))
        macro(f"Etwo{key}DelMax", fmt(z.delivery_only.max(), 3))
    bs = m[m.config == "both"]
    matb = bs.merge(mat[["city", "seed"]], on=["city", "seed"])
    macro("EtwoSubsidyMaterial", f"{int((matb.s_over_fee < 0).sum())} of {len(matb)}")
    bys = read("summary_E2_by_seed.csv")
    if bys is not None and "delivery_best_is_subsidy" in bys.columns:
        mm = bys[bys.both >= MATERIAL]
        macro("EtwoDelivSubsidyMaterial", f"{int(mm.delivery_best_is_subsidy.astype(str).str.lower().eq('true').sum())} of {len(mm)}")
    br = s[(s.objective == "broad") & (s.config == "both")]
    shut = [c for c in ORDER if c in set(br.city) and (br[br.city == c].served_share <= 1e-9).all()]
    macro("EtwoBroadShutdownCities", ", ".join(NAME[c] for c in shut))
    macro("EtwoBroadBA", byseed(br[br.city == "BuenosAires"].sort_values("seed").gain_pct_of_abs, 2))
    pa = br[br.city == "Paris"]
    macro("EtwoBroadParisServedMax", fmt(100 * pa.served_share.max(), 2))


# ---------------------------------------------------------------- E3
def t_e3():
    d = read("summary_E3.csv")
    if d is None:
        return
    if "seed" not in d.columns:
        d["seed"] = 0
    seeds_note(d, "EthreeSeeds")
    rows = []
    for c in ORDER:
        z = d[d.city == c].sort_values("seed")
        if not len(z):
            continue
        rows.append([NAME[c], mrange(z.W_SO, 3), (str(int(z.n_ne_distinct.min())) if z.n_ne_distinct.min() == z.n_ne_distinct.max() else f"{int(z.n_ne_distinct.min())}--{int(z.n_ne_distinct.max())}"),
                     byseed(z.PoA_zmc, 3), byseed(z.PoA, 3), byseed(z.PoS, 3), byseed(z.rel_gap_priced_pct, 2)])
    write_table("tab_e3.tex", ["City", "$W_{\\rm SO}$", "\\#NE", "PoA (ZMC eq.)", "PoA (worst NE)", "PoS",
                               "priced gap \\%"], rows, "lrrrrrr")
    g = d.groupby("city")
    low = [c for c in ORDER if c in g.groups and g.get_group(c).PoA_zmc.max() <= 1.06]
    high = [c for c in ORDER if c in g.groups and c not in low]
    macro("PoAlowCities", ", ".join(NAME[c] for c in low))
    macro("PoAlowN", str(len(low)))
    macro("PoAlowMax", fmt(d[d.city.isin(low)].PoA_zmc.max(), 3))
    macro("PoAhighCities", ", ".join(NAME[c] for c in high))
    for c, key in (("London", "London"), ("BuenosAires", "BA"), ("NewDelhi", "Delhi")):
        z = d[d.city == c]
        macro(f"PoA{key}Min", fmt(z.PoA_zmc.min(), 3))
        macro(f"PoA{key}Max", fmt(z.PoA_zmc.max(), 3))
    macro("PoAmax", fmt(d.PoA_zmc.max(), 3))
    macro("PoAworstMax", fmt(d.PoA.max(), 3))
    macro("PoAmaxCity", NAME[d.loc[d.PoA_zmc.idxmax(), "city"]])
    i = d.rel_gap_priced_pct.idxmax()
    macro("PricedGapMax", fmt(d.rel_gap_priced_pct.max(), 2))
    macro("PricedGapMaxCase", f"{NAME[d.loc[i, 'city']]}, seed {int(d.loc[i, 'seed'])}")
    macro("PoApricedMax", fmt(d.PoA_priced.max(), 3))
    zd = d[d.city == "NewDelhi"]
    macro("PricedGapDelhiMax", fmt(zd.rel_gap_priced_pct.max(), 2))
    macro("PricedGapDelhiSeed", str(int(zd.loc[zd.rel_gap_priced_pct.idxmax(), "seed"])))
    smallgap = [c for c in ORDER if c in g.groups and g.get_group(c).rel_gap_priced_pct.max() <= 0.4]
    macro("PricedSmallN", str(len(smallgap)))
    macro("PricedSmallCities", ", ".join(NAME[c] for c in smallgap))
    diff = d.PoA - d.PoS
    big = d[diff > 0.05]
    macro("PoSgapN", str(len(big)))
    macro("PoSgapTotal", str(len(d)))
    macro("PoSgapCases", ", ".join(f"{NAME[r.city]} seed {int(r.seed)} (PoS {fmt(r.PoS, 3)}, worst {fmt(r.PoA, 3)})" for _, r in big.iterrows()))
    macro("SObound", fmt(100 * (d.W_SO_bound / d.W_SO - 1).max(), 2))
    macro("SOboundCity", NAME[d.loc[(d.W_SO_bound / d.W_SO).idxmax(), "city"]])
    macro("NEmin", str(int(d.n_ne_distinct.min())))
    macro("NEmax", str(int(d.n_ne_distinct.max())))


# ---------------------------------------------------------------- E4
def t_e4():
    s = read("summary_E4.csv")
    if s is None:
        return
    if "seed" not in s.columns:
        s["seed"] = 0
    seeds_note(s, "EfourSeeds")
    pb = s[s.kind == "pbox"].sort_values("eps").groupby(["city", "seed"]).tail(1)
    ga = s[s.kind == "gamma"].sort_values("delta").groupby(["city", "seed"]).tail(1)
    mono = read("summary_E4_monotone.csv")
    red4 = reduced_cities("E4", 12)
    rows = []
    for c in ORDER:
        a, g = pb[pb.city == c], ga[ga.city == c]
        if not len(a) or not len(g):
            continue
        mcount = "--"
        if mono is not None:
            z = mono[mono.city == c]
            mcount = f"{int(z.monotone.astype(str).str.lower().eq('true').sum())}/{len(z)}"
        rows.append([NAME[c] + ("$^\\dagger$" if c in red4 else ""), mrange(a.d_deliveries_pct, 3), mrange(a.d_welfare_pct, 3), mrange(g.d_deliveries_pct, 3),
                     mrange(g.d_welfare_pct, 3), mcount])
    write_table("tab_e4.tex", ["City", "$\\Delta$deliv.\\ \\%", "$\\Delta W$ \\%", "$\\Delta$deliv.\\ \\%",
                               "$\\Delta W$ \\%", "monotone series"], rows, "lrrrrr")
    macro("EfourEps", fmt(pb.eps.max(), 2))
    macro("EfourDelta", fmt(ga.delta.max(), 2))
    macro("EfourPbDelMin", fmt(-pb.d_deliveries_pct.max(), 2))
    macro("EfourPbDelMax", fmt(-pb.d_deliveries_pct.min(), 2))
    macro("EfourPbWMin", fmt(-pb.d_welfare_pct.max(), 2))
    macro("EfourPbWMax", fmt(-pb.d_welfare_pct.min(), 2))
    macro("EfourGaDelMin", fmt(-ga.d_deliveries_pct.max(), 2))
    macro("EfourGaDelMax", fmt(-ga.d_deliveries_pct.min(), 3))
    macro("EfourGaWMin", fmt(-ga.d_welfare_pct.max(), 2))
    macro("EfourGaWMax", fmt(-ga.d_welfare_pct.min(), 3))
    lo = pb[pb.city == "London"].sort_values("seed")
    macro("EfourLondonPb", " / ".join(fmt(v, 3) for v in lo.d_deliveries_pct))
    if mono is not None:
        ok = mono.monotone.astype(str).str.lower().eq("true")
        macro("EfourNonMonoN", str(int((~ok).sum())))
        macro("EfourSeries", str(len(mono)))
        allok = [c for c in ORDER if c in set(mono.city) and ok[mono.city == c].all()]
        macro("EfourMonoCitiesN", str(len(allok)))
        macro("EfourNonMonoCities", ", ".join(NAME[c] for c in ORDER if c in set(mono.city) and c not in allok))
        macro("EfourMaxRise", str(int(mono.max_increase.max())))
    macro("EfourAllConverged", "all" if bool(s.converged.astype(str).str.lower().eq("true").all()) else "not all")
    macro("EfourRegretMax", fmt(s.max_regret.max()))


# ---------------------------------------------------------------- verification and E5, E6
def t_e5():
    d = read("summary_E5_calls_vs_Z.csv")
    if d is None:
        return
    d = order(d)
    rows = []
    for _, r in d.iterrows():
        rows.append([NAME[r.city], str(int(r.N)), str(int(r.Z)), str(int(r.d_eff))]
                    + [str(int(r[f"calls_{m}"])) for m in ("BR", "ZMC8", "FW8", "CG8", "CG(conv)")]
                    + [fmt(100 * r[f"gap_{m}"], 3) for m in ("BR", "ZMC8", "FW8", "CG8", "CG(conv)")])
    write_table("tab_e5.tex", ["City", "$N$", "$Z$", "$d_{\\rm eff}$", "BR", "ZMC", "FW", "CG8", "CG",
                               "BR", "ZMC", "FW", "CG8", "CG"], rows, "lrrr|rrrrr|rrrrr")
    tol = 1e-3
    br_ok = d[d.gap_BR <= d.gap_ZMC8 + tol]
    macro("EfiveBRasgoodN", str(len(br_ok)))
    macro("EfiveBRasgoodCities", ", ".join(NAME[c] for c in br_ok.city))
    worse = d[d.gap_BR > d.gap_ZMC8 + tol]
    macro("EfiveBRworseCities", ", ".join(NAME[c] for c in worse.city))
    zmc_best = d[d.gap_ZMC8 < d[["gap_FW8", "gap_CG8", "gap_BR"]].min(axis=1) - tol]
    macro("EfiveZMCstrictBestN", str(len(zmc_best)))
    macro("EfiveCallsBRmin", str(int(d.calls_BR.min())))
    macro("EfiveCallsBRmax", str(int(d.calls_BR.max())))
    macro("EfiveCallsZMCmin", str(int(d.calls_ZMC8.min())))
    macro("EfiveCallsZMCmax", str(int(d.calls_ZMC8.max())))
    macro("EfiveCallsCGmin", str(int(d["calls_CG(conv)"].min())))
    macro("EfiveCallsCGmax", str(int(d["calls_CG(conv)"].max())))
    macro("EfiveDeffMin", str(int(d.d_eff.min())))
    macro("EfiveDeffMax", str(int(d.d_eff.max())))
    macro("EfiveSameN", str(int((abs(d.gap_ZMC8 - d.gap_FW8) <= 5e-4).sum())))


def t_tiny():
    d = read("summary_verify_tiny.csv")
    if d is None:
        return
    rows = []
    lab = {"ZMC6": "ZMC (6 rounds)", "BR": "BR", "FW6": "FW (6 rounds)", "CG": "CG"}
    for _, r in d.iterrows():
        rows.append([lab.get(r.method, r.method), str(int(r.instances)), fmt(r.mean_calls, 3), fmt(r.is_ne_enum, 3),
                     fmt(r.max_regret_fresh), fmt(r.hits_global, 3), fmt(r.mean_excess_over_global, 2)])
    write_table("tab_tiny.tex", ["Method", "games", "calls", "is NE", "max regret", "global min.", "excess"],
                rows, "lrrrrrr")
    z = d.set_index("method")
    macro("TinyN", str(int(z.loc["ZMC6", "instances"])))
    macro("TinyZMCglobal", str(int(round(z.loc["ZMC6", "hits_global"] * z.loc["ZMC6", "instances"]))))
    macro("TinyBRglobal", str(int(round(z.loc["BR", "hits_global"] * z.loc["BR", "instances"]))))
    macro("TinyFWglobal", str(int(round(z.loc["FW6", "hits_global"] * z.loc["FW6", "instances"]))))
    macro("TinyCGglobal", str(int(round(z.loc["CG", "hits_global"] * z.loc["CG", "instances"]))))


def t_e6():
    d = read("summary_E6.csv")
    if d is None:
        return
    d = order(d)
    rows = [[NAME[r.city], fmt(r.max_abs_identity_resid), fmt(r.thm2_bound_holds_frac, 3), str(int(r.inverted_brackets_max)),
             str(int(r.n_act)), fmt(r.width_after_8, 3), fmt(r.frac_within_T8, 3), fmt(r.err_max_T8, 3), fmt(r.bound_T8, 3)]
            for _, r in d.iterrows()]
    write_table("tab_e6.tex", ["City", "identity resid.", "bound holds", "inverted", "active", "width$_8$",
                               "within$_8$", "err$_8$", "bound$_8$"], rows, "lrrrrrrrr")
    macro("EsixResid", fmt(d.max_abs_identity_resid.max()))
    macro("EsixBoundMin", fmt(d.thm2_bound_holds_frac.min(), 3))


# ---------------------------------------------------------------- algorithm prototypes (theory/)
def t_brl():
    B = ROOT / "theory/new_algorithm_B"
    raw = json.loads((B / "results_raw.json").read_text())
    macro("BRLtestAerr", fmt(raw["testA"]["max_rel_err_formula_vs_LP"]))
    macro("BRLtestAn", str(raw["testA"]["trials"]))
    macro("BRLindepMean", fmt(100 * raw["testA"]["mean_rel_excess_over_independent_coupling"], 2))
    macro("BRLindepMax", fmt(100 * raw["testA"]["max_rel_excess_over_independent_coupling"], 3))
    F = raw["testF"]
    macro("BRLfixeduSub", str(sum(1 for x in F if x["best_fixed_u_solution_gap_pct"] > 1e-9)))
    macro("BRLfixeduN", str(len(F)))
    macro("BRLfixeduMax", fmt(max(x["best_fixed_u_solution_gap_pct"] for x in F), 3))
    real = json.loads((B / "results_realC.json").read_text())
    macro("BRLrealCn", str(len(real)))
    macro("BRLrealCmatch", str(int(sum(x["match"] for x in real))))
    macro("BRLtestCn", str(raw["testC"]["trials"]))
    # Test D: pricing times
    rows = [json.loads(l) for l in (B / "results_D.jsonl").read_text().splitlines() if l.strip()]
    seen, tab = set(), []
    for r in rows:
        k = (r["n"], r["rep"])
        if k in seen:
            continue
        seen.add(k)

        def c(m):
            x = r[m]
            return "TO" if x["timeout"] else f"{fmt(x['time'], 2)} ({x['kept']})"
        tab.append([str(r["n"]), c("deterministic_mean"), "\\textbf{" + c("functional") + "}", c("tau"), c("pointwise"), c("scenario")])
    write_table("tab_brl_pricing.tex", ["$n$", "risk-neutral", "BRL", "sector ($K$)", "quantile ($L$)", "SAA scenarios"],
                tab, "rrrrrr")
    ft = [r["functional"]["time"] for r in rows]
    macro("BRLtimeMin", fmt(min(ft), 1))
    macro("BRLtimeMax", fmt(max(ft), 2))
    hd = json.loads((B / "results_D_highdual.json").read_text())
    top = max(hd, key=lambda r: r["n"])
    macro("BRLhdN", str(top["n"]))
    macro("BRLhdTime", fmt(top["functional"][0], 2))
    macro("BRLhdDetTO", "timed out" if top["deterministic_mean"][2] else f"took {fmt(top['deterministic_mean'][0], 2)} s")
    macro("BRLhdScale", fmt(hd[0]["dual_scale"], 2))
    # Test E: metro instances
    E = json.loads((B / "results_E.json").read_text())
    rows, better, worse, equal = [], [], [], []
    for e in sorted(E, key=lambda e: ORDER.index(e["city"]) if e["city"] in ORDER else 99):
        cg = e["cg"]
        h = {k: e[f"{k}_eval"]["pbox"] for k in ("pbox", "saa", "wass")}
        best_h = min(h.values())
        ub = cg["ub"]
        rel = 100 * (ub / best_h - 1)
        (better if rel < -0.05 else worse if rel > 0.05 else equal).append((NAME[e["city"]], rel))
        rows.append([NAME[e["city"]] + ("$^*$" if e.get("congestion_imputed") else ""), str(cg["iters"]), str(cg["cols"]),
                     fmt(cg["time"], 3), fmt(cg["lp_bound"], 4), fmt(ub, 4), fmt(100 * (ub - cg["lp_bound"]) / ub, 2),
                     fmt(h["pbox"], 4), fmt(h["saa"], 4), fmt(h["wass"], 4)])
    write_table("tab_brl_metro.tex", ["City", "iter.", "cols", "time s", "LP bound", "P\\&B plan", "gap \\%",
                                      "heur.\\ p-box", "heur.\\ SAA", "heur.\\ Wass."], rows, "lrrrrrrrrr")
    macro("BRLbetterCities", ", ".join(f"{c} ({fmt(r, 2)}\\%)" for c, r in better))
    macro("BRLworseCities", ", ".join(f"{c} (+{fmt(r, 2)}\\%)" for c, r in worse))
    macro("BRLequalN", str(len(equal)))
    macro("BRLcgTimeMin", fmt(min(e["cg"]["time"] for e in E), 2))
    macro("BRLcgTimeMax", fmt(max(e["cg"]["time"] for e in E), 3))
    gaps = [100 * (e["cg"]["ub"] - e["cg"]["lp_bound"]) / e["cg"]["ub"] for e in E]
    macro("BRLgapMin", fmt(min(gaps), 2))
    macro("BRLgapMax", fmt(max(gaps), 2))
    cons = [100 * (e["brl_cg_eval"]["pbox"] / e["brl_cg_eval"]["true"] - 1) for e in E]
    macro("BRLconsMin", fmt(min(cons), 2))
    macro("BRLconsMax", fmt(max(cons), 2))


def t_zmc_synth():
    A = json.loads((ROOT / "theory/new_algorithm_A/results.json").read_text())
    df = pd.DataFrame([{"N": r["N"], "Z": r["Z"], "seed": r["seed"],
                        **{f"{m}_calls": r[m]["calls"] for m in ("BR", "BRms", "FW", "CG", "ZMC", "CGfull")},
                        **{f"{m}_gap": r[m]["gap"] for m in ("BR", "BRms", "FW", "CG", "ZMC", "CGfull")}} for r in A["E2"]])
    rows, wins = [], 0
    for (n, z), g in df.groupby(["N", "Z"]):
        row = [str(n), str(z)]
        for m in ("BR", "BRms", "FW", "CG", "ZMC", "CGfull"):
            row.append(f"{g[m + '_calls'].mean():.0f} / {fmt(g[m + '_gap'].mean(), 3)}")
        w = int((g.ZMC_gap <= g[["FW_gap", "CG_gap", "BRms_gap"]].min(axis=1) + 1e-12).sum())
        wins += w
        row.append(f"{w}/{len(g)}")
        rows.append(row)
    write_table("tab_zmc_synth.tex", ["$N$", "$Z$", "BR", "BR multi-start", "FW8", "CG8", "ZMC", "CG full", "ZMC best"],
                rows, "rrrrrrrrr")
    macro("ZMCsynthWins", str(wins))
    macro("ZMCsynthN", str(len(df)))


# ---------------------------------------------------------------- branch-and-price (BRL integer step)
def pct(v, sig=2):
    s = fmt(v, sig)
    return ("+" + s if v > 0 else s) + "\\%"


def t_bp():
    b = read("summary_bp.csv")
    if b is not None:
        b = order(b)
        rows = []
        for _, r in b.iterrows():
            rows.append([NAME[r.city] + ("$^*$" if r.city == "Moscow" else ""), fmt(r.root_lp, 4), fmt(r.published_price_and_branch, 4),
                         fmt(r.branch_and_price, 4), fmt(r.gap_rel_pct, 2), str(int(r.nodes)), fmt(r.time_s, 3),
                         fmt(r.bp_vs_best_heur_pbox_pct, 2), fmt(r.bp_vs_saa_true_pct, 2)])
        write_table("tab_brl_metro.tex", ["City", "root LP", "P\\&B plan", "B\\&P optimum", "gap \\%", "nodes", "time s",
                                          "vs best heur.\\ \\%", "vs SAA, true law \\%"], rows, "lrrrrrrrr")
        macro("BPoptimalN", str(int((b.status == "optimal").sum())))
        macro("BPtimeMaxMin", fmt(b.time_s.max() / 60, 2))
        macro("BPtimeMaxCity", NAME[b.loc[b.time_s.idxmax(), "city"]])
        macro("BPpricingShare", fmt(100 * b.pricing_time_s.sum() / b.time_s.sum(), 2))
        macro("BPnodesMax", str(int(b.nodes.max())))
        better = b[b.bp_vs_best_heur_pbox_pct < -1e-6]
        equal = b[b.bp_vs_best_heur_pbox_pct.abs() <= 1e-6]
        macro("BPbetterCities", ", ".join(f"{NAME[r.city]} ({fmt(r.bp_vs_best_heur_pbox_pct, 2)}\\%)" for _, r in better.iterrows()))
        macro("BPequalCities", ", ".join(NAME[c] for c in equal.city))
        worse_true = b[b.bp_vs_saa_true_pct > 0.5]
        macro("BPtrueWorse", ", ".join(f"{NAME[r.city]} ({pct(r.bp_vs_saa_true_pct)})" for _, r in worse_true.iterrows()))
        macro("BPpbGapMax", fmt(b.pb_gap_to_bp_pct.max(), 2))
        macro("BPconsMin", fmt(b.pbox_to_true_pct.min(), 2))
        macro("BPconsMax", fmt(b.pbox_to_true_pct.max(), 2))
        lo = b[b.city == "London"].iloc[0]
        macro("BPLondonSame", "yes" if bool(lo.same_plan_as_saa) else "no")
    v = read("summary_bp_verify.csv")
    if v is not None:
        a = v[v.kind == "all"].iloc[0]
        macro("BPverN", str(int(a.instances)))
        macro("BPverExact", str(int(a.bp_exact)))
        macro("BPverPBsub", str(int(a.pb_suboptimal)))
        macro("BPverPBmax", fmt(a.max_pb_gap_pct, 2))
        macro("BPverNodesMax", str(int(a.max_nodes)))
    g = read("summary_bp_game.csv")
    if g is not None:
        g = g.set_index("city")
        for c in g.index:
            macro(f"BPgame{c}W", pct(g.loc[c, "welfare_change_pct"]))
            macro(f"BPgame{c}Ratio", fmt(g.loc[c, "runtime_ratio"], 2))
        macro("BPgameCities", ", ".join(NAME[c] for c in ORDER if c in g.index))


# ---------------------------------------------------------------- theory-to-experiment checks
def t_theory():
    import glob as _g
    s = read("theory_absorption_summary.csv")
    st = read("summary_theory.csv")
    if s is None or st is None:
        return
    m = s[s.anchor != "pure"]
    ma = m[m.w_mode == "agg"]
    macro("ThGamesMixed", str(int(st.seeds_with_mixed_anchor.sum())))
    macro("ThGamesTotal", str(int(st.n_seeds.sum())))
    macro("ThNoMixedCities", ", ".join(NAME[c] for c in st[st.seeds_with_mixed_anchor == 0].city))
    macro("ThAnchors", str(len(ma)))
    macro("ThProfiles", str(int(m.n_measured.sum())))
    macro("ThProfilesAgg", str(int(ma.n_measured.sum())))
    vio = int(s[[c for c in s.columns if c.startswith("viol")]].sum().sum())
    macro("ThViol", str(vio))
    macro("ThRatioMin", fmt(ma.ratio_Emax_over_bound.min(), 2))
    macro("ThRatioMax", fmt(ma.ratio_Emax_over_bound.max(), 2))
    macro("ThRatioMed", fmt(ma.ratio_Emax_over_bound.median(), 2))
    macro("ThRatioNMin", fmt(ma.ratio_Emax_over_boundN.min(), 2))
    macro("ThRatioNMax", fmt(ma.ratio_Emax_over_boundN.max(), 2))
    macro("ThHatMax", fmt(ma.ratio_E_over_hat_max.max(), 2))
    t1 = (ma.bound_anchor >= ma.T1 - 1e-12) if "T1" in ma.columns else None
    macro("ThZmcFinite", str(int(st.zmc_start_n_finite_E.sum())))
    macro("ThZmcN", str(int(st.zmc_start_n.sum())))
    rows = []
    for c in ORDER:
        z = st[st.city == c]
        if not len(z):
            continue
        r = z.iloc[0]
        has = r.seeds_with_mixed_anchor > 0
        rows.append([NAME[c], f"{int(r.seeds_with_mixed_anchor)}/{int(r.n_seeds)}",
                     fmt(r.agg_rho_bar, 2) if has else "--", fmt(r.agg_bound_anchor, 3) if has else "--",
                     fmt(r.agg_bound_N, 3) if has else "--", fmt(r.agg_E_max, 2) if has else "--",
                     fmt(r.agg_ratio_Emax_over_bound, 2) if has else "--",
                     fmt(r["gamma0.1_served_drop"], 2), fmt(r["gamma1.0_served_drop"], 2), fmt(r["gamma1.0_Mthr_over_delta"], 2)])
    write_table("tab_theory.tex", ["City", "mixed", "$\\bar\\rho$", "anchored bd.", "$N$-unif.\\ bd.", "max $\\delta_E$",
                                   "ratio", "drop $\\delta{=}0.1$", "drop $\\delta{=}1$", "M-thr./$\\delta$"], rows, "lrrrrrrrrr")
    macro("ThGamDropLoMin", fmt(st["gamma0.1_served_drop"].min(), 1))
    macro("ThGamDropLoMax", fmt(st["gamma0.1_served_drop"].max(), 2))
    macro("ThGamDropHiMin", fmt(st["gamma1.0_served_drop"].min(), 2))
    macro("ThGamDropHiMax", fmt(st["gamma1.0_served_drop"].max(), 2))
    macro("ThGamMthrMin", fmt(st["gamma1.0_Mthr_over_delta"].min(), 2))
    macro("ThGamMthrMax", fmt(st["gamma1.0_Mthr_over_delta"].max(), 2))
    gfs = [f for f in _g.glob(str(RES / "theory_gamma_*.csv"))]
    if gfs:
        g = pd.concat([pd.read_csv(f) for f in gfs], ignore_index=True)
        macro("ThGamCases", str(len(g)))
        macro("ThGamDiff", str(int((~g.same_profile.astype(str).str.lower().eq("true")).sum())))
        macro("ThGamNotAdm", str(int((g.gamma_adm_NE_frac < 1).sum())))
        r = (g.M_thr_G / g.delta).replace([np.inf], np.nan)
        macro("ThGamMthrAllMax", fmt(r.max(), 3))
        macro("ThGamInf", str(int(np.isinf(g.M_thr_G).sum())))
    p71 = read("theory_D2_prop71.csv")
    if p71 is not None:
        macro("ThPropOK", f"{int(p71.ok.sum())} of {len(p71)}")
    k = read("theory_D2_kernels.csv")
    if k is not None:
        macro("ThKernOK", f"{int((k.ok_sets & k.ok_existence).sum())} of {len(k)}")
    r = read("theory_D2_random_explicit.csv")
    if r is not None:
        d2, d1 = r[r.regime == "D2"], r[r.regime == "D1"]
        macro("ThRandDtwo", f"{int(d2.no_pne.sum())} of {len(d2)}")
        macro("ThRandDone", f"{int(d1.no_pne.sum())} of {len(d1)}")
    t = read("theory_D2_tiny.csv")
    if t is not None:
        macro("ThTiny", f"{int(t.no_pne_D2.sum())} of {len(t)}")
    cfs = _g.glob(str(RES / "theory_D2_*_s*.csv"))
    if cfs:
        c = pd.concat([pd.read_csv(f) for f in cfs], ignore_index=True)
        c = c[c.kind == "summary"]
        macro("ThCityRuns", str(int(c.n_starts.sum())))
        macro("ThCityConv", str(int(c.n_converged.sum())))
        macro("ThCityCycles", str(int(c.n_cycle.sum())))
        macro("ThCityScales", ", ".join(fmt(x, 1) for x in sorted(c.scale.unique())))


# ---------------------------------------------------------------- exact-oracle re-run: coverage, call statistics, old vs new
FULL_E2 = 63


def t_exact():
    import glob as _g
    d = read("summary_exact_oracle.csv")
    if d is None:
        return
    tot = d[["bp_calls", "bp_optimal", "bp_retried", "bp_unproven"]].sum()
    macro("ExCalls", f"{int(tot.bp_calls):,}".replace(",", "{,}"))
    macro("ExOptimal", f"{int(tot.bp_optimal):,}".replace(",", "{,}"))
    macro("ExProvenPct", f"{100 * tot.bp_optimal / tot.bp_calls:.2f}")
    macro("ExRetried", str(int(tot.bp_retried)))
    macro("ExUnproven", str(int(tot.bp_unproven)))
    macro("ExMaxGap", fmt(d.bp_max_gap.max(), 2))
    macro("ExRegretFreshMax", fmt(d.max_regret_fresh.max()))
    nz = d[d.max_regret_lp_bound > 1e-9]
    macro("ExBoundN", str(len(nz)))
    macro("ExBoundMax", fmt(nz.max_regret_lp_bound.max(), 3) if len(nz) else "0")
    # coverage
    e1 = d[d.experiment == "E1"]
    macro("ExEoneN", str(len(e1)))
    e2 = d[d.experiment == "E2"]
    macro("ExEtwoN", str(len(e2)))
    g = e2.groupby("city").rows_exact
    full = [c for c in ORDER if c in g.groups and (g.get_group(c) >= FULL_E2).all()]
    red = [c for c in ORDER if c in g.groups and c not in full]
    macro("ExEtwoFullCities", ", ".join(NAME[c] for c in full))
    macro("ExEtwoRedCities", ", ".join(NAME[c] for c in red))
    rr = e2[e2.city.isin(red)].rows_exact
    macro("ExEtwoRedMin", str(int(rr.min())) if len(rr) else "--")
    macro("ExEtwoRedMax", str(int(rr.max())) if len(rr) else "--")
    e3 = read("summary_E3.csv")
    if e3 is not None:
        macro("ExEthreeN", str(len(e3)))
        have = set(zip(e3.city, e3.seed))
        miss = [f"{NAME[c]} seed {s}" for c in ORDER for s in range(3) if (c, s) not in have]
        macro("ExEthreeMissing", ", ".join(miss) if miss else "none")
        macro("ExEthreeMissingClause", f" (missing: {', '.join(miss)})" if miss else "")
    e4 = d[d.experiment == "E4"]
    macro("ExEfourN", str(len(e4)))
    g4 = e4.groupby("city").rows_exact
    full4 = [c for c in ORDER if c in g4.groups and (g4.get_group(c) >= 12).all()]
    red4 = [c for c in ORDER if c in g4.groups and c not in full4]
    macro("ExEfourFullCities", ", ".join(NAME[c] for c in full4))
    macro("ExEfourRedCities", ", ".join(NAME[c] for c in red4))
    macro("ExEfourRedWidths", str(int(e4[e4.city.isin(red4)].rows_exact.max())) if red4 else "--")
    have4 = set(zip(e4.city, e4.seed))
    miss4 = [f"{NAME[c]} seed {s}" for c in ORDER for s in range(3) if (c, s) not in have4]
    macro("ExEfourMissing", ", ".join(miss4) if miss4 else "none")
    macro("ExEfourMissingClause", f" (missing: {', '.join(miss4)})" if miss4 else "")
    macro("ExTotalDone", str(len(e1) + len(e2) + (len(e3) if e3 is not None else 0) + len(e4)))
    # coverage table
    rows = []
    for c in ORDER:
        row = [NAME[c]]
        for s in range(3):
            def has(exp):
                z = d[(d.experiment == exp) & (d.city == c) & (d.seed == s)]
                return z
            a = "E1" if len(has("E1")) else "--"
            b2 = has("E2")
            b = f"{int(b2.rows_exact.iloc[0])}/63" if len(b2) else "--"
            t3 = "yes" if e3 is not None and ((e3.city == c) & (e3.seed == s)).any() else "--"
            b4 = has("E4")
            f4 = f"{int(b4.rows_exact.iloc[0])}/12" if len(b4) else "--"
            row += [b, t3, f4]
        rows.append(row)
    write_table("tab_coverage.tex", ["City"] + [f"{h} s{s}" for s in range(3) for h in ("E2", "E3", "E4")], rows,
                "l" + "rrr" * 3)
    # old (price-and-branch) equilibria under the exact oracle
    fs = sorted(_g.glob(str(RES / "exact_parts" / "oldreg_*.csv")))
    if fs:
        o = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
        bad = o[o.regret_exact_max > 1e-6]
        macro("ExOldN", str(len(o)))
        macro("ExOldBadN", str(len(bad)))
        macro("ExOldBadMax", fmt(bad.regret_exact_max.max(), 2) if len(bad) else "0")
        ok_c = [c for c in ORDER if c in set(o.city) and (o[o.city == c].regret_exact_max <= 1e-6).all()]
        macro("ExOldExactCities", ", ".join(NAME[c] for c in ok_c))
        parts = []
        for c in ORDER:
            z = o[o.city == c]
            b = z[z.regret_exact_max > 1e-6]
            if len(b):
                parts.append(f"{NAME[c]} ({len(b)} of {len(z)} seeds, up to {fmt(b.regret_exact_max.max(), 2)} USD)")
        macro("ExOldBadList", "; ".join(parts))
    # old vs new
    c = read("exact_vs_pb_comparison_by_seed.csv")
    if c is not None:
        def get(city, seed, col):
            z = c[(c.city == city) & (c.seed == seed)]
            return z[col].iloc[0] if len(z) else np.nan
        macro("ExBAPoAold", fmt(get("BuenosAires", 0, "E3_PoA_zmc_old"), 4))
        macro("ExBAPoAnew", fmt(get("BuenosAires", 0, "E3_PoA_zmc_new"), 4))
        macro("ExBerlinPoAold", fmt(get("Berlin", 0, "E3_PoA_zmc_old"), 4))
        macro("ExBerlinPoAnew", fmt(get("Berlin", 0, "E3_PoA_zmc_new"), 4))
        macro("ExBACongOld", fmt(get("BuenosAires", 0, "E2_gain_congestion_only_pct_old"), 3))
        macro("ExBACongNew", fmt(get("BuenosAires", 0, "E2_gain_congestion_only_pct_new"), 2))
        macro("ExDelhiShareOld", fmt(get("NewDelhi", 0, "E2_share_delivery_alone_old"), 2))
        macro("ExDelhiShareNew", fmt(get("NewDelhi", 0, "E2_share_delivery_alone_new"), 2))
        macro("ExMumbaiShareOld", fmt(get("Bombay", 0, "E2_share_delivery_alone_old"), 1))
        macro("ExMumbaiShareNew", fmt(get("Bombay", 0, "E2_share_delivery_alone_new"), 2))
        macro("ExBAWOld", fmt(get("BuenosAires", 0, "E1_welfare_old"), 4))
        macro("ExBAWNew", fmt(get("BuenosAires", 0, "E1_welfare_new"), 4))
        ws = c.dropna(subset=["E1_welfare_new"])
        dw = 100 * (ws.E1_welfare_new / ws.E1_welfare_old - 1)
        macro("ExEoneWChangeMaxNotBA", fmt(dw[ws.city != "BuenosAires"].abs().max(), 2))
        macro("ExEoneWChangeBA", fmt(dw[ws.city == "BuenosAires"].min(), 2))
        e4c = c.dropna(subset=["E4_pbox_widest_d_deliveries_pct_new"])
        ch = (e4c.E4_pbox_widest_d_deliveries_pct_new - e4c.E4_pbox_widest_d_deliveries_pct_old).abs()
        macro("ExEfourSeedChangeMax", fmt(ch.max(), 2))
    cm = read("exact_vs_pb_comparison.csv")
    if cm is not None:
        ch = pd.concat([(cm[f"E4_{k}_new"] - cm[f"E4_{k}_old"]).abs() for k in
                        ("pbox_widest_d_deliveries_pct", "pbox_widest_d_welfare_pct", "gamma_widest_d_deliveries_pct",
                         "gamma_widest_d_welfare_pct")])
        macro("ExEfourMeanChangeMax", fmt(ch.max(), 2))
        dp = (cm.E3_PoA_zmc_new - cm.E3_PoA_zmc_old).abs()
        macro("ExPoAMeanChangeMax", fmt(dp.max(), 2))
        dwm = 100 * (cm.E1_welfare_new / cm.E1_welfare_old - 1)
        macro("ExEoneWMeanMaxNotBA", fmt(dwm[cm.city != "BuenosAires"].abs().max(), 2))
        macro("ExEoneWMeanBA", fmt(dwm[cm.city == "BuenosAires"].iloc[0], 2))


# ---------------------------------------------------------------- dual implementation pricing (leader)
def t_dip():
    d = read("summary_dip.csv")
    if d is None:
        return
    d = d.copy()
    d["full"] = (d.grid_points >= 63) & (d.grid_oracle == "exact")
    # summary_dip stores welfare ratios W/W_SO; the price of anarchy is the inverse
    d["PoA_grid"] = 1.0 / d.poa_grid
    d["PoA_dip"] = 1.0 / d.poa_dip
    rows = []
    for c in ORDER:
        z = d[d.city == c].sort_values("seed")
        if not len(z):
            continue
        gp = " / ".join(("63" if r.grid_points >= 63 else str(int(r.grid_points))) + ("$^{\\rm pb}$" if r.grid_oracle != "exact" else "")
                        for _, r in z.iterrows())
        gs = " / ".join(fmt(v, 3) if pd.notna(v) else "n/a" for v in z.dip_gain_share)
        cs = " / ".join(fmt(100 * v, 2) for v in z.dip_calls_share)
        c63 = " / ".join(fmt(100 * v, 2) for v in z.dip_calls_share_63)
        rd = " / ".join(str(int(v)) for v in z.dip_rounds)
        ex = f"{int((z.dip_status == 'exact').sum())}/{len(z)}"
        rows.append([NAME[c], gp, gs, cs, c63, rd, ex, byseed(z.PoA_grid, 3), byseed(z.PoA_dip, 3)])
    write_table("tab_dip.tex", ["City", "grid pts", "gain share", "calls \\% (grid run)", "calls \\% (63 pts)", "rounds",
                                "exact", "PoA grid", "PoA DIP"], rows, "lrrrrrrrr")
    macro("DipRuns", str(len(d)))
    pb = d[d.grid_oracle != "exact"]
    macro("DipPbCases", ", ".join(f"{NAME[r.city]} seed {int(r.seed)}" for _, r in pb.iterrows()) or "none")
    macro("DipPbN", str(len(pb)))
    f = d[d.full]
    macro("DipFullN", str(len(f)))
    macro("DipFullCities", ", ".join(NAME[c] for c in ORDER if c in set(f.city)))
    macro("DipFullGainMin", fmt(100 * f.dip_gain_share.min(), 3))
    macro("DipFullGainMax", fmt(100 * f.dip_gain_share.max(), 3))
    macro("DipFullGainMean", fmt(100 * f.dip_gain_share.mean(), 3))
    macro("DipFullCallsMin", fmt(100 * f.dip_calls_share.min(), 2))
    macro("DipFullCallsMax", fmt(100 * f.dip_calls_share.max(), 2))
    macro("DipFullCallsMean", fmt(100 * f.dip_calls_share.mean(), 2))
    macro("DipFullPoAgridMin", fmt(f.PoA_grid.min(), 3))
    macro("DipFullPoAgridMax", fmt(f.PoA_grid.max(), 3))
    g = d.dip_gain_share.dropna()
    macro("DipGainMinAll", fmt(g.min(), 3))
    macro("DipNoGainCities", ", ".join(NAME[c] for c in ORDER if c in set(d.city) and d[d.city == c].dip_gain_share.isna().all()))
    macro("DipCallsSixtyThreeMax", fmt(100 * d.dip_calls_share_63.max(), 2))
    macro("DipCallsMin", str(int(d.dip_calls.min())))
    macro("DipCallsMax", str(int(d.dip_calls.max())))
    red = d[~d.full & (d.grid_oracle == "exact")]
    parts = []
    for c in ORDER:
        z = red[red.city == c]
        if len(z):
            lo, hi = 100 * z.dip_calls_share.min(), 100 * z.dip_calls_share.max()
            parts.append(f"{NAME[c]} {fmt(lo, 2)}" + (f"--{fmt(hi, 2)}" if hi - lo > 0.5 else "") + "\\%")
    macro("DipRedCalls", ", ".join(parts))
    macro("DipExactN", str(int((d.dip_status == "exact").sum())))
    macro("DipTangentN", str(int((d.dip_rounds == 1).sum())))
    macro("DipRoundsMax", str(int(d.dip_rounds.max())))
    macro("DipCutsMax", str(int(d.dip_n_cuts.max())))
    macro("DipRegretMax", fmt(d.verify_max_regret_fresh.max()))
    macro("DipPoAmin", f"{d.PoA_dip.min():.3f}")
    macro("DipPoAmax", f"{d.PoA_dip.max():.3f}")
    ts = d.dip_time_share.dropna()
    macro("DipTimeMed", fmt(ts.median(), 2))
    macro("DipTimeSlowN", str(int((ts > 1).sum())))
    lo = d[(d.city == "London") & (d.seed == 0)]
    if len(lo):
        macro("DipLondonTime", fmt(lo.dip_time_s.iloc[0], 3))
        macro("DipLondonGridTime", fmt(lo.grid_time_s.iloc[0], 3))
    fam = d.fam_gain_share.dropna()
    macro("DipFamMean", fmt(fam.mean(), 2))
    macro("DipFamMin", fmt(fam.min(), 2))
    i = d.fam_gain_share.idxmin()
    macro("DipFamMinCase", f"{NAME[d.loc[i, 'city']]}, seed {int(d.loc[i, 'seed'])}")
    macro("DipSelSame", str(int(d.sel_same.astype(str).str.lower().eq("true").sum())))
    macro("DipSelMin", fmt(d.sel_gain_share.dropna().min(), 3))
    macro("DipSubsMin", fmt(-d.dip_s_over_fee.max(), 2))
    macro("DipSubsMax", fmt(-d.dip_s_over_fee.min(), 2))
    cr = pd.concat([d["credal0.2_regret"], d["credal0.8_regret"]])
    macro("DipCredalRegret", fmt(cr.max()))
    macro("DipCredalSubMin", fmt(-d["credal0.8_s_over_fee"].max(), 2))
    macro("DipCredalSubMax", fmt(-d["credal0.8_s_over_fee"].min(), 2))
    t = read("dip_tiny.csv")
    if t is not None:
        macro("DipTinyN", str(len(t)))
        macro("DipTinyExact", str(int(t.dip_status.eq("exact").sum())))
        hit = (t.dip_sc <= t.opt_zone + 1e-6)
        macro("DipTinyHitPct", fmt(100 * hit.mean(), 2))
        hx = (t.dipx_sc <= t.opt_zone + 1e-6)
        macro("DipTinyHitXPct", fmt(100 * hx.mean(), 3))
        uniq = (t.dip_n_ne == 1)
        macro("DipTinyUniquePct", fmt(100 * uniq.mean(), 2))
        macro("DipTinyCallsMin", fmt(t.dip_calls.min(), 2))
        macro("DipTinyCallsMax", fmt(t.dip_calls.max(), 2))
        macro("DipTinyGridCallsMin", fmt(t.grid_calls.min(), 2))
        macro("DipTinyGridCallsMax", fmt(t.grid_calls.max(), 2))


def t_cert():
    fs = sorted(RES.glob("E2cert_*.csv"))
    if not fs:
        return
    d = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    macro("VerBestN", str(len(d)))
    macro("VerBestRegretMax", fmt(d.regret_fresh.max()))
    macro("VerBestRegretLPMax", fmt(d.regret_lp.max(), 2))


# ---------------------------------------------------------------- aggregate-response pricing (leader, observation only)
def t_arp():
    d = read("summary_arp.csv")
    if d is None:
        return
    d = d.copy()
    d["_o"] = d.city.map({c: i for i, c in enumerate(ORDER)})
    d = d.sort_values(["_o", "seed"]).drop(columns="_o")
    rows = []
    for _, r in d.iterrows():
        rows.append([NAME[r.city], str(int(r.seed)), fmt(r.rho, 2),
                     ("fixed point" if r.arp_status == "fixed_point" else "cycle") + f" / {int(r.arp_rounds)}",
                     fmt(100 * r.arp_gain_share, 3), str(int(r.arp_calls)),
                     fmt(100 * r.mct_br_gain_share, 3), str(int(r.mct_br_calls)),
                     fmt(100 * r.mct_so_gain_share, 3), str(int(r.mct_so_calls)),
                     fmt(100 * r.dip_gain_share, 3), str(int(r.dip_calls)), str(int(r.grid_calls))])
    write_table("tab_arp.tex", ["City", "seed", "$\\rho$", "ARP status / rounds", "ARP \\%", "calls", "tariff+BR \\%", "calls",
                                "tariff+SO \\%", "calls", "DIP \\%", "calls", "grid calls"], rows, "lrrlrrrrrrrrr")
    macro("ArpRuns", str(len(d)))
    macro("ArpCities", ", ".join(NAME[c] for c in ORDER if c in set(d.city)))
    macro("ArpNCities", str(d.city.nunique()))
    macro("ArpRhoMin", fmt(d.rho.min(), 2))
    macro("ArpRhoMax", fmt(d.rho.max(), 2))
    macro("ArpGainMin", fmt(100 * d.arp_gain_share.min(), 3))
    macro("ArpGainMax", fmt(100 * d.arp_gain_share.max(), 3))
    macro("ArpGainMean", fmt(100 * d.arp_gain_share.mean(), 3))
    macro("ArpCallsMin", str(int(d.arp_calls.min())))
    macro("ArpCallsMax", str(int(d.arp_calls.max())))
    macro("ArpRoundsMin", str(int(d.arp_rounds.min())))
    macro("ArpRoundsMax", str(int(d.arp_rounds.max())))
    fp = d[d.arp_status == "fixed_point"]
    macro("ArpFixedN", str(len(fp)))
    macro("ArpCycleN", str(int((d.arp_status != "fixed_point").sum())))
    macro("ArpFixedThreeRoundsN", str(int((fp.arp_rounds <= 3).sum())))
    tol = 0.02
    macro("ArpEqualsDipN", str(int((d.arp_gain_share >= d.dip_gain_share - tol).sum())))
    i = d.arp_gain_share.idxmin()
    macro("ArpMissCase", f"{NAME[d.loc[i, 'city']]} seed {int(d.loc[i, 'seed'])}")
    macro("ArpMissGain", fmt(100 * d.loc[i, "arp_gain_share"], 3))
    macro("ArpMissDip", fmt(100 * d.loc[i, "dip_gain_share"], 3))
    macro("ArpMissRho", fmt(d.loc[i, "rho"], 2))
    macro("MctGainMin", fmt(100 * d.mct_br_gain_share.min(), 3))
    macro("MctGainMax", fmt(100 * d.mct_br_gain_share.max(), 3))
    macro("MctGainMean", fmt(100 * d.mct_br_gain_share.mean(), 3))
    macro("MctCallsMin", str(int(d.mct_br_calls.min())))
    macro("MctCallsMax", str(int(d.mct_br_calls.max())))
    macro("MctMonotoneN", str(int(d.mct_br_monotone.astype(str).str.lower().eq("true").sum())))
    macro("MctEqualsDipN", str(int((d.mct_br_gain_share >= d.dip_gain_share - tol).sum())))
    macro("MctSoGainMin", fmt(100 * d.mct_so_gain_share.min(), 3))
    macro("MctSoGainMax", fmt(100 * d.mct_so_gain_share.max(), 3))
    macro("MctSoGainMean", fmt(100 * d.mct_so_gain_share.mean(), 3))
    macro("MctSoCallsMin", str(int(d.mct_so_calls.min())))
    macro("MctSoCallsMax", str(int(d.mct_so_calls.max())))
    macro("MctSoEqualsDipN", str(int((d.mct_so_gain_share >= d.dip_gain_share - tol).sum())))
    macro("ArpDipGainMin", fmt(100 * d.dip_gain_share.min(), 3))
    macro("ArpDipGainMax", fmt(100 * d.dip_gain_share.max(), 3))
    macro("ArpDipGainMean", fmt(100 * d.dip_gain_share.mean(), 3))
    macro("ArpDipCallsMin", str(int(d.dip_calls.min())))
    macro("ArpDipCallsMax", str(int(d.dip_calls.max())))
    macro("ArpGridCallsMin", str(int(d.grid_calls.min())))
    macro("ArpGridCallsMax", str(int(d.grid_calls.max())))
    macro("ArpRegretMax", fmt(d.verify_arp_regret_fresh.max()))
    macro("MctRegretMax", fmt(max(d.verify_mct_br_regret.max(), d.verify_mct_so_regret.max())))
    macro("ArpTimeMin", fmt(d.arp_time_s.min(), 2))
    macro("ArpTimeMax", fmt(d.arp_time_s.max(), 2))
    macro("ArpTimeRatioMed", fmt((d.arp_time_s / d.dip_time_s).median(), 2))
    macro("ArpSubsMin", fmt(-d.arp_s_over_fee.max(), 2))
    macro("ArpSubsMax", fmt(-d.arp_s_over_fee.min(), 2))
    macro("ArpDipSubsMin", fmt(-d.dip_s_over_fee.max(), 2))
    macro("ArpDipSubsMax", fmt(-d.dip_s_over_fee.min(), 2))
    macro("ArpPoAMin", fmt(d.poa_arp.min(), 3))
    macro("ArpPoAMax", fmt(d.poa_arp.max(), 3))
    macro("ArpUnproven", str(int(d.arp_bp_unproven.sum())))
    msa = d.dropna(subset=["arp_msa_gain_share"])
    macro("ArpMsaN", str(len(msa)))
    macro("ArpMsaGainMin", fmt(100 * msa.arp_msa_gain_share.min(), 3) if len(msa) else "--")
    macro("ArpMsaGainMax", fmt(100 * msa.arp_msa_gain_share.max(), 3) if len(msa) else "--")
    # tiny games with exhaustive enumeration
    t = read("arp_tiny.csv")
    if t is not None:
        pos = t[t.opt_zone < t.sc_ne - 1e-9].copy()
        den = pos.sc_ne - pos.opt_zone
        macro("ArpTinyN", str(len(t)))
        macro("ArpTinyPosN", str(len(pos)))
        macro("ArpTinyFixedN", str(int((t.arp_plain_status == "fixed_point").sum())))
        macro("ArpTinyCycleN", str(int((t.arp_plain_status != "fixed_point").sum())))
        macro("ArpTinyRoundsMean", fmt(t.arp_plain_rounds.mean(), 2))
        macro("ArpTinyRoundsMax", str(int(t.arp_plain_rounds.max())))
        macro("MctTinyMonotoneN", str(int(t.mct_br_monotone.astype(str).str.lower().eq("true").sum())))
        macro("MctTinyBestIsSO", str(int((abs(t.mct_best_sc - t.sc_so) <= 1e-6).sum())))
        meths = [("arp_plain_sc", "arp_plain_calls", "ARP flat (plain)", "$(Q_z,n_z)$"),
                 ("arp_msa_sc", "arp_msa_calls", "ARP flat (successive averages)", "$(Q_z,n_z)$"),
                 ("arp_known_sc", "arp_known_calls", "ARP flat, lots known", "$(Q_z,n_z)$ + lots"),
                 ("mct_br_sc", "mct_br_calls", "tariff + carriers' best responses", "own $q$, $Q_z$"),
                 ("mct_so_sc", "mct_so_calls", "tariff + potential solver", "oracle"),
                 ("dip_sc", "dip_calls", "DIP", "oracle"),
                 ("grid_selected", "grid_calls", "grid", "oracle")]
        rows = []
        keys = {"arp_plain_sc": "ArpTiny", "mct_br_sc": "MctTiny", "mct_so_sc": "MctSoTiny", "dip_sc": "DipArpTiny",
                "grid_selected": "GridArpTiny", "arp_known_sc": "ArpKnownTiny", "arp_msa_sc": "ArpMsaTiny"}
        for sc, calls, lab, info in meths:
            sh = (pos.sc_ne - pos[sc]) / den
            hit = (pos[sc] <= pos.opt_zone + 1e-6).mean()
            worse = int((pos[sc] > pos.sc_ne + 1e-6).sum())
            rows.append([lab, info, fmt(sh.mean(), 2), fmt(100 * hit, 2), str(worse), fmt(pos[calls].mean(), 2)])
            k = keys[sc]
            macro(k + "Share", fmt(sh.mean(), 2))
            macro(k + "Hit", fmt(100 * hit, 2))
            macro(k + "Worse", str(worse))
            macro(k + "Calls", fmt(pos[calls].mean(), 2))
        write_table("tab_arp_tiny.tex", ["Method", "city's information", "mean share", "optimum hit \\%", "worse than unpriced", "calls"],
                    rows, "llrrrr")
        parts = []
        for g, x in pos.groupby("gcx"):
            parts.append(f"{fmt(((x.sc_ne - x.arp_plain_sc) / (x.sc_ne - x.opt_zone)).mean(), 2)}")
        macro("ArpTinyShareByCong", " / ".join(parts))
        parts = []
        for g, x in pos.groupby("gcx"):
            parts.append(f"{fmt(((x.sc_ne - x.mct_br_sc) / (x.sc_ne - x.opt_zone)).mean(), 2)}")
        macro("MctTinyShareByCong", " / ".join(parts))
        parts = []
        for g, x in pos.groupby("gcx"):
            parts.append(f"{fmt(((x.sc_ne - x.dip_sc) / (x.sc_ne - x.opt_zone)).mean(), 2)}")
        macro("DipTinyShareByCong", " / ".join(parts))
        macro("ArpTinyCongLevels", ", ".join(str(int(g)) for g in sorted(pos.gcx.unique())))
        macro("ArpTinyRhoMed", " / ".join(fmt(x.rho.median(), 2) for _, x in pos.groupby("gcx")))
    r = read("arp_rates.csv")
    if r is not None:
        macro("ArpRatesN", str(len(r)))
        macro("ArpRatesRhoMin", fmt(r.rho.min(), 2))
        macro("ArpRatesRhoMax", fmt(r.rho.max(), 2))
        macro("ArpRatesAllOK", "all" if bool(r[["ok_lip", "ok_T", "ok_plain", "ok_damped"]].all().all()) else "not all")
        macro("ArpRatesLipMax", fmt(r.lipschitz_max.max(), 2))
        macro("ArpRatesPlainMax", fmt((r.plain_step_ratio_max / r.rho).max(), 2))
        macro("ArpRatesTMax", fmt((r.T_ratio_max / r.rho).max(), 2))
        macro("ArpRatesDampedMax", fmt((r.damped_step_ratio_max / r.rho_damped).max(), 3))


def main():
    for f in (t_params, t_cities, t_e1, t_sens, t_e2, t_e3, t_e4, t_e5, t_tiny, t_e6, t_brl, t_zmc_synth, t_cert, t_bp, t_theory, t_exact, t_dip, t_arp):
        try:
            f()
        except Exception as exc:  # keep going so that one changed file does not block the rest
            print(f"warning: {f.__name__} failed: {exc!r}")
    lines = ["% generated by paper/make_tables.py; do not edit"]
    lines += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in sorted(MACROS.items())]
    (OUT / "macros.tex").write_text("\n".join(lines) + "\n")
    print(f"wrote {len(list(OUT.glob('*.tex')))} files, {len(MACROS)} macros")


if __name__ == "__main__":
    main()
