"""Audit the MSW-style restructure: math unchanged except the planned additions, and no forward references inside proofs.

Usage: python msw_audit.py <old main.tex> <new main.tex> <report.json>
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


ENV = r'\\begin\{(%s)\}(\[[^\]]*\])?(.*?)\\end\{\1\}'


def envs(text, names):
    return [(m.group(1), norm(m.group(3)), m.start()) for m in re.finditer(ENV % names, text, re.S)]


def by_label(items):
    out = {}
    for name, body, _ in items:
        for lab in re.findall(r'\\label\{([^}]*)\}', body):
            out[lab] = body
    return out


disp = r'equation\*?|align\*?'
stmt = r'theorem|lemma|proposition|corollary|definition'
ld_old, ld_new = by_label(envs(old, disp)), by_label(envs(new, disp))
st_old, st_new = by_label(envs(old, stmt)), by_label(envs(new, stmt))


def unlabelled(text):
    items = [b for _, b, _ in envs(text, disp) if '\\label' not in b]
    items += [norm(m.group(1)) for m in re.finditer(r'\\\[(.*?)\\\]', text, re.S)]
    return Counter(items)


uo, un = unlabelled(old), unlabelled(new)

# Proof bodies keyed by the label of the statement they follow.
def proofs(text):
    out = {}
    stmts = [(m.start(), re.search(r'\\label\{([^}]*)\}', m.group(0))) for m in re.finditer(ENV % stmt, text, re.S)]
    for m in re.finditer(r'\\begin\{proof\}(\[[^\]]*\])?(.*?)\\end\{proof\}', text, re.S):
        opt = m.group(1) or ''
        ref = re.search(r'\\ref\{([^}]*)\}', opt)
        if ref:
            key = ref.group(1)
        else:
            prior = [s for s in stmts if s[0] < m.start()]
            key = prior[-1][1].group(1) if prior and prior[-1][1] else f'@{m.start()}'
        out[key] = norm(m.group(2))
    return out


po, pn = proofs(old), proofs(new)
changed_proofs = sorted(k for k in set(po) & set(pn) if po[k] != pn[k])

# Forward references inside proofs (new text).
labels = {m.group(1): m.start() for m in re.finditer(r'\\label\{([^}]*)\}', new)}
fwd = []
for m in re.finditer(r'\\begin\{proof\}(.*?)\\end\{proof\}', new, re.S):
    for r in re.finditer(r'\\(?:eq)?ref\{([^}]*)\}', m.group(0)):
        lab = r.group(1)
        if lab in labels and labels[lab] > m.start() and not lab.startswith(('sec:', 'app:', 'fig:', 'tab:')):
            fwd.append((new.count('\n', 0, m.start()) + 1, lab))

report = {
    'labelled_displays_same_keys': sorted(ld_old) == sorted(ld_new),
    'labelled_displays_changed': sorted(k for k in ld_old if k in ld_new and ld_old[k] != ld_new[k]),
    'labelled_display_count': len(ld_new),
    'statements_removed': sorted(set(st_old) - set(st_new)),
    'statements_added': sorted(set(st_new) - set(st_old)),
    'statements_changed': sorted(k for k in st_old if k in st_new and st_old[k] != st_new[k]),
    'statement_count': len(st_new),
    'unlabelled_displays_only_old': sorted((uo - un).elements()),
    'unlabelled_displays_only_new': sorted((un - uo).elements()),
    'proofs_changed': changed_proofs,
    'proof_count': len(pn),
    'forward_refs_in_proofs': fwd,
    'g1_markers_left': len(re.findall(r'% G1-', new)),
}
json.dump(report, open(report_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps(report, ensure_ascii=False, indent=1))
