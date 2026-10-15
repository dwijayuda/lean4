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
    return .error "explicit module headers are not yet supported in PSCV0"
  let imports := Lean.Elab.HeaderSyntax.imports header (includeInit := false)
  for imported in imports do
    unless StandardEnv.allowsImport imported.module && !imported.isMeta && !imported.importAll do
      return .error s!"unapproved PSCV0 imported module: {imported.module}"
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
  -- Freeze user-authored source once: check and emit use identical bytes.
  -- A future fully checked session must also bind Lean environment identity.
  unless path.endsWith ".ps" do
    IO.eprintln "PS0 expects a .ps source file"
    return 2
  let raw ← IO.FS.readFile path
  let status ← checkSource path raw
  if status != 0 then return status
  let (approved, body) ← match ← approvedSource raw path with
    | .ok v => pure v
    | .error err => IO.eprintln s!"PSCV0 source-profile error: {err}"; return 1
  let imports := String.join (approved.toList.map fun im => s!"import {im.module}\n")
  let src := "import PS0.Policy\n" ++ imports ++ body ++ "\n\n#pscv_gate\n"
  let out := System.FilePath.mk outputDir
  IO.FS.createDirAll out
  -- The preceding in-process check consumes the importer initialization flag.
  unsafe enableInitializersExecution
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
