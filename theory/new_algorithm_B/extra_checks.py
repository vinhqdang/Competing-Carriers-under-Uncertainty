"""Extra checks reported in results.md: loose deadlines, large duals, BRL vs enumeration on real 9-zone instances."""
import copy
import json

import numpy as np

import prototype as pr
import real_instances as ri


def loose():
    rng = np.random.default_rng(11)
    rows = []
    for Tf in (1.5, 2.5, 5.0):
        for n in (12, 16, 20):
            P = pr.random_pricing(rng, n, K=9, cap=6, Tfrac=Tf)
            row = {"Tfrac": Tf, "n": n}
            for rule in ("functional", "pointwise"):
                b, _, st = pr.espprc(P, rule, time_limit=60)
                row[rule] = (round(st["time"], 3), st["labels_kept"], st["timed_out"], b)
            print(row, flush=True)
            rows.append(row)
    json.dump(rows, open("results_D_loose.json", "w"), default=float, indent=1)


def highdual():
    rng = np.random.default_rng(12)
    rows = []
    for n in (12, 16, 20, 25):
        P = pr.random_pricing(rng, n, K=9, cap=6, Tfrac=0.8, dual_scale=2.5)
        Pd = copy.copy(P)
        Pd.loss = pr.Loss(P.loss.gamma, 0.0, P.loss.Tmax, P.loss.fixed)
        row = {"dual_scale": 2.5, "n": n}
        for rule, PP, rr in (("deterministic_mean", Pd, "functional"), ("functional", P, "functional"), ("pointwise", P, "pointwise")):
            b, _, st = pr.espprc(PP, rr, time_limit=120)
            row[rule] = (round(st["time"], 3), st["labels_kept"], st["timed_out"], round(b, 3))
        print(row, flush=True)
        rows.append(row)
    json.dump(rows, open("results_D_highdual.json", "w"), default=float, indent=1)


def real_exactness():
    rows = []
    for city in ri.CITIES:
        P, true, meta = ri.build(city, ncust=9, seed=3)
        P.cap = 40.0
        cost = ri.make_costs(P, true, 0.05)
        sol, _ = ri.heuristic(P, cost, "pbox", np.random.default_rng(0))
        ri.column_generation(P, cost, sol, ng_size=0)
        for scale in (1.0, 1.3):
            P.duals = P.duals * scale
            ref, _, s0 = pr.espprc(P, "none", time_limit=600)
            b, _, s1 = pr.espprc(P, "functional", time_limit=600)
            bp, _, s2 = pr.espprc(P, "pointwise", time_limit=600)
            rows.append(dict(city=city, dual_scale=scale, enum=ref, brl=b, pointwise=bp, enum_labels=s0["labels_created"],
                             brl_kept=s1["labels_kept"], pointwise_kept=s2["labels_kept"],
                             match=bool(abs(ref - b) < 1e-7 and abs(ref - bp) < 1e-7)))
            print(rows[-1], flush=True)
    json.dump(rows, open("results_realC.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    loose()
    highdual()
    real_exactness()
