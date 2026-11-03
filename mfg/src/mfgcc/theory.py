"""Closed forms and bounds of mfg/theory (numbers referred to in the paper)."""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from .qp import Block


def symmetric_one_zone(alpha: float, m: float, N: int) -> tuple[float, float]:
    """N identical carriers, linear profit alpha per delivery, slope m: (Q^N, Q^W) = (N/(N+1), 1) * alpha/m."""
    return N / (N + 1) * alpha / m, alpha / m


def sqrt_bound(a_W: list[np.ndarray], m: np.ndarray, counts: list[int] | None = None) -> float:
    """Theorem 1: ||A^N - A^W||_M <= 1/2 (sum_i ||a_i^W||_M^2)^(1/2).  a_W[b] is the contribution of one carrier of
    block b (for a replica block of n carriers pass the per-carrier contribution and counts[b] = n)."""
    counts = counts or [1] * len(a_W)
    return 0.5 * np.sqrt(sum(c * float(a @ (m * a)) for a, c in zip(a_W, counts)))


def tight_family(n: int, phi: float | None = None, tA: float = 1.0, tB: float = 0.0):
    """Proposition 2 (tightness family).  Two zones, M = I, n carriers of type A (contribution t e_1) and n of
    type B (contribution t v, v = (cos phi, sin phi)), linear profits alpha = G T^W with G the Gram matrix of
    (e_1, v) and Wardrop type totals T^W = (tA, tB).  Default phi: 1 - cos(phi) = 1/n.
    Returns dict with the closed-form Nash and Wardrop aggregates."""
    if phi is None:
        phi = float(np.arccos(1.0 - 1.0 / n))
    v = np.array([np.cos(phi), np.sin(phi)])
    J = np.column_stack([[1.0, 0.0], v])
    G = J.T @ J
    TW = np.array([tA, tB])
    alpha = G @ TW
    TN = np.linalg.solve(G + np.eye(2) / n, alpha)
    AW, AN = J @ TW, J @ TN
    return dict(phi=phi, v=v, J=J, G=G, alpha=alpha, TW=TW, TN=TN, AW=AW, AN=AN,
                gap=float(np.linalg.norm(AN - AW)),
                bound=0.5 * np.sqrt((tA ** 2 + tB ** 2) / n),
                s=float(max(TN.max(), TW.max()) / n))


def tight_family_blocks(n: int, phi: float | None = None, tA: float = 1.0, tB: float = 0.0, cap: float = 10.0):
    """The same family as replica blocks for the generic solver (linear profits, box [0, cap/n] per carrier)."""
    f = tight_family(n, phi, tA, tB)
    blocks = []
    for k, vec in enumerate((np.array([1.0, 0.0]), f["v"])):
        L = sp.csr_matrix(vec.reshape(2, 1))
        blocks.append(Block(p=np.array([f["alpha"][k]]), L=L, w=np.array([1.0]), B=cap, count=n, tag="AB"[k]))
    return blocks, f


def replica_affine_bound(G: np.ndarray, Dn_TW: np.ndarray) -> float:
    """Proposition 4 (affine interior replicas): ||A^N - A^W||_M <= ||D_n T^W||_{G^{-1}}."""
    return float(np.sqrt(Dn_TW @ np.linalg.solve(G, Dn_TW)))


def absorption_width(sigma_max: float, N: int, d: int) -> float:
    """Omega Theorem (credal absorption) uniform bound sigma_max * min{N-1, d+1, 1+sqrt(d ln(2d)/2)}."""
    return sigma_max * min(N - 1, d + 1, 1 + np.sqrt(d * np.log(2 * d) / 2))
