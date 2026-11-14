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
function nested(x: Option (Option Nat)): Nat := match x with {
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
    evidence = {'passed': passed, 'failures': failures, 'fixtures': fixtures,
                'driver_sha256': hashlib.sha256(args.driver.read_bytes()).hexdigest()}
    (args.output / 'result.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('PS0_R2_DATA_PATTERN', json.dumps(evidence), flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
