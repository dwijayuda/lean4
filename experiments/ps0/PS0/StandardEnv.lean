import Lean

/-!
PS0 v1 environment identity metadata. Language availability is determined
by the exact Lean 4.35.0 imports, registered syntax, attributes,
tactics, deriving handlers and actual native module scopes.

This module does NOT define a finite language-level Standard whitelist,
a mandatory axiom approval policy or a replacement Lean elaborator.
A complete dependency/registration digest is future conformance work.
-/

open Lean

namespace PS0.StandardEnv

def leanRevision : String := "eb6cafb7290e8bd5f2937522d8d804f58f02bafc"
def leanVersion : String := "4.35.0"

def manifest : Lean.Json := Lean.Json.mkObj [
  ("schema", toJson ("ps0-v1-environment/1" : String)),
  ("edition", toJson ("PS0 v1 R2" : String)),
  ("status", toJson ("import-driven-registration-closure-not-fully-digested" : String)),
  ("lean_commit", toJson leanRevision),
  ("lean_version", toJson leanVersion),
  ("language_reference", toJson ("PS0_V1_LANGUAGE_REFERENCE.md" : String))
]

end PS0.StandardEnv
