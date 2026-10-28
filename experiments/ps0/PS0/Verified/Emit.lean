import PS0.Verified.Core

/-! Candidate-only emitter. It cannot publish a verified artifact. The host
pipeline must independently replay the proofs and check the exact bytes.
TypeScript output is actual typed source, not just declarations. -/
namespace PS0.Verified

private def render : TargetExpr → String
  | .first => "stock"
  | .second => "requested"
  | .literal n => toString n ++ "n"
  | .add a b => "(" ++ render a ++ " + " ++ render b ++ ")"
  | .mul a b => "(" ++ render a ++ " * " ++ render b ++ ")"
  | .sub a b => "(" ++ render a ++ " - " ++ render b ++ ")"
  | .chooseGe a b yes no =>
      "((" ++ render a ++ " >= " ++ render b ++ ") ? " ++
      render yes ++ " : " ++ render no ++ ")"

/-- The fixed export ABI is intentionally not a general FFI. Invalid host
    inputs throw before arithmetic; valid inputs are primitive BigInts. -/
def emit (e : NatExpr) (typescript : Bool) : String :=
  let args := if typescript then "stock: bigint, requested: bigint" else "stock, requested"
  let result := if typescript then ": bigint" else ""
  "// PS0 experimental conditional Nat2 slice; see evidence.json.\n" ++
  "export function remaining(" ++ args ++ ")" ++ result ++ " {\n" ++
  "  if (typeof stock !== \"bigint\" || stock < 0n) throw new TypeError(\"Expected Nat bigint: stock\");\n" ++
  "  if (typeof requested !== \"bigint\" || requested < 0n) throw new TypeError(\"Expected Nat bigint: requested\");\n" ++
  "  return " ++ render (lower e) ++ ";\n" ++
  "}\n"

def NatExpr.json : NatExpr → Lean.Json
  | .first => Lean.Json.arr #[Lean.Json.str "first"]
  | .second => Lean.Json.arr #[Lean.Json.str "second"]
  | .literal n => Lean.Json.arr #[Lean.Json.str "literal", Lean.Json.str (toString n)]
  | .add a b => Lean.Json.arr #[Lean.Json.str "add", a.json, b.json]
  | .mul a b => Lean.Json.arr #[Lean.Json.str "mul", a.json, b.json]
  | .sub a b => Lean.Json.arr #[Lean.Json.str "sub", a.json, b.json]

end PS0.Verified
