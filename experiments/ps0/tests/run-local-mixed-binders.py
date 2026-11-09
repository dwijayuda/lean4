#!/usr/bin/env python3
"""Qualify PS comma groups at native named-local telescope positions."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('local-mixed-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout


fixture = Path('tests/v1/local_mixed_binders.ps')
native_layouts = run(['lake', 'env', 'lean', 'tests/debug-local-layout.lean'], 'native-layouts')
assert native_layouts.count('PS0_NATIVE_LOCAL_LAYOUT ') == 6
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'LocalMixed', work / 'native'], 'native')
oracle = 'PS0_LOCAL_MIXED:7:7:7:8:7:5'
assert oracle in run([work / 'native/LocalMixed'], 'runtime')
prefix = 'abbrev Box (α : Type) : Type := α\nfunction add(x: Nat, y: Nat): Nat := x + y\n'
for name, declaration, reason in [
    ('type-gap', 'let step (x: Box (Nat), y: Nat): Nat := add(x, y)', 'PS0V1-CALL-GAP'),
    ('default-gap', 'let rec step (x: Nat, y: Nat := add (1, 2)): Nat := add(x, y)', 'PS0V1-CALL-GAP'),
    ('default-order', 'let step (x: Nat, y: Nat := add(x := 1, 2)): Nat := add(x, y)', 'PS0V1-CALL-ORDER'),
    ('default-type', 'let step (x: Nat, y: Nat := "bad"): Nat := add(x, y)', 'type mismatch'),
    ('empty-local', 'let step (): Nat := 1', 'unexpected'),
    ('instance-spacing', 'let step (x: Nat)[Inhabited(Nat)]: Nat := x', 'space'),
]:
    path = work / (name + '.ps')
    path.write_text(prefix + 'const bad: Id(Nat) := do\n  ' + declaration + '\n  return step(4)\n')
    diagnostic = run(['lake', 'exe', 'ps0', 'check', path], name, ok=False)
    assert reason.lower() in diagnostic.lower(), (name, reason)
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': oracle,
    'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
    'origin_cases': 6, 'rejection_cases': 6,
    'native_quotation_control': True, 'duplicate_partition_coalesced': True,
    'different_partition_rejected': True,
    'native_layout_controls': 6, 'array_update_boundary': 'native parser only; not an elaboration/runtime claim',
    'scope': 'finite named do/pure let and let-rec mixed/comma telescopes, native DSL control; not all local/where grammar',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_LOCAL_MIXED_BINDERS: PASS', flush=True)
