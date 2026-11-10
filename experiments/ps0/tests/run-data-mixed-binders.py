#!/usr/bin/env python3
"""Require the frozen mixed-telescope grammar at native data signature positions."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

if len(sys.argv) != 1:
    raise SystemExit('run-data-mixed-binders.py accepts no arguments')
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('data-mixed-binders-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
cases = [
    ('structure-parameters',
     'structure Mixed (left : Nat) (right : Nat) where\n  value : Fin (left + right + 1)',
     'structure Mixed (left: Nat, right: Nat) where\n  value : Fin(left + right + 1)'),
    ('class-parameters',
     'class Mixed (left : Nat) (right : Nat) where\n  value : Fin (left + right + 1)',
     'class Mixed (left: Nat, right: Nat) where\n  value : Fin(left + right + 1)'),
    ('inductive-parameters',
     'inductive Mixed (left : Nat) (right : Nat) where\n  | mk : Mixed left right',
     'inductive Mixed (left: Nat, right: Nat) where\n  | mk : Mixed(left, right)'),
    ('class-inductive-parameters',
     'class inductive Mixed (left : Nat) (right : Nat) where\n  | mk : Mixed left right',
     'class inductive Mixed (left: Nat, right: Nat) where\n  | mk : Mixed(left, right)'),
    ('coinductive-parameters',
     'coinductive Mixed (left : Nat) (right : Nat) : Prop where\n  | step : Mixed left right',
     'coinductive Mixed (left: Nat, right: Nat) : Prop where\n  | step : Mixed(left, right)'),
    ('constructor-parameters',
     'inductive Mixed where\n  | mk (left : Nat) (right : Nat) : Mixed',
     'inductive Mixed where\n  | mk (left: Nat, right: Nat) : Mixed'),
    ('field-method-parameters',
     'structure Mixed where\n  value (left : Nat) (right : Nat) : Nat := left + right',
     'structure Mixed where\n  value (left: Nat, right: Nat) : Nat := left + right'),
    ('constructor-name-parameters',
     'structure Mixed (α : Type) (β : Type) where\n  mk (α) (β) ::\n  left : α\n  right : β',
     'structure Mixed (α : Type) (β : Type) where\n  mk (α) (β) ::\n  left : α\n  right : β'),
    ('dependent-parameter-defaults',
     'structure Mixed (left : Nat := 1) (right : Nat := left + 1) where\n  value : Nat := left + right',
     'structure Mixed (left: Nat := 1, right: Nat := left + 1) where\n  value : Nat := left + right'),
]
observations = []
for name, native, ps in cases:
    header = 'module\nprelude\npublic import ' + ('Lean' if name.startswith('coinductive') else 'Init') + '\npublic section\n'
    baseline = work / (name + '-native.ps')
    baseline.write_text(header + native + '\n')
    result = subprocess.run([str(ROOT / '.lake/build/bin/ps0'), 'census-source', baseline,
                             'DataMixedBaseline', work / (name + '-native-census.json')],
                            capture_output=True, text=True, timeout=300)
    (work / (name + '-native.log')).write_text(result.stdout + result.stderr)
    folder = work / (name + '-source')
    folder.mkdir()
    (folder / 'DataMixedProbe.ps').write_text(header + ps + '\n')
    mapped = subprocess.run(['lake', '-R', '-f', 'lakefile.project.lean',
        '-KsourceRoot=' + str(folder), '-Kroots=DataMixedProbe', '-KmoduleNames=DataMixedProbe',
        '-KsourceGrammar=true', '-Kbootstrap=true', '-Kdriver=' + str(ROOT / '.lake/build/bin/ps0'),
        '-KprojectBuildDir=' + str(work / (name + '-build')), 'build', 'DataMixedProbe'],
        capture_output=True, text=True, timeout=300)
    (work / (name + '-ps.log')).write_text(mapped.stdout + mapped.stderr)
    if mapped.returncode == 0:
        build = work / (name + '-build')
        census = build / 'lib/lean/DataMixedProbe.ilean.ps0-source-census.json'
        data = json.loads(census.read_text())
        captures = [row['dataDeclaration'] for row in data['commands'] if row.get('dataDeclaration')]
        assert len(captures) == 1 and captures[0]['mode'] == 'mapped-ps'
        shutil.copy2(census, work / (name + '-ps-census.json'))
        for relative in ['ir/DataMixedProbe.c', 'lib/lean/DataMixedProbe.olean']:
            file = build / relative
            shutil.copy2(file, work / (name + file.suffix))
    row = dict(case=name, native_baseline_passed=result.returncode == 0,
               native_exit=result.returncode, ps_exit=mapped.returncode,
               mapped_passed=mapped.returncode == 0,
               native_diagnostics=(result.stdout + result.stderr).splitlines()[:6],
               ps_diagnostics=(mapped.stdout + mapped.stderr).splitlines()[:6])
    observations.append(row)
    print('PS0_DATA_MIXED_OBSERVATION:' + json.dumps(row, sort_keys=True), flush=True)
(work / 'evidence.json').write_text(json.dumps(dict(source=os.environ['PS0_SOURCE_SHA'],
    observations=observations, scope='nine native-controlled data mixed-telescope admission cases',
    grammar_migration_complete=False, verified_execution=False), indent=2) + '\n')
assert all(row['native_baseline_passed'] and row['mapped_passed'] for row in observations)
print('PS0_DATA_MIXED_BINDERS: PASS', flush=True)
