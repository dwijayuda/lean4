import PS0.HostCategories
/-! Bound nested-parenthesis parsing through native and PS category infrastructure. -/
open Lean Lean.Parser

unsafe def main : IO Unit := do
  initSearchPath (← findSysroot)
  enableInitializersExecution
  let env ← importModules #[{module := `PS0.HostCategories, isMeta := true}] {}
    (leakEnv := true) (loadExts := true)
  let mut rows := #[]
  for category in #[`term, `psTerm] do
    for depth in #[4, 8, 12, 16] do
      let text := String.ofList (List.replicate depth '(') ++ "Nat.succ(1)" ++
        String.ofList (List.replicate depth ')')
      let start ← IO.monoMsNow
      let state := (categoryParser category 0).fn.run (mkInputContext text "paren-budget")
        {env, options := {}} (getTokenTable env) (mkParserState text)
      let elapsed := (← IO.monoMsNow) - start
      unless !state.hasError && state.pos == text.rawEndPos do
        throw (IO.userError s!"PS0_PAREN_PARSE: {category}/{depth}")
      let row := Json.mkObj [("category", toJson category.toString),
        ("depth", toJson depth), ("milliseconds", toJson elapsed)]
      IO.println ("PS0_PAREN_ROW:" ++ row.compress)
      rows := rows.push row
  IO.println ("PS0_PAREN_BUDGET:" ++ (toJson rows).compress)
