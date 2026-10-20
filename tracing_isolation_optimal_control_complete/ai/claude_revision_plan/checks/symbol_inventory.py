"""Inventory of math symbols in latex/main.tex (body only, auto-generated blocks excluded).
Collects letter-like tokens with their sub/superscripts, Greek and calligraphic symbols,
and reports count and first line.  Usage: python -I symbol_inventory.py main.tex"""
import re
import sys
import bisect
from collections import OrderedDict

GREEK = ('alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi pi rho '
         'sigma tau upsilon phi varphi chi psi omega Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega ell').split()
MACROS = {'Acal': r'\mathcal A', 'Dcal': r'\mathcal D', 'Gcal': r'\mathcal G', 'Uad': r'\mathcal U_{ad}', 'R': r'\mathbb R'}
SKIP_ARGS = ('label', 'ref', 'eqref', 'text', 'textup', 'mathrm', 'operatorname', 'texttt', 'mbox', 'num', 'begin', 'end',
             'citep', 'citet', 'NumTheoryRef', 'hspace', 'tag')


def math_segments(text):
    body_start = text.index(r'\begin{document}')
    # blank out auto-generated blocks and comments
    t = text
    for a, b in [('% BEGIN AUTO-GENERATED', '% END AUTO-GENERATED')]:
        while a in t:
            i = t.index(a); j = t.index(b, i); j = t.index('\n', j)
            t = t[:i] + ' ' * (j - i) + t[j:]
    t = re.sub(r'(?<!\\)%[^\n]*', lambda m: ' ' * len(m.group(0)), t)
    segs = []
    pat = re.compile(r'\$(.+?)\$|\\\[(.+?)\\\]|\\begin\{(equation\*?|align\*?)\}(.+?)\\end\{\3\}', re.S)
    for m in pat.finditer(t, body_start):
        g = m.group(1) or m.group(2) or m.group(4)
        start = m.start(1) if m.group(1) else (m.start(2) if m.group(2) else m.start(4))
        segs.append((start, g))
    return segs


def tokens(seg):
    k = 0; n = len(seg)
    while k < n:
        ch = seg[k]
        if ch == '\\':
            mm = re.match(r'\\([A-Za-z]+)', seg[k:])
            if not mm:
                k += 2; continue
            name = mm.group(1); k += len(mm.group(0))
            if name in SKIP_ARGS:
                while k < n and seg[k] == ' ': k += 1
                if k < n and seg[k] == '{':
                    d = 0
                    for j in range(k, n):
                        if seg[j] == '{': d += 1
                        elif seg[j] == '}':
                            d -= 1
                            if d == 0: k = j + 1; break
                continue
            if name in ('mathcal', 'mathbb', 'bar', 'hat', 'tilde', 'widehat'):
                while k < n and seg[k] == ' ': k += 1
                arg = seg[k] if k < n else ''
                if arg == '{':
                    e = seg.index('}', k); arg = seg[k + 1:e]; k = e + 1
                else:
                    k += 1
                base = '\\' + name + ' ' + arg
            elif name in GREEK:
                base = '\\' + name
            elif name in MACROS:
                base = MACROS[name]
            else:
                continue
        elif ch.isalpha():
            base = ch; k += 1
        else:
            k += 1; continue
        # attach immediate subscript (one token or braced group)
        sub = ''
        if k < n and seg[k] == '_':
            k += 1
            if k < n and seg[k] == '{':
                d = 0
                for j in range(k, n):
                    if seg[j] == '{': d += 1
                    elif seg[j] == '}':
                        d -= 1
                        if d == 0: sub = seg[k + 1:j]; k = j + 1; break
            elif k < n and seg[k] == '\\':
                mm = re.match(r'\\[A-Za-z]+', seg[k:]); sub = mm.group(0); k += len(mm.group(0))
            elif k < n:
                sub = seg[k]; k += 1
        yield base + ('_{' + sub + '}' if sub else '')


if __name__ == '__main__':
    text = open(sys.argv[1], encoding='utf-8').read()
    starts = [0] + [i + 1 for i, c in enumerate(text) if c == '\n']
    seen = OrderedDict()
    for pos, seg in math_segments(text):
        line = bisect.bisect_right(starts, pos)
        for tok in tokens(seg):
            if tok not in seen:
                seen[tok] = [line, 0]
            seen[tok][1] += 1
    for tok, (line, cnt) in sorted(seen.items(), key=lambda kv: kv[1][0]):
        print(f'{line:5d} {cnt:4d}  {tok}')
