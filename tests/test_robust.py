"""Closed-form Wasserstein route cost against a scenario LP, and basic robust-loss properties."""
import numpy as np
from scipy.optimize import linprog

from ccu.robust import LossParams, route_loss_stats, true_expected_loss

PARAMS = LossParams(f=1.0, gamma=1.0, rho=2.0, T_max=3.0)


def _lp_worst_case(tau, samples, eps, params, R=1e4, n_steps=12):
    """Worst-case expected loss over a type-1 W ball, LP on a candidate support set.

    Candidate points are the samples plus far shifts along +-e_k (the direction of
    unbounded slope); with R large the LP value approaches the closed form from below.
    """
    S, K = samples.shape
    shifts = np.geomspace(1.0, R, n_steps)
    pts = [samples]
    for k in range(K):
        for sign in (1.0, -1.0):
            for t in shifts:
                pts.append(samples + sign * t * np.eye(K)[k])
    G = np.vstack(pts)
    T = G @ tau
    loss_g = params.f + params.gamma * T + params.rho * np.maximum(0.0, T - params.T_max)
    M = len(G)
    cost = np.abs(samples[:, None, :] - G[None]).sum(-1)  # l1 ground norm
    c = -np.broadcast_to(loss_g, (S, M)).ravel()
    A_eq = np.zeros((S, S * M))
    for s in range(S):
        A_eq[s, s * M : (s + 1) * M] = 1.0
    res = linprog(
        c,
        A_ub=cost.ravel()[None],
        b_ub=[eps],
        A_eq=A_eq,
        b_eq=np.full(S, 1.0 / S),
        bounds=(0, None),
        method="highs",
    )
    assert res.success
    return -res.fun


def test_closed_form_matches_lp_worst_case():
    rng = np.random.default_rng(3)
    samples = rng.uniform(0.6, 1.6, (5, 2))
    tau = np.array([1.2, 2.1])
    eps = 0.05
    _, closed = route_loss_stats(tau, PARAMS, samples, eps)
    lp = _lp_worst_case(tau, samples, eps, PARAMS)
    assert lp <= closed + 1e-9
    assert closed - lp < 1e-3 * (1 + closed)


def test_eps_zero_is_empirical_mean():
    rng = np.random.default_rng(0)
    samples = rng.uniform(0.5, 2.0, (30, 3))
    tau = np.array([0.5, 1.0, 1.5])
    emp, robust = route_loss_stats(tau, PARAMS, samples, 0.0)
    T = samples @ tau
    expected = np.mean(PARAMS.f + PARAMS.gamma * T + PARAMS.rho * np.maximum(0, T - PARAMS.T_max))
    assert np.isclose(emp, expected) and np.isclose(robust, emp)
    assert np.isclose(true_expected_loss(tau, PARAMS, samples), emp)


def test_robust_cost_linear_in_eps():
    rng = np.random.default_rng(1)
    samples = rng.uniform(0.5, 2.0, (20, 2))
    tau = np.array([2.0, 0.7])
    vals = [route_loss_stats(tau, PARAMS, samples, e)[1] for e in (0.0, 0.1, 0.2, 0.4)]
    slopes = np.diff(vals) / np.diff([0.0, 0.1, 0.2, 0.4])
    assert np.allclose(slopes, (PARAMS.gamma + PARAMS.rho) * tau.max())
