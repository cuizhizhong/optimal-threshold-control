"""S1 专用定点符号迁移；不改历史迁移脚本、非数学文本或数值生成块。

用法：python -I migrate_s1_notation.py latex/main.tex [--write]
默认只报告；--write 才写回。所有作用域均由环境标签/原文锚点确定。
"""
import argparse
from collections import Counter
from pathlib import Path
import re


MATH_ENVS = r'equation\*?|align\*?|gather\*?|multline\*?|displaymath'
ARG_SKIP = {
    'label', 'ref', 'eqref', 'text', 'textup', 'mathrm', 'operatorname',
    'texttt', 'mbox', 'hbox', 'tag', 'num', 'cite', 'citep', 'citet',
    'path', 'url', 'href', 'begin', 'end', 'NumTheoryRef', 'mathbf',
    'textbf', 'emph', 'textit',
}


def group_end(text, start):
    depth = 0
    for pos in range(start, len(text)):
        if pos and text[pos - 1] == '\\':
            continue
        if text[pos] == '{':
            depth += 1
        elif text[pos] == '}':
            depth -= 1
            if not depth:
                return pos + 1
    raise ValueError(f'未闭合组：{start}')


def math_chunks(text):
    """返回原始正文的数学内容范围，跳过注释、代码和自动生成块。"""
    pos = text.index(r'\begin{document}')
    env_re = re.compile(r'\\begin\{(' + MATH_ENVS + r')\}')
    while pos < len(text):
        if text.startswith('% BEGIN AUTO-GENERATED', pos):
            pos = text.index('\n', text.index('% END AUTO-GENERATED', pos))
        elif text.startswith(r'\begin{lstlisting}', pos):
            pos = text.index(r'\end{lstlisting}', pos) + len(r'\end{lstlisting}')
        elif text[pos] == '%':
            end = text.find('\n', pos)
            pos = len(text) if end < 0 else end
        elif text.startswith(r'\[', pos) or text.startswith(r'\(', pos):
            close = r'\]' if text[pos + 1] == '[' else r'\)'
            end = text.index(close, pos + 2)
            yield pos + 2, end
            pos = end + 2
        elif (match := env_re.match(text, pos)):
            close = r'\end{' + match.group(1) + '}'
            end = text.index(close, match.end())
            yield match.end(), end
            pos = end + len(close)
        elif text[pos] == '\\':
            match = re.match(r'\\[A-Za-z]+\*?|\\.', text[pos:])
            pos += len(match.group())
        elif text[pos] == '$':
            end = pos + 1
            while True:
                end = text.index('$', end)
                if text[end - 1] != '\\':
                    break
                end += 1
            yield pos + 1, end
            pos = end + 1
        else:
            pos += 1


def proof_range(text, label):
    start = text.index(r'\begin{proof}', text.index(r'\label{' + label + '}'))
    return start, text.index(r'\end{proof}', start)


def protected_math(text):
    """保护标签、直立字体、文本、数值字面量及其参数。"""
    saved = []

    def save(value):
        saved.append(value)
        return f'\ue000{len(saved) - 1}\ue001'

    out = []
    pos = 0
    while pos < len(text):
        if text[pos] == '%':
            end = text.find('\n', pos)
            end = len(text) if end < 0 else end
            out.append(save(text[pos:end]))
            pos = end
            continue
        match = re.match(r'\\([A-Za-z]+)\*?', text[pos:])
        if match and match.group(1) in ARG_SKIP:
            name = match.group(1)
            end = pos + len(match.group())
            nargs = 2 if name in {'begin', 'NumTheoryRef'} else 1
            for _ in range(nargs):
                while end < len(text) and text[end] == ' ':
                    end += 1
                if end < len(text) and text[end] == '[':
                    end = text.index(']', end) + 1
                if end < len(text) and text[end] == '{':
                    end = group_end(text, end)
                elif name in {'mathrm', 'mathbf'} and end < len(text):
                    end += 1
                else:
                    break
            out.append(save(text[pos:end]))
            pos = end
            continue
        # 旧式直立字体组内的词也不是变量。
        if text.startswith(r'{\rm ', pos):
            end = group_end(text, pos)
            out.append(save(text[pos:end]))
            pos = end
            continue
        out.append(text[pos])
        pos += 1
    return ''.join(out), saved


def migrate(text):
    scopes = {
        name: proof_range(text, label) for name, label in {
            'tracking': 'lem:tracking-region', 'geometry': 'prop:Gamma-geometry',
            'regularity': 'prop:regularity', 'waiting': 'lem:waiting-HJB',
            'trajectory': 'lem:trajectory-verification',
        }.items()
    }
    scopes.update({
        'wellposed': (text.index(r'\label{thm:wellposed}'), text.index(r'\label{lem:ac-level-set}')),
        'residual': (text.index(r'\section{完全跟踪成本'), text.index(r'\section{全局最优性验证}')),
        'verification': (text.index(r'\section{全局最优性验证}'), text.index(r'\subsection{一维切换成本')),
        'one_dim': (text.index(r'\subsection{一维切换成本'), text.index(r'\subsection{从控制到两个传播系数}')),
        'numerical': (text.index(r'\section{数值方法'), text.index(r'\label{sec:time-varying}')),
        'time': (text.index(r'\label{sec:time-varying}'), text.index(r'\section{同时控制接触率')),
        'medical': (text.index(r'\label{app:medical-capacity}'), text.index(r'\label{app:numerical-reproducibility}')),
        'coefficients': (text.index('作部分分式'), text.index(r'\section{证明依赖与校验口径}')),
        'coordinates': (text.index('固定其中一个点'), text.index('变回原坐标')),
    })
    counts = Counter()
    out = []
    previous = 0
    for start, end in math_chunks(text):
        original = text[start:end]
        math, saved = protected_math(original)

        def inside(name):
            low, high = scopes[name]
            return low <= start < high

        def sub(item, pattern, replacement):
            nonlocal math
            math, count = re.subn(pattern, lambda m: replacement(m) if callable(replacement) else replacement, math)
            counts[item] += count

        def literal(item, old, new):
            sub(item, re.escape(old), new)

        def command_to_letters(item, old, new):
            # 控制词后紧接另一个控制词时无需空格；改为字母变量后须补分隔。
            before = math
            sub(item, re.escape(old), lambda m: (' ' if re.search(r'\\[A-Za-z]+$', before[:m.start()]) else '') + new)

        literal('#11', 's_K', 's_A')
        sub('#10', r'(?<![\\A-Za-z_])e(?![A-Za-z])', 's_e')
        sub('#20', r'(?<!\\mathcal )(?<!\\)I_(z|\\Gamma)', lambda m: r'\mathcal I_' + m.group(1))
        literal('#22', r'\epsilon', r'\varepsilon')
        sub('#15', r'(?<!\\mathcal )Q_K', r'\mathcal Q_K')
        literal('#21', r'f_{Q^*(x^*(v))}(x^*(v))', r'f(x^*(v),Q^*(x^*(v)))')
        literal('#21', r'L_{f_q}', r'L_{f(\cdot,q)}')
        literal('#21', r'f_q(s,K)', r'f((s,K),q)')
        literal('#21', r'f_q(x)', r'f(x,q)')
        literal('#21', 'f_q', 'f(x,q)')
        literal('#18', r'\tau_A', r'\tau_{\mathcal A}')

        if inside('wellposed'):
            sub('#12', r'(?<![\\A-Za-z])C', r'\bar c ')
            command_to_letters('#18', r'\tau', 'v')
        if inside('residual'):
            sub('#4', r'(?<![\\A-Za-z_])D(?![A-Za-z])', r'\Delta_\Theta')
        if inside('tracking'):
            literal('#3', r'\lambda', r'\mu')
        if inside('verification'):
            literal('#7', 'R^q', r'\rho^q')
        if inside('geometry'):
            literal('#14', r'L_s(z,\psi)', r'\left.\partial_s\ln\Theta(s,\psi+\ell\ln s)\right|_{s=z}')
            literal('#14', r'L(z(\psi),\psi)', r'\ln\Theta(z(\psi),\psi+\ell\ln z(\psi))')
            literal('#14', r'L(s,\psi)', r'\ln\Theta(s,\psi+\ell\ln s)')
            if r'F(s,\psi)=' in math and r'\qquad' in math:
                literal('#14-layout', r'\ln\Theta(s,\psi+\ell\ln s)=', r'\ln\Theta(s,\psi+\ell\ln s)&=')
                literal('#14-layout', r',\qquad', r',\\')
                literal('#14-layout', r'F(s,\psi)=', r'F(s,\psi)&=')
                math = '\n' + r'\begin{aligned}' + math + r'\end{aligned}' + '\n'
        if inside('regularity'):
            sub('#7', r'(?<![\\A-Za-z])R(?![A-Za-z])', r'\Pi')
            sub('#15', r'(?<![\\A-Za-z])Q(?![A-Za-z])', r'\Pi_0')
        if inside('coordinates'):
            sub('#27', r'(?<![\\A-Za-z])P(?![A-Za-z])', r'\mathbf P')
            sub('#27', r'(?<![\\A-Za-z])y(?![A-Za-z])', r'\zeta')
            literal('#27', 'ty', r't\zeta')
        if inside('regularity') or inside('trajectory'):
            sub('#25', r'(?<![\\A-Za-z])b(?![A-Za-z])', 'U_K')
        if inside('one_dim'):
            # 单控制词分母改为带下标变量时，必须补组，保持分式的取参范围。
            literal('#16', r'\frac \beta\sigma', r'\frac{\beta}{s_c}')
            command_to_letters('#16', r'\sigma', 's_c')
            literal('#16', 'F_{x_0}', r'\mathcal J_{x_0}')
        if inside('waiting'):
            literal('#17', r'\iota', r'i_{\rm nat}')
        if inside('numerical'):
            sub('#8', r'(?<![\\A-Za-z])N(?![A-Za-z])', 'n')
            sub('#9', r'\\delta(?![A-Za-z_])', r'\varepsilon_K')
        if inside('time'):
            literal('#18', r'\tau', r'\vartheta')
            sub('#15', r'(?<!\\mathcal )Q(?=\(t,s,|=\[0,1\])', r'\mathcal Q')
        if inside('coefficients'):
            sub('#26', r'(?<![\\A-Za-z_])A(?!_)', 'A_1')
            sub('#26', r'(?<![\\A-Za-z_])B(?!_)', 'A_2')
        if inside('medical'):
            # 旧的直立 init 被保护为一个占位符，按原文精确替换后恢复。
            for index, value in enumerate(saved):
                if value == r'\mathrm{init}':
                    literal('#4', 'D_{' + f'\ue000{index}\ue001' + '}', r'D_{\mathrm{ICU,init}}')
            literal('#4', 'D_0', r'D_{{\rm ICU},0}')
            sub('#4', r'(?<![\\A-Za-z_])D(?=\()', r'D_{\rm ICU}')
            sub('#12', r'(?<![\\A-Za-z])C(?![A-Za-z_])', r'C_{\rm ICU}')
            sub('#14', r'(?<![\\A-Za-z])L(?![A-Za-z_])', r'L_{\rm ICU}')
            sub('#24', r'(?<![\\A-Za-z])a(?![A-Za-z])', r'\theta')
        math = re.sub('\ue000([0-9]+)\ue001', lambda m: saved[int(m.group(1))], math)
        out.extend((text[previous:start], math))
        previous = end
    out.append(text[previous:])
    migrated = ''.join(out)
    # 非数学正文、注释、代码、标签及自动生成块的原始字节保持不变。
    def skeleton(source):
        pieces = []
        last = 0
        for low, high in math_chunks(source):
            pieces.extend((source[last:low], '<MATH>'))
            last = high
        pieces.append(source[last:])
        return ''.join(pieces)
    if skeleton(text) != skeleton(migrated):
        raise AssertionError('数学模式外内容发生变化')
    return migrated, {key: value for key, value in counts.items() if value}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    with args.path.open(encoding='utf-8', newline='') as handle:
        source = handle.read()
    result, report = migrate(source)
    print('replacements:', report)
    print('non_math_unchanged:', True)
    if args.write:
        with args.path.open('w', encoding='utf-8', newline='') as handle:
            handle.write(result)
        print('written:', args.path)
