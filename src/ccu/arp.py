"""Aggregate-response pricing (ARP): the city's zone charges from observed zone aggregates alone.

Setting (ccu.zmc_brl.RoutingGame, D1; the same game and notation as ccu.dip).  The city never sees a carrier's
routing costs, plans or lots.  After posting a per-delivery-equivalent charge vector u (one number per zone, realised
as a uniform per-delivery charge plus non-negative zone congestion charges, `dip.instruments`) it observes only the
zone aggregates of the equilibrium the carriers settle in: deliveries Q_z and the number n_z of carriers active in z.

Flat rule (ARP).  With kappa_z = gc_z r^2 (congestion slope in delivery units) and m_z = b_z + kappa_z:

    u_z  <-  (1 - theta_z) u_z + theta_z [ kappa_z Q_z - (m_z / 2) dbar_z ],      dbar_z ~ Q_z / n_z,

the Pigou term at the observed aggregate minus a half-lot Cournot subsidy, the mean lot estimated from the
observation (or learned from the jumps of Q_z when n_z changes by one).  theta = 1 is the plain fixed-point
iteration, theta_z = 2 m_z / (2 m_z + kappa_z) the damping of Theorem 2 (theory/new_algorithm_D/theory.tex), and
'msa' the successive-averages step 1/(t+1).

Marginal tariff (ARP-M).  The limit of re-tangenting at every transaction: carrier i pays, in zone z,
T_z(q_i, Q) = kappa_z q_i (Q - q_i) - (b_z / 2) q_i^2, a function of its own deliveries and the zone total only.
Under it the carriers' game has the social cost as exact potential (Theorem 7): every social optimum is an
equilibrium, and the carriers' own best-response dynamics never increase the social cost.

Theory (theory.tex).  In the convexified game the equilibrium aggregate is the proximal map of the carriers'
aggregate value function, u -> Q(u) = argmin_Q F(Q) + <u, Q>, so the leader's problem is a strongly convex dual
problem whose gradient (u + m dbar / 2) / kappa - Q(u) is observable; the flat rule is gradient descent on it, with
contraction ratio rho = max_z kappa_z / m_z (theta = 1) or rho / (2 + rho) (optimal damping), independent of Z, N and
of the routing structure (Theorems 1-2).  In the pure (lumpy) game every fixed point is a unilateral social optimum
up to the lot-asymmetry term of ccu.dip (Theorem 3).  Nothing in the rules depends on the carriers' ambiguity
attitude: a Gamma-maximin surcharge of any width is absorbed into the observed response (Proposition 5).
"""
from __future__ import annotations

import time

import numpy as np

from . import dip, zmc

# ------------------------------------------------------------------------------------------------ observation


def observe(g, prof):
    """What the city sees: deliveries Q_z and the number of active carriers n_z per zone."""
    Q = sum(p.q for p in prof)
    n = sum((p.q > 1e-12).astype(int) for p in prof)
    return Q, n


class LotMemory:
    """Per-zone lot sizes inferred from observations: Q_z itself when n_z = 1, and the jump |Q_z^t - Q_z^{t-1}| when
    n_z changes by exactly one between two observations (the entering or leaving carrier's lot)."""

    def __init__(self, Z):
        self.lots = [set() for _ in range(Z)]
        self.prev = None

    def update(self, Q, n):
        for z in range(len(Q)):
            if n[z] == 1 and Q[z] > 1e-9:
                self.lots[z].add(round(float(Q[z]), 9))
            if self.prev is not None:
                Qp, npv = self.prev
                if abs(int(n[z]) - int(npv[z])) == 1 and abs(Q[z] - Qp[z]) > 1e-9:
                    self.lots[z].add(round(float(abs(Q[z] - Qp[z])), 9))
        self.prev = (Q.copy(), n.copy())

    def mean(self, z):
        return float(np.mean(list(self.lots[z]))) if self.lots[z] else None


def mean_lot_estimate(g, Q, n, memory: LotMemory | None = None, fallback: float | None = None):
    """dbar_z: the mean of the lots learned in z (memory), else Q_z / n_z where observed, else the city-wide mean
    observed lot (or `fallback`)."""
    act = dip.active_zones(g)
    served = n > 0
    d = np.zeros(g.Z)
    d[served] = Q[served] / n[served]
    if fallback is None:
        fallback = float(Q[served].sum() / max(n[served].sum(), 1)) if served.any() else 0.0
    d[~served] = fallback
    if memory is not None:
        for z in range(g.Z):
            mz = memory.mean(z)
            if mz is not None:
                d[z] = mz
    return np.where(act, d, 0.0)


def observed_tangent(g, Q, n, dbar=None, memory=None):
    """u_z = kappa_z Q_z - (m_z/2) dbar_z from the observation (Q, n); `dbar` overrides the estimate."""
    kappa, m, _ = dip.curvatures(g)
    if dbar is None:
        dbar = mean_lot_estimate(g, Q, n, memory)
    return np.where(dip.active_zones(g), kappa * Q - 0.5 * m * dbar, 0.0)


def damping(g, mode="plain") -> np.ndarray:
    """theta_z: 1 (plain), 2 m_z / (2 m_z + kappa_z) (optimal constant step of the dual gradient method, Theorem 2)."""
    kappa, m, _ = dip.curvatures(g)
    if mode in ("plain", "msa"):
        return np.ones(g.Z)
    if mode == "optimal":
        return 2.0 * m / (2.0 * m + kappa)
    raise ValueError(mode)


def contraction_ratio(g) -> float:
    """rho = max_z kappa_z / m_z over active zones (contraction ratio of the plain iteration, Theorem 2)."""
    kappa, m, _ = dip.curvatures(g)
    act = dip.active_zones(g)
    return float(np.max(kappa[act] / m[act])) if act.any() else 0.0


def knorm(g, v) -> float:
    """||v||_{kappa^{-1}} over active zones (the metric of the contraction theorems)."""
    kappa, _, _ = dip.curvatures(g)
    act = dip.active_zones(g)
    return float(np.sqrt(np.sum(v[act] ** 2 / kappa[act])))


# ------------------------------------------------------------------------------------------------ carriers


def settle(g, prof, u, max_rounds: int = 60):
    """Carriers' day-to-day response to the posted flat charge u: Gauss-Seidel best responses from the current profile
    until no carrier improves (a potential descent).  Returns (profile, converged)."""
    _, _, toll = dip.instruments(g, u)
    g.set_charges(toll=toll, sur=g.sur)
    prof = [g.plan_from_routes(i, p.routes) for i, p in enumerate(prof)]  # re-priced under u
    return zmc.br_dynamics(g, init=prof, max_rounds=max_rounds)


def profile_key(prof):
    return tuple(tuple(sorted(p.routes)) for p in prof)


# ------------------------------------------------------------------------------------------------ the flat rule


def arp(g, init, *, theta="plain", max_rounds: int = 12, tol: float = 1e-6, dbar=None, learn_lots: bool = True,
        log=None) -> dict:
    """Aggregate-response pricing from the unpriced equilibrium `init` (a list of plans).

    theta: 'plain' | 'optimal' | 'msa' | array of per-zone damping factors.  dbar: None (estimated from observations)
    or a fixed mean-lot vector (information-rich benchmark; disables lot learning).  Stops at a fixed point (the
    tangent of the observed aggregate equals the posted charge, kappa^{-1} norm relative to the scale of u), when the
    posted charge and the carriers' profile repeat (cycle), or after max_rounds posted charges.  Every oracle call of
    the simulated carriers is counted on g.  The returned profile is the last equilibrium observed.
    """
    t0 = time.perf_counter()
    c0 = g.calls
    msa = isinstance(theta, str) and theta == "msa"
    th = damping(g, theta) if isinstance(theta, str) else np.asarray(theta, float)
    act = dip.active_zones(g)
    mem = LotMemory(g.Z) if (learn_lots and dbar is None) else None
    prof = list(init)
    u = np.zeros(g.Z)
    seen = {}
    hist = []
    status = "rounds"
    rounds = 0
    best = None
    for t in range(max_rounds + 1):
        Q, n = observe(g, prof)
        if mem is not None:
            mem.update(Q, n)
        u_tan = observed_tangent(g, Q, n, dbar, mem)
        sc = dip.social_cost(g, prof)
        step = knorm(g, u_tan - u)
        scale = max(knorm(g, u_tan), knorm(g, u), 1e-12)
        hist.append(dict(round=t, u=u.copy(), u_tan=u_tan.copy(), Q=Q.copy(), n=n.copy(), sc=sc, step=step,
                         step_rel=step / scale, calls=g.calls - c0, profile=prof))
        if log is not None:
            log.append(dict(round=t, sc=sc, step_rel=step / scale, calls=g.calls - c0))
        if best is None or sc < best["sc"] - 1e-9:
            best = hist[-1]
        if t > 0 and step <= tol * scale:
            status = "fixed_point"
            break
        key = (tuple(np.round(u[act], 6)), profile_key(prof))
        if key in seen:
            status = "cycle"
            hist[-1]["cycle_from"] = seen[key]
            break
        seen[key] = t
        if t == max_rounds:
            break
        w = (1.0 / (t + 1)) * np.ones(g.Z) if msa else th
        u = np.where(act, (1.0 - w) * u + w * u_tan, 0.0)
        prof, ok = settle(g, prof, u)
        rounds = t + 1
        if not ok:
            status = "carriers_not_converged"
            break
    last = hist[-1]
    return dict(profile=last["profile"], u=last["u"], Q=last["Q"], n=last["n"], sc=last["sc"], status=status,
                rounds=rounds, calls=g.calls - c0, time_s=time.perf_counter() - t0, hist=hist,
                best_round=best["round"], best_sc=best["sc"], rho=contraction_ratio(g),
                sc_path=[h["sc"] for h in hist])


# ------------------------------------------------------------------------------------------------ marginal tariff


class MarginalTariffGame:
    """The carriers' game under the realised-aggregate tariff T_z(q_i, Q) = kappa_z q_i (Q - q_i) - (b_z/2) q_i^2.

    Given the rivals' aggregate, the tariff is linear in the carrier's own service indicators (q_iz^2 = d_iz q_iz), so
    a best response is one call of the carrier's routing oracle with shifted zone prices.  The object exposes the
    interface used by `zmc.br_dynamics` (N, calls, br, J, empty_plan, plan_from_routes).  `g.toll` must be zero.
    """

    def __init__(self, g):
        self.g = g
        self.kappa, _, _ = dip.curvatures(g)
        self.D = dip.lots(g)
        self.N, self.Z = g.N, g.Z

    @property
    def calls(self):
        return self.g.calls

    def rate(self, i, A_minus) -> np.ndarray:
        """Per-delivery rate carrier i faces in each zone at the rivals' aggregate: kappa Q_-i - (b/2) d_i."""
        return self.kappa * A_minus[: self.Z] - 0.5 * self.g.b * self.D[i]

    def charge(self, i, p, A_minus) -> float:
        return float(self.rate(i, A_minus) @ p.q)

    def J(self, i, p, A_minus):
        return self.g.J(i, p, A_minus) + self.charge(i, p, A_minus)

    def br(self, i, A_minus, count=True):
        lam = self.g.M * A_minus
        lam = lam.copy()
        lam[: self.Z] += self.rate(i, A_minus)
        return self.g.oracle(i, lam, rho=0.0, count=count)

    def empty_plan(self, i):
        return self.g.empty_plan(i)

    def plan_from_routes(self, i, routes):
        return self.g.plan_from_routes(i, routes)

    def regrets(self, prof):
        A = sum(p.a for p in prof)
        out = np.zeros(self.N)
        for i, p in enumerate(prof):
            Am = A - p.a
            b = self.br(i, Am, count=False)
            out[i] = max(0.0, self.J(i, p, Am) - self.J(i, b, Am))
        return out

    def payments(self, prof) -> float:
        """Total tariff paid by the carriers (negative: the city pays)."""
        A = sum(p.a for p in prof)
        return float(sum(self.charge(i, p, A - p.a) for i, p in enumerate(prof)))

    def potential(self, prof) -> float:
        """Exact potential of the tariff game = social cost (Theorem 7)."""
        return dip.social_cost(self.g, prof)


def arp_marginal(g, init, max_rounds: int = 60) -> dict:
    """Carriers' best-response dynamics from `init` under the marginal tariff.  No iteration by the city."""
    t0 = time.perf_counter()
    c0 = g.calls
    g.set_charges(sur=g.sur)
    mg = MarginalTariffGame(g)
    prof = [g.plan_from_routes(i, p.routes) for i, p in enumerate(init)]
    sc0 = dip.social_cost(g, prof)
    trace = []
    prof, ok = zmc.br_dynamics(mg, init=prof, max_rounds=max_rounds, trace=trace)
    scs = [sc0] + [dip.social_cost(g, pr) for _, pr in trace]
    return dict(profile=prof, sc=dip.social_cost(g, prof), sc0=sc0, converged=ok, calls=g.calls - c0,
                time_s=time.perf_counter() - t0, payments=mg.payments(prof), sc_path=scs,
                monotone=bool(all(scs[k + 1] <= scs[k] + 1e-9 for k in range(len(scs) - 1))))


# ------------------------------------------------------------------------------------------------ convexified game (tests)


def convexified_response(g, plans, u, iters: int = 20000):
    """Equilibrium aggregate Q(u) of the convexified game over explicit plan lists (one list of Plan objects per
    carrier, priced at zero charges): minimiser of the convexified potential with the charge <u, q> added."""
    pools = []
    for i in range(g.N):
        pl = []
        for p in plans[i]:
            pl.append(type(p)(p.routes, p.q, p.a, p.c + float(u @ p.q), p.cr))
        pools.append(pl)
    W = [[1.0] + [0.0] * (len(pl) - 1) for pl in pools]
    g.set_charges()
    W = zmc._restricted_master(g, pools, W, iters=iters)
    Q = sum(sum(w * p.q for w, p in zip(W[i], pools[i])) for i in range(g.N))
    return Q, W


def convexified_social_optimum(g, plans, iters: int = 20000):
    """Minimiser of the convexified social cost over explicit plan lists (returns aggregate and weights)."""
    so = g.so_variant(False)
    pools = []
    for i in range(g.N):
        pl = []
        for p in plans[i]:
            pl.append(type(p)(p.routes, p.q, p.a, p.cr + float(np.sum(-g.alpha * p.q)), p.cr))
        pools.append(pl)
    W = [[1.0] + [0.0] * (len(pl) - 1) for pl in pools]
    W = zmc._restricted_master(so, pools, W, iters=iters)
    Q = sum(sum(w * p.q for w, p in zip(W[i], pools[i])) for i in range(g.N))
    return Q, W
