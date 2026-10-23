# Competing-Carriers-under-Uncertainty

Game-theoretic experiments on nine real city maps: Zone-Market Clearing (ZMC) with a Budget-Resource Labelling
(BRL) column-generation carrier oracle.

Reproduce (about 1-2 hours on 4 cores; seeds are fixed, `--seed 0` by default):

```
pip install numba            # compiled BRL pricer
python -m pytest -q
cd experiments
python run_verification.py tiny                       # exhaustive enumeration on tiny games
for c in NewDelhi Cairo Moscow BuenosAires NewYork Bombay London Paris Berlin; do
  python run_equilibria.py $c --seeds 0 1 2           # E1 + sensitivity (results/E1_<city>.csv)
  ./run_city.sh $c                                    # verification, E2/E3 (leader), E4 (imprecision), E5/E6 data
done
python summarize.py && python plot_equilibria.py && python plot_results.py
```

Details, tables, figures and limitations: `docs/EXPERIMENTS.md`.
