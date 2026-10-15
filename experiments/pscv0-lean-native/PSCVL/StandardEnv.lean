import Lean

/-!
A compile-time, frozen module selection for the Lean 4.35.0 PSCV0 frontend.
This is not the full semantic environment digest or a trusted plugin registry.
-/

open Lean

namespace PSCVL.StandardEnv

def leanRevision : String := "eb6cafb7290e8bd5f2937522d8d804f58f02bafc"
def leanVersion : String := "4.35.0"

def imports : List Lean.Name := [
  `Std, `Init.Data.List, `Init.Data.Array,
  `Std.Data.HashMap, `Std.Data.HashSet,
  `Std.Data.TreeMap, `Std.Data.TreeSet,
  `Std.Data.String, `Std.Data.Iterators
]

def derivingHandlers : List String :=
  ["Repr", "BEq", "DecidableEq", "Inhabited", "Hashable"]

def evalScalarTypes : List String :=
  ["Nat", "Int", "Bool", "String", "Char", "Unit"]

def allowsImport (modName : Lean.Name) : Bool := imports.contains modName

def manifest : Lean.Json := Lean.Json.mkObj [
  ("schema", toJson ("pscv0-standard-env/1" : String)),
  ("status", toJson ("provisional-module-allowlist-not-complete-semantic-snapshot" : String)),
  ("lean_commit", toJson leanRevision),
  ("lean_version", toJson leanVersion),
  ("allowed_imports", toJson (imports.map Name.toString)),
  ("deriving_handlers", toJson derivingHandlers),
  ("eval_scalar_types", toJson evalScalarTypes)
]

end PSCVL.StandardEnv
