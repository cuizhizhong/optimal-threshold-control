"""核对 S1 未改变保存数据、生成数值及导出器运算。"""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPO = PROJECT.parent
BASE = "420bcc7"


def base_file(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path.relative_to(REPO).as_posix()}"], cwd=REPO)


def normalize_lines(value):
    return value.replace(b"\r\n", b"\n")


def main():
    before = json.loads((HERE / "data_before.json").read_text(encoding="utf-8"))
    data = PROJECT / "data/numerical_scenarios"
    current = {p.relative_to(data).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in data.rglob("*") if p.is_file()}
    changed = sorted(name for name, digest in before["files"].items() if current.get(name) != digest)
    added = sorted(set(current) - set(before["files"]))
    assert set(changed) <= {"export_provenance.json"}, changed
    assert not added, added
    tex = PROJECT / "latex/main.tex"
    old = normalize_lines(base_file(tex)).decode("utf-8")
    new = tex.read_text(encoding="utf-8")
    script = PROJECT / "ai/claude_revision_plan/checks/migrate_s1_notation.py"
    spec = importlib.util.spec_from_file_location("s1_migration", script)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    migrated, counts = migration.migrate(old)
    all_generated = r"% BEGIN AUTO-GENERATED.*?% END AUTO-GENERATED[^\n]*"
    assert re.sub(all_generated, "<GENERATED>", migrated, flags=re.S) == re.sub(
        all_generated, "<GENERATED>", new, flags=re.S), "主文发生指定迁移之外的改动"
    generated = {}
    for kind in ["NUMERICAL REFERENCE VALUES", "NUMERICAL RESULTS"]:
        pattern = rf"% BEGIN AUTO-GENERATED {kind}.*?% END AUTO-GENERATED {kind}"
        original = re.search(pattern, old, re.S).group()
        latest = re.search(pattern, new, re.S).group()
        restored = latest.replace("$n=", "$N=").replace(r"\varepsilon_K", r"\delta")
        assert original == restored, f"生成块发生符号之外的改动：{kind}"
        generated[kind] = True
    exporter = PROJECT / "matlab/numerical_scenarios/export_numerical_latex.m"
    original = normalize_lines(base_file(exporter))
    expected = original.replace(b"$N=", b"$n=").replace(b"\\\\delta", b"\\\\varepsilon_K")
    assert normalize_lines(exporter.read_bytes()) == expected, "导出器发生显示字符串之外的改动"
    report = {"base_commit": BASE, "passed": True, "existing_data_files": len(before["files"]),
              "unchanged_data_files": len(before["files"]) - len(changed),
              "changed_data_files": changed, "added_data_files": added,
              "generated_blocks_identical_after_inverse_notation": generated,
              "handwritten_source_matches_scoped_migration": True,
              "migration_counts": counts,
              "exporter_only_display_strings_changed": True,
              "optimizer_calls": 0, "scientific_solves": 0}
    (HERE / "preservation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
