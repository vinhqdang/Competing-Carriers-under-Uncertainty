#!/bin/bash
# All stages of the BRL benchmark on one core, resumable (finished jobs are skipped).
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python experiments/run_brl_bench.py pub --tl 90 --reps 2
python experiments/run_brl_bench.py polish --tl 15
python experiments/run_brl_bench.py shift
python experiments/run_brl_bench.py labels --tl-cg 150
python experiments/run_brl_bench.py devices --tl-cg 200
python experiments/run_brl_bench.py bpscale --tl 1800
python experiments/run_brl_bench.py summary
