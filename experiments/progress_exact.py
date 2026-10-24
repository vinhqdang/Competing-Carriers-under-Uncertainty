"""Rewrite results/PROGRESS_exact.md (status of the exact-oracle re-run) from the result files that exist."""
import os
import time

from common import RES, read_rows, rpath, zb

SEEDS = (0, 1, 2)
PARTS = RES / "exact_parts"


def main():
    L = ["# Progress: exact-oracle (branch-and-price) re-run of E1-E4", "",
         "Resume after a restart (all commands skip finished work; 3 processes):", "",
         "```", "nohup experiments/run_exact.sh > results/logs/run_exact.out 2>&1 &", "```", "",
         f"Updated {time.strftime('%Y-%m-%d %H:%M:%S')}. x = finished, . = missing (E1 / E2 / E3 / E4 per seed; sens = E1 sensitivity).", "",
         "| city | s0 | s1 | s2 | E1 sens |", "|---|---|---|---|---|"]
    n = 0
    for c in zb.CITIES:
        cells = []
        for s in SEEDS:
            e1 = (PARTS / f"E1_{c}_s{s}.csv").exists()
            e2 = len(read_rows(rpath("E2", c, s))) == 63 and rpath("E2best", c, s).exists() and rpath("E2cert", c, s).exists()
            e3 = len(read_rows(rpath("E3", c, s))) == 10
            e4 = len(read_rows(rpath("E4", c, s))) == 12
            n += e1 + e2 + e3 + e4
            cells.append("/".join("x" if v else "." for v in (e1, e2, e3, e4)))
        L.append(f"| {c} | " + " | ".join(cells) + f" | {'x' if (PARTS / f'E1sens_{c}.done').exists() else '.'} |")
    L += ["", f"{n} of 108 city/seed/experiment results complete (E2/E3/E4 files are only counted when they were produced after the old ones were moved to results/pb_old).", ""]
    p = RES / "PROGRESS_exact.md"
    keep = ""
    if p.exists() and "## Log" in p.read_text():
        keep = p.read_text()[p.read_text().index("## Log"):]
    tmp = p.with_name("PROGRESS_exact.md.tmp%d" % os.getpid())
    tmp.write_text("\n".join(L) + "\n" + (keep or "## Log\n"))
    os.replace(tmp, p)


if __name__ == "__main__":
    main()
