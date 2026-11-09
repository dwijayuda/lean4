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

declare_syntax_cat psDeclValue

@[run_parser_attribute_hooks] def nativePSMatchAlts : Lean.Parser.Parser :=
  Lean.Parser.Term.matchAlts (Lean.Parser.categoryParser `psTerm 0)

syntax (name := ps0DeclSimple) ":=" psTerm (psDeclTail)? : psDeclValue
syntax (name := ps0DeclEqns) nativePSMatchAlts (psDeclTail)? : psDeclValue

declare_syntax_cat psStructFieldValue
declare_syntax_cat psStructField

syntax (name := ps0StructFieldDef) ":=" ("private")? psTerm : psStructFieldValue
syntax (name := ps0StructFieldEqns) ("private")? nativePSMatchAlts : psStructFieldValue
syntax (name := ps0StructField) Lean.Parser.Term.structInstLVal
  (psDeclBinder* (":" psTerm)? psStructFieldValue)? : psStructField

@[run_parser_attribute_hooks] def nativePSStructFields : Lean.Parser.Parser :=
  Lean.Parser.Term.structInstFields
    (Lean.Parser.sepByIndent (Lean.Parser.categoryParser `psStructField 0) "; " (allowTrailingSep := true))

syntax (name := ps0DeclWhere) "where" nativePSStructFields
  (Lean.Parser.Term.whereDecls)? : psDeclValue

private def lowerAlts (alts : Syntax) : MacroM Syntax := do
  let lowered ← alts[0].getArgs.mapM fun alt => do
    unless alt.isOfKind ``Lean.Parser.Term.matchAlt && alt.getArgs.size == 4 do
      Macro.throwError "PS0V1-DECL-EQUATIONS: unexpected native alternative shape"
    return alt.setArg 3 (← PS0.Syntax.lower `psTerm alt[3])
  return alts.setArg 0 (alts[0].setArgs lowered)

private def lowerField (field : Syntax) : MacroM Syntax := do
  let optionalBody := field[1]
  if optionalBody.getArgs.isEmpty then
    return mkNode ``Lean.Parser.Term.structInstField #[field[0], optionalBody]
  let binders ← PS0.Binders.lowerTelescope (optionalBody[0].getArgs.map (⟨·⟩ : Syntax → TSyntax `psDeclBinder))
  let ty := optionalBody[1]
  let ty ← if ty.getArgs.isEmpty then pure ty else do
    pure <| mkNullNode #[mkNode ``Lean.Parser.Term.typeSpec
      #[ty[0], ← PS0.Syntax.lower `psTerm ty[1]]]
  let value := optionalBody[2]
  let value ← if value.isOfKind ``ps0StructFieldDef then do
    pure <| mkNode ``Lean.Parser.Term.structInstFieldDef
      #[value[0], value[1], ← PS0.Syntax.lower `psTerm value[2]]
    else if value.isOfKind ``ps0StructFieldEqns then do
      pure <| mkNode ``Lean.Parser.Term.structInstFieldEqns #[value[0], ← lowerAlts value[1]]
    else Macro.throwError "PS0V1-STRUCT-FIELD: unsupported field declaration value"
  return mkNode ``Lean.Parser.Term.structInstField
    #[field[0], mkNullNode #[mkNullNode binders, ty, value]]

private def nativeValue (source : TSyntax `psDeclValue) : MacroM (TSyntax ``Lean.Parser.Command.declVal) := do
  let value := source.raw
  if value.isOfKind ``ps0DeclWhere then
    let fields := value[1]
    let lowered ← fields[0].getArgs.mapM fun field => do
      if field.isOfKind ``ps0StructField then lowerField field else pure field
    return ⟨mkNode ``Lean.Parser.Command.whereStructInst
      #[value[0], fields.setArg 0 (fields[0].setArgs lowered), value[2]]⟩
  let tail := value.getArgs.back![0]
  let defaults ← `(Lean.Parser.Command.definition| def __ps0Value := ())
  let suffix := if tail.isMissing then defaults.raw[3][2] else tail[0]
  let whereDecls := if tail.isMissing then defaults.raw[3][3] else tail[1]
  if value.isOfKind ``ps0DeclSimple then
    return ⟨mkNode ``Lean.Parser.Command.declValSimple
      #[value[0], ← PS0.Syntax.lower `psTerm value[1], suffix, whereDecls]⟩
  unless value.isOfKind ``ps0DeclEqns do
    Macro.throwError "PS0V1-DECL-VALUE: unsupported declaration value"
  return ⟨mkNode ``Lean.Parser.Command.declValEqns
    #[mkNode ``Lean.Parser.Term.matchAltsWhereDecls
      #[← lowerAlts value[0], suffix, whereDecls]]⟩

scoped syntax (name := ps0StandardDef) (priority := 20000)
  declModifiers "def " declId psDeclBinder* (":" psTerm)? psDeclValue : command
scoped syntax (name := ps0StandardAbbrev) (priority := 20000)
  declModifiers "abbrev " declId psDeclBinder* (":" psTerm)? psDeclValue : command
scoped syntax (name := ps0StandardTheorem) (priority := 20000)
  declModifiers "theorem " declId psDeclBinder* ":" psTerm psDeclValue : command
scoped syntax (name := ps0StandardExample) (priority := 20000)
  declModifiers "example " psDeclBinder* (":" psTerm)? psDeclValue : command

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardDef)
  | `($mods:declModifiers def $name:declId $bs:psDeclBinder* $[: $ty:psTerm]? $value:psDeclValue) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← ty.mapM nativeTerm
      let value ← nativeValue value
      let decl ← `(Lean.Parser.Command.definition| def $name:declId $bs:bracketedBinder* $[: $ty:term]? $value:declVal)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardAbbrev)
  | `($mods:declModifiers abbrev $name:declId $bs:psDeclBinder* $[: $ty:psTerm]? $value:psDeclValue) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← ty.mapM nativeTerm
      let value ← nativeValue value
      let decl ← `(Lean.Parser.Command.abbrev| abbrev $name:declId $bs:bracketedBinder* $[: $ty:term]? $value:declVal)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardTheorem)
  | `($mods:declModifiers theorem $name:declId $bs:psDeclBinder* : $ty:psTerm $value:psDeclValue) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← nativeTerm ty
      let value ← nativeValue value
      let decl ← `(Lean.Parser.Command.theorem| theorem $name:declId $bs:bracketedBinder* : $ty:term $value:declVal)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardExample)
  | `($mods:declModifiers example $bs:psDeclBinder* $[: $ty:psTerm]? $value:psDeclValue) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← ty.mapM nativeTerm
      let value ← nativeValue value
      let decl ← `(Lean.Parser.Command.example| example $bs:bracketedBinder* $[: $ty:term]? $value:declVal)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

scoped syntax (name := ps0StandardFunction) (priority := 20000)
  declModifiers "function " declId psDeclBinder+ (":" psTerm)? psDeclValue : command

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardFunction)
  | `($mods:declModifiers function $name:declId $bs:psDeclBinder* $[: $ty:psTerm]? $value:psDeclValue) => do
      let bs ← PS0.Binders.lowerTelescope bs true
      let ty ← ty.mapM nativeTerm
      let value ← nativeValue value
      let decl ← `(Lean.Parser.Command.definition| def $name:declId $bs:bracketedBinder* $[: $ty:term]? $value:declVal)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

scoped syntax (name := ps0StandardOpaque) (priority := 20000)
  declModifiers "opaque " declId psDeclBinder* ":" psTerm (":=" psTerm)? : command
scoped syntax (name := ps0StandardAxiom) (priority := 20000)
  declModifiers "axiom " declId psDeclBinder* ":" psTerm : command
scoped syntax (name := ps0StandardConst) (priority := 20000)
  declModifiers "const " declId (":" psTerm)? psDeclValue : command
scoped syntax (name := ps0StandardInstance) (priority := 20000)
  declModifiers attrKind "instance" optNamedPrio (declId)? psDeclBinder* ":" psTerm psDeclValue : command

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
  | `($mods:declModifiers const $name:declId $[: $ty:psTerm]? $value:psDeclValue) => do
      let ty ← ty.mapM nativeTerm
      let value ← nativeValue value
      let decl ← `(Lean.Parser.Command.definition| def $name:declId $[: $ty:term]? $value:declVal)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

open scoped PS0.StandardAdapters in
macro_rules (kind := ps0StandardInstance)
  | `($mods:declModifiers $kind:attrKind instance $[$prio:namedPrio]? $[$name:declId]? $bs:psDeclBinder* : $ty:psTerm $value:psDeclValue) => do
      let bs ← PS0.Binders.lowerTelescope bs
      let ty ← nativeTerm ty
      let value ← nativeValue value
      let decl ← `(Lean.Parser.Command.instance| $kind:attrKind instance $[$prio:namedPrio]? $[$name:declId]? $bs:bracketedBinder* : $ty:term $value:declVal)
      return mkNode ``Lean.Parser.Command.declaration #[mods.raw, decl.raw]

end PS0.StandardAdapters
