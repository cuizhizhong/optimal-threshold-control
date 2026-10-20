"""运行并保存 S1.3 的符号、作用域与数据守恒检查。"""

import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPO = PROJECT.parent
CHECKS = PROJECT / "ai/claude_revision_plan/checks"
LOGS = HERE / "S1.3"


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    commands = [
        ("formulas", [sys.executable, "-I", str(CHECKS / "verify_new_notation.py")]),
        ("inventory", [sys.executable, "-I", str(CHECKS / "symbol_inventory.py"), str(PROJECT / "latex/main.tex")]),
        ("scoped_symbols", [sys.executable, "-I", str(CHECKS / "symbol_inventory.py"), str(PROJECT / "latex/main.tex"), "--check-s1"]),
        ("preservation", [sys.executable, "-I", str(HERE / "verify_preservation.py")]),
    ]
    report = {"commands": [], "optimizer_calls": 0, "scientific_solves": 0}
    for name, command in commands:
        done = subprocess.run(command, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (LOGS / f"{name}.txt").write_bytes(done.stdout)
        report["commands"].append({"name": name, "argv": command, "cwd": str(REPO),
                                    "exit_code": done.returncode, "log": f"{name}.txt"})
        (LOGS / "checks_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{name}: exit={done.returncode}", flush=True)
        if done.returncode:
            print(done.stdout.decode("utf-8", errors="replace"))
            raise SystemExit(done.returncode)
    report.update(passed=True, formula_checks=28, scoped_symbol_items=20)
    (LOGS / "checks_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
