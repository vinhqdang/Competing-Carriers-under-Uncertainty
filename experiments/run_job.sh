#!/bin/sh
# usage: run_job.sh leader|imprecision CITY SEED   (resumable; logs in results/logs/)
cd "$(dirname "$0")"
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p ../results/logs
python run_$1.py $2 --seed $3 >> ../results/logs/$1_$2_s$3.log 2>&1
python progress.py
