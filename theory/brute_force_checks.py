"""Brute-force sanity checks for theory/main.tex (Thm 6.1, Thm 7.3, Thm 8.1, Props 7.1-7.2).
Run: python3 brute_force_checks.py   (numpy, scipy). Output observed on 2026-10-23:
  Test1 absorption N=2: 320 instances, 0 violations
  Test2 sparsify: 0 violations, max dh/bound 0.662
  Test3 kernel reduction: 7232 profiles, 0 mismatches
  Test4 D1 FW+sparsify+round: ok 60 of 60
  Test5 delta0 = 1/w for w in {1, 0.5, 2}
  Test6 product of cycles: min max regret = 3*ceil(Z/2), Z=1..5
"""
import numpy as np, itertools
from scipy.optimize import linprog
rng = np.random.default_rng(0)

# ---------- generic bilinear aggregative game ----------
# player i, plan p: pi[i][p] scalar, a[i][p] in R^d (contribution), phi[i][p] in R^d (exposure)
# u_i(p, m) = pi - phi . (M m), m = rival aggregate (belief mean); traffic fixed.
def util(G, i, p, m):
    return G['pi'][i][p] - G['phi'][i][p] @ (G['M'] * m)

def e_threshold(G, i, p, mhat, w):
    """min delta>=0 s.t. exists m>=0, |m-mhat|<=delta w, p optimal at m. LP in (m, delta)."""
    d = len(mhat); P = len(G['pi'][i])
    c = np.zeros(d + 1); c[-1] = 1
    A = []; b = []
    for q in range(P):
        if q == p: continue
        # u(q,m) - u(p,m) <= 0 : pi_q - pi_p - (phi_q - phi_p).(M m) <= 0
        row = np.zeros(d + 1); row[:d] = -(G['phi'][i][q] - G['phi'][i][p]) * G['M']
        A.append(row); b.append(G['pi'][i][p] - G['pi'][i][q])
    for z in range(d):
        r = np.zeros(d + 1); r[z] = 1; r[-1] = -w[z]; A.append(r); b.append(mhat[z])
        r = np.zeros(d + 1); r[z] = -1; r[-1] = -w[z]; A.append(r); b.append(-mhat[z])
    res = linprog(c, A_ub=np.array(A), b_ub=np.array(b), bounds=[(0, None)] * (d + 1), method='highs')
    return res.fun if res.status == 0 else np.inf

def profile_threshold(G, prof, w):
    N = len(prof); A = sum(G['a'][j][prof[j]] for j in range(N))
    return max(e_threshold(G, i, prof[i], A - G['a'][i][prof[i]], w) for i in range(N))

def delta0(G, w):
    return min(profile_threshold(G, prof, w) for prof in itertools.product(*[range(len(G['pi'][i])) for i in range(len(G['pi']))]))

# ---------- mixed NE for N=2 by support enumeration ----------
def mixed_ne_2p(G):
    P1, P2 = len(G['pi'][0]), len(G['pi'][1])
    U1 = np.array([[util(G, 0, p, G['a'][1][q]) for q in range(P2)] for p in range(P1)])
    U2 = np.array([[util(G, 1, q, G['a'][0][p]) for q in range(P2)] for p in range(P1)])
    out = []
    for k in range(1, min(P1, P2) + 1):
        for S1 in itertools.combinations(range(P1), k):
            for S2 in itertools.combinations(range(P2), k):
                # y on S2 makes player1 indifferent on S1 ; x on S1 makes player2 indifferent on S2
                Ay = np.zeros((k + 1, k + 1)); Ay[:k, :k] = U1[np.ix_(S1, S2)]; Ay[:k, k] = -1; Ay[k, :k] = 1
                Ax = np.zeros((k + 1, k + 1)); Ax[:k, :k] = U2[np.ix_(S1, S2)].T; Ax[:k, k] = -1; Ax[k, :k] = 1
                rhs = np.zeros(k + 1); rhs[k] = 1
                try:
                    sy = np.linalg.solve(Ay, rhs); sx = np.linalg.solve(Ax, rhs)
                except np.linalg.LinAlgError:
                    continue
                y = np.zeros(P2); y[list(S2)] = sy[:k]; x = np.zeros(P1); x[list(S1)] = sx[:k]
                if (y < -1e-12).any() or (x < -1e-12).any(): continue
                if (U1 @ y).max() > sy[k] + 1e-9 or (x @ U2).max() > sx[k] + 1e-9: continue
                out.append((np.clip(x, 0, None), np.clip(y, 0, None)))
    return out

def rand_game(N, d, P, D2=True, scale=3):
    G = {'M': rng.uniform(0.5, 1.5, d), 'pi': [], 'a': [], 'phi': []}
    for i in range(N):
        a = rng.integers(0, scale + 1, (P, d)).astype(float)
        phi = a.copy() if not D2 else rng.integers(0, scale + 1, (P, d)).astype(float)
        G['a'].append(a); G['phi'].append(phi); G['pi'].append(rng.uniform(0, 10, P))
    return G

# ---------- Test 1: absorption theorem, N=2 ----------
viol = 0; cnt = 0; tight = 0
for trial in range(300):
    d = rng.integers(1, 4); G = rand_game(2, d, rng.integers(2, 5)); w = rng.uniform(0.5, 2, d)
    nes = mixed_ne_2p(G)
    if not nes: continue
    d0 = delta0(G, w)
    for x, y in nes:
        xs = [x, y]; abar = [xs[i] @ G['a'][i] for i in range(2)]
        B = []
        for i in range(2):
            m = abar[1 - i]; vals = np.array([util(G, i, p, m) for p in range(len(G['pi'][i]))])
            B.append([p for p in range(len(vals)) if vals[p] >= vals.max() - 1e-9])
        rbar = max(np.abs(G['a'][j][p] - abar[j]).max(axis=None) if False else max((np.abs(G['a'][j][p] - abar[j]) / w).max() for p in B[j]) for j in range(2))
        # support selection: best pure profile in B1 x B2 by anchored distance
        best = np.inf; bestp = None
        for prof in itertools.product(*B):
            dist = max((np.abs(G['a'][1 - i][prof[1 - i]] - abar[1 - i]) / w).max() for i in range(2))
            if dist < best: best, bestp = dist, prof
        thr = profile_threshold(G, bestp, w)
        cnt += 1
        if not (d0 <= thr + 1e-7 and thr <= best + 1e-7 and best <= (2 - 1) * rbar + 1e-7):
            viol += 1; print('VIOL', d0, thr, best, rbar)
        if abs(d0 - best) < 1e-7 and best > 1e-7: tight += 1
print('Test1 absorption N=2: instances', cnt, 'violations', viol, 'cases delta0 == anchored bound > 0:', tight)

# ---------- Test 2: sparsification + rounding bounds, large N, arbitrary x ----------
def sparsify(acols, x):
    """acols[i]: (P_i,d) ; x[i] distribution. Return vertex x' with same aggregate (LP with random objective)."""
    N = len(acols); d = acols[0].shape[1]
    sizes = [len(c) for c in acols]; n = sum(sizes)
    Aeq = []; beq = []
    Abar = sum(x[i] @ acols[i] for i in range(N))
    for z in range(d):
        Aeq.append(np.concatenate([acols[i][:, z] for i in range(N)])); beq.append(Abar[z])
    off = 0
    for i in range(N):
        r = np.zeros(n); r[off:off + sizes[i]] = 1; Aeq.append(r); beq.append(1); off += sizes[i]
    res = linprog(rng.normal(size=n), A_eq=np.array(Aeq), b_eq=np.array(beq), bounds=[(0, None)] * n, method='highs-ds')
    xs = []; off = 0
    for i in range(N):
        xs.append(res.x[off:off + sizes[i]]); off += sizes[i]
    return xs

viol = 0; maxratio = 0
for trial in range(200):
    N = rng.integers(2, 25); d = rng.integers(1, 4); w = rng.uniform(0.5, 2, d)
    acols = [rng.integers(0, 4, (rng.integers(2, 4), d)).astype(float) for _ in range(N)]
    x = [rng.dirichlet(np.ones(len(c))) for c in acols]
    abar = [x[i] @ acols[i] for i in range(N)]; Abar = sum(abar)
    xp = sparsify(acols, x)
    J = [i for i in range(N) if (xp[i] > 1e-9).sum() > 1]
    assert len(J) <= d, (len(J), d)
    # deterministic rounding: J players pick the plan of max weight; others the unique support
    p = [int(np.argmax(xp[i])) for i in range(N)]
    s = np.array([[(acols[j][:, z].max() - acols[j][:, z].min()) / w[z] for z in range(d)] for j in range(N)])
    r = np.array([[np.abs(acols[j][:, z] - abar[j][z]).max() / w[z] for z in range(d)] for j in range(N)])
    sig, rho = s.max(), r.max()
    Ap = sum(acols[i][p[i]] for i in range(N))
    dh = max((np.abs((Ap - acols[i][p[i]]) - (Abar - abar[i])) / w).max() for i in range(N))
    k = len(J); bound = k * sig + rho
    if dh > bound + 1e-7: viol += 1; print('VIOL2', dh, bound)
    maxratio = max(maxratio, dh / bound if bound > 0 else 0)
print('Test2 sparsify: violations', viol, 'max dh/bound', round(maxratio, 3))

# ---------- Test 3: kernel reduction ----------
def kernel_game(n, arcs):
    E = list(arcs); d = len(E); Dout = max([sum(1 for (u, v) in E if u == i) for i in range(n)] + [1]); Din = max([sum(1 for (u, v) in E if v == i) for i in range(n)] + [1])
    eta = 1.0 / (2 * Din + 2)
    G = {'M': np.ones(d), 'pi': [], 'a': [], 'phi': []}
    for i in range(n):
        a_in = np.zeros(d); phi_in = np.zeros(d)
        for e, (u, v) in enumerate(E):
            if u == i: a_in[e] = 1; phi_in[e] = 1
            if v == i: a_in[e] = 2; phi_in[e] = eta
        G['pi'].append(np.array([0.0, 1.0])); G['a'].append(np.array([np.zeros(d), a_in])); G['phi'].append(np.array([np.zeros(d), phi_in]))
    return G, 1.0 / (2 * Dout + 1)

def is_kernel(n, arcs, S):
    for (u, v) in arcs:
        if u in S and v in S: return False
    for i in range(n):
        if i not in S and not any(u == i and v in S for (u, v) in arcs): return False
    return True

def maximal_ok(G, i, p, mhat, w, delta):
    # p maximal iff for all q: max_{m in box} u(p,m)-u(q,m) >= 0
    d = len(mhat)
    for q in range(len(G['pi'][i])):
        if q == p: continue
        dphi = (G['phi'][i][p] - G['phi'][i][q]) * G['M']
        # maximize pi_p - pi_q - dphi.m over box clipped at 0 -> choose m_z at lower end if dphi_z>0
        lo = np.maximum(mhat - delta * w, 0); hi = mhat + delta * w
        m = np.where(dphi > 0, lo, hi)
        if G['pi'][i][p] - G['pi'][i][q] - dphi @ m < -1e-12: return False
    return True

bad = 0; tot = 0
for trial in range(150):
    n = rng.integers(2, 7)
    arcs = [(u, v) for u in range(n) for v in range(n) if u != v and rng.random() < 0.35]
    if not arcs: continue
    G, dc = kernel_game(n, arcs); w = np.ones(len(arcs))
    for delta in [0.0, 0.999 * dc]:
        for prof in itertools.product([0, 1], repeat=n):
            S = {i for i in range(n) if prof[i] == 1}
            A = sum(G['a'][j][prof[j]] for j in range(n))
            E_ok = all(e_threshold(G, i, prof[i], A - G['a'][i][prof[i]], w) <= delta + 1e-9 for i in range(n))
            M_ok = all(maximal_ok(G, i, prof[i], A - G['a'][i][prof[i]], w, delta) for i in range(n))
            tot += 1
            if not (E_ok == M_ok == is_kernel(n, arcs, S)): bad += 1
print('Test3 kernel reduction: profiles checked', tot, 'mismatches', bad)

# ---------- Test 4: D1 relaxed potential, sparsify + conditional-expectation rounding ----------
def check_D1(N, d, P):
    M = rng.uniform(0.5, 1.5, d)
    a = [rng.integers(0, 4, (P, d)).astype(float) for _ in range(N)]
    pi = [rng.uniform(0, 20, P) for _ in range(N)]
    pit = [pi[i] + 0.5 * ((a[i] ** 2) * M).sum(1) for i in range(N)]
    def Psi_pure(prof):
        A = sum(a[i][prof[i]] for i in range(N)); return sum(pit[i][prof[i]] for i in range(N)) - 0.5 * (M * A * A).sum()
    def u(i, prof):
        Am = sum(a[j][prof[j]] for j in range(N) if j != i); return pi[i][prof[i]] - (a[i][prof[i]] * M) @ Am
    # Frank-Wolfe on Psibar
    x = [np.ones(P) / P for _ in range(N)]
    for t in range(3000):
        Abar = sum(x[i] @ a[i] for i in range(N))
        grads = [pit[i] - a[i] @ (M * Abar) for i in range(N)]
        s = [np.eye(P)[np.argmax(g)] for g in grads]
        gap = sum(grads[i] @ (s[i] - x[i]) for i in range(N))
        dirs = [s[i] - x[i] for i in range(N)]
        lin = sum(grads[i] @ dirs[i] for i in range(N)); D = sum(dirs[i] @ a[i] for i in range(N)); quad = (M * D * D).sum()
        g = 1.0 if quad <= 0 else min(1.0, lin / quad)
        x = [x[i] + g * dirs[i] for i in range(N)]
        if gap < 1e-9: break
    Abar = sum(x[i] @ a[i] for i in range(N))
    Psibar = sum(x[i] @ pit[i] for i in range(N)) - 0.5 * (M * Abar * Abar).sum()
    # sparsify: LP maximize sum x.pit subject to same aggregate
    n = N * P
    Aeq = [np.concatenate([a[i][:, z] for i in range(N)]) for z in range(d)]; beq = list(Abar)
    for i in range(N):
        r = np.zeros(n); r[i * P:(i + 1) * P] = 1; Aeq.append(r); beq.append(1)
    res = linprog(-np.concatenate(pit), A_eq=np.array(Aeq), b_eq=np.array(beq), bounds=[(0, None)] * n, method='highs-ds')
    xp = [res.x[i * P:(i + 1) * P] for i in range(N)]
    J = [i for i in range(N) if (xp[i] > 1e-9).sum() > 1]
    var = sum(xp[j] @ (((a[j] - xp[j] @ a[j]) ** 2) * M).sum(1) for j in J)
    # conditional expectations: fix players sequentially
    fixed = {}
    def condexp(fixed):
        mean = sum((a[i][fixed[i]] if i in fixed else xp[i] @ a[i]) for i in range(N))
        lin = sum((pit[i][fixed[i]] if i in fixed else xp[i] @ pit[i]) for i in range(N))
        v = sum(xp[i] @ (((a[i] - xp[i] @ a[i]) ** 2) * M).sum(1) for i in range(N) if i not in fixed)
        return lin - 0.5 * (M * mean * mean).sum() - 0.5 * v
    for i in range(N):
        cands = [p for p in range(P) if xp[i][p] > 1e-9]
        fixed[i] = max(cands, key=lambda p: condexp({**fixed, i: p}))
    prof = tuple(fixed[i] for i in range(N))
    Pmax = max(Psi_pure(q) for q in itertools.product(range(P), repeat=N))
    eta = Psibar - Psi_pure(prof)
    regret = max(max(u(i, prof[:i] + (q,) + prof[i + 1:]) for q in range(P)) - u(i, prof) for i in range(N))
    ok = (Pmax <= Psibar + 1e-6) and (Psi_pure(prof) >= Psibar - 0.5 * var - 1e-6) and (regret <= eta + 1e-6) and len(J) <= d
    return ok, eta, regret, 0.5 * var
oks = 0
for trial in range(60):
    ok, eta, reg, hv = check_D1(rng.integers(2, 5), rng.integers(1, 3), 3)
    oks += ok
print('Test4 D1 FW+sparsify+round: ok', oks, 'of 60')

# ---------- Test 5: tight example (Prop 1 of v4) ----------
G = {'M': np.array([1.0]), 'pi': [np.array([6.0, 0.0]), np.array([0.0, 6.0])],
     'a': [np.array([[1.0], [3.0]]), np.array([[1.0], [3.0]])], 'phi': [np.array([[4.0], [1.0]]), np.array([[1.0], [4.0]])]}
for wn in [1.0, 0.5, 2.0]:
    print('Test5 w=', wn, 'delta0 =', delta0(G, np.array([wn])), 'predicted 1/w =', 1 / wn)

# ---------- Test 6: product of cycles (Prop 7.2) ----------
if True:
    import itertools
    # zone game: player1 plans A(k=1,tau=4,pi=6), B(k=3,tau=1,pi=0); player2 X(k=1,tau=1,pi=0), Y(k=3,tau=4,pi=6); u = pi - tau*k_rival
    P1=[(1,4,6),(3,1,0)]; P2=[(1,1,0),(3,4,6)]
    for Z in [1,2,3,4,5]:
        plans1=list(itertools.product(range(2),repeat=Z)); plans2=plans1
        def u1(p,q): return sum(P1[p[z]][2]-P1[p[z]][1]*P2[q[z]][0] for z in range(Z))
        def u2(p,q): return sum(P2[q[z]][2]-P2[q[z]][1]*P1[p[z]][0] for z in range(Z))
        best=min(max(max(u1(pp,q) for pp in plans1)-u1(p,q), max(u2(p,qq) for qq in plans2)-u2(p,q)) for p in plans1 for q in plans2)
        print(Z, 'min max regret', best, ' 3*ceil(Z/2)=',3*((Z+1)//2), ' upper bound L*delta =',3*Z)
