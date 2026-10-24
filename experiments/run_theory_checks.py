"""Theory-to-experiment checks (docs/EXPERIMENTS.md, section 'Theory-to-experiment checks').

  python experiments/run_theory_checks.py absorb CITY [--seeds 0 1 2]   Thm 6.1 on real equilibria + Gamma-maximin (Lemma 3.6)
  python experiments/run_theory_checks.py d2tiny                        D2 on tiny games: exhaustive enumeration, gadgets (Prop 7.1, Thm 7.3)
  python experiments/run_theory_checks.py d2city CITY [--seeds 0 1 2]   D2 (vehicle-count congestion) on a real city
  python experiments/run_theory_checks.py report                        assemble results/theory_*.csv, summary_theory.csv, figures
  python experiments/run_theory_checks.py all-cities                    absorb for the nine cities (2 cores), then report

Everything is resumable: the state of one (city, seed) lives in results/theory_cache/<city>_s<seed>.json and every stage is
skipped when it is already stored.  See results/PROGRESS_theory.md.
"""
import argparse
import itertools
import json
import os
import time
from pathlib import Path

import numpy as np

from common import RES, FIG, ROOT, solve_ne, write_csv, zb, zmc  # noqa: F401  (common puts src/ on the path)
from ccu import credal as cr  # noqa: E402
from ccu import d2game as d2  # noqa: E402

CACHE = RES / "theory_cache"
CACHE.mkdir(exist_ok=True)
CITIES = ["Cairo", "Bombay", "Paris", "NewDelhi", "Moscow", "BuenosAires", "NewYork", "London", "Berlin"]
NCUST = 22
TOL = 1e-6
GAMMA_DELTAS = [0.1, 0.25, 0.5, 1.0]


# ---------------------------------------------------------------------------------------------------------------
# cache
# ---------------------------------------------------------------------------------------------------------------


def cpath(city, seed, tag=""):
    return CACHE / f"{city}_s{seed}{tag}.json"


def load(city, seed, tag=""):
    p = cpath(city, seed, tag)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {}


def save(city, seed, st, tag=""):
    p = cpath(city, seed, tag)
    tmp = p.with_name(p.name + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(st, default=_js))
    os.replace(tmp, p)


def _js(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def routes_of(prof):
    return [[[int(z) for z in r] for r in p.routes] for p in prof]


def rebuild(g, routes):
    return [g.plan_from_routes(i, [tuple(r) for r in rr]) for i, rr in enumerate(routes)]


def plan_from(g, i, rr):
    return g.plan_from_routes(i, [tuple(r) for r in rr])


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------------------------------------------------------
# Part 1: absorption
# ---------------------------------------------------------------------------------------------------------------


def stage_solve(g, st, city, seed):
    """ZMC + BRL equilibrium, polished until the independent fresh-pool oracle finds no improving deviation (as in E1)."""
    t0 = time.perf_counter()
    o = solve_ne(g, rounds=8, certify="fresh")
    r = o["result"]
    prof = o["profile"]
    P = [list(p) if not isinstance(p, list) else p for p in r["pools"]]
    rounded, _ = zmc.round_pools(g, P)
    start = {"price": r["best"][2], "round": rounded}[r["start"]]
    st["solve"] = dict(p0=routes_of(prof), start=routes_of(start), start_kind=r["start"], calls=o["row"]["calls"],
                       converged=bool(o["row"]["converged"]), regret_fresh=o["row"]["max_regret"], phi=g.potential(prof),
                       phi_start=g.potential(start), time_s=time.perf_counter() - t0, N=g.N, Z=g.Z, d_eff=g.meta["d_eff"],
                       overlap=g.meta["overlap"], served_share=float(o["eval"]["served_share"]), pool_sizes=[len(x) for x in P])
    save(city, seed, st)
    log(city, seed, "solve", round(st["solve"]["time_s"], 1), "s, calls", o["row"]["calls"], "fresh regret", o["row"]["max_regret"])


def stage_pures(g, st, city, seed, budget, max_starts):
    t0 = time.perf_counter()
    rng = np.random.default_rng(1000 + seed)
    p0 = rebuild(g, st["solve"]["p0"])
    seen = {cr.profile_key(p0)}
    pures = [p0]
    starts = []
    N = g.N
    empty = [g.empty_plan(i) for i in range(N)]
    for i in range(N):
        s = list(p0)
        s[i] = empty[i]
        starts.append(("drop%d" % i, s))
    zeroA = np.zeros(g.d)
    starts.append(("standalone", [g.br(i, zeroA, count=True) for i in range(N)]))
    for k in range(max(0, max_starts - len(starts))):
        sub = rng.choice(N, size=int(rng.integers(2, max(3, N // 2 + 1))), replace=False)
        s = list(p0)
        for i in sub:
            s[i] = empty[i]
        starts.append(("rand%d" % k, s))
    stats = []
    for name, s in starts[:max_starts]:
        if time.perf_counter() - t0 > budget:
            break
        res = cr.br_run(g, s, rng=rng, max_rounds=30)
        isne, new, reg = False, False, np.nan
        if res["status"] == "converged" and cr.profile_key(res["profile"]) not in seen:
            reg = float(g.regrets(res["profile"], count=False, fresh=True).max())  # independent oracle: only for new profiles
            isne = reg < 1e-6
            new = isne
        elif res["status"] == "converged":
            isne = True
        if new:
            seen.add(cr.profile_key(res["profile"]))
            pures.append(res["profile"])
        stats.append(dict(start=name, status=res["status"], rounds=res["rounds"], is_ne=bool(isne), new=bool(new)))
    st["pures"] = dict(routes=[routes_of(p) for p in pures], stats=stats, time_s=time.perf_counter() - t0)
    save(city, seed, st)
    log(city, seed, "pures: %d distinct pure NE from %d starts" % (len(pures), len(stats)), round(time.perf_counter() - t0, 1), "s")


def stage_mixed(g, st, city, seed, max_verify=12, max_keep=4):
    t0 = time.perf_counter()
    pures = [rebuild(g, r) for r in st["pures"]["routes"]]
    cands = cr.mixed_candidates(g, pures)
    cands.sort(key=lambda c: (-len(c[2]), 0))
    out = []
    nver = 0
    sigs = set()
    for support, weights, S in cands:
        if nver >= max_verify or len(out) >= max_keep:
            break
        sig = tuple(tuple(sorted((cr.plan_key(p), round(float(x), 6)) for p, x in zip(sp, wt))) for sp, wt in zip(support, weights))
        if sig in sigs:
            continue
        sigs.add(sig)
        nver += 1
        viol = cr.check_relaxed(g, support, weights)
        if viol <= 1e-6:
            out.append(dict(support=[[[list(map(int, r)) for r in p.routes] for p in s] for s in support], weights=weights,
                            mixers=list(S), violation=viol))
    st["mixed"] = dict(items=out, n_candidates=len(cands), n_verified_calls=nver, time_s=time.perf_counter() - t0)
    save(city, seed, st)
    log(city, seed, "mixed relaxed eq: %d verified of %d candidates (%d checked)" % (len(out), len(cands), nver),
        round(time.perf_counter() - t0, 1), "s")


def known_plans(g, st):
    known = [[g.empty_plan(i)] for i in range(g.N)]
    seen = [{cr.plan_key(known[i][0])} for i in range(g.N)]
    allp = [rebuild(g, r) for r in st["pures"]["routes"]] + [rebuild(g, st["solve"]["start"])]
    for prof in allp:
        for i, p in enumerate(prof):
            if cr.plan_key(p) not in seen[i]:
                seen[i].add(cr.plan_key(p))
                known[i].append(p)
    return known


def oracle_eps(g, st):
    """Per-carrier oracle inexactness: the largest improvement over the certified equilibria that a known plan (from any solve,
    including the pre-polish ZMC profile) or the pooled oracle itself offers at those equilibria's rival aggregates."""
    known = known_plans(g, st)
    eps = np.zeros(g.N)
    for r in st["pures"]["routes"]:
        prof = rebuild(g, r)
        for i in range(g.N):
            A = cr.rival_aggregate(prof, i)
            J = cr.cost_at(g, prof[i], A)
            for q in known[i]:
                eps[i] = max(eps[i], J - cr.cost_at(g, q, A))
            eps[i] = max(eps[i], J - cr.cost_at(g, cr.best_response(g, i, A), A))  # the pooled oracle's own answer at A
    return eps


def anchors_of(g, st):
    p0 = rebuild(g, st["solve"]["p0"])
    out = [("pure", [[p] for p in p0], [[1.0] for _ in p0], [])]
    for k, m in enumerate(st["mixed"]["items"]):
        support = [[plan_from(g, i, rr) for rr in s] for i, s in enumerate(m["support"])]
        out.append((f"mixed{k + 1}", support, m["weights"], m["mixers"]))
    return out


def stage_measure(g, st, city, seed, w_mode="agg", cap=16, tag=""):
    t0 = time.perf_counter()
    p0 = rebuild(g, st["solve"]["p0"])
    w = cr.make_weights(g, p0, w_mode)
    d = g.d
    smax = cr.sigma_max(g, w)
    bN = cr.n_uniform_bound(g.N, d, smax)
    known = known_plans(g, st)
    eps = oracle_eps(g, st)
    rows = []
    rng = np.random.default_rng(seed)
    for name, support, weights, mixers in anchors_of(g, st):
        s = cr.anchored_stats(g, support, weights, w, d=d)
        allprof = cr.profiles_in_support(support, cap=4096, rng=rng)
        dh_all = np.array([cr.delta_hat(pf, s["abar"], w) for pf in allprof])
        order = np.argsort(dh_all)
        pick = list(dict.fromkeys([int(order[0]), int(order[-1])] + list(rng.permutation(len(allprof))[: cap - 2])))[:cap]
        res = []
        for idx in pick:
            pf = allprof[idx]
            th = cr.profile_thresholds(g, pf, w, kinds=("E",), cuts=known, eps=eps)
            res.append((idx, th))
        emax = max(range(len(res)), key=lambda k: res[k][1]["E_max"])
        mi_idx = list(dict.fromkeys([res[0][0], res[1][0] if len(res) > 1 else res[0][0], res[emax][0]]))[:3]
        for idx, th in res:
            row = dict(city=city, seed=seed, N=g.N, Z=g.Z, d=d, d_eff=g.meta["d_eff"], w_mode=w_mode, anchor=name,
                       n_mixers=len(mixers), prod_size=len(allprof), idx=idx, sigma_max=smax, bound_N=bN, **{k: s[k] for k in (
                           "rho_bar", "sigma_bar", "d_L", "k_sharp", "T1", "T2", "T3", "bound")},
                       delta_hat=float(dh_all[idx]), min_delta_hat=float(dh_all.min()), max_delta_hat=float(dh_all.max()),
                       delta_E=th["E_max"], delta_M=np.nan, delta_ID=np.nan, eps_orc_max=float(eps.max()))
            if idx in mi_idx:
                th2 = cr.profile_thresholds(g, allprof[idx], w, kinds=("M", "ID"), e_given=th["E_by_carrier"], eps=eps)
                row["delta_M"], row["delta_ID"] = th2["M_max"], th2["ID_max"]
            rows.append(row)
        log(city, seed, w_mode, name, "profiles", len(allprof), "sampled", len(res), "dE max %.4g" % max(r[1]["E_max"] for r in res),
            "dhat min %.4g" % dh_all.min(), "bound %.4g" % s["bound"], "boundN %.4g" % bN, "%.0fs" % (time.perf_counter() - t0))
    # unpolished ZMC rounding (pre best-response polish): not a theorem test, reported as the RSRC certificate
    start = rebuild(g, st["solve"]["start"])
    th = cr.profile_thresholds(g, start, w, kinds=("E", "M", "ID"), cuts=known, eps=eps)
    rows.append(dict(city=city, seed=seed, N=g.N, Z=g.Z, d=d, d_eff=g.meta["d_eff"], w_mode=w_mode, anchor="zmc_start",
                     n_mixers=-1, prod_size=1, idx=0, sigma_max=smax, bound_N=bN, delta_E=th["E_max"], delta_M=th["M_max"],
                     delta_ID=th["ID_max"]))
    st["rows" + tag + "_" + w_mode] = rows
    st["time_measure_" + w_mode] = time.perf_counter() - t0
    save(city, seed, st)


def absorb(city, seeds, budget=240.0, max_starts=10, w_modes=("agg", "type_median")):
    for seed in seeds:
        st = load(city, seed)
        if "gamma_rows" in st and all(("rows_" + m) in st for m in w_modes):
            log(city, seed, "absorb already complete")
            continue
        g = zb.build_city_game(city, n_cust=NCUST, seed=seed)
        if "solve" not in st:
            stage_solve(g, st, city, seed)
        else:
            log(city, seed, "solve cached")
        if "pures" not in st:
            stage_pures(g, st, city, seed, budget, max_starts)
        if "mixed" not in st:
            stage_mixed(g, st, city, seed)
        for m in w_modes:
            if "rows_" + m not in st:
                stage_measure(g, st, city, seed, w_mode=m, cap=(16 if m == "agg" else 8))
        if "gamma_rows" not in st:
            stage_gamma(g, st, city, seed)


# ---------------------------------------------------------------------------------------------------------------
# Gamma-maximin (Lemma 3.6)
# ---------------------------------------------------------------------------------------------------------------


def stage_gamma(g, st, city, seed):
    t0 = time.perf_counter()
    p0 = rebuild(g, st["solve"]["p0"])
    w = cr.make_weights(g, p0, "agg")
    ev0 = g.evaluate(p0)
    known = known_plans(g, st)
    rows = []
    lam = None
    for de in GAMMA_DELTAS:
        t1 = time.perf_counter()
        g.set_charges(sur=de * g.M * w)
        o = solve_ne(g, rounds=6, lam0=lam, certify="fresh")
        lam = o["result"]["lam"]
        pG = o["profile"]
        regG = float(o["row"]["max_regret"])  # equilibrium of the surcharge game (independent oracle)
        routesG = routes_of(pG)
        g.set_charges()  # back to the precise game
        pG = rebuild(g, routesG)
        p0r = rebuild(g, st["solve"]["p0"])
        evG = g.evaluate(pG)
        gam_reg0 = [cr.gamma_regret(g, i, p0r, w, de) for i in range(g.N)]
        gam_regG = [cr.gamma_regret(g, i, pG, w, de) for i in range(g.N)]
        thG = cr.profile_thresholds(g, pG, w, kinds=("E", "M", "ID"), cuts=known, eps=oracle_eps(g, st))
        same = cr.profile_key(pG) == cr.profile_key(p0r)
        rows.append(dict(city=city, seed=seed, N=g.N, Z=g.Z, delta=de, same_profile=bool(same), regret_surcharge_game=regG,
                         gamma_regret_NE=max(gam_reg0), gamma_adm_NE_frac=float(np.mean(np.array(gam_reg0) <= 1e-5)),
                         gamma_regret_Gprofile=max(gam_regG), E_thr_G=thG["E_max"], M_thr_G=thG["M_max"], ID_thr_G=thG["ID_max"],
                         served_NE=ev0["served_share"], served_G=evG["served_share"], hours_NE=ev0["vehicle_hours"],
                         hours_G=evG["vehicle_hours"], welfare_NE=ev0["welfare"], welfare_G=evG["welfare"],
                         vehicles_NE=ev0["vehicles"], vehicles_G=evG["vehicles"], time_s=time.perf_counter() - t1))
        log(city, seed, "gamma delta", de, "same" if same else "diff", "served %.3f -> %.3f" % (ev0["served_share"], evG["served_share"]),
            "Gamma-regret(NE) %.3g" % max(gam_reg0), "M-thr(G) %.3g" % thG["M_max"], "E-thr(G) %.3g" % thG["E_max"])
    st["gamma_rows"] = rows
    st["time_gamma"] = time.perf_counter() - t0
    save(city, seed, st)


# ---------------------------------------------------------------------------------------------------------------
# Part 2a: D2 on tiny games and gadgets
# ---------------------------------------------------------------------------------------------------------------


def prop71_game(w=1.0):
    g = cr.ExplicitGame.from_profits([1.0], [[[1], [3]], [[1], [3]]], [[[4], [1]], [[1], [4]]], [[6, 0], [0, 6]],
                                     names=[["A1", "B1"], ["X", "Y"]])
    return g, np.array([float(w)])


def kernel_game(n, arcs):
    """Theorem 7.3 construction: one zone per arc, carrier plans 'out' (all 0) and 'in' (pi = 1, vehicles/exposure on its arcs)."""
    ne = len(arcs)
    indeg = np.zeros(n, int)
    for (_, v) in arcs:
        indeg[v] += 1
    eta = 1.0 / (2 * max(1, indeg.max()) + 2)
    a_in = [np.zeros(ne) for _ in range(n)]
    f_in = [np.zeros(ne) for _ in range(n)]
    for e, (u, v) in enumerate(arcs):
        a_in[u][e], f_in[u][e] = 1.0, 1.0
        a_in[v][e], f_in[v][e] = 2.0, eta
    a = [[np.zeros(ne), a_in[i]] for i in range(n)]
    f = [[np.zeros(ne), f_in[i]] for i in range(n)]
    pi = [[0.0, 1.0] for _ in range(n)]
    return cr.ExplicitGame.from_profits(np.ones(ne), a, f, pi, names=[[f"{i}:out", f"{i}:in"] for i in range(n)])


def kernels_of(n, arcs):
    out = []
    for mask in range(1 << n):
        S = {i for i in range(n) if mask >> i & 1}
        if any(u in S and v in S for (u, v) in arcs):
            continue
        if all(any(u == i and v in S for (u, v) in arcs) for i in range(n) if i not in S):
            out.append(tuple(int(i in S) for i in range(n)))
    return out


def profile_table(g, w, kinds=("E", "M", "ID")):
    """Exact thresholds of every pure profile of an ExplicitGame (cuts = all plans)."""
    tab = {}
    cuts = g.plans
    for idx in g.profiles():
        prof = g.profile(idx)
        th = cr.profile_thresholds(g, prof, w, kinds=kinds, cuts=cuts, iters=60)
        tab[idx] = th
    return tab


def kernel_checks(rows, nlist=((3, None), (4, 120), (5, 40)), seed=0):
    rng = np.random.default_rng(seed)
    for n, nsamp in nlist:
        pairs = [(u, v) for u in range(n) for v in range(n) if u != v]
        if nsamp is None:
            masks = range(1 << len(pairs))
        else:
            masks = [int(x) for x in rng.integers(0, 1 << len(pairs), nsamp)]
        for mk in masks:
            arcs = [pairs[k] for k in range(len(pairs)) if mk >> k & 1]
            if not arcs:
                continue
            outdeg = np.zeros(n, int)
            for (u, _) in arcs:
                outdeg[u] += 1
            dp = int(outdeg.max())
            pred = 1.0 / (2 * dp + 1)
            g = kernel_game(n, arcs)
            w = np.ones(len(arcs))
            tab = profile_table(g, w)
            ker = set(kernels_of(n, arcs))
            sigma = {tuple(k): i for i, k in enumerate(g.profiles())}  # profile index tuple -> position (indices are 0/1 = out/in)
            row = dict(n=n, arcs=len(arcs), max_outdeg=dp, pred_threshold=pred, n_kernels=len(ker), has_kernel=len(ker) > 0)
            for kind in ("E", "M", "ID"):
                row[f"delta0_{kind}"] = float(min(t[f"{kind}_max"] for t in tab.values()))
            for tag, dl in (("0", 0.0), ("below", 0.999 * pred), ("above", 1.5 * pred)):
                for kind in ("E", "M", "ID"):
                    S = {idx for idx, t in tab.items() if t[f"{kind}_max"] <= dl + 1e-9}
                    row[f"set_eq_{kind}_{tag}"] = bool(S == ker)
                Sg = set()
                for idx in tab:
                    prof = g.profile(idx)
                    if max(cr.gamma_regret(g, i, prof, w, dl) for i in range(n)) <= 1e-9:
                        Sg.add(idx)
                row[f"set_eq_G_{tag}"] = bool(Sg == ker)
            row["ok_existence"] = (row["delta0_E"] <= 1e-9) if row["has_kernel"] else (row["delta0_E"] >= pred - 1e-9)
            row["ok_sets"] = all(row[f"set_eq_{k}_{t}"] for k in ("E", "M", "ID", "G") for t in ("0", "below"))
            rows.append(row)
        log("kernel gadgets n=%d done" % n)


def random_explicit_checks(rows, N_games=400, D2=True, seed=1, N=3):
    """Random bilinear D2 (or D1) games: existence of pure NE, delta_0^E by enumeration, Thm 6.1 on verified relaxed equilibria."""
    rng = np.random.default_rng(seed)
    for it in range(N_games):
        d = int(rng.integers(1, 3))
        P = int(rng.integers(2, 4))
        M = rng.uniform(0.5, 1.5, d)
        w = rng.uniform(0.5, 2.0, d)
        a = [rng.integers(0, 4, (P, d)).astype(float) for _ in range(N)]
        phi = [rng.integers(0, 4, (P, d)).astype(float) for _ in range(N)] if D2 else [x.copy() for x in a]
        pi = [rng.uniform(0, 10, P) for _ in range(N)]
        g = cr.ExplicitGame.from_profits(M, a, phi, pi)
        tab = profile_table(g, w, kinds=("E",))
        d0 = min(t["E_max"] for t in tab.values())
        npne = sum(1 for t in tab.values() if t["E_max"] <= 1e-9)
        smax = cr.sigma_max(g, w)
        bN = cr.n_uniform_bound(N, d, smax)
        pures = [g.profile(idx) for idx in sorted(tab, key=lambda k: tab[k]["E_max"])[:12]]
        cands = cr.mixed_candidates(g, pures)
        nan_, ver, viol_hat, viol_bound, viol_d0 = 0, 0, 0, 0, 0
        worst_ratio, bounds_ratio = 0.0, 0.0
        sigs = set()
        for support, weights, S in cands[:60]:
            sig = tuple(tuple(sorted((p.name, round(float(x), 6)) for p, x in zip(sp, wt))) for sp, wt in zip(support, weights))
            if sig in sigs:
                continue
            sigs.add(sig)
            if cr.check_relaxed(g, support, weights) > 1e-7:
                continue
            ver += 1
            st = cr.anchored_stats(g, support, weights, w, d=d)
            allp = cr.profiles_in_support(support, cap=4096)
            dh = [cr.delta_hat(pf, st["abar"], w) for pf in allp]
            for pf, h in zip(allp, dh):
                idx = tuple(next(k for k, q in enumerate(g.plans[i]) if q.name == pf[i].name) for i in range(N))
                if tab[idx]["E_max"] > h + 1e-7:
                    viol_hat += 1
                if tab[idx]["E_max"] > 1e-9 and h > 1e-9:
                    worst_ratio = max(worst_ratio, tab[idx]["E_max"] / h)
            if min(dh) > st["bound"] + 1e-7:
                viol_bound += 1
            if d0 > min(dh) + 1e-7:
                viol_d0 += 1
            if st["bound"] > 1e-9:
                bounds_ratio = max(bounds_ratio, min(dh) / st["bound"])
        rows.append(dict(regime="D2" if D2 else "D1", N=N, d=d, P=P, no_pne=bool(npne == 0), n_pne=npne, delta0_E=d0, sigma_max=smax,
                         bound_N=bN, ok_boundN=bool(d0 <= bN + 1e-7), n_relaxed_verified=ver, viol_E_le_hat=viol_hat,
                         viol_minhat_le_bound=viol_bound, viol_d0_le_minhat=viol_d0, max_ratio_E_over_hat=worst_ratio,
                         max_ratio_minhat_over_bound=bounds_ratio))
    log("random explicit", "D2" if D2 else "D1", "done", N_games)


def integrated_tiny_checks(rows, nseeds=60, scales=(1, 30, 1000)):
    cfgs = [("tiny N3 Z6 n3", lambda s: zb.make_tiny_game(N=3, Z=6, n_cust=3, seed=s), d2.explicit_from_game),
            ("tiny N4 Z6 n2", lambda s: zb.make_tiny_game(N=4, Z=6, n_cust=2, seed=s), d2.explicit_from_game),
            ("dup-zone N3 Z2 n3", lambda s: d2.make_tiny_game_dup(N=3, Z=2, n_cust=3, seed=s, hvar=2.0, cap=12.0), d2.explicit_partitions)]
    for name, mk, enum in cfgs:
        for s in range(nseeds):
            g1 = mk(s)
            e1 = enum(g1)
            n1 = len(d2.pure_nash(e1))
            for sc in scales:
                G = d2.to_d2(g1, sc)
                e2 = enum(G)
                pne = d2.pure_nash(e2)
                row = dict(config=name, seed=s, scale=sc, N=G.N, Z=G.Z, plans=int(np.prod([len(p) for p in e2.plans])),
                           n_pne_D1=n1, n_pne_D2=len(pne), no_pne_D2=len(pne) == 0)
                if len(pne) == 0:
                    w = cr.make_weights(G, [pl[0] for pl in e2.plans] if False else [G.empty_plan(i) for i in range(G.N)], "coord_cap")
                    tab = profile_table(e2, w, kinds=("E",))
                    row["delta0_E"] = min(t["E_max"] for t in tab.values())
                    row["bound_N"] = cr.n_uniform_bound(G.N, G.d, cr.sigma_max(e2, w))
                else:
                    row["delta0_E"] = 0.0
                rows.append(row)
        log("integrated tiny", name, "done")


def d2tiny():
    out = RES / "theory_D2_tiny.csv"
    if out.exists():
        log("theory_D2_tiny.csv exists, skipping (delete to rerun)")
        return
    t0 = time.perf_counter()
    # Prop 7.1
    p71 = []
    for w in (0.5, 1.0, 2.0):
        g, wv = prop71_game(w)
        tab = profile_table(g, wv)
        d0 = {k: min(t[f"{k}_max"] for t in tab.values()) for k in ("E", "M", "ID")}
        support = [list(g.plans[0]), list(g.plans[1])]
        weights = [[0.5, 0.5], [0.5, 0.5]]
        viol = cr.check_relaxed(g, support, weights)
        st = cr.anchored_stats(g, support, weights, wv, d=1)
        allp = cr.profiles_in_support(support, cap=64)
        dh = [cr.delta_hat(pf, st["abar"], wv) for pf in allp]
        p71.append(dict(w=w, n_pne=sum(1 for t in tab.values() if t["E_max"] <= 1e-9), delta0_E=d0["E"], delta0_M=d0["M"],
                        delta0_ID=d0["ID"], predicted=1.0 / w, rho_bar=st["rho_bar"], bound_T1=st["T1"], min_delta_hat=min(dh),
                        relaxed_violation=viol, ok=bool(abs(d0["E"] - 1 / w) < 1e-6 and abs(d0["M"] - 1 / w) < 1e-6)))
    write_csv(RES / "theory_D2_prop71.csv", p71)
    log("Prop 7.1:", [(r["w"], round(r["delta0_E"], 6), r["predicted"]) for r in p71])
    ker = []
    kernel_checks(ker)
    write_csv(RES / "theory_D2_kernels.csv", ker)
    rnd = []
    random_explicit_checks(rnd, 400, D2=True, seed=1)
    random_explicit_checks(rnd, 150, D2=False, seed=2)
    write_csv(RES / "theory_D2_random_explicit.csv", rnd)
    itg = []
    integrated_tiny_checks(itg)
    write_csv(out, itg)
    log("d2tiny finished in %.0f s" % (time.perf_counter() - t0))


# ---------------------------------------------------------------------------------------------------------------
# Part 2b: D2 on real cities
# ---------------------------------------------------------------------------------------------------------------

D2_SCALES = (1.0, 10.0, 100.0)


def d2city(city, seeds, budget=900.0):
    path = RES / f"theory_D2_{city}.csv"
    from common import read_rows
    rows = read_rows(path)
    done = {(int(r["seed"]), float(r["scale"])) for r in rows if r.get("kind") == "summary"}
    for seed in seeds:
        todo = [sc for sc in D2_SCALES if (seed, sc) not in done]
        if not todo:
            continue
        st = load(city, seed)
        g = zb.build_city_game(city, n_cust=NCUST, seed=seed)
        if "solve" not in st:
            stage_solve(g, st, city, seed)
        rng = np.random.default_rng(77 + seed)
        for sc in todo:
            t0 = time.perf_counter()
            G = d2.to_d2(g, sc)
            pD1 = rebuild(G, st["solve"]["p0"])
            start = rebuild(G, st["solve"]["start"])
            regD1 = G.regrets(pD1, count=False)
            w = cr.make_weights(G, pD1, "agg")
            thD1 = cr.profile_thresholds(G, pD1, w, kinds=("E", "M", "ID"))
            thS = cr.profile_thresholds(G, start, w, kinds=("E", "M", "ID"))
            starts = [("D1_NE", pD1), ("zmc_start", start), ("standalone", [G.br(i, np.zeros(G.d), count=True) for i in range(G.N)]),
                      ("rand", [pD1[i] if rng.random() < 0.5 else G.empty_plan(i) for i in range(G.N)])]
            statuses, pures = [], []
            for name, s in starts:
                if time.perf_counter() - t0 > budget:
                    break
                trail = []
                res = cr.br_run(G, s, rng=rng, max_rounds=40, trail=trail)
                reg = float(G.regrets(res["profile"], count=False).max()) if res["status"] == "converged" else np.nan
                ev = G.evaluate(res["profile"])
                moved = sum(cr.plan_key(a) != cr.plan_key(b) for a, b in zip(res["profile"], pD1))
                rows.append(dict(kind="br", city=city, seed=seed, scale=sc, start=name, status=res["status"], rounds=res["rounds"],
                                 cycle_len=res["cycle_len"], calls=res["calls"], max_regret=reg, carriers_changed_vs_D1NE=int(moved),
                                 served_share=ev["served_share"], welfare=ev["welfare"]))
                statuses.append(res["status"])
                if res["status"] == "converged" and reg < 1e-6:
                    pures.append(res["profile"])
                if res["status"] != "converged":
                    # relaxed equilibrium on the cycle: pairs of distinct profiles of the trail
                    uniq = list({cr.profile_key(p): p for p in trail}.values())[-8:]
                    cands = cr.mixed_candidates(G, uniq)
                    for support, weights, S in cands[:6]:
                        if cr.check_relaxed(G, support, weights) <= 1e-6:
                            stt = cr.anchored_stats(G, support, weights, w, d=G.d)
                            allp = cr.profiles_in_support(support, cap=64)
                            for pf in allp[:16]:
                                th = cr.profile_thresholds(G, pf, w, kinds=("E",))
                                rows.append(dict(kind="cycle_anchor", city=city, seed=seed, scale=sc, start=name,
                                                 delta_hat=cr.delta_hat(pf, stt["abar"], w), delta_E=th["E_max"], bound=stt["bound"]))
                            break
            rows.append(dict(kind="summary", city=city, seed=seed, scale=sc, N=G.N, Z=G.Z, n_starts=len(statuses),
                             n_converged=sum(s == "converged" for s in statuses), n_cycle=sum(s == "cycle" for s in statuses),
                             n_budget=sum(s == "budget" for s in statuses), n_distinct_pne=len({cr.profile_key(p) for p in pures}),
                             regret_D1NE_under_D2=float(regD1.max()), D1NE_is_D2_NE=bool(regD1.max() < 1e-6),
                             delta_E_D1NE=thD1["E_max"], delta_M_D1NE=thD1["M_max"], delta_ID_D1NE=thD1["ID_max"],
                             delta_E_zmc_start=thS["E_max"], delta_M_zmc_start=thS["M_max"], delta_ID_zmc_start=thS["ID_max"],
                             time_s=time.perf_counter() - t0))
            write_csv(path, rows)
            log(city, seed, "D2 scale", sc, "converged %d/%d" % (sum(s == "converged" for s in statuses), len(statuses)),
                "D1-NE regret under D2 %.3g" % regD1.max(), "%.0f s" % (time.perf_counter() - t0))


# ---------------------------------------------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------------------------------------------


def anchor_summary(df):
    """One row per (city, seed, w_mode, anchor) from the profile-level rows."""
    import pandas as pd

    out = []
    d = df[df.anchor != "zmc_start"]
    for (city, seed, wm, an), x in d.groupby(["city", "seed", "w_mode", "anchor"]):
        ps = x.loc[x.delta_hat.idxmin()]  # p*: the profile of the construction (minimal anchored radius)
        fin = x[np.isfinite(x.delta_E)]
        pos = x[(x.delta_E > 1e-9) & (x.delta_hat > 1e-9)]
        b = float(x.bound.iloc[0])
        out.append(dict(
            city=city, seed=seed, w_mode=wm, anchor=an, N=int(x.N.iloc[0]), Z=int(x.Z.iloc[0]), d=int(x.d.iloc[0]), n_mixers=int(x.n_mixers.iloc[0]),
            n_profiles=int(x.prod_size.iloc[0]), n_measured=len(x), rho_bar=x.rho_bar.iloc[0], sigma_bar=x.sigma_bar.iloc[0],
            d_L=x.d_L.iloc[0], k_sharp=x.k_sharp.iloc[0], bound_anchor=b, bound_N=float(x.bound_N.iloc[0]), sigma_max=float(x.sigma_max.iloc[0]),
            min_delta_hat=float(x.delta_hat.min()), E_at_pstar=float(ps.delta_E), E_max=float(fin.delta_E.max()), E_median=float(fin.delta_E.median()),
            ratio_pstar_E_over_bound=(float(ps.delta_E) / b if b > 1e-9 else np.nan),
            ratio_minhat_over_bound=(float(x.delta_hat.min()) / b if b > 1e-9 else np.nan),
            ratio_Emax_over_bound=(float(fin.delta_E.max()) / b if b > 1e-9 else np.nan),
            ratio_Emax_over_boundN=float(fin.delta_E.max()) / float(x.bound_N.iloc[0]),
            ratio_E_over_hat_max=(float((pos.delta_E / pos.delta_hat).max()) if len(pos) else np.nan),
            ratio_E_over_hat_median=(float((pos.delta_E / pos.delta_hat).median()) if len(pos) else np.nan),
            viol_E_le_hat=int((x.delta_E > x.delta_hat + TOL).sum()),
            viol_minhat_le_bound=int(x.delta_hat.min() > b + TOL),
            viol_E_le_boundN=int((fin.delta_E.min() > float(x.bound_N.iloc[0]) + TOL)),
            viol_order=int(((x.delta_M > x.delta_E + 1e-4) | (x.delta_ID > x.delta_M + 1e-4)).sum()),
            n_E_infinite=int((~np.isfinite(x.delta_E)).sum())))
    res = pd.DataFrame(out)
    key = ["city", "seed", "w_mode", "rho_bar", "bound_anchor", "min_delta_hat", "E_max"]
    return res.drop_duplicates(subset=key).reset_index(drop=True)  # anchors with identical support products are listed once


def report():
    import pandas as pd

    allrows, gam, solve = [], [], []
    for f in sorted(CACHE.glob("*_s?.json")):
        city, seed = f.stem.rsplit("_s", 1)
        st = json.loads(f.read_text())
        for k, v in st.items():
            if k.startswith("rows_"):
                allrows.extend(v)
        gam.extend(st.get("gamma_rows", []))
        if "solve" in st:
            solve.append(dict(city=city, seed=int(seed), **{k: v for k, v in st["solve"].items() if not isinstance(v, (list, dict))},
                              n_pure_ne=len(st.get("pures", {}).get("routes", [])), n_mixed_anchors=len(st.get("mixed", {}).get("items", [])),
                              n_mixed_candidates=st.get("mixed", {}).get("n_candidates", np.nan)))
    if not allrows:
        print("nothing to report")
        return
    df = pd.DataFrame(allrows)
    for city, x in df.groupby("city"):
        write_csv(RES / f"theory_absorption_{city}.csv", x.to_dict("records"))
    summ = anchor_summary(df)
    write_csv(RES / "theory_absorption_summary.csv", summ.to_dict("records"))
    write_csv(RES / "theory_absorption_equilibria.csv", solve)
    G = pd.DataFrame(gam)
    for city, x in G.groupby("city"):
        write_csv(RES / f"theory_gamma_{city}.csv", x.to_dict("records"))
    # ---- summary_theory.csv (one row per city)
    rows = []
    sv = pd.DataFrame(solve)
    for city in [c for c in CITIES if c in set(sv.city)]:
        r = dict(city=city, N=int(sv[sv.city == city].N.iloc[0]), Z=int(sv[sv.city == city].Z.iloc[0]), n_seeds=int((sv.city == city).sum()))
        s_ = sv[sv.city == city]
        r.update(served_share_mean=s_.served_share.mean(), n_pure_ne_mean=s_.n_pure_ne.mean(), seeds_with_mixed_anchor=int((s_.n_mixed_anchors > 0).sum()))
        for wm in ("agg", "type_median"):
            a = summ[(summ.city == city) & (summ.w_mode == wm)]
            m = a[a.anchor != "pure"]
            r[f"{wm}_n_mixed_anchors"] = len(m)
            r[f"{wm}_viol_total"] = int(a[["viol_E_le_hat", "viol_minhat_le_bound", "viol_E_le_boundN"]].sum().sum())
            if len(m):
                r[f"{wm}_rho_bar"] = m.rho_bar.mean()
                r[f"{wm}_dL"] = m.d_L.mean()
                r[f"{wm}_bound_anchor"] = m.bound_anchor.mean()
                r[f"{wm}_bound_N"] = m.bound_N.mean()
                r[f"{wm}_min_delta_hat"] = m.min_delta_hat.mean()
                r[f"{wm}_E_max"] = m.E_max.mean()
                r[f"{wm}_ratio_pstar_E_over_bound"] = m.ratio_pstar_E_over_bound.mean()
                r[f"{wm}_ratio_Emax_over_bound"] = m.ratio_Emax_over_bound.mean()
                r[f"{wm}_ratio_Emax_over_boundN"] = m.ratio_Emax_over_boundN.mean()
                r[f"{wm}_ratio_E_over_hat_max"] = m.ratio_E_over_hat_max.max()
        z = df[(df.city == city) & (df.anchor == "zmc_start") & (df.w_mode == "agg")]
        if len(z):
            r["zmc_start_delta_E_mean"] = z.delta_E.mean()
            r["zmc_start_delta_E_max"] = z.delta_E.max()
        g_ = G[G.city == city] if len(G) else G
        for de in GAMMA_DELTAS:
            q = g_[np.isclose(g_.delta, de)] if len(g_) else g_
            if len(q):
                r[f"gamma{de}_served_drop"] = float((q.served_NE - q.served_G).mean())
                r[f"gamma{de}_NE_gamma_regret"] = float(q.gamma_regret_NE.mean())
                r[f"gamma{de}_Mthr_over_delta"] = float((q.M_thr_G / de).mean())
        d2p = RES / f"theory_D2_{city}.csv"
        if d2p.exists():
            D = pd.read_csv(d2p)
            S = D[D.kind == "summary"]
            for sc, q in S.groupby("scale"):
                r[f"D2x{sc:g}_converged_frac"] = float(q.n_converged.sum() / max(q.n_starts.sum(), 1))
                r[f"D2x{sc:g}_cycles"] = int(q.n_cycle.sum() + q.n_budget.sum())
                r[f"D2x{sc:g}_D1NE_is_D2NE_frac"] = float(q.D1NE_is_D2_NE.mean())
                r[f"D2x{sc:g}_deltaE_D1NE_max"] = float(q.delta_E_D1NE.max())
                r[f"D2x{sc:g}_deltaE_start_max"] = float(q.delta_E_zmc_start.max())
        rows.append(r)
    write_csv(RES / "summary_theory.csv", rows)
    make_figures(summ, G)
    print("report written:", len(df), "profile rows,", len(summ), "anchor rows")


def make_figures(summ, G):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    a = summ[(summ.w_mode == "agg") & (summ.anchor != "pure")]
    if len(a):
        cities = [c for c in CITIES if c in set(a.city)]
        col = dict(bN="#9a9a9a", b="#1b6ca8", hat="#d98e04", E="#c0392b")
        fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.8), gridspec_kw=dict(width_ratios=[1.6, 1]))
        floor = 1e-3
        for k, c in enumerate(cities):
            x = a[a.city == c]
            for key, off, m, lab in (("bound_N", -0.27, "_", "N-uniform bound"), ("bound_anchor", -0.09, "_", "anchored 3-term bound"),
                                     ("min_delta_hat", 0.09, "o", "min delta_hat(p)"), ("E_max", 0.27, "s", "empirical delta_E (worst p in prod B_j)")):
                cc = {"bound_N": col["bN"], "bound_anchor": col["b"], "min_delta_hat": col["hat"], "E_max": col["E"]}[key]
                y = np.maximum(x[key].to_numpy(float), floor)
                ax[0].plot(np.full(len(y), k + off), y, m, color=cc, ms=(11 if m == "_" else 5), mew=1.5, alpha=0.8,
                           label=lab if k == 0 else None, ls="none")
        ax[0].set_yscale("log")
        ax[0].set_xticks(range(len(cities)))
        ax[0].set_xticklabels(cities, rotation=30)
        ax[0].set_ylabel("credal width delta (units of w)")
        ax[0].set_title("Absorption on real equilibria (mixed relaxed equilibria, seeds 0-2)")
        ax[0].legend(frameon=False, fontsize=8, loc="upper left")
        ax[0].grid(axis="y", alpha=0.25)
        ratio = a.ratio_Emax_over_bound
        for c, mk in zip(cities, "os^Dv<>pP*"):
            x = a[a.city == c]
            ax[1].plot(x.N * 0 + x.d, x.ratio_Emax_over_bound, mk, ms=5, alpha=0.8, label=c)
        ax[1].set_xscale("log")
        ax[1].set_yscale("log")
        ax[1].axhline(1.0, color="k", lw=1)
        ax[1].set_xlabel("d = 2Z")
        ax[1].set_ylabel("max_p delta_E / anchored bound")
        ax[1].set_title("Ratio empirical/bound (<1: bound holds)")
        ax[1].legend(frameon=False, fontsize=7, ncol=2)
        ax[1].grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(FIG / "theory_absorption.png", dpi=150)
        plt.close(fig)
    # D2 figure (if city D2 data exist)
    import pandas as pd

    S = []
    for c in CITIES:
        p = RES / f"theory_D2_{c}.csv"
        if p.exists():
            D = pd.read_csv(p)
            S.append(D[D.kind == "summary"])
    if S:
        S = pd.concat(S)
        fig, ax = plt.subplots(1, 2, figsize=(10.5, 4))
        for c, x in S.groupby("city"):
            g_ = x.groupby("scale").agg(conv=("n_converged", "sum"), n=("n_starts", "sum"), dE=("delta_E_D1NE", "max"))
            ax[0].plot(g_.index, g_.conv / g_.n, "o-", label=c)
            ax[1].plot(g_.index, np.maximum(g_.dE, 1e-9), "s-", label=c)
        ax[0].set_xscale("log")
        ax[0].set_ylim(-0.05, 1.05)
        ax[0].set_xlabel("vehicle-count externality scale")
        ax[0].set_ylabel("share of best-response runs that converge")
        ax[1].set_xscale("log")
        ax[1].set_yscale("log")
        ax[1].set_xlabel("vehicle-count externality scale")
        ax[1].set_ylabel("delta_E of the D1 equilibrium under D2")
        ax[0].legend(frameon=False)
        for a_ in ax:
            a_.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(FIG / "theory_D2.png", dpi=150)
        plt.close(fig)


# ---------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("city", nargs="?")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--budget", type=float, default=240.0)
    ap.add_argument("--max-starts", type=int, default=10)
    a = ap.parse_args()
    if a.cmd == "absorb":
        absorb(a.city, a.seeds, a.budget, a.max_starts)
    elif a.cmd == "report":
        report()
    elif a.cmd == "d2tiny":
        d2tiny()
    elif a.cmd == "d2city":
        d2city(a.city, a.seeds)
