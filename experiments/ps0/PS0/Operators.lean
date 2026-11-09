/-
Copyright (c) 2026 Dwijayuda. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
module
public meta import Lean
public meta import PS0.OperatorDescriptors
public meta section

/-! Borrow native term parsers with explicit PS operand and legacy-surface boundaries. -/

open Lean Lean.Parser
namespace PS0.Operators

def ownedKind : Name := `PS0.Operators.ownedBinary
def ownedPostfixKind : Name := `PS0.Operators.ownedPostfix
def bridgeKind : Name := `ps0NativeTermBridge
def headBridgeKind : Name := `ps0NativeHeadBridge

def indexArity? (kind : Name) : Option Nat :=
  if kind == `«term__[_]» then some 4
  else if kind == `«term__[_]'_» then some 5
  else if kind == `«term__[_]_?» || kind == `«term__[_]_!» then some 7
  else none

def indexKinds : Array Name :=
  #[`«term__[_]», `«term__[_]'_», `«term__[_]_?», `«term__[_]_!»]

def sliceShape? (kind : Name) : Option (Nat × Array Nat) :=
  if kind == `Array.«term__[_:_]» then some (6, #[2, 4])
  else if kind == `Array.«term__[_:]» then some (5, #[2])
  else if kind == `Array.«term__[:_]» then some (5, #[3])
  else none

def bracketKinds : Array Name :=
  indexKinds ++ #[`Array.«term__[_:_]», `Array.«term__[_:]», `Array.«term__[:_]»]

builtin_initialize
  registerBuiltinNodeKind ownedKind
  registerBuiltinNodeKind ownedPostfixKind
  registerBuiltinNodeKind bridgeKind
  registerBuiltinNodeKind headBridgeKind

run_cmd do
  modifyEnv fun env => addSyntaxNodeKind
    (addSyntaxNodeKind (addSyntaxNodeKind (addSyntaxNodeKind env ownedKind) ownedPostfixKind) bridgeKind) headBridgeKind

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

private def filterToken (table : TokenMap (Parser × Nat)) (token : Name)
    (keep : Parser × Nat → Bool) : TokenMap (Parser × Nat) :=
  match table.get? token with
  | none => table
  | some parsers => Std.TreeMap.insert table token (parsers.filter keep)

private unsafe def leadingWith (head : Bool) : ParserFn := fun ctx initial => unsafeBaseIO do
  let some category := getParserCategory? ctx.env `term
    | return initial.mkUnexpectedError "PS0V1-OP-CATEGORY: missing native term category"
  let kinds := if head then #[] else PS0.OperatorDescriptors.binaryKinds ctx.env ctx.options
  let keepLeading := fun (entry : Parser × Nat) =>
    !(entry.1.info.collectKinds {}).contains `PS0.pscvBracedExpression
  let mut leadingTable := category.tables.leadingTable
  if head then
    leadingTable := filterToken leadingTable `«{» keepLeading
  else
    leadingTable := {}
    for (token, parsers) in category.tables.leadingTable do
      for entry in (parsers.filter keepLeading).reverse do
        leadingTable := leadingTable.insert token entry
  let leadingTables := {category.tables with
    leadingTable, leadingParsers := category.tables.leadingParsers.filter keepLeading}
  let keep := fun (entry : Parser × Nat) =>
    let collected := entry.1.info.collectKinds {}
    !kinds.any collected.contains && !bracketKinds.any collected.contains &&
      !collected.contains ``Lean.Parser.Term.pipeProj &&
      !collected.contains ``Lean.Parser.Term.pipeCompletion
  let mut trailingTable := category.tables.trailingTable
  if head then
    trailingTable := filterToken (filterToken trailingTable `«[» keep) `«|>.» keep
  else
    trailingTable := {}
    for (token, parsers) in category.tables.trailingTable do
      for entry in (parsers.filter keep).reverse do
        trailingTable := trailingTable.insert token entry
  let tables := {category.tables with
    trailingTable, trailingParsers := category.tables.trailingParsers.filter keep}
  -- The unrestricted legacy wrapper is not an ordinary PS term production.
  -- Native operands keep their context, precedence, antiquotations and syntax data.
  let parsed := leadingParser `term leadingTables category.behavior
    (mkCategoryAntiquotParser `term).fn ctx initial
  if parsed.hasError then return parsed
  let parsed := trailingLoop tables ctx parsed
  if parsed.hasError then return parsed
  let native := parsed.stxStack.back
  return parsed.popSyntax.pushSyntax <| .node .none (if head then headBridgeKind else bridgeKind) #[native]

private unsafe def leadingImpl : ParserFn := leadingWith false
@[implemented_by leadingImpl]
opaque leadingFn : ParserFn

@[expose, run_parser_attribute_hooks] def leading : Parser :=
  withFn (fun _ => leadingFn) (node bridgeKind (categoryParser `term 0))

private unsafe def headLeadingImpl : ParserFn :=
  andthenFn (checkPrecFn maxPrec) <|
    andthenFn (adaptCacheableContextFn ({ · with prec := maxPrec })
      (withCacheFn headBridgeKind (leadingWith true))) (setLhsPrecFn maxPrec)

@[implemented_by headLeadingImpl]
opaque headLeadingFn : ParserFn

@[expose, run_parser_attribute_hooks] def headLeading : Parser :=
  withFn (fun _ => headLeadingFn)
    (leadingNode headBridgeKind maxPrec (categoryParser `term maxPrec))

private unsafe def trailingWith (projectionOnly : Bool) : ParserFn := fun ctx initial => unsafeBaseIO do
  let some category := getParserCategory? ctx.env `term
    | return initial.mkUnexpectedError "PS0V1-OP-CATEGORY: missing native term category"
  let kinds := if projectionOnly then #[] else PS0.OperatorDescriptors.binaryKinds ctx.env ctx.options
  let (state, indexedParsers) := indexed category.tables.trailingTable ctx initial .default
  if state.hasError then return state
  let candidates := (indexedParsers ++ category.tables.trailingParsers).filter fun (parser, _) =>
    let collected := parser.info.collectKinds {}
    kinds.any collected.contains || bracketKinds.any collected.contains ||
      collected.contains ``Lean.Parser.Term.proj ||
      (!projectionOnly && collected.contains ``Lean.Parser.Term.pipeProj)
  if candidates.isEmpty then return initial.mkUnexpectedError "no owned native binary operator"
  let candidates := candidates.map fun (parser, priority) =>
    (if (parser.info.collectKinds {}).contains ``Lean.Parser.Term.proj then parser else operandParser parser, priority)
  let parsed := longestMatchFn (some initial.stxStack.back) candidates ctx initial.popSyntax
  if parsed.hasError then return parsed
  let native := parsed.stxStack.back
  if native.isOfKind choiceKind then
    unless !native.getArgs.isEmpty && native.getArgs.all (fun alternative =>
        kinds.contains alternative.getKind && alternative.getArgs.size == 3) do
      return parsed.mkUnexpectedError "PS0V1-OP-CHOICE: unsupported native operator alternatives"
    return parsed.popSyntax.pushSyntax <| .node .none ownedKind #[native]
  if native.isOfKind ``Lean.Parser.Term.pipeProj && native.getArgs.size == 5 then
    return parsed.popSyntax.pushSyntax <| .node .none ownedPostfixKind #[native]
  if let some arity := indexArity? native.getKind then
    unless native.getArgs.size == arity do
      return parsed.mkUnexpectedError "PS0V1-INDEX-SHAPE: unexpected native indexed access"
    return parsed.popSyntax.pushSyntax <| .node .none ownedPostfixKind #[native]
  if let some (arity, _) := sliceShape? native.getKind then
    unless native.getArgs.size == arity do
      return parsed.mkUnexpectedError "PS0V1-SLICE-SHAPE: unexpected native array slice"
    return parsed.popSyntax.pushSyntax <| .node .none ownedPostfixKind #[native]
  if native.isOfKind ``Lean.Parser.Term.proj && native.getArgs.size == 3 then
    return parsed.popSyntax.pushSyntax <| .node .none ownedPostfixKind #[native]
  unless kinds.contains native.getKind && native.getArgs.size == 3 do
    return parsed.mkUnexpectedError "PS0V1-OP-SHAPE: unexpected native binary operator result"
  return parsed.popSyntax.pushSyntax <| .node .none ownedKind #[native]

private unsafe def trailingImpl : ParserFn := trailingWith false

@[implemented_by trailingImpl]
opaque trailingFn : ParserFn

@[expose, run_parser_attribute_hooks] def trailing : TrailingParser :=
  withFn (fun _ => trailingFn) (node ownedKind (categoryParser `term 0))

private unsafe def projectionImpl : ParserFn := trailingWith true

@[implemented_by projectionImpl]
opaque projectionFn : ParserFn

@[expose, run_parser_attribute_hooks] def projection : TrailingParser :=
  withFn (fun _ => projectionFn) (node ownedPostfixKind (categoryParser `term 0))

end PS0.Operators
