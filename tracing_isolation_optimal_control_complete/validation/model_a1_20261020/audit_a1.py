"""捕获并核对 A1 保护基线、改动范围及模型源文件；不调用数值求解器。"""

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
BASE = "be23df7dedcec8d61c9b0283b5a10af98a3d53cf"
PREFIX = PROJECT.relative_to(REPO).as_posix() + "/"
BASELINE = HERE / "preservation_baseline.json"
TITLE = "感染阈值约束下跟踪隔离的全域最优控制"
PROTECTED_ROOTS = ("data/numerical_scenarios/", "figures/", "matlab/")
ALLOWED_TRACKED = {PREFIX + name for name in (
    "latex/main.tex", "latex/main.bbl", "latex/main.pdf", "latex/theory_only.pdf", "README.md")}


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
    assert git("rev-parse", "HEAD").decode().strip() == BASE, "捕获时 HEAD 必须为 A1 之前的 be23df7"
    records = {}
    for path, blob in tracked_protected().items():
        current = disk_path(REPO / path).read_bytes()
        # 直接读取 blob，避免 Git 对超长 revision:path 参数尝试路径解析。
        original = git("cat-file", "blob", blob)
        assert normalized(current) == normalized(original), f"保护文件在捕获时已偏离基准：{path}"
        records[path] = {"working_sha256": digest(current), "git_sha256": digest(original),
                         "git_blob": blob, "bytes": len(current)}
    base_source = git("show", f"{BASE}:{PREFIX}latex/main.tex").decode("utf-8")
    current_source = (LATEX / "main.tex").read_text(encoding="utf-8")
    assert generated_blocks(current_source) == generated_blocks(base_source), "捕获时自动生成数值块已改变"
    report = {"base_commit": BASE, "captured_utc": datetime.now(timezone.utc).isoformat(),
              "protected_roots": list(PROTECTED_ROOTS), "protected_files": records,
              "generated_blocks": generated_blocks(base_source),
              "initial_tracked_changes": git("diff", "--name-only", BASE).decode("utf-8").splitlines(),
              "optimizer_calls": 0, "scientific_solves": 0}
    write_json(BASELINE, report)
    print(f"A1 baseline captured: {len(records)} protected files; {len(report['generated_blocks'])} generated blocks")


def uncomment(source):
    return re.sub(r"(?<!\\)%[^\n]*", "", source)


def source_checks(source, model_label, equivalence_label):
    source = uncomment(source)
    checks = []

    def check(name, passed, details=None):
        entry = {"name": name, "passed": bool(passed)}
        if details is not None:
            entry["details"] = details
        checks.append(entry)

    old_patterns = {
        "beta_1/beta_2": r"\\beta\s*_\s*(?:\{\s*[12]\s*\}|[12])",
        "q_max": r"q\s*_\s*\{?\s*(?:\\max|max|\\mathrm\{max\})\s*\}?",
        "dual_transmission_wording": "双传播",
        "R^m": r"\\mathbb\s*\{?\s*R\s*\}?\s*\^\s*\{?m\}?",
        "aggregate_m": r"\\dot\s*\{?m\}?|m\s*\(\s*t\s*\)|s\s*\+\s*i\s*\+\s*m\s*=",
    }
    for name, pattern in old_patterns.items():
        matches = [{"line": source.count("\n", 0, m.start()) + 1, "match": m.group()}
                   for m in re.finditer(pattern, source)]
        check("no_old_" + name, not matches, matches)
    check("title_main", r"\title{\bfseries " + TITLE in source)
    check("title_metadata", "pdftitle={" + TITLE + "}" in source)
    check("title_header", r"\fancyhead[L]{" + TITLE + "}" in source)
    check("five_compartment_model_label", rf"\label{{{model_label}}}" in source)
    check("lambda_zero_equivalence_label", rf"\label{{{equivalence_label}}}" in source)
    for name, pattern in {
        "gamma_aggregation": r"\\gamma\s*=\s*\\delta_I\s*\+\s*\\gamma_I",
        "return_total_susceptible": r"\\tilde\s*\{?s\}?\s*=\s*s\s*\+\s*s_q",
        "five_compartment_conservation": r"s\s*\+\s*s_q\s*\+\s*i\s*\+\s*i_q\s*\+\s*r\s*=\s*1",
    }.items():
        check(name, re.search(pattern, source))
    definitions = list(re.finditer(r"P_0\s*\(\s*s\s*,\s*i\s*\)\s*:?=", source))
    check("P0_defined_exactly_once", len(definitions) == 1, len(definitions))
    if len(definitions) == 1:
        position = definitions[0].start()
        section_count = len(re.findall(r"\\section\s*\{", source[:position]))
        safe_pos = source.find(r"\label{eq:safe-set}")
        check("P0_defined_in_section_4", section_count == 4, section_count)
        check("P0_defined_before_safe_set", safe_pos > position)
        begin = source.rfind(r"\begin{equation}", 0, safe_pos)
        end = source.find(r"\end{equation}", safe_pos)
        check("safe_set_uses_P0", "P_0" in source[begin:end] and "K" in source[begin:end])
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
    checks = source_checks(source, args.model_label, args.equivalence_label)
    report = {"batch": "A1", "base_commit": BASE,
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
    parser.add_argument("--capture", action="store_true", help="仅在 A1 修改之前捕获保护基线")
    parser.add_argument("--model-label", default="eq:five-compartment-model")
    parser.add_argument("--equivalence-label", default="prop:five-compartment-reduction")
    parser.add_argument("--allow-tracked", action="append", default=[], help="显式追加的仓库相对允许路径")
    args = parser.parse_args()
    if args.capture:
        capture()
    else:
        audit(args)


if __name__ == "__main__":
    main()
