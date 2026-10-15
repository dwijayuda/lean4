import Lean
import PS0.Grammar
import PS0.Backend.Js.IR

/-!
Selected PS0 v1 source AST -> typed portable runtime IR.
This is NOT regex/string transpilation and never runs without a successful
official Lean elaboration plus PS0 proof/assumption preflight in PS0Main.
For now accept only exact explicit Nat signatures and straight-line Nat
expressions. Reject all unsupported commands instead of guessing JS behavior.
No imports, namespaces, effects, implicit binders or runtime proofs yet.
-/

open Lean

namespace PS0.Backend.Js

private def isNatType (t : TSyntax `term) : Bool :=
  t.raw.isIdent && t.raw.getId == `Nat

private def checkedName (n : Ident) : Except String String := do
  let value := n.getId.toString
  unless safePublicName value do
    throw s!"PS0-JS-NAME: unsupported JS/TypeScript identifier {value}"
  return value

/-- The current module graph is intentionally acyclic and source-ordered.
    Only preceding declarations with exact Nat signatures can be referenced.
    Lean checks meaning first; this second check proves the JS IR has no
    unchecked forward imports, unknown globals, partial applications or
    recursive calls. -/
private def findPrevious (previous : Array Decl) (name : String) :
    Option Decl :=
  previous.toList.find? (fun d => d.name == name)

private partial def lowerExpr (locals : Array String)
    (previous : Array Decl) (e : TSyntax `term) :
    Except String NatExpr := do
  match e with
  | `(term| { $inner:term }) => lowerExpr locals previous inner
  | `(term| ($inner:term)) => lowerExpr locals previous inner
  | `(term| $n:num) => return .literal n.getNat
  | `(term| $fn:term()) =>
      unless fn.raw.isIdent do
        throw "PS0-JS-CALL: callable head must be a previous named function"
      let name := fn.raw.getId.toString
      let some decl := findPrevious previous name
        | throw s!"PS0-JS-CALL: unresolved or forward function {name}"
      if decl.isConst || !decl.params.isEmpty then
        throw s!"PS0-JS-CALL: {name} is not a nullary Nat function"
      return .call name #[]
  | `(term| $fn:term($[$args:pscvCallArg],*)) =>
      unless fn.raw.isIdent do
        throw "PS0-JS-CALL: callable head must be a previous named function"
      let name := fn.raw.getId.toString
      let some decl := findPrevious previous name
        | throw s!"PS0-JS-CALL: unresolved or forward function {name}"
      if decl.isConst || decl.params.size != args.size then
        throw s!"PS0-JS-CALL: {name} has incompatible Nat argument arity"
      let mut lowered : Array NatExpr := #[]
      for arg in args do
        match arg with
        | `(pscvCallArg| $v:term) =>
            lowered := lowered.push (← lowerExpr locals previous v)
        | _ =>
            throw "PS0-JS-CALL: named/defaulted arguments are not supported"
      return .call name lowered
  | `(term| $n:ident) =>
      let name := n.getId.toString
      if locals.contains name then return .local name
      if let some decl := findPrevious previous name then
        if decl.isConst then return .globalConst name
      throw s!"PS0-JS-EXPR: nonlocal value {name} is outside the Nat MVP"
  | `(term| $a:term + $b:term) =>
      return .add (← lowerExpr locals previous a)
        (← lowerExpr locals previous b)
  | `(term| $a:term * $b:term) =>
      return .mul (← lowerExpr locals previous a)
        (← lowerExpr locals previous b)
  | `(term| $a:term - $b:term) =>
      return .sub (← lowerExpr locals previous a)
        (← lowerExpr locals previous b)
  | _ =>
      throw s!"PS0-JS-EXPR: unsupported Nat expression syntax {e.raw.getKind}"

/-- The normal PS0 v1 typed function/const body is psTerm, not merely a
    native Lean term. The Nat backend has an explicit, closed IR contract:
    only native Nat expressions and exact-arity calls to earlier Nat functions
    are eligible. This does not rewrite or trust arbitrary PS syntax. -/
private partial def lowerHostExpr (locals : Array String)
    (previous : Array Decl) (e : TSyntax `psTerm) :
    Except String NatExpr := do
  match e with
  | `(psTerm| $native:term) =>
      lowerExpr locals previous native
  | `(psTerm| $head:ident($[$args:psCallArg],*)) =>
      let name := head.getId.toString
      let some decl := findPrevious previous name
        | throw s!"PS0-JS-CALL: unresolved or forward function {name}"
      if decl.isConst || decl.params.size != args.size then
        throw s!"PS0-JS-CALL: {name} has incompatible Nat argument arity"
      let mut lowered : Array NatExpr := #[]
      for arg in args do
        match arg with
        | `(psCallArg| $v:psTerm) =>
            lowered := lowered.push (← lowerHostExpr locals previous v)
        | _ =>
            throw "PS0-JS-CALL: named/defaulted host arguments are not yet supported"
      return .call name lowered
  | _ =>
      throw s!"PS0-JS-EXPR: unsupported host expression kind {e.raw.getKind}"

private def lowerBinder (b : TSyntax `pscvBinder) : Except String String := do
  match b with
  | `(pscvBinder| $n:ident : $t:term) =>
      unless isNatType t do
        throw "PS0-JS-TYPE: MVP only supports Nat parameter types"
      checkedName n
  | _ =>
      throw "PS0-JS-PARAM: default, implicit and dependent binders are pending"

private def lowerParams (bs : Array (TSyntax `pscvBinder)) :
    Except String (Array String) := do
  let mut result := #[]
  for b in bs do
    let name ← lowerBinder b
    if result.contains name then
      throw s!"PS0-JS-PARAM: duplicate parameter {name}"
    result := result.push name
  return result

private def declOrigin (input : Parser.InputContext) (cmd : Syntax) :
    Except String Origin := do
  let some offset := cmd.getPos?
    | throw "PS0-JS-MAP: original source declaration position is unavailable"
  let pos := input.fileMap.toPosition offset
  return { line := pos.line - 1, column := pos.column }

private def lowerCommand (input : Parser.InputContext) (cmd : Syntax)
    (previous : Array Decl) :
    Except String Decl := do
  let origin ← declOrigin input cmd
  match cmd with
  | `(command| const $n:ident : $ty:term := $body:psTerm) =>
      unless isNatType ty do
        throw "PS0-JS-TYPE: MVP only exports explicitly typed Nat constants"
      let name ← checkedName n
      return { name, body := (← lowerHostExpr #[] previous body), isConst := true, origin }
  | `(command| function $n:ident ($[$bs:pscvBinder],*) :
      $ty:term := $body:psTerm) =>
      unless isNatType ty do
        throw "PS0-JS-TYPE: MVP only exports functions returning Nat"
      let name ← checkedName n
      let params ← lowerParams bs
      return {
        name, params, body := (← lowerHostExpr params previous body),
        isConst := false, origin
      }
  | `(command| const $n:ident : $ty:term := $body:term) =>
      unless isNatType ty do
        throw "PS0-JS-TYPE: MVP only exports explicitly typed Nat constants"
      let name ← checkedName n
      return { name, body := (← lowerExpr #[] previous body), isConst := true, origin }
  | `(command| function $n:ident ($[$bs:pscvBinder],*) :
      $ty:term := $body:term) =>
      unless isNatType ty do
        throw "PS0-JS-TYPE: MVP only exports functions returning Nat"
      let name ← checkedName n
      let params ← lowerParams bs
      return {
        name, params, body := (← lowerExpr params previous body),
        isConst := false, origin
      }
  | _ =>
      throw s!"PS0-JS-COMMAND: unsupported runtime declaration {cmd.getKind}"

/-- Confirm source exports against actual official Lean checked declarations.
    Only pure, total definitions with exactly the selected Core Nat telescope
    are permitted. This is stricter than matching a .ps header: no unchecked
    function name, implicit/default parameter or non-Nat Core result can be
    admitted to JS. Unit occurs only as the source-nullary function sugar. -/
private def exactCoreType (decl : Decl) (coreType : Expr) : Bool :=
  if decl.isConst then
    coreType == mkConst `Nat
  else Id.run do
    let mut ty := coreType
    if decl.params.isEmpty then
      match ty with
      | .forallE _ domain body info =>
          if !info.isExplicit || domain != mkConst `Unit then return false
          ty := body
      | _ => return false
    else
      for _ in [:decl.params.size] do
        match ty with
        | .forallE _ domain body info =>
            if !info.isExplicit || domain != mkConst `Nat then return false
            ty := body
        | _ => return false
    return ty == mkConst `Nat

def validateCheckedExports (checked : Environment) (p : Program) :
    Except String Unit := do
  for decl in p.declarations do
    let some info := checked.find? (Name.mkSimple decl.name)
      | throw s!"PS0-JS-CORE: checked Lean declaration missing: {decl.name}"
    match info with
    | .defnInfo d =>
        if d.safety != .safe then
          throw s!"PS0-JS-CORE: unsafe or partial declaration: {decl.name}"
        unless exactCoreType decl d.type do
          throw s!"PS0-JS-CORE: Core Nat signature mismatch for {decl.name}"
    | _ =>
        throw s!"PS0-JS-CORE: export {decl.name} is not a checked definition"

def lower (sourceName source : String) (env : Environment)
    (opts : Options) : Except String Program := Id.run do
  let input := Parser.mkInputContext source sourceName
  let mut parserState : Parser.ModuleParserState := {}
  let mut messages : MessageLog := {}
  let mut declarations : Array Decl := #[]
  repeat
    let (cmd, next, nextMessages) :=
      Parser.parseCommand input
        { env := env, options := opts, currNamespace := .anonymous, openDecls := [] }
        parserState messages
    if nextMessages.hasErrors then
      return .error "PS0-JS-PARSE: official Lean parser rejected source"
    if cmd.isOfKind ``Parser.Command.eoi then break
    if next.pos == parserState.pos then
      return .error "PS0-JS-PARSE: parser did not advance"
    let decl ← match lowerCommand input cmd declarations with
      | .ok v => pure v
      | .error e => return .error e
    if declarations.any (fun d => d.name == decl.name) then
      return .error s!"PS0-JS-EXPORT: duplicate public name {decl.name}"
    declarations := declarations.push decl
    parserState := next
    messages := nextMessages
  if declarations.isEmpty then
    return .error "PS0-JS-EMPTY: no eligible Nat declarations"
  return .ok { sourceName, sourceText := source, declarations }

end PS0.Backend.Js
