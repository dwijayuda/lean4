#!/usr/bin/env python3
"""Check intrinsic contracts and effectful erasure on the pinned PS0 frontend."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

SPEC = '''open Lean in
run_cmd do
  let some (.thmInfo _) := (← getEnv).find? ``checked.spec | throwError "missing spec theorem"
  let assumptions ← collectAxioms ``checked.spec
  if assumptions.contains ``sorryAx then throwError "incomplete spec"
  logInfo m!"PS0_CHECKED_SPEC {assumptions}"
'''
CASES = {
    'PS0-P-VC-01': ('''public import Std.WP
function checked(n: Nat): Id Nat
  given (target: Nat)
  requires n = target
  ensures r => r = target + 1 := do { return n + 1 }
''' + SPEC, 'PS0_CHECKED_SPEC', ''),
    'PS0-P-VC-02': ('''public import Std.WP
opaque hidden : Nat := 7
axiom hiddenLaw : hidden = 7
function checked(): Id Nat
  ensures r => r = 7 := do { return hidden }
  where { finally { | spec => { exact hiddenLaw } } }
''' + SPEC, 'PS0_CHECKED_SPEC', ''),
    'PS0-P-VC-03': ('''public import Std.WP
def effect (counter : IO.Ref Nat) : IO Nat := do
  counter.modify Nat.succ
  return 37
def observe : IO Nat := do
  let counter ← IO.mkRef 0
  erased _witness ← effect counter
  counter.get
#eval show IO Unit from do
  let n ← observe
  if n == 1 then IO.println "PS0_ERASED_EFFECT:1" else throw (IO.userError "erased effect missing")
''', 'PS0_ERASED_EFFECT:1', ''),
    'PS0-N-VC-01': ('''public import Std.WP
function repeated(n: Nat): Id Nat
  requires True
  requires True
  ensures r => r = n := do { return n }
function reordered(n: Nat): Id Nat
  ensures r => r = n
  requires True := do { return n }
''', '', r'unexpected token|expected|contract.*order'),
    'PS0-N-VC-02': ('''public import Std.WP
function bad(n: Nat): Id Nat
  ensures True := do { return n }
''', '', r'unexpected token|expected'),
    'PS0-N-VC-03': ('''public import Std.WP
function bad(n: Nat): Id Nat
  given target: Nat
  ensures r => r = target := do { return n }
''', '', r'unexpected token|expected|typed logical binder'),
    'PS0-N-VC-04': ('''module
prelude
public import Init
public section
function bad(n: Nat): Id Nat
  ensures r => r = n := do { return n }
''', '', r'Std.WP|Triple|requires.*import|verification environment'),
    'PS0-N-VC-05': ('''public import Std.WP
function bad(n: Nat): Id Nat
  ensures r => r = n := do { return n + 1 }
''', '', r'unproved verification conditions for the contract'),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('driver', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True)
    passed, failures, fixtures = [], [], {}
    for case, (source, expected, diagnostic) in CASES.items():
        path = args.output / (case + '.ps')
        path.write_text(source, encoding='utf-8')
        fixtures[case] = hashlib.sha256(path.read_bytes()).hexdigest()
        if case == 'PS0-N-VC-04':
            src = args.output / 'bootstrap'
            src.mkdir()
            native = src / 'MissingWP.ps'
            native.write_text(source, encoding='utf-8')
            command = ['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceGrammar=true',
                       f'-KsourceRoot={src.resolve()}', '-Kroots=MissingWP', '-KmoduleNames=MissingWP',
                       f'-Kdriver={args.driver.resolve()}',
                       f'-KprojectBuildDir={(args.output / "native").resolve()}', 'build', 'MissingWP']
        else:
            command = [args.driver, 'check', path]
        result = subprocess.run(command, env=os.environ, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        log = result.stdout
        (args.output / (case + '.log')).write_text(log, encoding='utf-8')
        if diagnostic:
            errors = [line for line in log.splitlines() if re.search(r':\d+:\d+: error(?:\([^)]*\))?:', line)]
            ok = result.returncode == 1 and bool(errors) and all(re.search(diagnostic, line, re.I) for line in errors)
            if case == 'PS0-N-VC-01':
                ok = result.returncode == 1 and len(errors) == 2 and all(
                    "unexpected token 'requires'" in line or "PS0V1-CONTRACT-ORDER" in line for line in errors)
        else:
            ok = result.returncode == 0 and expected in log
        (passed if ok else failures).append(case)
        print(case, 'PASS' if ok else 'FAIL', result.returncode, log, flush=True)
    evidence = {'passed': passed, 'failures': failures, 'fixtures': fixtures,
                'driver_sha256': hashlib.sha256(args.driver.read_bytes()).hexdigest()}
    (args.output / 'result.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('PS0_R2_CONTRACTS', json.dumps(evidence), flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
