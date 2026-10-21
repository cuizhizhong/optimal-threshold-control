"""仅安装 D 正文、证明和已核对的文献条目；可从本批片段更新。"""
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
path = PROJECT / "latex/main.tex"
text = path.read_text(encoding="utf-8")
additions = {
    "MAIN": ((HERE / "d_main.tex").read_text(encoding="utf-8"), r"\ifdefined\TheoryOnly\else" + "\n% 数值章节已内联"),
    "APPENDIX": ((HERE / "d_appendix.tex").read_text(encoding="utf-8"), r"\section{梯度拼接与相对正则性的详细证明}"),
    "ABSTRACT": ("固定传播概率的小容量展开进一步表明，在共同容量入口的初值族下，提前退出的绝对成本节省为 $K^2$ 阶，相对纯容量填充的节省为 $K^3$ 阶。\n", "\\ifdefined\\TheoryOnly\\else\n五个代表初值"),
}
for name, (content, anchor) in additions.items():
    packet = f"% BEGIN D {name}\n{content}% END D {name}\n"
    if f"% BEGIN D {name}\n" in text:
        pattern = rf"% BEGIN D {name}\n.*?% END D {name}\n"
        text, count = re.subn(pattern, lambda _: packet, text, flags=re.S)
        assert count == 1
    else:
        assert text.count(anchor) == 1, (name, anchor)
        text = text.replace(anchor, packet + anchor)
path.write_text(text, encoding="utf-8", newline="\n")
bib = PROJECT / "latex/references.bib"
source = bib.read_text(encoding="utf-8")
if "{He2023TDINN," not in source:
    source += "\n@article{He2023TDINN,\n  author = {He, Mengqi and Tang, Sanyi and Xiao, Yanni},\n  title = {Combining the dynamic model and deep neural networks to identify the intensity of interventions during COVID-19 pandemic},\n  journal = {PLOS Computational Biology},\n  year = {2023},\n  volume = {19},\n  number = {10},\n  pages = {e1011535},\n  doi = {10.1371/journal.pcbi.1011535}\n}\n"
    bib.write_text(source, encoding="utf-8", newline="\n")
print("D source additions installed")
