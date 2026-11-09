#!/usr/bin/env python3
"""Reject wrong-source and stale native syntax snapshots before corpus replanning."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from native_census_cache import NativeCensusCache

SOURCE = 'a' * 40
LEAN = 'b' * 40
RAW = b'module\nprelude\ndef answer : Nat := 42\n'
SDK_SHA = hashlib.sha256(RAW).hexdigest()


class NativeCacheIdentity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.summary = {'planner_source': SOURCE, 'module_count': 2569,
                        'source_grammar': True, 'refreshed_declaration_censuses': ['Init.Probe']}
        self.inventory = {'source_commit': SOURCE, 'lean_commit': LEAN,
                          'module_count': 2569, 'stage_driver_sha256': 'c' * 64,
                          'inputs': {'Init.Probe': {'original_sha256': SDK_SHA}}}
        self.snapshot = {'schema': 'ps0-native-source-census/1', 'leanCommit': LEAN,
                         'operatorDescriptorScope': 'active-and-captured-kinds/1',
                         'module': 'Init.Probe', 'nativeSource': RAW.decode(),
                         'commands': [{'declaration': {'mode': 'native-compatible'},
                                       'nestedCommands': []}]}
        self.path = self.root / 'current-source-plans/Init.Probe/native-census.json'
        self.path.parent.mkdir(parents=True)
        self.write()

    def write(self):
        (self.root / 'source-plan-summary.json').write_text(json.dumps(self.summary))
        (self.root / 'input-inventory.json').write_text(json.dumps(self.inventory))
        self.path.write_text(json.dumps(self.snapshot))

    def cache(self):
        return NativeCensusCache(self.root, SOURCE, LEAN)

    def test_exact_native_capture_and_missing_entry(self):
        cache = self.cache()
        self.assertEqual(cache.find('Init.Probe', RAW, SDK_SHA), self.path)
        self.assertIsNone(cache.find('Init.Absent', b'', 'd' * 64))
        self.assertEqual(cache.provenance['producer_source'], SOURCE)
        self.assertEqual(cache.provenance['producer_driver_sha256'], 'c' * 64)

    def test_snapshot_identity_and_native_mode_are_required(self):
        mutations = [
            ('schema', 'stale'), ('leanCommit', 'd' * 40), ('module', 'Init.Other'),
            ('operatorDescriptorScope', 'active-only'), ('nativeSource', RAW.decode() + '-- changed\n'),
            ('commands', [{'declaration': {'mode': 'mapped-ps'}, 'nestedCommands': []}]),
        ]
        for key, value in mutations:
            with self.subTest(key=key):
                original = self.snapshot[key]
                self.snapshot[key] = value
                self.write()
                with self.assertRaises(AssertionError):
                    self.cache().find('Init.Probe', RAW, SDK_SHA)
                self.snapshot[key] = original

    def test_both_sdk_and_converted_header_bytes_are_required(self):
        cache = self.cache()
        with self.assertRaises(AssertionError):
            cache.find('Init.Probe', RAW, 'd' * 64)
        with self.assertRaises(AssertionError):
            cache.find('Init.Probe', RAW + b'\n', SDK_SHA)

    def test_producer_identity_is_required(self):
        self.summary['planner_source'] = 'd' * 40
        self.write()
        with self.assertRaises(AssertionError):
            self.cache()
        self.summary['planner_source'] = SOURCE
        self.inventory['source_commit'] = 'd' * 40
        self.write()
        with self.assertRaises(AssertionError):
            self.cache()


if __name__ == '__main__':
    unittest.main()
