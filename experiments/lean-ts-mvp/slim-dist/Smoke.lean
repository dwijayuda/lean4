/-
Copyright (c) 2026. Released under Apache 2.0 license.
-/
module

import Lean

/-! Check everyday Lean tactics and compile-time evaluation in a slim runtime. -/

example (n : Nat) : n = n := by simp
example (n : Nat) : n + 0 = n := by omega
example (n : Nat) : n = n := by grind

#check Nat.add
#eval Nat.add 2 3
