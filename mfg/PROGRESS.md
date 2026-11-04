# Mean-field paper: progress log

Plan: docs/MFG_DIRECTION.md, Section 4 (steps 1-6); status table in its Section 6. Defaults used for the open
decisions: (1) mean-field agent = small multi-stop carriers; (2) major-minor model out of scope; (3) stylised hourly
profile, stated and graded as an assumption (src/mfgcc/profiles.py); (4) imprecise layer limited to the
Gamma-maximin surcharge and the belief-width scaling; (5) venue left to the author.

## Step 1-2: theory (done)
- Statements and proofs: theory/model.tex, gap.tex, leader.tex, imprecise.tex, d2.tex (standalone: theory/notes.pdf).
- Main finding: no instance-free O(1/N) constant once plans couple zones (Prop 5, explicit two-zone family attaining
  the general bound of Thm 4 up to 1/sqrt 2). O(s) with constant one for zone-separable carriers (Thm 6, sharp),
  for identical carriers in the M-norm (Prop 7); O(1/n) with instance constant for replicas (Thm 8, Prop 9).
- Leader: exact identity for the finite-market observation-only charge (Thm 12); instance-free O(s) welfare (Thm 13).
- Gamma-maximin (Prop 15), width (Cor 16), time-of-day p-box remark (Prop 17), D2 (Prop 18), Conjecture 19 (open).
- Brute-force checks: checks/theory_checks.py -> checks/theory_checks.out (all slacks >= 0).

## Step 3: computation (done)
- src/mfgcc: qp.py (interior point via Clarabel; Frank-Wolfe), city.py (time-expanded instances), leader.py,
  profiles.py, theory.py. Tests: `python3 -m pytest mfg/tests -q` (11 pass).
- Dependency added to the environment: `pip install clarabel` (also highspy, unused).

## Step 4: experiments (done)
- `mfg/experiments/run_all.sh` (resumable), then `PYTHONPATH=mfg/src python3 mfg/experiments/analyze.py`.
- Results: results/gap.csv (replicas at solver tolerance 1e-13, heterogeneous splits at 1e-10), gamma.csv,
  width.csv, arp_paths.csv, flat_rule.csv, solver_cost.csv, summary_*.csv; figures/mfg_*.png.
- Headline: gap slope -0.88 [-0.90,-0.86] in N, 0.95 [0.92,0.97] in the share; gap ~ one carrier delivery;
  observation-only charge harmful with few carriers, converges to Pigou; profile effect weak; width bound weak.

## Step 5: Lean (done)
- lean/MFG/Core.lean, separate Lake project reusing lean/'s Mathlib; `cd mfg/lean && lake build` passes, no sorry.

## Step 6: draft (done)
- paper/main.tex (elsarticle, 11pt) -> paper/main.pdf, 22 pages, compiles with pdflatex + bibtex.

## Step 7: stakeholder analysis (done)
- Code: src/mfgcc/stake.py (welfare decomposition CS + Pi + R = SW, charge rules, exposure), tests/test_stake.py (16 tests in total pass
  together with test_mfg.py: `python3 -m pytest mfg/tests -q`).
- Experiments (resumable): run_stake.py (stake.csv: 9 cities x 5 seeds x 9 sizes x rules none/obs/pm/opt; KSCALE=10 -> stake_k10.csv),
  run_ident.py (ident.csv, identical carriers), run_uniform.py (uniform.csv, misspec.csv, about 1 h on 4 cores), then
  `PYTHONPATH=mfg/src python3 mfg/experiments/analyze_stake.py` (summary_stake_*.csv, figures/mfg_stake_*.png, paper/numbers_stake.tex).
- Paper: paper/stake.tex (Section 11 'Who gains and who loses', Proposition 20, Tables 2-3, Figures 7-8); main.pdf 27 pages.
- Results (medians): N=6 market-power rule: welfare +19.6%, consumer surplus +69%, carrier net profit +132%, revenue -182% of no-charge
  welfare (subsidy); observation-only: welfare -0.5%, CS -1.0%. N=1536: both rules raise about 3% of welfare as revenue, CS -1.1 to -1.6%,
  carrier profit -0.1% of welfare (about -8% of their profit). Exposure Gini unchanged by charges at N=1536 (0.080); exposure share moves
  away from dense zones (Spearman -0.56). Best single city-wide charge: loss 3.41% vs 1.08% (zone-hour) vs 17.66% (none) at N=6; captures
  78% of the mean-field gain. Mis-specified charge (+-10, +-25%): bound holds 180/180, measured 0.2-0.98 of bound, losses <= 0.04%.
- Proposition 20 (u*_N = (kappa - m/N) Q_opt for identical carriers) holds exactly (error <= 5e-9 in 324 instances). The Cournot ratio
  N/(N+1) holds only where the fleet budget is slack (6 of 9 cities).
- Weak or negative: calibrated congestion is small (3.6% of welfare), so exposure and its inequality barely move; the efficient charge at
  small N is a large subsidy (budget neutral only for large N); the 'pm' rule does not reach the optimum with several carrier types (1.1% loss at N=6).

## Open items for the author
See docs/MFG_DIRECTION.md, Section 6, "Decisions for the author".

## Step 8: fees, entry, further externalities (done, 2026-11-04)
- Code: src/mfgcc/fees.py (fee schemes at fixed N; free entry with real counts per segment, secant on log k, sequential
  exit of the least viable segment; one-zone closed forms), src/mfgcc/extern.py (fastest-path km on the major graph,
  cached in results/geo/ [not committed, rebuilt on demand, ~30 s per city]; per-tour external cost: air pollution,
  climate, noise (EU Handbook 2019 values), through-traffic delay (BPR marginal external delay at the hourly congestion
  level, VOT = driver wage); exposure in vkm per resident). city.py records the legs of every tour (no equilibrium change).
  Tests: tests/test_ext.py; `python3 -m pytest mfg/tests -q` (all pass).
- Experiments (resumable, PYTHONPATH=mfg/src): run_fees.py -> results/fees.csv; run_entry.py -> results/entry.csv
  (seeds 0-2, N0 = 6, 24, 192); SWEEP=1 run_entry.py -> results/entry_sweep.csv (seed 0, N0 = 12, 48, 96, 384);
  run_extern.py -> results/extern.csv; then analyze_ext.py -> numbers_ext.tex, table_{fees,entry,extern}.tex,
  figures/mfg_entry.png, mfg_extern.png, results/summary_ext_*.csv.
- Paper: paper/ext.tex (Section 12, Props 21-23, Tables 4-7, Figs 9-10); abstract, contributions, discussion and
  limitations updated; 33 pages.
- Findings: see docs/MFG_DIRECTION.md Section 6 (rows Prop 21-23 and the three new experiment rows).
- Weak/negative: through-traffic delay (VOT proxy, grade C) carries the externality result; the free-entry pm/pmfee runs
  stop at 80 rounds in about a quarter of cases (residual up to 2% of F; signs unaffected); the recovery fee under
  free entry has outcomes from market closure to +26% welfare; second-best property of the Pigou charge proved for one
  zone only and holds approximately in the cities (best of the scalings in 27/27, 20/27, 12/27).

## Open items for the author
See docs/MFG_DIRECTION.md, Section 6, "Decisions for the author".

## Step 8: fees, entry, further externalities (in progress, 2026-11-04)
- Code: src/mfgcc/fees.py (fee schemes at fixed N, free entry with real counts per segment, one-zone closed forms),
  src/mfgcc/extern.py (fastest-path km on the major graph, cached in results/geo/ [not committed, rebuilt on demand];
  per-tour external cost: air pollution, climate, noise (EU Handbook 2019 values), through-traffic delay (BPR marginal
  external delay at the hourly congestion level, VOT = driver wage); exposure in vkm per resident). city.py records the
  legs of every tour (no change to any equilibrium). Tests: tests/test_ext.py (38 tests pass in total).
- Experiments (resumable, PYTHONPATH=mfg/src): run_fees.py -> results/fees.csv (done, 180 rows); run_entry.py ->
  results/entry.csv (SWEEP=1 -> entry_sweep.csv); run_extern.py -> results/extern.csv.
- First findings: N=6 recovery fee takes 96% of carrier profit (median); flat or fleet-proportional fee leaves some carrier
  with negative profit at N=6 in 45/45 and 41/45 instances; a carrier-specific (profit-proportional) fee balances in
  40/45 (not Buenos Aires). Free entry: the market-power subsidy attracts entrants and lowers welfare net of fixed costs;
  one zone: the observation-only (Pigou) charge is the second-best per-delivery charge under free entry.
  Through-traffic delay dominates the extra externalities (Paris: 0.62 USD/delivery vs 0.11 in-zone congestion charge).
