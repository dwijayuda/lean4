#!/usr/bin/env python3
"""Qualify native do indentation with explicit owned PS element operands."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('do-layout-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout


fixture = Path('tests/v1/do_layout_operands.ps')
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'DoLayout', work / 'native'], 'native')
oracle = 'PS0_DO_LAYOUT:7:3:3:7'
assert oracle in run([work / 'native/DoLayout'], 'runtime')
prefix = ('function add(x: Nat, y: Nat): Nat := x + y\n'
          'function pureNat(n: Nat): IO Nat := pure n\n'
          'function observe(n: Nat): IO Unit := pure ()\n')
for name, body, reason in [
    ('return-gap', '  return add (1, 2)', 'PS0V1-CALL-GAP'),
    ('let-gap', '  let n := add (1, 2)\n  return n', 'PS0V1-CALL-GAP'),
    ('statement-gap', '  observe (1)\n  return 2', 'PS0V1-CALL-GAP'),
    ('return-order', '  return add(x := 1, 2)', 'PS0V1-CALL-ORDER'),
    ('statement-type', '  pureNat(1)\n  return 2', 'IO Unit'),
]:
    path = work / (name + '.ps')
    path.write_text(prefix + 'const bad: IO Nat := do\n' + body + '\n')
    assert reason in run(['lake', 'exe', 'ps0', 'check', path], name, ok=False)
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': oracle,
    'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
    'scope': 'native do layout with explicit ordinary let/reassign/bind/return/expression operands; nested native syntax data remains native; not all do/control-flow grammar',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_DO_LAYOUT: PASS', flush=True)
