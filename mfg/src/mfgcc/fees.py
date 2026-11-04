"""Lump-sum recovery fees and free entry (zero profit) for the zone-time delivery market.

Fixed number of carriers (Section 'Fixed fees, entry and other externalities' of the paper):
    the per-delivery charge u is posted, every carrier pays in addition a fee T_i that does not depend on its own
    actions.  Carrier i's payoff J_i(y_i; y_-i) - T_i has the same maximisers as J_i, so the Nash equilibrium is
    unchanged as long as every carrier stays in the market (payoff after fee >= outside option).  Three ways to
    raise the deficit D = max(0, -R) of the charge, R = <u, Q>:
        flat     T_i = D / N
        fleet    T_i = D * B_i / sum_j B_j       (licence fee in proportion to licensed vehicle-hours; exogenous)
        profit   T_i = D * pi_i / sum_j pi_j     (benchmark: possible iff sum_i pi_i >= D, the aggregate condition)
    A fee computed from the *realised* deficit, T_i = -<u, Q>/N with Q including carrier i's deliveries, is not
    lump-sum: it rebates u/N per own delivery (see own_rebate_charge and the tests).

Free entry (segment theta has k_theta identical carriers sharing the segment's fleet budget B_theta; k real):
    carriers enter while profit per carrier net of fee exceeds the fixed cost F_theta per day, i.e.
        Pi_theta(k, u) / k_theta - T = F_theta  for every active segment,
    and a segment whose single carrier cannot cover F_theta exits.  Welfare net of fixed costs is
        SW - sum_theta k_theta F_theta = CS + R + N T   (exact under zero profit; tests).
"""
from __future__ import annotations

import numpy as np

from .leader import social_optimum
from .qp import Block, solve
from .stake import decompose, n_active


# ------------------------------------------------------------------ carrier profits
def block_profits(blocks, sol, m, u=None) -> np.ndarray:
    """Profit of each block (all carriers in it) net of the charge: <p,y> - <a, m Q> - <u, a>."""
    u = np.zeros(len(m)) if u is None else u
    return np.array([float(B.p @ y) - float(a @ (m * sol.Q)) - float(u @ a) for B, y, a in zip(blocks, sol.y, sol.a)])


def carrier_profits(blocks, sol, m, u=None) -> np.ndarray:
    """Profit of one carrier of each block (replica blocks: block profit / count)."""
    return block_profits(blocks, sol, m, u) / np.array([B.count for B in blocks], float)


def fee_table(blocks, sol, m, u, pi0=None) -> dict:
    """Fees that recover the deficit of the charge u at the equilibrium sol (fixed number of carriers).

    pi0: per-carrier profit without any charge (for the voluntary-participation test).  Returns, per scheme,
    the fee per carrier (mean over carriers), the share of pre-fee carrier profit it takes, and whether every
    carrier keeps profit >= 0 and >= pi0."""
    cnt = np.array([B.count for B in blocks], float)
    N = cnt.sum()
    pc = carrier_profits(blocks, sol, m, u)
    R = float(u @ sol.Q)
    D = max(0.0, -R)
    Bc = np.array([B.B for B in blocks]) / cnt  # fleet budget per carrier
    tot = float(np.sum(cnt * pc))
    out = dict(R=R, deficit=D, N=N, profit_total=tot, profit_min=float(pc.min()), aggregate_ok=bool(tot >= D))
    schemes = {"flat": np.full(len(blocks), D / N),
               "fleet": D * Bc / float(np.sum(cnt * Bc))}
    if tot > 0:
        schemes["profit"] = D * np.maximum(pc, 0.0) / float(np.sum(cnt * np.maximum(pc, 0.0)))
    for nm, T in schemes.items():
        after = pc - T
        out[f"{nm}_fee"] = float(np.sum(cnt * T) / N)
        out[f"{nm}_share"] = float(np.sum(cnt * T) / tot) if tot > 0 else float("inf")
        out[f"{nm}_min_after"] = float(after.min())
        out[f"{nm}_ok"] = bool(after.min() >= -1e-9 * max(1.0, abs(tot) / N))
        if pi0 is not None:
            out[f"{nm}_vol"] = bool(np.all(after >= pi0 - 1e-9 * max(1.0, abs(tot) / N)))
    return out


def own_rebate_charge(u, N):
    """Effective per-delivery charge when the deficit is recovered ex post as T_i = -<u, Q>/N (Q includes the
    carrier's own deliveries): carrier i receives u/N back per own delivery, so it faces u (1 - 1/N)."""
    return u * (1.0 - 1.0 / N)


# ------------------------------------------------------------------ one-zone closed forms (identical carriers)
def one_zone_free_entry(alpha, b, kappa, F, rule: str):
    """Identical carriers, one zone, slack budget, N real.  Returns dict(N, Q, u, T, SW, CS, R).

    Per carrier at Nash: q = (alpha - u - m Q)/m and profit m q^2 - T.  Rules: none (u = 0), obs (u = kappa Q),
    pm (u = (kappa - m/N) Q^opt), pmfee (pm and T = -u Q / N when u < 0)."""
    m = b + kappa
    s = np.sqrt(F / m)
    Qo = alpha / (m + kappa)
    T = 0.0
    if rule == "none":
        u, Q = 0.0, alpha / m - s
    elif rule == "obs":
        Q = (alpha - m * s) / (m + kappa)
        u = kappa * Q
    elif rule in ("pm", "pmfee"):
        Q = Qo
        N = Qo / s
        u = (kappa - m / N) * Qo
        if rule == "pmfee" and u < 0:
            N = kappa * Qo * Qo / F
            u = (kappa - m / N) * Qo
            T = -u * Qo / N
    else:
        raise ValueError(rule)
    q = s if T == 0.0 else F / (kappa * Qo)
    N = Q / q
    SW = alpha * Q - 0.5 * b * Q * Q - kappa * Q * Q - N * F
    return dict(N=N, Q=Q, u=u, T=T, SW=SW, CS=0.5 * b * Q * Q, R=u * Q + N * T)


# ------------------------------------------------------------------ free entry on city instances
def _with_counts(g, ks, active):
    out = []
    for th, Bd in enumerate(g.base):
        if active[th]:
            out.append(Block(Bd["rev"] - Bd["cost"], Bd["L"], Bd["w"], Bd["B"], count=float(ks[th]), tag=f"t{th}"))
    return out


def calibrate_F(g, k0: int) -> np.ndarray:
    """Fixed cost per carrier and day, per segment, such that the no-charge free-entry equilibrium has between k0
    and k0 + 1 carriers per segment: F = geometric mean of the profit per carrier at k0 and at k0 + 1 (u = 0).
    With continuous k the free-entry count then lies in (k0, k0 + 1) and its integer part is k0."""
    p = []
    for k in (k0, k0 + 1):
        bl = g.blocks(k)
        sol = solve(bl, g.m, own=True)
        p.append(carrier_profits(bl, sol, g.m))
    return np.sqrt(p[0] * p[1])


def free_entry(g, F, rule: str, *, theta: float = 1.0, k_init=None, tol: float = 1e-6, max_outer: int = 300,
               damp: float = 0.8, pm_rounds: int = 3, verbose=False) -> dict:
    """Free-entry equilibrium of the city instance g with per-segment fixed costs F (array) under a charge rule.

    rule: 'none' (u = 0); 'obs' (observation-only fixed point u = theta kappa Q(u), Nash carriers; theta = 1 is the
    paper's rule); 'pm' (Pigou minus market power, matching the social-optimum aggregate of the active segments);
    'pmfee' (pm plus a lump-sum licence fee that recovers the deficit: each segment repays the net subsidy
    max(0, -<u, a_theta>) it receives at the target, split equally among its carriers; the fee is fixed before
    carriers act, so it does not change their marginal incentives).  Counts are real and at least one per
    active segment; a segment whose single carrier cannot cover F_theta exits (it may be the whole market).
    Returns the equilibrium, the charge, the counts and the welfare terms."""
    m, kap, b = g.m, g.kappa, g.b
    nT = len(g.base)
    ks = np.full(nT, 1.0) if k_init is None else np.array(k_init, float)
    active = np.ones(nT, bool)
    low = np.zeros(nT, int)
    so = None
    u = None
    Tc = np.zeros(nT)
    err, resid, it, sol = np.inf, 0.0, 0, None
    for it in range(max_outer):
        if not active.any():
            break
        bl = _with_counts(g, ks, active)
        if rule in ("pm", "pmfee") and so is None:
            so = social_optimum(_with_counts(g, np.ones(nT), active), m, kap)  # independent of the counts
        if rule == "none":
            u = np.zeros(g.d)
            sol = solve(bl, m, own=True)
        elif rule == "obs":
            sol = solve(bl, m, mc=m + theta * kap, own=True)
            u = theta * kap * sol.Q
            sol = solve(bl, m, own=True, u=u)
        else:
            nact = np.maximum(n_active(bl, so), 1.0)
            if u is None:
                u = kap * so.Q - m * so.Q / nact
            for _ in range(pm_rounds):
                sol = solve(bl, m, own=True, u=u)
                u = u + 0.8 * m * (1.0 + 1.0 / nact) * (sol.Q - so.Q)
            sol = solve(bl, m, own=True, u=u)
            resid = float(np.sqrt(np.sum(m * (sol.Q - so.Q) ** 2) / np.sum(m * so.Q ** 2)))
        R = float(u @ sol.Q)
        Tc = np.zeros(nT)
        if rule == "pmfee":  # each segment repays the subsidy it receives (an ex-ante licence fee at the target)
            sub = np.array([max(0.0, -float(u @ a)) for a in sol.a])
            Tc[active] = sub / ks[active]
        pc = np.zeros(nT)
        pc[active] = carrier_profits(bl, sol, m, u) - Tc[active]
        r = np.ones(nT)
        r[active] = pc[active] / F[active]
        err = float(np.max(np.abs(r[active] - 1.0)))
        if verbose:
            print(it, rule, np.round(np.where(active, ks, 0), 3), f"err={err:.2e}", f"resid={resid:.1e}")
        if err < tol and resid < 1e-6:
            break
        for th in np.where(active)[0]:
            kn = 0.0 if r[th] <= 0 else (ks[th] + 1.0) * r[th] ** (0.5 * damp) - 1.0
            if kn < 1.0:
                kn = 1.0
                low[th] = low[th] + 1 if (r[th] < 1.0 and ks[th] <= 1.0 + 1e-12) else 0
            else:
                low[th] = 0
            ks[th] = kn
        # one carrier cannot cover F (for 3 rounds): the least viable such segment exits, one at a time
        cand = np.where(active & (low >= 3))[0]
        if len(cand):
            th = cand[np.argmin(r[cand])]
            active[th] = False
            low[:] = 0
            so, u = None, None
    if not active.any():  # the market closes
        return dict(rule=rule, theta=theta, k=np.zeros(nT), N=0.0, active=0, u=None, sol=None, T=0.0, fixed=0.0,
                    SW_gross=0.0, SW=0.0, CS=0.0, R=0.0, fee_rev=0.0, CC=0.0, Pi=0.0, err=0.0, iters=it + 1,
                    resid=float("nan"), neg_share=float("nan"), Q_total=0.0, fee_share=float("nan"))
    bl = _with_counts(g, ks, active)
    dec = decompose(bl, sol, b, kap, u)
    N = float(np.sum(ks[active]))
    fixed = float(np.sum(ks[active] * F[active]))
    fee_rev = float(np.sum(ks[active] * Tc[active]))
    return dict(rule=rule, theta=theta, k=np.where(active, ks, 0.0), N=N, active=int(active.sum()), u=u, sol=sol,
                T=fee_rev / N, fixed=fixed, SW_gross=dec["SW"], SW=dec["SW"] - fixed, CS=dec["CS"], R=dec["R"],
                fee_rev=fee_rev, CC=dec["CC"], Pi=dec["Pi"] - fee_rev, err=err, iters=it + 1, resid=resid,
                neg_share=float(np.mean(u < -1e-12)), Q_total=float(sol.Q.sum()),
                fee_share=fee_rev / (dec["Pi"]) if dec["Pi"] > 0 else float("nan"))


def planner_scale(g, F, ks, lambdas, u=None):
    """Welfare net of fixed costs when the counts are scaled by lambda (>= 1 carrier per segment), no change in
    conduct: the Mankiw-Whinston test of excess entry.  Returns list of (lambda, SW net)."""
    out = []
    m, kap, b = g.m, g.kappa, g.b
    for lam in lambdas:
        k = np.maximum(lam * np.asarray(ks, float), 1.0)
        bl = _with_counts(g, k, np.asarray(ks) > 0)
        sol = solve(bl, m, own=True, u=u)
        dec = decompose(bl, sol, b, kap, u)
        out.append((lam, dec["SW"] - float(np.sum(k[np.asarray(ks) > 0] * F[np.asarray(ks) > 0]))))
    return out
