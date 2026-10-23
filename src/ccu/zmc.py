"""Zone-Market Clearing (ZMC) and the baselines (best-response dynamics, Frank-Wolfe, column generation).

Port of theory/new_algorithm_A/{ssd,baselines,prototype}.py to a generic game object `g` with the interface
    g.N, g.d, g.M (np.ndarray, d), g.calls (oracle-call counter),
    g.oracle(i, lam, rho=1.0)  -> Plan with .a and .key()   (argmin ctilde_i + <lam, a_i>, rho = 1;  rho = 0 is a
                                   best response to the anchor lam = M A_-i),
    g.br(i, A_minus), g.J(i, plan, A_minus), g.ctilde(plan), g.potential(profile),
    g.full_a(i) (upper bound of every contribution), g.empty_plan(i), g.regrets(profile).
The algorithmic content (bracketed secant on the clearing residual, restricted master, derandomised rounding,
best-response polish) is unchanged from the prototype; only the game interface is generalised.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import isotonic_regression

# ------------------------------------------------------------------------------------------------- ZMC


def dual_value(g, lam, plans):
    """G(lam) = sum_i [ctilde_i + <lam, a_i>] - 1/2 lam' M^-1 lam  (exact when the plans are oracle answers)."""
    M = g.M
    v = sum(g.ctilde(p) + float(lam @ p.a) for p in plans)
    return v - 0.5 * float(lam @ (lam / M))


def _secant(x, y, m, lo, hi):
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


def zmc(g, rounds=8, hist=None, mode="secant", lam0=None):
    """Bracketed secant price search.  Returns (best=(G, lam, plans), pools, trace).

    trace: list of dicts per round with the maximal relative bracket width and the clearing error norm.
    lam0 warm-starts the first query (brackets are re-initialised, so the guarantee is unchanged).
    """
    M = g.M
    d = g.d
    Amax = np.zeros(d)
    for i in range(g.N):
        Amax += g.full_a(i)
    act = Amax > 0
    lo = np.zeros(d)
    hi = M * Amax
    lam = 0.5 * (lo + hi) if lam0 is None else np.clip(lam0, lo, hi)
    X, Y = [], []
    best = (-np.inf, None, None)
    pools = [dict() for _ in range(g.N)]
    trace = []
    for t in range(rounds):
        plans = [g.oracle(i, lam, rho=1.0) for i in range(g.N)]
        for i, p in enumerate(plans):
            pools[i][p.key()] = p
        A = sum(p.a for p in plans)
        G = dual_value(g, lam, plans)
        lbs = [getattr(p, "value_lb", -np.inf) for p in plans]
        G_lb = (float(sum(lbs)) - 0.5 * float(lam @ (lam / M))) if np.all(np.isfinite(lbs)) else -np.inf
        if G > best[0]:
            best = (G, lam.copy(), plans)
        s = A - lam / M
        e = lam / M - A
        lo = np.where(s > 0, np.maximum(lo, lam), lo)
        hi = np.where(s < 0, np.minimum(hi, lam), hi)
        zero = s == 0
        lo = np.where(zero, lam, lo)
        hi = np.where(zero, lam, hi)
        wid = ((hi - lo) / np.where(act, M * Amax, 1.0))[act] if act.any() else np.zeros(1)
        trace.append(dict(round=t + 1, calls=g.calls, G=G, G_lb=G_lb, err2=float(e @ (M * e)),
                          phi=float(g.potential(plans)), width_max=float(wid.max()), width_med=float(np.median(wid)),
                          n_inverted=int((wid < -1e-12).sum()), n_act=int(act.sum())))
        if hist is not None:
            hist.append((g.calls, G, lam.copy(), plans))
        X.append(lam.copy())
        Y.append(A)
        if mode == "bisect" or (mode == "secant" and t % 2 == 1):
            lam = 0.5 * (lo + hi)
            continue
        Xa, Ya = np.array(X), np.array(Y)
        new = np.empty(d)
        for k in range(d):
            if not act[k]:
                new[k] = 0.0
            else:
                new[k] = _secant(Xa[:, k], Ya[:, k], M[k], lo[k], hi[k])
        lam = new
    return best, pools, trace


# ------------------------------------------------------------------------------------------------- baselines


def zero_profile(g):
    return [g.empty_plan(i) for i in range(g.N)]


def br_dynamics(g, init=None, max_rounds=60, tol=1e-9, trace=None):
    """Gauss-Seidel best responses until a full pass produces no strict improvement."""
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


def _round_support(g, pools, weights):
    """Derandomised rounding (conditional expectations on the potential, main.tex eq. (8.1))."""
    M = g.M
    N = g.N
    mean = [sum(w * p.a for w, p in zip(weights[i], pools[i])) for i in range(N)]
    var = [sum(w * float((p.a - mean[i]) @ (M * (p.a - mean[i]))) for w, p in zip(weights[i], pools[i]))
           for i in range(N)]
    lin = [sum(w * g.ctilde(p) for w, p in zip(weights[i], pools[i])) for i in range(N)]
    chosen = [None] * N
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


def _restricted_master(g, pools, weights, iters=400):
    """min of the convexified potential over the product of simplices of the pools (pairwise FW, no oracle)."""
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


def relaxed_value(g, pools, weights):
    M = g.M
    A = sum(sum(w * p.a for w, p in zip(weights[i], pools[i])) for i in range(g.N))
    return sum(sum(w * g.ctilde(p) for w, p in zip(weights[i], pools[i])) for i in range(g.N)) + 0.5 * A @ (M * A)


def round_pools(g, P, iters=3000):
    """Oracle-free: restricted master over the collected plans, then derandomised rounding."""
    W = [[1.0 if j == 0 else 0.0 for j in range(len(P[i]))] for i in range(g.N)]
    W = _restricted_master(g, P, W, iters=iters)
    return _round_support(g, P, W), W


def frank_wolfe(g, iters=50, init=None):
    """FW with exact line search on the convexified potential; returns the rounded profile and the pools."""
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
        gap = float(lin.sum() - ls.sum() + (Abar - As) @ (M * Abar))
        hist.append((g.calls, gap))
        dA = As - Abar
        den = float(dA @ (M * dA))
        gam = 1.0 if den <= 0 else min(1.0, max(0.0, gap / den))
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


def column_generation(g, max_iter=50, tol=1e-7, init=None):
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
    weights = _restricted_master(g, pools, weights, iters=3000)
    return _round_support(g, pools, weights), hist, (pools, weights)


# ------------------------------------------------------------------------------------------------- drivers


def run_zmc(g, rounds=8, mode="secant", lam0=None, polish=True):
    """ZMC + oracle-free rounding + best-response polish.  Returns a dict."""
    c0 = g.calls
    best, pools, trace = zmc(g, rounds=rounds, mode=mode, lam0=lam0)
    P = [list(pools[i].values()) for i in range(g.N)]
    rounded, W = round_pools(g, P)
    cands = {"price": best[2], "round": rounded}
    start_name = min(cands, key=lambda k: g.potential(cands[k]))
    start = cands[start_name]
    calls_search = g.calls - c0
    if polish:
        prof, ok = br_dynamics(g, init=start)
    else:
        prof, ok = start, False
    return dict(profile=prof, calls=g.calls - c0, calls_search=calls_search, converged=ok, best=best, trace=trace,
                pools=P, start=start_name, phi_start=g.potential(start), lam=best[1],
                phi_relaxed=relaxed_value(g, P, W))


def run_fw(g, iters=8, polish=True):
    c0 = g.calls
    pf, hist, (P, W) = frank_wolfe(g, iters=iters)
    pr, _ = round_pools(g, P)
    start = min([pf, pr], key=g.potential)
    prof, ok = br_dynamics(g, init=start) if polish else (start, False)
    return dict(profile=prof, calls=g.calls - c0, converged=ok, hist=hist)


def run_cg(g, iters=8, polish=True):
    c0 = g.calls
    pc, hist, (P, W) = column_generation(g, max_iter=iters)
    prof, ok = br_dynamics(g, init=pc) if polish else (pc, False)
    return dict(profile=prof, calls=g.calls - c0, converged=ok, hist=hist, pools=P, weights=W)


def run_br(g, init=None):
    c0 = g.calls
    prof, ok = br_dynamics(g, init=init)
    return dict(profile=prof, calls=g.calls - c0, converged=ok)
