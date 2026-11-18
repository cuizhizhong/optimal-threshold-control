#!/usr/bin/env python3
"""High-precision checks of the manuscript's analytic formulas.

Run from any directory:
    python scripts/verify_analytic_results.py

Requires Python 3 and mpmath. Table 4 is read from latex/main.tex and
latex/generated/scaling_values.tex relative to this script's project directory.
The checks independently evaluate the endpoint identities, capacity costs,
table entries, asymptotic coefficients, and physical parameter regimes.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import mpmath as mp


mp.mp.dps = 110
IDENTITY_TOLERANCE = mp.mpf("1e-65")
FINEST_ASYMPTOTIC_TOLERANCE = mp.mpf("1e-5")


def number(value):
    """Read decimal strings without first rounding to a binary float."""
    if isinstance(value, mp.mpf):
        return value
    return mp.mpf(str(value))


def serialize(value):
    if isinstance(value, mp.mpf):
        return mp.nstr(value, 80)
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize(item) for item in value]
    return value


def relative_error(actual, reference):
    if reference == 0:
        return abs(actual)
    return abs(actual / reference - 1)


def reduced_parameters(v, beta):
    """Positive endpoint parameter v; Eq. (small-K-parametrization)."""
    if not v:
        return mp.mpf(0), mp.mpf(0)
    f = v - mp.log1p(v)
    u = mp.expm1(mp.log1p(v) + f / beta)
    k = u * (beta + v) * f / (beta * (u - v))
    return u, k


def solve_positive_endpoint(beta, k):
    """Bracket and bisect the scalar equation, without the original solver."""
    lo, hi = mp.mpf(0), max(k / beta, mp.mpf("0.01"))
    for _ in range(60):
        if reduced_parameters(hi, beta)[1] > k:
            break
        hi *= 2
    else:
        raise ArithmeticError("Could not bracket the positive endpoint")
    for _ in range(450):
        mid = (lo + hi) / 2
        if reduced_parameters(mid, beta)[1] < k:
            lo = mid
        else:
            hi = mid
        if hi - lo < mp.mpf("1e-95") * mid:
            return (lo + hi) / 2
    raise ArithmeticError("Endpoint bisection did not reach its tolerance")


def geometry(beta, c, gamma, capacity):
    beta, c, gamma, capacity = map(number, (beta, c, gamma, capacity))
    if not (0 < beta < 1 and c > 0 and gamma > 0 and 0 < capacity < 1):
        raise ValueError("Parameters do not satisfy the manuscript assumptions")
    h = gamma / (beta * c)
    ell, p = beta * h, (1 - beta) * h
    v = solve_positive_endpoint(beta, capacity / h)
    u, k_evaluated = reduced_parameters(v, beta)
    s_b, s_end = h * (1 + u), h * (1 + v)
    i_end = capacity - h * (v - mp.log1p(v))
    if not (h < s_end < s_b and 0 < i_end < capacity):
        raise AssertionError("Incorrect order of the switching and safe states")
    theta = lambda s, i: (s - h) / (i * (s - p))
    invariant_start = capacity - ell * mp.log(s_b)
    invariant_end = i_end - ell * mp.log(s_end)
    safe_peak = i_end + s_end - h - h * mp.log(s_end / h)
    residuals = {
        "scalar_equation_relative": relative_error(k_evaluated, capacity / h),
        "full_tracking_invariant_scaled": abs(invariant_start - invariant_end)
        / max(capacity, ell),
        "safe_boundary_relative": relative_error(safe_peak, capacity),
        "theta_matching_relative": relative_error(
            theta(s_b, capacity), theta(s_end, i_end)
        ),
    }
    for name, residual in residuals.items():
        if residual >= IDENTITY_TOLERANCE:
            raise AssertionError((name, mp.nstr(residual, 12)))
    return {
        "beta": beta, "c": c, "gamma": gamma, "K": capacity,
        "h": h, "ell": ell, "p": p, "s_B": s_b,
        "s_end": s_end, "i_end": i_end, "residuals": residuals,
    }


def capacity_cost(parameters, high, low):
    beta, p, capacity = (
        parameters["beta"], parameters["p"], parameters["K"]
    )
    return beta / (capacity * (1 - beta)) * (
        mp.log(high / low) - beta * mp.log((high - p) / (low - p))
    )


def capacity_time(parameters, high, low):
    return mp.log((high - parameters["p"]) / (low - parameters["p"])) / (
        parameters["c"] * parameters["K"]
    )


def common_tail_comparison(parameters, entry):
    """Compare closed-form total costs with independently integrated tails."""
    entry = number(entry)
    beta, c, gamma, capacity, h, p, s_b, i_end = (
        parameters[key]
        for key in ("beta", "c", "gamma", "K", "h", "p", "s_B", "i_end")
    )
    if not (s_b <= entry and entry + capacity <= 1):
        raise ValueError("A physical common capacity entry is required")
    tracking_cost = mp.log(capacity / i_end) / h
    tracking_time = mp.log(capacity / i_end) / gamma
    fill_cost = capacity_cost(parameters, entry, h)
    optimal_cost = capacity_cost(parameters, entry, s_b) + tracking_cost
    fill_time = capacity_time(parameters, entry, h)
    optimal_time = capacity_time(parameters, entry, s_b) + tracking_time

    # This quadrature is independent of the logarithmic antiderivative.
    integrated_tail_cost = beta / capacity * mp.quad(
        lambda s: (s - h) / (s * (s - p)), [h, s_b]
    )
    integrated_tail_time = mp.quad(
        lambda s: 1 / (c * capacity * (s - p)), [h, s_b]
    )
    delta_cost = integrated_tail_cost - tracking_cost
    delta_time = integrated_tail_time - tracking_time
    residuals = {
        "capacity_cost_quadrature_relative": relative_error(
            capacity_cost(parameters, s_b, h), integrated_tail_cost
        ),
        "capacity_time_quadrature_relative": relative_error(
            capacity_time(parameters, s_b, h), integrated_tail_time
        ),
        "common_tail_cost_identity_relative": relative_error(
            fill_cost - optimal_cost, delta_cost
        ),
        "common_tail_time_identity_relative": relative_error(
            fill_time - optimal_time, delta_time
        ),
    }
    for name, residual in residuals.items():
        if residual >= IDENTITY_TOLERANCE:
            raise AssertionError((name, mp.nstr(residual, 12)))
    if not (0 < optimal_cost < fill_cost and 0 < optimal_time < fill_time):
        raise AssertionError("Unexpected cost or duration order in a checked case")
    return {
        "s_1": entry, "J_fill": fill_cost, "J_star": optimal_cost,
        "Delta_J": delta_cost, "T_fill": fill_time, "T_star": optimal_time,
        "Delta_T": delta_time, "relative_cost_saving": delta_cost / fill_cost,
        "relative_duration_reduction": delta_time / fill_time,
        "duration_ratio": optimal_time / fill_time, "residuals": residuals,
    }


def newly_quarantined_susceptibles(parameters, s0, i0):
    """Evaluate the two policies at the manuscript's reported initial state."""
    s0, i0 = map(number, (s0, i0))
    beta, h, ell, p, capacity, s_b, s_end = (
        parameters[key] for key in ("beta", "h", "ell", "p", "K", "s_B", "s_end")
    )

    def entry_residual(s):
        return i0 + s0 - s + h * mp.log(s / s0) - capacity

    if not (0 < i0 <= capacity and h < s0 and s0 + i0 <= 1):
        raise ValueError("A physical initial state on the increasing infection branch is required")
    entry = s0 if i0 == capacity else mp.findroot(entry_residual, (h, s0), solver="anderson")
    if not (s_b <= entry <= s0 and abs(entry_residual(entry)) < IDENTITY_TOLERANCE):
        raise AssertionError("The two policies do not have a common capacity entry")

    def capacity_increment(low):
        return (1 - beta) * (entry - low - ell * mp.log((entry - p) / (low - p)))

    # Check the logarithmic antiderivative against direct quadrature on each arc.
    for low in (h, s_b):
        integrated = (1 - beta) * mp.quad(lambda s: (s - h) / (s - p), [low, entry])
        if relative_error(capacity_increment(low), integrated) >= IDENTITY_TOLERANCE:
            raise AssertionError("Inconsistent quarantined-susceptible increment")
    return {
        "s0": s0, "i0": i0, "s1": entry,
        "fill_population_fraction": capacity_increment(h),
        "optimal_population_fraction": capacity_increment(s_b) + (1 - beta) * (s_b - s_end),
    }


def checked_table_cell(computed, source, context, display_places=None):
    """Compare both the underlying TeX number and the typeset decimal value."""
    source_value = Decimal(source)
    source_places = -source_value.as_tuple().exponent
    computed_value = Decimal(mp.nstr(computed, 80))
    rounded = format(computed_value, f".{source_places}f")
    if rounded != source:
        raise AssertionError(f"{context}: computed {rounded}, manuscript {source}")
    places = source_places if display_places is None else display_places
    printed = format(source_value, f".{places}f")
    if printed != format(computed_value, f".{places}f"):
        raise AssertionError(f"{context}: rounding mismatch at display precision")
    return {"computed": computed, "latex_value": source, "printed": printed}


def verify_comparison_table(latex_dir, examples):
    """Read the four manuscript rows, resolve their macros, and verify each cell."""
    manuscript = (latex_dir / "main.tex").read_text(encoding="utf-8")
    macro_source = (latex_dir / "generated/scaling_values.tex").read_text(encoding="utf-8")
    macros = dict(re.findall(r"\\newcommand\{(\\[A-Za-z]+)\}\{(\d+(?:\.\d+)?)\}", macro_source))
    precision = re.search(
        r"\\newcommand\{\\Dur\}\[1\]\{\\num\[round-mode=places,round-precision=(\d+)\]\{#1\}\}",
        manuscript,
    )
    if precision is None:
        raise ValueError("Cannot read the manuscript's duration display precision")
    duration_places = int(precision.group(1))
    table = manuscript.split(r"\label{tab:quarantined-susceptibles}", 1)[1].split(r"\end{tabular}", 1)[0]
    body = table.split(r"\midrule", 1)[1].split(r"\bottomrule", 1)[0].replace(r"\addlinespace", "")
    scenarios = {"E2": "mathematical_example", "西安文献参数情景": "literature_parameter_illustration"}
    policies = {
        "纯容量填充": ("J_fill", "T_fill", "fill_population_fraction"),
        "最优追踪": ("J_star", "T_star", "optimal_population_fraction"),
    }
    indexed_examples = {example["label"]: example for example in examples}
    missing = {(scenario, policy) for scenario in scenarios for policy in policies}
    rows = []
    scenario = ""
    for row in body.strip().split(r"\\"):
        if not row.strip():
            continue
        label, policy, cost, duration, fraction = [cell.strip() for cell in row.split("&")]
        scenario = label or scenario
        if (scenario, policy) not in missing:
            raise ValueError(f"Unknown or repeated Table 4 row: {scenario}, {policy}")
        missing.remove((scenario, policy))
        example = indexed_examples[scenarios[scenario]]
        quarantine = example["newly_quarantined_susceptibles"]
        comparison = example["comparison"]
        if quarantine["s1"] != comparison["s_1"]:
            raise AssertionError(f"Table 4: inconsistent capacity entries for {scenario}")
        duration_match = re.fullmatch(r"\\Dur\{(\\[A-Za-z]+)\}\s*(日)?", duration)
        fraction_match = re.fullmatch(r"\$(\d+(?:\.\d+)?)\\%\$", fraction)
        unit = "日" if scenario == "西安文献参数情景" else ""
        if not duration_match or (duration_match[2] or "") != unit or not fraction_match:
            raise ValueError(f"Unexpected duration unit or percentage in Table 4: {row}")
        j_key, t_key, fraction_key = policies[policy]
        context = f"Table 4 {scenario}, {policy}"
        rows.append({
            "scenario": scenario, "strategy": policy, "s0": quarantine["s0"],
            "i0": quarantine["i0"], "s1": comparison["s_1"], "duration_unit_in_table": unit,
            "cells": {
                "J": checked_table_cell(comparison[j_key], macros[cost], f"{context}, J"),
                "T_plus": checked_table_cell(
                    comparison[t_key], macros[duration_match[1]], f"{context}, T_plus", duration_places
                ),
                "delta_s_q_percent": checked_table_cell(
                    100 * quarantine[fraction_key], fraction_match[1], f"{context}, delta_s_q_percent"
                ),
            },
        })
    if missing:
        raise ValueError(f"Missing rows in Table 4: {sorted(missing)}")
    return rows


def asymptotic_checks():
    """Fixed common entry: (s0(K),i0(K))=(0.7,K), so s1°=0.7."""
    rows, groups = [], []
    for beta_text in ("0.155", "0.5", "0.8"):
        beta = number(beta_text)
        group = []
        for capacity_text in ("1e-3", "1e-5", "1e-7", "1e-9"):
            parameters = geometry(beta, 1 / beta, "0.3", capacity_text)
            comparison = common_tail_comparison(parameters, "0.7")
            capacity, h, p, ell = (
                parameters[key] for key in ("K", "h", "p", "ell")
            )
            logarithm = mp.log((number("0.7") - p) / ell)
            duration_leading = capacity / (beta**2 * h * logarithm)
            cost_leading = capacity**2 / (24 * beta**4 * h**3)
            time_leading = 1 / (beta * parameters["gamma"])
            exit_second = capacity / beta - (1 - beta) * capacity**2 / (
                beta**3 * h
            )
            errors = {
                "cost_leading_relative_error": relative_error(
                    comparison["Delta_J"], cost_leading
                ),
                "absolute_duration_leading_relative_error": relative_error(
                    comparison["Delta_T"], time_leading
                ),
                "relative_duration_leading_relative_error": relative_error(
                    comparison["relative_duration_reduction"], duration_leading
                ),
            }
            row = {
                "beta": beta, "K": capacity, "s_1_limit": number("0.7"),
                "s_B_minus_h": parameters["s_B"] - h,
                "switching_second_order_prediction": exit_second,
                "switching_remainder_divided_by_K3": (
                    parameters["s_B"] - h - exit_second
                ) / capacity**3,
                "Delta_J": comparison["Delta_J"],
                "Delta_J_leading_prediction": cost_leading,
                "Delta_T": comparison["Delta_T"],
                "Delta_T_limit": time_leading,
                "relative_duration_reduction": comparison["relative_duration_reduction"],
                "relative_duration_leading_prediction": duration_leading,
                "T_star_divided_by_T_fill": comparison["duration_ratio"],
                "errors": errors,
                "identity_residuals": {
                    **parameters["residuals"], **comparison["residuals"]
                },
            }
            rows.append(row)
            group.append(row)
        for metric in group[0]["errors"]:
            values = [row["errors"][metric] for row in group]
            if not all(later < earlier for earlier, later in zip(values, values[1:])):
                raise AssertionError((beta_text, metric, "error did not decrease"))
            if values[-1] >= FINEST_ASYMPTOTIC_TOLERANCE:
                raise AssertionError((beta_text, metric, "finest error too large"))
        groups.append({
            "beta": beta, "finest_K": group[-1]["K"],
            "finest_errors": group[-1]["errors"],
            "all_reported_leading_errors_decrease": True,
        })
    return rows, groups


def zero_control_peak(s, i, h):
    return i if s <= h else i + s - h - h * mp.log(s / h)


def physical_regime_check(label, h_text, capacity_text):
    parameters = geometry("0.5", "2", h_text, capacity_text)
    h, capacity, s_b = (
        parameters[key] for key in ("h", "K", "s_B")
    )
    all_safe = h + capacity >= 1
    plateau_possible = s_b + capacity < 1
    computed = (
        "all_safe" if all_safe else
        "unsafe_without_positive_plateau" if not plateau_possible else
        "positive_plateau_possible"
    )
    if computed != label:
        raise AssertionError((label, computed))
    # Finite samples illustrate the analytic classification; they are not a proof.
    sample_count, unsafe_count, peak_excess = 0, 0, -mp.inf
    for row in range(1, 41):
        i = capacity * row / 40
        for column in range(1, 41):
            s = (1 - i) * column / 40
            excess = zero_control_peak(s, i, h) - capacity
            sample_count += 1
            unsafe_count += int(excess > IDENTITY_TOLERANCE)
            peak_excess = max(peak_excess, excess)
    if all_safe and unsafe_count:
        raise AssertionError("Unsafe sample in the analytically all-safe regime")
    if not all_safe and not unsafe_count:
        raise AssertionError("No unsafe sample found in the selected unsafe regime")
    witness = None
    if not all_safe:
        s = (h + 1 - capacity) / 2
        if not (s + capacity <= 1 and zero_control_peak(s, capacity, h) > capacity):
            raise AssertionError("Unsafe-state witness failed")
        witness = {"s": s, "i": capacity, "zero_control_peak": zero_control_peak(s, capacity, h)}
    plateau_witness = None
    if plateau_possible:
        s = (s_b + 1 - capacity) / 2
        duration = capacity_time(parameters, s, s_b)
        if not (s > s_b and s + capacity <= 1 and duration > 0):
            raise AssertionError("Positive capacity-stage witness failed")
        plateau_witness = {"s": s, "i": capacity, "capacity_stage_duration": duration}
    return {
        "regime": computed, "parameters": parameters,
        "h_plus_K": h + capacity, "s_B_plus_K": s_b + capacity,
        "sample_count": sample_count, "unsafe_sample_count": unsafe_count,
        "max_sampled_peak_excess": peak_excess,
        "unsafe_state_witness": witness, "positive_plateau_witness": plateau_witness,
        "interpretation": "A finite formula check supporting, not replacing, the manuscript proof.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "analytic_verification.json",
    )
    args = parser.parse_args()
    specifications = [
        ("mathematical_example", "0.5", "2", "0.3", "0.15"),
        ("literature_parameter_illustration", "0.13675", "10.1317", "0.3004", "0.01"),
        ("small_probability_example", "0.155", "10", "0.3504", "0.0001"),
        ("high_probability_example", "0.8", "1.25", "0.3", "0.05"),
        ("intermediate_probability_example", "0.25", "4", "0.3", "0.01"),
    ]
    table_initial_states = {
        "mathematical_example": ("0.99", "0.01"),
        "literature_parameter_illustration": ("0.9999", "0.0001"),
    }
    examples = []
    for label, beta, c, gamma, capacity in specifications:
        parameters = geometry(beta, c, gamma, capacity)
        example = {"label": label, "parameters": parameters}
        if label in table_initial_states:
            quarantine = newly_quarantined_susceptibles(parameters, *table_initial_states[label])
            entry = quarantine["s1"]
            example["newly_quarantined_susceptibles"] = quarantine
            example["entry_source"] = "first natural capacity contact from the reported initial state"
        else:
            entry = (parameters["s_B"] + 1 - parameters["K"]) / 2
            example["entry_source"] = "midpoint used for a formula check"
        example["comparison"] = common_tail_comparison(parameters, entry)
        examples.append(example)
    table_rows = verify_comparison_table(Path(__file__).resolve().parents[1] / "latex", examples)
    asymptotics, asymptotic_summary = asymptotic_checks()
    regimes = [
        physical_regime_check("all_safe", "0.9", "0.2"),
        physical_regime_check("all_safe", "0.8", "0.2"),
        physical_regime_check("unsafe_without_positive_plateau", "0.7", "0.2"),
        physical_regime_check("positive_plateau_possible", "0.3", "0.15"),
    ]
    maxima = {}
    residual_blocks = []
    for example in examples:
        residual_blocks.extend([
            example["parameters"]["residuals"], example["comparison"]["residuals"]
        ])
    residual_blocks.extend(row["identity_residuals"] for row in asymptotics)
    residual_blocks.extend(row["parameters"]["residuals"] for row in regimes)
    for block in residual_blocks:
        for metric, value in block.items():
            maxima[metric] = max(maxima.get(metric, mp.mpf(0)), value)
    summary = {
        "all_checks_passed": True,
        "decimal_precision": mp.mp.dps,
        "geometry_cases": len(examples) + len(asymptotics) + len(regimes),
        "common_tail_comparisons": len(examples) + len(asymptotics),
        "asymptotic_parameter_families": len(asymptotic_summary),
        "asymptotic_capacity_values_per_family": 4,
        "physical_regime_cases": len(regimes),
        "table_4_rows_verified": len(table_rows),
        "table_4_numeric_cells_verified": sum(len(row["cells"]) for row in table_rows),
        "physical_states_sampled": sum(row["sample_count"] for row in regimes),
        "maximum_identity_residuals": maxima,
        "finest_asymptotic_checks": asymptotic_summary,
    }
    result = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Independent analytic formula evaluation; not an optimal-control numerical solve.",
        "methods": [
            "Positive endpoint found by bracketed bisection at 110 decimal digits.",
            "Endpoint invariant, safe-boundary equation and Theta matching evaluated separately.",
            "Capacity tail cost and duration integrated by mpmath quadrature.",
            "Total-cost differences checked by integrating the two tails starting at the same switching state.",
            "For Table 4, both policies start at the same natural capacity entry from the scenario's initial state. All four rows are checked against the manuscript at source and printed precision.",
            "Fixed-entry families check the absolute and relative small-capacity duration limits.",
            "Explicit physical witnesses and finite samples illustrate the three parameter regimes.",
        ],
        "identity_tolerance": IDENTITY_TOLERANCE,
        "finest_asymptotic_relative_error_tolerance": FINEST_ASYMPTOTIC_TOLERANCE,
        "summary": summary, "examples": examples, "table_4": table_rows,
        "asymptotics": asymptotics, "physical_regimes": regimes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(serialize(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(serialize(summary), ensure_ascii=False, indent=2))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
