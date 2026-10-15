import Lean

/-!
PS0 v1 `0B: concrete host-category extension interfaces.

These four bridge rules are an INITIAL native-subcategory foundation only:
they preserve native Syntax nodes, source references and quotation payloads.
A true PS-host operand adapter must additionally own PS postfix calls,
record/body distinction and category-specific lowering before the claim
of complete PS0 v1 conformance. Never recursively transform independently
owned DSL/quotation payloads here.
-/

open Lean

declare_syntax_cat psTerm
declare_syntax_cat psCommand
declare_syntax_cat psTactic
declare_syntax_cat psDoSeq

syntax (name := ps0NativeTermBridge) term : psTerm
syntax (name := ps0NativeCommandBridge) command : psCommand
syntax (name := ps0NativeTacticBridge) tactic : psTactic
syntax (name := ps0NativeDoBridge) doSeq : psDoSeq

/-!
PS0V1-APP-01: the first host-owned postfix production. The high-priority
native/extension head categories and broader standard operand-slot registry
are separate work. The syntax captures comma-separated host arguments as
syntax data and checks source adjacency via Lean's native noWs token parser.
-/
declare_syntax_cat psCallArg
syntax (name := ps0PositionalArg) psTerm : psCallArg
syntax (name := ps0NamedArg) ident " := " psTerm : psCallArg

-- Deliberately limit this initial bridge to an identifier head. A native
-- projection/indexed/explicit-universe postfix needs the full head adapter.
syntax:max (name := ps0HostAdjacentCall)
  ident noWs "(" psCallArg,+ ")" : psTerm

namespace PS0.Syntax

/-- Explicit PS host-category → native-syntax bridge. No source-text
    reparsing, name lookup, type inference, or tactic/proof execution occurs.
    For an ordinary native capture the original tree is preserved exactly.
    For the owned adjacent call, each host argument is lowered in order and
    assembled into Lean's native application node. Quoted native syntax,
    extension-owned categories, and patterns are opaque to this function.
    Missing/malformed source category nodes fail closed. -/
partial def lower (category : Name) (source : Lean.Syntax) :
    Lean.MacroM Lean.Syntax := do
  if category == `psTerm then
    match source with
    | `(psTerm| $head:ident($[$args:psCallArg],*)) => do
        let mut positional := true
        let mut seen : Array Name := #[]
        let mut nativeArgs : Array Lean.Syntax := #[]
        for arg in args do
          match arg with
          | `(psCallArg| $name:ident := $value:psTerm) =>
              let n := name.getId
              if seen.contains n then
                throwError "PS0V1-CALL-NAMED: duplicate named argument {n}"
              positional := false
              seen := seen.push n
              let lowered ← lower `psTerm value.raw
              let term : TSyntax `term := ⟨lowered⟩
              let named ← `(Lean.Parser.Term.namedArgument| ($name:ident := $term:term))
              nativeArgs := nativeArgs.push named.raw
          | `(psCallArg| $value:psTerm) =>
              unless positional do
                throwError "PS0V1-CALL-ORDER: positional argument after named argument"
              nativeArgs := nativeArgs.push (← lower `psTerm value.raw)
          | _ =>
              throwError "PS0V1-HOST-LOWER: malformed psCallArg"
        return mkNode ``Lean.Parser.Term.app
          #[head.raw, mkNullNode nativeArgs]
    | `(psTerm| $native:term) => return native.raw
    | _ => throwError "PS0V1-HOST-LOWER: unsupported psTerm source production"
  else if category == `psCommand then
    match source with
    | `(psCommand| $native:command) => return native.raw
    | _ => throwError "PS0V1-HOST-LOWER: unsupported psCommand source production"
  else if category == `psTactic then
    match source with
    | `(psTactic| $native:tactic) => return native.raw
    | _ => throwError "PS0V1-HOST-LOWER: unsupported psTactic source production"
  else if category == `psDoSeq then
    match source with
    | `(psDoSeq| $native:doSeq) => return native.raw
    | _ => throwError "PS0V1-HOST-LOWER: unsupported psDoSeq source production"
  else
    throwError "PS0V1-HOST-LOWER: unrecognized PS category {category}"

end PS0.Syntax
