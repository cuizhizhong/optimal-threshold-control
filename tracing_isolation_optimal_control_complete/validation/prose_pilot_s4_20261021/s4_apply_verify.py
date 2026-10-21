"""Replace section 4 of main.tex with the rewritten block and verify that no mathematics changed.

Usage: python s4_apply_verify.py <old_main.tex from HEAD> <main.tex to write> <new_block.tex> <report.json>
"""
import json
import re
import sys
from collections import Counter

old_path, main_path, block_path, report_path = sys.argv[1:5]
START, END = '\\section{预备结果}', '\\section{候选策略的构造}'

old_text = open(old_path, encoding='utf-8').read()
s, e = old_text.index(START), old_text.index(END)
old_block = old_text[s:e]
new_block = open(block_path, encoding='utf-8').read()
if not new_block.endswith('\n\n'):
    new_block = new_block.rstrip('\n') + '\n\n'
new_text = old_text[:s] + new_block + old_text[e:]
with open(main_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(new_text)


def norm(x):
    return re.sub(r'\s+', ' ', x).strip()


def envs(text, names):
    pat = re.compile(r'\\begin\{(' + names + r')\}(\[[^\]]*\])?(.*?)\\end\{\1\}', re.S)
    return [(m.group(1), m.group(2) or '', norm(m.group(3))) for m in pat.finditer(text)]


def labelled_displays(text):
    out = {}
    for name, _, body in envs(text, r'equation\*?|align\*?'):
        for lab in re.findall(r'\\label\{([^}]*)\}', body):
            out[lab] = body
    return out


def unlabelled_displays(text):
    items = [body for name, _, body in envs(text, r'equation\*?|align\*?') if '\\label' not in body]
    items += [norm(m.group(1)) for m in re.finditer(r'\\\[(.*?)\\\]', text, re.S)]
    return Counter(items)


def inline_math(text):
    stripped = re.sub(r'\\begin\{(equation\*?|align\*?)\}.*?\\end\{\1\}', ' ', text, flags=re.S)
    stripped = re.sub(r'\\\[.*?\\\]', ' ', stripped, flags=re.S)
    return Counter(norm(m) for m in re.findall(r'\$([^$]+)\$', stripped))


lo, ln = labelled_displays(old_block), labelled_displays(new_block)
stmt_names = r'theorem|lemma|proposition|corollary|definition'
so, sn = envs(old_block, stmt_names), envs(new_block, stmt_names)
labels_old = sorted(re.findall(r'\\label\{([^}]*)\}', old_block))
labels_new = sorted(re.findall(r'\\label\{([^}]*)\}', new_block))
uo, un = unlabelled_displays(old_block), unlabelled_displays(new_block)
io, inn = inline_math(old_block), inline_math(new_block)
report = {
    'labels_identical': labels_old == labels_new,
    'label_count': len(labels_new),
    'labelled_displays_identical': lo == ln,
    'labelled_display_count': len(ln),
    'changed_labelled_displays': sorted(k for k in set(lo) | set(ln) if lo.get(k) != ln.get(k)),
    'statements_identical': so == sn,
    'statement_count': len(sn),
    'unlabelled_displays_identical': uo == un,
    'inline_math_only_in_old': sorted((io - inn).elements()),
    'inline_math_only_in_new': sorted((inn - io).elements()),
    'old_block_chars': len(old_block),
    'new_block_chars': len(new_block),
}
json.dump(report, open(report_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps({k: v for k, v in report.items() if not k.startswith('inline')}, ensure_ascii=False))
print('inline math only in old:', report['inline_math_only_in_old'])
print('inline math only in new:', report['inline_math_only_in_new'])
