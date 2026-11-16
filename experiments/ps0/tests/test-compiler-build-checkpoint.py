#!/usr/bin/env python3
"""Contracts for transporting one native Lake graph between Linux jobs."""
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('checkpoint', Path(__file__).with_name('compiler_build_checkpoint.py'))
checkpoint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checkpoint)
SOURCE = 'a' * 40


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'producer'
        self.root.mkdir()
        self.write('.lake/build/bin/ps0', b'compiler')
        self.write('build/graph/src/Init.ps', b'const answer := 42\n')
        self.write('build/graph/artifacts/lib/lean/Init.olean', b'actual output')
        self.write('build/compiler-evidence/input-inventory.json', b'{}')
        self.manifest = self.root / 'build/compiler-checkpoint.json'
        self.state = dict(source_commit=SOURCE, lean_commit=checkpoint.LEAN, run_id='123', phase='base',
            driver=str(self.root / '.lake/build/bin/ps0'), driver_sha256=checkpoint.sha(self.root / '.lake/build/bin/ps0'),
            work='build/graph', source_grammar=True)
        self.seal()

    def write(self, name, data):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def seal(self):
        checkpoint.seal(self.root, self.manifest, self.state,
            ['.lake', 'build/graph', 'build/compiler-evidence'])

    def verify(self, **changes):
        args = dict(source=SOURCE, phase='base', run_id='123', driver=self.state['driver'])
        args.update(changes)
        return checkpoint.verify(self.root, self.manifest, **args)

    def test_round_trip_rehashes_actual_outputs_and_sources(self):
        receipt = self.verify()
        self.assertEqual(len(receipt['files']), 4)
        archive = Path(self.temp.name) / 'checkpoint.tar.gz'
        checkpoint.pack(self.root, self.manifest, archive)
        restored = Path(self.temp.name) / 'restored'
        checkpoint.unpack(archive, restored)
        # Driver identity includes its original absolute location. Native Lake
        # graph continuation requires that same workspace, checked separately.
        self.assertEqual((restored / 'build/graph/src/Init.ps').read_bytes(), b'const answer := 42\n')
        self.assertEqual((restored / 'build/graph/artifacts/lib/lean/Init.olean').read_bytes(), b'actual output')

    def test_changed_output_is_rejected(self):
        self.write('build/graph/artifacts/lib/lean/Init.olean', b'tampered')
        with self.assertRaises(AssertionError): self.verify()

    def test_missing_source_is_rejected(self):
        (self.root / 'build/graph/src/Init.ps').unlink()
        with self.assertRaises(AssertionError): self.verify()

    def test_additional_source_is_rejected(self):
        self.write('build/graph/src/Hidden.lean', b'def hidden := 0')
        with self.assertRaises(AssertionError): self.verify()

    def test_source_pin_is_checked(self):
        with self.assertRaises(AssertionError): self.verify(source='b' * 40)

    def test_run_identity_is_checked(self):
        with self.assertRaises(AssertionError): self.verify(run_id='456')

    def test_slice_order_is_checked(self):
        with self.assertRaises(AssertionError): self.verify(phase='compiler')

    def test_graph_path_survives_a_new_workflow_run(self):
        self.state.update(run_id='456', graph_run_id='123', work='build/compiler-ps-123')
        self.seal()
        verified = self.verify(run_id='456')['state']
        self.assertEqual(checkpoint.graph_run_id(verified), '123')

    def test_graph_path_must_match_the_sealed_identity(self):
        self.state.update(graph_run_id='123', work='build/compiler-ps-456')
        with self.assertRaises(AssertionError):
            checkpoint.graph_run_id(self.state)

    def test_compiler_parts_partition_all_targets_with_root_last(self):
        modules = ['Init', 'Lean', 'Lean.Elab', 'Lean.Syntax']
        early = checkpoint.compiler_part_targets(modules, ['Lean.Syntax'], 'early')
        late = checkpoint.compiler_part_targets(modules, ['Lean.Syntax'], 'late', early)
        self.assertEqual(early, ['Lean.Syntax'])
        self.assertEqual(late, ['Lean', 'Lean.Elab'])

    def test_compiler_part_rejects_mismatched_predecessor(self):
        with self.assertRaises(AssertionError):
            checkpoint.compiler_part_targets(
                ['Lean', 'Lean.Elab', 'Lean.Syntax'], ['Lean.Syntax'], 'late', ['Lean.Elab'])

    def test_compiler_part_rejects_duplicate_foreign_or_root_targets(self):
        for early in (['Lean.Syntax', 'Lean.Syntax'], ['Std'], ['Lean']):
            with self.subTest(early=early), self.assertRaises(AssertionError):
                checkpoint.compiler_part_targets(['Lean', 'Lean.Syntax'], early, 'early')

    def test_three_compiler_parts_require_the_complete_predecessor(self):
        modules = ['Lean', 'Lean.Elab', 'Lean.Parser', 'Lean.Syntax']
        plan = {'early': ['Lean.Syntax'], 'middle': ['Lean.Parser']}
        self.assertEqual(checkpoint.compiler_part_targets(
            modules, plan, 'middle', ['Lean.Syntax']), ['Lean.Parser'])
        self.assertEqual(checkpoint.compiler_part_targets(
            modules, plan, 'late', ['Lean.Parser', 'Lean.Syntax']), ['Lean', 'Lean.Elab'])
        with self.assertRaises(AssertionError):
            checkpoint.compiler_part_targets(modules, plan, 'late', ['Lean.Syntax'])

    def test_three_compiler_parts_reject_overlap(self):
        plan = {'early': ['Lean.Syntax'], 'middle': ['Lean.Syntax']}
        with self.assertRaises(AssertionError):
            checkpoint.compiler_part_targets(['Lean', 'Lean.Syntax'], plan, 'early')

    def test_driver_identity_is_checked(self):
        self.write('.lake/build/bin/ps0', b'different compiler')
        with self.assertRaises(AssertionError): self.verify()

    def test_traversal_is_rejected(self):
        data = json.loads(self.manifest.read_text())
        data['files']['../outside'] = dict(sha256='0' * 64, size=0)
        self.manifest.write_text(json.dumps(data))
        with self.assertRaises(AssertionError): self.verify()

    def test_unpack_rejects_parent_path(self):
        import io
        import tarfile
        archive = Path(self.temp.name) / 'bad.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            entry = tarfile.TarInfo('../outside')
            entry.size = 1
            tar.addfile(entry, io.BytesIO(b'x'))
        with self.assertRaises(AssertionError): checkpoint.unpack(archive, self.root)

    def test_unpack_rejects_symlink(self):
        import tarfile
        archive = Path(self.temp.name) / 'link.tar.gz'
        with tarfile.open(archive, 'w:gz') as tar:
            entry = tarfile.TarInfo('build/link')
            entry.type = tarfile.SYMTYPE
            entry.linkname = '../outside'
            tar.addfile(entry)
        with self.assertRaises(AssertionError): checkpoint.unpack(archive, self.root)


if __name__ == '__main__':
    unittest.main()
