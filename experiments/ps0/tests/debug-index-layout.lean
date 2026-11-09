module
import Lean
import PS0

/-! Inspect native indexing dispatch and PS operands before elaboration. -/
open Lean
run_cmd do
  let env ← Lean.MonadEnv.getEnv
  for input in ["#[2, 3][0]", "#[2, 3][chooseIndex(0)]",
      "#[2, 3][chooseIndex(0)]?", "#[2, 3][chooseIndex(0)]!",
      "#[2, 3][0]'(bound(1))", "(makeStore(2) |>.entries)[chooseIndex(1)]!",
      "makeStore(2) |>.entries[chooseIndex(1)]?", "#[Nat.succ][chooseIndex(0)]!(2)"] do
    match Parser.runParserCategory env `psTerm input with
    | .ok syntax => logInfo m!"PS0_INDEX_PARSE {input}: {repr syntax}"
    | .error error => logInfo m!"PS0_INDEX_PARSE_ERROR {input}: {error}"
