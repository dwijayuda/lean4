import PS0.Policy
/-! Inspect native and owned operator parse boundaries, including empty calls after arrow types. -/
open Lean Lean.Parser
open scoped PS0.StandardAdapters

run_cmd do
  let env ← getEnv
  for (category, text) in #[
      (`term, "Unit → Nat"), (`psTerm, "Unit → Nat"),
      (`term, "higher()"), (`psTerm, "higher()"),
      (`command, "def bad : Unit → Nat := higher()") ] do
    let state := (categoryParser category 0).fn.run (mkInputContext text "operator-boundary")
      {env, options := {}} (getTokenTable env) (mkParserState text)
    logInfo m!"PS0_OPERATOR_PARSE_BOUNDARY category={category} input={text} stop={state.pos.byteIdx} lhsPrec={state.lhsPrec} error={state.hasError} syntax={repr state.stxStack.back}"
