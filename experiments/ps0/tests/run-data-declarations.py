#!/usr/bin/env python3
"""Compare data signature/default operands through native Lake and linking."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

if len(sys.argv) != 1:
    raise SystemExit('run-data-declarations.py accepts no arguments')

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('data-declarations-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
module = 'DataDeclarationsBootstrap'
header = 'module\nprelude\npublic import Init\npublic section\n'
native = '''def pairSum (p : Nat × Nat) : Nat := p.1 + p.2
structure DataPacket (limit : Nat := pairSum (1, 2)) where
  value : Fin (pairSum (limit, 1))
  count : Nat := pairSum (limit, 2)
  method (n : Nat := pairSum (limit, 3)) : Nat := pairSum (n, limit)
class DataClass where
  value : Nat := pairSum (1, 2)
inductive DataBox (limit : Nat := pairSum (1, 2)) where
  | mk (value : Fin (pairSum (limit, 1))) : DataBox limit
def packet : DataPacket := { value := ⟨1, by decide⟩ }
def classValue : DataClass := {}
def box : DataBox := .mk ⟨1, by decide⟩
private theorem packetCount : packet.count = 5 := rfl
private theorem packetMethod : packet.method = 9 := rfl
private theorem classDefault : classValue.value = 3 := rfl
'''
ps = '''function pairSum(p: Nat × Nat): Nat := p.1 + p.2
structure DataPacket (limit : Nat := pairSum((1, 2))) where
  value : Fin(pairSum((limit, 1)))
  count : Nat := pairSum((limit, 2))
  method (n : Nat := pairSum((limit, 3))) : Nat := pairSum((n, limit))
class DataClass where
  value : Nat := pairSum((1, 2))
inductive DataBox (limit : Nat := pairSum((1, 2))) where
  | mk (value : Fin(pairSum((limit, 1)))) : DataBox(limit)
def packet : DataPacket := { value := ⟨1, by decide⟩ }
def classValue : DataClass := {}
def box : DataBox := .mk ⟨1, by decide⟩
private theorem packetCount : packet.count = 5 := rfl
private theorem packetMethod : packet.method = 9 := rfl
private theorem classDefault : classValue.value = 3 := rfl
'''
native_main = '''def main : IO Unit := do
  unless packet.count == 5 && packet.method == 9 && classValue.value == 3 do
    throw (IO.userError "PS0_DATA_DECLARATIONS_VALUES")
  IO.println "PS0_DATA_DECLARATIONS: PASS"
'''
ps_main = '''def main : IO(Unit) := do
  unless packet.count == 5 && packet.method == 9 && classValue.value == 3 do
    throw(IO.userError("PS0_DATA_DECLARATIONS_VALUES"))
  IO.println "PS0_DATA_DECLARATIONS: PASS"
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
        assert len(rows) == 8 and all(row['mode'] == 'mapped-ps' for row in rows)
    data_rows = [row['dataDeclaration'] for row in observed['commands'] if row['dataDeclaration']]
    assert len(data_rows) == 3
    assert all(row['mode'] == ('native-compatible' if label == 'baseline' else 'mapped-ps') for row in data_rows)
    for relative in ['ir/' + module + '.c', 'lib/lean/' + module + '.olean']:
        file = build / relative
        comparisons.setdefault(relative, {})[label] = hashlib.sha256(file.read_bytes()).hexdigest()
        shutil.copy2(file, work / (label + file.suffix))
    if label == 'planned':
        run([*args, 'build', 'ps0project'], 'native-link')
        executable = build / 'bin/ps0project'
        assert run([executable], 'runtime').strip() == 'PS0_DATA_DECLARATIONS: PASS'
        shutil.copy2(executable, work / 'DataDeclarationsRuntime')
public_constants = {}
for label in ['migrated', 'planned']:
    native_olean = work / 'baseline-build/lib/lean' / (module + '.olean')
    ps_olean = work / (label + '-build/lib/lean') / (module + '.olean')
    comparison = json.loads(run(['lake', 'env', 'lean', '--run', 'tests/compare-compiler-olean.lean',
                                 native_olean, ps_olean], label + '-public-constants'))
    # The native reader compares all matching public ConstantInfo values and
    # their exact type/value representations. Require the complete name/import
    # and extension-count summaries too; do not infer extension payload parity.
    assert comparison['changedConstants'] == []
    assert comparison['native'] == comparison['ps']
    public_constants[label] = dict(all_public_constants_equal=True,
                                  module_summary=comparison['native'],
                                  extension_payloads_compared=False)
assert len(set(comparisons['ir/' + module + '.c'].values())) == 1
assert comparisons['lib/lean/' + module + '.olean']['baseline'] == comparisons['lib/lean/' + module + '.olean']['planned']
(work / 'evidence.json').write_text(json.dumps(dict(source=os.environ['PS0_SOURCE_SHA'],
    logical_imports=['Init'], mapped_definitions=5, mapped_theorems=3, mapped_data_declarations=3, comparisons=comparisons,
    public_constant_comparisons=public_constants,
    handwritten_public_olean_byte_equal=comparisons['lib/lean/' + module + '.olean']['baseline'] == comparisons['lib/lean/' + module + '.olean']['migrated'],
    native_executable_sha256=hashlib.sha256((work / 'DataDeclarationsRuntime').read_bytes()).hexdigest(),
    runtime='PS0_DATA_DECLARATIONS: PASS', private_rfl_guards=3,
    scope='finite data operands: exact C and planned public olean; exact public constants and summaries for handwritten PS; serialized extension payload parity remains unclaimed',
    grammar_migration_complete=False, verified_execution=False), indent=2) + '\n')
print('PS0_DATA_DECLARATIONS_C_AND_PUBLIC_CONSTANTS: PASS', flush=True)
