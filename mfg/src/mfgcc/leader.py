"""Leader quantities: Pigou toll, observation-only (ARP) fixed points, welfare, Gamma-maximin surcharge.

Delivery units: carriers face m = b + kappa; welfare SW(y) = sum <p, y> - 1/2 <Q, (m + kappa) Q> (consumer gross
benefit, routing costs, congestion cost; charges are transfers).  The observation-only rule posts
u <- kappa * Q(u); by Proposition 5 (mfg/theory) its unique fixed point is kappa * Q~ where Q~ is the aggregate of
the potential maximiser with coupling m + kappa (and own terms for the finite game), so one solve suffices.
"""
from __future__ import annotations

import numpy as np

from .qp import solve


def welfare(blocks, sol, m, kappa) -> float:
    return sum(float(B.p @ yb) for B, yb in zip(blocks, sol.y)) - 0.5 * float(sol.Q @ ((m + kappa) * sol.Q))


def social_optimum(blocks, m, kappa, **kw):
    return solve(blocks, m, mc=m + kappa, own=False, **kw)


def arp_fixed_point(blocks, m, kappa, own: bool, surcharge=None, **kw):
    """Fixed point u* = kappa Q(u* + surcharge) of the observation-only rule; returns (u*, equilibrium under it).

    surcharge: common per-delivery surcharge the carriers add themselves (Gamma-maximin, delta m w)."""
    lin = np.zeros(len(m)) if surcharge is None else surcharge
    sol = solve(blocks, m, mc=m + kappa, own=own, u=lin, **kw)
    return kappa * sol.Q, sol


def arp_iterate(blocks, m, kappa, own: bool, rounds: int = 15, theta: float = 1.0, u0=None, **kw):
    """Plain/damped ARP: u <- (1 - theta) u + theta kappa Q(u).  Returns list of posted charges."""
    u = np.zeros(len(m)) if u0 is None else u0.copy()
    path = [u.copy()]
    for _ in range(rounds):
        Q = solve(blocks, m, own=own, u=u, **kw).Q
        u = (1 - theta) * u + theta * kappa * Q
        path.append(u.copy())
    return path


def knorm_inv(v, kappa) -> float:
    return float(np.sqrt(np.sum(v * v / kappa)))


def knorm(v, kappa) -> float:
    return float(np.sqrt(np.sum(kappa * v * v)))
