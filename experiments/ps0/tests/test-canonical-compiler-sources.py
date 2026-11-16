#!/usr/bin/env python3
"""Canonical compiler paths and checkout-byte validation."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from canonical_compiler_sources import LEAN, canonical_paths, definition_digest, read_canonical_corpus, stage_canonical_corpus


class CanonicalSourceTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = Path(temporary.name)
        self.project = self.repo / 'experiments/ps0'
        self.project.mkdir(parents=True)
        self.inventory = {'leanCommit': LEAN, 'count': 2, 'entries': [
            {'module': 'Lean', 'repositoryPath': 'src/Lean.lean'},
            {'module': 'Lake.CLI.Main', 'repositoryPath': 'src/lake/Lake/CLI/Main.lean'},
        ]}
        self.payload = b'function demo(x : Nat) : Nat := x\n'
        self.paths = {'Lean': 'src/Lean.ps', 'Lake.CLI.Main': 'src/lake/Lake/CLI/Main.ps',
                      'PS0': 'experiments/ps0/PS0.ps', 'PS0Main': 'experiments/ps0/PS0Main.ps'}
        digest = hashlib.sha256(self.payload).hexdigest()
        self.modules = {name: dict(path=relative, ps_sha256=digest, original_sha256='0' * 64,
                                  definition_count=1, definition_sha256=definition_digest([('demo', 'function')]),
                                  data_declarations=0, initialization_commands=0)
                        for name, relative in self.paths.items()}
        self.manifest = self.project / 'compiler-canonical-sources.json'
        for relative in self.paths.values():
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.payload)
        self.write_catalog()

    def write_catalog(self):
        self.manifest.write_text(json.dumps(dict(schema='ps0-canonical-compiler-corpus/1', leanCommit=LEAN,
                                               modules=self.modules)), encoding='utf-8')

    def load(self):
        return read_canonical_corpus(self.repo, self.manifest, self.inventory)

    def test_checkout_bytes_staged_at_logical_lake_paths(self):
        self.assertEqual(canonical_paths(self.inventory, self.paths), self.paths)
        destination = self.repo / 'stage'
        staged = stage_canonical_corpus(self.repo, self.load(), destination)
        self.assertEqual((destination / 'Lake/CLI/Main.ps').read_bytes(), self.payload)
        self.assertEqual(staged['Lean']['canonical_path'], 'src/Lean.ps')
        self.assertEqual(staged['Lean']['body_mode'], 'planned-ps-grammar')

    def test_rejects_native_collision(self):
        (self.repo / 'src/Lean.lean').write_bytes(self.payload)
        with self.assertRaisesRegex(AssertionError, 'native compiler source'):
            self.load()

    def test_rejects_changed_bytes(self):
        (self.repo / 'src/Lean.ps').write_bytes(self.payload + b'\n')
        with self.assertRaisesRegex(AssertionError, 'canonical source hash'):
            self.load()

    def test_rejects_altered_repository_path(self):
        self.modules['Lean']['path'] = 'src/../src/Lean.ps'
        self.write_catalog()
        with self.assertRaisesRegex(AssertionError, 'canonical repository path'):
            self.load()

    def test_rejects_unlisted_compiler_source(self):
        (self.repo / 'src/Other.ps').write_bytes(self.payload)
        with self.assertRaisesRegex(AssertionError, 'canonical compiler path inventory'):
            self.load()


if __name__ == '__main__':
    unittest.main()
