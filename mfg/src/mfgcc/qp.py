"""Equilibria of the affine Cournot-congestion game as convex quadratic programs.

A *block* is either one carrier or a group of ``count`` identical carriers (replicas) that the solver treats
through their common aggregate.  Block b chooses column weights y_b >= 0 with one budget <w_b, y_b> <= B_b
(for a group, B_b is the group's budget).  Column j of block b has private profit p_bj and contribution L_b[:, j]
(deliveries in the zone-time coordinates).  The coupling is diagonal: carriers face the price slope m_k on the
aggregate Q_k = sum_b L_b y_b.  Every equilibrium notion used in the paper maximises a concave potential

    Phi(y) = sum_b [<p_b, y_b> - <sigma_b, a_b>] - <u, Q> - 1/2 <Q, mc Q> - 1/2 sum_b omega_b <a_b, m a_b>,

with a_b = L_b y_b and:
    Nash (finite N)      mc = m,            omega_b = 1/count_b  (own effect of each carrier; replicas symmetric)
    Wardrop (mean field) mc = m,            omega_b = 0
    social optimum       mc = m + kappa,    omega_b = 0           (welfare, with u = 0)
    ARP fixed point (N)  mc = m + kappa,    omega_b = 1/count_b   (then the posted charge is kappa * Q)
(see mfg/theory/model.tex for the derivations).  The reference solver is the interior-point method Clarabel; a
Frank-Wolfe solver (the learning dynamics of the paper, Section 4) is included and reports its own duality gap.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp


@dataclass
class Block:
    p: np.ndarray  # (n,) profit of each column
    L: sp.csr_matrix  # (d, n) contributions (deliveries per zone-time)
    w: np.ndarray  # (n,) budget weight of each column (vehicle-hours)
    B: float  # budget of the block
    count: int = 1  # number of identical carriers represented by the block
    sigma: np.ndarray | None = None  # (d,) extra linear cost per unit contribution (surcharge)
    tag: str = ""
    meta: dict = field(default_factory=dict)


@dataclass
class Solution:
    y: list  # per block column weights
    a: list  # per block contribution vectors (d,)
    Q: np.ndarray  # aggregate
    obj: float  # potential value
    gap: float  # Frank-Wolfe (duality) gap of the potential at the returned point
    status: str
    iters: int = 0


def _support(L: sp.csr_matrix) -> np.ndarray:
    return np.unique(L.tocoo().row)


def potential_grad(blocks, y, m, mc, omega, u):
    """Gradient of Phi w.r.t. each y_b, plus a_b and Q."""
    a = [B.L @ yb for B, yb in zip(blocks, y)]
    Q = np.sum(a, axis=0)
    g = []
    for B, yb, ab, om in zip(blocks, y, a, omega):
        price = mc * Q + u + om * m * ab
        if B.sigma is not None:
            price = price + B.sigma
        g.append(B.p - B.L.T @ price)
    return g, a, Q


def potential_value(blocks, y, m, mc, omega, u):
    a = [B.L @ yb for B, yb in zip(blocks, y)]
    Q = np.sum(a, axis=0)
    v = -np.dot(u, Q) - 0.5 * np.dot(Q, mc * Q)
    for B, yb, ab, om in zip(blocks, y, a, omega):
        v += np.dot(B.p, yb) - 0.5 * om * np.dot(ab, m * ab)
        if B.sigma is not None:
            v -= np.dot(B.sigma, ab)
    return v


def fw_gap(blocks, y, g) -> float:
    """max over the product of budget polytopes of <g, y' - y> (>= Phi* - Phi(y))."""
    tot = 0.0
    for B, yb, gb in zip(blocks, y, g):
        r = gb / B.w
        best = max(0.0, float(r.max())) * B.B
        tot += best - float(gb @ yb)
    return tot


def _omega(blocks, own: bool):
    return [1.0 / B.count if own else 0.0 for B in blocks]


def solve(blocks: list[Block], m: np.ndarray, *, mc: np.ndarray | None = None, own: bool = True,
          u: np.ndarray | None = None, tol: float = 1e-10, max_iter: int = 400) -> Solution:
    """Maximise Phi with Clarabel (interior point).  own=True: Nash; own=False: Wardrop / social."""
    import clarabel

    d = len(m)
    mc = m if mc is None else mc
    u = np.zeros(d) if u is None else u
    omega = _omega(blocks, own)
    sizes = [len(B.p) for B in blocks]
    sup = [_support(B.L) for B in blocks]
    ny = sum(sizes)
    na = sum(len(s) for s in sup)
    nx = ny + na + d
    # objective 1/2 x'Px + q'x (minimisation of -Phi)
    Pdiag = np.zeros(nx)
    q = np.zeros(nx)
    off_y, off_a = 0, ny
    rows_eq, cols_eq, vals_eq = [], [], []
    req = 0
    a_index = []
    for B, sb, om, n in zip(blocks, sup, omega, sizes):
        q[off_y:off_y + n] = -B.p
        ia = np.arange(off_a, off_a + len(sb))
        a_index.append(ia)
        Pdiag[ia] = om * m[sb]
        if B.sigma is not None:
            q[ia] = B.sigma[sb]
        # a_b - L_b[sb] y_b = 0
        Ls = B.L[sb].tocoo()
        rows_eq += list(req + np.arange(len(sb)))
        cols_eq += list(ia)
        vals_eq += [1.0] * len(sb)
        rows_eq += list(req + Ls.row)
        cols_eq += list(off_y + Ls.col)
        vals_eq += list(-Ls.data)
        req += len(sb)
        off_y += n
        off_a += len(sb)
    iQ = np.arange(ny + na, nx)
    Pdiag[iQ] = mc
    q[iQ] = u
    # Q - sum_b E_b a_b = 0
    rows_eq += list(req + np.arange(d))
    cols_eq += list(iQ)
    vals_eq += [1.0] * d
    for sb, ia in zip(sup, a_index):
        rows_eq += list(req + sb)
        cols_eq += list(ia)
        vals_eq += [-1.0] * len(sb)
    req += d
    # inequalities: budgets and y >= 0  (A x + s = b, s >= 0)
    rows_in, cols_in, vals_in, b_in = [], [], [], []
    r = 0
    off = 0
    for B, n in zip(blocks, sizes):
        rows_in += [r] * n
        cols_in += list(off + np.arange(n))
        vals_in += list(B.w)
        b_in.append(B.B)
        r += 1
        off += n
    rows_in += list(r + np.arange(ny))
    cols_in += list(np.arange(ny))
    vals_in += [-1.0] * ny
    b_in += [0.0] * ny
    r += ny
    A = sp.vstack([sp.csc_matrix((vals_eq, (rows_eq, cols_eq)), shape=(req, nx)),
                   sp.csc_matrix((vals_in, (rows_in, cols_in)), shape=(r, nx))]).tocsc()
    bvec = np.concatenate([np.zeros(req), np.array(b_in)])
    P = sp.diags(Pdiag).tocsc()
    st = clarabel.DefaultSettings()
    st.verbose = False
    st.tol_gap_abs = tol
    st.tol_gap_rel = tol
    st.tol_feas = 1e-10
    st.max_iter = max_iter
    solver = clarabel.DefaultSolver(P, q, A, bvec, [clarabel.ZeroConeT(req), clarabel.NonnegativeConeT(r)], st)
    res = solver.solve()
    x = np.asarray(res.x)
    y, off = [], 0
    for B, n in zip(blocks, sizes):
        yb = np.maximum(x[off:off + n], 0.0)
        tot = float(B.w @ yb)
        if tot > B.B:
            yb *= B.B / tot
        y.append(yb)
        off += n
    g, a, Q = potential_grad(blocks, y, m, mc, omega, u)
    return Solution(y, a, Q, potential_value(blocks, y, m, mc, omega, u), fw_gap(blocks, y, g), str(res.status),
                    int(res.iterations))


def frank_wolfe(blocks: list[Block], m: np.ndarray, *, mc: np.ndarray | None = None, own: bool = True,
                u: np.ndarray | None = None, iters: int = 2000, tol: float = 1e-9, y0=None,
                trace: list | None = None) -> Solution:
    """Conditional gradient on Phi with exact line search.

    Each iteration asks every block for one best response against the current prices (the most profitable column
    per unit budget: one routing-oracle call per carrier type), then moves the profile toward it.  This is the
    learning dynamics of potential mean-field games (fictitious play / generalized conditional gradient,
    Cardaliaguet-Hadikhanloo 2017, Lavigne-Pfeiffer 2023); its gap decreases at rate O(1/k).
    """
    d = len(m)
    mc = m if mc is None else mc
    u = np.zeros(d) if u is None else u
    omega = _omega(blocks, own)
    y = [np.zeros(len(B.p)) for B in blocks] if y0 is None else [v.copy() for v in y0]
    gap = np.inf
    k = 0
    for k in range(iters):
        g, a, Q = potential_grad(blocks, y, m, mc, omega, u)
        dirs = []
        gap = 0.0
        for B, yb, gb in zip(blocks, y, g):
            rr = gb / B.w
            j = int(np.argmax(rr))
            v = np.zeros_like(yb)
            if rr[j] > 0:
                v[j] = B.B / B.w[j]
            dirs.append(v - yb)
            gap += float(gb @ (v - yb))
        if trace is not None:
            trace.append(gap)
        if gap <= tol:
            break
        da = [B.L @ db for B, db in zip(blocks, dirs)]
        dQ = np.sum(da, axis=0)
        curv = float(dQ @ (mc * dQ)) + sum(om * float(x @ (m * x)) for om, x in zip(omega, da))
        step = 1.0 if curv <= 0 else min(1.0, gap / curv)
        y = [yb + step * db for yb, db in zip(y, dirs)]
    g, a, Q = potential_grad(blocks, y, m, mc, omega, u)
    return Solution(y, a, Q, potential_value(blocks, y, m, mc, omega, u), fw_gap(blocks, y, g), "fw", k + 1)


def aggregate_error_bound(gap: float, mc_min_ratio: float = 1.0) -> float:
    """||Q - Q*||_mc <= sqrt(2 gap): Phi is 1-strongly concave in Q in the mc-norm."""
    return float(np.sqrt(2.0 * max(gap, 0.0) / mc_min_ratio))
