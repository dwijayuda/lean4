import Lean
import PS0.Grammar
import PS0.Backend.Js.IR

/-!
Selected v7 source AST -> typed portable runtime IR.
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

private partial def lowerExpr (locals : Array String)
    (e : TSyntax `term) : Except String NatExpr := do
  match e with
  | `(term| { $inner:term }) => lowerExpr locals inner
  | `(term| ($inner:term)) => lowerExpr locals inner
  | `(term| $n:num) => return .literal n.getNat
  | `(term| $n:ident) =>
      let name := n.getId.toString
      if locals.contains name then return .local name
      throw s!"PS0-JS-EXPR: nonlocal value {name} is outside the Nat MVP"
  | `(term| $a:term + $b:term) =>
      return .add (← lowerExpr locals a) (← lowerExpr locals b)
  | `(term| $a:term * $b:term) =>
      return .mul (← lowerExpr locals a) (← lowerExpr locals b)
  | `(term| $a:term - $b:term) =>
      return .sub (← lowerExpr locals a) (← lowerExpr locals b)
  | _ =>
      throw s!"PS0-JS-EXPR: unsupported Nat expression syntax {e.raw.getKind}"

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

private def declOrigin (input : Parser.InputContext) (cmd : Syntax) : Origin :=
  let pos := input.fileMap.toPosition (cmd.getPos?.getD 0)
  { line := pos.line - 1, column := pos.column }

private def lowerCommand (input : Parser.InputContext) (cmd : Syntax) :
    Except String Decl := do
  let origin := declOrigin input cmd
  match cmd with
  | `(command| const $n:ident : $ty:term := $body:term) =>
      unless isNatType ty do
        throw "PS0-JS-TYPE: MVP only exports explicitly typed Nat constants"
      let name ← checkedName n
      return { name, body := (← lowerExpr #[] body), isConst := true, origin }
  | `(command| function $n:ident ($[$bs:pscvBinder],*) :
      $ty:term := $body:term) =>
      unless isNatType ty do
        throw "PS0-JS-TYPE: MVP only exports functions returning Nat"
      let name ← checkedName n
      let params ← lowerParams bs
      return {
        name, params, body := (← lowerExpr params body),
        isConst := false, origin
      }
  | _ =>
      throw s!"PS0-JS-COMMAND: unsupported runtime declaration {cmd.getKind}"

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
    if cmd.isOfKind `Parser.Command.eoi then break
    if next.pos == parserState.pos then
      return .error "PS0-JS-PARSE: parser did not advance"
    let decl ← match lowerCommand input cmd with
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
