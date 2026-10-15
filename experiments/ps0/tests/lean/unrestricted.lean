import Lean

/-!
Ordinary .lean is deliberately unrestricted. These declarations are valid
Lean source but explicitly outside the PSCV0 v7 .ps profile.
-/

axiom nativeAssumption : Prop
unsafe def nativeUnsafe : Nat := 40
partial def nativePartial (n : Nat) : Nat :=
  if n == 0 then 0 else nativePartial (n - 1)
theorem nativeProofHole : True := by sorry

#eval nativeUnsafe + 2
#eval do
  IO.println "PS0_LEAN_UNRESTRICTED_OK"
