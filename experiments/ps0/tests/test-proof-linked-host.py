#!/usr/bin/env python3
"""Host-contract tests only; these never claim Lean proof qualification."""
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
M = runpy.run_path(str(ROOT / 'scripts/proof_linked.py'))
Refusal = M['Refusal']
IR = ['sub', ['first'], ['second']]


class HostContractTests(unittest.TestCase):
    def candidate(self, root, ir=None):
        ir = IR if ir is None else ir
        root.mkdir()
        (root / 'ir.json').write_text(json.dumps({'schema': M['SCHEMA'], 'root': M['ROOT'], 'ir': ir}))
        for name, typed in [('inventory.js', False), ('inventory.ts', True)]:
            (root / name).write_bytes(M['expected_source'](ir, typed))

    def test_valid_typed_ir(self):
        self.assertEqual(M['validate_ir'](IR), IR)
        self.assertEqual(M['lean_expr'](IR), '(.sub .first .second)')

    def test_nested_arithmetic(self):
        ir = ['add', ['mul', ['first'], ['literal', '2']], ['sub', ['second'], ['literal', '1']]]
        self.assertEqual(M['validate_ir'](ir), ir)
        self.assertIn('bigint', M['expected_source'](ir, True).decode())

    def test_invalid_shapes(self):
        for value in [None, True, 1, {}, [], ['first', 0], ['sub', ['first']], ['call', 'evil']]:
            with self.subTest(value=value), self.assertRaises(Refusal):
                M['validate_ir'](value)

    def test_invalid_literals(self):
        for value in ['-1', '01', '', '1.0', '1n', 'NaN', '0;process.exit()', 1, True, '1' * 1025]:
            with self.subTest(value=value), self.assertRaises(Refusal):
                M['validate_ir'](['literal', value])

    def test_depth_budget(self):
        value = ['first']
        for _ in range(40):
            value = ['sub', value, ['literal', '0']]
        with self.assertRaises(Refusal):
            M['validate_ir'](value)

    def test_candidate_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'candidate'
            self.candidate(path)
            ir, files = M['read_candidate'](path)
            self.assertEqual(ir, IR)
            self.assertIn(b': bigint', files['inventory.ts'])
            self.assertNotIn(b': bigint', files['inventory.js'])

    def test_wrong_body_is_not_approved_by_host_matching(self):
        # Consistent same-signature/wrong-behavior artifacts can pass this byte
        # validator. The independent extraction/specification proofs are REQUIRED.
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'candidate'
            wrong = ['add', ['first'], ['second']]
            self.candidate(path, wrong)
            self.assertEqual(M['read_candidate'](path)[0], wrong)
            self.assertNotEqual(wrong, IR)

    def test_changed_js_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'candidate'
            self.candidate(path)
            source = (path / 'inventory.js').read_bytes().replace(b' - ', b' + ')
            (path / 'inventory.js').write_bytes(source)
            with self.assertRaisesRegex(Refusal, 'PS0-ARTIFACT'):
                M['read_candidate'](path)

    def test_changed_typescript_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'candidate'
            self.candidate(path)
            (path / 'inventory.ts').write_bytes(b'export const remaining = 0;\n')
            with self.assertRaisesRegex(Refusal, 'PS0-ARTIFACT'):
                M['read_candidate'](path)

    def test_missing_artifact_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'candidate'
            self.candidate(path)
            (path / 'inventory.ts').unlink()
            with self.assertRaises(Refusal):
                M['read_candidate'](path)

    def test_extra_artifact_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'candidate'
            self.candidate(path)
            (path / 'claim.json').write_text('{"verified":true}')
            with self.assertRaises(Refusal):
                M['read_candidate'](path)

    def test_duplicate_json_key_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'candidate'
            self.candidate(path)
            (path / 'ir.json').write_text('{"schema":"ps0-nat2-candidate/1","root":"Inventory.remaining","ir":["first"],"ir":["second"]}')
            with self.assertRaisesRegex(Refusal, 'PS0-JSON'):
                M['read_candidate'](path)

    def test_wrong_root_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'candidate'
            self.candidate(path)
            data = json.loads((path / 'ir.json').read_text())
            data['root'] = 'Other.remaining'
            (path / 'ir.json').write_text(json.dumps(data))
            with self.assertRaises(Refusal):
                M['read_candidate'](path)

    def test_symlink_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'candidate'
            self.candidate(path)
            original = (path / 'inventory.js').read_bytes()
            (path / 'inventory.js').unlink()
            (Path(d) / 'other.js').write_bytes(original)
            (path / 'inventory.js').symlink_to(Path(d) / 'other.js')
            with self.assertRaisesRegex(Refusal, 'PS0-FILE'):
                M['read_candidate'](path)

    def test_strict_profile_cannot_downgrade(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'out'
            with self.assertRaisesRegex(Refusal, 'PS0-POLICY'):
                M['build'](ROOT, Path(d), out, 'verified-portable')
            self.assertFalse(out.exists())

    def test_atomic_publication_preserves_existing_empty_directory(self):
        with tempfile.TemporaryDirectory() as d:
            stage, out = Path(d) / 'stage', Path(d) / 'out'
            stage.mkdir()
            out.mkdir()
            (stage / 'candidate').write_text('new')
            with self.assertRaisesRegex(Refusal, 'PS0-PUBLISH'):
                M['publish_noreplace'](stage, out)
            self.assertEqual(list(out.iterdir()), [])
            self.assertTrue((stage / 'candidate').exists())

    def test_atomic_publication_moves_whole_bundle(self):
        with tempfile.TemporaryDirectory() as d:
            stage, out = Path(d) / 'stage', Path(d) / 'out'
            stage.mkdir()
            (stage / 'candidate').write_text('new')
            M['publish_noreplace'](stage, out)
            self.assertEqual((out / 'candidate').read_text(), 'new')
            self.assertFalse(stage.exists())

    def test_tsc_formatting_not_semantic_change(self):
        source = M['expected_source'](IR, False)
        reformatted = source.replace(b'  ', b'    ')
        self.assertEqual(M['target_tokens'](source), M['target_tokens'](reformatted))
        with self.assertRaises(Refusal):
            M['target_tokens'](source + b'process.exit(0);')

    def test_size_preflight_matches_actual_small_expressions(self):
        cases = [['first'], ['second'], ['literal', '0'], ['literal', '1234567890'], IR]
        cases += [[op, IR, ['literal', '42']] for op in ['add', 'mul', 'sub']]
        for ir in cases:
            with self.subTest(ir=ir):
                self.assertEqual(M['target_size'](ir), len(M['target_expr'](ir).encode()))
                for typed in [False, True]:
                    self.assertLess(len(M['expected_source'](ir, typed)) - M['target_size'](ir), 512)

    def test_exponential_expansion_refused_before_rendering(self):
        ir = ['first']
        for _ in range(32):
            ir = ['sub', ir, ['second']]
        M['validate_ir'](ir)  # This is inside the IR depth/node budgets.
        renderer = mock.Mock(side_effect=AssertionError('must not allocate huge output'))
        with mock.patch.dict(M['expected_source'].__globals__, {'target_expr': renderer}):
            with self.assertRaisesRegex(Refusal, 'PS0-OUTPUT-SIZE'):
                M['expected_source'](ir, False)
        renderer.assert_not_called()

    def test_changed_challenge_inputs_refused(self):
        for name in ['Admitted.lean', 'ChallengeSource.lean', 'Candidate.lean', 'target-comparator.json', 'lean-toolchain']:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as d:
                path = Path(d)
                (path / name).write_text('original')
                snapshot = M['snapshot_files'](path)
                (path / name).write_text('changed')
                with self.assertRaisesRegex(Refusal, 'PS0-SNAPSHOT'):
                    M['verify_snapshot'](path, snapshot)

    def test_deleted_proof_input_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            (path / 'Solution.lean').write_text('proof')
            snapshot = M['snapshot_files'](path)
            (path / 'Solution.lean').unlink()
            with self.assertRaisesRegex(Refusal, 'PS0-SNAPSHOT'):
                M['verify_snapshot'](path, snapshot)

    def test_unexpected_input_refused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            snapshot = M['snapshot_files'](path)
            (path / 'Unreviewed.lean').write_text('extra')
            with self.assertRaisesRegex(Refusal, 'PS0-SNAPSHOT'):
                M['verify_snapshot'](path, snapshot)

    def test_allowed_manifest_is_then_frozen_and_cache_is_not_source(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            (path / '.lake').mkdir()
            (path / '.lake/cache').write_text('generated')
            (path / 'lake-manifest.json').write_text('{}')
            snapshot = M['verify_snapshot'](path, {}, ['lake-manifest.json'])
            self.assertEqual(set(snapshot), {'lake-manifest.json'})
            (path / '.lake/cache').write_text('updated cache')
            M['verify_snapshot'](path, snapshot)
            (path / 'lake-manifest.json').write_text('{"changed":true}')
            with self.assertRaisesRegex(Refusal, 'PS0-SNAPSHOT'):
                M['verify_snapshot'](path, snapshot)

    def test_symlink_directory_is_not_an_invisible_input(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            (path / 'real').mkdir()
            (path / 'alias').symlink_to(path / 'real', target_is_directory=True)
            with self.assertRaisesRegex(Refusal, 'PS0-SNAPSHOT'):
                M['snapshot_files'](path)

    def test_bounded_file_read(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'large'
            path.write_bytes(b'x' * 4096)
            with self.assertRaisesRegex(Refusal, 'PS0-SIZE'):
                M['regular_bytes'](path, 8)

    def test_wrong_target_version_fails_before_compilation(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)
            (path / '.lake').mkdir()
            tsc = path / 'tsc.js'
            tsc.write_text('not executed')
            runner = mock.Mock(side_effect=['v0.0.0', M['TSC_VERSION']])
            with mock.patch.dict(os.environ, {'PS0_TSC': str(tsc)}):
                with mock.patch.dict(M['check_targets'].__globals__, {'run': runner}):
                    with self.assertRaisesRegex(Refusal, 'PS0-TARGET-PIN'):
                        M['check_targets'](ROOT, path, {}, path / 'logs')
            self.assertEqual(runner.call_count, 2)
            self.assertEqual(list((path / '.lake/ps0-target-check').iterdir()), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
