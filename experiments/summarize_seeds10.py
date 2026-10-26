"""Ten-seed summary: seeds 0-2 (earlier exact runs, results/*.csv) and seeds 3-9 (results/seeds10_parts/) in one table.

Writes
  results/seeds10_runs.csv           one row per city and seed: every per-run quantity (also summary_seeds10.csv, same content, sorted)
  results/seeds10_grid_points.csv    every exact grid point of seeds 3-9 (and of seeds 0-2: exact rows of E2)
  results/seeds10_oracle.csv         oracle calls, time and proof status per city, seed and stage (budget of the extension)
  results/summary_seeds10.csv        per city and seed (the 'runs' table)
  results/summary_seeds10_ci.csv     per city and quantity: n, mean, sd, bootstrap 95% CI of the mean over seeds, min, max, 3-seed mean/sd
  results/seeds10_conclusions.csv    the claims of the 3-seed analysis checked at ten seeds (stable / flipped / CI crosses the threshold)
Bootstrap: percentile interval of the mean, 10,000 resamples of the seeds (with replacement), generator seed 20261026.
Reduced grids: for the six cities without the full 63-point grid every grid quantity is a LOWER BOUND (best of an exact subset).
"""
import json

import numpy as np
import pandas as pd

from common import RES, zb

CITIES = zb.CITIES
OLD = (0, 1, 2)
PARTS = RES / "seeds10_parts"
FULL = ("NewDelhi", "BuenosAires", "London")
B_BOOT = 10000
RNG_SEED = 20261026
CONG_BOUND, SHARE_BOUND, POA_LARGE = 1.7, 0.5, 1.10
MIN_GAIN_PCT = 0.5  # shares are only meaningful where the two-instrument gain is at least this many percent of |SC|
MIN_SO_GAP_PCT = 0.5  # gain share vs the social optimum only where the unpriced equilibrium is at least this far (percent of |SC|) from it


def jload(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def rp(prefix, c, s):
    return RES / (f"{prefix}_{c}.csv" if s == 0 else f"{prefix}_{c}_s{s}.csv")


def grid_stats(rows: pd.DataFrame, sc0: float) -> dict:
    """best exact social cost per configuration (the leader may always choose 'none')"""
    out = {}
    for cfg in ("congestion_only", "delivery_only", "both"):
        c = rows[rows.config.isin([cfg, "none"])]
        b = c.loc[c.social_cost.idxmin()]
        out[f"sc_{cfg}"] = float(b.social_cost)
        out[f"theta_{cfg}"], out[f"sfrac_{cfg}"] = float(b.theta), float(b.sfrac)
        out[f"gain_{cfg}_pct"] = 100 * (sc0 - b.social_cost) / abs(sc0)
        out[f"served_{cfg}"] = float(b.served_share)
    b = rows.loc[rows.social_cost.idxmin()]
    out["sc_grid_best"] = float(b.social_cost)
    out["grid_best_theta"], out["grid_best_sfrac"] = float(b.theta), float(b.sfrac)
    nz = rows[rows.config != "none"]
    out["grid_points"] = int(len(rows))
    out["grid_calls_sum"] = float(rows.calls.sum())
    out["grid_calls_mean_pt"] = float(rows.calls.mean())
    out["grid_calls_nonbase_mean"] = float(nz.calls.mean()) if len(nz) else np.nan
    out["grid_bp_calls_sum"] = float(rows.bp_calls.fillna(0).sum()) if "bp_calls" in rows else np.nan
    out["grid_time_sum"] = float(rows.time_s.sum())
    out["grid_max_regret"] = float(rows.max_regret.max())
    out["grid_all_converged"] = bool(rows.converged.all())
    return out


def load_old(c, s):
    r = dict(city=c, seed=s, source="earlier_run")
    e1 = pd.read_csv(RES / "exact_parts" / f"E1_{c}_s{s}.csv").iloc[0]
    r.update(sc0=float(e1.social_cost), welfare0=float(e1.welfare), served_share0=float(e1.served_share), slowdown_pct0=100 * float(e1.mean_slowdown),
             e1_calls=float(e1.bp_calls), e1_time_s=float(e1.time_s), e1_regret_fresh=float(e1.max_regret), e1_unproven=float(e1.bp_unproven))
    e3 = pd.read_csv(rp("E3", c, s)).set_index("kind")
    r["sc_so_e3"] = float(e3.loc["SO_main"].social_cost)
    ne = e3[e3.index.str.startswith("NE_") & ~e3.index.str.contains("priced")]
    r["w_ne_zmc"], r["w_ne_best"], r["w_ne_worst"] = float(e3.loc["NE_zmc"].welfare), float(ne.welfare.max()), float(ne.welfare.min())
    r["n_ne_distinct"] = int(1 + ne.distinct.fillna(False).sum())
    r["sc_priced_e3"] = float(e3.loc["NE_priced_main"].social_cost)
    r["e3_calls"] = float(e3.calls.fillna(0).sum())
    e2 = pd.read_csv(rp("E2", c, s))
    ex = e2[e2.oracle.fillna("exact") == "exact"] if "oracle" in e2 else e2
    r.update(grid_stats(ex, r["sc0"]))
    r["grid_mode"] = "full" if len(ex) == 63 else "coarse"
    d = pd.read_csv(RES / "summary_dip.csv")
    d = d[(d.city == c) & (d.seed == s)].iloc[0]
    r.update(sc_dip=float(d.dip_sc), sc_dip_target=float(d.dip_sc_target), dip_calls=float(d.dip_calls), dip_time_s=float(d.dip_time_s),
             dip_status=d.dip_status, dip_regret_fresh=float(d.verify_max_regret_fresh), dip_s_over_fee=float(d.dip_s_over_fee),
             dip_served_share=float(d.dip_served_share), dip_first_sc_target=float(d.e3_so_sc))
    a = pd.read_csv(RES / "summary_arp.csv")
    a = a[(a.city == c) & (a.seed == s)]
    if len(a):
        a = a.iloc[0]
        r.update(sc_arp=float(a.arp_sc), arp_status=a.arp_status, arp_calls=float(a.arp_calls), sc_arp_msa=float(a.arp_msa_sc), arp_msa_calls=float(a.arp_msa_calls),
                 sc_mct_br=float(a.mct_br_sc), mct_br_calls=float(a.mct_br_calls), sc_mct_so=float(a.mct_so_sc), mct_so_calls=float(a.mct_so_calls),
                 arp_regret_fresh=float(a.verify_arp_regret_fresh))
    return r, ex.assign(city=c, seed=s)


def load_new(c, s):
    cp = jload(PARTS / f"core_{c}_s{s}.json")
    if not cp.get("done"):
        return None, None
    r = dict(city=c, seed=s, source="seeds10")
    e1 = cp["e1"]["row"]
    r.update(sc0=e1["social_cost"], welfare0=e1["welfare"], served_share0=e1["served_share"], slowdown_pct0=100 * e1["mean_slowdown"],
             e1_calls=e1.get("bp_calls", np.nan), e1_time_s=e1["time_s"], e1_regret_fresh=e1["max_regret"], e1_unproven=e1.get("bp_unproven", np.nan))
    D, ne = cp["dip"], cp["ne"]["rows"]
    r["sc_so_e3"] = D["first_sc_target"]
    w = {x["kind"]: x["welfare"] for x in ne}
    nes = [x for x in ne if x["kind"].startswith("NE_")]
    r["w_ne_zmc"], r["w_ne_best"], r["w_ne_worst"] = w["NE_zmc"], max(x["welfare"] for x in nes), min(x["welfare"] for x in nes)
    r["n_ne_distinct"] = int(sum(bool(x.get("distinct")) for x in nes) + 1)
    r["e3_calls"] = float(D["calls_so"] - D["calls_restarts"] + cp["ne"]["bp_calls"])
    r.update(sc_dip=D["sc"], sc_dip_target=D["sc_target"], dip_calls=D["calls"], dip_time_s=D["time_s"], dip_status=D["status"],
             dip_regret_fresh=cp["verify"]["max_regret_fresh"], dip_s_over_fee=D["s"] / cp["e1"]["fee"], dip_served_share=D["served_share"],
             dip_first_sc_target=D["first_sc_target"])
    gp = jload(PARTS / f"grid_{c}_s{s}.json")
    grid = None
    if gp.get("done"):
        g = pd.DataFrame(gp["rows"])
        g["oracle"] = "exact"
        r.update(grid_stats(g, r["sc0"]))
        r["grid_mode"] = gp["mode"]
        cert = gp["cert"]
        r["sc_priced_e3"] = cert["social_cost"]
        r["grid_cert_regret_fresh"] = cert["regret_fresh"]
        r["dip_proj_theta"], r["dip_proj_sfrac"] = gp.get("dip_proj_theta", np.nan), gp.get("dip_proj_sfrac", np.nan)
        grid = g.assign(city=c, seed=s)
    af = PARTS / f"arp_{c}_s{s}.csv"
    if af.exists():
        a = pd.read_csv(af).iloc[0]
        r.update(sc_arp=float(a.arp_sc), arp_status=a.arp_status, arp_calls=float(a.arp_calls), sc_arp_msa=float(a.arp_msa_sc), arp_msa_calls=float(a.arp_msa_calls),
                 sc_mct_br=float(a.mct_br_sc), mct_br_calls=float(a.mct_br_calls), sc_mct_so=float(a.mct_so_sc), mct_so_calls=float(a.mct_so_calls),
                 arp_regret_fresh=float(a.verify_arp_regret_fresh))
    return r, grid


def load_arp_extra(c, s, r):
    """ARP runs of seeds 0-2 for the cities that had none (written by run_seeds10.py arp)"""
    af = PARTS / f"arp_{c}_s{s}.csv"
    if "sc_arp" not in r and af.exists():
        a = pd.read_csv(af).iloc[0]
        r.update(sc_arp=float(a.arp_sc), arp_status=a.arp_status, arp_calls=float(a.arp_calls), sc_arp_msa=float(a.arp_msa_sc), arp_msa_calls=float(a.arp_msa_calls),
                 sc_mct_br=float(a.mct_br_sc), mct_br_calls=float(a.mct_br_calls), sc_mct_so=float(a.mct_so_sc), mct_so_calls=float(a.mct_so_calls),
                 arp_regret_fresh=float(a.verify_arp_regret_fresh))


def derive(r):
    """quantities derived from the raw per-run values"""
    sc0 = r["sc0"]
    so_e3 = r["sc_so_e3"]
    r["sc_so_best"] = min(so_e3, r["sc_dip_target"], r["sc_dip"])  # best social cost found (exact E3 solve, DIP multi-start target, DIP profile)
    r["poa_zmc"] = -so_e3 / r["w_ne_zmc"] if r["w_ne_zmc"] > 0 else np.nan
    r["pos"] = -so_e3 / r["w_ne_best"] if r["w_ne_best"] > 0 else np.nan
    r["poa_worst"] = -so_e3 / r["w_ne_worst"] if r["w_ne_worst"] > 0 else np.nan
    r["gap_unpriced_pct"] = 100 * (sc0 - so_e3) / abs(so_e3)  # (W_SO - W_NE)/W_SO in percent, E3 optimum
    r["so_gap_pct_of_abs"] = 100 * (sc0 - r["sc_so_best"]) / abs(sc0)
    if "sc_priced_e3" in r:
        r["priced_gap_pct"] = 100 * (r["sc_priced_e3"] - so_e3) / abs(so_e3)
        r["poa_priced"] = -so_e3 / -r["sc_priced_e3"] if r["sc_priced_e3"] < 0 else np.nan
    r["dip_priced_gap_pct"] = 100 * (r["sc_dip"] - so_e3) / abs(so_e3)
    r["dip_gain_pct"] = 100 * (sc0 - r["sc_dip"]) / abs(sc0)
    for k in ("arp", "arp_msa", "mct_br", "mct_so"):
        if f"sc_{k}" in r:
            r[f"{k}_gain_pct"] = 100 * (sc0 - r[f"sc_{k}"]) / abs(sc0)
    if "gain_both_pct" in r:
        r["share_delivery"] = r["gain_delivery_only_pct"] / r["gain_both_pct"] if r["gain_both_pct"] >= MIN_GAIN_PCT else np.nan
        r["share_delivery_raw"] = r["gain_delivery_only_pct"] / r["gain_both_pct"] if r["gain_both_pct"] > 1e-9 else np.nan
        r["grid_gain_pct"] = 100 * (sc0 - r["sc_grid_best"]) / abs(sc0)
        gg = r["grid_gain_pct"]
        r["dip_vs_grid_gain"] = r["dip_gain_pct"] / gg if gg >= MIN_GAIN_PCT else np.nan  # DIP gain / best grid gain
        r["dip_calls_share63"] = r["dip_calls"] / (63 * r["grid_calls_mean_pt"]) if r["grid_calls_mean_pt"] else np.nan
        r["dip_calls_share_exact"] = r["dip_calls"] / r["grid_calls_sum"] if r["grid_calls_sum"] else np.nan
        for k in ("arp", "arp_msa", "mct_br", "mct_so"):
            if f"sc_{k}" in r:
                r[f"{k}_vs_grid_gain"] = r[f"{k}_gain_pct"] / gg if gg >= MIN_GAIN_PCT else np.nan
    for k in ("arp", "arp_msa", "mct_br", "mct_so"):
        if f"sc_{k}" in r:
            r[f"{k}_vs_dip_gain"] = r[f"{k}_gain_pct"] / r["dip_gain_pct"] if r["dip_gain_pct"] >= MIN_GAIN_PCT else np.nan
    # gain share against the social optimum: (SC_unpriced - SC_method) / (SC_unpriced - SC_social optimum)
    den = sc0 - r["sc_so_best"]
    ok = r["so_gap_pct_of_abs"] >= MIN_SO_GAP_PCT
    meth = {"grid": r.get("sc_grid_best"), "dip": r["sc_dip"], "arp": r.get("sc_arp"), "arp_msa": r.get("sc_arp_msa"),
            "mct_br": r.get("sc_mct_br"), "mct_so": r.get("sc_mct_so"), "grid_cong": r.get("sc_congestion_only"),
            "grid_delivery": r.get("sc_delivery_only")}
    for k, v in meth.items():
        r[f"so_share_{k}"] = (sc0 - v) / den if (v is not None and np.isfinite(v) and ok) else np.nan
    # the same with the E3 optimum (without DIP's multi-start improvement)
    den3 = sc0 - so_e3
    ok3 = 100 * den3 / abs(sc0) >= MIN_SO_GAP_PCT
    for k in ("grid", "dip", "arp"):
        v = meth[k]
        r[f"so_share_e3_{k}"] = (sc0 - v) / den3 if (v is not None and np.isfinite(v) and ok3) else np.nan
    r["grid_lower_bound"] = r.get("grid_mode") == "coarse"
    return r


def build_runs():
    runs, grids = [], []
    for c in CITIES:
        for s in range(10):
            if s in OLD:
                r, g = load_old(c, s)
                load_arp_extra(c, s, r)
            else:
                r, g = load_new(c, s)
                if r is None:
                    continue
            runs.append(derive(r))
            if g is not None:
                grids.append(g)
    return pd.DataFrame(runs), (pd.concat(grids, ignore_index=True) if grids else pd.DataFrame())


# ------------------------------------------------------------------------------------------------ statistics
def boot_ci(x, stat=np.mean, B=B_BOOT, seed=RNG_SEED):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan, np.nan
    if len(x) == 1 or np.ptp(x) == 0:
        return float(stat(x)), float(stat(x))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(B, len(x)))
    v = np.array([stat(x[i]) for i in idx]) if stat is not np.mean else x[idx].mean(1)
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def boot_ratio_ci(num, den, B=B_BOOT, seed=RNG_SEED):
    """ratio of means sum(num)/sum(den) over seeds, percentile bootstrap (paired resampling of the seeds)"""
    num, den = np.asarray(num, float), np.asarray(den, float)
    m = np.isfinite(num) & np.isfinite(den)
    num, den = num[m], den[m]
    if len(num) < 2 or den.sum() == 0:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(num), size=(B, len(num)))
    d = den[idx].sum(1)
    v = np.where(np.abs(d) > 1e-12, num[idx].sum(1) / np.where(np.abs(d) > 1e-12, d, 1), np.nan)
    return float(num.sum() / den.sum()), float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))


QUANTITIES = [  # (column, label, group)
    ("served_share0", "unpriced served share", "E1"),
    ("slowdown_pct0", "unpriced added slowdown (%)", "E1"),
    ("gain_congestion_only_pct", "congestion-only gain (% of |SC|)", "grid"),
    ("gain_delivery_only_pct", "delivery-only gain (% of |SC|)", "grid"),
    ("gain_both_pct", "two-instrument gain (% of |SC|)", "grid"),
    ("share_delivery", "delivery-only share of the combined gain", "grid"),
    ("poa_zmc", "PoA (ZMC equilibrium)", "E3"),
    ("pos", "PoS (best equilibrium found)", "E3"),
    ("poa_worst", "PoA (worst equilibrium found)", "E3"),
    ("gap_unpriced_pct", "unpriced gap to the social optimum (% of W_SO)", "E3"),
    ("priced_gap_pct", "priced gap, grid-best point (% of W_SO)", "E3"),
    ("dip_priced_gap_pct", "priced gap, DIP (% of W_SO)", "dip"),
    ("dip_gain_pct", "DIP gain (% of |SC|)", "dip"),
    ("dip_vs_grid_gain", "DIP gain / best grid gain", "dip"),
    ("dip_calls", "DIP oracle calls", "dip"),
    ("dip_calls_share63", "DIP calls / calls of a 63-point grid", "dip"),
    ("dip_calls_share_exact", "DIP calls / calls of the exact grid points run", "dip"),
    ("arp_gain_pct", "ARP flat gain (% of |SC|)", "arp"),
    ("arp_calls", "ARP flat oracle calls", "arp"),
    ("mct_br_gain_pct", "marginal tariff + best responses gain (% of |SC|)", "arp"),
    ("mct_so_gain_pct", "marginal tariff + solver gain (% of |SC|)", "arp"),
    ("arp_vs_dip_gain", "ARP flat gain / DIP gain", "arp"),
    ("mct_br_vs_dip_gain", "tariff + BR gain / DIP gain", "arp"),
    ("so_share_grid", "gain share vs social optimum: grid-best", "so"),
    ("so_share_grid_cong", "gain share vs social optimum: congestion-only", "so"),
    ("so_share_grid_delivery", "gain share vs social optimum: delivery-only", "so"),
    ("so_share_dip", "gain share vs social optimum: DIP", "so"),
    ("so_share_arp", "gain share vs social optimum: ARP flat", "so"),
    ("so_share_mct_br", "gain share vs social optimum: tariff + BR", "so"),
    ("so_share_mct_so", "gain share vs social optimum: tariff + solver", "so"),
    ("so_gap_pct_of_abs", "social-optimum gain (% of |SC|)", "so"),
]


def ci_table(runs):
    rows = []
    for c in CITIES:
        d = runs[runs.city == c]
        old, new = d[d.seed.isin(OLD)], d[~d.seed.isin(OLD)]
        for col, label, grp in QUANTITIES:
            if col not in d:
                continue
            x = d[col].astype(float)
            xs = x[np.isfinite(x)]
            if len(xs) == 0:
                continue
            lo, hi = boot_ci(xs)
            x3 = old[col].astype(float)
            x3 = x3[np.isfinite(x3)]
            rows.append(dict(city=c, quantity=col, label=label, group=grp, n_seeds=len(xs), mean=xs.mean(), sd=xs.std(ddof=1) if len(xs) > 1 else np.nan,
                             ci_lo=lo, ci_hi=hi, min=xs.min(), max=xs.max(), median=xs.median(),
                             n_seeds_3=len(x3), mean_3=x3.mean() if len(x3) else np.nan, sd_3=x3.std(ddof=1) if len(x3) > 1 else np.nan,
                             mean_new=new[col].astype(float).mean() if len(new) else np.nan,
                             lower_bound_grid=bool(grp in ("grid", "so") and c not in FULL and ("grid" in col or col.startswith("gain") or col.startswith("share") or col.startswith("dip_vs") or col.startswith("so_share_grid")
                                                                                                or col in ("dip_calls_share63", "dip_calls_share_exact", "arp_vs_grid_gain", "priced_gap_pct")))))
    return pd.DataFrame(rows)


def conclusions(runs):
    """the claims of the three-seed analysis at ten seeds"""
    out = []
    S3 = runs[runs.seed.isin(OLD)]

    def add(claim, city, metric, thr, direction, v3, v10, n10, lo, hi, extra="", crosses=None):
        holds3 = (v3 < thr) if direction == "<" else (v3 >= thr)
        holds10 = (v10 < thr) if direction == "<" else (v10 >= thr)
        cross = (lo < thr <= hi) if crosses is None else crosses
        word = "holds" if holds10 else "fails"
        verdict = "FLIPPED" if holds3 != holds10 else (f"{word}, CI crosses threshold" if cross else f"stable ({word})")
        out.append(dict(claim=claim, city=city, metric=metric, threshold=f"{direction} {thr}", value_3seeds=v3, value_10seeds=v10, n_seeds=n10,
                        ci_lo=lo, ci_hi=hi, holds_3=holds3, holds_10=holds10, verdict=verdict, note=extra))

    for c in CITIES:
        d = runs[runs.city == c]
        d3 = S3[S3.city == c]
        if "gain_congestion_only_pct" not in d:
            continue
        # C2 congestion-only below 1.7 % of |SC| in every seed (sample maximum), and in the mean
        x = d.gain_congestion_only_pct.values
        x = x[np.isfinite(x)]
        if len(x) == 0:
            continue
        lo, hi = boot_ci(x)
        add("C2 congestion-only gain below 1.7% (maximum over seeds)", c, "max over seeds (%)", CONG_BOUND, "<", d3.gain_congestion_only_pct.max(), x.max(), len(x), lo, hi,
            extra=f"{int((x >= CONG_BOUND).sum())} of {len(x)} seeds at or above 1.7; mean {x.mean():.3g}" + ("; lower bound (reduced grid)" if c not in FULL else ""),
            crosses=bool(hi >= CONG_BOUND) and not bool(x.max() >= CONG_BOUND))
        # C1 delivery-only at least half of the combined gain (ratio of means; only where the combined gain is material)
        both, dl = d.gain_both_pct.values, d.gain_delivery_only_pct.values
        okm = np.isfinite(both)
        both, dl = both[okm], dl[okm]
        if len(both) and both.mean() >= MIN_GAIN_PCT:
            r10, lo, hi = boot_ratio_ci(dl, both)
            b3, d3v = d3.gain_both_pct.values, d3.gain_delivery_only_pct.values
            r3 = d3v.sum() / b3.sum() if b3.sum() > 0 else np.nan
            nfrac = int(np.sum(d.share_delivery_raw.values[np.isfinite(d.share_delivery_raw.values)] >= SHARE_BOUND))
            add("C1 delivery-only >= half of the combined gain (ratio of mean gains)", c, "share", SHARE_BOUND, ">=", r3, r10, len(both), lo, hi,
                extra=f"{nfrac} of {len(both)} seeds have a per-seed share >= 0.5" + ("; share can exceed 1 with a reduced grid" if c not in FULL else ""))
    # C3 PoA ordering London > Buenos Aires > New Delhi (paired over seeds)
    P = runs.pivot(index="seed", columns="city", values="poa_zmc")
    if {"London", "BuenosAires", "NewDelhi"} <= set(P.columns):
        P = P[["London", "BuenosAires", "NewDelhi"]].dropna()
        for a, b in (("London", "BuenosAires"), ("BuenosAires", "NewDelhi")):
            dif = (P[a] - P[b]).values
            lo, hi = boot_ci(dif)
            d3 = dif[[i for i, s in enumerate(P.index) if s in OLD]]
            frac = float((dif > 0).mean())
            add(f"C3 PoA ordering {a} > {b}", f"{a} - {b}", "mean PoA difference", 0.0, ">=", d3.mean() if len(d3) else np.nan, dif.mean(), len(dif), lo, hi,
                extra=f"ordering holds in {int((dif > 0).sum())} of {len(dif)} seeds")
        both_ok = ((P.London > P.BuenosAires) & (P.BuenosAires > P.NewDelhi)).mean()
        out.append(dict(claim="C3 PoA ordering London > Buenos Aires > New Delhi in each seed", city="three cities", metric="share of seeds with the full ordering",
                        threshold="= 1", value_3seeds=float(((P.London > P.BuenosAires) & (P.BuenosAires > P.NewDelhi))[P.index.isin(OLD)].mean()), value_10seeds=both_ok,
                        n_seeds=len(P), holds_3=True, holds_10=bool(both_ok == 1.0), verdict="stable (holds)" if both_ok == 1.0 else "FLIPPED (not in every seed)",
                        note=f"{int(round(both_ok * len(P)))} of {len(P)} seeds"))
    for c in CITIES:  # large PoA only in the three cities
        d = runs[runs.city == c]
        x = d.poa_zmc.values
        lo, hi = boot_ci(x)
        thr = POA_LARGE
        v3 = S3[S3.city == c].poa_zmc.mean()
        large = c in FULL
        holds3, holds10 = (v3 >= thr) == large, (x.mean() >= thr) == large
        cross = lo < thr <= hi
        out.append(dict(claim="C3 PoA >= 1.10 only in London, Buenos Aires, New Delhi", city=c, metric="mean PoA (ZMC equilibrium)", threshold=f"{'>=' if large else '<'} {thr}",
                        value_3seeds=v3, value_10seeds=x.mean(), n_seeds=len(x), ci_lo=lo, ci_hi=hi, holds_3=holds3, holds_10=holds10,
                        verdict="FLIPPED" if holds3 != holds10 else ("CI crosses threshold" if cross else f"stable ({'holds' if holds10 else 'fails'})"), note=f"max over seeds {x.max():.3f}"))
    # priced gap: the 3-seed text says at most 7.4% in every seed and at most 0.4% in six cities
    for c in CITIES:
        d = runs[runs.city == c]
        if "priced_gap_pct" not in d:
            continue
        x = d.priced_gap_pct.values
        x = x[np.isfinite(x)]
        lo, hi = boot_ci(x)
        add("C4 priced equilibrium within 7.5% of the social optimum in every seed (3-seed maximum 7.43, London)", c, "max over seeds (% of W_SO)", 7.5, "<",
            S3[S3.city == c].priced_gap_pct.max(), x.max(), len(x), lo, hi, extra=f"mean {x.mean():.3g}; grid-best point" + ("; reduced grid: upper bound" if c not in FULL else ""),
            crosses=bool(hi >= 7.5) and not bool(x.max() >= 7.5))
    # DIP vs grid: DIP at least as good as the best grid point (share >= 1) and uses <10% of the calls of a 63-point grid
    for c in CITIES:
        d = runs[runs.city == c]
        if "dip_vs_grid_gain" not in d:
            continue
        x = d.dip_vs_grid_gain.values
        x = x[np.isfinite(x)]
        if len(x):
            lo, hi = boot_ci(x)
            v3 = S3[S3.city == c].dip_vs_grid_gain.mean()
            add("C5 DIP gain >= best grid gain (share >= 1)", c, "mean gain share", 1.0, ">=", v3, x.mean(), len(x), lo, hi,
                extra=f"min {x.min():.3g}" + ("; against a lower-bound grid" if c not in FULL else ""))
        y = d.dip_calls_share63.values
        y = y[np.isfinite(y)]
        lo, hi = boot_ci(y)
        add("C5 DIP uses less than 10% of the calls of a 63-point grid", c, "mean call share", 0.10, "<", S3[S3.city == c].dip_calls_share63.mean(), y.mean(), len(y), lo, hi,
            extra=f"max {y.max():.3g}")
    # ARP vs DIP: ARP flat reaches at most DIP's gain; tariff + BR close to DIP
    for c in CITIES:
        d = runs[runs.city == c]
        if "arp_vs_dip_gain" not in d:
            continue
        for k, lab in (("arp_vs_dip_gain", "ARP flat"), ("mct_br_vs_dip_gain", "marginal tariff + BR")):
            x = d[k].values
            x = x[np.isfinite(x)]
            if len(x) < 2:
                continue
            lo, hi = boot_ci(x)
            v3 = S3[S3.city == c][k].mean()
            add(f"C6 {lab} gain below DIP's gain (ratio < 1)", c, "mean gain ratio", 1.0, "<", v3 if np.isfinite(v3) else np.nan, x.mean(), len(x), lo, hi,
                extra=f"ratio >= 0.98 in {int((x >= 0.98).sum())} of {len(x)} seeds")
    return pd.DataFrame(out)


def oracle_budget(runs):
    rows = []
    for c in CITIES:
        for s in range(3, 10):
            cp = jload(PARTS / f"core_{c}_s{s}.json")
            if not cp.get("done"):
                continue
            r = dict(city=c, seed=s, e1_bp_calls=cp["e1"]["row"].get("bp_calls"), e1_time_s=cp["e1"]["row"]["time_s"],
                     e1_unproven=cp["e1"]["row"].get("bp_unproven"), e1_retried=cp["e1"]["row"].get("bp_retried"),
                     dip_bp_calls=cp["dip"]["bp_calls"], dip_zmc_calls=cp["dip"]["calls"], dip_time_s=cp["dip"]["time_s"], dip_unproven=cp["dip"]["bp_unproven"],
                     dip_retried=cp["dip"].get("bp_retried"), verify_bp_calls=cp["verify"]["bp_calls"], verify_time_s=cp["verify"]["time_s"],
                     ne_bp_calls=cp["ne"]["bp_calls"], ne_time_s=cp["ne"]["time_s"], ne_unproven=cp["ne"]["bp_unproven"], ne_retried=cp["ne"].get("bp_retried"))
            ap = PARTS / "arp" / f"{c}_s{s}.json"
            if ap.exists():
                A = jload(ap)
                if A.get("done"):
                    r.update(arp_bp_calls=sum(A[k]["bp_calls"] for k in ("arp", "arp_msa", "mct_br", "mct_so") if k in A and "bp_calls" in A[k]),
                             arp_time_s=sum(A[k]["time_s"] for k in ("arp", "arp_msa", "mct_br", "mct_so") if k in A and "time_s" in A[k]),
                             arp_unproven=sum(A[k].get("bp_unproven", 0) for k in ("arp", "arp_msa", "mct_br", "mct_so") if k in A))
            gp = jload(PARTS / f"grid_{c}_s{s}.json")
            if gp.get("done"):
                rr = [x for x in gp["rows"] if x["config"] != "none"]
                r.update(grid_points_solved=len(rr), grid_bp_calls=sum(x.get("bp_calls", 0) for x in rr) + gp["cert"].get("bp_calls", 0),
                         grid_time_s=sum(x["time_s"] for x in rr), grid_unproven=sum(x.get("bp_unproven", 0) for x in rr),
                         grid_retried=sum(x.get("bp_retried", 0) for x in rr), grid_max_regret=max(x["max_regret"] for x in rr) if rr else 0.0,
                         cert_regret_fresh=gp["cert"]["regret_fresh"])
            rows.append(r)
    return pd.DataFrame(rows)


def main():
    runs, grids = build_runs()
    runs = runs.sort_values(["city", "seed"], key=lambda s: s.map({c: i for i, c in enumerate(CITIES)}) if s.name == "city" else s)
    runs.to_csv(RES / "seeds10_runs.csv", index=False, float_format="%.6g")
    runs.to_csv(RES / "summary_seeds10.csv", index=False, float_format="%.6g")
    if len(grids):
        keep = [c for c in ("city", "seed", "config", "theta", "sfrac", "social_cost", "welfare", "served_share", "mean_slowdown", "calls", "time_s", "max_regret",
                            "converged", "bp_calls", "bp_unproven") if c in grids]
        grids[keep].to_csv(RES / "seeds10_grid_points.csv", index=False, float_format="%.6g")
    ci = ci_table(runs)
    ci.to_csv(RES / "summary_seeds10_ci.csv", index=False, float_format="%.6g")
    con = conclusions(runs)
    con.to_csv(RES / "seeds10_conclusions.csv", index=False, float_format="%.6g")
    ob = oracle_budget(runs)
    if len(ob):
        ob.to_csv(RES / "seeds10_oracle.csv", index=False, float_format="%.6g")
    n = runs.groupby("city").seed.nunique()
    print("seeds per city:", n.to_dict())
    print(con[["claim", "city", "value_3seeds", "value_10seeds", "ci_lo", "ci_hi", "verdict"]].to_string(index=False))


if __name__ == "__main__":
    main()
