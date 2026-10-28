import Lean

/-!
PS0 v1 section 0B: explicit host-category interfaces.

This is a bounded host-category adapter, not full standard operand-slot
coverage. Independently owned native syntax, quotations and DSL operands
must remain opaque to this lowerer. No source text is printed or reparsed.
-/

open Lean

declare_syntax_cat psTerm
declare_syntax_cat psCommand
declare_syntax_cat psTactic
declare_syntax_cat psDoSeq

-- An owned host call must win over the native term bridge for the same
-- input span. Do not let a native application interpretation change the
-- host argument partition or hide the raw host node from an extension.
syntax (name := ps0NativeTermBridge) (priority := low) term : psTerm
syntax (name := ps0NativeCommandBridge) command : psCommand
syntax (name := ps0NativeTacticBridge) tactic : psTactic
syntax (name := ps0NativeDoBridge) doSeq : psDoSeq

declare_syntax_cat psCallArg
syntax (name := ps0PositionalArg) psTerm : psCallArg
syntax (name := ps0NamedArg) ident " := " psTerm : psCallArg

-- The third descriptor argument is the separator's formatting parser;
-- allowTrailingSep occupies the fourth slot in pinned Lean 4.35.0.
-- sepBy1 retains nonemptiness: a comma alone is not an empty invocation,
-- and a repeated comma cannot manufacture a missing operand.
-- Identifier heads only; other high-postfix heads remain a separate task.
syntax:max (name := ps0HostAdjacentCall) (priority := high)
  ident noWs "(" sepBy1(psCallArg, ",", ppSpace, allowTrailingSep) ")" : psTerm

namespace PS0.Syntax

/-- Generated native nodes retain the source extent for diagnostics, but
    are marked synthetic rather than pretending to be original native
    source. This is not an assertion of source-fidelity certification. -/
private def loweringInfo (source : Lean.Syntax) : SourceInfo :=
  match source.getRange? with
  | some span => .synthetic span.start span.stop false
  | none => .none

/-- Lower only explicitly owned PS nodes to native elaboration syntax.
    Native captures are returned unchanged, including their syntax info,
    scopes and pre-resolved identifiers. An unresolved parser choice is
    not permission to choose a more convenient native interpretation.
    Type inference, coercion and proof checking remain Lean's work. -/
partial def lower (category : Name) (source : Lean.Syntax) :
    Lean.MacroM Lean.Syntax := withRef source do
  if source.isOfKind choiceKind then
    throwError "PS0V1-HOST-AMBIGUITY: resolve the host syntax alternative before lowering"
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
                withRef name do
                  throwError "PS0V1-CALL-NAMED: duplicate named argument {n}"
              positional := false
              seen := seen.push n
              let lowered <- lower `psTerm value.raw
              let nativeTerm : TSyntax `term := ⟨lowered⟩
              let named <- withRef arg do
                `(Lean.Parser.Term.namedArgument| ($name:ident := $nativeTerm:term))
              nativeArgs := nativeArgs.push named.raw
          | `(psCallArg| $value:psTerm) =>
              unless positional do
                withRef arg do
                  throwError "PS0V1-CALL-ORDER: positional argument after named argument"
              nativeArgs := nativeArgs.push (← lower `psTerm value.raw)
          | _ =>
              throwError "PS0V1-HOST-LOWER: malformed psCallArg"
        return Lean.Syntax.node (loweringInfo source) ``Lean.Parser.Term.app
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
