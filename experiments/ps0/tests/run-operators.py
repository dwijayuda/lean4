#!/usr/bin/env python3
"""Qualify native operator parsing with owned PS call operands."""
from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('operators-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=600)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout


run(['lake', 'env', 'lean', '--run', 'tests/inspect-operators.lean'], 'native-descriptors')
run(['lake', 'env', 'lean', 'tests/inspect-owned-operators.lean'], 'parse-boundaries')
fixture = 'tests/v1/operator_operands.ps'
oracle = 'PS0_OPERATORS:17:6:5:512:8:1:10:10'
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'OperatorOperands', work / 'native'], 'native')
assert oracle in run([work / 'native/OperatorOperands'], 'runtime')
prefix = 'function add(x: Nat, y: Nat): Nat := x + y\n'
for name, source, reason in [
    ('left-gap', 'const bad: Nat := add (1, 2) + 3', 'PS0V1-CALL-GAP'),
    ('right-gap', 'const bad: Nat := 1 + add (2, 3)', 'PS0V1-CALL-GAP'),
    ('right-order', 'const bad: Nat := 1 + add(x := 2, 3)', 'PS0V1-CALL-ORDER'),
    ('local-scope', 'section\nlocal infixl:65 " <%%> " => Nat.add\nend\nconst bad: Nat := 1 <%%> 2', None),
]:
    path = work / (name + '.ps')
    path.write_text(prefix + source + '\n')
    diagnostic = run(['lake', 'exe', 'ps0', 'check', path], name, ok=False)
    assert reason is None or reason in diagnostic, (name, reason)
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': oracle,
    'scope': 'finite native operator descriptor adapter, precedence/scoping and owned term operands; not all notation or whole grammar',
    'verified_execution': False,
}, indent=2) + '\n')
print('PS0_NATIVE_OPERATOR_OPERANDS: PASS', flush=True)
