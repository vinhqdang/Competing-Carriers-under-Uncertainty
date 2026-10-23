"""Core model for the direction-A prototypes: affine aggregative carrier game with a routing-type oracle.

Coordinates: k in [0, Z) are deliveries q_z, k in [Z, 2Z) are the congestion variable x_z.
D1: a = (q, tau), phi = a.   D2: a = (q, n), phi = (q, tau).
Game cost of carrier i:  J_i(p; A_-i) = c_i(p) + <phi_i(p), M A_-i>,  M = diag(b, gamma*c) >= 0.
The oracle returns argmin_p c_i(p) + <lam, phi_i(p)> + rho * (-1/2) ||a_i(p)||_M^2 exactly (dynamic programme
over zones with a fleet coupling term F * ceil(sum_z n_z / R) that makes the plan set non-separable).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Plan:
    q: np.ndarray  # (Z,) deliveries
    n: np.ndarray  # (Z,) vehicle visits
    tau: np.ndarray  # (Z,) vehicle hours
    a: np.ndarray  # (2Z,) contribution
    phi: np.ndarray  # (2Z,) exposure
    c: float  # private cost

    def key(self) -> bytes:
        return self.q.astype(np.int16).tobytes()


@dataclass
class Carrier:
    S: np.ndarray  # zones served
    D: np.ndarray  # (Z,) demand (0 outside S)
    v: np.ndarray  # (Z,) unit handling cost
    kap: np.ndarray  # (Z,) per vehicle-visit cost
    t: np.ndarray  # (Z,) hours per vehicle visit
    s: np.ndarray  # (Z,) hours per delivery
    F: float  # cost per vehicle (fleet)
    R: int  # zone visits per vehicle
    cap: int  # deliveries per vehicle visit


@dataclass
class Game:
    Z: int
    carriers: list[Carrier]
    alpha: np.ndarray
    b: np.ndarray
    gc: np.ndarray  # gamma * c_z
    gmu: np.ndarray  # gamma * mean traffic
    regime: str = "D1"
    toll: np.ndarray | None = None  # (2Z,) leader charge on a
    calls: int = 0
    _cache: dict = field(default_factory=dict)

    @property
    def N(self) -> int:
        return len(self.carriers)

    @property
    def d(self) -> int:
        return 2 * self.Z

    @property
    def M(self) -> np.ndarray:
        return np.concatenate([self.b, self.gc])

    # ------------------------------------------------------------------ plans
    def zone_options(self, i: int, z: int):
        """All options in zone z for carrier i: arrays q, n, tau, private cost (excluding fleet term)."""
        key = ("opt", i, z, self.regime)
        if key in self._cache:
            return self._cache[key]
        cr = self.carriers[i]
        q = np.arange(int(cr.D[z]) + 1, dtype=float)
        n = np.ceil(q / cr.cap)
        tau = n * cr.t[z] + q * cr.s[z]
        x_own = tau if self.regime == "D1" else n
        cost = -self.alpha[z] * q + self.b[z] * q * q + self.gc[z] * tau * x_own + self.gmu[z] * tau
        cost = cost + cr.v[z] * q + cr.kap[z] * n
        if self.toll is not None:
            ax = tau if self.regime == "D1" else n
            cost = cost + self.toll[z] * q + self.toll[self.Z + z] * ax
        out = (q, n, tau, cost)
        self._cache[key] = out
        return out

    def make_plan(self, i: int, q: np.ndarray) -> Plan:
        cr = self.carriers[i]
        Z = self.Z
        q = np.asarray(q, dtype=float)
        n = np.ceil(q / cr.cap)
        tau = n * cr.t + q * cr.s
        x_own = tau if self.regime == "D1" else n
        cost = float(np.sum(-self.alpha * q + self.b * q * q + self.gc * tau * x_own + self.gmu * tau
                            + cr.v * q + cr.kap * n))
        cost += cr.F * math.ceil(n.sum() / cr.R - 1e-12)
        if self.regime == "D1":
            a = np.concatenate([q, tau])
            phi = a
        else:
            a = np.concatenate([q, n])
            phi = np.concatenate([q, tau])
        if self.toll is not None:
            cost += float(self.toll @ a)
        return Plan(q, n, tau, a, phi, cost)

    # ------------------------------------------------------------------ oracle
    def oracle(self, i: int, lam: np.ndarray, rho: float = 0.0, lam_a: np.ndarray | None = None,
               count: bool = True) -> Plan:
        """argmin_p c_i(p) + <lam, phi_i(p)> + <lam_a, a_i(p)> - rho/2 ||a_i(p)||_M^2 (exact DP)."""
        if count:
            self.calls += 1
        cr = self.carriers[i]
        Z = self.Z
        M = self.M
        best_V = np.array([0.0])  # value per total visits V
        choice = []
        for z in cr.S:
            q, n, tau, cost = self.zone_options(i, z)
            phx = tau
            ax = tau if self.regime == "D1" else n
            val = cost + lam[z] * q + lam[Z + z] * phx
            if lam_a is not None:
                val = val + lam_a[z] * q + lam_a[Z + z] * ax
            if rho:
                val = val - 0.5 * rho * (M[z] * q * q + M[Z + z] * ax * ax)
            nmax = int(n.max())
            # best q for each n
            bq = np.full(nmax + 1, -1, dtype=int)
            bv = np.full(nmax + 1, np.inf)
            for k in range(len(q)):
                nk = int(n[k])
                if val[k] < bv[nk] - 1e-12:
                    bv[nk] = val[k]
                    bq[nk] = k
            L = len(best_V)
            new = np.full(L + nmax, np.inf)
            arg = np.zeros(L + nmax, dtype=int)
            for nk in range(nmax + 1):
                if not np.isfinite(bv[nk]):
                    continue
                cand = best_V + bv[nk]
                sl = slice(nk, nk + L)
                better = cand < new[sl] - 1e-12
                new[sl] = np.where(better, cand, new[sl])
                arg[sl] = np.where(better, nk, arg[sl])
            choice.append((z, bq, arg))
            best_V = new
        Vs = np.arange(len(best_V))
        tot = best_V + cr.F * np.ceil(Vs / cr.R - 1e-12)
        V = int(np.argmin(tot))
        qv = np.zeros(Z)
        for z, bq, arg in reversed(choice):
            nk = int(arg[V])
            qv[z] = bq[nk]
            V -= nk
        return self.make_plan(i, qv)

    # ------------------------------------------------------------------ game quantities
    def J(self, i: int, p: Plan, A_minus: np.ndarray) -> float:
        return p.c + float(p.phi @ (self.M * A_minus))

    def br(self, i: int, A_minus: np.ndarray, count: bool = True) -> Plan:
        return self.oracle(i, self.M * A_minus, count=count)

    def regrets(self, prof: list[Plan], count: bool = False) -> np.ndarray:
        A = sum(p.a for p in prof)
        out = np.zeros(self.N)
        for i, p in enumerate(prof):
            Am = A - p.a
            b = self.br(i, Am, count=count)
            out[i] = max(0.0, self.J(i, p, Am) - self.J(i, b, Am))
        return out

    def potential(self, prof: list[Plan]) -> float:
        """Exact potential (D1): sum c_i + 1/2 ||A||_M^2 - 1/2 sum ||a_i||_M^2 (to be minimised)."""
        M = self.M
        A = sum(p.a for p in prof)
        return sum(p.c for p in prof) + 0.5 * float(A @ (M * A)) - 0.5 * sum(float(p.a @ (M * p.a)) for p in prof)

    def ctilde(self, p: Plan) -> float:
        return p.c - 0.5 * float(p.a @ (self.M * p.a))


def make_game(N=4, Z=20, seed=0, regime="D1", support=0.5, Dmax=6, local=True, scale=1.0) -> Game:
    """Random structured instance. Zones on a ring; carrier supports are arcs (local) or random subsets."""
    rng = np.random.default_rng(seed)
    carriers = []
    for i in range(N):
        m = max(1, int(round(support * Z)))
        if local:
            start = int(rng.integers(Z))
            S = np.sort((start + np.arange(m)) % Z)
        else:
            S = np.sort(rng.choice(Z, m, replace=False))
        D = np.zeros(Z)
        D[S] = rng.integers(2, Dmax + 1, size=len(S))
        carriers.append(Carrier(
            S=S, D=D,
            v=rng.uniform(0.5, 1.5, Z), kap=rng.uniform(1.0, 3.0, Z),
            t=rng.uniform(0.3, 0.8, Z), s=rng.uniform(0.05, 0.15, Z),
            F=float(rng.uniform(4, 8)), R=int(rng.integers(2, 4)), cap=int(rng.integers(2, 4)),
        ))
    alpha = rng.uniform(6, 10, Z) * scale
    b = rng.uniform(0.3, 0.8, Z)
    gc = rng.uniform(0.5, 1.5, Z)
    gmu = rng.uniform(0.5, 1.0, Z)
    return Game(Z=Z, carriers=carriers, alpha=alpha, b=b, gc=gc, gmu=gmu, regime=regime)
