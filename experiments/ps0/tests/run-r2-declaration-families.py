#!/usr/bin/env python3
"""Check declaration, scope, and logical-boundary capability families."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

CASES = {
    'V1-010': '''class HasScore (α : Type) where
  score : α → Nat
structure Box where
  score : Nat
instance : HasScore Box := ⟨Box.score⟩
instance : Coe Box Nat := ⟨Box.score⟩
def checked (box : Box) : Nat := HasScore.score box + box
private example : checked({ score := 21 }) = 42 := rfl
''',
    'V1-016': '''namespace Outer
section
variable (n : Nat)
include n
theorem explicitScope : True := True.intro
omit n
theorem omittedScope : True := True.intro
end
end Outer
private example : Nat → True := Outer.explicitScope
private example : True := Outer.omittedScope
''',
    'V1-017': '''namespace Names
def first : Nat := 11
def second : Nat := 17
def third : Nat := 23
scoped notation "localNumeral" => 31
end Names
open Names hiding second
open Names (second)
open Names renaming third → renamed
open scoped Names
namespace Bridge
export Names (first)
end Bridge
private example : first + second + renamed + Bridge.first + localNumeral = 93 := rfl
''',
    'V1-019': '''public meta import Lean
meta def compileTime : Nat := 7
noncomputable def classicalValue (h : Nonempty Nat) : Nat := Classical.choice h
namespace Scope
def value : Nat := 3
namespace Inner
nonrec def value : Nat := value + 4
end Inner
end Scope
private example : Scope.Inner.value = 7 := rfl
open Lean in
run_cmd do
  let env ← getEnv
  unless isMarkedMeta env ``compileTime do throwError "missing meta modifier"
  unless isNoncomputable env ``classicalValue do throwError "missing noncomputable modifier"
''',
    'V1-020': ('''@[expose] def ordinary : Nat := 42
abbrev synonym : Nat := ordinary
theorem checked : synonym = 42 := rfl
example : synonym = 42 := checked
open Lean in
run_cmd do
  let env ← getEnv
  let some (.defnInfo defn) := env.find? ``synonym | throwError "missing abbreviation"
  unless defn.hints matches .abbrev do throwError "missing abbreviation hint"
  let some (.thmInfo _) := env.find? ``checked | throwError "missing theorem"
''',
    'V1-021': '''const parameterless: Nat := 42
function nullary(): Nat := parameterless
private example : nullary(()) = 42 := rfl
private example : nullary() = 42 := rfl
open Lean in
run_cmd do
  unless !(← getConstInfo ``parameterless).type.isForall do throwError "const telescope"
  let .forallE _ domain body _ := (← getConstInfo ``nullary).type | throwError "nullary telescope"
  unless domain.isConstOf ``Unit && body.isConstOf ``Nat do throwError "nullary Unit binder"
''',
    'V1-022': '''opaque defined : Nat := 42
opaque inhabited : Nat
open Lean in
run_cmd do
  let env ← getEnv
  for name in [``defined, ``inhabited] do
    let some (.opaqueInfo _) := env.find? name | throwError "missing opaque declaration"
''',
    'V1-023': '''axiom assumed : True
theorem assumptionDependent : True := assumed
open Lean in
run_cmd do
  unless (← collectAxioms ``assumptionDependent) == #[``assumed] do throwError "axiom closure"
''',
    'PS0-N-ASSURE-01': '''theorem unfinished : True := by sorry
theorem dependent : True := unfinished
open Lean in
run_cmd do
  unless (← collectAxioms ``dependent).contains ``sorryAx do throwError "transitive sorry missing"
''',
    'PS0-N-ASSURE-02': '''axiom unchecked : True
theorem dependent : True := unchecked
theorem nativeFact : 21 + 21 = 42 := by native_decide
open Lean in
run_cmd do
  unless (← collectAxioms ``dependent) == #[``unchecked] do throwError "user axiom missing"
  let assumptions ← collectAxioms ``nativeFact
  if assumptions.isEmpty || assumptions.contains ``sorryAx then throwError "native assumption missing"
''',
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('driver', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True)
    passed, failures, fixtures = [], [], {}
    for case, source in CASES.items():
        path = args.output / (case + '.ps')
        path.write_text(source, encoding='utf-8')
        fixtures[case] = hashlib.sha256(path.read_bytes()).hexdigest()
        result = subprocess.run([args.driver, 'check', path], text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        log = result.stdout
        (args.output / (case + '.log')).write_text(log, encoding='utf-8')
        ok = result.returncode == 0
        if case.startswith('PS0-N-ASSURE'):
            ok = ok and 'Lean checking passed (UNCERTIFIED)' in log and 'no verified certificate issued' in log
        (passed if ok else failures).append(case)
        print(case, 'PASS' if ok else 'FAIL', result.returncode, log, flush=True)
    evidence = {'passed': passed, 'failures': failures, 'fixtures': fixtures,
                'driver_sha256': hashlib.sha256(args.driver.read_bytes()).hexdigest()}
    (args.output / 'result.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('PS0_R2_DECLARATION_FAMILIES', json.dumps(evidence), flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
