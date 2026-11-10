import Lean

/-! Inspect native module constants while reporting generated bound-name differences separately. -/

open Lean

private partial def anonymousBinders : Expr → Expr
  | .forallE _ type body info => .forallE .anonymous (anonymousBinders type) (anonymousBinders body) info
  | .lam _ type body info => .lam .anonymous (anonymousBinders type) (anonymousBinders body) info
  | .letE _ type value body nondep =>
    .letE .anonymous (anonymousBinders type) (anonymousBinders value) (anonymousBinders body) nondep
  | .app fn arg => .app (anonymousBinders fn) (anonymousBinders arg)
  | .mdata metadata body => .mdata metadata (anonymousBinders body)
  | .proj name index body => .proj name index (anonymousBinders body)
  | other => other

private def constantKind : ConstantInfo → Nat
  | .axiomInfo _ => 0
  | .defnInfo _ => 1
  | .thmInfo _ => 2
  | .opaqueInfo _ => 3
  | .quotInfo _ => 4
  | .inductInfo _ => 5
  | .ctorInfo _ => 6
  | .recInfo _ => 7

private def summary (data : ModuleData) : Json := Json.mkObj [
  ("isModule", toJson data.isModule),
  ("imports", toJson data.imports),
  ("constantNames", toJson (data.constNames.map Name.toString)),
  ("extraConstNames", toJson (data.extraConstNames.map Name.toString)),
  ("extensions", toJson (data.entries.map fun (name, entries) =>
    Json.mkObj [("name", toJson name.toString), ("count", toJson entries.size)]))]

private unsafe def loadParts (file : String) (allParts : Bool) : IO ModuleData := do
  let parts ← if allParts then
      readModuleDataParts #[file, OLeanLevel.server.adjustFileName file,
        OLeanLevel.private.adjustFileName file]
    else do pure #[← readModuleData file]
  let some (first, _) := parts[0]? | throw (IO.userError "module parts are empty")
  let mut result := first
  for (_, region) in parts do
    let _ ← Runtime.markPersistent region
  if allParts then
    -- Later parts replace public/server stubs with the private constant body.
    -- Comparing concatenated arrays would compare a body with an earlier stub.
    let mut constants : Array ConstantInfo := #[]
    for (part, _) in parts.reverse do
      for constant in part.constants do
        unless constants.any (fun previous => previous.name == constant.name) do
          constants := constants.push constant
    result := { result with
      constants
      constNames := constants.map (·.name)
      extraConstNames := parts.foldl (fun acc part => acc ++ part.1.extraConstNames) #[] }
  return result

unsafe def main (args : List String) : IO Unit := do
  let (baseline, converted, allParts) ← match args with
    | [a, b] => pure (a, b, false)
    | [a, b, "--all-parts"] => pure (a, b, true)
    | _ => throw (IO.userError "expected two public olean files and optional --all-parts")
  let native ← loadParts baseline allParts
  let ps ← loadParts converted allParts
  let mut changes := #[]
  for a in native.constants do
    let some b := ps.constants.find? (fun c => c.name == a.name) | continue
    unless a == b && reprStr a.type == reprStr b.type &&
        reprStr (a.value? true) == reprStr (b.value? true) do
      let mut fields := [
        ("name", toJson a.name.toString),
        ("kindEqual", toJson (constantKind a == constantKind b)),
        ("typeEqual", toJson (a.type == b.type)),
        ("valueEqual", toJson (a.value? true == b.value? true)),
        ("typeReprEqualIgnoringBinderNames", toJson (reprStr (anonymousBinders a.type) == reprStr (anonymousBinders b.type))),
        ("valueReprEqualIgnoringBinderNames", toJson (reprStr ((a.value? true).map anonymousBinders) == reprStr ((b.value? true).map anonymousBinders))),
        ("nativeLevels", toJson (a.levelParams.map Name.toString)),
        ("psLevels", toJson (b.levelParams.map Name.toString))]
      if reprStr a.type != reprStr b.type then
        fields := fields ++ [("nativeType", toJson (reprStr a.type)), ("psType", toJson (reprStr b.type))]
      if reprStr (a.value? true) != reprStr (b.value? true) then
        fields := fields ++ [("nativeValue", toJson (reprStr (a.value? true))), ("psValue", toJson (reprStr (b.value? true)))]
      if let .defnInfo x := a then
        if let .defnInfo y := b then
          fields := fields ++ [("hintsEqual", toJson (x.hints == y.hints)),
            ("nativeMutual", toJson (x.all.map Name.toString)), ("psMutual", toJson (y.all.map Name.toString))]
      changes := changes.push (Json.mkObj fields)
  IO.println (Json.mkObj [("native", summary native), ("ps", summary ps),
    ("changedConstants", toJson changes)]).pretty
