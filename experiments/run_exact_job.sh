#!/bin/sh
# usage: run_exact_job.sh e1|e1sens|leader|imprecision CITY [SEED]  (resumable, idempotent; logs in results/logs/exact_*.log)
cd "$(dirname "$0")"
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export CCU_BP_TIME=${CCU_BP_TIME:-20} CCU_BP_RETRY=${CCU_BP_RETRY:-120}
mkdir -p ../results/logs
k=$1; c=$2; s=${3:-0}
case $k in
  e1) python run_exact.py e1 $c $s ;;
  e1sens) python run_exact.py e1sens $c ;;
  leader) python run_leader.py $c --seed $s ;;
  imprecision) python run_imprecision.py $c --seed $s ;;
esac >> ../results/logs/exact_${k}_${c}_s${s}.log 2>&1
python progress_exact.py
