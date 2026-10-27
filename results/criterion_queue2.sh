#!/bin/bash
# Final phase: Wasserstein-CV in the heavy cities (Paris and Berlin: seed 0 only, the oracle needs 20-40 min per game).
cd "$(dirname "$0")/.."
R="taskset -c 1 python experiments/run_criterion_robust.py run"
$R --cities Moscow NewYork Cairo Paris Berlin --seeds 0 --criteria wass_cv
$R --cities Moscow NewYork Cairo --seeds 1 2 --criteria wass_cv
