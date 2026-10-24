"""Integrated ZMC + BRL game: exhaustive enumeration on tiny games, exactness of the returned profiles, clearing identity."""
import numpy as np
import pytest

from ccu import zmc, zmc_brl as zb


def _index(plans_i, p):
    for k, (_, pl) in enumerate(plans_i):
        if np.allclose(pl.a, p.a):
            return k
    raise AssertionError("plan not in enumeration")


@pytest.mark.parametrize("seed", range(5))
def test_equilibrium_equals_exhaustive_ne(seed):
    g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=seed)
    Phi, ne, plans = zb.enumerate_game(g)
    r = zmc.run_zmc(g, rounds=6)
    prof = r["profile"]
    idx = tuple(_index(plans[i], p) for i, p in enumerate(prof))
    assert ne[idx], "returned profile is not a pure NE of the exhaustively enumerated game"
    assert abs(g.potential(prof) - Phi[idx]) < 1e-7
    # the potential lies inside the range of the enumerated equilibria (it need not be the best one; see verify_tiny)
    assert Phi[ne].min() - 1e-9 <= g.potential(prof) <= Phi[ne].max() + 1e-9


@pytest.mark.parametrize("seed", range(3))
def test_regrets_zero_with_independent_oracle(seed):
    g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=10 + seed)
    prof = zmc.run_zmc(g, rounds=6)["profile"]
    assert g.regrets(prof, fresh=True).max() < 1e-7
    assert g.regrets(prof, fresh=False).max() < 1e-7


def test_clearing_identity():
    """Phi(sigma) - G(lam) = 1/2 ||M^-1 lam - A||_M^2 for any plans (Theorem 2, algebraic part)."""
    g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=3)
    rng = np.random.default_rng(0)
    lam = rng.uniform(0, 3, g.d) * g.M
    plans = [g.oracle(i, lam, rho=1.0) for i in range(g.N)]
    A = sum(p.a for p in plans)
    e = lam / g.M - A
    lhs = g.potential(plans) - zmc.dual_value(g, lam, plans)
    assert abs(lhs - 0.5 * float(e @ (g.M * e))) < 1e-8


def test_city_game_smoke():
    g = zb.build_city_game("Cairo", n_cust=8, seed=1)
    assert g.N == 4 and g.Z == 42
    r = zmc.run_zmc(g, rounds=4)
    assert r["converged"]
    assert g.regrets(r["profile"], fresh=True).max() < 1e-6
    ev = g.evaluate(r["profile"])
    assert 0.0 <= ev["served_share"] <= 1.0


def test_exact_oracle_counters_and_retry():
    """bp_time switches the integer step to branch-and-price; counters are shared with the social-cost variant."""
    g = zb.make_tiny_game(N=2, Z=5, n_cust=3, seed=1)
    ref = [g.oracle(i, np.zeros(g.d), rho=0.0, count=False) for i in range(g.N)]
    g.bp_time, g.bp_retry = 10.0, 30.0
    g._cache.clear()
    ex = [g.oracle(i, np.zeros(g.d), rho=0.0, count=False) for i in range(g.N)]
    assert g.bp_calls == 2 and g.bp_optimal == 2 and g.bp_timeouts == 0
    assert all(abs(a.c - b.c) < 1e-6 for a, b in zip(ref, ex))  # tiny instances: price-and-branch is already exact
    so = g.so_variant(False)
    so.oracle(0, np.zeros(g.d), rho=1.0, count=False)
    assert g.bp_calls == 3  # shared counters
    assert g._st["br_calls"] == 2  # best responses (rho = 0) are counted separately
