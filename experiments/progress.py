"""Rewrite the status table of results/PROGRESS.md from the result files that exist (E2/E3/E4, seeds 0-2, nine cities)."""
import os
import time

from common import RES, read_rows, rpath, zb

SEEDS = (0, 1, 2)
MARK = "<!-- SEEDS-STATUS -->"


def status(c, s):
    e2 = len(read_rows(rpath("E2", c, s))) == 63 and rpath("E2best", c, s).exists() and rpath("E2cert", c, s).exists()
    e3 = len(read_rows(rpath("E3", c, s))) == 10
    e4 = len(read_rows(rpath("E4", c, s))) == 12
    return e2, e3, e4


def main():
    lines = [MARK, f"Status of E2 / E3 / E4 per city and seed (updated {time.strftime('%Y-%m-%d %H:%M:%S')}; x = complete file, . = missing).",
             "Rerun `experiments/run_seeds.sh` after a restart: finished files are skipped, the E2 grid and E4 rows resume.", "",
             "| city | s0 E2/E3/E4 | s1 E2/E3/E4 | s2 E2/E3/E4 |", "|---|---|---|---|"]
    n = 0
    for c in zb.CITIES:
        cells = []
        for s in SEEDS:
            st = status(c, s)
            n += sum(st)
            cells.append("/".join("x" if v else "." for v in st))
        lines.append(f"| {c} | " + " | ".join(cells) + " |")
    lines += [f"", f"{n} of {9 * 3 * 3} city/seed/experiment results complete.", MARK]
    p = RES / "PROGRESS.md"
    txt = p.read_text() if p.exists() else ""
    if MARK in txt:
        a = txt.index(MARK)
        b = txt.rindex(MARK) + len(MARK)
        txt = txt[:a] + "\n".join(lines) + txt[b:]
    else:
        txt = txt.rstrip() + "\n\n## Seed robustness runs (E2, E3, E4 on seeds 0-2)\n\n" + "\n".join(lines) + "\n"
    tmp = p.with_name("PROGRESS.md.tmp%d" % os.getpid())
    tmp.write_text(txt)
    os.replace(tmp, p)


if __name__ == "__main__":
    main()
