/-
Copyright (c) 2026. Released under Apache 2.0 license.
-/
module

import LeanTs

/-! Unsupported Lean executable constants must be rejected. -/

def unsupported (n : Nat) : Nat :=
  Nat.div n 2

#lean_ts_export unsupported
