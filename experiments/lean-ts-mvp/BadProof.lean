/-
Copyright (c) 2026. Released under Apache 2.0 license.
-/
module

import Lean
meta import LeanTs

/-! Invalid Lean proofs must prevent a successful compilation. -/

theorem impossible : (1 : Nat) = 2 := by omega

def afterBadProof (n : Nat) : Nat := Nat.add n 1

#lean_ts_export afterBadProof
