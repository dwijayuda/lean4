#!/usr/bin/env python3
"""Test-first probe for R2 braced local helper grammar; not yet a primary qualification gate."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('where-local-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout


fixture = Path('tests/v1/where_local_helpers.ps')
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'WhereLocal', work / 'native'], 'native')
oracle = 'PS0_WHERE_LOCAL:7:5:4:4:5'
proof_oracle = 'PS0_WHERE_PROOF:5:7:5:6:7:7'
runtime = run([work / 'native/WhereLocal'], 'runtime')
assert oracle in runtime and proof_oracle in runtime
prefix = 'abbrev Box (α : Type) : Type := α\nfunction add(x: Nat, y: Nat): Nat := x + y\n'
for name, source in [
    ('type-gap', 'function bad(n: Nat): Nat := helper(n)\nwhere { def helper(x: Box (Nat), y: Nat): Nat := add(x, y) }\n'),
    ('default-gap', 'function bad(n: Nat): Nat := helper(n)\nwhere { def helper(x: Nat, y: Nat := add (1, 2)): Nat := add(x, y) }\n'),
    ('body-gap', 'function bad(n: Nat): Nat := helper(n)\nwhere { def helper(x: Nat): Nat := add (x, 1) }\n'),
    ('nested-helper-tail', 'function bad(n: Nat): Nat := helper(n)\nwhere { def helper(x: Nat): Nat := x where { def nested(y: Nat): Nat := y } }\n'),
    ('attached-helper-finally', 'function bad(n: Nat): Nat := helper(n)\nwhere { def helper(x: Nat): Nat := ?value finally { | value => { exact(1) } } }\n'),
    ('unsolved-hole', 'function bad(n: Nat): Nat := ?value\nwhere { finally { } }\n'),
    ('bad-proof', 'function bad(n: Nat): Nat := ?value\nwhere { finally { | value => { exact("wrong") } } }\n'),
    ('duplicate-proof-section', 'function bad(n: Nat): Nat := ?value\nwhere { finally { | value => { exact(1) } | value => { exact(2) } } }\n'),
]:
    path = work / (name + '.ps')
    path.write_text(prefix + source)
    diagnostic = run(['lake', 'exe', 'ps0', 'check', path], name, ok=False)
    if name in ['type-gap', 'default-gap', 'body-gap']:
        assert 'PS0V1-CALL-GAP' in diagnostic
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': oracle, 'proof_oracle': proof_oracle,
    'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
    'rejection_cases': 8,
    'scope': 'finite braced/native where helper/default/capture/equation/record/body-wrapper/mutual-visibility and enclosing finally proof cases; not full signature/contract grammar',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_WHERE_LOCAL_HELPERS: PASS', flush=True)
