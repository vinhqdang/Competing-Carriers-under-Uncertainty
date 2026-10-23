#!/bin/sh
# full pipeline for one city (after run_equilibria.py): verification (2c, E6), leader (E2, E3), imprecision (E4)
c=$1
cd "$(dirname "$0")"
python run_verification.py city $c > ../results/logs/V_$c.log 2>&1
python run_leader.py $c > ../results/logs/L_$c.log 2>&1
python run_imprecision.py $c > ../results/logs/I_$c.log 2>&1
