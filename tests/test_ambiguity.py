"""Tests of the ambiguity-criteria study (src/ccu/ambiguity.py, src/ccu/ambiguity_game.py)."""
import itertools

import numpy as np
import pytest

from ccu import ambiguity as A
from ccu import brl, robust
from ccu import zmc_brl as zb
from ccu.ambiguity_game import HeurPool


def tiny_metro(n=6, K=3, seed=0, cap=3.0):
    rng = np.random.default_rng(seed)
    xy = rng.uniform(0, 1, (n + 1, 2))
    TT = np.linalg.norm(xy[:, None] - xy[None], axis=-1) * 5000.0 + 300.0
    tau = np.zeros((n + 1, n + 1, K))
    sec = rng.integers(0, K, n + 1)
    for a in range(n + 1):
        for b in range(n + 1):
            if a != b:
                tau[a, b, sec[a]] += TT[a, b] / 2
                tau[a, b, sec[b]] += TT[a, b] / 2
    dem = np.concatenate([[0.0], np.ones(n)])
    svc = dem * 1500.0
    loss = brl.Loss(1 / 3600, 3 / 3600, 4.0 * 3600, 2.0)
    m = np.array([1.5, 1.3, 1.7])[:K]
    true = m[None] * np.exp(0.2 * rng.standard_normal((400, 1)) + 0.15 * rng.standard_normal((400, K)))
    return A.Metro("tiny", n, tau, svc, dem, cap, loss, m, 0.2, 0.15, 1.0, 3.0, true, true[:60], {})


def all_routes(M):
    n = M.n
    out = []
    for k in range(1, int(M.cap) + 1):
        for sub in itertools.combinations(range(1, n + 1), k):
            for perm in itertools.permutations(sub):
                out.append(perm)
    return out


def brute_partition(M, pl, crit):
    """Exact minimum over set partitions into capacity-feasible routes (best order per subset)."""
    best = {}
    for r in all_routes(M):
        key = frozenset(r)
        c = pl.cost(crit, r)
        if key not in best or c < best[key]:
            best[key] = c
    full = (1 << M.n) - 1
    mask = {sum(1 << (j - 1) for j in k): c for k, c in best.items()}
    f = {0: 0.0}
    for S in range(1, full + 1):
        low = S & -S
        T = S
        v = np.inf
        while T:
            if T & low and T in mask and (S ^ T) in f:
                v = min(v, mask[T] + f[S ^ T])
            T = (T - 1) & S
        f[S] = v
    return f[full]


def test_cvar_of_matches_rockafellar_uryasev():
    rng = np.random.default_rng(1)
    for n, a in [(10, 0.9), (10, 0.8), (7, 0.75), (60, 0.95), (13, 0.9)]:
        x = rng.normal(size=n)
        eta = np.sort(x)
        ru = min(e + np.mean(np.maximum(x - e, 0.0)) / (1 - a) for e in eta)
        assert A.cvar_of(x, a) == pytest.approx(ru, rel=1e-9)


def test_wasserstein_closed_form_matches_robust_module():
    M = tiny_metro()
    days = M.true[:20]
    pl = A.Planner(M)
    crit = A.make_wass(M.loss, days, 0.1)
    lp = robust.LossParams(M.loss.fixed, M.loss.gamma, M.loss.rho, M.loss.Tmax)
    for r in [(1,), (2, 5), (3, 1, 4)]:
        tau, svc = pl.tau_of(r)
        T = days @ tau + svc
        emp = lp.f + lp.gamma * T + lp.rho * np.maximum(T - lp.T_max, 0)
        # robust.route_loss_stats has no service time: compare the penalty term only
        base = robust.route_loss_stats(tau, lp, days, 0.0)[0]
        pen = robust.route_loss_stats(tau, lp, days, 0.1)[1] - base
        assert pl.cost(crit, r) == pytest.approx(emp.mean() + pen, rel=1e-12)


def test_pbox_ud_is_upper_bound_of_saa_and_matches_brl_profile():
    M = tiny_metro()
    days = M.true[:25]
    pl = A.Planner(M)
    w, Q = A.pbox_levels(days, 2.0, M.xmax)
    ud = A.make_pbox_ud(M.loss, w, Q, "ud")
    saa = A.make_saa(M.loss, days)
    ind = A.make_pbox_ind(M.loss, w, Q, "ind", np.random.default_rng(0), M=4000)
    for r in [(1,), (2, 5), (3, 1, 4)]:
        assert pl.cost(ud, r) >= pl.cost(saa, r) - 1e-9  # comonotone coupling maximises a convex loss
        assert pl.cost(ud, r) >= pl.cost(ind, r) - 0.05  # and the independent coupling (Monte Carlo)
    # profile = BRL route profile
    qfs = [brl.dkw_upper_quantile(days[:, k], 0.05, M.xmax) for k in range(3)]
    _, w2, Q2 = brl.common_grid(qfs)
    inst = brl.RoutingInstance(M.n, M.tau, M.svc, M.dem, M.cap, Q2, w2, M.loss)
    ud95 = A.make_pbox_ud(M.loss, w2, Q2, "ud95")
    for r in [(1,), (2, 5), (3, 1, 4)]:
        assert pl.cost(ud95, r) == pytest.approx(inst.route_cost(r), rel=1e-12)


@pytest.mark.parametrize("kind", ["saa", "pbox", "cvar"])
def test_planner_reaches_enumerated_optimum_on_tiny_instance(kind):
    M = tiny_metro()
    days = M.true[:15]
    if kind == "saa":
        crit = A.make_saa(M.loss, days)
    elif kind == "cvar":
        crit = A.make_cvar(M.loss, days, 0.8)
    else:
        w, Q = A.pbox_levels(days, 0.1, M.xmax)
        crit = A.make_pbox_ud(M.loss, w, Q, "pb")
    pl = A.Planner(M)
    sol, v = pl.plan(crit, np.random.default_rng(0))
    assert sorted(j for r in sol for j in r) == list(range(1, M.n + 1))
    assert v == pytest.approx(brute_partition(M, pl, crit), rel=1e-9, abs=1e-9)


def test_plan_metrics_are_consistent():
    M = tiny_metro()
    pl = A.Planner(M)
    sol = [[1, 2, 3], [4, 5, 6]]
    law = A.TestLaw("t", M.true)
    mt = A.plan_metrics(M, pl, sol, law)
    # expected cost = sum of the SAA cost of the routes on the same days
    saa = A.make_saa(M.loss, M.true)
    assert mt["exp"] == pytest.approx(sum(pl.cost(saa, tuple(r)) for r in sol), rel=1e-10)
    assert mt["cvar95"] >= mt["exp"]
    assert 0.0 <= mt["p_ot_day"] <= 1.0
    sh = A.plan_metrics(M, pl, sol, A.TestLaw("s", M.true, 0.3))
    assert sh["exp"] >= mt["exp"]  # a congestion shock never lowers the cost


def test_wass_radius_decreases_with_n():
    rng = np.random.default_rng(0)
    d = 1.5 * np.exp(0.3 * rng.standard_normal((60, 9)))
    assert A.wass_radius(d[:10], "sqrt") > A.wass_radius(d[:60], "sqrt")
    assert A.wass_radius(d[:60], "fg") > A.wass_radius(d[:60], "sqrt")  # the K-dimensional rate is far larger


def _packing_by_enumeration(pool, kappa):
    inst = pool.inst
    best = {}
    for k in range(1, int(inst.cap // inst.dem[1:].min()) + 1):
        for sub in itertools.combinations(range(1, inst.n + 1), k):
            if inst.dem[list(sub)].sum() > inst.cap:
                continue
            for perm in itertools.permutations(sub):
                c = pool._cost(perm) + sum(kappa[j] for j in perm)
                key = frozenset(sub)
                if key not in best or c < best[key]:
                    best[key] = c
    keys = list(best)
    f = {0: 0.0}
    mask = {sum(1 << (j - 1) for j in k): best[k] for k in keys}
    full = (1 << inst.n) - 1
    for S in range(1, full + 1):
        v = np.inf
        T = S
        while T:
            if T in mask and (S ^ T) in f:
                v = min(v, mask[T] + f[S ^ T])
            T = (T - 1) & S
        f[S] = v
    # packing: customers optional -> minimum over all subsets S of f[S]
    return min(0.0, min(f.values()))


@pytest.mark.parametrize("kind,eps", [("saa", 0.0), ("wass", 0.3)])
def test_heuristic_oracle_matches_enumeration_on_tiny_game(kind, eps):
    g = zb.make_tiny_game(N=1, Z=6, n_cust=5, seed=3, K=2, ndays=20, cap=9.0)
    cr = g.carriers[0]
    days = 1.3 * np.exp(0.2 * np.random.default_rng(0).standard_normal((20, 2)))
    pool = HeurPool(cr.inst, days, kind, eps=eps, xmax=3.0, ng_size=cr.inst.n)
    rng = np.random.default_rng(5)
    hits = 0
    for t in range(6):
        kappa = np.concatenate([[0.0], rng.uniform(-80.0, 20.0, cr.inst.n)])
        res = pool.solve(kappa)
        assert res.bound_valid is False  # heuristic pricing never certifies a bound
        want = _packing_by_enumeration(pool, kappa)
        assert res.value >= want - 1e-7  # never better than the exact optimum
        hits += abs(res.value - want) < 1e-6 * max(1.0, abs(want))
    assert hits >= 5  # and almost always equal to it


def test_game_pool_fresh_is_backward_compatible():
    g = zb.make_tiny_game(N=2, Z=5, n_cust=3, seed=0)
    pool = g.carriers[0].pool
    assert isinstance(pool.fresh(), brl.RoutePool)
    p = g.oracle(0, np.zeros(g.d), rho=0.0, fresh=True)
    q = g.oracle(0, np.zeros(g.d), rho=0.0)
    assert abs(g.J(0, p, np.zeros(g.d)) - g.J(0, q, np.zeros(g.d))) < 1e-7
