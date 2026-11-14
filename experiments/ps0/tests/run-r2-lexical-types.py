#!/usr/bin/env python3
"""Check finite lexical, type, documentation and bootstrap families."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

CASES = {
    'V1-001': ('''namespace Outer.Inner
def ἀριθμός : Nat := 19
def «two words» : Nat := 23
end Outer.Inner
private example : Outer.Inner.ἀριθμός + Outer.Inner.«two words» = 42 := rfl
''', '', ''),
    'V1-002': ('''public meta import Lean
-- A line comment and a /- spelling that is part of the comment.
/- outer /- nested -/ retained trivia -/
/-- exact documentation marker -/
def documented : Nat := 42
open Lean in
run_cmd do
  let some text ← findDocString? (← getEnv) ``documented | throwError "missing doc comment"
  unless text.trimAscii.toString == "exact documentation marker" do throwError "wrong doc comment"
''', '', ''),
    'V1-003': ('''public meta import Lean
syntax "quantity" num : term
macro_rules | `(quantity $n:num) => pure n
private example : quantity 42 = (42 : Nat) := rfl
private example : (2.5e1 : Float) == 25.0 := by native_decide
private example : 'λ'.toNat = 955 := rfl
private example : "42".length = 2 := rfl
''', '', ''),
    'V1-004': ('''function add(a: Nat, b: Nat): Nat := a + b
const rawText: String := r#"a"b"#
private example : rawText = "a\\"b" := rfl
#eval show IO Unit from do
  if s!"answer:{add 19 23}" == "answer:42" then pure Unit.unit else throw (IO.userError "interpolation")
''', '', ''),
    'V1-005': ('''universe u
def idSort.{v} (α : Sort v) (x : α) : α := x
def idType {α : Type u} (x : α) : α := x
private example : idSort.{0} True True.intro = True.intro := rfl
private example : idType(42) = 42 := rfl
private example : Prop = Sort 0 := rfl
''', '', ''),
    'V1-006': ('''function implicit {α: Type}(x: α): α := x
function strict ⦃α: Type⦄(x: α): α := x
function choose {α: Type}[Inhabited α](x: α): α := x
private example : implicit(1) = 1 := rfl
private example : strict(2) = 2 := rfl
private example : choose(3) = 3 := rfl
open Lean in
run_cmd do
  for (name, expected) in [(``implicit, BinderInfo.implicit), (``strict, BinderInfo.strictImplicit)] do
    let .forallE _ _ (.forallE _ _ _ explicit) actual := (← getConstInfo name).type |
      throwError "binder telescope"
    unless actual == expected && explicit.isExplicit do throwError "binder kind"
  let .forallE _ _ (.forallE _ _ _ kind) _ := (← getConstInfo ``choose).type |
    throwError "instance telescope"
  unless kind.isInstImplicit do throwError "instance binder"
''', '', ''),
    'V1-007': ('''section
variable (n: Nat)
function ordered(k: Nat)[Decidable(k = n)](x: Fin(n + 1)): Nat := x.val + n
end
private example : ordered(4, 3, ⟨2, by decide⟩) = 6 := rfl
''', '', ''),
    'V1-008': ('''def ordinary (n : Nat := 42) : Nat := n
def automated (h : True := by trivial) : True := h
private example : ordinary() = 42 := rfl
private example : ordinary(n := 3) = 3 := rfl
private example : True := automated()
open Lean in
run_cmd do
  let .forallE _ ordinaryBinder _ _ := (← getConstInfo ``ordinary).type | throwError "ordinary telescope"
  let .forallE _ autoBinder _ _ := (← getConstInfo ``automated).type | throwError "automatic telescope"
  unless ordinaryBinder.isOptParam && autoBinder.isAutoParam do throwError "default annotation"
''', '', ''),
    'V1-009': ('''def dependent : (α : Type) → α → α := fun α x => x
def pattern : Option Nat → Nat := fun | some n => n | none => 0
private example : dependent(Nat, 42) = 42 := rfl
private example : pattern(some(7)) = 7 := rfl
private example : pattern(none) = 0 := rfl
''', '', ''),
    'PS0-N-BOOT-01': ('public import Init\ninit_quot\ninit_quot\n', '', r'quotient.*already|already.*quot|kernel.*quot'),
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
        result = subprocess.run([args.driver, 'check', path], text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        log = result.stdout
        (args.output / (case + '.log')).write_text(log, encoding='utf-8')
        ok = (result.returncode == 1 and re.search(diagnostic, log, re.I)) if diagnostic else (
            result.returncode == 0 and expected in log)
        (passed if ok else failures).append(case)
        print(case, 'PASS' if ok else 'FAIL', result.returncode, log, flush=True)
    evidence = {'passed': passed, 'failures': failures, 'fixtures': fixtures,
                'driver_sha256': hashlib.sha256(args.driver.read_bytes()).hexdigest()}
    (args.output / 'result.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('PS0_R2_LEXICAL_TYPES', json.dumps(evidence), flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
