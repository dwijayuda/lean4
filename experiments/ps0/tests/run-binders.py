#!/usr/bin/env python3
"""Qualify PS-owned binder operands against native Lean semantics and Lake linking."""
from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('binders-' + os.environ.get('GITHUB_RUN_ID', str(os.getpid())))
work.mkdir(parents=True, exist_ok=False)

def run(args, ok=True):
    r = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=300)
    print(r.stdout, end='', flush=True)
    assert (r.returncode == 0) == ok, (args, r.returncode)
    return r.stdout

fixture = 'tests/v1/binder_operands.ps'
run(['lake', 'exe', 'ps0', 'check', fixture])
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'BinderOperands', work / 'native'])
assert 'PS0_BINDERS:3:3:2:3:3:3' in run([work / 'native/BinderOperands'])
prefix = 'function add(x: Nat, y: Nat): Nat := x + y\n'
for name, decl, reason in [
    ('default-gap', 'def bad (x : Nat := add (1, 2)) : Nat := x', 'PS0V1-CALL-GAP'),
    ('type-gap', 'abbrev sized (n : Nat) : Type := Fin n\ndef bad (x : sized (3)) : Nat := x.val', 'PS0V1-CALL-GAP'),
    ('default-order', 'def bad (x: Nat := add(x := 1, 2), y: Nat := 0) : Nat := x', 'PS0V1-CALL-ORDER'),
    ('alias-adjacent', 'function bad(x: Nat)(y: Nat): Nat := x + y', 'PS0V1-BIND-02'),
    ('empty-def', 'def bad(): Nat := 0', None),
    ('untyped-comma', 'def bad(x, y: Nat): Nat := y', None),
    ('default-type', 'def bad (x: Nat := true, y: Nat := 0) : Nat := x', 'Bool'),
]:
    path = work / (name + '.ps')
    path.write_text(prefix + decl + '\n')
    diagnostic = run(['lake', 'exe', 'ps0', 'check', path], ok=False)
    assert reason is None or reason in diagnostic
(work / 'binder-evidence.json').write_text(json.dumps({
    'source': os.environ.get('PS0_SOURCE_SHA'), 'fixture': fixture,
    'oracle': 'PS0_BINDERS:3:3:2:3:3:3', 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_BINDER_OPERANDS: PASS', flush=True)
