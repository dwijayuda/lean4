#!/usr/bin/env python3
# Copyright (c) 2026 Dwijayuda. All rights reserved.
# Released under Apache 2.0 license as described in LICENSE.
"""Map the tracked ProofScript corpus to Lean and Lake module paths."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil

from native_compiler_prefix import LEAN, beneath, sha

PROJECT = PurePosixPath('experiments/ps0')


def module_path(module):
    assert '/' not in module and '\\' not in module and all(module.split('.')), module
    return PurePosixPath(*module.split('.')).with_suffix('.ps')


def definition_digest(sequence):
    data = json.dumps(list(sequence), ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def canonical_paths(inventory, modules):
    assert inventory['leanCommit'] == LEAN and len(inventory['entries']) == inventory['count']
    expected = {}
    for entry in inventory['entries']:
        path = PurePosixPath(entry['repositoryPath'])
        assert path.parts[0] == 'src' and '..' not in path.parts and path.suffix == '.lean', path
        assert entry['module'] not in expected, entry['module']
        expected[entry['module']] = path.with_suffix('.ps').as_posix()
    assert expected.keys() <= set(modules)
    assert {'PS0', 'PS0Main'} <= set(modules)
    for module in sorted(set(modules) - expected.keys()):
        assert module in ['PS0', 'PS0Main'] or module.startswith('PS0.'), module
        expected[module] = (PROJECT / module_path(module)).as_posix()
    return expected


def read_canonical_corpus(repo, catalog, inventory):
    data = json.loads(catalog.read_text(encoding='utf-8'))
    assert data['schema'] == 'ps0-canonical-compiler-corpus/1' and data['leanCommit'] == LEAN
    modules = data['modules']
    expected = canonical_paths(inventory, modules)
    for module, item in modules.items():
        assert item['path'] == expected[module], ('canonical repository path', module)
        for field in ['ps_sha256', 'original_sha256', 'definition_sha256']:
            assert re.fullmatch('[0-9a-f]{64}', item[field]), (module, field)
        for field in ['definition_count', 'data_declarations', 'initialization_commands']:
            assert type(item[field]) is int and item[field] >= 0, (module, field)
        path = beneath(repo, item['path'])
        assert path.is_file() and not path.is_symlink() and sha(path) == item['ps_sha256'], ('canonical source hash', module)
    project = repo / PROJECT
    roots = [repo / 'src', project / 'PS0']
    assert not any(next(root.rglob('*.lean'), None) for root in roots), 'native compiler source under the canonical roots'
    assert not any((project / name).is_file() for name in ['PS0.lean', 'PS0Main.lean']), 'native compiler source at the PS0 root'
    paths = {p.relative_to(repo).as_posix() for root in roots for p in root.rglob('*.ps')}
    paths.update((PROJECT / name).as_posix() for name in ['PS0.ps', 'PS0Main.ps'] if (project / name).is_file())
    assert paths == set(expected.values()), 'canonical compiler path inventory differs from the catalog'
    return modules


def stage_canonical_corpus(repo, modules, destination):
    destination.mkdir(parents=True, exist_ok=False)
    inputs = {}
    for module, item in sorted(modules.items()):
        source = beneath(repo, item['path'])
        target = destination / module_path(module)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        assert sha(target) == item['ps_sha256'], ('staged canonical source hash', module)
        inputs[module] = dict(original=PurePosixPath(item['path']).with_suffix('.lean').as_posix(),
                              canonical_path=item['path'], ps=str(target), original_sha256=item['original_sha256'],
                              ps_sha256=item['ps_sha256'], body_mode='planned-ps-grammar')
    return inputs
