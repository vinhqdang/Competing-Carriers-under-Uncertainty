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

## Open items for the author
See docs/MFG_DIRECTION.md, Section 6, "Decisions for the author".
