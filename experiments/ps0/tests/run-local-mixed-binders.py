#!/usr/bin/env python3
"""Qualify PS comma groups at native named-local telescope positions."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('local-mixed-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout


fixture = Path('tests/v1/local_mixed_binders.ps')
native_layouts = run(['lake', 'env', 'lean', 'tests/debug-local-layout.lean'], 'native-layouts')
assert native_layouts.count('PS0_NATIVE_LOCAL_LAYOUT ') == 6
assert 'PS0_LOCAL_ARRAY_UPDATE_BOUNDARY: PASS' in native_layouts
interpolation_controls = run(['lake', 'env', 'lean', 'tests/debug-interpolation-layout.lean'], 'interpolation-layout')
assert interpolation_controls.count('PS0_INTERPOLATION_CONTROL_') == 6
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'LocalMixed', work / 'native'], 'native')
oracle = 'PS0_LOCAL_MIXED:7:7:7:8:7:5'
runtime = run([work / 'native/LocalMixed'], 'runtime')
equation_oracle = 'PS0_LOCAL_EQNS:7:7'
assert oracle in runtime and equation_oracle in runtime
bootstrap_comparisons = {}
bootstrap_sources = {
    'baseline': ('def plus (x y : Nat) : Nat := x + y\n'
                 'def value : Nat := let step (x : Nat) (y : Nat := plus 1 2) : Nat := plus x y; step 4\n'),
    'migrated': ('function plus(x: Nat, y: Nat): Nat := x + y\n'
                 'const value: Nat := let step (x: Nat, y: Nat := plus(1, 2)): Nat := plus(x, y); step(4)\n'),
}
for label, text in bootstrap_sources.items():
    source_root = work / (label + '-source')
    source_root.mkdir()
    source = source_root / 'LocalMixedBootstrap.ps'
    source.write_text('module\nprelude\npublic import Init\npublic section\n' + text)
    shutil.copy2(source, work / (label + '-LocalMixedBootstrap.ps'))
    header = json.loads(run([ROOT / '.lake/build/bin/ps0', 'lake-header', source], label + '-header'))
    assert [entry['module'] for entry in header['imports']] == ['Init']
    directory = work / (label + '-bootstrap')
    args = ['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceRoot=' + str(source_root),
            '-Kroots=LocalMixedBootstrap', '-KmoduleNames=LocalMixedBootstrap',
            '-Kdriver=' + str(ROOT / '.lake/build/bin/ps0'),
            '-KprojectBuildDir=' + str(directory), '-Kbootstrap=true']
    if label == 'migrated':
        args += ['-KsourceGrammar=true']
    run([*args, 'build', 'LocalMixedBootstrap'], label + '-bootstrap')
    source_map = directory / 'lib/lean/LocalMixedBootstrap.ilean.ps0-source-map.json'
    mapping = json.loads(source_map.read_text())
    assert mapping['source'].encode() == source.read_bytes()
    assert all(segment['kind'] == 'original' for segment in mapping['segments'])
    shutil.copy2(source_map, work / (label + '-bootstrap-source-map.json'))
    if label == 'migrated':
        census_path = directory / 'lib/lean/LocalMixedBootstrap.ilean.ps0-source-census.json'
        census = json.loads(census_path.read_text())
        declarations = [row['declaration'] for row in census['commands'] if row['declaration']]
        assert len(declarations) == 2
        assert all(row['mode'] == 'mapped-ps' for row in declarations)
        assert {row['production'] for row in declarations} == {
            'PS0.StandardAdapters.ps0StandardFunction', 'PS0.StandardAdapters.ps0StandardConst'}
        shutil.copy2(census_path, work / 'migrated-bootstrap-source-census.json')
    for relative in ['ir/LocalMixedBootstrap.c', 'lib/lean/LocalMixedBootstrap.olean']:
        path = directory / relative
        bootstrap_comparisons.setdefault(relative, {})[label] = hashlib.sha256(path.read_bytes()).hexdigest()
        shutil.copy2(path, work / (label + '-LocalMixedBootstrap' + path.suffix))
assert all(pair['baseline'] == pair['migrated'] for pair in bootstrap_comparisons.values())
print('PS0_LOCAL_MIXED_PRELUDE_NATIVE_PARITY: PASS', flush=True)
prefix = 'abbrev Box (α : Type) : Type := α\nfunction add(x: Nat, y: Nat): Nat := x + y\n'
for name, declaration, reason in [
    ('type-gap', 'let step (x: Box (Nat), y: Nat): Nat := add(x, y)', 'PS0V1-CALL-GAP'),
    ('default-gap', 'let rec step (x: Nat, y: Nat := add (1, 2)): Nat := add(x, y)', 'PS0V1-CALL-GAP'),
    ('default-order', 'let step (x: Nat, y: Nat := add(x := 1, 2)): Nat := add(x, y)', 'PS0V1-CALL-ORDER'),
    ('default-type', 'let step (x: Nat, y: Nat := "bad"): Nat := add(x, y)', 'type mismatch'),
    ('empty-local', 'let step (): Nat := 1', 'Invalid pattern'),
    ('default-forward', 'let step (x: Nat, y: Nat := add(z, 1), z: Nat := 2): Nat := add(x, y)', 'Unknown identifier'),
]:
    path = work / (name + '.ps')
    path.write_text(prefix + 'const bad: Id(Nat) := do\n  ' + declaration + '\n  return step(4)\n')
    diagnostic = run(['lake', 'exe', 'ps0', 'check', path], name, ok=False)
    assert reason.lower() in diagnostic.lower(), (name, reason)
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': oracle,
    'recursive_equation_oracle': equation_oracle,
    'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
    'origin_cases': 6, 'rejection_cases': 6,
    'native_quotation_control': True, 'duplicate_partition_coalesced': True,
    'different_partition_rejected': True,
    'native_layout_controls': 6, 'array_update_boundary': 'native parser only; not an elaboration/runtime claim',
    'prelude_native_parity': bootstrap_comparisons,
    'prelude_logical_imports': ['Init'],
    'prelude_mapped_definitions': 2,
    'scope': 'finite named do/pure let and let-rec mixed/comma telescopes, native DSL control; not all local/where grammar',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_LOCAL_MIXED_BINDERS: PASS', flush=True)
