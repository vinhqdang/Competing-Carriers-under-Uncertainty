"""Test E: BRL column generation on the nine metro instances (data/processed/<City>/).

Calibration (stated assumptions, see results.md):
  * base arc time = free-flow zone-to-zone time (travel_time_matrix.npy, seconds), split half to the
    sector of each end zone; K = 9 sectors from k-means on zone coordinates;
  * true sector multiplier law: xi_k = m_k exp(s_c g + s_s e_k - (s_c^2 + s_s^2)/2), g, e_k iid N(0,1),
    mean m_k = 1 + TomTom all-day congestion (scaled 0.85-1.15 by sector centrality),
    total log-sd s such that the 0.95-quantile equals 1 + TomTom peak-hour congestion; s_c = 0.7 s;
  * the carrier observes n = 60 days; sector p-box = DKW band (alpha = 0.05) with support cap
    1 + 2 x peak congestion;
  * loss in driver-hour units: fixed 2 per route, gamma = 1 per hour, rho = 3 per hour beyond the
    shift length (TomTom-free city parameter shift_hours, default 8.4 h);
  * 22 customer zones drawn with probability proportional to population, 3-9 drops each,
    3 minutes per drop, vehicle capacity = drops_per_vehicle_per_day (default 70).
"""
from __future__ import annotations

import csv
import math
import time

import numpy as np
from scipy.optimize import linprog, milp, LinearConstraint, Bounds

from prototype import ROOT, Loss, Pricing, common_grid, cost_profile, dkw_upper_quantile, espprc, phi, route_profile, route_tau

CITIES = {"Berlin": "Berlin", "Bombay": "Mumbai", "BuenosAires": "Buenos Aires", "Cairo": "Cairo", "London": "London",
          "Moscow": "Moscow", "NewDelhi": "New Delhi", "NewYork": "New York", "Paris": "Paris"}


def city_params():
    out = {}
    for r in csv.DictReader(open(ROOT + "/data/parameters/city_parameters.csv")):
        try:
            v = float(r["value"])
        except ValueError:
            continue
        out.setdefault(r["city"], {})[r["parameter"]] = v
    return out


def kmeans(X, K, rng, it=50):
    C = X[rng.choice(len(X), K, replace=False)]
    for _ in range(it):
        lab = np.argmin(((X[:, None] - C[None]) ** 2).sum(-1), 1)
        C = np.array([X[lab == k].mean(0) if np.any(lab == k) else C[k] for k in range(K)])
    return lab, C


def build(city: str, ncust=22, K=9, ndays=60, seed=0):
    rng = np.random.default_rng(seed)
    pars = city_params()
    pc = pars.get(CITIES[city], {})
    allc = [p.get("tomtom_congestion_pct") for p in pars.values() if "tomtom_congestion_pct" in p]
    allp = [p.get("tomtom_peak_hour_congestion_pct") for p in pars.values() if "tomtom_peak_hour_congestion_pct" in p]
    cong = pc.get("tomtom_congestion_pct", float(np.mean(allc))) / 100
    peak = pc.get("tomtom_peak_hour_congestion_pct", float(np.mean(allp))) / 100
    shift = pc.get("shift_hours", 8.4) * 3600
    cap = pc.get("drops_per_vehicle_per_day", 70)
    rows = list(csv.DictReader(open(f"{ROOT}/data/processed/{city}/zones.csv")))
    xy = np.array([[float(r["lon"]), float(r["lat"])] for r in rows])
    pop = np.array([float(r["pop"]) for r in rows])
    ds = np.array([float(r["depot_score"]) for r in rows])
    TT = np.load(f"{ROOT}/data/processed/{city}/travel_time_matrix.npy").astype(float)
    depot = int(np.lexsort((pop, ds))[-1])
    p = pop.copy()
    p[depot] = 0
    cust = rng.choice(len(rows), ncust, replace=False, p=p / p.sum())
    nodes = np.concatenate([[depot], cust])
    lab, C = kmeans((xy - xy.mean(0)) / xy.std(0), K, rng)
    cen = np.linalg.norm(C, axis=1)
    m = 1 + cong * (1.15 - 0.3 * (cen - cen.min()) / (np.ptp(cen) + 1e-12))
    # total log-sd s from the peak quantile: m exp(1.645 s - s^2/2) = 1 + peak (use mean multiplier)
    target = math.log((1 + peak) / (1 + cong))
    s = 1.645 - math.sqrt(max(1.645**2 - 2 * target, 0.0))
    sc, ss = 0.7 * s, math.sqrt(max(s * s - (0.7 * s) ** 2, 0.0))

    def draw(N):
        g = rng.standard_normal((N, 1))
        e = rng.standard_normal((N, K))
        return m[None] * np.exp(sc * g + ss * e - 0.5 * (sc * sc + ss * ss))

    days = draw(ndays)
    true = draw(20000)
    xmax = 1 + 2 * peak
    qfs = [dkw_upper_quantile(days[:, k], 0.05, xmax) for k in range(K)]
    _, w, Qk = common_grid(qfs)
    n = ncust
    tau = np.zeros((n + 1, n + 1, K))
    for a in range(n + 1):
        for b in range(n + 1):
            if a != b:
                t = TT[nodes[a], nodes[b]]
                tau[a, b, lab[nodes[a]]] += t / 2
                tau[a, b, lab[nodes[b]]] += t / 2
    dem = np.concatenate([[0], rng.integers(3, 10, n)]).astype(float)
    svc = dem * 180.0
    loss = Loss(gamma=1 / 3600, rho=3 / 3600, Tmax=shift, fixed=2.0)
    P = Pricing(n, tau, svc, dem, float(cap), Qk, w, loss, np.zeros(n + 1), days)
    meta = {"city": city, "depot_zone": depot, "cong": cong, "peak": peak, "shift_h": shift / 3600, "cap": cap,
            "L": int(len(w)), "sigma_log": s, "total_drops": float(dem.sum())}
    return P, true, meta


# ------------------------------------------------------------------ route cost models


def make_costs(P: Pricing, true: np.ndarray, eps_w: float):
    cache = {}
    n_days = P.scen.shape[0]

    def tau_svc(r):
        return route_tau(P, r), float(P.svc[list(r)].sum())

    def cost(r, model):
        if not r:
            return 0.0
        key = (r, model)
        if key in cache:
            return cache[key]
        if model == "pbox":
            v = cost_profile(route_profile(P, r), P.w, P.loss)
        else:
            t, s = tau_svc(r)
            if model == "saa":
                v = float(np.mean(phi(P.scen @ t + s, P.loss)))
            elif model == "wass":  # src/ccu/robust.py closed form
                v = float(np.mean(phi(P.scen @ t + s, P.loss))) + eps_w * (P.loss.gamma + P.loss.rho) * float(t.max())
            elif model == "true":
                v = float(np.mean(phi(true @ t + s, P.loss)))
            elif model == "indep_pbox":  # worst marginals, independent sectors (precise-probability model)
                rng = np.random.default_rng(1)
                U = rng.uniform(size=(20000, len(t)))
                ends = np.cumsum(P.w)
                idx = np.minimum(np.searchsorted(ends, U), len(ends) - 1)
                X = P.Qk[np.arange(len(t))[None, :], idx]
                v = float(np.mean(phi(X @ t + s, P.loss)))
            else:
                raise ValueError(model)
        cache[key] = v
        return v

    return cost


def heuristic(P: Pricing, cost, model, rng, starts=3):
    """Clarke-Wright savings (mean times) + relocate / swap / 2-opt descent under the given cost model."""
    n = P.n
    D = P.tau.sum(-1)
    best_sol, best_val = None, math.inf
    for st in range(starts):
        routes = {j: [j] for j in range(1, n + 1)}
        rid = {j: j for j in range(1, n + 1)}
        sav = [(D[0, a] + D[0, b] - D[a, b] + (rng.normal(0, 60) if st else 0), a, b) for a in range(1, n + 1) for b in range(a + 1, n + 1)]
        sav.sort(reverse=True)
        for s, a, b in sav:
            ra, rb = rid[a], rid[b]
            if ra == rb or s <= 0:
                continue
            A, B = routes[ra], routes[rb]
            if P.dem[A].sum() + P.dem[B].sum() > P.cap:
                continue
            if A[-1] == a and B[0] == b:
                new = A + B
            elif A[0] == a and B[-1] == b:
                new = B + A
            elif A[0] == a and B[0] == b:
                new = A[::-1] + B
            elif A[-1] == a and B[-1] == b:
                new = A + B[::-1]
            else:
                continue
            if cost(tuple(new), model) > cost(tuple(A), model) + cost(tuple(B), model):
                continue
            routes[ra] = new
            del routes[rb]
            for j in new:
                rid[j] = ra
        sol = [r for r in routes.values()]
        val = sum(cost(tuple(r), model) for r in sol)
        improved = True
        while improved:
            improved = False
            # relocate
            for ri in range(len(sol)):
                for pos in range(len(sol[ri])):
                    c = sol[ri][pos]
                    rest = sol[ri][:pos] + sol[ri][pos + 1:]
                    base = cost(tuple(sol[ri]), model)
                    for rj in range(len(sol) + 1):
                        if rj == ri:
                            continue
                        tgt = sol[rj] if rj < len(sol) else []
                        if P.dem[tgt].sum() + P.dem[c] > P.cap if tgt else False:
                            continue
                        for q in range(len(tgt) + 1):
                            nt = tgt[:q] + [c] + tgt[q:]
                            d = cost(tuple(rest), model) + cost(tuple(nt), model) - base - cost(tuple(tgt), model)
                            if d < -1e-9:
                                sol[ri] = rest
                                if rj < len(sol):
                                    sol[rj] = nt
                                else:
                                    sol.append(nt)
                                sol = [r for r in sol if r]
                                improved = True
                                break
                        if improved:
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                continue
            # 2-opt within route
            for ri, r in enumerate(sol):
                for a in range(len(r)):
                    for b in range(a + 2, len(r) + 1):
                        nr = r[:a] + r[a:b][::-1] + r[b:]
                        if cost(tuple(nr), model) < cost(tuple(r), model) - 1e-9:
                            sol[ri] = nr
                            improved = True
                            break
                    if improved:
                        break
                if improved:
                    break
            if improved:
                continue
            # swap between routes
            for ri in range(len(sol)):
                for rj in range(ri + 1, len(sol)):
                    for a in range(len(sol[ri])):
                        for b in range(len(sol[rj])):
                            A, B = sol[ri][:], sol[rj][:]
                            A[a], B[b] = B[b], A[a]
                            if P.dem[A].sum() > P.cap or P.dem[B].sum() > P.cap:
                                continue
                            d = cost(tuple(A), model) + cost(tuple(B), model) - cost(tuple(sol[ri]), model) - cost(tuple(sol[rj]), model)
                            if d < -1e-9:
                                sol[ri], sol[rj] = A, B
                                improved = True
                                break
                        if improved:
                            break
                    if improved:
                        break
                if improved:
                    break
        val = sum(cost(tuple(r), model) for r in sol)
        if val < best_val:
            best_sol, best_val = [list(r) for r in sol], val
    return best_sol, best_val


def column_generation(P: Pricing, cost, init_routes, tl_total=1200.0, tl_price=300.0):
    n = P.n
    cols = {}
    for r in init_routes:
        cols[tuple(r)] = cost(tuple(r), "pbox")
    for j in range(1, n + 1):
        cols.setdefault((j,), cost((j,), "pbox"))
    t0 = time.perf_counter()
    it, price_time, lab_stats = 0, 0.0, []
    exact_bound = False
    while True:
        R = list(cols)
        c = np.array([cols[r] for r in R])
        A = np.zeros((n, len(R)))
        for k, r in enumerate(R):
            for j in r:
                A[j - 1, k] = 1
        res = linprog(c, A_ub=-A, b_ub=-np.ones(n), bounds=(0, None), method="highs")
        duals = np.concatenate([[0.0], -res.ineqlin.marginals])
        P.duals = duals
        tp = time.perf_counter()
        best, new, st = espprc(P, "functional", time_limit=tl_price, max_cols=40)
        price_time += time.perf_counter() - tp
        lab_stats.append(st["labels_kept"])
        it += 1
        if st["timed_out"]:
            break
        if best > -1e-7 * max(1, abs(res.fun)):
            exact_bound = True
            break
        added = 0
        for rc, r in new:
            if r not in cols:
                cols[r] = cost(r, "pbox")
                added += 1
        if added == 0 or time.perf_counter() - t0 > tl_total:
            break
    lp = float(res.fun)
    # price-and-branch: integer set covering over generated columns
    R = list(cols)
    c = np.array([cols[r] for r in R])
    A = np.zeros((n, len(R)))
    for k, r in enumerate(R):
        for j in r:
            A[j - 1, k] = 1
    m = milp(c, constraints=LinearConstraint(A, lb=np.ones(n), ub=np.inf), integrality=np.ones(len(R)), bounds=Bounds(0, 1),
             options={"time_limit": 300})
    sol = [list(R[k]) for k in np.flatnonzero(m.x > 0.5)]
    # covering may visit a customer twice; repair by dropping duplicates (never increases cost here: costs are monotone)
    seen, fixed = set(), []
    for r in sol:
        rr = [j for j in r if j not in seen]
        seen |= set(rr)
        if rr:
            fixed.append(rr)
    ub = sum(cost(tuple(r), "pbox") for r in fixed)
    return {"lp_bound": lp, "bound_is_exact": exact_bound, "ub": ub, "iters": it, "cols": len(cols),
            "time": time.perf_counter() - t0, "pricing_time": price_time, "max_labels_kept": int(max(lab_stats))}, fixed


def testE(cities=None, ncust=22):
    out = []
    for city in cities or list(CITIES):
        P, true, meta = build(city, ncust=ncust)
        cost = make_costs(P, true, eps_w=0.05)
        rng = np.random.default_rng(0)
        row = dict(meta)
        sols = {}
        for model in ("pbox", "saa", "wass"):
            t0 = time.perf_counter()
            sol, val = heuristic(P, cost, model, rng)
            sols[model] = sol
            row[f"heur_{model}_time"] = time.perf_counter() - t0
        cg, cg_sol = column_generation(P, cost, sols["pbox"])
        sols["brl_cg"] = cg_sol
        row["cg"] = cg
        for name, sol in sols.items():
            row[f"{name}_eval"] = {ev: sum(cost(tuple(r), ev) for r in sol) for ev in ("pbox", "indep_pbox", "saa", "true")}
            row[f"{name}_routes"] = len(sol)
        out.append(row)
        print(city, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in row["cg"].items()},
              {n: round(row[f"{n}_eval"]["pbox"], 3) for n in sols}, flush=True)
    return out


if __name__ == "__main__":
    import sys

    print(testE(sys.argv[1:] or ["Paris"]))
