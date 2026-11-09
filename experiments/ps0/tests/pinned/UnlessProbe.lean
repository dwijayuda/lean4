module
prelude
public import Lean
/-! Native unless conditions/blocks and early return must retain compiler output identity. -/
public section
namespace Lean.Compiler.UnlessProbe

def add (x y : Nat) : Nat := x + y
def below (n : Nat) : Bool := n < 3
def observe (n : Nat) : IO Unit := if n == 99 then pure () else pure ()
def bodyValue : IO Nat := do
  let mut total := 0
  unless below (add (1) (2)) do
    total := add total (2)
  unless below (add (0) (1)) do
    total := add total (100)
  return total
def early (n : Nat) : IO Nat := do
  unless below (add n (1)) do
    return add n (10)
  return add n (20)
def termValue : IO Unit := unless below (add (1) (2)) do
  observe (add (1) (2))

end Lean.Compiler.UnlessProbe
