import NativeMath
def main : IO Unit := do
  let result := NativeMath.add 20 22
  if result == 42 && NativeMath.square 7 == 49 then
    IO.println "PSCV0_NATIVE_OK"
  else
    throw <| IO.userError "native ProofScript computation mismatch"
