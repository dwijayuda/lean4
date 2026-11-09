#!/usr/bin/env python3
"""Compare native match/pattern-lambda semantics and the syntax-only PS prelude route."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('match-host-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
header = 'module\nprelude\npublic import Init\npublic section\n'
native = '''def add (x y : Nat) : Nat := x + y
def pairSum (p : Nat × Nat) : Nat := p.1 + p.2
def unary (n : Nat) : Nat := match n with
  | 0 => add 1 2
  | Nat.succ k => add k 1
def multi (n m : Nat) : Nat := match n, m with
  | 0, 0 => add 1 2
  | a, b => add a b
def named (n : Nat) : Nat := match h : n with
  | 0 => add 1 2
  | Nat.succ k => add k 1
def withMotive (n : Nat) : Nat := match (motive := Nat → Nat) n with
  | 0 => add 1 2
  | Nat.succ k => add k 1
def options (n : Nat) : Nat := match some n with
  | some (Nat.succ k) => add k 1
  | some 0 => 0
  | none => 0
def alternatives (n : Nat) : Nat := match n with
  | 0 | 1 => add 1 2
  | k => k
def pattern (n : Nat) : Nat := (fun | 0 => add 1 2 | Nat.succ k => add k 1) n
'''
ps = '''function add(x: Nat, y: Nat): Nat := x + y
function pairSum(p: Nat × Nat): Nat := p.1 + p.2
function unary(n: Nat): Nat := match n with
  | 0 => add(1, 2)
  | Nat.succ k => add(k, 1)
function multi(n: Nat, m: Nat): Nat := match n, m with
  | 0, 0 => add(1, 2)
  | a, b => add(a, b)
function named(n: Nat): Nat := match h : n with
  | 0 => add(1, 2)
  | Nat.succ k => add(k, 1)
function withMotive(n: Nat): Nat := match (motive := Nat → Nat) n with
  | 0 => add(1, 2)
  | Nat.succ k => add(k, 1)
function options(n: Nat): Nat := match some n with
  | some (Nat.succ k) => add(k, 1)
  | some 0 => 0
  | none => 0
function alternatives(n: Nat): Nat := match n with
  | 0 | 1 => add(1, 2)
  | k => k
function pattern(n: Nat): Nat := (fun | 0 => add(1, 2) | Nat.succ k => add(k, 1))(n)
'''
guards = '''private theorem unaryZero : unary 0 = 3 := rfl
private theorem unaryFour : unary 4 = 4 := rfl
private theorem multiZero : multi 0 0 = 3 := rfl
private theorem multiValues : multi 2 3 = 5 := rfl
private theorem namedValue : named 2 = 2 := rfl
private theorem motiveValue : withMotive 0 = 3 := rfl
private theorem optionValue : options 3 = 3 := rfl
private theorem alternativeValue : alternatives 1 = 3 := rfl
private theorem patternValue : pattern 3 = 3 := rfl
'''

# Deliberately retain native pattern application and field binders. Only the
# ordinary value roles change grammar, with original UTF-8 bytes retained.
native += '''-- Source fidelity: π / 😀; native patterns stay native.
structure AdapterCell where
  value : Nat
  step : Nat → Nat
def record (n : Nat) : AdapterCell := { value := add n 1, step x := add x n }
def typedRecord (n : Nat) : AdapterCell := { value := add n 1, step := fun x => add x n : AdapterCell }
def updated (n : Nat) : AdapterCell := { record n with value := add n 2 }
def fieldEqns (n : Nat) : AdapterCell := { value := n, step | 0 => add n 1 | Nat.succ k => add k n }
def branch (n : Nat) : Id Nat := do
  if n == 0 then return add 1 2
  else if n == 1 then return add 2 2
  else return add n 0
def proofBranch (n : Nat) : Id Nat := do
  if h : n = 0 then return add n 3
  return add n 1
def patternBranch (n : Nat) : Id Nat := do
  if let some (Nat.succ k) := some n then return add k 1
  return 0
def boundBranch (n : Nat) : Id Nat := do
  if let some (Nat.succ k) ← pure (some n) then return add k 1
  return 0
'''
ps += '''-- Source fidelity: π / 😀; native patterns stay native.
structure AdapterCell where
  value : Nat
  step : Nat → Nat
function record(n: Nat): AdapterCell := { value := add(n, 1), step x := add(x, n) }
function typedRecord(n: Nat): AdapterCell := { value := add(n, 1), step := fun x => add(x, n) : AdapterCell }
function updated(n: Nat): AdapterCell := { record(n) with value := add(n, 2) }
function fieldEqns(n: Nat): AdapterCell := { value := n, step | 0 => add(n, 1) | Nat.succ k => add(k, n) }
function branch(n: Nat): Id(Nat) := do
  if n == 0 then return add(1, 2)
  else if n == 1 then return add(2, 2)
  else return add(n, 0)
function proofBranch(n: Nat): Id(Nat) := do
  if h : n = 0 then return add(n, 3)
  return add(n, 1)
function patternBranch(n: Nat): Id(Nat) := do
  if let some (Nat.succ k) := some n then return add(k, 1)
  return 0
function boundBranch(n: Nat): Id(Nat) := do
  if let some (Nat.succ k) ← pure(some n) then return add(k, 1)
  return 0
'''
guards += '''private theorem recordValue : (record 3).value = 4 := rfl
private theorem typedRecordValue : (typedRecord 3).step 2 = 5 := rfl
private theorem updatedValue : (updated 3).value = 5 := rfl
private theorem fieldEquationValue : (fieldEqns 3).step 0 = 4 := rfl
private theorem branchValue : branch 1 = 4 := rfl
private theorem proofBranchValue : proofBranch 0 = 3 := rfl
private theorem patternBranchValue : patternBranch 3 = 3 := rfl
private theorem boundBranchValue : boundBranch 3 = 3 := rfl
'''
native += '''def doMatchValue (n : Nat) : Id Nat := do
  match (dependent := false) n with
  | 0 => return add 1 2
  | Nat.succ k => return add k 1
def doMatchPair (n m : Nat) : Id Nat := do
  match n, m with
  | 0, 0 => return add 1 2
  | a, b => return add a b
def haveValue (n : Nat) : Id Nat := do
  have k : Nat := add n 1
  return k
def haveDefault (n : Nat) : Id Nat := do
  have step (x : Nat := add n 1) : Nat := add x 1
  return step
'''
ps += '''function doMatchValue(n: Nat): Id(Nat) := do
  match (dependent := false) n with
  | 0 => return add(1, 2)
  | Nat.succ k => return add(k, 1)
function doMatchPair(n: Nat, m: Nat): Id(Nat) := do
  match n, m with
  | 0, 0 => return add(1, 2)
  | a, b => return add(a, b)
function haveValue(n: Nat): Id(Nat) := do
  have k : Nat := add(n, 1)
  return k
function haveDefault(n: Nat): Id(Nat) := do
  have step (x: Nat := add(n, 1)): Nat := add(x, 1)
  return step
'''
guards += '''private theorem doMatchValueResult : doMatchValue 3 = 3 := rfl
private theorem doMatchPairResult : doMatchPair 2 3 = 5 := rfl
private theorem haveValueResult : haveValue 3 = 4 := rfl
private theorem haveDefaultResult : haveDefault 3 = 5 := rfl
'''


def run(args, label):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=300)
    text = result.stdout + result.stderr
    (work / (label + '.log')).write_text(text)
    print(text, end='', flush=True)
    assert result.returncode == 0, (label, result.returncode)
    return text


comparisons = {}
for label, body in [('baseline', native), ('migrated', ps), ('planned', None)]:
    source_root = work / (label + '-source')
    source_root.mkdir()
    source = source_root / 'MatchHostBootstrap.ps'
    proof_guards = guards
    if label == 'migrated':
        proof_guards = proof_guards.replace('(typedRecord 3).step 2', '((typedRecord(3)).step)(2)')
        proof_guards = proof_guards.replace('(fieldEqns 3).step 0', '((fieldEqns(3)).step)(0)')
    source.write_text((work / 'planned-source.ps').read_text() if body is None else header + body + proof_guards)
    shutil.copy2(source, work / (label + '-MatchHostBootstrap.ps'))
    directory = work / (label + '-build')
    args = ['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceRoot=' + str(source_root),
            '-Kroots=MatchHostBootstrap', '-KmoduleNames=MatchHostBootstrap', '-Kbootstrap=true',
            '-Kdriver=' + str(ROOT / '.lake/build/bin/ps0'), '-KprojectBuildDir=' + str(directory)]
    if label != 'baseline':
        args.append('-KsourceGrammar=true')
    run([*args, 'build', 'MatchHostBootstrap'], label)
    mapping = directory / 'lib/lean/MatchHostBootstrap.ilean.ps0-source-map.json'
    mapped = json.loads(mapping.read_text())
    assert mapped['source'].encode() == source.read_bytes()
    assert all(segment['kind'] == 'original' for segment in mapped['segments'])
    shutil.copy2(mapping, work / (label + '-source-map.json'))
    census = directory / 'lib/lean/MatchHostBootstrap.ilean.ps0-source-census.json'
    shutil.copy2(census, work / (label + '-source-census.json'))
    if label == 'baseline':
        run(['python3', 'tests/migrate-compiler-heads.py', census, source,
             work / 'planned-source.ps', '--plan', work / 'planned-edits.json'], 'plan')
    else:
        observed = json.loads(census.read_text())
        rows = [c['declaration'] for c in observed['commands'] if c['declaration']]
        assert observed['imports'] == ['Init']
        assert len(rows) == 42 and all(d['mode'] == 'mapped-ps' for d in rows)
    for relative in ['ir/MatchHostBootstrap.c', 'lib/lean/MatchHostBootstrap.olean']:
        file = directory / relative
        comparisons.setdefault(relative, {})[label] = hashlib.sha256(file.read_bytes()).hexdigest()
        shutil.copy2(file, work / (label + '-MatchHostBootstrap' + file.suffix))
assert all(pair['baseline'] == pair['migrated'] == pair['planned'] for pair in comparisons.values())
fixture = Path('tests/v1/ordinary_host_origins.ps')
origin_log = run(['lake', 'exe', 'ps0', 'check', fixture], 'origins')
assert 'PS0_HOST_NATIVE_QUOTATION: PASS' in origin_log
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'OrdinaryHostOrigins', work / 'native'], 'native-origins')
executable = work / 'native/OrdinaryHostOrigins'
runtime = run([executable], 'runtime-origins')
assert runtime.strip() == 'PS0_HOST_ORIGINS: PASS'
shutil.copy2(executable, work / 'OrdinaryHostOrigins')
(work / 'evidence.json').write_text(json.dumps(dict(source=os.environ['PS0_SOURCE_SHA'],
    comparisons=comparisons, mapped_definitions=21, mapped_theorems=21, logical_imports=['Init'],
    native_patterns_preserved=True, prepared_source_identity=True,
    source_origin_fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
    source_origin_cases=6, independently_owned_native_dsl=True, native_quotation=True,
    native_executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
    runtime_oracle='PS0_HOST_ORIGINS: PASS',
    scope='finite match/pattern-lambda/record/do-if ordinary values with native patterns and field binders',
    grammar_migration_complete=False, verified_execution=False), indent=2) + '\n')
print('PS0_MATCH_HOST_NATIVE_PARITY: PASS', flush=True)
