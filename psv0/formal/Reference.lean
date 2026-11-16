-- Copyright (c) 2026 ProofScript contributors. All rights reserved.
-- Independent reference semantics for PSV0's current arithmetic IR.
namespace PSV0Reference

inductive Expr where
  | lit (value : Nat)
  | arg (index : Nat)
  | add (left right : Expr)
  | sub (left right : Expr)
  | mul (left right : Expr)
  deriving Repr

namespace Expr

-- Mathematical Nat semantics, including saturating subtraction.
def eval (arguments : List Nat) : Expr → Nat
  | .lit n => n
  | .arg i => (arguments.get? i).getD 0
  | .add x y => eval arguments x + eval arguments y
  | .sub x y => eval arguments x - eval arguments y
  | .mul x y => eval arguments x * eval arguments y

-- A model of the bigint target's nonnegative subtraction branch.
def targetSub (a b : Nat) : Nat := if b ≤ a then a - b else 0

private theorem targetSub_eq (a b : Nat) : targetSub a b = a - b := by
  by_cases h : b ≤ a
  · simp [targetSub, h]
  · have hle : a ≤ b := Nat.le_of_lt (Nat.lt_of_not_ge h)
    simp [targetSub, h, Nat.sub_eq_zero_of_le hle]

def evalTarget (arguments : List Nat) : Expr → Nat
  | .lit n => n
  | .arg i => (arguments.get? i).getD 0
  | .add x y => evalTarget arguments x + evalTarget arguments y
  | .sub x y => targetSub (evalTarget arguments x) (evalTarget arguments y)
  | .mul x y => evalTarget arguments x * evalTarget arguments y

-- This proves only the restricted mathematical target MODEL, not real JS/TS.
theorem targetModel_correct (e : Expr) (arguments : List Nat) :
    evalTarget arguments e = eval arguments e := by
  induction e with
  | lit n => rfl
  | arg i => rfl
  | add x y hx hy => simp [evalTarget, eval, hx, hy]
  | sub x y hx hy => simp [evalTarget, eval, targetSub_eq, hx, hy]
  | mul x y hx hy => simp [evalTarget, eval, hx, hy]

end Expr
end PSV0Reference
