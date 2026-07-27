"""Heavy compute for Panel B; saves everything to panelB.pkl next to this file so plotting is fast."""
import sys, pickle, time, numpy as np
from pathlib import Path
CACHE = Path(__file__).resolve().parent / "panelB.pkl"
# 自动把三个求解器模块目录加入 sys.path（免手动设 PYTHONPATH）。
_XCC = Path(__file__).resolve().parent.parent / "xian_control_comparison"
for _p in (_XCC, _XCC / "threshold_landscape_analysis", _XCC / "effective_population_sensitivity"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
if not hasattr(np, "trapz"):
    np.trapz = np.trapezoid
from panels import (TH, N_OF, N_FULL, solve_threshold, solve_tdinn, prep, _envelope,
                    build_plot_series, compute_inflection)

ETA = 100.0
roles = ["clear", "cum", "interior", "dur45", "cost", "dur150"]
t0 = time.time()
series = {}
clears = []
for r in roles:
    N = N_OF[r]
    p, df, d = solve_threshold(N, ETA)
    try:
        infl = compute_inflection(ETA, p, d)
        ti, qi = float(infl["t_inflection"]), float(infl["q_at_inflection"])
    except Exception:
        ti, qi = float(d["t2"]), float("nan")
    series[r] = dict(N=N, df=df, d=d, ti=ti, qi=qi)
    clears.append(float(d["clear_time"]))
    print(f"  thr {r:8s} N={N:7.0f} clear={float(d['clear_time']):7.2f}  ({time.time()-t0:.0f}s)")

tend = 1.05 * max(clears)
tg = np.linspace(0, tend, 1400)
built = {}
for r in roles:
    p = prep(series[r]["N"])[0]
    s = build_plot_series(ETA, p, series[r]["df"], series[r]["d"], series[r]["ti"], tend)
    built[r] = dict(t=s["t"].to_numpy(float), I=s["I"].to_numpy(float), q=s["q"].to_numpy(float),
                    N=series[r]["N"], ti=series[r]["ti"], qi=series[r]["qi"])

# 常规控制带的 N 区间与六个阈值角色的 N 范围严格对齐（原先下端 5800 未盖住
# clear 角色的 N=4537）。8 条成员各自按自身 N 重拟合 I0，故轨迹会相互交叉，
# 包络并非处处由两端成员给出。
Nrib = np.geomspace(min(N_OF.values()), max(N_OF.values()), 8)
_lo0, _hi0, rreps = _envelope(lambda N: prep(N)[2], Nrib, tg)
_M = np.vstack([rreps[N] for N in Nrib])
rn = np.isfinite(_M).sum(axis=0)                      # 每点仍有效的成员数(供诊断)
# 各成员清零时刻不同(36.7~52.4 d)。若把清零后记为 NaN,包络会在成员逐条退出时跳变;
# 改为按动态清零判据补成 I=1(亦即纵轴下界),包络在全区间良定义,带子自然收口到底部。
_M = np.where(np.isfinite(_M), _M, 1.0)
rlo = np.maximum(_M.min(axis=0), 1.0)
rhi = _M.max(axis=0)
print(f"  routine ribbon done ({time.time()-t0:.0f}s)  N in [{Nrib[0]:.0f}, {Nrib[-1]:.0f}]")
rep_r = {float(N): prep(N)[2][["t", "I"]].to_dict("list") for N in (Nrib[0], Nrib[-1])}
# TDINN = 已发生的现实控制，只在全市口径下拟合一次，不随 N_eff 变 -> 单条曲线
_td = solve_tdinn(N_FULL)
print(f"  TDINN (city-fit) done ({time.time()-t0:.0f}s)")
tdinn_I = dict(t=_td["t"].to_numpy(float), I=_td["I"].to_numpy(float))
tdinn_q = dict(t=_td["t"].to_numpy(float), q=_td["q"].to_numpy(float))

out = dict(roles=roles, tend=tend, tg=tg, rlo=rlo, rhi=rhi, rn=rn,
           Nrib=Nrib, rep_r=rep_r, built=built, tdinn_I=tdinn_I, tdinn_q=tdinn_q)
with open(CACHE, "wb") as f:
    pickle.dump(out, f)
print(f"SAVED {CACHE}  total {time.time()-t0:.0f}s")
