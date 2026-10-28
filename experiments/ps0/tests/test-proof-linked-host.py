#!/usr/bin/env python3
"""Host-contract tests only; these never claim Lean proof qualification."""
import json
from pathlib import Path
import runpy
import tempfile
import unittest

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


if __name__ == '__main__':
    unittest.main(verbosity=2)
