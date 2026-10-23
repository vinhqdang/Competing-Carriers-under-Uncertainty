"""Baselines: sequential best-response dynamics, Frank-Wolfe on the convexified potential with rounding,
and column generation (simplicial decomposition) with rounding. Every oracle call is counted in game.calls."""
from __future__ import annotations

import numpy as np

from core import Game, Plan


def zero_profile(g: Game) -> list[Plan]:
    return [g.make_plan(i, np.zeros(g.Z)) for i in range(g.N)]


def br_dynamics(g: Game, init=None, max_rounds=200, tol=1e-9, trace=None):
    """Gauss-Seidel best responses until a full round produces no strict improvement."""
    prof = list(init) if init is not None else zero_profile(g)
    A = sum(p.a for p in prof)
    stable = 0
    rounds = 0
    while rounds < max_rounds:
        rounds += 1
        for i in range(g.N):
            Am = A - prof[i].a
            b = g.br(i, Am)
            if g.J(i, b, Am) < g.J(i, prof[i], Am) - tol:
                A = Am + b.a
                prof[i] = b
                stable = 0
            else:
                stable += 1
            if trace is not None:
                trace.append((g.calls, prof.copy()))
            if stable >= g.N:
                return prof, True
    return prof, False


# ---------------------------------------------------------------- convexified potential (D1)
def _round_support(g: Game, pools, weights):
    """Derandomised rounding (conditional expectations on the potential, main.tex eq. (8.1))."""
    M = g.M
    N = g.N
    mean = [sum(w * p.a for w, p in zip(weights[i], pools[i])) for i in range(N)]
    var = [sum(w * float((p.a - mean[i]) @ (M * (p.a - mean[i]))) for w, p in zip(weights[i], pools[i]))
           for i in range(N)]
    lin = [sum(w * g.ctilde(p) for w, p in zip(weights[i], pools[i])) for i in range(N)]
    chosen: list[Plan | None] = [None] * N
    for j in np.argsort([-v for v in var]):
        best, bv = None, np.inf
        for w, p in zip(weights[j], pools[j]):
            if w <= 1e-12:
                continue
            mu = sum((chosen[i].a if chosen[i] is not None else mean[i]) for i in range(N) if i != j) + p.a
            val = sum(g.ctilde(chosen[i]) if chosen[i] is not None else lin[i] for i in range(N) if i != j)
            val += g.ctilde(p) + 0.5 * float(mu @ (M * mu))
            val += 0.5 * sum(var[i] for i in range(N) if i != j and chosen[i] is None)
            if val < bv:
                best, bv = p, val
        chosen[j] = best
    return chosen


def frank_wolfe(g: Game, iters=50, init=None):
    """FW with exact line search on Phi_bar(x) = sum <x_i, ctilde_i> + 1/2 ||Abar||_M^2. Returns rounded profile."""
    M = g.M
    prof = list(init) if init is not None else zero_profile(g)
    pools = [[p] for p in prof]
    weights = [[1.0] for _ in prof]
    Abar = sum(p.a for p in prof)
    lin = np.array([g.ctilde(p) for p in prof])
    hist = []
    for t in range(iters):
        S = [g.oracle(i, M * Abar, rho=1.0) for i in range(g.N)]
        As = sum(s.a for s in S)
        ls = np.array([g.ctilde(s) for s in S])
        # gap
        gap = float(lin.sum() - ls.sum() + (Abar - As) @ (M * Abar))
        hist.append((g.calls, gap))
        dA = As - Abar
        den = float(dA @ (M * dA))
        num = gap
        gam = 1.0 if den <= 0 else min(1.0, max(0.0, num / den))
        if gam <= 0:
            break
        for i in range(g.N):
            weights[i] = [w * (1 - gam) for w in weights[i]]
            k = next((j for j, p in enumerate(pools[i]) if p.key() == S[i].key()), None)
            if k is None:
                pools[i].append(S[i])
                weights[i].append(gam)
            else:
                weights[i][k] += gam
        Abar = Abar + gam * dA
        lin = lin + gam * (ls - lin)
    return _round_support(g, pools, weights), hist, (pools, weights)


def _restricted_master(g: Game, pools, weights, iters=400):
    """Solve min Phi_bar over the product of simplices of the pools (pairwise FW, no oracle calls)."""
    M = g.M
    N = g.N
    Ap = [np.array([p.a for p in pools[i]]) for i in range(N)]
    cp = [np.array([g.ctilde(p) for p in pools[i]]) for i in range(N)]
    W = [np.array(w, dtype=float) for w in weights]
    for _ in range(iters):
        Abar = sum(W[i] @ Ap[i] for i in range(N))
        lam = M * Abar
        best = None
        for i in range(N):
            r = cp[i] + Ap[i] @ lam
            s = int(np.argmin(r))
            act = np.flatnonzero(W[i] > 1e-14)
            aw = act[int(np.argmax(r[act]))]
            gapi = r[aw] - r[s]
            if best is None or gapi > best[0]:
                best = (gapi, i, s, aw)
        gapi, i, s, aw = best
        if gapi < 1e-10:
            break
        dA = Ap[i][s] - Ap[i][aw]
        den = float(dA @ (M * dA))
        gmax = W[i][aw]
        gam = gmax if den <= 0 else min(gmax, gapi / den)
        W[i][s] += gam
        W[i][aw] -= gam
    return [list(w) for w in W]


def column_generation(g: Game, max_iter=50, tol=1e-7, init=None):
    """Simplicial decomposition: restricted master on pools + one pricing call per carrier per iteration."""
    M = g.M
    prof = list(init) if init is not None else zero_profile(g)
    pools = [[p] for p in prof]
    weights = [[1.0] for _ in prof]
    hist = []
    for it in range(max_iter):
        weights = _restricted_master(g, pools, weights)
        Abar = sum(sum(w * p.a for w, p in zip(weights[i], pools[i])) for i in range(g.N))
        added = 0
        gap = 0.0
        for i in range(g.N):
            s = g.oracle(i, M * Abar, rho=1.0)
            rs = g.ctilde(s) + float(s.a @ (M * Abar))
            cur = sum(w * (g.ctilde(p) + float(p.a @ (M * Abar))) for w, p in zip(weights[i], pools[i]))
            gap += max(0.0, cur - rs)
            if all(p.key() != s.key() for p in pools[i]) and rs < cur - tol:
                pools[i].append(s)
                weights[i].append(0.0)
                added += 1
        hist.append((g.calls, gap))
        if added == 0:
            break
    return _round_support(g, pools, weights), hist, (pools, weights)
