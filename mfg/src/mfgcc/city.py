"""Time-expanded zone-graph instances on the nine processed cities (data/processed/<City>).

Base instance (one city, one seed): ``n_types`` segments of small multi-stop carriers.  Segment theta has a depot
zone, ``n_cust`` customer zones (gravity sampling around the depot, as in ccu.zmc_brl.build_city_game), lots per
stop (Omega calibration) and a fleet budget in vehicle-hours.  A *tour* (column) starts at hour t0, visits one to
``max_stops`` distinct customer zones in the order of least travel time, delivers one lot at each stop in the hour
in which the stop starts, and returns to the depot before 18:00.  Hourly travel times are the zone-to-zone times
of travel_time_matrix.npy multiplied by (1 + cong(h)) of the stylised profile (mfgcc.profiles).

Coupling (delivery units, Omega assumption C3): vehicle-hours in zone-time (z, t) are r * Q_zt with r = in-zone
hours per delivery, so carriers face m_zt = b_zt + kappa_zt per delivery, kappa_zt = gamma_h c_zt r^2, where
b_zt = alpha / (2 Q^full_zt) (Omega inverse-demand convention, hour share psi_t / H of the slice's daily demand)
and c_zt is the BPR slope at the hourly congestion level with the slice multiplicity of ccu.zmc_brl.

Splits: the base segment theta with budget B_theta is divided among k small carriers, either as exact replicas
(budget B_theta / k each; one solver block with count k) or heterogeneously (Dirichlet(2) budget shares and an
individual routing-cost multiplier U[0.85, 1.15]; k solver blocks).  N = n_types * k.
"""
from __future__ import annotations

import itertools
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

from .profiles import congestion_profile, demand_profile, peak_levels
from .qp import Block

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from ccu.zmc_brl import CITIES, load_wide  # noqa: E402  (read-only reuse)
from ccu.geo import select_depot_sites  # noqa: E402

H = 10  # periods 08:00-18:00


@dataclass
class CityGame:
    city: str
    seed: int
    base: list  # list of dict(rev, cost, L, w, B, depot, zones)
    coords: np.ndarray  # (d, 2) zone, hour of each coordinate
    b: np.ndarray
    kappa: np.ndarray
    alpha: float
    r: float
    gamma_h: float
    meta: dict = field(default_factory=dict)

    @property
    def m(self) -> np.ndarray:
        return self.b + self.kappa

    @property
    def d(self) -> int:
        return len(self.b)

    def blocks(self, k: int, mode: str = "replica", rng: np.random.Generator | None = None) -> list[Block]:
        out = []
        for th, B in enumerate(self.base):
            if mode == "replica":
                out.append(Block(B["rev"] - B["cost"], B["L"], B["w"], B["B"], count=k, tag=f"t{th}"))
            else:
                share = rng.dirichlet(np.full(k, 2.0)) if k > 1 else np.ones(1)
                mult = rng.uniform(0.85, 1.15, k) if k > 1 else np.ones(1)
                for i in range(k):
                    out.append(Block(B["rev"] - mult[i] * B["cost"], B["L"], B["w"], B["B"] * share[i], count=1,
                                     tag=f"t{th}c{i}"))
        return out


def _tt(TT, a, b):
    return TT[a, b] / 3600.0  # hours


def build(city: str, seed: int = 0, *, n_types: int = 6, n_cust: int = 8, max_stops: int = 3, amp: float = 1.0,
          reach: float = 0.4, min_sep_km: float = 3.0, pce: float = 1.5, fleet_factor: float = 1.0,
          kappa_scale: float = 1.0) -> CityGame:
    rng = np.random.default_rng([seed, 4242])
    P = load_wide(city)
    zdir = ROOT / "data/processed" / city
    zones = pd.read_csv(zdir / "zones.csv")
    TT = np.load(zdir / "travel_time_matrix.npy").astype(float)
    Z = len(zones)
    pop = np.maximum(zones["pop"].to_numpy(float), 0.0)
    lane = np.maximum(zones["lane_km_major"].to_numpy(float), 1.0)
    ppc, drops, shift = P["parcels_per_capita_per_day"], P["drops_per_vehicle_per_day"], P["shift_hours"]
    fee, wage, fuel, cap = P["delivery_fee_usd"], P["driver_wage_usd_per_hour"], P["fuel_usd_per_litre"], P[
        "van_capacity_parcels"]
    cong0 = P["tomtom_congestion_pct"] / 100.0
    cong = congestion_profile(city, cong0, amp)  # (H,)
    psi = demand_profile(amp)  # (H,)
    fuel_l = 1.0 if cap <= 60 else 3.0
    gamma_h = wage + fuel_l * fuel
    r = 0.6 * shift / drops  # in-zone hours per delivery (Omega h_drop)
    sites = select_depot_sites(zones[["zone_id", "lon", "lat", "depot_score", "pop"]], n_types, rng, min_sep_km)
    if len(sites) < n_types:
        order = [int(z) for z in np.argsort(-zones["depot_score"].to_numpy()) if int(z) not in set(sites.tolist())]
        sites = np.concatenate([sites, np.array(order[: n_types - len(sites)], dtype=np.int64)])
    depots = [int(z) for z in sites[:n_types]]
    custs = []
    for th in range(n_types):
        t = TT[depots[th]]
        w = pop * np.exp(-t / max(np.percentile(t, 100.0 * reach), 1.0))
        w[depots[th]] = 0.0
        w = np.where(pop > 0, w, 0.0)
        k = min(n_cust, int((w > 0).sum()))
        custs.append(np.sort(rng.choice(Z, k, replace=False, p=w / w.sum())))
    share = 1.0 / n_types
    parc = [share * pop[c] * ppc for c in custs]
    q90 = float(np.quantile(np.concatenate(parc), 0.9))
    dmax, dmin = max(3, int(round(0.5 * drops))), max(2, int(round(0.1 * drops)))
    lots = [np.clip(np.round(dmax * pc / q90), dmin, dmax) for pc in parc]
    # ---- columns (tours) on the time-expanded graph
    coord_index: dict = {}
    raw = []
    for th in range(n_types):
        dep, cz, lot = depots[th], custs[th], lots[th]
        cols = []
        for ns in range(1, max_stops + 1):
            for sub in itertools.combinations(range(len(cz)), ns):
                best = None
                for perm in itertools.permutations(sub):
                    seq = [dep] + [int(cz[j]) for j in perm] + [dep]
                    tt = sum(_tt(TT, seq[i], seq[i + 1]) for i in range(len(seq) - 1))
                    if best is None or tt < best[0]:
                        best = (tt, perm)
                perm = best[1]
                for t0 in range(H):
                    clock = float(t0)
                    pos = dep
                    stops = []
                    legs = []  # (from zone, to zone, departure period); used only by mfgcc.extern
                    for j in perm:
                        z = int(cz[j])
                        legs.append((pos, z, min(int(clock), H - 1)))
                        clock += _tt(TT, pos, z) * (1 + cong[min(int(clock), H - 1)])
                        if clock >= H:
                            break
                        hour = int(clock)
                        stops.append((z, hour, float(lot[j])))
                        clock += lot[j] * r
                        pos = z
                    if len(stops) < ns:
                        continue
                    legs.append((pos, dep, min(int(clock), H - 1)))
                    clock += _tt(TT, pos, dep) * (1 + cong[min(int(clock), H - 1)])
                    if clock > H + 1e-9:
                        continue
                    dur = clock - t0
                    cols.append((stops, dur, legs))
        raw.append(cols)
        for stops, _, _ in cols:
            for z, hour, _ in stops:
                coord_index.setdefault((z, hour), len(coord_index))
    d = len(coord_index)
    coords = np.array(sorted(coord_index, key=coord_index.get))
    # ---- demand and congestion slopes per coordinate
    zc, hc = coords[:, 0], coords[:, 1]
    Qfull_z = np.zeros(Z)
    for th in range(n_types):
        np.add.at(Qfull_z, custs[th], share * pop[custs[th]] * ppc)
    Qfull = Qfull_z[zc] * psi[hc] / H
    alpha = 1.5 * fee
    b = alpha / (2.0 * np.maximum(Qfull, 1.0))
    bpr_a, bpr_b = P["bpr_alpha"], P["bpr_beta"]
    v0 = (cong[hc] / bpr_a) ** (1.0 / bpr_b)
    dBPR = bpr_a * bpr_b * v0 ** (bpr_b - 1.0)
    v_ff = 600.0 / P["tomtom_min_per_10km"] * (1.0 + cong0)
    Kz = lane[zc] * P["lane_capacity_veh_per_hour"] / v_ff
    mult = pop[zc] * ppc / np.maximum(Qfull_z[zc], 1e-9)  # slice multiplicity (real / modelled deliveries)
    cz = dBPR * pce * mult / Kz  # slowdown per modelled vehicle-hour in the hour
    kappa = kappa_scale * gamma_h * cz * r * r  # kappa_scale != 1 only in the congestion-heavy sensitivity run
    base = []
    for th in range(n_types):
        cols = raw[th]
        rows, cidx, vals = [], [], []
        rev = np.zeros(len(cols))
        cost = np.zeros(len(cols))
        w = np.zeros(len(cols))
        for j, (stops, dur, _) in enumerate(cols):
            for z, hour, q in stops:
                rows.append(coord_index[(z, hour)])
                cidx.append(j)
                vals.append(q)
                rev[j] += alpha * q
            cost[j] = gamma_h * (dur + 1.0)  # one vehicle-hour fixed cost per tour
            w[j] = dur
        L = sp.csr_matrix((vals, (rows, cidx)), shape=(d, len(cols)))
        fleet_vh = fleet_factor * float(np.sum(share * pop[custs[th]] * ppc)) / drops * shift
        base.append(dict(rev=rev, cost=cost, L=L, w=w, B=fleet_vh, depot=depots[th], zones=custs[th],
                         lots=lots[th], tours=[(st, lg) for st, _, lg in cols]))
    am, pm, grade = peak_levels(city, cong0)
    meta = dict(city=city, seed=seed, kappa_scale=kappa_scale, n_types=n_types, n_cust=n_cust, max_stops=max_stops, amp=amp, Z=Z, d=d,
                n_cols=int(sum(len(c) for c in raw)), gamma_h=gamma_h, r=r, fee=fee, cong_allday=cong0,
                cong_am=am, cong_pm=pm, peak_grade=grade, rho=float((kappa / (b + kappa)).max()))
    # per-coordinate population data (used only by the exposure analysis; they do not enter the equilibrium)
    meta.update(pop_c=pop[zc], area_c=zones["area_km2"].to_numpy(float)[zc], mult_c=mult, ppc=float(ppc))
    # city-level data used only by the externality extension (mfgcc.extern); they do not enter the equilibrium
    meta.update(cong=cong, v_ff=v_ff, pop_z=pop, area_z=zones["area_km2"].to_numpy(float), Qfull_z=Qfull_z,
                fuel_l=fuel_l, wage=wage, cap=cap, bpr_beta=bpr_b, pce=pce)
    return CityGame(city, seed, base, coords, b, kappa, alpha, r, gamma_h, meta)


__all__ = ["build", "CityGame", "CITIES", "H"]
