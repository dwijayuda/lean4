module
prelude
public import Lean
/-! Native do layout, local signatures/defaults, bindings and mutable ID operands. -/
public section
namespace Lean.Compiler.DoLayoutProbe

def add (x y : Nat) : Nat := x + y
def pureNat (n : Nat) : IO Nat := pure n
def observe (n : Nat) : IO Unit := if n == 99 then pure () else pure ()

def layoutValue : IO Nat := do
  let first : Nat := add (1) (1)
  let mut total := add first (1)
  total := add total (1)
  let next : Nat ← pureNat (add (1) (2))
  observe (next)
  return add next (total)

def nestedValue : IO Nat := do
  let value ← do
    let first := add (1) (1)
    return add first (1)
  return value

def localDefault : IO Nat := do
  let step (x : Nat := add (1) (2)) : Nat := add x (1)
  return step

def localShared : IO Nat := do
  let step (x y : Nat) : Nat := add x (y)
  return step (1) (2)

def unitReturn : IO Unit := do
  return

end Lean.Compiler.DoLayoutProbe
