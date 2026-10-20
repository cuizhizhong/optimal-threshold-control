"""S2.7 核对重跑前后两个正文生成块与块外文字，不替换新结果。"""

import difflib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]


def main():
    before = (HERE / "baseline_main.tex").read_text(encoding="utf-8")
    after = (PROJECT / "latex/main.tex").read_text(encoding="utf-8")
    report = {"step": "S2.7", "blocks": {}, "optimizer_calls": 0}
    for name in ("NUMERICAL REFERENCE VALUES", "NUMERICAL RESULTS"):
        pattern = rf"% BEGIN AUTO-GENERATED {name}.*?% END AUTO-GENERATED {name}"
        old, new = re.findall(pattern, before, re.S), re.findall(pattern, after, re.S)
        assert len(old) == len(new) == 1
        same = old[0] == new[0]
        report["blocks"][name] = {"identical": same,
            "diff": list(difflib.unified_diff(old[0].splitlines(), new[0].splitlines(), lineterm=""))}
        before = re.sub(pattern, f"<BLOCK {name}>", before, flags=re.S)
        after = re.sub(pattern, f"<BLOCK {name}>", after, flags=re.S)
    report["outside_generated_blocks_identical"] = before == after
    report["passed"] = before == after and all(x["identical"] for x in report["blocks"].values())
    output = HERE / "S2.7/macro_comparison_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    assert report["passed"], "停止：正文数值生成块或块外文字发生变化，先报告差异。"


if __name__ == "__main__":
    main()
