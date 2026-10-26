#!/bin/bash
# ARP on the city games, exact oracle, 3 jobs in parallel, resumable.  Usage: experiments/run_arp_queue.sh [cities...]
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 CCU_BP_TIME=${CCU_BP_TIME:-20} CCU_BP_RETRY=${CCU_BP_RETRY:-120}
CITIES=${@:-"London BuenosAires NewDelhi Bombay"}
PAR=${ARP_PAR:-3}
mkdir -p results/logs
for city in $CITIES; do
  for seed in 0 1 2; do
    while [ "$(jobs -rp | wc -l)" -ge "$PAR" ]; do sleep 20; done
    python experiments/run_arp.py "$city" --seed "$seed" > "results/logs/arp_${city}_s${seed}.out" 2>&1 &
    sleep 2
  done
done
wait
python experiments/run_arp.py summary
