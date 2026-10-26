"""Scheduler of the ten-seed extension (seeds 3..9): at most NPROC (default 2) jobs at a time, each pinned to one CPU core.
Resume after a restart (finished jobs are skipped, a per-job flock prevents duplicates, a scheduler flock prevents two schedulers):
    nohup python experiments/run_seeds10_queue.py > results/logs/seeds10_queue.out 2>&1 &
Job order (priority): core (E1, DIP+social optimum, further equilibria) for all cities and seeds, ARP, the full 63-point grid of
New Delhi / Buenos Aires / London for seeds 3-5, then their seeds 6-9, then the coarse exact grid of the six other cities.
Options:  --phases core arp grid   restrict;  --deadline "YYYY-mm-dd HH:MM"  do not start jobs after this local time.
"""
import argparse
import fcntl
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent / "results"
PARTS = RES / "seeds10_parts"
PARTS.mkdir(exist_ok=True)
(RES / "logs").mkdir(exist_ok=True)
CITIES = ["NewDelhi", "Cairo", "Moscow", "BuenosAires", "NewYork", "Bombay", "London", "Paris", "Berlin"]
FULL = ["NewDelhi", "BuenosAires", "London"]
COARSE = ["Bombay", "Berlin", "Moscow", "NewYork", "Paris", "Cairo"]
NEW = list(range(3, 10))
ARP_OLD = {"London", "BuenosAires", "NewDelhi", "Bombay"}  # seeds 0-2 exist in results/arp_*.csv


def arp_part(c, s):
    import json
    return PARTS / "arp" / f"{c}_s{s}.json", json


def is_done(phase, c, s):
    import json
    f = PARTS / ("arp" if phase == "arp" else "") / (f"{c}_s{s}.json" if phase == "arp" else f"{phase}_{c}_s{s}.json")
    try:
        return bool(json.loads(f.read_text()).get("done"))
    except Exception:
        return False


def job_list(phases):
    jobs = []
    if os.environ.get("S10_ORDER") == "light_first":
        # cheap work for the cities with the full grid first (headline), then the remaining heavy core jobs seed by seed
        for s in NEW:
            for c in FULL:
                jobs.append(("core", c, s))
        for s in NEW:
            for c in FULL:
                jobs += [("grid", c, s), ("arp", c, s)]
        for s in NEW:
            for c in CITIES:
                jobs.append(("core", c, s))
        for s in NEW:
            for c in CITIES:
                jobs.append(("arp", c, s))
        for s in (0, 1, 2):
            for c in CITIES:
                if c not in ARP_OLD:
                    jobs.append(("arp", c, s))
        for s in NEW:
            for c in COARSE:
                jobs.append(("grid", c, s))
        return [j for j in jobs if j[0] in phases]
    if "core" in phases:
        for s in NEW:
            for c in CITIES:
                jobs.append(("core", c, s))
    if "arp" in phases:
        for s in NEW:
            for c in CITIES:
                jobs.append(("arp", c, s))
        for s in (0, 1, 2):
            for c in CITIES:
                if c not in ARP_OLD:
                    jobs.append(("arp", c, s))
    if "grid" in phases:
        for s in (3, 4, 5):
            for c in FULL:
                jobs.append(("grid", c, s))
        for s in (6, 7, 8, 9):
            for c in FULL:
                jobs.append(("grid", c, s))
        for s in NEW:
            for c in COARSE:
                jobs.append(("grid", c, s))
    return jobs


def progress():
    old = ""
    pf = RES / "PROGRESS_seeds10.md"
    if pf.exists():
        t = pf.read_text()
        old = t[t.index("## Log"):] if "## Log" in t else ""
    mark = lambda ph, c, s: "x" if is_done(ph, c, s) else "."
    lines = ["# Progress: ten-seed extension (seeds 3..9 added to 0..2), exact oracle", "",
             "Resume after a restart (every job is resumable and writes atomically; finished work is skipped; 2 cores):", "",
             "```", "nohup python experiments/run_seeds10_queue.py > results/logs/seeds10_queue.out 2>&1 &", "```", "",
             f"Updated {time.strftime('%Y-%m-%d %H:%M:%S')}. Cells: core / arp / grid per seed, x = finished, . = missing, - = not scheduled "
             "(seeds 0-2: ARP exists for London, Buenos Aires, New Delhi, Mumbai; E1-E3, DIP and the grid of seeds 0-2 are the earlier runs).", "",
             "| city | " + " | ".join(f"s{s}" for s in NEW) + " | arp s0 s1 s2 |", "|---|" + "---|" * (len(NEW) + 1)]
    n_done = n_all = 0
    for c in CITIES:
        cells = []
        for s in NEW:
            cells.append("/".join([mark("core", c, s), mark("arp", c, s), mark("grid", c, s)]))
            n_done += sum(is_done(p, c, s) for p in ("core", "arp", "grid"))
            n_all += 3
        if c in ARP_OLD:
            a = "existing"
        else:
            a = " ".join(mark("arp", c, s) for s in (0, 1, 2))
            n_done += sum(is_done("arp", c, s) for s in (0, 1, 2))
            n_all += 3
        lines.append(f"| {c} | " + " | ".join(cells) + f" | {a} |")
    lines += ["", f"{n_done} of {n_all} scheduled results complete.", ""]
    lines.append(old if old else "## Log\n")
    tmp = pf.with_name(pf.name + f".tmp{os.getpid()}")
    tmp.write_text("\n".join(lines))
    os.replace(tmp, pf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phases", nargs="+", default=["core", "arp", "grid"])
    ap.add_argument("--deadline", default=None)
    ap.add_argument("--nproc", type=int, default=int(os.environ.get("NPROC", "2")))
    a = ap.parse_args()
    lock = open(PARTS / ".lock_scheduler", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another scheduler is running", flush=True)
        return
    deadline = time.mktime(time.strptime(a.deadline, "%Y-%m-%d %H:%M")) if a.deadline else None
    env = dict(os.environ, OMP_NUM_THREADS="1", NUMBA_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               CCU_BP_TIME=os.environ.get("CCU_BP_TIME", "20"), CCU_BP_RETRY=os.environ.get("CCU_BP_RETRY", "120"))
    cores = [0, 1][:a.nproc]
    running = {}  # core -> (Popen, job, t0)
    jobs = [j for j in job_list(a.phases) if not is_done(*j)]
    print(time.strftime("%H:%M:%S"), len(jobs), "jobs to do", flush=True)
    progress()

    def external():
        """run_seeds10.py processes of an earlier scheduler (still running after a scheduler restart): {core: pid}"""
        out = subprocess.run(["pgrep", "-f", "run_seeds10.py"], capture_output=True, text=True).stdout.split()
        own = {p.pid for p, _, _ in running.values()}
        ext = {}
        for pid in out:
            pid = int(pid)
            if pid in own or pid == os.getpid():
                continue
            cmd = open(f"/proc/{pid}/cmdline").read().replace("\0", " ") if os.path.exists(f"/proc/{pid}/cmdline") else ""
            if "run_seeds10.py" in cmd and "queue" not in cmd and "python" in cmd and "taskset" not in cmd:
                aff = subprocess.run(["taskset", "-cp", str(pid)], capture_output=True, text=True).stdout.strip().split(":")[-1].strip()
                ext[pid] = int(aff.split(",")[0].split("-")[0]) if aff else 0
        return ext

    def reap():
        for core, (p, job, t0) in list(running.items()):
            if p.poll() is not None:
                print(time.strftime("%H:%M:%S"), "finished", job, "rc", p.returncode, f"{time.time() - t0:.0f}s", flush=True)
                del running[core]
                progress()

    for job in jobs:
        if is_done(*job):
            continue
        while True:
            reap()
            used = set(running) | set(external().values())
            if len(used) < len(cores):
                break
            time.sleep(5)
        if deadline and time.time() > deadline:
            print("deadline reached, no new jobs", flush=True)
            break
        core = [c for c in cores if c not in used][0]
        ph, c, s = job
        log = open(RES / "logs" / f"s10_{ph}_{c}_s{s}.log", "a")
        p = subprocess.Popen(["taskset", "-c", str(core), sys.executable, str(HERE / "run_seeds10.py"), c, str(s), ph], cwd=HERE, env=env,
                             stdout=log, stderr=subprocess.STDOUT)
        running[core] = (p, job, time.time())
        print(time.strftime("%H:%M:%S"), "started", job, "on core", core, flush=True)
    while running:
        time.sleep(5)
        reap()
    progress()
    print("queue finished", flush=True)


if __name__ == "__main__":
    main()
