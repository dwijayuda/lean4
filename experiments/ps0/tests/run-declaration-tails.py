#!/usr/bin/env python3
"""Qualify PS declaration values with Lean's where and termination machinery."""
from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('declaration-tails-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)

def run(args, label):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=600)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert result.returncode == 0, (label, result.returncode)
    return result.stdout

fixture = 'tests/v1/declaration_tails.ps'
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'DeclarationTails', work / 'native'], 'native')
oracle = 'PS0_DECLARATION_TAILS:4:3:7:5'
assert oracle in run([work / 'native/DeclarationTails'], 'runtime')
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': oracle,
    'scope': 'native where binding and termination suffixes on owned declaration values; not complete local declaration conversion',
    'verified_execution': False,
}, indent=2) + '\n')
print('PS0_DECLARATION_TAIL_ADAPTERS: PASS', flush=True)
