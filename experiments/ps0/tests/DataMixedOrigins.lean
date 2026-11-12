import PS0.StandardAdapters

/-! Comma expansion preserves parameter identities and operand ranges at data signature positions. -/

open Lean

private partial def commaGroups (source : Syntax) : Array Syntax :=
  if source.isOfKind `PS0.StandardAdapters.psDataCommaBinder then #[source[0]]
  else source.getArgs.foldl (fun result child => result ++ commaGroups child) #[]

private partial def nativeBinder? (source parameter : Syntax) : Option Syntax :=
  if source.isOfKind ``Lean.Parser.Term.explicitBinder && source[1].getArgs.size == 1 &&
      source[1][0].getRange? == parameter[0].getRange? then some source
  else source.getArgs.findSome? (fun child => nativeBinder? child parameter)

open scoped PS0.StandardAdapters

run_cmd do
  let cases := #[
    "structure Origin (first: Nat, second: Nat := first + 1) where\n  value : Nat",
    "inductive Origin (first: Nat, second: Nat := first + 1) where\n  | mk (arg: Fin(add(first, 1)), tag: Nat := second) : Origin(first, second)",
    "class Origin where\n  value (first: Nat, second: Nat := first + 1) : Nat := add(first, second)"]
  let mut groups := 0
  let mut parameters := 0
  for text in cases do
    let before ← match Parser.runParserCategory (← getEnv) `command text with
      | .ok source => pure source
      | .error message => throwError "{message}"
    unless before.isOfKind `PS0.StandardAdapters.ps0StandardData do
      throwError "PS0_DATA_MIXED_ORIGIN_WRAPPER"
    let after ← Elab.liftMacroM <| PS0.StandardAdapters.lowerData before
    unless before[0].getKind == after.getKind && before[0].getRange? == after.getRange? do
      throwError "PS0_DATA_MIXED_ORIGIN_COMMAND"
    unless before[0][0].eqWithInfo after[0] && before[0][1][0].eqWithInfo after[1][0] do
      throwError "PS0_DATA_MIXED_ORIGIN_MODIFIERS_OR_KEYWORD"
    for group in commaGroups before do
      groups := groups + 1
      for parameter in group[1].getSepArgs do
        let some binder := nativeBinder? after parameter
          | throwError "PS0_DATA_MIXED_ORIGIN_PARAMETER"
        unless binder.getRange? == parameter.getRange? &&
            binder[1][0].eqWithInfo parameter[0] && binder[2][0].eqWithInfo parameter[1] &&
            binder[2][1].getRange? == parameter[2].getRange? do
          throwError "PS0_DATA_MIXED_ORIGIN_NAME_COLON_TYPE"
        if !parameter[3].getArgs.isEmpty then
          unless binder[3][0][0].eqWithInfo parameter[3][0][0] &&
              binder[3][0][1].getRange? == parameter[3][0][1].getRange? do
            throwError "PS0_DATA_MIXED_ORIGIN_DEFAULT"
        parameters := parameters + 1
  unless groups == 4 && parameters == 8 do
    throwError "PS0_DATA_MIXED_ORIGIN_COUNTS"
  logInfo "PS0_DATA_MIXED_ORIGINS: PASS 3 cases / 4 groups / 8 parameters"
