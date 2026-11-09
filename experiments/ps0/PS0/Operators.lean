/-
Copyright (c) 2026 Dwijayuda. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
module
public meta import Lean
public meta section

/-! Borrow native binary operator parsers and route their single term operand to PS. -/

open Lean Lean.Parser
namespace PS0.Operators

def ownedKind : Name := `PS0.Operators.ownedBinary
def bridgeKind : Name := `ps0NativeTermBridge

private def label : Name → String
  | .str _ s => s
  | _ => ""

private partial def roles : ParserDescr → Option (Array Nat)
  | .symbol _ | .nonReservedSymbol .. | .unicodeSymbol .. => some #[0]
  | .cat `term _ => some #[1]
  | .const n => if #["ppSpace", "ppLine", "ppHardLine", "ppAllowUngrouped"].contains (label n) then some #[] else none
  | .unary n p =>
      if #["ppGroup", "ppRealGroup", "withoutPosition", "withPosition"].contains (label n) then roles p else none
  | .binary n p q => if n == `andthen then do return (← roles p) ++ (← roles q) else none
  | _ => none

private unsafe def operatorKinds (env : Environment) (opts : Options) : Array Name := Id.run do
  let mut result := #[``Lean.Parser.Term.arrow]
  let some category := getParserCategory? env `term | return result
  let names := category.kinds.foldl (fun names name _ => names.push name) (#[] : Array Name)
  for name in names do
    if let some info := env.find? name then
      if info.type.getAppFn.isConstOf ``TrailingParserDescr then
        if let .ok (.trailingNode kind _ _ body) := env.evalConst TrailingParserDescr opts name then
          if roles body == some #[0, 1] then result := result.push kind
  return result

private def ownedOperandContext (ctx : ParserContextCore) : ParserContextCore := Id.run do
  let native := categoryParserFnExtension.getState ctx.env
  let dispatch : CategoryParserFn := fun category =>
    if category == `term then
      adaptUncacheableContextFn
        (fun child => {child with env := categoryParserFnExtension.setState child.env native})
        (native `psTerm)
    else native category
  return {ctx with env := categoryParserFnExtension.setState ctx.env dispatch}

private def operandParser (parser : Parser) : Parser :=
  withFn (adaptUncacheableContextFn ownedOperandContext) parser

private unsafe def leadingImpl : ParserFn := fun ctx initial => unsafeBaseIO do
  let kinds := operatorKinds ctx.env ctx.options
  let mut prec := 0
  let mut parsed := (categoryParser `term prec).fn ctx initial
  while !parsed.hasError && kinds.contains parsed.stxStack.back.getKind do
    let next := parsed.lhsPrec + 1
    if next <= prec then
      return parsed.mkUnexpectedError "PS0V1-OP-PRECEDENCE: native operator did not advance binding power"
    prec := next
    parsed := (categoryParser `term prec).fn ctx initial
  if parsed.hasError then return parsed
  let native := parsed.stxStack.back
  return parsed.popSyntax.pushSyntax <| .node native.getHeadInfo bridgeKind #[native]

@[implemented_by leadingImpl]
opaque leadingFn : ParserFn

def leading : Parser := {info := nodeInfo bridgeKind (categoryParser `term 0).info, fn := leadingFn}

private unsafe def trailingImpl : ParserFn := fun ctx initial => unsafeBaseIO do
  let some category := getParserCategory? ctx.env `term
    | return initial.mkUnexpectedError "PS0V1-OP-CATEGORY: missing native term category"
  let kinds := operatorKinds ctx.env ctx.options
  let (state, indexedParsers) := indexed category.tables.trailingTable ctx initial .default
  if state.hasError then return state
  let candidates := (indexedParsers ++ category.tables.trailingParsers).filter fun (parser, _) =>
    let collected := parser.info.collectKinds {}
    kinds.any collected.contains
  if candidates.isEmpty then return initial.mkUnexpectedError "no owned native binary operator"
  let candidates := candidates.map fun (parser, priority) => (operandParser parser, priority)
  let parsed := longestMatchFn (some initial.stxStack.back) candidates ctx initial.popSyntax
  if parsed.hasError then return parsed
  let native := parsed.stxStack.back
  unless kinds.contains native.getKind && native.getArgs.size == 3 do
    return parsed.mkUnexpectedError "PS0V1-OP-SHAPE: unexpected native binary operator result"
  return parsed.popSyntax.pushSyntax <| .node native.getHeadInfo ownedKind #[native]

@[implemented_by trailingImpl]
opaque trailingFn : ParserFn

def trailing : TrailingParser := {info := nodeInfo ownedKind {}, fn := trailingFn}

builtin_initialize
  registerBuiltinNodeKind ownedKind
  registerBuiltinNodeKind bridgeKind

end PS0.Operators
