module
meta import Lean
meta import PS0.StandardAdapters
/-! Check nested PS operator/projection parsing and retain scoped where-layout diagnostics. -/
open Lean Elab.Command
open scoped PS0.StandardAdapters
meta section
run_cmd do
  let env ← getEnv
  for input in [
    "List.map((· + 1), [1])",
    "(List.map((· + 1), [1]))",
    "(List.map((· + 1), [1])).head!",
    "· + (List.map((· + 1), [1])).head!",
    "(· + (List.map((· + 1), [1])).head!)",
    "xs.map((· + (List.map((· + 1), [1])).head!))",
    "· + List.length([1])",
    "· + (List.length([1]))",
    "· + (1)"] do
    match Parser.runParserCategory env `psTerm input with
    | .ok stx => logInfo m!"PS0_TERM_PARSE_OK: {input}; kind={stx.getKind}"
    | .error message => throwError "PS0_TERM_PARSE_ERROR: {input}; {message}"
  for input in [
    "def exampleWhere (n : Nat) : Pair where\n  value := Nat.add n 1\n  apply x := Nat.add n x\n  witness := True.intro\n",
    "def boolDecision (a b : Bool) : Decidable( (Eq a b)) where\n  decide := a.beq b\n  reflects_decide :=\n    match a, b with\n    | false, false => rfl\n    | false, true => Bool.noConfusion\n    | true, false => Bool.noConfusion\n    | true, true => rfl\n"] do
    match Parser.runParserCategory env `command input with
    | .ok stx => logInfo m!"PS0_WHERE_PARSE_OK: {repr stx}"
    | .error message => logInfo m!"PS0_WHERE_PARSE_ERROR: {message}"
