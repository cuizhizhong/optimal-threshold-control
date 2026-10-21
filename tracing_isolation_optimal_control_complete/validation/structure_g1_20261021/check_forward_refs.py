#!/usr/bin/env python3
"""列出 LaTeX 中指向定理类对象和带标签公式的引用及前向引用。

只使用 Python 标准库；忽略未转义的注释，保留原文件行号。源码必须已经
完成条件分支清理；仅识别已知的 NumTheoryRef 引用包装宏，其他宏和 input
不展开，主文件中的定义与引用逐项检查。基准版本可用 --git-ref 读取。
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
import subprocess
from pathlib import Path


THEOREM_ENVS = {"theorem", "lemma", "proposition", "corollary"}
MATH_ENVS = {
    "equation", "align", "alignat", "gather", "multline", "flalign",
    "eqnarray", "subequations",
}
REFERENCE_COMMANDS = {"ref", "eqref", "autoref", "cref", "Cref", "vref", "Vref"}
WRAPPED_REFERENCE_COMMANDS = {"NumTheoryRef"}
TOKEN = re.compile(
    r"\\(?P<command>section|subsection|subsubsection|paragraph|appendix|"
    r"begin|end|label|ref|eqref|autoref|cref|Cref|vref|Vref|NumTheoryRef)\*?(?![A-Za-z])"
)


def uncomment(source: str) -> str:
    """注释换为空格，避免源码偏移和行号改变。"""
    lines = []
    for line in source.splitlines(keepends=True):
        for i, char in enumerate(line):
            if char != "%":
                continue
            backslashes = 0
            j = i - 1
            while j >= 0 and line[j] == "\\":
                backslashes += 1
                j -= 1
            if backslashes % 2 == 0:
                ending = "\n" if line.endswith("\n") else ""
                line = line[:i] + " " * (len(line) - i - len(ending)) + ending
                break
        lines.append(line)
    return "".join(lines)


def argument(source: str, offset: int, opening: str = "{") -> tuple[str, int]:
    while offset < len(source) and source[offset].isspace():
        offset += 1
    if offset >= len(source) or source[offset] != opening:
        return "", offset
    closing = "}" if opening == "{" else "]"
    start = offset + 1
    depth = 1
    offset += 1
    while offset < len(source):
        if source[offset] == "\\":
            offset += 2
            continue
        if source[offset] == opening:
            depth += 1
        elif source[offset] == closing:
            depth -= 1
            if depth == 0:
                return source[start:offset], offset + 1
        offset += 1
    raise ValueError(f"未闭合的 {opening} 参数，源码偏移 {start - 1}")


def plain_title(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse(source: str) -> tuple[dict[str, dict], list[dict], list[dict]]:
    clean = uncomment(source)
    source_lines = source.splitlines()
    line_starts = [0] + [m.end() for m in re.finditer("\n", source)]

    def line_at(offset: int) -> int:
        return bisect.bisect_right(line_starts, offset)

    sections: list[dict] = []
    counters = [0, 0, 0, 0]
    in_appendix = False
    envs: list[dict] = []
    definitions: dict[str, dict] = {}
    refs: list[dict] = []
    proofs: list[dict] = []
    last_closed_statement: dict | None = None

    def location() -> dict:
        return {
            "section": " > ".join(f"{s['number']} {s['title']}" for s in sections),
            "top_section_number": sections[0]["number"] if sections else "",
            "top_section_title": sections[0]["title"] if sections else "",
            "top_section_label": sections[0].get("label", "") if sections else "",
        }

    for match in TOKEN.finditer(clean):
        command = match.group("command")
        offset = match.start()
        lineno = line_at(offset)
        if command == "appendix":
            in_appendix = True
            counters = [0, 0, 0, 0]
            sections = []
            continue
        arg, arg_end = argument(clean, match.end())
        if not arg:
            continue
        if command in {"section", "subsection", "subsubsection", "paragraph"}:
            depth = {"section": 0, "subsection": 1, "subsubsection": 2, "paragraph": 3}[command]
            counters[depth] += 1
            for k in range(depth + 1, len(counters)):
                counters[k] = 0
            parts = [str(value) for value in counters[:depth + 1]]
            if in_appendix:
                parts[0] = chr(ord("A") + counters[0] - 1)
            sections = sections[:depth]
            sections.append({"number": ".".join(parts), "title": plain_title(arg), "line": lineno})
            continue
        if command == "begin":
            optional, _ = argument(clean, arg_end, "[")
            env = {"env": arg.rstrip("*"), "offset": offset, "line": lineno,
                   "title": plain_title(optional), "labels": [], **location()}
            if env["env"] == "proof":
                owner = ""
                title_refs = re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", optional)
                if title_refs:
                    owner = title_refs[0]
                elif last_closed_statement and not clean[last_closed_statement["end"]:offset].strip():
                    owner = ",".join(last_closed_statement["labels"])
                else:
                    preceding = clean[max(0, offset - 500):offset]
                    announced = re.findall(
                        r"(?:定理|引理|命题|推论)\s*\\ref\{([^}]+)\}[^。\n]*证明",
                        preceding,
                    )
                    if announced:
                        owner = announced[-1]
                if not owner and sections:
                    section_label = sections[0].get("label", "")
                    if section_label.startswith("app:") and section_label.endswith("-proof"):
                        suffix = section_label.removeprefix("app:").removesuffix("-proof")
                        candidates = [key for key, value in definitions.items()
                                      if value["type"] in THEOREM_ENVS and key.split(":", 1)[-1] == suffix]
                        if len(candidates) == 1:
                            owner = candidates[0]
                env["proof_id"] = len(proofs) + 1
                env["owner"] = owner
                proofs.append({key: value for key, value in env.items() if key != "labels"})
            envs.append(env)
            continue
        if command == "end":
            wanted = arg.rstrip("*")
            for i in range(len(envs) - 1, -1, -1):
                if envs[i]["env"] == wanted:
                    closed = envs[i]
                    envs = envs[:i]
                    if wanted in THEOREM_ENVS:
                        last_closed_statement = {**closed, "end": arg_end}
                    break
            continue
        if command == "label":
            matched = next((env for env in reversed(envs)
                            if env["env"] in THEOREM_ENVS | MATH_ENVS), None)
            if matched:
                matched["labels"].append(arg)
                object_type = "equation" if matched["env"] in MATH_ENVS else matched["env"]
                if arg in definitions:
                    raise ValueError(f"重复标签 {arg}，行 {lineno}")
                definitions[arg] = {
                    "label": arg, "type": object_type, "environment": matched["env"],
                    "definition_line": matched["line"], "label_line": lineno,
                    "offset": matched["offset"], "label_offset": offset,
                    "title": matched["title"], **location(),
                }
            elif sections and arg.startswith(("sec:", "app:")):
                sections[-1]["label"] = arg
            continue
        if command in REFERENCE_COMMANDS | WRAPPED_REFERENCE_COMMANDS:
            proof = next((env for env in reversed(envs) if env["env"] == "proof"), None)
            wrapper_text, _ = argument(clean, arg_end) if command in WRAPPED_REFERENCE_COMMANDS else ("", arg_end)
            for label in arg.split(","):
                refs.append({
                    "label": label.strip(), "command": command, "line": lineno,
                    "column": offset - line_starts[lineno - 1] + 1,
                    "offset": offset, **location(), "in_proof": proof is not None,
                    "proof_id": proof["proof_id"] if proof else None,
                    "proof_owner": proof["owner"] if proof else "",
                    "proof_title": proof["title"] if proof else "",
                    "proof_start_line": proof["line"] if proof else None,
                    "source_line": source_lines[lineno - 1].strip(),
                    "wrapper_text": wrapper_text,
                    "expanded_reference": f"\\ref{{{label.strip()}}}" if command in WRAPPED_REFERENCE_COMMANDS else "",
                })

    tracked_refs = []
    for ref in refs:
        target = definitions.get(ref["label"])
        if target is None:
            continue
        forward = ref["offset"] < target["offset"]
        overview = ref["top_section_label"] == "sec:main-results" or (
            ref["top_section_number"] == "3" and ref["top_section_title"] == "主结果与最优分区")
        tracked_refs.append({**ref, "target": target,
                             "forward": forward,
                             "intentional_overview": forward and overview,
                             "self_reference": ref["proof_owner"] == ref["label"]})
    return definitions, tracked_refs, proofs


def table(rows: list[dict]) -> str:
    header = ("| 序号 | 引用行:列 | 命令及标签 | 所在节 | 证明 | 对象定义行 / 标签行 | 前向 |\n"
              "|---:|---|---|---|---|---|---|\n")
    cells = []
    for ref in rows:
        proof = f"证明 {ref['proof_id']}，{ref['proof_owner'] or ref['proof_title'] or '未指定对象'}" if ref["in_proof"] else "正文"
        values = [str(ref["id"]), f"{ref['line']}:{ref['column']}",
                  f"`\\{ref['command']}{{{ref['label']}}}" + (f"{{{ref['wrapper_text']}}}" if ref["wrapper_text"] else "") + "`", ref["section"], proof,
                  f"{ref['target']['definition_line']} / {ref['target']['label_line']}",
                  "是（第 3 节概览）" if ref["intentional_overview"] else "是" if ref["forward"] else "否"]
        cells.append("| " + " | ".join(value.replace("|", "\\|").replace("\n", " ") for value in values) + " |\n")
    return header + "".join(cells) if rows else "无。\n"


def run() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tex", type=Path, default=here.parent.parent / "latex" / "main.tex")
    parser.add_argument("--out-dir", type=Path, default=here)
    parser.add_argument("--stem", default="forward_refs")
    parser.add_argument("--git-ref", help="从指定 Git 提交读取 --tex 对应的基准文件，而不创建源码副本")
    args = parser.parse_args()
    source_name = str(args.tex.resolve())
    if args.git_ref:
        repo = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=args.tex.parent, text=True).strip())
        relative = args.tex.resolve().relative_to(repo.resolve()).as_posix()
        source_name = f"git:{args.git_ref}:{relative}"
        source_bytes = subprocess.check_output(["git", "show", f"{args.git_ref}:{relative}"], cwd=repo)
    else:
        source_bytes = args.tex.read_bytes()
    source = source_bytes.decode("utf-8-sig")
    known_wrapper = r"\providecommand{\NumTheoryRef}[2]{#2~\ref{#1}}"
    if r"\NumTheoryRef" in source and known_wrapper not in uncomment(source):
        raise ValueError("NumTheoryRef 的定义与已知包装宏不符，不能推断其展开")
    definitions, refs, proofs = parse(source)
    for i, ref in enumerate(refs, 1):
        ref["id"] = i
    forward = [ref for ref in refs if ref["forward"]]
    overview = [ref for ref in forward if ref["intentional_overview"]]
    other = [ref for ref in forward if not ref["intentional_overview"]]
    proof_forward = [ref for ref in other if ref["in_proof"]]
    payload = {
        "schema_version": 2, "source": source_name,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "method": "逐个词法解析主文件命令；忽略注释；以对象 begin 位置为定义起点；已知 NumTheoryRef{#1}{#2} 展开为 #2~ref{#1}，其他任意宏与 input 不展开。",
        "counts": {"definitions": len(definitions), "references": len(refs),
                   "wrapped_references": sum(ref["command"] in WRAPPED_REFERENCE_COMMANDS for ref in refs),
                   "forward": len(forward), "intentional_overview": len(overview),
                   "other_forward": len(other), "proof_forward_outside_overview": len(proof_forward)},
        "definitions": list(definitions.values()), "references": refs, "proofs": proofs,
    }
    report = [
        "# 前向引用完整清单\n\n",
        f"源文件：`{source_name}`；SHA-256：`{payload['source_sha256']}`。\n\n",
        "检查 `ref`、`eqref`、`autoref`、`cref` 等命令及已知引用包装宏 `NumTheoryRef`，目标限于定理、引理、命题、推论和带标签公式。",
        "未转义注释不参与扫描；定义位置采用对象的 `begin` 行，另列 `label` 行。",
        "同一公式内部的自引用不计为前向。已核对 `\\providecommand{\\NumTheoryRef}[2]{#2~\\ref{#1}}`，",
        "只按这一已知展开纳入该包装宏；目标是定义、图表等其他类型时仍按范围排除。",
        "其他任意宏不推断，主文件之外的 `input` 不展开，当前审计范围为 `main.tex`。\n\n",
        "计数：" + "；".join(f"{key}={value}" for key, value in payload["counts"].items()) + "。\n\n",
        "## 第 3 节概览中的有意前向引用\n\n", table(overview),
        "\n## 其他前向引用\n\n", table(other),
        "\n## 概览以外证明中的前向引用\n\n", table(proof_forward),
        "\n## 全部引用（按源码顺序）\n\n", table(refs),
        "\n## 解释限制\n\n",
        "前向引用属于排版次序事实；是否构成循环依赖还需阅读对应证明。",
        "附录中的独立计算或详细证明在正文陈述之后出现，不能单凭其位置判为循环。",
        "`self_reference` 只表示证明中指向其所证明对象的引用，不能代替证明依赖判断。\n",
    ]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / f"{args.stem}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.out_dir / f"{args.stem}.md").write_text("".join(report), encoding="utf-8")
    print(json.dumps(payload["counts"], ensure_ascii=False))


if __name__ == "__main__":
    run()
