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
namespace PS0

syntax (name := ps0StandardDef) (priority := high)
  declModifiers "def " ident bracketedBinder* (":" psTerm)? ":=" psTerm : command
syntax (name := ps0StandardAbbrev) (priority := high)
  declModifiers "abbrev " ident bracketedBinder* (":" psTerm)? ":=" psTerm : command
syntax (name := ps0StandardTheorem) (priority := high)
  declModifiers "theorem " ident bracketedBinder* ":" psTerm ":=" psTerm : command
syntax (name := ps0StandardExample) (priority := high)
  declModifiers "example " bracketedBinder* ":" psTerm ":=" psTerm : command

private def nativeTerm (body : TSyntax `psTerm) : MacroM (TSyntax `term) := do
  return ⟨← PS0.Syntax.lower `psTerm body.raw⟩

macro_rules (kind := ps0StandardDef)
  | `($mods:declModifiers def $name:ident $bs:bracketedBinder* $[: $ty:psTerm]? := $body:psTerm) => do
      let ty ← ty.mapM nativeTerm
      let body ← nativeTerm body
      `($mods:declModifiers def $name:ident $bs:bracketedBinder* $[: $ty:term]? := $body:term)

macro_rules (kind := ps0StandardAbbrev)
  | `($mods:declModifiers abbrev $name:ident $bs:bracketedBinder* $[: $ty:psTerm]? := $body:psTerm) => do
      let ty ← ty.mapM nativeTerm
      let body ← nativeTerm body
      `($mods:declModifiers abbrev $name:ident $bs:bracketedBinder* $[: $ty:term]? := $body:term)

macro_rules (kind := ps0StandardTheorem)
  | `($mods:declModifiers theorem $name:ident $bs:bracketedBinder* : $ty:psTerm := $body:psTerm) => do
      let ty ← nativeTerm ty
      let body ← nativeTerm body
      `($mods:declModifiers theorem $name:ident $bs:bracketedBinder* : $ty:term := $body:term)

macro_rules (kind := ps0StandardExample)
  | `($mods:declModifiers example $bs:bracketedBinder* : $ty:psTerm := $body:psTerm) => do
      let ty ← nativeTerm ty
      let body ← nativeTerm body
      `($mods:declModifiers example $bs:bracketedBinder* : $ty:term := $body:term)

end PS0
