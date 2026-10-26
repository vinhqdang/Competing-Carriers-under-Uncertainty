"""Carrier oracle for a sample-based criterion (SAA, type-1 Wasserstein ball, CVaR) in the ZMC + BRL game.

`ccu.zmc_brl.RoutingGame` asks its carrier pool for the minimiser of  sum_r (c_r + sum_{j in r} kappa_j) x_r  over
node-disjoint routes.  With p-box costs the pricing step is exact (BRL).  For a sample-based route cost c_r the dominance
argument of BRL is not valid (the scenario times of a route are not comonotone across sectors), so `HeurPool` replaces
the exact pricing by a heuristic one:

  1. exact BRL pricing for the *surrogate* cost "empirical marginals, unknown dependence" (a p-box without a DKW band),
     which is an upper bound of the SAA cost, so every surrogate-improving column is improving for the true criterion;
  2. local search (insert / remove / swap / relocate / 2-opt) in the prize space of the node duals, started from the
     columns with the smallest reduced cost, with the criterion's own route cost.

Columns are priced with the criterion's own cost c_r (cached), the master LP and the integer packing are those of
`ccu.brl.RoutePool`.  The answer is therefore a heuristic upper bound with no certificate: `PackResult.bound_valid` is
False, and `RoutingGame` records `value_lb = -inf` for it.  The quality of this oracle is checked against complete
enumeration on tiny games (tests/test_ambiguity.py).
"""
from __future__ import annotations

import time

import numpy as np

from . import ambiguity as amb
from . import brl


class HeurPool(brl.RoutePool):
    exact = False  # RoutingGame never replaces this pool's integer step by branch-and-price

    def __init__(self, inst: brl.RoutingInstance, days: np.ndarray, kind: str, *, eps: float = 0.0, alpha: float = 0.9,
                 xmax: float = 3.0, ng_size: int = 8, max_pool: int = 6000, n_local: int = 8):
        self.days = np.asarray(days, float)
        self.kind = kind
        self.eps = float(eps)
        self.alpha = float(alpha)
        self.xmax = float(xmax)
        self.n_local = n_local
        self._tmp: dict = {}
        self._args = dict(kind=kind, eps=eps, alpha=alpha, xmax=xmax, max_pool=max_pool, n_local=n_local)
        if kind == "saa":
            self.crit = amb.make_saa(inst.loss, self.days)
        elif kind == "wass":
            self.crit = amb.make_wass(inst.loss, self.days, eps)
        elif kind == "cvar":
            self.crit = amb.make_cvar(inst.loss, self.days, alpha)
        else:
            raise ValueError(kind)
        w, Q = amb.pbox_levels(self.days, 2.0, self.xmax)  # surrogate: empirical marginals, comonotone
        self.sur = inst.with_pbox(Q, w)
        super().__init__(inst, ng_size=ng_size, max_pool=max_pool)

    # ---- route data
    def _vec(self, r: tuple):
        p = (0, *r, 0)
        tau = self.inst.tau[list(p[:-1]), list(p[1:])].sum(0)
        return tau, float(self.inst.svc[list(r)].sum())

    def _cost(self, r: tuple) -> float:
        if len(set(r)) != len(r):
            return float(self.sur.route_cost(r))  # non-elementary column (never produced here): surrogate bound
        tau, svc = self._vec(r)
        return float(self.crit.fn(tau, svc))

    def fresh(self) -> "HeurPool":
        a = self._args
        return HeurPool(self.inst, self.days, a["kind"], eps=a["eps"], alpha=a["alpha"], xmax=a["xmax"], ng_size=self.inst.n,
                        max_pool=a["max_pool"], n_local=a["n_local"])

    # ---- pricing
    def _price(self, duals: np.ndarray):
        t0 = time.perf_counter()
        inst = self.inst
        n = inst.n
        dem, cap = inst.dem, inst.cap

        def rc(r):
            return self._cost_cached(r) - float(sum(duals[j] for j in r))

        cand: dict = {}
        _, sur_new, _ = brl.espprc(self.sur, duals, ng=self.ng, max_cols=40)
        starts = [r for _, r in sur_new if len(set(r)) == len(r)]
        # columns of the pool with the smallest reduced cost (the LP support has reduced cost 0)
        pool_rc = sorted(self.cols, key=lambda r: self.cols[r] - sum(duals[j] for j in r))[: self.n_local]
        starts += pool_rc
        starts += [(j,) for j in np.argsort(-duals[1:])[:3] + 1]
        seen = set()
        for r0 in starts:
            r0 = tuple(int(v) for v in r0)
            if r0 in seen:
                continue
            seen.add(r0)
            r = self._improve(r0, duals, dem, cap)
            v = rc(r)
            if v < -1e-9 and r not in self.cols:
                cand[r] = v
            v0 = rc(r0)
            if v0 < -1e-9 and r0 not in self.cols:
                cand[r0] = v0
        out = sorted(((v, r) for r, v in cand.items()))[:40]
        best = out[0][0] if out else min([rc(r) for r in pool_rc] + [0.0])
        return float(best), out, {"time": time.perf_counter() - t0, "created": 0, "kept": 0, "overflow": True}

    def _cost_cached(self, r: tuple) -> float:
        c = self.cols.get(r)
        if c is None:
            c = self._tmp.get(r)
            if c is None:
                c = self._cost(r)
                if len(self._tmp) > 50000:
                    self._tmp.clear()
                self._tmp[r] = c
        return c

    def _improve(self, r0: tuple, duals: np.ndarray, dem, cap, max_iter: int = 60) -> tuple:
        """First-improvement local search of one route in the prize space (minimise cost - sum of duals)."""
        n = self.inst.n
        r = list(r0)

        def f(route):
            if not route:
                return 0.0
            t = tuple(route)
            return self._cost_cached(t) - float(sum(duals[j] for j in t))

        cur = f(r)
        for _ in range(max_iter):
            best, bv = None, cur - 1e-9
            load = float(dem[r].sum()) if r else 0.0
            # remove
            for i in range(len(r)):
                c = f(r[:i] + r[i + 1:])
                if c < bv:
                    best, bv = r[:i] + r[i + 1:], c
            # insert
            for j in range(1, n + 1):
                if j in r or load + dem[j] > cap + 1e-12 or duals[j] <= 0:
                    continue
                for q in range(len(r) + 1):
                    nr = r[:q] + [j] + r[q:]
                    c = f(nr)
                    if c < bv:
                        best, bv = nr, c
            # swap a route node for an outside node
            for i in range(len(r)):
                for j in range(1, n + 1):
                    if j in r or load - dem[r[i]] + dem[j] > cap + 1e-12:
                        continue
                    nr = r[:i] + [j] + r[i + 1:]
                    c = f(nr)
                    if c < bv:
                        best, bv = nr, c
            # relocate inside the route and 2-opt
            for i in range(len(r)):
                rest = r[:i] + r[i + 1:]
                for q in range(len(rest) + 1):
                    if q == i:
                        continue
                    nr = rest[:q] + [r[i]] + rest[q:]
                    c = f(nr)
                    if c < bv:
                        best, bv = nr, c
            for a in range(len(r)):
                for b in range(a + 2, len(r) + 1):
                    nr = r[:a] + r[a:b][::-1] + r[b:]
                    c = f(nr)
                    if c < bv:
                        best, bv = nr, c
            if best is None:
                break
            r, cur = best, bv
        return tuple(r)
