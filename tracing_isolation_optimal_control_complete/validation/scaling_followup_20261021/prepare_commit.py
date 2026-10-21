"""以显式清单暂存D后续；不包含旧未跟踪文件或临时构建副本。"""
import argparse
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
    actual = sorted(p for p in git("diff", "--cached", "--name-only", "-z").decode().split("\0") if p)
    assert actual == expected, {"extra": sorted(set(actual) - set(expected)), "missing": sorted(set(expected) - set(actual))}
    bad = []
    for name in expected:
        staged, working = git("show", ":" + name), (REPO / name).read_bytes()
        if name == PROJECT.name + "/latex/main.tex":
            staged, working = staged.replace(b"\r\n", b"\n"), working.replace(b"\r\n", b"\n")
        if staged != working:
            bad.append(name)
    assert not bad, bad
    print(f"D followup staging verified: {len(expected)} paths, bytes identical")
else:
    prefix = PROJECT.name + "/"
    allowed = {prefix + "latex/" + name for name in ("main.tex", "main.pdf", "theory_only.pdf", "main.bbl")}
    tracked_changes = set(git("diff", "--name-only", "HEAD").decode().splitlines())
    new_prefixes = (prefix + "validation/scaling_followup_20261021/", prefix + "latex/generated/", prefix + "figures/scaling/")
    unexpected = {p for p in tracked_changes if p not in allowed and not p.startswith(new_prefixes)}
    assert not unexpected, unexpected
    paths = set(tracked_changes)
    for folder in (HERE, PROJECT / "latex/generated", PROJECT / "figures/scaling"):
        paths.update(p.relative_to(REPO).as_posix() for p in folder.rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    paths.update((HERE / name).relative_to(REPO).as_posix() for name in ("staging_paths.json", "changed_files.txt"))
    paths = sorted(paths)
    (HERE / "changed_files.txt").write_text("\n".join(paths) + "\n", encoding="utf-8", newline="\n")
    (HERE / "staging_paths.json").write_text(json.dumps({"base_commit": "9a67992248f41dada8c02b2e1851fc87ffa54f4f", "count": len(paths), "paths": paths}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    message = "paper: 突出时长结果并使D节自包含\n\n摘要与D节强调低强度尾段被短时完全跟踪替代的时长效应，新增80位公共尾段时长差/缩短百分比；宏移入latex/generated并前言引入，图移入figures/scaling，移除D标记和重复E2例子。图d改归一时长差与y=1参考线，按实际正文宽度使用Times/STIX字体，外置子图标签与单次图例，中文图注交代mask。\n\n核对：时长与旧宏30/30、图前三面板及网格30/30、符号28/28、独立范围25/25、保护审计12/12及最终汇总23/23通过。仓库内和仅latex/figures的全新副本双稿最终各四阶段16命令退出0、零最终诊断，页数均46/36，逐页提取文本一致；12页150dpi实际目视。记录首次clean引用警告及新副本自身初始化8命令，不伪称首次clean四阶段即零警告。6730个旧文件、旧17宏、2个auto块、全部模型/定理/证明与8个保护图保持。\n\nMATLAB、优化器、新增OCP与ODE均0，不推送，不进入F；提交后等待作者审阅。\n\nCo-Authored-By: Codex <noreply@openai.com>\n"
    target = PROJECT / "tmp/scaling_followup_20261021/commit_message.txt"
    target.write_text(message, encoding="utf-8", newline="\n")
    print(f"D followup explicit staging inventory: {len(paths)} paths")
