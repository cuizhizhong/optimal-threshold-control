"""捕获并核对无回流模型返修的保护基线、改动范围及源文件；不调用数值求解器。"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPO = PROJECT.parent
LATEX = PROJECT / "latex"
BASE = "e40c8971692a97feba6faea38bef6bae7167b941"
PREFIX = PROJECT.relative_to(REPO).as_posix() + "/"
BASELINE = HERE / "preservation_baseline.json"
TITLE = "感染阈值约束下跟踪隔离的全域最优控制"
PROTECTED_ROOTS = ("data/numerical_scenarios/", "figures/", "matlab/")
ALLOWED_TRACKED = {PREFIX + name for name in (
    "latex/main.tex", "latex/main.bbl", "latex/main.pdf", "latex/theory_only.pdf", "README.md",
    "ai/claude_revision_plan/START_HERE_CODEX.md", "ai/claude_revision_plan/REVISION_PLAN.md",
    "ai/claude_revision_plan/SYMBOL_TABLE.md", "ai/claude_revision_plan/REVISION_PLAN_v4.md")}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalized(value):
    return value.replace(b"\r\n", b"\n")


def disk_path(path):
    # 已有评估记录的文件名可能使绝对路径超过 Windows 传统的 260 字符限制。
    return Path("\\\\?\\" + str(path.resolve())) if os.name == "nt" else path


def generated_blocks(source):
    pattern = r"% BEGIN AUTO-GENERATED (?P<name>[^\r\n]+).*?% END AUTO-GENERATED (?P=name)"
    return {match.group("name"): digest(normalized(match.group().encode("utf-8")))
            for match in re.finditer(pattern, source, re.S)}


def tracked_protected():
    entries = git("ls-tree", "-r", "-z", BASE, "--", PREFIX).decode("utf-8").split("\0")
    paths = {}
    for entry in entries:
        if not entry:
            continue
        metadata, path = entry.split("\t", 1)
        if any(path.startswith(PREFIX + root) for root in PROTECTED_ROOTS) or path.lower().endswith(".m"):
            paths[path] = metadata.split()[2]
    return dict(sorted(paths.items()))


def capture():
    if BASELINE.exists():
        raise SystemExit(f"已有保护基线，拒绝覆盖：{BASELINE}")
    assert git("rev-parse", "HEAD").decode().strip() == BASE, "捕获时 HEAD 必须为返修前的 e40c897"
    previous_path = PROJECT / "validation/model_a1_20261020/preservation_baseline.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    committed = tracked_protected()
    assert set(committed) == set(previous["protected_files"]), "本轮与旧 manifest 的保护文件集合不同"
    records = {}
    for path, blob in committed.items():
        old = previous["protected_files"][path]
        assert blob == old["git_blob"], f"e40c897 中保护文件相对旧基线改变：{path}"
        current = disk_path(REPO / path).read_bytes()
        assert digest(current) == old["working_sha256"], f"当前保护文件偏离旧 manifest：{path}"
        records[path] = {"working_sha256": digest(current), "git_sha256": old["git_sha256"],
                         "git_blob": blob, "bytes": len(current)}
    base_source = git("show", f"{BASE}:{PREFIX}latex/main.tex").decode("utf-8")
    current_source = (LATEX / "main.tex").read_text(encoding="utf-8")
    assert generated_blocks(current_source) == generated_blocks(base_source), "捕获时自动生成数值块已改变"
    report = {"base_commit": BASE, "captured_utc": datetime.now(timezone.utc).isoformat(),
              "protected_roots": list(PROTECTED_ROOTS), "protected_files": records,
              "verified_previous_manifest": previous_path.relative_to(REPO).as_posix(),
              "previous_manifest_sha256": digest(previous_path.read_bytes()),
              "generated_blocks": generated_blocks(base_source),
              "initial_tracked_changes": git("diff", "--name-only", BASE).decode("utf-8").splitlines(),
              "optimizer_calls": 0, "scientific_solves": 0}
    write_json(BASELINE, report)
    print(f"A1 no-return revision baseline captured: {len(records)} protected files; {len(report['generated_blocks'])} generated blocks")


def uncomment(source):
    return re.sub(r"(?<!\\)%[^\n]*", "", source)


def source_checks(source, count_model_label):
    source = uncomment(source)
    checks = []

    def check(name, passed, details=None):
        entry = {"name": name, "passed": bool(passed)}
        if details is not None:
            entry["details"] = details
        checks.append(entry)

    def equation(label):
        pos = source.find(rf"\label{{{label}}}")
        if pos < 0:
            return ""
        start = source.rfind(r"\begin{equation}", 0, pos)
        end = source.find(r"\end{equation}", pos)
        return source[start:end] if start >= 0 and end > pos else ""

    model_start = source.find(r"\label{sec:model}")
    model_end = source.find(r"\section{", model_start)
    model = source[model_start:model_end]
    check("model_section_found", model_start >= 0 and model_end > model_start)
    forbidden = {
        "lambda": r"\lambda",
        "V_lambda": r"V_\lambda",
        "tilde_s": r"\tilde s",
        "V_0": "V_0",
        "independent_reduction_proposition": r"\label{prop:five-compartment-reduction}",
        "five_compartment_value": r"\label{eq:five-compartment-value}",
        "five_compartment_equivalence": r"\label{eq:five-compartment-equivalence}",
    }
    for name, token in forbidden.items():
        check("model_no_" + name, token not in model)
    check("model_no_braced_tilde_s", not re.search(r"\\tilde\s*\{s\}", model))
    count_block = equation(count_model_label)
    check("count_model_label_exists", bool(count_block), count_model_label)
    count_cases = re.search(r"\\begin\{cases\}(.*?)\\end\{cases\}", count_block, re.S)
    count_rows = re.split(r"\\\\", count_cases.group(1)) if count_cases else []
    count_rows = [row for row in count_rows if row.strip()]
    check("count_model_has_five_equations", len(count_rows) == 5, len(count_rows))
    for state in ["S", "I", "S_q", "I_q", "R"]:
        subscript = state.split("_", 1)
        pattern = r"\\dot\s*(?:\{" + re.escape(subscript[0]) + r"\}|" + re.escape(subscript[0]) + ")"
        pattern += r"\s*_\s*\{?q\}?" if len(subscript) == 2 else r"(?!\s*_)"
        check("count_equation_" + state, any(re.search(pattern, row) for row in count_rows))
    normalized_block = equation("eq:normalized-model")
    normalized_cases = re.search(r"\\begin\{cases\}(.*?)\\end\{cases\}", normalized_block, re.S)
    normalized_rows = re.split(r"\\\\", normalized_cases.group(1)) if normalized_cases else []
    check("normalized_two_equations", len([row for row in normalized_rows if row.strip()]) == 2)
    for label in ["eq:five-compartment-conservation", "eq:capacity", "eq:linear-cost", "def:admissible"]:
        check("required_label_" + label, rf"\label{{{label}}}" in source)
    check("gamma_aggregation", re.search(r"\\gamma\s*=\s*\\delta_I\s*\+\s*\\gamma_I", model))
    check("title_main", r"\title{\bfseries " + TITLE in source)
    check("title_metadata", "pdftitle={" + TITLE + "}" in source)
    check("title_header", r"\fancyhead[L]{" + TITLE + "}" in source)
    for name, pattern in {
        "beta_1/beta_2": r"\\beta\s*_\s*(?:\{\s*[12]\s*\}|[12])",
        "q_max": r"q\s*_\s*\{?\s*(?:\\max|max|\\mathrm\{max\})\s*\}?",
        "dual_transmission_wording": "双传播",
    }.items():
        matches = [{"line": source.count("\n", 0, m.start()) + 1, "match": m.group()}
                   for m in re.finditer(pattern, source)]
        check("no_old_" + name, not matches, matches)
    definitions = list(re.finditer(r"P_0\s*\(\s*s\s*,\s*i\s*\)\s*:?=", source))
    check("P0_defined_exactly_once", len(definitions) == 1, len(definitions))
    if len(definitions) == 1:
        position = definitions[0].start()
        check("P0_defined_in_section_4", len(re.findall(r"\\section\s*\{", source[:position])) == 4)
        check("P0_defined_before_safe_set", source.find(r"\label{eq:safe-set}") > position)
        check("safe_set_uses_P0", "P_0" in equation("eq:safe-set"))
    labels = re.findall(r"\\label\s*\{([^{}]+)\}", source)
    duplicates = sorted(key for key, count in Counter(labels).items() if count > 1 and "#" not in key)
    check("no_duplicate_labels", not duplicates, duplicates)
    reference_keys = []
    for match in re.finditer(r"\\(?:eqref|ref|pageref|autoref|cref|Cref)\*?\s*\{([^{}]+)\}", source):
        reference_keys.extend(key.strip() for key in match.group(1).split(",") if "#" not in key)
    unresolved = sorted(set(reference_keys) - set(labels) - {"LastPage"})
    check("source_references_resolve", not unresolved, unresolved)
    citations = []
    for match in re.finditer(r"\\cite\w*\*?(?:\s*\[[^\]]*\])*\s*\{([^{}]+)\}", source):
        citations.extend(key.strip() for key in match.group(1).split(",") if "#" not in key)
    bib_source = (LATEX / "references.bib").read_text(encoding="utf-8")
    bib_keys = set(re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib_source))
    unresolved_citations = sorted(set(citations) - bib_keys)
    check("source_citations_resolve", not unresolved_citations, unresolved_citations)
    return checks


def audit(args):
    before = json.loads(BASELINE.read_text(encoding="utf-8"))
    changed = []
    groups = {root: 0 for root in PROTECTED_ROOTS}
    for path, record in before["protected_files"].items():
        full = disk_path(REPO / path)
        if not full.exists() or digest(full.read_bytes()) != record["working_sha256"]:
            changed.append(path)
        for root in groups:
            groups[root] += path.startswith(PREFIX + root)
    tracked_changes = git("diff", "--name-only", BASE).decode("utf-8").splitlines()
    allowed = ALLOWED_TRACKED | set(args.allow_tracked)
    validation_prefix = HERE.relative_to(REPO).as_posix() + "/"
    outside = [path for path in tracked_changes if path not in allowed and not path.startswith(validation_prefix)]
    source = (LATEX / "main.tex").read_text(encoding="utf-8")
    generated_unchanged = generated_blocks(source) == before["generated_blocks"]
    checks = source_checks(source, args.count_model_label)
    report = {"batch": "A1_no_return_revision", "base_commit": BASE,
              "protected_file_count": len(before["protected_files"]), "protected_group_counts": groups,
              "changed_protected_files": changed, "tracked_changes": tracked_changes,
              "outside_allowed_tracked_scope": outside, "extra_allowed_tracked": args.allow_tracked,
              "generated_blocks_unchanged": generated_unchanged,
              "source_checks": checks, "source_check_count": len(checks),
              "source_checks_passed": sum(item["passed"] for item in checks),
              "optimizer_calls": 0, "scientific_solves": 0}
    report["passed"] = not changed and not outside and generated_unchanged and all(item["passed"] for item in checks)
    write_json(HERE / "audit_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", action="store_true", help="捕获无回流模型返修的保护基线")
    parser.add_argument("--count-model-label", default="eq:five-compartment-model")
    parser.add_argument("--allow-tracked", action="append", default=[], help="显式追加的仓库相对允许路径")
    args = parser.parse_args()
    if args.capture:
        capture()
    else:
        audit(args)


if __name__ == "__main__":
    main()
