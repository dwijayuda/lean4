import Lean
/-! Inspect pinned imported parser descriptors; this is metadata inspection, not qualification. -/
open Lean

private partial def view : ParserDescr → Json
  | .const n => toJson #[toJson "const", toJson n.toString]
  | .parser n => toJson #[toJson "parser", toJson n.toString]
  | .cat n p => toJson #[toJson "cat", toJson n.toString, toJson p]
  | .symbol s => toJson #[toJson "symbol", toJson s]
  | .nonReservedSymbol s b => toJson #[toJson "nonReserved", toJson s, toJson b]
  | .unicodeSymbol s a b => toJson #[toJson "unicode", toJson s, toJson a, toJson b]
  | .unary n p => toJson #[toJson "unary", toJson n.toString, view p]
  | .binary n p q => toJson #[toJson "binary", toJson n.toString, view p, view q]
  | .node n p q => toJson #[toJson "node", toJson n.toString, toJson p, view q]
  | .trailingNode n p l q => toJson #[toJson "trailing", toJson n.toString, toJson p, toJson l, view q]
  | .nodeWithAntiquot s n p => toJson #[toJson "antiquot", toJson s, toJson n.toString, view p]
  | .sepBy p s q b => toJson #[toJson "sepBy", view p, toJson s, view q, toJson b]
  | .sepBy1 p s q b => toJson #[toJson "sepBy1", view p, toJson s, view q, toJson b]

unsafe def main : IO Unit := do
  initSearchPath (← findSysroot)
  let env ← importModules #[{module := `Lean, isMeta := true}] {} (leakEnv := true) (loadExts := true)
  let some category := Lean.Parser.getParserCategory? env `term | throw (IO.userError "missing term")
  let names := category.kinds.foldl (fun names name _ => names.push name) (#[] : Array Name)
  let mut rows := #[]
  for name in names do
    if let some info := env.find? name then
      if info.type.getAppFn.isConstOf ``TrailingParserDescr then
        if let .ok descr := env.evalConst TrailingParserDescr {} name then
          rows := rows.push <| Json.mkObj [("declaration",toJson name.toString),("descriptor",view descr)]
  IO.println (Json.mkObj [("lean_commit",toJson Lean.githash),("operators",toJson rows)]).compress
