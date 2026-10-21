#!/usr/bin/env python3
"""G1 文字、公式及保护文件审计；只读 Git 与保护目录，不运行数值程序。"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPO = PROJECT.parent
BASELINE = "689a627"
MAIN = PROJECT / "latex/main.tex"
MAIN_REL = MAIN.relative_to(REPO).as_posix()
SNAPSHOT = HERE / "protected_files_initial.json"
TIME_EQ = {"eq:time-HJB", "eq:time-boundary-set", "eq:time-switch",
           "eq:regularized-cost", "eq:projection-feedback"}
REMOVED_LABELS = TIME_EQ | {"sec:time-varying", "prop:time-conditional",
                            "prop:regularized-pointwise", "app:proof-scope"}
NEW_LABELS = {"sec:preliminaries", "sec:candidate-construction", "sec:optimality",
              "sec:mechanisms", "sec:numerics", "sec:discussion", "app:tracking-region-proof"}
MARKERS = {
    "G1-INTRO-PRELIMINARIES": "附录 E 前两段改为新第 4 节证明路线",
    "G1-INTRO-CONSTRUCTION": "新第 5 节导读",
    "G1-INTRO-VERIFICATION": "新第 6 节导读",
    "G1-TRACKING-PROOF-SKETCH": "正文引理证明思路及附录指引",
    "G1-UNIQUENESS-ROADMAP": "唯一性证明路线",
}


def git(*args: str, data: bytes | None = None) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO, input=data)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def disk(path: Path) -> Path:
    """Windows 长路径必须使用 extended-length 路径，避免静默漏枚举。"""
    if os.name == "nt" and not str(path).startswith("\\\\?\\"):
        return Path("\\\\?\\" + str(path.absolute()))
    return path


def text(data: bytes) -> str:
    return data.decode("utf-8-sig").replace("\r\n", "\n")


def balanced_arg(source: str, opening: int) -> tuple[str, int]:
    if source[opening] != "{":
        raise ValueError("缺少左花括号")
    depth = 0
    for pos in range(opening, len(source)):
        if source[pos] == "{" and (pos == 0 or source[pos - 1] != "\\"):
            depth += 1
        elif source[pos] == "}" and (pos == 0 or source[pos - 1] != "\\"):
            depth -= 1
            if not depth:
                return source[opening + 1:pos], pos + 1
    raise ValueError("未闭合花括号")


def headings(source: str) -> list[dict]:
    result = []
    for match in re.finditer(r"\\(section|subsection|subsubsection)\*?\{", source):
        title, end = balanced_arg(source, match.end() - 1)
        result.append({"level": match.group(1), "title": title,
                       "start": match.start(), "end": end,
                       "line": source.count("\n", 0, match.start()) + 1})
    return result


def remove_headings(source: str) -> str:
    for item in reversed(headings(source)):
        source = source[:item["start"]] + source[item["end"]:]
    # 节标签是结构 token；对象标签在其他专项检查中单独核对。
    return re.sub(r"\\label\{(?:sec|app):[^}]+\}", "", source)


def remove_comments(source: str) -> str:
    return re.sub(r"(?m)(?<!\\)%[^\n]*", "", source)


def canonical(source: str) -> str:
    source = remove_headings(remove_comments(source))
    source = re.sub(r"\\(?:begin|end)\{proof\}(?:\[[^\]]*\])?", "\n\n", source)
    return re.sub(r"\s+", " ", source).strip()


def paragraphs(source: str) -> list[str]:
    # 先移除结构 token，避免标题降级或新增空行人为制造正文差异。
    source = remove_headings(remove_comments(source))
    source = re.sub(r"\\(?:begin|end)\{proof\}(?:\[[^\]]*\])?", "\n\n", source)
    return [p for raw in re.split(r"\n[ \t]*\n+", source)
            if (p := re.sub(r"\s+", " ", raw).strip())]


def unwrap_theory(source: str) -> tuple[str, list[dict]]:
    changes = []
    token = re.compile(r"\\ifdefined\\TheoryOnly|\\if[A-Za-z]+\b|\\else\b|\\fi\b")
    while (begin := re.search(r"\\ifdefined\\TheoryOnly", source)):
        depth, alt, finish = 1, None, None
        for match in token.finditer(source, begin.end()):
            value = match.group()
            if value == r"\fi":
                depth -= 1
                if depth == 0:
                    finish = match
                    break
            elif value == r"\else":
                if depth == 1:
                    alt = match
            else:
                depth += 1
        if finish is None:
            raise ValueError("TheoryOnly 条件未闭合")
        dropped = source[begin.end():alt.start() if alt else finish.start()]
        kept = source[alt.end():finish.start()] if alt else ""
        changes.append({"id": f"theory-branch-{len(changes)+1}",
                        "reason": "删除 TheoryOnly 专属分支及条件壳，保留主文分支",
                        "old": source[begin.start():finish.end()], "new": kept,
                        "deleted_content": dropped})
        source = source[:begin.start()] + kept + source[finish.end():]
    return source, changes


def remove_section(source: str, label: str) -> tuple[str, str]:
    loc = source.index(r"\label{" + label + "}")
    hs = [h for h in headings(source) if h["level"] == "section"]
    item = max((h for h in hs if h["start"] < loc), key=lambda h: h["start"])
    stop = min((h["start"] for h in hs if h["start"] > loc), default=len(source))
    return source[:item["start"]] + source[stop:], source[item["start"]:stop]


def marked_paragraph(source: str, marker: str) -> tuple[str, str]:
    match = re.search(r"(?m)^%\s*" + re.escape(marker) + r"\s*\n", source)
    if not match:
        raise ValueError(f"新增白名单缺少标记 {marker}")
    stop = re.search(r"\n[ \t]*\n", source[match.end():])
    end = match.end() + stop.start() if stop else len(source)
    value = source[match.end():end].strip()
    if not value:
        raise ValueError(f"新增白名单为空 {marker}")
    return source[:match.start()] + source[end:], value


def proof_after_label(source: str, label: str) -> str:
    start = source.index(r"\label{" + label + "}")
    begin = source.index(r"\begin{proof}", start)
    end = source.index(r"\end{proof}", begin) + len(r"\end{proof}")
    return source[begin:end]


def protected(path: str) -> bool:
    p = Path(path)
    rel = p.relative_to(Path(PROJECT.relative_to(REPO)))
    if rel.parts[0] in {"data", "figures"}:
        return True
    if rel.parts[:2] == ("latex", "generated"):
        return True
    if rel.parts[0] == "validation":
        return rel.parts[1] != HERE.name
    return rel.parts[0] == "matlab" and p.suffix.lower() in {".m", ".py"}


def protected_current() -> list[str]:
    roots = [PROJECT / name for name in ("data", "figures", "latex/generated", "matlab", "validation")]
    return sorted(p.relative_to(disk(REPO)).as_posix() for root in roots if disk(root).exists()
                  for p in disk(root).rglob("*") if p.is_file() and protected(p.relative_to(disk(REPO)).as_posix()))


def capture_protected() -> None:
    if SNAPSHOT.exists():
        raise ValueError("原始保护快照已存在，拒绝覆盖")
    tree = {}
    for row in git("ls-tree", "-rz", BASELINE, "--", PROJECT.relative_to(REPO).as_posix()).split(b"\0"):
        if row:
            meta, name = row.split(b"\t", 1)
            rel = name.decode("utf-8")
            if protected(rel):
                tree[rel] = meta.split()[2].decode("ascii")
    # Git 一次比较负责属性过滤和 CRLF；避免每个文件启动一次 hash-object。
    changed = [p.decode("utf-8") for p in git("diff", "--name-only", "-z", BASELINE,
               "--", PROJECT.relative_to(REPO).as_posix()).split(b"\0") if p]
    mismatches = [rel for rel in changed if protected(rel)]
    files = {}
    for rel in protected_current():
        data = disk(REPO / rel).read_bytes()
        entry = {"sha256": sha(data), "bytes": len(data), "tracked_at_baseline": rel in tree}
        if rel in tree:
            entry.update({"baseline_git_blob": tree[rel], "git_diff_baseline_identical": rel not in mismatches})
        files[rel] = entry
    missing = sorted(set(tree) - files.keys())
    if mismatches or missing:
        raise ValueError(f"保护文件初始状态不等于基准：changed={mismatches}, missing={missing}")
    SNAPSHOT.write_text(json.dumps({"baseline": BASELINE, "files": files,
                                  "note": "原始工作区 SHA-256；Git blob 比较使用项目换行过滤规则。"},
                                 ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"保护文件初始快照：{len(files)} 个，Git 基准内容全部一致。")


def equation_blocks(source: str) -> dict[str, str]:
    result = {}
    # 公式的最外层数学环境，包含其全部空白、标签和内部 aligned/cases。
    math_envs = {"equation", "equation*", "align", "align*", "gather", "gather*", "multline", "multline*"}
    stack = []
    for match in re.finditer(r"\\(begin|end)\{([^}]+)\}", source):
        kind, env = match.groups()
        if env not in math_envs:
            continue
        if kind == "begin":
            stack.append((env, match.start()))
        else:
            opened, pos = stack.pop()
            if opened != env:
                raise ValueError("数学环境不匹配")
            if not stack:
                block = source[pos:match.end()]
                for label in re.findall(r"\\label\{([^}]+)\}", block):
                    result[label] = block
    return result


def run_audit() -> int:
    old_raw = git("show", f"{BASELINE}:{MAIN_REL}")
    new_raw = MAIN.read_bytes()
    old, new = text(old_raw), text(new_raw)
    errors, changes = [], []
    old_adjusted, theory_changes = unwrap_theory(old)
    changes.extend(theory_changes)
    if len(theory_changes) != 7:
        errors.append(f"TheoryOnly 分支应为 7，实际 {len(theory_changes)}")
    old_route = ""
    for label, reason in [("sec:time-varying", "整节删除时变接触率条件性结论"),
                          ("app:proof-scope", "前两段转为新第 4 节证明路线")]:
        old_adjusted, deleted = remove_section(old_adjusted, label)
        if label == "app:proof-scope":
            body = deleted.split(r"\label{app:proof-scope}", 1)[1].strip()
            parts = re.split(r"\n[ \t]*\n+", body)
            scan = "任何一个数值扫描都不被用于证明这些全称命题。"
            if len(parts) != 3 or scan not in parts[1]:
                raise ValueError("附录 E 原文三段或扫描句定位失败")
            old_route = parts[0] + "\n\n" + parts[1].replace(scan, "").rstrip()
            changes.append({"id": "proof-scope-scan", "reason": "删除数值扫描句", "old": scan, "new": ""})
            changes.append({"id": "proof-scope-last-paragraph", "reason": "删除附录 E 最后校验口径段", "old": parts[2], "new": ""})
        else:
            changes.append({"id": label, "reason": reason, "old": deleted, "new": ""})
    conclusion = ("时变接触率仅保留条件性的验证与唯一性讨论。\n"
                  "严格凸正则化给出的是固定状态和梯度下的唯一点态极小元，不能单凭此推出整个非线性控制问题全局唯一。\n"
                  "本稿未完成的扩展证明已在注\\ref{rem:unproved-extensions}中列明，不作为常接触率主定理的结论。")
    if old_adjusted.count(conclusion) != 1:
        errors.append("结论时变段定位失败")
    old_adjusted = old_adjusted.replace(conclusion, "", 1)
    changes.append({"id": "conclusion-time", "reason": "删除结论时变段", "old": conclusion, "new": ""})
    new_adjusted = new
    additions = {}
    for marker, reason in MARKERS.items():
        new_adjusted, value = marked_paragraph(new_adjusted, marker)
        additions[marker] = value
        changes.append({"id": marker, "reason": reason,
                        "old": old_route if marker == "G1-INTRO-PRELIMINARIES" else "", "new": value})
    old_scope = "本节及第\\ref{sec:constant-problem}--\\ref{sec:constant-uniqueness}节固定\n"
    loc = new_adjusted.index(r"\label{sec:main-results}") + len(r"\label{sec:main-results}")
    end = new_adjusted.index(r"\begin{equation}", loc)
    new_scope = new_adjusted[loc:end].strip()
    if not all(ref in new_scope for ref in ("sec:main-results", "sec:mechanisms", "thm:wellposed")):
        errors.append("常接触率范围句未同时引用 main-results、mechanisms、wellposed")
    if old_adjusted.count(old_scope) != 1:
        errors.append("旧常接触率范围句定位失败")
    old_adjusted = old_adjusted.replace(old_scope, "", 1)
    new_adjusted = new_adjusted[:loc] + new_adjusted[end:]
    changes.append({"id": "constant-scope", "reason": "对应新第 3–7 节并说明一般时变 c 的适定性", "old": old_scope, "new": new_scope})
    emph_old = ["各分区内的控制选择。", "容量弧上的延续。", "切换曲线上的行为。", "各阶段轨道的唯一确定。"]
    for step, title in enumerate(emph_old, 1):
        old_title = r"\emph{" + title + "}"
        pattern = r"\\emph\{第\s*" + str(step) + r"\s*步：" + re.escape(title) + r"\}"
        matches = list(re.finditer(pattern, new_adjusted))
        if len(matches) != 1:
            errors.append(f"唯一性证明第 {step} 步标题定位失败")
        else:
            value = matches[0].group()
            new_adjusted = new_adjusted[:matches[0].start()] + old_title + new_adjusted[matches[0].end():]
            changes.append({"id": f"uniqueness-step-{step}", "reason": "仅增加分步前缀", "old": old_title, "new": value})
    # 纯结构 token：新增 proof appendix 标签、不同级别标题及空行不计入正文改写。
    old_pars, new_pars = paragraphs(old_adjusted), paragraphs(new_adjusted)
    old_full, new_full = canonical(old_adjusted), canonical(new_adjusted)
    old_counts, new_counts = Counter(old_pars), Counter(new_pars)
    lost = [{"paragraph": para, "count": count} for para, count in old_counts.items()
            if para not in new_full]
    added = [{"paragraph": para, "count": count} for para, count in new_counts.items()
             if para not in old_full]
    if lost:
        errors.append(f"未解释旧段落缺失：{len(lost)}")
    if added:
        errors.append(f"未解释新段落：{len(added)}")
    # 附加字符级多重集与逐段比对互补，防止重复短段落被无意合并或删除。
    old_chars, new_chars = Counter(re.sub(r"\s+", "", old_full)), Counter(re.sub(r"\s+", "", new_full))
    if old_chars != new_chars:
        errors.append("白名单及结构 token 剥离后字符多重集不一致")
    old_eq, new_eq = equation_blocks(old), equation_blocks(new)
    removed_eq, added_eq = sorted(set(old_eq) - new_eq.keys()), sorted(set(new_eq) - old_eq.keys())
    changed_eq = [label for label in old_eq.keys() & new_eq.keys() if old_eq[label] != new_eq[label]]
    if set(removed_eq) != TIME_EQ or added_eq or changed_eq:
        errors.append("带标签公式未通过逐字保全或删除白名单核验")
    old_labels = Counter(re.findall(r"\\label\{([^}]+)\}", old))
    new_labels = Counter(re.findall(r"\\label\{([^}]+)\}", new))
    removed_labels, added_labels = sorted((old_labels - new_labels).elements()), sorted((new_labels - old_labels).elements())
    if set(removed_labels) != REMOVED_LABELS or set(added_labels) != NEW_LABELS:
        errors.append("对象标签增删超出结构及删除白名单")
    auto = []
    for match in re.finditer(r"(?m)^% BEGIN AUTO-GENERATED ([^\n]+)\n", old):
        title = match.group(1)
        pattern = r"(?ms)^% BEGIN AUTO-GENERATED " + re.escape(title) + r"\n.*?^% END AUTO-GENERATED " + re.escape(title) + r"[^\n]*"
        before, after = re.search(pattern, old), re.search(pattern, new)
        same = bool(before and after and before.group() == after.group())
        raw_pattern = pattern.encode("utf-8")
        before_raw, after_raw = re.search(raw_pattern, old_raw), re.search(raw_pattern, new_raw)
        raw_same = bool(before_raw and after_raw and before_raw.group() == after_raw.group())
        auto.append({"name": title, "identical": same, "raw_bytes_identical": raw_same,
                     "sha256": sha(before.group().encode())})
        if not same:
            errors.append(f"自动生成块变化：{title}")
        if not raw_same:
            errors.append(f"自动生成块原始字节变化：{title}")
    if len(auto) != 2:
        errors.append("自动生成块数量不是 2")
    original_tracking = proof_after_label(old, "lem:tracking-region")
    moved_tracking = proof_after_label(new, "app:tracking-region-proof")
    tracking_identical = original_tracking == moved_tracking
    if not tracking_identical:
        errors.append("完全跟踪分区引理的移入附录证明不逐字一致")
    unique_original = proof_after_label(old, "thm:unique-q")
    unique_new = proof_after_label(new_adjusted, "thm:unique-q")
    unique_normalized_identical = canonical(unique_original) == canonical(unique_new)
    # 新增路线的包装使 proof 开头多出空行；仅剥离这处包装空白，
    # proof 内已有句子、公式、空白及行尾一律严格比较。
    def proof_body(value: str) -> str:
        return value[len(r"\begin{proof}"): -len(r"\end{proof}")].lstrip("\n")
    unique_identical = proof_body(unique_original) == proof_body(unique_new)
    if not unique_identical or not unique_normalized_identical:
        errors.append("唯一性证明在排除新增路线与分步前缀后不一致")
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    protected_diff = []
    for rel, info in snapshot["files"].items():
        path = disk(REPO / rel)
        if not path.exists() or sha(path.read_bytes()) != info["sha256"]:
            protected_diff.append(rel)
    protected_new = sorted(set(protected_current()) - snapshot["files"].keys())
    if protected_diff or protected_new:
        errors.append("保护文件原始字节或文件清单变化")
    report = {"baseline": BASELINE, "passed": not errors, "errors": errors,
              "normalization": "只折叠段落空白并剥离标题/节标签/注释/proof 包装；正文保全双向匹配且核对字符多重集；公式另作保留全部源空白的逐字核对（统一行尾LF）。",
              "source_sha256": {"old_git_blob_raw": sha(old_raw), "new_worktree_raw": sha(new_raw)},
              "paragraphs": {"old_after_whitelist": len(old_pars), "new_after_whitelist": len(new_pars),
                             "unexplained_lost": lost, "unexplained_added": added,
                             "character_multiset_identical": old_chars == new_chars},
              "whitelist_changes": changes,
              "structural_headings": {"old": headings(old), "new": headings(new)},
              "equations": {"old_labels": len(old_eq), "new_labels": len(new_eq), "removed": removed_eq,
                            "added": added_eq, "changed": changed_eq},
              "labels": {"removed": removed_labels, "added": added_labels},
              "auto_generated_blocks": auto,
              "proofs": {"tracking_region_exactly_moved": tracking_identical,
                         "uniqueness_content_preserved": unique_identical,
                         "uniqueness_strict_source_identical_after_authorized_removal": unique_identical,
                         "uniqueness_normalized_identical": unique_normalized_identical,
                         "uniqueness_wrapper_cleanup": "仅移除新增路线包装后位于 proof 开头的额外换行；原有证明内部逐字比较"},
              "protected_files": {"count": len(snapshot["files"]), "changed_or_missing": protected_diff,
                                  "unexpected_new": protected_new,
                                  "initial_snapshot": SNAPSHOT.name},
              "optimizer_calls": 0, "new_ocp_solves": 0, "matlab_calls": 0}
    (HERE / "preservation_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = ["# G1 文字及保护文件保全审计", "", f"- 基准：`{BASELINE}`。", f"- 结果：{'通过' if not errors else '失败'}。",
          f"- 旧/新归一化段落数：{len(old_pars)} / {len(new_pars)}。",
          f"- 保留带标签公式：{len(new_eq)}；仅删除 {', '.join(removed_eq)}。",
          f"- 两个自动生成块逐字不变：{all(x['identical'] for x in auto)}。",
          f"- 保护文件原始 SHA-256：{len(snapshot['files'])} 个；变化 {len(protected_diff)}，新增 {len(protected_new)}。",
          f"- 移入附录的证明逐字不变：{tracking_identical}；唯一性证明排除获准新增文字后不变：{unique_identical}。",
          "- 优化器调用 / 新增 OCP 求解 / MATLAB 调用：0 / 0 / 0。", "", report["normalization"], ""]
    if errors:
        md += ["## 失败项目", ""] + [f"- {err}" for err in errors] + [""]
    md += ["## 白名单逐项原文与新文", ""]
    for change in changes:
        md += [f"### {change['id']}：{change['reason']}", "", "原文：", "", "```latex", change["old"] or "（新增，原文为空）", "```", "", "新文：", "", "```latex", change["new"] or "（删除，新文为空）", "```", ""]
    md += ["## 结构 token 变动", "", "标题和节标签在段落审计中剥离；下面完整列出新旧标题，供作者核对层级及标题。", "", "### 原标题", ""]
    md += [f"- L{h['line']} `{h['level']}`：{h['title']}" for h in headings(old)]
    md += ["", "### 新标题", ""] + [f"- L{h['line']} `{h['level']}`：{h['title']}" for h in headings(new)]
    for key, title in [("unexplained_lost", "未解释旧段落"), ("unexplained_added", "未解释新段落")]:
        md += ["", f"## {title}", ""]
        md += ["```latex\n" + row["paragraph"] + "\n```\n" for row in report["paragraphs"][key]] or ["无。"]
    (HERE / "preservation_audit.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"passed": not errors, "errors": errors, "protected_files": len(snapshot["files"]),
                      "old_paragraphs": len(old_pars), "new_paragraphs": len(new_pars)}, ensure_ascii=False))
    return int(bool(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-protected", action="store_true", help="首次运行时建立保护文件原始字节快照，拒绝覆盖")
    args = parser.parse_args()
    if args.capture_protected:
        capture_protected()
        return 0
    return run_audit()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"审计失败：{exc}", file=sys.stderr)
        sys.exit(2)
