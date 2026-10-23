"""Brute-force validation of the best response, and the exact-potential identity."""
from functools import lru_cache
from itertools import combinations, permutations

import numpy as np

from ccu import make_instance
from ccu.carrier import best_response, make_plan, plan_cost_J, diversion_total
from ccu.game import potential
from ccu.routing import route_model


def _exact_routing(m, items, Q):
    """Optimal CVRP cost of the item set by subset recursion over all route orders."""
    rc = {}

    def route_cost(sub):
        if sub not in rc:
            rc[sub] = min(m.cost(p) for p in permutations(sub))
        return rc[sub]

    @lru_cache(maxsize=None)
    def best(rest):
        if not rest:
            return 0.0
        first, others = rest[0], rest[1:]
        out = np.inf
        for k in range(min(Q - 1, len(others)) + 1):
            for comb in combinations(others, k):
                rem = tuple(x for x in others if x not in comb)
                out = min(out, route_cost((first,) + comb) + best(rem))
        return out

    return best(tuple(sorted(items)))


def test_best_response_matches_brute_force_tiny():
    worst = 0.0
    for seed in range(3):
        inst = make_instance(N=2, n_per_carrier=5, Z=1, seed=seed, Q=3)
        i, Lo, p = 0, np.array([3.0]), np.array([0.1])
        m = route_model(inst, i)
        n = 5
        best_exact = np.inf
        for k in range(n + 1):
            for D in combinations(range(n), k):
                served = [j for j in range(n) if j not in D]
                routing = _exact_routing(m, served, inst.Q)
                u = np.array([float(len(D))])
                cong = np.sum(p * u + inst.beta / inst.C * u * (Lo + u))
                val = routing + diversion_total(inst, i, frozenset(D)) + cong
                best_exact = min(best_exact, val)
        plan = best_response(inst, i, Lo, p, np.random.default_rng(seed), starts=5)
        got = plan_cost_J(inst, i, plan, Lo, p)
        assert got >= best_exact - 1e-9
        worst = max(worst, (got - best_exact) / best_exact)
    print(f"max relative gap of best response to brute force: {worst:.2e}")
    assert worst < 1e-2


def test_potential_identity_unilateral_deviation():
    rng = np.random.default_rng(7)
    inst = make_instance(N=3, n_per_carrier=8, Z=2, seed=4)
    profile = [make_plan(inst, i, np.flatnonzero(rng.random(8) < 0.3), "robust", rng) for i in range(3)]
    p = np.array([0.4, 0.15])
    for i in range(3):
        others = [profile[k] for k in range(3) if k != i]
        Lo = sum(pl.usage for pl in others)
        for _ in range(3):
            D1 = np.flatnonzero(rng.random(8) < 0.5)
            D2 = np.flatnonzero(rng.random(8) < 0.5)
            pa = make_plan(inst, i, D1, "robust", rng)
            pb = make_plan(inst, i, D2, "robust", rng)
            prof_a = list(profile)
            prof_b = list(profile)
            prof_a[i], prof_b[i] = pa, pb
            dJ = plan_cost_J(inst, i, pb, Lo, p) - plan_cost_J(inst, i, pa, Lo, p)
            dPhi = potential(inst, prof_b, p) - potential(inst, prof_a, p)
            assert abs(dJ - dPhi) < 1e-9 * (1 + abs(dPhi))
