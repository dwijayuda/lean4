/-
Copyright (c) 2026 Dwijayuda. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
module
public meta import Lean
public import PS0.Syntax
public meta section

/-! Pinned declaration operand adapters; Lean keeps modifier, binder and declaration semantics. -/

open Lean Lean.Parser.Command Lean.Parser.Term
open PS0.Binders
namespace PS0.StandardAdapters

private def nativeTerm (body : TSyntax `psTerm) : MacroM (TSyntax `term) := do
  return ⟨← PS0.Syntax.lower `psTerm body.raw⟩

declare_syntax_cat psDeclTail

@[run_parser_attribute_hooks] def nativeDeclTail : Lean.Parser.Parser :=
  -- Empty tails must also be tried when no hint keyword is the next token.
  Lean.Parser.withoutInfo (Lean.Parser.Termination.suffix >>
    Lean.Parser.optional Lean.Parser.Term.whereDecls)
syntax (name := ps0DeclTail) nativeDeclTail : psDeclTail

private def attachTail (decl : Syntax) (tail? : Option (TSyntax `psDeclTail)) : MacroM Syntax := do
  let some tail := tail? | return decl
  for i in [:decl.getArgs.size] do
    let value := decl[i]
    if value.isOfKind ``Lean.Parser.Command.declValSimple then
      return decl.setArg i ((value.setArg 2 tail.raw[0]).setArg 3 tail.raw[1])
  Macro.throwError "PS0V1-DECL-TAIL: missing native simple declaration value"

scoped syntax (name := ps0StandardDef) (priority := 20000)
  declModifiers "def " declId psDeclBinder* (":" psTerm)? ":=" psTerm
  (psDeclTail)? : command
scoped syntax (name := ps0StandardAbbrev) (priority := 20000)
  declModifiers "abbrev " declId psDeclBinder* (":" psTerm)? ":=" psTerm
  (psDeclTail)? : command
scoped syntax (name := ps0StandardTheorem) (priority := 20000)
  declModifiers "theorem " declId psDeclBinder* ":" psTerm ":=" psTerm
  (psDeclTail)? : command
scoped syntax (name := ps0StandardExample) (priority := 20000)
  declModifiers "example " psDeclBinder* (":" psTerm)? ":=" psTerm
  (psDeclTail)? : command

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardDef)
  | `($mods:declModifiers def $name:declId $bs:psDeclBinder* $[: $ty:psTerm]? := $body:psTerm
      $[$tail:psDeclTail]?) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← ty.mapM nativeTerm
      let body ← nativeTerm body
      let decl ← `(Lean.Parser.Command.definition| def $name:declId $bs:bracketedBinder* $[: $ty:term]? := $body:term)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, ← attachTail decl.raw tail]

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardAbbrev)
  | `($mods:declModifiers abbrev $name:declId $bs:psDeclBinder* $[: $ty:psTerm]? := $body:psTerm
      $[$tail:psDeclTail]?) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← ty.mapM nativeTerm
      let body ← nativeTerm body
      let decl ← `(Lean.Parser.Command.abbrev| abbrev $name:declId $bs:bracketedBinder* $[: $ty:term]? := $body:term)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, ← attachTail decl.raw tail]

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardTheorem)
  | `($mods:declModifiers theorem $name:declId $bs:psDeclBinder* : $ty:psTerm := $body:psTerm
      $[$tail:psDeclTail]?) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← nativeTerm ty
      let body ← nativeTerm body
      let decl ← `(Lean.Parser.Command.theorem| theorem $name:declId $bs:bracketedBinder* : $ty:term := $body:term)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, ← attachTail decl.raw tail]

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardExample)
  | `($mods:declModifiers example $bs:psDeclBinder* $[: $ty:psTerm]? := $body:psTerm
      $[$tail:psDeclTail]?) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← ty.mapM nativeTerm
      let body ← nativeTerm body
      let decl ← `(Lean.Parser.Command.example| example $bs:bracketedBinder* $[: $ty:term]? := $body:term)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, ← attachTail decl.raw tail]

scoped syntax (name := ps0StandardFunction) (priority := 20000)
  declModifiers "function " declId psDeclBinder+ (":" psTerm)? ":=" psTerm
  (psDeclTail)? : command

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardFunction)
  | `($mods:declModifiers function $name:declId $bs:psDeclBinder* $[: $ty:psTerm]? := $body:psTerm
      $[$tail:psDeclTail]?) => do
      let bs ← PS0.Binders.lowerTelescope bs true
      let ty ← ty.mapM nativeTerm
      let body ← nativeTerm body
      let decl ← `(Lean.Parser.Command.definition| def $name:declId $bs:bracketedBinder* $[: $ty:term]? := $body:term)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, ← attachTail decl.raw tail]

scoped syntax (name := ps0StandardOpaque) (priority := 20000)
  declModifiers "opaque " declId psDeclBinder* ":" psTerm (":=" psTerm)? : command
scoped syntax (name := ps0StandardAxiom) (priority := 20000)
  declModifiers "axiom " declId psDeclBinder* ":" psTerm : command
scoped syntax (name := ps0StandardConst) (priority := 20000)
  declModifiers "const " declId (":" psTerm)? ":=" psTerm
  (psDeclTail)? : command
scoped syntax (name := ps0StandardInstance) (priority := 20000)
  declModifiers attrKind "instance" optNamedPrio (declId)? psDeclBinder* ":" psTerm ":=" psTerm
  (psDeclTail)? : command

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardOpaque)
  | `($mods:declModifiers opaque $name:declId $bs:psDeclBinder* : $ty:psTerm $[:= $body:psTerm]?) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← nativeTerm ty
      let body ← body.mapM nativeTerm
      let decl ← `(Lean.Parser.Command.opaque| opaque $name:declId $bs:bracketedBinder* : $ty:term $[:= $body:term]?)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardAxiom)
  | `($mods:declModifiers axiom $name:declId $bs:psDeclBinder* : $ty:psTerm) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← nativeTerm ty
      let decl ← `(Lean.Parser.Command.axiom| axiom $name:declId $bs:bracketedBinder* : $ty:term)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardConst)
  | `($mods:declModifiers const $name:declId $[: $ty:psTerm]? := $body:psTerm
      $[$tail:psDeclTail]?) => do
      let ty ← ty.mapM nativeTerm
      let body ← nativeTerm body
      let decl ← `(Lean.Parser.Command.definition| def $name:declId $[: $ty:term]? := $body:term)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, ← attachTail decl.raw tail]

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardInstance)
  | `($mods:declModifiers $kind:attrKind instance $[$prio:namedPrio]? $[$name:declId]? $bs:psDeclBinder* : $ty:psTerm := $body:psTerm
      $[$tail:psDeclTail]?) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← nativeTerm ty
      let body ← nativeTerm body
      let decl ← `(Lean.Parser.Command.instance| $kind:attrKind instance $[$prio:namedPrio]? $[$name:declId]? $bs:bracketedBinder* : $ty:term := $body:term)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, ← attachTail decl.raw tail]

end PS0.StandardAdapters
