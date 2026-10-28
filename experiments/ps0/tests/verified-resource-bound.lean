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
example : (nestedSub 32).targetSize = 65537 := by decide
example : (nestedSub 32).withinOutputBudget = false := by decide

-- Only the small expression is rendered; the deep case must be refused
-- by the staging command before constructing lower/render output.
#guard (emit (.sub .first .second) true).utf8ByteSize < 65536
