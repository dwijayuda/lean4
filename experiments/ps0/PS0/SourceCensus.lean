/-
Copyright (c) 2026 Dwijayuda. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
module
public import Lean
public import PS0.OperatorDescriptors
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

private partial def signatureSyntax (operators : Array Name) (source : Syntax) : Json :=
  Json.mkObj [
    ("kind", toJson source.getKind.toString), ("range", sourceRange source),
    ("ident", if source.isIdent then toJson source.getId.toString else .null),
    ("atom", if source.isAtom then toJson source.getAtomVal else .null),
    ("nativeBinaryOperator", toJson (operators.contains source.getKind)),
    ("args", toJson (source.getArgs.map (signatureSyntax operators)))]

private def application (value : Syntax) : Json := Id.run do
  unless value.isOfKind ``Lean.Parser.Term.app do return .null
  return Json.mkObj [
    ("range", sourceRange value), ("functionRange", sourceRange value[0]),
    ("arguments", toJson (value[1].getArgs.map fun arg => Json.mkObj [
      ("kind", toJson arg.getKind.toString), ("range", sourceRange arg)]))]

private def valueApplication (native : Syntax) : Json := Id.run do
  unless native.isOfKind ``Lean.Parser.Command.definition &&
      native[3].isOfKind ``Lean.Parser.Command.declValSimple do return .null
  return application native[3][1]

private def lambdaBodyApplications (native : Syntax) : Array Json := Id.run do
  unless native.isOfKind ``Lean.Parser.Command.definition &&
      native[3].isOfKind ``Lean.Parser.Command.declValSimple do return #[]
  let value := native[3][1]
  unless value.isOfKind ``Lean.Parser.Term.app do return #[]
  let mut result := #[]
  for arg in value[1].getArgs do
    let body := if arg.isOfKind ``Lean.Parser.Term.paren then arg[1] else arg
    if body.isOfKind ``Lean.Parser.Term.fun && body[1].isOfKind ``Lean.Parser.Term.basicFun then
      match application body[1][3] with
      | .null => pure ()
      | call => result := result.push call
  return result

private partial def ownedOperators (source : Syntax) : Array Name := Id.run do
  if source.isOfKind `PS0.Operators.ownedBinary then
    return #[source[0].getKind] ++ ownedOperators source[0][0] ++ ownedOperators source[0][2]
  let containers := #[`null, `ps0HostAdjacentCall, `ps0HostHeadTerm, `ps0HeadCall,
    `ps0HeadEmptyCall, `ps0ParenthesizedHead, `ps0HostParens, `ps0HostBraces,
    `ps0PositionalArg, `ps0NamedArg, `ps0HostLambda]
  unless containers.contains source.getKind do return #[]
  return source.getArgs.foldl (fun kinds arg => kinds ++ ownedOperators arg) #[]

private def declaration (operators : Array Name) (source : Syntax) : Json := Id.run do
  let kind := source.getKind
  let mapped := #[
    `PS0.StandardAdapters.ps0StandardDef, `PS0.StandardAdapters.ps0StandardAbbrev,
    `PS0.StandardAdapters.ps0StandardTheorem, `PS0.StandardAdapters.ps0StandardOpaque,
    `PS0.StandardAdapters.ps0StandardAxiom, `PS0.StandardAdapters.ps0StandardFunction,
    `PS0.StandardAdapters.ps0StandardConst]
  if mapped.contains kind then
    let hasTail := #[`PS0.StandardAdapters.ps0StandardDef, `PS0.StandardAdapters.ps0StandardAbbrev,
      `PS0.StandardAdapters.ps0StandardTheorem, `PS0.StandardAdapters.ps0StandardFunction,
      `PS0.StandardAdapters.ps0StandardConst].contains kind
    let declValue := if hasTail then source.getArgs.back! else Syntax.missing
    let value := if declValue.isOfKind `PS0.StandardAdapters.ps0DeclSimple then declValue[1] else Syntax.missing
    let tail := if hasTail then declValue.getArgs.back![0] else Syntax.missing
    let equationBodies := if declValue.isOfKind `PS0.StandardAdapters.ps0DeclEqns then
      declValue[0][0].getArgs.map (fun alt => alt[3].getKind.toString) else #[]
    return Json.mkObj [
      ("mode", toJson ("mapped-ps" : String)), ("production", toJson kind.toString),
      ("sourceName", toJson source[2][0].getId.toString),
      ("keywordRange", sourceRange source[1]), ("nameRange", sourceRange source[2]),
      ("signatureRange", sourceRange source[3]), ("signatureSyntax", signatureSyntax operators source[3]),
      ("valueRootKind", toJson value.getKind.toString),
      ("ownedValueCall", toJson (value.isOfKind `ps0HostAdjacentCall ||
        (value.isOfKind `ps0HostHeadTerm && value[0].isOfKind `ps0HeadCall))),
      ("ownedOperatorKinds", toJson ((ownedOperators value).map Name.toString)),
      ("declarationValueKind", toJson declValue.getKind.toString),
      ("equationBodyKinds", toJson equationBodies),
      ("nativeWhereTail", toJson (hasTail && tail[1].getArgs.any (·.isOfKind ``Lean.Parser.Term.whereDecls)))]
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
        ("signatureRange", sourceRange native[2]), ("signatureSyntax", signatureSyntax operators native[2]),
        ("valueSyntax", signatureSyntax operators native[3]),
        ("valueApplication", valueApplication native),
        ("lambdaBodyApplications", toJson (lambdaBodyApplications native))]
  return .null

private partial def command (operators : Array Name) (source : Syntax) : Json :=
  let viewed := if source.isOfKind `ps0NativeCommandBridge then source[0] else source
  let nested := if viewed.isOfKind ``Lean.Parser.Command.«in» then #[viewed[2]] else
    if viewed.isOfKind ``Lean.Parser.Command.«mutual» then viewed[1].getArgs else #[]
  Json.mkObj [
    ("kind", toJson source.getKind.toString), ("range", sourceRange source),
    ("headKind", toJson (if viewed.isOfKind ``Lean.Parser.Command.declaration then
      viewed[1].getKind.toString else viewed.getKind.toString)),
    ("declaration", declaration operators viewed),
    ("nestedCommands", toJson (nested.map (command operators)))]

def collect (commands : Array Syntax) : CommandElabM Unit := do
  let output := (← getOptions).get `ps0.sourceCensusPath ("" : String)
  unless output.isEmpty do
    let context ← read
    let env ← getEnv
    let operators := PS0.OperatorDescriptors.binaryKinds env (← getOptions)
    let locals ← env.getLocalConstantInfos
    let imports := env.header.imports.map (fun (i : Import) => i.module.toString)
    let names := locals.map (fun (c : AsyncConstantInfo) => c.toConstantInfo.name.toString)
      |>.qsort (· < ·)
    let data := Json.mkObj [
      ("schema", toJson ("ps0-native-source-census/1" : String)),
      ("leanCommit", toJson Lean.githash), ("module", toJson (← getMainModule).toString),
      ("file", toJson context.fileName), ("nativeSource", toJson context.fileMap.source),
      ("commands", toJson (commands.map (command operators))),
      ("imports", toJson imports),
      ("environmentDeclNames", toJson names),
      ("grammarMigrationComplete", toJson false)]
    IO.FS.writeFile output data.compress

builtin_initialize
  addModuleLinter { name := `PS0.SourceCensus.collect, run := collect }

end PS0.SourceCensus
