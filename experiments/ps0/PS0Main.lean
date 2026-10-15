import Lean
import Lean.Elab.Frontend
import Lean.Elab.Import
import Lean.Compiler.LCNF.EmitC
import PS0.Grammar
import PS0.Policy
import PS0.StandardEnv

/-!
PS0 standalone Lean-native frontend. Lean performs all declaration elaboration, proof
checking, compiler lowering and C emission. No alternative typechecker.
-/

open Lean

namespace PS0

-- The imported PS0-owned modules are the only ProofScript frontend authority.

private def options : Options :=
  ({} : Options)
    |>.setBool `experimental.vcgen true
    |>.setBool `experimental.intrinsic true

/-- Only named upstream modules in the pinned PSCV0 Standard snapshot
    may enter the runtime and syntax environment. -/
private def approvedSource (src filename : String) :
    IO (Except String (Array Import × String)) := do
  let inputCtx := Parser.mkInputContext src filename
  let (header, state, messages) ← Parser.parseHeader inputCtx
  if messages.hasErrors then
    return .error "invalid Lean import header"
  if Lean.Elab.HeaderSyntax.isModule header then
    return .error "PSCV0-MODULE-HEADER-PENDING: v7 module exposure not implemented"
  -- A source-level public import needs v7's explicit module/public exposure
  -- translation. Lean treats all imports in legacy modules as exported, so
  -- inspecting Import.isExported alone cannot distinguish the written forms.
  match header with
  | `(Parser.Module.header| $[module%$moduleTk]? $[prelude%$preludeTk]? $importStx*) =>
    for imp in importStx do
      match imp with
      | `(Parser.Module.import| $[public%$publicTk]? $[meta%$metaTk]? import $[all%$allTk]? $name) =>
        if publicTk.isSome then
          return .error "PSCV0-MODULE-PUBLIC-IMPORT-PENDING"
      | _ => return .error "PSCV0-MODULE-IMPORT-HEADER-UNSUPPORTED"
  | _ => return .error "PSCV0-MODULE-IMPORT-HEADER-UNSUPPORTED"
  let imports := Lean.Elab.HeaderSyntax.imports header (includeInit := false)
  for imported in imports do
    if imported.isMeta then
      return .error s!"PSCV0-ENV-META-IMPORT-REFUSED: {imported.module}"
    if imported.importAll then
      return .error s!"PSCV0-ENV-IMPORT-ALL-REFUSED: {imported.module}"
    unless StandardEnv.allowsImport imported.module do
      return .error s!"PSCV0-ENV-UNAPPROVED-IMPORT: {imported.module}"
  let bytes := src.toByteArray.extract state.pos.byteIdx src.utf8ByteSize
  let some body := bytes.utf8Decode?
    | return .error "invalid UTF-8 boundary at PSCV0 import header"
  return .ok (imports, String.ofList body.toList)

private def checkSource (path source : String) : IO UInt32 := do
  let (approved, body) ← match ← approvedSource source path with
    | .ok v => pure v
    | .error err => IO.eprintln s!"PSCV0 source-profile error: {err}"; return 1
  initSearchPath (← findSysroot)
  unsafe enableInitializersExecution
  let env ← importModules (#[{ module := `PS0.Policy : Import }] ++ approved) {}
    (trustLevel := 0) (loadExts := true)
  match validateSourceSyntax body path env options with
  | .error msg =>
      IO.eprintln s!"PSCV0 source-profile error: {msg}"
      return 1
  | .ok () => pure ()
  let (_, messages) ← Elab.process (body ++ "\n\n#pscv_gate\n") env options (some path)
  for msg in messages.markAllReported.reported do
    IO.eprintln (← msg.toString)
  if messages.hasErrors then
    IO.eprintln "PSCV0: Lean checking failed; no artifacts emitted"
    return 1
  IO.println "PSCV0: Lean checking passed (UNCERTIFIED)"
  return 0

private def checkFile (path : String) : IO UInt32 := do
  unless path.endsWith ".ps" do
    IO.eprintln "PS0 expects a .ps source file"
    return 2
  let source ← IO.FS.readFile path
  checkSource path source

private def validModuleName (s : String) : Bool :=
  !s.isEmpty && !(s.contains '/') && !(s.contains '.') &&
    !(s.contains '\\') && !(s.contains ' ')

/-- Native build consumes exactly the same .ps bytes that passed preflight.
It uses Lean's official runFrontend and LCNF emitC without an intermediate
textual .lean file. Native codegen does not confer verified-executable status. -/
private def buildFile (path moduleName outputDir : String) : IO UInt32 := do
  unless validModuleName moduleName do
    IO.eprintln "PSCV0 native module name must be a simple identifier"
    return 2
  -- Freeze user-authored source once. No source re-read or duplicate Lean
  -- elaboration is permitted in this single-module native build.
  unless path.endsWith ".ps" do
    IO.eprintln "PS0 expects a .ps source file"
    return 2
  let raw ← IO.FS.readFile path
  -- The build does *one* full Lean elaboration: the same runFrontend that
  -- produces the checked environment also executes #pscv_gate before emission.
  -- Parsing/source-policy admission occurs first but does not create output.
  let (approved, body) ← match ← approvedSource raw path with
    | .ok v => pure v
    | .error err => IO.eprintln s!"PSCV0 source-profile error: {err}"; return 1
  initSearchPath (← findSysroot)
  unsafe enableInitializersExecution
  let sourceEnv ← importModules (#[{ module := `PS0.Policy : Import }] ++ approved) {}
    (trustLevel := 0) (loadExts := true)
  match validateSourceSyntax body path sourceEnv options with
  | .error msg =>
      IO.eprintln s!"PSCV0 source-profile error: {msg}"
      return 1
  | .ok () => pure ()
  let imports := String.join (approved.toList.map fun im => s!"import {im.module}\n")
  let src := "import PS0.Policy\n" ++ imports ++ body ++ "\n\n#pscv_gate\n"
  let out := System.FilePath.mk outputDir
  IO.FS.createDirAll out
  -- No separate source elaboration pass: runFrontend's checked environment
  -- is the sole authority for the subsequently emitted native C.
  let moduleId := Name.mkSimple moduleName
  let oleanPath := out / s!"{moduleName}.olean"
  let cPath := out / s!"{moduleName}.c"
  let env? ← Elab.runFrontend src options path moduleId
    (trustLevel := 0) (oleanFileName? := some oleanPath)
  let some env := env?
    | IO.eprintln "PSCV0 native compilation rejected Lean frontend output"
      return 1
  let cText ← Compiler.LCNF.emitC moduleId
    |>.toIO' { fileName := path, fileMap := default } { env }
  IO.FS.writeFile cPath cText
  IO.println s!"PSCV0 native module ready (UNCERTIFIED): {cPath} and {oleanPath}"
  return 0

private def syntaxKinds (path : String) : IO UInt32 := do
  unless path.endsWith ".ps" do
    IO.eprintln "PS0 expects a .ps source file"
    return 2
  let source ← IO.FS.readFile path
  let (approved, body) ← match ← approvedSource source path with
    | .ok v => pure v
    | .error err => IO.eprintln s!"PSCV0 source-profile error: {err}"; return 1
  initSearchPath (← findSysroot)
  unsafe enableInitializersExecution
  let env ← importModules (#[{ module := `PS0.Policy : Import }] ++ approved) {}
    (trustLevel := 0) (loadExts := true)
  match auditSourceSyntax body path env options with
  | .ok kinds =>
      for kind in kinds do IO.println kind
      return 0
  | .error msg =>
      IO.eprintln s!"PSCV0 source-profile error: {msg}"
      return 1

def cli (args : List String) : IO UInt32 := do
  -- Do not accept an accidental RC4 / nightly / local Lean binary.
  let expected := "eb6cafb7290e8bd5f2937522d8d804f58f02bafc"
  if Lean.githash != expected || PS0.StandardEnv.leanRevision != expected then
    IO.eprintln s!"PS0-LEAN-PIN: expected official Lean 4.35.0 ({expected}); found {Lean.githash}"
    return 2
  try
    match args with
    | ["environment"] => do
        IO.println StandardEnv.manifest.pretty
        return 0
    | ["check", path] => checkFile path
    | ["build", path, moduleName, outputDir] => buildFile path moduleName outputDir
    | ["syntax-kinds", path] => syntaxKinds path
    | _ =>
        IO.eprintln "usage: ps0 {environment|check FILE.ps|build FILE.ps ModuleName OUTPUT_DIR|syntax-kinds FILE.ps}"
        return 2
  catch ex =>
    IO.eprintln s!"PSCV0 error: {ex}"
    return 1

end PS0

def main (args : List String) : IO UInt32 := PS0.cli args
