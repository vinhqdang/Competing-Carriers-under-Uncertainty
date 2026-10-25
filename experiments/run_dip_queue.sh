#!/bin/sh
# all city/seed jobs of run_dip.py, two at a time (resumable: finished jobs are skipped)
cd "$(dirname "$0")"
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export CCU_BP_TIME=${CCU_BP_TIME:-20} CCU_BP_RETRY=${CCU_BP_RETRY:-120}
mkdir -p ../results/logs
P=${DIP_PAR:-2}
{ for c in London BuenosAires NewDelhi; do for s in 0 1 2; do echo "$c $s"; done; done
  for s in 0 1 2; do for c in Bombay Cairo Moscow NewYork Berlin Paris; do echo "$c $s"; done; done; } |
  xargs -P "$P" -L 1 sh -c 'python run_dip.py $0 --seed $1 >> ../results/logs/dip_$0_s$1.out 2>&1'
python run_dip.py summary
