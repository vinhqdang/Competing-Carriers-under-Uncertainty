"""Sanity checks for the MFG memo (docs/MFG_DIRECTION.md, Problem B).

Continuous (convexified) Cournot-congestion game with Z separable zones in delivery units:
carrier i chooses x_i in X_i = {x >= 0, sum_z x_iz <= cap_i}, payoff
    sum_z x_iz (alpha_z - m_z Q_z) - c_iz x_iz,   m_z = b_z + kappa_z,  Q_z = sum_i x_iz.
Nash equilibrium   = maximiser of P_N(x) = sum <a_i, x_i> - sum_z m_z/2 (Q_z^2 + sum_i x_iz^2),  a = alpha - c.
Wardrop (mean-field, price-taking) equilibrium = maximiser of P_W(x) = sum <a_i, x_i> - sum_z m_z/2 Q_z^2.
(Both are exact potentials; Slade 1994, Beckmann et al. 1956.)

Checks:
 1. symmetric one-zone closed form Q^N = N/(N+1) Q^W;
 2. one-zone bound |Q^N - Q^W| <= s (s = largest carrier capacity), from the cost-shift argument in the memo;
 3. multi-zone, carriers coupled by a capacity budget across zones: ratio max_z |Q^N_z - Q^W_z| / s over random
    instances and N = 2..64 (is the gap O(s) with a constant that does not grow with N or Z?);
    3c. exact replicas of a fixed 2-type instance: does the ratio settle as N grows (gap of order s = 1/N)?
 4. D2 coupling with two courier types of different dwell times: the symmetric part of the coupling operator is
    indefinite, so Lasry-Lions monotonicity fails, while a per-type reweighting restores a potential iff dwell
    times are rank one across (type, zone).
Run:  python3 -I mfg/checks/finite_to_mf_gap.py
"""
from __future__ import annotations

import numpy as np


def proj_capped_simplex(v: np.ndarray, cap: np.ndarray) -> np.ndarray:
    """Row-wise Euclidean projection onto {x >= 0, sum x <= cap}."""
    out = np.maximum(v, 0.0)
    over = out.sum(axis=1) > cap
    if over.any():
        w = v[over]
        c = cap[over]
        u = -np.sort(-w, axis=1)
        css = np.cumsum(u, axis=1) - c[:, None]
        k = np.arange(1, w.shape[1] + 1)
        cond = u - css / k > 0
        r = cond.shape[1] - 1 - np.argmax(cond[:, ::-1], axis=1)
        theta = css[np.arange(len(r)), r] / (r + 1)
        out[over] = np.maximum(w - theta[:, None], 0.0)
    return out


def solve(a, m, cap, own: bool, iters=40000, tol=1e-12):
    """FISTA on -P (own=True: Nash potential; own=False: Wardrop potential). Returns x, Frank-Wolfe gap."""
    N, Z = a.shape
    L = m.max() * (N + (1 if own else 0))
    x = np.zeros((N, Z)); y = x.copy(); t = 1.0

    def grad(x):
        g = a - m * x.sum(0)
        return g - m * x if own else g

    for _ in range(iters):
        xn = proj_capped_simplex(y + grad(y) / L, cap)
        tn = (1 + np.sqrt(1 + 4 * t * t)) / 2
        y = xn + (t - 1) / tn * (xn - x)
        x, t = xn, tn
        if _ % 500 == 0:
            g = grad(x)
            best = np.where(g.max(1) > 0, cap * g.max(1), 0.0)
            gap = best.sum() - (g * x).sum()
            if gap < tol:
                break
    g = grad(x)
    gap = np.where(g.max(1) > 0, cap * g.max(1), 0.0).sum() - (g * x).sum()
    return x, gap


def check1():
    alpha, m = 3.0, 1.5
    errs = []
    for N in (1, 2, 5, 10, 50):
        a = np.full((N, 1), alpha)
        cap = np.full(N, 10.0)
        QN = solve(a, np.array([m]), cap, True)[0].sum()
        QW = solve(a, np.array([m]), cap, False)[0].sum()
        errs.append(abs(QN - N / (N + 1) * QW))
    return max(errs)


def instance(rng, N, Z, replicate=None):
    alpha = rng.uniform(2, 4, Z)
    m = rng.uniform(0.5, 2.0, Z)
    if replicate is None:
        c = rng.uniform(0, 2.5, (N, Z))
    else:  # T base types, each split into N/T identical carriers
        base = rng.uniform(0, 2.5, (replicate, Z))
        c = np.repeat(base, N // replicate, axis=0)
    c[rng.random((N, Z)) < 0.3] = 50.0  # zones a carrier does not serve
    K = rng.uniform(0.5, 1.5) * (alpha / m).sum()
    cap = np.full(N, K / N)
    return alpha[None, :] - c, m, cap


def gap_ratio(a, m, cap):
    xN, gN = solve(a, m, cap, True)
    xW, gW = solve(a, m, cap, False)
    s = cap.max()
    dQ = np.abs(xN.sum(0) - xW.sum(0))
    err = np.sqrt(2 * max(gN, 0) / m.min()) + np.sqrt(2 * max(gW, 0) / m.min())  # accuracy of the solves
    return dQ.max() / s, err / s


def main():
    rng = np.random.default_rng(0)
    print("check 1  symmetric closed form  max|Q^N - N/(N+1) Q^W| =", f"{check1():.2e}")

    worst1 = 0.0
    for _ in range(200):
        N = int(rng.integers(1, 40))
        a, m, cap = instance(rng, N, 1)
        r, e = gap_ratio(a, m, cap)
        worst1 = max(worst1, r - e)
    print(f"check 2  one zone, 200 random instances: max |Q^N-Q^W|/s = {worst1:.4f}  (bound 1)")

    print("check 3  multi-zone with cross-zone capacity budget, max over instances of max_z|dQ_z|/s")
    print("   N    Z  heterogeneous  replicated(T=2)  solver-accuracy/s")
    for Z in (3, 8):
        for N in (2, 4, 8, 16, 32, 64):
            rh, rr, acc = 0.0, 0.0, 0.0
            for _ in range(15):
                r, e = gap_ratio(*instance(rng, N, Z)); rh = max(rh, r); acc = max(acc, e)
                r, e = gap_ratio(*instance(rng, N, Z, replicate=2)); rr = max(rr, r); acc = max(acc, e)
            print(f"  {N:3d}  {Z:3d}  {rh:12.4f}  {rr:14.4f}  {acc:16.1e}")

    # exact replica family: T = 2 base types (costs and served zones fixed), each split into N/2 identical carriers
    print("check 3c exact replicas (Z=3, T=2), ratio max_z|dQ_z|/s for N = 4, 16, 64, 256 (fixed instance per row)")
    for k in range(6):
        r6 = np.random.default_rng(100 + k)
        Z, T = 3, 2
        alpha = r6.uniform(2, 4, Z); m = r6.uniform(0.5, 2, Z)
        base = r6.uniform(0, 2.5, (T, Z)); base[r6.random((T, Z)) < 0.3] = 50.0
        K = r6.uniform(0.5, 1.5) * (alpha / m).sum()
        row = [gap_ratio(alpha[None, :] - np.repeat(base, N // T, axis=0), m, np.full(N, K / N))[0]
               for N in (4, 16, 64, 256)]
        print("   instance", k, " ".join(f"{r:.3f}" for r in row))

    # adversarial search on small instances
    best = 0.0
    for _ in range(3000):
        N, Z = int(rng.integers(2, 5)), int(rng.integers(2, 4))
        a, m, cap = instance(rng, N, Z)
        cap = rng.uniform(0.2, 2.0, N)
        r, e = gap_ratio(a, m, cap)
        best = max(best, r - e)
    print(f"check 3b adversarial random search (3000 small instances, unequal caps): max ratio = {best:.4f}")

    # check 4: D2 coupling operator for two courier types with dwell times h (hours per vehicle)
    h = np.array([0.5, 2.0])
    w = 1 / h
    K = np.outer(np.ones(2), w)  # cost per vehicle-hour of type t depends on vehicle count sum_t' tau_t'/h_t'
    eig = np.linalg.eigvalsh((K + K.T) / 2)
    D = np.diag(w)
    eigw = np.linalg.eigvalsh((D @ K + (D @ K).T) / 2)
    print(f"check 4  D2 two types h={h}: eig(sym part)={np.round(eig, 3)}  -> not monotone;"
          f" after per-type weight 1/h: eig={np.round(eigw, 3)} -> PSD (weighted potential)")
    H = np.array([[0.5, 2.0], [2.0, 0.5]])  # dwell time by (type, zone): rank two
    print(f"         dwell matrix rank {np.linalg.matrix_rank(H)} across (type, zone): no single per-type weight"
          " symmetrises both zones; potential argument fails (non-monotone coupling possible)")


if __name__ == "__main__":
    main()
