# Mean-field paper: progress log

Plan: docs/MFG_DIRECTION.md, Section 4 (steps 1-6). Defaults used for the open decisions: (1) mean-field agent =
small multi-stop carriers; (2) major-minor model out of scope; (3) stylised hourly profile, stated and graded as an
assumption (mfg/src/mfgcc/profiles.py); (4) imprecise-probability layer limited to the Gamma-maximin surcharge and
the belief-width scaling; (5) venue left to the author.

## Milestone 1 (theory statements, checks, solver)
- Theory checks: `PYTHONPATH=mfg/src python3 mfg/checks/theory_checks.py mfg/checks/theory_checks.out`.
- Package `mfg/src/mfgcc` (qp, theory, city, profiles, leader); tests `python3 -m pytest mfg/tests -q` (11 pass).
- Key theory finding: no instance-free O(1/N) constant exists once carriers' plans couple zones; an explicit
  two-zone family attains the O(1/sqrt N) bound up to the factor 1/sqrt 2 (check output, "Prop 2").
