#!/usr/bin/env python3
"""Reproducible checks for the targeted mathematical revision.

Run: python checks/check_revision.py
Requirements: numpy, scipy, sympy; a Git executable for the patch round-trip.
This program checks source consistency, exact algebra, and finite numerical
samples. It does not establish the quantified analytical theorems or compile TeX.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any
import numpy as np
import verify_revision as regression

ROOT = Path(__file__).resolve().parents[1]
REL = Path('tracing_isolation_optimal_control_complete/latex/main.tex')
BASE = ROOT / 'base/main.tex'
TEX = ROOT / REL


def blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def strip_comments(text: str) -> str:
    return '\n'.join(re.sub(r'(?<!\\)%.*', '', line) for line in text.splitlines())


def block(text: str, label: str, env: str = 'equation') -> str:
    pattern = re.compile(r'\\begin\{' + re.escape(env) + r'\}.*?\\end\{' + re.escape(env) + r'\}', re.S)
    hits = [m.group() for m in pattern.finditer(text) if r'\label{' + label + '}' in m.group()]
    if len(hits) != 1:
        raise ValueError(f'Expected one {env} block for {label}, found {len(hits)}')
    return hits[0]


def static_checks() -> dict[str, Any]:
    before = BASE.read_text(encoding='utf-8')
    after = TEX.read_text(encoding='utf-8')
    manifest = json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
    old_labels = set(re.findall(r'\\label\{([^}]+)\}', strip_comments(before)))
    new_labels = set(re.findall(r'\\label\{([^}]+)\}', strip_comments(after)))
    sc = regression.source_checks(TEX)
    env_stack: list[str] = []
    env_errors: list[str] = []
    text = strip_comments(after)
    for match in re.finditer(r'\\(begin|end)\{([^}]+)\}', text):
        action, env = match.groups()
        if action == 'begin':
            env_stack.append(env)
        elif not env_stack or env_stack.pop() != env:
            env_errors.append(f'Mismatch at offset {match.start()}: {match.group()}')
    brace_depth = 0
    brace_error = False
    for pos, char in enumerate(text):
        if char not in '{}':
            continue
        preceding = 0
        i = pos-1
        while i >= 0 and text[i] == '\\':
            preceding += 1
            i -= 1
        if preceding % 2:
            continue
        brace_depth += 1 if char == '{' else -1
        if brace_depth < 0:
            brace_error = True
    controls = re.findall(r'\\(?:[A-Za-z@]+|[^A-Za-z@])', text)
    protected = {
        label: block(before, label) == block(after, label)
        for label in (
            'eq:count-model', 'eq:beta12', 'eq:normalized-model', 'eq:capacity',
            'eq:linear-cost', 'eq:constants', 'eq:value-definition',
            'eq:regions', 'eq:candidate-feedback', 'eq:candidate-U',
            'eq:global-optimality', 'eq:capacity-tie'
        ) if label != 'eq:regions'
    }
    protected['eq:regions'] = block(before, 'eq:regions', 'align') == block(after, 'eq:regions', 'align')
    protected['def:admissible'] = block(before, 'def:admissible', 'definition') == block(after, 'def:admissible', 'definition')
    protected['tab:baseline-results'] = block(before, 'tab:baseline-results', 'table') == block(after, 'tab:baseline-results', 'table')
    figs_before = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', before)
    figs_after = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', after)
    forbidden = ('右连续', 'càdlàg', 'cadlag', '逐点唯一', 'V_{\\mathrm{rc}}')
    extra = {
        'base_matches_live_blob': blob(BASE.read_bytes()) == manifest['base_git_blob'],
        'revised_matches_manifest': blob(TEX.read_bytes()) == manifest['revised_git_blob'],
        'all_existing_labels_preserved': old_labels.issubset(new_labels),
        'new_labels_exactly_as_documented': new_labels-old_labels == set(manifest['new_labels']),
        'protected_model_cost_control_candidate_blocks_unchanged': all(protected.values()),
        'right_continuity_compatibility_not_added': all(token not in after for token in forbidden),
        'no_stale_G1_G4_text': 'G1--G4' not in text and '本次' not in text,
        'environment_stack_balanced': not env_stack and not env_errors,
        'grouping_braces_balanced': brace_depth == 0 and not brace_error,
        'math_display_pairs_balanced': controls.count(r'\[')==controls.count(r'\]') and controls.count(r'\(')==controls.count(r'\)'),
        'dollar_math_delimiters_even': len(re.findall(r'(?<!\\)\$', text)) % 2 == 0,
        'original_figure_references_preserved': figs_before == figs_after,
        'bibliography_copy_unchanged': (ROOT/'base/references.bib').read_bytes() == (TEX.parent/'references.bib').read_bytes(),
        'no_duplicate_labels': not sc['duplicate_labels'],
        'no_undefined_references': not sc['undefined_references'],
        'no_missing_citation_keys': not sc['missing_bibliography_keys'],
    }
    label_lines = {}
    for num, line in enumerate(after.splitlines(),1):
        for label in re.findall(r'\\label\{([^}]+)\}',line):
            label_lines[label] = num
    (ROOT/'checks/label_locations.json').write_text(json.dumps(label_lines,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return {'status': 'PASS' if all(extra.values()) else 'FAIL', 'checks':extra,
            'protected_blocks':protected, 'latex_static':sc, 'new_labels':sorted(new_labels-old_labels),
            'environment_errors':env_errors, 'remaining_environment_stack':env_stack,
            'scope':'Lightweight source checks, not a TeX compiler or proof assistant.'}


def sign_region_checks() -> dict[str, Any]:
    settings = [(.5,.3,.15),(.25,.2,.08),(.75,.2,.3),(.8,.65,.03),(.2,.08,.4),(.9,.15,.01),(.5,1.2,.15),(.4,.8,.35)]
    counts: Counter = Counter()
    assertions: list[bool] = []
    max_zero_error = 0.0
    max_phi_identity_error = 0.0
    for p,h,K in settings:
        m = regression.Model(p=p,c=2.,gamma=2*p*h,K=K)
        for z in np.linspace(m.zB+.04*(m.e-m.zB), m.e-.04*(m.e-m.zB),16):
            s,j = m.gamma_point(float(z))
            phi_g = m.phi(s,j)
            delta = .04*min(j,K-j,phi_g-m.phiA,m.phiB-phi_g)
            if delta <= 0:
                raise ArithmeticError('Test sample lost the required interior margins.')
            for sign in (-1,1):
                i = j+sign*delta
                chi = i-j
                phi = m.phi(s,i)
                eta,_ = m.gamma_hit(phi)
                expected = 'tracking' if sign>0 else 'wait_gamma'
                assertions.append(m.evaluate(s,i).region == expected)
                assertions.append((s<eta)==(chi>0))
                max_phi_identity_error = max(max_phi_identity_error,abs((phi-phi_g)-chi))
                if sign>0:
                    assertions.append(s<m.sB and phi<m.phiB)
                counts['above' if sign>0 else 'below'] += 1
            eta,_ = m.gamma_hit(phi_g)
            max_zero_error = max(max_zero_error,abs(s-eta))
            counts['on_interface'] += 1
        for fraction in (.2,.5,.8,1.):
            s=m.h+fraction*(m.e-m.h)
            i=.5*(m.a(s)+m.K)
            assertions.append(m.phiA<m.phi(s,i)<m.phiB)
            assertions.append(m.evaluate(s,i).region=='tracking')
            counts['h_to_e_unsafe']+=1
        for fraction in (1e-4,.02,.25):
            s=m.sB-fraction*(m.sB-m.e)
            assertions.append(m.evaluate(s,m.K).region=='tracking')
            assertions.append(m.phi(s,m.K)<m.phiB)
            counts['capacity_left_of_sB']+=1
    passed = all(assertions) and max_zero_error<1e-8 and max_phi_identity_error<1e-12
    return {'status':'PASS' if passed else 'FAIL', 'counts':dict(counts),
            'models':len(settings), 'all_boolean_comparisons_passed':all(assertions),
            'max_gamma_hit_inverse_error':max_zero_error,
            'max_phi_minus_phiGamma_minus_chi_error':max_phi_identity_error,
            'scope':'Finite auxiliary-strip samples for the new region-side lemma; the universal statement is proved in TeX.'}


def patch_checks() -> dict[str, Any]:
    patch = ROOT/'math_revision.patch'
    with tempfile.TemporaryDirectory(prefix='threshold_roundtrip_') as tmp:
        root=Path(tmp)
        target=root/REL
        target.parent.mkdir(parents=True)
        target.write_bytes(BASE.read_bytes())
        def git(*args:str) -> str:
            result=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True,check=False)
            if result.returncode:
                raise RuntimeError(f'git {args!r}: {result.stderr}')
            return result.stdout
        git('init','-q')
        git('add',str(REL))
        git('apply','--check',str(patch))
        git('apply',str(patch))
        matched=target.read_bytes()==TEX.read_bytes()
        git('diff','--check')
        stat=git('diff','--numstat').strip()
        git('apply','--reverse','--check',str(patch))
        git('apply','--reverse',str(patch))
        restored=target.read_bytes()==BASE.read_bytes()
    return {'status':'PASS' if matched and restored else 'FAIL',
            'git_apply_check_passed':True, 'patch_output_byte_identical_to_delivered_main':matched,
            'reverse_patch_restores_exact_base':restored,'git_diff_check_passed':True,'numstat':stat,
            'scope':'Disposable local test repository only; no remote branch was modified.'}


def main() -> int:
    report:dict[str,Any]={'generated_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Analytical proofs are in main.tex. These checks are not formal proof verification.',
        'compiled_in_this_round':False,
        'not_run':['XeLaTeX/BibTeX or full-figure PDF build','MATLAB/Octave/OpenOCL','time-varying SLSQP','new parameter convergence studies']}
    try:
        report['source']=static_checks()
        report['new_region_side_samples']=sign_region_checks()
        report['existing_formula_regression']=regression.checks()
        report['patch']=patch_checks()
        report['status']='PASS' if all(report[key]['status']=='PASS' for key in ('source','new_region_side_samples','existing_formula_regression','patch')) else 'FAIL'
    except Exception as exc:
        report.update(status='ERROR', error_type=type(exc).__name__,error=str(exc))
    (ROOT/'checks/check_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':
    sys.exit(main())
