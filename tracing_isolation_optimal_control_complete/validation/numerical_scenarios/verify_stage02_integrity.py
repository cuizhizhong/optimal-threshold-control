"""核对本批受保护的历史文件、正文标签及生成块；不调用求解器。"""
import argparse
import hashlib
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--root", type=Path, help="待核对的独立导出目录；默认当前项目根目录")
    parser.add_argument("--normalized-text", action="store_true", help="跨检出只对文本统一 CRLF/LF 后比较；二进制仍比较原字节")
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    root = args.root.resolve() if args.root else here.parents[2]
    baseline = json.loads((here / "BASELINE.json").read_text(encoding="utf-8"))
    changed = []
    expected_hashes = baseline["protected_normalized_sha256"] if args.normalized_text else baseline["protected_sha256"]
    for relative, expected in expected_hashes.items():
        target = root / relative
        if not target.is_file():
            changed.append(relative)
            continue
        raw = target.read_bytes()
        if args.normalized_text and target.suffix in baseline["normalized_text_suffixes"]:
            raw = raw.replace(b"\r\n", b"\n")
        if hashlib.sha256(raw).hexdigest() != expected:
            changed.append(relative)
    tex = (root / "tracing_isolation_optimal_control_complete/latex/main.tex").read_text(encoding="utf-8")
    labels = re.findall(r"\\label\{([^}]+)\}", tex)
    markers = re.findall(r"^% (?:BEGIN|END) AUTO-GENERATED NUMERICAL.*$", tex, re.M)
    report = {
        "status": "tested",
        "comparison": "normalized_text" if args.normalized_text else "original_bytes",
        "protected_files": len(baseline["protected_sha256"]),
        "changed_protected_files": changed,
        "labels": len(labels),
        "labels_unchanged": labels == baseline["labels"],
        "auto_generated_markers_unchanged": markers == baseline["auto_generated_markers"],
        "optimization_calls": 0,
    }
    report["passed"] = not changed and report["labels_unchanged"] and report["auto_generated_markers_unchanged"]
    if args.write_report:
        (here / "integrity_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
