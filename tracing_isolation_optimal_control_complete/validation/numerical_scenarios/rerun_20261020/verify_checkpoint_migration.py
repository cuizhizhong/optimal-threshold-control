#!/usr/bin/env python3
"""S2.3：逆映射字段后逐项核对解析检查点；不运行生成器或优化器。"""
from __future__ import annotations

import argparse
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
RELATIVE_TOLERANCE = Decimal("1e-12")


def git_text(repository, *arguments):
    return subprocess.check_output(
        ["git", "-C", str(repository), *arguments], text=True, encoding="utf-8"
    )


def input_digest(text):
    inputs = json.loads(text)
    canonical = dict(inputs, cases=sorted(inputs["cases"], key=lambda row: row["case_id"]))
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def inverse_fields(checkpoint):
    result = copy.deepcopy(checkpoint)
    for section, mapping in (
        ("parameters", {"beta": "p"}),
        ("geometry", {"p": "r", "s_A": "s_K", "s_e": "e"}),
    ):
        for new, old in mapping.items():
            if new not in result[section] or old in result[section]:
                raise ValueError(f"Expected only migrated field {section}.{new}")
            result[section][old] = result[section].pop(new)
    return result


def compare_checkpoints(baseline, current):
    """零值严格相等；其他数值以旧值为分母检查相对差。"""
    report = dict(numeric_fields=0, zero_fields=0, largest_relative_difference="0",
                  largest_relative_difference_path=None, skipped_metadata=[])
    largest = Decimal(0)

    def compare(old, new, path):
        nonlocal largest
        if path == "fixture.generator.input_sha256":
            # 调用者已分别用原始输入重算并核实这两个来源哈希。
            report["skipped_metadata"].append(dict(path=path, old=old, new=new))
        elif isinstance(old, dict):
            if not isinstance(new, dict) or old.keys() != new.keys():
                raise ValueError(f"Fields differ at {path}")
            for key in old:
                compare(old[key], new[key], f"{path}.{key}")
        elif isinstance(old, list):
            if not isinstance(new, list) or len(old) != len(new):
                raise ValueError(f"Array differs at {path}")
            if path == "fixture.cases":
                old_ids = [row["case_id"] for row in old]
                new_ids = [row["case_id"] for row in new]
                if len(set(old_ids)) != len(old_ids) or len(set(new_ids)) != len(new_ids):
                    raise ValueError("Duplicated case_id")
                compare({row["case_id"]: row for row in old},
                        {row["case_id"]: row for row in new}, path)
            else:
                for index, (left, right) in enumerate(zip(old, new)):
                    compare(left, right, f"{path}[{index}]")
        elif isinstance(old, bool) or old is None or isinstance(old, str):
            if type(old) is not type(new) or old != new:
                raise ValueError(f"Metadata differs at {path}: {old!r} versus {new!r}")
        elif isinstance(old, (int, Decimal)):
            if isinstance(new, bool) or not isinstance(new, (int, Decimal)):
                raise ValueError(f"Numeric type differs at {path}")
            left, right = Decimal(old), Decimal(new)
            if not left.is_finite() or not right.is_finite():
                raise ValueError(f"Nonfinite value at {path}")
            report["numeric_fields"] += 1
            if left == 0 or right == 0:
                report["zero_fields"] += 1
                if left != right:
                    raise ValueError(f"Zero value differs at {path}: {left} versus {right}")
            else:
                relative = abs(right - left) / abs(left)
                if relative > RELATIVE_TOLERANCE:
                    raise ValueError(f"Relative difference {relative} exceeds tolerance at {path}")
                if relative > largest:
                    largest = relative
                    report["largest_relative_difference_path"] = path
        else:
            raise TypeError(f"Unsupported value at {path}: {type(old).__name__}")

    compare(baseline, inverse_fields(current), "fixture")
    report["largest_relative_difference"] = str(largest)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-ref", default="pre-code-rename")
    parser.add_argument("--fixture", type=Path, default=ROOT / "analytic_checkpoints.json")
    parser.add_argument("--inputs", type=Path, default=ROOT / "scenario_inputs.json")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    repository = Path(git_text(ROOT, "rev-parse", "--show-toplevel").strip())
    fixture_path = (ROOT / "analytic_checkpoints.json").relative_to(repository).as_posix()
    input_path = (ROOT / "scenario_inputs.json").relative_to(repository).as_posix()
    baseline_text = git_text(repository, "show", f"{args.baseline_ref}:{fixture_path}")
    baseline_inputs = git_text(repository, "show", f"{args.baseline_ref}:{input_path}")
    current_text = args.fixture.read_text(encoding="utf-8-sig")
    current_inputs = args.inputs.read_text(encoding="utf-8-sig")
    baseline = json.loads(baseline_text, parse_float=Decimal)
    current = json.loads(current_text, parse_float=Decimal)
    for label, checkpoint, inputs in (
        ("baseline", baseline, baseline_inputs), ("current", current, current_inputs)
    ):
        if checkpoint["generator"]["input_sha256"] != input_digest(inputs):
            raise ValueError(f"{label} input_sha256 is inconsistent with its source inputs")
    report = compare_checkpoints(baseline, current)
    report.update(status="pass", relative_tolerance=str(RELATIVE_TOLERANCE),
                  baseline_ref=args.baseline_ref,
                  baseline_commit=git_text(repository, "rev-parse", args.baseline_ref).strip(),
                  current_fixture=str(args.fixture.resolve()),
                  optimizer_executions=0)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
