"""Synthetic city instances: geometry, sectors, hubs, demand and travel-time samples."""
from __future__ import annotations

from dataclasses import dataclass, field
from math import isqrt

import numpy as np

from .robust import LossParams


@dataclass(eq=False)
class Instance:
    """Multi-carrier last-mile instance (DESIGN.md Section 2)."""

    N: int
    K: int
    Z: int
    depots: np.ndarray  # (N, 2)
    customers: list[np.ndarray]  # N x (n_i, 2)
    hubs: np.ndarray  # (Z, 2)
    C: np.ndarray  # (Z,) hub capacity scale
    beta: np.ndarray  # (Z,) congestion coefficient
    zone_of: list[np.ndarray]  # N x (n_i,) nearest hub index
    Q: int  # vehicle capacity (parcels)
    T_max: float  # shift length
    f: float
    gamma: float
    rho: float
    eta: float
    theta: float
    phi: float
    speed: float  # time per unit distance
    service: float  # service time per stop
    samples: np.ndarray  # (N, S, K) carrier data samples
    true_samples: np.ndarray  # (S_true, K) fresh draws from the true law
    eps: np.ndarray  # (N,) ambiguity radii
    _cache: dict = field(default_factory=dict, repr=False)

    def loss(self) -> LossParams:
        """Route loss parameters."""
        return LossParams(self.f, self.gamma, self.rho, self.T_max)

    def diversion_cost(self, i: int) -> np.ndarray:
        """Per-customer diversion cost a_ij = eta*dist(depot, hub) + theta*dist(j, hub)."""
        key = ("a", i)
        if key not in self._cache:
            h = self.hubs[self.zone_of[i]]
            d_dep = np.linalg.norm(h - self.depots[i], axis=1)
            d_cus = np.linalg.norm(self.customers[i] - h, axis=1)
            self._cache[key] = self.eta * d_dep + self.theta * d_cus
        return self._cache[key]


def sector_index(K: int, pts: np.ndarray) -> np.ndarray:
    """Quadrant-grid sector id (row-major) of points in the unit square."""
    s = isqrt(K)
    g = np.clip((np.asarray(pts) * s).astype(int), 0, s - 1)
    return g[..., 0] * s + g[..., 1]


def arc_time_tensor(inst: Instance, xy: np.ndarray) -> np.ndarray:
    """(n, n, K) base time of every arc between points xy, split to the midpoint's sector."""
    mid = (xy[:, None] + xy[None]) / 2
    length = np.linalg.norm(xy[:, None] - xy[None], axis=-1) * inst.speed
    return np.eye(inst.K)[sector_index(inst.K, mid)] * length[..., None]


def arc_sector_time(inst: Instance, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Base time of arc a -> b as a K-vector, all mass in the sector of the midpoint."""
    return arc_time_tensor(inst, np.vstack([a, b]))[0, 1]


def tau_of_route(inst: Instance, depot: np.ndarray, stops: np.ndarray) -> np.ndarray:
    """Base time per sector of the tour depot -> stops -> depot, service charged to each stop's sector."""
    stops = np.asarray(stops, dtype=float).reshape(-1, 2)
    path = np.vstack([depot, stops, depot])
    mid = (path[:-1] + path[1:]) / 2
    length = np.linalg.norm(path[1:] - path[:-1], axis=1) * inst.speed
    tau = np.bincount(sector_index(inst.K, mid), weights=length, minlength=inst.K)
    svc = np.bincount(sector_index(inst.K, stops), minlength=inst.K)
    return tau + inst.service * svc


def _nn_tour_length(depot: np.ndarray, pts: np.ndarray) -> float:
    """Length of a nearest-neighbour tour from the depot through pts and back."""
    cur, rem, total = depot, list(range(len(pts))), 0.0
    while rem:
        d = np.linalg.norm(pts[rem] - cur, axis=1)
        k = int(np.argmin(d))
        total += float(d[k])
        cur = pts[rem.pop(k)]
    return total + float(np.linalg.norm(cur - depot))


def _draw_xi(rng: np.random.Generator, n: int, K: int, sc: float, ss: float) -> np.ndarray:
    """Lognormal sector multipliers with mean one: common shock plus sector noise."""
    g = rng.standard_normal((n, 1))
    e = rng.standard_normal((n, K))
    return np.exp(sc * g + ss * e - 0.5 * (sc * sc + ss * ss))


def make_instance(
    N: int,
    n_per_carrier: int,
    K: int = 4,
    Z: int = 2,
    seed: int = 0,
    share: np.ndarray | None = None,
    overlap: float = 0.3,
    eps: float | np.ndarray = 0.05,
    Q: int = 8,
    T_max: float = 4.0,
    route_frac: float = 0.7,
    cap_frac: float = 0.6,
    beta: float | np.ndarray = 0.2,
    sigma_c: float = 0.25,
    sigma_s: float = 0.25,
    S: int = 30,
    S_true: int = 2000,
    f: float = 1.0,
    gamma: float = 1.0,
    rho: float = 2.0,
    eta: float = 0.5,
    theta: float = 0.5,
    phi: float = 0.1,
    service: float = 0.05,
    spread: float = 0.12,
) -> Instance:
    """Generate a unit-square instance.

    share: optional relative customer counts per carrier (default equal).
    overlap: fraction of each carrier's customers drawn uniformly over the city.
    cap_frac: hub capacity as a fraction of the average hub's share of total demand.
    speed is set so that a typical Q-stop nearest-neighbour route lasts route_frac*T_max.
    """
    if isqrt(K) ** 2 != K:
        raise ValueError("K must be a perfect square")
    rng = np.random.default_rng(seed)

    t = (np.arange(N) + 0.5) / N * 4
    depots = np.empty((N, 2))
    for i, tt in enumerate(t):
        e, fr = int(tt), tt - int(tt)
        depots[i] = [(fr, 0.0), (1.0, fr), (1.0 - fr, 1.0), (0.0, 1.0 - fr)][e]

    w = np.ones(N) if share is None else np.asarray(share, dtype=float)
    counts = np.maximum(1, np.round(n_per_carrier * N * w / w.sum()).astype(int))

    centres = rng.uniform(0.3, 0.7, (N, 2))
    customers = []
    for i in range(N):
        n_u = int(round(overlap * counts[i]))
        uni = rng.uniform(0.0, 1.0, (n_u, 2))
        gau = np.clip(centres[i] + spread * rng.standard_normal((counts[i] - n_u, 2)), 0, 1)
        customers.append(np.vstack([uni, gau]))

    cand = rng.uniform(0.05, 0.95, (500, 2))
    hubs = [cand[rng.integers(len(cand))]]
    for _ in range(Z - 1):
        d = np.linalg.norm(cand[:, None] - np.array(hubs)[None], axis=-1).min(axis=1)
        hubs.append(cand[int(np.argmax(d))])
    hubs = np.array(hubs)
    zone_of = [np.argmin(np.linalg.norm(c[:, None] - hubs[None], axis=-1), axis=1) for c in customers]

    C = np.full(Z, cap_frac * counts.sum() / Z)
    beta_arr = np.broadcast_to(np.asarray(beta, dtype=float), (Z,)).copy()

    lens = [
        _nn_tour_length(depots[i], customers[i][s0 : s0 + Q])
        for i in range(N)
        for s0 in range(0, len(customers[i]), Q)
    ]
    speed = route_frac * T_max / float(np.mean(lens))

    samples = _draw_xi(rng, N * S, K, sigma_c, sigma_s).reshape(N, S, K)
    true_samples = _draw_xi(rng, S_true, K, sigma_c, sigma_s)

    return Instance(
        N=N, K=K, Z=Z, depots=depots, customers=customers, hubs=hubs, C=C,
        beta=beta_arr, zone_of=zone_of, Q=Q, T_max=T_max, f=f, gamma=gamma, rho=rho,
        eta=eta, theta=theta, phi=phi, speed=speed, service=service, samples=samples,
        true_samples=true_samples, eps=np.broadcast_to(np.asarray(eps, dtype=float), (N,)).copy(),
    )
