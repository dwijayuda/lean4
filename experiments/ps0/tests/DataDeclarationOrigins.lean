import PS0.StandardAdapters

/-! Preserve native data roots, modifiers, binder grouping, constructor patterns and tokens. -/

open Lean
open scoped PS0.StandardAdapters

private partial def checkNativeRoles (before after : Syntax) : Elab.Command.CommandElabM Unit := do
  if before.isOfKind `PS0.StandardAdapters.psDataNativeBinder then
    return ← checkNativeRoles before[0] after
  if before.isOfKind choiceKind then
    if let some native := before.getArgs.find?(·.isOfKind `PS0.StandardAdapters.psDataNativeBinder) then
      return ← checkNativeRoles native[0] after
  if before.isOfKind `PS0.StandardAdapters.psDataTerm ||
      before.isOfKind `PS0.StandardAdapters.psDataTactic then return
  unless before.getKind == after.getKind && before.getRange? == after.getRange? &&
      before.getArgs.size == after.getArgs.size do
    throwError "PS0_DATA_ORIGIN_NATIVE_NODE: {before.getKind}"
  if before.getArgs.isEmpty then
    unless before.eqWithInfo after do throwError "PS0_DATA_ORIGIN_NATIVE_LEAF"
  for (a, b) in before.getArgs.zip after.getArgs do checkNativeRoles a b

run_cmd do
  let cases := #[
    "structure OriginPacket (n : Nat := add(1, 2)) extends Parent(n) where\n  value : Fin(add(n, 1))\n  method (k : Nat := add(n, 2)) : Nat := add(k, n)",
    "class OriginClass (n : Nat) where\n  value : Fin(add(n, 1))",
    "inductive OriginTree where\n  | leaf (n : Fin(add(1, 2))) : OriginTree",
    "class inductive OriginClassInductive where\n  | mk (n : Fin(add(1, 2))) : OriginClassInductive",
    "coinductive OriginStream : Prop where\n  | step : OriginStream\nmonotonicity_by exact witness(n)"]
  for text in cases do
    let before ← match Parser.runParserCategory (← getEnv) `command text with
      | .ok source => pure source
      | .error message => throwError "{message}"
    unless before.isOfKind `PS0.StandardAdapters.ps0StandardData do
      throwError "PS0_DATA_ORIGIN_WRAPPER"
    let after ← Elab.liftMacroM <| PS0.StandardAdapters.lowerData before
    checkNativeRoles before[0] after
  logInfo "PS0_DATA_DECLARATION_ORIGINS: PASS 5"
