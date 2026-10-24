"""Scheduler of the exact-oracle re-run: keeps at most NPROC (default 3) jobs running, in priority order.
Every job is idempotent (finished work is skipped, a per-job flock prevents duplicates), so after a container restart simply run
    nohup python experiments/run_exact_queue.py > results/logs/run_exact_queue.out 2>&1 &
Priority: E1 parts, E2+E3 (run_leader.py; E3 needs the E2 best points), E4 seed 0, 1, 2, old-equilibrium regrets, E1 sensitivity.
Finally the E1 parts are assembled (run_exact.py assemble --keep-old-sens)."""
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
NPROC = int(os.environ.get("NPROC", "3"))
HEAVY_FIRST = ["Cairo", "Paris", "BuenosAires", "London", "NewDelhi", "Bombay", "NewYork", "Moscow", "Berlin"]  # cheap cities before the heavy tail (Berlin)
jobs = []
for c in HEAVY_FIRST:
    for s in (0, 1, 2):
        jobs.append(("e1", c, s))
LATE = ["Berlin"]  # slowest city: after E4 seed 0 of the others
for c in HEAVY_FIRST:
    if c not in LATE:
        for s in (0, 1, 2):
            jobs.append(("leader", c, s))
for c in HEAVY_FIRST:
    jobs.append(("imprecision", c, 0))
for c in LATE:
    for s in (0, 1, 2):
        jobs.append(("leader", c, s))
for s in (1, 2):
    for c in HEAVY_FIRST:
        jobs.append(("imprecision", c, s))
for c in HEAVY_FIRST:
    for s in (0, 1, 2):
        jobs.append(("oldreg", c, s))
for c in HEAVY_FIRST:
    jobs.append(("e1sens", c, 0))
if len(sys.argv) > 1:  # restrict to some job kinds, e.g. "leader imprecision"
    jobs = [j for j in jobs if j[0] in sys.argv[1:]]


def running():
    out = subprocess.run(["pgrep", "-af", r"python (run_leader|run_imprecision|run_old_regret|run_exact)\.py"], capture_output=True, text=True).stdout
    return [l for l in out.splitlines() if "pgrep" not in l]


def is_running(k, c, s):
    pat = {"e1": f"run_exact.py e1 {c} {s}", "leader": f"run_leader.py {c} --seed {s}", "imprecision": f"run_imprecision.py {c} --seed {s}",
           "oldreg": f"run_old_regret.py {c} {s}", "e1sens": f"run_exact.py e1sens {c}"}[k]
    return any(pat in l for l in running())


procs = []
for k, c, s in jobs:
    while True:
        procs = [p for p in procs if p.poll() is None]
        if len(running()) < NPROC:
            break
        time.sleep(15)
    if is_running(k, c, s):
        continue
    procs.append(subprocess.Popen([str(HERE / "run_exact_job.sh"), k, c, str(s)]))
    time.sleep(3)
for p in procs:
    p.wait()
subprocess.run([sys.executable, str(HERE / "run_exact.py"), "assemble", "--keep-old-sens"], cwd=HERE)
subprocess.run([sys.executable, str(HERE / "progress_exact.py")], cwd=HERE)
