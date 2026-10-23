"""Brute-force check of the dynamic-programming oracle on tiny instances."""
import itertools

import numpy as np

from core import make_game

for reg in ["D1", "D2"]:
    for seed in range(5):
        g = make_game(N=2, Z=4, seed=seed, regime=reg, support=0.75, Dmax=3)
        rng = np.random.default_rng(seed)
        for i in range(2):
            cr = g.carriers[i]
            rngs = [range(int(cr.D[z]) + 1) if z in cr.S else [0] for z in range(g.Z)]
            plans = [g.make_plan(i, np.array(q)) for q in itertools.product(*rngs)]
            for trial in range(6):
                lam = rng.normal(0, 3, g.d)
                rho = trial % 2
                vals = [p.c + lam @ p.phi - 0.5 * rho * (p.a @ (g.M * p.a)) for p in plans]
                o = g.oracle(i, lam, rho=rho)
                vo = o.c + lam @ o.phi - 0.5 * rho * (o.a @ (g.M * o.a))
                assert abs(vo - min(vals)) < 1e-8, (reg, seed, vo, min(vals))
print("oracle ok")
