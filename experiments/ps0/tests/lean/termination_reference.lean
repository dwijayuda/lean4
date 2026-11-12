-- Native Lean 4.35.0 reference; no ProofScript grammar restrictions.
def down (n : Nat) : Nat :=
  if n == 0 then 0 else down (n - 1)
termination_by n
decreasing_by omega

def downInferred (n : Nat) : Nat :=
  if n == 0 then 0 else downInferred (n - 1)
termination_by n

theorem downZero : down 0 = 0 := by rfl
