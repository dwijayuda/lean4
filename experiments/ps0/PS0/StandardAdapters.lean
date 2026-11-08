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
namespace PS0.StandardAdapters

private def nativeTerm (body : TSyntax `psTerm) : MacroM (TSyntax `term) := do
  return ⟨← PS0.Syntax.lower `psTerm body.raw⟩

scoped syntax (name := ps0StandardDef) (priority := 2000)
  declModifiers "def " declId psDeclBinder* (":" psTerm)? ":=" psTerm : command
scoped syntax (name := ps0StandardAbbrev) (priority := 2000)
  declModifiers "abbrev " declId psDeclBinder* (":" psTerm)? ":=" psTerm : command
scoped syntax (name := ps0StandardTheorem) (priority := 2000)
  declModifiers "theorem " declId psDeclBinder* ":" psTerm ":=" psTerm : command
scoped syntax (name := ps0StandardExample) (priority := 2000)
  declModifiers "example " psDeclBinder* ":" psTerm ":=" psTerm : command

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardDef)
  | `($mods:declModifiers def $name:declId $bs:psDeclBinder* $[: $ty:psTerm]? := $body:psTerm) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← ty.mapM nativeTerm
      let body ← nativeTerm body
      let decl ← `(Lean.Parser.Command.definition| def $name:declId $bs:bracketedBinder* $[: $ty:term]? := $body:term)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardAbbrev)
  | `($mods:declModifiers abbrev $name:declId $bs:psDeclBinder* $[: $ty:psTerm]? := $body:psTerm) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← ty.mapM nativeTerm
      let body ← nativeTerm body
      let decl ← `(Lean.Parser.Command.abbrev| abbrev $name:declId $bs:bracketedBinder* $[: $ty:term]? := $body:term)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardTheorem)
  | `($mods:declModifiers theorem $name:declId $bs:psDeclBinder* : $ty:psTerm := $body:psTerm) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← nativeTerm ty
      let body ← nativeTerm body
      let decl ← `(Lean.Parser.Command.theorem| theorem $name:declId $bs:bracketedBinder* : $ty:term := $body:term)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardExample)
  | `($mods:declModifiers example $bs:psDeclBinder* : $ty:psTerm := $body:psTerm) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← nativeTerm ty
      let body ← nativeTerm body
      let decl ← `(Lean.Parser.Command.example| example $bs:bracketedBinder* : $ty:term := $body:term)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

scoped syntax (name := ps0StandardFunction) (priority := 2000)
  declModifiers "function " declId psDeclBinder+ (":" psTerm)? ":=" psTerm : command

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardFunction)
  | `($mods:declModifiers function $name:declId $bs:psDeclBinder* $[: $ty:psTerm]? := $body:psTerm) => do
      let bs ← PS0.Binders.lowerTelescope bs true
      let ty ← ty.mapM nativeTerm
      let body ← nativeTerm body
      let decl ← `(Lean.Parser.Command.definition| def $name:declId $bs:bracketedBinder* $[: $ty:term]? := $body:term)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

end PS0.StandardAdapters
