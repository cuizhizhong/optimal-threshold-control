"""实际执行 XeLaTeX/BibTeX，并保留每个命令和最终日志诊断。"""
from pathlib import Path
import json
import re
import subprocess

P = Path(__file__).resolve().parents[2]
V = P / "validation/numerical_scenarios"
LATEX = P / "latex"
ISSUES = re.compile(r"(?:^.*\bWarning:|^(?:Overfull|Underfull)|Missing character|Undefined control sequence|^!|LaTeX Error|File .+ not found|multiply defined)", re.I)


def build(name):
    records = []
    commands = [["xelatex", "-interaction=nonstopmode", "-halt-on-error", f"{name}.tex"],
                ["bibtex", name],
                ["xelatex", "-interaction=nonstopmode", "-halt-on-error", f"{name}.tex"],
                ["xelatex", "-interaction=nonstopmode", "-halt-on-error", f"{name}.tex"]]
    for n, command in enumerate(commands, 1):
        result = subprocess.run(command, cwd=LATEX, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = result.stdout.decode("utf-8", errors="replace")
        logfile = V / f"step1011_{name}_build_{n}.log"
        logfile.write_text(output, encoding="utf-8")
        records.append({"command": command, "exit_code": result.returncode, "log": logfile.name,
                        "issues": [line for line in output.splitlines() if ISSUES.search(line)]})
        if result.returncode:
            return {"success": False, "commands": records, "final_log_issues": [], "pages": None}
    final = (LATEX / f"{name}.log").read_text(encoding="utf-8", errors="replace")
    (V / f"step1011_{name}_final.log").write_text(final, encoding="utf-8")
    issues = [line for line in final.splitlines() if ISSUES.search(line)]
    info = subprocess.check_output(["pdfinfo", str(LATEX / f"{name}.pdf")], text=True, encoding="utf-8", errors="replace")
    return {"success": True, "commands": records, "final_log_issues": issues,
            "pages": int(re.search(r"Pages:\s+(\d+)", info).group(1)), "pdfinfo": info}


def main():
    wrapper = LATEX / "theory_only.tex"
    content = "\\def\\TheoryOnly{1}\n\\input{main.tex}\n"
    if wrapper.exists():
        assert wrapper.read_text(encoding="utf-8").strip() == content.strip(), "Unexpected TheoryOnly wrapper"
    else:
        wrapper.write_text(content, encoding="utf-8")
    report = {"main": build("main"), "theory_only": build("theory_only")}
    (V / "step1011_build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({name: {k: r[k] for k in ("success", "pages", "final_log_issues")} for name, r in report.items()}, ensure_ascii=False))
    assert all(r["success"] for r in report.values()), "Actual LaTeX build failed; see saved logs"


if __name__ == "__main__":
    main()
