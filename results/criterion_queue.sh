#!/bin/bash
# Resumable queue of the criterion-robustness study (one core).  Re-run to continue after an interruption.
cd "$(dirname "$0")/.."
R="taskset -c 1 python experiments/run_criterion_robust.py run"
$R --cities London BuenosAires NewDelhi Bombay --criteria saa wass_th wass_cv pbox
$R --cities Moscow NewYork Cairo Paris Berlin --seeds 0 --criteria saa wass_th
$R --cities Moscow NewYork Cairo Paris Berlin --seeds 1 2 --criteria saa wass_th
$R --cities Moscow NewYork Cairo Paris Berlin --seeds 0 1 2 --criteria wass_cv
