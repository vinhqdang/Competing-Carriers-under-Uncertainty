"""Variant kernel: dominance rules, SAA / Wasserstein / CVaR route costs, completion bound, heuristic cap."""
import importlib.util
import itertools
import pathlib
import sys

import numpy as np
import pytest

from ccu import brl, brl_variants as bv

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _prototype():
    spec = importlib.util.spec_from_file_location("brl_prototype_bv", ROOT / "theory/new_algorithm_B/prototype.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _inst(n, seed, cap=4, Tfrac=0.9):
    pr = _prototype()
    rng = np.random.default_rng(seed)
    P = pr.random_pricing(rng, n, K=4, cap=cap, Tfrac=Tfrac)
    loss = brl.Loss(P.loss.gamma, P.loss.rho, P.loss.Tmax, P.loss.fixed)
    return brl.RoutingInstance(n, P.tau, P.svc, P.dem, P.cap, P.Qk, P.w, loss), P


def _brute(inst, duals):
    """Minimum reduced cost over all elementary routes (any order)."""
    best = 0.0
    n = inst.n
    for k in range(1, n + 1):
        for sub in itertools.combinations(range(1, n + 1), k):
            if inst.dem[list(sub)].sum() > inst.cap:
                continue
            for perm in itertools.permutations(sub):
                best = min(best, inst.route_cost(perm) - duals[list(perm)].sum())
    return best


@pytest.mark.parametrize("seed", range(3))
@pytest.mark.parametrize("mode", ["window", "nowin", "qv"])
def test_modes_equal_reference(seed, mode):
    inst, P = _inst(7, seed)
    ref, _, _ = brl.espprc(inst, P.duals, max_cols=5)
    b, routes, st = bv.price(inst, P.duals, mode=mode, max_cols=5)
    assert not st["overflow"] and abs(b - ref) < 1e-8 * max(1, abs(ref))
    for rc, r in routes:
        assert abs(inst.route_cost(r) - P.duals[list(r)].sum() - rc) < 1e-7


@pytest.mark.parametrize("seed", range(3))
def test_completion_bound_keeps_negative_columns(seed):
    inst, P = _inst(8, 10 + seed)
    duals = P.duals * 1.5
    ref, _, st0 = bv.price(inst, duals, mode="window")
    b, _, st1 = bv.price(inst, duals, mode="window", lbprune=True)
    assert abs(min(b, 0) - min(ref, 0)) < 1e-8 * max(1, abs(ref))
    assert st1["kept"] <= st0["kept"] + 1 or st1["created"] <= st0["created"]


@pytest.mark.parametrize("variant", ["saa", "wass", "cvar"])
def test_vec_variants_exact(variant):
    inst, P = _inst(6, 21, cap=3)
    rng = np.random.default_rng(5)
    scen = rng.lognormal(0.2, 0.25, size=(12, inst.tau.shape[2]))
    kw = dict(saa={}, wass=dict(wass_eps=0.05), cvar=dict(risk=1, alpha=0.75, lam=0.5))[variant]
    vi = bv.vec_instance_saa(inst, scen, **kw)
    duals = P.duals * 3.0
    b, routes, st = bv.price(vi, duals, mode="qv")
    assert not st["overflow"]
    assert abs(min(b, 0) - _brute(vi, duals)) < 1e-8 * max(1, abs(b))
    # lower bound variant too
    b2, _, _ = bv.price(vi, duals, mode="qv", lbprune=True)
    assert abs(min(b2, 0) - min(b, 0)) < 1e-8 * max(1, abs(b))


def test_heuristic_cap_returns_feasible_columns():
    inst, P = _inst(9, 33)
    duals = P.duals * 2.0
    b, routes, st = bv.price(inst, duals, mode="window", bcap_h=3)
    ref, _, _ = bv.price(inst, duals, mode="window")
    assert b >= ref - 1e-9
    for rc, r in routes:
        assert abs(inst.route_cost(r) - duals[list(r)].sum() - rc) < 1e-7


def test_more_than_64_customers():
    """Two-word ng masks: n = 70, capacity of two customers, all rules against complete enumeration of 1- and 2-routes."""
    pr = _prototype()
    rng = np.random.default_rng(7)
    P = pr.random_pricing(rng, 70, K=4, cap=2, Tfrac=0.9)
    loss = brl.Loss(P.loss.gamma, P.loss.rho, P.loss.Tmax, P.loss.fixed)
    inst = brl.RoutingInstance(70, P.tau, P.svc, np.ones(71) * np.r_[0, np.ones(70)], 2.0, P.Qk, P.w, loss)
    duals = P.duals * 3.0
    best = min(min(inst.route_cost((a,)) - duals[a] for a in range(1, 71)),
               min(inst.route_cost((a, b)) - duals[a] - duals[b] for a in range(1, 71) for b in range(1, 71) if a != b))
    for mode in ("window", "nowin", "qv"):
        b, routes, st = bv.price(inst, duals, mode=mode, ng=bv.ng_masks_py(inst, 6))
        assert not st["overflow"]
        assert abs(b - min(best, b)) < 1e-9 and abs(min(b, 0) - min(best, 0)) < 1e-8 * max(1, abs(best))


@pytest.mark.parametrize("seed", [1, 12])
@pytest.mark.parametrize("variant", ["brl", "heur+lb+ng3", "saa", "wass", "cvar"])
def test_vbp_equals_enumeration(seed, variant):
    from ccu import bp
    inst, _ = _inst(8, seed, cap=3)
    rs = np.random.default_rng(3).lognormal(0.2, 0.25, size=(10, 4))
    if variant == "brl":
        vi, kw = inst, dict()
    elif variant == "heur+lb+ng3":
        vi, kw = inst, dict(heur_first=2, lbprune=True, ng_size=3)
    else:
        vi = bv.vec_instance_saa(inst, rs, **dict(saa={}, wass=dict(wass_eps=0.05), cvar=dict(risk=1))[variant])
        kw = dict(mode="qv", ng_size=4)
    ex, _ = bp.exact_by_enumeration(vi, None, True)
    r = bv.VBP(vi, None, partition=True, **kw).run(time_limit=60)
    assert r.status == "optimal" and r.bound_valid
    assert abs(r.value - ex) < 1e-6 * max(1, abs(ex)) and r.lb <= ex + 1e-6


def test_root_cg_devices_agree():
    inst, _ = _inst(9, 4, cap=3)
    base = bv.root_cg(inst, ng_size=9)
    for kw in (dict(lbprune=True), dict(heur_first=3), dict(dssr=True, ng_size=2), dict(dssr=True, ng_size=2, heur_first=3, lbprune=True)):
        r = bv.root_cg(inst, **kw)
        assert r["status"] == "converged"
        assert abs(r["lp"] - base["lp"]) < 1e-6 * abs(base["lp"])
