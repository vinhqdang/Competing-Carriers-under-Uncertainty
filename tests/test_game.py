"""Best-response dynamics convergence, exploitability, and price monotonicity on small instances."""
import numpy as np

from ccu import best_response_dynamics, exploitability, make_instance, social_cost
from ccu.game import total_load


def test_dynamics_converge_and_exploitability_small():
    inst = make_instance(N=2, n_per_carrier=6, Z=2, seed=2)
    rng = np.random.default_rng(0)
    profile, hist, converged = best_response_dynamics(inst, np.array([0.2, 0.2]), rng, max_iter=30)
    assert converged
    assert all(b <= a + 1e-9 for a, b in zip(hist, hist[1:]))  # potential never increases
    expl = exploitability(inst, profile, np.array([0.2, 0.2]), rng, starts=16)
    assert expl < 1e-2 * (1 + abs(social_cost(inst, profile)))


def test_higher_uniform_price_lowers_hub_load():
    inst = make_instance(N=2, n_per_carrier=10, Z=2, seed=5)
    rng = np.random.default_rng(1)
    loads = []
    profile = None
    for p in (0.0, 0.5, 1.0, 2.0):
        profile, _, conv = best_response_dynamics(inst, np.full(2, p), rng, init=profile, max_iter=40)
        assert conv
        loads.append(float(total_load(profile, inst.Z).sum()))
    print("hub loads along uniform price grid:", loads)
    assert all(b <= a for a, b in zip(loads, loads[1:]))
    assert loads[-1] < loads[0]
