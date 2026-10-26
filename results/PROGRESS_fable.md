# Progress: new algorithm D (ARP, aggregate-response pricing)

All done (2026-10-26).
- Stage 1 brainstorm: seven candidates, six killed (list in theory/new_algorithm_D/algorithm.md); survivor: observation-only leader.
- Stage 2 theory: theory/new_algorithm_D/theory.tex (+pdf, 9 pages, pdflatex), 8 theorems/propositions with proofs; constants checked in results/arp_rates.csv.
- Stage 3 prototype: src/ccu/arp.py, tests/test_arp.py (22 tests; full suite 132 pass + 1 skip).
  Tiny games: results/arp_tiny.csv (210 games). Cities: London, BuenosAires, NewDelhi, Bombay x seeds 0-2, exact oracle:
  results/arp_<city>*.csv, results/arp_charges_*.csv, results/summary_arp.csv, stages in results/arp_parts/.
- Stage 4 novelty: 12 queries logged in algorithm.md; verdict incremental (principle known: Yang-Meng-Lee 2004, Maheshwari et al. 2022, Sandholm 2002).
- Stage 5 write-up: algorithm.md, results.md, docs/EXPERIMENTS.md section "Aggregate-response pricing", figures/arp_{calls_vs_gain,paths,tiny}.png.

Restart / reproduce: see docs/EXPERIMENTS.md, 'Aggregate-response pricing' (all drivers resumable).
