import Lean
import PS0.Backend.Js.IR

/-!
Source Map v3, real Base64-VLQ segments. Every generated JS runtime declaration
is anchored to its original .ps declaration start. Coarse statement-level
mappings are truthful; fine-grained expression spans can be carried through
Origin in future typed IR. No external JS source-map package or .mjs generator.
-/

namespace PS0.Backend.Js

private def base64 : Array Char :=
  ("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/").toList.toArray

private partial def vlqUnsigned (n : Nat) : String :=
  let remainder := n / 32
  let digit := (n % 32) + (if remainder == 0 then 0 else 32)
  let head := String.singleton (base64[digit]!)
  if remainder == 0 then head else head ++ vlqUnsigned remainder

private def vlq (n : Int) : String :=
  vlqUnsigned (if n < 0 then n.natAbs * 2 + 1 else n.toNat * 2)

/-- Four source-map fields: generated column, source index, original
line delta and original column delta. All generated segments start at
column zero on their generated line. -/
private def encodeMapping (prevLine prevColumn : Nat) (span : Origin) : String :=
  vlq 0 ++ vlq 0 ++
  vlq (Int.ofNat span.line - Int.ofNat prevLine) ++
  vlq (Int.ofNat span.column - Int.ofNat prevColumn)

def sourceMap (program : Program) (jsFile : String)
    (origins : Array (Option Origin)) : String := Id.run do
  let mut prevLine : Nat := 0
  let mut prevColumn : Nat := 0
  let mut rows : Array String := #[]
  for origin in origins do
    match origin with
    | none => rows := rows.push ""
    | some loc =>
        rows := rows.push (encodeMapping prevLine prevColumn loc)
        prevLine := loc.line
        prevColumn := loc.column
  let result := Lean.Json.mkObj [
    ("version", Lean.toJson (3 : Nat)),
    ("file", Lean.toJson jsFile),
    ("sources", Lean.toJson #[program.sourceName]),
    ("sourcesContent", Lean.toJson #[program.sourceText]),
    ("names", Lean.toJson (#[] : Array String)),
    ("mappings", Lean.toJson (String.intercalate ";" rows.toList))
  ]
  return result.compress

end PS0.Backend.Js
