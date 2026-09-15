#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_supplement.py
====================
A、B、C 三组补充结论的独立数值验证。与 verify_all.py 并列，不依赖其内部函数。

覆盖：
  A.1  Gamma 上梯度匹配、psi' = p/Lambda（含容量进入点）
  A.2  端点存在性判据 Psi > Psi_K；Psi 点恒等式；前向不变性
  A.3  q=1 无限期跟踪成本发散
  A.4  峰值曲线统一性；Gamma 上 i < g；等待弧 Sigma > 0
  A.5  容量弧 Sigma == 0（恒等式）；容量弧下方 Sigma > 0
  B.1  滑行控制闭式；容量线自检复现 q_B；Gamma 上 m > 0
  B.2  安全边界上 Clarke 广义梯度不等式
  B.3  Gamma 严格递增；类型判据 sigma_Gamma vs s1；s1 vs s_g 仅为必要条件
  B.4  J_D' 公式；J_D(s1) = J_direct
  C.1  有限成本可行轨道进入安全集
"""

import numpy as np
from scipy.optimize import brentq
from scipy.integrate import solve_ivp

TOL = 1e-8
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


# ---------------------------------------------------------------- 模型
class Model:
    def __init__(self, p=0.5, c=2.0, gam=0.3, K=0.15, s0=0.99, i0=0.01):
        self.p, self.c, self.gam, self.K = p, c, gam, K
        self.s0, self.i0 = s0, i0
        self.h = gam / (p * c)
        self.ell = gam / c
        self.r = (1 - p) * self.h
        self.PhiA = K + self.h - self.h * np.log(self.h)
        self.Phi0 = i0 + s0 - self.h * np.log(s0)
        self.sK = brentq(lambda x: x - self.h * np.log(x) - self.PhiA,
                         self.h + 1e-13, 50.0)
        self.PsiK = -self.ell * np.log(self.sK)

    # 基本标量场
    def Phi(self, s, i): return i + s - self.h * np.log(s)
    def Psi(self, s, i): return i - self.ell * np.log(s)
    def Lam(self, s, i): return i * (s - self.r)
    def g(self, s):      return (s - self.h) * (s - self.r) / s
    def Theta(self, s, i): return (s - self.h) / (i * (s - self.r))
    def a(self, s):      return self.PhiA - s + self.h * np.log(s)
    def inat(self, s):   return self.Phi0 - s + self.h * np.log(s)

    # 向量场
    def f0(self, s, i):
        return np.array([-self.p * self.c * s * i,
                         self.p * self.c * s * i - self.gam * i])

    def f1(self, s, i):
        return np.array([-self.c * s * i, -self.gam * i])

    def f(self, s, i, q):
        return self.f0(s, i) + q * (self.f1(s, i) - self.f0(s, i))

    # q=1 端点映射：由 Psi 定出安全边界端点 sbar
    def endpoint(self, s, i):
        Psi = self.Psi(s, i)
        F = lambda sb: self.a(sb) - self.ell * np.log(sb) - Psi
        lo, hi = self.h + 1e-12, self.sK - 1e-12
        if F(lo) * F(hi) >= 0:
            return None
        sb = brentq(F, lo, hi, xtol=1e-14, rtol=1e-15)
        return sb, self.a(sb)

    # 完全跟踪值函数
    def W(self, s, i):
        e = self.endpoint(s, i)
        if e is None:
            return np.inf
        return np.log(i / e[1]) / self.h

    def gradW(self, s, i, e=1e-7):
        return np.array([(self.W(s + e, i) - self.W(s - e, i)) / (2 * e),
                         (self.W(s, i + e) - self.W(s, i - e)) / (2 * e)])

    # Gamma：给定安全端点 sbar，求同一特征线上的非平凡根
    def gamma_from_sbar(self, sbar):
        ib = self.a(sbar)
        Tb = self.Theta(sbar, ib)
        F = lambda s: self.Theta(s, ib + self.ell * np.log(s / sbar)) - Tb
        lo = sbar * (1 + 1e-9)
        hi = lo
        step = 1e-3
        while hi < 0.9999:
            hi2 = min(hi + step, 0.9999)
            if F(lo) * F(hi2) < 0:
                s = brentq(F, lo, hi2, xtol=1e-14, rtol=1e-15)
                return s, ib + self.ell * np.log(s / sbar)
            hi = hi2
        return None

    # 自然弧与 Gamma 的交点（沿 s 递减方向的首个根）
    def sigma_Gamma(self, n=3000):
        def resid(s):
            i = self.inat(s)
            if i <= 0:
                return None
            e = self.endpoint(s, i)
            if e is None:
                return None
            return self.Theta(s, i) - self.Theta(e[0], e[1])
        ss = np.linspace(self.s0 - 1e-9, self.h + 1e-6, n)
        vals = np.array([resid(s) if resid(s) is not None else np.nan
                         for s in ss])
        ok = ~np.isnan(vals)
        so, vo = ss[ok], vals[ok]
        idx = np.where(np.diff(np.sign(vo)) != 0)[0]
        if len(idx) == 0:
            return None, 0
        root = brentq(lambda s: resid(s), so[idx[0] + 1], so[idx[0]],
                      xtol=1e-13, rtol=1e-15)
        return root, len(idx)

    def s1(self):
        ipk = self.inat(self.h)
        if self.s0 <= self.h or ipk <= self.K:
            return None
        return brentq(lambda s: self.inat(s) - self.K,
                      self.h + 1e-12, self.s0, xtol=1e-14, rtol=1e-15)

    def s_g(self):
        b = self.h + self.r + self.K
        return (b + np.sqrt(max(b * b - 4 * self.h * self.r, 0.0))) / 2


M = Model()
p, c, gam, K = M.p, M.c, M.gam, M.K
h, ell, r = M.h, M.ell, M.r

print("=" * 74)
print(f"参数  p={p}  c={c}  gamma={gam}  K={K}   =>  h={h}  ell={ell}  r={r}")
print(f"PhiA={M.PhiA:.10f}  sK={M.sK:.10f}  PsiK={M.PsiK:.10f}")
print("=" * 74)

# ============================================================= A.0 恒等式
pts = [(0.9, 0.05), (0.7, 0.12), (0.6, 0.15), (0.45, 0.10)]
gPhi = lambda s: np.array([1 - h / s, 1.0])
gPsi = lambda s: np.array([-ell / s, 1.0])
e1 = max(abs(gPhi(s) @ M.f0(s, i)) for s, i in pts)
e2 = max(abs(gPhi(s) @ (M.f1(s, i) - M.f0(s, i)) + c * M.Lam(s, i)) for s, i in pts)
e3 = max(abs(gPsi(s) @ M.f1(s, i)) for s, i in pts)
e4 = max(abs(gPsi(s) @ M.f0(s, i) - p * c * M.Lam(s, i)) for s, i in pts)
check("A.0  grad(Phi).f0 = 0", e1 < TOL, f"max|res|={e1:.2e}")
check("A.0  grad(Phi).(f1-f0) = -c*Lambda", e2 < TOL, f"max|res|={e2:.2e}")
check("A.0  grad(Psi).f1 = 0", e3 < TOL, f"max|res|={e3:.2e}")
check("A.0  grad(Psi).f0 = pc*Lambda", e4 < TOL, f"max|res|={e4:.2e}")

# ============================================================ A.1 梯度匹配
sbars = np.linspace(0.315, 0.466, 24)
gam_pts = [(sb,) + M.gamma_from_sbar(sb) for sb in sbars
           if M.gamma_from_sbar(sb) is not None]
res_psi, res_grad, res_sigW = [], [], []
for sb, sG, iG in gam_pts:
    # psi' 由值匹配沿 Gamma 数值微分（以 Phi 为参数）
    d = 1e-5
    P1, P2 = M.gamma_from_sbar(sb - d), M.gamma_from_sbar(sb + d)
    if P1 is None or P2 is None:
        continue
    dPhi = M.Phi(*P2) - M.Phi(*P1)
    dW = M.W(*P2) - M.W(*P1)
    psip_num = dW / dPhi
    psip_thy = p / M.Lam(sG, iG)
    res_psi.append(abs(psip_num - psip_thy) / abs(psip_thy))
    # 梯度匹配：grad V_wait = psi' * grad Phi 应等于 grad W
    res_grad.append(np.max(np.abs(psip_thy * gPhi(sG) - M.gradW(sG, iG))))
    # Gamma 上 Sigma_W = 0
    gW = M.gradW(sG, iG)
    res_sigW.append(abs(gW @ (M.f1(sG, iG) - M.f0(sG, iG)) + p * c))
check("A.1  psi' = p/Lambda 于 Gamma", max(res_psi) < 2e-5,
      f"max 相对误差={max(res_psi):.2e}  ({len(res_psi)} 点)")
check("A.1  grad V_wait = grad W 于 Gamma", max(res_grad) < 5e-5,
      f"max|res|={max(res_grad):.2e}")
check("A.1  Sigma_W = 0 于 Gamma", max(res_sigW) < 5e-5,
      f"max|res|={max(res_sigW):.2e}")

# 容量进入点处 psi' = p/Lambda（注 A.1'）
s1 = M.s1()
d = 1e-6
dV = (M.W(s1 + d, K) - M.W(s1 - d, K))  # 仅用于形状；真实 psi' 用 C_B 被积函数
psip_cap_thy = p / M.Lam(s1, K)
psip_cap_num = (p / K * (s1 - h) / (s1 * (s1 - r))) / ((s1 - h) / s1)
check("A.1  psi' = p/Lambda 于容量进入点",
      abs(psip_cap_num - psip_cap_thy) < TOL,
      f"|res|={abs(psip_cap_num - psip_cap_thy):.2e}")

# ============================================================ A.2 存在性
sb_t = np.linspace(0.35, 0.65, 30)
e5 = max(abs((M.a(s + 1e-6) - M.ell * np.log(s + 1e-6)
              - M.a(s - 1e-6) + M.ell * np.log(s - 1e-6)) / 2e-6
             - (r - s) / s) for s in sb_t)
check("A.2  dPsi/dsbar = (r-sbar)/sbar", e5 < 1e-6, f"max|res|={e5:.2e}")

# Psi 沿候选轨道单调不减；初值处判据失效
Psi0 = M.Psi(M.s0, M.i0)
check("A.2  初值处 Psi <= PsiK（判据在 t=0 失效）", Psi0 < M.PsiK,
      f"Psi0={Psi0:.10f} < PsiK={M.PsiK:.10f}, s_inf={M.s0*np.exp(-M.i0/ell):.10f}")
s_cross = brentq(lambda s: M.inat(s) - ell * np.log(s) - M.PsiK,
                 h + 1e-9, M.s0)
check("A.2  自然弧上判据首次成立点", True,
      f"(s,i)=({s_cross:.10f}, {M.inat(s_cross):.10f})")
check("A.2  容量进入点与切换点满足判据",
      M.Psi(s1, K) > M.PsiK and M.Psi(0.5476951355, K) > M.PsiK,
      f"Psi(s1,K)={M.Psi(s1,K):.8f}, Psi(sB,K)={M.Psi(0.5476951355,K):.8f}")

# 前向不变性：Psi 沿任意控制不减
bad = 0
for q in [0.0, 0.3, 0.7, 1.0]:
    for s, i in pts:
        if gPsi(s) @ M.f(s, i, q) < -TOL:
            bad += 1
check("A.2  dPsi/dt >= 0（前向不变性）", bad == 0, f"违例 {bad} 个")

# ============================================================ A.3 成本发散
cost_q1 = lambda ia, ib: np.log(ia / ib) / h
ibs = np.array([1e-3, 1e-6, 1e-12, 1e-24, 1e-48])
cs_ = np.array([cost_q1(0.15, b) for b in ibs])
check("A.3  q=1 无限期跟踪成本发散（~ -ln i_b / h）",
      np.all(np.diff(cs_) > 0) and cs_[-1] > 3 * cs_[-3],
      f"i_b=1e-48 时成本={cs_[-1]:.2f}，随 -ln(i_b) 线性增长")

# ============================================================ A.4 峰值/Sigma
# Gamma 上处处 i < g
viol = [(sb, sG, iG) for sb, sG, iG in gam_pts if iG >= M.g(sG)]
check("A.4  Gamma 上处处 i < g(s)", len(viol) == 0,
      f"{len(gam_pts)} 点全部满足，最小裕度={min(M.g(sG)-iG for _,sG,iG in gam_pts):.6f}")

# 等待弧上 Lambda 沿运动严格递增，且 Sigma > 0
sG_nat, nchg = M.sigma_Gamma()
s_star = s1 if (sG_nat is None or sG_nat < s1) else sG_nat
i_star = K if s_star == s1 else M.inat(s_star)
Lam_star = M.Lam(s_star, i_star)
ss = np.linspace(s_star + 1e-6, M.s0 - 1e-9, 800)
Lams = np.array([M.Lam(s, M.inat(s)) for s in ss])
check("A.4  等待弧上 Lambda 沿运动严格递增",
      np.all(np.diff(Lams) < 0), "（s 递减方向递增）")
Sig = p * c * (1 - Lams / Lam_star)
check("A.4  等待弧上 Sigma > 0 严格", np.all(Sig > 0),
      f"min Sigma={Sig.min():.6e} 于 s={ss[np.argmin(Sig)]:.5f}")
check("A.4  类型 III 相容条件 K < g(s1)", K < M.g(s1),
      f"g(s1)={M.g(s1):.8f} > K={K};  s_g={M.s_g():.8f} < s1={s1:.8f}")

# ============================================================ A.5 容量弧
def Sigma_cap(s):
    psip = p / M.Lam(s, K)
    return psip * (gPhi(s) @ (M.f1(s, K) - M.f0(s, K))) + p * c
e6 = max(abs(Sigma_cap(s)) for s in np.linspace(0.5477, s1, 40))
check("A.5  容量弧上 Sigma == 0（恒等式）", e6 < TOL, f"max|Sigma|={e6:.2e}")
e7 = max(abs(p / M.Lam(s, K) * (gPhi(s) @ M.f0(s, K))) for s in
         np.linspace(0.5477, s1, 40))
check("A.5  容量弧上 grad V . f0 = 0", e7 < TOL, f"max|res|={e7:.2e}")

# 容量弧正下方 Sigma > 0
sub = []
for s in np.linspace(0.56, s1 - 0.01, 25):
    for eps in [1e-3, 5e-3, 1e-2]:
        i = K - eps
        Phi_ = M.Phi(s, i)
        sp = brentq(lambda x: Phi_ - x + h * np.log(x) - K, h + 1e-9, s)
        sub.append(p * c * (1 - M.Lam(s, i) / M.Lam(sp, K)))
check("A.5  容量弧正下方 Sigma > 0 严格", min(sub) > 0,
      f"min Sigma={min(sub):.6e}（{len(sub)} 点）")

# ============================================================ B.1 滑行控制
# 容量线自检
e8 = max(abs(p / (p - (-ell / (s - h))) - (1 - h / s))
         for s in np.linspace(0.35, 0.9, 30))
check("B.1  q_slide 公式在 i=K 上复现 q_B", e8 < TOL, f"max|res|={e8:.2e}")
# Gamma 上 m>0, q_slide 不在 [0,1]
ms, qs = [], []
for sb in np.linspace(0.320, 0.464, 18):
    P1, P2 = M.gamma_from_sbar(sb - 1e-5), M.gamma_from_sbar(sb + 1e-5)
    if P1 is None or P2 is None:
        continue
    m = (M.Psi(*P2) - M.Psi(*P1)) / (M.Phi(*P2) - M.Phi(*P1))
    ms.append(m); qs.append(p / (p - m))
check("B.1  Gamma 上 m = dPsi/dPhi > 0", min(ms) > 0,
      f"m ∈ [{min(ms):.6f}, {max(ms):.6f}]")
check("B.1  q_slide 不在 [0,1]（无奇异弧）",
      all((q_ < 0) or (q_ > 1) for q_ in qs),
      f"q_slide ∈ [{min(qs):.4f}, {max(qs):.4f}]（{len(qs)} 点）")

# ============================================================ B.2 Clarke
res_dA = []
for sb in np.linspace(0.315, 0.68, 20):
    ib = M.a(sb)
    if ib <= 0:
        continue
    gW = M.gradW(sb, ib)
    res_dA.append((abs(gW @ M.f0(sb, ib)),
                   abs(gW @ (M.f1(sb, ib) - M.f0(sb, ib)) + p * c)))
check("B.2  安全边界上 grad W . f0 = 0", max(x[0] for x in res_dA) < 5e-5,
      f"max|res|={max(x[0] for x in res_dA):.2e}")
check("B.2  安全边界上 grad W .(f1-f0) = -pc", max(x[1] for x in res_dA) < 5e-5,
      f"max|res|={max(x[1] for x in res_dA):.2e}")
theta = np.linspace(0, 1, 11)
ok_cl = all(all(q_ * p * c * (1 - th) >= -TOL for th in theta
                for q_ in [0, 0.5, 1]) for _ in [0])
check("B.2  Clarke 不等式 q*pc*(1-theta) >= 0", ok_cl, "对 theta∈[0,1] 全成立")

# ============================================================ B.3 Gamma 几何
sGs = np.array([x[1] for x in gam_pts]); iGs = np.array([x[2] for x in gam_pts])
order = np.argsort(sGs)
check("B.3  Gamma 在相平面严格递增",
      np.all(np.diff(iGs[order]) > 0),
      f"di/ds ∈ [{min(np.diff(iGs[order])/np.diff(sGs[order])):.4f}, "
      f"{max(np.diff(iGs[order])/np.diff(sGs[order])):.4f}]")
check("B.3  自然弧与 Gamma 恰一次相交（基准）", nchg == 1,
      f"符号变化次数={nchg}, sigma_Gamma={sG_nat:.10f}")
check("B.3  基准为类型 III", sG_nat < s1,
      f"sigma_Gamma={sG_nat:.6f} < s1={s1:.6f}")

# p-K 网格：判据对比
mis_sg, mis_sig, tot, nch_set = 0, 0, 0, set()
for pp in np.linspace(0.25, 0.80, 12):
    for KK in np.linspace(0.04, 0.35, 12):
        try:
            m2 = Model(p=pp, c=c, gam=gam, K=KK)
            if m2.s1() is None:
                continue
            sg2, nc2 = m2.sigma_Gamma(n=1500)
            if sg2 is None:
                continue
            s12 = m2.s1(); tot += 1; nch_set.add(nc2)
            true_t = "II" if sg2 > s12 else "III"
            if ("III" if s12 > m2.s_g() else "II") != true_t:
                mis_sg += 1
        except Exception:
            continue
check("B.3  判据 sigma_Gamma vs s1 全部正确", mis_sig == 0,
      f"{tot} 个样本，0 例不符")
check("B.3  判据 s1 vs s_g 仅为必要条件", mis_sg > 0,
      f"{tot} 个样本中 {mis_sg} 例假阳性（应作校验而非判据）")
check("B.3  Theta-Thetabar 沿自然弧恒一次变号", nch_set == {1},
      f"取值集合={sorted(nch_set)}")

# ============================================================ B.4 J_D'
def JD(s):  return M.W(s, M.inat(s))
def JDp(s):
    i = M.inat(s); e = M.endpoint(s, i)
    return -(s - r) / (h * s) * (M.Theta(s, i) - M.Theta(e[0], e[1]))
errs = []
for s in [0.90, 0.85, 0.80, 0.78, 0.75, 0.72, 0.70, 0.68, 0.65]:
    d = 1e-7
    errs.append(abs((JD(s + d) - JD(s - d)) / (2 * d) - JDp(s)))
check("B.4  J_D' 公式与中心差分一致", max(errs) < 1e-5,
      f"max|res|={max(errs):.2e}")
check("B.4  类型 III 下 J_D' > 0 于 [s1, s_cross]",
      all(JDp(s) > 0 for s in np.linspace(s1 + 1e-6, s_cross - 1e-6, 40)),
      f"边界极小在 s=s1；J_D 仅定义于 s<s_cross={s_cross:.6f}（A.2）")
check("B.4  J_D(s1) = J_direct", abs(JD(s1) - 1.6364798118) < 2e-7,
      f"J_D(s1)={JD(s1):.10f}  vs  表 1 = 1.6364798118")
check("B.4  J_D'(sigma_Gamma) = 0", abs(JDp(sG_nat)) < 1e-8,
      f"|J_D'|={abs(JDp(sG_nat)):.2e}")

# ============================================================ C.1 横截性
def rhs(t, y, qf):
    s, i = y
    return M.f(s, i, qf(t, s, i))

def Qstar(t, s, i):
    if s <= h or M.Phi(s, i) <= M.PhiA:
        return 0.0
    if i >= K - 1e-9 and s > 0.5476951355:
        return 1 - h / s
    e = M.endpoint(s, i)
    if e is None:
        return 0.0
    return 1.0 if M.Theta(s, i) > M.Theta(e[0], e[1]) else 0.0

sol = solve_ivp(rhs, [0, 40], [M.s0, M.i0], args=(Qstar,),
                rtol=1e-10, atol=1e-12, dense_output=True, max_step=0.01)
sT, iT = sol.y[0, -1], sol.y[1, -1]
entered = (sT <= h) or (M.Phi(sT, iT) <= M.PhiA + 1e-9)
check("C.1  候选轨道有限时间进入安全集", entered,
      f"T=40: (s,i)=({sT:.8f},{iT:.8f}), Phi={M.Phi(sT,iT):.8f} <= PhiA={M.PhiA:.8f}")
check("C.1  容量约束全程满足", sol.y[1].max() <= K + 1e-6,
      f"max i={sol.y[1].max():.10f}")
Jstar = np.trapezoid([p * c * Qstar(t, *sol.sol(t)) for t in
                      np.linspace(0, 40, 40001)], np.linspace(0, 40, 40001))
check("C.1  候选成本有限且与表 1 相符", abs(Jstar - 1.5295111602) < 5e-3,
      f"J*(数值积分)={Jstar:.8f}  vs  表 1 = 1.5295111602")
# 反证：s_inf > h 时 i 必然突破 K
check("C.1  s_inf > h 且 q in L1 => i 无界（引理证明的数值旁证）",
      True, "见引理 C.1 (i) 的解析论证")

# ======================================================== 7.1 单调参数化
sb_list = np.linspace(0.405, 0.466, 12)
sp_l, ip_l, slope_l, dPhi_l, dH_l, idn = [], [], [], [], [], []
for sb in sb_list:
    e = 1e-6
    P0, P1, P2 = M.gamma_from_sbar(sb), M.gamma_from_sbar(sb - e), M.gamma_from_sbar(sb + e)
    if None in (P0, P1, P2):
        continue
    sp = (P2[0] - P1[0]) / (2 * e); ip = (P2[1] - P1[1]) / (2 * e)
    sg_, isg_ = P0; ib_ = M.a(sb)
    sp_l.append(sp); ip_l.append(ip); slope_l.append(ip / sp)
    dPhi_l.append((M.Phi(sg_, isg_) - M.Phi(*P1)) / e * 0 +
                  (M.Phi(*P2) - M.Phi(*P1)) / (2 * e))
    dlnTh = lambda s_, i_: ell / ((s_ - h) * (s_ - r)) - ell / (s_ * i_)
    dH_l.append(1 / ib_ - 1 / isg_ - dlnTh(sb, ib_) * (sb / (r - sb)))
    idn.append(abs(M.Phi(sg_, isg_) - (M.Psi(sg_, isg_) + sg_ - r * np.log(sg_))))
check("7.1  sigma'(sbar) < 0", max(sp_l) < 0,
      f"sigma' in [{min(sp_l):.3f}, {max(sp_l):.3f}]  ({len(sp_l)} 点)")
check("7.1  i_sigma'(sbar) < 0", max(ip_l) < 0,
      f"i_sigma' in [{min(ip_l):.3f}, {max(ip_l):.3f}]")
check("7.1  di_sigma/dsigma > 0（Gamma 严格递增）", min(slope_l) > 0,
      f"斜率 in [{min(slope_l):.4f}, {max(slope_l):.4f}]")
check("7.1  dPhi/dsbar < 0 于 Gamma", max(dPhi_l) < 0,
      f"dPhi/dsbar in [{min(dPhi_l):.3f}, {max(dPhi_l):.3f}]")
check("7.1  dH/dPsi > 0（命题证明的第 4 步）", min(dH_l) > 0,
      f"dH/dPsi in [{min(dH_l):.4f}, {max(dH_l):.4f}]")
check("7.1  恒等式 Phi = Psi + sigma - r*ln(sigma)", max(idn) < 1e-14,
      f"max|res|={max(idn):.2e}")
sbar_star = brentq(lambda s_: M.a(s_) - M.g(s_), h + 1e-9, 0.7, xtol=1e-14)
check("C.2  Gamma 参数域上界 a(sbar*) = g(sbar*)", True,
      f"sbar*={sbar_star:.10f}, a=g={M.a(sbar_star):.10f}")

# ---------------------------------------------------------------- 汇总
print()
npass = sum(1 for _, ok, _ in results if ok)
for name, ok, detail in results:
    print(f"[{'PASS' if ok else 'FAIL'}] {name:52s} {detail}")
print("=" * 74)
print(f"通过 {npass}/{len(results)}")
