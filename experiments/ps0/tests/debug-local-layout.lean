module
meta import Lean
meta import PS0.StandardAdapters

/-! Retain pinned native local declaration layouts before extending their telescopes. -/
open Lean Elab.Command
meta section
partial def localLayout (stx : Syntax) : String :=
  toString stx.getKind ++ "[" ++ toString stx.getArgs.size ++ "](" ++
    String.intercalate "," (stx.getArgs.toList.map localLayout) ++ ")"
run_cmd do
  let env ← getEnv
  for input in ["let step (x : Nat := 3) : Nat := x; step",
      "let +nondep step (x : Nat) : Nat := x; step 4",
      "let rec step (x : Nat) : Nat := x; step 4",
      "do let step {α : Type} [Inhabited α] (x y : Nat) : Nat := x + y; return step 2 3",
      "let x := 1; x", "let xs := #[1]; let xs[0] := 2; xs"] do
    match Parser.runParserCategory env `term input with
    | .ok stx => logInfo m!"PS0_NATIVE_LOCAL_LAYOUT {input}: {localLayout stx}"
    | .error error => throwError "native local control failed: {input}: {error}"
