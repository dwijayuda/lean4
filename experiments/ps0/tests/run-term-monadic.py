#!/usr/bin/env python3
"""Compare native monadic term grammar and PS roles through native Lake and linking."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

if len(sys.argv) != 1:
    raise SystemExit('run-term-monadic.py accepts no arguments')

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('term-monadic-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
module = 'TermMonadicBootstrap'
header = 'module\nprelude\npublic import Init\npublic section\n'
native = '''def pairSum (p : Nat × Nat) : Nat := p.1 + p.2
def pairSumM (p : Nat × Nat) : Id Nat := pure (pairSum p)
def nestedValue (n : Nat) : Id Nat := do
  let result := (← pairSumM (n, 1))
  return result
def returnValue (n : Nat) : Id Nat := return pairSum (n, 1)
def tryValue (n : Nat) : IO Nat := try
  return pairSum (n, 1)
catch _ =>
  return n
def caughtValue (n : Nat) : IO Nat := try
  throw (IO.userError "expected")
catch _ =>
  return pairSum (n, 1)
def forValue (n : Nat) : IO Nat := do
  let result ← IO.mkRef n
  let loop : IO Unit := for _ in [0:1] do
    result.modify (fun k => pairSum (k, 1))
  loop
  result.get
private theorem nestedResult : Id.run (nestedValue 2) = 3 := rfl
private theorem returnResult : Id.run (returnValue 2) = 3 := rfl
'''
ps = '''function pairSum(p: Nat × Nat): Nat := p.1 + p.2
function pairSumM(p: Nat × Nat): Id(Nat) := pure(pairSum(p))
function nestedValue(n: Nat): Id(Nat) := do
  let result := (← pairSumM((n, 1)))
  return result
function returnValue(n: Nat): Id(Nat) := return pairSum((n, 1))
function tryValue(n: Nat): IO(Nat) := try
  return pairSum((n, 1))
catch _ =>
  return n
function caughtValue(n: Nat): IO(Nat) := try
  throw(IO.userError("expected"))
catch _ =>
  return pairSum((n, 1))
function forValue(n: Nat): IO(Nat) := do
  let result ← IO.mkRef(n)
  let loop : IO(Unit) := for _ in [0:1] do
    result.modify(fun k => pairSum((k, 1)))
  loop
  result.get
private theorem nestedResult : Id.run(nestedValue(2)) = 3 := rfl
private theorem returnResult : Id.run(returnValue(2)) = 3 := rfl
'''
native_main = '''def main : IO Unit := do
  unless Id.run (nestedValue 2) == 3 && Id.run (returnValue 2) == 3 do
    throw (IO.userError "PS0_TERM_MONADIC_PURE")
  unless (← tryValue 2) == 3 && (← caughtValue 2) == 3 && (← forValue 2) == 3 do
    throw (IO.userError "PS0_TERM_MONADIC_IO")
  IO.println "PS0_TERM_MONADIC: PASS"
'''
ps_main = '''def main : IO Unit := do
  unless Id.run(nestedValue(2)) == 3 && Id.run(returnValue(2)) == 3 do
    throw(IO.userError("PS0_TERM_MONADIC_PURE"))
  unless (← tryValue(2)) == 3 && (← caughtValue(2)) == 3 && (← forValue(2)) == 3 do
    throw(IO.userError("PS0_TERM_MONADIC_IO"))
  IO.println "PS0_TERM_MONADIC: PASS"
'''


def run(args, name):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=300)
    output = result.stdout + result.stderr
    (work / (name + '.log')).write_text(output)
    print(output, end='', flush=True)
    assert result.returncode == 0, (name, result.returncode)
    return output


comparisons = {}
for label, body in [('baseline', native + native_main), ('migrated', ps + ps_main), ('planned', None)]:
    source_root = work / (label + '-source')
    source_root.mkdir()
    source = source_root / (module + '.ps')
    source.write_text((work / 'planned-source.ps').read_text() if body is None else header + body)
    shutil.copy2(source, work / (label + '-source.ps'))
    build = work / (label + '-build')
    args = ['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceRoot=' + str(source_root),
            '-Kroots=' + module, '-KmoduleNames=' + module, '-KrootModule=' + module,
            '-Kdriver=' + str(ROOT / '.lake/build/bin/ps0'),
            '-KprojectBuildDir=' + str(build)]
    if label != 'baseline':
        args.append('-KsourceGrammar=true')
    run([*args, 'build', module], label)
    census = build / ('lib/lean/' + module + '.ilean.ps0-source-census.json')
    mapping = build / ('lib/lean/' + module + '.ilean.ps0-source-map.json')
    observed, mapped = json.loads(census.read_text()), json.loads(mapping.read_text())
    assert observed['imports'] == ['Init']
    assert mapped['source'].encode() == source.read_bytes()
    assert all(segment['kind'] == 'original' for segment in mapped['segments'])
    shutil.copy2(census, work / (label + '-census.json'))
    shutil.copy2(mapping, work / (label + '-map.json'))
    if label == 'baseline':
        run(['python3', 'tests/migrate-compiler-heads.py', census, source,
             work / 'planned-source.ps', '--plan', work / 'plan.json'], 'plan')
    else:
        rows = [row['declaration'] for row in observed['commands'] if row['declaration']]
        assert len(rows) == 10 and all(row['mode'] == 'mapped-ps' for row in rows)
    for relative in ['ir/' + module + '.c', 'lib/lean/' + module + '.olean']:
        file = build / relative
        comparisons.setdefault(relative, {})[label] = hashlib.sha256(file.read_bytes()).hexdigest()
        shutil.copy2(file, work / (label + file.suffix))
    if label == 'planned':
        run([*args, 'build', 'ps0project'], 'native-link')
        executable = build / 'bin/ps0project'
        assert run([executable], 'runtime').strip() == 'PS0_TERM_MONADIC: PASS'
        shutil.copy2(executable, work / 'TermMonadicRuntime')
assert all(value['baseline'] == value['migrated'] == value['planned'] for value in comparisons.values())
(work / 'evidence.json').write_text(json.dumps(dict(source=os.environ['PS0_SOURCE_SHA'],
    logical_imports=['Init'], mapped_definitions=8, mapped_theorems=2, comparisons=comparisons,
    native_executable_sha256=hashlib.sha256((work / 'TermMonadicRuntime').read_bytes()).hexdigest(),
    runtime='PS0_TERM_MONADIC: PASS', private_rfl_guards=2,
    scope='finite nested action and native return/try/for term roles; native exception and reference-loop runtime',
    grammar_migration_complete=False, verified_execution=False), indent=2) + '\n')
print('PS0_TERM_MONADIC_NATIVE_PARITY: PASS', flush=True)
