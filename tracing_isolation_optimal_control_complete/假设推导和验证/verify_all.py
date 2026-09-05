#!/usr/bin/env python3
"""
verify_all.py —— 跟踪隔离最优控制报告：假设 G1--G4 全部升格为定理的验证脚本。

用法:
    python verify_all.py            # 全部检查
    python verify_all.py --quick    # 跳过耗时的大网格扫描

依赖: numpy, scipy, sympy
模型: sdot = -c[p+(1-p)q]si,  idot = pc(1-q)si - gamma i,  J = int pc q dt,  i <= K
记号: b=pc, h=gamma/(pc), ell=gamma/c=ph, r=(1-p)h, kappa=(1-p)/p
      Theta(s,i)=(s-h)/(i(s-r)),  g(s)=(s-h)(s-r)/s,  phi(x)=(x-h)(x-r)^2/x
"""
import sys
import numpy as np
import sympy as sp
from math import log, exp, sqrt
from scipy.optimize import brentq

QUICK = "--quick" in sys.argv
C, GAM, S0, I0 = 2.0, 0.3, 0.99, 0.01          # 报告基准的固定参数
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"   {detail}" if detail else ""))


# ======================================================================
# 模型工具
# ======================================================================
class Cfg:
    """给定 (p, K) 的一组导出常数与基本函数。"""
    __slots__ = ("p", "K", "h", "ell", "r", "A0")

    def __init__(self, p, K):
        self.p, self.K = p, K
        self.h = GAM / (p * C)
        self.ell = GAM / C
        self.r = (1 - p) * self.h
        self.A0 = K + self.h - self.h * log(self.h)

    def a(self, s):                                  # 安全边界 i = a(s)
        return self.A0 - s + self.h * log(s)

    def av(self, s):
        return self.A0 - s + self.h * np.log(s)

    def inat(self, s):                               # 自然轨道
        return I0 + S0 - s + self.h * log(s / S0)

    def inatv(self, s):
        return I0 + S0 - s + self.h * np.log(s / S0)

    def Th(self, s, i):                              # Theta
        return (s - self.h) / (i * (s - self.r))

    def g(self, s):                                  # 奇异轨迹 / 单峰性分界
        return (s - self.h) * (s - self.r) / s

    def phi(self, x):
        return (x - self.h) * (x - self.r) ** 2 / x


def smax(cf):
    """a(x)=0 在 (h, inf) 上的唯一根：安全边界与 i=0 的交点。"""
    hi = cf.h * 2.0
    while cf.a(hi) > 0:
        hi *= 1.5
    return brentq(cf.a, cf.h * (1 + 1e-14), hi, xtol=1e-15, rtol=8.9e-16)


def endpoint(cf, s, i, n=64):
    """q=1 特征线与安全边界的交点 sbar；不可达返回 None。"""
    h, ell = cf.h, cf.ell
    if s <= h or i <= cf.a(s):
        return None
    x0 = s * exp(-i / ell)                           # 特征线上 i=0 的极限位置
    if x0 > h and cf.a(x0) < 0:
        return None                                  # G1: 够不到安全集
    Psi = i - ell * log(s)
    lo, hi = h, s
    for _ in range(n):                               # G 在 [h,s] 上严格单减
        m = 0.5 * (lo + hi)
        if cf.a(m) - ell * log(m) - Psi > 0:
            lo = m
        else:
            hi = m
    sb = 0.5 * (lo + hi)
    return sb if (cf.a(sb) > 0 and h < sb < s) else None


def endpoint_v(cf, s, i, n=56):
    h, ell = cf.h, cf.ell
    x0 = s * np.exp(-i / ell)
    ok = (x0 <= h) | (cf.av(np.maximum(x0, 1e-12)) >= 0)
    ok &= (s > h) & (i > cf.av(s))
    Psi = i - ell * np.log(s)
    lo, hi = np.full_like(s, h), s.copy()
    for _ in range(n):
        m = 0.5 * (lo + hi)
        pos = cf.av(m) - ell * np.log(m) - Psi > 0
        lo, hi = np.where(pos, m, lo), np.where(pos, hi, m)
    sb = 0.5 * (lo + hi)
    ok &= (cf.av(sb) > 0) & (sb > h) & (sb < s)
    return sb, ok


def s1_of(cf):
    """自然轨道首次触及 i=K 的大根；类型 I 返回 None。"""
    h = cf.h
    if cf.K <= I0:                                   # K <= i0 时初值即违反容量约束
        return None
    if S0 <= h or I0 + S0 - h + h * log(h / S0) <= cf.K:
        return None
    lo, hi = h, S0
    for _ in range(90):
        m = 0.5 * (lo + hi)
        if cf.inat(m) - cf.K > 0:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def iwait(cf, s1, s):
    return cf.K if s <= s1 else cf.inat(s)


def Dscal(cf, s1, s):
    """统一残差 D(s) = Theta(sbar, abar) - Theta(s, i_wait(s))。"""
    i = iwait(cf, s1, s)
    sb = endpoint(cf, s, i)
    if sb is None:
        return None
    return cf.Th(sb, cf.a(sb)) - cf.Th(s, i)


def CB(cf, hi, lo):
    p, K, r = cf.p, cf.K, cf.r
    return p / (K * (1 - p)) * (log(hi / lo) - p * log((hi - r) / (lo - r)))


def find_zero(cf, s1, n=2400):
    """在等待轨迹上定位 D 的零点；返回 (s_star, n_roots) 或 (None, n_roots)。"""
    h = cf.h
    sb_ = np.linspace(h * (1 + 1e-9), s1, n // 2, endpoint=False)
    sn_ = np.linspace(s1, S0 * (1 - 1e-9), n - n // 2)
    s = np.concatenate([sb_, sn_])
    iw = np.concatenate([np.full(sb_.size, cf.K), cf.inatv(sn_)])
    sbv, ok = endpoint_v(cf, s, iw)
    if ok.sum() < 20:
        return None, 0
    ss, iws = s[ok], iw[ok]
    dd = cf.Th(sbv[ok], cf.av(sbv[ok])) - cf.Th(ss, iws)
    keep = ss > h + 0.02 * (S0 - h)                  # 排除 s->h 的平凡零点
    ssk, ddk = ss[keep], dd[keep]
    cr = np.where(np.sign(ddk[:-1]) * np.sign(ddk[1:]) < 0)[0]
    if len(cr) != 1:
        return None, len(cr)
    k = cr[0]
    lo, hi, sl = ssk[k], ssk[k + 1], np.sign(ddk[k])
    for _ in range(80):
        m = 0.5 * (lo + hi)
        dm = Dscal(cf, s1, m)
        if dm is None or np.sign(dm) == sl:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi), 1


# ======================================================================
# 第 1 部分：符号验证
# ======================================================================
def part1_symbolic():
    print("\n" + "=" * 72)
    print("第 1 部分  符号验证 (sympy)")
    print("=" * 72)

    s, i, q, p, b, h = sp.symbols("s i q p b h", positive=True)
    ls, li = sp.symbols("lambda_s lambda_i", real=True)
    kap, r, ell = (1 - p) / p, (1 - p) * h, p * h

    A, B = b * (1 + kap * q), b * (1 - q)
    sdot, idot = -A * s * i, B * s * i - b * h * i
    H = ls * sdot + li * idot + b * q
    Sig = sp.simplify(sp.diff(H, q))

    # 1.1 切换函数与报告式 (eq:switching-function) 一致
    Sig_report = b - (b / p) * s * i * ((1 - p) * ls + p * li)
    check("1.1  Sigma = pc - c s i[(1-p)V_s + p V_i]",
          sp.simplify(Sig - Sig_report) == 0)

    # 1.2 dSigma/dt 不含 q（Lie 括号相消）
    lsdot, lidot = -sp.diff(H, s), -sp.diff(H, i)
    Sigdot = sp.expand(sp.diff(Sig, s) * sdot + sp.diff(Sig, i) * idot
                       + sp.diff(Sig, ls) * lsdot + sp.diff(Sig, li) * lidot)
    check("1.2  dSigma/dt 与 q 无关", sp.simplify(sp.diff(Sigdot, q)) == 0)

    # 1.3 (Sigma=0, H0=0) 唯一确定共态
    H0 = sp.simplify(H.subs(q, 0))
    sol = sp.solve([sp.Eq(Sig, 0), sp.Eq(H0, 0)], [ls, li], dict=True)[0]
    LS, LI = sp.simplify(sol[ls]), sp.simplify(sol[li])
    Theta = (s - h) / (i * (s - r))
    check("1.3  lambda_s = p*Theta/s,  lambda_i = p*Theta/(s-h)",
          sp.simplify(LS - p * Theta / s) == 0
          and sp.simplify(LI - p * Theta / (s - h)) == 0)

    # 1.4 异常极值：齐次方程组行列式非零
    Mrow = sp.Matrix([[kap, 1], [-s, s - h]])
    check("1.4  异常极值排除 (det = (s-r)/p != 0)",
          sp.simplify(Mrow.det() - (s - r) / p) == 0)

    # 1.5 奇异轨迹 = g(s)
    E2 = sp.simplify(Sigdot.subs({ls: LS, li: LI}))
    locus = sp.solve(sp.Eq(E2, 0), i)
    gfun = (s - h) * (s - r) / s
    check("1.5  奇异轨迹 i = g(s) = (s-h)(s-r)/s",
          any(sp.simplify(x - gfun) == 0 for x in locus))

    # 1.6 奇异控制的两个恒等式
    gp = sp.diff(gfun, s)
    qs = sp.simplify(sp.solve(sp.Eq(sp.simplify((idot - gp * sdot).subs(i, gfun)), 0), q)[0])
    Den = (2 * p - 1) * s ** 2 + r ** 2
    Num = p * ((s - h) * (s + r) + s * (s - r))
    check("1.6a q_sing = p[(s-h)(s+r)+s(s-r)] / [(2p-1)s^2+r^2]",
          sp.simplify(qs - Num / Den) == 0)
    check("1.6b q_sing - 1 = (s-h)(s+r) / [(2p-1)s^2+r^2]",
          sp.simplify(qs - 1 - (s - h) * (s + r) / Den) == 0)

    # 1.7 D' 的两段化简恒等式
    sb, ab = sp.symbols("sbar abar", positive=True)
    Pb = ell / ((sb - h) * (sb - r)) + (sb - h) / (sb * ab)

    #   自然轨道段: w = (h-s)/s
    w = (h - s) / s
    P = ell / ((s - h) * (s - r)) - w / i
    sbp = sb * (ell / s - w) / (sb - r)
    ab_zero = (sb - h) * i * (s - r) / ((s - h) * (sb - r))      # 由 Theta_bar = Theta
    lhs_nat = sp.simplify((Pb * sbp - P).subs(ab, ab_zero))
    tgt_nat = (s - r) * ell / s * (sb / ((sb - h) * (sb - r) ** 2)
                                   - s / ((s - h) * (s - r) ** 2))
    check("1.7a 自然段:  P̄·s̄' - P = ((s-r)ℓ/s)[1/φ(s̄) - 1/φ(s)]",
          sp.simplify(lhs_nat - tgt_nat) == 0)

    #   容量边界段: w = 0, i = K
    K = sp.Symbol("K", positive=True)
    T = (s - h) / (K * (s - r))
    ab_K = (sb - h) / (T * (sb - r))
    Pb_K = ell / ((sb - h) * (sb - r)) + (sb - h) / (sb * ab_K)
    lhs_cap = sp.simplify(Pb_K * (sb * ell / (s * (sb - r))) - ell / ((s - h) * (s - r)))
    tgt_cap = (ell / s) * (ell * sb / ((sb - h) * (sb - r) ** 2) + T
                           - s / ((s - h) * (s - r)))
    check("1.7b 容量段:  P̄·s̄' - P = (ℓ/s)[ℓs̄/((s̄-h)(s̄-r)²) + Θ - s/((s-h)(s-r))]",
          sp.simplify(lhs_cap - tgt_cap) == 0)

    # 1.8 容量段松弛量的分子 = s[g(s) - K]
    gap = ell * s / ((s - h) * (s - r) ** 2) + T - s / ((s - h) * (s - r))
    check("1.8  松弛量分子 = (s-h)(s-r) - Ks = s[g(s) - K]",
          sp.simplify(sp.numer(sp.cancel(gap)) - ((s - h) * (s - r) - K * s)) == 0)

    # 1.9 phi 的对数导数分解
    x = sp.Symbol("x", positive=True)
    phi = (x - h) * (x - r) ** 2 / x
    check("1.9  (ln φ)' = 1/(x-h) + 2/(x-r) - 1/x",
          sp.simplify(sp.diff(sp.log(phi), x) - (1 / (x - h) + 2 / (x - r) - 1 / x)) == 0)

    # 1.10 容量等待弧上 Sigma 恒为零
    cc = sp.Symbol("c", positive=True)
    ThK = (s - h) / (K * (s - r))
    Vs, Vi = p * ThK / s, p / (K * (s - r))
    check("1.10 容量等待弧上 Sigma ≡ 0 (恒等式)",
          sp.simplify(p * cc - cc * s * K * ((1 - p) * Vs + p * Vi)) == 0)

    # 1.11 沿自然轨道 d/ds[i(s)(s-r)] = i - g(s)
    io = sp.Symbol("iota", positive=True)
    check("1.11 d/ds[i(s)(s-r)]|_{q=0} = i - g(s)",
          sp.simplify(((h - s) / s) * (s - r) + io - (io - gfun)) == 0)


# ======================================================================
# 第 2 部分：G4 —— 不存在奇异弧
# ======================================================================
def part2_G4():
    print("\n" + "=" * 72)
    print("第 2 部分  定理 G4：不存在正长度奇异弧")
    print("=" * 72)

    nbad, nmin, tot = 0, np.inf, 0
    for p in np.linspace(0.001, 0.999, 400 if not QUICK else 80):
        h = GAM / (p * C)
        if h >= S0:
            continue                                  # h>=s0 时无流行阶段
        r = (1 - p) * h
        s = np.linspace(h * (1 + 1e-9), 1.0, 2000 if not QUICK else 400)
        N = p * ((s - h) * (s + r) + s * (s - r))
        Den = (2 * p - 1) * s ** 2 + r ** 2
        nmin = min(nmin, N.min())
        with np.errstate(divide="ignore", invalid="ignore"):
            qq = np.where(np.abs(Den) > 1e-15, N / Den, np.nan)
        nbad += int(np.nansum((qq >= -1e-12) & (qq <= 1 + 1e-12)))
        tot += s.size
    check("2.1  s>h 上 N > 0 恒成立", nmin > 0, f"min N = {nmin:.4e}")
    check("2.2  q_sing 从不落入 [0,1]", nbad == 0, f"样本 {tot}, 违例 {nbad}")

    cf = Cfg(0.5, 0.15)
    vals = []
    for s in (0.31, 0.40, 0.55, 0.70, 0.90):
        N = cf.p * ((s - cf.h) * (s + cf.r) + s * (s - cf.r))
        Den = (2 * cf.p - 1) * s ** 2 + cf.r ** 2
        vals.append(N / Den)
    check("2.3  基准参数下 q_sing 全部 > 1", all(v > 1 for v in vals),
          "q_sing = " + ", ".join(f"{v:.3f}" for v in vals))


# ======================================================================
# 第 3 部分：G3 —— 横截性与至多一个交点
# ======================================================================
def part3_G3():
    print("\n" + "=" * 72)
    print("第 3 部分  定理 G3：横截性与至多一个切换点")
    print("=" * 72)

    npg = 40 if not QUICK else 14
    nkg = 25 if not QUICK else 10
    rows, nroot_bad = [], 0
    for p in np.linspace(0.20, 0.95, npg):
        h = GAM / (p * C)
        if h >= S0:
            continue
        ipk = I0 + S0 - h + h * log(h / S0)
        for f in np.linspace(0.05, 0.97, nkg):
            K = round(ipk * f, 6)
            cf = Cfg(p, K)
            s1 = s1_of(cf)
            if s1 is None:
                continue
            st, nr = find_zero(cf, s1)
            if nr != 1:
                nroot_bad += 1
                continue
            iw = iwait(cf, s1, st)
            w = 0.0 if st <= s1 else (h - st) / st
            sb = endpoint(cf, st, iw)
            ab = cf.a(sb)
            T = cf.Th(st, iw)
            P = cf.ell / ((st - h) * (st - cf.r)) - w / iw
            Pb = cf.ell / ((sb - h) * (sb - cf.r)) + (sb - h) / (sb * ab)
            sbp = sb * (cf.ell / st - w) / (sb - cf.r)
            e = 1e-6
            dnum = (Dscal(cf, s1, st + e) - Dscal(cf, s1, st - e)) / (2 * e)
            rows.append(dict(p=p, K=K, st=st, sb=sb,
                             dnum=dnum, dform=T * (Pb * sbp - P),
                             lemA=iw < cf.g(st), lemB=ab > cf.g(sb),
                             phi=cf.phi(sb) < cf.phi(st), bdry=st <= s1))
    n = len(rows)
    check("3.1  D 的零点数处处为 1", nroot_bad == 0, f"样本 {n + nroot_bad}, 违例 {nroot_bad}")
    check("3.2  D' 闭式 T(P̄s̄'-P) = 数值导数",
          all(abs(x["dnum"] - x["dform"]) <= 1e-5 * abs(x["dnum"]) for x in rows),
          f"最大相对差 {max(abs(x['dnum']-x['dform'])/abs(x['dnum']) for x in rows):.2e}")
    check("3.3  D'(s*) > 0 处处成立", all(x["dnum"] > 0 for x in rows),
          f"min D' = {min(x['dnum'] for x in rows):.4f}")
    check("3.4  引理 A: i_w(s*) < g(s*)", all(x["lemA"] for x in rows))
    check("3.5  引理 B: ā > g(s̄)", all(x["lemB"] for x in rows))
    check("3.6  φ(s̄) < φ(s*)  (φ 严格递增, s̄ < s*)", all(x["phi"] for x in rows))
    check("3.7  s̄ < s* 恒成立", all(x["sb"] < x["st"] for x in rows))
    nb = sum(x["bdry"] for x in rows)
    print(f"        样本 {n} 个：容量边界段 {nb}，自然轨道段 {n - nb}")


# ======================================================================
# 第 4 部分：G1 —— 可达域的闭式刻画
# ======================================================================
def part4_G1():
    print("\n" + "=" * 72)
    print("第 4 部分  定理 G1：可达域 D = { i > ℓ·ln(s/s_max) }")
    print("=" * 72)

    npg = 30 if not QUICK else 10
    nkg = 30 if not QUICK else 10
    bad = tot = 0
    for p in np.linspace(0.16, 0.95, npg):
        for K in np.linspace(0.02, 0.42, nkg):
            cf = Cfg(p, K)
            if cf.h >= S0:
                continue
            sm = smax(cf)
            for s in np.linspace(cf.h * 1.001, 0.99, 40 if not QUICK else 15):
                for i in np.linspace(1e-4, K, 15 if not QUICK else 6):
                    if i <= cf.a(s):
                        continue
                    tot += 1
                    if (i > cf.ell * log(s / sm)) != (endpoint(cf, s, i) is not None):
                        bad += 1
    check("4.1  闭式判据 = 实际端点存在性", bad == 0, f"样本 {tot}, 不符 {bad}")

    # rho(s) = i_nat(s) - ell*ln(s/s_max) 严格递减 => 等待轨迹恰穿越 dD 一次
    ok_rho = True
    for p in np.linspace(0.16, 0.95, npg):
        for K in np.linspace(0.02, 0.42, 12):
            cf = Cfg(p, K)
            if cf.h >= S0:
                continue
            sm = smax(cf)
            ss = np.linspace(max(cf.h, cf.r) * 1.01, 0.99, 400)
            if np.any(np.diff(cf.inatv(ss) - cf.ell * np.log(ss / sm)) > 0):
                ok_rho = False
    check("4.2  rho' = (r-s)/s < 0 : 等待轨迹恰穿越 ∂D 一次", ok_rho)

    # R(s) = i_w(s) - ell*ln(s/s_max) 在整条等待轨迹上严格递减, 且 R(h+)>0
    #   自然段 R' = (h-s)/s - ell/s = (r-s)/s < 0 ;  容量段 R' = -ell/s < 0
    # => D 与等待轨迹之交恰为单个区间 (h, s_D)
    ok_mono, ok_left = True, True
    for p in np.linspace(0.16, 0.95, npg):
        h = GAM / (p * C)
        if h >= S0:
            continue
        ipk = I0 + S0 - h + h * log(h / S0)
        for f in np.linspace(0.05, 0.98, 20):
            cf = Cfg(p, round(ipk * f, 6))
            s1 = s1_of(cf)
            if s1 is None:
                continue
            sm = smax(cf)
            nb = 400
            sb_ = np.linspace(cf.h * (1 + 1e-9), s1, nb, endpoint=False)
            sn_ = np.linspace(s1, S0 * (1 - 1e-9), nb)
            ss = np.concatenate([sb_, sn_])
            iw = np.concatenate([np.full(nb, cf.K), cf.inatv(sn_)])
            if np.any(np.diff(iw - cf.ell * np.log(ss / sm)) > 1e-14):
                ok_mono = False
            if not cf.K - cf.ell * log(cf.h / sm) > 0:
                ok_left = False
    check("4.3  R(s) 沿等待轨迹严格递减 => D∩W 是单个区间", ok_mono)
    check("4.4  R(h+) = K - ℓ·ln(h/s_max) > 0  (因 h < s_max)", ok_left)

    cf = Cfg(0.5, 0.15)
    sm = smax(cf)
    s1 = s1_of(cf)
    sD = brentq(lambda s: cf.inat(s) - cf.ell * log(s / sm), s1, S0 * (1 - 1e-12))
    print(f"        基准: s_max = {sm:.10f},  自然轨道可达上界 s_D = {sD:.10f}")


# ======================================================================
# 第 5 部分：注 8.2(iii) 的修正
# ======================================================================
def part5_boundary():
    print("\n" + "=" * 72)
    print("第 5 部分  修正：容量等待弧上 Sigma ≡ 0，但唯一性仍成立")
    print("=" * 72)

    def sprime(cf, s, i):
        Phi = i + s - cf.h * log(s)
        return brentq(lambda x: cf.K + x - cf.h * log(x) - Phi, cf.h + 1e-12, s + 1e-12)

    def Sigma(cf, s, i):
        sp_ = sprime(cf, s, i)
        Vi = cf.p / (cf.K * (sp_ - cf.r))
        Vs = cf.p * (s - cf.h) / (cf.K * s * (sp_ - cf.r))
        return cf.p * C - C * s * i * ((1 - cf.p) * Vs + cf.p * Vi)

    cf = Cfg(0.5, 0.15)
    s1 = s1_of(cf)
    sB, _ = find_zero(cf, s1)
    on = [abs(Sigma(cf, s, cf.K)) for s in np.linspace(sB * 1.001, s1 * 0.999, 25)]
    check("5.1  边界上 Sigma = 0 (机器精度)", max(on) < 1e-9, f"max|Sigma| = {max(on):.2e}")

    below = []
    for spr in np.linspace(sB * 1.02, s1 * 0.98, 14):       # 自然轨道触及 i=K 的位置
        Phi = cf.K + spr - cf.h * log(spr)
        for s in np.linspace(spr * 1.002, min(spr * 1.35, S0 * 0.99), 14):
            i = Phi - s + cf.h * log(s)
            if 0 < i < cf.K:
                below.append(Sigma(cf, s, i))

    check("5.2  边界下方 Sigma > 0 严格", len(below) > 50 and min(below) > 0,
          f"样本 {len(below)}, min Sigma = {min(below):.3e}")

    # 机制: i <= K < g(s_B) <= g(s) 对 s >= s_B
    ok = True
    for p in np.linspace(0.20, 0.95, 25):
        h = GAM / (p * C)
        if h >= S0:
            continue
        ipk = I0 + S0 - h + h * log(h / S0)
        for f in np.linspace(0.05, 0.97, 15):
            c2 = Cfg(p, round(ipk * f, 6))
            t1 = s1_of(c2)
            if t1 is None:
                continue
            st, nr = find_zero(c2, t1)
            if nr != 1 or st > t1:
                continue                              # 只看容量段情形
            if not (c2.K < c2.g(st) and sqrt(c2.h * c2.r) < c2.h < st):
                ok = False
    check("5.3  K < g(s_B) 且 g 在 (s_B,·) 上递增", ok)


# ======================================================================
# 第 6 部分：基准数值复现
# ======================================================================
def part6_baseline():
    print("\n" + "=" * 72)
    print("第 6 部分  报告基准数值复现 (p=0.5, c=2, gamma=0.3, K=0.15)")
    print("=" * 72)

    cf = Cfg(0.5, 0.15)
    s1 = s1_of(cf)
    sB, _ = find_zero(cf, s1)
    sb = endpoint(cf, sB, cf.K)
    ab = cf.a(sb)
    ipk = I0 + S0 - cf.h + cf.h * log(cf.h / S0)
    W = (1 / cf.h) * log(cf.K / ab)
    Jstar = CB(cf, s1, sB) + W
    Jfb = CB(cf, s1, cf.h * (1 + 1e-11))
    ref = {
        "i_pk": (ipk, 0.3418232595),
        "s_1": (s1, 0.7775221610),
        "s_B": (sB, 0.5476951355),
        "s_R": (sb, 0.4516637907),
        "i_R": (ab, 0.1210828901),
        "T_B": (1 / (C * cf.K) * log((s1 - cf.r) / (sB - cf.r)), 1.5203108877),
        "T_q1": ((1 / GAM) * log(cf.K / ab), 0.7138664706),
        "J*": (Jstar, 1.5295111602),
    }
    worst = 0.0
    for k, (v, r0) in ref.items():
        d = abs(v - r0)
        worst = max(worst, d)
        print(f"        {k:6s} = {v:.10f}   报告 {r0:.10f}   差 {d:.2e}")
    check("6.1  全部关键量与报告一致 (<1e-7)", worst < 1e-7, f"最大偏差 {worst:.2e}")
    sav = 100 * (Jfb - Jstar) / Jfb
    check("6.2  相对 filling-the-box 节省 ≈ 3.0965%", abs(sav - 3.0964769812) < 1e-4,
          f"{sav:.7f}%")


# ======================================================================
if __name__ == "__main__":
    print("=" * 72)
    print("跟踪隔离最优控制：假设 G1--G4 的完整验证" + ("  [quick]" if QUICK else ""))
    print("=" * 72)
    part1_symbolic()
    part2_G4()
    part3_G3()
    part4_G1()
    part5_boundary()
    part6_baseline()

    npass = sum(v for _, v in RESULTS)
    print("\n" + "=" * 72)
    print(f"总计 {npass}/{len(RESULTS)} 项通过")
    if npass < len(RESULTS):
        print("失败项：" + ", ".join(k for k, v in RESULTS if not v))
    print("=" * 72)
    sys.exit(0 if npass == len(RESULTS) else 1)
