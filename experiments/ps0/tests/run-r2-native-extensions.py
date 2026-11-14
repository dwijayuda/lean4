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
    'PS0-N-EXT-01': ('''public meta import Lean
meta def nativeQuote : Lean.MacroM(Lean.TSyntax `term) := `(term| f (x, y))
open Lean in
run_cmd do
  let tree ← Elab.liftMacroM nativeQuote
  let args := tree.raw[1].getArgs
  unless args.size == 1 && args[0]!.isOfKind ``Parser.Term.tuple do
    throwError "native tuple application was rewritten as a PS comma call"
''', None),
    'PS0-N-EXT-02': ('''public meta import Lean
macro "hostOperand " x:psTerm : psTerm => pure x
function sumPair(p: Nat × Nat): Nat := p.1 + p.2
const bad: Nat := hostOperand sumPair (1, 2)
''', r':4:\d+: error: PS0V1-CALL-GAP'),
    'PS0-P-ENV-01': ('''public import Lake
open Lake DSL
package r2example where
  version := v!"0.2.0"
lean_lib R2Library where
  roots := #[`R2Library]
open Lean in
run_cmd do
  let env ← getEnv
  unless env.contains `pkgConfig do throwError "missing Lake configuration declaration"
''', None),
    'PS0-N-ASSURE-03': ('''partial function loop(n: Nat): Nat := loop(n)
open Lean in
run_cmd do
  let env ← getEnv
  let some (.opaqueInfo _) := env.find? ``loop | throwError "missing opaque interface"
  unless (env.find? (Compiler.mkUnsafeRecName ``loop)).any ConstantInfo.isPartial do
    throwError "expected compiled partial implementation"
''', None),
    'PS0-N-ASSURE-04': ('''public import Std.WP
def effect (counter : IO.Ref Nat) : IO Nat := do
  counter.modify Nat.succ
  return 37
def observe : IO Nat := do
  let counter ← IO.mkRef 0
  erased _witness ← effect counter
  counter.get
#eval show IO Unit from do
  let n ← observe
  if n == 1 then IO.println "PS0_EFFECT_RETAINED" else throw (IO.userError "erased effect missing")
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
    'PS0-P-DOC-01': ('''public meta import Lean
/-- A Markdown docstring. -/
def markdownDocumented : Nat := 1
set_option doc.verso true in
/-- A *Verso* docstring. -/
def versoDocumented : Nat := 2
open Lean in
run_cmd do
  let env ← getEnv
  let some (.inl _) ← findInternalDocString? env ``markdownDocumented | throwError "Markdown missing"
  let some (.inr _) ← findInternalDocString? env ``versoDocumented | throwError "Verso missing"
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
        if case == 'PS0-N-ASSURE-03':
            ok = ok and 'UNCERTIFIED' in log and 'no verified certificate issued' in log
        if case == 'PS0-N-ASSURE-04':
            ok = ok and 'PS0_EFFECT_RETAINED' in log
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
        if case == 'PS0-P-RUN-03':
            control = out / 'PS0-N-ASSURE-05.ps'
            control.write_text(source + '\nprivate example : model 40 = 41 := rfl\n', encoding='utf-8')
            fixtures['PS0-N-ASSURE-05'] = hashlib.sha256(control.read_bytes()).hexdigest()
            logical, log = run('PS0-N-ASSURE-05', [args.driver, 'check', control])
            (passed if ok and logical == 0 and 'UNCERTIFIED' in log else failures).append('PS0-N-ASSURE-05')
    native = out / 'PS0-N-ASSURE-06.lean'
    proofscript = out / 'PS0-N-ASSURE-06.ps'
    source = 'def nativeOnly (x : Nat) : Nat := x\ndef checked : Nat := nativeOnly (42)\n'
    for path in (native, proofscript):
        path.write_text(source, encoding='utf-8')
    fixtures['PS0-N-ASSURE-06'] = hashlib.sha256(proofscript.read_bytes()).hexdigest()
    native_code, native_log = run('native-pass-through', [args.driver, 'check', native])
    ps_code, ps_log = run('PS0-N-ASSURE-06', [args.driver, 'check', proofscript])
    (passed if native_code == 0 and 'PS0V1:' not in native_log and ps_code == 1 and
        'PS0V1-CALL-GAP' in ps_log else failures).append('PS0-N-ASSURE-06')
    evidence = {'passed': passed, 'failures': failures, 'fixtures': fixtures,
                'driver_sha256': hashlib.sha256(args.driver.read_bytes()).hexdigest()}
    (out / 'result.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('PS0_R2_NATIVE_EXTENSIONS', json.dumps(evidence), flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
