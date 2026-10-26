"""Tables (results/brl_bench_*.csv, results/summary_brl_bench.md) and figures (figures/brl_bench_*.png)."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
JOBS = RES / "brl_bench"
FIG = ROOT / "figures"

ARM_NAME = {"brl": "BRL (p-box, unknown dependence)", "saa": "SAA (expected cost)", "wass": "Wasserstein type-1",
            "cvar": "mean-CVaR (0.5, 0.8)", "det": "deterministic mean"}
COL = {"brl": "#1f77b4", "saa": "#2ca02c", "wass": "#d62728", "cvar": "#9467bd", "det": "#7f7f7f"}


def load(stage: str) -> pd.DataFrame:
    rows = []
    for p in sorted((JOBS / stage).glob("*.json")):
        d = json.loads(p.read_text())
        if "error" in d:
            continue
        d.pop("routes", None)
        d.pop("duals", None)
        rows.append(d)
    return pd.DataFrame(rows)


def md_table(df: pd.DataFrame, fmt: dict | None = None) -> str:
    fmt = fmt or {}
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append("" if not np.isfinite(v) else (fmt.get(c, "{:.3g}").format(v)))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------------------------
# A: public benchmark
# ---------------------------------------------------------------------------------------------------------------


def pub_tables(out_md: list):
    df = load("pub")
    if df.empty:
        return
    df.to_csv(RES / "brl_bench_pub.csv", index=False, float_format="%.8g")
    df["cell"] = df.inst + "|" + df.N.astype(str) + "|" + df.rep.astype(str)
    full = df.groupby("cell").arm.transform("count") == len(ARM_NAME)
    d = df[full].copy()
    ncell = d.cell.nunique()
    # relative out-of-sample statistics against the SAA plan of the same cell
    ref = d[d.arm == "saa"].set_index("cell")
    for m in ("oos_mean", "oos_p95", "oos_cvar90"):
        d[m + "_rel"] = 100 * (d[m].values / ref.loc[d.cell, m].values - 1)
    d["overtime_rel"] = d.oos_overtime - ref.loc[d.cell, "oos_overtime"].values
    # quality under the objective each arm optimises: the plan's own criterion vs best plan of any arm (same cell)
    for k in ARM_NAME:
        best = d.groupby("cell")[f"val_{k}"].transform("min")
        d[f"gap_{k}"] = 100 * (d[f"val_{k}"] / best - 1)
    d["own_gap"] = [r[f"gap_{r.arm}"] for _, r in d.iterrows()]
    d["proven_f"] = d.proven.astype(float)
    g = d.groupby(["N", "arm"]).agg(cells=("cell", "nunique"), proven=("proven_f", "mean"), time_mean=("time", "mean"),
                                    time_median=("time", "median"), labels_max_median=("max_labels", "median"),
                                    created_median=("created", "median"), own_gap_pct=("own_gap", "mean"),
                                    oos_mean=("oos_mean", "mean"), oos_mean_rel_saa=("oos_mean_rel", "mean"),
                                    oos_p95_rel_saa=("oos_p95_rel", "mean"), oos_cvar90_rel_saa=("oos_cvar90_rel", "mean"),
                                    overtime_mean=("oos_overtime", "mean"), late_route_frac=("oos_late_route_frac", "mean"),
                                    late_day_frac=("oos_late_day_frac", "mean"), n_routes=("n_routes", "mean")).reset_index()
    order = {a: i for i, a in enumerate(ARM_NAME)}
    g = g.sort_values(["N", "arm"], key=lambda s: s.map(order) if s.name == "arm" else s)
    g.to_csv(RES / "brl_bench_pub_summary.csv", index=False, float_format="%.6g")
    out_md.append(f"## A. Public benchmark ({ncell} complete cells = instance x N x data draw)\n")
    out_md.append(md_table(g.assign(arm=g.arm.map(ARM_NAME)), {"proven": "{:.2f}", "time_mean": "{:.1f}", "time_median": "{:.1f}",
                                                                "labels_max_median": "{:.0f}", "created_median": "{:.3g}",
                                                                "own_gap_pct": "{:.2f}", "oos_mean": "{:.1f}",
                                                                "oos_mean_rel_saa": "{:+.2f}", "oos_p95_rel_saa": "{:+.2f}",
                                                                "oos_cvar90_rel_saa": "{:+.2f}", "overtime_mean": "{:.2f}",
                                                                "late_route_frac": "{:.3f}", "late_day_frac": "{:.3f}",
                                                                "n_routes": "{:.1f}"}))
    # cross-criterion matrix: plan of arm (rows) evaluated under criterion (columns), % above the best plan, by N
    rows = []
    for N in sorted(d.N.unique()):
        for a in ARM_NAME:
            r = {"N": N, "plan from": ARM_NAME[a]}
            for k in ARM_NAME:
                r[f"under {k}"] = d[(d.N == N) & (d.arm == a)][f"gap_{k}"].mean()
            rows.append(r)
    cm = pd.DataFrame(rows)
    cm.to_csv(RES / "brl_bench_pub_cross.csv", index=False, float_format="%.5g")
    out_md.append("\nPlan of each arm (rows) evaluated under every training-data criterion (columns): mean % above the best plan "
                  "found by any arm under that criterion (0 = best).\n")
    out_md.append(md_table(cm, {c: "{:.2f}" for c in cm.columns if c.startswith("under")}))
    # polished plans (local search under each criterion, started from the best plan of any arm)
    pl = load("polish")
    if not pl.empty:
        pl.to_csv(RES / "brl_bench_polish.csv", index=False, float_format="%.8g")
        pl["cell"] = pl.inst + "|" + pl.N.astype(str) + "|" + pl.rep.astype(str)
        pl["base_arm"] = pl.arm.str.replace("_ls", "")
        okc = pl.groupby("cell").arm.transform("count") == len(ARM_NAME)
        p2 = pl[okc].copy()
        raw = d[d.cell.isin(p2.cell)]
        allp = pd.concat([raw.assign(kind="raw"), p2.assign(kind="ls", arm=p2.base_arm)], ignore_index=True)
        for k in ARM_NAME:
            best = allp.groupby("cell")[f"val_{k}"].transform("min")
            allp[f"gap_{k}"] = 100 * (allp[f"val_{k}"] / best - 1)
        allp["own_gap"] = [r[f"gap_{r.arm}"] for _, r in allp.iterrows()]
        ls = allp[allp.kind == "ls"].copy()
        refl = ls[ls.arm == "saa"].set_index("cell")
        for m in ("oos_mean", "oos_p95", "oos_cvar90"):
            ls[m + "_rel"] = 100 * (ls[m].values / refl.loc[ls.cell, m].values - 1)
        gl = ls.groupby(["N", "arm"]).agg(cells=("cell", "nunique"), own_gap_pct=("own_gap", "mean"), oos_mean=("oos_mean", "mean"),
                                          oos_mean_rel_saa_ls=("oos_mean_rel", "mean"), oos_p95_rel_saa_ls=("oos_p95_rel", "mean"),
                                          oos_cvar90_rel_saa_ls=("oos_cvar90_rel", "mean"), overtime_mean=("oos_overtime", "mean"),
                                          late_route_frac=("oos_late_route_frac", "mean"), n_routes=("n_routes", "mean")).reset_index()
        gl = gl.sort_values(["N", "arm"], key=lambda s_: s_.map(order) if s_.name == "arm" else s_)
        gl.to_csv(RES / "brl_bench_pub_summary_polished.csv", index=False, float_format="%.6g")
        out_md.append("\nSame plans after local-search polishing under each arm's own criterion (start: best plan of any arm under that "
                      "criterion). Relative statistics are against the polished SAA plan.\n")
        out_md.append(md_table(gl.assign(arm=gl.arm.map(ARM_NAME)), {"own_gap_pct": "{:.2f}", "oos_mean": "{:.1f}",
                                                                      "oos_mean_rel_saa_ls": "{:+.2f}", "oos_p95_rel_saa_ls": "{:+.2f}",
                                                                      "oos_cvar90_rel_saa_ls": "{:+.2f}", "overtime_mean": "{:.2f}",
                                                                      "late_route_frac": "{:.3f}", "n_routes": "{:.1f}"}))
        imp = (p2.start_value - p2.value) / p2.start_value.abs() * 100
        out_md.append(f"\nLocal search improved the starting plan in {int((imp > 1e-7).sum())} of {len(p2)} cases (mean {imp.mean():.2f}%, max {imp.max():.2f}%).\n")
    # per instance family, BRL against SAA
    d["family"] = d.inst.str.split("/").str[0]
    fam = d[d.arm.isin(["brl", "saa"])].groupby(["family", "N", "arm"]).agg(
        proven=("proven_f", "mean"), time=("time", "median"), oos_mean=("oos_mean", "mean"), oos_p95=("oos_p95", "mean")).reset_index()
    fam.to_csv(RES / "brl_bench_pub_family.csv", index=False, float_format="%.6g")
    # figure: relative out-of-sample metrics by N and arm; proven rate and time
    fig, ax = plt.subplots(1, 4, figsize=(17, 3.8))
    arms = list(ARM_NAME)
    xs = np.arange(len(NS := sorted(d.N.unique())))
    wd = 0.16
    for ai, (m, ttl) in enumerate([("oos_mean_rel", "held-out mean cost\n% vs SAA plan"), ("oos_p95_rel", "held-out 95th pct cost\n% vs SAA plan"),
                                   ("oos_cvar90_rel", "held-out CVaR90 of daily cost\n% vs SAA plan")]):
        for j, a in enumerate(arms):
            vals = [d[(d.N == N) & (d.arm == a)][m].mean() for N in NS]
            ax[ai].bar(xs + (j - 2) * wd, vals, wd, color=COL[a], label=ARM_NAME[a])
        ax[ai].set_xticks(xs, [f"N={N}" for N in NS])
        ax[ai].axhline(0, color="k", lw=0.6)
        ax[ai].set_title(ttl, fontsize=9)
    for j, a in enumerate(arms):
        vals = [d[(d.N == N) & (d.arm == a)]["time"].median() for N in NS]
        ax[3].bar(xs + (j - 2) * wd, vals, wd, color=COL[a])
        pr = [d[(d.N == N) & (d.arm == a)]["proven_f"].mean() for N in NS]
        for x, v, p in zip(xs + (j - 2) * wd, vals, pr):
            ax[3].text(x, v, f"{100 * p:.0f}%", ha="center", va="bottom", fontsize=6, rotation=90)
    ax[3].set_xticks(xs, [f"N={N}" for N in NS])
    ax[3].set_title("median solve time (s); label: % proven optimal", fontsize=9)
    ax[0].legend(fontsize=6, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "brl_bench_pub.png", dpi=140)
    plt.close(fig)


def shift_table(out_md: list):
    df = load("shift")
    if df.empty:
        return
    df["cell"] = df.inst + "|" + df.N.astype(str) + "|" + df.rep.astype(str)
    df["kind"] = np.where(df.arm.str.endswith("_ls"), "polished", "raw")
    df["arm"] = df.arm.str.replace("_ls", "")
    df.to_csv(RES / "brl_bench_shift.csv", index=False, float_format="%.8g")
    ok = df.groupby(["cell", "kind"]).arm.transform("count") == len(ARM_NAME)
    d = df[ok].copy()
    rows = []
    for kind in ("polished", "raw"):
        e = d[d.kind == kind]
        ref = e[e.arm == "saa"].set_index("cell")
        for m in ("shift_oos_mean", "shift_oos_p95", "shift_oos_cvar90"):
            e = e.assign(**{m + "_rel": 100 * (e[m].values / ref.loc[e.cell, m].values - 1)})
        g = e.groupby(["N", "arm"]).agg(cells=("cell", "nunique"), mean_rel=("shift_oos_mean_rel", "mean"), p95_rel=("shift_oos_p95_rel", "mean"),
                                        cvar90_rel=("shift_oos_cvar90_rel", "mean"), overtime=("shift_oos_overtime", "mean"),
                                        late_route_frac=("shift_oos_late_route_frac", "mean")).reset_index()
        g.insert(0, "plans", kind)
        rows.append(g)
    t = pd.concat(rows)
    order = {a_: i for i, a_ in enumerate(ARM_NAME)}
    t = t.sort_values(["plans", "N", "arm"], key=lambda s_: s_.map(order) if s_.name == "arm" else s_, ascending=[False, True, True])
    t.to_csv(RES / "brl_bench_shift_summary.csv", index=False, float_format="%.6g")
    out_md.append("\n### Stress test: plans evaluated on days from a shifted law (congestion excess x1.5, volatility x1.25), no re-solving; % vs the SAA plan of the same kind\n")
    out_md.append(md_table(t.assign(arm=t.arm.map(ARM_NAME)), {"mean_rel": "{:+.2f}", "p95_rel": "{:+.2f}", "cvar90_rel": "{:+.2f}",
                                                                 "overtime": "{:.2f}", "late_route_frac": "{:.3f}"}))


# ---------------------------------------------------------------------------------------------------------------
# B: label counts (central figure), devices, branch-and-price
# ---------------------------------------------------------------------------------------------------------------


def labels_tables(out_md: list):
    df = load("labels")
    if df.empty:
        return
    df["family"] = np.where(df.name.str.startswith("metro/"), "metro", df.name.str.split("/").str[0].str.replace(r"\d+$", "", regex=True))
    df.to_csv(RES / "brl_bench_labels.csv", index=False, float_format="%.8g")
    modes = ["window", "nowin", "qv"]
    nm = {"window": "completion-window (BRL)", "nowin": "stop-loss, no window", "qv": "quantile-vector"}
    cl = {"window": "#1f77b4", "nowin": "#ff7f0e", "qv": "#d62728"}
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.3))
    metro = df[df.family == "metro"]
    pub = df[df.family != "metro"]
    for gi, (grp, nme) in enumerate([(metro, "nine metro instances"), (pub, "public instances (Solomon, Augerat)")]):
        if grp.empty:
            continue
        for m in modes:
            for n, sub in grp.groupby("n"):
                v = sub[f"{m}_kept"].values.astype(float)
                cens = sub[f"{m}_overflow"].values
                ax[gi].scatter([n] * len(v), v, s=14, facecolors=np.where(cens, "none", cl[m]), edgecolors=cl[m], alpha=0.7)
            med = grp.groupby("n")[f"{m}_kept"].median()
            ax[gi].plot(med.index, med.values, "-", color=cl[m], label=nm[m])
        ax[gi].set_yscale("log")
        ax[gi].set_xscale("log")
        ax[gi].set_xlabel("customers n")
        ax[gi].set_ylabel("labels kept at the end of one pricing call")
        ax[gi].set_title(nme + "\n(hollow = hit the cap, censored)", fontsize=9)
        ax[gi].legend(fontsize=7)
    for m, ls in (("nowin", "--"), ("qv", "-")):
        for fam, grp, mk in (("metro", metro, "o"), ("public", pub, "s")):
            if grp.empty:
                continue
            ratio = (grp[f"{m}_kept"] / grp["window_kept"]).groupby(grp.n).median()
            ax[2].plot(ratio.index, ratio.values, ls, marker=mk, color=cl[m], label=f"{nm[m]} / window ({fam})")
    ax[2].set_yscale("log")
    ax[2].set_xscale("log")
    ax[2].set_xlabel("customers n")
    ax[2].set_ylabel("median ratio of kept labels")
    ax[2].set_title("label reduction of the completion window\n(lower bound where censored)", fontsize=9)
    ax[2].axhline(1, color="k", lw=0.6)
    ax[2].legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(FIG / "brl_bench_labels.png", dpi=140)
    plt.close(fig)
    # table by n
    rows = []
    for (fam, n), sub in df.groupby([df.family.where(df.family == "metro", "public"), "n"]):
        r = {"family": fam, "n": n, "instances": len(sub), "CG converged": int((sub.cg_status == "converged").sum())}
        for m in modes:
            r[f"{m} kept (median)"] = sub[f"{m}_kept"].median()
            r[f"{m} capped"] = int(sub[f"{m}_overflow"].sum())
            r[f"{m} time s (median)"] = sub[f"{m}_time"].median()
        r["nowin/window"] = (sub.nowin_kept / sub.window_kept).median()
        r["qv/window"] = (sub.qv_kept / sub.window_kept).median()
        r["qv/window created"] = (sub.qv_created / sub.window_created).median()
        r["window cmp"] = sub.window_ncmp.median()
        r["qv cmp"] = sub.qv_ncmp.median()
        rows.append(r)
    t = pd.DataFrame(rows).sort_values(["family", "n"])
    t.to_csv(RES / "brl_bench_labels_summary.csv", index=False, float_format="%.5g")
    out_md.append("\n## B1. Labels kept by the three dominance rules (same duals: root column generation, ng-8)\n")
    out_md.append(md_table(t, {c: "{:.3g}" for c in t.columns}))
    # root CG scale table
    cg = df.assign(fam=df.family.where(df.family == "metro", "public")).groupby(["fam", "n"]).agg(
        instances=("name", "count"), converged=("cg_status", lambda s: int((s == "converged").sum())),
        cg_time_median=("cg_time", "median"), cg_time_max=("cg_time", "max"), iters_median=("cg_iters", "median"),
        max_kept_median=("cg_max_kept", "median")).reset_index()
    cg.to_csv(RES / "brl_bench_scale.csv", index=False, float_format="%.5g")
    out_md.append("\n## B1b. Root column generation with exact BRL pricing (time limit per instance as stated)\n")
    out_md.append(md_table(cg, {"cg_time_median": "{:.1f}", "cg_time_max": "{:.0f}", "iters_median": "{:.0f}", "max_kept_median": "{:.0f}"}))


def devices_tables(out_md: list):
    df = load("devices")
    if df.empty:
        return
    df["key"] = df.name + "@" + df.n.astype(str)
    df.to_csv(RES / "brl_bench_devices.csv", index=False, float_format="%.8g")
    base = df[df.cfg == "base_ng8"].set_index("key")
    rows = []
    for cfg, sub in df.groupby("cfg"):
        s = sub.set_index("key")
        common = [i for i in s.index if i in base.index and (s.loc[i].get("status") is not None)]
        both = [i for i in common if s.loc[i, "status"] == "converged" and base.loc[i, "status"] == "converged"]
        sp = [base.loc[i, "time"] / s.loc[i, "time"] for i in both]
        rows.append(dict(config=cfg, instances=len(s), converged=int((s.status == "converged").sum()),
                         both_converged=len(both), speedup_median=float(np.median(sp)) if sp else np.nan,
                         speedup_min=min(sp) if sp else np.nan, speedup_max=max(sp) if sp else np.nan,
                         lp_diff_max=max([abs(s.loc[i, "lp"] - base.loc[i, "lp"]) / abs(base.loc[i, "lp"]) for i in both] or [np.nan]),
                         lp_ge_base=int(sum(s.loc[i, "lp"] >= base.loc[i, "lp"] - 1e-6 * abs(base.loc[i, "lp"]) for i in both)),
                         time_total=float(s.time.sum()), created_total=float(s.created.sum())))
    t = pd.DataFrame(rows)
    t.to_csv(RES / "brl_bench_devices_summary.csv", index=False, float_format="%.5g")
    out_md.append("\n## B2. Scale-up devices at the root (set-partitioning LP by column generation)\n")
    out_md.append(md_table(t, {"speedup_median": "{:.2f}", "speedup_min": "{:.2f}", "speedup_max": "{:.2f}", "lp_diff_max": "{:.2e}",
                               "time_total": "{:.0f}", "created_total": "{:.3g}"}))
    piv = df.pivot_table(index="key", columns="cfg", values="time", aggfunc="first")
    st = df.pivot_table(index="key", columns="cfg", values="status", aggfunc="first")
    cell = piv.round(1).astype(str) + st.map(lambda s: "" if s == "converged" else "*")
    out_md.append("\nRoot time per instance in seconds (* = time limit or label cap before convergence):\n")
    out_md.append(md_table(cell.reset_index()))


def bp_tables(out_md: list):
    df = load("bpscale")
    if df.empty:
        return
    df.to_csv(RES / "brl_bench_bpscale.csv", index=False, float_format="%.8g")
    cols = ["name", "n", "cfg", "status", "value", "lb", "rel_gap", "nodes", "time", "root_time", "pricing_time", "heur_time",
            "max_labels", "n_cols", "ng_aug"]
    t = df[cols].sort_values(["name", "n", "cfg"])
    out_md.append("\n## B3. Full branch-and-price as the instance grows (time limit as stated in the table `tl`)\n")
    out_md.append(md_table(t, {"value": "{:.4f}", "lb": "{:.4f}", "rel_gap": "{:.2e}", "time": "{:.0f}", "root_time": "{:.1f}",
                               "pricing_time": "{:.0f}", "heur_time": "{:.0f}"}))
    # figure: time and status vs n
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    for name, sub in df.groupby("name"):
        for cfg, ls in (("exact", "-"), ("devices", "--")):
            s = sub[sub.cfg == cfg].sort_values("n")
            if s.empty:
                continue
            ax[0].plot(s.n, s.time, ls, marker="o", label=f"{name} {cfg}")
            fin = s[s.status != "optimal"]
            ax[0].scatter(fin.n, fin.time, marker="x", color="k", zorder=5)
    ax[0].set_yscale("log")
    ax[0].set_xscale("log")
    ax[0].set_xlabel("customers n")
    ax[0].set_ylabel("branch-and-price wall time (s), x = not proven")
    ax[0].legend(fontsize=5, ncol=2)
    d2 = df[df.rel_gap.notna()]
    for name, sub in d2.groupby("name"):
        s = sub[sub.cfg == "exact"].sort_values("n")
        ax[1].plot(s.n, 100 * s.rel_gap.clip(lower=1e-6), marker="o", label=name)
    ax[1].set_yscale("log")
    ax[1].set_xlabel("customers n")
    ax[1].set_ylabel("remaining gap at the limit (%) [exact config]")
    fig.tight_layout()
    fig.savefig(FIG / "brl_bench_bpscale.png", dpi=140)
    plt.close(fig)


def main():
    out = ["# BRL benchmark and scale study: generated summary\n", "Generated by experiments/summarize_brl_bench.py from results/brl_bench/*/*.json.\n"]
    pub_tables(out)
    shift_table(out)
    labels_tables(out)
    devices_tables(out)
    bp_tables(out)
    (RES / "summary_brl_bench.md").write_text("\n".join(out))
    print("\n".join(out)[:6000])


if __name__ == "__main__":
    main()
