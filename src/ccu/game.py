"""Follower game: best-response dynamics, exploitability, social cost and benchmarks."""
from __future__ import annotations

import numpy as np

from .carrier import (
    TOL,
    Plan,
    as_price,
    best_response,
    diversion_total,
    make_plan,
    plan_cost_J,
    plan_cost_SC,
)
from .instance import Instance


def others_load(profile: list[Plan], i: int, Z: int) -> np.ndarray:
    """Hub loads of all carriers except i."""
    L = np.zeros(Z)
    for k, pl in enumerate(profile):
        if k != i:
            L += pl.usage
    return L


def total_load(profile: list[Plan], Z: int) -> np.ndarray:
    """Hub loads L_z summed over carriers."""
    L = np.zeros(Z)
    for pl in profile:
        L += pl.usage
    return L


def potential(inst: Instance, profile: list[Plan], p: float | np.ndarray) -> float:
    """Exact potential Phi(pi) of DESIGN.md Section 3."""
    price = as_price(inst, p)
    L = total_load(profile, inst.Z)
    val = 0.0
    sq = np.zeros(inst.Z)
    for i, pl in enumerate(profile):
        val += pl.base_cost + diversion_total(inst, i, pl.diverted) + float(price @ pl.usage)
        sq += pl.usage**2
    val += float(np.sum(inst.beta / (2 * inst.C) * (L**2 + sq)))
    return val


def random_profile(inst: Instance, rng: np.random.Generator) -> list[Plan]:
    """Random diversion masks for all carriers (robust plans)."""
    profile = []
    for i in range(inst.N):
        n = len(inst.customers[i])
        mask = rng.random(n) < rng.uniform(0.1, 0.5)
        profile.append(make_plan(inst, i, np.flatnonzero(mask), "robust", rng))
    return profile


def doorstep_profile(inst: Instance, rng: np.random.Generator) -> list[Plan]:
    """All parcels delivered to the doorstep."""
    return [make_plan(inst, i, frozenset(), "robust", rng) for i in range(inst.N)]


def best_response_dynamics(
    inst: Instance,
    p: float | np.ndarray,
    rng: np.random.Generator,
    max_iter: int = 50,
    init: list[Plan] | None = None,
    starts: int = 4,
    tol: float = TOL,
) -> tuple[list[Plan], list[float], bool]:
    """Round-robin best responses; a carrier switches only if its J_i drops by more than tol.

    Returns (profile, potential history, converged). Converged means a full round had no change.
    """
    price = as_price(inst, p)
    profile = list(init) if init is not None else doorstep_profile(inst, rng)
    history = [potential(inst, profile, price)]
    for _ in range(max_iter):
        changed = False
        for i in range(inst.N):
            Lo = others_load(profile, i, inst.Z)
            cur = plan_cost_J(inst, i, profile[i], Lo, price)
            cand = best_response(inst, i, Lo, price, rng, starts=starts, init=profile[i])
            if plan_cost_J(inst, i, cand, Lo, price) < cur - tol:
                profile[i] = cand
                changed = True
        history.append(potential(inst, profile, price))
        if not changed:
            return profile, history, True
    return profile, history, False


def exploitability(
    inst: Instance,
    profile: list[Plan],
    p: float | np.ndarray,
    rng: np.random.Generator,
    starts: int = 16,
) -> float:
    """NashConv: sum_i [J_i(pi) - min over the oracle's best response (and pi_i)]; >= 0."""
    price = as_price(inst, p)
    total = 0.0
    for i in range(inst.N):
        Lo = others_load(profile, i, inst.Z)
        cur = plan_cost_J(inst, i, profile[i], Lo, price)
        br = best_response(inst, i, Lo, price, rng, starts=starts)
        total += cur - min(cur, plan_cost_J(inst, i, br, Lo, price))
    return float(total)


def social_cost(inst: Instance, profile: list[Plan]) -> float:
    """SC(pi): true routing and diversion costs, hub congestion sum_z beta/C L^2, phi * vehicle time."""
    L = total_load(profile, inst.Z)
    val = sum(
        pl.true_cost + diversion_total(inst, i, pl.diverted) + inst.phi * pl.vehicle_time
        for i, pl in enumerate(profile)
    )
    return float(val + np.sum(inst.beta / inst.C * L**2))


def centralized_optimum(
    inst: Instance,
    rng: np.random.Generator,
    starts: int = 3,
    inner_starts: int = 2,
    max_sweeps: int = 50,
) -> tuple[list[Plan], float]:
    """Potential descent on SC over joint plans from several starts. Returns (profile, SC)."""
    best_profile, best_sc = None, np.inf
    for s in range(starts):
        profile = doorstep_profile(inst, rng) if s == 0 else random_profile(inst, rng)
        for _ in range(max_sweeps):
            changed = False
            for i in range(inst.N):
                Lo = others_load(profile, i, inst.Z)
                cur = plan_cost_SC(inst, i, profile[i], Lo)
                cand = best_response(inst, i, Lo, 0.0, rng, starts=inner_starts, kind="SC", init=profile[i])
                if plan_cost_SC(inst, i, cand, Lo) < cur - TOL:
                    profile[i] = cand
                    changed = True
            if not changed:
                break
        sc = social_cost(inst, profile)
        if sc < best_sc:
            best_profile, best_sc = profile, sc
    assert best_profile is not None
    return best_profile, best_sc


def stand_alone_cost(inst: Instance, i: int, rng: np.random.Generator, starts: int = 3) -> float:
    """Cost of carrier i alone: no other carriers' congestion, no price."""
    zero = np.zeros(inst.Z)
    plan = best_response(inst, i, zero, 0.0, rng, starts=starts)
    return plan_cost_J(inst, i, plan, zero, zero)


def gini(values: np.ndarray) -> float:
    """Gini coefficient of non-negative values."""
    x = np.asarray(values, dtype=float)
    if x.size == 0 or x.mean() <= 0:
        return 0.0
    return float(np.abs(x[:, None] - x[None]).sum() / (2 * x.size**2 * x.mean()))


def carrier_costs(inst: Instance, profile: list[Plan], p: float | np.ndarray) -> np.ndarray:
    """Realised J_i of each carrier in a profile."""
    price = as_price(inst, p)
    return np.array(
        [plan_cost_J(inst, i, pl, others_load(profile, i, inst.Z), price) for i, pl in enumerate(profile)]
    )


def poa_pos(
    inst: Instance,
    rng: np.random.Generator,
    p: float | np.ndarray = 0.0,
    n_ne: int = 4,
    starts: int = 4,
) -> dict[str, object]:
    """Price of anarchy and stability from equilibria reached by dynamics from random starts."""
    _, sc_opt = centralized_optimum(inst, rng)
    sc_ne = []
    for r in range(n_ne):
        init = None if r == 0 else random_profile(inst, rng)
        prof, _, _ = best_response_dynamics(inst, p, rng, init=init, starts=starts)
        sc_ne.append(social_cost(inst, prof))
    return {
        "sc_opt": sc_opt,
        "sc_ne": sc_ne,
        "poa": max(sc_ne) / sc_opt,
        "pos": min(sc_ne) / sc_opt,
    }
