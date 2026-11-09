#!/usr/bin/env python3
"""Qualify native recursive declaration structure with explicitly owned PS operands."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('local-recursion-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout


native = work / 'NativeRec.ps'
native.write_text('''module
prelude
public import Lean
public section
abbrev box (α : Type) : Type := α
def add (x y : Nat) : Nat := x + y
def simple : Id Nat := do
  let rec step (n : box Nat) (bias : Nat := add 1 2) : box Nat := add n bias
  return step 4
def equation : Id Nat := do
  let rec total : Nat → Nat
    | 0 => add 0 1
    | n + 1 => add (total n) 1
  return total 3
def pureValue : Nat := let rec step (n : Nat) := add n 1; step 4
''')
census = work / 'native-census.json'
run(['lake', 'exe', 'ps0', 'census-source', native, 'NativeRec', census], 'native-census')
shapes = []


def walk(value):
    if isinstance(value, dict):
        kind = value.get('kind', '')
        if kind.startswith('Lean.Parser.Term.') and kind.rsplit('.', 1)[-1] in {
                'doLetRec', 'letrec', 'letRecDecls', 'letRecDecl', 'letDecl',
                'letIdDecl', 'letEqnsDecl', 'matchAlts', 'matchAlt'}:
            shapes.append(dict(kind=kind, arity=len(value['args']),
                               children=[dict(kind=x['kind'], atom=x.get('atom')) for x in value['args']]))
        for child in value.values():
            walk(child)
    elif isinstance(value, list):
        for child in value:
            walk(child)


walk(json.loads(census.read_text()))
assert shapes, 'native control must retain native declaration values'
print('PS0_NATIVE_RECURSION_SHAPES:' + json.dumps(shapes, sort_keys=True), flush=True)
fixture = Path('tests/v1/local_recursion_operands.ps')
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'LocalRec', work / 'native'], 'native')
oracle = 'PS0_LOCAL_REC:7:4:5:7:4'
assert oracle in run([work / 'native/LocalRec'], 'runtime')
prefix = 'abbrev Box (α : Type) : Type := α\nfunction add(x: Nat, y: Nat): Nat := x + y\n'
for name, body, reason in [
    ('binder-gap', '  let rec step (n : Box (Nat)) := n\n  return step(1)', 'PS0V1-CALL-GAP'),
    ('default-gap', '  let rec step (n : Nat := add (1, 2)) := n\n  return step(1)', 'PS0V1-CALL-GAP'),
    ('body-gap', '  let rec step (n : Nat) := add (n, 1)\n  return step(1)', 'PS0V1-CALL-GAP'),
    ('equation-gap', '  let rec step : Nat → Nat\n    | n => add (n, 1)\n  return step(1)', 'PS0V1-CALL-GAP'),
    ('body-order', '  let rec step (n : Nat) := add(x := n, 1)\n  return step(1)', 'PS0V1-CALL-ORDER'),
    ('default-type', '  let rec step (n : Nat := "wrong") := n\n  return step(1)', 'Nat'),
]:
    path = work / (name + '.ps')
    path.write_text(prefix + 'const bad: Id(Nat) := do\n' + body + '\n')
    assert reason in run(['lake', 'exe', 'ps0', 'check', path], name, ok=False)
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': oracle,
    'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
    'original_let_rec_separator_and_root_ranges': True,
    'scope': 'native local recursive declaration groups, PS ID signatures/defaults and simple/equation values, native pattern/termination/quotation ownership; not all recursion/control grammar',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_LOCAL_RECURSION_OPERANDS: PASS', flush=True)
