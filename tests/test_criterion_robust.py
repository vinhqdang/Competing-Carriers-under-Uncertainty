"""Tests of the criterion-robustness study (experiments/run_criterion_robust.py, experiments/criterion_summary.py)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))

import criterion_summary as cs  # noqa: E402
import run_criterion_robust as rc  # noqa: E402
from ccu import dip, zmc_brl as zb  # noqa: E402
from ccu.ambiguity_game import HeurPool  # noqa: E402


def saa_tiny(seed=0, N=2):
    g = zb.make_tiny_game(N=N, Z=6, n_cust=3, seed=seed, K=2, ndays=20)
    days = 1.3 * np.exp(0.2 * np.random.default_rng(seed).standard_normal((20, 2)))
    for cr in g.carriers:
        cr.pool = HeurPool(cr.inst, days, "saa", ng_size=cr.inst.n)
    g._cache = {}
    return g


def test_cv_radii_are_on_the_grid_and_deterministic():
    g = saa_tiny()
    e1, s1 = rc.cv_radii(g, seed=0)
    e2, _ = rc.cv_radii(g, seed=0)
    assert len(e1) == g.N and e1 == e2
    assert all(e in rc.EPS_GRID for e in e1)
    assert np.all(np.isfinite(np.array(s1)))


def test_grid_points_depend_on_delivery_axis_and_dip():
    P = {"grid": {}}
    base = rc.grid_points(P)
    assert base[0] == (0.0, 0.0) and len(base) == 1 + len(rc.SFRAC_AX) + len(rc.THETAS_AX)
    P["ne"] = {"eqs": [{"social_cost_true": -100.0}]}
    P["dip"] = {"s_over_fee": -0.38, "fee": 1.0}
    P["grid"] = {f"0.0|{s}": {"social_cost_true": -100.0 - (1.0 if s == -0.2 else 0.0)} for s in rc.SFRAC_AX}
    pts = rc.grid_points(P)
    both = [p for p in pts if p[0] > 0 and p[1] != 0]
    assert {s for _, s in both} == {-0.2, -0.4} and len(both) == 2 * len(rc.THETAS_AX)
    assert rc.grid_points(P) == pts  # deterministic
    assert 14 <= len(pts) <= 18


def test_dip_target_is_equilibrium_under_fresh_pool_with_heuristic_oracle():
    g = saa_tiny(seed=2, N=3)
    g.gc = g.gc * 30
    o = dip.dip(g, so_iters=20)
    prof = rc.plans_from(g, rc.routes_of(o["profile"]))
    dip._set_u(g, np.array(o["u"]))
    if o["status"] == "exact":
        assert g.regrets(prof, fresh=True).max() < 1e-6
    ev = g.evaluate(prof)
    assert ev["served_share"] >= 0.0 and "welfare_true" not in ev  # tiny game has no true law installed


def _unit(sc0, scs, served, grid=None):
    eq = dict(social_cost=sc0, social_cost_true=sc0, welfare=-sc0, welfare_true=-sc0, served_share=served, vehicles=3, vehicle_hours=1.0,
              mean_price=1.0, mean_slowdown=0.1, max_slowdown=0.2, profit_total=0.0, charges=0.0, consumer_surplus=1.0, congestion_cost=1.0,
              routing_cost=1.0, routing_cost_true=1.0, gini_access=0.1, deliveries=1.0, demand=2.0, max_regret=0.0, converged=True,
              calls=10, kind="NE_zmc", X=[1.0], q=[1.0], lam=[0.0], routes=[])
    so = dict(eq, welfare=-scs, welfare_true=-scs, social_cost=scs, social_cost_true=scs, served_share=1.0)
    P = dict(ne=dict(eqs=[eq]), so=so)
    P["dip"] = dict(eq, status="exact", rounds=1, n_cuts=0, sc_model=scs, social_cost_true=scs, calls=30, calls_so=20, time_s=1.0,
                    s_over_fee=-0.4, u_mean_over_fee=-0.3, u_q_weighted_over_fee=-0.3, u_min_over_fee=-0.4, u_max_over_fee=-0.1, t_max=0.0,
                    slope_fee_over_nz=-0.375, corr_fee_over_nz=-0.99, n_active=5, verify_regret_pooled=0.0, verify_regret_fresh=0.0,
                    verify_target_fresh=0.0, loss_bound=0.0, welfare_true=-scs, fee=1.0)
    if grid:
        G = {}
        for (th, sf), sc in grid.items():
            G[f"{th}|{sf}"] = dict(eq, theta=th, sfrac=sf, social_cost=sc, social_cost_true=sc, calls=10)
        P.update(grid=G, gridcert={}, grid_calls=100, grid_n=len(G))
    return P


def test_summary_claims_flag_subsidy_dominance():
    grid = {(0.0, 0.0): -100.0, (0.0, -0.4): -150.0, (4.0, 0.0): -99.0, (4.0, -0.4): -152.0}
    U = {("London", 0, "saa"): _unit(-100.0, -155.0, 0.4, grid)}
    un, dp, gr = cs.unpriced_rows(U), cs.dip_rows(U), cs.grid_rows(U)
    assert abs(un.poa_true.iloc[0] - 1.55) < 1e-9 and abs(un.pos_true.iloc[0] - 1.55) < 1e-9
    cl = cs.claims_rows(gr, dp)
    r = cl.iloc[0]
    assert r.subsidy_dominates and r.best_delivery_is_subsidy and r.gain_congestion_only_pct == 0.0
    assert abs(r.delivery_share - 50.0 / 52.0) < 1e-9
    assert r.dip_ge_grid and abs(dp.gain_true_pct.iloc[0] - 55.0) < 1e-9


def test_agg_reports_sd_over_seeds():
    df = pd.DataFrame(dict(city=["A"] * 3, criterion=["saa"] * 3, v=[1.0, 2.0, 3.0]))
    a = cs.agg(df, ["city", "criterion"], ["v"])
    assert a.v.iloc[0] == 2.0 and abs(a.v_sd.iloc[0] - 1.0) < 1e-12 and a.n_seeds.iloc[0] == 3
