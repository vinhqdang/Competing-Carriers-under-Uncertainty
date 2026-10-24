"""Credal thresholds, anchored bounds, Gamma surcharge lemma, D2 variant, gadgets (theory/main.tex Sections 3, 6, 7)."""
import itertools
import math

import numpy as np
import pytest

from ccu import credal as cr, d2game as d2, zmc, zmc_brl as zb


def prop71(w=1.0):
    g = cr.ExplicitGame.from_profits([1.0], [[[1], [3]], [[1], [3]]], [[[4], [1]], [[1], [4]]], [[6, 0], [0, 6]],
                                     names=[["A1", "B1"], ["X", "Y"]])
    return g, np.array([float(w)])


def table(g, w, kinds=("E",)):
    return {idx: cr.profile_thresholds(g, g.profile(idx), w, kinds=kinds, cuts=g.plans, iters=60) for idx in g.profiles()}


@pytest.mark.parametrize("w", [0.5, 1.0, 2.0])
def test_prop71_threshold_is_one_over_w(w):
    g, wv = prop71(w)
    tab = table(g, wv, kinds=("E", "M", "ID"))
    assert all(t["E_max"] > 1e-9 for t in tab.values()), "no pure Nash equilibrium"
    assert min(t["E_max"] for t in tab.values()) == pytest.approx(1.0 / w, abs=1e-5)
    assert min(t["M_max"] for t in tab.values()) == pytest.approx(1.0 / w, abs=1e-5)
    assert min(t["ID_max"] for t in tab.values()) <= min(t["M_max"] for t in tab.values()) + 1e-9  # ID <= M <= E


def test_prop71_mixed_equilibrium_and_bound():
    g, wv = prop71(1.0)
    support = [list(g.plans[0]), list(g.plans[1])]
    weights = [[0.5, 0.5], [0.5, 0.5]]
    assert cr.check_relaxed(g, support, weights) < 1e-12
    st = cr.anchored_stats(g, support, weights, wv, d=1)
    assert st["rho_bar"] == pytest.approx(1.0) and st["T1"] == pytest.approx(1.0)  # (N-1) rho_bar = 1/w
    # mixing system recovers (1/2, 1/2)
    p0 = [g.plans[0][0], g.plans[1][0]]
    p1 = [g.plans[0][1], g.plans[1][1]]
    t = cr.mix_pair(g, p0, p1, [0, 1], p0)
    assert np.allclose(t, [0.5, 0.5])
    # every profile of the support product: E-threshold <= anchored radius (Thm 6.1(a))
    tab = table(g, wv)
    for idx in g.profiles():
        pf = g.profile(idx)
        assert tab[idx]["E_max"] <= cr.delta_hat(pf, st["abar"], wv) + 1e-9


def test_br_dynamics_cycles_on_prop71():
    g, _ = prop71(1.0)
    res = cr.br_run(g, g.profile((0, 0)), order=[0, 1], max_rounds=20)
    assert res["status"] == "cycle"


def test_n_uniform_bound_formula():
    assert cr.n_uniform_bound(5, 10, 2.0) == pytest.approx(2.0 * min(4, 11, 1 + math.sqrt(10 * math.log(20) / 2)))
    assert cr.n_uniform_bound(2, 1000, 1.0) == pytest.approx(1.0)


def _tiny_with_wrap(seed):
    g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=seed)
    return g, d2.explicit_from_game(g)


@pytest.mark.parametrize("seed", [2, 5])
def test_oracle_thresholds_equal_enumeration(seed):
    """E, M, ID thresholds computed with the BRL oracle (cuts + shifted prices) equal the enumerated ones."""
    g, eg = _tiny_with_wrap(seed)
    prof0 = zmc.run_zmc(g, rounds=6)["profile"]
    w = cr.make_weights(g, prof0, "agg")
    rng = np.random.default_rng(seed)
    plans = [[p for _, p in pl] for pl in zb.enumerate_game(g)[2]]
    for _ in range(3):
        prof = [pl[rng.integers(len(pl))] for pl in plans]
        for i in range(g.N):
            e1, _ = cr.e_threshold(g, i, prof, w)
            e2, _ = cr.e_threshold(g, i, prof, w, cuts=plans[i])
            assert e1 == pytest.approx(e2, abs=1e-6) or (math.isinf(e1) and math.isinf(e2))
            m1 = cr.m_threshold(g, i, prof, w, hi=e1)
            m2 = cr.m_threshold(eg, i, prof, w, hi=e1)
            assert m1 == pytest.approx(m2, abs=1e-4) or (math.isinf(m1) and math.isinf(m2))
            d1 = cr.id_threshold(g, i, prof, w, hi=m1)
            d2_ = cr.id_threshold(eg, i, prof, w, hi=m1)
            assert d1 == pytest.approx(d2_, abs=1e-4) or (math.isinf(d1) and math.isinf(d2_))
            if np.isfinite(e1):
                assert d1 <= m1 + 1e-5 and m1 <= e1 + 1e-5  # Lemma 3.4 ordering (bisection tolerance)


def test_equilibrium_has_zero_thresholds():
    g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=4)
    prof = zmc.run_zmc(g, rounds=6)["profile"]
    w = cr.make_weights(g, prof, "agg")
    th = cr.profile_thresholds(g, prof, w, kinds=("E", "M", "ID"))
    assert th["E_max"] == 0.0 and th["M_max"] == 0.0 and th["ID_max"] == 0.0


def test_gamma_surcharge_lemma():
    """Lemma 3.6: worst case of J over the box is attained at the upper corner and equals the cost in the surcharge game."""
    g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=1)
    prof = zmc.run_zmc(g, rounds=6)["profile"]
    w = cr.make_weights(g, prof, "agg")
    delta = 0.4
    i = 0
    A = cr.rival_aggregate(prof, i)
    hi = A + delta * w
    lo = np.maximum(A - delta * w, 0.0)
    rng = np.random.default_rng(0)
    plan = prof[i]
    worst = max(cr.cost_at(g, plan, np.where(rng.random(g.d) < 0.5, lo, hi)) for _ in range(300))
    assert worst <= cr.cost_at(g, plan, hi) + 1e-9
    g.set_charges(sur=delta * g.M * w)
    ps = g.plan_from_routes(i, plan.routes)
    assert g.J(i, ps, A) == pytest.approx(cr.cost_at(g, plan, hi), rel=1e-9, abs=1e-9)
    g.set_charges()
    # Gamma-admissibility = best response in the surcharge game
    g.set_charges(sur=delta * g.M * w)
    br = g.br(i, A, count=False)
    best_sur = g.J(i, br, A)
    g.set_charges()
    q = g.plan_from_routes(i, br.routes)
    assert cr.cost_at(g, q, hi) == pytest.approx(best_sur, rel=1e-9, abs=1e-9)
    assert cr.gamma_regret(g, i, prof, w, delta) >= -1e-12


def test_anchored_bound_and_absorption_random_games():
    """Theorem 6.1 on random D2 bilinear games: for verified relaxed equilibria, E-threshold <= delta_hat, min delta_hat <= bound."""
    rng = np.random.default_rng(3)
    checked = 0
    for _ in range(60):
        N, d, P = 3, int(rng.integers(1, 3)), int(rng.integers(2, 4))
        M = rng.uniform(0.5, 1.5, d)
        w = rng.uniform(0.5, 2.0, d)
        a = [rng.integers(0, 4, (P, d)).astype(float) for _ in range(N)]
        phi = [rng.integers(0, 4, (P, d)).astype(float) for _ in range(N)]
        pi = [rng.uniform(0, 10, P) for _ in range(N)]
        g = cr.ExplicitGame.from_profits(M, a, phi, pi)
        tab = table(g, w)
        d0 = min(t["E_max"] for t in tab.values())
        assert d0 <= cr.n_uniform_bound(N, d, cr.sigma_max(g, w)) + 1e-7
        pures = [g.profile(idx) for idx in sorted(tab, key=lambda k: tab[k]["E_max"])[:10]]
        for support, weights, S in cr.mixed_candidates(g, pures)[:20]:
            if cr.check_relaxed(g, support, weights) > 1e-7:
                continue
            checked += 1
            st = cr.anchored_stats(g, support, weights, w, d=d)
            allp = cr.profiles_in_support(support, cap=4096)
            dh = []
            for pf in allp:
                h = cr.delta_hat(pf, st["abar"], w)
                dh.append(h)
                idx = tuple(next(k for k, q in enumerate(g.plans[i]) if q.name == pf[i].name) for i in range(N))
                assert tab[idx]["E_max"] <= h + 1e-7
            assert min(dh) <= st["bound"] + 1e-7
            assert d0 <= min(dh) + 1e-7
    assert checked > 0


def _kernel_game(n, arcs):
    indeg = np.zeros(n, int)
    for (_, v) in arcs:
        indeg[v] += 1
    eta = 1.0 / (2 * max(1, indeg.max()) + 2)
    ne = len(arcs)
    a_in = [np.zeros(ne) for _ in range(n)]
    f_in = [np.zeros(ne) for _ in range(n)]
    for e, (u, v) in enumerate(arcs):
        a_in[u][e], f_in[u][e] = 1.0, 1.0
        a_in[v][e], f_in[v][e] = 2.0, eta
    return cr.ExplicitGame.from_profits(np.ones(ne), [[np.zeros(ne), a_in[i]] for i in range(n)],
                                        [[np.zeros(ne), f_in[i]] for i in range(n)], [[0.0, 1.0]] * n)


@pytest.mark.parametrize("arcs,has_kernel", [([(0, 1), (1, 2), (2, 0)], False), ([(0, 1), (1, 0), (1, 2)], True)])
def test_kernel_gadget_thm73(arcs, has_kernel):
    n = 3
    g = _kernel_game(n, arcs)
    w = np.ones(len(arcs))
    dplus = max(sum(1 for (u, _) in arcs if u == i) for i in range(n))
    pred = 1.0 / (2 * dplus + 1)
    tab = table(g, w)
    ker = set()
    for mask in range(1 << n):
        S = {i for i in range(n) if mask >> i & 1}
        if any(u in S and v in S for (u, v) in arcs):
            continue
        if all(any(u == i and v in S for (u, v) in arcs) for i in range(n) if i not in S):
            ker.add(tuple(int(i in S) for i in range(n)))
    assert bool(ker) == has_kernel
    for dl in (0.0, 0.999 * pred):
        assert {idx for idx, t in tab.items() if t["E_max"] <= dl + 1e-9} == ker
    d0 = min(t["E_max"] for t in tab.values())
    assert d0 <= 1e-9 if has_kernel else d0 >= pred - 1e-9


def test_d2_game_matches_enumeration_and_d1_when_vehicle_hours_equal():
    g1 = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=7)
    G = d2.to_d2(g1, 5.0)
    eg = d2.explicit_from_game(G)
    rng = np.random.default_rng(0)
    for _ in range(10):
        idx = tuple(int(rng.integers(len(p))) for p in eg.plans)
        prof = eg.profile(idx)
        A = sum(p.a for p in prof)
        for i in range(G.N):
            Am = A - prof[i].a
            br = G.br(i, Am, count=False)
            brv = G.J(i, br, Am)
            ev = min(cr.cost_at(eg, q, Am) for q in eg.plans[i])
            assert brv == pytest.approx(ev, abs=1e-6)
    # vehicle count = served indicator, exposure = hours
    p = G.oracle(0, G.M * np.zeros(G.d), rho=0.0, count=False)
    assert set(np.unique(p.a[G.Z:])) <= {0.0, 1.0}
    # D2 differs from D1 (phi != a) while the delivery coordinates coincide
    assert not np.allclose(p.phi, p.a) or p.q.sum() == 0
    with pytest.raises(NotImplementedError):
        G.oracle(0, np.zeros(G.d), rho=1.0, count=False)


def test_d1_has_pne_and_zero_threshold_on_tiny_games():
    """Prop 7.1 / H4 control: D1 games always have a pure equilibrium, so delta_0 = 0."""
    for seed in range(4):
        g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=seed)
        eg = d2.explicit_from_game(g)
        assert len(d2.pure_nash(eg)) > 0


def test_profiles_in_support_and_weights():
    g, _ = prop71(1.0)
    support = [list(g.plans[0]), list(g.plans[1])]
    assert len(cr.profiles_in_support(support, cap=64)) == 4
    assert len(cr.profiles_in_support(support, cap=2, rng=np.random.default_rng(0))) == 2
