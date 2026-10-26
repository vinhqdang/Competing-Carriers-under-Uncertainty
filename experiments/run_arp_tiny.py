"""Tiny games with exhaustive enumeration: aggregate-response pricing against the exact leader optimum, DIP and the grid.

Same instances and references as experiments/dip_tiny.py (results/dip_tiny.csv: exact optimistic leader optimum over
all zone charges, DIP, grid).  Added here, per instance:
  arp_<mode>   flat ARP from the unpriced (potential-minimising) equilibrium; modes plain / optimal / msa, with lot
               learning; 'known' = plain with DIP's mean lot (information-rich benchmark)
  mct_br       marginal tariff + carriers' best-response dynamics from the unpriced equilibrium (observation-only)
  mct_so       marginal tariff + the potential-minimising solver (ZMC on the social-cost potential, needs the oracle)
  worst-case:  worst pure NE under DIP's charges, under the unpriced game and under the marginal tariff (all NE enumerated)

Usage: python experiments/run_arp_tiny.py [--n 30]   -> results/arp_tiny.csv (resumable per instance)
"""
import argparse
import itertools
import time

import numpy as np

from common import RES, read_rows, write_csv, zb, zmc  # noqa: F401
from ccu import arp, dip
import dip_tiny as dt

MODES = ["plain", "optimal", "msa"]


def ne_set_mct(g, P, idxs, SC):
    """Pure NE of the marginal-tariff game = profiles with no unilateral social-cost improvement (Theorem 7)."""
    shape = [len(p) for p in P]
    pos = {idx: n for n, idx in enumerate(idxs)}
    out = []
    for n, idx in enumerate(idxs):
        ok = True
        for i in range(len(shape)):
            for k in range(shape[i]):
                if k == idx[i]:
                    continue
                alt = list(idx)
                alt[i] = k
                if SC[pos[tuple(alt)]] < SC[n] - 1e-9:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            out.append(n)
    return out


def run_instance(seed, N, Z, n_cust, gcx, ref):
    g = dt.make(seed, N, Z, n_cust, gcx)
    P = dt.enum(g)
    idxs, SC, Phi0 = dt.profile_tables(g, P)
    act = dip.active_zones(g)
    ne0 = dt.ne_set(g, P, idxs, np.zeros(Z))
    sc0 = float(SC[min(ne0, key=lambda n: Phi0[n])])
    opt = float(ref["opt_zone"]) if ref is not None else np.nan
    row = dict(seed=seed, N=N, Z=Z, n_cust=n_cust, gcx=gcx, sc_ne=sc0, sc_so=float(SC.min()), opt_zone=opt,
               rho=arp.contraction_ratio(g), n_ne0=len(ne0), sc_ne0_worst=float(max(SC[n] for n in ne0)))
    if ref is not None:
        row.update(dip_sc=float(ref["dip_sc"]), dip_calls=int(ref["dip_calls"]), dip_worst_sc=float(ref["dip_worst_sc"]),
                   grid_selected=float(ref["grid_selected"]), grid_calls=int(ref["grid_calls"]))
    # flat ARP
    D = dip.lots(g)
    has = D > 0
    dbar_known = np.where(has.any(0), D.sum(0) / np.maximum(has.sum(0), 1), 0.0)
    for mode in MODES + ["known"]:
        gg = dt.make(seed, N, Z, n_cust, gcx)
        base = zmc.run_zmc(gg, rounds=6)
        c0 = gg.calls
        kw = dict(theta="plain", dbar=dbar_known) if mode == "known" else dict(theta=mode)
        o = arp.arp(gg, base["profile"], max_rounds=15, **kw)
        # worst NE under the final charge
        ne_u = dt.ne_set(g, P, idxs, o["u"])
        row.update({f"arp_{mode}_sc": o["sc"], f"arp_{mode}_status": o["status"], f"arp_{mode}_rounds": o["rounds"],
                    f"arp_{mode}_calls": gg.calls - c0, f"arp_{mode}_best_sc": o["best_sc"],
                    f"arp_{mode}_worst_sc": float(max(SC[n] for n in ne_u)) if ne_u else np.nan,
                    f"arp_{mode}_regret": float(gg.regrets(o["profile"]).max())})
    # marginal tariff: BR from the unpriced equilibrium, and the potential-minimising solver
    gg = dt.make(seed, N, Z, n_cust, gcx)
    base = zmc.run_zmc(gg, rounds=6)
    c0 = gg.calls
    om = arp.arp_marginal(gg, base["profile"])
    row.update(mct_br_sc=om["sc"], mct_br_calls=gg.calls - c0, mct_br_monotone=om["monotone"],
               mct_br_regret=float(arp.MarginalTariffGame(gg).regrets(om["profile"]).max()), mct_br_payments=om["payments"])
    gs = dt.make(seed, N, Z, n_cust, gcx)
    so = gs.so_variant(False)
    c0 = so.calls
    r = zmc.run_zmc(so, rounds=6)
    prof = [gs.plan_from_routes(i, p.routes) for i, p in enumerate(r["profile"])]
    row.update(mct_so_sc=dip.social_cost(gs, prof), mct_so_calls=so.calls - c0,
               mct_so_regret=float(arp.MarginalTariffGame(gs).regrets(prof).max()))
    nem = ne_set_mct(g, P, idxs, SC)
    row.update(mct_n_ne=len(nem), mct_worst_sc=float(max(SC[n] for n in nem)), mct_best_sc=float(min(SC[n] for n in nem)))
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    a = ap.parse_args()
    path = RES / "arp_tiny.csv"
    rows = read_rows(path)
    done = {(int(r["seed"]), int(r["N"]), int(r["n_cust"]), float(r["gcx"])) for r in rows}
    refs = {(int(r["seed"]), int(r["N"]), int(r["n_cust"]), float(r["gcx"])): r for r in read_rows(RES / "dip_tiny.csv")}
    configs = [(3, 6, 3, 1.0), (3, 6, 4, 1.0), (4, 5, 3, 1.0), (3, 5, 4, 20.0), (4, 5, 3, 20.0), (3, 5, 4, 60.0), (4, 5, 4, 60.0)]
    for seed in range(a.n):
        for N, Z, nc, gcx in configs:
            key = (seed, N, nc, gcx)
            if key in done:
                continue
            t0 = time.perf_counter()
            r = run_instance(seed, N, Z, nc, gcx, refs.get(key))
            r["time_s"] = time.perf_counter() - t0
            rows.append(r)
            write_csv(path, rows)
            print(seed, N, Z, nc, gcx, "ne %.2f opt %.2f arp %.2f(%s) mct_br %.2f mct_so %.2f dip %.2f" % (
                r["sc_ne"], r["opt_zone"], r["arp_plain_sc"], r["arp_plain_status"], r["mct_br_sc"], r["mct_so_sc"],
                r.get("dip_sc", np.nan)), round(r["time_s"], 1), flush=True)


if __name__ == "__main__":
    main()
