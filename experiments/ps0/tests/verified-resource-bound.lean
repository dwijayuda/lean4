import PS0.Verified.Emit

open PS0.Verified

-- These are model/resource regressions, not a serialization theorem.
private def nestedSub : Nat → NatExpr
  | 0 => .first
  | n + 1 => .sub (nestedSub n) .second

example : (NatExpr.add .first .second).targetSize = 19 := by decide
example : (NatExpr.sub .first .second).targetSize = 49 := by decide
example : (NatExpr.literal 1234567890).targetSize = 11 := by decide
example : (NatExpr.sub .first .second).withinOutputBudget = true := by decide

-- Once saturated, deeper source expressions cannot become eligible again.
-- A reusable induction avoids asking the elaborator to unfold a deep tree.
private theorem saturated_step (e : NatExpr) (h : e.targetSize = 65537) :
    (NatExpr.sub e .second).targetSize = 65537 := by
  change min 65537 (2 * (e.targetSize + 9) + 21) = 65537
  rw [h]
  decide

private theorem nested_saturated (n : Nat) :
    (nestedSub (11 + n)).targetSize = 65537 := by
  induction n with
  | zero => decide
  | succ n ih =>
      change (NatExpr.sub (nestedSub (11 + n)) .second).targetSize = 65537
      exact saturated_step _ ih

example : (nestedSub 32).targetSize = 65537 := nested_saturated 21
example : (nestedSub 32).withinOutputBudget = false := by
  change decide ((nestedSub 32).targetSize + 512 ≤ 65536) = false
  rw [nested_saturated 21]
  decide

-- Only the small expression is rendered; the deep case must be refused
-- by the staging command before constructing lower/render output.
#guard (emit (.sub .first .second) true).utf8ByteSize < 65536
