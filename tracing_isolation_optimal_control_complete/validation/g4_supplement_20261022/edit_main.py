"""G4 主文定点拆分；保留数学内容和作者指定原句。"""
from pathlib import Path
import json

project = Path(__file__).resolve().parents[2]
path = project / 'latex/main.tex'
text = path.read_text(encoding='utf-8')
baseline = json.loads((Path(__file__).parent / 'baseline.json').read_text(encoding='utf-8'))
assert baseline['protected_sentence'] in text

def replace_once(old, new):
    global text
    assert text.count(old) == 1, old[:100]
    text = text.replace(old, new, 1)

for line in text.splitlines()[:3]:
    assert line.startswith('%')
    replace_once(line + '\n', '')
replace_once('pdfauthor={Technical report}', 'pdfauthor={}')
replace_once('\\author{技术分析报告}', '\\author{}')
replace_once('\\date{2026年9月19日}', '\\date{}')
start = text.index('\\newif\\ifNumResultsVerified')
end = text.index('\\lstset', start)
text = text[:start] + '\\input{generated/numerical_values.tex}\n\n' + text[end:]
start = text.index('% BEGIN AUTO-GENERATED NUMERICAL REFERENCE VALUES')
end_marker = '% END AUTO-GENERATED NUMERICAL RESULTS'
end = text.index(end_marker, start) + len(end_marker)
text = text[:start] + text[end:]
replace_once('% 数值章节已内联；下方两个标记块由数值导出程序定点更新。',
             '% 数值数据由导言区加载的共享生成文件提供。')
replace_once('完整配置、判据与诊断结果见补充材料附录\\ref{app:numerical-reproducibility}。',
             '附加数值设置、核对结果与误差判据见补充材料 S1--S3。')
start = text.index('\\section{补充材料 S：数值复现、复核与诊断记录}')
end = text.index('\\bibliographystyle', start)
text = text[:start] + text[end:]
assert baseline['protected_sentence'] in text
assert '\\section{感染阈值与医疗需求}' in text
assert 'app:numerical-reproducibility' not in text
with path.open('w', encoding='utf-8', newline='\n') as stream:
    stream.write(text)
print('MAIN_SPLIT_OK protected_sentence=unchanged')
