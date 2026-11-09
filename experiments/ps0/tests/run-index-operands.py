#!/usr/bin/env python3
"""Qualify native indexed-access parsers, PS operands and original syntax information."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('index-operands-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout


native = work / 'NativeIndex.ps'
native.write_text('module\nprelude\npublic import Lean\npublic section\nnamespace NativeIndexProbe\n'
                  'def plain : Nat := #[2, 3][0]\n'
                  'def optional : Option Nat := #[2, 3][1]?\n'
                  'def panicValue : Nat := #[2, 3][1]!\n'
                  "def proofValue : Nat := #[2, 3][0]'(by decide)\n"
                  'def sliceBoth : Subarray Nat := #[2, 3][0:2]\n'
                  'def sliceLower : Subarray Nat := #[2, 3][1:]\n'
                  'def sliceUpper : Subarray Nat := #[2, 3][:1]\n')
census = work / 'native-census.json'
run(['lake', 'exe', 'ps0', 'census-source', native, 'NativeIndex', census], 'native-census')
shapes = []
for command in json.loads(census.read_text())['commands']:
    declaration = command['declaration']
    if not declaration:
        continue
    value = declaration['valueSyntax']['args'][1]
    shapes.append(dict(name=declaration['sourceName'], kind=value['kind'], arity=len(value['args']),
                       children=[dict(kind=x['kind'], atom=x['atom']) for x in value['args']]))
assert len(shapes) == 7
print('PS0_NATIVE_INDEX_SHAPES:' + json.dumps(shapes, sort_keys=True), flush=True)
fixture = Path('tests/v1/index_operands.ps')
assert 'PS0_INDEX_PARSE_ERROR' not in run(
    ['lake', 'env', 'lean', 'tests/debug-index-layout.lean'], 'parser-layout')
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'IndexOperands', work / 'native'], 'native')
oracle = 'PS0_INDEX:3:2:3:2:3:2:1:1'
assert oracle in run([work / 'native/IndexOperands'], 'runtime')
assert 'PS0_PROJECTED_INDEX:3:2:1' in (work / 'runtime.log').read_text()
prefix = ('function add(x: Nat, y: Nat): Nat := x + y\n'
          'function chooseIndex(n: Nat): Nat := n\n'
          'function bound(n: Nat): 0 < 2 := by decide\n')
for name, source, reason in [
    ('index-gap', 'const bad: Option(Nat) := #[2, 3][chooseIndex (1)]?', 'PS0V1-CALL-GAP'),
    ('index-order', 'const bad: Option(Nat) := #[2, 3][add(x := 0, 1)]?', 'PS0V1-CALL-ORDER'),
    ('proof-gap', "const bad: Nat := #[2, 3][0]'(bound (1))", 'PS0V1-CALL-GAP'),
    ('proof-type', "const bad: Nat := #[2, 3][0]'True.intro", 'type mismatch'),
    ('slice-gap', 'const bad: Subarray(Nat) := #[2, 3][:chooseIndex (1)]', 'PS0V1-CALL-GAP'),
    ('slice-order', 'const bad: Subarray(Nat) := #[2, 3][add(x := 0, 1):]', 'PS0V1-CALL-ORDER'),
    ('projected-index-gap', 'const bad: Nat := (#[2, 3][chooseIndex (1)]?).getD(0)', 'PS0V1-CALL-GAP'),
    ('projected-index-order', 'const bad: Nat := (#[2, 3][add(x := 0, 1)]?).getD(0)', 'PS0V1-CALL-ORDER'),
    ('projected-slice-gap', 'const bad: Nat := (#[2, 3][:chooseIndex (1)]).size', 'PS0V1-CALL-GAP'),
]:
    path = work / (name + '.ps')
    path.write_text(prefix + source + '\n')
    diagnostic = run(['lake', 'exe', 'ps0', 'check', path], name, ok=False)
    assert reason.lower() in diagnostic.lower(), (name, reason)
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': oracle,
    'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
    'native_syntax_shapes': shapes, 'original_index_tokens_and_ranges': 13,
    'projected_oracle': 'PS0_PROJECTED_INDEX:3:2:1',
    'native_projected_index_quotation_ownership': True,
    'scope': 'four pinned native indexed-access and three competing array-slice productions, PS subject/index/proof/bound operands and callable heads; not all postfix/collection grammar',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_INDEX_OPERANDS: PASS', flush=True)
