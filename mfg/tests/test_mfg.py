"""Tests for mfg/src/mfgcc (run: python3 -m pytest mfg/tests -q)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mfgcc import theory as th  # noqa: E402
from mfgcc.leader import arp_fixed_point, arp_iterate, knorm_inv, social_optimum, welfare  # noqa: E402
from mfgcc.profiles import congestion_profile, demand_profile, peak_levels  # noqa: E402
from mfgcc.qp import Block, frank_wolfe, solve  # noqa: E402


def one_zone(N, alpha=3.0, m=1.5, cap=10.0):
    return [Block(np.array([alpha]), sp.csr_matrix(np.ones((1, 1))), np.array([1.0]), cap, 1) for _ in range(N)], \
        np.array([m])


def rand_blocks(rng, N, d, ncol=5):
    bl = []
    for _ in range(N):
        L = rng.uniform(0, 1, (d, ncol)) * (rng.random((d, ncol)) < 0.7) + 0.05
        bl.append(Block(rng.uniform(1, 3, ncol) * L.sum(0), sp.csr_matrix(L), rng.uniform(0.5, 1.5, ncol),
                        rng.uniform(0.5, 1.5) * d / N, 1))
    return bl, rng.uniform(0.5, 2.0, d)


@pytest.mark.parametrize("N", [1, 2, 5, 20])
def test_symmetric_closed_form(N):
    bl, m = one_zone(N)
    QN, QW = th.symmetric_one_zone(3.0, 1.5, N)
    assert solve(bl, m, own=True).Q[0] == pytest.approx(QN, abs=1e-6)
    assert solve(bl, m, own=False).Q[0] == pytest.approx(QW, abs=1e-6)


def test_replica_block_equals_individual_carriers():
    rng = np.random.default_rng(0)
    bl, m = rand_blocks(rng, 1, 3)
    k = 4
    group = [Block(bl[0].p, bl[0].L, bl[0].w, bl[0].B, count=k)]
    indiv = [Block(bl[0].p, bl[0].L, bl[0].w, bl[0].B / k, 1) for _ in range(k)]
    assert np.allclose(solve(group, m, own=True).Q, solve(indiv, m, own=True).Q, atol=1e-5)
    assert np.allclose(solve(group, m, own=False).Q, solve(indiv, m, own=False).Q, atol=1e-5)


def test_frank_wolfe_matches_interior_point():
    rng = np.random.default_rng(1)
    bl, m = rand_blocks(rng, 4, 3)
    for own in (True, False):
        ref = solve(bl, m, own=own)
        fw = frank_wolfe(bl, m, own=own, iters=20000, tol=1e-8)
        assert fw.gap <= 1e-6 or fw.iters == 20000
        assert np.linalg.norm(np.sqrt(m) * (fw.Q - ref.Q)) <= np.sqrt(2 * max(fw.gap, 0)) + 1e-4


def test_linearisation_lemma():
    rng = np.random.default_rng(2)
    bl, m = rand_blocks(rng, 3, 3)
    sN = solve(bl, m, own=True)
    sur = [Block(b.p, b.L, b.w, b.B, 1, sigma=m * a) for b, a in zip(bl, sN.a)]
    assert np.allclose(solve(sur, m, own=False).Q, sN.Q, atol=1e-5)


def test_sqrt_bound_and_tight_family():
    rng = np.random.default_rng(3)
    for _ in range(10):
        bl, m = rand_blocks(rng, 5, 3)
        sN, sW = solve(bl, m, own=True), solve(bl, m, own=False)
        gap = np.sqrt(np.sum(m * (sN.Q - sW.Q) ** 2))
        assert gap <= th.sqrt_bound(sW.a, m) + 1e-5
    for n in (4, 64, 1024):
        f = th.tight_family(n)
        assert f["gap"] == pytest.approx(np.sqrt(1 / (8 * n) + (2 * n - 1) / (8 * n ** 3)), rel=1e-10)
        assert f["gap"] >= f["bound"] / np.sqrt(2) - 1e-12
        assert f["gap"] <= f["bound"] + 1e-12
        bl, _ = th.tight_family_blocks(n)
        dq = solve(bl, np.ones(2), own=True).Q - solve(bl, np.ones(2), own=False).Q
        assert np.linalg.norm(dq) == pytest.approx(f["gap"], rel=2e-3)


def test_leader_fixed_point_contraction_and_welfare():
    rng = np.random.default_rng(4)
    bl, _ = rand_blocks(rng, 4, 3)
    b, kap = rng.uniform(0.2, 1.0, 3), rng.uniform(0.1, 1.0, 3)
    m = b + kap
    rho = float((kap / m).max())
    for own in (True, False):
        u, eqm = arp_fixed_point(bl, m, kap, own=own)
        assert np.allclose(kap * solve(bl, m, own=own, u=u).Q, u, atol=1e-6)
        path = arp_iterate(bl, m, kap, own=own, rounds=6)
        d = [knorm_inv(p - u, kap) for p in path]
        for a, c in zip(d[:-1], d[1:]):
            assert c <= rho * a + 1e-6
    so = social_optimum(bl, m, kap)
    _, fp = arp_fixed_point(bl, m, kap, own=False)
    assert welfare(bl, fp, m, kap) == pytest.approx(welfare(bl, so, m, kap), abs=1e-5)
    _, fpN = arp_fixed_point(bl, m, kap, own=True)
    loss = welfare(bl, so, m, kap) - welfare(bl, fpN, m, kap)
    assert -1e-6 <= loss <= 0.5 * sum(float(a @ (m * a)) for a in so.a) + 1e-6


def test_profiles():
    am, pm, grade = peak_levels("Cairo", 0.405)
    assert grade == "A" and am == pytest.approx(0.427) and pm == pytest.approx(0.758)
    c = congestion_profile("Cairo", 0.405, 1.0)
    assert c[0] == pytest.approx(0.427, abs=0.01) and c[-1] == pytest.approx(0.758, abs=0.01)
    assert np.allclose(congestion_profile("Cairo", 0.405, 0.0), 0.405)
    assert demand_profile(1.0).mean() == pytest.approx(1.0) and np.allclose(demand_profile(0.0), 1.0)
    assert peak_levels("Moscow", 0.54)[2].startswith("C")


def test_city_instance_and_gap_order():
    from mfgcc import city as C
    g = C.build("Cairo", 0)
    assert g.d > 0 and np.all(g.b > 0) and np.all(g.kappa > 0) and g.meta["rho"] < 1
    for B in g.base:
        assert B["L"].shape[0] == g.d and np.all(B["w"] > 0) and B["B"] > 0
    m = g.m
    sW = solve(g.blocks(1), m, own=False)
    gaps = []
    for k in (4, 32):
        sN = solve(g.blocks(k), m, own=True)
        gaps.append(np.abs(sN.Q - sW.Q).max())
    assert gaps[1] < gaps[0] / 4  # the gap shrinks roughly like 1/k
