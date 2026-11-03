#!/bin/bash
# Resumable driver for all city experiments (re-run after a container restart; finished rows are skipped).
cd "$(dirname "$0")/../.."
export PYTHONPATH=mfg/src NPROC=${NPROC:-3}
for w in main kappa profile hetero; do
  python3 mfg/experiments/run_gap.py $w >> mfg/results/log_$w.txt 2>&1
done
python3 mfg/experiments/run_extra.py >> mfg/results/log_extra.txt 2>&1
