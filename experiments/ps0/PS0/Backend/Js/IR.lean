import Lean

/-!
Portable JS backend IR: backend-neutral concepts (typed Nat expressions,
public bindings, source origins) are separate from JavaScript syntax.
The MVP only claims a selected Nat fragment; unknown constructs must fail
during lowering. Expand the IR with typed products/ADTs/closures later,
rather than adding source-text substitutions to the emitter.
-/

namespace PS0.Backend.Js

inductive NatExpr where
  | literal (value : Nat)
  | local (name : String)
  | add (lhs rhs : NatExpr)
  | mul (lhs rhs : NatExpr)
  | sub (lhs rhs : NatExpr)
  deriving Repr, Inhabited

structure Origin where
  /-- Zero-based source position in the exact original .ps bytes. -/
  line : Nat
  column : Nat
  deriving Repr, Inhabited

structure Decl where
  name : String
  params : Array String := #[]
  body : NatExpr
  isConst : Bool
  origin : Origin
  deriving Repr, Inhabited

structure Program where
  sourceName : String
  sourceText : String
  declarations : Array Decl
  deriving Repr, Inhabited

/-- Identifiers must have a stable, injective JS/TS export spelling.
    Unicode/qualified namespaces are intentionally pending a name-mangler. -/
def safePublicName (name : String) : Bool := Id.run do
  if name.isEmpty then return false
  let chars := name.toList
  let start c := (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_'
  let follow c := start c || (c >= '0' && c <= '9')
  if !start chars.head! || !chars.all follow then return false
  let reserved := [
    "await", "break", "case", "catch", "class", "const", "continue",
    "debugger", "default", "delete", "do", "else", "enum", "export",
    "extends", "false", "finally", "for", "function", "if", "import",
    "in", "instanceof", "new", "null", "return", "super", "switch",
    "this", "throw", "true", "try", "typeof", "var", "void", "while",
    "with", "yield", "let", "static", "implements", "interface",
    "package", "private", "protected", "public", "arguments", "eval"
  ]
  return !reserved.contains name

end PS0.Backend.Js
