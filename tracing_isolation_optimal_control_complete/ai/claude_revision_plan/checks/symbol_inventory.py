"""Inventory of math symbols in latex/main.tex (body only, auto-generated blocks excluded).
Collects letter-like tokens with their sub/superscripts, Greek and calligraphic symbols,
and reports count and first line.  Usage: python -I symbol_inventory.py main.tex [--check-s1]
The S1 audit includes generated blocks and checks the 20 scoped decisions;
it complements the algebra checks and is not a proof checker."""
import re
import sys
import bisect
from pathlib import Path
import runpy
from collections import OrderedDict

GREEK = ('alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi pi rho '
         'sigma tau upsilon phi varphi chi psi omega Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega ell').split()
MACROS = {'Acal': r'\mathcal A', 'Dcal': r'\mathcal D', 'Gcal': r'\mathcal G', 'Uad': r'\mathcal U_{ad}', 'R': r'\mathbb R'}
SKIP_ARGS = ('label', 'ref', 'eqref', 'text', 'textup', 'mathrm', 'operatorname', 'texttt', 'mbox', 'num', 'begin', 'end',
             'citep', 'citet', 'NumTheoryRef', 'hspace', 'tag')


def math_segments(text, include_generated=False):
    body_start = text.find(r'\begin{document}')
    body_start = max(body_start, 0)
    # blank out auto-generated blocks and comments
    t = text
    blank = lambda m: re.sub(r'[^\n]', ' ', m.group(0))
    if not include_generated:
        t = re.sub(r'% BEGIN AUTO-GENERATED[^\n]*\n.*?% END AUTO-GENERATED[^\n]*', blank, t, flags=re.S)
    t = re.sub(r'\\begin\{lstlisting\}.*?\\end\{lstlisting\}', blank, t, flags=re.S)
    t = re.sub(r'(?<!\\)%[^\n]*', lambda m: ' ' * len(m.group(0)), t)
    segs = []
    pat = re.compile(r'(?<!\\)\$(.+?)(?<!\\)\$|\\\[(.+?)\\\]|\\\((.+?)\\\)|'
                     r'\\begin\{(equation\*?|align\*?|gather\*?|multline\*?|displaymath)\}(.+?)\\end\{\4\}', re.S)
    for m in pat.finditer(t, body_start):
        group = next(g for g in (1, 2, 3, 5) if m.group(g) is not None)
        segs.append((m.start(group), m.group(group)))
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
                elif name == 'mathrm' and k < n:
                    # TeX also permits the unbraced form \mathrm D.
                    mm = re.match(r'\\[A-Za-z]+|.', seg[k:])
                    k += len(mm.group(0))
                continue
            if name in ('mathcal', 'mathbb', 'mathbf', 'bm', 'bar', 'hat', 'tilde', 'widehat'):
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
        # Attach subscript and superscript; keep q in rho^q distinguishable.
        scripts = {}
        while k < n and seg[k] in '_^':
            kind = seg[k]
            k += 1
            if k < n and seg[k] == '{':
                d = 0
                for j in range(k, n):
                    if seg[j] == '{': d += 1
                    elif seg[j] == '}':
                        d -= 1
                        if d == 0: scripts[kind] = seg[k + 1:j]; k = j + 1; break
            elif k < n and seg[k] == '\\':
                mm = re.match(r'\\[A-Za-z]+|\\.', seg[k:]); scripts[kind] = mm.group(0); k += len(mm.group(0))
            elif k < n:
                scripts[kind] = seg[k]; k += 1
        yield base + ''.join(kind + '{' + scripts[kind] + '}' for kind in '_^' if kind in scripts)


if __name__ == '__main__':
    text = open(sys.argv[1], encoding='utf-8').read()
    if '--check-s1' in sys.argv[2:]:
        audit = runpy.run_path(str(Path(__file__).with_name('s1_source_audit.py')))
        raise SystemExit(0 if audit['check_s1'](text, math_segments, tokens) else 1)
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
