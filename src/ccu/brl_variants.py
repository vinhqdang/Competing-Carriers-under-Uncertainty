"""Labelling variants for the BRL benchmark and scale study (additive module; `ccu.brl` is unchanged).

One compiled label-setting kernel with
  * three dominance rules for the comonotone (p-box) route-time profile S (levels ascending):
        mode 0  "window"  : BRL, stop-loss comparison restricted to the completion window (identical to `brl.espprc`);
        mode 1  "nowin"   : the same stop-loss comparison over the whole budget range D >= 0 (valid, weaker);
        mode 2  "qv"      : quantile-vector (pointwise) dominance  S_a <= S_b  plus a scalar tie-break (valid, weakest);
  * `mode 2` is also the exact rule for vector-valued resources that are not comonotone: SAA scenario vectors, the
    Wasserstein-ball cost (scenario vector + K sector-time accumulators) and mean-CVaR route costs;
  * a per-bucket label cap (`bcap_h`, heuristic pricing: keeps the labels with the best scalar reduced cost; the result
    is then NOT a certificate);
  * an optional completion bound (`lbprune`): a label is dropped when the lower bound
        f(S + SP_levels[j]) - pi - rem_cap * max_j max(dual_j, 0)/dem_j     is >= 0,
    which is valid for ng-routes (customers may repeat) and cannot remove any route of negative reduced cost;
  * counters (labels created, kept, dominance comparisons) and caps on created labels / comparisons, used as a
    machine-independent time limit.  A hit cap sets `overflow` (the result is then not a certificate).

Masks are two 64-bit words (customers 1..127).

Scalar tie-break of the pointwise rules: a dominates b if S_a <= S_b componentwise and  tie*sum_l w_l S_a - pi_a <=
tie*sum_l w_l S_b - pi_b, where `tie` is a lower bound of the marginal cost of one unit of mean route time (gamma for the
risk-neutral and Wasserstein costs, (1-lambda)*gamma for mean-CVaR).  It is valid because every route cost used here is
nondecreasing in S and increases by at least tie*mean(Delta S).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
from numba import njit

from .brl import Loss, _dominates, _feval  # noqa: F401

_M64 = (1 << 64) - 1


def ng_masks_py(inst, size: int = 8) -> np.ndarray:
    """ng-neighbourhoods as Python-int bit masks (object array), any n <= 127 (`brl.ng_masks` stops at n = 63)."""
    D = inst.tau.sum(-1)
    ng = np.zeros(inst.n + 1, dtype=object)
    for i in range(inst.n + 1):
        ng[i] = 0
    for i in range(1, inst.n + 1):
        near = list(np.argsort(D[i, 1:] + D[1:, i]) + 1)[:size]
        m = 1 << i
        for j in near:
            m |= 1 << int(j)
        ng[i] = m
    return ng


@njit(cache=True)
def _dom_nowin(Sa, WSa, pia, Sb, WSb, pib, wsuf, gamma, rho, tol):
    L = Sa.shape[0]
    hi = max(Sa[L - 1], Sb[L - 1])
    if _feval(Sa, WSa, pia, 0.0, wsuf, gamma, rho) > _feval(Sb, WSb, pib, 0.0, wsuf, gamma, rho) + tol:
        return False
    if _feval(Sa, WSa, pia, hi, wsuf, gamma, rho) > _feval(Sb, WSb, pib, hi, wsuf, gamma, rho) + tol:
        return False
    for k in range(L):
        v = Sa[k]
        if v > 0.0 and v < hi:
            if _feval(Sa, WSa, pia, v, wsuf, gamma, rho) > _feval(Sb, WSb, pib, v, wsuf, gamma, rho) + tol:
                return False
        v = Sb[k]
        if v > 0.0 and v < hi:
            if _feval(Sa, WSa, pia, v, wsuf, gamma, rho) > _feval(Sb, WSb, pib, v, wsuf, gamma, rho) + tol:
                return False
    return True


@njit(cache=True)
def _dom_qv(Sa, sca, Sb, scb, tol):
    if sca > scb + tol:
        return False
    for l in range(Sa.shape[0]):
        if Sa[l] > Sb[l] + tol:
            return False
    return True


@njit(cache=True)
def _final_cost(S, w, L0, gamma, rho, Tmax, fixed, wass, risk, alpha, lam, buf):
    """Route cost of a completed profile.  risk 0: expectation (+ Wasserstein term on S[L0:]); risk 1: mean-CVaR."""
    L = S.shape[0]
    if risk == 0:
        tot = 0.0
        over = 0.0
        for l in range(L0):
            tot += w[l] * S[l]
            if S[l] > Tmax:
                over += w[l] * (S[l] - Tmax)
        c = fixed + gamma * tot + rho * over
        if wass > 0.0 and L > L0:
            m = 0.0
            for x in range(L0, L):
                if S[x] > m:
                    m = S[x]
            c += wass * m
        return c
    # mean-CVaR over the L0 equally weighted scenarios
    for l in range(L0):
        buf[l] = gamma * S[l] + rho * max(S[l] - Tmax, 0.0)
    mean = 0.0
    for l in range(L0):
        mean += buf[l] / L0
    srt = np.sort(buf[:L0])
    k = (1.0 - alpha) * L0  # mass of the tail in scenarios
    full = int(np.floor(k + 1e-12))
    acc = 0.0
    for t in range(full):
        acc += srt[L0 - 1 - t]
    rem = k - full
    if rem > 1e-12 and full < L0:
        acc += rem * srt[L0 - 1 - full]
    cvar = acc / k
    return fixed + (1.0 - lam) * mean + lam * cvar


@njit(cache=True)
def _kernel(n, L, L0, arcS, dem, cap, w, wsuf, gamma, rho, Tmax, fixed, Cmin, ng_lo, ng_hi, duals, maxlab, bcap, kcols, tol_rc,
            allow, mode, tie, wass, risk, alpha, lam, bcap_h, lbprune, spl, rmax, max_created, max_cmp, maxlen):
    wl = 1 if mode == 2 else L + 1
    Sarr = np.empty((maxlab, L))
    WSarr = np.empty((maxlab, wl))
    node = np.empty(maxlab, np.int32)
    mlo = np.empty(maxlab, np.uint64)
    mhi = np.empty(maxlab, np.uint64)
    load = np.empty(maxlab)
    pil = np.empty(maxlab)
    scl = np.empty(maxlab)
    pred = np.empty(maxlab, np.int32)
    alive = np.zeros(maxlab, np.bool_)
    bk = np.empty((n + 1, bcap), np.int32)
    bc = np.zeros(n + 1, np.int64)
    tS = np.empty(L)
    tWS = np.empty(wl)
    buf = np.empty(L0)
    cand_rc = np.full(kcols, 1e300)
    cand_lab = np.full(kcols, -1, np.int32)
    best = 1e300
    created = 0
    ncmp = 0
    npruned = 0
    nheur = 0
    overflow = False
    node[0] = 0
    mlo[0] = np.uint64(0)
    mhi[0] = np.uint64(0)
    load[0] = 0.0
    pil[0] = 0.0
    scl[0] = 0.0
    pred[0] = -1
    alive[0] = True
    for l in range(L):
        Sarr[0, l] = 0.0
    for l in range(wl):
        WSarr[0, l] = 0.0
    nlab = 1
    head = 0
    one = np.uint64(1)
    tcl = np.empty(L)
    while head < nlab:
        lab = head
        head += 1
        if not alive[lab]:
            continue
        i = node[lab]
        if i != 0 and allow[i, 0]:
            for l in range(L):
                tcl[l] = Sarr[lab, l] + arcS[i, 0, l]
            rc = _final_cost(tcl, w, L0, gamma, rho, Tmax, fixed, wass, risk, alpha, lam, buf) - pil[lab]
            if rc < best:
                best = rc
            if rc < -tol_rc:
                worst = 0
                for c in range(1, kcols):
                    if cand_rc[c] > cand_rc[worst]:
                        worst = c
                if rc < cand_rc[worst]:
                    cand_rc[worst] = rc
                    cand_lab[worst] = lab
        for j in range(1, n + 1):
            if j < 64:
                if (mlo[lab] >> np.uint64(j)) & one:
                    continue
            else:
                if (mhi[lab] >> np.uint64(j - 64)) & one:
                    continue
            if not allow[i, j]:
                continue
            if load[lab] + dem[j] > cap + 1e-12:
                continue
            for l in range(L):
                tS[l] = Sarr[lab, l] + arcS[i, j, l]
            acc = 0.0
            if mode == 2:
                for l in range(L0):
                    acc += w[l] * tS[l]
                sc_new = tie * acc
            else:
                for l in range(L - 1, -1, -1):
                    acc += w[l] * tS[l]
                    tWS[l] = acc
                tWS[L] = 0.0
                sc_new = tie * tWS[0]
            npi = pil[lab] + duals[j]
            nload = load[lab] + dem[j]
            sc_new -= npi
            created += 1
            if created > max_created or ncmp > max_cmp:
                overflow = True
                break
            if lbprune:
                lbv = 0.0
                over = 0.0
                for l in range(L0):
                    v = tS[l] + spl[j, l]
                    lbv += w[l] * v
                    if v > Tmax:
                        over += w[l] * (v - Tmax)
                lbc = fixed + gamma * lbv + rho * over - npi - max(cap - nload, 0.0) * rmax
                if lbc >= -tol_rc:
                    npruned += 1
                    continue
            nlo = mlo[lab] & ng_lo[j]
            nhi = mhi[lab] & ng_hi[j]
            if j < 64:
                nlo = nlo | (one << np.uint64(j))
            else:
                nhi = nhi | (one << np.uint64(j - 64))
            hi_lim = Tmax - Cmin[j]
            dom = False
            cnt = bc[j]
            for t in range(cnt):
                o = bk[j, t]
                if load[o] > nload + 1e-9:
                    continue
                if (mlo[o] & ~nlo) != np.uint64(0) or (mhi[o] & ~nhi) != np.uint64(0):
                    continue
                ncmp += 1
                if mode == 0:
                    d = _dominates(Sarr[o], WSarr[o], pil[o], tS, tWS, npi, hi_lim, wsuf, gamma, rho, 1e-9)
                elif mode == 1:
                    d = _dom_nowin(Sarr[o], WSarr[o], pil[o], tS, tWS, npi, wsuf, gamma, rho, 1e-9)
                else:
                    d = _dom_qv(Sarr[o], scl[o], tS, sc_new, 1e-9)
                if d:
                    dom = True
                    break
            if dom:
                continue
            t = 0
            while t < bc[j]:
                o = bk[j, t]
                if nload <= load[o] + 1e-9 and (nlo & ~mlo[o]) == np.uint64(0) and (nhi & ~mhi[o]) == np.uint64(0):
                    ncmp += 1
                    if mode == 0:
                        d = _dominates(tS, tWS, npi, Sarr[o], WSarr[o], pil[o], hi_lim, wsuf, gamma, rho, 1e-9)
                    elif mode == 1:
                        d = _dom_nowin(tS, tWS, npi, Sarr[o], WSarr[o], pil[o], wsuf, gamma, rho, 1e-9)
                    else:
                        d = _dom_qv(tS, sc_new, Sarr[o], scl[o], 1e-9)
                    if d:
                        alive[o] = False
                        bk[j, t] = bk[j, bc[j] - 1]
                        bc[j] -= 1
                        continue
                t += 1
            if bcap_h > 0 and bc[j] >= bcap_h:
                # heuristic: replace the label with the worst scalar score if the new one is better
                wt = 0
                for t in range(1, bc[j]):
                    if scl[bk[j, t]] > scl[bk[j, wt]]:
                        wt = t
                nheur += 1
                if sc_new < scl[bk[j, wt]]:
                    alive[bk[j, wt]] = False
                    bk[j, wt] = bk[j, bc[j] - 1]
                    bc[j] -= 1
                else:
                    continue
            if nlab >= maxlab or bc[j] >= bcap:
                overflow = True
                break
            nid = nlab
            nlab += 1
            node[nid] = j
            mlo[nid] = nlo
            mhi[nid] = nhi
            load[nid] = nload
            pil[nid] = npi
            scl[nid] = sc_new
            pred[nid] = lab
            alive[nid] = True
            for l in range(L):
                Sarr[nid, l] = tS[l]
            for l in range(wl):
                WSarr[nid, l] = tWS[l]
            bk[j, bc[j]] = nid
            bc[j] += 1
        if overflow:
            break
    kept = 0
    for j in range(1, n + 1):
        kept += bc[j]
    routes = np.zeros((kcols, maxlen), np.int32)
    rlen = np.zeros(kcols, np.int32)
    for c in range(kcols):
        lab = cand_lab[c]
        if lab < 0:
            continue
        tmp = np.empty(maxlen, np.int32)
        m = 0
        x = lab
        while x >= 0 and node[x] != 0:
            tmp[m] = node[x]
            m += 1
            x = pred[x]
        rlen[c] = m
        for t in range(m):
            routes[c, t] = tmp[m - 1 - t]
    return best, cand_rc, routes, rlen, created, kept, overflow, ncmp, npruned, nheur


MODES = {"window": 0, "nowin": 1, "qv": 2}


@dataclass
class VecInstance:
    """Instance whose route-time profile is a plain vector (SAA scenarios, Wasserstein, mean-CVaR).

    arcS[i, j, :] holds, for the first L0 entries, the arc time under each scenario (service included); the optional
    trailing entries (Wasserstein) are the K sector-time accumulators of the arc.  Weights w sum to one over L0.
    """

    n: int
    tau: np.ndarray  # (n+1, n+1, K) sector base times (only used for ng-neighbourhoods and the Wasserstein term)
    arcS: np.ndarray
    dem: np.ndarray
    cap: float
    w: np.ndarray
    L0: int
    loss: Loss
    wass: float = 0.0
    risk: int = 0
    alpha: float = 0.8
    lam: float = 0.5
    Cmin: np.ndarray = field(init=False)
    wsuf: np.ndarray = field(init=False)

    def __post_init__(self):
        c0 = self.arcS[:, :, :self.L0].mean(-1).copy()
        np.fill_diagonal(c0, np.inf)
        dist = c0[:, 0].copy()
        dist[0] = 0.0
        for _ in range(self.n + 1):
            dist = np.minimum(dist, np.min(c0 + dist[None, :], axis=1))
            dist[0] = 0.0
        self.Cmin = dist
        self.wsuf = np.zeros(self.arcS.shape[2] + 1)

    # -- exact route cost (numpy), consistent with the kernel
    def profile(self, route):
        p = (0, *route, 0)
        return sum(self.arcS[p[t], p[t + 1]] for t in range(len(p) - 1))

    def route_cost(self, route) -> float:
        S = self.profile(route)
        ls = self.loss
        T = S[: self.L0]
        phi = ls.gamma * T + ls.rho * np.maximum(T - ls.Tmax, 0.0)
        if self.risk == 0:
            c = ls.fixed + float(self.w[: self.L0] @ phi)
            if self.wass > 0:
                c += self.wass * float(S[self.L0:].max())
            return c
        srt = np.sort(phi)
        k = (1 - self.alpha) * self.L0
        full = int(np.floor(k + 1e-12))
        acc = float(srt[self.L0 - full:].sum()) if full > 0 else 0.0
        rem = k - full
        if rem > 1e-12 and full < self.L0:
            acc += rem * float(srt[self.L0 - 1 - full])
        return ls.fixed + (1 - self.lam) * float(phi.mean()) + self.lam * acc / k


def _tie(inst) -> float:
    ls = inst.loss
    if getattr(inst, "risk", 0) == 1:
        return (1.0 - inst.lam) * ls.gamma
    return ls.gamma


def sp_levels(inst, allow: np.ndarray | None = None) -> np.ndarray:
    """spl[j, l]: shortest j -> depot time under the level-l (or scenario-l) arc times (arcs `allow`ed)."""
    n = inst.n
    L0 = getattr(inst, "L0", inst.arcS.shape[2])
    A = inst.arcS[:, :, :L0].copy()
    if allow is not None:
        A = np.where(allow[:, :, None], A, np.inf)
    idx = np.arange(n + 1)
    A[idx, idx, :] = np.inf
    dist = A[:, 0, :].copy()
    dist[0] = 0.0
    for _ in range(n + 1):
        new = np.minimum(dist, np.min(A + dist[None, :, :], axis=1))
        new[0] = 0.0
        if np.allclose(new, dist):
            break
        dist = new
    return np.where(np.isfinite(dist), dist, 1e15)


def price(inst, duals: np.ndarray, *, mode: str = "window", ng: np.ndarray | None = None, max_cols: int = 40,
          maxlab: int = 300_000, bcap: int = 50_000, tol_rc: float = 1e-9, allow: np.ndarray | None = None, Cmin: np.ndarray | None = None,
          fixed_shift: float = 0.0, bcap_h: int = 0, lbprune: bool = False, spl: np.ndarray | None = None,
          max_created: int = 2_000_000_000, max_cmp: int = 2_000_000_000):
    """Pricing with the variant kernel.  Returns (best rc, [(rc, route)], stats).

    `inst` is a `brl.RoutingInstance` (modes window / nowin / qv) or a `VecInstance` (mode qv only)."""
    n = inst.n
    L = inst.arcS.shape[2]
    L0 = getattr(inst, "L0", L)
    if ng is None:
        ng = ng_masks_py(inst, n)
    ng_lo = np.array([int(x) & _M64 for x in ng], np.uint64)
    ng_hi = np.array([int(x) >> 64 for x in ng], np.uint64)
    ls = inst.loss
    if allow is None:
        allow = np.ones((n + 1, n + 1), np.bool_)
    if Cmin is None:
        Cmin = inst.Cmin
    dem = inst.dem.astype(np.float64)
    duals = np.asarray(duals, float)
    rmax = 0.0
    if lbprune:
        pos = np.maximum(duals[1:], 0.0) / np.maximum(dem[1:], 1e-12)
        rmax = float(pos.max()) if n else 0.0
        if spl is None:
            spl = sp_levels(inst, allow)
    else:
        spl = np.zeros((n + 1, L0))
    pdem = dem[1:][dem[1:] > 0]
    maxlen = int(min(float(inst.cap) / float(pdem.min()) + 2, 4 * n + 4)) if len(pdem) else n + 2
    t0 = time.perf_counter()
    out = _kernel(n, L, L0, inst.arcS, dem, float(inst.cap), np.asarray(inst.w, float), inst.wsuf, ls.gamma, ls.rho,
                  ls.Tmax, ls.fixed + fixed_shift, np.asarray(Cmin, float), ng_lo, ng_hi, duals, maxlab, bcap,
                  max_cols, tol_rc, np.asarray(allow, np.bool_), MODES[mode], _tie(inst), float(getattr(inst, "wass", 0.0)),
                  int(getattr(inst, "risk", 0)), float(getattr(inst, "alpha", 0.8)), float(getattr(inst, "lam", 0.5)),
                  int(bcap_h), bool(lbprune), np.asarray(spl, float), rmax, int(max_created), int(max_cmp), maxlen)
    best, crc, rts, rl, created, kept, overflow, ncmp, npruned, nheur = out
    res = []
    for c in np.argsort(crc):
        if rl[c] > 0 and crc[c] < 1e299:
            res.append((float(crc[c]), tuple(int(v) for v in rts[c, : rl[c]])))
    return float(best), res, {"time": time.perf_counter() - t0, "created": int(created), "kept": int(kept),
                              "overflow": bool(overflow), "ncmp": int(ncmp), "pruned": int(npruned),
                              "heur_drops": int(nheur)}


def vec_instance_saa(inst, scen: np.ndarray, *, wass_eps: float = 0.0, risk: int = 0, alpha: float = 0.8,
                     lam: float = 0.5) -> VecInstance:
    """SAA instance on the training days `scen` (S, K); `wass_eps > 0` adds the type-1 Wasserstein closed form of
    `ccu.robust` (eps*(gamma+rho)*max_k tau_k, tau_k = route base time of sector k, service excluded); `risk=1` mean-CVaR."""
    S = scen.shape[0]
    arc = np.einsum("ijk,sk->ijs", inst.tau, scen) + inst.svc[None, :, None]
    ls = inst.loss
    wass = 0.0
    if wass_eps > 0:
        arc = np.concatenate([arc, inst.tau], axis=2)
        wass = wass_eps * (ls.gamma + ls.rho)
    w = np.concatenate([np.full(S, 1.0 / S), np.zeros(arc.shape[2] - S)])
    return VecInstance(inst.n, inst.tau, arc, inst.dem, inst.cap, w, S, ls, wass, risk, alpha, lam)


# ---------------------------------------------------------------------------------------------------------------
# column generation at the root (devices: DSSR-style ng growth, heuristic-first pricing, completion bound)
# and a branch-and-price whose pricing is the variant kernel
# ---------------------------------------------------------------------------------------------------------------


def cycle_augment(ng: np.ndarray, route) -> bool:
    """Enlarge the ng-sets along the first cycle of `route` (same rule as `BranchAndPrice._augment`).  In place."""
    pos = {}
    changed = False
    for t, j in enumerate(route):
        if j in pos:
            for q in range(pos[j] + 1, t):
                v = route[q]
                if not (int(ng[v]) >> j) & 1:
                    ng[v] = int(ng[v]) | (1 << j)
                    changed = True
            break
        pos[j] = t
    return changed


def is_elementary(route) -> bool:
    return len(set(route)) == len(route)


def price_dssr(inst, duals, ng, *, max_rounds: int = 60, **kw):
    """Exact pricing for ELEMENTARY routes by DSSR-style growth of the ng-sets (`ng` is enlarged in place).

    Price with the current ng-sets; while the cheapest route found is not elementary, enlarge the ng-sets along its
    cycle and price again.  When the cheapest route is elementary it is optimal for the elementary problem, since the
    ng-routes contain all elementary routes.  Returns (best rc, [(rc, route)] elementary only, stats incl. rounds)."""
    tot = {"time": 0.0, "created": 0, "kept": 0, "overflow": False, "ncmp": 0, "pruned": 0, "heur_drops": 0, "rounds": 0}
    for rnd in range(max_rounds):
        best, cols, st = price(inst, duals, ng=ng, **kw)
        for k in ("time", "created", "ncmp", "pruned", "heur_drops"):
            tot[k] += st[k]
        tot["kept"] = max(tot["kept"], st["kept"])
        tot["overflow"] = tot["overflow"] or st["overflow"]
        tot["rounds"] += 1
        if not cols or is_elementary(cols[0][1]) or st["overflow"]:
            break
        if not cycle_augment(ng, cols[0][1]):
            break
    elem = [(rc, r) for rc, r in cols if is_elementary(r)]
    tot["elementary_exact"] = bool(not cols or is_elementary(cols[0][1])) and not tot["overflow"]
    return best, elem, tot


def root_cg(inst, *, mode: str = "window", ng_size: int = 8, dssr: bool = False, heur_first: int = 0,
            lbprune: bool = False, time_limit: float = 300.0, max_iter: int = 2000, max_cols: int = 60,
            maxlab: int = 300_000, max_created: int = 400_000_000, max_cmp: int = 4_000_000_000, tol: float = 1e-6,
            init_cols: dict | None = None, log=None):
    """Column generation for the set-partitioning LP (every customer once).  Returns a dict with the LP value, a valid
    lower bound `lb` (Lagrangian, valid only if `exact_pricing`), the final duals, times, label counts, columns.

    `heur_first > 0`: price first with at most that many labels per node (heuristic); the exact pricing runs only when
    the heuristic finds no column.  `dssr`: elementary pricing with ng growth from `ng_size` (see `price_dssr`)."""
    from scipy.optimize import linprog

    n = inst.n
    ng = ng_masks_py(inst, ng_size)
    cols = {(j,): inst.route_cost((j,)) for j in range(1, n + 1)}
    if init_cols:
        cols.update(init_cols)
    t0 = time.perf_counter()
    spl = sp_levels(inst) if lbprune else None
    tprice = theur = 0.0
    nex = nhe = 0
    maxkept = 0
    created = ncmp = 0
    overflow = False
    exact_final = False
    z = lb = float("nan")
    duals = np.zeros(n + 1)
    status = "time_limit"
    it = 0
    for it in range(1, max_iter + 1):
        routes = list(cols)
        A = np.zeros((n, len(routes)))
        for k, r in enumerate(routes):
            for j in r:
                A[j - 1, k] += 1.0
        c = np.array([cols[r] for r in routes])
        res = linprog(c, A_eq=A, b_eq=np.ones(n), bounds=(0, None), method="highs")
        z = float(res.fun)
        y = res.eqlin.marginals
        duals = np.concatenate([[0.0], y])
        kw = dict(mode=mode, max_cols=max_cols, maxlab=maxlab, max_created=max_created, max_cmp=max_cmp)
        new = []
        if heur_first > 0:
            b, cand, st = price(inst, duals, ng=ng, bcap_h=heur_first, **kw)
            theur += st["time"]
            nhe += 1
            tprice += st["time"]
            created += st["created"]
            new = [(rc, r) for rc, r in cand if r not in cols and rc < -tol * (1 + abs(z)) and (is_elementary(r) or not dssr)]
        exact_call = not new
        if exact_call:
            if dssr:
                best, cand, st = price_dssr(inst, duals, ng, lbprune=lbprune, spl=spl, **kw)
            else:
                best, cand, st = price(inst, duals, ng=ng, lbprune=lbprune, spl=spl, **kw)
            nex += 1
            tprice += st["time"]
            created += st["created"]
            ncmp += st["ncmp"]
            maxkept = max(maxkept, st["kept"])
            overflow = overflow or st["overflow"]
            new = [(rc, r) for rc, r in cand if r not in cols and rc < -tol * (1 + abs(z))]
            lb = z + n * min(best, 0.0)
            if best > -tol * (1 + abs(z)) or not new:
                exact_final = not st["overflow"]
                status = "converged" if exact_final else "label_overflow"
                break
        for rc, r in new:
            cols[r] = inst.route_cost(r)
        if log and it % 10 == 0:
            log(f"  cg it {it} z {z:.4f} cols {len(cols)} t {time.perf_counter() - t0:.0f}s")
        if time.perf_counter() - t0 > time_limit:
            status = "time_limit"
            break
    wall = time.perf_counter() - t0
    return dict(status=status, lp=z, lb=lb if exact_final else float("nan"), exact_pricing=bool(exact_final), iters=it,
                cols=len(cols), time=wall, price_time=tprice, heur_time=theur, n_exact=nex, n_heur=nhe, max_kept=maxkept,
                created=created, ncmp=ncmp, overflow=bool(overflow), duals=duals.tolist(), ng_final=float(np.mean(
                    [bin(int(x)).count("1") for x in ng[1:]])))


from . import bp as _bp  # noqa: E402


class VBP(_bp.BranchAndPrice):
    """Branch-and-price with the variant pricing kernel (python-int ng masks, any n <= 127).

    mode: 'window' (BRL, p-box worst case), or 'qv' for `VecInstance` (SAA, Wasserstein, mean-CVaR, deterministic).
    heur_first: bucket cap of an initial heuristic pricing call (0 = off); exact pricing only runs when it finds nothing
    (the Lagrangian bound is never taken from a heuristic call).  lbprune: completion bound in the exact call."""

    def __init__(self, inst, kappa=None, *, mode: str = "window", ng_size: int = 8, heur_first: int = 0,
                 lbprune: bool = False, maxlab: int = 300_000, max_created: int = 400_000_000,
                 max_cmp: int = 4_000_000_000, **kw):
        kw.setdefault("augment_ng", True)
        super().__init__(inst, kappa, ng=np.zeros(inst.n + 1, np.uint64), **kw)
        self.ng = ng_masks_py(inst, ng_size)
        self.mode, self.heur_first, self.lbprune = mode, heur_first, lbprune
        self.maxlab, self.max_created, self.max_cmp = maxlab, max_created, max_cmp
        self.t_heur = 0.0
        self.n_heur = 0
        self.n_exact = 0
        self.created = 0
        self.ncmp = 0
        self.cmp_rate = 2e6  # dominance comparisons per second (running estimate; sizes the per-call cap)
        self._deadline = float("inf")

    def run(self, *, time_limit: float = 600.0, **kw):
        self._deadline = time.perf_counter() + time_limit
        return super().run(time_limit=time_limit, **kw)

    def _cap(self) -> int:
        rem = self._deadline - time.perf_counter()
        return int(min(self.max_cmp, max(2e5, self.cmp_rate * max(rem, 0.0) * 0.8)))

    def _augment(self, r) -> bool:
        changed = cycle_augment(self.ng, r)
        if changed:
            for k, rr in enumerate(self.R):
                if not self.dead[k] and not self.ng_feasible(rr):
                    self.dead[k] = True
            self.ng_aug += 1
        return changed

    def _price(self, node, duals, Cmin, shift=0.0):
        kw = dict(mode=self.mode, ng=self.ng, max_cols=self.max_cols, allow=node.allow, Cmin=Cmin, fixed_shift=shift,
                  maxlab=self.maxlab, max_created=self.max_created, max_cmp=self._cap())
        if self.heur_first > 0:
            b, cand, st = price(self.inst, duals, bcap_h=self.heur_first, **kw)
            self.t_heur += st["time"]
            self.ptime += st["time"]
            self.n_heur += 1
            self.n_pricing += 1
            new = [(rc, r) for rc, r in cand if r not in self.index and rc < -1e-9]
            if new:
                return -1e18, new  # not a certificate: the node bound is not updated from this call
        b, new, st = price(self.inst, duals, lbprune=self.lbprune, **kw)
        self.n_pricing += 1
        self.n_exact += 1
        self.ptime += st["time"]
        self.created += st["created"]
        self.ncmp += st["ncmp"]
        if st["time"] > 0.2 and st["ncmp"] > 1000 and not st["overflow"]:
            self.cmp_rate = 0.5 * self.cmp_rate + 0.5 * st["ncmp"] / st["time"]
        self.max_labels = max(self.max_labels, st["kept"])
        if st["overflow"]:
            self.bound_valid = False
        return b, new


def solve_variant(inst, *, mode: str = "window", time_limit: float = 120.0, ng_size: int = 8, heur_first: int = 0,
                  lbprune: bool = False, node_limit: int = 100000, mip_time: float = 10.0, **kw):
    """Partition branch-and-price with `VBP`; if the time limit hits before any incumbent exists, the MILP over the
    generated columns (the singletons make it feasible) supplies an incumbent.  Returns (BPResult, VBP)."""
    import math
    b = VBP(inst, None, partition=True, mode=mode, ng_size=ng_size, heur_first=heur_first, lbprune=lbprune,
            mip_time=mip_time, **kw)
    r = b.run(time_limit=time_limit, node_limit=node_limit)
    if not math.isfinite(r.value):  # no incumbent: bp.run's gap test is meaningless with UB = inf
        b._milp(mip_time)
        r.value, r.routes = b.UB, list(b.best_routes)
        r.status = "time_limit" if r.status == "optimal" else r.status
    return r, b
