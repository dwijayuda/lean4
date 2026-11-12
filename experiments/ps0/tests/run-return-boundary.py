#!/usr/bin/env python3
"""Check native empty-return line boundaries through PS control and pattern fallback adapters."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('return-boundary-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert result.returncode == 0, (label, result.returncode)
    return result.stdout


fixture = Path('tests/v1/native_return_boundary.ps')
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'ReturnBoundary', work / 'native'], 'native')
runtime = run([work / 'native/ReturnBoundary'], 'runtime')
assert runtime.splitlines() == ['PS0_RETURN_BOUNDARY:0']
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'],
    'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
    'oracle': 'PS0_RETURN_BOUNDARY:0', 'empty_return_does_not_consume_next_line': True,
    'scope': 'native empty return before a native pattern let fallback and owned PS continuation',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_RETURN_BOUNDARY: PASS', flush=True)
