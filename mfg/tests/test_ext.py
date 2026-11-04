"""Tests for the extensions: lump-sum fees, free entry and further externalities (mfgcc.fees, mfgcc.extern)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mfgcc import fees as Fe  # noqa: E402
from mfgcc import extern as X  # noqa: E402
from mfgcc.city import CityGame  # noqa: E402
from mfgcc.leader import social_optimum, welfare  # noqa: E402
from mfgcc.qp import Block, solve  # noqa: E402
from mfgcc.stake import decompose  # noqa: E402
from test_mfg import rand_blocks  # noqa: E402

ALPHA, B, KAP = 3.0, 1.0, 0.4


def one_zone_game(alpha=ALPHA, b=B, kap=KAP, cap=1e6):
    base = [dict(rev=np.array([alpha]), cost=np.array([0.0]), L=sp.csr_matrix(np.ones((1, 1))), w=np.array([1.0]),
                 B=cap)]
    return CityGame("toy", 0, base, np.array([[0, 0]]), np.array([b]), np.array([kap]), alpha, 1.0, 1.0, {})


# ------------------------------------------------------------------ Item 1: fees with a fixed number of carriers
def test_lump_sum_fee_leaves_best_responses_unchanged():
    """J_i - T_i has the maximisers of J_i: verified by the variational inequality of every carrier."""
    rng = np.random.default_rng(3)
    bl, m = rand_blocks(rng, 4, 3)
    u = rng.normal(0, 0.2, 3)
    sol = solve(bl, m, own=True, u=u)
    T = rng.uniform(0, 5, 4)
    for i, (Bk, y, a) in enumerate(zip(bl, sol.y, sol.a)):
        A_other = sol.Q - a
        # best response of carrier i with the fee: maximise <p,y> - <a, m (A_-i + a)> - <u,a> - T_i
        br = solve([Block(Bk.p - Bk.L.T @ (m * A_other), Bk.L, Bk.w, Bk.B, 1)], m, own=True, u=u)
        pay = lambda yy, aa: float(Bk.p @ yy) - float(aa @ (m * (A_other + aa))) - float(u @ aa) - T[i]
        assert pay(br.y[0], br.a[0]) <= pay(y, a) + 1e-7 * (1 + abs(pay(y, a)))


def test_fee_table_recovers_deficit():
    rng = np.random.default_rng(5)
    bl, m = rand_blocks(rng, 3, 3)
    u = -np.abs(rng.normal(0, 0.3, 3))
    sol = solve(bl, m, own=True, u=u)
    ft = Fe.fee_table(bl, sol, m, u)
    assert ft["deficit"] == pytest.approx(-float(u @ sol.Q))
    for s in ("flat", "fleet", "profit"):
        assert ft[f"{s}_fee"] * ft["N"] == pytest.approx(ft["deficit"], rel=1e-10)
        assert ft[f"{s}_share"] == pytest.approx(ft["deficit"] / ft["profit_total"], rel=1e-10)
    assert ft["profit_ok"] == ft["aggregate_ok"]


def test_ex_post_recovery_is_not_lump_sum():
    """Recovering the realised deficit, T_i = -u Q / N, rebates u/N per own delivery (one zone, closed form)."""
    N, m = 4, B + KAP
    u = -0.5
    bl = [Block(np.array([ALPHA]), sp.csr_matrix(np.ones((1, 1))), np.array([1.0]), 1e6, N)]
    q_lump = solve(bl, np.array([m]), own=True, u=np.array([u])).Q[0]
    q_ep = solve(bl, np.array([m]), own=True, u=Fe.own_rebate_charge(np.array([u]), N)).Q[0]
    assert q_lump == pytest.approx(N / (N + 1) * (ALPHA - u) / m, rel=1e-8)
    assert q_ep == pytest.approx(N / (N + 1) * (ALPHA - u * (1 - 1 / N)) / m, rel=1e-8)
    assert abs(q_ep - q_lump) > 1e-3


# ------------------------------------------------------------------ Item 2: free entry
@pytest.mark.parametrize("rule", ["none", "obs", "pm", "pmfee"])
@pytest.mark.parametrize("Fv", [0.02, 0.5])  # 0.5: the market-power charge is a subsidy (N < m / kappa)
def test_one_zone_free_entry_matches_closed_form(rule, Fv):
    g = one_zone_game()
    F = np.array([Fv])
    cf = Fe.one_zone_free_entry(ALPHA, B, KAP, F[0], rule)
    r = Fe.free_entry(g, F, rule, k_init=[3.0], tol=1e-10, max_outer=600)
    assert r["N"] == pytest.approx(cf["N"], rel=1e-5)
    assert r["SW"] == pytest.approx(cf["SW"], rel=1e-6)
    # zero profit: welfare net of fixed costs = consumer surplus + city revenue (charge and fee)
    assert r["SW"] == pytest.approx(r["CS"] + r["R"] + r["fee_rev"], rel=1e-6)
    if rule == "pmfee" and Fv == 0.5:
        assert cf["T"] > 0 and cf["N"] < Fe.one_zone_free_entry(ALPHA, B, KAP, Fv, "pm")["N"]


def test_one_zone_free_entry_count_formula():
    """N* + 1 = (alpha - u) / sqrt(m F) for a fixed charge u (no charge here)."""
    m = B + KAP
    for F in (0.005, 0.05, 0.3):
        cf = Fe.one_zone_free_entry(ALPHA, B, KAP, F, "none")
        assert cf["N"] + 1 == pytest.approx(ALPHA / np.sqrt(m * F), rel=1e-12)


def test_observation_only_charge_is_second_best_under_free_entry():
    """One zone: welfare net of fixed costs as a function of a constant charge u is maximised at u = kappa Q."""
    m, F = B + KAP, 0.02
    s = np.sqrt(F / m)

    def sw(u):
        Q = (ALPHA - u) / m - s
        return ALPHA * Q - 0.5 * B * Q * Q - KAP * Q * Q - (Q / s) * F

    us = np.linspace(-0.5, 1.0, 30001)
    best = us[np.argmax([sw(x) for x in us])]
    obs = Fe.one_zone_free_entry(ALPHA, B, KAP, F, "obs")
    assert best == pytest.approx(obs["u"], abs=1e-4)
    pm = Fe.one_zone_free_entry(ALPHA, B, KAP, F, "pm")
    assert obs["SW"] >= pm["SW"]


def test_excess_entry_one_zone():
    """Mankiw-Whinston: at the free-entry count (no charge) welfare falls with one more carrier."""
    m, F = B + KAP, 0.02
    N = Fe.one_zone_free_entry(ALPHA, B, KAP, F, "none")["N"]

    def sw(n):
        Q = n / (n + 1) * ALPHA / m
        return ALPHA * Q - 0.5 * B * Q * Q - KAP * Q * Q - n * F

    eps = 1e-4
    assert (sw(N + eps) - sw(N - eps)) / (2 * eps) < 0


def test_free_entry_zero_profit_identity_city():
    from mfgcc import city as C
    g = C.build("Cairo", 0)
    F = Fe.calibrate_F(g, 2)
    for rule in ("none", "obs"):
        r = Fe.free_entry(g, F, rule, k_init=np.full(6, 2.5))
        assert r["err"] < 1e-5
        assert r["SW"] == pytest.approx(r["CS"] + r["R"] + r["fee_rev"], rel=1e-5)
    r0 = Fe.free_entry(g, F, "none", k_init=np.full(6, 2.5))
    assert np.all((r0["k"] > 2) & (r0["k"] < 3))  # calibration puts the free-entry count between k0 and k0 + 1


# ------------------------------------------------------------------ Item 3: further externalities
def _ext_from_E(blocks, E):
    return [dict(E=e, comp={"air": e, "clim": 0 * e, "noise": 0 * e, "cong": 0 * e}, vkm_leg=e, vkm_in=0 * e)
            for e in E]


def test_extended_pigou_with_tour_charge_is_optimal():
    """Charging E per tour plus kappa Q' per delivery makes the mean-field equilibrium the extended optimum."""
    rng = np.random.default_rng(11)
    bl, m0 = rand_blocks(rng, 3, 3)
    kap = rng.uniform(0.1, 0.5, 3)
    m = m0 + kap
    E = [rng.uniform(0, 0.5, len(Bk.p)) for Bk in bl]
    ble = [Block(Bk.p - e, Bk.L, Bk.w, Bk.B, 1) for Bk, e in zip(bl, E)]
    so = social_optimum(ble, m, kap)
    war = solve(ble, m, own=False, u=kap * so.Q)
    assert welfare(ble, war, m, kap) == pytest.approx(welfare(ble, so, m, kap), rel=1e-8)


def test_extended_charge_identical_carriers():
    """Proposition 20 with profits p - E: u = (kappa - m/N) Q' plus the tour charge implements the extended optimum."""
    from mfgcc import city as C
    g = C.build("Cairo", 0, n_types=1)
    m, kap = g.m, g.kappa
    rng = np.random.default_rng(2)
    E = [rng.uniform(0, 0.2, len(g.base[0]["rev"])) * g.gamma_h]
    for N in (3, 30):
        bl = [Block(g.base[0]["rev"] - g.base[0]["cost"] - E[0], g.base[0]["L"], g.base[0]["w"], g.base[0]["B"], N)]
        so = social_optimum(bl, m, kap)
        nash = solve(bl, m, own=True, u=(kap - m / N) * so.Q)
        assert welfare(bl, nash, m, kap) == pytest.approx(welfare(bl, so, m, kap), rel=1e-8)


def test_per_delivery_charge_exact_when_external_cost_is_delivery_proportional():
    """If E_j = <e, L_j> for a common e, the per-delivery charge kappa Q' + e implements the extended optimum."""
    rng = np.random.default_rng(13)
    bl, m0 = rand_blocks(rng, 3, 3)
    kap = rng.uniform(0.1, 0.5, 3)
    m = m0 + kap
    e = rng.uniform(0, 0.3, 3)
    E = [Bk.L.T @ e for Bk in bl]
    ble = [Block(Bk.p - x, Bk.L, Bk.w, Bk.B, 1) for Bk, x in zip(bl, E)]
    so = social_optimum(ble, m, kap)
    war = solve(bl, m, own=False, u=kap * so.Q + e)
    ext = _ext_from_E(bl, E)
    sw_ext = welfare(bl, war, m, kap) - X.external_cost(war, ext)["E"]
    assert sw_ext == pytest.approx(welfare(ble, so, m, kap), rel=1e-8)


def test_per_delivery_allocation_sums_to_total():
    rng = np.random.default_rng(17)
    bl, m = rand_blocks(rng, 3, 4)
    sol = solve(bl, m, own=True)
    E = [rng.uniform(0, 1, len(Bk.p)) for Bk in bl]
    ext = _ext_from_E(bl, E)
    eb = X.per_delivery_external(bl, sol, ext)
    assert float(eb @ sol.Q) == pytest.approx(X.external_cost(sol, ext)["E"], rel=1e-10)


def test_extended_welfare_decomposition():
    """SW_ext = CS + Pi + R_delivery + R_tour - E, with Pi net of both charges."""
    rng = np.random.default_rng(19)
    bl, m0 = rand_blocks(rng, 3, 3)
    b, kap = m0, rng.uniform(0.1, 0.5, 3)
    m = b + kap
    E = [rng.uniform(0, 0.4, len(Bk.p)) for Bk in bl]
    ble = [Block(Bk.p - x, Bk.L, Bk.w, Bk.B, 1) for Bk, x in zip(bl, E)]
    u = kap * social_optimum(ble, m, kap).Q
    sol = solve(ble, m, own=True, u=u)
    dec = decompose(ble, sol, b, kap, u)  # Pi here is net of the tour charge (profits p - E)
    Etot = X.external_cost(sol, _ext_from_E(bl, E))["E"]
    sw_ext = welfare(bl, sol, m, kap) - Etot
    assert dec["CS"] + dec["Pi"] + dec["R"] + Etot - Etot == pytest.approx(sw_ext, rel=1e-10)


def test_bpr_marginal_external_delay():
    """BPR t = t0 (1 + a (v/c)^beta): v dt/dv = beta (t - t0), the delay one vehicle imposes on the others."""
    t0, a, beta, c = 0.05, 0.15, 4.0, 1000.0
    v = 900.0
    t = lambda x: t0 * (1 + a * (x / c) ** beta)
    h = 1e-3
    ext = v * (t(v + h) - t(v - h)) / (2 * h)
    cong = (t(v) - t0) / t0
    assert ext == pytest.approx(beta * cong * t0, rel=1e-6)


def test_zone_paths_reproduce_travel_times():
    f = X.CACHE / "Cairo.npz"
    if not f.exists():
        pytest.skip("path cache not built (mfg/experiments/run_extern.py builds it)")
    geo = X.zone_paths("Cairo")
    TT = np.load(X.ROOT / "data/processed/Cairo/travel_time_matrix.npy")
    off = ~np.eye(len(TT), dtype=bool)
    assert np.max(np.abs(geo["time"][off] + 2 * 120.0 - TT[off]) / TT[off]) < 1e-5
    assert np.all(geo["dist"][off] > 0)
