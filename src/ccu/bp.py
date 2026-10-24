"""Branch-and-price for the BRL routing problem: an exact integer method on top of the exact BRL pricer.

Problem (same as `ccu.brl.RoutePool`).  Customers 1..n, depot 0, routes with exact p-box route costs c_r (BRL,
Theorem 2.1).  Either
    packing    min  sum_r (c_r + sum_{j in r} kappa_j) x_r   s.t.  sum_{r: j in r} x_r <= 1   (customers are optional)
    partition  the same with  = 1  for every customer (all customers must be served; the metro study of the paper).

Scheme
  * node LP: restricted master over a global column pool shared by all nodes (a column is used at a node iff all its
    arcs are allowed there), solved by column generation with the exact BRL labelling pricer (`brl.espprc`, with the
    arc restrictions of the node and a return-time bound recomputed on the allowed arcs);
  * branching on the aggregated arc flow f_ij = sum_r a^r_ij x_r (i, j in {0..n}); the pricing problem is unchanged:
        f_ij = 0 :  arc (i, j) removed from the graph;
        f_ij = 1 :  every other arc leaving i (i != 0) and every other arc entering j (j != 0) is removed, and the
                    customer i (or j if i = 0) gets an equality row ("served").  A forced arc therefore changes only
                    the pricing graph and the sense of one master row;
  * integral arc flows imply an integral x (every customer has in-flow <= 1, so every route is determined), hence no
    other branching is needed; fractional ng-route (non-elementary) columns are removed by enlarging the ng-sets
    (`augment_ng`), which keeps all earlier bounds valid;
  * node selection: best bound (lowest node bound first, deeper first on ties);
  * lower bounds: the node LP value at convergence; during column generation the Lagrangian bound
        z_LP + n * min(0, min reduced cost)           (every plan has at most n routes)
    is used for early pruning.  They are valid only if no pricing call hits the label limit (`bound_valid`);
  * upper bounds: integral nodes, and a restricted master MILP over the generated elementary columns (root and every
    `mip_every` nodes) with reduced-cost fixing from the root duals;
  * infeasible nodes are handled by one big-M artificial column per equality row, which keeps every node bound valid
    (the artificial relaxation only lowers the optimum), so no separate infeasibility test is needed.

Result: proven optimum (relative gap <= gap_tol) or an explicit remaining gap `ub - lb` with the status
'optimal' / 'time_limit' / 'node_limit'.  The bound is for the problem in which routes are elementary, since ng-routes
are a relaxation of elementary routes.
"""
from __future__ import annotations

import heapq
import math
import time
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp

from . import brl


@dataclass
class BPResult:
    routes: list
    value: float  # best integer objective found (upper bound)
    lb: float  # global lower bound (valid iff bound_valid)
    bound_valid: bool
    status: str  # 'optimal' | 'time_limit' | 'node_limit'
    root_lp: float  # LP value at the end of column generation at the root (before any ng enlargement)
    root_lp_final: float  # root LP after ng enlargement at the root (== root_lp if none)
    pb_value: float  # price-and-branch value: MILP over the columns generated at the root
    nodes: int
    n_pricing: int
    pricing_time: float
    time: float
    n_cols: int
    max_labels: int = 0
    ng_aug: int = 0
    root_time: float = 0.0
    nodes_open: int = 0
    notes: list = field(default_factory=list)
    pb_routes: list = field(default_factory=list)

    @property
    def gap(self) -> float:
        return max(self.value - self.lb, 0.0)

    @property
    def rel_gap(self) -> float:
        return self.gap / max(1.0, abs(self.value))


def _cmin_allowed(inst: brl.RoutingInstance, allow: np.ndarray):
    """Shortest return time to the depot on allowed arcs (level-0 quantile profile); customers that cannot return
    are cut off (all their arcs removed) until a fixed point.  Returns (allow', Cmin)."""
    n = inst.n
    allow = allow.copy()
    np.fill_diagonal(allow, False)
    c0 = inst.arcS[:, :, 0]
    while True:
        c = np.where(allow, c0, np.inf)
        dist = c[:, 0].copy()
        dist[0] = 0.0
        for _ in range(n + 1):
            dist = np.minimum(dist, np.min(c + dist[None, :], axis=1))
            dist[0] = 0.0
        dead = [j for j in range(1, n + 1) if not np.isfinite(dist[j]) and (allow[:, j].any() or allow[j, :].any())]
        if not dead:
            break
        for j in dead:
            allow[:, j] = False
            allow[j, :] = False
    out = np.where(np.isfinite(dist), dist, 1e15)
    return allow, out


class _Node:
    __slots__ = ("lb", "depth", "allow", "forced", "uid", "valid", "nvalid")

    def __init__(self, lb, depth, allow, forced, uid):
        self.lb, self.depth, self.allow, self.forced, self.uid = lb, depth, allow, forced, uid
        self.valid = None
        self.nvalid = 0


class BranchAndPrice:
    def __init__(self, inst: brl.RoutingInstance, kappa=None, *, partition: bool = False, ng_size: int = 8,
                 ng: np.ndarray | None = None, init_cols: dict | None = None, augment_ng: bool = True,
                 max_cols: int = 60, mip_every: int = 8, mip_time: float = 10.0, verbose: bool = False, log=None):
        self.inst = inst
        n = inst.n
        self.n = n
        kap = np.zeros(n + 1) if kappa is None else np.asarray(kappa, float).copy()
        kap[0] = 0.0
        self.kap = kap
        self.partition = partition
        self.ng = (brl.ng_masks(inst, ng_size) if ng is None else np.asarray(ng, np.uint64).copy())
        self.augment_ng = augment_ng
        self.max_cols = max_cols
        self.mip_every = mip_every
        self.mip_time = mip_time
        self.verbose = verbose
        self.log = log
        # global column pool
        self.R: list = []
        self.index: dict = {}
        self.cost = np.zeros(0)
        self.A = np.zeros((n, 0))
        self.arcs: list = []
        self.dead = np.zeros(0, bool)
        items = {(j,): None for j in range(1, n + 1)}
        if init_cols:
            for r, c in init_cols.items():
                if r not in items and self.ng_feasible(r):
                    items[r] = c
        self._bulk(items)
        scale = max(1.0, float(np.abs(self.cost).sum()) / max(1, len(self.cost)) * n + np.abs(kap).sum())
        self.M = 1e3 * scale
        self.UB = 0.0 if not partition else math.inf
        self.best_routes: list = []
        self.n_pricing = 0
        self.ptime = 0.0
        self.max_labels = 0
        self.bound_valid = True
        self.root_y = None
        self.root_z = None
        self.ng_aug = 0
        self.notes: list = []

    # ------------------------------------------------------------------ columns
    def ng_feasible(self, r) -> bool:
        mask = 0
        ng = self.ng
        for j in r:
            if (mask >> j) & 1:
                return False
            mask = (mask & int(ng[j])) | (1 << j)
        return True

    def _bulk(self, items: dict) -> None:
        routes = list(items)
        costs = np.array([self.inst.route_cost(r) if items[r] is None else items[r] for r in routes])
        A = np.zeros((self.n, len(routes)))
        for k, r in enumerate(routes):
            for j in r:
                A[j - 1, k] += 1.0
            p = (0, *r, 0)
            self.arcs.append([(p[t], p[t + 1]) for t in range(len(p) - 1)])
            self.index[r] = len(self.R)
            self.R.append(r)
        self.cost = costs
        self.A = A
        self.dead = np.zeros(len(routes), bool)

    def _add(self, r: tuple, cost: float | None = None) -> bool:
        if r in self.index:
            return False
        if cost is None:
            cost = self.inst.route_cost(r)
        col = np.zeros((self.n, 1))
        for j in r:
            col[j - 1, 0] += 1.0
        p = (0, *r, 0)
        self.index[r] = len(self.R)
        self.R.append(r)
        self.cost = np.append(self.cost, cost)
        self.A = np.hstack([self.A, col])
        self.arcs.append([(p[t], p[t + 1]) for t in range(len(p) - 1)])
        self.dead = np.append(self.dead, False)
        return True

    def _node_valid(self, node: _Node) -> np.ndarray:
        """Boolean mask of the global columns usable at `node` (extended lazily to new columns)."""
        m = len(self.R)
        if node.valid is None:
            node.valid = np.zeros(m, bool)
            node.nvalid = 0
        elif len(node.valid) < m:
            node.valid = np.concatenate([node.valid, np.zeros(m - len(node.valid), bool)])
        al = node.allow
        for k in range(node.nvalid, m):
            node.valid[k] = all(al[a, b] for a, b in self.arcs[k])
        node.nvalid = m
        return node.valid & ~self.dead

    # ------------------------------------------------------------------ master LP
    def _lp(self, node: _Node, idx: np.ndarray):
        n = self.n
        eq = np.zeros(n, bool)
        if self.partition:
            eq[:] = True
        for j in node.forced:
            eq[j - 1] = True
        A = self.A[:, idx]
        c = self.cost[idx] + self.kap[1:] @ A
        eqrows = np.flatnonzero(eq)
        ubrows = np.flatnonzero(~eq)
        if len(eqrows):
            E = np.zeros((n, len(eqrows)))
            E[eqrows, np.arange(len(eqrows))] = 1.0
            Af = np.hstack([A, E])
            cf = np.concatenate([c, np.full(len(eqrows), self.M)])
        else:
            Af, cf = A, c
        res = linprog(cf, A_ub=Af[ubrows] if len(ubrows) else None, b_ub=np.ones(len(ubrows)) if len(ubrows) else None,
                      A_eq=Af[eqrows] if len(eqrows) else None, b_eq=np.ones(len(eqrows)) if len(eqrows) else None,
                      bounds=(0, None), method="highs")
        if res.status != 0:
            raise RuntimeError(f"node LP failed: {res.message}")
        y = np.zeros(n)
        if len(ubrows):
            y[ubrows] = res.ineqlin.marginals
        if len(eqrows):
            y[eqrows] = res.eqlin.marginals
        x = res.x[: len(idx)]
        art = float(res.x[len(idx):].sum()) if len(eqrows) else 0.0
        return float(res.fun), x, y, art, c

    # ------------------------------------------------------------------ node column generation
    def _price(self, node: _Node, duals: np.ndarray, Cmin: np.ndarray):
        best, new, st = brl.espprc(self.inst, duals, ng=self.ng, max_cols=self.max_cols, allow=node.allow, Cmin=Cmin)
        self.n_pricing += 1
        self.ptime += st["time"]
        self.max_labels = max(self.max_labels, st["kept"])
        if st["overflow"]:
            self.bound_valid = False
        return best, new

    gap_tol = 1e-6

    def _gap_tol(self):
        return self.gap_tol * max(1.0, abs(self.UB)) if math.isfinite(self.UB) else 0.0

    def _solve_node(self, node: _Node, deadline: float, tol: float = 1e-9):
        """Column generation at a node.  Returns (status, z, x, idx, y, art); status in
        {'pruned', 'converged', 'timeout'}.  node.lb is raised as bounds are certified."""
        node.allow, Cmin = _cmin_allowed(self.inst, node.allow)
        it = 0
        while True:
            it += 1
            valid = self._node_valid(node)
            idx = np.flatnonzero(valid)
            z, x, y, art, c = self._lp(node, idx)
            duals = np.concatenate([[0.0], y - self.kap[1:]])
            best, new = self._price(node, duals, Cmin)
            lag = z + self.n * min(best, 0.0)
            node.lb = max(node.lb, lag)  # valid also with artificial columns (they are not in any feasible plan)
            if node.lb >= self.UB - self._gap_tol() - 1e-12:
                return "pruned", z, x, idx, y, art
            if best > -tol * (1.0 + abs(z)) - 1e-9 or not new:
                if art > 1e-6:
                    # artificial column in the optimum although the node bound is below the incumbent: M too small
                    self.M *= 100.0
                    self.notes.append("bigM raised")
                    if self.M > 1e12:
                        return "pruned", z, x, idx, y, art
                    continue
                return "converged", z, x, idx, y, art
            added = 0
            for rc, r in new:
                if rc < -1e-9 and self._add(r):
                    added += 1
            if added == 0:
                return "converged", z, x, idx, y, art
            if time.perf_counter() > deadline:
                return "timeout", z, x, idx, y, art

    # ------------------------------------------------------------------ integer heuristics
    def _milp(self, tlim: float):
        """Restricted master MILP over the generated elementary columns (reduced-cost fixing from the root duals)."""
        n = self.n
        ok = np.array([len(set(r)) == len(r) for r in self.R]) & ~self.dead
        idx = np.flatnonzero(ok)
        if len(idx) == 0:
            return
        A = self.A[:, idx]
        c = self.cost[idx] + self.kap[1:] @ A
        if self.root_y is not None and math.isfinite(self.UB):
            rc = c - self.root_y @ A
            keep = rc <= (self.UB - self.root_z) + 1e-7
            idx, A, c = idx[keep], A[:, keep], c[keep]
        if len(idx) == 0:
            return
        if self.partition:
            cons = LinearConstraint(A, lb=np.ones(n), ub=np.ones(n))
        else:
            cons = LinearConstraint(A, ub=np.ones(n))
        m = milp(c, constraints=cons, integrality=np.ones(len(idx)), bounds=Bounds(0, 1),
                 options={"time_limit": tlim, "mip_rel_gap": 1e-9})
        if m.x is None:
            return
        sel = [self.R[idx[k]] for k in np.flatnonzero(m.x > 0.5)]
        val = float(sum(self.cost[self.index[r]] + sum(self.kap[j] for j in r) for r in sel))
        self._update_ub(val, sel)

    def _update_ub(self, val, routes):
        if val < self.UB - 1e-9:
            self.UB = val
            self.best_routes = list(routes)

    # ------------------------------------------------------------------ branching
    def _arc_flows(self, idx, x):
        n = self.n
        f = np.zeros((n + 1, n + 1))
        for k in np.flatnonzero(x > 1e-9):
            for a, b in self.arcs[idx[k]]:
                f[a, b] += x[k]
        return f

    @staticmethod
    def _child(node: _Node, i: int, j: int, force: bool, uid: int, lb: float):
        al = node.allow.copy()
        forced = set(node.forced)
        was = bool(node.allow[i, j])
        if not force:
            al[i, j] = False
        else:
            if i != 0:
                al[i, :] = False
                forced.add(i)
            if j != 0:
                al[:, j] = False
                if i == 0:
                    forced.add(j)
            al[i, j] = was
        return _Node(lb, node.depth + 1, al, frozenset(forced), uid)

    def _nonelementary(self, idx, x):
        for k in np.flatnonzero(x > 1e-7):
            r = self.R[idx[k]]
            if len(set(r)) < len(r):
                return r
        return None

    def _augment(self, r) -> bool:
        pos = {}
        changed = False
        for t, j in enumerate(r):
            if j in pos:
                a = pos[j]
                for q in range(a + 1, t):
                    v = r[q]
                    if not (int(self.ng[v]) >> j) & 1:
                        self.ng[v] = np.uint64(int(self.ng[v]) | (1 << j))
                        changed = True
                break
            pos[j] = t
        if changed:
            for k, rr in enumerate(self.R):
                if not self.dead[k] and not self.ng_feasible(rr):
                    self.dead[k] = True
            self.ng_aug += 1
        return changed

    # ------------------------------------------------------------------ main loop
    def run(self, *, time_limit: float = 600.0, node_limit: int = 100000, gap_tol: float = 1e-6) -> BPResult:
        t0 = time.perf_counter()
        deadline = t0 + time_limit
        self.gap_tol = gap_tol
        n = self.n
        allow0 = np.ones((n + 1, n + 1), bool)
        np.fill_diagonal(allow0, False)
        root = _Node(-math.inf, 0, allow0, frozenset(), 0)
        heap = [(-math.inf, 0, 0, root)]
        uid = 1
        nodes = 0
        root_lp = root_lp_final = math.nan
        pb_value = math.nan
        pb_routes = []
        root_time = 0.0
        status = "optimal"
        global_lb = -math.inf
        while heap:
            lbn, _, _, node = heapq.heappop(heap)
            gtol = gap_tol * max(1.0, abs(self.UB)) if math.isfinite(self.UB) else 0.0
            if node.lb >= self.UB - gtol:
                continue
            if time.perf_counter() > deadline:
                heapq.heappush(heap, (node.lb, 0, node.uid, node))
                status = "time_limit"
                break
            if nodes >= node_limit:
                heapq.heappush(heap, (node.lb, 0, node.uid, node))
                status = "node_limit"
                break
            nodes += 1
            # --- solve node LP (with ng enlargement loop)
            first = True
            while True:
                st, z, x, idx, y, art = self._solve_node(node, deadline)
                if nodes == 1 and first:
                    root_lp = z if st == "converged" else node.lb
                    first = False
                if st == "timeout":
                    heapq.heappush(heap, (node.lb, 0, node.uid, node))
                    status = "time_limit"
                    break
                if st == "pruned":
                    break
                if self.augment_ng and art <= 1e-7:
                    ne = self._nonelementary(idx, x)
                    if ne is not None and self._augment(ne):
                        continue
                break
            if st == "timeout":
                break
            if nodes == 1:
                root_lp_final = node.lb if st == "pruned" else z
                root_time = time.perf_counter() - t0
                if st == "converged":
                    self.root_y, self.root_z = y.copy(), z
                self._milp(self.mip_time)
                pb_value = self.UB
                pb_routes = list(self.best_routes)
                if self.verbose or self.log:
                    self._say(f"root: lp {root_lp:.6f} (final {root_lp_final:.6f}) pb {pb_value:.6f} "
                              f"cols {len(self.R)} t {root_time:.1f}s")
            if st == "pruned":
                continue
            # --- integral?
            f = self._arc_flows(idx, x)
            frac = np.abs(f - np.round(f))
            if art <= 1e-7 and np.all(np.abs(x - np.round(x)) < 1e-6):
                sel = [self.R[idx[k]] for k in np.flatnonzero(x > 0.5)]
                val = float(sum(self.cost[self.index[r]] + sum(self.kap[j] for j in r) for r in sel))
                self._update_ub(val, sel)
                continue
            if nodes % self.mip_every == 0:
                self._milp(self.mip_time)
                if node.lb >= self.UB - gap_tol * max(1.0, abs(self.UB)):
                    continue
            if frac.max() < 1e-6:
                # integral arc flows but fractional x: cannot happen for elementary columns; fall back to the MILP
                self.notes.append("integral flows, fractional x")
                self._milp(self.mip_time)
                continue
            # most fractional arc (largest min(f, 1-f)), ties by larger flow
            sc = np.minimum(f - np.floor(f), np.ceil(f) - f)
            i, j = np.unravel_index(int(np.argmax(sc + 1e-9 * f)), sc.shape)
            for force in (False, True):
                heapq.heappush(heap, (node.lb, -(node.depth + 1), uid, self._child(node, int(i), int(j), force, uid, node.lb)))
                uid += 1
            if self.verbose and nodes % 10 == 0:
                self._say(f"node {nodes} lb {node.lb:.5f} ub {self.UB:.5f} open {len(heap)} t {time.perf_counter() - t0:.0f}s")
        if heap:
            global_lb = min(h[3].lb for h in heap)
            global_lb = min(global_lb, self.UB)
        else:
            global_lb = self.UB
        if status == "optimal" and heap:
            status = "optimal"
        wall = time.perf_counter() - t0
        gap_ok = (self.UB - global_lb) <= gap_tol * max(1.0, abs(self.UB)) + 1e-12
        if status == "optimal" and not self.bound_valid:
            status = "label_overflow"
        if status != "optimal" and gap_ok and self.bound_valid:
            status = "optimal"
        return BPResult(self.best_routes, self.UB, global_lb, self.bound_valid, status, root_lp, root_lp_final, pb_value,
                        nodes, self.n_pricing, self.ptime, wall, len(self.R), self.max_labels, self.ng_aug, root_time,
                        len(heap), list(dict.fromkeys(self.notes)), pb_routes)

    def _say(self, msg):
        if self.log:
            self.log(msg)
        elif self.verbose:
            print(msg, flush=True)


def solve_bp(inst: brl.RoutingInstance, kappa=None, *, partition=False, ng_size=8, time_limit=600.0, node_limit=100000,
             gap_tol=1e-6, init_cols=None, **kw) -> BPResult:
    return BranchAndPrice(inst, kappa, partition=partition, ng_size=ng_size, init_cols=init_cols, **kw).run(
        time_limit=time_limit, node_limit=node_limit, gap_tol=gap_tol)


def solve_pool_bp(pool: brl.RoutePool, kappa, *, time_limit: float = 20.0, node_limit: int = 100000, gap_tol: float = 1e-6,
                  mip_time: float = 5.0) -> brl.PackResult:
    """Drop-in exact replacement of `RoutePool.solve` for the packing oracle: shares and extends the pool's columns.

    `PackResult.lp` is the global lower bound (the LP value when the root closes the gap), `bound_valid` is False if a
    pricing call overflowed.  Extra attribute `status` and `nodes` are attached.
    """
    bp = BranchAndPrice(pool.inst, kappa, partition=False, ng=pool.ng, init_cols=pool.cols, augment_ng=False,
                        mip_time=mip_time)
    # columns of the pool that are ng-feasible are kept; non-elementary ones are allowed since augment_ng is off
    res = bp.run(time_limit=time_limit, node_limit=node_limit, gap_tol=gap_tol)
    for r in bp.R:
        pool._add(r)
    if len(pool.cols) > pool.max_pool:
        pool._prune(res.routes)
    out = brl.PackResult(res.routes, min(res.value, 0.0), res.lb, res.bound_valid, res.n_pricing, len(pool.cols), res.pricing_time)
    out.status = res.status
    out.nodes = res.nodes
    out.pb_value = res.pb_value
    out.root_lp = res.root_lp
    return out


def exact_by_enumeration(inst: brl.RoutingInstance, kappa=None, partition=False):
    """Exact integer optimum by complete enumeration of all elementary routes (best order per customer subset) and an
    integer program over all subsets; for tests on small n.  Returns (value, routes)."""
    kap = np.zeros(inst.n + 1) if kappa is None else np.asarray(kappa, float)
    best = brl.enumerate_best_routes(inst)
    keys = list(best)
    routes = [best[k][1] for k in keys]
    A = np.zeros((inst.n, len(routes)))
    for k, r in enumerate(routes):
        for j in r:
            A[j - 1, k] = 1.0
    c = np.array([best[k][0] for k in keys]) + kap[1:] @ A
    cons = LinearConstraint(A, lb=np.ones(inst.n), ub=np.ones(inst.n)) if partition else LinearConstraint(A, ub=np.ones(inst.n))
    m = milp(c, constraints=cons, integrality=np.ones(len(routes)), bounds=Bounds(0, 1))
    sel = [routes[k] for k in np.flatnonzero(m.x > 0.5)]
    return float(m.fun), sel
