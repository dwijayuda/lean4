#!/usr/bin/env python3
"""Qualify native macro dispatch at the owned PS term lowering boundary."""
from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('owned-macros-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)


def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout


fixture = 'tests/v1/owned_category_macros.ps'
run(['lake', 'exe', 'ps0', 'check', fixture], 'check')
run(['lake', 'exe', 'ps0', 'build-native', fixture, 'OwnedMacros', work / 'native'], 'native')
assert 'PS0_OWNED_MACROS:8:6' in run([work / 'native/OwnedMacros'], 'runtime')
prefix = 'function add(x: Nat, y: Nat): Nat := x + y\n'
for name, source, reason in [
    ('argument-gap', 'macro "passOwnedPS " x:psTerm : psTerm => pure x\nconst bad: Nat := passOwnedPS (add (1, 2))', 'PS0V1-CALL-GAP'),
    ('expanded-order', 'macro "badOrderPS" : psTerm => `(psTerm| add(x := 1, 2))\nconst bad: Nat := badOrderPS', 'PS0V1-CALL-ORDER'),
    ('macro-cycle', 'set_option maxRecDepth 64\nsyntax (name := loopOwnedPS) "loopOwnedPS" : psTerm\nmacro_rules (kind := loopOwnedPS)\n  | `(psTerm| loopOwnedPS) => `(psTerm| loopOwnedPS)\nconst bad: Nat := loopOwnedPS', 'maximum recursion depth'),
    ('unowned-result', 'syntax (name := alienOwnedPS) "alienOwnedPS" : psTerm\n@[macro alienOwnedPS]\nmeta def expandAlienOwnedPS : Lean.Macro := fun _ => return .node .none `deliberatelyUnownedNativeTerm #[]\nconst bad: Nat := alienOwnedPS', 'PS0V1-HOST-LOWER'),
]:
    file = work / (name + '.ps')
    file.write_text(prefix + source + '\n')
    diagnostic = run(['lake', 'exe', 'ps0', 'check', file], name, ok=False)
    assert reason in diagnostic, (name, reason)
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': 'PS0_OWNED_MACROS:8:6',
    'scope': 'registered psTerm macros, native dispatch/hygiene, recursive owned lowering and bounded errors; not all category extensions or whole compiler grammar',
    'verified_execution': False,
}, indent=2) + '\n')
print('PS0_OWNED_TERM_MACRO_EXPANSION: PASS', flush=True)
