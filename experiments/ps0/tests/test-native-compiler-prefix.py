#!/usr/bin/env python3
"""Synthetic artifact contracts only; fixtures are never executed or compiler qualification."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from native_compiler_prefix import LEAN, beneath, verify_compiler_prefix

SOURCE = 'a' * 40


def digest(data):
    return hashlib.sha256(data).hexdigest()


class CompilerPrefixIdentity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.driver = b'\x7fELF synthetic nonexecutable contract fixture\n'
        self.write('compiler-prefix/bin/ps0', self.driver)
        names = ['PS0.olean', 'PS0/Policy.olean', 'PS0/StandardAdapters.olean', 'PS0/Policy.ir']
        metadata = {}
        for name in names:
            data = ('synthetic metadata ' + name).encode()
            self.write('compiler-prefix/lib/lean/' + name, data)
            metadata[name] = digest(data)
        self.prefix = dict(driver='compiler-prefix/bin/ps0', metadata='compiler-prefix/lib/lean',
                           driver_sha256=digest(self.driver), metadata_sha256=metadata)
        self.host = dict(source=SOURCE, driver_sha256=digest(self.driver), host_metadata={
            name: dict(source_sha256=value, published_sha256=value) for name, value in metadata.items()})
        names = ['Init', 'Std', 'Lean', 'Lake', 'PS0', 'PS0Main']
        names += ['Lean.Fixture' + str(n) for n in range(2569 - len(names))]
        inputs = {}
        for name in names:
            data = ('module\n-- synthetic source ' + name + '\n').encode()
            self.write('transformed-source/' + name.replace('.', '/') + '.ps', data)
            inputs[name] = dict(ps_sha256=digest(data), body_mode='planned-ps-grammar')
        self.migration = dict(schema='ps0-compiler-source-migration/1', source_commit=SOURCE,
            lean_commit=LEAN, module_count=2569, inputs=inputs,
            outputs={name: dict(c_sha256='c' * 64, olean_sha256='d' * 64) for name in names},
            stage_lean_options={'ps0.sourceGrammar': True, 'interpreter.prefer_native': False},
            runtime_smoke='PASS', runtime_grammar_host=dict(status='PASS', metadata_files=len(metadata)),
            driver_sha256=digest(self.driver), compiler_prefix=self.prefix)
        self.save()

    def write(self, relative, data):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def save(self):
        host = json.dumps(self.host).encode()
        self.write('native-grammar-host.json', host)
        self.migration['runtime_grammar_host']['evidence_sha256'] = digest(host)
        self.write('migration.json', json.dumps(self.migration).encode())
        self.write('compiler-prefix/compiler-prefix.json', json.dumps(dict(
            schema='ps0-compiler-prefix/1', source_commit=SOURCE, lean_commit=LEAN, **self.prefix)).encode())

    def verify(self):
        return verify_compiler_prefix(self.root, SOURCE)

    def test_consistent_fixture_rehashes_every_source(self):
        report = self.verify()
        self.assertEqual(report['ps_sources_rehashed'], 2569)
        self.assertEqual(report['metadata_files'], 4)
        self.assertFalse(report['verified_execution'])
        self.assertFalse(report['grammar_migration_complete'])

    def test_expected_source_and_pinned_lean_required(self):
        with self.assertRaises(AssertionError):
            verify_compiler_prefix(self.root, 'b' * 40)
        self.migration['lean_commit'] = 'b' * 40
        self.save()
        with self.assertRaises(AssertionError):
            self.verify()

    def test_metadata_hash_manifest_alone_is_insufficient(self):
        del self.migration['compiler_prefix']
        self.save()
        with self.assertRaisesRegex(AssertionError, 'lacks retained'):
            self.verify()

    def test_driver_bytes_and_elf_header_required(self):
        self.write('compiler-prefix/bin/ps0', self.driver + b'corruption')
        with self.assertRaises(AssertionError):
            self.verify()
        self.write('compiler-prefix/bin/ps0', b'#!/bin/sh\n')
        self.prefix['driver_sha256'] = self.migration['driver_sha256'] = digest(b'#!/bin/sh\n')
        self.host['driver_sha256'] = self.prefix['driver_sha256']
        self.save()
        with self.assertRaises(AssertionError):
            self.verify()

    def test_missing_or_corrupt_actual_metadata_rejected(self):
        path = self.root / 'compiler-prefix/lib/lean/PS0/Policy.ir'
        original = path.read_bytes()
        path.unlink()
        with self.assertRaises(AssertionError):
            self.verify()
        path.write_bytes(original + b'changed')
        with self.assertRaises(AssertionError):
            self.verify()

    def test_extra_sdk_metadata_rejected_even_with_consistent_hashes(self):
        data = b'synthetic SDK metadata'
        self.write('compiler-prefix/lib/lean/Init.olean', data)
        self.prefix['metadata_sha256']['Init.olean'] = digest(data)
        self.host['host_metadata']['Init.olean'] = dict(source_sha256=digest(data), published_sha256=digest(data))
        self.migration['runtime_grammar_host']['metadata_files'] += 1
        self.save()
        with self.assertRaises(AssertionError):
            self.verify()

    def test_original_host_metadata_identity_required(self):
        self.host['host_metadata']['PS0/Policy.olean']['source_sha256'] = 'f' * 64
        self.save()
        with self.assertRaises(AssertionError):
            self.verify()

    def test_host_evidence_itself_is_rehashed(self):
        path = self.root / 'native-grammar-host.json'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaises(AssertionError):
            self.verify()

    def test_manifest_cannot_disagree_with_migration(self):
        path = self.root / 'compiler-prefix/compiler-prefix.json'
        manifest = json.loads(path.read_text())
        manifest['driver_sha256'] = 'f' * 64
        path.write_text(json.dumps(manifest))
        with self.assertRaises(AssertionError):
            self.verify()

    def test_incomplete_or_unqualified_graph_rejected(self):
        for key in ['runtime_smoke', 'module_count']:
            original = self.migration[key]
            self.migration[key] = 'PENDING'
            self.save()
            with self.assertRaises(AssertionError):
                self.verify()
            self.migration[key] = original
        self.migration['stage_lean_options']['ps0.sourceGrammar'] = False
        self.save()
        with self.assertRaises(AssertionError):
            self.verify()

    def test_source_bytes_are_verified_not_only_declared_hashes(self):
        self.write('transformed-source/Lean/Fixture1337.ps', b'changed')
        with self.assertRaises(AssertionError):
            self.verify()

    def test_native_source_and_unplanned_source_rejected(self):
        self.write('transformed-source/Native.lean', b'module\n')
        with self.assertRaises(AssertionError):
            self.verify()
        (self.root / 'transformed-source/Native.lean').unlink()
        self.migration['inputs']['PS0']['body_mode'] = 'native-header-adapter'
        self.save()
        with self.assertRaises(AssertionError):
            self.verify()

    def test_artifact_paths_cannot_escape_root(self):
        for relative in ['../escape', '/escape', 'a/../../escape', 'a\\escape', 'a//b']:
            with self.subTest(relative=relative), self.assertRaises(AssertionError):
                beneath(self.root, relative)
        (self.root / 'outside-link').symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaises(AssertionError):
            beneath(self.root, 'outside-link/escape')


if __name__ == '__main__':
    unittest.main(verbosity=2)
