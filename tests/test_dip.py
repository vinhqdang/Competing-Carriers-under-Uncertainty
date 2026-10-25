"""Dual implementation pricing (ccu.dip): identities and the method on tiny games with exhaustive enumeration."""
import itertools

import numpy as np
import pytest

from ccu import dip, zmc, zmc_brl as zb


def _profiles(g):
    g.set_charges()
    _, _, plans = zb.enumerate_game(g)
    return plans


def _rebuild(g, i, p):
    return g._plan(i, (), p.q, p.a[g.Z:], p.cr)


@pytest.mark.parametrize("seed", range(3))
def test_potential_identity(seed):
    """Phi_u(sigma) - SC(sigma) - wedge(sigma) is the same constant for every pure profile (Lemma 1)."""
    g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=seed)
    g.gc = g.gc * 30
    plans = _profiles(g)
    Qref = np.random.default_rng(seed).uniform(0, 8, g.Z)
    u = dip.tangent_charge(g, Qref)
    g.set_charges(toll=dip.instruments(g, u)[2])
    vals = []
    for idx in itertools.product(*[range(len(p)) for p in plans]):
        prof = [_rebuild(g, i, plans[i][k][1]) for i, k in enumerate(idx)]
        vals.append(g.potential(prof) - dip.social_cost(g, prof) - dip.potential_wedge(g, prof, Qref, u))
    assert np.ptp(vals) < 1e-8


def test_instruments_reproduce_zone_charge():
    g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=4)
    u = np.random.default_rng(1).normal(0, 3, g.Z)
    s, t, toll = dip.instruments(g, u)
    assert np.all(t >= -1e-12)
    for i, pl in enumerate(_profiles(g)):
        for _, p in pl:
            assert abs(float(toll @ p.a) - float(u @ p.q)) < 1e-9


@pytest.mark.parametrize("seed", range(3))
def test_personalised_charges_make_social_deviations_private(seed):
    """Under U_iz = kappa Q*_-i - b d_iz / 2 a carrier's cost difference equals the social-cost difference (Prop. 2)."""
    g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=seed)
    g.gc = g.gc * 30
    plans = _profiles(g)
    rng = np.random.default_rng(seed)
    idx = [int(rng.integers(len(p))) for p in plans]
    prof = [_rebuild(g, i, plans[i][k][1]) for i, k in enumerate(idx)]
    U = dip.personalised_charge(g, prof)
    A = sum(p.a for p in prof)
    for i in range(g.N):
        Am = A - prof[i].a
        base_priv = g.J(i, prof[i], Am) + float(U[i] @ prof[i].q)
        base_soc = dip.social_cost(g, prof)
        for _, p in plans[i]:
            p = _rebuild(g, i, p)
            alt = prof.copy()
            alt[i] = p
            dpriv = g.J(i, p, Am) + float(U[i] @ p.q) - base_priv
            dsoc = dip.social_cost(g, alt) - base_soc
            assert abs(dpriv - dsoc) < 1e-8


@pytest.mark.parametrize("seed", range(4))
def test_dip_returns_exact_equilibrium_and_improves(seed):
    g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=seed)
    g.gc = g.gc * 20
    base = zmc.run_zmc(g, rounds=6)
    sc0 = dip.social_cost(g, base["profile"])
    out = dip.dip(g, so_iters=20)
    assert g.regrets(out["profile"], fresh=True).max() < 1e-7
    assert out["sc"] <= sc0 + 1e-9 or out["status"] != "exact"
    if out["status"] == "exact":
        assert abs(out["sc"] - out["sc_target"]) < 1e-9


def test_surcharge_shift_keeps_target():
    """P_delta(sigma*) = P_0(sigma*) - sur: the shifted charge keeps the target an exact equilibrium (Theorem 6)."""
    g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=2)
    g.gc = g.gc * 20
    out = dip.dip(g, so_iters=20)
    if out["status"] != "exact":
        pytest.skip("target not implementable in this instance")
    w = np.ones(2 * g.Z)
    for de in (0.1, 0.5):
        sur = de * g.M * w
        ud = dip.surcharge_shift(g, out["u"], sur)
        g.set_charges(toll=dip.instruments(g, ud)[2], sur=sur)
        prof = [g.plan_from_routes(i, p.routes) for i, p in enumerate(out["profile"])]
        assert g.regrets(prof).max() < 1e-7


def test_family_restricted_implementation_runs():
    g = zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=1)
    g.gc = g.gc * 20
    target, info = dip.social_target(g, iters=20)
    B, ufix = dip.grid_family(g, g.gc * sum(p.a[g.Z:] for p in target))
    imp = dip.implement(g, target, dip.tangent_charge(g, sum(p.q for p in target)), basis=B, ufix=ufix)
    assert imp["status"] in ("exact", "empty", "rounds")
    u = imp["u"]
    act = dip.active_zones(g)
    y = np.linalg.lstsq(B[act], u[act], rcond=None)[0]
    assert np.allclose(B[act] @ y, u[act])
