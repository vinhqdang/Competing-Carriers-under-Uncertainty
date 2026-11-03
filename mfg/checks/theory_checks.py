"""Brute-force numerical checks of every theorem in mfg/theory (run: PYTHONPATH=mfg/src python3 -I mfg/checks/theory_checks.py).

Each check prints the worst violation found (a positive "slack" means the bound holds).  The instances are small
random games with linear column profits and one budget per carrier (the model of mfg/theory/model.tex); equilibria
are computed with the interior-point reference solver of mfgcc.qp (accuracy reported through the duality gap), and
pure equilibria of lumpy games by exhaustive enumeration.  Output: mfg/checks/theory_checks.out.
"""
from __future__ import annotations

import itertools
import sys

import numpy as np
import scipy.sparse as sp

from mfgcc.qp import Block, solve
from mfgcc import theory as th

RNG = np.random.default_rng(20261103)
TOL = 1e-6


def rand_game(rng, N, d, ncol=6, sep=False, identical=False, scale=1.0):
    """N carriers, d coordinates; columns = random nonnegative contribution vectors (sparse), linear profits."""
    m = rng.uniform(0.5, 2.0, d)
    blocks = []
    base = None
    for i in range(N):
        if identical and base is not None:
            blocks.append(Block(base.p.copy(), base.L.copy(), base.w.copy(), base.B, 1))
            continue
        if sep:  # zone-separable: each column touches one coordinate
            L = np.zeros((d, ncol))
            for j in range(ncol):
                L[rng.integers(d), j] = rng.uniform(0.2, 1.0)
        else:
            L = rng.uniform(0, 1, (d, ncol)) * (rng.random((d, ncol)) < 0.6)
            L[rng.integers(d, size=ncol), np.arange(ncol)] += 0.3
        p = rng.uniform(1.0, 3.0, ncol) * L.sum(0)
        w = np.ones(ncol) if sep else rng.uniform(0.5, 1.5, ncol)
        B = scale / N * rng.uniform(0.5, 1.5) * d
        blk = Block(p, sp.csr_matrix(L), w, B, 1)
        blocks.append(blk)
        base = blk
    if sep:  # separable: give every carrier its own budget per coordinate by splitting into one block per zone
        out = []
        for blk in blocks:
            L = blk.L.toarray()
            for k in range(d):
                cols = np.where(L[k] > 0)[0]
                if len(cols):
                    out.append(Block(blk.p[cols], sp.csr_matrix(L[:, cols]), blk.w[cols], blk.B / d, 1,
                                     meta=dict(owner=len(out))))
        blocks = out
    return blocks, m


def eq(blocks, m, own, **kw):
    s = solve(blocks, m, own=own, **kw)
    return s


def mnorm(x, m):
    return float(np.sqrt(x @ (m * x)))


def check_linearisation():
    """Lemma 2(c): a Nash equilibrium is a Wardrop equilibrium with own surcharges sigma_i = M a_i^N."""
    worst = 0.0
    for _ in range(40):
        N, d = int(RNG.integers(2, 6)), int(RNG.integers(2, 5))
        bl, m = rand_game(RNG, N, d)
        sN = eq(bl, m, True)
        bl2 = [Block(b.p, b.L, b.w, b.B, 1, sigma=m * a) for b, a in zip(bl, sN.a)]
        sW = eq(bl2, m, False)
        worst = max(worst, float(np.abs(sW.Q - sN.Q).max()))
    return worst


def check_sqrt_bound():
    """Theorem 4(a): ||A^N - A^W||_M <= 1/2 (sum ||a_i^W||_M^2)^(1/2), any Wardrop selection."""
    worst, ratio = np.inf, 0.0
    for _ in range(150):
        N, d = int(RNG.integers(2, 12)), int(RNG.integers(2, 6))
        bl, m = rand_game(RNG, N, d)
        sN, sW = eq(bl, m, True), eq(bl, m, False)
        lhs = mnorm(sN.Q - sW.Q, m)
        rhs = th.sqrt_bound(sW.a, m)
        acc = np.sqrt(2 * max(sN.gap, 0)) + np.sqrt(2 * max(sW.gap, 0))
        worst = min(worst, rhs - lhs + acc)
        ratio = max(ratio, lhs / rhs)
    return worst, ratio


def check_tight_family():
    rows = []
    for n in (4, 16, 64, 256, 1024, 4096):
        f = th.tight_family(n)
        exact = np.sqrt(1 / (8 * n) + (2 * n - 1) / (8 * n ** 3))
        bl, _ = th.tight_family_blocks(n)
        sN, sW = eq(bl, np.ones(2), True), eq(bl, np.ones(2), False)
        rows.append((n, f["gap"], exact, float(np.linalg.norm(sN.Q - sW.Q)), f["gap"] / f["bound"],
                     f["gap"] * np.sqrt(n), f["gap"] / f["s"]))
    fixed = [(n, th.tight_family(n, phi=0.2)["gap"] * n) for n in (4, 16, 64, 256, 1024, 4096, 16384)]
    return rows, fixed


def lumpy_pure_equilibria(plans, profits, m):
    """All pure Nash equilibria of a lumpy game: plans[i] = list of contribution vectors, profits[i] = list."""
    N = len(plans)
    out = []
    for prof in itertools.product(*[range(len(p)) for p in plans]):
        A = sum(plans[i][prof[i]] for i in range(N))
        ok = True
        for i in range(N):
            R = A - plans[i][prof[i]]
            cur = profits[i][prof[i]] - plans[i][prof[i]] @ (m * (R + plans[i][prof[i]]))
            for j in range(len(plans[i])):
                alt = profits[i][j] - plans[i][j] @ (m * (R + plans[i][j]))
                if alt > cur + 1e-12:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            out.append((prof, A))
    return out


def lumpy_wardrop(plans, profits, m, d):
    blocks = [Block(np.array(pr, float), sp.csr_matrix(np.column_stack(pl)), np.ones(len(pl)), 1.0, 1)
              for pl, pr in zip(plans, profits)]
    return solve(blocks, m, own=False)


def check_zone_separable():
    """Theorem 6: one coordinate.  Splittable: 0 <= Q^W - Q^N <= max_i q_i^N.  Lumpy pure: 0 <= Q^W - Q^N <= max lot."""
    worst_split, worst_lumpy, max_ratio, n_eq = np.inf, np.inf, 0.0, 0
    for _ in range(200):
        N = int(RNG.integers(1, 30))
        m = np.array([RNG.uniform(0.3, 2.0)])
        blocks = []
        for i in range(N):  # concave piecewise-linear profit on [0, cap]: columns = segments of decreasing slope
            k = int(RNG.integers(1, 4))
            slopes = np.sort(RNG.uniform(0.0, 3.0, k))[::-1]
            seg = RNG.uniform(0.05, 1.0, k) / np.sqrt(N)
            # deliver q_j units of segment j: column j contributes 1 per unit budget, profit slope_j per unit
            for j in range(k):
                blocks.append(Block(np.array([slopes[j]]), sp.csr_matrix(np.ones((1, 1))), np.array([1.0]), seg[j],
                                    1, meta=dict(owner=i)))
        merged = []
        owners = sorted(set(b.meta["owner"] for b in blocks))
        for o in owners:
            segs = [b for b in blocks if b.meta["owner"] == o]
            merged.append(segs)
        # exact Wardrop (bisection on the aggregate) and Nash (best-response iteration) with segment caps
        QW = _onezone_wardrop(merged, m[0])
        QN, qN = _onezone_nash(merged, m[0])
        s = max(qN) if len(qN) else 0.0
        worst_split = min(worst_split, min(QW - QN, s - (QW - QN)) + 1e-9)
        if s > 0:
            max_ratio = max(max_ratio, (QW - QN) / s)
    # lumpy pure equilibria by enumeration (one zone)
    for _ in range(300):
        N = int(RNG.integers(1, 6))
        m = np.array([RNG.uniform(0.3, 2.0)])
        plans, profits = [], []
        for i in range(N):
            k = int(RNG.integers(1, 4))
            q = np.concatenate([[0.0], np.sort(RNG.uniform(0.1, 1.0, k))])
            pr = np.concatenate([[0.0], RNG.uniform(0.0, 3.0, k) * q[1:]])
            plans.append([np.array([x]) for x in q])
            profits.append(list(pr))
        eqs = lumpy_pure_equilibria(plans, profits, m)
        sW = lumpy_wardrop(plans, profits, m, 1)
        smax = max(max(x[0] for x in pl) for pl in plans)
        for _, A in eqs:
            n_eq += 1
            diff = sW.Q[0] - A[0]
            worst_lumpy = min(worst_lumpy, min(diff, smax - diff) + 1e-7)
    return worst_split, max_ratio, worst_lumpy, n_eq


def _onezone_wardrop(carriers, m):
    """Wardrop aggregate with concave piecewise-linear profits: segments (slope, cap) supplied iff slope > m Q."""
    segs = [(b.p[0], b.B) for c in carriers for b in c]
    lo, hi = 0.0, sum(c for _, c in segs) + 1.0
    for _ in range(200):
        Q = 0.5 * (lo + hi)
        sup = sum(c if sl > m * Q else 0.0 for sl, c in segs)
        if sup > Q:
            lo = Q
        else:
            hi = Q
    return 0.5 * (lo + hi)


def _onezone_nash(carriers, m):
    """Splittable Nash with concave piecewise-linear profits: carrier best response to Q_-i maximises
    pi(q) - m q (Q_-i + q); iterate best responses (a potential game with a strictly concave potential in q)."""
    q = np.zeros(len(carriers))
    for _ in range(3000):
        old = q.copy()
        for i, c in enumerate(carriers):
            R = q.sum() - q[i]
            segs = sorted([(b.p[0], b.B) for b in c], key=lambda x: -x[0])
            # maximise concave f(q) = pi(q) - m q (R + q): marginal slope_j - m R - 2 m q
            x = 0.0
            for sl, cap in segs:
                # within this segment, optimal increment solves sl - m R - 2 m (x + t) = 0
                t = (sl - m * R) / (2 * m) - x
                if t <= 0:
                    break
                x += min(t, cap)
                if t < cap:
                    break
            q[i] = x
        if np.abs(q - old).max() < 1e-13:
            break
    return q.sum(), list(q)


def check_common_surcharge():
    """Proposition 7: identical carriers, any coupling: ||A^N - A^W||_M <= ||a^N||_M."""
    worst, ratio = np.inf, 0.0
    for _ in range(60):
        N, d = int(RNG.integers(2, 10)), int(RNG.integers(2, 6))
        bl, m = rand_game(RNG, N, d, identical=True)
        sN, sW = eq(bl, m, True), eq(bl, m, False)
        lhs = mnorm(sN.Q - sW.Q, m)
        rhs = mnorm(sN.a[0], m)
        worst = min(worst, rhs - lhs + 1e-6)
        ratio = max(ratio, lhs / rhs)
    return worst, ratio


def check_replica_affine():
    """Proposition 9: affine interior replicas: ||A^N - A^W||_M <= ||D_n T^W||_{G^{-1}} (and the 1/2-sqrt bound)."""
    worst = np.inf
    for _ in range(100):
        d, Th = int(RNG.integers(2, 5)), int(RNG.integers(2, 5))
        n = int(RNG.integers(1, 200))
        Ldir = RNG.uniform(0, 1, (d, Th))
        m = RNG.uniform(0.5, 2, d)
        Mh = np.diag(np.sqrt(m))
        G = (Mh @ Ldir).T @ (Mh @ Ldir) + 1e-9 * np.eye(Th)
        TW = RNG.uniform(0.5, 2.0, Th)
        alpha = G @ TW
        D = np.diag(np.diag(G)) / n  # each type is one-dimensional: L_theta^T M L_theta / n
        TN = np.linalg.solve(G + D, alpha)
        if (TN < 0).any():
            continue
        gap = mnorm(Ldir @ (TN - TW), m)
        b = th.replica_affine_bound(G, D @ TW)
        worst = min(worst, b - gap)
    return worst


def check_lumpy_multizone():
    """Theorem 4(b): pure Nash of a lumpy game: ||A(p) - A^W||_M^2 <= sum_i E_{x_i^W} ||a_i||_M^2."""
    worst, cnt = np.inf, 0
    for _ in range(200):
        N, d = int(RNG.integers(2, 5)), int(RNG.integers(2, 4))
        m = RNG.uniform(0.5, 2.0, d)
        plans, profits = [], []
        for i in range(N):
            k = int(RNG.integers(2, 4))
            P = [np.zeros(d)] + [RNG.uniform(0, 1, d) * (RNG.random(d) < 0.7) for _ in range(k)]
            plans.append(P)
            profits.append([0.0] + [RNG.uniform(0.5, 3.0) * p.sum() for p in P[1:]])
        eqs = lumpy_pure_equilibria(plans, profits, m)
        sW = lumpy_wardrop(plans, profits, m, d)
        Ea2 = sum(float(yb @ np.array([pl @ (m * pl) for pl in P])) for yb, P in zip(sW.y, plans))
        for _, A in eqs:
            cnt += 1
            worst = min(worst, Ea2 - mnorm(A - sW.Q, m) ** 2 + 1e-6)
    return worst, cnt


def check_leader():
    """Proposition 11 / Theorems 12-13: ARP contraction, fixed-point characterisation, toll convergence, welfare bound."""
    worst_c, worst_fp, worst_toll, worst_w = np.inf, 0.0, np.inf, np.inf
    for _ in range(40):
        N, d = int(RNG.integers(2, 8)), int(RNG.integers(2, 5))
        bl, _ = rand_game(RNG, N, d)
        b = RNG.uniform(0.2, 1.0, d)
        kap = RNG.uniform(0.1, 1.5, d)
        m = b + kap
        rho = float((kap / m).max())
        # contraction of T_X(u) = kappa Q^X(u) in the kappa^{-1} norm
        for own in (True, False):
            u1, u2 = RNG.uniform(0, 2, d), RNG.uniform(0, 2, d)
            Q1, Q2 = solve(bl, m, own=own, u=u1).Q, solve(bl, m, own=own, u=u2).Q
            lhs = np.sqrt(np.sum((kap * (Q1 - Q2)) ** 2 / kap))
            rhs = rho * np.sqrt(np.sum((u1 - u2) ** 2 / kap))
            worst_c = min(worst_c, rhs - lhs + 1e-6)
        # fixed points by one solve with mc = m + kappa, then verify u = kappa Q(u)
        uN = kap * solve(bl, m, mc=m + kap, own=True).Q
        uW = kap * solve(bl, m, mc=m + kap, own=False).Q
        worst_fp = max(worst_fp, float(np.abs(kap * solve(bl, m, own=True, u=uN).Q - uN).max()),
                       float(np.abs(kap * solve(bl, m, own=False, u=uW).Q - uW).max()))
        eps = np.sqrt(np.sum((kap * (solve(bl, m, own=True, u=uN).Q - solve(bl, m, own=False, u=uN).Q)) ** 2 / kap))
        dist = np.sqrt(np.sum((uN - uW) ** 2 / kap))
        worst_toll = min(worst_toll, eps / (1 - rho) - dist + 1e-6)
        # welfare of the observation-only fixed point: SW* - SW(y^N(u_N*)) <= 1/2 sum ||a_i*||_m^2
        so = solve(bl, m, mc=m + kap, own=False)
        yN = solve(bl, m, own=True, u=uN)

        def SW(sol):
            return sum(float(B.p @ yb) for B, yb in zip(bl, sol.y)) - 0.5 * float(sol.Q @ ((m + kap) * sol.Q))
        loss = SW(so) - SW(yN)
        bound = 0.5 * sum(float(a @ (m * a)) for a in so.a)
        worst_w = min(worst_w, bound - loss + 1e-6)
    return worst_c, worst_fp, worst_toll, worst_w


def check_gamma():
    """Proposition 15: Gamma-maximin surcharge delta m w: ||Q^Gamma - Q^W||_m <= delta ||w||_m, and the ARP fixed
    point under Gamma-maximin carriers loses at most 1/2 delta^2 ||m w||^2_{(m+kappa)^{-1}} of welfare (mean field)."""
    worst_p, worst_w = np.inf, np.inf
    for _ in range(40):
        N, d = int(RNG.integers(2, 8)), int(RNG.integers(2, 5))
        bl, _ = rand_game(RNG, N, d)
        b, kap = RNG.uniform(0.2, 1.0, d), RNG.uniform(0.1, 1.5, d)
        m = b + kap
        w = RNG.uniform(0.2, 1.0, d)
        delta = RNG.uniform(0, 1.0)
        QW = solve(bl, m, own=False).Q
        QG = solve(bl, m, own=False, u=delta * m * w).Q
        worst_p = min(worst_p, delta * mnorm(w, m) - mnorm(QG - QW, m) + 1e-6)
        # fixed point u = kappa Q^W(u + delta m w): v = u + delta m w solves v = kappa Q(v) + delta m w,
        # i.e. maximise Phi with mc = m + kappa and linear term -delta m w (then v = kappa Q + delta m w)
        sol = solve(bl, m, mc=m + kap, own=False, u=delta * m * w)
        v = kap * sol.Q + delta * m * w
        chk = solve(bl, m, own=False, u=v)
        so = solve(bl, m, mc=m + kap, own=False)

        def SW(s):
            return sum(float(B.p @ yb) for B, yb in zip(bl, s.y)) - 0.5 * float(s.Q @ ((m + kap) * s.Q))
        loss = SW(so) - SW(chk)
        worst_w = min(worst_w, 0.5 * delta ** 2 * np.sum((m * w) ** 2 / (m + kap)) - loss + 1e-6)
    return worst_p, worst_w


def check_d2():
    """Proposition 18: rank-one dwell times <=> per-type weights symmetrise the D2 coupling; two types with different dwell
    times give an indefinite symmetric part with determinant -(1/h1 - 1/h2)^2 / 4 (times g^2)."""
    worst_det = 0.0
    for _ in range(200):
        h1, h2, g = RNG.uniform(0.2, 3, 3)
        K = g * np.array([[1 / h1, 1 / h2], [1 / h1, 1 / h2]])
        S = (K + K.T) / 2
        worst_det = max(worst_det, abs(np.linalg.det(S) + g * g * (1 / h1 - 1 / h2) ** 2 / 4))
    ok_rank1, ok_rank2 = True, True
    for _ in range(200):
        Th, Z = 3, 4
        eta, zeta = RNG.uniform(0.3, 2, Th), RNG.uniform(0.3, 2, Z)
        H = np.outer(eta, zeta)
        w = 1 / eta
        for z in range(Z):
            Kz = np.array([[w[a] / H[b, z] for b in range(Th)] for a in range(Th)])
            ok_rank1 &= np.allclose(Kz, Kz.T)
            ok_rank1 &= np.linalg.eigvalsh((Kz + Kz.T) / 2).min() > -1e-9
        H2 = RNG.uniform(0.3, 2, (Th, Z))
        if np.linalg.matrix_rank(np.log(H2) - np.log(H2).mean(1, keepdims=True) - np.log(H2).mean(0) +
                                 np.log(H2).mean(), tol=1e-6) > 0:
            # no positive weights symmetrise all zones: w_a / h_bz = w_b / h_az needs h_az / h_bz independent of z
            ratios = H2[0] / H2[1]
            ok_rank2 &= ratios.std() > 1e-6
    # rank-one D2 nonatomic game: potential maximiser solves the equilibrium conditions (two types, two zones)
    eta, zeta, g = np.array([0.5, 2.0]), np.array([1.0, 1.5]), np.array([1.0, 0.7])
    val = np.array([[3.0, 2.0], [2.5, 3.5]])  # linear value per vehicle-hour of type a in zone z, budget 1 per type
    # potential: sum_a (1/eta_a) <val_a, tau_a> - 1/2 sum_z g_z zeta_z X_z^2, X_z = sum_a tau_az/(eta_a zeta_z)
    best, tau_best = -np.inf, None
    grid = np.linspace(0, 1, 401)
    for t0 in grid:
        for t1 in grid:
            tau = np.array([[t0, 1 - t0], [t1, 1 - t1]])
            X = (tau / eta[:, None] / zeta[None]).sum(0)
            P = ((val * tau).sum(1) / eta).sum() - 0.5 * (g * zeta * X * X).sum()
            if P > best:
                best, tau_best = P, tau
    X = (tau_best / eta[:, None] / zeta[None]).sum(0)
    # equilibrium check: each type uses only zones maximising val_az - g_z X_z (up to grid resolution)
    eqerr = 0.0
    for a in range(2):
        net = val[a] - g * X
        used = tau_best[a] > 1e-9
        eqerr = max(eqerr, float(net.max() - net[used].min()))
    return worst_det, bool(ok_rank1), bool(ok_rank2), eqerr


def check_time_of_day_corner():
    """Proposition 17: with a charge U paid when arriving before t=1, the worst case over all laws on [0, 2] is a
    travel time just below 1 (cost close to 1 + U), not the slowest law T = 2 (cost 2), when U > 2."""
    U = 3.0
    xs = np.linspace(0, 2, 2001)
    cost = xs + U * (xs < 1)
    return float(cost.max()), float(xs[cost.argmax()])


def check_toll_separable_and_welfare_any_charge():
    """Theorem 12(b): zone-separable carriers: 0 <= u_W* - u_N* <= kappa * max_i q~_i^N per coordinate.
    Theorem 13(a): SW* - SW(y^W(v)) <= <v - kappa Q*, Q* - Q> - 1/2 ||Q - Q*||_b^2 for any charge v.
    Theorem 13(c): |SW(y^N(u)) - SW(y^W(u))| bound."""
    worst_t, worst_a, worst_c = np.inf, np.inf, np.inf
    for _ in range(60):
        N, d = int(RNG.integers(1, 8)), int(RNG.integers(1, 4))
        bl, _ = rand_game(RNG, N, d, sep=True)
        b, kap = RNG.uniform(0.2, 1.0, d), RNG.uniform(0.1, 1.5, d)
        m = b + kap
        tN = solve(bl, m, mc=m + kap, own=True)
        tW = solve(bl, m, mc=m + kap, own=False)
        diff = kap * tW.Q - kap * tN.Q
        # the separable blocks of rand_game(sep=True) are one block per (carrier, coordinate)
        qmax = np.max(np.array([a for a in tN.a]), axis=0)
        worst_t = min(worst_t, float(np.min(diff)) + 1e-7, float(np.min(kap * qmax - diff)) + 1e-7)

        def SW(sol):
            return sum(float(B.p @ yb) for B, yb in zip(bl, sol.y)) - 0.5 * float(sol.Q @ ((m + kap) * sol.Q))
        so = solve(bl, m, mc=m + kap, own=False)
        v = RNG.uniform(0, 2, d)
        yv = solve(bl, m, own=False, u=v)
        dQ = yv.Q - so.Q
        rhs = float((v - kap * so.Q) @ (so.Q - yv.Q)) - 0.5 * float(dQ @ (b * dQ))
        worst_a = min(worst_a, rhs - (SW(so) - SW(yv)) + 1e-6)
        yN = solve(bl, m, own=True, u=v)
        mid = 0.5 * (yN.Q + yv.Q)
        bnd = 0.5 * sum(float(a @ (m * a)) for a in yv.a) + \
            np.sqrt(np.sum(kap * (yN.Q - yv.Q) ** 2)) * np.sqrt(np.sum(kap * (mid - v / kap) ** 2))
        worst_c = min(worst_c, bnd - abs(SW(yN) - SW(yv)) + 1e-6)
    return worst_t, worst_a, worst_c


def main():
    out = []

    def p(*a):
        s = " ".join(str(x) for x in a)
        print(s)
        out.append(s)
    p("Theory checks for mfg/theory (min slack >= 0 means the bound holds on every instance)")
    p(f"Lemma 2(c) linearisation (Nash = Wardrop with own surcharge): max |dQ| = {check_linearisation():.2e}")
    w, r = check_sqrt_bound()
    p(f"Thm 4(a) sqrt bound, 150 random multi-zone games: min slack {w:.2e}, max ratio gap/bound {r:.3f}")
    rows, fixed = check_tight_family()
    p("Prop 5   tightness family (1 - cos phi = 1/n):  n  gap(closed)  gap(exact formula)  gap(solver)  gap/bound"
      "  gap*sqrt(n)  gap/s")
    for r_ in rows:
        p("         " + "  ".join(f"{x:.6g}" for x in r_))
    p("         fixed phi = 0.2: n * gap = " + ", ".join(f"{n}:{g:.4f}" for n, g in fixed) +
      f"  (limit 1/sin(phi) = {1 / np.sin(0.2):.4f})")
    ws, mr, wl, ne = check_zone_separable()
    p(f"Thm 6    one zone, splittable (200 games): min slack {ws:.2e}, max (Q^W-Q^N)/max_i q_i^N = {mr:.4f};"
      f" lumpy pure ({ne} equilibria of 300 games): min slack {wl:.2e}")
    w, r = check_common_surcharge()
    p(f"Prop 7   identical carriers: min slack {w:.2e}, max ratio {r:.3f}")
    p(f"Prop 9   affine replica bound: min slack {check_replica_affine():.2e}")
    w, c = check_lumpy_multizone()
    p(f"Thm 4(b) lumpy pure equilibria, multi-zone ({c} equilibria): min slack {w:.2e}")
    wc, wf, wt, ww = check_leader()
    p(f"Prop 11  ARP contraction (N and W): min slack {wc:.2e};  fixed-point residual {wf:.2e}")
    p(f"Thm 12   toll gap <= eps/(1-rho): min slack {wt:.2e};  Thm 13(b) welfare bound: min slack {ww:.2e}")
    w1, w2, w3 = check_toll_separable_and_welfare_any_charge()
    p(f"Thm 12(b) separable charge gap: min slack {w1:.2e}; Thm 13(a) any charge: min slack {w2:.2e};"
      f" Thm 13(c): min slack {w3:.2e}")
    wp, wg = check_gamma()
    p(f"Prop 15  Gamma-maximin prox bound: min slack {wp:.2e}; welfare of ARP under Gamma: min slack {wg:.2e}")
    det, r1, r2, ee = check_d2()
    p(f"Prop 18  D2: |det(sym part) + g^2 (1/h1-1/h2)^2/4| max {det:.2e}; rank one symmetrisable & PSD: {r1};"
      f" rank two not symmetrisable: {r2}; rank-one potential maximiser equilibrium error (grid) {ee:.2e}")
    mx, arg = check_time_of_day_corner()
    p(f"Prop 17  time-of-day: worst-case cost {mx:.3f} attained at travel time {arg:.3f} (the slowest law, T = 2, costs only 2)")
    return out


if __name__ == "__main__":
    lines = main()
    if len(sys.argv) > 1:
        open(sys.argv[1], "w").write("\n".join(lines) + "\n")
