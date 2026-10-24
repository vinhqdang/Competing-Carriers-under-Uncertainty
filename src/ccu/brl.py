"""Budget-Resource Labelling (BRL) pricing and a packing column-generation / price-and-branch solver.

This is a compiled (numba) port of the exact functional-dominance pricer of theory/new_algorithm_B/prototype.py
(`espprc(..., rule="functional")`) plus the surrounding column generation, so that a carrier's routing plan can be
re-solved thousands of times inside an equilibrium computation.  The labelling logic is identical to the prototype
(same dominance rule, same completion window, same ng-route memory); `tests/test_brl.py` checks it against the
prototype and against complete enumeration.

Model of one carrier (see docs/EXPERIMENTS.md, Section 2):
  * nodes 1..n are customer zones (all-or-nothing lots), node 0 is the depot;
  * the arc time between two nodes is a nonnegative combination of K sector multipliers, each with a p-box
    (DKW band) quantile function on a common level grid; the dependence between sectors is unknown, so the route
    time at level l is the comonotone sum  S_l = sum_a q_a[l]  (Theorem 2.1 of the BRL theory);
  * the route loss is convex piecewise linear, phi(T) = fixed + gamma*T + rho*max(0, T - Tmax), and its upper
    expectation is  c_r = fixed + gamma * sum_l w_l S_l + rho * sum_l w_l max(S_l - Tmax, 0);
  * a plan is a set of node-disjoint routes; every served node carries an additive node cost kappa_j (prices,
    prizes), so the carrier's problem is a prize-collecting set-packing problem
        min  sum_r (c_r + sum_{j in r} kappa_j) x_r   s.t.  sum_{r : j in r} x_r <= 1,  x binary.

`RoutePool.solve` runs column generation with BRL pricing to LP convergence (this gives a valid lower bound under
the ng-route relaxation when pricing is not truncated) and then solves the integer packing over the generated
elementary columns (price-and-branch without branching): an upper bound.  The result is therefore an *oracle with
a certified gap*, not a proven integer optimum.  That is the main approximation of the integration.
An exact integer step (branch-and-price on arc flows and fleet size, same pricer) is in `ccu.bp`.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np
from numba import njit
from scipy.optimize import Bounds, LinearConstraint, linprog, milp

# ---------------------------------------------------------------------------------------------------------------
# p-boxes
# ---------------------------------------------------------------------------------------------------------------


def dkw_eps(n: int, alpha: float) -> float:
    """DKW half-width sqrt(ln(2/alpha) / (2n)); alpha >= 2 gives 0 (empirical law, no band)."""
    return math.sqrt(max(math.log(2.0 / alpha), 0.0) / (2.0 * n))


def dkw_upper_quantile(x: np.ndarray, alpha: float, xmax: float) -> tuple[np.ndarray, np.ndarray]:
    """Upper quantile function of the DKW lower CDF max(F_n - eps, 0), capped at the support bound xmax.

    Returns (right ends of the constancy intervals, values), a left-continuous step function on (0, 1].
    """
    x = np.sort(np.asarray(x, float))
    n = len(x)
    eps = dkw_eps(n, alpha)
    ends, vals = [], []
    for j in range(1, n + 1):
        u = j / n - eps
        if u <= 1e-12:
            continue
        if u >= 1.0 - 1e-12:
            break
        ends.append(u)
        vals.append(x[j - 1])
    ends.append(1.0)
    vals.append(max(xmax, x[-1]))
    return np.array(ends), np.array(vals)


def common_grid(qfs):
    """Merge step quantile functions onto the union of their breakpoints: (u_left, w, Q[k, l])."""
    ends = np.unique(np.round(np.concatenate([e for e, _ in qfs] + [np.array([1.0])]), 13))
    ends = ends[(ends > 0) & (ends <= 1.0)]
    left = np.concatenate([[0.0], ends[:-1]])
    w = ends - left
    mid = (left + ends) / 2
    Q = np.empty((len(qfs), len(ends)))
    for k, (e, v) in enumerate(qfs):
        idx = np.searchsorted(e, mid, side="left")
        Q[k] = v[np.minimum(idx, len(v) - 1)]
    return left, w, Q


@dataclass
class Loss:
    """phi(T) = fixed + gamma*T + rho*max(0, T - Tmax)."""

    gamma: float
    rho: float
    Tmax: float
    fixed: float = 0.0


def cost_profile(S: np.ndarray, w: np.ndarray, loss: Loss) -> float:
    """Upper expectation of the loss for the comonotone route-time profile S (level values, ascending)."""
    return loss.fixed + loss.gamma * float(w @ S) + loss.rho * float(w @ np.maximum(S - loss.Tmax, 0.0))


# ---------------------------------------------------------------------------------------------------------------
# routing instance of one carrier
# ---------------------------------------------------------------------------------------------------------------


@dataclass
class RoutingInstance:
    """Depot (node 0) plus n customer nodes.

    tau[i, j, k]: base time (s) of arc (i, j) attributed to sector k.  svc[j]: deterministic service time at j (s).
    Qk[k, l]: sector multiplier quantiles on the common level grid with weights w[l].
    """

    n: int
    tau: np.ndarray
    svc: np.ndarray
    dem: np.ndarray
    cap: float
    Qk: np.ndarray
    w: np.ndarray
    loss: Loss
    arcS: np.ndarray = field(init=False)
    Cmin: np.ndarray = field(init=False)
    wsuf: np.ndarray = field(init=False)

    def __post_init__(self):
        self.arcS = np.einsum("ijk,kl->ijl", self.tau, self.Qk) + self.svc[None, :, None]
        c0 = self.arcS[:, :, 0].copy()
        np.fill_diagonal(c0, np.inf)
        dist = c0[:, 0].copy()
        dist[0] = 0.0
        for _ in range(self.n + 1):
            dist = np.minimum(dist, np.min(c0 + dist[None, :], axis=1))
            dist[0] = 0.0
        self.Cmin = dist
        self.wsuf = np.concatenate([np.cumsum(self.w[::-1])[::-1], [0.0]])

    def profile(self, route) -> np.ndarray:
        p = (0, *route, 0)
        return sum(self.arcS[p[t], p[t + 1]] for t in range(len(p) - 1))

    def route_cost(self, route) -> float:
        return cost_profile(self.profile(route), self.w, self.loss)

    def with_pbox(self, Qk: np.ndarray, w: np.ndarray) -> "RoutingInstance":
        return RoutingInstance(self.n, self.tau, self.svc, self.dem, self.cap, Qk, w, self.loss)


def ng_masks(inst: RoutingInstance, size: int = 8) -> np.ndarray:
    """ng-neighbourhood bit masks (nearest `size` customers by symmetric mean time); size >= n gives elementary."""
    D = inst.tau.sum(-1)
    ng = np.zeros(inst.n + 1, dtype=np.uint64)
    for i in range(1, inst.n + 1):
        near = list(np.argsort(D[i, 1:] + D[1:, i]) + 1)[:size]
        m = 1 << i
        for j in near:
            m |= 1 << int(j)
        ng[i] = np.uint64(m)
    return ng


# ---------------------------------------------------------------------------------------------------------------
# compiled labelling
# ---------------------------------------------------------------------------------------------------------------


@njit(cache=True)
def _feval(S, WS, pi, D, wsuf, gamma, rho):
    L = S.shape[0]
    lo = 0
    hi = L
    while lo < hi:
        mid = (lo + hi) // 2
        if S[mid] <= D:
            lo = mid + 1
        else:
            hi = mid
    return gamma * WS[0] + rho * (WS[lo] - D * wsuf[lo]) - pi


@njit(cache=True)
def _dominates(Sa, WSa, pia, Sb, WSb, pib, hi_lim, wsuf, gamma, rho, tol):
    L = Sa.shape[0]
    hi = min(Sb[L - 1], hi_lim)
    lo = min(Sb[0], hi)
    if _feval(Sa, WSa, pia, lo, wsuf, gamma, rho) > _feval(Sb, WSb, pib, lo, wsuf, gamma, rho) + tol:
        return False
    if _feval(Sa, WSa, pia, hi, wsuf, gamma, rho) > _feval(Sb, WSb, pib, hi, wsuf, gamma, rho) + tol:
        return False
    for k in range(L):
        v = Sa[k]
        if v > lo and v < hi:
            if _feval(Sa, WSa, pia, v, wsuf, gamma, rho) > _feval(Sb, WSb, pib, v, wsuf, gamma, rho) + tol:
                return False
        v = Sb[k]
        if v > lo and v < hi:
            if _feval(Sa, WSa, pia, v, wsuf, gamma, rho) > _feval(Sb, WSb, pib, v, wsuf, gamma, rho) + tol:
                return False
    return True


@njit(cache=True)
def _espprc_nb(n, L, arcS, dem, cap, w, wsuf, gamma, rho, Tmax, fixed, Cmin, ng, duals, maxlab, bcap, kcols, tol_rc,
               allow):
    Sarr = np.empty((maxlab, L))
    WSarr = np.empty((maxlab, L + 1))
    node = np.empty(maxlab, np.int32)
    mask = np.empty(maxlab, np.uint64)
    load = np.empty(maxlab)
    pil = np.empty(maxlab)
    pred = np.empty(maxlab, np.int32)
    alive = np.zeros(maxlab, np.bool_)
    bk = np.empty((n + 1, bcap), np.int32)
    bc = np.zeros(n + 1, np.int64)
    tS = np.empty(L)
    tWS = np.empty(L + 1)
    cand_rc = np.full(kcols, 1e300)
    cand_lab = np.full(kcols, -1, np.int32)
    best = 1e300
    created = 0
    overflow = False
    # start label
    node[0] = 0
    mask[0] = np.uint64(0)
    load[0] = 0.0
    pil[0] = 0.0
    pred[0] = -1
    alive[0] = True
    for l in range(L):
        Sarr[0, l] = 0.0
    for l in range(L + 1):
        WSarr[0, l] = 0.0
    nlab = 1
    head = 0
    one = np.uint64(1)
    while head < nlab:
        lab = head
        head += 1
        if not alive[lab]:
            continue
        i = node[lab]
        if i != 0 and allow[i, 0]:
            tot = 0.0
            over = 0.0
            for l in range(L):
                s = Sarr[lab, l] + arcS[i, 0, l]
                tot += w[l] * s
                if s > Tmax:
                    over += w[l] * (s - Tmax)
            rc = fixed + gamma * tot + rho * over - pil[lab]
            if rc < best:
                best = rc
            if rc < -tol_rc:
                worst = 0
                for c in range(1, kcols):
                    if cand_rc[c] > cand_rc[worst]:
                        worst = c
                if rc < cand_rc[worst]:
                    cand_rc[worst] = rc
                    cand_lab[worst] = lab
        for j in range(1, n + 1):
            if (mask[lab] >> np.uint64(j)) & one:
                continue
            if not allow[i, j]:
                continue
            if load[lab] + dem[j] > cap + 1e-12:
                continue
            for l in range(L):
                tS[l] = Sarr[lab, l] + arcS[i, j, l]
            acc = 0.0
            for l in range(L - 1, -1, -1):
                acc += w[l] * tS[l]
                tWS[l] = acc
            tWS[L] = 0.0
            npi = pil[lab] + duals[j]
            nload = load[lab] + dem[j]
            nmask = (mask[lab] & ng[j]) | (one << np.uint64(j))
            created += 1
            hi_lim = Tmax - Cmin[j]
            dom = False
            cnt = bc[j]
            for t in range(cnt):
                o = bk[j, t]
                if load[o] > nload + 1e-9:
                    continue
                if (mask[o] & ~nmask) != np.uint64(0):
                    continue
                if _dominates(Sarr[o], WSarr[o], pil[o], tS, tWS, npi, hi_lim, wsuf, gamma, rho, 1e-9):
                    dom = True
                    break
            if dom:
                continue
            # kill dominated
            t = 0
            while t < bc[j]:
                o = bk[j, t]
                if nload <= load[o] + 1e-9 and (nmask & ~mask[o]) == np.uint64(0):
                    if _dominates(tS, tWS, npi, Sarr[o], WSarr[o], pil[o], Tmax - Cmin[j], wsuf, gamma, rho, 1e-9):
                        alive[o] = False
                        bk[j, t] = bk[j, bc[j] - 1]
                        bc[j] -= 1
                        continue
                t += 1
            if nlab >= maxlab or bc[j] >= bcap:
                overflow = True
                break
            nid = nlab
            nlab += 1
            node[nid] = j
            mask[nid] = nmask
            load[nid] = nload
            pil[nid] = npi
            pred[nid] = lab
            alive[nid] = True
            for l in range(L):
                Sarr[nid, l] = tS[l]
            for l in range(L + 1):
                WSarr[nid, l] = tWS[l]
            bk[j, bc[j]] = nid
            bc[j] += 1
        if overflow:
            break
    kept = 0
    for j in range(1, n + 1):
        kept += bc[j]
    # reconstruct routes
    routes = np.zeros((kcols, n), np.int32)
    rlen = np.zeros(kcols, np.int32)
    for c in range(kcols):
        lab = cand_lab[c]
        if lab < 0:
            continue
        tmp = np.empty(n + 2, np.int32)
        m = 0
        x = lab
        while x >= 0 and node[x] != 0:
            tmp[m] = node[x]
            m += 1
            x = pred[x]
        rlen[c] = m
        for t in range(m):
            routes[c, t] = tmp[m - 1 - t]
    return best, cand_rc, routes, rlen, created, kept, overflow


def espprc(inst: RoutingInstance, duals: np.ndarray, *, ng: np.ndarray | None = None, max_cols: int = 40,
           maxlab: int = 200_000, tol_rc: float = 1e-9, allow: np.ndarray | None = None,
           Cmin: np.ndarray | None = None, fixed_shift: float = 0.0):
    """BRL pricing with node duals (reduced cost = route cost - sum_j duals[j]).

    `allow[i, j]` (bool, (n+1) x (n+1)) removes arcs (branching in ccu.bp); `Cmin` is then the shortest return time on the
    allowed arcs (a smaller-or-equal value is always valid).  `fixed_shift` is added to every route's reduced cost
    (the dual of a fleet-size row).
    Returns (best reduced cost over all routes, [(rc, route)] sorted, stats).  `overflow=True` in stats means the
    label limit was hit and the result is not a certificate.
    """
    n = inst.n
    L = inst.Qk.shape[1]
    if ng is None:
        ng = ng_masks(inst, n)
    ls = inst.loss
    if allow is None:
        allow = np.ones((n + 1, n + 1), np.bool_)
    if Cmin is None:
        Cmin = inst.Cmin
    t0 = time.perf_counter()
    best, crc, rts, rl, created, kept, overflow = _espprc_nb(
        n, L, inst.arcS, inst.dem.astype(np.float64), float(inst.cap), inst.w, inst.wsuf, ls.gamma, ls.rho, ls.Tmax,
        ls.fixed + fixed_shift, np.asarray(Cmin, float), ng.astype(np.uint64), np.asarray(duals, float), maxlab, 4096, max_cols,
        tol_rc, np.asarray(allow, np.bool_))
    out = []
    for c in np.argsort(crc):
        if rl[c] > 0 and crc[c] < 1e299:
            out.append((float(crc[c]), tuple(int(v) for v in rts[c, : rl[c]])))
    return float(best), out, {"time": time.perf_counter() - t0, "created": int(created), "kept": int(kept),
                              "overflow": bool(overflow)}


# ---------------------------------------------------------------------------------------------------------------
# column generation + price-and-branch over a persistent route pool
# ---------------------------------------------------------------------------------------------------------------


@dataclass
class PackResult:
    routes: list  # selected routes (tuples of node ids)
    value: float  # integer objective (upper bound)
    lp: float  # LP value at convergence (lower bound if `bound_valid`)
    bound_valid: bool
    n_pricing: int
    n_cols: int
    pricing_time: float


class RoutePool:
    """Persistent column pool of one carrier.  Route costs do not depend on prices, so columns are reused."""

    def __init__(self, inst: RoutingInstance, ng_size: int = 8, max_pool: int = 6000):
        self.inst = inst
        self.ng = ng_masks(inst, ng_size)
        self.max_pool = max_pool
        self.cols: dict[tuple, float] = {}
        self.calls = 0
        for j in range(1, inst.n + 1):
            self._add((j,))

    def _add(self, r: tuple) -> bool:
        if r in self.cols:
            return False
        self.cols[r] = self.inst.route_cost(r)
        return True

    def reset(self):
        self.cols = {}
        for j in range(1, self.inst.n + 1):
            self._add((j,))

    def _matrix(self, routes):
        A = np.zeros((self.inst.n, len(routes)))
        for k, r in enumerate(routes):
            for j in r:
                A[j - 1, k] += 1.0
        return A

    def solve(self, kappa: np.ndarray, *, tol: float = 1e-6, max_iter: int = 400, integer: bool = True,
              mip_gap: float = 1e-7, mip_time: float = 20.0) -> PackResult:
        """kappa[j] (j = 1..n): additive node cost when j is served (kappa[0] ignored)."""
        inst = self.inst
        n = inst.n
        kap = np.asarray(kappa, float).copy()
        kap[0] = 0.0
        ng = self.ng
        valid = True
        npr, ptime = 0, 0.0
        lp = 0.0
        for it in range(max_iter):
            routes = list(self.cols)
            A = self._matrix(routes)
            c = np.array([self.cols[r] for r in routes]) + kap[1:] @ A
            res = linprog(c, A_ub=A, b_ub=np.ones(n), bounds=(0, None), method="highs")
            lp = float(res.fun)
            u = -res.ineqlin.marginals  # >= 0
            duals = np.concatenate([[0.0], -(u + kap[1:])])
            best, new, st = espprc(inst, duals, ng=ng, max_cols=40)
            npr += 1
            ptime += st["time"]
            self.calls += 1
            if st["overflow"]:
                valid = False
            if best > -tol * (1.0 + abs(lp)) or not new:
                break
            added = 0
            for rc, r in new:
                if rc < -tol and self._add(r):
                    added += 1
            if added == 0:
                break
        else:
            valid = False
        # ---- integer step: packing MILP over the generated elementary columns.  Columns whose LP reduced cost
        # exceeds the gap to a greedy incumbent cannot be in any better integer solution (reduced-cost fixing), so
        # they are dropped before the MILP; this keeps the MILP tiny and the answer optimal over the pool.
        if integer:
            x = res.x
            rcost = c + u @ A  # reduced costs of the LP columns (>= 0 at convergence)
            order = np.argsort(-x)
            used = np.zeros(n, bool)
            ub0 = 0.0
            for k in order:
                if x[k] <= 1e-9:
                    break
                cols = [j - 1 for j in routes[k]]
                if len(set(cols)) == len(cols) and not used[cols].any() and c[k] < 0:
                    used[cols] = True
                    ub0 += c[k]
            if np.all((x < 1e-7) | (x > 1 - 1e-7)):
                ub0 = min(ub0, lp + 1e-9) if ub0 <= lp + 1e-7 else ub0
            gap = max(ub0 - lp, 0.0) + 1e-7
            keep = [k for k in range(len(routes)) if rcost[k] <= gap and len(set(routes[k])) == len(routes[k])]
            elem = [routes[k] for k in keep]
            if not elem:
                sel, val = [], 0.0
            else:
                A2 = A[:, keep]
                c2 = c[keep]
                m = milp(c2, constraints=LinearConstraint(A2, ub=np.ones(n)), integrality=np.ones(len(elem)),
                         bounds=Bounds(0, 1), options={"time_limit": mip_time, "mip_rel_gap": mip_gap})
                if m.x is None:
                    sel, val = [], 0.0
                else:
                    sel = [elem[k] for k in np.flatnonzero(m.x > 0.5)]
                    val = float(sum(self.cols[r] + sum(kap[j] for j in r) for r in sel))
                if val > 0.0 or m.x is None:
                    sel, val = [], 0.0  # the empty plan is always feasible
        else:
            sel, val = [], lp
        if len(self.cols) > self.max_pool:
            self._prune(sel)
        return PackResult(sel, val, lp, valid, npr, len(self.cols), ptime)

    def _prune(self, keep_routes):
        """Drop the longest-unused-looking columns (here: keep singletons, the selected routes and the cheapest)."""
        keep = {r for r in self.cols if len(r) == 1} | set(keep_routes)
        rest = sorted((r for r in self.cols if r not in keep), key=lambda r: self.cols[r] / max(len(r), 1))
        for r in rest[: self.max_pool // 2]:
            keep.add(r)
        self.cols = {r: v for r, v in self.cols.items() if r in keep}


def enumerate_best_routes(inst: RoutingInstance):
    """All elementary capacity-feasible routes (best visiting order per customer subset) with exact robust cost."""
    best: dict[frozenset, tuple[float, tuple]] = {}
    stack = [((), 0.0)]
    while stack:
        r, load = stack.pop()
        if r:
            key = frozenset(r)
            c = inst.route_cost(r)
            if key not in best or c < best[key][0]:
                best[key] = (c, r)
        for j in range(1, inst.n + 1):
            if j not in r and load + inst.dem[j] <= inst.cap + 1e-12:
                stack.append((r + (j,), load + inst.dem[j]))
    return best


def exact_pack_by_enumeration(inst: RoutingInstance, kappa: np.ndarray, subsets=None):
    """Brute-force optimum of the packing problem (all subsets partitioned into routes), for tests on tiny n."""
    best = enumerate_best_routes(inst) if subsets is None else subsets
    keys = list(best)
    routes = [best[k][1] for k in keys]
    A = np.zeros((inst.n, len(routes)))
    for k, r in enumerate(routes):
        for j in r:
            A[j - 1, k] = 1.0
    c = np.array([best[k][0] for k in keys]) + np.asarray(kappa, float)[1:] @ A
    m = milp(c, constraints=LinearConstraint(A, ub=np.ones(inst.n)), integrality=np.ones(len(routes)), bounds=Bounds(0, 1))
    sel = [routes[k] for k in np.flatnonzero(m.x > 0.5)]
    return float(min(m.fun, 0.0)), sel
