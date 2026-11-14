#!/usr/bin/env python3
"""Check R2 data and pattern semantics through the PS0 frontend."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


# Each positive checks the resulting terms with Lean, including both layouts
# in DATA-01 and the named equation, motive, and generalization in PAT-03.
CASES = {
    'PS0-P-DATA-01': ('''structure BracedPoint where {
  x : Nat
  y : Nat
}
structure NativePoint where
  x : Nat
  y : Nat
inductive BracedColor where {
  | red
  | blue (shade : Nat)
} deriving Repr
inductive NativeColor where
  | red
  | blue (shade : Nat)
private example : ({ x := 2, y := 3 } : BracedPoint).y =
                  ({ x := 2, y := 3 } : NativePoint).y := rfl
function bracedShade(c: BracedColor): Nat := match c with
  | .red => 0
  | .blue n => n
function nativeShade(c: NativeColor): Nat := match c with
  | .red => 0
  | .blue n => n
private example : bracedShade(.blue(4)) = nativeShade(.blue(4)) := rfl
private example : bracedShade(.red) = nativeShade(.red) := rfl
#synth Repr BracedColor
''', None, None),
    'PS0-P-DATA-02': ('''inductive Color where
  | red
  | blue
instance : Inhabited Color := ⟨Color.red⟩
private example : (default : Color) = Color.red := rfl
''', None, None),
    'PS0-P-DATA-03': ('''structure Point where
  x : Nat
  y : Nat
deriving instance Repr for Point
#synth Repr Point
#eval reprStr ({ x := 2, y := 3 } : Point)
''', None, None),
    'PS0-P-DATA-04': ('''structure Point where
  x : Nat
  y : Nat
function move(p: Point): Point := { p with x := p.x + 1 }
const point: Point := { x := 2, y := 3 }
private example : (move(point)).x = 3 := rfl
private example : (move(point)).y = 3 := rfl
private example : point.x = 2 := rfl
''', None, None),
    'PS0-P-DATA-05': ('''const bounded: { n: Nat // n < 10 } := ⟨3, by { decide }⟩
private example : bounded.val = 3 := rfl
private example : bounded.val < 10 := bounded.property
''', None, None),
    'PS0-P-PAT-01': ('''function pred(n: Nat): Nat := match n with {
  | 0 => 0
  | k + 1 => k
}
private example : pred(0) = 0 := rfl
private example : pred(5) = 4 := rfl
''', None, None),
    'PS0-P-PAT-02': ('''function unpack(x: Option Nat): Nat := match x with {
  | some(n) => n
  | none => 0
}
function nested(x: Option(Option Nat)): Nat := match x with {
  | .some(.some(n,),) => n
  | .some(.none()) => 1
  | .none() => 0
}
function nativeSpaced(x: Option Nat): Nat := match x with
  | some (n) => n
  | none => 0
private example : unpack(some(7)) = 7 := rfl
private example : unpack(none) = 0 := rfl
private example : nested(some(some(8))) = 8 := rfl
private example : nested(some(none)) = 1 := rfl
private example : nested(none) = 0 := rfl
private example : nativeSpaced(some(9)) = 9 := rfl
''', None, None),
    'PS0-P-PAT-03': ('''function useEquation(n: Nat): Nat :=
  match h : n with {
    | 0 => by { have zero : n = 0 := h; exact n }
    | k + 1 => by { have succ : n = k + 1 := h; exact k }
  }
function dependent(n: Nat): n = n :=
  match (motive := (k : Nat) → k = k) n with {
    | 0 => rfl
    | k + 1 => rfl
  }
function generalized(n: Nat, h: n = n): n = n :=
  match (generalizing := true) n with {
    | 0 => h
    | k + 1 => h
  }
private example : useEquation(3) = 2 := rfl
private example : dependent(2) = rfl := rfl
private example : generalized(2, rfl) = rfl := rfl
''', None, None),
    'PS0-P-PAT-04': ('''inductive OnlyZero : Nat → Type where
  | zero : OnlyZero 0
function eliminate(impossible: OnlyZero(1)): Nat := nomatch impossible
''', None, None),
    'V1-024': ('''inductive Code : Nat → Type where
  | zero : Code 0
  | step (prev : Code n) : Code (n + 1)
example : Code.rec (motive := fun _ _ => Nat) 0 (fun _ k => k + 1)
    (.step(.step(.zero))) = 2 := rfl
#check Code.casesOn
#check Code.noConfusion
''', None, None),
    'V1-025': ('''mutual
inductive A where
  | zero
  | wrap (b : B)
inductive B where
  | wrap (a : A)
end
inductive Rose where
  | node (children : List Rose)
example : A = A := rfl
#check A.rec
#check B.rec
#check Rose.rec
''', None, None),
    'V1-026': ('''structure Point where { x: Nat }
structure ColoredPoint extends point : Point where
  make ::
  color : Nat
def p : ColoredPoint := ColoredPoint.make (Point.mk 2) 5
example : p.point.x = 2 ∧ p.color = 5 := ⟨rfl, rfl⟩
''', None, None),
    'V1-027': ('''structure Config where
  {α : Type}
  [inst : Inhabited α]
  value : α := default
  ok : value = value := rfl
def config : Config := { α := Nat }
example : (show Nat from config.value) = 0 := rfl
example : config.ok = rfl := rfl
''', None, None),
    'V1-028': ('''class Measure (α : Type) where { size: α → Nat }
instance : Measure Nat where
  size := id
class inductive Choice (α : Type) where
  | choose (value : α)
instance : Choice Nat := .choose 7
example : Measure.size(3) = 3 := rfl
example : (inferInstance : Choice Nat) = .choose 7 := rfl
''', None, None),
    'V1-029': ('''inductive Color where { | red | blue } deriving Repr
deriving instance DecidableEq for Color
example : Color.red ≠ Color.blue := by { decide }
#synth Repr Color
''', None, None),
    'V1-040': ('''inductive Marker : Nat → Type where
  | zero : Marker 0
  | next (n : Nat) : Marker (n + 1)
function inspect(n: Nat, m: Marker(n)): Nat := match n, m with
  | .(0), .zero => 0
  | .(k + 1), .next(k) => k + 1
example : inspect(3, .next(2)) = 3 := rfl
function predecessor(n: Nat): Nat := match n with { | 0 => 0 | k + 1 => k }
example : predecessor(7) = 6 := rfl
''', None, None),
    'V1-041': ('''function inspect(n: Nat, flag: Bool, h: n = n): n = n :=
  match (generalizing := true) n, flag with
  | 0, false => h
  | 0, true => h
  | k + 1, _ => rfl
example : inspect(0, true, rfl) = rfl := rfl
function explicitMotive(n: Nat, flag: Bool): n = n :=
  match (motive := (k : Nat) → Bool → k = k) n, flag with
  | 0, false => rfl
  | 0, true => rfl
  | k + 1, _ => rfl
example : explicitMotive(3, false) = rfl := rfl
''', None, None),
    'V1-042': ('''function inspect(value: Option Nat): Nat :=
  match h : value with {
    | chosen@(some n) => by {
        have e : value = some n := h
        have alias : Option Nat := chosen
        exact n
      }
    | none => 0
  }
example : inspect(some(7)) = 7 := rfl
''', None, None),
    'PS0-N-DATA-01': ('''inductive Negative where
  | mk (consume : Negative → Nat) : Negative
''', 'inductive Negative', r'non positive|non-positive|positivity'),
    'PS0-N-DATA-02': ('''const bad: { n: Nat // n < 10 } := ⟨3, True.intro⟩
''', 'const bad', r'type mismatch|application type mismatch'),
    'PS0-N-PAT-01': ('''function arbitrary(n: Nat): Nat := n + 1
function bad(n: Nat): Nat := match n with {
  | arbitrary(k) => k
  | _ => 0
}
''', '| arbitrary', r'invalid pattern|invalid constructor|not a constructor|PS0V1-PATTERN'),
    'PS0-N-PAT-02': ('''inductive Token where
  | mk (u : Unit)
function bad(t: Token): Nat := match t with {
  | Token.mk() => 1
}
inductive Defaulted where
  | mk (n : Nat := 2)
function badDefault(t: Defaulted): Nat := match t with {
  | Defaulted.mk() => 1
}
''', ('| Token.mk', '| Defaulted.mk'), r'Invalid pattern: Not enough arguments'),
    'PS0-N-PAT-03': ('''function bad(n: Nat): Nat := nomatch n
''', 'function bad', r'missing cases|did not eliminate|is not empty'),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('driver', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True)
    passed = []
    failures = []
    fixtures = {}
    for case, (source, anchor, diagnostic) in CASES.items():
        fixture = args.output / (case + '.ps')
        fixture.write_text(source, encoding='utf-8')
        fixtures[case] = hashlib.sha256(fixture.read_bytes()).hexdigest()
        result = subprocess.run([args.driver, 'check', fixture], text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        log = result.stdout
        (args.output / (case + '.log')).write_text(log, encoding='utf-8')
        if diagnostic is None:
            ok = result.returncode == 0
        else:
            anchors = (anchor,) if isinstance(anchor, str) else anchor
            lines = [next(i for i, text in enumerate(source.splitlines(), 1) if tag in text)
                     for tag in anchors]
            ok = result.returncode == 1 and all(any(
                re.search(rf':{line}:\d+: error(?:\([^)]*\))?:', entry)
                and re.search(diagnostic, entry, re.IGNORECASE) for entry in log.splitlines())
                for line in lines)
        (passed if ok else failures).append(case)
        print(case, 'PASS' if ok else 'FAIL', result.returncode, log, flush=True)
    # The mutual/nested witness also requires the positivity rejection.
    if 'V1-025' in passed and 'PS0-N-DATA-01' not in passed:
        passed.remove('V1-025')
        failures.append('V1-025')
    evidence = {'passed': passed, 'failures': failures, 'fixtures': fixtures,
                'driver_sha256': hashlib.sha256(args.driver.read_bytes()).hexdigest()}
    (args.output / 'result.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('PS0_R2_DATA_PATTERN', json.dumps(evidence), flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
