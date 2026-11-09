module
meta import Lean
meta import PS0.StandardAdapters
/-! Retain native parser diagnostics for multiline PS where-field boundaries. -/
open Lean Elab.Command
open scoped PS0.StandardAdapters
meta section
run_cmd do
  let env ← getEnv
  for input in [
    "def exampleWhere (n : Nat) : Pair where\n  value := Nat.add n 1\n  apply x := Nat.add n x\n  witness := True.intro\n",
    "def boolDecision (a b : Bool) : Decidable( (Eq a b)) where\n  decide := a.beq b\n  reflects_decide :=\n    match a, b with\n    | false, false => rfl\n    | false, true => Bool.noConfusion\n    | true, false => Bool.noConfusion\n    | true, true => rfl\n"] do
    match Parser.runParserCategory env `command input with
    | .ok stx => logInfo m!"PS0_WHERE_PARSE_OK: {repr stx}"
    | .error message => logInfo m!"PS0_WHERE_PARSE_ERROR: {message}"
