"""生成D批显式暂存清单；--check仅核对实际暂存路径和字节。"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
REPO = PROJECT.parent


def git(*args):
    return subprocess.check_output(["git", *args], cwd=REPO)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
if args.check:
    expected = json.loads((HERE / "staging_paths.json").read_text(encoding="utf-8"))["paths"]
    actual = sorted(x for x in git("diff", "--cached", "--name-only", "-z").decode().split("\0") if x)
    assert actual == expected, {"extra": sorted(set(actual) - set(expected)), "missing": sorted(set(expected) - set(actual))}
    bad = []
    for name in expected:
        staged = git("show", ":" + name)
        working = (REPO / name).read_bytes()
        # 根目录既有TeX/Bib的Git文本换行策略仍适用，其余本批文件按局部.gitattributes保留原始字节。
        if name.startswith(PROJECT.name + "/latex/") and Path(name).suffix in (".tex", ".bib", ".bbl"):
            staged, working = staged.replace(b"\r\n", b"\n"), working.replace(b"\r\n", b"\n")
        if staged != working:
            bad.append(name)
    assert not bad, bad
    print(f"D staging verified: {len(expected)} paths; staged/worktree identity passed")
else:
    paths = {str((PROJECT / "latex" / name).relative_to(REPO).as_posix()) for name in
             ("main.tex", "references.bib", "main.bbl", "main.pdf", "theory_only.pdf")}
    paths.update(p.relative_to(REPO).as_posix() for p in HERE.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    paths.update((HERE / name).relative_to(REPO).as_posix() for name in ("changed_files.txt", "staging_paths.json"))
    paths = sorted(paths)
    (HERE / "changed_files.txt").write_text("\n".join(paths) + "\n", encoding="utf-8", newline="\n")
    (HERE / "staging_paths.json").write_text(json.dumps({"base_commit": "8b8f5a239193f8b5102355f9946b43eaea2b72ea", "count": len(paths), "paths": paths}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    message = "paper: 量级与小容量渐近（D）\n\n定义同入口纯容量填充、成本/时长指标，补固定beta的小容量命题和完整解析证明，核实Zhou/He参数来源；使用80位解析量级图，不新增优化。\n\n核对：28/28原符号、10/10新增代数与2/2片段、10/10保护审计及20/20汇总验收通过；620组扫描中1组不满足共同入口条件而明确mask，35组小容量族、18个精度阈值和2项独立积分。最终双稿46/36页，8/8编译命令退出0且最终日志零问题，24页实际目视；6645个既有文件哈希不变。保留排版、长路径和映射文件回写失败记录；正式产物与最终构建哈希一致。\n\nMATLAB、优化器、新增OCP与ODE均0；止于D，不进入F，不推送，main不变。\n\nCo-Authored-By: Codex <noreply@openai.com>\n"
    temp = PROJECT / "tmp/scaling_asymptotics_20261021/commit_message.txt"
    temp.write_text(message, encoding="utf-8", newline="\n")
    print(f"D explicit staging inventory: {len(paths)} paths")
