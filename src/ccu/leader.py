"""City (leader) side: Pigouvian price, posted-price search and price sweeps."""
from __future__ import annotations

import numpy as np

from .carrier import Plan
from .game import best_response_dynamics, exploitability, social_cost, total_load
from .instance import Instance


def pigouvian_price(inst: Instance, profile: list[Plan]) -> np.ndarray:
    """Pigouvian hub prices p_z = beta_z / C_z * L_z."""
    return inst.beta / inst.C * total_load(profile, inst.Z)


def optimise_price(
    inst: Instance,
    rng: np.random.Generator,
    p_max: float,
    grid_points: int = 5,
    passes: int = 2,
    starts: int = 4,
) -> dict[str, object]:
    """Coordinate grid search over per-hub prices in [0, p_max], each evaluated at a warm-started NE.

    Each pass halves the search window around the incumbent price of every hub.
    Returns a dict with keys p, profile, sc and evals.
    """
    Z = inst.Z
    p = np.full(Z, p_max / 2)
    profile, _, _ = best_response_dynamics(inst, p, rng, starts=starts)
    sc = social_cost(inst, profile)
    evals = 1
    half = p_max / 2
    for _ in range(passes):
        for z in range(Z):
            for v in np.linspace(max(0.0, p[z] - half), min(p_max, p[z] + half), grid_points):
                q = p.copy()
                q[z] = v
                prof, _, _ = best_response_dynamics(inst, q, rng, init=profile, starts=starts)
                evals += 1
                s = social_cost(inst, prof)
                if s < sc - 1e-12:
                    p, profile, sc = q, prof, s
        half /= 2
    return {"p": p, "profile": profile, "sc": sc, "evals": evals}


def price_curve(
    inst: Instance,
    rng: np.random.Generator,
    prices: np.ndarray,
    starts: int = 4,
    expl_starts: int = 16,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Sweep a uniform price over all hubs, warm-starting along the grid.

    Returns arrays (p, social cost, total hub load, exploitability) of the reached equilibria.
    """
    sc, load, expl = [], [], []
    profile = None
    for p in prices:
        price = np.full(inst.Z, float(p))
        profile, _, _ = best_response_dynamics(inst, price, rng, init=profile, starts=starts)
        sc.append(social_cost(inst, profile))
        load.append(float(total_load(profile, inst.Z).sum()))
        expl.append(exploitability(inst, profile, price, rng, starts=expl_starts))
    return np.asarray(prices, float), np.asarray(sc), np.asarray(load), np.asarray(expl)
