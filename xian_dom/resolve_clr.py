"""重算 clr 弧到精确口径 t_end^T = 45.27 d（原为圆整 45.0 d）。
输出 clr_4527.json（与本文件同目录）：弧线全部点、有效池下界端点、峰值顶端点、N_clr(100)。"""
import sys, json, time, numpy as np
from pathlib import Path
# 自动把三个求解器模块目录加入 sys.path（免手动设 PYTHONPATH）。
_XCC = Path(__file__).resolve().parent.parent / "xian_control_comparison"
for _p in (_XCC, _XCC / "threshold_landscape_analysis", _XCC / "effective_population_sensitivity"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
_OUTJSON = Path(__file__).resolve().parent / "clr_4527.json"
if not hasattr(np, "trapz"):
    np.trapz = np.trapezoid
from scipy.optimize import brentq
import xian_control_comparison as xcc
import threshold_landscape_analysis as tla
from effective_population_sensitivity import fit_initial_condition_for_N

TARGET = 45.27          # TDINN 清零时刻（§7 表值）
IPEAK = 151.90
NFLOOR = 2096.76        # 有效池下界 = I^T_tcum
YMIN = 10.0             # 图纵轴下界

OBS = xcc.load_observed_data()
_c = {}


def prep(N):
    N = float(N)
    if N not in _c:
        p = tla.LandscapeParams(N=N)
        f = fit_initial_condition_for_N(OBS, p)
        r = tla.solve_time_control_param("常规控制", f, p, tla.c_const(p), tla.q_const(p))
        _c[N] = (p, f, r)
    return _c[N]


def clear_of(N, eta):
    p, f, r = prep(N)
    df, d = tla.solve_threshold_fast(f, eta, p, r)
    return float(tla.summarize_threshold(df, eta, p, d)["clear_time"])


# 旧弧（45.0 d）作为求根初值来源
OLD_N = [1125, 1135, 1150, 1170, 1200, 1250, 1300, 1350, 1400, 1450, 1500,
         1539, 1692, 1860, 2045, 2096.76, 2249, 2472, 2718, 2988, 3285, 3611,
         3970, 4365, 4799, 5276, 5800]
OLD_E = [10.24, 10.39, 10.61, 10.91, 11.37, 12.15, 12.96, 13.79, 14.64,
         15.51, 16.40, 17.11, 19.99, 23.33, 27.22, 28.3480, 31.77, 37.04,
         43.20, 50.38, 58.79, 68.63, 80.14, 93.67, 109.63, 128.45, 150.68]

t0 = time.time()
out_N, out_E = [], []
for N, e0 in zip(OLD_N, OLD_E):
    try:
        e = brentq(lambda x: clear_of(N, x) - TARGET, 0.80 * e0, 1.20 * e0, xtol=1e-4)
        out_N.append(float(N)); out_E.append(float(e))
        print(f"  N={N:9.2f}  eta*: {e0:7.3f} -> {e:7.3f}  ({100*(e-e0)/e0:+5.2f}%)  "
              f"[{time.time()-t0:.0f}s]", flush=True)
    except Exception as ex:
        print(f"  N={N:9.2f}  FAIL {ex}", flush=True)

# 顶端：弧线与峰值天花板 eta=I^T_peak 的交点
N_top = brentq(lambda N: clear_of(N, IPEAK) - TARGET, 5000, 7000, xtol=1e-2)
print(f"\n顶端 (eta=I^T_peak): N={N_top:.1f}  校验 clear={clear_of(N_top, IPEAK):.3f}")

# 有效池下界端点
i_fl = out_N.index(NFLOOR)
eta_floor = out_E[i_fl]
print(f"有效池下界: N={NFLOOR}  eta*={eta_floor:.4f}  校验 clear={clear_of(NFLOOR, eta_floor):.3f}")

# eta=100 处的 N_clr（直接对 N 求根，比插值准）
N_clr100 = brentq(lambda N: clear_of(N, 100.0) - TARGET, 3500, 5500, xtol=1e-2)
print(f"N_clr(eta=100) = {N_clr100:.1f}  校验 clear={clear_of(N_clr100, 100.0):.3f}")

# 尾端：若最低点已跌破图纵轴下界，另求 eta*=YMIN 处的 N 作为收尾
tail = None
if out_E[0] < YMIN:
    tail = brentq(lambda N: clear_of(N, YMIN) - TARGET, 1119.0, 1400.0, xtol=1e-2)
    print(f"尾端(eta={YMIN}): N={tail:.1f}  校验 clear={clear_of(tail, YMIN):.3f}")
else:
    print(f"尾端未跌破 eta={YMIN}（最低 eta*={out_E[0]:.3f}），保留原最低 N={out_N[0]:.0f}")

json.dump(dict(target=TARGET, N=out_N, eta=out_E, N_top=float(N_top),
               N_floor=NFLOOR, eta_floor=float(eta_floor),
               N_clr100=float(N_clr100), tail_N=(float(tail) if tail else None)),
          open(_OUTJSON, "w"), indent=1)
print(f"\nSAVED {_OUTJSON}   总耗时 {time.time()-t0:.0f}s")
