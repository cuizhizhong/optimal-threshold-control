"""Scoped S1 source audit, invoked by symbol_inventory.py --check-s1.

This audit checks names and their intended scopes, not mathematical validity.
The seven accepted decisions assigned to later stages are deliberately excluded.
"""
import re
from collections import OrderedDict


def scope(text, label, proof=False):
    marker = r'\label{' + label + '}'
    start = text.index(marker)
    if proof:
        end = text.index(r'\end{proof}', text.index(r'\begin{proof}', start)) + len(r'\end{proof}')
    else:
        m = re.search(r'\\section\{', text[start + len(marker):])
        end = len(text) if m is None else start + len(marker) + m.start()
    return text[start:end]


def check_s1(text, math_segments, tokens):
    all_tokens = lambda source: [tok for _, seg in math_segments(source, True) for tok in tokens(seg)]
    global_tokens = all_tokens(text)
    regularity = scope(text, 'prop:regularity', True)
    tracking = scope(text, 'lem:tracking-region', True)
    geometry = scope(text, 'prop:Gamma-geometry', True)
    wellposed = scope(text, 'thm:wellposed', True)
    medical = scope(text, 'app:medical-capacity')
    partial = scope(text, 'app:capacity-integral')
    waiting = scope(text, 'lem:waiting-HJB', True)
    trajectory = scope(text, 'lem:trajectory-verification', True)
    time = scope(text, 'sec:time-varying')
    family_start = text.index(r'\subsection{一维切换成本')
    family = text[family_start:text.index(r'\subsection', family_start + 1)]
    local_start = regularity.rfind(r'\[', 0, regularity.index(r'\Xi('))
    local_end = regularity.index('变回原坐标', local_start)
    local_coordinates = regularity[local_start:local_end]
    generated = ''.join(m.group(0) for m in re.finditer(
        r'% BEGIN AUTO-GENERATED[^\n]*\n.*?% END AUTO-GENERATED[^\n]*', text, re.S))
    numerical_start = text.index(r'\label{sec:numerical-method}')
    numerical_end = text.index(r'\label{sec:time-varying}')
    numerical = text[numerical_start:numerical_end] + generated
    compact = lambda source: re.sub(r'\s+|\\(?:bigl|bigr|Bigl|Bigr|left|right)', '', source)

    def renamed(source, old, new=()):
        found = all_tokens(source)
        return not any(tok in found for tok in old) and all(tok in found for tok in new)

    def medical_name(base):
        found = [tok for tok in all_tokens(medical) if tok == base or tok.startswith(base + '_')]
        return bool(found) and all('ICU' in tok for tok in found)

    checks = OrderedDict()
    checks[3] = renamed(tracking, [r'\lambda'], [r'\mu'])
    checks[4] = renamed(text, ['D'], [r'\Delta_{\Theta}']) and medical_name('D')
    checks[7] = renamed(regularity, ['R', 'M_{R}'], [r'\Pi']) and renamed(text, ['R^{q}'], [r'\rho^{q}'])
    checks[8] = renamed(numerical, ['N'], ['n'])
    checks[9] = renamed(numerical, [r'\delta'], [r'\varepsilon_{K}'])
    checks[10] = renamed(text, ['e'], ['s_{e}'])
    checks[11] = renamed(text, ['s_{K}'], ['s_{A}'])
    checks[12] = renamed(wellposed, ['C'], [r'\bar c']) and medical_name('C')
    checks[14] = ('L_{s}' not in all_tokens(geometry)
                  and not re.search(r'(?<![A-Za-z\\])L\s*\(', geometry)
                  and r'\ln\Theta' in compact(geometry) and medical_name('L'))
    checks[15] = (renamed(text, ['Q_{K}'], [r'\mathcal Q_{K}'])
                  and renamed(regularity, ['Q'], [r'\Pi_{0}'])
                  and r'\mathcalQ(t,s,i)' in compact(time) and r'\mathcalQ(t,s,K)' in compact(time)
                  and not re.search(r'(?<![A-Za-z\\])Q\(t,s,[iK]\)', compact(time))
                  and not re.search(r'(?<![A-Za-z\\])Q=\[0,1\]', compact(time)))
    checks[16] = renamed(family, [r'\sigma', 'F_{x_0}'], ['s_{c}', r'\mathcal J_{x_0}'])
    checks[17] = renamed(waiting, [r'\iota']) and any('nat' in tok for tok in all_tokens(waiting))
    checks[18] = (r'\tau' not in all_tokens(wellposed) and 'v' in all_tokens(wellposed)
                  and r'\vartheta' in all_tokens(time) and r'\tau' not in all_tokens(time)
                  and r'\tau_{A}' not in global_tokens
                  and any(tok.startswith(r'\tau_{') and ('Acal' in tok or 'mathcal A' in tok) for tok in global_tokens))
    checks[20] = renamed(text, ['I_{z}', r'I_{\Gamma}'], [r'\mathcal I_{z}', r'\mathcal I_{\Gamma}'])
    checks[21] = (not any(tok.startswith('f_{q}') or tok.startswith('f_{Q^*') for tok in global_tokens)
                  and 'f(x,q)' in compact(text) and r'L_{f(\cdot,q)}' in compact(text)
                  and 'f((s,K),q)' in compact(text) and 'f(x^*(v),Q^*(x^*(v)))' in compact(text)
                  and 'f(x,q)(' not in compact(text))
    checks[22] = r'\epsilon' not in global_tokens and r'\varepsilon' in global_tokens
    checks[24] = renamed(medical, ['a'], [r'\theta']) and r'\kappa(\theta)' in compact(medical)
    checks[25] = renamed(regularity + trajectory, ['b'], ['U_{K}'])
    checks[26] = renamed(partial, ['A', 'B'], ['A_{1}', 'A_{2}'])
    checks[27] = (renamed(local_coordinates, ['P', 'y', 'y_{1}', 'y_{2}'],
                          [r'\mathbf P', r'\zeta', r'\zeta_{1}', r'\zeta_{2}'])
                  and 'y' in all_tokens(regularity[local_end:]))
    for item, result in checks.items():
        print(f'{str(result):5}  S1 #{item}: scoped notation')
    print(f'S1 source checks: {sum(checks.values())}/{len(checks)}')
    print('ALL OK' if all(checks.values()) else 'SOME FAILED')
    return all(checks.values())
