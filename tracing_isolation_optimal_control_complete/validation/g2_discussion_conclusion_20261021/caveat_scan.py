"""List caveat-style sentences in main.tex, grouped by section.

Usage: python caveat_scan.py <main.tex>
"""
import re
import sys
from collections import Counter

PAT = re.compile(r'不等同|不构成|不声称|不代替|不替代|不意味|不作为|不能(?:直接|解释|称|将|把|只)|并非|不是本文|仅用于|只用于|只说明|不承担|不提供|不预先|未在本稿|本稿不|不证明|未证明|不自动|不应|浮点诊断|不复现|不等于|另行')

lines = open(sys.argv[1], encoding='utf-8').read().split('\n')
sec = 'front'
hits = []
for n, line in enumerate(lines, 1):
    m = re.match(r'\\section\{([^}]*)\}', line)
    if m:
        sec = m.group(1)
    if line.lstrip().startswith('%') or '\\providecommand' in line or '\\renewcommand' in line:
        continue
    if PAT.search(line):
        hits.append((sec, n, line.strip()))

count = Counter(s for s, _, _ in hits)
for s, c in count.items():
    print(f'{c:3d}  {s}')
print()
for s, n, l in hits:
    print(f'[{s[:8]}] {n}: {l[:150]}')
