"""Shared helpers for the game-theoretic experiments (ZMC + BRL on the nine city maps)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ccu import zmc, zmc_brl as zb  # noqa: E402

RES = ROOT / "results"
FIG = ROOT / "figures"
RES.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

SCALARS = ["deliveries", "demand", "served_share", "vehicles", "vehicle_hours", "mean_price", "mean_slowdown",
           "max_slowdown", "profit_total", "charges", "social_cost", "welfare", "consumer_surplus",
           "congestion_cost", "routing_cost", "bg_delay_cost", "social_cost_broad", "gini_access", "gini_price"]


def scalars(ev: dict) -> dict:
    return {k: float(ev[k]) for k in SCALARS}


def solve_ne(g, rounds: int = 8, lam0=None, certify: str = "none") -> dict:
    """ZMC equilibrium + metrics.  certify: 'none' | 'oracle' (pooled oracle) | 'fresh' (independent fresh-pool oracle)."""
    t0 = time.perf_counter()
    c_start = g.calls
    r = zmc.run_zmc(g, rounds=rounds, lam0=lam0)
    prof = r["profile"]
    ev = g.evaluate(prof)
    row = scalars(ev)
    row.update(calls=r["calls"], calls_search=r["calls_search"], converged=bool(r["converged"]), start=r["start"],
               phi=g.potential(prof), phi_relaxed=r["phi_relaxed"])
    lbs = [t["G_lb"] for t in r["trace"] if np.isfinite(t["G_lb"])]
    row["eta_cert"] = (row["phi"] - max(lbs)) if lbs else np.nan
    row["eta_rel"] = row["eta_cert"] / abs(row["phi"]) if lbs and row["phi"] != 0 else np.nan
    row["time_s"] = time.perf_counter() - t0
    if certify == "fresh":
        # independent fresh-pool oracle; its columns are injected into the pooled oracle, and the profile is
        # re-polished until the independent oracle finds no improving deviation (at most 3 times)
        for k in range(3):
            if g.regrets(prof, count=False, fresh=True).max() < 1e-7:
                break
            prof, ok = zmc.br_dynamics(g, init=prof)
            row["polish_after_fresh"] = k + 1
        ev = g.evaluate(prof)
        row.update(scalars(ev))
        row["phi"] = g.potential(prof)
        row["converged"] = bool(ok) if "polish_after_fresh" in row else row["converged"]
        row["calls"] = g.calls - c_start
    if certify != "none":
        reg = g.regrets(prof, count=False, fresh=(certify == "fresh"))
        row["max_regret"] = float(reg.max())
        row["max_regret_lp"] = float(np.nanmax(g._last_regret_lp))
    row["lp_gap_max"] = g.lp_gap_max
    return dict(row=row, result=r, profile=prof, eval=ev)


def write_csv(path, rows: list[dict]):
    """Atomic write (temp file in the same directory, then os.replace): a killed job never leaves a truncated file."""
    import os

    import pandas as pd

    path = Path(path)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    pd.DataFrame(rows).to_csv(tmp, index=False, float_format="%.6g")
    os.replace(tmp, path)


def rpath(prefix: str, city: str, seed: int = 0) -> Path:
    """Result file of one (experiment, city, seed). Seed 0 keeps the historical name <prefix>_<city>.csv."""
    return RES / (f"{prefix}_{city}.csv" if seed == 0 else f"{prefix}_{city}_s{seed}.csv")


def read_rows(path) -> list[dict]:
    """Rows of a partial result file (empty list when absent or unreadable)."""
    import pandas as pd

    try:
        return pd.read_csv(path).to_dict("records")
    except Exception:
        return []
