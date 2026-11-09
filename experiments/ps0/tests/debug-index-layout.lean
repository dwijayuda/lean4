module
meta import Lean
meta import PS0.StandardAdapters

/-! Inspect native indexing dispatch and PS operands before elaboration. -/
open Lean Elab.Command
open scoped PS0.StandardAdapters
meta section
run_cmd do
  let env ← getEnv
  for input in ["#[2, 3][0]", "#[2, 3][chooseIndex(0)]",
      "#[2, 3][chooseIndex(0)]?", "#[2, 3][chooseIndex(0)]!",
      "#[2, 3][0]'(bound(1))", "(makeStore(2) |>.entries)[chooseIndex(1)]!",
      "makeStore(2) |>.entries[chooseIndex(1)]?", "#[Nat.succ][chooseIndex(0)]!(2)"] do
    match Parser.runParserCategory env `psTerm input with
    | .ok stx => logInfo m!"PS0_INDEX_PARSE {input}: {repr stx}"
    | .error error => logInfo m!"PS0_INDEX_PARSE_ERROR {input}: {error}"
