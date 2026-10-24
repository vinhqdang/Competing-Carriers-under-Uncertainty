"""D2 regime of the integrated game: vehicle-count congestion (main.tex Example 2.2, regime D2).

D1 (zmc_brl.RoutingGame): the congestion coordinate of zone z is the vehicle-hours X_z = sum_i tau_iz, contribution and
exposure coincide (phi = a = (q, tau)).
D2 (this module): the congestion coordinate is the vehicle count X_z = sum_i n_iz, where n_iz is the number of routes of
carrier i that enter zone z.  Contribution a_i(p) = (q_z, n_z), exposure phi_i(p) = (q_z, tau_z), so phi != a.  Carrier i pays

    J_i(p; A_-i) = c_i(p) + <phi_i(p), M A_-i>,   c_i(p) = sum_r c_r + sum_z [ -alpha_z q + b_z q^2 + M_Xz tau_z n_z ] + charges,
    M = diag(b_z, M_Xz),   M_Xz = scale * gc_z * hbar_z,

where hbar_z is the mean lot duration (hours) offered in zone z, so that for scale = 1 a vehicle in zone z creates on average
the same congestion as an average lot of vehicle-hours under D1 (NEW calibration, documented in docs/EXPERIMENTS.md).
`scale` multiplies the strength of the vehicle-count externality (scale > 1 is a stress test).

Approximation shared with the D1 game: every customer node is in its own zone and is served all-or-nothing, so n_iz = 1[z is
served by i]; the own term M_X tau n is then linear in the service indicator and the carrier problem stays a
prize-collecting set-packing problem solved by `RoutePool` (the oracle is only implemented for best responses, rho = 0).
Under D2 the game has no exact potential in general (cross coefficients M_X h_i vs M_X h_j differ), so ZMC is not an
equilibrium solver here; best-response dynamics may cycle (Prop 7.1) and no pure equilibrium need exist (Thm 7.3).
"""
from __future__ import annotations

import copy
import itertools

import numpy as np

from . import zmc_brl as zb
from .credal import EPlan, ExplicitGame


class RoutingGameD2(zb.RoutingGame):
    """Vehicle-count variant of `RoutingGame` (build with `to_d2`)."""

    @property
    def M(self):
        return np.concatenate([self.b, self.mx])

    def _make_full(self, i):
        cr = self.carriers[i]
        a = np.zeros(2 * self.Z)
        np.add.at(a, cr.zones, cr.d)
        np.add.at(a, self.Z + cr.zones, 1.0)
        return a

    def full_phi(self, i):
        cr = self.carriers[i]
        f = np.zeros(2 * self.Z)
        np.add.at(f, cr.zones, cr.d)
        np.add.at(f, self.Z + cr.zones, cr.h)
        return f

    def _plan(self, i, routes, q, tau, route_cost, lb=-np.inf):
        Z = self.Z
        n = np.zeros(Z)
        for r in routes:
            for z in set(r):
                n[z] += 1.0
        a = np.concatenate([q, n])
        phi = np.concatenate([q, tau])
        c = route_cost + float(np.sum(-self.alpha * q + self.b * q * q + self.mx * tau * n)) \
            + float(self.toll @ a) + float(self.sur @ phi)
        p = zb.Plan(routes, q, a, c, route_cost, lb)
        p.phi = phi
        return p

    def empty_plan(self, i):
        return self._plan(i, (), np.zeros(self.Z), np.zeros(self.Z), 0.0)

    def _kappa(self, i, lam, rho):
        if rho == 1.0:
            raise NotImplementedError("pricing (rho = 1) needs a potential; D2 has none")
        cr = self.carriers[i]
        z = cr.zones
        Z = self.Z
        Me = self.M
        k = Me[z] * cr.d ** 2 + Me[Z + z] * cr.h - self.alpha[z] * cr.d \
            + self.toll[z] * cr.d + self.toll[Z + z] + self.sur[z] * cr.d + self.sur[Z + z] * cr.h \
            + lam[z] * cr.d + lam[Z + z] * cr.h
        return np.concatenate([[0.0], k])

    def J(self, i, p, A_minus):
        return p.c + float(p.phi @ (self.M * A_minus))

    def ctilde(self, p):
        return np.nan

    def potential(self, prof):
        return np.nan

    def evaluate(self, prof) -> dict:
        Z = self.Z
        q = sum(p.q for p in prof)
        n = sum(p.a[Z:] for p in prof)
        cs = float(np.sum(self.alpha * q - 0.5 * self.b * q * q))
        cong = sum(float(np.sum(self.mx * p.phi[Z:] * n)) for p in prof)
        route = sum(p.cr for p in prof)
        qfull = sum(self._full[i][:Z] for i in range(self.N))
        W = cs - cong - route
        return dict(deliveries=float(q.sum()), demand=float(qfull.sum()), served_share=float(q.sum() / max(qfull.sum(), 1e-12)),
                    vehicles=int(sum(len(p.routes) for p in prof)), welfare=W, congestion_cost=cong, routing_cost=route,
                    consumer_surplus=cs, q_z=q, n_z=n)


def to_d2(g: zb.RoutingGame, scale: float = 1.0) -> RoutingGameD2:
    """D2 copy of a (D1, mode 'ne') game sharing carriers, route pools and calibration."""
    Z = g.Z
    hsum = np.zeros(Z)
    cnt = np.zeros(Z)
    for cr in g.carriers:
        np.add.at(hsum, cr.zones, cr.h)
        np.add.at(cnt, cr.zones, 1.0)
    hall = float(hsum.sum() / max(cnt.sum(), 1.0))
    hbar = np.where(cnt > 0, hsum / np.maximum(cnt, 1.0), hall)
    d2 = copy.copy(g)
    d2.__class__ = RoutingGameD2
    d2.mx = float(scale) * g.gc * hbar
    d2.d2_scale = float(scale)
    d2.mode = "ne"
    d2._cache = {}
    d2._full = [d2._make_full(i) for i in range(d2.N)]
    d2.calls = 0
    d2.name = g.name + f"_D2x{scale:g}"
    return d2


# ---------------------------------------------------------------------------------------------------------------
# exhaustive enumeration of tiny games (D1 or D2), served sets as plans
# ---------------------------------------------------------------------------------------------------------------


def explicit_from_game(g) -> ExplicitGame:
    """All served-set plans of every carrier (exact partition-optimal route cost) as an ExplicitGame (works for D1 and D2 games)."""
    plans = []
    for i in range(g.N):
        cr = g.carriers[i]
        f = zb.served_set_costs(g, i)
        lst = []
        for m, rcst in enumerate(f):
            if not np.isfinite(rcst):
                continue
            q = np.zeros(g.Z)
            tau = np.zeros(g.Z)
            routes = []
            for j in range(cr.inst.n):
                if m >> j & 1:
                    q[cr.zones[j]] += cr.d[j]
                    tau[cr.zones[j]] += cr.h[j]
                    routes.append((int(cr.zones[j]),))  # pseudo-routes: only used to count vehicles per zone (n = served indicator)
            p = g._plan(i, tuple(routes), q, tau, rcst)
            lst.append(EPlan(p.a, getattr(p, "phi", p.a), p.c, f"{i}:{m}"))
        plans.append(lst)
    return ExplicitGame(np.asarray(g.M, float), plans)


def pure_nash(eg: ExplicitGame, tol=1e-9):
    """Pure Nash equilibria of an ExplicitGame by enumeration (indices)."""
    out = []
    for idx in eg.profiles():
        prof = eg.profile(idx)
        A = sum(p.a for p in prof)
        ok = True
        for i, p in enumerate(prof):
            Am = A - p.a
            cur = p.c + float(p.phi @ (eg.M * Am))
            if min(q.c + float(q.phi @ (eg.M * Am)) for q in eg.plans[i]) < cur - tol:
                ok = False
                break
        if ok:
            out.append(idx)
    return out


def make_tiny_game_dup(N=3, Z=3, n_cust=3, seed=0, K=2, ndays=20, alpha_dkw=0.2, cap=9.0, dmax=8, hscale=0.08,
                       hvar=0.0) -> zb.RoutingGame:
    """Tiny game in which customer nodes may share a zone (several lots per zone), so that a carrier's vehicle count in a zone
    (number of routes entering it) is a real decision.  Same cost structure as `make_tiny_game`; lot hours h = hscale * d *
    exp(hvar * N(0,1)) (hvar > 0 decouples hours from deliveries, which is what makes D2 differ from D1)."""
    from . import brl

    rng = np.random.default_rng(seed)
    xy = rng.uniform(0, 1, (Z, 2))
    TT = np.linalg.norm(xy[:, None] - xy[None], axis=-1) * 3000.0 + 300.0
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
        c = np.sort(rng.integers(0, Z, n_cust))
        d = rng.integers(2, dmax + 1, n_cust).astype(float)
        h = d * hscale * np.exp(hvar * rng.standard_normal(n_cust))
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
        inst = brl.RoutingInstance(n, tau, svc, dem, float(cap), Qk, wl, loss)
        carriers.append(zb.CarrierData(depot, c, d, h, inst, brl.RoutePool(inst, ng_size=n), 1.0 / N))
        np.add.at(Qfull, c, d)
    alpha = np.full(Z, 12.0)
    b = alpha / (2.0 * np.maximum(Qfull, 1.0)) * rng.uniform(0.8, 1.6, Z)
    gc = rng.uniform(0.3, 1.5, Z)
    return zb.RoutingGame(Z, carriers, alpha, b, gc, gamma_h, bg=np.zeros(Z), name=f"tinydup{seed}")


def explicit_partitions(g) -> ExplicitGame:
    """Exhaustive plans = served subsets partitioned into capacity-feasible routes (route cost = exact robust cost, best order).

    Needed when a zone holds several lots, because then the vehicle count n_z depends on the partition.  Works for D1 and D2."""
    from . import brl

    plans = []
    for i in range(g.N):
        cr = g.carriers[i]
        n = cr.inst.n
        best = brl.enumerate_best_routes(cr.inst)
        keys = list(best)

        def parts(rem):
            if not rem:
                yield []
                return
            first = min(rem)
            rest = [x for x in rem if x != first]
            for r in range(len(rest) + 1):
                for comb in itertools.combinations(rest, r):
                    blk = frozenset((first,) + comb)
                    if blk in best:
                        for tail in parts([x for x in rest if x not in comb]):
                            yield [blk] + tail

        lst = []
        seen = set()
        for mask in range(1 << n):
            nodes = [j + 1 for j in range(n) if mask >> j & 1]
            for pt in parts(nodes):
                routes = tuple(sorted(best[b][1] for b in pt))
                if routes in seen:
                    continue
                seen.add(routes)
                q = np.zeros(g.Z)
                tau = np.zeros(g.Z)
                for r in routes:
                    for j in r:
                        q[cr.zones[j - 1]] += cr.d[j - 1]
                        tau[cr.zones[j - 1]] += cr.h[j - 1]
                zr = tuple(tuple(int(cr.zones[j - 1]) for j in r) for r in routes)
                rc = sum(best[frozenset(r)][0] for r in routes)
                p = g._plan(i, zr, q, tau, rc)
                lst.append(EPlan(p.a, getattr(p, "phi", p.a), p.c, f"{i}:{routes}"))
        plans.append(lst)
    return ExplicitGame(np.asarray(g.M, float), plans)
