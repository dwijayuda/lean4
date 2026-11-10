import Lean
import PS0.HostCategories

/-! Inspect PS category ownership beneath a native do-bind followed by an indented if. -/

open Lean

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
  for (label, text) in [
      ("bound-if", "do\n  let result ← if b then\n    pure <| add(1, 2)\n  else\n    addM(3, 4)\n  return result"),
      ("standalone-if", "do\n  if b then\n    pure <| add(1, 2)\n  else\n    addM(3, 4)") ] do
    let parsed ← IO.ofExcept <| Parser.runParserCategory env `psTerm text
    let lowered ← Elab.liftMacroM <| PS0.Syntax.lower `psTerm parsed
    logInfo ("PS0_BOUND_IF_ROLE_PATHS:" ++ (Json.mkObj [
      ("case", toJson label), ("parsed", toJson (roleNodes parsed)),
      ("lowered", toJson (roleNodes lowered))]).compress)
