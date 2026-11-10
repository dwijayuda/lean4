#!/usr/bin/env python3
"""Compare initializer phases and cross-module order using native Lake artifacts/runtime."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

if len(sys.argv) != 1:
    raise SystemExit('run-initializers.py accepts no arguments')
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('initializers-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
modules = ['InitializerBase', 'InitializerMain']
header = 'module\nprelude\npublic import Init\npublic section\n'
native_base = '''def pairSum (p : Nat × Nat) : Nat := p.1 + p.2
builtin_initialize builtinLog : IO.Ref (List Nat) ← IO.mkRef []
builtin_initialize builtinMarker : Nat ← do
  builtinLog.modify (fun values => values ++ [pairSum (1, 2)])
  pure (pairSum (1, 2))
initialize ordinaryLog : IO.Ref (List Nat) ← IO.mkRef []
initialize ordinaryMarker : Nat ← do
  ordinaryLog.modify (fun values => values ++ [pairSum (1, 3)])
  pure (pairSum (2, 3))
initialize
  ordinaryLog.modify (fun values => values ++ [pairSum (2, 4)])
'''
ps_base = '''function pairSum(p: Nat × Nat): Nat := p.1 + p.2
builtin_initialize builtinLog : IO.Ref(List(Nat)) ← IO.mkRef([])
builtin_initialize builtinMarker : Nat ← do
  builtinLog.modify(fun values => values ++ [pairSum((1, 2))])
  pure(pairSum((1, 2)))
initialize ordinaryLog : IO.Ref(List(Nat)) ← IO.mkRef([])
initialize ordinaryMarker : Nat ← do
  ordinaryLog.modify(fun values => values ++ [pairSum((1, 3))])
  pure(pairSum((2, 3)))
initialize
  ordinaryLog.modify(fun values => values ++ [pairSum((2, 4))])
'''
main_header = 'module\nprelude\npublic import InitializerBase\npublic section\n'
native_main = '''initialize
  ordinaryLog.modify (fun values => values ++ [pairSum (3, 5)])
def main : IO Unit := do
  unless (← builtinLog.get) == [3] && builtinMarker == 3 do
    throw (IO.userError "PS0_INITIALIZERS_BUILTIN")
  unless (← ordinaryLog.get) == [4, 6, 8] && ordinaryMarker == 5 do
    throw (IO.userError "PS0_INITIALIZERS_ORDER")
  IO.println "PS0_INITIALIZERS: PASS"
'''
ps_main = '''initialize
  ordinaryLog.modify(fun values => values ++ [pairSum((3, 5))])
def main : IO(Unit) := do
  unless (← builtinLog.get) == [3] && builtinMarker == 3 do
    throw(IO.userError("PS0_INITIALIZERS_BUILTIN"))
  unless (← ordinaryLog.get) == [4, 6, 8] && ordinaryMarker == 5 do
    throw(IO.userError("PS0_INITIALIZERS_ORDER"))
  IO.println "PS0_INITIALIZERS: PASS"
'''


def run(args, name):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=300)
    output = result.stdout + result.stderr
    (work / (name + '.log')).write_text(output)
    print(output, end='', flush=True)
    assert result.returncode == 0, (name, result.returncode)
    return output


comparisons, executables = {}, {}
for label, bodies in [('baseline', [header + native_base, main_header + native_main]),
                      ('migrated', [header + ps_base, main_header + ps_main]),
                      ('planned', None)]:
    source_root = work / (label + '-source')
    source_root.mkdir()
    for index, module in enumerate(modules):
        source = source_root / (module + '.ps')
        source.write_text((work / ('planned-' + module + '.ps')).read_text()
                          if bodies is None else bodies[index])
        shutil.copy2(source, work / (label + '-' + module + '.ps'))
    build = work / (label + '-build')
    args = ['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceRoot=' + str(source_root),
            '-Kroots=' + ','.join(modules), '-KmoduleNames=' + ','.join(modules),
            '-KrootModule=InitializerMain', '-Kdriver=' + str(ROOT / '.lake/build/bin/ps0'),
            '-KprojectBuildDir=' + str(build)]
    if label != 'baseline':
        args.append('-KsourceGrammar=true')
    run([*args, 'build', 'ps0project'], label)
    for module in modules:
        source = source_root / (module + '.ps')
        census = build / ('lib/lean/' + module + '.ilean.ps0-source-census.json')
        mapping = build / ('lib/lean/' + module + '.ilean.ps0-source-map.json')
        observed, mapped = json.loads(census.read_text()), json.loads(mapping.read_text())
        assert observed['imports'] == (['Init'] if module == 'InitializerBase' else ['InitializerBase'])
        assert observed['initializerOperandScope'] == 'native-initializer-operands/1'
        assert mapped['source'].encode() == source.read_bytes()
        assert all(segment['kind'] == 'original' for segment in mapped['segments'])
        rows = [row['initialization'] for row in observed['commands'] if row['initialization']]
        assert len(rows) == (5 if module == 'InitializerBase' else 1)
        assert all(row['mode'] == ('native-compatible' if label == 'baseline' else 'mapped-ps')
                   for row in rows)
        for row in rows:
            syntax = row['syntax']
            assert syntax['kind'] == 'Lean.Parser.Command.initialize' and len(syntax['args']) == 4
        shutil.copy2(census, work / (label + '-' + module + '-census.json'))
        shutil.copy2(mapping, work / (label + '-' + module + '-map.json'))
        if label == 'baseline':
            run(['python3', 'tests/migrate-compiler-heads.py', census, source,
                 work / ('planned-' + module + '.ps'), '--plan', work / (module + '-plan.json')],
                'plan-' + module)
        for relative in ['ir/' + module + '.c', 'lib/lean/' + module + '.olean']:
            file = build / relative
            comparisons.setdefault(relative, {})[label] = hashlib.sha256(file.read_bytes()).hexdigest()
            shutil.copy2(file, work / (label + '-' + module + file.suffix))
    executable = build / 'bin/ps0project'
    assert run([executable], label + '-runtime').strip() == 'PS0_INITIALIZERS: PASS'
    executables[label] = hashlib.sha256(executable.read_bytes()).hexdigest()
    shutil.copy2(executable, work / (label + '-InitializerRuntime'))
assert all(value['baseline'] == value['migrated'] == value['planned'] for value in comparisons.values())
(work / 'evidence.json').write_text(json.dumps(dict(source=os.environ['PS0_SOURCE_SHA'],
    modules=modules, initialization_commands=6, comparisons=comparisons, executables=executables,
    runtime='PS0_INITIALIZERS: PASS', builtin_values=[3], ordinary_values=[4, 6, 8],
    scope='finite native builtin/ordinary named/unnamed startup phases and cross-module order',
    grammar_migration_complete=False, verified_execution=False), indent=2) + '\n')
print('PS0_INITIALIZERS_NATIVE_PARITY: PASS', flush=True)
