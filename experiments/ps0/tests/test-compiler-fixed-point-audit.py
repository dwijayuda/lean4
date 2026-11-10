#!/usr/bin/env python3
"""Synthetic audit rejection contracts; no fixture binary is ever executed."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import unittest


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


fixture = module('prefix_fixture', 'test-native-compiler-prefix.py')
audit = module('fixed_point_audit', 'audit-compiler-fixed-point.py')


class FixedPointArtifactContracts(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.CompilerPrefixIdentity()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.first = self.fixture.root
        self.second = self.first.parent / (self.first.name + '-second')
        shutil.copytree(self.first, self.second)
        self.addCleanup(shutil.rmtree, self.second)
        self.base = self.fixture.migration
        for root, mode in [(self.first, 'isolated-sdk-assisted-preparation'),
                           (self.second, 'retained-ps-built-prefix')]:
            metadata = dict(mode=mode, path='/retained-stage/compiler-prefix/lib/lean',
                stage_source=fixture.SOURCE, driver_sha256=self.base['driver_sha256'])
            self.write(root, 'source-plan-summary.json', dict(planner_source=fixture.SOURCE,
                module_count=2569, source_grammar=True, self_census_metadata=metadata))
            summary = dict(schema='ps0-compiler-source-census/1', source_commit=fixture.SOURCE,
                lean_commit=fixture.LEAN, module_count=2569, modules={},
                declaration_modes={}, nested_declaration_modes={})
            for name, item in self.base['inputs'].items():
                observed = dict(schema='ps0-native-source-census/1', leanCommit=fixture.LEAN,
                    module=name, mappedOperandSyntaxScope='raw-command-before-native-lowering/1',
                    nativeSource='synthetic captured source ' + name, commands=[])
                data = json.dumps(observed).encode()
                relative = 'source-census/' + name.replace('.', '/') + '.json'
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                summary['modules'][name] = dict(ps_sha256=item['ps_sha256'], command_count=0,
                    census_sha256=hashlib.sha256(data).hexdigest(),
                    native_source_sha256=hashlib.sha256(observed['nativeSource'].encode()).hexdigest())
            self.write(root, 'source-census/summary.json', summary)
            (root / 'compiler-link.map').write_text('synthetic link-map fixture\n')
        self.write(self.second, 'stage-prefix-verification.json', dict(
            schema='ps0-verified-stage-prefix/1', source=fixture.SOURCE,
            driver_sha256=self.base['driver_sha256'], metadata_files=4,
            ps_sources_rehashed=2569, metadata='/retained-stage/compiler-prefix/lib/lean'))
        self.write(self.second, 'input-inventory.json', dict(stage_driver_sha256=self.base['driver_sha256']))
        migration = audit.read(self.second, 'migration.json')
        migration['fixed_point'] = dict(changed_c=[], changed_olean=[])
        self.write(self.second, 'migration.json', migration)

    def write(self, root, name, value):
        (root / name).write_text(json.dumps(value))

    def verify(self):
        return audit.verify_fixed_point(self.first, self.second, fixture.SOURCE)

    def test_equal_synthetic_receipts_and_retained_files(self):
        report = self.verify()
        self.assertEqual(report['ps_sources_rehashed'], 5138)
        self.assertEqual(report['mapped_censuses_rehashed'], 5138)
        self.assertFalse(report['verified_execution'])

    def test_changed_c_or_olean_receipt_rejected(self):
        original = audit.read(self.second, 'migration.json')
        for field in ['c_sha256', 'olean_sha256']:
            changed = json.loads(json.dumps(original))
            changed['outputs']['PS0'][field] = 'f' * 64
            self.write(self.second, 'migration.json', changed)
            with self.subTest(field=field), self.assertRaises(AssertionError):
                self.verify()

    def test_dirty_fixed_point_receipt_rejected(self):
        value = audit.read(self.second, 'migration.json')
        value['fixed_point']['changed_c'] = ['PS0']
        self.write(self.second, 'migration.json', value)
        with self.assertRaises(AssertionError):
            self.verify()

    def test_equal_outputs_do_not_excuse_sdk_metadata_preparation(self):
        value = audit.read(self.second, 'source-plan-summary.json')
        value['self_census_metadata']['mode'] = 'isolated-sdk-assisted-preparation'
        self.write(self.second, 'source-plan-summary.json', value)
        with self.assertRaises(AssertionError):
            self.verify()

    def test_metadata_phase_path_and_driver_must_match_verified_prefix(self):
        original = audit.read(self.second, 'source-plan-summary.json')
        for key, changed in [('path', '/unverified/metadata'), ('driver_sha256', 'f' * 64)]:
            value = json.loads(json.dumps(original))
            value['self_census_metadata'][key] = changed
            self.write(self.second, 'source-plan-summary.json', value)
            with self.subTest(key=key), self.assertRaises(AssertionError):
                self.verify()

    def test_actual_sdk_preparation_log_rejected(self):
        (self.second / 'self-native-metadata.log').write_text('SDK-assisted preparation occurred')
        with self.assertRaises(AssertionError):
            self.verify()

    def test_actual_census_corruption_rejected(self):
        path = self.second / 'source-census/PS0.json'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaises(AssertionError):
            self.verify()

    def test_wrong_input_compiler_rejected(self):
        self.write(self.second, 'input-inventory.json', dict(stage_driver_sha256='f' * 64))
        with self.assertRaises(AssertionError):
            self.verify()


if __name__ == '__main__':
    unittest.main(verbosity=2)
