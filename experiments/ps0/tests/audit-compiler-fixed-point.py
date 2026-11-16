#!/usr/bin/env python3
"""Rehash retained compiler artifacts and independently compare completed stage receipts."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
from native_compiler_prefix import LEAN, beneath, sha, verify_compiler_prefix


def read(root, name):
    return json.loads((root / name).read_text())


def census(root, migration):
    summary = read(root, 'source-census/summary.json')
    assert summary['schema'] == 'ps0-compiler-source-census/1'
    assert summary['source_commit'] == migration['source_commit']
    assert summary['lean_commit'] == LEAN
    assert summary['module_count'] == 2569
    assert summary['modules'].keys() == migration['inputs'].keys()
    modes, nested_modes = Counter(), Counter()

    def declarations(commands, counter):
        for command in commands:
            if command['declaration'] is not None:
                counter[command['declaration']['mode']] += 1
            declarations(command.get('nestedCommands', []), nested_modes)

    for module, item in summary['modules'].items():
        assert item['ps_sha256'] == migration['inputs'][module]['ps_sha256']
        path = beneath(root / 'source-census', '/'.join(module.split('.')) + '.json')
        assert sha(path) == item['census_sha256'], module
        observed = json.loads(path.read_text())
        assert observed['schema'] == 'ps0-native-source-census/1'
        assert observed['leanCommit'] == LEAN and observed['module'] == module
        assert observed['mappedOperandSyntaxScope'] == 'raw-command-before-native-lowering/1'
        assert hashlib.sha256(observed['nativeSource'].encode()).hexdigest() == item['native_source_sha256']
        assert len(observed['commands']) == item['command_count']
        declarations(observed['commands'], modes)
    assert dict(modes) == summary['declaration_modes']
    assert dict(nested_modes) == summary['nested_declaration_modes']
    assert not modes.get('native-compatible') and not nested_modes.get('native-compatible')
    assert (root / 'compiler-link.map').stat().st_size > 0
    return summary


def verify_fixed_point(first, second, expected_source):
    roots = [Path(first).resolve(), Path(second).resolve()]
    verified = [verify_compiler_prefix(root, expected_source) for root in roots]
    a, b = [read(root, 'migration.json') for root in roots]
    assert {k: (v['original_sha256'], v['ps_sha256']) for k, v in a['inputs'].items()} == {
        k: (v['original_sha256'], v['ps_sha256']) for k, v in b['inputs'].items()}, 'stage original/PS source identities differ'
    assert a['outputs'] == b['outputs'], 'per-module C/public olean receipts differ'
    assert b['fixed_point'] == {'changed_c': [], 'changed_olean': []}
    receipt = read(roots[1], 'stage-prefix-verification.json')
    assert receipt['schema'] == 'ps0-verified-stage-prefix/1'
    assert receipt['source'] == expected_source
    assert receipt['driver_sha256'] == verified[0]['driver_sha256']
    assert receipt['metadata_files'] == verified[0]['metadata_files']
    assert receipt['ps_sources_rehashed'] == 2569
    assert read(roots[1], 'input-inventory.json')['stage_driver_sha256'] == verified[0]['driver_sha256']
    summaries = [read(root, 'source-plan-summary.json') for root in roots]
    for summary in summaries:
        assert summary['planner_source'] == expected_source
        assert summary['module_count'] == 2569 and summary['source_grammar'] is True
    if any(summary.get('input_mode') == 'canonical-git' for summary in summaries):
        assert [summary.get('input_mode') for summary in summaries] == ['canonical-git'] * 2
        assert [summary['stage_compiler'] for summary in summaries] == [
            'retained-audited-bootstrap-prefix', 'retained-ps-built-prefix']
        catalogs = [root / 'canonical-source-catalog.json' for root in roots]
        assert sha(catalogs[0]) == sha(catalogs[1]) == summaries[0]['catalog_sha256'] == summaries[1]['catalog_sha256']
        catalog = json.loads(catalogs[0].read_text())
        assert catalog['schema'] == 'ps0-canonical-compiler-corpus/1' and catalog['leanCommit'] == LEAN
        for migration in [a, b]:
            assert migration['source_input_mode'] == 'canonical-git'
            assert migration['inputs'].keys() == catalog['modules'].keys()
            for module, item in migration['inputs'].items():
                expected = catalog['modules'][module]
                assert item['canonical_path'] == expected['path']
                assert all(item[key] == expected[key] for key in ['ps_sha256', 'original_sha256'])
        bootstrap = read(roots[0], 'bootstrap-prefix-verification.json')
        assert bootstrap['schema'] == 'ps0-verified-stage-prefix/1'
        assert bootstrap['ps_sources_rehashed'] == 2569
        assert summaries[0]['stage_driver_sha256'] == bootstrap['driver_sha256']
        assert summaries[1]['stage_driver_sha256'] == verified[0]['driver_sha256']
        metadata_mode = summaries[1]['stage_compiler']
    else:
        assert summaries[0]['self_census_metadata']['mode'] == 'isolated-sdk-assisted-preparation'
        metadata = summaries[1]['self_census_metadata']
        assert metadata['mode'] == 'retained-ps-built-prefix'
        assert metadata['stage_source'] == expected_source
        assert metadata['driver_sha256'] == verified[0]['driver_sha256']
        assert metadata['path'] == receipt['metadata']
        metadata_mode = metadata['mode']
    assert not (roots[1] / 'self-native-metadata.log').exists(), 'stage two rebuilt SDK-assisted PS0 metadata'
    snapshots = [census(root, migration) for root, migration in zip(roots, [a, b])]
    assert {m: row['native_source_sha256'] for m, row in snapshots[0]['modules'].items()} == {
        m: row['native_source_sha256'] for m, row in snapshots[1]['modules'].items()}
    return dict(schema='ps0-independent-fixed-point-artifact-audit/1', source=expected_source,
        lean_commit=LEAN, modules=2569, stages=2, ps_sources_rehashed=5138,
        mapped_censuses_rehashed=5138, driver_files_rehashed=2,
        metadata_files_rehashed=sum(row['metadata_files'] for row in verified),
        source_identity_counts=verified[0]['source_identity_counts'],
        c_and_public_olean_receipt_hashes_compared=5138,
        stage_two_metadata_mode=metadata_mode, status='PASS',
        scope='Actual retained sources/censuses/prefix files rehashed; C/public olean equality from producer receipts, not independent rehash of unretained target output files; no bit-identical final ELF or language-wide conformance claim',
        grammar_migration_complete=False, verified_execution=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('first', type=Path)
    parser.add_argument('second', type=Path)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify_fixed_point(args.first, args.second, args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print('PS0_INDEPENDENT_FIXED_POINT_ARTIFACT_AUDIT: PASS', flush=True)
