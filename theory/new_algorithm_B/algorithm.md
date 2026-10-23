# BRL: Budget-Resource Labelling

Exact pricing (and column generation) for vehicle routing when arc travel times are given by p-boxes (DKW or imprecise-Dirichlet bands, or any lower/upper CDF pair with bounded support), the dependence between arcs is unknown, and the route loss is convex piecewise linear, e.g. `phi(T) = c0 + gamma*T + rho*max(0, T - Tmax)`. Proofs are in `theory.tex`; numbers are in `results.md`.

## 1. Structural theorem behind the method

For a route r with arc p-boxes and unknown dependence (Theorem 2.1 in `theory.tex`):

    sup_P E_P phi(T_r) = int_0^1 phi( sum_a Qbar_a(u) ) du
                       = c0 + sum_a gamma*mubar_a + rho * min { sum_a pibar_a(d_a) : sum_a d_a <= Tmax }

Here `Qbar_a` is the quantile of the lower CDF, `mubar_a` is its mean, and `pibar_a(d) = E_lowerCDF (X_a - d)^+` is convex, nonincreasing, with slope in [-1, 0]. The supremum is attained by the comonotone coupling. With integer data, an integer budget vector `d` is optimal.

Consequence (Theorem 2.5): the dependence-robust pricing problem is an ESPPRC with **one extra resource per kink of the loss** (kappa resources). The amount `d_a` of that resource used on arc a is a *decision*, paid through the convex arc cost `gamma*mubar_a + rho*pibar_a(d_a)`. The resource count does not depend on the number L of quantile levels, the sample size or the number of arcs.

Concatenating a partial path p with a completion q is an inf-convolution of their cost functions, `f_{p+q}(Tmax) = min_D f_p(D) + f_q(Tmax - D)` (Lemma 3.1). Because the slopes lie in [-rho, 0], the optimal split D lies in a *completion window* `J(p)` computable from p alone (Lemma 3.2).

## 2. Pseudo-code

```
BRL(graph, demands d, capacity Q, level weights w[1..L], arc level profiles q[a][1..L],
    gamma, rho, Tmax, c0, duals pi):
  Cmin[v] := shortest path v -> depot with arc lengths q[a][1]      # completion lower bound
  bucket[v] := {} for all v ; queue := { depot label (0, {}, 0, S=0 in R^L, pi=0) }
  while queue not empty:                                            # FIFO by #customers
    p := pop(queue); if p deleted: continue
    if p.v != depot: record route p+(v,0) with rc = c0 + f_{S_p + q[v,0]}(Tmax) - p.pi
    for j not in p.V with p.load + d_j <= Q:
      p' := (j, p.V+{j}, p.load+d_j, S_p + q[(v,j)], p.pi + pi_j)
      if exists o in bucket[j] with FDOM(o, p'): discard p'
      else: delete {o in bucket[j] : FDOM(p', o)}; insert p'; push p'
  return recorded routes sorted by rc

f_S(D) = gamma * sum_l w_l S_l + rho * sum_l w_l max(0, S_l - D)       # O(log L) via suffix sums

FDOM(a, b):  # a dominates b
  require a.V subset of b.V and a.load <= b.load
  h  := min(S_b[L], Tmax - Cmin[b.v]);  lo := min(S_b[1], h)            # window J(b) = [lo, h]
  pts := {lo, h} + {S_a[l], S_b[l] strictly inside (lo, h)}
  return all over D in pts:  f_{S_a}(D) - a.pi <= f_{S_b}(D) - b.pi
```

Column generation uses this pricing. The master is set covering with exact route costs `c0 + f_{S_r}(Tmax)`. When BRL returns min rc >= 0 the master value is the exact LP bound. Integer solutions come from price-and-branch (MILP on the generated columns), or from branching on arcs in a full branch-and-price.

Add-on: since the pricing is exact, the final master value is a valid lower bound on the robust optimum. It turns any integer plan into a certified gap. This is a by-product and not the contribution.

Several kinks (`kappa > 1`): labels carry one window per kink and the test is applied per kink (Remark 3.8). A common traffic factor with m atoms gives `kappa*m` resources (Theorem 7.1).

## 3. Closest prior art and what is new

| Item | Status | Source |
|---|---|---|
| `sup E phi(sum X_a)` over the Frechet class equals the comonotone value; stop-loss decomposition `E(S^c - t)^+ = min_{sum d = t} sum E(X_a - d_a)^+` | **Known** | Meilijson & Nadas, J. Appl. Probab. 1979; Kaas, Dhaene & Goovaerts 2000; Dhaene et al. 2002 |
| Worst marginal in a p-box for a monotone loss is the lower CDF | **Known** | Williamson & Downs 1990; Ferson et al. 2003 |
| Comonotone worst case for ambiguous *demand* marginals in the CVRP, reduced to a scenario CVRP (2n+1 points) solved by branch-and-cut | **Known (closest)** | Ghosal, Ho & Wiesemann, Oper. Res. 72(2), 2024 (meet/join argument, Sec. on ambiguity set (7)) |
| ESPPRC labelling, resource extension functions | **Known** | Feillet et al. 2004; Irnich & Desaulniers 2005 |
| Path dominance by second-order stochastic dominance for *independent* arc times | **Known** | Nie, Wu & Homem-de-Mello 2012 |
| Lateness and riskiness indices in routing (independent arcs, or moment ambiguity) | **Known** | Adulyasak & Jaillet 2016 (assumes independent arcs); Jaillet, Qi & Sim 2016; Zhang, Baldacci, Sim & Tang 2019; Zhang, Zhang & Baldacci 2024 |
| Mean-covariance correlated travel times in branch-price-and-cut | Known, different model | Rostami, Desaulniers, Errico & Lodi, Oper. Res. 2021 |
| DR project crashing without correlation information | Known, different problem | Ahipasaoglu, Natarajan & Shi, Networks 2019 |
| **Per-arc budget as a decision resource of the pricing problem, kappa resources independent of L** | **New as far as found** | Theorem 2.5 |
| **Completion-window functional dominance and its exactness proof** | **New as far as found** | Lemma 3.2, Thm 3.4, Thm 4.1 |
| Envelope dominance with `Tmax/delta + 1` labels per bucket | New, proved, **not implemented or tested** | Prop. 6.1 |
| Factor extension (kappa*m resources) | New as stated; a direct corollary | Thm 7.1 |
| Fixed-u (single risk level) sweep is not exact | Numerical observation plus an elementary bound | Prop. 5.1, Test F |

Searches (2026-10-23, snippet-level plus a full-text grep of Adulyasak & Jaillet and Ghosal, Ho & Wiesemann):
- "vehicle routing travel times marginal distributions unknown dependence comonotonic worst-case labeling column generation"
- "Meilijson Nadas convex majorization critical path"
- "Adulyasak Jaillet ... deadlines"
- "Zhang Baldacci Sim Tang ... essential riskiness index"
- "Jaillet Qi Sim ... RV index"
- "distributionally robust shortest path marginal distributions no correlation information"
- "Ahipasaoglu Natarajan Shi"
- "vehicle routing p-box imprecise probability"
- "vehicle routing CVaR travel times unknown correlation"
- "Ghosal Wiesemann ... marginal"
- "comonotonic vehicle routing / shortest path stop-loss labeling"
- "Nie Wu Homem-de-Mello SSD"
- "robust routing budget allocation per arc"

No source found applies the stop-loss decomposition as a labelling resource, or uses a completion-window stop-loss dominance. Absence of hits is weak evidence. Before submission, check full texts of Ghosal, Ho & Wiesemann 2024 (and its e-companion), Zhang, Zhang & Baldacci 2024 (Transp. Sci.) and Boland et al. ("Dominance in pricing problems with stochasticity", Optimization Online 2015).

**Referee risk, stated plainly.** A referee can say: "Theorem 2.1 is Meilijson–Nadas; the rest is ESPPRC labelling with a resource." Two answers. First, the dominance rule is not the generic resource dominance: generic 2-D dominance on (budget used, cost) points with discrete menus is either inexact (single path interpolation is lost) or needs a fine D-grid, and pointwise L-vector dominance is what the scenario reduction of GHW24 would give. Second, the window argument is what makes BRL keep 10-100x fewer labels than L-vector dominance (Test C/D). The defensible claim is: *an exact pricing algorithm for the dependence-robust VRP whose label comparisons are stop-loss comparisons restricted to a completion window, with kappa decision resources instead of L scenario resources.*

**What it reduces to when things degenerate.** With rho = 0 (risk-neutral) BRL is a standard ESPPRC with scalar cost. With L = 1 (a p-box collapsed to a point) the robust model is deterministic. With independent arcs the method does **not** apply (Lemma 3.1 fails).

## 4. What did not survive, or was not pursued

- **Quantile-vector dominance (direction (b) of the brief as first stated).** It is valid but weak (Prop. 3.5). It keeps 10-100x more labels and times out where BRL finishes; it is used as the baseline.
- **Single-level Lagrangian / fixed-u CVaR arc costs** as an exact method: refuted (Test F, 9/20 suboptimal, bound gap up to 22%). As a heuristic it is good on tiny instances (optimal in 10/10 with n=8, cap=3).
- **Lower previsions** (best case over couplings) have no comonotone-type closed form for 3+ arcs; not pursued.
- **Imprecise Markov / lower-prevision value iteration over zones (direction (c))**: not pursued. The zone structure here is static and enters only through prices, so a Bellman contraction adds nothing that Theorem 7.1 does not already give.
- **Polynomial-time claims**: none. The pricing contains the deterministic ESPPRC.
