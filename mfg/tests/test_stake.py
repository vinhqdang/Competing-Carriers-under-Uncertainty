"""Tests for the stakeholder accounting (mfgcc.stake)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mfgcc.leader import social_optimum, welfare  # noqa: E402
from mfgcc.qp import solve  # noqa: E402
from mfgcc import stake as S  # noqa: E402
from test_mfg import rand_blocks  # noqa: E402


def test_decomposition_sums_to_welfare_exactly():
    rng = np.random.default_rng(7)
    for _ in range(5):
        bl, _ = rand_blocks(rng, 4, 3)
        b, kap = rng.uniform(0.2, 1.0, 3), rng.uniform(0.1, 1.0, 3)
        m = b + kap
        u = rng.normal(0, 0.3, 3)
        for sol in (solve(bl, m, own=True, u=u), solve(bl, m, own=False, u=u), social_optimum(bl, m, kap)):
            dec = S.decompose(bl, sol, b, kap, u)
            sw = welfare(bl, sol, m, kap)
            assert dec["SW"] == pytest.approx(sw, rel=1e-12, abs=1e-12)
            assert dec["CS"] + dec["Pi"] + dec["R"] == pytest.approx(sw, rel=1e-12, abs=1e-12)
            assert dec["CS"] + dec["Pi_op"] - dec["CC"] == pytest.approx(sw, rel=1e-12, abs=1e-12)
            assert dec["CS"] >= 0 and dec["CC"] >= 0


def test_carrier_profit_matches_payoffs():
    """Pi equals the sum of the carriers' payoffs <p,y> - <a, M Q> - <u, a> (Nash, replica blocks of count 1)."""
    rng = np.random.default_rng(8)
    bl, _ = rand_blocks(rng, 3, 3)
    b, kap = rng.uniform(0.2, 1.0, 3), rng.uniform(0.1, 1.0, 3)
    m = b + kap
    u = rng.uniform(0, 0.3, 3)
    sol = solve(bl, m, own=True, u=u)
    pay = sum(float(B.p @ y) - float(a @ (m * sol.Q)) - float(u @ a) for B, y, a in zip(bl, sol.y, sol.a))
    assert S.decompose(bl, sol, b, kap, u)["Pi"] == pytest.approx(pay, rel=1e-10)


def test_identical_carriers_optimal_charge_closed_form():
    """N identical carriers: u*_N = (kappa - m/N) Q^opt makes the Nash equilibrium the social optimum."""
    from mfgcc import city as C
    g = C.build("Cairo", 0, n_types=1)
    m, kap = g.m, g.kappa
    for N in (2, 5, 40):
        bl = g.blocks(N)
        so = social_optimum(bl, m, kap)
        u = S.identical_optimal_charge(m, kap, so.Q, N)
        nash = solve(bl, m, own=True, u=u)
        assert np.sqrt(np.sum(m * (nash.Q - so.Q) ** 2)) <= 1e-6 * np.sqrt(np.sum(m * so.Q ** 2))
        assert welfare(bl, nash, m, kap) == pytest.approx(welfare(bl, so, m, kap), rel=1e-9)


def test_one_zone_charge_from_cournot_ratio():
    """Interior one-zone case: Q^N = N/(N+1) Q^W gives u* = kappa Q^opt - m Q^opt / N by direct algebra."""
    alpha, b, kap = 3.0, 1.0, 0.5
    m = b + kap
    for N in (1, 3, 10, 100):
        QW, Qopt = alpha / m, alpha / (m + kap)
        QN_with_u = lambda u: N / (N + 1) * (alpha - u) / m
        u = kap * Qopt - m * Qopt / N
        assert QN_with_u(u) == pytest.approx(Qopt, rel=1e-12)
        assert N / (N + 1) * QW == pytest.approx(QN_with_u(0.0))


def test_gini_and_decile_ratio():
    assert S.wgini([1, 1, 1, 1], [1, 2, 3, 4]) == pytest.approx(0.0, abs=1e-12)
    assert S.wgini([0, 0, 0, 1], [1, 1, 1, 1]) == pytest.approx(0.75)
    assert S.decile_ratio([1, 2], [1, 1], q=0.5) == pytest.approx(2.0)
    assert S.decile_ratio([1, 3, 5, 7, 9], [1, 1, 1, 1, 1], q=0.4) == pytest.approx(8.0 / 2.0)
