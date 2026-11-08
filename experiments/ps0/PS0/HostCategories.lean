module
public meta import Lean

public meta section

/-! PS-owned category adapters; independently owned native and DSL syntax stays opaque. -/

open Lean

declare_syntax_cat psTerm
declare_syntax_cat psCommand
declare_syntax_cat psTactic
declare_syntax_cat psDoSeq
declare_syntax_cat psCallArg
declare_syntax_cat psHead
declare_syntax_cat psDoElem
declare_syntax_cat psDoItem

syntax (name := ps0NativeTermBridge) (priority := low) term : psTerm
syntax (name := ps0NativeCommandBridge) command : psCommand
syntax (name := ps0NativeTacticBridge) (priority := low) tactic : psTactic
syntax (name := ps0NativeDoBridge) (priority := low) doSeq : psDoSeq
syntax (name := ps0NativeDoElemBridge) (priority := low) doElem : psDoElem
syntax (name := ps0PositionalArg) psTerm : psCallArg
syntax (name := ps0NamedArg) ident " := " psTerm : psCallArg

syntax:max (name := ps0HostAdjacentCall) (priority := high)
  ident noWs "(" sepBy1(psCallArg, ",", "," ppSpace, allowTrailingSep) ")" : psTerm

syntax:max (name := ps0NativeHeadBridge) (priority := low) term:max : psHead
syntax:max (name := ps0ParenthesizedHead) "(" psTerm ")" : psHead
syntax:max (name := ps0HeadCall) psHead:max noWs
  "(" sepBy1(psCallArg, ",", "," ppSpace, allowTrailingSep) ")" : psHead
syntax:max (name := ps0HeadEmptyCall) psHead:max noWs "(" ")" : psHead
syntax (name := ps0HostHeadTerm) psHead : psTerm
syntax:max (name := ps0HostParens) (priority := high) "(" psTerm ")" : psTerm
syntax:max (name := ps0HostBraces) (priority := high) "{" psTerm "}" : psTerm
syntax (name := ps0HostIf) (priority := high) "if " psTerm " then " psTerm " else " psTerm : psTerm
syntax (name := ps0HostExact) (priority := high) "exact " psTerm : psTactic
syntax (name := ps0HostApply) (priority := high) "apply " psTerm : psTactic
syntax (name := ps0HostRefine) (priority := high) "refine " psTerm : psTactic
syntax (name := ps0HostBy) (priority := high)
  "by " "{" sepBy1(psTactic, ";", ";" ppSpace, allowTrailingSep) "}" : psTerm
syntax (name := ps0HostDoLet) (priority := high)
  "let " ident (":" psTerm)? ":=" psTerm : psDoElem
syntax (name := ps0HostDoBind) (priority := high)
  "let " ident "←" psTerm : psDoElem
syntax (name := ps0HostDoReturn) (priority := high) "return " psTerm : psDoElem
syntax (name := ps0HostDoExpr) (priority := high) psTerm : psDoElem
syntax (name := ps0HostDoItem) ppLine psDoElem ";"? : psDoItem
syntax (name := ps0HostDoSeq) (priority := high) "{" psDoItem+ ppLine "}" : psDoSeq
syntax (name := ps0HostDo) (priority := high) "do " psDoSeq : psTerm

namespace PS0.Syntax

private def loweringInfo (source : Lean.Syntax) : SourceInfo :=
  match source.getRange? with
  | some span => .synthetic span.start span.stop false
  | none => .none

private def rejectHostGap (source : Lean.Syntax) : MacroM Unit := do
  if let .node (.synthetic ..) _ _ := source then return ()
  if source.isOfKind ``Lean.Parser.Term.app then
    for arg in source[1].getArgs do
      if arg.isOfKind ``Lean.Parser.Term.paren || arg.isOfKind ``Lean.Parser.Term.tuple then
        if let some start := arg.getPos? then
          if let some stop := source[0].getTailPos? then
            if stop < start then
              withRef arg do Macro.throwError "PS0V1-CALL-GAP: parenthesized host arguments require adjacency"

mutual
partial def lower (category : Name) (source : Lean.Syntax) :
    MacroM Lean.Syntax := withRef source do
  if source.isOfKind choiceKind then
    Macro.throwError "PS0V1-HOST-AMBIGUITY: resolve host syntax before lowering"
  if category == `psTerm then
    if source.isOfKind ``ps0NativeTermBridge then
      let native := source[0]
      rejectHostGap native
      return native
    match source with
    | `(psTerm| $head:ident($[$args:psCallArg],*)) => lowerCall head.raw args source
    | `(psTerm| $head:psHead) => lowerHead head.raw
    | `(psTerm| ($body:psTerm)) => do
        let body : TSyntax `term := ⟨← lower `psTerm body.raw⟩
        return (← `(($body))).raw
    | `(psTerm| { $body:psTerm }) => do
        let body : TSyntax `term := ⟨← lower `psTerm body.raw⟩
        return (← `(($body))).raw
    | `(psTerm| if $cond:psTerm then $yes:psTerm else $no:psTerm) => do
        let cond : TSyntax `term := ⟨← lower `psTerm cond.raw⟩
        let yes : TSyntax `term := ⟨← lower `psTerm yes.raw⟩
        let no : TSyntax `term := ⟨← lower `psTerm no.raw⟩
        return (← `(if $cond then $yes else $no)).raw
    | `(psTerm| by { $[$items:psTactic];* }) => do
        let items ← items.mapM fun item => do
          return (⟨← lower `psTactic item.raw⟩ : TSyntax `tactic)
        return (← `(by { $[$items:tactic];* })).raw
    | `(psTerm| do $seq:psDoSeq) => do
        let seq : TSyntax ``Lean.Parser.Term.doSeq := ⟨← lower `psDoSeq seq.raw⟩
        return (← `(do $seq:doSeq)).raw
    | _ => Macro.throwError "PS0V1-HOST-LOWER: unsupported psTerm"
  else if category == `psCommand then
    match source with
    | `(psCommand| $native:command) => return native.raw
    | _ => Macro.throwError "PS0V1-HOST-LOWER: unsupported psCommand"
  else if category == `psTactic then
    match source with
    | `(psTactic| exact $body:psTerm) => do
        let body : TSyntax `term := ⟨← lower `psTerm body.raw⟩
        return (← `(tactic| exact $body)).raw
    | `(psTactic| apply $body:psTerm) => do
        let body : TSyntax `term := ⟨← lower `psTerm body.raw⟩
        return (← `(tactic| apply $body)).raw
    | `(psTactic| refine $body:psTerm) => do
        let body : TSyntax `term := ⟨← lower `psTerm body.raw⟩
        return (← `(tactic| refine $body)).raw
    | `(psTactic| $native:tactic) => return native.raw
    | _ => Macro.throwError "PS0V1-HOST-LOWER: unsupported psTactic"
  else if category == `psDoSeq then
    match source with
    | `(psDoSeq| { $items:psDoItem* }) => do
        let mut nativeItems := #[]
        for item in items do
          let native ← lowerDoElem item.raw[0]
          nativeItems := nativeItems.push <| .node (loweringInfo item.raw)
            ``Lean.Parser.Term.doSeqItem #[native, item.raw[1]]
        return .node (loweringInfo source) ``Lean.Parser.Term.doSeqBracketed
          #[source[0], mkNullNode nativeItems, source[2]]
    | `(psDoSeq| $native:doSeq) => return native.raw
    | _ => Macro.throwError "PS0V1-HOST-LOWER: unsupported psDoSeq"
  else Macro.throwError s!"PS0V1-HOST-LOWER: unrecognized PS category {category}"

partial def lowerDoElem (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  match source with
  | `(psDoElem| let $name:ident $[: $ty:psTerm]? := $value:psTerm) => do
      let ty ← ty.mapM fun t => do return (⟨← lower `psTerm t.raw⟩ : TSyntax `term)
      let value : TSyntax `term := ⟨← lower `psTerm value.raw⟩
      return (← `(doElem| let $name:ident $[: $ty:term]? := $value)).raw
  | `(psDoElem| let $name:ident ← $value:psTerm) => do
      let value : TSyntax `term := ⟨← lower `psTerm value.raw⟩
      let action : TSyntax `doElem := ⟨.node (loweringInfo source)
        ``Lean.Parser.Term.doExpr #[value.raw]⟩
      return (← `(doElem| let $name:ident ← $action:doElem)).raw
  | `(psDoElem| return $value:psTerm) => do
      let value : TSyntax `term := ⟨← lower `psTerm value.raw⟩
      return (← `(doElem| return $value)).raw
  | `(psDoElem| $value:psTerm) => do
      let value : TSyntax `term := ⟨← lower `psTerm value.raw⟩
      return (← `(doElem| $value:term)).raw
  | `(psDoElem| $native:doElem) => return native.raw
  | _ => Macro.throwError "PS0V1-HOST-LOWER: unsupported psDoElem"

partial def lowerHead (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  match source with
  | `(psHead| $head:psHead($[$args:psCallArg],*)) =>
      lowerCall (← lowerHead head.raw) args source
  | `(psHead| $head:psHead()) =>
      return .node (loweringInfo source) `PS0.pscvEmptyCall
        #[← lowerHead head.raw, mkAtom "(", mkAtom ")"]
  | `(psHead| ($body:psTerm)) => do
      let body : TSyntax `term := ⟨← lower `psTerm body.raw⟩
      return (← `(($body))).raw
  | `(psHead| $native:term) => return native.raw
  | _ => Macro.throwError "PS0V1-HOST-LOWER: unsupported postfix head"

partial def lowerCall (head : Lean.Syntax) (args : Array (TSyntax `psCallArg))
    (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  let mut positional := true
  let mut seen : Array Name := #[]
  let mut nativeArgs : Array Lean.Syntax := #[]
  for arg in args do
    match arg with
    | `(psCallArg| $name:ident := $value:psTerm) =>
        let n := name.getId
        if seen.contains n then
          withRef name do Macro.throwError s!"PS0V1-CALL-NAMED: duplicate named argument {n}"
        positional := false
        seen := seen.push n
        let value : TSyntax `term := ⟨← lower `psTerm value.raw⟩
        nativeArgs := nativeArgs.push (← `(Lean.Parser.Term.namedArgument| ($name := $value))).raw
    | `(psCallArg| $value:psTerm) =>
        unless positional do
          withRef arg do Macro.throwError "PS0V1-CALL-ORDER: positional argument after named argument"
        nativeArgs := nativeArgs.push (← lower `psTerm value.raw)
    | _ => Macro.throwError "PS0V1-HOST-LOWER: malformed psCallArg"
  return .node (loweringInfo source) ``Lean.Parser.Term.app #[head, mkNullNode nativeArgs]
end
end PS0.Syntax
