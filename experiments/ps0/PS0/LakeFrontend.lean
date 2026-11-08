/-
Copyright (c) 2026 Dwijayuda. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
import Lean
import Lean.Elab.Frontend
import Lean.Elab.Import
import Lean.Compiler.LCNF.EmitC

/-! Source-kind adaptation for Lean's ordinary Lake module compilation protocol. -/

open Lean System
namespace PS0.LakeFrontend

def parseHeader (raw filename : String) :
    IO (Except String (Elab.HeaderSyntax × Parser.ModuleParserState × Nat)) := do
  let (header, state, messages) ← Parser.parseHeader (Parser.mkInputContext raw filename)
  if Elab.HeaderSyntax.isModule header then
    if messages.hasErrors then return .error "PS0-MODULE-HEADER: invalid import header"
    return .ok (header, state, 0)
  let modulePrefix := "module\n"
  let (header, state, messages) ← Parser.parseHeader (Parser.mkInputContext (modulePrefix ++ raw) filename)
  if messages.hasErrors then return .error "PS0-MODULE-HEADER: invalid implicit module header"
  return .ok (header, state, modulePrefix.utf8ByteSize)

def sourceImportsAndBody (raw filename : String) : IO (Except String (Array Import × String)) := do
  let (header, state, prefixBytes) ← match ← parseHeader raw filename with
    | .ok x => pure x
    | .error e => return .error e
  if state.pos.byteIdx < prefixBytes then return .error "PS0-MODULE-HEADER: invalid source offset"
  let some body := (raw.toByteArray.extract (state.pos.byteIdx - prefixBytes) raw.utf8ByteSize).utf8Decode?
    | return .error "PS0-MODULE-HEADER: invalid UTF-8 boundary"
  return .ok (Elab.HeaderSyntax.imports header (includeInit := false), String.ofList body.toList)

def isPrelude (header : Elab.HeaderSyntax) : Bool :=
  match header with
  | `(Parser.Module.header| $[module%$_]? $[prelude%$p]? $_imports*) => p.isSome
  | _ => false

def importSource (im : Import) : String :=
  (if im.isExported then "public " else "") ++ (if im.isMeta then "meta " else "") ++
  "import " ++ (if im.importAll then "all " else "") ++ im.module.toString ++ "\n"

def prepare (raw filename : String) : IO (Except String String) := do
  let (header, _, prefixBytes) ← match ← parseHeader raw filename with
    | .ok x => pure x
    | .error e => return .error e
  -- Native bootstrap modules retain their own substrate; no hidden Init or PS0 import.
  if isPrelude header then return .ok raw
  let (imports, body) ← match ← sourceImportsAndBody raw filename with
    | .ok x => pure x
    | .error e => return .error e
  return .ok ("module\npublic import PS0.Policy\n" ++
    String.join (imports.toList.map importSource) ++
    (if prefixBytes == 0 then "" else "public section\n") ++
    "open scoped PS0.StandardAdapters\n" ++ body ++ "\n#ps0_evidence\n")

def printHeader (path : String) : IO UInt32 := do
  let raw ← IO.FS.readFile path
  let source ← match ← prepare raw path with
    | .ok x => pure x
    | .error e => IO.eprintln e; return 1
  let header ← Lean.parseImports' source path
  IO.println (toJson header).compress
  return 0

def compile (args : List String) : IO UInt32 := do
  let mut source? : Option String := none
  let mut setup? : Option FilePath := none
  let mut olean? : Option FilePath := none
  let mut ilean? : Option FilePath := none
  let mut c? : Option FilePath := none
  let mut json := false
  let mut requireMain := false
  let mut rest := args
  while !rest.isEmpty do
    match rest with
    | "--setup" :: p :: tail => setup? := some p; rest := tail
    | "-o" :: p :: tail => olean? := some p; rest := tail
    | "-i" :: p :: tail => ilean? := some p; rest := tail
    | "-c" :: p :: tail => c? := some p; rest := tail
    | "--json" :: tail => json := true; rest := tail
    | "--ps0-entry" :: tail => requireMain := true; rest := tail
    | p :: tail =>
        unless p.endsWith ".ps" && source?.isNone do
          IO.eprintln s!"PS0-LAKE-ARG: unsupported module invocation argument {p}"
          return 2
        source? := some p
        rest := tail
    | [] => pure ()
  let some path := source? | IO.eprintln "PS0-LAKE-INPUT: missing .ps source"; return 2
  let some setupFile := setup? | IO.eprintln "PS0-LAKE-SETUP: missing native module setup"; return 2
  let setup ← ModuleSetup.load setupFile
  let raw ← IO.FS.readFile path
  let source ← match ← prepare raw path with
    | .ok x => pure x
    | .error e => IO.eprintln e; return 1
  initSearchPath (← findSysroot)
  unsafe enableInitializersExecution
  let nativePrelude := source == raw
  let opts := if nativePrelude then ({} : Options) else
    ({} : Options) |>.setBool `experimental.vcgen true |>.setBool `experimental.intrinsic true
  let some env ← Elab.runFrontend source opts path setup.name
      (trustLevel := 0) (oleanFileName? := olean?) (ileanFileName? := ilean?)
      (jsonOutput := json) (setup? := some setup)
    | return 1
  if let some c := c? then
    if requireMain then
      let localCode ← Compiler.LCNF.getLocalImpureDecls
        |>.toIO' {fileName := path, fileMap := default} {env}
      unless localCode.contains `main do
        IO.eprintln "PS0-NATIVE-MAIN: executable entry module must compile its own main"
        return 1
    let code ← Compiler.LCNF.emitC setup.name |>.toIO' {fileName := path, fileMap := default} {env}
    IO.FS.writeFile c code
  return 0

/-- Preserve native bodies while making a legacy header explicit in PS0's modern module model. -/
def convertNative (source target : FilePath) : IO Unit := do
  let raw ← IO.FS.readFile source
  let (header, state, messages) ← Parser.parseHeader (Parser.mkInputContext raw source.toString)
  if messages.hasErrors then throw <| IO.userError s!"PS0-CONVERT-HEADER: {source}"
  let converted ← if isPrelude header then pure raw else do
    let some body := (raw.toByteArray.extract state.pos.byteIdx raw.utf8ByteSize).utf8Decode?
      | throw <| IO.userError "PS0-CONVERT-UTF8"
    let first := header.raw.getPos?.getD ⟨0⟩
    let leading := String.fromUTF8! (raw.toByteArray.extract 0 first.byteIdx)
    let imports := Elab.HeaderSyntax.imports header (includeInit := true)
    let rendered := imports.toList.map fun im =>
      if im.importAll && im.isExported then
        importSource {im with importAll := false} ++ importSource {im with isExported := false}
      else importSource im
    pure (leading ++ "module\nprelude\n" ++ String.join rendered ++
      (if Elab.HeaderSyntax.isModule header then "" else "public section\n") ++ String.ofList body.toList)
  IO.FS.createDirAll (target.parent.getD ".")
  IO.FS.writeFile target converted

def convertTree (source target : FilePath) : IO UInt32 := do
  let files ← source.walkDir
  let mut count := 0
  for file in files do
    if file.extension == some "lean" then
      let relative := file.toString.drop (source.toString.length + 1) |>.toString
      convertNative file (target / (FilePath.mk relative).withExtension "ps")
      count := count + 1
  IO.println s!"PS0_NATIVE_SOURCE_CONVERSION: {count} modules"
  return 0

end PS0.LakeFrontend
