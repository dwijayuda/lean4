#!/usr/bin/env python3
"""Qualify finite owned lambda operands while retaining native binder elaboration."""
from pathlib import Path
import json
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
prefix = 'function add(x: Nat, y: Nat): Nat := x + y\nabbrev sized (n : Nat) := Fin n\n'
for name, source, reason in [
    ('body-gap', 'const bad: Nat → Nat := fun (n : Nat) => add (n, 1)', 'PS0V1-CALL-GAP'),
    ('body-order', 'const bad: Nat → Nat := fun (n : Nat) => add(x := n, 1)', 'PS0V1-CALL-ORDER'),
    ('type-gap', 'const bad: sized(3) → Nat := fun (n : sized (3)) => n.val', 'PS0V1-CALL-GAP'),
    ('lambda-default', 'const bad: Nat → Nat := fun (n : Nat := 3) => n', None),
]:
    file = work / (name + '.ps')
    file.write_text(prefix + source + '\n')
    diagnostic = run(['lake', 'exe', 'ps0', 'check', file], name, ok=False)
    assert reason is None or reason in diagnostic, (name, reason)
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': oracle,
    'scope': 'single-body lambda operands and native binder/pattern elaboration; native quotations remain opaque; not all lambda/match/term grammar',
    'verified_execution': False,
}, indent=2) + '\n')
print('PS0_LAMBDA_OPERANDS: PASS', flush=True)
