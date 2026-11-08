#!/usr/bin/env python3
"""Exercise mapped host operands and preserve native quotation/DSL ownership."""
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('categories-' + os.environ.get('GITHUB_RUN_ID', str(os.getpid())))
work.mkdir(parents=True, exist_ok=False)

def run(args, ok=True):
    r = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=300)
    print(r.stdout, end='', flush=True)
    assert (r.returncode == 0) == ok, (args, r.returncode)
    return r.stdout

run(['lake', 'exe', 'ps0', 'check', 'tests/v1/standard_category_slots.ps'])
run(['lake', 'exe', 'ps0', 'build-native', 'tests/v1/standard_category_slots.ps', 'CategorySlots', work / 'native'])
assert 'PS0_CATEGORY_SLOTS:3:3:3:3:3' in run([work / 'native/CategorySlots'])
run(['lake', 'exe', 'ps0', 'check', 'tests/v1/category_do_operands.ps'])
run(['lake', 'exe', 'ps0', 'build-native', 'tests/v1/category_do_operands.ps', 'DoOperands', work / 'do-native'])
assert 'PS0_DO_OPERANDS:8:3' in run([work / 'do-native/DoOperands'])
for name, call, reason in [
    ('order', 'add(x := 1, 2)', 'PS0V1-CALL-ORDER'),
    ('duplicate', 'add(x := 1, x := 2)', 'PS0V1-CALL-NAMED'),
    ('gap', 'add (1, 2)', 'PS0V1-CALL-GAP'),
]:
    path = work / (name + '.ps')
    path.write_text('function add(x: Nat, y: Nat): Nat := x + y\ndef bad : Nat := ' + call + '\n')
    assert reason in run(['lake', 'exe', 'ps0', 'check', path], ok=False)
print('PS0_STANDARD_CATEGORY_SLOTS: PASS', flush=True)
