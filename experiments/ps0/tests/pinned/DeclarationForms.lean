module
prelude
public import Lean
/-! Equation theorems, instance signatures and native where-field declarations. -/
public section
namespace Lean.Compiler.DeclarationForms

structure Pair where
  value : Nat
  apply : Nat → Nat
  witness : True

def make (n : Nat) : Pair where
  value := Nat.succ (n)
  apply x := Nat.add (n) (x)
  witness := True.intro

theorem boolRefl : (b : Bool) → b = b
  | true => Eq.refl (true)
  | false => Eq.refl (false)

class Transform (α : Type) where
  apply : α → α

instance natTransform : Transform (Nat) where
  apply x := Nat.succ (x)

instance : Inhabited (Pair) where
  default := make (0)

def boolTransform : Transform Bool where
  apply
    | true => id (true)
    | false => id (false)

def makeCurried (n : Nat) : Pair where
  value := Nat.add n 1
  apply x := Nat.add n x
  witness := True.intro

def boolDecision (a b : Bool) : Decidable (Eq a b) where
  decide := a.beq b
  reflects_decide :=
    match a, b with
    | false, false => rfl
    | false, true => Bool.noConfusion
    | true, false => Bool.noConfusion
    | true, true => rfl

example [Subsingleton α] (p : α → Prop) : Subsingleton (Subtype p) :=
  ⟨fun ⟨x, _⟩ ⟨y, _⟩ => by congr; exact Subsingleton.elim x y⟩
example (n : Nat := Nat.add (1) (2)) : Eq (n) (n) := Eq.refl (n)

theorem nestedEllipsis (a i j : Nat) : a - i ≤ a + j - i :=
  Nat.sub_le_sub_right (Nat.le_add_right ..) ..
theorem namedEllipsis (a i j : Nat) : a - i ≤ a + j - i :=
  Nat.sub_le_sub_right (Nat.le_add_right ..) (k := i) ..

end Lean.Compiler.DeclarationForms
