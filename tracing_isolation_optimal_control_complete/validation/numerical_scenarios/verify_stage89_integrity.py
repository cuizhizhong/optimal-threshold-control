"""第8--9步独立核验；只读原始记录，以实际数组重新计算，不调用优化器。"""
import csv
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.io import loadmat
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
DATA = PROJECT / "data/numerical_scenarios"
CHECKS = DATA / "revision_checks"
CODE = PROJECT / "matlab/numerical_scenarios"
CASES = {f"E{k}" for k in range(1, 6)}
MODES = ("initialization", "grid", "horizon", "threshold")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def native_path(path):
    # Windows 下 assessment 文件名超过 MAX_PATH；显式保留完整绝对路径。
    name = str(path.resolve())
    if os.name == "nt":
        name = "\\\\?\\" + name
    return name


def mat(path, variable):
    return loadmat(native_path(path), simplify_cells=True)[variable]


def sha(path):
    with open(native_path(path), "rb") as stream:
        result = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def sequence(value):
    if isinstance(value, dict):
        return [value]
    if isinstance(value, np.ndarray):
        return list(value.reshape(-1))
    return list(value)


def arr(value):
    return np.asarray(value, dtype=float)


def close(a, b, tolerance=1e-12, context=""):
    aa, bb = arr(a), arr(b)
    assert aa.shape == bb.shape or aa.size == bb.size, context
    aa, bb = aa.reshape(-1), bb.reshape(-1)
    assert np.allclose(aa, bb, rtol=0, atol=tolerance, equal_nan=True), context


def same(a, b, context=""):
    """兼容 MATLAB 单元素/空数组与 JSON 标量/null 的值比较。"""
    if isinstance(a, dict) or isinstance(b, dict):
        assert isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys(), context
        for key in a:
            same(a[key], b[key], context + "/" + key)
    elif isinstance(a, str) or isinstance(b, str):
        assert str(a) == str(b), context
    else:
        # scipy 将 MATLAB 数组保存为 ndarray；数值 NaN 在 JSON 中为 null。
        def numeric(value):
            if value is None:
                return np.array([np.nan])
            if isinstance(value, (list, tuple)) and any(v is None for v in value):
                return np.array([np.nan if v is None else v for v in value])
            return arr(value)
        close(numeric(a), numeric(b), context=context)


def csv_agrees(path, rows):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        saved = list(csv.DictReader(stream))
    assert len(saved) == len(rows), str(path)
    for a, b in zip(saved, rows):
        for key, value in a.items():
            expected = b[key]
            if isinstance(expected, str):
                assert value == expected, (path.name, key)
            elif expected is None:
                assert value in ("NaN", "nan", ""), (path.name, key)
            else:
                close(float(value), expected, 1e-12, f"{path.name}/{key}")


def integrate(par, x0, edges, control, tau=None):
    """每个实际常控制区间独立 DOP853；峰值用增长率变号求根定位。"""
    n = len(control)
    nodes = np.empty((n + 1, 2)); nodes[0] = x0
    internals = []
    peak, peak_time = float(x0[1]), float(edges[0])
    for k, q in enumerate(control):
        left, right = edges[k:k + 2]
        def rhs(_, x):
            s, i = x
            return [-par["c"] * (par["p"] + (1 - par["p"]) * q) * s * i,
                    (par["p"] * par["c"] * (1 - q) * s - par["gamma"]) * i]
        sol = solve_ivp(rhs, (left, right), nodes[k], method="DOP853",
                        rtol=2e-11, atol=2e-14, dense_output=True)
        assert sol.success
        nodes[k + 1] = sol.y[:, -1]
        if tau is not None:
            internals.append(sol.sol(left + (right-left) * tau).T)
        local = max(nodes[k, 1], nodes[k + 1, 1])
        tp = left if nodes[k, 1] >= nodes[k + 1, 1] else right
        if q < 1:
            critical = par["gamma"] / (par["p"] * par["c"] * (1-q))
            if nodes[k, 0] > critical > nodes[k + 1, 0]:
                tp = brentq(lambda t: sol.sol(t)[0] - critical, left, right, xtol=1e-13)
                local = float(sol.sol(tp)[1])
        if local > peak:
            peak, peak_time = local, float(tp)
    return nodes, np.vstack(internals) if internals else None, peak, peak_time


def safe_peak(x, par):
    s, i = x; h = par["gamma"] / (par["p"] * par["c"])
    return float(i if s <= h else i+s-h-h*np.log(s/h))


def check_grid(run):
    grid, settings = run["actual_grid"], run["solver_settings"]
    n, t = int(settings["N"]), float(settings["T"])
    edges = arr(grid["control_interval_edges"])
    assert int(settings["d"]) == 2 and len(edges) == n+1
    close(edges, np.linspace(0, t, n+1), 2e-10, "uniform actual edges")
    close(grid["t_state"], edges, 1e-10)
    close(grid["t_control"], edges[:-1], 1e-10)
    close(grid["dt_control"], np.diff(edges), 1e-10)
    tau = arr(grid["collocation_tau"])[1:]
    close(tau, [1/3, 1], 1e-12)
    interior = (edges[:-1, None] + np.diff(edges)[:, None]*tau).reshape(-1)
    close(grid["t_integrator"], interior, 1e-10)
    close(run["initial_guess"]["t_state"], edges, 1e-10)
    close(run["initial_guess"]["t_control"], edges[:-1], 1e-10)
    close(run["initial_guess"]["t_integrator"], interior, 1e-10)
    a = run["actual_solver_settings"]
    assert not a["controls_regularization"]
    assert all(a[k] == "none" for k in ("terminal_constraint", "terminal_cost", "grid_constraints", "grid_costs"))
    close(a["state_lower_bounds"], [0, 0]); close(a["state_upper_bounds"], [1, run["parameters"]["K"]])
    assert a["control_lower_bound"] == 0 and a["control_upper_bound"] == 1
    close(a["initial_state"], run["x0"])
    return edges, tau


def check_initial(run, edges, tau):
    g, initial = run["initialization"], run["initial_guess"]
    control = arr(initial["control"])
    close(control, g["actual_control_guess"], 0, "actual initial control")
    close(initial["node_states"], initial["states"], 0, "initial node alias")
    out = {"run_id": run["run_id"], "type": g["type"], "capacity_excess": float(initial["capacity_excess"])}
    if g["type"] == "analytic_reference":
        return out
    if g["type"] == "constant_control":
        value = float(g["control"])
        assert 0 <= value <= 1
        close(control, np.full(len(edges)-1, value), 0, "actual constant control")
        out["control"] = value
    else:
        assert g["type"] == "seeded_random" and g["generator"] == "mt19937ar" and g["interpolation"] == "linear"
        seed = 20261008 + int(run["case_id"][1:]); assert int(g["seed"]) == seed
        final_time = float(run["solver_settings"]["T"])
        knots = np.unique(np.r_[np.arange(0, min(20, final_time)+1, 2), final_time])
        values = .15+.70*np.random.RandomState(seed).rand(len(knots))
        close(g["knot_times"], knots, 0, "random knot times")
        close(g["knot_values"], values, 0, "seed reconstruction")
        close(control, np.interp(edges[:-1], knots, values), 3e-15, "sampled random controls")
        out["seed"] = seed; out["seed_value_max_abs_difference"] = 0.0
    nodes, internals, _, _ = integrate(run["parameters"], arr(run["x0"]), edges, control, tau)
    node_error = float(np.max(np.abs(nodes-arr(initial["node_states"]))))
    internal_error = float(np.max(np.abs(internals-arr(initial["integrator_states"]))))
    assert node_error <= 2e-9 and internal_error <= 2e-9, (run["run_id"], node_error, internal_error)
    sampled_excess = max(0., float(np.max(arr(initial["node_states"])[:, 1])-run["parameters"]["K"]),
                         float(np.max(arr(initial["integrator_states"])[:, 1])-run["parameters"]["K"]))
    close(sampled_excess, initial["capacity_excess"], 2e-14, "initial sampled capacity excess")
    out.update(node_max_abs_difference=node_error, integrator_max_abs_difference=internal_error,
               independent_integrator="scipy DOP853 rtol=2e-11 atol=2e-14 per actual control interval")
    return out


def labels(control, nodes, k, epsq, epsk):
    q = arr(control); label = np.full(len(q), 3)
    label[np.abs(q) <= epsq] = 0; label[np.abs(q-1) <= epsq] = 1
    atcap = np.maximum(np.abs(nodes[:-1, 1]-k), np.abs(nodes[1:, 1]-k)) <= epsk
    label[atcap & (q > epsq) & (q < 1-epsq)] = 2
    names = ("0", "1", "q_B", "transition")
    starts = np.r_[0, np.flatnonzero(np.diff(label))+1]; ends = np.r_[starts[1:], len(q)]
    return label, [(names[label[a]], int(a), int(b)) for a, b in zip(starts, ends)]


def check_detection(det, run, a, epsq, epsk):
    nodes = np.c_[a["reintegration"]["s"], a["reintegration"]["i"]]
    label, arcs = labels(run["q_control"], nodes, run["parameters"]["K"], epsq, epsk)
    close(det["cell_labels"], label, 0, "detected labels from saved original control")
    observed = " -> ".join(name for name, _, _ in arcs if name != "transition")
    assert det["observed_structure"] == observed
    saved_arcs = sequence(det["arcs"])
    assert len(saved_arcs) == len(arcs)
    t = arr(run["t_state"])
    for arc, (name, left, right) in zip(saved_arcs, arcs):
        assert arc["type"] == name and int(arc["cells"]) == right-left
        close([arc["t_start"], arc["t_end"]], [t[left], t[right]], 1e-10)
    counts = {"intervention": 0, "capacity_enter": 0, "capacity_exit": 0, "full_start": 0, "release": 0}
    predicted_intervals = {name: [] for name in counts}
    invalid = False
    direct_allowed = {("0", "q_B"), ("0", "1"), ("q_B", "1"), ("1", "0")}
    transition_allowed = direct_allowed | {("initial", "q_B"), ("initial", "1")}
    for j, (name, left, right) in enumerate(arcs):
        previous = arcs[j-1][0] if j else "initial"
        following = arcs[j+1][0] if j+1 < len(arcs) else "missing"
        entering = ([t[left], t[left]] if j == 0 or previous != "transition" else
                    [t[arcs[j-1][1]], t[arcs[j-1][2]]])
        if name == "q_B":
            counts["capacity_enter"] += 1
            predicted_intervals["capacity_enter"].append(entering)
            counts["capacity_exit"] += int(j+1 < len(arcs))
            if j+1 < len(arcs):
                predicted_intervals["capacity_exit"].append(
                    [t[arcs[j+1][1]], t[arcs[j+1][2]]] if following == "transition" else [t[right], t[right]])
        if name == "1":
            counts["full_start"] += 1
            predicted_intervals["full_start"].append(entering)
        if name == "0" and j:
            counts["release"] += 1
            predicted_intervals["release"].append(entering)
        if name != "0" and (j == 0 or previous == "0"):
            counts["intervention"] += 1
            predicted_intervals["intervention"].append(
                [t[0], t[0]] if j == 0 else [t[left], t[right]] if name == "transition" else [t[left], t[left]])
        if name == "transition":
            invalid |= (right-left > det["thresholds"]["max_transition_cells"] or
                        (previous, following) not in transition_allowed)
        elif following not in ("transition", "missing"):
            invalid |= (name, following) not in direct_allowed
    invalid |= any(c > 1 for c in counts.values())
    assert bool(det["diagnostics"]["passed"]) == (not invalid), "detection diagnostics must match actual arcs"
    for name, count in counts.items():
        assert det["events"][name]["candidate_count"] == count
        candidates = sequence(det["events"][name]["candidates"])
        assert len(candidates) == count
        for candidate, interval in zip(candidates, predicted_intervals[name]):
            close(candidate["interval"], interval, 1e-10, "event candidate interval from actual arcs")
        if count == 1:
            close(det["events"][name]["interval"], predicted_intervals[name][0], 1e-10)
    for event in det["events"].values():
        if int(event["candidate_count"]) != 1:
            continue
        endpoint = arr(event["interval"])
        indices = [int(np.argmin(np.abs(t-v))) for v in endpoint]
        close(t[indices], endpoint, 1e-10, "event uses original nodes")
        close(event["numerical_endpoint_states"], nodes[indices].T, 1e-12)
        assert event["transition_cells"] == np.size(event["transition_cell_indices"])
    return observed


def check_event_comparison(saved, first, second):
    """只比较保存的数值事件，不用理论时刻补写或扩展区间。"""
    if not saved:
        return
    ea = first["assessment"]["structured_events"]; eb = second["assessment"]["structured_events"]
    for name, comp in saved.items():
        a, b = ea[name], eb[name]
        same(comp["reference_interval"], a["interval"]); same(comp["other_interval"], b["interval"])
        if a["candidate_count"] == b["candidate_count"] == 1:
            ia, ib = arr(a["interval"]), arr(b["interval"])
            distance = float(max(ia[0]-ib[1], ib[0]-ia[1], 0))
            allowed = max(a["local_max_cell_width"], b["local_max_cell_width"])
            close(distance, comp["distance_between_intervals"]); close(allowed, comp["allowed_cell_width"])
            passed = distance <= allowed+1e-10
        else:
            passed = a["candidate_count"] == b["candidate_count"] == 0
        assert bool(comp["passed"]) == bool(passed)


def recommended_grid_pair_checks(summary, runs, records):
    """按计划的建议口径检查最细级；不覆盖原调度器较严格的摘要状态。"""
    result = []
    for case in sorted(CASES):
        candidates = [r for r in summary["rows"] if r["case_id"] == case and r["N"] in (4000, 8000)]
        candidates.sort(key=lambda r: r["N"])
        assert len(candidates) == 2
        second, finest = [runs[r["run_id"]] for r in candidates]
        aa, bb = records[finest["run_id"]], records[second["run_id"]]
        out = {"case_id": case, "N_pair": [4000, 8000],
               "source_run_ids": [second["run_id"], finest["run_id"]],
               "finest_numeric_pass": False, "structure_comparable": False,
               "relative_cost_difference": None, "event_comparisons": {}, "recommended_consistency_pass": False}
        if aa is not None and bb is not None and finest["success"] and second["success"]:
            a, b = aa["assessment"], bb["assessment"]
            out["finest_numeric_pass"] = bool(a["numeric_pass"])
            out["structure_comparable"] = bool(a["observed_structure"] == b["observed_structure"] and
                                                 a["event_detection"]["diagnostics"]["passed"] and b["event_detection"]["diagnostics"]["passed"])
            out["relative_cost_difference"] = abs(finest["J_openocl"]-second["J_openocl"])/max(abs(finest["J_openocl"]), 1e-12)
            all_events = True
            for name in a["structured_events"]:
                first, other = a["structured_events"][name], b["structured_events"][name]
                distance = allowed = None
                if first["candidate_count"] == other["candidate_count"] == 1:
                    ia, ib = arr(first["interval"]), arr(other["interval"])
                    distance = float(max(ia[0]-ib[1], ib[0]-ia[1], 0))
                    allowed = float(max(first["local_max_cell_width"], other["local_max_cell_width"]))
                    passed = distance <= allowed+1e-10
                else:
                    passed = first["candidate_count"] == other["candidate_count"] == 0
                all_events &= passed
                out["event_comparisons"][name] = {"passed": bool(passed), "distance_between_intervals": distance, "allowed_cell_width": allowed}
            out["recommended_consistency_pass"] = bool(out["finest_numeric_pass"] and out["structure_comparable"] and all_events and out["relative_cost_difference"] <= 1e-4)
        result.append(out)
    return result


def check_assessment(run, record, edges):
    a, opts = record["assessment"], record["assessment_settings"]
    for name, expected in {"state_tolerance": 1e-6, "capacity_tolerance": 1e-6,
                           "control_tolerance": 1e-6, "tail_control_tolerance": 1e-6,
                           "relative_cost_tolerance": 1e-4, "capacity_control_tolerance": 2e-3,
                           "tail_duration": 20, "event_max_transition_cells": 2,
                           "event_control_threshold": 1e-3, "event_capacity_threshold": 2e-5}.items():
        assert opts[name] == expected, "predeclared assessment threshold changed: "+name
    assert record["run_id"] == run["run_id"] and record["solve_fingerprint"] == run["solve_fingerprint"]
    q, par = arr(run["q_control"]), run["parameters"]
    nodes, _, peak, peak_time = integrate(par, arr(run["x0"]), edges, q)
    saved_nodes = np.c_[a["reintegration"]["s"], a["reintegration"]["i"]]
    node_error = float(np.max(np.abs(nodes-saved_nodes)))
    assert node_error <= 2e-9, (run["run_id"], node_error)
    close(peak, a["reintegration"]["max_i"], 2e-9, "independent infection peak")
    # 峰时在平坦容量段可能由不同浮点极值决定；不把峰时差作为状态误差。
    cost = float(par["p"]*par["c"]*np.dot(q, np.diff(edges)))
    close(cost, run["J_openocl"], 3e-12, "complete weighted control cost")
    close(cost, a["J_reintegrated_control"], 3e-12)
    discrepancy = float(np.max(np.abs(nodes-np.c_[run["s_state"], run["i_state"]])))
    close(discrepancy, a["state_discrepancy"], 2e-9)
    close(max(0., peak-par["K"]), a["capacity_excess"], 2e-9)
    tail = float(np.max(np.abs(q[edges[1:] > edges[-1]-20])))
    close(tail, a["tail_max_q"], 1e-14)
    close(safe_peak(nodes[-1], par), a["terminal_peak"], 2e-9)
    output_nodes = np.c_[run["s_state"], run["i_state"]]
    initial_error = float(np.max(np.abs(output_nodes[0]-arr(run["x0"]))))
    control_violation = float(max(0, np.max(-q), np.max(q-1)))
    state_violation = float(max(0, np.max(-output_nodes), np.max(output_nodes[:, 0]-1), np.max(output_nodes[:, 1]-par["K"])))
    close(initial_error, a["initial_error"]); close(control_violation, a["control_violation"]); close(state_violation, a["state_violation"])
    expected_checks = {"solver_success": bool(run["success"]), "provenance": bool(a["provenance_pass"]),
                       "problem": bool(a["problem_pass"]), "capacity": a["capacity_excess"] <= opts["capacity_tolerance"],
                       "state_discrepancy": a["state_discrepancy"] <= opts["state_tolerance"],
                       "initial_state": initial_error <= opts["state_tolerance"],
                       "control_bounds": control_violation <= opts["control_tolerance"],
                       "node_state_bounds": state_violation <= opts["state_tolerance"],
                       "reintegration_state_bounds": a["reintegrated_state_violation"] <= opts["state_tolerance"],
                       "tail_control": tail <= opts["tail_control_tolerance"],
                       "safe_continuation": a["terminal_peak"] <= par["K"]+opts["capacity_tolerance"],
                       "cost_accounting": abs(run["J_openocl"]-a["J_reintegrated_control"]) <= opts["cost_accounting_tolerance"]*max(1, abs(a["J_reintegrated_control"]))}
    assert all(bool(a["numeric_checks"][name]) == bool(value) for name, value in expected_checks.items())
    assert bool(a["numeric_pass"]) == all(bool(v) for v in a["numeric_checks"].values())
    fixture = read_json(HERE / "analytic_checkpoints.json")
    reference = next(c for c in fixture["cases"] if c["case_id"] == run["case_id"])
    close(record["reference"]["J_reference"], reference["J_reference"], 2e-12, "independent analytic checkpoint cost")
    gap = a["J_reintegrated_control"]-record["reference"]["J_reference"]
    relative_gap = gap/max(abs(record["reference"]["J_reference"]), 1e-12)
    close(gap, a["signed_cost_difference"]); close(relative_gap, a["relative_cost_difference"])
    cost_pass = abs(relative_gap) <= opts["relative_cost_tolerance"]
    assert bool(a["cost_agreement"]["passed"]) == cost_pass
    assert bool(a["agreement_pass"]) == bool(cost_pass and a["event_comparison"]["agreement_pass"])
    check_detection(a["event_detection"], run, a, opts["event_control_threshold"], opts["event_capacity_threshold"])
    return {"run_id": run["run_id"], "independent_node_max_abs_difference": node_error,
            "J_full_control_sum": cost, "independent_peak_i": peak, "independent_peak_time": peak_time,
            "numeric_pass": bool(a["numeric_pass"]), "agreement_pass": bool(a["agreement_pass"])}


def check_summary_row(row, run, record):
    assert row["case_id"] == run["case_id"] and row["solve_fingerprint"] == run["solve_fingerprint"]
    assert bool(row["success"]) == bool(run["success"]) and row["return_status"] == run["return_status"]
    assert row["initialization"] == run["initialization"]["type"]
    if row["initialization"] == "constant_control":
        assert float(run["initialization"]["control"]) == .7, "default constant protocol"
    assert row["T"] == run["solver_settings"]["T"] and row["N"] == run["solver_settings"]["N"]
    same(row["J_openocl"], run.get("J_openocl", np.nan))
    if record is None:
        assert not run["success"] and not row["numeric_pass"] and not row["agreement_pass"]
        assert not row["event_intervals"] and row["observed_structure"] == ""
        assert all(row[k] is None for k in ("capacity_excess", "state_discrepancy", "tail_max_q", "terminal_peak"))
        return
    a = record["assessment"]
    for name in ("numeric_pass", "agreement_pass", "capacity_excess", "state_discrepancy", "tail_max_q", "terminal_peak", "observed_structure"):
        same(row[name], a[name], name)
    same(row["event_intervals"], a["structured_events"], "summary event intervals")


def main():
    started = time.perf_counter()
    baseline = read_json(HERE / "step89_baseline.json")
    preserved = []
    for item in baseline["historical_files"]:
        path = PROJECT / item["path"]
        assert path.stat().st_size == item["bytes"] and sha(path) == item["sha256"], item["path"]
        preserved.append(item["path"])
    index = read_json(DATA / "run_index.json")["entries"]
    inputs = read_json(HERE / "scenario_inputs.json")
    input_cases = {c["case_id"]: c for c in inputs["cases"]}
    indexed = {e["run_id"]: e for e in index}
    assert len(indexed) == len(index)
    assert {p.stem for p in (DATA / "runs").glob("*.mat")} == set(indexed), "raw MAT and run_index must be bijective"
    assert {p.name.removesuffix(".solver.json") for p in (DATA / "runs").glob("*.solver.json")} == set(indexed)
    for original in baseline["run_index_entries_at_start"]:
        assert indexed[original["run_id"]] == original, "historical index entry changed"
    runs, records, initial_checks, optimized_checks = {}, {}, [], []
    fingerprints = {}
    for entry in index:
        rid = entry["run_id"]; path = DATA / entry["raw_file"]
        assert sha(path) == entry["raw_sha256"], rid
        run = mat(path, "run"); runs[rid] = run
        assert run["run_id"] == rid and run["case_id"] == entry["case_id"]
        assert run["solve_fingerprint"] == entry["solve_fingerprint"] and bool(run["success"]) == entry["success"]
        assert int(run["attempt"]) == entry["attempt"]
        assert run["provenance"]["solve_started_utc"] == entry["solve_started_utc"]
        same(run["parameters"], inputs["parameters"], "original parameters")
        case = input_cases[run["case_id"]]
        close(run["x0"], [case["s0"], case["i0"]], 0, "original initial state")
        for field in ("case_id", "parameters", "x0", "solver_settings", "actual_solver_settings", "actual_grid", "initialization", "initial_guess"):
            same(run[field], run["solve_fingerprint_payload"][field], "immutable fingerprint payload/"+field)
        for source in sequence(run["provenance"]["solve_source_files"]):
            assert sha(CODE / source["path"]) == source["sha256"], source["path"]
        diagnostic = read_json(DATA / "runs" / f"{rid}.solver.json")
        assert diagnostic["run_id"] == rid and diagnostic["success"] == bool(run["success"])
        assert diagnostic["return_status"] == run["return_status"]
        for name, metric in run["solver_diagnostics"].items():
            if isinstance(metric, dict) and "status" in metric:
                stored = diagnostic["solver_diagnostics"][name]
                assert stored["status"] == metric["status"]
                same(stored["value"], metric["value"], "real solver diagnostic/"+name)
        edges, tau = check_grid(run)
        initial_checks.append(check_initial(run, edges, tau))
        matches = list((CHECKS / "assessments").glob(f"{rid}_*.mat"))
        assert matches or not run["success"], "successful record has no saved assessment: "+rid
        matches.sort(key=lambda p: os.stat(native_path(p)).st_mtime_ns)
        record = mat(matches[-1], "assessment_record") if matches else None
        records[rid] = record
        if run["success"]:
            optimized_checks.append(check_assessment(run, record, edges))
        fingerprints.setdefault(run["solve_fingerprint"], []).append(rid)
        print(f"CHECKED_RAW {rid} {run['case_id']} T={run['solver_settings']['T']} N={run['solver_settings']['N']} success={bool(run['success'])}", flush=True)
    for ids in fingerprints.values():
        assert sorted(int(runs[rid]["attempt"]) for rid in ids) == list(range(1, len(ids)+1)), "attempt records may not be dropped or overwritten"
    summaries, reports = {}, {}
    for mode in MODES:
        summary = read_json(CHECKS / f"{mode}_summary.json")
        csv_agrees(CHECKS / f"{mode}_summary.csv", summary["rows"])
        summaries[mode] = summary
        report = read_json(HERE / f"step89_{mode}_report.json"); reports[mode] = report
        assert report["mode"] == mode and report["finished_utc"]
        assert report["protocol_complete"], mode+" did not attempt the complete protocol"
        manifest = read_json(CHECKS / f"{report['batch_id']}_manifest.json")
        assert manifest["mode"] == mode and manifest["protocol_hash"] == report["protocol_hash"]
        assert manifest["default_unique_count"] == 35
        if mode != "threshold":
            expected_n = 10 if mode == "initialization" else 15
            assert len(summary["rows"]) == len(report["rows"]) == expected_n
            assert len({r["configuration_id"] for r in summary["rows"]}) == expected_n
            assert report["solver_calls"] == sum(bool(r["solver_called"]) for r in report["rows"])
            assert report["cache_hits"] == sum(bool(r["cache_hit"]) for r in report["rows"])
            assert report["successful_count"] == sum(bool(r["success"]) for r in report["rows"])
            assert report["failed_count"] == sum(not bool(r["success"]) for r in report["rows"])
            for row in summary["rows"]:
                rid = row["run_id"]; assert rid in indexed
                check_summary_row(row, runs[rid], records[rid])
                report_row = next(r for r in report["rows"] if r["configuration_id"] == row["configuration_id"])
                assert report_row["run_id"] == rid and report_row["solve_fingerprint"] == row["solve_fingerprint"]
                assert bool(report_row["success"]) == bool(row["success"])
                assert not report_row["cache_hit"] or row["success"], "failed solver result reused as successful cache"
                request = read_json(CHECKS / f"{report['batch_id']}_{row['configuration_id']}_request.json")
                assert request["case_id"] == row["case_id"] and request["solve_fingerprint"] == row["solve_fingerprint"]
                assert manifest["solve_code_hash"] == runs[rid]["provenance"]["solve_code_hash"]
                assert manifest["environment_fingerprint"] == runs[rid]["provenance"]["environment_fingerprint"]
                for field in ("actual_solver_settings", "actual_grid", "initialization", "initial_guess"):
                    same(request[field], runs[rid][field], "saved actual request/"+field)
            for case in CASES:
                rows = [r for r in summary["rows"] if r["case_id"] == case]
                expected = ({(300, 4000 if case in {"E1", "E3", "E5"} else 8000, g)
                             for g in ("constant_control", "seeded_random")} if mode == "initialization" else
                            {(300, n, "analytic_reference") for n in (2000, 4000, 8000)} if mode == "grid" else
                            {(t, n, "analytic_reference") for t, n in ((60, 1600), (120, 3200), (300, 8000))})
                assert {(r["T"], r["N"], r["initialization"]) for r in rows} == expected
                if mode == "horizon":
                    assert all(abs(r["T"]/r["N"]-.0375) <= 1e-14 for r in rows)
                comparison = next(c for c in summary["case_comparisons"] if c["case_id"] == case)
                assert set(comparison["source_run_ids"]) == {r["run_id"] for r in rows}
                base_id = comparison["reference_run_id"]
                if base_id:
                    base = runs[base_id]
                    assert base["case_id"] == case
                    if mode == "initialization":
                        assert base["initialization"]["type"] == "analytic_reference" and base["solver_settings"]["N"] == rows[0]["N"]
                        for row in rows:
                            actual = runs[row["run_id"]]
                            a = dict(actual["solver_settings"]); b = dict(base["solver_settings"])
                            a.pop("initialization"); b.pop("initialization")
                            same(a, b, "same discrete OCP options for initializations")
                        gaps = comparison["cost_absolute_difference"]
                        if gaps:
                            assert len(gaps) == len(rows)
                            for row, gap in zip(rows, gaps):
                                if gap is not None:
                                    close(abs(row["J_openocl"]-base["J_openocl"]), gap, 2e-14)
                        for row, events in zip(rows, comparison["event_comparisons"]):
                            if events:
                                check_event_comparison(events, records[base_id], records[row["run_id"]])
                    else:
                        assert base["solver_settings"]["T"] == 300 and base["solver_settings"]["N"] == 8000
                if mode == "grid" and comparison["finest_relative_cost_difference"] is not None:
                    ordered = sorted(rows, key=lambda r: r["N"])
                    costs = [r["J_openocl"] for r in ordered]
                    close(abs(costs[-1]-costs[-2])/max(abs(costs[-1]), 1e-12), comparison["finest_relative_cost_difference"], 2e-14)
                    check_event_comparison(comparison["event_comparisons"], records[ordered[-1]["run_id"]], records[ordered[-2]["run_id"]])
                if mode == "horizon" and comparison["cost_absolute_span"] is not None:
                    costs = [r["J_openocl"] for r in rows]
                    close(max(costs)-min(costs), comparison["cost_absolute_span"], 2e-14)
                    base = runs[base_id]; ba = records[base_id]["assessment"]
                    for row, events in zip(sorted(rows, key=lambda r: r["T"]), comparison["event_comparisons"]):
                        if events:
                            check_event_comparison(events, records[base_id], records[row["run_id"]])
                    for row, window in zip(sorted(rows, key=lambda r: r["T"]), comparison["common_window_comparisons"]):
                        run = runs[row["run_id"]]; a = records[row["run_id"]]["assessment"]
                        ia = arr(base["t_state"]) <= 18+1e-10; ib = arr(run["t_state"]) <= 18+1e-10
                        assert window["same_control_step"] and ia.sum() == ib.sum()
                        state_a = np.c_[ba["reintegration"]["s"], ba["reintegration"]["i"]][ia]
                        state_b = np.c_[a["reintegration"]["s"], a["reintegration"]["i"]][ib]
                        close(np.max(np.abs(state_a-state_b)), window["state_max_abs_difference"], 2e-14)
                        qa = arr(base["q_control"])[arr(base["t_control"]) <= 18+1e-10]
                        qb = arr(run["q_control"])[arr(run["t_control"]) <= 18+1e-10]
                        close(np.max(np.abs(qa-qb)), window["control_max_abs_difference"], 2e-14)
            assert bool(summary["consistency_pass"]) == bool(summary["protocol_complete"] and summary["comparison_complete"] and
                                                            all(c["consistency_pass"] for c in summary["case_comparisons"]))
        else:
            assert report["solver_calls"] == report["cache_hits"] == report["attempted_count"] == 0
            assert summary["optimizer_calls"] == 0 and len(summary["rows"]) == 45
            selected = {e["case_id"]: e["run_id"] for e in read_json(DATA / "selection_manifest.json")["entries"]}
            for case in CASES:
                rows = [r for r in summary["rows"] if r["case_id"] == case]
                assert {(r["control_threshold"], r["capacity_threshold"]) for r in rows} == {
                    (q, k) for q in (5e-4, 1e-3, 2e-3) for k in (1e-5, 2e-5, 4e-5)}
                assert {r["run_id"] for r in rows} == {selected[case]}
                for row in rows:
                    rid = row["run_id"]; run, a = runs[rid], records[rid]["assessment"]
                    assert row["solve_fingerprint"] == run["solve_fingerprint"]
                    check_detection(row["detection"], run, a, row["control_threshold"], row["capacity_threshold"])
                    passes = []
                    for name, comp in row["event_comparison"].items():
                        first = a["event_detection"]["events"][name]; second = row["detection"]["events"][name]
                        status = first["status"] == second["status"] and first["candidate_count"] == second["candidate_count"]
                        if first["candidate_count"] == second["candidate_count"] == 1:
                            shift = float(np.max(np.abs(arr(first["interval"])-arr(second["interval"]))))
                            allowed = max(first["local_max_cell_width"], second["local_max_cell_width"])
                            close(shift, comp["endpoint_maximum_shift"], 1e-12); close(allowed, comp["local_maximum_cell_width"], 1e-12)
                            passed = status and shift <= allowed+1e-10
                        else:
                            passed = status and first["candidate_count"] == 0
                        assert bool(comp["passed"]) == passed; passes.append(passed)
                    expected_pass = (a["observed_structure"] == row["observed_structure"] and row["detection"]["diagnostics"]["passed"] and all(passes))
                    assert bool(row["consistency_pass"]) == bool(expected_pass)
            assert bool(summary["consistency_pass"]) == all(r["consistency_pass"] for r in summary["rows"])
    configured = set()
    for r in runs.values():
        g = r["initialization"]
        seed = int(g["seed"]) if np.size(g.get("seed", [])) else None
        control = float(g["control"]) if "control" in g else None
        configured.add((r["case_id"], r["solver_settings"]["T"], r["solver_settings"]["N"], g["type"], seed, control))
    expected_configurations = set()
    for case in CASES:
        main_n = input_cases[case]["main_N"]
        for guess in ("analytic_reference", "constant_control", "seeded_random"):
            seed = 20261008+int(case[1:]) if guess == "seeded_random" else None
            control = .7 if guess == "constant_control" else None
            expected_configurations.add((case, 300, main_n, guess, seed, control))
        expected_configurations.update((case, 300, n, "analytic_reference", None, None) for n in (2000, 4000, 8000))
        expected_configurations.update((case, t, n, "analytic_reference", None, None) for t, n in ((60, 1600), (120, 3200), (300, 8000)))
    assert len(expected_configurations) == 35 and expected_configurations <= configured, "default optimization configurations incomplete"
    counts = {mode: {k: reports[mode][k] for k in ("solver_calls", "cache_hits", "successful_count", "failed_count", "protocol_complete", "consistency_pass")} for mode in MODES}
    report = {"passed": True, "scope": "steps_8_to_9", "starting_commit": baseline["starting_commit"],
              "protected_original_files": len(preserved), "unchanged_historical_paths": preserved,
              "indexed_raw_records": len(runs), "all_raw_sha256_verified": True,
              "default_distinct_configurations_observed": len(expected_configurations),
              "additional_distinct_configurations_observed": len(configured-expected_configurations), "execution_counts": counts,
              "non_theory_initial_controls_verified": sum(r["type"] != "analytic_reference" for r in initial_checks),
              "initial_guess_checks": initial_checks, "independent_original_control_checks": optimized_checks,
              "max_independent_initial_guess_state_difference": max(
                  (max(r.get("node_max_abs_difference", 0), r.get("integrator_max_abs_difference", 0)) for r in initial_checks), default=0),
              "max_independent_original_control_node_difference": max(
                  (r["independent_node_max_abs_difference"] for r in optimized_checks), default=0),
              "recommended_grid_pair_checks": recommended_grid_pair_checks(summaries["grid"], runs, records),
              "threshold_source_records": 5, "threshold_detection_rows": 45, "threshold_optimizer_calls": 0,
              "independent_python_environment": {"numpy": np.__version__, "scipy": scipy.__version__},
              "failed_solver_records_preserved": [rid for rid, r in runs.items() if not r["success"]],
              "numeric_failed_records_preserved": [rid for rid, a in records.items() if a is None or not a["assessment"]["numeric_pass"]],
              "agreement_failed_records_preserved": [rid for rid, a in records.items() if a is None or not a["assessment"]["agreement_pass"]],
              "elapsed_seconds": time.perf_counter()-started,
              "limitations": "状态、峰值与阈值结果均为浮点诊断，不构成连续时间严格可行性或全局最优性证书。"}
    (HERE / "step89_integrity_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"STAGE89_INTEGRITY_OK protected={len(preserved)} raw={len(runs)} non_theory_initials={report['non_theory_initial_controls_verified']} threshold=45 optimizer_calls=0")


if __name__ == "__main__":
    main()
