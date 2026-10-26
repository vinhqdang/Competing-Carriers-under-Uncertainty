"""Instance builders and plan evaluation for experiments/run_brl_bench.py.

Public instances: Solomon (R1/C1/RC1, 25/50/100 customers) and Augerat (A, B) read from data/public_instances.
Uncertainty (emulated, see docs/EXPERIMENTS.md): K sector multipliers with a common-factor lognormal law, as in the
metro calibration of theory/new_algorithm_B/real_instances.py; carriers observe N training days, p-boxes are DKW bands.
"""
from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "theory/new_algorithm_B"))
PUB = ROOT / "data/public_instances"

from ccu import brl, brl_variants as bv  # noqa: E402


# ---------------------------------------------------------------------------------------------------------------
# parsers
# ---------------------------------------------------------------------------------------------------------------


def parse_solomon(path: Path) -> dict:
    lines = [ln.rstrip() for ln in Path(path).read_text().splitlines()]
    name = lines[0].strip()
    i = next(k for k, ln in enumerate(lines) if ln.strip().startswith("NUMBER"))
    cap = float(lines[i + 1].split()[1])
    j = next(k for k, ln in enumerate(lines) if ln.strip().startswith("CUST NO"))
    rows = [list(map(float, ln.split())) for ln in lines[j + 1:] if ln.strip()]
    a = np.array(rows)
    return dict(name=name, cap=cap, xy=a[:, 1:3], dem=a[:, 3], ready=a[:, 4], due=a[:, 5], svc=a[:, 6],
                horizon=float(a[0, 5]), kind="solomon")


def parse_augerat(path: Path) -> dict:
    txt = Path(path).read_text().splitlines()
    d = {}
    sec = None
    coords, dems = [], []
    for ln in txt:
        s = ln.strip()
        if not s or s == "EOF":
            continue
        if ":" in s and not s[0].isdigit():
            k, v = s.split(":", 1)
            d[k.strip()] = v.strip()
            continue
        if s.startswith("NODE_COORD_SECTION"):
            sec = "c"
            continue
        if s.startswith("DEMAND_SECTION"):
            sec = "d"
            continue
        if s.startswith("DEPOT_SECTION"):
            sec = None
            continue
        if sec == "c":
            p = s.split()
            coords.append([float(p[1]), float(p[2])])
        elif sec == "d":
            p = s.split()
            dems.append(float(p[1]))
    comment = d.get("COMMENT", "")
    import re
    mo = re.search(r"(?:Optimal|Best) value:\s*(\d+)", comment)
    mk = re.search(r"Min no of trucks:\s*(\d+)", comment)
    return dict(name=d["NAME"], cap=float(d["CAPACITY"]), xy=np.array(coords), dem=np.array(dems),
                svc=np.zeros(len(dems)), opt=float(mo.group(1)) if mo else np.nan, k=int(mk.group(1)) if mk else 1,
                kind="augerat")


def public_path(inst: str) -> Path:
    """'solomon25/R101', 'solomon50/C101', 'solomon100/RC101', 'augerat_A/A-n32-k5'."""
    fam, nm = inst.split("/")
    if fam.startswith("solomon"):
        return PUB / f"solomon_{fam[7:]}" / f"{nm}.txt"
    return PUB / fam / f"{nm}.vrp"


# ---------------------------------------------------------------------------------------------------------------
# uncertainty law and instance specification
# ---------------------------------------------------------------------------------------------------------------


@dataclass
class Law:
    m: np.ndarray
    sc: float
    ss: float
    xmax: float

    def draw(self, rng, N):
        K = len(self.m)
        g = rng.standard_normal((N, 1))
        e = rng.standard_normal((N, K))
        return self.m[None] * np.exp(self.sc * g + self.ss * e - 0.5 * (self.sc ** 2 + self.ss ** 2))


def make_law(K: int, cong: float, peak: float, spread=(0.85, 1.15)) -> Law:
    m = 1 + cong * np.linspace(spread[1], spread[0], K)
    target = math.log((1 + peak) / (1 + cong))
    s = 1.645 - math.sqrt(max(1.645 ** 2 - 2 * target, 0.0))
    sc = 0.7 * s
    ss = math.sqrt(max(s * s - sc * sc, 0.0))
    return Law(m, sc, ss, 1 + 2 * peak)


def kmeans(X, K, rng, it=50):
    C = X[rng.choice(len(X), K, replace=False)]
    lab = np.zeros(len(X), int)
    for _ in range(it):
        lab = np.argmin(((X[:, None] - C[None]) ** 2).sum(-1), 1)
        C = np.array([X[lab == k].mean(0) if np.any(lab == k) else C[k] for k in range(K)])
    return lab


@dataclass
class Spec:
    name: str
    n: int
    tau: np.ndarray
    svc: np.ndarray
    dem: np.ndarray
    cap: float
    loss: brl.Loss
    law: Law
    K: int
    meta: dict


def public_spec(inst: str, n: int | None = None, K: int = 4, cong: float = 0.3, peak: float = 0.8,
                fixed_frac: float = 0.25, rho_ratio: float = 3.0, tmax_scale: float = 1.0) -> Spec:
    d = parse_solomon(public_path(inst)) if inst.startswith("solomon") else parse_augerat(public_path(inst))
    xy, dem, svc = d["xy"], d["dem"], d["svc"]
    if n is not None:
        xy, dem, svc = xy[: n + 1], dem[: n + 1], svc[: n + 1]
    n = len(xy) - 1
    if d["kind"] == "solomon":
        Tmax = d["horizon"] * tmax_scale  # route duration (return to the depot) due date of the depot
    else:
        Tmax = 1.1 * d["opt"] / d["k"] * tmax_scale  # 10% above the mean length of a best-known route
    rng = np.random.default_rng(12345)
    lab = kmeans((xy - xy.mean(0)) / (xy.std(0) + 1e-9), K, rng)
    D = np.sqrt(((xy[:, None] - xy[None]) ** 2).sum(-1))
    tau = np.zeros((n + 1, n + 1, K))
    for a in range(n + 1):
        for b in range(n + 1):
            if a != b:
                tau[a, b, lab[a]] += D[a, b] / 2
                tau[a, b, lab[b]] += D[a, b] / 2
    loss = brl.Loss(gamma=1.0, rho=rho_ratio, Tmax=float(Tmax), fixed=fixed_frac * float(Tmax))
    law = make_law(K, cong, peak)
    return Spec(inst, n, tau, svc.astype(float), dem.astype(float), float(d["cap"]), loss, law, K,
                dict(Tmax=Tmax, kind=d["kind"], cong=cong, peak=peak))


def metro_spec(city: str, n: int, seed: int = 0, ndays: int = 60) -> tuple[Spec, np.ndarray, np.ndarray]:
    """Metro instance of theory/new_algorithm_B/real_instances.py with `n` customer zones (K = 9 sectors, time in
    seconds).  Returns (spec, training days (ndays, K), true-law draws)."""
    import real_instances as ri
    P, true, meta = ri.build(city, ncust=n, K=9, ndays=ndays, seed=seed)
    loss = brl.Loss(P.loss.gamma, P.loss.rho, P.loss.Tmax, P.loss.fixed)
    spec = Spec(f"metro/{city}", n, P.tau, P.svc, P.dem, float(P.cap), loss, None, 9, meta)
    spec.meta["Qk"], spec.meta["w"] = P.Qk, P.w
    return spec, P.scen, true


# ---------------------------------------------------------------------------------------------------------------
# data, p-box, criteria
# ---------------------------------------------------------------------------------------------------------------


def make_days(spec: Spec, rep: int, Nmax: int = 60, ntest: int = 2000):
    # deterministic across processes: seed from a stable hash of the name
    h = sum((i + 1) * ord(c) for i, c in enumerate(spec.name)) % 100_000
    rng = np.random.default_rng([h, rep, 1])
    train = spec.law.draw(rng, Nmax)
    test = spec.law.draw(np.random.default_rng([h, rep, 2]), ntest)
    return train, test


def pbox_instance(spec: Spec, train: np.ndarray, alpha: float = 0.05) -> brl.RoutingInstance:
    qfs = [brl.dkw_upper_quantile(train[:, k], alpha, spec.law.xmax) for k in range(spec.K)]
    _, w, Qk = brl.common_grid(qfs)
    return brl.RoutingInstance(spec.n, spec.tau, spec.svc, spec.dem, spec.cap, Qk, w, spec.loss)


def criteria_instances(spec: Spec, train: np.ndarray, wass_eps: float = 0.05, cvar_alpha: float = 0.8, lam: float = 0.5):
    """All five route-cost models on the same data: BRL p-box, SAA, Wasserstein type-1, mean-CVaR, deterministic mean."""
    pb = pbox_instance(spec, train)
    base = pb  # carries tau, svc, dem, cap, loss
    out = {
        "brl": pb,
        "saa": bv.vec_instance_saa(base, train),
        "wass": bv.vec_instance_saa(base, train, wass_eps=wass_eps),
        "cvar": bv.vec_instance_saa(base, train, risk=1, alpha=cvar_alpha, lam=lam),
        "det": bv.vec_instance_saa(base, train.mean(0, keepdims=True)),
    }
    return out


def route_tau(spec: Spec, route) -> np.ndarray:
    p = (0, *route, 0)
    return sum(spec.tau[p[t], p[t + 1]] for t in range(len(p) - 1))


def evaluate_plan(spec: Spec, routes, test: np.ndarray) -> dict:
    """Out-of-sample statistics of a plan on held-out days (multiplier matrix `test`, shape (T, K))."""
    ls = spec.loss
    T = len(test)
    tot = np.zeros(T)
    over = np.zeros(T)
    late = np.zeros(T)
    dur = np.zeros(T)
    for r in routes:
        t = route_tau(spec, r)
        s = float(spec.svc[list(r)].sum())
        Tr = test @ t + s
        ov = np.maximum(Tr - ls.Tmax, 0.0)
        tot += ls.fixed + ls.gamma * Tr + ls.rho * ov
        over += ov
        late += (Tr > ls.Tmax)
        dur += Tr
    srt = np.sort(tot)
    k = max(1, int(math.ceil(0.1 * T)))
    nr = max(len(routes), 1)
    return dict(oos_mean=float(tot.mean()), oos_p95=float(np.quantile(tot, 0.95)), oos_cvar90=float(srt[-k:].mean()),
                oos_overtime=float(over.mean()), oos_late_route_frac=float(late.mean() / nr),
                oos_late_day_frac=float(((over > 0)).mean()), oos_mean_time=float(dur.mean()), n_routes=len(routes))


def plan_costs(crit: dict, routes) -> dict:
    """The plan's value under each of the five criteria (train-data based)."""
    return {f"val_{k}": float(sum(inst.route_cost(r) for r in routes)) for k, inst in crit.items()}


def local_search(inst, routes, tlim: float = 10.0):
    """Relocate / swap / intra-route 2-opt descent on `inst.route_cost` (first improvement, memoised route costs).

    Used to polish the plans of the baselines so that they are not limited by the pricing heuristic.  Customers stay
    partitioned (all customers served) and the capacity is respected.  Returns (routes, value)."""
    import time as _t
    t0 = _t.perf_counter()
    dem, cap = inst.dem, inst.cap
    memo: dict = {}

    def c(r):
        r = tuple(r)
        if not r:
            return 0.0
        v = memo.get(r)
        if v is None:
            v = memo[r] = inst.route_cost(r)
        return v

    sol = [list(r) for r in routes]
    load = lambda r: float(dem[list(r)].sum()) if len(r) else 0.0  # noqa: E731
    improved = True
    while improved and _t.perf_counter() - t0 < tlim:
        improved = False
        for a in range(len(sol)):
            if improved:
                break
            ra = sol[a]
            ca = c(ra)
            # intra-route 2-opt
            for i in range(len(ra) - 1):
                for j in range(i + 1, len(ra)):
                    nr = ra[:i] + ra[i:j + 1][::-1] + ra[j + 1:]
                    if c(nr) < ca - 1e-9:
                        sol[a] = nr
                        improved = True
                        break
                if improved:
                    break
            if improved:
                break
            # relocate and swap
            for b in range(len(sol) + 1):
                if b == a:
                    continue
                rb = sol[b] if b < len(sol) else []
                cb = c(rb)
                lb = load(rb)
                for i, cust in enumerate(ra):
                    rest = ra[:i] + ra[i + 1:]
                    if lb + dem[cust] <= cap + 1e-9:
                        for q in range(len(rb) + 1):
                            nb = rb[:q] + [cust] + rb[q:]
                            if c(rest) + c(nb) < ca + cb - 1e-9:
                                sol[a] = rest
                                if b < len(sol):
                                    sol[b] = nb
                                else:
                                    sol.append(nb)
                                improved = True
                                break
                    if improved:
                        break
                    for q, other in enumerate(rb):
                        if load(rest) + dem[other] <= cap + 1e-9 and lb - dem[other] + dem[cust] <= cap + 1e-9:
                            na = ra[:i] + [other] + ra[i + 1:]
                            nb = rb[:q] + [cust] + rb[q + 1:]
                            if c(na) + c(nb) < ca + cb - 1e-9:
                                sol[a], sol[b] = na, nb
                                improved = True
                                break
                    if improved:
                        break
                if improved:
                    break
        sol = [r for r in sol if r]
    return [tuple(r) for r in sol], float(sum(c(r) for r in sol))
