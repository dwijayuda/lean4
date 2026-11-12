#!/usr/bin/env python3
# Copyright (c) 2026 Dwijayuda. All rights reserved.
# Released under Apache 2.0 license as described in the file LICENSE.
"""Transport exact native Lake inputs/outputs; never treat a checkpoint as qualification."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import re
import shutil
import tarfile

LEAN = 'eb6cafb7290e8bd5f2937522d8d804f58f02bafc'

def graph_run_id(state):
    origin = state.get('graph_run_id', state['run_id'])
    assert re.fullmatch(r'[0-9]+', origin), origin
    assert state['work'] == 'build/compiler-ps-' + origin, state['work']
    return origin


def compiler_part_targets(modules, plan, part, previous=None):
    targets = {module for module in modules if module == 'Lean' or module.startswith('Lean.')}
    if isinstance(plan, list):
        early, middle = plan, []
    else:
        assert plan.keys() == {'early', 'middle'} and plan['middle'], 'invalid three-part plan'
        early, middle = plan['early'], plan['middle']
    first = set(early)
    second = set(middle)
    assert len(first) == len(early) and len(second) == len(middle) and first and not first & second
    preceding = first | second
    assert preceding < targets and 'Lean' not in preceding
    if part == 'early':
        return sorted(first)
    if part == 'middle':
        assert second and previous == sorted(first), 'middle partition requires the exact early checkpoint'
        return sorted(second)
    assert part == 'late' and previous == sorted(preceding), 'compiler partition changed since its checkpoint'
    return sorted(targets - preceding)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def beneath(root, relative):
    pure = PurePosixPath(relative)
    assert relative and not pure.is_absolute() and '..' not in pure.parts
    assert '\\' not in relative and '\n' not in relative and ':' not in relative
    assert pure.parts[0] in ['.lake', 'build'], relative
    path = (root / str(pure)).resolve()
    assert path.is_relative_to(root.resolve()), relative
    return path


def inventory(root, roots):
    files = {}
    for relative in roots:
        folder = beneath(root, relative)
        if not folder.exists():
            continue
        assert folder.is_dir() and not folder.is_symlink(), relative
        for path in sorted(folder.rglob('*')):
            assert not path.is_symlink(), path
            if path.is_file():
                name = path.relative_to(root).as_posix()
                assert name not in files, name
                files[name] = dict(sha256=sha(path), size=path.stat().st_size)
    return files


def seal(root, manifest, state, roots):
    root = Path(root).resolve()
    assert state['lean_commit'] == LEAN and state['source_grammar'] is True
    assert state['phase'] in ['base', 'compiler']
    assert sha(Path(state['driver'])) == state['driver_sha256']
    data = dict(schema='ps0-native-lake-build-checkpoint/1', workspace=str(root),
        state=state, roots=roots, files=inventory(root, roots),
        scope='Partial native Lake graph only; full graph/link/runtime/census and stage-two gates still required')
    assert data['files']
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(data, indent=2) + '\n')
    return data


def verify(root, manifest, *, source, phase, run_id, driver):
    root = Path(root).resolve()
    data = json.loads(Path(manifest).read_text())
    assert data['schema'] == 'ps0-native-lake-build-checkpoint/1'
    assert data['workspace'] == str(root), 'native Lake graph workspace changed'
    state = data['state']
    assert state['source_commit'] == source and state['lean_commit'] == LEAN
    assert state['phase'] == phase and state['run_id'] == str(run_id)
    assert state['source_grammar'] is True
    assert state['driver'] == str(Path(driver).resolve())
    assert sha(Path(driver)) == state['driver_sha256']
    for name in data['files']:
        beneath(root, name)
    assert inventory(root, data['roots']) == data['files'], 'checkpoint files changed, missing or added'
    return data


def pack(root, manifest, archive):
    root, manifest = Path(root).resolve(), Path(manifest).resolve()
    data = json.loads(manifest.read_text())
    verify(root, manifest, source=data['state']['source_commit'], phase=data['state']['phase'],
        run_id=data['state']['run_id'], driver=data['state']['driver'])
    archive = Path(archive)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, 'w:gz', compresslevel=1) as tar:
        for name in [manifest.relative_to(root).as_posix(), *sorted(data['files'])]:
            tar.add(beneath(root, name), arcname=name, recursive=False)


def unpack(archive, root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, 'r:gz') as tar:
        entries = tar.getmembers()
        names = [entry.name for entry in entries]
        assert len(names) == len(set(names)), 'duplicate archive member'
        for entry in entries:
            beneath(root, entry.name)
            assert entry.isfile(), 'only regular checkpoint files are admitted'
        for entry in entries:
            target = beneath(root, entry.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(entry) as src, target.open('wb') as dst:
                shutil.copyfileobj(src, dst)
            target.chmod(entry.mode & 0o777)
            os.utime(target, (entry.mtime, entry.mtime))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    packing = sub.add_parser('pack')
    packing.add_argument('root', type=Path)
    packing.add_argument('manifest', type=Path)
    packing.add_argument('archive', type=Path)
    unpacking = sub.add_parser('unpack')
    unpacking.add_argument('archive', type=Path)
    unpacking.add_argument('root', type=Path)
    args = parser.parse_args()
    if args.command == 'pack':
        pack(args.root, args.manifest, args.archive)
    else:
        unpack(args.archive, args.root)
