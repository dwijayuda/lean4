#!/usr/bin/env python3
"""Qualify native unless condition/block ownership and source fidelity."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('unless-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout


fixture = Path('tests/v1/unless_operands.ps')
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'UnlessOperands', work / 'native'], 'native')
oracle = 'PS0_UNLESS:2:20:13:3:20:4:12'
runtime = run([work / 'native/UnlessOperands'], 'runtime')
assert oracle in runtime and runtime.count('PS0_UNLESS_BODY:3') == 1
prefix = ('function add(x: Nat, y: Nat): Nat := x + y\n'
          'function below(n: Nat): Bool := n < 3\n'
          'function observe(n: Nat): IO Unit := pure(())\n')
for name, body, reason in [
    ('condition-gap', '  unless below (3) do\n    observe(1)\n  return 2', 'PS0V1-CALL-GAP'),
    ('body-gap', '  unless below(3) do\n    observe (1)\n  return 2', 'PS0V1-CALL-GAP'),
    ('body-order', '  unless below(3) do\n    return add(x := 1, 2)\n  return 2', 'PS0V1-CALL-ORDER'),
    ('condition-type', '  unless add(1, 2) do\n    observe(1)\n  return 2', None),
    ('empty-body', '  unless below(3) do', None),
    ('pattern-value-gap', '  let some n ← pure ((some 3 : Option Nat))\n    | return 0\n  return n', 'PS0V1-CALL-GAP'),
    ('pattern-fallback-gap', '  let some n ← pure((some 3 : Option Nat))\n    | return add (1, 2)\n  return n', 'PS0V1-CALL-GAP'),
    ('pattern-continuation-gap', '  let some n ← pure((some 3 : Option Nat))\n    | return 0\n  return add (n, 2)', 'PS0V1-CALL-GAP'),
]:
    path = work / (name + '.ps')
    path.write_text(prefix + 'const bad: IO Nat := do\n' + body + '\n')
    diagnostic = run(['lake', 'exe', 'ps0', 'check', path], name, ok=False)
    assert reason is None or reason in diagnostic, (name, reason)
for name, expression, reason in [
    ('term-condition-gap', 'unless below (3) do { observe(1) }', 'PS0V1-CALL-GAP'),
    ('term-body-gap', 'unless below(3) do { observe (1) }', 'PS0V1-CALL-GAP'),
]:
    path = work / (name + '.ps')
    path.write_text(prefix + 'const bad: IO Unit := ' + expression + '\n')
    assert reason in run(['lake', 'exe', 'ps0', 'check', path], name, ok=False)
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': oracle,
    'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
    'original_condition_block_token_ranges': True,
    'original_pattern_optional_type_arrow_and_branch_ranges': True,
    'native_quotation_and_explicit_doSeq_ownership': True,
    'scope': 'native doUnless/termUnless condition and sequence operands and native pattern-binding value/fallback/continuation do elements; pattern and optional native type remain unchanged; not all control/pattern grammar',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_NATIVE_UNLESS: PASS', flush=True)
