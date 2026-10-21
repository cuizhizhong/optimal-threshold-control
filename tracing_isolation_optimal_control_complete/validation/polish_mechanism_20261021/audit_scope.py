"""核对本轮源文范围、保护文件、解析记录与最终双编译产物。"""

import hashlib
import json
from pathlib import Path
import re
import subprocess


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
ROOT = PROJECT.parent
BASE = "6b48cc6b0bb4b222415853bf575c8f7ccc48e561"


def raw(path):
    # 部分旧记录路径超过传统 Windows MAX_PATH。
    return Path("\\\\?\\" + str(path.resolve())).read_bytes()


def digest(path):
    return hashlib.sha256(raw(path)).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def sections(text):
    parts = re.split(r"(?m)(?=^\\section\{)", text)
    return dict(enumerate(parts))


def main():
    relative = "tracing_isolation_optimal_control_complete/latex/main.tex"
    before = subprocess.check_output(["git", "show", f"{BASE}:{relative}"], cwd=ROOT).decode("utf-8")
    after = (PROJECT / "latex/main.tex").read_text(encoding="utf-8")
    old, new = sections(before), sections(after)
    assert len(old) == len(new)
    unchanged = [number for number in old if number not in (1, 3, 15, 20)]
    assert all(old[number] == new[number] for number in unchanged)
    expected_intro = old[1].replace(
        r"定理\ref{thm:main-overview}给出全域最优反馈及其阶段结构；",
        r"定理\ref{thm:main-overview}保证全域最优性与唯一性，命题\ref{prop:main-structure}给出阶段结构；"
    ).replace(
        r"结合推论\ref{cor:optimal-synthesis}，当最优轨道含有正长度容量阶段时，",
        r"命题\ref{prop:main-structure}表明，当最优轨道含有正长度容量阶段时，")
    assert new[1] == expected_intro
    blocks = []
    for title in ("NUMERICAL REFERENCE VALUES", "NUMERICAL RESULTS"):
        pattern = f"% BEGIN AUTO-GENERATED {title}.*?% END AUTO-GENERATED {title}"
        one, two = re.search(pattern, before, re.S)[0], re.search(pattern, after, re.S)[0]
        assert one == two
        blocks.append({"name": title, "normalized_text_sha256": hashlib.sha256(one.encode()).hexdigest(),
                       "unchanged": True})
    for label in ("eq:cost-in-Phi", "eq:waiting-marginal-cost"):
        pattern = r"\\begin\{equation\}(?:(?!\\end\{equation\}).)*?\\label\{" + re.escape(label) + r"\}.*?\\end\{equation\}"
        assert re.search(pattern, before, re.S)[0] == re.search(pattern, after, re.S)[0]
    labels = re.findall(r"\\label\{([^}]+)\}", after)
    references = re.findall(r"\\(?:eqref|ref|autoref|cref|Cref)\{([^}]+)\}", after)
    assert len(labels) == len(set(labels))
    missing = sorted({key for key in references if not key.startswith("#") and key not in labels})
    assert not missing, missing

    authorized = {f"tracing_isolation_optimal_control_complete/figures/numerical_scenarios/FigN1_optimal_partition.{ext}"
                  for ext in ("pdf", "png")}
    baseline = load("baseline_sha256.json")
    protected = {key: value for key, value in baseline["files"].items() if key not in authorized}
    changed = [key for key, value in protected.items() if digest(ROOT / key) != value]
    assert not changed, changed
    for key in authorized:
        blob = subprocess.check_output(["git", "show", f"{BASE}:{key}"], cwd=ROOT)
        assert hashlib.sha256(blob).hexdigest() == baseline["files"][key]

    analytical = load("analytic_checks.json")
    previous = json.loads((PROJECT / "validation/figure1_layout_20261021/analytic_checks.json").read_text(encoding="utf-8"))
    for key in ("geometry", "checkpoint_errors", "trajectories", "E2_analytic_cost", "protected_outputs_unchanged"):
        assert analytical[key] == previous[key], key
    for group in ("sources_sha256", "outputs_sha256", "protected_outputs_unchanged"):
        for key, value in analytical[group].items():
            assert digest(PROJECT / key) == value, key
    assert analytical["checkpoint_max_absolute_error"] < 1e-12
    assert analytical["theta_max_absolute_residual"] < 1e-10
    assert analytical["s_e_safe_Gamma_intersection"]["maximum_residual"] < 1e-12
    collisions = analytical["label_collision_checks"]
    assert not collisions["label_curve_intersections"] and not collisions["label_pair_intersections"]
    mechanism = load("mechanism_checks.json")
    assert mechanism["passed"] and mechanism["symbolic"]["passed_count"] == 9
    assert mechanism["script_sha256"] == digest(HERE / "check_mechanism.py")
    for key, value in mechanism["inputs_sha256"].items():
        assert digest(PROJECT / key) == value
    assert all(value == 0 for value in mechanism["execution_counts"].values())
    log_bytes = (HERE / "notation_check.log").read_bytes()
    notation = log_bytes.decode("utf-16" if log_bytes.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
    assert "Original symbolic checks: 28/28" in notation and "SOME FAILED" not in notation

    build = load("attempt1/build_report.json")
    assert build["success"] and len(build["documents"]) == 2
    for name, value in build["source_sha256"].items():
        assert digest(PROJECT / "latex" / name) == value
    for name, value in build["figure_sha256"].items():
        assert digest(PROJECT / name) == value
    for document in build["documents"]:
        assert document["success"] and not document["final_log_issues"]
        assert len(document["commands"]) == 4 and all(c["exit_code"] == 0 for c in document["commands"])
        assert digest(PROJECT / "latex" / (document["name"] + ".pdf")) == document["pdf_sha256"]
    aux = PROJECT / "tmp/polish_mechanism_20261021/attempt1"
    for document in ("main", "theory_only"):
        text = (aux / (document + ".aux")).read_text(encoding="utf-8")
        assert r"\newlabel{thm:main-overview}{{3.1}" in text
        assert r"\newlabel{prop:main-structure}{{3.2}" in text
    theory = (aux / "theory_only.aux").read_text(encoding="utf-8")
    assert r"\newlabel{sec:limitations}" not in theory
    rendered = load("render_manifest.json")
    assert len(rendered["pages"]) == 12
    for page in rendered["pages"]:
        assert page["exit_code"] == 0 and page["dpi"] == 150
        assert digest(PROJECT / page["png"]) == page["png_sha256"]
        assert digest(PROJECT / "latex" / (page["document"] + ".pdf")) == page["pdf_sha256"]
    report = {"base_commit": BASE, "success": True, "unchanged_section_indices": unchanged,
              "introduction_only_authorized_reference_updates": True,
              "generated_blocks": blocks, "preserved_equations_unchanged": True,
              "undefined_direct_references": missing, "old_protected_files_unchanged": len(protected),
              "changed_protected_files": changed, "geometry_trajectories_and_costs_unchanged": True,
              "notation_checks": "28/28", "mechanism_symbolic_checks": "9/9",
              "actual_tex_bibtex_processes": 8, "final_pages": [d["pages"] for d in build["documents"]],
              "final_log_issues": [], "rendered_pages_150dpi": len(rendered["pages"]),
              "optimizer_calls": 0, "new_ocp_solves": 0, "matlab_calls": 0}
    (HERE / "audit_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
