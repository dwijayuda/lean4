#!/usr/bin/env python3
"""Test-first rejection probes for ordinary host bodies beneath borrowed native syntax."""
from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('host-island-gaps-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
native_prefix = ('module\nprelude\npublic import Init\npublic section\n'
                 'def pairSum (p : Nat × Nat) : Nat := p.1 + p.2\n'
                 'structure IslandCell where\n  value : Nat\n')
ps_prefix = ('module\nprelude\npublic import Init\npublic section\n'
             'function pairSum(p: Nat × Nat): Nat := p.1 + p.2\n'
             'structure IslandCell where\n  value : Nat\n')
cases = [
    ('match', 'def bad (n : Nat) : Nat := match n with | 0 => pairSum (1, 2) | k => k',
     'function bad(n: Nat): Nat := match n with | 0 => pairSum (1, 2) | k => k'),
    ('pattern-lambda', 'def bad (n : Nat) : Nat := (fun | 0 => pairSum (1, 2) | k => k) n',
     'function bad(n: Nat): Nat := (fun | 0 => pairSum (1, 2) | k => k)(n)'),
    ('record-field', 'def bad (n : Nat) : IslandCell := { value := pairSum (n, 1) }',
     'function bad(n: Nat): IslandCell := { value := pairSum (n, 1) }'),
    ('do-if', 'def bad (n : Nat) : Id Nat := do\n  if n == 0 then return pairSum (n, 1)\n  return n',
     'function bad(n: Nat): Id(Nat) := do\n  if n == 0 then return pairSum (n, 1)\n  return n'),
]
observations = []
for name, native, ps in cases:
    baseline = work / (name + '-native.ps')
    baseline.write_text(native_prefix + native + '\n')
    native_result = subprocess.run([str(ROOT / '.lake/build/bin/ps0'), 'census-source', str(baseline),
                                    'HostIslandBaseline', str(work / (name + '-native-census.json'))],
                                   capture_output=True, text=True, timeout=300)
    (work / (name + '-native.log')).write_text(native_result.stdout + native_result.stderr)
    assert native_result.returncode == 0, (name, native_result.stdout, native_result.stderr)
    source = work / (name + '-ps.ps')
    source.write_text(ps_prefix + ps + '\n')
    result = subprocess.run([str(ROOT / '.lake/build/bin/ps0'), '-Dps0.sourceGrammar=true', str(source)],
                            capture_output=True, text=True, timeout=300)
    diagnostic = result.stdout + result.stderr
    (work / (name + '-ps.log')).write_text(diagnostic)
    print(diagnostic, end='', flush=True)
    observations.append(dict(case=name, native_baseline_passed=True, ps_exit_code=result.returncode,
                             diagnostic_excerpt=diagnostic.splitlines()[:8],
                             invalid_host_gap_rejected=result.returncode != 0 and 'PS0V1-CALL-GAP' in diagnostic))
    print('PS0_HOST_ISLAND_OBSERVATION:' + json.dumps(observations[-1], sort_keys=True), flush=True)
(work / 'evidence.json').write_text(json.dumps(dict(source=os.environ['PS0_SOURCE_SHA'],
    observations=observations, scope='ordinary match, pattern lambda, record value and do-if host operands; native baselines typecheck',
    grammar_migration_complete=False, verified_execution=False), indent=2) + '\n')
assert all(row['invalid_host_gap_rejected'] for row in observations), 'ordinary host bodies must not silently accept native-only parenthesized application'
print('PS0_HOST_ISLAND_GAPS: PASS', flush=True)
