#!/usr/bin/env python3
"""Independently rehash actual compiler module outputs and reconstruct source edits."""
from pathlib import Path
import argparse
import hashlib
import json

parser = argparse.ArgumentParser()
parser.add_argument('artifact', type=Path)
parser.add_argument('--source', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
sha = lambda data: hashlib.sha256(data).hexdigest()
reports = []

def declarations(commands):
    for command in commands:
        if command['declaration'] is not None:
            yield command['declaration']
        yield from declarations(command.get('nestedCommands', []))

for path in sorted(args.artifact.rglob('evidence.json')):
    if not path.parent.name.startswith('compiler-heads-'):
        continue
    root = path.parent
    evidence = json.loads(path.read_text())
    assert evidence['source'] == args.source
    module_path = Path(*evidence['module'].split('.'))
    original = (root / 'original/src' / module_path.with_suffix('.ps')).read_bytes()
    converted = (root / 'converted/src' / module_path.with_suffix('.ps')).read_bytes()
    plan = json.loads((root / 'plan.json').read_text())
    assert sha(original) == plan['source_sha256']
    assert sha(converted) == plan['result_sha256']
    chunks, cursor = [], 0
    for edit in plan['edits']:
        assert cursor <= edit['start'] <= edit['end'] <= len(original)
        assert original[edit['start']:edit['end']].decode() == edit['old']
        assert edit['old'].count('\n') == edit['new'].count('\n')
        chunks += [original[cursor:edit['start']], edit['new'].encode()]
        cursor = edit['end']
    chunks.append(original[cursor:])
    assert b''.join(chunks) == converted
    assert original.count(b'\n') == converted.count(b'\n')
    census_path = root / 'migrated/lib/lean' / module_path.with_suffix('.ilean.ps0-source-census.json')
    observed = json.loads(census_path.read_text())
    assert observed['nativeSource'].encode() == converted
    native_census = json.loads((root / 'original-census.json').read_text())
    assert native_census['nativeSource'].encode() == original
    assert observed['imports'] == native_census['imports']
    mapped = {declaration['sourceName']: declaration for declaration in declarations(observed['commands'])}
    productions = dict(function='PS0.StandardAdapters.ps0StandardFunction',
                       const='PS0.StandardAdapters.ps0StandardConst',
                       def_='PS0.StandardAdapters.ps0StandardDef')
    for strategy in plan['strategies']:
        declaration = mapped[strategy['sourceName']]
        keyword = strategy['targetKeyword']
        assert declaration['mode'] == 'mapped-ps'
        assert declaration['production'] == productions['def_' if keyword == 'def' else keyword]
    hashes = {}
    for relative, recorded in evidence['comparisons'].items():
        native, ps = (root / 'baseline' / relative).read_bytes(), (root / 'migrated' / relative).read_bytes()
        assert sha(native) == recorded['native'] == recorded['ps'] == sha(ps)
        assert native == ps
        hashes[relative] = sha(native)
    counts = {}
    for strategy in plan['strategies']:
        counts[strategy['targetKeyword']] = counts.get(strategy['targetKeyword'], 0) + 1
    report = dict(module=evidence['module'], pinned_blob=evidence['pinned_blob'],
                  definitions=len(evidence['converted_declarations']), strategies=counts,
                  equation_definitions=evidence.get('equation_definitions', []),
                  edits=len(plan['edits']), source_sha256=plan['source_sha256'],
                  converted_sha256=plan['result_sha256'], hashes=hashes,
                  mapped_census_sha256=sha(census_path.read_bytes()),
                  source_lines=original.count(b'\n'), line_count_preserved=True,
                  mapped_source_roles=evidence['mapped_source_roles'])
    reports.append(report)
assert reports, 'no retained compiler-module evidence'
args.output.write_text(json.dumps(dict(source=args.source, modules=reports,
                                      grammar_migration_complete=False, verified_execution=False), indent=2) + '\n')
print('PS0_COMPILER_ARTIFACT_REHASH:' + json.dumps(reports, sort_keys=True), flush=True)
