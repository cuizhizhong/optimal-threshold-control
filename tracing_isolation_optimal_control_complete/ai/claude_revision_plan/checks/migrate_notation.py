"""Paper-layer notation migration for latex/main.tex (code is NOT renamed).

In math mode only, in a single simultaneous pass:
  probability  p   -> \\beta
  geometric    r   -> p
  trajectory subscripts  x_q, s_q, i_q, R_q, \\tau_q  -> x^q, s^q, i^q, R^q, \\tau^q
Skipped: preamble, comments, AUTO-GENERATED blocks, lstlisting, arguments of label/ref/text/mathrm/...,
and letters following \\rm inside a group.  Usage:  python -I migrate_notation.py main.tex [--write]
"""
import re
import sys

ARG_SKIP = {'label', 'ref', 'eqref', 'text', 'textup', 'mathrm', 'operatorname', 'texttt', 'mbox', 'hbox',
            'tag', 'num', 'cite', 'citep', 'citet', 'path', 'url', 'href', 'begin', 'end', 'NumTheoryRef',
            'mathbf', 'textbf', 'emph', 'textit'}
MATH_ENVS = ('equation', 'equation*', 'align', 'align*', 'gather', 'gather*', 'multline', 'multline*', 'displaymath')


def read_group(s, k):
    """s[k] == '{' ; return index after the matching '}'."""
    depth = 0
    for j in range(k, len(s)):
        if s[j] == '\\':
            continue
        if s[j] == '{' and (j == 0 or s[j - 1] != '\\'):
            depth += 1
        elif s[j] == '}' and (j == 0 or s[j - 1] != '\\'):
            depth -= 1
            if depth == 0:
                return j + 1
    raise ValueError('unbalanced group at %d' % k)


def convert_math(m, report, line_of):
    out = []; k = 0; n = len(m); rm_depth = None; depth = 0
    while k < n:
        ch = m[k]
        if ch == '\\':
            mm = re.match(r'\\([A-Za-z]+)\*?', m[k:])
            if mm:
                name = mm.group(1); out.append(mm.group(0)); k += len(mm.group(0))
                if name == 'rm':
                    rm_depth = depth
                if name in ARG_SKIP:
                    # copy optional [..] and up to two brace args verbatim (begin{array}{cols})
                    nargs = 2 if name in ('begin', 'NumTheoryRef') else 1
                    for _ in range(nargs):
                        while k < n and m[k] == ' ':
                            out.append(m[k]); k += 1
                        if k < n and m[k] == '[':
                            e = m.index(']', k) + 1; out.append(m[k:e]); k = e
                        if k < n and m[k] == '{':
                            e = read_group(m, k); out.append(m[k:e]); k = e
                        elif name in ('mathrm', 'text') and k < n:
                            out.append(m[k]); k += 1  # \mathrm d
                        else:
                            break
                        if name != 'begin' or not m[k - 1 - len(''):k].endswith('}'):
                            pass
                    continue
                if name == 'tau' and m[k:k + 2] == '_q':
                    out.append('^q'); k += 2; report.append(('tau_q', line_of(k))); continue
                continue
            out.append(m[k:k + 2]); k += 2; continue  # control symbol
        if ch == '{':
            depth += 1
        elif ch == '}':
            if rm_depth is not None and depth == rm_depth:
                rm_depth = None
            depth -= 1
        if rm_depth is not None and ch.isalpha():
            out.append(ch); k += 1; continue
        if ch in 'xsiR' and m[k + 1:k + 3] == '_q' and not (k + 3 < n and m[k + 3].isalpha()):
            out.append(ch + '^q'); k += 3; report.append((ch + '_q', line_of(k))); continue
        if ch == 'p':
            nxt = m[k + 1] if k + 1 < n else ''
            out.append('\\beta' + (' ' if nxt.isalpha() else '')); k += 1; report.append(('p', line_of(k))); continue
        if ch == 'r':
            out.append('p'); k += 1; report.append(('r', line_of(k))); continue
        out.append(ch); k += 1
    return ''.join(out)


def migrate(text):
    report = []
    begin = text.index('\\begin{document}')
    line_starts = [0] + [i + 1 for i, c in enumerate(text) if c == '\n']
    import bisect
    def line_of_abs(pos):
        return bisect.bisect_right(line_starts, pos)
    out = [text[:begin]]; k = begin; n = len(text)
    env_re = re.compile(r'\\begin\{(' + '|'.join(re.escape(e) for e in MATH_ENVS) + r')\}')
    while k < n:
        if text.startswith('% BEGIN AUTO-GENERATED', k):
            e = text.index('% END AUTO-GENERATED', k); e = text.index('\n', e); out.append(text[k:e]); k = e; continue
        if text.startswith('\\begin{lstlisting}', k):
            e = text.index('\\end{lstlisting}', k) + len('\\end{lstlisting}'); out.append(text[k:e]); k = e; continue
        ch = text[k]
        if ch == '%' and (k == 0 or text[k - 1] != '\\'):
            e = text.find('\n', k); e = n if e < 0 else e; out.append(text[k:e]); k = e; continue
        if ch == '\\' and text.startswith('\\[', k):
            e = text.index('\\]', k); seg = text[k + 2:e]
            out.append('\\[' + convert_math(seg, report, lambda j, b=k + 2: line_of_abs(b + j)) + '\\]'); k = e + 2; continue
        if ch == '\\' and text.startswith('\\(', k):
            e = text.index('\\)', k); seg = text[k + 2:e]
            out.append('\\(' + convert_math(seg, report, lambda j, b=k + 2: line_of_abs(b + j)) + '\\)'); k = e + 2; continue
        mm = env_re.match(text, k)
        if mm:
            env = mm.group(1); endtag = '\\end{%s}' % env; e = text.index(endtag, k)
            seg = text[mm.end():e]
            out.append(mm.group(0) + convert_math(seg, report, lambda j, b=mm.end(): line_of_abs(b + j)) + endtag)
            k = e + len(endtag); continue
        if ch == '\\':
            mm = re.match(r'\\[A-Za-z]+\*?|\\.', text[k:]); out.append(mm.group(0)); k += len(mm.group(0)); continue
        if ch == '$':
            e = k + 1
            while True:
                e = text.index('$', e)
                if text[e - 1] != '\\':
                    break
                e += 1
            seg = text[k + 1:e]
            out.append('$' + convert_math(seg, report, lambda j, b=k + 1: line_of_abs(b + j)) + '$'); k = e + 1; continue
        out.append(ch); k += 1
    return ''.join(out), report


if __name__ == '__main__':
    path = sys.argv[1]
    text = open(path, encoding='utf-8').read()
    new, report = migrate(text)
    from collections import Counter
    print('replacements:', dict(Counter(r[0] for r in report)))
    lines = sorted(set(r[1] for r in report))
    print('lines touched:', len(lines), 'first..last:', lines[:3], '...', lines[-3:])
    if '--write' in sys.argv:
        open(path, 'w', encoding='utf-8', newline='').write(new)
        print('written')
    else:
        open(path + '.migrated', 'w', encoding='utf-8', newline='').write(new)
        print('dry run written to', path + '.migrated')
