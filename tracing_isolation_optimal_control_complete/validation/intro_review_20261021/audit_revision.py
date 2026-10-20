"""B 作者审阅修订：核对范围、既有记录、模型系数和引用，不调用优化器。"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPO = PROJECT.parent
PREFIX = PROJECT.name + "/"
BASE = "80074ec37c0827e38552f3255f46a1a73a223cc4"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return Path("\\\\?\\" + str(path.resolve())).read_bytes() if os.name == "nt" else path.read_bytes()


old = git("show", f"{BASE}:{PREFIX}latex/main.tex").decode()
new = (PROJECT / "latex/main.tex").read_text(encoding="utf-8")
checks = []


def check(name, passed, details=None):
    checks.append({"name": name, "passed": bool(passed), "details": details})


mark = r"\section{模型与控制问题}"
cost = ("记自然传播系数 $b_0=\\beta c$、非隔离感染生成项中的有效传播系数 $b=\\beta c(1-q)$，\n"
        "则 $\\beta cq=b_0-b=[b_0-b]_+$ 是该系数相对自然水平的削减量，与 \\citet{MicloSpiroWeibull2022} 的线性代价同形。\n")
check("only_cost_explanation_added_after_intro", new.split(mark, 1)[1].replace(cost, "") == old.split(mark, 1)[1])
check("preamble_unchanged", old.split(r"\begin{abstract}", 1)[0] == new.split(r"\begin{abstract}", 1)[0])
check("cost_identity_present_once", new.count(cost) == 1)
check("bibliography_unchanged", (PROJECT / "latex/references.bib").read_text(encoding="utf-8") ==
      git("show", f"{BASE}:{PREFIX}latex/references.bib").decode())
intro = new.split(r"\label{sec:introduction}", 1)[1].split(mark, 1)[0]
abstract = new.split(r"\begin{abstract}", 1)[1].split(r"\end{abstract}", 1)[0]
check("AFG_uniqueness_acknowledged", "定理5.6与注5.7(2)" in intro and "时间上几乎处处唯一" in intro)
check("Angulo_early_start_acknowledged", r"\citep[图3b]{Angulo2021}" in intro)
check("own_early_start_explains_cost_mechanism", r"\dot i=-\gamma i<0" in intro and "由成本最小化决定" in intro)
check("whole_boundary_interval_stated", r"[q_B(s),1]" in intro and "逐点极小条件不能单独" in intro)
check("plain_abstract_capacity_conclusion", "并非最低成本的选择" in abstract and r"s_B>h" in abstract)
check("first_paragraph_has_source", r"\citep" in intro.strip().split("\n\n", 1)[0])
check("no_new_return_or_effect_size", not re.search(r"\\lambda|V_\\lambda|3\.10|两个端点", abstract + intro))
labels = set(re.findall(r"\\label\{([^{}]+)\}", new))
refs = set(re.findall(r"\\(?:eqref|ref|pageref)\{([^{}]+)\}", new))
check("references_resolve", not {x for x in refs - labels - {"LastPage"} if "#" not in x})
bibkeys = set(re.findall(r"@\w+\s*\{\s*([^,]+),", (PROJECT / "latex/references.bib").read_text(encoding="utf-8")))
cites = set()
for match in re.finditer(r"\\cite\w*\*?(?:\[[^\]]*\])*\{([^{}]+)\}", new):
    cites.update(k.strip() for k in match.group(1).split(","))
check("citations_resolve", cites <= bibkeys)
prior = json.loads((PROJECT / "validation/model_no_return_revision_20261020/preservation_baseline.json").read_text(encoding="utf-8"))
bad = [p for p, v in prior["protected_files"].items() if sha(read(REPO / p)) != v["working_sha256"]]
check("535_protected_records_code_figures_unchanged", not bad, {"count": len(prior["protected_files"]), "changed": bad})
report = {"batch": "B_author_review", "base_commit": BASE, "checks": checks,
          "passed": sum(c["passed"] for c in checks), "total": len(checks),
          "success": all(c["passed"] for c in checks), "optimizer_calls": 0, "ocp_solves": 0}
(HERE / "audit_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"B author review audit: {report['passed']}/{report['total']}")
assert report["success"], [c for c in checks if not c["passed"]]
