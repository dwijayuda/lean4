/-
Copyright (c) 2026 Dwijayuda. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
import Lean
import PS0.StandardAdapters

/-! Syntax-only host registrations for a target prelude with no logical PS0 import. -/

open Lean Lean.Parser Lean.Elab
namespace PS0.SourceGrammar

register_builtin_option ps0.sourceGrammar : Bool := {
  defValue := false
  descr := "enable the finite owned PS grammar host for compiler source migration"
}

private def categoryNames : Array Name :=
  #[`psTerm, `psCommand, `psTactic, `psDoSeq, `psCallArg, `psHead,
    `psDoElem, `psDoItem, `psBinderParam, `psDeclBinder]

private def commandNames : Array Name :=
  #[`PS0.StandardAdapters.ps0StandardDef, `PS0.StandardAdapters.ps0StandardAbbrev,
    `PS0.StandardAdapters.ps0StandardTheorem, `PS0.StandardAdapters.ps0StandardExample,
    `PS0.StandardAdapters.ps0StandardFunction, `PS0.StandardAdapters.ps0StandardOpaque,
    `PS0.StandardAdapters.ps0StandardAxiom, `PS0.StandardAdapters.ps0StandardConst,
    `PS0.StandardAdapters.ps0StandardInstance]

-- Contextual alias words must remain ordinary identifiers in native DSL syntax.
private partial def contextualAliases : ParserDescr → ParserDescr
  | .symbol word =>
      if word.trimAscii.toString == "function" || word.trimAscii.toString == "const" then
        .nonReservedSymbol word true
      else .symbol word
  | .unary name p => .unary name (contextualAliases p)
  | .binary name p q => .binary name (contextualAliases p) (contextualAliases q)
  | .node name prec p => .node name prec (contextualAliases p)
  | .nodeWithAntiquot text name p => .nodeWithAntiquot text name (contextualAliases p)
  | .sepBy p sep q trail => .sepBy (contextualAliases p) sep (contextualAliases q) trail
  | .sepBy1 p sep q trail => .sepBy1 (contextualAliases p) sep (contextualAliases q) trail
  | .trailingNode name prec lhs p => .trailingNode name prec lhs (contextualAliases p)
  | other => other

private def copyMacros (host : Environment) (kind : Name) : IO Unit := do
  registerBuiltinNodeKind kind
  for entry in macroAttribute.getEntries host kind do
    macroAttribute.addBuiltin kind entry.declName entry.value

private def rootDispatch (native : CategoryParserFn) : CategoryParserFn := fun category =>
  if category != `command then native category else fun ctx state =>
    if ctx.options.getBool `ps0.sourceGrammar false then
      -- Consume the route only in this parser context. Native command operands,
      -- quotations and independently owned DSL categories keep native parsing.
      adaptUncacheableContextFn
        (fun c => {c with options := c.options.setBool `ps0.sourceGrammar false})
        (native `psCommand) ctx state
    else native category ctx state

private unsafe def installImpl (options : Options) : IO Unit := do
  -- Native toolchains ship compiler metadata beside their executable. Load that
  -- host metadata in a separate environment, then restore target module lookup.
  let targetPath ← searchPathRef.get
  let binDir := (← IO.appPath).parent.getD "."
  let hostPath := binDir / ".." / "lib" / "lean"
  searchPathRef.set (hostPath :: targetPath)
  let host ← try
    importModules #[{module := `PS0.StandardAdapters, isMeta := true}] options (loadExts := true)
  finally
    searchPathRef.set targetPath
  let state := parserExtension.getState host
  for name in categoryNames do
    let some cat := state.categories.find? name
      | throw <| IO.userError s!"PS0-SOURCE-GRAMMAR: missing host category {name}"
    builtinParserCategoriesRef.modify fun cats => cats.insert name cat
    builtinSyntaxNodeKindSetRef.modify fun kinds =>
      cat.kinds.foldl (fun kinds kind _ => kinds.insert kind) kinds
  for name in commandNames do
    let descr ← IO.ofExcept <| host.evalConst ParserDescr options name
    let parser ← (compileParserDescr state.categories (contextualAliases descr)).run
      {env := host, opts := options}
    addBuiltinLeadingParser `psCommand name parser 20000
    copyMacros host name
  -- This bridge is an identity macro; target logic never imports its declaration.
  macroAttribute.addBuiltin `ps0NativeCommandBridge `PS0.SourceGrammar.nativeCommand
    (fun source => pure source[0])
  registerBuiltinNodeKind `ps0NativeCommandBridge
  -- Empty-call elaboration is an owned operand produced by the PS head adapter.
  for entry in Elab.Term.termElabAttribute.getEntries host `PS0.pscvEmptyCall do
    Elab.Term.termElabAttribute.addBuiltin `PS0.pscvEmptyCall entry.declName entry.value
  registerBuiltinNodeKind `PS0.pscvEmptyCall
  registerBuiltinNodeKind `PS0.Binders.binderDefault
  let native ← categoryParserFnRef.get
  categoryParserFnRef.set (rootDispatch native)

@[implemented_by installImpl]
opaque install (options : Options) : IO Unit

end PS0.SourceGrammar
