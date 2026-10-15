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

namespace PS0.Syntax

/-- Explicit bridge from a supported native-capture host category into its
    underlying native syntax. This does not elaborate the source or synthesize
    arguments; it preserves the original input subtree and scope references.

    Host-specific call nodes must use their semantic elaborator before they
    become native executable terms. Until that adapter is complete, this
    function rejects unsupported raw PS nodes rather than repairing them
    or reparsing their printed text. -/
def lower (category : Name) (source : Lean.Syntax) :
    Lean.MacroM Lean.Syntax := do
  if category == `psTerm then
    match source with
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
