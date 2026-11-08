/-
Copyright (c) 2026 Dwijayuda. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
module
public import Lean
public section

/-! Observe the original command stream supplied by Lean's native module-linter hook. -/

open Lean Lean.Elab.Command
namespace PS0.SourceCensus

register_builtin_option ps0.sourceCensusPath : String := {
  defValue := ""
  descr := "write actual native frontend source-command census evidence"
}

private def sourceRange (source : Syntax) : Json :=
  match source.getRange? with
  | none => .null
  | some r => Json.mkObj [("start", toJson r.start.byteIdx), ("end", toJson r.stop.byteIdx)]

private partial def signatureSyntax (source : Syntax) : Json :=
  Json.mkObj [
    ("kind", toJson source.getKind.toString), ("range", sourceRange source),
    ("ident", if source.isIdent then toJson source.getId.toString else .null),
    ("atom", if source.isAtom then toJson source.getAtomVal else .null),
    ("args", toJson (source.getArgs.map signatureSyntax))]

private def valueApplication (native : Syntax) : Json := Id.run do
  unless native.isOfKind ``Lean.Parser.Command.definition &&
      native[3].isOfKind ``Lean.Parser.Command.declValSimple do return .null
  let value := native[3][1]
  unless value.isOfKind ``Lean.Parser.Term.app do return .null
  return Json.mkObj [
    ("range", sourceRange value), ("functionRange", sourceRange value[0]),
    ("arguments", toJson (value[1].getArgs.map fun arg => Json.mkObj [
      ("kind", toJson arg.getKind.toString), ("range", sourceRange arg)]))]

private def declaration (source : Syntax) : Json := Id.run do
  let kind := source.getKind
  let mapped := #[
    `PS0.StandardAdapters.ps0StandardDef, `PS0.StandardAdapters.ps0StandardAbbrev,
    `PS0.StandardAdapters.ps0StandardTheorem, `PS0.StandardAdapters.ps0StandardOpaque,
    `PS0.StandardAdapters.ps0StandardAxiom, `PS0.StandardAdapters.ps0StandardFunction,
    `PS0.StandardAdapters.ps0StandardConst]
  if mapped.contains kind then
    return Json.mkObj [
      ("mode", toJson ("mapped-ps" : String)), ("production", toJson kind.toString),
      ("sourceName", toJson source[2][0].getId.toString),
      ("keywordRange", sourceRange source[1]), ("nameRange", sourceRange source[2]),
      ("signatureRange", sourceRange source[3]), ("signatureSyntax", signatureSyntax source[3])]
  if source.isOfKind ``Lean.Parser.Command.declaration then
    let native := source[1]
    let supported := #[``Lean.Parser.Command.definition, ``Lean.Parser.Command.abbrev,
      ``Lean.Parser.Command.theorem, ``Lean.Parser.Command.opaque, ``Lean.Parser.Command.axiom]
    if supported.contains native.getKind then
      return Json.mkObj [
        ("mode", toJson ("native-compatible" : String)),
        ("production", toJson native.getKind.toString),
        ("sourceName", toJson native[1][0].getId.toString),
        ("keywordRange", sourceRange native[0]), ("nameRange", sourceRange native[1]),
        ("signatureRange", sourceRange native[2]), ("signatureSyntax", signatureSyntax native[2]),
        ("valueApplication", valueApplication native)]
  return .null

private partial def command (source : Syntax) : Json :=
  let viewed := if source.isOfKind `ps0NativeCommandBridge then source[0] else source
  let nested := if viewed.isOfKind ``Lean.Parser.Command.«in» then #[viewed[2]] else
    if viewed.isOfKind ``Lean.Parser.Command.«mutual» then viewed[1].getArgs else #[]
  Json.mkObj [
    ("kind", toJson source.getKind.toString), ("range", sourceRange source),
    ("headKind", toJson (if viewed.isOfKind ``Lean.Parser.Command.declaration then
      viewed[1].getKind.toString else viewed.getKind.toString)),
    ("declaration", declaration viewed),
    ("nestedCommands", toJson (nested.map command))]

def collect (commands : Array Syntax) : CommandElabM Unit := do
  let output := (← getOptions).get `ps0.sourceCensusPath ("" : String)
  unless output.isEmpty do
    let context ← read
    let env ← getEnv
    let locals ← env.getLocalConstantInfos
    let imports := env.header.imports.map (fun (i : Import) => i.module.toString)
    let names := locals.map (fun (c : AsyncConstantInfo) => c.toConstantInfo.name.toString)
      |>.qsort (· < ·)
    let data := Json.mkObj [
      ("schema", toJson ("ps0-native-source-census/1" : String)),
      ("leanCommit", toJson Lean.githash), ("module", toJson (← getMainModule).toString),
      ("file", toJson context.fileName), ("nativeSource", toJson context.fileMap.source),
      ("commands", toJson (commands.map command)),
      ("imports", toJson imports),
      ("environmentDeclNames", toJson names),
      ("grammarMigrationComplete", toJson false)]
    IO.FS.writeFile output data.compress

builtin_initialize
  addModuleLinter { name := `PS0.SourceCensus.collect, run := collect }

end PS0.SourceCensus
