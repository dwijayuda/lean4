/-! Native telescope forms admitted by R2 must retain elaboration and output identity. -/
module
prelude
public import Lean
public section
namespace Lean.Compiler.TelescopeProbe
def typed (x : Nat) : Nat := x + 1
def implicitFirst {α : Type} (x : α) : α := x
def implicitInferred {α} (x : α) : α := x
def strictFirst ⦃α : Type⦄ (x : α) : α := x
def asciiStrict {{α : Type}} (x : α) : α := x
def interleaved (x : Nat) {α : Type} (y : α) : Nat := x
def grouped (x y : Nat) : Nat := x + y
def inferred (x y) := Nat.add x y
def bare x := Nat.succ x
def anonymous (_ : Nat) (y : Nat) : Nat := y
def autoProof (n : Nat) (h : n = n := by rfl) : Nat := n
def ordinaryProof (n : Nat) (h : n = n := (by rfl)) : Nat := n
def groupedDefault (x y : Nat := 3) : Nat := x + y
end Lean.Compiler.TelescopeProbe
