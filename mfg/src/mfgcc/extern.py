"""External costs of delivery driving beyond in-zone congestion: emissions, noise and through-traffic congestion.

The equilibrium model prices congestion only through the in-zone dwell time r Q (kappa Q per delivery; delay
borne by the delivery fleet).  Here every tour j also imposes a cost E_j on third parties that is linear in the
tour's vehicle-km:

    E_j = sum_legs km_leg [e_air + e_clim + e_noise + e_cong(h_leg)] + sum_stops km_stop [e_air + e_clim + e_noise]

  km_leg   inter-zone driving: length of the fastest path on the major road graph of data/processed/<city>
           (major_graph.npz, read only; the same paths as travel_time_matrix.npy) plus an access drive of 120 s at
           each end (the access time of the travel-time matrix) at ACCESS_KMH;
  km_stop  driving between the drops of one stop inside the zone, the Beardwood-Halton-Hammersley approximation
           0.7124 sqrt(area_z * lot) of a tour through `lot` points spread uniformly over the zone;
  e_*      USD per vehicle-km (PARAMS, with sources and grades); e_cong(h) is the marginal external delay that one
           vehicle-km on the major roads imposes on all other traffic under the BPR curve at the hourly congestion
           level cong(h) of the profile: per free-flow hour of the leg on the graph, pce * beta * cong(h) * VOT (the BPR
           marginal external delay; applied to inter-zone legs only, so as not to double count the in-zone congestion kappa, which is internal to the fleet).

Welfare with these externalities: SW_ext = SW - sum_b <E_b, y_b>.  Because E is linear in the tour weights, the
extended problem is the original one with tour profits p - E: a per-tour (distance) charge E plus the per-delivery
congestion charge implements the extended optimum (mean field), and Proposition 20 applies to p - E.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / "mfg" / "results" / "geo"
DIRNAME = {"New Delhi": "NewDelhi", "Mumbai": "Bombay", "Buenos Aires": "BuenosAires", "New York": "NewYork"}

EUR16_USD = 1.285 * 1.122  # euro-area HICP 2016 -> 2025 (Eurostat annual rates, product 1.285) x USD per EUR of
#                            the repository's wage conversion (Paris: EUR 14.01/h = USD 15.72/h); grade B
PARAMS = dict(
    air=0.0219 * EUR16_USD,     # Handbook 2019 Table 19: LCV diesel Euro 6, metropolitan area, urban road, 2.19 EURct/vkm
    air_hi=0.0313 * EUR16_USD,  # same, Euro 4 (older fleets), 3.13 EURct/vkm
    clim=0.0240 * EUR16_USD,    # Handbook 2019 Table 28: LCV diesel Euro 6, urban road, 2.40 EURct/vkm at EUR 100/t CO2e
    clim_hi_factor=240.0 / (100.0 * EUR16_USD),  # US EPA (2023) USD 190/t (2020 USD), about USD 240/t in 2026 USD
    noise=0.017 * EUR16_USD,    # Handbook 2019 Table 37: LCV, day, dense traffic, urban, 1.7 EURct/vkm
    wage_eu=(15.72 + 18.78 + 18.76) / 3.0,  # Paris, Berlin, London driver wages (USD/h): income reference (C)
    access_s=120.0, access_kmh=20.0,        # access drive per trip end (C)
    bhh=0.7124,                              # Beardwood-Halton-Hammersley constant (A, a theorem)
    small_vehicle=1.0 / 3.0,                 # emissions of the small vehicles (van capacity <= 60): fuel ratio 1/3 (C)
)
COMPONENTS = ("air", "clim", "noise", "cong")


# ------------------------------------------------------------------ fastest paths on the major graph
def zone_paths(city: str, refresh: bool = False):
    """Length (km) of the fastest major-road path between zone nodes, and the km driven in every zone on it.

    Cached in mfg/results/geo/<city>.npz (derived from data/processed, which is only read).  Returns dict with
    dist (Z x Z km), time (Z x Z s, graph only) and the sparse allocation alloc[(o, d)] = (zones, km)."""
    from scipy.sparse.csgraph import dijkstra

    d = DIRNAME.get(city, city)
    f = CACHE / f"{d}.npz"
    if f.exists() and not refresh:
        z = np.load(f)
        return dict(dist=z["dist"], time=z["time"], pair=z["pair"], zone=z["zone"], km=z["km"], Z=int(z["Z"]))
    zdir = ROOT / "data" / "processed" / d
    G = np.load(zdir / "major_graph.npz")
    zones = pd.read_csv(zdir / "zones.csv")
    bnd = np.load(zdir / "zone_bounds.npy")  # lon_min, lat_min, lon_max, lat_max per zone
    Z = len(zones)
    n = len(G["lon"])
    src, dst = G["src"].astype(np.int64), G["dst"].astype(np.int64)
    t, ln = G["time_s"].astype(np.float64), G["length_m"].astype(np.float64)
    rows, cols = np.concatenate([src, dst]), np.concatenate([dst, src])
    Gt = sp.csr_matrix((np.concatenate([t, t]), (rows, cols)), shape=(n, n))
    key = rows * n + cols
    o = np.argsort(key)
    key, lens = key[o], np.concatenate([ln, ln])[o]
    lon, lat = G["lon"], G["lat"]
    nz = np.full(n, -1, np.int64)
    for zi in range(Z):
        msk = (lon >= bnd[zi, 0]) & (lon < bnd[zi, 2]) & (lat >= bnd[zi, 1]) & (lat < bnd[zi, 3])
        nz[msk & (nz < 0)] = zi
    znode = zones["node"].to_numpy(np.int64)
    dist = np.zeros((Z, Z))
    tim = np.zeros((Z, Z))
    P_, Zo, K_ = [], [], []
    for s0 in range(0, Z, 16):
        idx = znode[s0:s0 + 16]
        dd, pred = dijkstra(Gt, directed=True, indices=idx, return_predecessors=True)
        for a, srcnode in enumerate(idx):
            oz = s0 + a
            for dz in range(Z):
                if dz == oz:
                    continue
                v = znode[dz]
                path = [v]
                while v != srcnode:
                    v = pred[a, v]
                    if v < 0:
                        break
                    path.append(v)
                path = np.array(path[::-1], np.int64)
                kk = path[:-1] * n + path[1:]
                el = lens[np.searchsorted(key, kk)] / 1000.0
                tim[oz, dz] = dd[a, znode[dz]]
                dist[oz, dz] = el.sum()
                ez = nz[path[:-1]]
                ok = ez >= 0
                if ok.any():
                    acc = np.bincount(ez[ok], weights=el[ok], minlength=Z)
                    nzz = np.nonzero(acc)[0]
                    P_.append(np.full(len(nzz), oz * Z + dz, np.int32))
                    Zo.append(nzz.astype(np.int16))
                    K_.append(acc[nzz].astype(np.float32))
    CACHE.mkdir(parents=True, exist_ok=True)
    out = dict(dist=dist, time=tim, pair=np.concatenate(P_), zone=np.concatenate(Zo), km=np.concatenate(K_), Z=Z)
    np.savez_compressed(f, **out)
    return out


def _alloc_lookup(geo):
    """dict (o, d) -> (zones, km) from the cached COO arrays."""
    Z = geo["Z"]
    pair = geo["pair"].astype(np.int64)
    order = np.argsort(pair, kind="stable")
    pair, zone, km = pair[order], geo["zone"][order].astype(np.int64), geo["km"][order].astype(float)
    cut = np.flatnonzero(np.diff(pair)) + 1
    starts = np.concatenate([[0], cut])
    ends = np.concatenate([cut, [len(pair)]])
    return {(int(pair[s] // Z), int(pair[s] % Z)): (zone[s:e], km[s:e]) for s, e in zip(starts, ends)}


# ------------------------------------------------------------------ external cost per vehicle-km and per tour
def rates(g, variant: str = "base") -> dict:
    """USD per vehicle-km for the city of instance g.  Variants: base; eu (no income transfer); hi (Euro 4 air
    pollution, EPA carbon value, through congestion as in base); nocong (no through congestion)."""
    P = PARAMS
    M = g.meta
    inc = 1.0 if variant == "eu" else M["wage"] / P["wage_eu"]  # unit-value transfer, income elasticity 1 (C)
    veh = P["small_vehicle"] if M["cap"] <= 60 else 1.0
    air = (P["air_hi"] if variant == "hi" else P["air"]) * inc * veh
    clim = P["clim"] * veh * (P["clim_hi_factor"] if variant == "hi" else 1.0)
    noise = P["noise"] * inc
    vot = M["wage"]  # value of a vehicle-hour of other traffic: driver wage (C)
    cong = M["pce"] * M["bpr_beta"] * M["cong"] * vot  # (H,) USD per free-flow vehicle-hour on the major roads
    if variant == "nocong":
        cong = 0.0 * cong
    return dict(air=air, clim=clim, noise=noise, cong=cong, inc=inc, veh=veh)


def tour_externalities(g, variant: str = "base", geo=None) -> list:
    """Per segment (base block) a dict with, per tour: vkm (inter-zone and in-zone), the external cost of each
    component (USD per tour) and E (their sum), plus the sparse matrix K (Z x tours) of vkm driven in each zone."""
    geo = zone_paths(g.city) if geo is None else geo
    alloc = geo.get("_alloc") or _alloc_lookup(geo)
    geo["_alloc"] = alloc
    rt = rates(g, variant)
    P = PARAMS
    acc = P["access_s"] / 3600.0 * P["access_kmh"]
    area = g.meta["area_z"]
    Z = len(area)
    base_rate = rt["air"] + rt["clim"] + rt["noise"]
    out = []
    for Bd in g.base:
        nt = len(Bd["tours"])
        comp = {c: np.zeros(nt) for c in COMPONENTS}
        vk_leg, vk_in = np.zeros(nt), np.zeros(nt)
        rows, cols, vals = [], [], []
        for j, (stops, legs) in enumerate(Bd["tours"]):
            for a, b2, h in legs:
                km = geo["dist"][a, b2] + 2.0 * acc
                vk_leg[j] += km
                comp["cong"][j] += geo["time"][a, b2] / 3600.0 * rt["cong"][h]
                for c in ("air", "clim", "noise"):
                    comp[c][j] += km * rt[c]
                zz, kk = alloc.get((a, b2), (np.zeros(0, int), np.zeros(0)))
                rows += list(zz) + [a, b2]
                cols += [j] * (len(zz) + 2)
                vals += list(kk) + [acc, acc]
            for z, _, lot in stops:
                km = P["bhh"] * np.sqrt(area[z] * lot)
                vk_in[j] += km
                for c in ("air", "clim", "noise"):
                    comp[c][j] += km * rt[c]
                rows.append(z)
                cols.append(j)
                vals.append(km)
        K = sp.csr_matrix((vals, (rows, cols)), shape=(Z, nt))
        E = sum(comp[c] for c in COMPONENTS)
        out.append(dict(vkm_leg=vk_leg, vkm_in=vk_in, comp=comp, E=E, K=K))
    _ = base_rate
    return out


def ext_blocks(g, k, ext, charge_tours: bool):
    """Replica blocks of instance g with k carriers per segment; with charge_tours the carriers pay E per tour
    (tour profits p - E), which is the extended social problem when the city levies the distance charge."""
    from .qp import Block
    out = []
    for th, (Bd, ex) in enumerate(zip(g.base, ext)):
        p = Bd["rev"] - Bd["cost"] - (ex["E"] if charge_tours else 0.0)
        out.append(Block(p, Bd["L"], Bd["w"], Bd["B"], count=k, tag=f"t{th}"))
    return out


def external_cost(sol, ext) -> dict:
    """Total external cost of a profile by component, vkm, and the per-delivery allocation e_k (each tour's E spread
    over its deliveries in proportion to lots)."""
    out = {c: float(sum(ex["comp"][c] @ y for ex, y in zip(ext, sol.y))) for c in COMPONENTS}
    out["E"] = sum(out[c] for c in COMPONENTS)
    out["vkm"] = float(sum((ex["vkm_leg"] + ex["vkm_in"]) @ y for ex, y in zip(ext, sol.y)))
    out["vkm_in"] = float(sum(ex["vkm_in"] @ y for ex, y in zip(ext, sol.y)))
    return out


def per_delivery_external(blocks, sol, ext) -> np.ndarray:
    """e_k: external cost of the tours that deliver at coordinate k, per delivery made there (tour cost split over
    the tour's deliveries in proportion to its lots).  Zero where nothing is delivered."""
    d = len(sol.Q)
    num = np.zeros(d)
    for B, y, ex in zip(blocks, sol.y, ext):
        q = np.asarray(B.L.sum(axis=0)).ravel()
        share = ex["E"] * y / np.maximum(q, 1e-12)  # external cost per delivery of each tour, times tour weight
        num += B.L @ share
    return np.where(sol.Q > 1e-12, num / np.maximum(sol.Q, 1e-12), 0.0)


def zone_vkm(g, sol, ext, scale: float = 1.0) -> np.ndarray:
    return scale * np.asarray(sum(ex["K"] @ y for ex, y in zip(ext, sol.y))).ravel()


def real_scale(g) -> float:
    """Real over modelled deliveries in the customer zones (one factor per instance)."""
    Qz = g.meta["Qfull_z"]
    cz = Qz > 0
    return float(np.sum(g.meta["pop_z"][cz] * g.meta["ppc"]) / np.sum(Qz[cz]))
