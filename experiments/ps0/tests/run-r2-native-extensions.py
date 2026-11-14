#!/usr/bin/env python3
"""Check native extensions, diagnostics, registration and native ABI execution."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

CASES = {
    'PS0-P-EXT-01': ('''public meta import Lean
syntax "identityTerm " term : term
macro_rules | `(identityTerm $x) => pure x
macro "forty " : term => `(40)
elab "checkedForty" : term => do
  Lean.Elab.Term.elabTerm (← `(40)) none
syntax "checkedTwo" : term
elab_rules : term
  | `(checkedTwo) => do Lean.Elab.Term.elabTerm (← `(2)) none
private example : (identityTerm forty) + checkedTwo = 42 := rfl
private example : checkedForty = 40 := rfl
''', None),
    'PS0-P-EXT-02': ('''public meta import Lean
meta def pairQuote : Lean.MacroM(Lean.TSyntax `term) := `(term| f (x, y))
open Lean in
run_cmd do
  let syntaxTree ← Elab.liftMacroM pairQuote
  unless syntaxTree.raw.isOfKind ``Parser.Term.app &&
      syntaxTree.raw[1].getArgs.size == 1 && syntaxTree.raw[1][0].isOfKind ``Parser.Term.tuple do
    throwError "tuple partition changed"
''', None),
    'PS0-P-META-02': ('''public import Lean
private example : binop% HAdd.hAdd 20 22 = (42 : Nat) := rfl
''', None),
    'PS0-P-RUN-02': ('''unsafe def raw : Nat := 42
open Lean in
run_cmd do
  unless ((← getEnv).find? ``raw).any ConstantInfo.isUnsafe do throwError "missing unsafe classification"
''', None),
    'PS0-P-DIAG-01': ('''theorem proven : True := True.intro
#check proven
#print axioms proven
#eval IO.println "PS0_DIAGNOSTIC_EVAL"
#guard 4 + 5 == 9
''', None),
    'PS0-P-RUN-01': ('''function say(): IO Unit := do
  IO.println("PS0_R2_IO:hello")
#eval say ()
''', None),
    'PS0-N-EXT-03': ('''@[unregistered_r2_attribute] def value : Nat := 1
''', r'Unknown attribute.*unregistered_r2_attribute'),
}

NATIVE_ABI = '''module
prelude
public import Init
public section
@[extern "lean_uint32_of_nat"] opaque borrowed (n : @& Nat) : UInt32
def replacement (n : UInt32) : UInt32 := n + 2
@[implemented_by replacement] def model (n : UInt32) : UInt32 := n + 1
def main : IO Unit := do
  IO.println(s!"PS0_R2_ABI:{model(borrowed(40))}")
'''
INITIALIZERS = '''module
prelude
public import Init
public section
initialize ordinaryRef : IO.Ref Nat ← IO.mkRef 17
builtin_initialize earlyRef : IO.Ref Nat ← IO.mkRef 23
def main : IO Unit := do
  let first ← ordinaryRef.get
  let second ← earlyRef.get
  unless first == 17 && second == 23 do throw(IO.userError("initializer result"))
  IO.println "PS0_R2_INITIALIZERS:17:23"
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('driver', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True)
    passed, failures, fixtures = [], [], {}

    def run(label, command):
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=240)
        (out / (label + '.log')).write_text(result.stdout, encoding='utf-8')
        print(label, result.returncode, result.stdout, flush=True)
        return result.returncode, result.stdout

    for case, (source, diagnostic) in CASES.items():
        path = out / (case + '.ps')
        path.write_text(source, encoding='utf-8')
        fixtures[case] = hashlib.sha256(path.read_bytes()).hexdigest()
        code, log = run(case, [args.driver, 'check', path])
        ok = code == 1 and re.search(diagnostic, log, re.I) if diagnostic else code == 0
        if case == 'PS0-P-DIAG-01':
            ok = ok and 'does not depend on any axioms' in log and 'PS0_DIAGNOSTIC_EVAL' in log
        if case == 'PS0-P-RUN-01':
            ok = ok and 'PS0_R2_IO:hello' in log
        (passed if ok else failures).append(case)

    src = out / 'src'
    src.mkdir()
    for case, module, source, expected in [
        ('PS0-P-RUN-03', 'NativeABI', NATIVE_ABI, 'PS0_R2_ABI:42'),
        ('PS0-P-META-01', 'NativeInitializers', INITIALIZERS, 'PS0_R2_INITIALIZERS:17:23'),
    ]:
        path = src / (module + '.ps')
        path.write_text(source, encoding='utf-8')
        fixtures[case] = hashlib.sha256(path.read_bytes()).hexdigest()
        build = out / module
        code, _ = run(case, ['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceGrammar=true',
                            f'-KsourceRoot={src}', f'-Kroots={module}', f'-KrootModule={module}',
                            f'-KmoduleNames={module}', f'-Kdriver={args.driver.resolve()}',
                            f'-KprojectBuildDir={build}', 'build', 'ps0project'])
        ok = code == 0
        if ok:
            code, log = run(case + '-runtime', [build / 'bin/ps0project'])
            ok = code == 0 and log.strip() == expected
        (passed if ok else failures).append(case)
    evidence = {'passed': passed, 'failures': failures, 'fixtures': fixtures,
                'driver_sha256': hashlib.sha256(args.driver.read_bytes()).hexdigest()}
    (out / 'result.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('PS0_R2_NATIVE_EXTENSIONS', json.dumps(evidence), flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
