#!/bin/sh
# Exact-oracle re-run, 3 parallel jobs, priority order; PHASES selects what runs (default: all in order).
# Safe to rerun after a restart: every job skips finished work.   nohup experiments/run_exact.sh > results/logs/run_exact.out 2>&1 &
cd "$(dirname "$0")"
PHASES=${PHASES:-"e1 leader imprecision e1sens"}
CITIES="Cairo Paris Berlin NewYork Moscow BuenosAires London NewDelhi Bombay"
for ph in $PHASES; do
  for c in $CITIES; do
    for s in 0 1 2; do
      [ $ph = e1sens ] && [ $s != 0 ] && continue
      echo "$ph $c $s"
    done
  done | xargs -P ${NPROC:-3} -L 1 ./run_exact_job.sh
done
python run_exact.py assemble --keep-old-sens
python progress_exact.py
