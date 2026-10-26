"""Aggregate-response pricing (ccu.arp): the identities behind the method, checked on tiny games with exhaustive enumeration."""
import itertools

import numpy as np
import pytest

from ccu import arp, dip, zmc, zmc_brl as zb


def _plans(g):
    g.set_charges()
    _, _, plans = zb.enumerate_game(g)
    return [[p for _, p in pl] for pl in plans]


def _rebuild(g, i, p):
    return g._plan(i, (), p.q, p.a[g.Z:], p.cr)


def _game(seed, gcx=30.0):
    g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=seed)
    g.gc = g.gc * gcx
    return g


@pytest.mark.parametrize("seed", range(3))
def test_observed_tangent_matches_dip_with_known_lots(seed):
    """With the true mean lot the observed tangent is DIP's tangent charge at the observed aggregate."""
    g = _game(seed)
    plans = _plans(g)
    rng = np.random.default_rng(seed)
    prof = [_rebuild(g, i, plans[i][int(rng.integers(len(plans[i])))]) for i in range(g.N)]
    Q, n = arp.observe(g, prof)
    D = dip.lots(g)
    has = D > 0
    dbar = np.where(has.any(0), D.sum(0) / np.maximum(has.sum(0), 1), 0.0)
    assert np.allclose(arp.observed_tangent(g, Q, n, dbar=dbar), dip.tangent_charge(g, Q))


@pytest.mark.parametrize("seed", range(3))
def test_convexified_response_is_lipschitz_and_plain_map_contracts(seed):
    """||Q(u1) - Q(u2)||_m <= ||u1 - u2||_{m^-1} and ||T(u1) - T(u2)||_{k^-1} <= rho ||u1 - u2||_{k^-1} (Theorems 1-2)."""
    g = _game(seed, gcx=60.0)
    plans = _plans(g)
    kappa, m, _ = dip.curvatures(g)
    act = dip.active_zones(g)
    rho = arp.contraction_ratio(g)
    rng = np.random.default_rng(seed)
    for _ in range(3):
        u1 = np.where(act, rng.normal(0, 2, g.Z), 0.0)
        u2 = np.where(act, rng.normal(0, 2, g.Z), 0.0)
        Q1, _ = arp.convexified_response(g, plans, u1)
        Q2, _ = arp.convexified_response(g, plans, u2)
        lhs = np.sqrt(np.sum(m[act] * (Q1 - Q2)[act] ** 2))
        rhs = np.sqrt(np.sum((u1 - u2)[act] ** 2 / m[act]))
        assert lhs <= rhs * (1 + 1e-4) + 1e-6
        T1, T2 = kappa * Q1, kappa * Q2
        assert arp.knorm(g, T1 - T2) <= rho * arp.knorm(g, u1 - u2) * (1 + 1e-4) + 1e-6


@pytest.mark.parametrize("seed", range(3))
def test_fixed_point_is_unilateral_social_optimum_up_to_lot_asymmetry(seed):
    """At a fixed point (u = tangent at the observed aggregate, sigma a NE under u):
    SC(p, sigma_-i) >= SC(sigma) + L(sigma) - L(p, sigma_-i) + kappa/2 (dQ)^2 for every unilateral deviation (Theorem 3)."""
    g = _game(seed, gcx=20.0)
    plans = _plans(g)
    kappa, m, _ = dip.curvatures(g)
    base = zmc.run_zmc(g, rounds=6)
    out = arp.arp(g, base["profile"], theta="plain", max_rounds=12, dbar=None)
    if out["status"] != "fixed_point":
        pytest.skip("no fixed point reached on this instance")
    prof = out["profile"]
    u = out["u"]
    Q = sum(p.q for p in prof)
    # dbar implied by the posted charge (u = kappa Q - m/2 dbar)
    dbar = np.where(dip.active_zones(g), 2.0 * (kappa * Q - u) / np.where(dip.active_zones(g), m, 1.0), 0.0)
    D = dip.lots(g)

    def L(pr):
        return sum(float(((0.5 * m) * (D[i] - dbar) * p.q).sum()) for i, p in enumerate(pr))

    sc = dip.social_cost(g, prof)
    for i in range(g.N):
        for p in plans[i]:
            alt = list(prof)
            alt[i] = _rebuild(g, i, p)
            dQ = alt[i].q - prof[i].q
            assert dip.social_cost(g, alt) >= sc + L(prof) - L(alt) + 0.5 * float((kappa * dQ * dQ).sum()) - 1e-7


@pytest.mark.parametrize("seed", range(4))
def test_marginal_tariff_potential_is_social_cost(seed):
    """Under T_z(q, Q) = kappa q (Q - q) - b/2 q^2 a carrier's cost change equals the social-cost change (Theorem 7)."""
    g = _game(seed, gcx=30.0)
    plans = _plans(g)
    mg = arp.MarginalTariffGame(g)
    rng = np.random.default_rng(seed)
    prof = [_rebuild(g, i, plans[i][int(rng.integers(len(plans[i])))]) for i in range(g.N)]
    A = sum(p.a for p in prof)
    sc = dip.social_cost(g, prof)
    for i in range(g.N):
        Am = A - prof[i].a
        for p in plans[i]:
            q = _rebuild(g, i, p)
            alt = list(prof)
            alt[i] = q
            assert abs((mg.J(i, q, Am) - mg.J(i, prof[i], Am)) - (dip.social_cost(g, alt) - sc)) < 1e-8


@pytest.mark.parametrize("seed", range(4))
def test_marginal_tariff_dynamics_monotone_and_exact_equilibrium(seed):
    g = _game(seed, gcx=20.0)
    base = zmc.run_zmc(g, rounds=6)
    sc0 = dip.social_cost(g, base["profile"])
    out = arp.arp_marginal(g, base["profile"])
    assert out["monotone"] and out["sc"] <= sc0 + 1e-9
    assert arp.MarginalTariffGame(g).regrets(out["profile"]).max() < 1e-7
    # every social optimum is an equilibrium of the tariff game
    _, _, plans = zb.enumerate_game(g)
    best, bv = None, np.inf
    for idx in itertools.product(*[range(len(p)) for p in plans]):
        pr = [_rebuild(g, i, plans[i][k][1]) for i, k in enumerate(idx)]
        v = dip.social_cost(g, pr)
        if v < bv:
            best, bv = pr, v
    assert arp.MarginalTariffGame(g).regrets(best).max() < 1e-7


@pytest.mark.parametrize("seed", range(3))
def test_arp_returns_exact_equilibrium_under_posted_charge(seed):
    g = _game(seed, gcx=20.0)
    base = zmc.run_zmc(g, rounds=6)
    out = arp.arp(g, base["profile"], theta="plain", max_rounds=10)
    _, _, toll = dip.instruments(g, out["u"])
    g.set_charges(toll=toll)
    prof = [g.plan_from_routes(i, p.routes) for i, p in enumerate(out["profile"])]
    assert g.regrets(prof, fresh=True).max() < 1e-7
    assert out["status"] in ("fixed_point", "cycle", "rounds")


def test_lot_memory_learns_lots_from_jumps():
    mem = arp.LotMemory(3)
    mem.update(np.array([5.0, 0.0, 9.0]), np.array([1, 0, 2]))
    mem.update(np.array([5.0, 3.0, 4.0]), np.array([1, 1, 1]))
    assert mem.mean(0) == 5.0 and mem.mean(1) == 3.0
    assert set(mem.lots[2]) == {4.0, 5.0}


def test_credal_surcharge_does_not_enter_the_rule():
    """The rule depends on (Q, n) only; a Gamma-maximin surcharge changes the response, not the formula."""
    g = _game(0, gcx=10.0)
    base = zmc.run_zmc(g, rounds=6)
    Q, n = arp.observe(g, base["profile"])
    u0 = arp.observed_tangent(g, Q, n)
    A = sum(p.a for p in base["profile"])
    g.set_charges(sur=0.3 * g.M * np.where(A > 0, A, 1.0))
    assert np.allclose(arp.observed_tangent(g, Q, n), u0)
