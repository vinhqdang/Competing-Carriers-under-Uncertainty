#!/bin/sh
# usage: run_exact_job.sh e1|e1sens|leader|imprecision CITY [SEED]  (resumable, idempotent; logs in results/logs/exact_*.log)
cd "$(dirname "$0")"
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export CCU_BP_TIME=${CCU_BP_TIME:-20} CCU_BP_RETRY=${CCU_BP_RETRY:-120}
mkdir -p ../results/logs
k=$1; c=$2; s=${3:-0}
exec 9>../results/logs/lock_${k}_${c}_${s}
flock -n 9 || exit 0  # another process already runs this job
# E2 grid and E4 widths: exact oracle everywhere for the cheap cities, reduced exact set for the heavy ones
# (see docs/EXPERIMENTS.md, 'Exact oracle re-run'); override with CCU_E2_MODE / CCU_E4_MODE = full | reduced
if [ -z "$CCU_E2_MODE" ]; then
  case $c in Cairo|Paris|Berlin|NewYork|Moscow) CCU_E2_MODE=minimal ;; *) CCU_E2_MODE=full ;; esac
fi
if [ -z "$CCU_E4_MODE" ]; then
  case $c in Cairo|Paris|Berlin|NewYork|Moscow) CCU_E4_MODE=reduced ;; *) CCU_E4_MODE=full ;; esac
fi
if [ -z "$CCU_E3_SO_BROAD" ]; then
  case $c in NewYork|Moscow|Berlin) CCU_E3_SO_BROAD=pb ;; *) CCU_E3_SO_BROAD=exact ;; esac
fi
export CCU_E2_MODE CCU_E4_MODE CCU_E3_SO_BROAD
case $k in
  e1) python run_exact.py e1 $c $s ;;
  e1sens) python run_exact.py e1sens $c ;;
  oldreg) python run_old_regret.py $c $s ;;
  leader) python run_leader.py $c --seed $s ;;
  imprecision) python run_imprecision.py $c --seed $s ;;
esac >> ../results/logs/exact_${k}_${c}_s${s}.log 2>&1
python progress_exact.py
