"""Stakeholder accounting for the zone-time delivery market: welfare decomposition, charge rules, exposure.

Model conventions (mfg/theory/model.tex): inverse demand alpha - b Q, a delivery at a coordinate carries the delay
cost kappa Q (so carriers pay (b + kappa) Q per delivery, m = b + kappa) and a charge u per delivery.  With
p = carrier profit vector of the columns (it contains the reference price alpha and the routing cost):

    consumer surplus      CS    = 1/2 <b, Q^2>
    operating profit      Pi_op = <p, y> - <b, Q^2>          (revenue (alpha - bQ)Q minus routing cost)
    congestion cost       CC    = <kappa, Q^2>               (delay cost of all vehicles; borne by the fleet here)
    charge revenue        R     = <u, Q>                     (a transfer to the city)
    carrier profit (net)  Pi    = Pi_op - CC - R

    SW = CS + Pi + R = CS + Pi_op - CC = <p, y> - 1/2 <Q, (m + kappa) Q>   (identity; tests/test_stake.py)

Charge rules for the finite market with N carriers (all evaluated at the Nash equilibrium under the posted u):
    none  u = 0
    obs   observation-only fixed point u = kappa Q(u)   (Pigou without subsidy; leader.arp_fixed_point)
    pm    Pigou minus market power: start from u0 = kappa Q^opt - m abar^opt (abar = social-optimum aggregate per
          active carrier), then correct u <- u + theta m (1 + 1/n_act) (Q(u) - Q^opt) for a fixed number of rounds so
          that the Nash aggregate matches Q^opt up to the reported residual.
"""
from __future__ import annotations

import numpy as np

from .leader import arp_fixed_point, social_optimum, welfare
from .qp import solve


def decompose(blocks, sol, b, kappa, u=None) -> dict:
    Q = sol.Q
    prof = sum(float(B.p @ yb) for B, yb in zip(blocks, sol.y))
    cs = 0.5 * float(np.sum(b * Q * Q))
    pi_op = prof - float(np.sum(b * Q * Q))
    cc = float(np.sum(kappa * Q * Q))
    rev = 0.0 if u is None else float(np.dot(u, Q))
    return dict(CS=cs, Pi_op=pi_op, CC=cc, R=rev, Pi=pi_op - cc - rev, SW=cs + pi_op - cc)


def n_active(blocks, sol, tol=1e-9):
    """Number of carriers with a positive delivery at each coordinate (replica blocks count k)."""
    return np.sum([(a / B.count > tol) * B.count for a, B in zip(sol.a, blocks)], axis=0)


def pm_charge(blocks, m, kappa, so, rounds: int = 25, theta: float = 0.8):
    """Pigou-minus-market-power charge matching the social-optimum aggregate (see module docstring).

    Returns (u, equilibrium under u, relative M-norm residual of the aggregate)."""
    nact = np.maximum(n_active(blocks, so), 1.0)
    abar = so.Q / nact
    u = kappa * so.Q - m * abar
    den = np.sqrt(np.sum(m * so.Q ** 2))
    sol = solve(blocks, m, own=True, u=u)
    for _ in range(rounds):
        u = u + theta * m * (1.0 + 1.0 / nact) * (sol.Q - so.Q)
        sol = solve(blocks, m, own=True, u=u)
    res = float(np.sqrt(np.sum(m * (sol.Q - so.Q) ** 2)) / den)
    return u, sol, res


def identical_optimal_charge(m, kappa, Qopt, N):
    """N identical carriers (one replica block): the charge that makes the Nash aggregate equal Q^opt.

    u*_N = kappa Q^opt - (m / N) Q^opt   (exact, any coupling; Proposition in Section 'Who gains')."""
    return (kappa - m / N) * Qopt


# ------------------------------------------------------------------ exposure
def wgini(v, w) -> float:
    v, w = np.asarray(v, float), np.asarray(w, float)
    o = np.argsort(v)
    v, w = v[o], w[o]
    if v.sum() <= 0 or w.sum() <= 0:
        return float("nan")
    cw = np.concatenate([[0.0], np.cumsum(w) / w.sum()])
    cv = np.concatenate([[0.0], np.cumsum(w * v) / np.sum(w * v)])
    return float(1.0 - np.sum((cw[1:] - cw[:-1]) * (cv[1:] + cv[:-1])))


def decile_ratio(v, w, q: float = 0.1) -> float:
    """Mean of the top population decile over the mean of the bottom one (residents ranked by exposure)."""
    v, w = np.asarray(v, float), np.asarray(w, float)
    o = np.argsort(v)
    v, w = v[o], w[o]
    W = w.sum()
    cw = np.concatenate([[0.0], np.cumsum(w)])

    def tail(lo, hi):  # weight of each unit inside the population interval [lo W, hi W]
        take = np.clip(np.minimum(cw[1:], hi * W) - np.maximum(cw[:-1], lo * W), 0.0, None)
        return float(np.sum(take * v) / take.sum())

    bot, top = tail(0.0, q), tail(1.0 - q, 1.0)
    return float(top / bot) if bot > 0 else float("inf")


def spearman(x, y) -> float:
    from scipy.stats import spearmanr
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 4 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return float("nan")
    return float(spearmanr(x, y)[0])


def exposure_grid(g, Q):
    """Vehicle-hours per resident in each covered zone and hour.

    X_zt = r Q_zt mult_z is the in-zone (delivery dwell) vehicle-hours of the real city (mult_z: real over modelled
    deliveries of the zone, the slice multiplicity of the congestion calibration), divided by the residents of
    the zone.  Returns zones (covered), pop, area, E (n_zones x H) and X (vehicle-hours, same shape)."""
    zc, hc = g.coords[:, 0], g.coords[:, 1]
    zones = np.unique(zc)
    idx = {int(z): i for i, z in enumerate(zones)}
    zi = np.array([idx[int(z)] for z in zc])
    pop = np.zeros(len(zones))
    area = np.zeros(len(zones))
    pop[zi] = g.meta["pop_c"]
    area[zi] = g.meta["area_c"]
    X = np.zeros((len(zones), 10))
    np.add.at(X, (zi, hc), g.r * Q * g.meta["mult_c"])
    return zones, pop, area, X / pop[:, None], X


def exposure_metrics(g, Q, Q0=None) -> dict:
    zones, pop, area, E, X = exposure_grid(g, Q)
    ez = E.sum(1)  # vehicle-hours per resident per day
    out = dict(
        n_zones=len(zones), pop_cov=float(pop.sum()),
        veh_hours=float(X.sum()),
        exp_mean_min=float(60.0 * np.sum(pop * ez) / pop.sum()),  # vehicle-minutes per resident-day
        gini_zone=wgini(ez, pop),
        gini_zh=wgini(E.ravel(), np.repeat(pop, E.shape[1])),
        d10d1=decile_ratio(ez, pop),
        peak_hour_min=float(60.0 * (X.sum(0) / pop.sum()).max()),
    )
    if Q0 is not None:
        _, _, _, E0, X0 = exposure_grid(g, Q0)
        x, x0 = X.sum(1), X0.sum(1)
        dens = np.log(pop / area)
        ok = x0 > 0
        out["corr_rel_dens"] = spearman(dens[ok], (x[ok] - x0[ok]) / x0[ok])
        sh, sh0 = x / x.sum(), x0 / x0.sum()
        out["corr_share_dens"] = spearman(dens[ok], (sh[ok] - sh0[ok]) / sh0[ok])
        out["dens_mass_shift"] = float(np.sum(sh * dens) - np.sum(sh0 * dens))  # change in mean log density of exposure
    return out
