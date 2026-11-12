import Lean
import PS0.HostCategories

/-! Inspect PS category ownership beneath a native do-bind followed by an indented if. -/

open Lean
open Lean.Parser

private partial def escapedIf (source : Syntax) : Bool :=
  (source.isOfKind ``ps0NativeDoElemBridge && source[0].isOfKind ``Lean.Parser.Term.doIf) ||
    source.getArgs.any escapedIf

private partial def adjacentCalls (source : Syntax) : Nat :=
  (if source.isOfKind ``ps0HostAdjacentCall then 1 else 0) +
    source.getArgs.foldl (fun count child => count + adjacentCalls child) 0

private partial def roleNodes (source : Syntax) (path : Array String := #[]) : Array Json := Id.run do
  let kind := source.getKind.toString
  let path := path.push kind
  let selected := kind.startsWith "ps0" ||
    #["Lean.Parser.Term.doIf", "Lean.Parser.Term.doLetArrow", "Lean.Parser.Term.doExpr",
      "Lean.Parser.Term.app", "PS0.Operators.ownedBinary"].contains kind
  let rows := if selected then #[Json.mkObj [
    ("kind", toJson kind), ("path", toJson path),
    ("children", toJson (source.getArgs.map fun child => child.getKind.toString))]] else #[]
  return source.getArgs.foldl (fun rows child => rows ++ roleNodes child path) rows

run_cmd do
  let env ← getEnv
  let some category := getParserCategory? env `psDoElem
    | throwError "missing psDoElem category"
  let keep := fun (entry : Parser × Nat) =>
    !(entry.1.info.collectKinds {}).contains ``ps0NativeDoElemBridge
  let mut leadingTable : TokenMap (Parser × Nat) := {}
  for (token, parsers) in category.tables.leadingTable do
    for entry in (parsers.filter keep).reverse do
      leadingTable := leadingTable.insert token entry
  let tables := {category.tables with
    leadingTable, leadingParsers := category.tables.leadingParsers.filter keep}
  let owned := leadingParser `psDoElem tables category.behavior
    (mkCategoryAntiquotParser `psDoElem).fn
  let native := categoryParserFnExtension.getState env
  let dispatch : CategoryParserFn := fun category =>
    if category == `psDoElem then owned else native category
  let strict := categoryParserFnExtension.setState env dispatch
  for (label, text) in [
      ("bound-if", "do\n  let result ← if b then\n    pure <| add(1, 2)\n  else\n    addM(3, 4)\n  return result"),
      ("standalone-if", "do\n  if b then\n    pure <| add(1, 2)\n  else\n    addM(3, 4)") ] do
    let parsed ← IO.ofExcept <| Parser.runParserCategory env `psTerm text
    match Parser.runParserCategory strict `psTerm text with
    | .ok _ => logInfo s!"PS0_BOUND_IF_WITHOUT_FALLBACK:{label}:PASS"
    | .error error => logInfo s!"PS0_BOUND_IF_WITHOUT_FALLBACK:{label}:{error}"
    unless !escapedIf parsed && adjacentCalls parsed == 2 do
      throwError s!"PS0_BOUND_IF_OWNERSHIP: {label}: escaped={escapedIf parsed}, calls={adjacentCalls parsed}"
    let lowered ← Elab.liftMacroM <| PS0.Syntax.lower `psTerm parsed
    logInfo ("PS0_BOUND_IF_ROLE_PATHS:" ++ (Json.mkObj [
      ("case", toJson label), ("parsed", toJson (roleNodes parsed)),
      ("lowered", toJson (roleNodes lowered))]).compress)
