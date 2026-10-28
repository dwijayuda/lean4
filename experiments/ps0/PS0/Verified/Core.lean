module
public import Lean

public section

/-!
A deliberately small, typed-by-construction executable fragment.

There are exactly two Nat inputs and no effects, imports, calls, recursion,
unsafe operations or erased runtime data in this first slice. TargetExpr
models the emitted NONNEGATIVE BigInt fragment, not all ECMAScript. An
unguarded subtraction that would produce a negative value is undefined in
this restricted model. The lowerer proves it never produces that case.

The theorem below is source-to-target-MODEL correspondence. Connecting the
model to source bytes, TypeScript erasure, an engine and resource limits is
an explicit conditional trust boundary, not another kernel theorem.
-/
namespace PS0.Verified

inductive NatExpr where
  | first | second
  | literal (value : Nat)
  | add (left right : NatExpr)
  | mul (left right : NatExpr)
  | sub (left right : NatExpr)
  deriving Repr, DecidableEq, Inhabited

@[expose] def NatExpr.eval : NatExpr → Nat → Nat → Nat
  | .first, x, _ => x
  | .second, _, y => y
  | .literal n, _, _ => n
  | .add a b, x, y => a.eval x y + b.eval x y
  | .mul a b, x, y => a.eval x y * b.eval x y
  | .sub a b, x, y => a.eval x y - b.eval x y

inductive TargetExpr where
  | first | second
  | literal (value : Nat)
  | add (left right : TargetExpr)
  | mul (left right : TargetExpr)
  | sub (left right : TargetExpr)
  | chooseGe (left right yes no : TargetExpr)
  deriving Repr, Inhabited

@[expose] def TargetExpr.eval : TargetExpr → Nat → Nat → Option Nat
  | .first, x, _ => some x
  | .second, _, y => some y
  | .literal n, _, _ => some n
  | .add a b, x, y =>
      match a.eval x y, b.eval x y with
      | some l, some r => some (l + r)
      | _, _ => none
  | .mul a b, x, y =>
      match a.eval x y, b.eval x y with
      | some l, some r => some (l * r)
      | _, _ => none
  | .sub a b, x, y =>
      match a.eval x y, b.eval x y with
      | some l, some r => if r ≤ l then some (l - r) else none
      | _, _ => none
  | .chooseGe a b yes no, x, y =>
      match a.eval x y, b.eval x y with
      | some l, some r => if r ≤ l then yes.eval x y else no.eval x y
      | _, _ => none

@[expose] def lower : NatExpr → TargetExpr
  | .first => .first
  | .second => .second
  | .literal n => .literal n
  | .add a b => .add (lower a) (lower b)
  | .mul a b => .mul (lower a) (lower b)
  | .sub a b =>
      .chooseGe (lower a) (lower b) (.sub (lower a) (lower b)) (.literal 0)

/-- All supported expressions preserve their mathematical Nat result;
    generated target-model evaluation is defined, not merely safe if it ends. -/
theorem lower_correct (e : NatExpr) (x y : Nat) :
    (lower e).eval x y = some (e.eval x y) := by
  induction e with
  | first => rfl
  | second => rfl
  | literal n => rfl
  | add a b ha hb =>
      simp [lower, TargetExpr.eval, NatExpr.eval, ha, hb]
  | mul a b ha hb =>
      simp [lower, TargetExpr.eval, NatExpr.eval, ha, hb]
  | sub a b ha hb =>
      by_cases h : b.eval x y ≤ a.eval x y
      · simp [lower, TargetExpr.eval, NatExpr.eval, ha, hb, h]
      · have hz : a.eval x y - b.eval x y = 0 :=
          Nat.sub_eq_zero_of_le (Nat.le_of_lt (Nat.lt_of_not_ge h))
        simp [lower, TargetExpr.eval, NatExpr.eval, ha, hb, h, hz]

end PS0.Verified
