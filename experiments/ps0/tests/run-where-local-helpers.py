#!/usr/bin/env python3
"""Test-first probe for R2 braced local helper grammar; not yet a primary qualification gate."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('where-local-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout


fixture = Path('tests/v1/where_local_helpers.ps')
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'WhereLocal', work / 'native'], 'native')
oracle = 'PS0_WHERE_LOCAL:7:5:4:4:5'
proof_oracle = 'PS0_WHERE_PROOF:5:7:5:6:7:7'
runtime = run([work / 'native/WhereLocal'], 'runtime')
assert oracle in runtime and proof_oracle in runtime
baseline = '''def add (x y : Nat) : Nat := x + y
structure LocalPoint where
  x : Nat
  y : Nat
def defaultHelper (n : Nat) : Nat := helper n
where
  helper (x : Nat) (y : Nat := add 1 2) : Nat := add x y
def capturedHelper (n : Nat) : Nat := helper 1
where
  /-- Preserve local helper documentation and its permitted attribute. -/
  @[inline] helper (x : Nat) : Nat := add n x
def equationHelper (n : Nat) : Nat := helper 0 n 0
where
  helper (offset value : Nat) : Nat → Nat
    | 0 => add offset value
    | Nat.succ k => helper offset value k
def recordHelper (n : Nat) : Nat := (helper n).x
where
  helper (k : Nat) : LocalPoint := { x := k, y := 0 }
def forwardHelper (n : Nat) : Nat := first n
where
  first (x : Nat) : Nat := second x
  second (x : Nat) : Nat := add x 1
def namedProof (n : Nat) : Nat := ?value
where
finally
  exact add n 1
'''
migrated = '''function add(x: Nat, y: Nat): Nat := x + y
structure LocalPoint where
  x : Nat
  y : Nat
function defaultHelper(n: Nat): Nat := helper(n)
where { def helper(x: Nat, y: Nat := add(1, 2)): Nat := add(x, y) }
function capturedHelper(n: Nat): Nat := helper(1)
where {
  /-- Preserve local helper documentation and its permitted attribute. -/
  @[inline] def helper(x: Nat): Nat := add(n, x)
}
function equationHelper(n: Nat): Nat := helper(0, n, 0)
where {
  def helper(offset: Nat, value: Nat): Nat → Nat
    | 0 => add(offset, value)
    | Nat.succ k => helper(offset, value, k)
}
function recordHelper(n: Nat): Nat := helper(n).x
where { def helper(k: Nat): LocalPoint where { x := k; y := 0 } }
function forwardHelper(n: Nat): Nat := first(n)
where {
  def first(x: Nat): Nat := second(x)
  def second(x: Nat): Nat := add(x, 1)
}
function namedProof(n: Nat): Nat := ?value
where { finally { exact(add(n, 1)) } }
'''
bootstrap_comparisons = {}
bootstrap_roles = []
for label, text in [('baseline', baseline), ('migrated', migrated)]:
    source_root = work / (label + '-source')
    source_root.mkdir()
    source = source_root / 'WhereLocalBootstrap.ps'
    source.write_text('module\nprelude\npublic import Init\npublic section\n' + text)
    shutil.copy2(source, work / (label + '-WhereLocalBootstrap.ps'))
    header = json.loads(run([ROOT / '.lake/build/bin/ps0', 'lake-header', source], label + '-header'))
    assert [entry['module'] for entry in header['imports']] == ['Init']
    directory = work / (label + '-bootstrap')
    args = ['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceRoot=' + str(source_root),
            '-Kroots=WhereLocalBootstrap', '-KmoduleNames=WhereLocalBootstrap',
            '-Kdriver=' + str(ROOT / '.lake/build/bin/ps0'),
            '-KprojectBuildDir=' + str(directory), '-Kbootstrap=true']
    if label == 'migrated':
        native_args = [arg if not arg.startswith('-KprojectBuildDir=') else
                       '-KprojectBuildDir=' + str(work / 'native-rejects-migrated') for arg in args]
        run([*native_args, 'build', 'WhereLocalBootstrap'], 'native-rejects-migrated', ok=False)
        args += ['-KsourceGrammar=true']
    run([*args, 'build', 'WhereLocalBootstrap'], label + '-bootstrap')
    source_map = directory / 'lib/lean/WhereLocalBootstrap.ilean.ps0-source-map.json'
    mapping = json.loads(source_map.read_text())
    assert mapping['source'].encode() == source.read_bytes()
    assert all(segment['kind'] == 'original' for segment in mapping['segments'])
    shutil.copy2(source_map, work / (label + '-bootstrap-source-map.json'))
    if label == 'migrated':
        census_path = directory / 'lib/lean/WhereLocalBootstrap.ilean.ps0-source-census.json'
        census = json.loads(census_path.read_text())
        bootstrap_roles = [row['declaration'] for row in census['commands'] if row['declaration']]
        assert len(bootstrap_roles) == 7 and all(row['mode'] == 'mapped-ps' for row in bootstrap_roles)
        by_name = {row['sourceName']: row for row in bootstrap_roles}
        assert by_name['forwardHelper']['whereHelperNames'] == ['first', 'second']
        assert by_name['capturedHelper']['whereHelperDocCount'] == 1
        assert by_name['capturedHelper']['whereHelperAttributeCount'] == 1
        assert by_name['recordHelper']['whereHelperValueKinds'] == ['PS0.StandardAdapters.psWhereLocalRecord']
        assert by_name['equationHelper']['whereHelperValueKinds'] == ['PS0.StandardAdapters.psWhereLocalEquations']
        assert by_name['namedProof']['whereFinallyKind'] == 'PS0.StandardAdapters.psWhereFinallyNative'
        assert by_name['namedProof']['whereFinallySectionNames'] == []
        shutil.copy2(census_path, work / 'migrated-bootstrap-source-census.json')
    for relative in ['ir/WhereLocalBootstrap.c', 'lib/lean/WhereLocalBootstrap.olean']:
        path = directory / relative
        bootstrap_comparisons.setdefault(relative, {})[label] = hashlib.sha256(path.read_bytes()).hexdigest()
        shutil.copy2(path, work / (label + '-WhereLocalBootstrap' + path.suffix))
assert all(pair['baseline'] == pair['migrated'] for pair in bootstrap_comparisons.values())
print('PS0_WHERE_LOCAL_PRELUDE_NATIVE_PARITY: PASS', flush=True)
prefix = 'abbrev Box (α : Type) : Type := α\nfunction add(x: Nat, y: Nat): Nat := x + y\n'
for name, source in [
    ('type-gap', 'function bad(n: Nat): Nat := helper(n)\nwhere { def helper(x: Box (Nat), y: Nat): Nat := add(x, y) }\n'),
    ('default-gap', 'function bad(n: Nat): Nat := helper(n)\nwhere { def helper(x: Nat, y: Nat := add (1, 2)): Nat := add(x, y) }\n'),
    ('body-gap', 'function bad(n: Nat): Nat := helper(n)\nwhere { def helper(x: Nat): Nat := add (x, 1) }\n'),
    ('nested-helper-tail', 'function bad(n: Nat): Nat := helper(n)\nwhere { def helper(x: Nat): Nat := x where { def nested(y: Nat): Nat := y } }\n'),
    ('attached-helper-finally', 'function bad(n: Nat): Nat := helper(n)\nwhere { def helper(x: Nat): Nat := ?value finally { exact(1) } }\n'),
    ('unsolved-hole', 'function bad(n: Nat): Nat := ?value\nwhere { finally { } }\n'),
    ('bad-proof', 'function bad(n: Nat): Nat := ?value\nwhere { finally { exact("wrong") } }\n'),
    ('ordinary-named-sections', 'function bad(n: Nat): Nat := ?value\nwhere { finally { | value => { exact(1) } | value => { exact(2) } } }\n'),
    ('anonymous-helper', 'function bad(n: Nat): Nat := n\nwhere { def (x: Nat): Nat := x }\n'),
    ('empty-helper', 'function bad(n: Nat): Nat := helper()\nwhere { def helper(): Nat := 1 }\n'),
]:
    path = work / (name + '.ps')
    path.write_text(prefix + source)
    diagnostic = run(['lake', 'exe', 'ps0', 'check', path], name, ok=False)
    if name in ['type-gap', 'default-gap', 'body-gap']:
        assert 'PS0V1-CALL-GAP' in diagnostic
    if name == 'ordinary-named-sections':
        assert 'does not currently support any named sub-sections' in diagnostic
native_sections = work / 'native-ordinary-named-sections.ps'
native_sections.write_text('module\nprelude\npublic import Init\npublic section\n'
                           'def bad (n : Nat) : Nat := ?value\nwhere\nfinally\n| value => exact 1\n')
native_diagnostic = run([ROOT / '.lake/build/bin/ps0', 'check', native_sections],
                        'native-ordinary-named-sections', ok=False)
assert 'does not currently support any named sub-sections' in native_diagnostic
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': oracle, 'proof_oracle': proof_oracle,
    'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
    'rejection_cases': 10,
    'prelude_native_parity': bootstrap_comparisons,
    'prelude_logical_imports': ['Init'], 'prelude_mapped_definitions': 7,
    'mapped_where_roles': bootstrap_roles,
    'ordinary_named_sections_match_native_rejection': True,
    'scope': 'finite braced/native where helper/default/capture/equation/record/body-wrapper/mutual-visibility and enclosing finally proof cases; not full signature/contract grammar',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_WHERE_LOCAL_HELPERS: PASS', flush=True)
