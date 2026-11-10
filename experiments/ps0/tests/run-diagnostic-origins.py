#!/usr/bin/env python3
"""Compare original PS diagnostic coordinates with an aligned native Lean control."""
from pathlib import Path
import json
import os
import re
import subprocess
import sys

if len(sys.argv) != 1:
    raise SystemExit('run-diagnostic-origins.py accepts no arguments')
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('diagnostic-origins-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
driver = ROOT / '.lake/build/bin/ps0'
observations = []
for modern in [False, True]:
    for crlf in [False, True]:
        name = ('modern' if modern else 'legacy') + ('-crlf' if crlf else '-lf')
        header = ('module\n' if modern else '') + 'import Init\n'
        body = '-- π / 😀\nfunction bad(n: Nat): Nat := /- π / 😀 -/ missingName\n'
        ps = work / (name + '.ps')
        native = work / (name + '.lean')
        text = header + body
        if crlf:
            text = text.replace('\n', '\r\n')
        ps.write_bytes(text.encode())
        native.write_bytes(text.replace('function bad', 'def      bad').encode())
        positions = {}
        for label, args, path in [('native', ['lake', 'env', 'lean', str(native)], native),
                                  ('ps', ['lake', 'env', str(driver), 'check', str(ps)], ps)]:
            result = subprocess.run(args, capture_output=True, text=True, timeout=120)
            diagnostic = result.stdout + result.stderr
            (work / (name + '-' + label + '.log')).write_text(diagnostic)
            assert result.returncode != 0, (name, label)
            matches = re.findall(re.escape(str(path)) + r':(\d+):(\d+):[^\n]*[Uu]nknown identifier[^\n]*missingName', diagnostic)
            assert len(matches) == 1, (name, label, diagnostic)
            positions[label] = [int(x) for x in matches[0]]
        observations.append(dict(case=name, positions=positions,
                                 original_coordinates_match=positions['native'] == positions['ps']))
        print('PS0_DIAGNOSTIC_ORIGIN:' + json.dumps(observations[-1], sort_keys=True), flush=True)
(work / 'evidence.json').write_text(json.dumps(dict(source=os.environ['PS0_SOURCE_SHA'],
    observations=observations, scope='finite original CLI error coordinates, LF/CRLF and Unicode; no compiler graph claim',
    grammar_migration_complete=False, verified_execution=False), indent=2) + '\n')
assert all(row['original_coordinates_match'] for row in observations)
print('PS0_DIAGNOSTIC_ORIGINS: PASS', flush=True)
