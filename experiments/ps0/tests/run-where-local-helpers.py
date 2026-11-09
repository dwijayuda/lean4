#!/usr/bin/env python3
"""Test-first probe for R2 braced local helper grammar; not yet a primary qualification gate."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('where-local-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert result.returncode == 0, (label, result.returncode)
    return result.stdout


fixture = Path('tests/v1/where_local_helpers.ps')
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'WhereLocal', work / 'native'], 'native')
oracle = 'PS0_WHERE_LOCAL:7:5:4:4:5'
assert oracle in run([work / 'native/WhereLocal'], 'runtime')
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': oracle,
    'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
    'scope': 'test-first finite braced where defaults/capture/equations/record/forward-helper cases; excludes full tail and signature matrix',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_WHERE_LOCAL_HELPERS: PASS', flush=True)
