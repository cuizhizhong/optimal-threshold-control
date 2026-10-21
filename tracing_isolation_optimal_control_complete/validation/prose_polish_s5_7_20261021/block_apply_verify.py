"""Replace one block of main.tex (between two marker lines) and verify the mathematics is unchanged.

Usage: python block_apply_verify.py <in main.tex> <out main.tex> <new block> <start marker> <end marker> <report.json>
The block runs from the start marker up to (not including) the end marker.
"""
import json
import re
import sys
from collections import Counter

in_path, out_path, block_path, start, end, report_path = sys.argv[1:7]
text = open(in_path, encoding='utf-8').read()
s = text.index(start)
e = text.index(end, s + len(start))
old_block = text[s:e]
new_block = open(block_path, encoding='utf-8').read()
if not new_block.endswith('\n\n'):
    new_block = new_block.rstrip('\n') + '\n\n'
with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(text[:s] + new_block + text[e:])


def norm(x):
    return re.sub(r'\s+', ' ', x).strip()


ENV = r'\\begin\{(%s)\}(\[[^\]]*\])?(.*?)\\end\{\1\}'


def envs(t, names):
    return [(m.group(1), norm(m.group(3))) for m in re.finditer(ENV % names, t, re.S)]


def labelled(t):
    out = {}
    for _, body in envs(t, r'equation\*?|align\*?'):
        for lab in re.findall(r'\\label\{([^}]*)\}', body):
            out[lab] = body
    return out


def unlabelled(t):
    items = [b for _, b in envs(t, r'equation\*?|align\*?') if '\\label' not in b]
    items += [norm(m.group(1)) for m in re.finditer(r'\\\[(.*?)\\\]', t, re.S)]
    return Counter(items)


def statements(t):
    return [b for _, b in envs(t, r'theorem|lemma|proposition|corollary|definition')]


def inline(t):
    t = re.sub(r'\\begin\{(equation\*?|align\*?)\}.*?\\end\{\1\}', ' ', t, flags=re.S)
    t = re.sub(r'\\\[.*?\\\]', ' ', t, flags=re.S)
    return Counter(norm(m) for m in re.findall(r'\$([^$]+)\$', t))


lo, ln = labelled(old_block), labelled(new_block)
uo, un = unlabelled(old_block), unlabelled(new_block)
io, inn = inline(old_block), inline(new_block)
report = {
    'block': f'{start} .. {end}',
    'labels_identical': sorted(re.findall(r'\\label\{([^}]*)\}', old_block)) == sorted(re.findall(r'\\label\{([^}]*)\}', new_block)),
    'labelled_displays_identical': lo == ln,
    'changed_labelled_displays': sorted(k for k in set(lo) | set(ln) if lo.get(k) != ln.get(k)),
    'statements_identical': statements(old_block) == statements(new_block),
    'statement_count': len(statements(new_block)),
    'unlabelled_displays_identical': uo == un,
    'unlabelled_only_old': sorted((uo - un).elements()),
    'unlabelled_only_new': sorted((un - uo).elements()),
    'refs_only_old': sorted(set(re.findall(r'ref\{([^}]*)\}', old_block)) - set(re.findall(r'ref\{([^}]*)\}', new_block))),
    'refs_only_new': sorted(set(re.findall(r'ref\{([^}]*)\}', new_block)) - set(re.findall(r'ref\{([^}]*)\}', old_block))),
    'inline_only_old': sorted((io - inn).elements()),
    'inline_only_new_count': sum((inn - io).values()),
}
json.dump(report, open(report_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(json.dumps(report, ensure_ascii=False, indent=1))
