"""BRL pricing (compiled port) against the prototype and against complete enumeration."""
import importlib.util
import pathlib
import sys

import numpy as np
import pytest

from ccu import brl

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _prototype():
    spec = importlib.util.spec_from_file_location("brl_prototype", ROOT / "theory/new_algorithm_B/prototype.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("n,seed", [(6, 0), (8, 1), (10, 2)])
def test_pricing_matches_prototype(n, seed):
    pr = _prototype()
    rng = np.random.default_rng(seed)
    P = pr.random_pricing(rng, n, K=4, cap=4, Tfrac=0.9)
    loss = brl.Loss(P.loss.gamma, P.loss.rho, P.loss.Tmax, P.loss.fixed)
    inst = brl.RoutingInstance(n, P.tau, P.svc, P.dem, P.cap, P.Qk, P.w, loss)
    ref, _, _ = pr.espprc(P, "functional", max_cols=5)
    best, routes, st = brl.espprc(inst, P.duals, max_cols=5)
    assert not st["overflow"]
    assert abs(best - ref) < 1e-8 * max(1.0, abs(ref))
    # every returned route has the stated reduced cost
    for rc, r in routes:
        assert abs(inst.route_cost(r) - float(P.duals[list(r)].sum()) - rc) < 1e-7


@pytest.mark.parametrize("seed", range(4))
def test_column_generation_vs_enumeration(seed):
    pr = _prototype()
    rng = np.random.default_rng(100 + seed)
    P = pr.random_pricing(rng, 7, K=4, cap=4, Tfrac=0.9)
    loss = brl.Loss(P.loss.gamma, P.loss.rho, P.loss.Tmax, P.loss.fixed)
    inst = brl.RoutingInstance(7, P.tau, P.svc, P.dem, P.cap, P.Qk, P.w, loss)
    kappa = np.concatenate([[0.0], rng.uniform(-90, 10, 7)])  # prizes and costs
    pool = brl.RoutePool(inst, ng_size=7)
    res = pool.solve(kappa)
    exact, _ = brl.exact_pack_by_enumeration(inst, kappa)
    assert res.bound_valid
    assert res.lp <= exact + 1e-6          # LP bound is a lower bound of the integer optimum
    assert res.value >= exact - 1e-6       # price-and-branch value is feasible
    assert res.value - exact < 1e-6 or res.value - res.lp > 0  # equal, or the gap certificate is nonzero
