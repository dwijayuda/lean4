/-
Copyright (c) 2026 Dwijayuda. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
module
public meta import Lean
public meta import PS0.OperatorDescriptors
public meta section

/-! Borrow native binary operator parsers and route their single term operand to PS. -/

open Lean Lean.Parser
namespace PS0.Operators

def ownedKind : Name := `PS0.Operators.ownedBinary
def ownedPostfixKind : Name := `PS0.Operators.ownedPostfix
def bridgeKind : Name := `ps0NativeTermBridge

builtin_initialize
  registerBuiltinNodeKind ownedKind
  registerBuiltinNodeKind ownedPostfixKind
  registerBuiltinNodeKind bridgeKind

run_cmd do
  modifyEnv fun env => addSyntaxNodeKind (addSyntaxNodeKind (addSyntaxNodeKind env ownedKind) ownedPostfixKind) bridgeKind

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
  let kinds := PS0.OperatorDescriptors.binaryKinds ctx.env ctx.options
  let mut prec := ctx.prec
  let mut parsed := (categoryParser `term prec).fn ctx initial
  while parsed.hasError || kinds.contains parsed.stxStack.back.getKind do
    -- Builtin parsers may return max lhsPrec while checking a lower binding power.
    -- A native operator's RHS can also fail on PS syntax before we get its node.
    -- Ask for a successful operator-free prefix, then let the owned trailing
    -- parser read the RHS. Failed probes require a tighter binding power.
    let mut low := prec
    let mut high := maxPrec
    if high <= prec then return parsed
    let leadingProbe := (categoryParser `term high).fn ctx initial
    if leadingProbe.hasError || kinds.contains leadingProbe.stxStack.back.getKind then
      return parsed
    while low + 1 < high do
      let middle := low + (high - low) / 2
      let probe := (categoryParser `term middle).fn ctx initial
      if !probe.hasError && !kinds.contains probe.stxStack.back.getKind then
        high := middle
      else low := middle
    if high <= prec then
      return parsed.mkUnexpectedError "PS0V1-OP-PRECEDENCE: native operator did not advance binding power"
    prec := high
    parsed := (categoryParser `term prec).fn ctx initial
  let native := parsed.stxStack.back
  return parsed.popSyntax.pushSyntax <| .node .none bridgeKind #[native]

@[implemented_by leadingImpl]
opaque leadingFn : ParserFn

@[expose, run_parser_attribute_hooks] def leading : Parser :=
  withFn (fun _ => leadingFn) (node bridgeKind (categoryParser `term 0))

private unsafe def trailingImpl : ParserFn := fun ctx initial => unsafeBaseIO do
  let some category := getParserCategory? ctx.env `term
    | return initial.mkUnexpectedError "PS0V1-OP-CATEGORY: missing native term category"
  let kinds := PS0.OperatorDescriptors.binaryKinds ctx.env ctx.options
  let (state, indexedParsers) := indexed category.tables.trailingTable ctx initial .default
  if state.hasError then return state
  let candidates := (indexedParsers ++ category.tables.trailingParsers).filter fun (parser, _) =>
    let collected := parser.info.collectKinds {}
    kinds.any collected.contains || collected.contains ``Lean.Parser.Term.proj
  if candidates.isEmpty then return initial.mkUnexpectedError "no owned native binary operator"
  let candidates := candidates.map fun (parser, priority) =>
    (if (parser.info.collectKinds {}).contains ``Lean.Parser.Term.proj then parser else operandParser parser, priority)
  let parsed := longestMatchFn (some initial.stxStack.back) candidates ctx initial.popSyntax
  if parsed.hasError then return parsed
  let native := parsed.stxStack.back
  if native.isOfKind ``Lean.Parser.Term.proj && native.getArgs.size == 3 then
    return parsed.popSyntax.pushSyntax <| .node .none ownedPostfixKind #[native]
  unless kinds.contains native.getKind && native.getArgs.size == 3 do
    return parsed.mkUnexpectedError "PS0V1-OP-SHAPE: unexpected native binary operator result"
  return parsed.popSyntax.pushSyntax <| .node .none ownedKind #[native]

@[implemented_by trailingImpl]
opaque trailingFn : ParserFn

@[expose, run_parser_attribute_hooks] def trailing : TrailingParser :=
  withFn (fun _ => trailingFn) (node ownedKind (categoryParser `term 0))

end PS0.Operators
