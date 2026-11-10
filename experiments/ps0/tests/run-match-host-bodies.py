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
native += '''def forValue (n : Nat) : Id Nat := do
  let mut result := n
  for k in [0:2] do
    result := add result k
  return result
def forPairs (n : Nat) : Id Nat := do
  let mut result := n
  for (a, b) in [(1, 2), (3, 4)] do
    result := add result (add a b)
  return result
def tryValue (n : Nat) : IO Nat := do
  try
    if n == 0 then throw (IO.userError "zero")
    return add n 1
  catch e : IO.Error => return add n 2
  finally pure ()
def catchMatchValue (n : Nat) : IO Nat := do
  try return add n 1
  catch | _ => return add n 2
'''
ps += '''function forValue(n: Nat): Id(Nat) := do
  let mut result := n
  for k in [0:2] do
    result := add(result, k)
  return result
function forPairs(n: Nat): Id(Nat) := do
  let mut result := n
  for (a, b) in [(1, 2), (3, 4)] do
    result := add(result, add(a, b))
  return result
function tryValue(n: Nat): IO(Nat) := do
  try
    if n == 0 then throw(IO.userError("zero"))
    return add(n, 1)
  catch e : IO.Error => return add(n, 2)
  finally pure(())
function catchMatchValue(n: Nat): IO(Nat) := do
  try return add(n, 1)
  catch | _ => return add(n, 2)
'''
guards += '''private theorem forPairsResult : forPairs 3 = 13 := rfl
'''
native += '''def proofIf (n : Nat) : Nat := if h : n = 0 then add n 3 else add n 1
def typedValue (n : Nat) : Nat := (add n 1 : Nat)
def inferredAscription (n : Nat) : Nat := (add n 1 :)
def typedId (n : Nat) : Id Nat := (add n 1 : Id Nat)
def tacticValue (n : Nat) : Nat := by
  exact add n 1
def tacticBraced (n : Nat) : Nat := by { exact add n 1 }
def tacticApply (n : Nat) : Nat := by apply add n 1
def tacticRefine (n : Nat) : Nat := by refine add n 1
'''
ps += '''function proofIf(n: Nat): Nat := if h : n = 0 then add(n, 3) else add(n, 1)
function typedValue(n: Nat): Nat := (add(n, 1) : Nat)
function inferredAscription(n: Nat): Nat := (add(n, 1) :)
function typedId(n: Nat): Id(Nat) := (add(n, 1) : Id(Nat))
function tacticValue(n: Nat): Nat := by
  exact add(n, 1)
function tacticBraced(n: Nat): Nat := by { exact add(n, 1) }
function tacticApply(n: Nat): Nat := by apply add(n, 1)
function tacticRefine(n: Nat): Nat := by refine add(n, 1)
'''
guards += '''private theorem proofIfResult : proofIf 0 = 3 := rfl
private theorem typedValueResult : typedValue 3 = 4 := rfl
private theorem inferredAscriptionResult : inferredAscription 3 = 4 := rfl
private theorem typedIdResult : typedId 3 = 4 := rfl
private theorem tacticValueResult : tacticValue 3 = 4 := rfl
private theorem tacticBracedResult : tacticBraced 3 = 4 := rfl
private theorem tacticApplyResult : tacticApply 3 = 4 := rfl
private theorem tacticRefineResult : tacticRefine 3 = 4 := rfl
'''


native += '''def tupleValue (n : Nat) : Nat × Nat := (add n 1, n)
def listValue (n : Nat) : List Nat := [add n 1, n,]
def arrayValue (n : Nat) : Array Nat := #[add n 1, n,]
def interpolationValue (n : Nat) : String := s!"value:{add n 1}"
def forallDomain : Prop := ∀ (n : Fin (add 1 2)), n.val < 3
def forallBody : Prop := forall (n : Nat), add n 0 = n
def patternLet (n : Nat) : Nat := let (a, b) : Nat × Nat := (add n 1, n); add a b
def patternIf (n : Nat) : Nat := if let some (Nat.succ k) := some (add n 1) then add k 1 else add n 0
'''
ps += '''function tupleValue(n: Nat): Nat × Nat := (add(n, 1), n)
function listValue(n: Nat): List(Nat) := [add(n, 1), n,]
function arrayValue(n: Nat): Array(Nat) := #[add(n, 1), n,]
function interpolationValue(n: Nat): String := s!"value:{add(n, 1)}"
const forallDomain: Prop := ∀ (n : Fin(add(1, 2))), n.val < 3
const forallBody: Prop := forall (n : Nat), add(n, 0) = n
function patternLet(n: Nat): Nat := let (a, b) : Nat × Nat := (add(n, 1), n); add(a, b)
function patternIf(n: Nat): Nat := if let some (Nat.succ k) := some(add(n, 1)) then add(k, 1) else add(n, 0)
'''
guards += '''private theorem tupleValueResult : tupleValue 2 = (3, 2) := rfl
private theorem listValueResult : listValue 2 = [3, 2] := rfl
private theorem arrayValueResult : arrayValue 2 = #[3, 2] := rfl
private theorem interpolationValueResult : interpolationValue 2 = s!"value:{3}" := rfl
private theorem forallDomainResult : forallDomain = (∀ (n : Fin 3), n.val < 3) := rfl
private theorem forallBodyResult : forallBody = (∀ (n : Nat), n = n) := rfl
private theorem patternLetResult : patternLet 2 = 5 := rfl
private theorem patternIfResult : patternIf 2 = 3 := rfl
'''


native += '''def constructorValue (n : Nat) : Nat × Nat := ⟨add n 1, n⟩
def showValue (n : Nat) : Nat := show Nat from add n 1
def showType (n : Nat) : Fin (add n 1) := show Fin (add n 1) from ⟨0, Nat.zero_lt_succ n⟩
def showBy (n : Nat) : Nat := show Nat by exact add n 1
def pureHave (n : Nat) : Nat := have step (x : Nat := add n 1) : Nat := add x 1; step
def whileValue (n : Nat) : IO Nat := do
  let mut result := n
  while h : result < add n 2 do
    result := add result 1
  return result
def repeatValue (n : Nat) : IO Nat := do
  let mut result := n
  repeat
    result := add result 1
  until result == add n 2
  return result
'''
ps += '''function constructorValue(n: Nat): Nat × Nat := ⟨add(n, 1), n⟩
function showValue(n: Nat): Nat := show Nat from add(n, 1)
function showType(n: Nat): Fin(add(n, 1)) := show Fin(add(n, 1)) from ⟨0, Nat.zero_lt_succ(n)⟩
function showBy(n: Nat): Nat := show Nat by exact add(n, 1)
function pureHave(n: Nat): Nat := have step (x: Nat := add(n, 1)): Nat := add(x, 1); step
function whileValue(n: Nat): IO(Nat) := do
  let mut result := n
  while h : result < add(n, 2) do
    result := add(result, 1)
  return result
function repeatValue(n: Nat): IO(Nat) := do
  let mut result := n
  repeat
    result := add(result, 1)
  until result == add(n, 2)
  return result
'''
guards += '''private theorem constructorValueResult : (constructorValue 2).1 = 3 := rfl
private theorem showValueResult : showValue 2 = 3 := rfl
private theorem showTypeResult : (showType 2).val = 0 := rfl
private theorem showByResult : showBy 2 = 3 := rfl
private theorem pureHaveResult : pureHave 2 = 4 := rfl
'''


def run(args, label):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=300)
    text = result.stdout + result.stderr
    (work / (label + '.log')).write_text(text)
    print(text, end='', flush=True)
    assert result.returncode == 0, (label, result.returncode)
    return text


comparisons = {}
run(['lake', 'env', 'lean', 'tests/debug-native-dependent-if.lean'], 'native-dependent-if')
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
        assert len(rows) == 91 and all(d['mode'] == 'mapped-ps' for d in rows)
        by_name = {row['sourceName']: row for row in rows}
        assert 'Lean.Parser.Term.doWhile' in by_name['whileValue']['ownedDoElementKinds']
        assert 'Lean.Parser.Term.doRepeatUntil' in by_name['repeatValue']['ownedDoElementKinds']
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
    comparisons=comparisons, mapped_definitions=48, mapped_theorems=43, logical_imports=['Init'],
    native_patterns_preserved=True, prepared_source_identity=True,
    source_origin_fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
    source_origin_cases=32, independently_owned_native_dsl=True, native_quotation=True,
    native_executable_sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
    runtime_oracle='PS0_HOST_ORIGINS: PASS',
    scope='finite native term/do matches, patterns/records/conditions/bindings/loop values, collections/interpolation/forall, ascriptions/direct tactics; loop contracts and deeper ordinary roles remain open',
    grammar_migration_complete=False, verified_execution=False), indent=2) + '\n')
print('PS0_MATCH_HOST_NATIVE_PARITY: PASS', flush=True)
