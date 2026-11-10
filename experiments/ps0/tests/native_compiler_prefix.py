#!/usr/bin/env python3
# Copyright (c) 2026 Dwijayuda. All rights reserved.
# Released under Apache 2.0 license as described in LICENSE.
"""Verify retained PS-built stage inputs before executing a subsequent compiler stage."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re

LEAN = 'eb6cafb7290e8bd5f2937522d8d804f58f02bafc'


def beneath(root, relative):
    assert isinstance(relative, str) and relative and '\\' not in relative
    parts = relative.split('/')
    assert not PurePosixPath(relative).is_absolute() and all(p not in ['', '.', '..'] for p in parts)
    path = root.joinpath(*parts)
    assert path.resolve().is_relative_to(root.resolve()), relative
    return path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_compiler_prefix(root, expected_source):
    root = Path(root).resolve()
    assert re.fullmatch('[0-9a-f]{40}', expected_source), expected_source
    migration = json.loads((root / 'migration.json').read_text())
    assert migration['schema'] == 'ps0-compiler-source-migration/1'
    assert migration['source_commit'] == expected_source and migration['lean_commit'] == LEAN
    assert migration['module_count'] == len(migration['inputs']) == len(migration['outputs']) == 2569
    assert migration['inputs'].keys() == migration['outputs'].keys()
    assert {'Init', 'Std', 'Lean', 'Lake', 'PS0', 'PS0Main'} <= migration['inputs'].keys()
    assert migration['stage_lean_options']['ps0.sourceGrammar'] is True
    assert migration['stage_lean_options']['interpreter.prefer_native'] is False
    assert migration['runtime_smoke'] == 'PASS' and migration['runtime_grammar_host']['status'] == 'PASS'
    assert 'compiler_prefix' in migration, 'stage artifact lacks retained PS-built compiler prefix'
    prefix = migration['compiler_prefix']
    assert prefix['driver'] == 'compiler-prefix/bin/ps0'
    assert prefix['metadata'] == 'compiler-prefix/lib/lean'
    driver, metadata = [beneath(root, prefix[key]) for key in ['driver', 'metadata']]
    assert driver.read_bytes().startswith(b'\x7fELF')
    assert sha(driver) == prefix['driver_sha256'] == migration['driver_sha256']
    manifest = json.loads((root / 'compiler-prefix/compiler-prefix.json').read_text())
    assert manifest['schema'] == 'ps0-compiler-prefix/1'
    assert manifest['source_commit'] == expected_source and manifest['lean_commit'] == LEAN
    assert all(manifest[key] == value for key, value in prefix.items())
    host_file = root / 'native-grammar-host.json'
    host = json.loads(host_file.read_text())
    assert sha(host_file) == migration['runtime_grammar_host']['evidence_sha256']
    assert host['source'] == expected_source and host['driver_sha256'] == sha(driver)
    expected = prefix['metadata_sha256']
    assert set(expected) == set(host['host_metadata'])
    assert len(expected) == migration['runtime_grammar_host']['metadata_files']
    assert {'PS0.olean', 'PS0/Policy.olean', 'PS0/StandardAdapters.olean'} <= set(expected)
    assert {str(p.relative_to(metadata)).replace('\\', '/') for p in metadata.rglob('*') if p.is_file()} == set(expected)
    for relative, digest in expected.items():
        parts = PurePosixPath(relative).parts
        assert parts[0] == 'PS0' or PurePosixPath(relative).name.startswith('PS0.'), relative
        assert '.olean' in relative or '.ir' in relative, relative
        assert sha(beneath(metadata, relative)) == digest
        assert host['host_metadata'][relative]['source_sha256'] == digest
        assert host['host_metadata'][relative]['published_sha256'] == digest
    transformed = root / 'transformed-source'
    for module, item in migration['inputs'].items():
        assert '/' not in module and '\\' not in module and all(module.split('.'))
        assert item['body_mode'] == 'planned-ps-grammar', module
        relative = '/'.join(module.split('.')) + '.ps'
        assert sha(beneath(transformed, relative)) == item['ps_sha256'], module
        assert all(re.fullmatch('[0-9a-f]{64}', migration['outputs'][module][key])
                   for key in ['c_sha256', 'olean_sha256']), module
    assert not list(transformed.rglob('*.lean'))
    assert len(list(transformed.rglob('*.ps'))) == 2569
    return dict(schema='ps0-verified-stage-prefix/1', source=expected_source,
        driver=str(driver), metadata=str(metadata), migration=str(root / 'migration.json'), driver_sha256=sha(driver),
        metadata_files=len(expected), ps_sources_rehashed=2569,
        scope='Artifact identity and retained stage prerequisites only; no new compilation or fixed-point result',
        grammar_migration_complete=False, verified_execution=False)
