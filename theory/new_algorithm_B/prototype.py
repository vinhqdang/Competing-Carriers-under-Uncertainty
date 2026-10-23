"""Budget-Resource Labelling (BRL) for dependence-robust routing under p-boxes.

Prototype for theory/new_algorithm_B. Sections:
  core      p-boxes, common level grid, comonotone route profile, exact route cost
  testA     upper expectation formula vs LP over all joint laws (brute force)
  testB     budget-allocation identity and integrality vs LP / integer DP
  testC     ESPPRC pricing: every dominance rule vs complete enumeration (exactness)
  testD     ESPPRC scaling: labels and time per dominance rule
  testE     real metro instances: column generation with BRL pricing vs heuristics

Run:  python prototype.py [A B C D E]   (default: all). Writes results_raw.json.
"""
from __future__ import annotations

import itertools
import json
import math
import sys
import time
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds

ROOT = __file__.rsplit("/theory/", 1)[0]
OUT = {}

# ---------------------------------------------------------------------------
# core
# ---------------------------------------------------------------------------


def dkw_upper_quantile(x: np.ndarray, alpha: float, xmax: float) -> tuple[np.ndarray, np.ndarray]:
    """Upper quantile function of the DKW lower CDF max(F_n - eps, 0), capped at support bound xmax.

    Returns (right ends u of the constancy intervals, values), a left-continuous step function on (0,1].
    """
    x = np.sort(np.asarray(x, float))
    n = len(x)
    eps = math.sqrt(math.log(2 / alpha) / (2 * n))
    ends, vals = [], []
    for j in range(1, n + 1):  # F_lo jumps to j/n - eps at x_(j)
        u = j / n - eps
        if u <= 0:
            continue
        ends.append(u)
        vals.append(x[j - 1])
    ends.append(1.0)
    vals.append(max(xmax, x[-1]))
    return np.array(ends), np.array(vals)


def idm_upper_quantile(x: np.ndarray, s: float, xmax: float) -> tuple[np.ndarray, np.ndarray]:
    """Upper quantile of the imprecise Dirichlet model lower CDF: count/(n+s), mass s/(n+s) at xmax."""
    x = np.sort(np.asarray(x, float))
    n = len(x)
    ends = [j / (n + s) for j in range(1, n + 1)] + [1.0]
    vals = list(x) + [max(xmax, x[-1])]
    return np.array(ends), np.array(vals)


def common_grid(qfs: list[tuple[np.ndarray, np.ndarray]]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Merge step quantile functions onto the union of their breakpoints.

    Returns (u_left, w, Qmat) with Qmat[k, l] the value of function k on level interval l.
    """
    ends = np.unique(np.round(np.concatenate([e for e, _ in qfs] + [np.array([1.0])]), 13))
    ends = ends[(ends > 0) & (ends <= 1.0)]
    left = np.concatenate([[0.0], ends[:-1]])
    w = ends - left
    mid = (left + ends) / 2
    Q = np.empty((len(qfs), len(ends)))
    for k, (e, v) in enumerate(qfs):
        idx = np.searchsorted(e, mid, side="left")
        Q[k] = v[np.minimum(idx, len(v) - 1)]
    return left, w, Q


@dataclass
class Loss:
    """phi(T) = fixed + gamma*T + rho*max(0, T - Tmax)."""

    gamma: float
    rho: float
    Tmax: float
    fixed: float = 0.0


def cost_profile(S: np.ndarray, w: np.ndarray, loss: Loss, D: float | None = None) -> float:
    """f_S(D) = fixed + gamma*E S + rho*E(S-D)^+ for the comonotone sum with level values S (ascending)."""
    D = loss.Tmax if D is None else D
    return loss.fixed + loss.gamma * float(w @ S) + loss.rho * float(w @ np.maximum(S - D, 0.0))


def phi(T, loss: Loss):
    return loss.fixed + loss.gamma * T + loss.rho * np.maximum(T - loss.Tmax, 0.0)


# ---------------------------------------------------------------------------
# testA: upper expectation over all joint laws (LP) vs comonotone formula
# ---------------------------------------------------------------------------


def random_pbox(rng, m, lo=1.0, hi=6.0):
    """Random p-box on a finite support grid: lower CDF <= upper CDF, both nondecreasing, lower reaches 1 at max."""
    v = np.sort(rng.uniform(lo, hi, m))
    a = np.sort(rng.uniform(0, 1, m))
    b = np.sort(rng.uniform(0, 1, m))
    Fup = np.maximum(a, b)
    Flo = np.minimum(a, b)
    Fup[-1] = Flo[-1] = 1.0
    return v, Flo, Fup


def upper_quantile_from_cdf(v, Flo):
    """Step upper quantile of the lower CDF Flo on support v."""
    ends, vals = [], []
    for j in range(len(v)):
        if j == 0 or Flo[j] > Flo[j - 1] + 1e-15:
            if Flo[j] > 0:
                ends.append(Flo[j])
                vals.append(v[j])
    return np.array(ends), np.array(vals)


def lp_upper_expectation(pboxes, loss, factor=None):
    """max E phi(sum X) over all joint pmfs on the product grid with marginal CDFs inside the p-boxes.

    factor: optional (pmf over atoms g, pboxes_by_g); then X | G=g has p-boxes pboxes_by_g[g], unknown
    dependence given G, G with known pmf.
    """
    if factor is None:
        atoms = [(1.0, pboxes)]
    else:
        pg, by_g = factor
        atoms = list(zip(pg, by_g))
    A = len(atoms[0][1])
    m = len(atoms[0][1][0][0])
    grid = list(itertools.product(range(m), repeat=A))
    nv = len(grid) * len(atoms)
    c = np.zeros(nv)
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for gi, (pg, pbs) in enumerate(atoms):
        off = gi * len(grid)
        row = np.zeros(nv)
        row[off : off + len(grid)] = 1
        A_eq.append(row)
        b_eq.append(pg)
        for x_idx, x in enumerate(grid):
            T = sum(pbs[a][0][x[a]] for a in range(A))
            c[off + x_idx] = -phi(T, loss)
        for a in range(A):
            v, Flo, Fup = pbs[a]
            for j in range(m - 1):
                row = np.zeros(nv)
                for x_idx, x in enumerate(grid):
                    if x[a] <= j:
                        row[off + x_idx] = 1
                A_ub.append(-row)
                b_ub.append(-pg * Flo[j])
                A_ub.append(row)
                b_ub.append(pg * Fup[j])
    res = linprog(c, A_ub=np.array(A_ub), b_ub=b_ub, A_eq=np.array(A_eq), b_eq=b_eq, bounds=(0, None), method="highs")
    assert res.status == 0, res.message
    return -res.fun


def formula_upper_expectation(pboxes, loss):
    qfs = [upper_quantile_from_cdf(v, Flo) for v, Flo, _ in pboxes]
    _, w, Q = common_grid(qfs)
    return cost_profile(Q.sum(0), w, loss)


def testA(rng, trials=40):
    errs, errs_f, gaps_indep = [], [], []
    for t in range(trials):
        A = int(rng.integers(2, 4))
        m = 4 if A == 3 else 5
        pbs = [random_pbox(rng, m) for _ in range(A)]
        Tmax = float(rng.uniform(0.6, 1.0) * sum(p[0][-1] for p in pbs))
        loss = Loss(gamma=1.0, rho=float(rng.uniform(0.5, 4)), Tmax=Tmax)
        lp = lp_upper_expectation(pbs, loss)
        fo = formula_upper_expectation(pbs, loss)
        errs.append(abs(lp - fo) / max(1, abs(lp)))
        # independent coupling of the worst marginals (a precise-probability model), for scale
        qfs = [upper_quantile_from_cdf(v, Flo) for v, Flo, _ in pbs]
        pm = []
        for e, val in qfs:
            pr = np.diff(np.concatenate([[0], e]))
            pm.append((val, pr))
        Ei = 0.0
        for combo in itertools.product(*[range(len(p[0])) for p in pm]):
            pr = np.prod([pm[a][1][combo[a]] for a in range(A)])
            Ei += pr * phi(sum(pm[a][0][combo[a]] for a in range(A)), loss)
        gaps_indep.append((fo - Ei) / fo)
    # factor model: G with 2 atoms, conditional p-boxes
    for t in range(trials // 2):
        A, m = 2, 4
        pg = np.array([0.4, 0.6])
        by_g = [[random_pbox(rng, m, 1, 3) for _ in range(A)], [random_pbox(rng, m, 2, 6) for _ in range(A)]]
        # same support grid needed for LP grid indexing: fine, each pbox carries its own v
        loss = Loss(1.0, 2.0, 6.0)
        lp = lp_upper_expectation(None, loss, factor=(pg, by_g))
        fo = sum(pg[g] * formula_upper_expectation(by_g[g], loss) for g in range(2))
        errs_f.append(abs(lp - fo) / max(1, abs(lp)))
    OUT["testA"] = {
        "trials": trials,
        "max_rel_err_formula_vs_LP": float(max(errs)),
        "factor_trials": trials // 2,
        "max_rel_err_factor_formula_vs_LP": float(max(errs_f)),
        "mean_rel_excess_over_independent_coupling": float(np.mean(gaps_indep)),
        "max_rel_excess_over_independent_coupling": float(np.max(gaps_indep)),
    }
    print("testA", OUT["testA"])


# ---------------------------------------------------------------------------
# testB: budget allocation identity f_r(T) = min_{sum d <= T} sum_a c_a(d_a)
# ---------------------------------------------------------------------------


def lp_budget(Qa: np.ndarray, w: np.ndarray, loss: Loss):
    """min sum_a [gamma mu_a + rho sum_l w_l (q_al - d_a)^+] s.t. sum_a d_a <= Tmax, d free (LP)."""
    A, L = Qa.shape
    # variables: d (A), t (A*L) with t_al >= q_al - d_a, t >= 0
    nv = A + A * L
    c = np.concatenate([np.zeros(A), loss.rho * np.tile(w, A)])
    A_ub, b_ub = [], []
    for a in range(A):
        for l in range(L):
            row = np.zeros(nv)
            row[a] = -1
            row[A + a * L + l] = -1
            A_ub.append(row)
            b_ub.append(-Qa[a, l])
    row = np.zeros(nv)
    row[:A] = 1
    A_ub.append(row)
    b_ub.append(loss.Tmax)
    bounds = [(None, None)] * A + [(0, None)] * (A * L)
    res = linprog(c, A_ub=np.array(A_ub), b_ub=b_ub, bounds=bounds, method="highs")
    assert res.status == 0
    return loss.fixed + loss.gamma * float((Qa @ w).sum()) + res.fun, res.x[:A]


def int_dp_budget(Qa, w, loss):
    """Integer allocations d_a in {0..Tmax}: exact min by DP (min-plus convolution)."""
    T = int(loss.Tmax)
    F = np.zeros(T + 1)  # F[D] = min cost with budget used <= D
    first = True
    for a in range(Qa.shape[0]):
        d = np.arange(T + 1)
        ca = loss.rho * (np.maximum(Qa[a][None, :] - d[:, None], 0) @ w)
        if first:
            F = np.minimum.accumulate(ca)
            first = False
            continue
        G = np.full(T + 1, np.inf)
        for D in range(T + 1):
            G[D] = np.min(F[: D + 1][::-1] + ca[: D + 1])
        F = G
    return loss.fixed + loss.gamma * float((Qa @ w).sum()) + F[T]


def testB(rng, trials=60):
    e_lp, e_int, nfrac = [], [], []
    for t in range(trials):
        A = int(rng.integers(2, 7))
        L = int(rng.integers(3, 9))
        w = rng.dirichlet(np.ones(L))
        Qa = np.sort(rng.integers(1, 20, (A, L)), axis=1).astype(float)
        S = Qa.sum(0)
        Tmax = float(int(rng.uniform(S[0], S[-1] + 3)))
        loss = Loss(1.0, float(rng.uniform(0.5, 3)), Tmax)
        exact = cost_profile(S, w, loss)
        lpv, d = lp_budget(Qa, w, loss)
        e_lp.append(abs(exact - lpv))
        e_int.append(abs(exact - int_dp_budget(Qa, w, loss)))
    OUT["testB"] = {"trials": trials, "max_abs_err_LP_budget": float(max(e_lp)), "max_abs_err_integer_budget_DP": float(max(e_int))}
    print("testB", OUT["testB"])


# ---------------------------------------------------------------------------
# ESPPRC instances and labelling
# ---------------------------------------------------------------------------


@dataclass
class Pricing:
    """Elementary pricing instance. Node 0 = depot. tau[i,j] is a K-vector of base times per sector."""

    n: int
    tau: np.ndarray  # (n+1, n+1, K)
    svc: np.ndarray  # (n+1,) deterministic service time at node
    dem: np.ndarray  # (n+1,)
    cap: float
    Qk: np.ndarray  # (K, L) upper quantiles of the sector multipliers on the common grid
    w: np.ndarray  # (L,)
    loss: Loss
    duals: np.ndarray  # (n+1,), duals[0] = 0
    scen: np.ndarray | None = None  # (S, K) multiplier samples (SAA reference)
    arcS: np.ndarray = field(init=False)
    Cmin: np.ndarray = field(init=False)

    def __post_init__(self):
        # level profile of every arc incl. service at the head node
        self.arcS = np.einsum("ijk,kl->ijl", self.tau, self.Qk) + self.svc[None, :, None]
        # minimal completion budget: shortest path to depot on level-0 values (Bellman-Ford, small n)
        c0 = self.arcS[:, :, 0].copy()
        np.fill_diagonal(c0, np.inf)
        dist = c0[:, 0].copy()
        dist[0] = 0.0
        for _ in range(self.n + 1):
            dist = np.minimum(dist, np.min(c0 + dist[None, :], axis=1))
            dist[0] = 0.0
        self.Cmin = dist
        self.Wsuf = np.concatenate([np.cumsum(self.w[::-1])[::-1], [0.0]])


class Label:
    __slots__ = ("node", "mask", "load", "tau", "S", "pi", "WS", "pred", "alive")

    def __init__(self, node, mask, load, tau, S, pi, w, pred):
        self.node, self.mask, self.load, self.tau, self.S, self.pi, self.pred = node, mask, load, tau, S, pi, pred
        self.WS = np.concatenate([np.cumsum((w * S)[::-1])[::-1], [0.0]])
        self.alive = True


def f_eval(lab: Label, D: np.ndarray, P: Pricing) -> np.ndarray:
    """Vectorised f_S(D) - pi (without the fixed cost)."""
    idx = np.searchsorted(lab.S, D, side="right")
    tail = lab.WS[idx] - D * P.Wsuf[idx]
    return P.loss.gamma * lab.WS[0] + P.loss.rho * tail - lab.pi


def dominates(a: Label, b: Label, rule: str, P: Pricing, tol=1e-9) -> bool:
    """Does label a dominate label b (same node)? Rules: 'tau', 'pointwise', 'functional'."""
    if a.load > b.load + tol or (a.mask & ~b.mask):
        return False
    if a.pi < b.pi - tol and rule != "functional":
        return False
    if rule == "tau":
        return bool(np.all(a.tau <= b.tau + tol))
    if rule == "pointwise":
        return bool(np.all(a.S <= b.S + tol))
    if rule == "scenario":
        return bool(np.all(a.S <= b.S + tol))  # S holds scenario route times here
    # functional (stop-loss) dominance on the completion window
    hi = min(b.S[-1], P.loss.Tmax - P.Cmin[b.node])
    lo = min(b.S[0], hi)
    pts = np.concatenate([[lo, hi], a.S[(a.S > lo) & (a.S < hi)], b.S[(b.S > lo) & (b.S < hi)]])
    return bool(np.all(f_eval(a, pts, P) <= f_eval(b, pts, P) + tol))


def label_cost_final(lab: Label, P: Pricing, rule: str) -> float:
    """Reduced cost of a completed route (label at depot)."""
    if rule == "scenario":
        return float(np.mean(phi(lab.S, P.loss))) - lab.pi
    return cost_profile(lab.S, P.w, P.loss) - lab.pi


def espprc(P: Pricing, rule: str, time_limit: float = 120.0, max_cols: int = 50):
    """Mono-directional label-setting ESPPRC; returns (best reduced cost, routes with negative rc, stats).

    rule: 'none' (complete enumeration), 'tau', 'pointwise', 'functional', 'scenario' (SAA objective).
    """
    t0 = time.perf_counter()
    n = P.n
    K = P.tau.shape[2]
    w = P.w if rule != "scenario" else np.full(P.scen.shape[0], 1.0 / P.scen.shape[0])
    if rule == "scenario":
        arcX = np.einsum("ijk,sk->ijs", P.tau, P.scen) + P.svc[None, :, None]
    else:
        arcX = P.arcS
    start = Label(0, 0, 0.0, np.zeros(K), np.zeros(arcX.shape[2]), 0.0, w, None)
    buckets: list[list[Label]] = [[] for _ in range(n + 1)]
    queue = [start]
    created = 0
    best, cols = math.inf, []
    timed_out = False
    while queue:
        nxt = []
        for lab in queue:
            if not lab.alive:
                continue
            if time.perf_counter() - t0 > time_limit:
                timed_out = True
                break
            i = lab.node
            # close the route
            if i != 0:
                S = lab.S + arcX[i, 0]
                if rule == "scenario":
                    S = np.sort(S) if False else S
                done = Label(0, lab.mask, lab.load, lab.tau + P.tau[i, 0], S, lab.pi, w, lab)
                rc = label_cost_final(done, P, rule) + P.loss.fixed
                if rc < best:
                    best = rc
                if rc < -1e-9:
                    cols.append((rc, done))
            for j in range(1, n + 1):
                if lab.mask >> j & 1 or lab.load + P.dem[j] > P.cap + 1e-12:
                    continue
                S = lab.S + arcX[i, j]
                new = Label(j, lab.mask | (1 << j), lab.load + P.dem[j], lab.tau + P.tau[i, j], S, lab.pi + P.duals[j], w, lab)
                created += 1
                if rule != "none":
                    B = buckets[j]
                    if any(o.alive and dominates(o, new, rule, P) for o in B):
                        continue
                    for o in B:
                        if o.alive and dominates(new, o, rule, P):
                            o.alive = False
                    buckets[j] = [o for o in B if o.alive]
                    buckets[j].append(new)
                nxt.append(new)
        if timed_out:
            break
        queue = nxt
    cols.sort(key=lambda t: t[0])
    routes = []
    seen = set()
    for rc, lab in cols:
        r = []
        x = lab.pred
        while x is not None and x.node != 0:
            r.append(x.node)
            x = x.pred
        r = tuple(reversed(r))
        if r not in seen:
            seen.add(r)
            routes.append((rc, r))
        if len(routes) >= max_cols:
            break
    stats = {"rule": rule, "time": time.perf_counter() - t0, "labels_created": created,
             "labels_kept": int(sum(len(b) for b in buckets)), "timed_out": timed_out}
    return best, routes, stats


def route_profile(P: Pricing, route: tuple[int, ...]) -> np.ndarray:
    p = (0, *route, 0)
    return sum(P.arcS[p[t], p[t + 1]] for t in range(len(p) - 1))


def route_tau(P: Pricing, route) -> np.ndarray:
    p = (0, *route, 0)
    return sum(P.tau[p[t], p[t + 1]] for t in range(len(p) - 1))


def random_pricing(rng, n, K=4, nsamp=40, alpha=0.05, cap=None, dual_scale=1.0, seed_duals=True, Tfrac=0.75):
    """Random Euclidean pricing instance with sector p-boxes from DKW bands of lognormal multipliers."""
    xy = rng.uniform(0, 1, (n + 1, 2))
    xy[0] = 0.5
    s = int(round(math.sqrt(K)))
    sec = np.clip((xy * s).astype(int), 0, s - 1)
    sec = sec[:, 0] * s + sec[:, 1]
    dist = np.linalg.norm(xy[:, None] - xy[None], axis=-1) * 100  # minutes-ish
    tau = np.zeros((n + 1, n + 1, K))
    for i in range(n + 1):
        for j in range(n + 1):
            tau[i, j, sec[i]] += dist[i, j] / 2
            tau[i, j, sec[j]] += dist[i, j] / 2
    svc = np.full(n + 1, 5.0)
    svc[0] = 0
    dem = np.ones(n + 1)
    dem[0] = 0
    cap = cap or max(3, n // 3)
    g = rng.standard_normal((nsamp, 1))
    e = rng.standard_normal((nsamp, K))
    scen = np.exp(0.3 * g + 0.2 * e) * (1 + 0.4 * rng.uniform(0, 1, K))
    qfs = [dkw_upper_quantile(scen[:, k], alpha, xmax=2.5 * scen[:, k].max()) for k in range(K)]
    _, w, Qk = common_grid(qfs)
    # deadline: a fraction of a typical full route's mean duration
    typical = cap * (svc[1] + 25.0) * float(Qk.mean())
    loss = Loss(gamma=1.0, rho=3.0, Tmax=Tfrac * typical, fixed=20.0)
    duals = np.concatenate([[0.0], dual_scale * rng.uniform(20, 60, n)])
    return Pricing(n, tau, svc, dem, cap, Qk, w, loss, duals, scen)


def testC(rng, trials=12):
    rows = []
    for t in range(trials):
        n = int(rng.integers(6, 9))
        P = random_pricing(rng, n, cap=int(rng.integers(3, 6)), Tfrac=float(rng.uniform(0.4, 1.1)))
        ref, _, st0 = espprc(P, "none")
        row = {"n": n, "enum_best": ref, "enum_labels": st0["labels_created"]}
        for rule in ("tau", "pointwise", "functional"):
            b, _, st = espprc(P, rule)
            row[rule] = b
            row[rule + "_labels"] = st["labels_kept"]
            assert abs(b - ref) < 1e-6 * max(1, abs(ref)), (rule, b, ref)
        # single-level Lagrangian bound max_u min_r (common u for all routes), via enumeration of routes
        rows.append(row)
    OUT["testC"] = {"trials": trials, "all_rules_match_enumeration": True, "rows": rows}
    print("testC ok", [(r["n"], r["enum_labels"], r["pointwise_labels"], r["functional_labels"]) for r in rows])


def testD(rng, sizes=(10, 15, 20, 25, 30), reps=2, tl=120.0):
    import copy

    rows = []
    for n in sizes:
        for r in range(reps):
            P = random_pricing(rng, n, K=9, cap=6, Tfrac=0.8)
            Pdet = copy.copy(P)
            Pdet.loss = Loss(P.loss.gamma, 0.0, P.loss.Tmax, P.loss.fixed)  # risk-neutral mean cost
            row = {"n": n, "rep": r, "L": int(len(P.w))}
            for rule in ("deterministic_mean", "functional", "tau", "pointwise", "scenario"):
                PP, rr = (Pdet, "functional") if rule == "deterministic_mean" else (P, rule)
                b, _, st = espprc(PP, rr, time_limit=tl)
                row[rule] = {"best": b, "time": round(st["time"], 3), "kept": st["labels_kept"],
                             "created": st["labels_created"], "timeout": st["timed_out"]}
            rows.append(row)
            print("testD", n, r, {k: (v["time"], v["kept"], v["timeout"]) for k, v in row.items() if isinstance(v, dict)})
    OUT["testD"] = rows


if __name__ == "__main__":
    which = sys.argv[1:] or list("ABCDE")
    rng = np.random.default_rng(20261023)
    if "A" in which:
        testA(rng)
    if "B" in which:
        testB(rng)
    if "C" in which:
        testC(rng)
    if "D" in which:
        testD(rng)
    if "E" in which:
        from real_instances import testE  # noqa: E402

        OUT["testE"] = testE()
    try:
        old = json.load(open(ROOT + "/theory/new_algorithm_B/results_raw.json"))
    except Exception:
        old = {}
    old.update(OUT)
    json.dump(old, open(ROOT + "/theory/new_algorithm_B/results_raw.json", "w"), indent=1, default=float)
