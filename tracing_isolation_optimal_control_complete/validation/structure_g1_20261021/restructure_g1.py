"""从指定基准按段移动 G1 正文；不调用任何数值程序。"""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / 'tracing_isolation_optimal_control_complete'
MAIN = PROJECT / 'latex/main.tex'
BASE = '689a627'
REL = MAIN.relative_to(ROOT).as_posix()


def unwrap_theory(text):
    # 只移除 TheoryOnly 分支壳；保留其中嵌套的数值条件。
    pattern = re.compile(r'\\ifdefined\\TheoryOnly|\\if[A-Za-z]+|\\else\b|\\fi\b')
    while (m := re.search(r'\\ifdefined\\TheoryOnly', text)):
        depth, otherwise, end = 0, None, None
        for token in pattern.finditer(text, m.start()):
            s = token.group()
            if s.startswith('\\if'):
                depth += 1
            elif s == r'\else' and depth == 1:
                otherwise = token
            elif s == r'\fi':
                depth -= 1
                if depth == 0:
                    end = token
                    break
        assert end
        kept = text[otherwise.end():end.start()] if otherwise else ''
        text = text[:m.start()] + kept + text[end.end():]
    return text


def demote(text):
    return re.sub(r'\\(section|subsection)\{',
                  lambda m: '\\' + {'section': 'subsection', 'subsection': 'subsubsection'}[m[1]] + '{', text)


def header(title, label, intro='', marker=''):
    return '\\section{' + title + '}\n\\label{' + label + '}\n\n' + (('% ' + marker + '\n') if marker else '') + intro + '\n\n'


def main():
    old = subprocess.check_output(['git', 'show', f'{BASE}:{REL}'], cwd=ROOT).decode('utf-8')
    old = old.replace('\r\n', '\n')
    text = '\n'.join(line for line in old.split('\n') if not (line.startswith('%') and 'TheoryOnly' in line))
    text = unwrap_theory(text)
    starts = list(re.finditer(r'^\\section\{', text, re.M))
    preamble = text[:starts[0].start()]
    blocks = [text[m.start():(starts[n+1].start() if n+1 < len(starts) else len(text))] for n, m in enumerate(starts)]
    assert len(blocks) == 29, len(blocks)
    # 原正文 22 节，附录 7 节；由 label 而非旧节号选择。
    def block(label):
        return next(b for b in blocks if '\\label{' + label + '}' in b[:250])
    def replace_block(label, value):
        idx = blocks.index(block(label))
        blocks[idx] = value

    scope = block('sec:main-results').replace(
        '本节及第\\ref{sec:constant-problem}--\\ref{sec:constant-uniqueness}节固定',
        '预备结果中的适定性定理\\ref{thm:wellposed}对一般 $c(t)$ 成立。\n第\\ref{sec:main-results}--\\ref{sec:mechanisms}节固定')
    replace_block('sec:main-results', scope)

    synthesis = block('sec:synthesis')
    pos = synthesis.index('\\label{lem:tracking-region}')
    start = synthesis.index('\\begin{proof}', pos)
    stop = synthesis.index('\\end{proof}', start) + len('\\end{proof}')
    proof = synthesis[start:stop]
    sketch = (r'% G1-TRACKING-PROOF-SKETCH' + '\n'
        r'证明先由同一自然轨道上的不变量比较确定完全跟踪可达性，再以单峰性刻画 $\Delta_\Theta$ 的零集及其在切换点附近的符号。' + '\n'
        r'结合严格横穿和分区关系，可知完全跟踪弧在到达安全集前不再返回等待区；正安全端点给出有限到达时间。' + '\n'
        r'完整证明见附录 \ref{app:tracking-region-proof}。')
    replace_block('sec:synthesis', synthesis[:start] + sketch + synthesis[stop:])

    unique = block('sec:constant-uniqueness')
    p = unique.index('\\begin{proof}', unique.index('\\label{thm:unique-q}')) + len('\\begin{proof}')
    roadmap = ('\n% G1-UNIQUENESS-ROADMAP\n'
        r'证明先用推论\ref{cor:verification-equality}的等号条件及引理\ref{lem:waiting-HJB}、命题\ref{prop:all-HJB}确定各分区内的控制。' + '\n'
        r'随后由引理\ref{lem:no-early-boundary-exit}确定容量弧上的延续，再用引理\ref{lem:strict-crossing}和引理\ref{lem:chi-regions}处理切换曲线。' + '\n'
        r'最后结合命题\ref{prop:candidate-attainment}、引理\ref{lem:tracking-region}及各段状态方程解的唯一性，依次确定全部阶段和安全延拓。' + '\n')
    unique = unique[:p] + roadmap + '\n' + unique[p:]
    for n, title in enumerate(['各分区内的控制选择。', '容量弧上的延续。', '切换曲线上的行为。', '各阶段轨道的唯一确定。'], 1):
        unique = unique.replace('\\emph{' + title + '}', '\\emph{第 ' + str(n) + ' 步：' + title + '}')
    split = unique.index('\\subsection{一维切换成本与全局结论的关系}')
    unique_body, one_d = unique[:split], unique[split:]

    # 原第 12 节在两个新章间分开，保留原标签在第一个子节。
    gradients = block('sec:verification-details')
    gradients = gradients.replace('\\section{全域梯度、拼接正则性与验证不等式}\n\\label{sec:verification-details}\n', '')
    gradients = gradients.replace('\\subsection{两种等待分支的统一导数}', '\\subsection{两种等待分支的统一导数}\n\\label{sec:verification-details}')
    split = gradients.index('\\subsection{容量 Hamiltonian 与沿任意轨道的链式法则}')
    gradient_body, verification_part = gradients[:split], gradients[split:]

    # 生成块整体移至数值章开头，其内部字节不变。
    scaling = block('sec:scaling')
    split = scaling.index('% 数值章节已内联')
    numeric_macros, scaling = scaling[split:], scaling[:split]

    conclusions = block('sec:conclusions')
    conclusions = conclusions[:conclusions.index('时变接触率仅保留条件性的验证与唯一性讨论。')]
    conclusions = conclusions.replace('\\section{主要结论}', '\\section{结论}').rstrip() + '\n\n\\appendix\n'

    prelim_intro = (
        r'本节先建立状态正性和耗散、安全集及两类控制弧，再证明有限成本轨道入安全集，并给出后文使用的 HJB 边界条件。' + '\n'
        r'后续构造先处理完全跟踪可达域和成本、切换曲线几何、全域候选及达到性与梯度拼接，再沿任意轨道验证全局最优性；推论\ref{cor:one-dimensional-min}在全局验证之后陈述，不用候选策略族内的极小性替代全控制类比较。' + '\n'
        r'全局最优性确立后，推论\ref{cor:verification-equality}由沿轨道验证不等式积分得到最优控制的等号条件，引理\ref{lem:no-early-boundary-exit}据此证明容量弧上的延续性质，再由定理\ref{thm:unique-q}完成控制与状态轨道的唯一性证明；上述推论和引理均不依赖定理\ref{thm:unique-q}。' + '\n'
        r'具体地，端点存在性由命题\ref{prop:reachable}及引理\ref{lem:tracking-region}处理，曲线正则性和横截性由命题\ref{prop:Gamma-geometry}、推论\ref{cor:Gamma-labels}处理，不滑行由引理\ref{lem:strict-crossing}处理，横穿方向与实际分区的衔接由引理\ref{lem:chi-regions}处理；容量和安全时间集合上的导数关系统一使用式\eqref{eq:ac-level-set}的水平集性质，局部 Lipschitz 性和终端处理分别由命题\ref{prop:regularity}及引理\ref{lem:finite-entry}证明。')
    construction_intro = (
        r'本节从完全跟踪成本的有限可达域出发，依次构造切换曲线、全域候选反馈和候选成本。' + '\n'
        r'随后计算等待分支的梯度并处理拼接正则性，为第\ref{sec:optimality}节沿任意可行轨道的验证准备候选函数。')
    optimality_intro = (
        r'本节利用前节候选函数的梯度和正则性，先建立各分区的 Hamiltonian 关系及沿任意轨道的验证不等式。' + '\n'
        r'再结合有限成本入安全集性质证明全局最优性，并用验证等号条件、容量弧延续和切换曲线横穿逐段确定最优轨道，完成唯一性证明。')

    medical = block('app:medical-capacity')
    supplement = block('app:numerical-reproducibility')
    out = preamble + ''.join(block(x) for x in ['sec:introduction', 'sec:model', 'sec:main-results'])
    out += header('预备结果', 'sec:preliminaries', prelim_intro, 'G1-INTRO-PRELIMINARIES')
    out += ''.join(demote(block(x)) for x in ['sec:wellposed', 'sec:constant-problem', 'sec:arcs', 'sec:exit-time', 'sec:HJB'])
    out += header('候选策略的构造', 'sec:candidate-construction', construction_intro, 'G1-INTRO-CONSTRUCTION')
    out += ''.join(demote(block(x)) for x in ['sec:q1-value', 'sec:switching-curve', 'sec:synthesis']) + gradient_body
    out += header('全局最优性与唯一性', 'sec:optimality', optimality_intro, 'G1-INTRO-VERIFICATION')
    out += verification_part + demote(block('sec:global-verification')) + demote(unique_body)
    out += header('机制与量级', 'sec:mechanisms') + one_d + demote(block('sec:switching-mechanism')) + demote(scaling)
    out += header('数值结果', 'sec:numerics') + numeric_macros + demote(block('sec:numerical-method')) + demote(block('sec:numerical-results'))
    joint = next(b for b in blocks if b.startswith('\\section{同时控制'))
    out += header('讨论', 'sec:discussion') + demote(joint) + demote(block('sec:limitations')) + conclusions
    out += block('app:W-derivatives') + block('app:capacity-integral')
    out += header('完全跟踪分区可达性与不再返回等待区的证明', 'app:tracking-region-proof') + proof + '\n\n'
    out += block('app:regularity-proof') + block('app:small-capacity-proof') + medical + supplement
    assert 'TheoryOnly' not in out
    assert 'sec:time-varying' not in out and 'app:proof-scope' not in out
    MAIN.write_text(out, encoding='utf-8', newline='\n')
    for name in ['theory_only.tex', 'theory_only.pdf']:
        (PROJECT / 'latex' / name).unlink()
    print('G1 重排完成；TheoryOnly 两个指定文件已删除。')


if __name__ == '__main__':
    main()
