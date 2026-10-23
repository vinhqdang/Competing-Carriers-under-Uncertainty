#!/bin/sh
# E2/E3 (run_leader.py) and E4 (run_imprecision.py) for seeds 1 and 2 on all nine cities, 4 parallel jobs, slowest first.
# Safe to rerun after a container restart: complete result files are skipped and partial E2/E4 files resume.
#   nohup experiments/run_seeds.sh > results/logs/run_seeds.out 2>&1 &
cd "$(dirname "$0")"
mkdir -p ../results/logs
SEEDS=${SEEDS:-"1 2"}
CITIES="Cairo London Berlin Paris NewYork Moscow BuenosAires NewDelhi Bombay"
for k in leader imprecision; do
  for c in $CITIES; do for s in $SEEDS; do echo "$k $c $s"; done; done
done | xargs -P 4 -L 1 ./run_job.sh
python progress.py
