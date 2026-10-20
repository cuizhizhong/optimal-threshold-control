"""S2 追加重跑前后核对旧 raw、solver 和 assessment 字节；不调用优化器。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
REPO = PROJECT.parent
DATA = PROJECT / "data/numerical_scenarios"
TAG = "pre-code-rename"


def read(path):
    name = str(path.resolve())
    return Path("\\\\?\\" + name if os.name == "nt" else name).read_bytes()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["capture", "check"])
    parser.add_argument("--step", default="S2.2")
    args = parser.parse_args()
    baseline = HERE / "record_baseline.json"
    if args.mode == "capture":
        assert not baseline.exists(), "保护基准已存在，禁止覆盖。"
        paths = [f"{PROJECT.name}/data/numerical_scenarios/{part}" for part in
                 ("runs", "revision_checks/assessments")]
        names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "-z", TAG, "--", *paths],
                                        cwd=REPO).decode().rstrip("\0").split("\0")
        protected = {name: hashlib.sha256(read(REPO / name)).hexdigest() for name in names}
        index = json.loads(read(DATA / "run_index.json"))
        assert len(index["entries"]) == 35
        payload = {"tag": TAG, "tag_commit": subprocess.check_output(["git", "rev-parse", TAG],
                   cwd=REPO, text=True).strip(), "protected": protected, "old_index": index}
        baseline.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (HERE / "baseline_main.tex").write_bytes(read(PROJECT / "latex/main.tex"))
    before = json.loads(baseline.read_text(encoding="utf-8"))
    for name, digest in before["protected"].items():
        assert hashlib.sha256(read(REPO / name)).hexdigest() == digest, f"旧记录被改写：{name}"
    current = json.loads(read(DATA / "run_index.json"))
    assert current["entries"][:35] == before["old_index"]["entries"], "旧索引条目被改写或移除。"
    report = {"step": args.step, "passed": True, "old_protected_file_count": len(before["protected"]),
              "old_index_entries_unchanged": True, "current_index_entries": len(current["entries"]),
              "raw_mat_count": len(list((DATA / "runs").glob("*.mat"))),
              "assessment_mat_count": len(list((DATA / "revision_checks/assessments").glob("*.mat")))}
    output = HERE / args.step
    output.mkdir(exist_ok=True)
    (output / "preservation_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                                     encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
