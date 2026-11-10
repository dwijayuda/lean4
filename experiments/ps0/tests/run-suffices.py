#!/usr/bin/env python3
"""Compare native suffices grammar and PS roles through native Lake and linking."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

if len(sys.argv) != 1:
    raise SystemExit('run-suffices.py accepts no arguments')

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('suffices-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
module = 'SufficesBootstrap'
header = 'module\nprelude\npublic import Init\npublic section\n'
native = '''def pairSum (p : Nat × Nat) : Nat := p.1 + p.2
def sufficesBody (n : Nat) : Nat := suffices h : Nat from pairSum (h, 1); n
def sufficesType (n : Nat) : Nat := suffices h : (fun (_ : Nat) => Nat) (pairSum (n, 1)) from h; n
def sufficesContinuation (n : Nat) : Nat := suffices h : Nat from h; pairSum (n, 1)
def sufficesBy (n : Nat) : Nat := suffices h : Nat by { exact pairSum (h, 1) }; n
def sufficesAnonymous (n : Nat) : Nat := suffices Nat from pairSum (this, 1); n
private theorem bodyResult : sufficesBody 2 = 3 := rfl
private theorem typeResult : sufficesType 2 = 2 := rfl
private theorem continuationResult : sufficesContinuation 2 = 3 := rfl
private theorem byResult : sufficesBy 2 = 3 := rfl
private theorem anonymousResult : sufficesAnonymous 2 = 3 := rfl
'''
ps = '''function pairSum(p: Nat × Nat): Nat := p.1 + p.2
function sufficesBody(n: Nat): Nat := suffices h : Nat from pairSum((h, 1)); n
function sufficesType(n: Nat): Nat := suffices h : (fun (_ : Nat) => Nat)(pairSum((n, 1))) from h; n
function sufficesContinuation(n: Nat): Nat := suffices h : Nat from h; pairSum((n, 1))
function sufficesBy(n: Nat): Nat := suffices h : Nat by { exact pairSum((h, 1)) }; n
function sufficesAnonymous(n: Nat): Nat := suffices Nat from pairSum((this, 1)); n
private theorem bodyResult : sufficesBody 2 = 3 := rfl
private theorem typeResult : sufficesType 2 = 2 := rfl
private theorem continuationResult : sufficesContinuation 2 = 3 := rfl
private theorem byResult : sufficesBy 2 = 3 := rfl
private theorem anonymousResult : sufficesAnonymous 2 = 3 := rfl
'''
native_main = '''def main : IO Unit := do
  unless sufficesBody 2 == 3 && sufficesType 2 == 2 && sufficesContinuation 2 == 3 &&
      sufficesBy 2 == 3 && sufficesAnonymous 2 == 3 do
    throw (IO.userError "PS0_SUFFICES_RUNTIME")
  IO.println "PS0_SUFFICES: PASS"
'''
ps_main = '''def main : IO Unit := do
  unless sufficesBody(2) == 3 && sufficesType(2) == 2 && sufficesContinuation(2) == 3 &&
      sufficesBy(2) == 3 && sufficesAnonymous(2) == 3 do
    throw(IO.userError("PS0_SUFFICES_RUNTIME"))
  IO.println "PS0_SUFFICES: PASS"
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
        assert len(rows) == 12 and all(row['mode'] == 'mapped-ps' for row in rows)
    for relative in ['ir/' + module + '.c', 'lib/lean/' + module + '.olean']:
        file = build / relative
        comparisons.setdefault(relative, {})[label] = hashlib.sha256(file.read_bytes()).hexdigest()
        shutil.copy2(file, work / (label + file.suffix))
    if label == 'planned':
        run([*args, 'build', 'ps0project'], 'native-link')
        executable = build / 'bin/ps0project'
        assert run([executable], 'runtime').strip() == 'PS0_SUFFICES: PASS'
        shutil.copy2(executable, work / 'SufficesRuntime')
assert all(value['baseline'] == value['migrated'] == value['planned'] for value in comparisons.values())
(work / 'evidence.json').write_text(json.dumps(dict(source=os.environ['PS0_SOURCE_SHA'],
    logical_imports=['Init'], mapped_definitions=7, mapped_theorems=5, comparisons=comparisons,
    native_executable_sha256=hashlib.sha256((work / 'SufficesRuntime').read_bytes()).hexdigest(),
    runtime='PS0_SUFFICES: PASS', private_rfl_guards=5,
    scope='finite suffices type/from/by/continuation roles with native named and anonymous binder nodes',
    grammar_migration_complete=False, verified_execution=False), indent=2) + '\n')
print('PS0_LOOP_CONTRACT_NATIVE_PARITY: PASS', flush=True)
