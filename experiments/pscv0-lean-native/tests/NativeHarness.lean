import NativeMath

def referenceAdd (x y : Nat) : Nat := x + y
def referenceSquare (n : Nat) : Nat := n * n

theorem pscv0AddCorrespondence (x y : Nat) :
    NativeMath.add x y = referenceAdd x y := by rfl

theorem pscv0SquareCorrespondence (n : Nat) :
    NativeMath.square n = referenceSquare n := by rfl

def main : IO Unit := do
  let result := NativeMath.add 20 22
  if result == 42 && NativeMath.square 7 == 49 then
    IO.println "PSCV0_NATIVE_OK"
  else
    throw <| IO.userError "native ProofScript computation mismatch"
