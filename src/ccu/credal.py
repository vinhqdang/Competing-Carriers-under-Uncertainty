"""Credal-width quantities of theory/main.tex evaluated on integrated games (city games, tiny games, explicit games).

Conventions (main.tex, Assumption 2.2 and Section 3).  Costs instead of profits: carrier i at belief m (mean of the rival
aggregate) pays  J_i(p; m) = c_i(p) + <phi_i(p), M m>  with phi_i = a_i under D1 and phi_i != a_i under D2.  An oracle
`g.oracle(i, lam, rho=0.0)` returns argmin_p c_i(p) + <phi_i(p), lam> (so lam = M m is a best response to the belief m).
The credal box around a pure profile p is  K^delta = {m >= 0: |m_k - A_{-i,k}(p)| <= delta w_k}  (traffic is inside the
p-box of the route cost, so the traffic box is degenerate).

Thresholds of a pure profile p (all are monotone in delta, Lemma 3.5, so they are the smallest admissible widths):
  E   exact LP (Thm 8.5(a)) with Kelley cuts supplied by the oracle;
  M   (maximal) smallest delta with  max_{p'} [J(p;A) - J(p';A) - V(p',delta)] <= 0,  V = sum_k M_k [D+_k min(delta w_k,A_k) + D-_k delta w_k],
      D = phi(p) - phi(p');  the minimisation over p' is one oracle call with shifted prices (all-or-nothing lots make V linear in
      the service indicators);  bisection on delta;
  ID  smallest delta with  min_{m in K} J(p;m) <= min_{p'} max_{m in K} J(p';m)  (oracle at the upper corner);  bisection;
  Gamma  regret  max_m J(p;m) - min_{p'} max_m J(p';m)  at a given delta (Lemma 3.6: best response in the surcharge game).
Anchored radius (Thm 6.1): delta_hat(p) = max_i ||A_{-i}(p) - Abar*_{-i}||_{w,inf} for a relaxed equilibrium x*, with the
three-term bound and the N-uniform bound.
"""
from __future__ import annotations

import itertools
import math
import time
from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog

# ---------------------------------------------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------------------------------------------


def phi_of(p):
    return getattr(p, "phi", p.a)


def full_phi(g, i):
    f = getattr(g, "full_phi", None)
    return np.asarray(f(i) if f is not None else g.full_a(i), float)


def cost_at(g, p, m):
    """J(p; m) = c(p) + <phi(p), M m>."""
    return float(p.c + phi_of(p) @ (g.M * m))


def agg(prof):
    return sum(p.a for p in prof)


def rival_aggregate(prof, i):
    return agg(prof) - prof[i].a


def best_response(g, i, m, fresh=False):
    return g.oracle(i, g.M * np.asarray(m, float), rho=0.0, count=False, fresh=fresh)


def plan_key(p):
    # routes alone do not identify plans built without routes (enumerated tiny games), so the contribution is included
    return (p.key(), np.round(p.a, 9).tobytes(), np.round(phi_of(p), 9).tobytes())


def profile_key(prof):
    return tuple(plan_key(p) for p in prof)


# ---------------------------------------------------------------------------------------------------------------
# weights
# ---------------------------------------------------------------------------------------------------------------


def make_weights(g, prof, mode: str = "type_median") -> np.ndarray:
    """Belief-width weights w_k (verification_plan.md, Part B: w is the city median of the rival aggregate).

    type_median : one constant per coordinate type (deliveries Q, second block X): median over (carrier, own zone) pairs of the
                  realised rival aggregate at `prof`, positive entries only (fallback: mean full capacity of the type);
    coord_cap   : w_k = mean over carriers of the rival *capacity* sum_{j != i} full_a_jk (coordinate specific).
    """
    Z, N = g.Z, g.N
    full = np.array([g.full_a(i) for i in range(N)])
    if mode == "coord_cap":
        w = (full.sum(0)[None, :] - full).mean(0)
        fb = np.array([w[:Z][w[:Z] > 0].mean() if (w[:Z] > 0).any() else 1.0, w[Z:][w[Z:] > 0].mean() if (w[Z:] > 0).any() else 1.0])
        w = np.where(w > 0, w, np.concatenate([np.full(Z, fb[0]), np.full(Z, fb[1])]))
        return w
    A = agg(prof)
    vals = [[], []]
    for i in range(N):
        Am = A - prof[i].a
        for z in g.carriers[i].zones:
            if Am[z] > 0:
                vals[0].append(Am[z])
            if Am[Z + z] > 0:
                vals[1].append(Am[Z + z])
    out = []
    for t in range(2):
        if vals[t]:
            out.append(float(np.median(vals[t])))
        else:
            f = full[:, t * Z:(t + 1) * Z]
            out.append(float(f[f > 0].mean()) if (f > 0).any() else 1.0)
    return np.concatenate([np.full(Z, out[0]), np.full(Z, out[1])])


# ---------------------------------------------------------------------------------------------------------------
# thresholds
# ---------------------------------------------------------------------------------------------------------------


def e_threshold(g, i, prof, w, cuts=(), tol=1e-7, max_iter=400, fresh_final=False):
    """Exact E-admissibility threshold A_i^E(p) (eq. EthrLP) by Kelley cutting planes.  Returns (delta, info)."""
    p = prof[i]
    A = rival_aggregate(prof, i)
    K = np.flatnonzero(full_phi(g, i) > 0)
    nK = len(K)
    M = np.asarray(g.M, float)
    wk = np.asarray(w, float)[K]
    phi_p = phi_of(p)
    # box rows:  m_k - w_k delta <= A_k ;  -m_k - w_k delta <= -A_k
    rows, rhs = [], []
    for j, k in enumerate(K):
        r = np.zeros(nK + 1)
        r[j] = 1.0
        r[-1] = -wk[j]
        rows.append(r)
        rhs.append(A[k])
        r = np.zeros(nK + 1)
        r[j] = -1.0
        r[-1] = -wk[j]
        rows.append(r)
        rhs.append(-A[k])
    seen = {plan_key(p)}
    ncut = 0

    def add_cut(q):
        nonlocal ncut
        r = np.zeros(nK + 1)
        r[:nK] = ((phi_p - phi_of(q)) * M)[K]
        rows.append(r)
        rhs.append(q.c - p.c)
        ncut += 1

    for q in cuts:
        if plan_key(q) not in seen:
            seen.add(plan_key(q))
            add_cut(q)
    c = np.zeros(nK + 1)
    c[-1] = 1.0
    delta = np.inf
    iters = 0
    for iters in range(1, max_iter + 1):
        res = linprog(c, A_ub=np.array(rows), b_ub=np.array(rhs), bounds=[(0, None)] * (nK + 1), method="highs")
        if res.status != 0:
            return float("inf"), dict(cuts=ncut, iters=iters, status="infeasible")
        delta = float(res.x[-1])
        m = A.copy()
        m[K] = res.x[:nK]
        q = best_response(g, i, m)
        gain = cost_at(g, p, m) - cost_at(g, q, m)
        if gain <= tol * (1.0 + abs(cost_at(g, p, m))):
            if fresh_final:
                q2 = best_response(g, i, m, fresh=True)
                if cost_at(g, p, m) - cost_at(g, q2, m) > tol * (1.0 + abs(cost_at(g, p, m))):
                    q = q2
                else:
                    return delta, dict(cuts=ncut, iters=iters, status="ok", fresh_checked=True)
            else:
                return delta, dict(cuts=ncut, iters=iters, status="ok")
        if plan_key(q) in seen:
            return delta, dict(cuts=ncut, iters=iters, status="stalled")
        seen.add(plan_key(q))
        add_cut(q)
    return delta, dict(cuts=ncut, iters=iters, status="max_iter")


def _V(g, p, q, A, w, delta):
    D = phi_of(p) - phi_of(q)
    M = np.asarray(g.M, float)
    return float(np.sum(M * (np.maximum(D, 0.0) * np.minimum(delta * w, A) + np.maximum(-D, 0.0) * delta * w)))


def _min_M(g, i, p, A, w, delta, fresh=False):
    """min over p' of J(p';A) + V(p', delta)   (>= J(p;A) iff p is maximal)."""
    plans = g.plans_of(i) if hasattr(g, "plans_of") else None
    if plans is not None:
        return min(cost_at(g, q, A) + _V(g, p, q, A, w, delta) for q in plans)
    M = np.asarray(g.M, float)
    f = full_phi(g, i)
    phi_p = phi_of(p)
    s = (f > 0) & (phi_p > 0.5 * f)
    beta = np.where(f > 0, np.where(s, -M * np.minimum(delta * w, A), M * delta * w), 0.0)
    q = g.oracle(i, M * A + beta, rho=0.0, count=False, fresh=fresh)
    return cost_at(g, q, A) + _V(g, p, q, A, w, delta)


def _id_sides(g, i, p, A, w, delta, fresh=False):
    """(min_m J(p;m), min_{p'} max_m J(p';m)) over the clipped box."""
    M = np.asarray(g.M, float)
    lo = np.maximum(A - delta * w, 0.0)
    hi = A + delta * w
    jl = float(p.c + phi_of(p) @ (M * lo))
    plans = g.plans_of(i) if hasattr(g, "plans_of") else None
    if plans is not None:
        return jl, min(cost_at(g, q, hi) for q in plans)
    q = g.oracle(i, M * hi, rho=0.0, count=False, fresh=fresh)
    return jl, cost_at(g, q, hi)


def _bisect(adm, hi, iters, rel=1e-6):
    """Smallest delta in [0, hi] with adm(delta) True (adm monotone); returns hi if adm(0) False and adm(hi) True."""
    if adm(0.0):
        return 0.0
    if not np.isfinite(hi):
        hi = 1.0
        while not adm(hi):
            hi *= 4.0
            if hi > 1e6:
                return float("inf")
    elif not adm(hi):
        h2 = hi
        while not adm(h2):
            h2 = max(h2 * 2.0, 1e-3)
            if h2 > 1e6:
                return float("inf")
        hi = h2
    lo = 0.0
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if adm(mid):
            hi = mid
        else:
            lo = mid
        if hi - lo <= rel * max(hi, 1e-9):
            break
    return hi


def m_threshold(g, i, prof, w, hi=np.inf, tol=1e-7, iters=40, fresh=False):
    p = prof[i]
    A = rival_aggregate(prof, i)
    Jp = cost_at(g, p, A)

    def adm(d):
        return _min_M(g, i, p, A, w, d, fresh=fresh) >= Jp - tol * (1.0 + abs(Jp))

    return _bisect(adm, hi, iters)


def id_threshold(g, i, prof, w, hi=np.inf, tol=1e-7, iters=40, fresh=False):
    p = prof[i]
    A = rival_aggregate(prof, i)

    def adm(d):
        jl, jmin = _id_sides(g, i, p, A, w, d, fresh=fresh)
        return jl <= jmin + tol * (1.0 + abs(jl))

    return _bisect(adm, hi, iters)


def gamma_regret(g, i, prof, w, delta, fresh=False):
    """Gamma-maximin regret of p_i at width delta: max_m J(p;m) - min_{p'} max_m J(p';m)  (>= 0, = 0 iff Gamma-admissible)."""
    p = prof[i]
    A = rival_aggregate(prof, i)
    hi = A + delta * w
    q = g.oracle(i, np.asarray(g.M, float) * hi, rho=0.0, count=False, fresh=fresh) if not hasattr(g, "plans_of") else \
        min(g.plans_of(i), key=lambda r: cost_at(g, r, hi))
    return max(0.0, cost_at(g, p, hi) - cost_at(g, q, hi))


def profile_thresholds(g, prof, w, kinds=("E", "M", "ID"), cuts=None, iters=24):
    """Per-carrier thresholds and their maxima.  The order ID <= M <= E (Lemma 3.4) is used to bracket the bisections."""
    N = len(prof)
    out = {k: np.full(N, np.nan) for k in kinds}
    info = []
    for i in range(N):
        e = np.nan
        if "E" in kinds or "M" in kinds or "ID" in kinds:
            e, inf_ = e_threshold(g, i, prof, w, cuts=(cuts[i] if cuts else ()))
            info.append(inf_)
        if "E" in kinds:
            out["E"][i] = e
        mval = np.nan
        if "M" in kinds or "ID" in kinds:
            mval = m_threshold(g, i, prof, w, hi=e, iters=iters)
            if "M" in kinds:
                out["M"][i] = mval
        if "ID" in kinds:
            out["ID"][i] = id_threshold(g, i, prof, w, hi=mval, iters=iters)
    res = {f"{k}_max": float(np.max(v)) for k, v in out.items()}
    res.update({f"{k}_by_carrier": v for k, v in out.items()})
    res["info"] = info
    return res


# ---------------------------------------------------------------------------------------------------------------
# anchored radius and bounds (Theorem 6.1)
# ---------------------------------------------------------------------------------------------------------------


def sigma_max(g, w):
    """max_{i,k} range_{p in P_i} a_ik(p) / w_k  (the range of a coordinate is bounded by the full contribution)."""
    best = 0.0
    for i in range(g.N):
        r = np.asarray(g.a_range(i) if hasattr(g, "a_range") else g.full_a(i), float)
        best = max(best, float(np.max(r / w)))
    return best


def n_uniform_bound(N, d, smax):
    """sigma_max * min{N-1, d+1, 1 + sqrt(d ln(2d)/2)}  (Thm 6.1(c))."""
    return smax * min(N - 1, d + 1, 1.0 + math.sqrt(d * math.log(2 * d) / 2.0))


def mean_contribution(support, weights):
    return [sum(float(x) * p.a for x, p in zip(weights[j], support[j])) for j in range(len(support))]


def anchored_stats(g, support, weights, w, d=None):
    """rho-bar, sigma-bar, d_L, k, three bounds of Thm 6.1(b) for a relaxed equilibrium x* with B_j := supp x*_j."""
    N = len(support)
    d = d if d is not None else len(w)
    abar = mean_contribution(support, weights)
    r = np.zeros((N, len(w)))
    s = np.zeros((N, len(w)))
    diffs = []
    for j in range(N):
        Aj = np.array([p.a for p in support[j]])
        r[j] = np.abs(Aj - abar[j]).max(0)
        s[j] = Aj.max(0) - Aj.min(0)
        diffs.extend(list(Aj - Aj[0]))
    rho = float((r / w).max())
    sig = float((s / w).max())
    dL = int(np.linalg.matrix_rank(np.array(diffs), tol=1e-9)) if len(diffs) and np.abs(np.array(diffs)).max() > 1e-12 else 0
    kk = min(N, dL)
    rsum = (r / w).sum(0)  # sum_j r_jk / w_k
    t1 = max(float(((r / w).sum(0)[None, :] - r / w).max()), 0.0)
    t2 = kk * sig + rho
    t3 = sig * math.sqrt(kk * math.log(2 * d) / 2.0) + rho
    return dict(rho_bar=rho, sigma_bar=sig, d_L=dL, k_sharp=kk, T1=t1, T2=t2, T3=t3, bound=min(t1, t2, t3), abar=abar,
                Abar=sum(abar))


def delta_hat(prof, abar, w):
    """Anchored radius max_i || A_{-i}(p) - Abar*_{-i} ||_{w,inf}."""
    A = agg(prof)
    Abar = sum(abar)
    out = 0.0
    for i, p in enumerate(prof):
        out = max(out, float(np.max(np.abs((A - p.a) - (Abar - abar[i])) / w)))
    return out


# ---------------------------------------------------------------------------------------------------------------
# relaxed equilibria
# ---------------------------------------------------------------------------------------------------------------


def check_relaxed(g, support, weights, tol=1e-7, fresh=False):
    """Largest violation of the relaxed-equilibrium condition: support plans must minimise J_i(.; Abar_{-i}) over the full plan set."""
    abar = mean_contribution(support, weights)
    Abar = sum(abar)
    worst = 0.0
    for i in range(len(support)):
        m = Abar - abar[i]
        b = best_response(g, i, m, fresh=fresh)
        vb = cost_at(g, b, m)
        for x, p in zip(weights[i], support[i]):
            if x > 1e-12:
                worst = max(worst, cost_at(g, p, m) - vb)
    return worst


def mix_pair(g, p0, p1, mixers, base):
    """Indifference system for carriers `mixers` mixing between p0[i] (t=0) and p1[i] (t=1); the others play base[j].

    Returns t (array over mixers) or None when the system is singular."""
    S = list(mixers)
    if len(S) < 2:
        return None
    M = np.asarray(g.M, float)
    cur = [base[j] if j not in S else p0[j] for j in range(len(p0))]
    Ab = agg(cur)
    da = {j: p1[j].a - p0[j].a for j in S}
    dphi = {j: phi_of(p1[j]) - phi_of(p0[j]) for j in S}
    dc = {j: p1[j].c - p0[j].c for j in S}
    G = np.zeros((len(S), len(S)))
    r = np.zeros(len(S))
    for a_, i in enumerate(S):
        r[a_] = -(dc[i] + float(dphi[i] @ (M * (Ab - cur[i].a))))
        for b_, j in enumerate(S):
            if i != j:
                G[a_, b_] = float(dphi[i] @ (M * da[j]))
    if abs(np.linalg.det(G)) < 1e-14 * max(1.0, np.abs(G).max() ** len(S)):
        return None
    try:
        return np.linalg.solve(G, r)
    except np.linalg.LinAlgError:
        return None


def mixed_candidates(g, pures, margin=1e-6):
    """Candidate mixed relaxed equilibria from pairs of distinct pure profiles (two plans per mixing carrier)."""
    cands, seen = [], set()
    n = len(pures)
    N = g.N
    for a_ in range(n):
        for b_ in range(a_ + 1, n):
            p0, p1 = pures[a_], pures[b_]
            diff = [i for i in range(N) if plan_key(p0[i]) != plan_key(p1[i])]
            if len(diff) < 2:
                continue
            for k in range(2, len(diff) + 1):
                for S in itertools.combinations(diff, k):
                    for base in (p0, p1):
                        t = mix_pair(g, p0, p1, S, base)
                        if t is None or not np.all((t > margin) & (t < 1 - margin)):
                            continue
                        key = (a_, b_, S, id(base) == id(p0), tuple(np.round(t, 9)))
                        if key in seen:
                            continue
                        seen.add(key)
                        support = [[base[j]] for j in range(N)]
                        weights = [[1.0] for _ in range(N)]
                        for tt, i in zip(t, S):
                            support[i] = [p0[i], p1[i]]
                            weights[i] = [1.0 - float(tt), float(tt)]
                        cands.append((support, weights, S))
    return cands


def profiles_in_support(support, cap=64, rng=None):
    """Pure profiles in the product of the supports (all of them, or a random sample of `cap` including the extremes)."""
    sizes = [len(s) for s in support]
    total = int(np.prod(sizes))
    if total <= cap:
        return [[support[j][c[j]] for j in range(len(support))] for c in itertools.product(*[range(s) for s in sizes])]
    rng = rng or np.random.default_rng(0)
    seen, out = set(), []
    for _ in range(50 * cap):
        c = tuple(int(rng.integers(s)) for s in sizes)
        if c not in seen:
            seen.add(c)
            out.append([support[j][c[j]] for j in range(len(support))])
        if len(out) >= cap:
            break
    return out


def br_run(g, init, order=None, max_rounds=60, tol=1e-9, rng=None):
    """Gauss-Seidel best-response dynamics with cycle detection.

    Returns dict(profile, status in {'converged','cycle','budget'}, rounds, cycle_len, calls)."""
    prof = list(init)
    A = agg(prof)
    N = len(prof)
    seen = {profile_key(prof): 0}
    c0 = getattr(g, "calls", 0)
    for rnd in range(1, max_rounds + 1):
        moved = False
        ord_ = list(order) if order is not None else (list(rng.permutation(N)) if rng is not None else list(range(N)))
        for i in ord_:
            Am = A - prof[i].a
            b = g.br(i, Am, count=True) if hasattr(g, "br") else best_response(g, i, Am)
            if g.J(i, b, Am) < g.J(i, prof[i], Am) - tol:
                A = Am + b.a
                prof[i] = b
                moved = True
        if not moved:
            return dict(profile=prof, status="converged", rounds=rnd, cycle_len=0, calls=getattr(g, "calls", 0) - c0)
        k = profile_key(prof)
        if k in seen:
            return dict(profile=prof, status="cycle", rounds=rnd, cycle_len=rnd - seen[k], calls=getattr(g, "calls", 0) - c0)
        seen[k] = rnd
    return dict(profile=prof, status="budget", rounds=max_rounds, cycle_len=0, calls=getattr(g, "calls", 0) - c0)


# ---------------------------------------------------------------------------------------------------------------
# explicit finite games (tests, Prop 7.1)
# ---------------------------------------------------------------------------------------------------------------


@dataclass
class EPlan:
    a: np.ndarray
    phi: np.ndarray
    c: float  # cost = - private profit
    name: str = ""

    def key(self):
        return self.name or (tuple(np.round(self.a, 9)), tuple(np.round(self.phi, 9)), round(self.c, 9))


class ExplicitGame:
    """Game with explicit plan lists; cost J_i(p; m) = c_i(p) + <phi_i(p), M m> (utility = -J)."""

    def __init__(self, M, plans):
        self.M = np.asarray(M, float)
        self.plans = plans
        self.N = len(plans)
        self.d = len(self.M)
        self.calls = 0

    @classmethod
    def from_profits(cls, M, a, phi, pi, names=None):
        plans = []
        for i in range(len(a)):
            plans.append([EPlan(np.asarray(a[i][p], float), np.asarray(phi[i][p], float), -float(pi[i][p]),
                                (names[i][p] if names else f"{i}:{p}")) for p in range(len(a[i]))])
        return cls(M, plans)

    def plans_of(self, i):
        return self.plans[i]

    def full_a(self, i):
        return np.max([p.a for p in self.plans[i]], axis=0)

    def full_phi(self, i):
        return np.max([p.phi for p in self.plans[i]], axis=0)

    def a_range(self, i):
        A = np.array([p.a for p in self.plans[i]])
        return A.max(0) - A.min(0)

    def J(self, i, p, Am):
        return cost_at(self, p, Am)

    def oracle(self, i, lam, rho=0.0, count=True, fresh=False, integer=True):
        lam = np.asarray(lam, float)
        return min(self.plans[i], key=lambda p: p.c + float(phi_of(p) @ lam))

    def br(self, i, Am, count=True):
        return self.oracle(i, self.M * Am)

    def profiles(self):
        return itertools.product(*[range(len(p)) for p in self.plans])

    def profile(self, idx):
        return [self.plans[i][k] for i, k in enumerate(idx)]


def enumerate_thresholds(g, w, kinds=("E",)):
    """Exact existence thresholds by enumeration of all pure profiles of an ExplicitGame.

    Returns dict with delta0 per kind (min over profiles of the max over carriers), list of profile thresholds and the
    list of pure Nash equilibria (indices)."""
    prof_thr = {k: [] for k in kinds}
    idxs = list(g.profiles())
    ne = []
    for idx in idxs:
        prof = g.profile(idx)
        res = profile_thresholds(g, prof, w, kinds=kinds, iters=60)
        for k in kinds:
            prof_thr[k].append(res[f"{k}_max"])
        reg = max(cost_at(g, prof[i], rival_aggregate(prof, i)) - min(cost_at(g, q, rival_aggregate(prof, i)) for q in g.plans[i])
                  for i in range(g.N))
        if reg <= 1e-9:
            ne.append(idx)
    return dict(delta0={k: float(np.min(v)) for k, v in prof_thr.items()}, thresholds=prof_thr, profiles=idxs, ne=ne)
