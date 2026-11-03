# Mean-field limit of the carrier game

- Decision memo and status: `docs/MFG_DIRECTION.md` (Section 6 = status after execution); log: `PROGRESS.md`.
- Draft manuscript: `paper/main.tex` / `paper/main.pdf`; theory sections in `theory/` (standalone `theory/notes.pdf`).
- Code: `src/mfgcc`; tests: `python3 -m pytest mfg/tests -q`; theory checks:
  `PYTHONPATH=mfg/src python3 mfg/checks/theory_checks.py mfg/checks/theory_checks.out`.
- Experiments: `mfg/experiments/run_all.sh` (resumable), then `PYTHONPATH=mfg/src python3 mfg/experiments/analyze.py`.
- Lean: `cd mfg/lean && lake build` (reuses the Mathlib build of `lean/`).
- Earlier sanity checks of the memo: `checks/finite_to_mf_gap.py` (output `checks/finite_to_mf_gap.out`).
