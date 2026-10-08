#!/usr/bin/env python3
"""独立评价正文解析公式；不读取优化结果，也不修改论文或 MATLAB 数组。"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import mpmath as mp

ROOT = Path(__file__).resolve().parent
DPS = 50
ROOT_TOL = mp.mpf("1e-40")
CHECK_TOL = 5e-12


def bracket_root(fun, lo, hi):
    """有界二分法；只有符号变号区间才交给求根器。"""
    fl, fh = fun(lo), fun(hi)
    if fl == 0:
        return lo
    if fh == 0:
        return hi
    if not mp.isfinite(fl) or not mp.isfinite(fh) or fl * fh >= 0:
        raise ValueError("Root is not bracketed by finite opposite signs")
    for _ in range(400):
        mid = (lo + hi) / 2
        fm = fun(mid)
        if fm == 0 or hi - lo < ROOT_TOL * max(1, abs(mid)):
            return mid
        if fl * fm < 0:
            hi = mid
        else:
            lo, fl = mid, fm
    raise RuntimeError("Bounded root did not converge")


class Geometry:
    def __init__(self, parameters):
        self.p, self.c, self.gamma, self.K = (
            mp.mpf(str(parameters[key])) for key in ("p", "c", "gamma", "K")
        )
        if not (0 < self.p < 1 and min(self.c, self.gamma, self.K) > 0):
            raise ValueError("Invalid model parameters")
        self.h = self.gamma / (self.p * self.c)
        self.ell = self.gamma / self.c
        self.r = self.h - self.ell
        self.Phi_A = self.K + self.h - self.h * mp.log(self.h)
        hi = max(mp.mpf(1), 2 * self.h)
        while self.a(hi) > 0:
            hi *= 2
        self.s_K = bracket_root(self.a, self.h, hi)
        self.e = bracket_root(lambda s: self.a(s) - self.g(s), self.h, self.s_K)
        lo = (self.h + self.e) / 2
        while self.switch_point(lo)[1] < self.K:
            lo = self.h + (lo - self.h) / 10
        self.z_B = bracket_root(lambda z: self.switch_point(z)[1] - self.K, lo, self.e)
        self.s_B, i_B, self.peak_B = self.switch_point(self.z_B)
        assert abs(i_B - self.K) < mp.mpf("1e-35")
        self.Phi_B = self.phi(self.s_B, self.K)

    def phi(self, s, i):
        return i + s - self.h * mp.log(s)

    def a(self, s):
        return self.Phi_A - s + self.h * mp.log(s)

    def g(self, s):
        return (s - self.h) * (s - self.r) / s

    def G(self, s):
        return self.a(s) - self.ell * mp.log(s)

    def theta(self, s, i):
        return (s - self.h) / (i * (s - self.r))

    def switch_point(self, z):
        """先解 I_z=g 定位峰点，再解峰点右侧的正文原始 Theta 方程。"""
        if z == self.e:
            return z, self.a(z), z  # 已知合并极限，不作为非平凡根。
        if not self.h < z < self.e:
            raise ValueError("Nontrivial switch requires h < z < e")
        az = self.a(z)
        iz = lambda s: az + self.ell * mp.log(s / z)
        hi = max(2 * z, self.e)
        while iz(hi) - self.g(hi) > 0:
            hi *= 2
        peak = bracket_root(lambda s: iz(s) - self.g(s), z, hi)
        level = self.theta(z, az)
        original_theta = lambda s: self.theta(s, iz(s)) - level
        assert peak > z and original_theta(peak) > 0
        hi = 2 * peak
        while original_theta(hi) >= 0:
            hi *= 2
        s = bracket_root(original_theta, peak, hi)
        i = iz(s)
        assert s > peak > z and i > 0  # 显式排除 s=z 及零长度假根。
        assert abs(original_theta(s)) < mp.mpf("1e-34")
        return s, i, peak

    def endpoint(self, s, i):
        if not s * mp.exp(-i / self.ell) < self.s_K:
            raise ValueError("Full tracing has no reachable positive safe endpoint")
        psi = i - self.ell * mp.log(s)
        z = bracket_root(lambda v: self.G(v) - psi, self.h, min(s, self.s_K))
        return z, self.a(z)

    def waiting_time(self, s0, i0, s_end):
        if s0 == s_end:
            return mp.mpf(0)
        label = self.phi(s0, i0)
        integrand = lambda s: 1 / (self.p * self.c * s * (label - s + self.h * mp.log(s)))
        # 两级独立精度评价确认自适应积分收敛。
        value = mp.quad(integrand, [s_end, (s0 + s_end) / 2, s0])
        with mp.workdps(DPS + 15):
            refined = mp.quad(integrand, [s_end, (s0 + s_end) / 2, s0])
        assert abs(value - refined) < mp.mpf("1e-35")
        return value

    def safe_peak(self, s, i):
        return i if s <= self.h else i + s - self.h - self.h * mp.log(s / self.h)


def evaluate_case(row, geo):
    s0, i0 = mp.mpf(str(row["s0"])), mp.mpf(str(row["i0"]))
    if not (s0 > 0 and 0 < i0 <= geo.K and s0 + i0 <= 1):
        raise ValueError(f"Invalid initial state: {row['case_id']}")
    label = geo.phi(s0, i0)
    zero = mp.mpf(0)
    tw = tb = tf = cb = zero
    capacity = None
    sf = iff = None
    if geo.safe_peak(s0, i0) <= geo.K:
        region, sr, ir = "A", s0, i0
    else:
        if label > geo.Phi_B:
            if i0 == geo.K:
                region, capacity = "B", s0
            else:
                region = "W_K"
                capacity = bracket_root(lambda s: geo.phi(s, geo.K) - label, geo.h, s0)
                tw = geo.waiting_time(s0, i0, capacity)
            sf, iff = geo.s_B, geo.K
            tb = mp.log((capacity - geo.r) / (sf - geo.r)) / (geo.c * geo.K)
            cb = geo.p / (geo.K * (1 - geo.p)) * (
                mp.log(capacity / sf) - geo.p * mp.log((capacity - geo.r) / (sf - geo.r))
            )
        else:
            z = bracket_root(lambda v: geo.phi(*geo.switch_point(v)[:2]) - label, geo.z_B, geo.e)
            sg, ig, _ = geo.switch_point(z)
            if s0 > sg:
                region, sf, iff = "W_Gamma", sg, ig
                tw = geo.waiting_time(s0, i0, sf)
            else:
                region, sf, iff = "T", s0, i0
        sr, ir = geo.endpoint(sf, iff)
        tf = mp.log(iff / ir) / geo.gamma
        assert zero < ir <= iff <= geo.K and geo.h < sr < sf
        assert abs(geo.safe_peak(sr, ir) - geo.K) < mp.mpf("1e-35")
        assert abs((iff - geo.ell * mp.log(sf)) - (ir - geo.ell * mp.log(sr))) < mp.mpf("1e-35")
        assert sr + ir <= sf + iff <= s0 + i0
    assert region == row["expected_region"], f"Region differs for {row['case_id']}"
    t_full = None if region == "A" else tw + tb
    t_release = None if region == "A" else tw + tb + tf
    # 安全算例无解除事件；其自然峰值时刻从初始状态计算。
    peak_time = (zero if region == "A" else t_release) + (
        geo.waiting_time(sr, ir, geo.h) if sr > geo.h else zero
    )
    out = dict(case_id=row["case_id"], s0=s0, i0=i0, region=region, phi0=label,
               s_capacity=capacity, s_full=sf, i_full=iff, s_release=sr, i_release=ir,
               tau_wait=tw, tau_boundary=tb, tau_full=tf, t_full_start=t_full,
               t_release=t_release, t_natural_peak=peak_time, J_boundary=cb,
               J_reference=cb + geo.p * geo.c * tf)
    return {key: float(value) if isinstance(value, mp.mpf) else value for key, value in out.items()}


def load_inputs(path):
    inputs = json.loads(path.read_text(encoding="utf-8"))
    if inputs.get("schema_version") != 1:
        raise ValueError("Unsupported scenario_inputs schema")
    ids = [row["case_id"] for row in inputs["cases"]]
    required = inputs["main_case_ids"] + [inputs["safe_case_id"]]
    if len(ids) != len(set(ids)) or set(ids) != set(required) or len(required) != len(set(required)):
        raise ValueError("Missing, duplicated, or unexpected case_id")
    if sorted(inputs["run_order"]) != sorted(inputs["main_case_ids"]):
        raise ValueError("run_order must contain every main case exactly once")
    return inputs


def calculate(inputs):
    with mp.workdps(DPS):
        geo = Geometry(inputs["parameters"])
        indexed = {row["case_id"]: row for row in inputs["cases"]}
        cases = [evaluate_case(indexed[key], geo) for key in inputs["main_case_ids"] + [inputs["safe_case_id"]]]
        geometry = {key: float(getattr(geo, key)) for key in (
            "h", "ell", "r", "s_K", "e", "z_B", "s_B", "Phi_A", "Phi_B"
        )}
        geometry["theta_peak_s_at_z_B"] = float(geo.peak_B)
    canonical = dict(inputs, cases=sorted(inputs["cases"], key=lambda row: row["case_id"]))
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return dict(schema_version=2, status="analytical_formula_evaluation_only", openocl_executed=False,
                generator=dict(implementation="mpmath_original_theta_peak_then_nontrivial_root",
                               mpmath_version=mp.__version__, decimal_precision=DPS,
                               root_tolerance="1e-40", check_absolute_tolerance=CHECK_TOL,
                               input_sha256=digest),
                parameters=inputs["parameters"], geometry=geometry, cases=cases)


def compare_fixture(actual, expected):
    """按 case_id 比较，fixture 的数组顺序不影响验证。"""
    def compare(a, b, path):
        if isinstance(a, dict):
            if not isinstance(b, dict) or set(a) != set(b):
                raise ValueError(f"Fixture fields differ at {path}")
            for key in a:
                compare(a[key], b[key], f"{path}.{key}")
        elif isinstance(a, bool) or a is None or isinstance(a, str):
            if a != b:
                raise ValueError(f"Fixture metadata differs at {path}")
        elif isinstance(a, (int, float)):
            if not isinstance(b, (int, float)) or isinstance(b, bool) or not math.isfinite(b) or abs(a - b) > CHECK_TOL:
                raise ValueError(f"Fixture value differs at {path}: {a!r} versus {b!r}")
        else:
            raise TypeError(f"Unsupported fixture value at {path}")
    compare({key: value for key, value in actual.items() if key != "cases"},
            {key: value for key, value in expected.items() if key != "cases"}, "fixture")
    def index(rows):
        result = {row["case_id"]: row for row in rows}
        if len(rows) != len(result):
            raise ValueError("Duplicated case_id in fixture")
        return result
    compare(index(actual["cases"]), index(expected["cases"]), "fixture.cases")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="重新计算并只读比较已有 fixture")
    action.add_argument("--write", action="store_true", help="显式生成解析 fixture")
    parser.add_argument("--inputs", type=Path, default=ROOT / "scenario_inputs.json")
    parser.add_argument("--fixture", type=Path, default=ROOT / "analytic_checkpoints.json")
    args = parser.parse_args()
    actual = calculate(load_inputs(args.inputs))
    if args.check:
        if not args.fixture.is_file():
            raise FileNotFoundError(f"Missing fixture: {args.fixture}; run {Path(__file__).name} --write")
        compare_fixture(actual, json.loads(args.fixture.read_text(encoding="utf-8")))
        print("ANALYTIC_CHECKPOINTS_CHECK_OK (read only; optimizer executions=0)")
    else:
        args.fixture.write_text(json.dumps(actual, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"ANALYTIC_CHECKPOINTS_WRITTEN: {args.fixture} (optimizer executions=0)")
    for row in actual["cases"]:
        print(f"{row['case_id']}: {row['region']} J_reference={row['J_reference']:.12f}")


if __name__ == "__main__":
    main()
