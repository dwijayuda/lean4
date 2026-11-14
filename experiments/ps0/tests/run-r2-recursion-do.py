#!/usr/bin/env python3
"""Qualify R2 recursion and do notation through Lean's PS0 frontend."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

CASES = {
    'V1-046': ('''function length(xs: List Nat): Nat := match xs with
  | [] => 0
  | _ :: tail => 1 + length(tail)
termination_by structural xs
private example : length([1, 2, 3]) = 3 := rfl
''', (), ''),
    'V1-052': ('''const result: Option Nat := do
  let x ← some 5
  let y := 2 + (← some 3)
  pure(x + y)
private example : result = some(10) := rfl
''', (), ''),
    'V1-053': ('''const result: Option Nat := do
  let mut count := 2
  count := count + 3
  count ← some count.succ
  return count
private example : result = some(6) := rfl
''', (), ''),
    'V1-054': ('''function fallback(input: Option Nat): Id Nat := do
  let some n := input | return 99
  return n
private example : Id.run(fallback(some(7))) = 7 := rfl
private example : Id.run(fallback(none)) = 99 := rfl
''', (), ''),
    'V1-055': ('''function branch(input: Option Nat): Id Nat := do
  let mut n := 0
  if let some k ← (pure input : Id(Option Nat)) then
    n := k
  else
    n := 4
  unless n == 7 do n := n + 1
  return n
private example : Id.run(branch(some(7))) = 7 := rfl
private example : Id.run(branch(none)) = 5 := rfl
''', (), ''),
    'V1-058': ('''function run(limit: Nat): Id Nat := do
  let mut total := 0
  for n in [1, 2, 3, 4] do
    if n == 1 then continue
    if n == limit then return total + 100
    if n == 4 then break
    total := total + n
  return total
private example : Id.run(run(3)) = 102 := rfl
private example : Id.run(run(9)) = 5 := rfl
''', (), ''),
    'PS0-P-REC-01': ('''function down(n: Nat): Nat :=
  if n = 0 then 0 else 1 + down(n - 1)
termination_by n
decreasing_by omega
private example : down(4) = 4 := by simp [down]
''', (), ''),
    'PS0-P-REC-02': ('''partial function spin(n: Nat): Nat := spin(n)
open Lean in
run_cmd do
  let env ← getEnv
  let some (.opaqueInfo _) := env.find? ``spin | throwError "missing opaque logical interface"
  unless (env.find? (Compiler.mkUnsafeRecName ``spin)).any ConstantInfo.isPartial do
    throwError "missing partial implementation"
''', (), ''),
    'PS0-P-REC-03': ('''function eventually(n: Nat): Option Nat :=
  if n == 0 then some(7) else eventually(n - 1)
partial_fixpoint
private example : eventually(0) = some(7) := by simp [eventually.eq_def]
''', (), ''),
    'PS0-P-REC-04': ('''function least(n: Nat): Prop := n = 0 ∨ least(n - 1)
inductive_fixpoint
function greatest(n: Nat): Prop := n = 0 ∧ greatest(n)
coinductive_fixpoint
private example : least(0) := by
  rw [least.eq_def]
  exact Or.inl rfl
private example : ¬ (greatest 1) := by
  rw [greatest.eq_def]
  exact fun h => Nat.noConfusion h.1
''', (), ''),
    'PS0-P-DO-01': ('''const value: Id Nat := do { let mut n := 0; n := n + 1; return n }
private example : Id.run(value) = 1 := rfl
''', (), ''),
    'PS0-P-DO-02': ('''const value: Id Nat := do
  let mut total := 0
  for x in [1, 2, 90], y in [10, 20] do { total := total + x + y }
  return total
private example : Id.run(value) = 33 := rfl
''', (), ''),
    'PS0-P-DO-03': ('''const loopResult: IO Nat := do
  let mut n := 0
  repeat
    n := n + 1
    if n == 2 then break
  while n < 4 do
    n := n + 1
  repeat { n := n + 1 } until n == 6
  return n
#eval show IO Unit from do
  let observed ← loopResult
  if observed == 6 then pure Unit.unit else throw (IO.userError "loop oracle")
''', (), ''),
    'PS0-P-DO-04': ('''function getValue(x: Option Nat): Id Nat := do
  if let some n ← (pure x : Id(Option Nat)) then
    return n
  else
    return 0
private example : Id.run(getValue(some(7))) = 7 := rfl
private example : Id.run(getValue(none)) = 0 := rfl
''', (), ''),
    'PS0-P-DO-05': ('''def wrap {α : Type} (body : Option α) : Option α := body
const value: Option Nat := do
  wrap(do← { return 7 })
  return 9
private example : value = some(7) := rfl
''', (), ''),
    'PS0-P-DO-06': ('''def runCatch : IO Nat := do
  let cleanup ← IO.mkRef false
  let value ← try
    throw(IO.userError("trigger"))
  catch e : IO.Error =>
    match e with
    | .userError msg => pure(if msg == "trigger" then 7 else 0)
    | _ => pure 0
  finally
    cleanup.set true
  if ← cleanup.get then return value else return 0

def runPatternCatch : IO Nat := do
  try
    throw(IO.userError("pattern"))
  catch
  | .userError msg => return if msg == "pattern" then 9 else 0
  | _ => return 0
  finally
    pure Unit.unit

#eval show IO Unit from do
  let typed ← runCatch
  let patterned ← runPatternCatch
  if typed == 7 && patterned == 9 then pure Unit.unit else throw (IO.userError "catch oracle")
''', (), ''),
    'PS0-N-REC-01': ('''function bad(n: Nat): Nat := match n with
  | 0 => 0
  | k + 1 => bad(k)
termination_by structural n
decreasing_by omega
''', ('termination_by', 'decreasing_by'), r'Incompatible termination hint.*structural'),
    'PS0-N-REC-02': ('''function bad(n: Nat): Nat := if n = 0 then 0 else bad(n + 1)
termination_by n
decreasing_by omega
''', ('decreasing_by', 'function bad'), r'omega could not prove|failed to prove termination|could not prove|failed to discharge'),
    'PS0-N-REC-03': ('''function bad(n: Nat): Prop := ¬ (bad n)
inductive_fixpoint
''', ('function bad', 'inductive_fixpoint'), r'monotonicity|monotone'),
    'PS0-N-DO-01': ('''const bad: Id Nat := do
  let n := 1
  n := 2
  return n
''', ('n := 2',), r'cannot be mutated'),
    'PS0-N-DO-02': ('''const badBreak: Id Unit := do
  break
const badContinue: Id Unit := do
  continue
''', ('  break', '  continue'), r'must be nested inside a loop'),
    'PS0-N-DO-03': ('''def wrap (body : Id Nat) (after : Nat) : Id Nat := body
const bad: Id Nat := do
  wrap(do← { return 7 }, 9)
''', ('wrap(do',), r'do.*forward|do←.*(?:last|argument|allowed|unexpected)|(?:last|argument|allowed|unexpected).*do←'),
}
for family, case in {
    'V1-047': 'PS0-P-REC-01', 'V1-048': 'PS0-P-REC-02',
    'V1-049': 'PS0-P-REC-03', 'V1-050': 'PS0-P-REC-04',
    'V1-051': 'PS0-P-DO-01', 'V1-056': 'PS0-P-DO-02',
    'V1-057': 'PS0-P-DO-03', 'V1-059': 'PS0-P-DO-05',
    'V1-060': 'PS0-P-DO-06',
}.items():
    CASES[family] = CASES[case]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('driver', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True)
    passed, failures, fixtures = [], [], {}
    for case, (source, anchors, diagnostic) in CASES.items():
        path = args.output / (case + '.ps')
        path.write_text(source, encoding='utf-8')
        fixtures[case] = hashlib.sha256(path.read_bytes()).hexdigest()
        result = subprocess.run([args.driver, 'check', path], text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        log = result.stdout
        (args.output / (case + '.log')).write_text(log, encoding='utf-8')
        ok = result.returncode == 0
        if diagnostic:
            lines = {i for i, text in enumerate(source.splitlines(), 1) if any(a in text for a in anchors)}
            matched = {int(m[1]) for text in log.splitlines()
                       if (m := re.search(r':(\d+):\d+: error(?:\([^)]*\))?:', text))
                       and re.search(diagnostic, text, re.I)}
            ok = result.returncode == 1 and (lines <= matched if case == 'PS0-N-DO-02' else bool(lines & matched))
        (passed if ok else failures).append(case)
        print(case, 'PASS' if ok else 'FAIL', result.returncode, log, flush=True)
    evidence = {'passed': passed, 'failures': failures, 'fixtures': fixtures,
                'driver_sha256': hashlib.sha256(args.driver.read_bytes()).hexdigest()}
    (args.output / 'result.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('PS0_R2_RECURSION_DO', json.dumps(evidence), flush=True)
    return int(bool(failures))

if __name__ == '__main__':
    raise SystemExit(main())
