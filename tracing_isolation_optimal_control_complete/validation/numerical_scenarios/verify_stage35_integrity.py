"""第3--5步授权改动与历史结果隔离检查；只写独立报告。"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    baseline = json.loads((HERE / "BASELINE.json").read_text(encoding="utf-8"))
    allowed = {
        "tracing_isolation_optimal_control_complete/latex/main.tex",
        "tracing_isolation_optimal_control_complete/latex/main.pdf",
        "tracing_isolation_optimal_control_complete/latex/main.bbl",
    }
    checked = {}
    for name, expected in baseline["protected_sha256"].items():
        if name in allowed:
            continue
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        assert actual == expected, f"历史文件被改动: {name}"
        checked[name] = actual
    source = ROOT / "tracing_isolation_optimal_control_complete/latex/main.tex"
    data = source.read_bytes()
    text = data.decode("utf-8")
    labels = re.findall(r"\\label\{([^}]+)\}", text)
    assert len(labels) == len(set(labels))
    assert set(labels) - set(baseline["labels"]) == {"lem:ac-composition"}
    assert set(baseline["labels"]) <= set(labels)
    refs = re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", text)
    assert not {r for r in refs if not r.startswith("#")} - set(labels)
    protection = json.loads((HERE / "step5_theory_protection.json").read_text(encoding="utf-8"))
    assert protection["after_sha256"] == hashlib.sha256(data).hexdigest()
    assert all(b["unchanged"] for b in protection["protected_blocks"])
    committed = subprocess.check_output(["git", "show", "fa9dc05229bfdcde079624fc4fe5118b97e288cf:tracing_isolation_optimal_control_complete/latex/main.tex"], cwd=ROOT)
    for block in ("NUMERICAL REFERENCE VALUES", "NUMERICAL RESULTS"):
        begin = f"% BEGIN AUTO-GENERATED {block}".encode()
        end = f"% END AUTO-GENERATED {block}".encode()
        assert data.count(begin) == data.count(end) == 1
        actual = data[data.index(begin):data.index(end) + len(end)].replace(b"\r\n", b"\n")
        expected = committed[committed.index(begin):committed.index(end) + len(end)].replace(b"\r\n", b"\n")
        assert actual == expected, f"数值生成块被改动: {block}"
    index = json.loads((ROOT / "tracing_isolation_optimal_control_complete/data/numerical_scenarios/run_index.json").read_text(encoding="utf-8"))
    assert not index["entries"], "本批不得启动科学优化实验"
    report = {
        "passed": True, "scope": "steps_3_to_5",
        "historical_files_unchanged": len(checked), "historical_file_sha256": checked,
        "label_count": len(labels), "added_labels": ["lem:ac-composition"],
        "protected_theory_blocks_unchanged": len(protection["protected_blocks"]),
        "numerical_generated_blocks_unchanged": True, "actual_optimizer_calls": 0,
        "scientific_run_index_entries": 0, "default_matrix_completed": "0/35",
    }
    (HERE / "step35_integrity_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"STAGE35_INTEGRITY_OK historical_files={len(checked)} labels={len(labels)} actual_optimizer=0")


if __name__ == "__main__":
    main()
