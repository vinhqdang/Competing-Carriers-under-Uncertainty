"""Zone-Market Clearing search (ZMC): the direction-A method.

All carriers are priced at ONE common vector lam (the shadow price of the zone aggregates in the dual of the
convexified potential). One round = N oracle calls (parallel), and returns for EVERY coordinate k at once the signed
clearing residual s_k = A_k(lam) - lam_k / M_k.  Each coordinate keeps a bracket [l_k, u_k] that is updated by the sign
of s_k (Theorem 2 in theory.tex) and the next price is a safeguarded secant step on a decreasing (isotonic) interpolant
of the observed responses (odd rounds) or the bracket midpoint (even rounds).  The cost per round does not depend on
the number of zones.  The pure profile is then obtained from the collected plans (restricted master + rounding,
no oracle calls) and polished by best responses.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import isotonic_regression

from core import Game, Plan


def dual_value(g: Game, lam: np.ndarray, plans: list[Plan]) -> float:
    """G(lam) = sum_i min_p [ctilde_i(p) + <lam, a_i(p)>] - 1/2 lam^T M^-1 lam (exact when plans are oracle answers)."""
    M = g.M
    v = sum(g.ctilde(p) + float(lam @ p.a) for p in plans)
    return v - 0.5 * float(lam @ (lam / M))


def _secant(x: np.ndarray, y: np.ndarray, m: float, lo: float, hi: float) -> float:
    """Crossing of the decreasing piecewise-linear (isotonic) interpolant of (x, y) with l/m, clipped to [lo, hi]."""
    ux, inv = np.unique(x, return_inverse=True)
    cnt = np.bincount(inv).astype(float)
    uy = np.bincount(inv, weights=y) / cnt
    if len(ux) > 1:
        uy = isotonic_regression(uy, weights=cnt, increasing=False).x
    f = uy - ux / m
    r = None
    if f[0] <= 0:
        r = min(ux[0], m * uy[0])
    else:
        for j in range(len(ux) - 1):
            if f[j] > 0 >= f[j + 1]:
                r = ux[j] + (ux[j + 1] - ux[j]) * f[j] / (f[j] - f[j + 1])
                break
        if r is None:
            r = max(ux[-1], m * uy[-1])
    return float(min(hi, max(lo, r)))


def zmc(g: Game, rounds: int = 10, hist: list | None = None, mode: str = "secant"):
    """mode: 'secant' (safeguarded secant, default), 'bisect' (pure simultaneous bisection), 'free' (no brackets)."""
    M = g.M
    d = g.d
    Amax = np.zeros(d)
    for i, cr in enumerate(g.carriers):
        Amax += g.make_plan(i, cr.D).a  # contributions are monotone in q, so this bounds every aggregate
    lo = np.zeros(d)
    hi = M * Amax
    lam = 0.5 * (lo + hi) if mode != "free" else np.zeros(d)
    X, Y = [], []
    best = (-np.inf, None, None)
    pools = [dict() for _ in range(g.N)]
    for t in range(rounds):
        plans = [g.oracle(i, lam, rho=1.0) for i in range(g.N)]
        for i, p in enumerate(plans):
            pools[i][p.key()] = p
        A = sum(p.a for p in plans)
        G = dual_value(g, lam, plans)
        if G > best[0]:
            best = (G, lam.copy(), plans)
        if hist is not None:
            hist.append((g.calls, G, lam.copy(), plans))
        s = A - lam / M
        X.append(lam.copy())
        Y.append(A)
        if mode != "free":
            lo = np.where(s > 0, np.maximum(lo, lam), lo)
            hi = np.where(s < 0, np.minimum(hi, lam), hi)
            zero = s == 0
            lo = np.where(zero, lam, lo)
            hi = np.where(zero, lam, hi)
        if mode == "bisect" or (mode == "secant" and t % 2 == 1):
            lam = 0.5 * (lo + hi)
            continue
        Xa, Ya = np.array(X), np.array(Y)
        new = np.empty(d)
        for k in range(d):
            if mode == "free":
                new[k] = _secant(Xa[:, k], Ya[:, k], M[k], 0.0, M[k] * Amax[k])
            else:
                new[k] = _secant(Xa[:, k], Ya[:, k], M[k], lo[k], hi[k])
        lam = new
    return best, pools


# backwards-compatible name used in early scratch tests
def ssd(g: Game, rounds: int = 10, hist: list | None = None):
    return zmc(g, rounds=rounds, hist=hist, mode="free")
