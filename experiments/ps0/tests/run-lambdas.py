#!/usr/bin/env python3
"""Qualify finite owned lambda operands while retaining native binder elaboration."""
from pathlib import Path
import json
import hashlib
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('lambdas-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout


fixture = 'tests/v1/lambda_operands.ps'
oracle = 'PS0_LAMBDAS:3:3:3:3:3:3:2:3:3:3:3'
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'LambdaOperands', work / 'native'], 'native')
assert oracle in run([work / 'native/LambdaOperands'], 'runtime')
projection = 'tests/v1/pending_section_projection.ps'
run(['lake', 'exe', 'ps0', 'check', projection], 'projection-check')
run(['lake', 'exe', 'ps0', 'build-native', projection, 'SectionProjection', work / 'projection-native'], 'projection-native')
assert 'PS0_SECTION_PROJECTION:3' in run([work / 'projection-native/SectionProjection'], 'projection-runtime')
native_pun = work / 'native-invalid-punning.ps'
native_pun.write_text('module\nprelude\npublic import Lean\npublic section\n'
                     'structure PunningTarget where\n  value : Nat\n'
                     'def bad : Id PunningTarget := do\n'
                     '  let f : Nat → Nat := Nat.succ\n  let x := 2\n'
                     '  return {\n    f\n    x\n  }\n')
native_pun_diagnostic = run(['lake', 'exe', 'ps0', 'census-source', native_pun,
                            'NativeInvalidPunning', work / 'invalid-punning-census.json'],
                           'native-invalid-punning', ok=False)
assert 'not a field of structure' in native_pun_diagnostic
native_coerced_pun = work / 'native-coerced-invalid-punning.ps'
native_coerced_pun.write_text(native_pun.read_text().replace(
    'def bad', 'instance : Coe Nat PunningTarget where\n  coe n := ⟨n⟩\ndef bad'))
native_coerced_diagnostic = run(['lake', 'exe', 'ps0', 'census-source', native_coerced_pun,
                                'NativeCoercedInvalidPunning', work / 'coerced-invalid-punning-census.json'],
                               'native-coerced-invalid-punning', ok=False)
assert 'not a field of structure' in native_coerced_diagnostic
native_argument_wrapper = work / 'native-argument-wrapper.ps'
native_argument_wrapper.write_text('module\nprelude\npublic import Lean\npublic section\n'
                                   'def bad : Nat := Nat.succ ({ (1 + 1) })\n')
native_argument_diagnostic = run(['lake', 'exe', 'ps0', 'census-source', native_argument_wrapper,
                                 'NativeArgumentWrapper', work / 'argument-wrapper-census.json'],
                                'native-argument-wrapper', ok=False)
assert 'Singleton' in native_argument_diagnostic
prefix = 'function add(x: Nat, y: Nat): Nat := x + y\nabbrev sized (n : Nat) := Fin n\n'
for name, source, reason in [
    ('body-gap', 'const bad: Nat → Nat := fun (n : Nat) => add (n, 1)', 'PS0V1-CALL-GAP'),
    ('body-order', 'const bad: Nat → Nat := fun (n : Nat) => add(x := n, 1)', 'PS0V1-CALL-ORDER'),
    ('unicode-body-gap', 'const bad: Nat → Nat := fun n ↦ add (n, 1)', 'PS0V1-CALL-GAP'),
    ('unicode-body-order', 'const bad: Nat → Nat := λ n ↦ add(x := n, 1)', 'PS0V1-CALL-ORDER'),
    ('type-gap', 'abbrev Small := sized(3)\nconst bad: Small → Nat := fun (n : sized (3)) => n.val', 'PS0V1-CALL-GAP'),
    ('lambda-default', 'const bad: Nat → Nat := fun (n : Nat := 3) => n', None),
    ('projection-subject-gap', 'const bad: Nat := (List.head! ([3])).succ', 'PS0V1-CALL-GAP'),
    ('projection-call-head-gap', 'const bad: Nat := (List.head! ([3])).add(4)', 'PS0V1-CALL-GAP'),
    ('invalid-punning', 'structure PunningTarget where\n  value : Nat\n'
     'const bad: Id(PunningTarget) := do\n  let f : Nat → Nat := Nat.succ\n  let x := 2\n'
     '  return {\n    f\n    x\n  }', 'not a field of structure'),
    ('coerced-invalid-punning', 'structure PunningTarget where\n  value : Nat\n'
     'instance : Coe Nat PunningTarget where\n  coe n := ⟨n⟩\n'
     'const bad: Id(PunningTarget) := do\n  let f : Nat → Nat := Nat.succ\n  let x := 2\n'
     '  return {\n    f\n    x\n  }', 'not a field of structure'),
    ('argument-wrapper', 'const bad: Nat := Nat.succ({ (1 + 1) })', 'Singleton'),
]:
    file = work / (name + '.ps')
    file.write_text(prefix + source + '\n')
    diagnostic = run(['lake', 'exe', 'ps0', 'check', file], name, ok=False)
    assert reason is None or reason in diagnostic, (name, reason)
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': oracle,
    'fixture_sha256': hashlib.sha256(Path(fixture).read_bytes()).hexdigest(),
    'original_lambda_and_arrow_token_checks': 2,
    'native_and_ps_invalid_multi_pun_rejection': 'not a field of structure',
    'native_and_ps_coerced_invalid_multi_pun_rejection': 'not a field of structure',
    'projection': {
        'source_sha256': hashlib.sha256(Path(projection).read_bytes()).hexdigest(),
        'executable_sha256': hashlib.sha256((work / 'projection-native/SectionProjection').read_bytes()).hexdigest(),
        'oracle': 'PS0_SECTION_PROJECTION:3',
        'original_range_checks': 2,
        'native_head_gap_rejection': 'PS0V1-CALL-GAP',
    },
    'scope': 'single-body lambda operands, nested sections and native projection reuse with original ranges; native quotations remain opaque; not all lambda/match/term grammar',
    'verified_execution': False,
}, indent=2) + '\n')
print('PS0_LAMBDA_OPERANDS: PASS', flush=True)
