#!/usr/bin/env python3
"""Compare native loop annotation grammar and PS roles through native Lake and linking."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

if len(sys.argv) != 1:
    raise SystemExit('run-loop-contracts.py accepts no arguments')

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('loop-contracts-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
module = 'LoopContractBootstrap'
header = 'module\nprelude\npublic import Std.WP\npublic section\n'
native = '''def pairSum (p : Nat × Nat) : Nat := p.1 + p.2
def annotatedFor (n : Nat) : Id Nat := do
  let mut result := n
  for k in [n]
  invariant pref suff => pairSum (n, 1) = n + 1
  do result := pairSum (k, 1)
  return result
def annotatedType (n : Nat) : Id Nat := do
  let mut result := n
  for k in [n]
  invariant (pref : (fun (_ : Nat) => List Nat) (pairSum (n, 1))) suff => True
  do result := k
  return result
def annotatedWhile (n : Nat) : Id Nat := do
  let mut result := n
  while false
  invariant exit => pairSum (n, 1) = n + 1
  do result := n
  return result
def measuredWhile (n : Nat) : Id Nat := do
  let mut result := n
  while false
  decreasing pairSum (n, 1)
  do result := n
  return result
'''
ps = '''function pairSum(p: Nat × Nat): Nat := p.1 + p.2
function annotatedFor(n: Nat): Id(Nat) := do
  let mut result := n
  for k in [n]
  invariant pref suff => pairSum((n, 1)) = n + 1
  do result := pairSum((k, 1))
  return result
function annotatedType(n: Nat): Id(Nat) := do
  let mut result := n
  for k in [n]
  invariant (pref : (fun (_ : Nat) => List(Nat))(pairSum((n, 1)))) suff => True
  do result := k
  return result
function annotatedWhile(n: Nat): Id(Nat) := do
  let mut result := n
  while false
  invariant exit => pairSum((n, 1)) = n + 1
  do result := n
  return result
function measuredWhile(n: Nat): Id(Nat) := do
  let mut result := n
  while false
  decreasing pairSum((n, 1))
  do result := n
  return result
'''
native_main = '''def main : IO Unit := do
  unless Id.run (annotatedFor 2) == 3 && Id.run (annotatedType 2) == 2 &&
      Id.run (annotatedWhile 2) == 2 && Id.run (measuredWhile 2) == 2 do
    throw (IO.userError "PS0_LOOP_CONTRACT_RUNTIME")
  IO.println "PS0_LOOP_CONTRACTS: PASS"
'''
ps_main = '''def main : IO Unit := do
  unless Id.run(annotatedFor(2)) == 3 && Id.run(annotatedType(2)) == 2 &&
      Id.run(annotatedWhile(2)) == 2 && Id.run(measuredWhile(2)) == 2 do
    throw(IO.userError("PS0_LOOP_CONTRACT_RUNTIME"))
  IO.println "PS0_LOOP_CONTRACTS: PASS"
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
    assert observed['imports'] == ['Std.WP']
    assert mapped['source'].encode() == source.read_bytes()
    assert all(segment['kind'] == 'original' for segment in mapped['segments'])
    shutil.copy2(census, work / (label + '-census.json'))
    shutil.copy2(mapping, work / (label + '-map.json'))
    if label == 'baseline':
        run(['python3', 'tests/migrate-compiler-heads.py', census, source,
             work / 'planned-source.ps', '--plan', work / 'plan.json'], 'plan')
    else:
        rows = [row['declaration'] for row in observed['commands'] if row['declaration']]
        assert len(rows) == 6 and all(row['mode'] == 'mapped-ps' for row in rows)
    for relative in ['ir/' + module + '.c', 'lib/lean/' + module + '.olean']:
        file = build / relative
        comparisons.setdefault(relative, {})[label] = hashlib.sha256(file.read_bytes()).hexdigest()
        shutil.copy2(file, work / (label + file.suffix))
    if label == 'planned':
        run([*args, 'build', 'ps0project'], 'native-link')
        executable = build / 'bin/ps0project'
        assert run([executable], 'runtime').strip() == 'PS0_LOOP_CONTRACTS: PASS'
        shutil.copy2(executable, work / 'LoopContracts')
assert all(value['baseline'] == value['migrated'] == value['planned'] for value in comparisons.values())
(work / 'evidence.json').write_text(json.dumps(dict(source=os.environ['PS0_SOURCE_SHA'],
    logical_imports=['Std.WP'], mapped_definitions=6, comparisons=comparisons,
    native_executable_sha256=hashlib.sha256((work / 'LoopContracts').read_bytes()).hexdigest(),
    runtime='PS0_LOOP_CONTRACTS: PASS', annotations_erased_by_native_gadgets=True,
    scope='finite annotation expression/type/measure roles; runtime metadata erasure is not a proof of loop invariants',
    grammar_migration_complete=False, verified_execution=False), indent=2) + '\n')
print('PS0_LOOP_CONTRACT_NATIVE_PARITY: PASS', flush=True)
