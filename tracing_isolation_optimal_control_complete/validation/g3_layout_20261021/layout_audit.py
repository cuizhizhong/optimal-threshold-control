"""Audit stage G2: mathematics and numbers unchanged except the planned removals.

Usage: python g2_audit.py <old main.tex> <new main.tex> <report.json>
"""
import json
import re
import sys
from collections import Counter

old_path, new_path, report_path = sys.argv[1:4]
old = open(old_path, encoding='utf-8').read()
new = open(new_path, encoding='utf-8').read()


def norm(x):
    return re.sub(r'\s+', ' ', x).strip()


def strip_comments(t):
    return '\n'.join(l for l in t.split('\n') if not l.lstrip().startswith('%'))


ENV = r'\\begin\{(%s)\}(\[[^\]]*\])?(.*?)\\end\{\1\}'


def by_label(t, names):
    out = {}
    for m in re.finditer(ENV % names, t, re.S):
        body = norm(m.group(3))
        for lab in re.findall(r'\\label\{([^}]*)\}', body):
            out[lab] = body
    return out


def unlabelled(t):
    items = [norm(m.group(3)) for m in re.finditer(ENV % r'equation\*?|align\*?', t, re.S) if '\\label' not in m.group(3)]
    items += [norm(m.group(1)) for m in re.finditer(r'\\\[(.*?)\\\]', t, re.S)]
    return Counter(items)


def proofs(t):
    out = {}
    pat = re.compile(r'\\begin\{(theorem|lemma|proposition|corollary)\}(\[[^\]]*\])?\s*\\label\{([^}]*)\}.*?\\end\{\1\}\s*\\begin\{proof\}(.*?)\\end\{proof\}', re.S)
    for m in pat.finditer(t):
        out[m.group(3)] = norm(m.group(4))
    return out


def numbers(t):
    t = strip_comments(t)
    t = re.sub(r'\\(label|ref|eqref|cite|citet|citep|includegraphics|input)(\[[^\]]*\])?\{[^}]*\}', ' ', t)
    return Counter(re.findall(r'(?<![A-Za-z\\])\d+(?:\.\d+)?(?:e-?\d+)?', t))


def macros(t):
    return Counter(re.findall(r'\\((?:D|Num)[A-Za-z]+)', strip_comments(t)))


disp, stmt = r'equation\*?|align\*?', r'theorem|lemma|proposition|corollary|definition'
ld_o, ld_n = by_label(old, disp), by_label(new, disp)
st_o, st_n = by_label(old, stmt), by_label(new, stmt)
pf_o, pf_n = proofs(old), proofs(new)
lab_o = set(re.findall(r'\\label\{([^}]*)\}', old))
lab_n = set(re.findall(r'\\label\{([^}]*)\}', new))
refs_n = set(re.findall(r'\\(?:eq)?ref\{([^}#]*)\}', new))
uo, un = unlabelled(old), unlabelled(new)
no, nn = numbers(old), numbers(new)
mo, mn = macros(old), macros(new)
report = {
    'labelled_displays_removed': sorted(set(ld_o) - set(ld_n)),
    'labelled_displays_added': sorted(set(ld_n) - set(ld_o)),
    'labelled_displays_changed': sorted(k for k in set(ld_o) & set(ld_n) if ld_o[k] != ld_n[k]),
    'labelled_display_count': len(ld_n),
    'statements_removed': sorted(set(st_o) - set(st_n)),
    'statements_added': sorted(set(st_n) - set(st_o)),
    'statements_changed': sorted(k for k in set(st_o) & set(st_n) if st_o[k] != st_n[k]),
    'statement_count': len(st_n),
    'unlabelled_displays_only_old': sorted((uo - un).elements()),
    'unlabelled_displays_only_new': sorted((un - uo).elements()),
    'labels_removed': sorted(lab_o - lab_n),
    'labels_added': sorted(lab_n - lab_o),
    'refs_without_label': sorted(refs_n - lab_n),
    'proofs_changed': sorted(k for k in set(pf_o) & set(pf_n) if pf_o[k] != pf_n[k]),
    'numbers_only_old': dict(sorted((no - nn).items())),
    'numbers_only_new': dict(sorted((nn - no).items())),
    'macro_uses_only_old': dict(sorted((mo - mn).items())),
    'macro_uses_only_new': dict(sorted((mn - mo).items())),
}
json.dump(report, open(report_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(report, ensure_ascii=False, indent=1))
