"""CVRP heuristic under the robust route cost: Clarke-Wright savings plus local search."""
from __future__ import annotations

import numpy as np

from .instance import Instance, arc_time_tensor, sector_index
from .robust import LossParams, route_loss_stats

EPS = 1e-12


class RouteModel:
    """Per-carrier memoised route times and costs. Node 0 is the depot, node j+1 is local customer j."""

    def __init__(self, inst: Instance, i: int) -> None:
        self.inst, self.i = inst, i
        xy = np.vstack([inst.depots[i], inst.customers[i]])
        self.A = arc_time_tensor(inst, xy)  # (n+1, n+1, K)
        self.svc = np.zeros((len(xy), inst.K))
        self.svc[1:] = np.eye(inst.K)[sector_index(inst.K, xy[1:])] * inst.service
        self.D = self.A.sum(-1)  # arc travel times, used for savings
        self.loss: LossParams = inst.loss()
        self.true_mean = inst.true_samples.mean(0)
        self._tau: dict[tuple[int, ...], np.ndarray] = {}
        self._cost: dict[tuple, float] = {}

    def tau(self, route: tuple[int, ...]) -> np.ndarray:
        """Base time per sector of the depot-route-depot tour."""
        t = self._tau.get(route)
        if t is None:
            p = np.array((0, *(j + 1 for j in route), 0))
            t = self.A[p[:-1], p[1:]].sum(0) + self.svc[p].sum(0)
            self._tau[route] = t
        return t

    def cost(self, route: tuple[int, ...], mode: str = "robust", eps: float | None = None) -> float:
        """Route cost: 'robust' (radius eps, default inst.eps[i]), 'nominal' (empirical) or 'true'."""
        if not route:
            return 0.0
        key = (route, mode, eps)
        v = self._cost.get(key)
        if v is None:
            inst, i = self.inst, self.i
            if mode == "robust":
                samples = inst.samples[i]
                e = float(inst.eps[i]) if eps is None else eps
            elif mode == "nominal":
                samples, e = inst.samples[i], 0.0
            elif mode == "true":
                samples, e = inst.true_samples, 0.0
            else:
                raise ValueError(f"unknown mode {mode!r}")
            v = float(route_loss_stats(self.tau(route), self.loss, samples, e)[1])
            self._cost[key] = v
        return v


def route_model(inst: Instance, i: int) -> RouteModel:
    """Cached RouteModel of carrier i."""
    key = ("model", i)
    if key not in inst._cache:
        inst._cache[key] = RouteModel(inst, i)
    return inst._cache[key]


def cheapest_insertion(
    m: RouteModel, routes: list[list[int]], c: int, mode: str, eps: float | None
) -> tuple[float, int, int]:
    """Cheapest feasible insertion of customer c: (cost delta, route index or -1 for new route, position)."""
    best = (m.cost((c,), mode, eps), -1, 0)
    for ri, r in enumerate(routes):
        if len(r) >= m.inst.Q:
            continue
        base = m.cost(tuple(r), mode, eps)
        for pos in range(len(r) + 1):
            d = m.cost(tuple(r[:pos]) + (c,) + tuple(r[pos:]), mode, eps) - base
            if d < best[0]:
                best = (d, ri, pos)
    return best


def _clarke_wright(m: RouteModel, cset: list[int], Q: int) -> list[list[int]]:
    """Parallel Clarke-Wright savings on travel times, respecting capacity Q."""
    pairs = []
    for x, a in enumerate(cset):
        for b in cset[x + 1 :]:
            s = m.D[0, a + 1] + m.D[0, b + 1] - m.D[a + 1, b + 1]
            if s > 0:
                pairs.append((float(s), a, b))
    pairs.sort(key=lambda t: (-t[0], t[1], t[2]))
    routes = {j: [j] for j in cset}
    rid = {j: j for j in cset}
    for _, a, b in pairs:
        ra, rb = rid[a], rid[b]
        if ra == rb:
            continue
        A, B = routes[ra], routes[rb]
        if len(A) + len(B) > Q:
            continue
        if A[-1] != a:
            if A[0] != a:
                continue
            A.reverse()
        if B[0] != b:
            if B[-1] != b:
                continue
            B.reverse()
        routes[ra] = A + B
        del routes[rb]
        for j in B:
            rid[j] = ra
    return list(routes.values())


def _repair(
    m: RouteModel, routes: list[list[int]], cset: list[int], mode: str, eps: float | None
) -> list[list[int]]:
    """Restrict a warm-start solution to cset and insert uncovered customers cheapest-first."""
    keep = set(cset)
    out = [[j for j in r if j in keep] for r in routes]
    out = [r for r in out if r]
    seen = {j for r in out for j in r}
    for c in cset:
        if c in seen:
            continue
        _, ri, pos = cheapest_insertion(m, out, c, mode, eps)
        if ri < 0:
            out.append([c])
        else:
            out[ri].insert(pos, c)
    return out


def _two_opt(routes: list[list[int]], c) -> bool:
    for ri, r in enumerate(routes):
        base = c(r)
        for a in range(len(r) - 1):
            for b in range(a + 1, len(r)):
                cand = r[:a] + r[a : b + 1][::-1] + r[b + 1 :]
                if c(cand) < base - EPS:
                    routes[ri] = cand
                    return True
    return False


def _relocate(routes: list[list[int]], c, Q: int) -> bool:
    for ia, a in enumerate(routes):
        for k, cust in enumerate(a):
            a_wo = a[:k] + a[k + 1 :]
            save = c(a) - c(a_wo)
            for ib, b in enumerate(routes):
                if ib == ia or len(b) >= Q:
                    continue
                cb = c(b)
                for pos in range(len(b) + 1):
                    nb = b[:pos] + [cust] + b[pos:]
                    if c(nb) - cb < save - EPS:
                        routes[ia], routes[ib] = a_wo, nb
                        return True
    return False


def _swap(routes: list[list[int]], c) -> bool:
    for ia in range(len(routes)):
        for ib in range(ia + 1, len(routes)):
            a, b = routes[ia], routes[ib]
            base = c(a) + c(b)
            for x in range(len(a)):
                for y in range(len(b)):
                    na = a[:x] + [b[y]] + a[x + 1 :]
                    nb = b[:y] + [a[x]] + b[y + 1 :]
                    if c(na) + c(nb) < base - EPS:
                        routes[ia], routes[ib] = na, nb
                        return True
    return False


def _local_search(
    m: RouteModel, routes: list[list[int]], mode: str, eps: float | None,
    rng: np.random.Generator, Q: int,
) -> list[list[int]]:
    """First-improvement 2-opt, relocate and swap until no move lowers the total cost."""

    def c(r: list[int]) -> float:
        return m.cost(tuple(r), mode, eps)

    for _ in range(10_000):
        routes[:] = [r for r in routes if r]
        order = rng.permutation(len(routes))
        routes[:] = [routes[k] for k in order]
        if _two_opt(routes, c) or _relocate(routes, c, Q) or _swap(routes, c):
            continue
        break
    return [r for r in routes if r]


def solve_cvrp(
    inst: Instance,
    i: int,
    customers_idx: list[int] | np.ndarray,
    eps: float | None = None,
    rng: np.random.Generator | None = None,
    mode: str = "robust",
    init: list[list[int]] | None = None,
) -> tuple[list[list[int]], float]:
    """Route carrier i's customers (local indices) minimising the mode cost.

    mode: 'robust' (radius eps, default inst.eps[i]), 'nominal' (eps=0 on carrier data) or
    'true' (expected loss on the true law). init: optional warm-start routes.
    Returns (routes, total cost); an empty customer set gives ([], 0.0).
    """
    cset = [int(j) for j in customers_idx]
    if not cset:
        return [], 0.0
    m = route_model(inst, i)
    rng = rng or np.random.default_rng(0)
    if init is None:
        routes = _clarke_wright(m, cset, inst.Q)
    else:
        routes = _repair(m, init, cset, mode, eps)
    routes = _local_search(m, routes, mode, eps, rng, inst.Q)
    return routes, sum(m.cost(tuple(r), mode, eps) for r in routes)
