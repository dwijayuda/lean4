/-
Copyright (c) 2026. Released under Apache 2.0 license.
-/
module

import Lean
import LeanTs

/-! Kernel-checked Lean functions and proofs, with emitted Nat-only TypeScript. -/

def increment (n : Nat) : Nat :=
  Nat.add n 1

def square (n : Nat) : Nat :=
  Nat.mul n n

def saturatingSub (a b : Nat) : Nat :=
  Nat.sub a b

theorem increment_gt (n : Nat) : n < increment n := by
  unfold increment
  omega

theorem saturatingSub_le (a b : Nat) : saturatingSub a b ≤ a := by
  unfold saturatingSub
  omega

#lean_ts_export increment
#lean_ts_export square
#lean_ts_export saturatingSub
