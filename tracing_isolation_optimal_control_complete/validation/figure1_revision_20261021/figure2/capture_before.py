"""保存本轮图2重导出前的证据；不修改旧数据或历史验证记录。"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
REPO = PROJECT.parent
BASE = "54470c531e3214bdf379b073f69593ec47fecb6a"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    before = HERE / "before"
    before.mkdir(parents=True, exist_ok=False)
    selected = [
        "latex/main.tex",
        "data/numerical_scenarios/figure_provenance.json",
        "data/numerical_scenarios/export_provenance.json",
    ]
    for name in ["FigN1_regions", "FigN2_waiting", "FigN3_boundary_tracking"]:
        selected.extend(f"figures/numerical_scenarios/{name}.{suffix}" for suffix in ("pdf", "png"))
    records = []
    for rel in selected:
        source = PROJECT / rel
        dest = before / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        records.append({"path": rel, "sha256": sha(source), "backup": dest.relative_to(HERE).as_posix()})
    data = [
        {"path": path.relative_to(PROJECT).as_posix(), "sha256": sha(path)}
        for path in sorted((PROJECT / "data/numerical_scenarios").rglob("*")) if path.is_file()
    ]
    code_rel = "tracing_isolation_optimal_control_complete/matlab/numerical_scenarios/make_numerical_figures.m"
    original = subprocess.check_output(["git", "show", f"{BASE}:{code_rel}"], cwd=REPO)
    (before / "make_numerical_figures.m").write_bytes(original)
    original_driver = PROJECT / "validation/numerical_scenarios/rerun_20261020/run_s27_regression.m"
    shutil.copy2(original_driver, HERE / "run_s27_regression.m")
    report = {"base_commit": BASE, "files": records, "data_files": data,
              "base_figure_code_sha256": hashlib.sha256(original).hexdigest(),
              "driver_source": original_driver.relative_to(PROJECT).as_posix(),
              "driver_sha256": sha(original_driver),
              "driver_is_byte_identical_copy": sha(original_driver) == sha(HERE / "run_s27_regression.m")}
    (HERE / "before_hashes.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"BACKUP_OK figures=6 data_files={len(data)} driver_byte_identical=True")

if __name__ == "__main__":
    main()
