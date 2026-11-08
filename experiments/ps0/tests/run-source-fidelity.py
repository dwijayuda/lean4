#!/usr/bin/env python3
"""Byte-exact origin coverage, including native header trivia and generated spans."""
from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('source-fidelity-' + os.environ.get('GITHUB_RUN_ID', str(os.getpid())))
work.mkdir(parents=True, exist_ok=False)
cases = {
    'implicit': '/- α /- nested -/ β -/\r\npublic import Init\r\n-- header λ\r\ndef café : Nat := 1\r\n',
    'explicit': 'module\n/- between header tokens λ -/\npublic import Init -- retained\n/-! module docs -/\ndef café : Nat := 1\n',
    'prelude': 'module\nprelude\n/- exact native substrate -/\npublic import Init\ndef café : Nat := 1\n',
    'empty': '',
    'eof-comment': 'public import Init -- final header comment λ',
}
for name, raw in cases.items():
    path = work / (name + '.ps')
    path.write_bytes(raw.encode())
    r = subprocess.run(['lake', 'exe', 'ps0', 'source-map', str(path)], text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
    assert r.returncode == 0, (name, r.stdout, r.stderr)
    result = json.loads(r.stdout)
    assert result['schema'] == 'ps0-source-map/1'
    prepared = result['source'].encode()
    original = raw.encode()
    assert result['originalByteSize'] == len(original)
    cursor = origin = 0
    recovered = bytearray()
    for span in result['segments']:
        assert span['preparedStart'] == cursor
        cursor = span['preparedEnd']
        data = prepared[span['preparedStart']:cursor]
        if span['kind'] == 'original':
            assert span['originalStart'] == origin
            origin = span['originalEnd']
            assert data == original[span['originalStart']:origin]
            recovered.extend(data)
        else:
            assert span['kind'] == 'generated'
            assert 'originalStart' not in span and span['reason']
    assert cursor == len(prepared) and origin == len(original)
    assert recovered == original
    if name == 'prelude':
        assert prepared == original and len(result['segments']) == 1
    checked = subprocess.run(['lake', 'exe', 'ps0', 'check', str(path)], text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
    assert checked.returncode == 0, (name, checked.stdout)
    (work / (name + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print('PS0_SOURCE_ORIGIN:' + name + ':PASS', flush=True)
print('PS0_SOURCE_FIDELITY_MAP: PASS', flush=True)
