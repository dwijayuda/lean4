import NativeMath

def referenceAdd (x y : Nat) : Nat := x + y
def referenceSquare (n : Nat) : Nat := n * n

theorem ps0AddCorrespondence (x y : Nat) :
    NativeMath.add x y = referenceAdd x y := by rfl

theorem ps0SquareCorrespondence (n : Nat) :
    NativeMath.square n = referenceSquare n := by rfl

-- v7 nullary functions are genuine Unit -> Nat, not hidden zero-arity calls.
-- The reference is Lean syntax; both expressions must be definitionally equal.
theorem ps0NullaryUnitCorrespondence :
    NativeMath.tick () = (fun (_u : Unit) => (42 : Nat)) () := by rfl

def main : IO Unit := do
  let result := NativeMath.add 20 22
  if result == 42 && NativeMath.square 7 == 49 && NativeMath.tick () == 42 then
    IO.println "PS0_NATIVE_OK"
  else
    throw <| IO.userError "native ProofScript computation mismatch"
