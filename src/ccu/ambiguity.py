"""Out-of-sample comparison of ambiguity criteria for route planning ("Why probability boxes").

One carrier, one depot, 22 customer zones that must all be served (the metro instances of
theory/new_algorithm_B/real_instances.py), route loss phi(T) = fixed + gamma*T + rho*max(0, T - Tmax) and sector
multipliers xi in R^K with a common-factor lognormal law.  A planner sees n training days and picks a partition of the
customers into routes by minimising a *criterion*  sum_r c(r), where c(r) is a functional of the law of the route time
T_r = <tau_r, xi> + svc_r (tau_r = base time per sector of the route, svc_r = service time):

  saa        empirical expectation of phi(T_r)
  wass       type-1 Wasserstein ball, closed form (ccu.robust):  saa + eps*(gamma+rho)*max_k tau_rk
  cvar       CVaR_alpha of phi(T_r) over the training days (route-wise, so the plan value is additive over routes)
  pbox_ud    DKW p-box on every sector marginal, unknown dependence: comonotone upper expectation (BRL, Thm 2.1)
  pbox_ind   same marginals (the worst one, the lower CDF) but independent sectors (Monte Carlo, common random numbers)
  *_emp      no DKW band: empirical marginals (unknown dependence = comonotone; independent)

Every criterion is solved by the *same* heuristic: multi-start Clarke-Wright + relocate / 2-opt / swap local search under
the criterion, then a set-partitioning MILP over the pool of all routes found for the draw (the integer step of
`ccu.brl.RoutePool`, with a pool built by local search instead of exact pricing).  This is not an exact method; its gap to
the exact branch-and-price (`ccu.bp`) is measured in `validate_against_bp` (experiments/run_ambiguity.py validate).
"""
from __future__ import annotations

import importlib.util
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp

from . import brl

ROOT = Path(__file__).resolve().parents[2]

CITIES = ["NewDelhi", "Cairo", "Moscow", "BuenosAires", "NewYork", "Bombay", "London", "Paris", "Berlin"]
EPS_GRID = (0.0, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0)  # Wasserstein radii (multiplier units, l1 ground metric)
CVAR_LEVELS = (0.8, 0.9)
DKW_CONF = (0.80, 0.90, 0.95, 0.99)  # confidence 1 - alpha_DKW
BETA = 0.05


# ---------------------------------------------------------------------------------------------------------------
# instance and laws
# ---------------------------------------------------------------------------------------------------------------


@dataclass
class Metro:
    name: str
    n: int
    tau: np.ndarray  # (n+1, n+1, K) base sector times (s)
    svc: np.ndarray  # (n+1,) service (s)
    dem: np.ndarray
    cap: float
    loss: brl.Loss
    m: np.ndarray  # (K,) mean multipliers
    sc: float  # sd of the common factor (log scale)
    ss: float  # sd of the sector factor
    peak: float
    xmax: float  # a-priori support bound of a sector multiplier
    true: np.ndarray  # (S, K) the instance's held-out true-law days
    own_days: np.ndarray  # (60, K) the instance's own observed days (BP study)
    meta: dict = field(default_factory=dict)

    @property
    def K(self):
        return self.tau.shape[2]

    def sample(self, rng, N: int, kind: str = "base", nu: float = 3.0) -> np.ndarray:
        """Draw N days.  base: the instance's lognormal common-factor law.  heavy: same mean, same variance structure but
        Student-t(nu) factors (linear scale, truncated below at 0.25)."""
        K = self.K
        if kind == "base":
            g = rng.standard_normal((N, 1))
            e = rng.standard_normal((N, K))
            return self.m[None] * np.exp(self.sc * g + self.ss * e - 0.5 * (self.sc ** 2 + self.ss ** 2))
        if kind == "heavy":
            c = 1.0 / math.sqrt(nu / (nu - 2.0))
            g = rng.standard_t(nu, (N, 1)) * c
            e = rng.standard_t(nu, (N, K)) * c
            return np.maximum(0.25, self.m[None] * (1.0 + self.sc * g + self.ss * e))
        raise ValueError(kind)


def _load_ri():
    d = str(ROOT / "theory/new_algorithm_B")
    if d not in sys.path:
        sys.path.insert(0, d)
    import real_instances as ri  # noqa: WPS433

    return ri


def load_metro(city: str) -> Metro:
    """The instance of the BRL metro study (seed 0, 22 customer zones), plus the parameters of its true law."""
    ri = _load_ri()
    P, true, meta = ri.build(city)
    # recompute the law parameters with the same random stream as ri.build (depot / customers / k-means come first)
    import csv

    rng = np.random.default_rng(0)
    pars = ri.city_params()
    pc = pars.get(ri.CITIES[city], {})
    allc = [p.get("tomtom_congestion_pct") for p in pars.values() if "tomtom_congestion_pct" in p]
    cong = pc.get("tomtom_congestion_pct", float(np.mean(allc))) / 100
    rows = list(csv.DictReader(open(f"{ri.ROOT}/data/processed/{city}/zones.csv")))
    xy = np.array([[float(r["lon"]), float(r["lat"])] for r in rows])
    pop = np.array([float(r["pop"]) for r in rows])
    ds = np.array([float(r["depot_score"]) for r in rows])
    depot = int(np.lexsort((pop, ds))[-1])
    p = pop.copy()
    p[depot] = 0
    rng.choice(len(rows), 22, replace=False, p=p / p.sum())
    K = 9
    lab, C = ri.kmeans((xy - xy.mean(0)) / xy.std(0), K, rng)
    cen = np.linalg.norm(C, axis=1)
    m = 1 + cong * (1.15 - 0.3 * (cen - cen.min()) / (np.ptp(cen) + 1e-12))
    s = meta["sigma_log"]
    sc, ss = 0.7 * s, math.sqrt(max(s * s - (0.7 * s) ** 2, 0.0))
    if not np.allclose(true.mean(0), m, rtol=0.02):
        raise RuntimeError("law parameters do not reproduce the instance's true law")
    loss = brl.Loss(P.loss.gamma, P.loss.rho, P.loss.Tmax, P.loss.fixed)
    return Metro(city, P.n, P.tau, P.svc, P.dem, float(P.cap), loss, m, sc, ss, meta["peak"], 1 + 2 * meta["peak"], true,
                 np.asarray(P.scen), meta)


# ---------------------------------------------------------------------------------------------------------------
# criteria
# ---------------------------------------------------------------------------------------------------------------


def cvar_of(values: np.ndarray, alpha: float) -> float:
    """CVaR_alpha (upper tail mean) of a sample, with the fractional-weight convention of Rockafellar-Uryasev."""
    v = np.sort(np.asarray(values, float))[::-1]
    k = (1.0 - alpha) * len(v)
    full = int(math.floor(k + 1e-12))
    frac = k - full
    s = v[:full].sum() + (frac * v[full] if full < len(v) and frac > 1e-12 else 0.0)
    return float(s / k)


def phi(T, loss: brl.Loss):
    return loss.fixed + loss.gamma * T + loss.rho * np.maximum(T - loss.Tmax, 0.0)


def pbox_levels(days: np.ndarray, alpha: float, xmax: float):
    """DKW p-box of every sector on the union grid: (w, Qk) with Qk the upper quantile of the lower CDF (K, L)."""
    qfs = [brl.dkw_upper_quantile(days[:, k], alpha, xmax) for k in range(days.shape[1])]
    _, w, Q = brl.common_grid(qfs)
    return w, Q


class Criterion:
    """Route functional.  `cost(tau, svc)` with tau the (K,) base-time vector of the route and svc its service time."""

    def __init__(self, name: str, fn, kind: str, param=None):
        self.name = name
        self.fn = fn
        self.kind = kind
        self.param = param
        self.cache: dict = {}


def make_saa(loss, X, name="saa"):
    g, r, Tm, f = loss.gamma, loss.rho, loss.Tmax, loss.fixed

    def fn(tau, svc):
        T = X @ tau + svc
        return f + g * T.mean() + r * np.maximum(T - Tm, 0.0).mean()

    return Criterion(name, fn, "saa")


def make_wass(loss, X, eps, name=None):
    g, r, Tm, f = loss.gamma, loss.rho, loss.Tmax, loss.fixed
    pen = eps * (g + r)

    def fn(tau, svc):
        T = X @ tau + svc
        return f + g * T.mean() + r * np.maximum(T - Tm, 0.0).mean() + pen * tau.max()

    return Criterion(name or f"wass_e{eps}", fn, "wass", eps)


def make_cvar(loss, X, alpha, name=None):
    g, r, Tm, f = loss.gamma, loss.rho, loss.Tmax, loss.fixed
    k = (1.0 - alpha) * X.shape[0]
    full = int(math.floor(k + 1e-12))
    frac = k - full

    def fn(tau, svc):
        T = X @ tau + svc
        v = f + g * T + r * np.maximum(T - Tm, 0.0)
        if full >= len(v):
            return float(v.mean())
        # partial sort: the top `full + 1` values
        top = np.partition(v, len(v) - full - 1)[len(v) - full - 1:]  # ascending-unordered, top full+1 elements
        top.sort()
        s = top[1:].sum() + (frac * top[0] if frac > 1e-12 else 0.0)
        return float(s / k)

    return Criterion(name or f"cvar{int(round(alpha * 100))}", fn, "cvar", alpha)


def make_pbox_ud(loss, w, Q, name):
    g, r, Tm, f = loss.gamma, loss.rho, loss.Tmax, loss.fixed

    def fn(tau, svc):
        S = tau @ Q + svc
        return f + g * float(w @ S) + r * float(w @ np.maximum(S - Tm, 0.0))

    return Criterion(name, fn, "pbox_ud")


def make_pbox_ind(loss, w, Q, name, rng, M=2000):
    """Independent sectors with the p-box's worst marginal (lower CDF); common random numbers."""
    g, r, Tm, f = loss.gamma, loss.rho, loss.Tmax, loss.fixed
    K = Q.shape[0]
    ends = np.cumsum(w)
    U = rng.uniform(size=(M, K))
    idx = np.minimum(np.searchsorted(ends, U), len(ends) - 1)
    X = Q[np.arange(K)[None, :], idx]

    def fn(tau, svc):
        T = X @ tau + svc
        return f + g * T.mean() + r * np.maximum(T - Tm, 0.0).mean()

    return Criterion(name, fn, "pbox_ind")


# ---------------------------------------------------------------------------------------------------------------
# planner: local search + pool MILP
# ---------------------------------------------------------------------------------------------------------------


class Planner:
    """Route-pool planner of one (instance, draw).  All criteria share the tau cache and the route pool."""

    def __init__(self, M: Metro):
        self.M = M
        self.n = M.n
        self.D = M.tau.sum(-1)
        self._tau: dict = {}
        self.pool: set = set()
        self._dem = M.dem
        self._svc = M.svc

    # ---- route data
    def tau_of(self, r: tuple):
        v = self._tau.get(r)
        if v is None:
            p = (0, *r, 0)
            v = self.M.tau[list(p[:-1]), list(p[1:])].sum(0)
            self._tau[r] = (v, float(self._svc[list(r)].sum()))
            v = self._tau[r]
        return v

    def cost(self, crit: Criterion, r: tuple) -> float:
        if not r:
            return 0.0
        c = crit.cache.get(r)
        if c is None:
            tau, svc = self.tau_of(r)
            c = float(crit.fn(tau, svc))
            crit.cache[r] = c
        return c

    def total(self, crit: Criterion, sol) -> float:
        return sum(self.cost(crit, tuple(r)) for r in sol)

    # ---- construction heuristic and descent
    def clarke_wright(self, crit, rng, noise=0.0):
        n, D, dem, cap = self.n, self.D, self._dem, self.M.cap
        routes = {j: [j] for j in range(1, n + 1)}
        rid = {j: j for j in range(1, n + 1)}
        sav = [(D[0, a] + D[0, b] - D[a, b] + (rng.normal(0, noise) if noise else 0.0), a, b)
               for a in range(1, n + 1) for b in range(a + 1, n + 1)]
        sav.sort(reverse=True)
        for s, a, b in sav:
            ra, rb = rid[a], rid[b]
            if ra == rb or s <= 0:
                continue
            A, B = routes[ra], routes[rb]
            if dem[A].sum() + dem[B].sum() > cap:
                continue
            if A[-1] == a and B[0] == b:
                new = A + B
            elif A[0] == a and B[-1] == b:
                new = B + A
            elif A[0] == a and B[0] == b:
                new = A[::-1] + B
            elif A[-1] == a and B[-1] == b:
                new = A + B[::-1]
            else:
                continue
            if self.cost(crit, tuple(new)) > self.cost(crit, tuple(A)) + self.cost(crit, tuple(B)):
                continue
            routes[ra] = new
            del routes[rb]
            for j in new:
                rid[j] = ra
        return [list(r) for r in routes.values()]

    def descend(self, crit, sol):
        sol = [list(r) for r in sol]
        dem, cap = self._dem, self.M.cap
        cost = lambda r: self.cost(crit, tuple(r))  # noqa: E731
        improved = True
        while improved:
            improved = False
            # relocate (also into a new route)
            for ri in range(len(sol)):
                for pos in range(len(sol[ri])):
                    c = sol[ri][pos]
                    rest = sol[ri][:pos] + sol[ri][pos + 1:]
                    base = cost(sol[ri]) - cost(rest)
                    for rj in range(len(sol) + 1):
                        if rj == ri:
                            continue
                        tgt = sol[rj] if rj < len(sol) else []
                        if tgt and dem[tgt].sum() + dem[c] > cap:
                            continue
                        ct = cost(tgt) if tgt else 0.0
                        for q in range(len(tgt) + 1):
                            nt = tgt[:q] + [c] + tgt[q:]
                            if cost(nt) - ct - base < -1e-9:
                                sol[ri] = rest
                                if rj < len(sol):
                                    sol[rj] = nt
                                else:
                                    sol.append(nt)
                                sol = [r for r in sol if r]
                                improved = True
                                break
                        if improved:
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                continue
            for ri, r in enumerate(sol):  # 2-opt inside a route
                cr = cost(r)
                for a in range(len(r)):
                    for b in range(a + 2, len(r) + 1):
                        nr = r[:a] + r[a:b][::-1] + r[b:]
                        if cost(nr) < cr - 1e-9:
                            sol[ri] = nr
                            improved = True
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                continue
            for ri in range(len(sol)):  # swap between routes
                for rj in range(ri + 1, len(sol)):
                    base = cost(sol[ri]) + cost(sol[rj])
                    for a in range(len(sol[ri])):
                        for b in range(len(sol[rj])):
                            A, B = sol[ri][:], sol[rj][:]
                            A[a], B[b] = B[b], A[a]
                            if dem[A].sum() > cap or dem[B].sum() > cap:
                                continue
                            if cost(A) + cost(B) - base < -1e-9:
                                sol[ri], sol[rj] = A, B
                                improved = True
                                break
                        if improved:
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                continue
            for ri in range(len(sol)):  # 2-opt*: exchange tails of two routes
                for rj in range(ri + 1, len(sol)):
                    A0, B0 = sol[ri], sol[rj]
                    base = cost(A0) + cost(B0)
                    for a in range(len(A0) + 1):
                        for b in range(len(B0) + 1):
                            if (a == len(A0) and b == len(B0)) or (a == 0 and b == 0):
                                continue
                            A = A0[:a] + B0[b:]
                            B = B0[:b] + A0[a:]
                            if (A and dem[A].sum() > cap) or (B and dem[B].sum() > cap):
                                continue
                            if (cost(A) if A else 0.0) + (cost(B) if B else 0.0) - base < -1e-9:
                                sol[ri], sol[rj] = A, B
                                sol = [r for r in sol if r]
                                improved = True
                                break
                        if improved:
                            break
                    if improved:
                        break
                if improved:
                    break
        return sol

    def seeded_start(self, crit, rng, m):
        """m routes seeded by random customers, the others inserted at their cheapest feasible position."""
        n, dem, cap = self.n, self._dem, self.M.cap
        order = [int(c) for c in rng.permutation(np.arange(1, n + 1))]
        sol = [[c] for c in order[:m]]
        for c in order[m:]:
            best, bd = None, math.inf
            for ri in range(len(sol) + 1):
                tgt = sol[ri] if ri < len(sol) else []
                if tgt and dem[tgt].sum() + dem[c] > cap:
                    continue
                if ri == len(sol) and best is not None:
                    continue  # open a new route only when nothing fits
                ct = self.cost(crit, tuple(tgt)) if tgt else 0.0
                for q in range(len(tgt) + 1):
                    d = self.cost(crit, tuple(tgt[:q] + [c] + tgt[q:])) - ct
                    if d < bd:
                        best, bd = (ri, q), d
            ri, q = best
            if ri < len(sol):
                sol[ri] = sol[ri][:q] + [c] + sol[ri][q:]
            else:
                sol.append([c])
        return sol

    def ruin_recreate(self, crit, sol, rng, kmin=2, kmax=5):
        """Remove k random customers and reinsert each at its cheapest feasible position (new route allowed)."""
        sol = [list(r) for r in sol]
        allc = [c for r in sol for c in r]
        k = int(rng.integers(kmin, min(kmax, len(allc)) + 1))
        out = list(rng.choice(allc, k, replace=False))
        out = [int(c) for c in out]
        sol = [[c for c in r if c not in out] for r in sol]
        sol = [r for r in sol if r]
        dem, cap = self._dem, self.M.cap
        for c in out:
            best, bd = None, math.inf
            for ri in range(len(sol) + 1):
                tgt = sol[ri] if ri < len(sol) else []
                if tgt and dem[tgt].sum() + dem[c] > cap:
                    continue
                ct = self.cost(crit, tuple(tgt)) if tgt else 0.0
                for q in range(len(tgt) + 1):
                    d = self.cost(crit, tuple(tgt[:q] + [c] + tgt[q:])) - ct
                    if d < bd:
                        best, bd = (ri, q), d
            ri, q = best
            if ri < len(sol):
                sol[ri] = sol[ri][:q] + [c] + sol[ri][q:]
            else:
                sol.append([c])
        return sol

    def search(self, crit, rng, starts: int = 4, init=(), ils: int = 8, nseed: int = 4):
        """Best local optimum over Clarke-Wright starts (the first without noise) and given initial solutions,
        followed by `ils` ruin-and-recreate iterations from the best one."""
        best, bv = None, math.inf
        cands = [self.clarke_wright(crit, rng, 60.0 if s else 0.0) for s in range(starts)] + [list(map(list, s)) for s in init]
        m0 = int(math.ceil(self._dem.sum() / self.M.cap))
        cands += [self.seeded_start(crit, rng, m0 + (s % 3)) for s in range(nseed)]
        for sol in cands:
            sol = self.descend(crit, sol)
            for r in sol:
                self.pool.add(tuple(r))
            v = self.total(crit, sol)
            if v < bv - 1e-12:
                best, bv = sol, v
        for _ in range(ils):
            sol = self.descend(crit, self.ruin_recreate(crit, best, rng))
            for r in sol:
                self.pool.add(tuple(r))
            v = self.total(crit, sol)
            if v < bv - 1e-12:
                best, bv = sol, v
        return best, bv

    # ---- integer step over the pool
    def milp(self, crit, ub: float = math.inf, time_limit: float = 0.8):
        """Set partitioning over every route the local search of `crit` has evaluated (best order per customer subset),
        after reduced-cost fixing from the LP relaxation against the incumbent value `ub`."""
        best: dict = {}
        for r in set(crit.cache) | self.pool:
            if not r:
                continue
            key = frozenset(r)
            c = self.cost(crit, r)
            if key not in best or c < best[key][0]:
                best[key] = (c, r)
        keys = list(best)
        n = self.n
        A = np.zeros((n, len(keys)))
        for k, key in enumerate(keys):
            for j in key:
                A[j - 1, k] = 1.0
        c = np.array([best[k][0] for k in keys])
        lp = linprog(c, A_eq=A, b_eq=np.ones(n), bounds=(0, None), method="highs")
        if lp.status != 0:
            return None, math.inf
        y = lp.eqlin.marginals
        rc = c - A.T @ y
        gap = (ub - lp.fun if np.isfinite(ub) else 1e9) + 1e-6 * max(1.0, abs(lp.fun))
        keep = np.flatnonzero(rc <= max(gap, 1e-7))
        res = milp(c[keep], constraints=LinearConstraint(A[:, keep], lb=np.ones(n), ub=np.ones(n)),
                   integrality=np.ones(len(keep)), bounds=Bounds(0, 1), options={"time_limit": time_limit, "mip_rel_gap": 1e-7})
        if res.x is None:
            return None, math.inf
        sel = keep[np.flatnonzero(res.x > 0.5)]
        return [list(best[keys[k]][1]) for k in sel], float(sum(c[k] for k in sel))

    def plan(self, crit, rng, starts: int = 4, init=(), ils: int = 8, nseed: int = 4):
        """Local search (multi-start + ruin-and-recreate), then the MILP over all routes it evaluated."""
        sol, v = self.search(crit, rng, starts, init, ils, nseed)
        s2, v2 = self.milp(crit, ub=v)
        if s2 is not None and v2 < v - 1e-9:
            sol, v = s2, v2
        return sol, v


# ---------------------------------------------------------------------------------------------------------------
# evaluation of a plan on test laws
# ---------------------------------------------------------------------------------------------------------------


class TestLaw:
    def __init__(self, name: str, Z: np.ndarray, shift: float = 0.0):
        self.name = name
        self.Z = Z
        self.shift = shift


def plan_metrics(M: Metro, planner: Planner, sol, law: TestLaw) -> dict:
    """Expected cost, upper tail, overtime and fleet statistics of a plan on the test days of `law`."""
    ls = M.loss
    D = np.zeros(law.Z.shape[0])
    ot = np.zeros(law.Z.shape[0])
    nrt_ot = 0.0
    tot_T = 0.0
    anyot = np.zeros(law.Z.shape[0], bool)
    for r in sol:
        tau, svc = planner.tau_of(tuple(r))
        T = law.Z @ tau + law.shift * tau.sum() + svc
        o = np.maximum(T - ls.Tmax, 0.0)
        D += ls.fixed + ls.gamma * T + ls.rho * o
        ot += o
        anyot |= o > 0
        nrt_ot += float((o > 0).mean())
        tot_T += float(T.mean())
    return dict(exp=float(D.mean()), cvar95=cvar_of(D, 0.95), p_ot_day=float(anyot.mean()), p_ot_route=nrt_ot / len(sol),
                ot_h=float(ot.mean() / 3600.0), ot_h_cond=float(ot[anyot].mean() / 3600.0) if anyot.any() else 0.0,
                drive_h=tot_T / 3600.0, sd=float(D.std()))


def cvar_route_sum(M: Metro, planner: Planner, sol, law: TestLaw, alpha: float) -> float:
    ls = M.loss
    tot = 0.0
    for r in sol:
        tau, svc = planner.tau_of(tuple(r))
        T = law.Z @ tau + law.shift * tau.sum() + svc
        tot += cvar_of(phi(T, ls), alpha)
    return tot


# ---------------------------------------------------------------------------------------------------------------
# theory radius
# ---------------------------------------------------------------------------------------------------------------


def wass_radius(days: np.ndarray, kind: str = "sqrt", beta: float = BETA) -> float:
    """Theory-motivated Wasserstein radius (multiplier units).

    sqrt: route loss depends on the one-dimensional projection <tau, xi>, for which E W1(P_n, P) <= sigma / sqrt(n);
          a sub-Gaussian concentration step gives  eps = sigma * sqrt(2 ln(1/beta) / n)  with sigma the mean sector sd.
    fg:   dimension-dependent Fournier-Guillin rate sigma * n^(-1/K) for the K-dimensional law (constant set to 1).
    """
    n, K = days.shape
    sig = float(days.std(0, ddof=1).mean())
    if kind == "sqrt":
        return sig * math.sqrt(2.0 * math.log(1.0 / beta) / n)
    if kind == "fg":
        return sig * n ** (-1.0 / K)
    raise ValueError(kind)


# ---------------------------------------------------------------------------------------------------------------
# one block = one (city, training regime, n, draw): all criteria, all test laws
# ---------------------------------------------------------------------------------------------------------------


def saa_value(M: Metro, planner: Planner, sol, X: np.ndarray) -> float:
    ls = M.loss
    return float(sum(phi(X @ planner.tau_of(tuple(r))[0] + planner.tau_of(tuple(r))[1], ls).mean() for r in sol))


def criteria_for_draw(M: Metro, days: np.ndarray, rng, *, with_ind: bool = True):
    """All criteria of one training sample, in solving order.  Returns list of (family, Criterion)."""
    ls, n = M.loss, days.shape[0]
    out = [("saa", make_saa(M.loss, days))]
    for conf in DKW_CONF:
        w, Q = pbox_levels(days, 1.0 - conf, M.xmax)
        out.append(("pbox_ud", make_pbox_ud(ls, w, Q, f"pbox_ud_{int(round(conf * 100))}")))
    w0, Q0 = pbox_levels(days, 2.0, M.xmax)  # alpha >= 2: no band, empirical marginals
    out.append(("pbox_ud", make_pbox_ud(ls, w0, Q0, "pbox_ud_emp")))
    if with_ind:
        for conf in (0.80, 0.95):
            w, Q = pbox_levels(days, 1.0 - conf, M.xmax)
            out.append(("pbox_ind", make_pbox_ind(ls, w, Q, f"pbox_ind_{int(round(conf * 100))}", np.random.default_rng(7))))
        out.append(("pbox_ind", make_pbox_ind(ls, w0, Q0, "pbox_ind_emp", np.random.default_rng(7))))
    for a in CVAR_LEVELS:
        out.append(("cvar", make_cvar(ls, days, a)))
    for e in EPS_GRID[1:]:
        out.append(("wass", make_wass(ls, days, e, f"wass_e{e:g}")))
    out.append(("wass", make_wass(ls, days, wass_radius(days, "sqrt"), "wass_th")))
    out.append(("wass", make_wass(ls, days, wass_radius(days, "fg"), "wass_fg")))
    return out


def cv_wass_eps(M: Metro, pl: Planner, days: np.ndarray, rng, init_sol, folds: int = 3):
    """Cross-validated Wasserstein radius: plan on the training folds for every radius of EPS_GRID with the same local
    search (no MILP), score the plan by the SAA expected cost on the held-out fold, pick the best radius."""
    n = days.shape[0]
    perm = rng.permutation(n)
    parts = np.array_split(perm, min(folds, n))
    score = np.zeros(len(EPS_GRID))
    for f, te in enumerate(parts):
        tr = np.setdiff1d(perm, te)
        for ie, e in enumerate(EPS_GRID):
            crit = make_wass(M.loss, days[tr], e)
            sol, _ = pl.search(crit, rng, starts=1, init=[init_sol], ils=2, nseed=1)
            score[ie] += saa_value(M, pl, sol, days[te]) * len(te)
    score /= n
    best = int(np.argmin(score - 1e-9 * np.arange(len(score))))  # ties: the smaller radius
    return EPS_GRID[best], score


def run_block(M: Metro, laws: dict, days: np.ndarray, rng, *, with_ind: bool = True, with_cv: bool = True):
    """Plan with every criterion on one training sample; evaluate on every test law.  Returns list of row dicts."""
    pl = Planner(M)
    crits = criteria_for_draw(M, days, rng, with_ind=with_ind)
    plans: dict = {}
    vals: dict = {}
    times: dict = {}
    import time as _t

    order = [c for c in crits]
    seeds: list = []
    for fam, crit in order:
        t0 = _t.perf_counter()
        sol, v = pl.plan(crit, rng, init=seeds[:3])
        plans[crit.name] = (fam, crit, sol)
        vals[crit.name] = v
        times[crit.name] = _t.perf_counter() - t0
        if fam in ("saa", "pbox_ud") and len(seeds) < 3:
            seeds.append(sol)
    if with_cv:
        t0 = _t.perf_counter()
        eps_cv, score = cv_wass_eps(M, pl, days, rng, plans["saa"][2])
        name = "saa" if eps_cv == 0.0 else f"wass_e{eps_cv:g}"
        fam, crit, sol = plans[name]
        plans["wass_cv"] = ("wass", crit, sol)
        vals["wass_cv"] = vals[name]
        times["wass_cv"] = _t.perf_counter() - t0
        plans["wass_cv"] = ("wass_cv", crit, sol)
        eps_chosen = eps_cv
    else:
        eps_chosen = float("nan")
    rows = []
    for name, (fam, crit, sol) in plans.items():
        row = dict(criterion=name, family=fam, param=crit.param if name != "wass_cv" else eps_chosen,
                   crit_value=vals[name], n_routes=len(sol), plan=";".join("-".join(map(str, r)) for r in sol),
                   time=times[name])
        if name == "wass_cv":
            row["crit_value"] = vals["saa"] if eps_chosen == 0.0 else vals[f"wass_e{eps_chosen:g}"]
        for ln, law in laws.items():
            for k, v in plan_metrics(M, pl, sol, law).items():
                row[f"{ln}_{k}"] = v
        if fam == "cvar":
            row["cvar_route_true"] = cvar_route_sum(M, pl, sol, laws[next(iter(laws))], crit.param)
        rows.append(row)
    return rows
