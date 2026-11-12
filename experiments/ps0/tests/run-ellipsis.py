#!/usr/bin/env python3
"""Check native ellipsis completion in PS call arguments, including exact syntax fidelity."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('ellipsis-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout


fixture = Path('tests/v1/ellipsis_operands.ps')
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'EllipsisOperands', work / 'native'], 'native')
assert 'PS0_NATIVE_ELLIPSIS:PASS' in run([work / 'native/EllipsisOperands'], 'runtime')
for name, source, reason in [
    ('named-before-ellipsis', 'const bad: Eq(3, 3) := Eq.refl(a := 3, ..)', 'PS0V1-CALL-ORDER'),
    ('unresolved-ellipsis', 'function identity(n: Nat): Nat := n\nconst bad: Nat := identity(..)', None),
    ('nonterminal-ellipsis', 'const bad: Eq(3, 3) := Eq.refl(.., 3)', "unexpected '..'"),
    ('repeated-ellipsis', 'const bad: Eq(3, 3) := Eq.refl(.., ..)', "unexpected '..'"),
]:
    path = work / (name + '.ps')
    path.write_text(source + '\n')
    diagnostic = run(['lake', 'exe', 'ps0', 'check', path], name, ok=False)
    assert reason is None or reason in diagnostic
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'],
    'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
    'oracle': 'PS0_NATIVE_ELLIPSIS:PASS', 'original_native_node_identity': True,
    'scope': 'explicit ellipsis arguments reuse the native argument parser and application elaborator; no new empty-call/default completion rule',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_ELLIPSIS_OPERANDS: PASS', flush=True)
