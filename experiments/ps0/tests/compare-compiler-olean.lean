import Lean

open Lean

private def summary (data : ModuleData) : Json := Json.mkObj [
  ("isModule", toJson data.isModule),
  ("imports", toJson data.imports),
  ("constantNames", toJson (data.constNames.map Name.toString)),
  ("extraConstNames", toJson (data.extraConstNames.map Name.toString)),
  ("extensions", toJson (data.entries.map fun (name, entries) =>
    Json.mkObj [("name", toJson name.toString), ("count", toJson entries.size)]))]

unsafe def main (args : List String) : IO Unit := do
  let [baseline, converted] := args | throw (IO.userError "expected two public olean files")
  let (native, nativeRegion) ← readModuleData baseline
  let (ps, psRegion) ← readModuleData converted
  let _ ← Runtime.markPersistent nativeRegion
  let _ ← Runtime.markPersistent psRegion
  let mut changes := #[]
  for a in native.constants do
    let some b := ps.constants.find? (fun c => c.name == a.name) | continue
    unless a == b do
      let mut fields := [
        ("name", toJson a.name.toString),
        ("typeEqual", toJson (a.type == b.type)),
        ("valueEqual", toJson (a.value? true == b.value? true)),
        ("nativeLevels", toJson (a.levelParams.map Name.toString)),
        ("psLevels", toJson (b.levelParams.map Name.toString))]
      if a.type != b.type then
        fields := fields ++ [("nativeType", toJson (reprStr a.type)), ("psType", toJson (reprStr b.type))]
      if a.value? true != b.value? true then
        fields := fields ++ [("nativeValue", toJson (reprStr (a.value? true))), ("psValue", toJson (reprStr (b.value? true)))]
      if let .defnInfo x := a then
        if let .defnInfo y := b then
          fields := fields ++ [("hintsEqual", toJson (x.hints == y.hints)),
            ("nativeMutual", toJson (x.all.map Name.toString)), ("psMutual", toJson (y.all.map Name.toString))]
      changes := changes.push (Json.mkObj fields)
  IO.println (Json.mkObj [("native", summary native), ("ps", summary ps),
    ("changedConstants", toJson changes)]).pretty
