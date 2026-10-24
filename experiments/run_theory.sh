#!/bin/sh
# Theory-to-experiment checks for all nine cities and seeds 0-2, 2 parallel jobs (at most 2 cores), slowest first.
# Resumable: every stage is cached in results/theory_cache/; rerun after a container restart.
#   nohup experiments/run_theory.sh > results/logs/run_theory.out 2>&1 &
cd "$(dirname "$0")"
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p ../results/logs
KIND=${KIND:-absorb}
SEEDS=${SEEDS:-"0 1 2"}
CITIES="Berlin London Cairo Paris NewYork Moscow BuenosAires NewDelhi Bombay"
for s in $SEEDS; do for c in $CITIES; do echo "$c $s"; done; done | \
  xargs -P 2 -L 1 sh -c 'python run_theory_checks.py '"$KIND"' $0 --seeds $1 >> ../results/logs/theory_'"$KIND"'_$0_s$1.log 2>&1'
