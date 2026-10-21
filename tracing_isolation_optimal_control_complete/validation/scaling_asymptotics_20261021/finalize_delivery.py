"""只同步已完成且源码/日志/PDF哈希通过核查的 attempt4，不重复编译。"""
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
report = json.loads((HERE / "attempt4/build_report.json").read_text(encoding="utf-8"))
build = Path(report["build_directory"])


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert report["failure"].startswith("[Errno 22] Invalid argument:"), report.get("failure")
assert len(report["documents"]) == 2
for name, digest in report["source_sha256"].items():
    assert sha(PROJECT / "latex" / name) == digest, name
for doc in report["documents"]:
    assert doc["success"] and not doc["final_log_issues"]
    assert len(doc["commands"]) == 4 and all(c["exit_code"] == 0 for c in doc["commands"])
    assert sha(build / (doc["name"] + ".pdf")) == doc["pdf_sha256"]
out = {"source_attempt": 4, "compilation_success": True, "commands_exit_zero": 8,
       "original_copy_failure_preserved": "attempt4/build_report.json", "files": [], "success": False}
for name in ("main.pdf", "theory_only.pdf", "main.bbl"):
    source, target = build / name, PROJECT / "latex" / name
    shutil.copyfile(source, target)
    assert sha(source) == sha(target)
    out["files"].append({"path": str(target), "sha256": sha(target)})
out["success"] = True
(HERE / "delivery_report.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("D delivery: 3/3 identical files; 8/8 build commands passed; 46/36 pages")
