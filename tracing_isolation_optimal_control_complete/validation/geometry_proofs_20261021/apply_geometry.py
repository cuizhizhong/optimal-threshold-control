"""一次性集成 C1--C4；只调整计划指定的结构、可行性和机制说明。"""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
BASE = "e86ec62094f72c2aa56c05191c0ecaf5166d3cf6"
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT).decode().strip() == BASE
target = PROJECT / "latex/main.tex"
text = target.read_text(encoding="utf-8")
old = subprocess.check_output(["git", "show", f"{BASE}:{PROJECT.name}/latex/main.tex"], cwd=PROJECT).decode()
assert text == old, "C 集成前主文必须与 B 修订提交相同"

# 将常系数、物理域及未来峰值提前，原位置保留动力学推导。
cs = text.index("从本节至第\\ref{sec:constant-uniqueness}节固定")
ce = text.index("此处的下确界没有预先限制", cs)
constants = text[cs:ce]
text = text[:cs] + "本节沿用式\\eqref{eq:constants}的参数与式\\eqref{eq:value-definition}的物理域。\n" + text[ce:]
ps = text.index("因而对 $s>0$、$i>0$，无控制的未来感染峰值为")
pe = text.index(r"\subsection{安全集与目标边界}", ps)
peak = text[ps:pe].replace("因而对", "对", 1)
text = text[:ps] + "由上述自然轨道可得概览中的未来峰值公式\\eqref{eq:uncontrolled-future-peak}。\n\n" + text[pe:]
overview = (HERE / "main_results_template.tex").read_text(encoding="utf-8")
overview = overview.replace("__CONSTANTS__", constants).replace("__PEAK__", peak)
overview = overview.replace("sec:candidate", "sec:synthesis")
text = text.replace(r"\section{解的适定性、正性与基本耗散}", overview + "\n" + r"\section{解的适定性、正性与基本耗散}", 1)

# 标准事实由教材引用支撑，保留后续容量时间集的专门论证。
start = text.index(r"\begin{lemma}[绝对连续函数的水平集性质]")
end = text.index(r"\section{常接触率问题、自然轨道与安全目标集}", start)
text = text[:start] + (HERE / "standard_analysis.tex").read_text(encoding="utf-8") + "\n" + text[end:]
text = text.replace(r"引理\ref{lem:ac-level-set}", "绝对连续函数的水平集性质")
text = text.replace(r"引理\ref{lem:ac-composition}", "Lipschitz 复合的绝对连续性")

# 受限能力命题紧随安全集分析，先于成本最优分区。
restricted = (HERE / "c3_feasibility.tex").read_text(encoding="utf-8")
restricted = restricted[restricted.index(r"\subsection{受限跟踪能力与可行域}"):]
a = restricted.index("给定跟踪能力上限")
b = restricted.index("当 $0\\le\\bar q<1$ 时，定义", a)
restricted = restricted[:a] + "对概览中定义的 $\\mathcal V_{\\bar q}$，以下只判定约束可行性，不比较可行策略的成本。\n" + restricted[b:]
text = text.replace(r"\section{两类控制弧与显式成本}", restricted + "\n" + r"\section{两类控制弧与显式成本}", 1)
text = text.replace("从 $\\widehat{\\Acal}$ 出发的任意 $[0,1]$ 值控制均保持在 $\\widehat{\\Acal}$；在物理域中相应保持在 $\\Acal$。",
                    "从 $\\widehat{\\Acal}$ 出发的任意 $[0,1]$ 值可测控制均保持在 $\\widehat{\\Acal}$；在物理域中相应保持在 $\\Acal$。\n此外，$\\mathcal A^0=\\Acal=\\mathcal V_0$，且 $\\mathcal V_1=\\Dcal$。")
text = text.replace("物理总量约束由 \\eqref{eq:sum-decay} 保持。\n\\end{proof}",
                    "物理总量约束由 \\eqref{eq:sum-decay} 保持。\n这给出 $\\Acal\\subset\\mathcal A^0$；反向包含由零控制属于所有允许控制之一得到，且 $\\mathcal V_0=\\Acal$。\n恒取 $q=1$ 时 $i(t)=i_0\\e^{-\\gamma t}\\le K$，故 $\\mathcal V_1=\\Dcal$。\n\\end{proof}", 1)

# 完整移动正则性长证明，避免切开梯度匹配与边界处理的依赖。
label = text.index(r"\label{prop:regularity}")
rs = text.index(r"\begin{proof}", label)
re = text.index(r"\end{proof}", rs) + len(r"\end{proof}")
regularity_proof = text[rs:re]
brief = ("\\begin{proof}\n各光滑分支的导数由式\\eqref{eq:waiting-gradient}和式\\eqref{eq:Ws}--\\eqref{eq:Wi}给出。\n"
         "先核对内部界面的函数值与梯度匹配，再处理安全边界连续性和容量内侧迹；\n"
         "正感染紧邻域上的一致梯度界给出相对局部 Lipschitz 性。\n"
         "完整拼接与边界计算移至附录\\ref{app:regularity-proof}。\n\\end{proof}")
text = text[:rs] + brief + text[re:]
appendix = ("\\section{梯度拼接与相对正则性的详细证明}\n\\label{app:regularity-proof}\n"
            "本附录给出命题\\ref{prop:regularity}的完整证明，所用分区与候选成本均已在正文定义。\n" + regularity_proof + "\n\n")
text = text.replace(r"\section{证明依赖与校验口径}", appendix + r"\section{证明依赖与校验口径}", 1)

# 机制说明置于理论综合之后，两份编译均保留。
text = text.replace(r"\ifdefined\TheoryOnly\else" + "\n% 数值章节已内联",
                    (HERE / "mechanism.tex").read_text(encoding="utf-8") + "\n" + r"\ifdefined\TheoryOnly\else" + "\n% 数值章节已内联", 1)
assert r"\label{sec:switching-mechanism}" in text, "机制节插入点必须匹配"

# C 已给出可行域，不扩大到受限能力最优综合。
text = text.replace("$\\bar q<1$、完全跟踪后残余感染生成、隔离者回流、联合控制以及参数不确定的情形需重新建立可行域和验证函数。",
                    "受限能力 $\\bar q<1$ 的可行域已由命题\\ref{prop:restricted-feasibility}给出，其成本最优反馈和验证函数尚未构造。\n完全跟踪后残余感染生成、隔离者回流、联合控制以及参数不确定的情形仍需另行建立可行域和验证函数。")

# 统一使用前置主定理，避免贡献段变成证明清单。
old_contribution = ("命题\\ref{prop:Gamma-geometry}、推论\\ref{cor:Gamma-labels}和引理\\ref{lem:strict-crossing}\n"
                    "给出非平凡切换曲线的单调性、唯一容量交点和界面横穿性质；\n"
                    "推论\\ref{cor:optimal-synthesis}据此确定不安全初值的两类阶段结构\n")
new_contribution = ("定理\\ref{thm:main-overview}给出全域最优反馈及其阶段结构；非平凡切换曲线的单调性、唯一容量交点和横穿性质见第\\ref{sec:switching-curve}节。\n"
                    "不安全初值对应两类阶段结构\n")
assert old_contribution in text
text = text.replace(old_contribution, new_contribution, 1)

# 数值节不重复原单层相图，保留原图和原provenance文件供历史追溯。
fs = text.index("\\begin{figure}[H]\n\\centering\n\\NumFigureOrBlank{FigN1_regions.pdf}")
fe = text.index(r"\end{figure}", fs) + len(r"\end{figure}")
text = text[:fs] + "代表初值与成本分区的关系参照图\\ref{fig:two-layer-regions}；本节使用表\\ref{tab:numerical-scenarios}核对各例的阶段与成本。\n" + text[fe:]

text = text.replace("图\\ref{fig:numerical-regions}用同一相平面标记初值、区域和相应轨道。",
                    "图\\ref{fig:two-layer-regions}给出各例所属成本分区的理论几何。")
text = text.replace("绝对连续函数的水平集性质的零水平集性质", "绝对连续函数的零水平集性质")
text = text.replace("绝对连续函数的水平集性质的第二条", "两个绝对连续函数在可测集合上相等时的导数性质")
text = text.replace("上述复合引理", "上述复合性质")
text = text.replace("检查区间内部的容量峰值、与配点状态的偏差以及终端零控制延拓。\n终端延拓检查使用第\\ref{sec:constant-problem}节式",
                    "检查区间内部的容量峰值、与配点状态的偏差以及终端零控制延拓。\n\n终端延拓检查使用式")

target.write_text(text, encoding="utf-8", newline="\n")
bib = PROJECT / "latex/references.bib"
with bib.open("a", encoding="utf-8", newline="\n") as handle:
    handle.write("\n@book{Fremlin2001Volume2,\n"
                 "  author = {David H. Fremlin},\n"
                 "  title = {Measure Theory, Volume 2: Broad Foundations},\n"
                 "  publisher = {Torres Fremlin},\n"
                 "  address = {Colchester},\n"
                 "  year = {2001},\n"
                 "  url = {https://www1.essex.ac.uk/maths/people/fremlin/mt.htm}\n}\n")
(HERE / "content_movement.json").write_text(json.dumps({
    "base_commit": BASE,
    "regularity_proof_sha256_before": hashlib.sha256(regularity_proof.encode()).hexdigest(),
    "regularity_proof_moved_verbatim": regularity_proof in text,
    "old_main_sha256": hashlib.sha256(old.encode()).hexdigest(),
    "new_main_sha256": hashlib.sha256(text.encode()).hexdigest(),
    "optimizer_calls": 0, "ocp_solves": 0}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("C1--C4 integrated; regularity proof moved verbatim")
