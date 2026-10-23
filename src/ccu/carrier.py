"""Carrier plans, the cost J_i and a multi-start best response over diversion sets."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .instance import Instance
from .routing import cheapest_insertion, route_model, solve_cvrp

TOL = 1e-9


@dataclass
class Plan:
    """Carrier plan: diverted local customer indices, doorstep routes and their costs."""

    diverted: frozenset[int]
    routes: list[list[int]]
    base_cost: float  # robust routing cost c_i(pi; eps_i)
    true_cost: float  # expected routing cost on the true law
    usage: np.ndarray  # (Z,) hub usage u_iz
    vehicle_time: float  # expected total vehicle time


def as_price(inst: Instance, p: float | np.ndarray) -> np.ndarray:
    """Broadcast a scalar or per-hub price to shape (Z,)."""
    return np.broadcast_to(np.asarray(p, dtype=float), (inst.Z,)).astype(float)


def diversion_total(inst: Instance, i: int, diverted: frozenset[int]) -> float:
    """Sum of a_ij over the diverted set."""
    if not diverted:
        return 0.0
    idx = np.fromiter(diverted, dtype=int, count=len(diverted))
    return float(inst.diversion_cost(i)[idx].sum())


def make_plan(
    inst: Instance,
    i: int,
    diverted: frozenset[int] | set[int],
    mode: str = "robust",
    rng: np.random.Generator | None = None,
    init: list[list[int]] | None = None,
) -> Plan:
    """Plan for diversion set D: CVRP on the complement (cached per carrier, mode and D)."""
    D = frozenset(int(j) for j in diverted)
    cache = inst._cache.setdefault(("plan", i, mode), {})
    if D in cache:
        return cache[D]
    m = route_model(inst, i)
    served = [j for j in range(len(inst.customers[i])) if j not in D]
    routes, _ = solve_cvrp(inst, i, served, None, rng, mode, init)
    zones = inst.zone_of[i][np.fromiter(D, dtype=int, count=len(D))]
    usage = np.bincount(zones, minlength=inst.Z).astype(float)
    tau_sum = np.zeros(inst.K)
    for r in routes:
        tau_sum += m.tau(tuple(r))
    plan = Plan(
        diverted=D,
        routes=routes,
        base_cost=sum(m.cost(tuple(r), "robust") for r in routes),
        true_cost=sum(m.cost(tuple(r), "true") for r in routes),
        usage=usage,
        vehicle_time=float(tau_sum @ m.true_mean),
    )
    cache[D] = plan
    return plan


def objective(
    inst: Instance, i: int, plan: Plan, load_others: np.ndarray, p: np.ndarray, kind: str = "J"
) -> float:
    """J_i (kind 'J') or the carrier's share of social cost (kind 'SC', exact potential for SC)."""
    u, b, C = plan.usage, inst.beta, inst.C
    div = diversion_total(inst, i, plan.diverted)
    if kind == "J":
        return plan.base_cost + div + float(np.sum(p * u + b / C * u * (load_others + u)))
    cong = np.sum(b / C * ((load_others + u) ** 2 - load_others**2))
    return plan.true_cost + div + float(cong) + inst.phi * plan.vehicle_time


def plan_cost_J(inst: Instance, i: int, plan: Plan, load_others: np.ndarray, p) -> float:
    """Carrier cost J_i(pi_i, pi_-i) of DESIGN.md Section 2."""
    return objective(inst, i, plan, np.asarray(load_others, float), as_price(inst, p), "J")


def plan_cost_SC(inst: Instance, i: int, plan: Plan, load_others: np.ndarray) -> float:
    """Carrier's contribution to social cost given others' loads (true costs, no price)."""
    return objective(inst, i, plan, np.asarray(load_others, float), np.zeros(inst.Z), "SC")


def evaluate_plan_true(inst: Instance, i: int, plan: Plan) -> tuple[float, float]:
    """(true expected routing plus diversion cost, expected vehicle time) of a plan."""
    return plan.true_cost + diversion_total(inst, i, plan.diverted), plan.vehicle_time


def _estimates(
    inst: Instance, i: int, plan: Plan, Lo: np.ndarray, p: np.ndarray, kind: str, mode: str
) -> list[tuple[float, int]]:
    """Cheap ranking of single-customer toggles: exact diversion and congestion terms, estimated routing."""
    m = route_model(inst, i)
    a, zones, b, C = inst.diversion_cost(i), inst.zone_of[i], inst.beta, inst.C
    u = plan.usage

    def g(v: np.ndarray) -> np.ndarray:
        return p * v + b / C * v * (Lo + v) if kind == "J" else b / C * (Lo + v) ** 2

    owner: dict[int, int] = {}
    for ri, r in enumerate(plan.routes):
        for j in r:
            owner[j] = ri
    est = []
    for j in range(len(a)):
        z = int(zones[j])
        if j in plan.diverted:
            s = -1.0
            d_route = cheapest_insertion(m, plan.routes, j, mode, None)[0]
            d_div = -a[j]
        else:
            s = 1.0
            r = plan.routes[owner[j]]
            rest = [x for x in r if x != j]
            d_route = m.cost(tuple(rest), mode) - m.cost(tuple(r), mode)
            d_div = a[j]
        u2 = u.copy()
        u2[z] += s
        d_cong = float(g(u2)[z] - g(u)[z])
        est.append((d_route + d_div + d_cong, j))
    est.sort()
    return est


def _try_sets(
    inst: Instance, i: int, sets: list[frozenset[int]], Lo: np.ndarray, price: np.ndarray,
    kind: str, mode: str, rng: np.random.Generator, val: float, routes: list[list[int]],
) -> tuple[float, Plan] | None:
    """Best strictly improving plan among candidate diversion sets (warm-started from routes)."""
    best = None
    for D in sets:
        cand = make_plan(inst, i, D, mode, rng, routes)
        v = objective(inst, i, cand, Lo, price, kind)
        if v < val - TOL and (best is None or v < best[0]):
            best = (v, cand)
    return best


def best_response(
    inst: Instance,
    i: int,
    load_others: np.ndarray,
    p: float | np.ndarray,
    rng: np.random.Generator | None = None,
    starts: int = 3,
    kind: str = "J",
    init: Plan | None = None,
    k: int = 3,
) -> Plan:
    """Heuristic best response of carrier i over diversion sets.

    Each start runs descent with three neighbourhoods, tried in order until one improves:
    the top-k single toggles ranked by estimate (routing re-solved exactly), whole-route
    diversion blocks (captures the fixed-cost saving of emptying a route), and one-for-one
    swaps. Start 0 is `init` (or all-doorstep), start 1 divert-all, later starts random masks.
    kind 'J' minimises J_i under price p; kind 'SC' minimises the social-cost share (p ignored).
    """
    rng = rng or np.random.default_rng(0)
    mode = "robust" if kind == "J" else "true"
    Lo = np.asarray(load_others, dtype=float)
    price = np.zeros(inst.Z) if kind == "SC" else as_price(inst, p)
    n = len(inst.customers[i])
    all_set = frozenset(range(n))
    best, best_val = None, np.inf
    for s in range(starts):
        if s == 0:
            if init is not None:
                cur = make_plan(inst, i, init.diverted, mode, rng, init.routes)
            else:
                cur = make_plan(inst, i, frozenset(), mode, rng)
        elif s == 1:
            cur = make_plan(inst, i, all_set, mode, rng)
        else:
            mask = rng.random(n) < rng.uniform(0.1, 0.6)
            cur = make_plan(inst, i, np.flatnonzero(mask), mode, rng)
        val = objective(inst, i, cur, Lo, price, kind)
        for _ in range(2 * n + 2):
            est = _estimates(inst, i, cur, Lo, price, kind, mode)
            singles = [cur.diverted ^ {j} for _, j in est[:k]]
            blocks = [cur.diverted | frozenset(r) for r in cur.routes if not set(r) <= cur.diverted]
            routed = [j for j in range(n) if j not in cur.diverted]
            swaps = [(cur.diverted - {d}) | {r} for d in cur.diverted for r in routed]
            nxt = None
            for group in (singles, blocks, swaps):
                nxt = _try_sets(inst, i, group, Lo, price, kind, mode, rng, val, cur.routes)
                if nxt is not None:
                    break
            if nxt is None:
                break
            val, cur = nxt
        if val < best_val:
            best, best_val = cur, val
    assert best is not None
    return best
