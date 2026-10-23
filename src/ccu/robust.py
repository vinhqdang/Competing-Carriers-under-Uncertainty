"""Route loss and Wasserstein-robust route cost (closed form, DESIGN.md Section 2)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class LossParams:
    """Route loss f + gamma*T + rho*max(0, T - T_max)."""

    f: float
    gamma: float
    rho: float
    T_max: float


def route_loss_stats(
    tau: np.ndarray, params: LossParams, samples: np.ndarray, eps: float
) -> tuple[np.ndarray, np.ndarray]:
    """Return (empirical expected loss, robust loss) for route(s) with base times tau.

    tau has shape (K,) or (R, K); samples has shape (S, K). The robust loss adds
    eps * (gamma + rho) * max_k tau_k, the type-1 Wasserstein worst case on R^K.
    """
    tau = np.asarray(tau, dtype=float)
    T = tau @ samples.T
    loss = params.f + params.gamma * T + params.rho * np.maximum(0.0, T - params.T_max)
    emp = loss.mean(axis=-1)
    robust = emp + eps * (params.gamma + params.rho) * tau.max(axis=-1)
    return emp, robust


def true_expected_loss(
    tau: np.ndarray, params: LossParams, true_samples: np.ndarray
) -> np.ndarray:
    """Expected route loss under the true travel-time distribution (empirical on true samples)."""
    return route_loss_stats(tau, params, true_samples, 0.0)[0]
