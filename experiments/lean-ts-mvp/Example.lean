/-
Copyright (c) 2026. Released under Apache 2.0 license.
-/
module

import Lean
meta import LeanTs

/-! Kernel-checked Lean functions and proofs, with emitted Nat-only TypeScript. -/

def increment (n : Nat) : Nat :=
  Nat.add n 1

def square (n : Nat) : Nat :=
  Nat.mul n n

def saturatingSub (a b : Nat) : Nat :=
  Nat.sub a b

theorem increment_gt (n : Nat) : n < increment n := by
  simpa only [increment] using (Nat.lt_add_one n)

theorem square_nonneg (n : Nat) : 0 ≤ square n := by
  exact Nat.zero_le (square n)

#lean_ts_export increment
#lean_ts_export square
#lean_ts_export saturatingSub
