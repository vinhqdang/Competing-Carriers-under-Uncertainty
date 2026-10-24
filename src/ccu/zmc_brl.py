"""ZMC + BRL integration: the aggregative Cournot-congestion game whose carrier oracle is a BRL column-generation /
price-and-branch solve of the carrier's routing plan under p-box travel times (see docs/EXPERIMENTS.md, Section 2).

Game (D1, main.tex Example 2.2 with costs instead of profits).  Zones z = 0..Z-1, coordinates a = (q_z, tau_z):
deliveries and vehicle-hours.  A carrier i has n customer zones (nodes 1..n of its routing instance) and decides
which of them to serve (all-or-nothing lots of d_iz deliveries) and how to route them (routes of one depot).  Its
cost is

    J_i(p; A_-i) = c_i(p) + <a_i(p), M A_-i>,   M = diag(b_z, gc_z),
    c_i(p)       = sum_r c_r  +  sum_{z served} [ -alpha_z d + b_z d^2 + gc_z h^2 + (toll + sur) . a_z ],

with c_r the upper expectation of the route loss under p-box travel times and unknown dependence (BRL, Thm 2.1),
d the lot size, h = d * h_drop the vehicle-hours attributed to the lot, toll the leader's charges (transfers) and sur
the Gamma-maximin ambiguity surcharge delta * M_k * w_k of main.tex Lemma 3.6.  Because a served zone is visited once,
the quadratic own terms are linear in the service indicator, so the whole carrier problem is a prize-collecting
set-packing problem with additive node costs, which is exactly what `ccu.brl.RoutePool` solves.

Approximations (all listed again in docs/EXPERIMENTS.md):
  A1  all-or-nothing lots (no partial service of a customer zone);
  A2  the carrier oracle is column generation with exact BRL pricing + integer packing over the generated columns
      (price-and-branch, no branching).  The LP value is a lower bound, so every oracle answer carries a gap;
  A3  vehicle-hours that create congestion are the in-zone hours of the lots (service plus local circulation), not
      the inter-zone driving, which is priced through the p-box route loss only;
  A4  the congestion externality enters linearly (cost gamma*tau*(xi + c_z X_z)); xi is inside the p-box.
"""
from __future__ import annotations

import copy
import csv
import itertools
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import bp, brl

ROOT = Path(__file__).resolve().parents[2]
CITIES = ["NewDelhi", "Cairo", "Moscow", "BuenosAires", "NewYork", "Bombay", "London", "Paris", "Berlin"]
WIDE_NAME = {"NewDelhi": "New Delhi", "Bombay": "Mumbai", "BuenosAires": "Buenos Aires", "NewYork": "New York"}
# five weakest numbers used for the sensitivity runs (SOURCES.md: flagged weak(C) for most cities, wide ranges)
WEAK_PARAMS = ["delivery_fee_usd", "driver_wage_usd_per_hour", "drops_per_vehicle_per_day",
               "parcels_per_capita_per_day", "n_major_carriers"]

# market shares from data/parameters/city_parameters.csv (rows carrier_market_shares); None = not available
MARKET_SHARES = {
    "Paris": [0.50, 0.15, 0.14, 0.105, 0.105],  # La Poste ~50%, Amazon 15%, Mondial Relay 14%; rest split equally
    "Berlin": [0.42, 0.175, 0.10, 0.10, 0.10, 0.10],  # DHL >40%, Amazon 15-20%, four others 5-15% (midpoints)
}


# ---------------------------------------------------------------------------------------------------------------
# data access
# ---------------------------------------------------------------------------------------------------------------


def load_wide(city: str) -> dict:
    name = WIDE_NAME.get(city, city)
    with open(ROOT / "data/parameters/city_parameters_wide.csv") as fh:
        for r in csv.DictReader(fh):
            if r["city"] == name:
                return {k: float(v) for k, v in r.items() if k not in ("city", "flags")}
    raise KeyError(city)


def load_ranges() -> dict:
    """{parameter: {city display name: (low, base, high)}} parsed from the tables of data/parameters/SOURCES.md."""
    txt = (ROOT / "data/parameters/SOURCES.md").read_text()
    out: dict = {}
    cur = None
    for line in txt.splitlines():
        m = re.match(r"^### (\w+)", line)
        if m:
            cur = m.group(1)
            out[cur] = {}
            continue
        if line.startswith("## "):
            cur = None
        if cur and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4:
                try:
                    out[cur][cells[0]] = (float(cells[1]), float(cells[2]), float(cells[3]))
                except ValueError:
                    pass
    return out


def peak_congestion(city: str, default: float) -> float:
    name = WIDE_NAME.get(city, city)
    with open(ROOT / "data/parameters/city_parameters.csv") as fh:
        for r in csv.DictReader(fh):
            if r["city"] == name and r["parameter"] == "tomtom_peak_hour_congestion_pct":
                try:
                    return float(r["value"]) / 100.0
                except ValueError:
                    pass
    return default


def _kmeans(X, K, rng, it=50):
    C = X[rng.choice(len(X), K, replace=False)]
    for _ in range(it):
        lab = np.argmin(((X[:, None] - C[None]) ** 2).sum(-1), 1)
        C = np.array([X[lab == k].mean(0) if np.any(lab == k) else C[k] for k in range(K)])
    return lab, C


# ---------------------------------------------------------------------------------------------------------------
# game objects
# ---------------------------------------------------------------------------------------------------------------


@dataclass
class Plan:
    routes: tuple  # tuple of routes, each a tuple of global zone ids
    q: np.ndarray  # (Z,) deliveries
    a: np.ndarray  # (2Z,) contribution (q, tau)
    c: float  # carrier cost c_i(p) including charges and surcharge
    cr: float  # sum of route losses
    lb: float = -math.inf  # certified lower bound of the oracle objective that produced it (if any)

    def key(self):
        return tuple(sorted(self.routes))


@dataclass
class CarrierData:
    depot: int
    zones: np.ndarray  # (n,) global zone ids of nodes 1..n
    d: np.ndarray  # (n,) lot sizes (deliveries)
    h: np.ndarray  # (n,) vehicle-hours of the lot
    inst: brl.RoutingInstance
    pool: brl.RoutePool
    share: float = 1.0


class RoutingGame:
    """Aggregative game with BRL carrier oracle.  `mode='ne'` is the Cournot-congestion game, `mode='so'` the
    social-cost potential (same carriers and pools) used for the convexified optimum."""

    def __init__(self, Z, carriers, alpha, b, gc, gamma_h, bg=None, name="game", meta=None, mode="ne"):
        self.Z = Z
        self.carriers = carriers
        self.alpha = np.asarray(alpha, float)
        self.b = np.asarray(b, float)
        self.gc = np.asarray(gc, float)
        self.gamma_h = float(gamma_h)
        self.bg = np.zeros(Z) if bg is None else np.asarray(bg, float)  # background-delay cost per unit X_z
        self.name = name
        self.meta = meta or {}
        self.mode = mode
        self.toll = np.zeros(2 * Z)
        self.sur = np.zeros(2 * Z)
        self.calls = 0
        self.lp_gap_max = 0.0
        self.invalid_bounds = 0
        self.bp_time = None  # per-call time limit (s) of the exact branch-and-price integer step; None = price-and-branch
        self.bp_calls = self.bp_optimal = self.bp_timeouts = self.bp_nodes = 0
        self.bp_max_gap = 0.0
        self.bp_time_used = 0.0
        self.ng_size = None
        self.so_broad = False
        self._cache = {}
        self._full = [self._make_full(i) for i in range(self.N)]

    # -------------------------------------------------------------- basic
    @property
    def N(self):
        return len(self.carriers)

    @property
    def d(self):
        return 2 * self.Z

    @property
    def M(self):
        gc = self.gc if self.mode == "ne" else 2.0 * self.gc
        return np.concatenate([self.b, gc])

    def so_variant(self, broad: bool = False) -> "RoutingGame":
        """Social-cost potential (convexified optimum, E3).  broad=True adds the background-delay cost bg_z X_z."""
        g = copy.copy(self)
        g.mode = "so"
        g.so_broad = broad
        g.calls = 0
        g._cache = {}
        return g

    def set_charges(self, toll=None, sur=None):
        self.toll = np.zeros(2 * self.Z) if toll is None else np.asarray(toll, float).copy()
        self.sur = np.zeros(2 * self.Z) if sur is None else np.asarray(sur, float).copy()

    def _make_full(self, i):
        cr = self.carriers[i]
        a = np.zeros(2 * self.Z)
        a[cr.zones] = cr.d
        a[self.Z + cr.zones] = cr.h
        return a

    def full_a(self, i):
        return self._full[i]

    # -------------------------------------------------------------- plans
    def _plan_from_nodes(self, i, node_routes, lb=-math.inf) -> Plan:
        cr = self.carriers[i]
        Z = self.Z
        q = np.zeros(Z)
        tau = np.zeros(Z)
        routes = []
        route_cost = 0.0
        for r in node_routes:
            routes.append(tuple(int(cr.zones[j - 1]) for j in r))
            route_cost += cr.pool.cols[tuple(r)] if tuple(r) in cr.pool.cols else cr.inst.route_cost(tuple(r))
            for j in r:
                q[cr.zones[j - 1]] += cr.d[j - 1]
                tau[cr.zones[j - 1]] += cr.h[j - 1]
        return self._plan(i, tuple(routes), q, tau, route_cost, lb)

    def _plan(self, i, routes, q, tau, route_cost, lb=-math.inf) -> Plan:
        a = np.concatenate([q, tau])
        if self.mode == "ne":
            c = route_cost + float(np.sum(-self.alpha * q + self.b * q * q + self.gc * tau * tau)) \
                + float((self.toll + self.sur) @ a)
        else:  # social-cost potential: ctilde = routing - alpha q  (own terms are inside 1/2 ||A||^2_M)
            c = route_cost + float(np.sum(-self.alpha * q))
            if self.so_broad:
                c += float(np.sum(self.bg * tau))
        return Plan(routes, q, a, c, route_cost, lb)

    def empty_plan(self, i) -> Plan:
        return self._plan(i, (), np.zeros(self.Z), np.zeros(self.Z), 0.0)

    def plan_from_routes(self, i, zone_routes) -> Plan:
        """Rebuild a plan from routes given as tuples of global zone ids."""
        cr = self.carriers[i]
        idx = {int(z): j + 1 for j, z in enumerate(cr.zones)}
        return self._plan_from_nodes(i, [tuple(idx[z] for z in r) for r in zone_routes])

    # -------------------------------------------------------------- oracle
    def _kappa(self, i, lam, rho):
        cr = self.carriers[i]
        z = cr.zones
        Z = self.Z
        Me = self.M
        own = 0.5 * (1.0 - rho) if self.mode == "so" else 0.5 * (2.0 - rho)  # so: rho=1 pricing, rho=0 coordinate step
        k = own * (Me[z] * cr.d ** 2 + Me[Z + z] * cr.h ** 2)
        if self.mode == "ne":
            k = k - self.alpha[z] * cr.d + (self.toll[z] + self.sur[z]) * cr.d \
                + (self.toll[Z + z] + self.sur[Z + z]) * cr.h
        else:
            k = k - self.alpha[z] * cr.d
            if self.so_broad:
                k = k + self.bg[z] * cr.h
        k = k + lam[z] * cr.d + lam[Z + z] * cr.h
        return np.concatenate([[0.0], k])

    PRICE_GAP = 5e-3  # relative MIP gap of the integer step in pricing calls (rho = 1); best responses are solved to 1e-7

    def oracle(self, i, lam, rho=1.0, count=True, fresh=False, integer=True) -> Plan:
        """argmin_p ctilde_i(p) + <lam, a_i(p)>  (rho = 1);  rho = 0: c_i(p) + <lam, a_i(p)> (best response)."""
        if count:
            self.calls += 1
        cr = self.carriers[i]
        kap = self._kappa(i, np.asarray(lam, float), rho)
        gap = self.PRICE_GAP if rho == 1.0 else 1e-7
        ck = None
        if not fresh:
            ck = (i, kap.tobytes(), gap)
            hit = self._cache.get(ck)
            if hit is not None:
                return hit
        if fresh:
            pool = brl.RoutePool(cr.inst, ng_size=cr.inst.n)  # elementary routes, empty pool
        else:
            pool = cr.pool
        if self.bp_time and integer:
            # exact integer step (ccu.bp): branch-and-price on the pool columns; res.lp is the global lower bound
            res = bp.solve_pool_bp(pool, kap, time_limit=self.bp_time, gap_tol=(gap if rho == 1.0 else 1e-8),
                                   mip_time=min(5.0, self.bp_time))
            self.bp_calls += 1
            self.bp_optimal += int(res.status == "optimal")
            self.bp_timeouts += int(res.status != "optimal")
            self.bp_nodes += res.nodes
            self.bp_max_gap = max(self.bp_max_gap, res.value - res.lp)
            self.bp_time_used += res.pricing_time
        else:
            res = pool.solve(kap, integer=integer, mip_gap=gap, mip_time=(4.0 if rho == 1.0 else 20.0))
        if fresh:  # inject the independent columns so that the pooled oracle can reproduce an improvement
            for r in pool.cols:
                cr.pool._add(r)
            self._cache.clear()  # earlier answers may be stale w.r.t. the enlarged pool
        if res.bound_valid:
            self.lp_gap_max = max(self.lp_gap_max, res.value - res.lp)
        else:
            self.invalid_bounds += 1
        p = self._plan_from_nodes(i, res.routes, lb=res.lp if res.bound_valid else -math.inf)
        p.value_lb = res.lp if res.bound_valid else -math.inf  # lower bound on min of the oracle objective
        p.value = res.value
        if ck is not None:
            if len(self._cache) > 4000:
                self._cache.clear()
            self._cache[ck] = p
        return p

    # -------------------------------------------------------------- game quantities
    def J(self, i, p, A_minus):
        if self.mode == "so":  # coordinate step of the social potential: ctilde + <a, M A_-i> + 1/2 ||a||_M^2
            return p.c + float(p.a @ (self.M * A_minus)) + 0.5 * float(p.a @ (self.M * p.a))
        return p.c + float(p.a @ (self.M * A_minus))

    def br(self, i, A_minus, count=True):
        return self.oracle(i, self.M * A_minus, rho=0.0, count=count)

    def ctilde(self, p):
        if self.mode == "so":
            return p.c
        return p.c - 0.5 * float(p.a @ (self.M * p.a))

    def potential(self, prof):
        A = sum(p.a for p in prof)
        M = self.M
        if self.mode == "so":
            return sum(p.c for p in prof) + 0.5 * float(A @ (M * A))
        return sum(p.c for p in prof) + 0.5 * float(A @ (M * A)) - 0.5 * sum(float(p.a @ (M * p.a)) for p in prof)

    def regrets(self, prof, count=False, fresh=False):
        """Oracle regret of every carrier (best response value computed with the oracle, optionally a fresh pool)."""
        A = sum(p.a for p in prof)
        out = np.zeros(self.N)
        lbr = np.zeros(self.N)
        for i, p in enumerate(prof):
            Am = A - p.a
            b = self.oracle(i, self.M * Am, rho=0.0, count=count, fresh=fresh)
            out[i] = max(0.0, self.J(i, p, Am) - self.J(i, b, Am))
            lbj = getattr(b, "value_lb", -math.inf)
            lbr[i] = max(0.0, self.J(i, p, Am) - lbj) if np.isfinite(lbj) else np.nan
        self._last_regret_lp = lbr
        return out

    # -------------------------------------------------------------- outcome metrics
    def evaluate(self, prof) -> dict:
        Z = self.Z
        q = sum(p.q for p in prof)
        X = sum(p.a[Z:] for p in prof)
        qfull = sum(self._full[i][:Z] for i in range(self.N))
        price = np.where(q > 0, self.alpha - self.b * q, np.nan)
        cz = self.gc / self.gamma_h
        slow = cz * X
        route = sum(p.cr for p in prof)
        cs = float(np.sum(self.alpha * q - 0.5 * self.b * q * q))
        cong = float(np.sum(self.gc * X * X))
        W = cs - cong - route  # welfare, charges are transfers
        profits, revs, charges = [], [], []
        for p in prof:
            rev = float(np.sum(p.q * (self.alpha - self.b * q)))
            cg = float(np.sum(self.gc * p.a[Z:] * X))
            ch = float(self.toll @ p.a)
            profits.append(rev - cg - p.cr - ch)
            revs.append(rev)
            charges.append(ch)
        bgc = float(np.sum(self.bg * X))
        act = qfull > 0
        access = np.where(act, q / np.where(act, qfull, 1.0), np.nan)
        return dict(
            deliveries=float(q.sum()), demand=float(qfull.sum()), served_share=float(q.sum() / max(qfull.sum(), 1e-12)),
            vehicles=int(sum(len(p.routes) for p in prof)), vehicle_hours=float(X.sum()),
            mean_price=float(np.nansum(np.where(q > 0, price * q, 0.0)) / max(q.sum(), 1e-12)),
            mean_slowdown=float((slow * X).sum() / max(X.sum(), 1e-12)), max_slowdown=float(slow.max()),
            profit_total=float(sum(profits)), profits=profits, charges=float(sum(charges)),
            social_cost=-W, welfare=W, consumer_surplus=cs, congestion_cost=cong, routing_cost=route,
            bg_delay_cost=bgc, social_cost_broad=-W + bgc,
            gini_access=gini(access[act]), gini_price=gini(price[q > 0]),
            q_z=q, X_z=X, price_z=price, slow_z=slow, access_z=access)

    def exposure_of(self, prof):
        return sum(p.a for p in prof)


def gini(x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) == 0 or x.sum() <= 0:
        return float("nan")
    x = np.sort(x)
    n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1) @ x / (n * x.sum()))


# ---------------------------------------------------------------------------------------------------------------
# city builder
# ---------------------------------------------------------------------------------------------------------------


def build_city_game(city: str, *, overrides: dict | None = None, n_cust: int = 12, K: int = 9, ndays: int = 30,
                    alpha_dkw: float = 0.05, seed: int = 0, ng_size: int = 8, min_sep_km: float = 3.0,
                    pce: float = 1.5, bg_hours: float = 1.0, reach: float = 0.4, N_override: int | None = None) -> RoutingGame:
    """Calibrated game on a real city map.

    Reused conventions: p-box construction, sectors, loss (fixed 2, gamma 1, rho 3 driver-hour units, shift deadline)
    from theory/new_algorithm_B/real_instances.py; inverse demand alpha = 1.5 * fee, b = alpha / (2 * full demand)
    from theory/new_algorithm_A/core.py; depots from geo.select_depot_sites.
    New assumptions are flagged NEW in the comments and listed in docs/EXPERIMENTS.md.
    """
    from .geo import select_depot_sites

    rng = np.random.default_rng(seed)
    P = load_wide(city)
    if overrides:
        P.update(overrides)
    N = int(round(P["n_major_carriers"])) if N_override is None else N_override
    zdir = ROOT / "data/processed" / city
    zones = pd.read_csv(zdir / "zones.csv")
    TT = np.load(zdir / "travel_time_matrix.npy").astype(float)  # seconds
    Z = len(zones)
    pop = np.maximum(zones["pop"].to_numpy(float), 0.0)
    lane = np.maximum(zones["lane_km_major"].to_numpy(float), 1.0)
    ppc, drops, shift = P["parcels_per_capita_per_day"], P["drops_per_vehicle_per_day"], P["shift_hours"]
    fee, wage, fuel = P["delivery_fee_usd"], P["driver_wage_usd_per_hour"], P["fuel_usd_per_litre"]
    cong = P["tomtom_congestion_pct"] / 100.0
    cap = P["van_capacity_parcels"]

    # ---- carriers: shares, depots, customer zones
    share = np.array(MARKET_SHARES.get(city, []), float) if overrides is None or "n_major_carriers" not in overrides else np.array([])
    if len(share) != N:
        share = np.full(N, 1.0 / N)
    share = share / share.sum()
    sites = select_depot_sites(zones[["zone_id", "lon", "lat", "depot_score", "pop"]], N, rng, min_sep_km)
    if len(sites) < N:  # NEW: pad with the next best-scored unused zones
        order = [int(z) for z in np.argsort(-zones["depot_score"].to_numpy()) if int(z) not in set(sites.tolist())]
        sites = np.concatenate([sites, np.array(order[: N - len(sites)], dtype=np.int64)])
    depots = [int(z) for z in sites[:N]]
    custs, parc = [], []
    for i in range(N):
        t = TT[depots[i]]
        w = pop * np.exp(-t / max(np.percentile(t, 100.0 * reach), 1.0))  # NEW: gravity sampling around the depot
        w[depots[i]] = 0.0
        w = np.where(pop > 0, w, 0.0)
        k = min(n_cust, int((w > 0).sum()))
        c = np.sort(rng.choice(Z, k, replace=False, p=w / w.sum()))
        custs.append(c)
        parc.append(share[i] * pop[c] * ppc)
    q90 = float(np.quantile(np.concatenate(parc), 0.9))
    dmax = max(3, int(round(0.5 * drops)))
    dmin = max(2, int(round(0.1 * drops)))
    # ---- unit costs  (NEW: fuel burn 1 L/h for two-wheeler classes (van capacity <= 60), 3 L/h otherwise)
    fuel_l = 1.0 if cap <= 60 else 3.0
    gamma_h = wage + fuel_l * fuel  # USD per vehicle-hour
    h_drop = 0.6 * shift / drops  # NEW: in-zone hours per delivery = 0.6 of the time budget per drop
    # ---- sectors and p-box (conventions of real_instances.build)
    allp = []
    peak = peak_congestion(city, np.nan)
    if not np.isfinite(peak):
        vals = [peak_congestion(c, np.nan) for c in CITIES]
        peak = float(np.nanmean(vals))
    xy = zones[["lon", "lat"]].to_numpy(float)
    lab, C = _kmeans((xy - xy.mean(0)) / xy.std(0), K, rng)
    cen = np.linalg.norm(C, axis=1)
    m = 1 + cong * (1.15 - 0.3 * (cen - cen.min()) / (np.ptp(cen) + 1e-12))
    target = math.log((1 + peak) / (1 + cong))
    s = 1.645 - math.sqrt(max(1.645 ** 2 - 2 * target, 0.0))
    sc, ss = 0.7 * s, math.sqrt(max(s * s - (0.7 * s) ** 2, 0.0))
    g_ = rng.standard_normal((ndays, 1))
    e_ = rng.standard_normal((ndays, K))
    days = m[None] * np.exp(sc * g_ + ss * e_ - 0.5 * (sc * sc + ss * ss))
    xmax = 1 + 2 * peak
    qfs = [brl.dkw_upper_quantile(days[:, k], alpha_dkw, xmax) for k in range(K)]
    _, wl, Qk = brl.common_grid(qfs)
    loss = brl.Loss(gamma=gamma_h / 3600.0, rho=3.0 * gamma_h / 3600.0, Tmax=shift * 3600.0, fixed=2.0 * gamma_h)
    carriers = []
    Xfull = np.zeros(Z)
    Qfull = np.zeros(Z)
    for i in range(N):
        c = custs[i]
        d = np.clip(np.round(dmax * parc[i] / q90), dmin, dmax)
        h = d * h_drop
        nodes = np.concatenate([[depots[i]], c])
        n = len(c)
        tau = np.zeros((n + 1, n + 1, K))
        for a in range(n + 1):
            for b2 in range(n + 1):
                if a != b2:
                    t = TT[nodes[a], nodes[b2]]
                    tau[a, b2, lab[nodes[a]]] += t / 2
                    tau[a, b2, lab[nodes[b2]]] += t / 2
        svc = np.concatenate([[0.0], h * 3600.0])
        dem = np.concatenate([[0.0], d])
        inst = brl.RoutingInstance(n, tau, svc, dem, float(cap), Qk, wl, loss)
        pool = brl.RoutePool(inst, ng_size=ng_size)
        carriers.append(CarrierData(depots[i], c, d, h, inst, pool, share[i]))
        np.add.at(Xfull, c, h)
        np.add.at(Qfull, c, d)
    # ---- inverse demand (core.py convention) and BPR congestion slope (NEW calibration, see docs)
    alpha = np.full(Z, 1.5 * fee)
    b = alpha / (2.0 * np.maximum(Qfull, 1.0))
    bpr_a, bpr_b = P["bpr_alpha"], P["bpr_beta"]
    v0 = (cong / bpr_a) ** (1.0 / bpr_b)  # v/C ratio at which BPR reproduces the TomTom all-day congestion
    dBPR = bpr_a * bpr_b * v0 ** (bpr_b - 1.0)  # d(multiplier)/d(v/C)
    v_ff = 600.0 / P["tomtom_min_per_10km"] * (1.0 + cong)  # km/h
    Kz = lane * P["lane_capacity_veh_per_hour"] / v_ff  # vehicles on the major network at capacity density
    H_real = pop * ppc * h_drop  # real delivery vehicle-hours per day in the zone
    mz = np.where(Xfull > 0, H_real / np.maximum(Xfull, 1e-12), 0.0)  # representative-slice multiplicity
    cz = dBPR * pce * mz / (shift * Kz)  # slowdown per sample vehicle-hour
    gc = np.where(Xfull > 0, gamma_h * cz, 1e-9)
    veh_bg = pop * P["vehicles_per_1000_people"] / 1000.0 * bg_hours  # background vehicle-hours per day
    bg = np.where(Xfull > 0, wage * veh_bg / np.maximum(mz, 1e-12) * cz, 0.0)
    meta = dict(city=city, N=N, Z=Z, depots=depots, n_cust=[len(c) for c in custs], seed=seed, alpha_dkw=alpha_dkw,
                L=int(len(wl)), gamma_h=gamma_h, h_drop=h_drop, params=P, d_eff=int((Xfull > 0).sum()),
                overlap=float(np.mean([np.mean([(Qfull[z] > carriers[i].d[j]) for j, z in enumerate(carriers[i].zones)])
                                       for i in range(N)])), full_slowdown=float((cz * Xfull)[Xfull > 0].mean()),
                share=share.tolist(), peak=peak, ndays=ndays, K=K, ng_size=ng_size)
    g = RoutingGame(Z, carriers, alpha, b, gc, gamma_h, bg=bg, name=city, meta=meta)
    g.ng_size = ng_size
    return g


# ---------------------------------------------------------------------------------------------------------------
# tiny synthetic games (tests, exhaustive enumeration)
# ---------------------------------------------------------------------------------------------------------------


def make_tiny_game(N=2, Z=5, n_cust=3, seed=0, K=2, ndays=20, alpha_dkw=0.2, cap=None, overlap=True) -> RoutingGame:
    """Small random game on a synthetic plane (for tests): same cost structure as the city games."""
    rng = np.random.default_rng(seed)
    xy = rng.uniform(0, 1, (Z, 2))
    TT = np.linalg.norm(xy[:, None] - xy[None], axis=-1) * 3000.0 + 300.0  # seconds
    np.fill_diagonal(TT, 0.0)
    sec = (xy[:, 0] > 0.5).astype(int) % K
    days = np.exp(0.25 * rng.standard_normal((ndays, 1)) + 0.15 * rng.standard_normal((ndays, K))) * 1.3
    qfs = [brl.dkw_upper_quantile(days[:, k], alpha_dkw, 3.0) for k in range(K)]
    _, wl, Qk = brl.common_grid(qfs)
    gamma_h = 10.0
    loss = brl.Loss(gamma_h / 3600.0, 3 * gamma_h / 3600.0, 3.0 * 3600.0, 2 * gamma_h)
    carriers = []
    Qfull = np.zeros(Z)
    for i in range(N):
        depot = int(rng.integers(Z))
        pool_z = [z for z in range(Z) if z != depot]
        c = np.sort(rng.choice(pool_z, n_cust, replace=False))
        d = rng.integers(3, 7, n_cust).astype(float)
        h = d * 0.08
        nodes = np.concatenate([[depot], c])
        n = len(c)
        tau = np.zeros((n + 1, n + 1, K))
        for a in range(n + 1):
            for b2 in range(n + 1):
                if a != b2:
                    t = TT[nodes[a], nodes[b2]]
                    tau[a, b2, sec[nodes[a]]] += t / 2
                    tau[a, b2, sec[nodes[b2]]] += t / 2
        svc = np.concatenate([[0.0], h * 3600.0])
        dem = np.concatenate([[0.0], d])
        inst = brl.RoutingInstance(n, tau, svc, dem, float(cap or 9.0), Qk, wl, loss)
        carriers.append(CarrierData(depot, c, d, h, inst, brl.RoutePool(inst, ng_size=n), 1.0 / N))
        np.add.at(Qfull, c, d)
    alpha = np.full(Z, 12.0)
    b = alpha / (2.0 * np.maximum(Qfull, 1.0)) * rng.uniform(0.8, 1.6, Z)
    gc = rng.uniform(0.3, 1.5, Z)
    return RoutingGame(Z, carriers, alpha, b, gc, gamma_h, bg=np.zeros(Z), name=f"tiny{seed}")


def served_set_costs(g: RoutingGame, i: int):
    """Exact (enumerated) minimal route loss for every subset of customer nodes of carrier i (partition DP)."""
    cr = g.carriers[i]
    n = cr.inst.n
    best = brl.enumerate_best_routes(cr.inst)
    sub = {0: 0.0}
    keys = list(best)
    full = (1 << n) - 1
    rc = {fs: best[fs][0] for fs in keys}
    mask_cost = {sum(1 << (j - 1) for j in fs): c for fs, c in rc.items()}
    INF = float("inf")
    f = [INF] * (full + 1)
    f[0] = 0.0
    for S in range(1, full + 1):
        low = S & -S
        T = S
        while T:
            if T & low and T in mask_cost:
                v = mask_cost[T] + f[S ^ T]
                if v < f[S]:
                    f[S] = v
            T = (T - 1) & S
    return f  # f[mask] = min route loss to serve exactly the nodes in mask (inf if infeasible)


def enumerate_game(g: RoutingGame):
    """Exhaustive pure-profile enumeration (NE mode).  Returns (potential array, NE boolean array, plans per carrier).

    A plan is a served set (bitmask); its routing loss is the exact partition optimum.  Carrier cost is
    J_i = c_i + <a_i, M A_-i> with the same terms as `RoutingGame.J`.
    """
    N, Z = g.N, g.Z
    plans = []
    for i in range(N):
        cr = g.carriers[i]
        f = served_set_costs(g, i)
        lst = []
        for m, rcst in enumerate(f):
            if not np.isfinite(rcst):
                continue
            q = np.zeros(Z)
            tau = np.zeros(Z)
            for j in range(cr.inst.n):
                if m >> j & 1:
                    q[cr.zones[j]] += cr.d[j]
                    tau[cr.zones[j]] += cr.h[j]
            lst.append((m, g._plan(i, (), q, tau, rcst)))
        plans.append(lst)
    shape = [len(p) for p in plans]
    M = g.M
    a = [np.array([p.a for _, p in pl]) for pl in plans]
    c = [np.array([p.c for _, p in pl]) for pl in plans]
    A = np.zeros(shape + [g.d])
    for i in range(N):
        sh = [1] * N
        sh[i] = shape[i]
        A = A + a[i].reshape(sh + [g.d])
    J = []
    for i in range(N):
        sh = [1] * N
        sh[i] = shape[i]
        Am = A - a[i].reshape(sh + [g.d])
        Ji = c[i].reshape(sh) + np.einsum("...k,k,...k->...", np.broadcast_to(a[i].reshape(sh + [g.d]), A.shape), M, Am)
        J.append(Ji)
    ne = np.ones(shape, dtype=bool)
    for i in range(N):
        ne &= J[i] <= J[i].min(axis=i, keepdims=True) + 1e-7
    ct = [np.array([g.ctilde(p) for _, p in pl]) for pl in plans]
    Phi = np.zeros(shape)
    for i in range(N):
        sh = [1] * N
        sh[i] = shape[i]
        Phi = Phi + ct[i].reshape(sh)
    Phi = Phi + 0.5 * np.einsum("...k,k,...k->...", A, M, A)
    return Phi, ne, plans
