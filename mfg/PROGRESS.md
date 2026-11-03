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
