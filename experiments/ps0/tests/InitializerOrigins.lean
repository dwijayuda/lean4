import PS0.StandardAdapters

/-! Initializer lowering retains native roots, modifiers, phases, names and type/arrow tokens. -/

open Lean
open scoped PS0.StandardAdapters

run_cmd do
  let cases := #[
    "initialize origin : IO.Ref(List(Nat)) ← IO.mkRef([])",
    "builtin_initialize origin : IO.Ref(List(Nat)) ← IO.mkRef([])",
    "initialize IO.println(\"ordinary\")",
    "builtin_initialize IO.println(\"builtin\")"]
  for text in cases do
    let before ← match Parser.runParserCategory (← getEnv) `command text with
      | .ok source => pure source
      | .error message => throwError "{message}"
    unless before.isOfKind `PS0.StandardAdapters.ps0StandardInitialize do
      throwError "PS0_INITIALIZER_ORIGIN_WRAPPER"
    let after ← Elab.liftMacroM <| PS0.StandardAdapters.lowerInitialize before
    let native := before[0]
    unless after.getKind == native.getKind && after.getRange? == native.getRange? do
      throwError "PS0_INITIALIZER_ORIGIN_ROOT"
    for index in #[0, 1] do
      unless native[index].eqWithInfo after[index] do
        throwError "PS0_INITIALIZER_ORIGIN_MODIFIER_OR_PHASE"
    unless native[2].getArgs.size == after[2].getArgs.size do
      throwError "PS0_INITIALIZER_ORIGIN_NAMED_SHAPE"
    if !native[2].getArgs.isEmpty then
      for index in #[0, 2] do
        unless native[2][index].eqWithInfo after[2][index] do
          throwError "PS0_INITIALIZER_ORIGIN_NAME_OR_ARROW"
      unless native[2][1][0].eqWithInfo after[2][1][0] do
        throwError "PS0_INITIALIZER_ORIGIN_TYPE_COLON"
  logInfo "PS0_INITIALIZER_ORIGINS: PASS 4"
