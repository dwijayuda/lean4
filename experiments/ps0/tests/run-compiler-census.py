#!/usr/bin/env python3
"""Join actual native command snapshots to exact PS inputs and origin maps."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import os
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('--migration', type=Path, default=Path('build/compiler-evidence/migration.json'))
parser.add_argument('--build-dir', type=Path)
parser.add_argument('--output', type=Path, default=Path('build/compiler-evidence/source-census'))
parser.add_argument('--fixture-subset', action='store_true')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
data = json.loads(args.migration.read_text())
LEAN = 'eb6cafb7290e8bd5f2937522d8d804f58f02bafc'
assert data['lean_commit'] == LEAN
inputs = data['inputs']
assert data['module_count'] == len(inputs) and inputs
if not args.fixture_subset:
    manifest = json.loads((ROOT / 'compiler-source-inventory.json').read_text())
    assert manifest['leanCommit'] == LEAN
    assert all(e['module'] in inputs for e in manifest['entries'])
build = args.build_dir or ROOT / 'build' / ('compiler-ps-' + os.environ['GITHUB_RUN_ID']) / 'artifacts'
args.output.mkdir(parents=True, exist_ok=True)
modes, heads = Counter(), Counter()
nested_modes, nested_heads = Counter(), Counter()
modules = {}

def collect_nested(commands):
    for command in commands:
        nested_heads[command['headKind']] += 1
        declaration = command['declaration']
        if declaration is not None:
            nested_modes[declaration['mode']] += 1
        collect_nested(command.get('nestedCommands', []))

for module, item in sorted(inputs.items()):
    rel = Path(*module.split('.'))
    census_file = build / 'lib/lean' / rel.with_suffix('.ilean.ps0-source-census.json')
    origin_file = build / 'lib/lean' / rel.with_suffix('.ilean.ps0-source-map.json')
    census = json.loads(census_file.read_text())
    origin = json.loads(origin_file.read_text())
    assert census['schema'] == 'ps0-native-source-census/1'
    assert census['leanCommit'] == LEAN and census['module'] == module
    assert census['file'] == origin['file'] == item['ps']
    assert census['nativeSource'] == origin['nativeSource'], ('native snapshot/source-map mismatch', module)
    prepared = origin['source'].encode()
    recovered = b''.join(prepared[s['preparedStart']:s['preparedEnd']]
                         for s in origin['segments'] if s['kind'] == 'original')
    original = Path(item['ps']).read_bytes()
    assert recovered == original, ('source origin mismatch', module)
    for command in census['commands']:
        heads[command['headKind']] += 1
        declaration = command['declaration']
        if declaration is not None:
            modes[declaration['mode']] += 1
        collect_nested(command.get('nestedCommands', []))
    retained = args.output / rel.with_suffix('.json')
    retained.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(census_file, retained)
    modules[module] = {
        'ps_sha256': hashlib.sha256(original).hexdigest(),
        'native_source_sha256': hashlib.sha256(census['nativeSource'].encode()).hexdigest(),
        'census_sha256': hashlib.sha256(census_file.read_bytes()).hexdigest(),
        'command_count': len(census['commands']),
    }
summary = {
    'schema': 'ps0-compiler-source-census/1',
    'source_commit': data['source_commit'], 'lean_commit': LEAN,
    'scope': 'fixture subset' if args.fixture_subset else 'all pinned compiler source inputs and PS0 modules',
    'module_count': len(modules), 'modules': modules,
    'declaration_modes': dict(sorted(modes.items())),
    'source_command_heads': dict(sorted(heads.items())),
    'nested_source_command_heads': dict(sorted(nested_heads.items())),
    'nested_declaration_modes': dict(sorted(nested_modes.items())),
    'nested_scope': 'explicit native in RHS and mutual command arrays only; quotations/DSL/generated data are opaque',
    'grammar_migration_complete': False,
    'verified_execution': False,
}
(args.output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print('PS0_COMPILER_SOURCE_CENSUS: PASS; modules=' + str(len(modules)) + '; modes=' + json.dumps(dict(modes)), flush=True)
