"""Branch-and-price for BRL: exact against complete enumeration of all route sets; arc-restricted pricing."""
import importlib.util
import pathlib
import sys

import numpy as np
import pytest

from ccu import bp, brl

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _prototype():
    spec = importlib.util.spec_from_file_location("brl_prototype_bp", ROOT / "theory/new_algorithm_B/prototype.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _instance(seed):
    """Random Euclidean instance; the generator of experiments/run_bp.py --verify (same seeds)."""
    pr = _prototype()
    rng = np.random.default_rng(1000 + seed)
    n = int(rng.integers(7, 11))
    cap = int(rng.integers(2, 6))
    Tfrac = float(rng.uniform(0.3, 1.2))
    P = pr.random_pricing(np.random.default_rng(seed), n, K=4, cap=cap, Tfrac=Tfrac)
    loss = brl.Loss(P.loss.gamma, P.loss.rho, P.loss.Tmax, P.loss.fixed)
    return brl.RoutingInstance(n, P.tau, P.svc, P.dem, P.cap, P.Qk, P.w, loss), rng


# seeds 1, 8, 12 are instances where price-and-branch (MILP over the root columns) is suboptimal
@pytest.mark.parametrize("seed", [1, 8, 12, 15, 16, 20, 3, 5])
@pytest.mark.parametrize("partition", [True, False])
def test_bp_equals_enumeration(seed, partition):
    inst, rng = _instance(seed)
    n = inst.n
    if partition:
        kap = None if seed % 2 == 0 else np.concatenate([[0.0], rng.uniform(-50, 50, n)])
    else:
        kap = np.concatenate([[0.0], -rng.uniform(0.6, 2.2, n) * np.array([inst.route_cost((j,)) for j in range(1, n + 1)])])
    exact, _ = bp.exact_by_enumeration(inst, kap, partition)
    if not partition:
        exact = min(exact, 0.0)
    r = bp.solve_bp(inst, kap, partition=partition, ng_size=4, time_limit=120)
    assert r.status == "optimal" and r.bound_valid
    assert abs(r.value - exact) < 1e-6 * max(1.0, abs(exact))
    assert r.lb <= exact + 1e-6
    assert r.root_lp <= exact + 1e-6 and r.pb_value >= exact - 1e-6
    # the returned plan is feasible and has the stated value
    seen = [j for rt in r.routes for j in rt]
    assert len(seen) == len(set(seen))
    if partition:
        assert sorted(seen) == list(range(1, n + 1))
    kk = np.zeros(n + 1) if kap is None else kap
    val = sum(inst.route_cost(rt) + sum(kk[j] for j in rt) for rt in r.routes)
    assert abs(val - r.value) < 1e-6 * max(1.0, abs(val))
    assert all(sum(inst.dem[j] for j in rt) <= inst.cap + 1e-9 for rt in r.routes)


def test_price_and_branch_suboptimal_cases_exist():
    """On seed 12 the MILP over the root columns is strictly worse than the optimum, branch-and-price is not."""
    inst, rng = _instance(12)
    exact, _ = bp.exact_by_enumeration(inst, None, True)
    r = bp.solve_bp(inst, None, partition=True, ng_size=4, time_limit=120)
    assert r.pb_value > exact + 1.0
    assert abs(r.value - exact) < 1e-6 * abs(exact)
    assert r.nodes > 1


@pytest.mark.parametrize("seed", range(4))
def test_pricing_with_forbidden_arcs(seed):
    """espprc with an arc mask equals the brute-force minimum over all allowed routes."""
    inst, rng = _instance(seed)
    n = inst.n
    allow = rng.uniform(size=(n + 1, n + 1)) > 0.25
    np.fill_diagonal(allow, False)
    allow2, Cmin = bp._cmin_allowed(inst, allow)
    duals = np.concatenate([[0.0], rng.uniform(20, 80, n)])
    best, routes, st = brl.espprc(inst, duals, allow=allow2, Cmin=Cmin, max_cols=3)
    assert not st["overflow"]
    ref = np.inf
    stack = [((), 0.0)]
    while stack:
        r, load = stack.pop()
        if r:
            p = (0, *r, 0)
            if all(allow2[p[t], p[t + 1]] for t in range(len(p) - 1)):
                ref = min(ref, inst.route_cost(r) - float(duals[list(r)].sum()))
        for j in range(1, n + 1):
            if j not in r and load + inst.dem[j] <= inst.cap + 1e-12:
                stack.append((r + (j,), load + inst.dem[j]))
    assert abs(best - ref) < 1e-7 * max(1.0, abs(ref))


def test_pool_oracle_matches_enumeration():
    inst, rng = _instance(4)
    n = inst.n
    kap = np.concatenate([[0.0], -rng.uniform(0.6, 2.2, n) * np.array([inst.route_cost((j,)) for j in range(1, n + 1)])])
    pool = brl.RoutePool(inst, ng_size=n)
    res = bp.solve_pool_bp(pool, kap, time_limit=60)
    exact, _ = brl.exact_pack_by_enumeration(inst, kap)
    assert res.bound_valid and res.status == "optimal"
    assert abs(res.value - exact) < 1e-6 * max(1.0, abs(exact))
