#!/usr/bin/env python3
"""Test finite proof, binder and lexical R2 acceptance cases."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

CASES = {
    'PS0-P-PROOF-01': ('''theorem identityProof(p: Prop): p → p := by { intro h; exact h }
open Lean in
run_cmd do
  unless (← collectAxioms ``identityProof).isEmpty do throwError "unexpected assumptions"
''', ''),
    'PS0-P-PROOF-02': ('''public meta import Lean
elab "customTrue" : tactic => do
  Lean.Elab.Tactic.evalTactic (← `(tactic| exact True.intro))
theorem customProof: True := by { customTrue }
open Lean in
run_cmd do
  unless (← collectAxioms ``customProof).isEmpty do throwError "unexpected assumptions"
''', ''),
    'PS0-P-PROOF-03': ('''theorem nativeResult: 42 + 1 = 43 := by native_decide
open Lean in
run_cmd do
  let assumptions ← collectAxioms ``nativeResult
  if assumptions.isEmpty || assumptions.contains ``sorryAx then
    throwError "expected native computation assumptions without sorry"
  logInfo m!"PS0_NATIVE_ASSUMPTIONS {assumptions}"
#print axioms nativeResult
''', ''),
    'PS0-N-BIND-01': ('function bad(x: Nat)(y: Nat) := x + y\n',
                     r'adjacent explicit groups|unexpected token.*expected'),
    'PS0-N-BIND-02': ('function bad()(x: Nat) := x\n',
                     r'nullary|empty|unexpected token.*expected'),
    'PS0-N-BIND-03': ('def bad() : Nat := 7\n', r'PS0V1-BIND-EMPTY: only function'),
    'PS0-N-BIND-04': ('const bad(x: Nat) := x\n', r'expected|unexpected token'),
    'PS0-N-LEX-01': ('const bad: Nat := /* not a comment */ 7\n',
                    r'unexpected token|expected term|unknown identifier'),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('driver', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True)
    passed, failures, fixtures = [], [], {}
    for case, (source, diagnostic) in CASES.items():
        fixture = args.output / (case + '.ps')
        fixture.write_text(source, encoding='utf-8')
        fixtures[case] = hashlib.sha256(fixture.read_bytes()).hexdigest()
        result = subprocess.run([args.driver, 'check', fixture], text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        log = result.stdout
        (args.output / (case + '.log')).write_text(log, encoding='utf-8')
        if diagnostic:
            ok = result.returncode == 1 and any(re.search(r':1:\d+: error(?:\([^)]*\))?:', line)
                and re.search(diagnostic, line, re.I) for line in log.splitlines())
        else:
            ok = result.returncode == 0
        (passed if ok else failures).append(case)
        print(case, 'PASS' if ok else 'FAIL', result.returncode, log, flush=True)
    evidence = {'passed': passed, 'failures': failures, 'fixtures': fixtures,
                'driver_sha256': hashlib.sha256(args.driver.read_bytes()).hexdigest()}
    (args.output / 'result.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('PS0_R2_PROOF_BIND', json.dumps(evidence), flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
