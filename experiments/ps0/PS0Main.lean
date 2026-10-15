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

/-- v7 .ps source implicitly has an official Lean module header. The
    synthetic header is parser input only, never user-authored .ps text.
    Its byte length must be removed from the parsed command-body offset. -/
private def psModulePrefix : String := "module\n"

/-- Use exactly the pinned native Lean header parser, but in module mode.
    A literal source 'module' header is not valid v7 .ps; public imports
    are valid source syntax even though source-public body exposure is
    still not implemented for compiled PS0 modules. -/
private def parsePsModuleHeader (src filename : String) :
    IO (Except String (Lean.Elab.HeaderSyntax × Parser.ModuleParserState)) := do
  let original := Parser.mkInputContext src filename
  let (sourceHeader, _, _) ← Parser.parseHeader original
  if Lean.Elab.HeaderSyntax.isModule sourceHeader then
    return .error "PSCV0-MODULE-EXPLICIT-HEADER: .ps source modules are implicit"
  let injected := Parser.mkInputContext (psModulePrefix ++ src) filename
  let (header, state, diagnostics) ← Parser.parseHeader injected
  if diagnostics.hasErrors then
    return .error "PSCV0-MODULE-HEADER-MALFORMED: invalid selected .ps header"
  return .ok (header, state)

/-- Only named upstream modules in the pinned PSCV0 Standard snapshot
    may enter the runtime and syntax environment. -/
private def approvedSource (src filename : String) :
    IO (Except String (Array Import × String)) := do
  let (header, state) ← match ← parsePsModuleHeader src filename with
    | .ok answer => pure answer
    | .error why => return .error why
  match header with
  | `(Parser.Module.header| $[module%$_]? $[prelude%$preludeTk]? $importStx*) =>
    if preludeTk.isSome then
      return .error "PSCV0-MODULE-PRELUDE-REFUSED: source cannot bypass selected Standard"
    for imp in importStx do
      match imp with
      | `(Parser.Module.import| $[public%$publicTk]? $[meta%$metaTk]? import $[all%$allTk]? $name) =>
        if publicTk.isSome then
          return .error "PSCV0-MODULE-PUBLIC-IMPORT-PENDING: source-public name/body policy is not implemented"
        if metaTk.isSome then
          return .error s!"PSCV0-ENV-META-IMPORT-REFUSED: {name.getId}"
        if allTk.isSome then
          return .error s!"PSCV0-ENV-IMPORT-ALL-REFUSED: {name.getId}"
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
  let inputEnd := state.pos.byteIdx - psModulePrefix.utf8ByteSize
  let bytes := src.toByteArray.extract inputEnd src.utf8ByteSize
  let some body := bytes.utf8Decode?
    | return .error "invalid UTF-8 boundary at PSCV0 import header"
  return .ok (imports, String.ofList body.toList)

/-- First PS0-03 primitive: inspect *Lean's actual parsed module header*
    without authorizing its use as a v7 checked source. This preserves
    isModule/isExported/isMeta/importAll identities instead of inferring them
    by searching header text. The eventual project compiler must still enforce
    default-public names and non-exposed bodies before emitting any artifacts.
    Native .lean continues through an unrestricted external Lean process. -/
private def inspectModuleHeader (path : String) : IO UInt32 := do
  unless path.endsWith ".ps" do
    IO.eprintln "PS0-MODULE-INFO: expects a .ps file"
    return 2
  let source ← IO.FS.readFile path
  let header ← match ← parsePsModuleHeader source path with
    | .ok answer => pure answer.1
    | .error why => IO.eprintln why; return 1
  let modules := Lean.Elab.HeaderSyntax.imports header (includeInit := false)
  let entries : List Json := modules.toList.map fun item =>
    Json.mkObj [
      ("module", toJson item.module.toString),
      ("public", toJson item.isExported),
      ("meta", toJson item.isMeta),
      ("all", toJson item.importAll)
    ]
  let result := Json.mkObj [
    ("schema", toJson ("ps0-source-module-header/1" : String)),
    ("source", toJson path),
    ("is_module", toJson (Lean.Elab.HeaderSyntax.isModule header)),
    ("implicit_module", toJson true),
    ("imports", toJson entries),
    ("compile_ready", toJson false)
  ]
  IO.println result.pretty
  return 0

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

/-- Run ordinary .lean with the official external Lean executable, not through
PS0.Policy or PS0.Syntax. An OS child process gives Lean its unmodified parser,
tactics, attributes, source imports, and usual unsafe/partial/axiom/sorry rules.
This output is native Lean, never a PSCV0 verified-source certificate. -/
private def runUnrestrictedLean (argv : List String) : IO UInt32 := do
  -- Resolve Lean from the installed sysroot, never a different binary on PATH.
  let executable := if System.Platform.isWindows then "lean.exe" else "lean"
  let native := (← findSysroot) / "bin" / executable
  let result ← IO.Process.output { cmd := native.toString, args := argv.toArray }
  IO.print result.stdout
  IO.eprint result.stderr
  return result.exitCode

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
  -- The final bundle directory is published with one same-filesystem
  -- directory rename. Lean may write .olean before later C emission fails;
  -- neither file becomes visible in the requested output on such a failure.
  -- Refuse replacement of an existing published bundle.
  let out := System.FilePath.mk outputDir
  if ← out.pathExists then
    IO.eprintln s!"PS0-OUTPUT-EXISTS: refusing to replace {out}"
    return 2
  let parent := out.parent.getD "."
  IO.FS.createDirAll parent
  let nonce ← IO.monoMsNow
  let stage := parent / s!".ps0-stage-{moduleName}-{nonce}"
  IO.FS.createDir stage
  try
    let moduleId := Name.mkSimple moduleName
    let stagedOlean := stage / s!"{moduleName}.olean"
    let stagedC := stage / s!"{moduleName}.c"
    -- One authoritative Lean elaboration and policy gate for both outputs.
    let env? ← Elab.runFrontend src options path moduleId
      (trustLevel := 0) (oleanFileName? := some stagedOlean)
    let some env := env?
      | IO.eprintln "PS0-NATIVE-ELAB: Lean frontend or source policy refused emission"
        return 1
    let cText ← Compiler.LCNF.emitC moduleId
      |>.toIO' { fileName := path, fileMap := default } { env }
    IO.FS.writeFile stagedC cText
    if !(← stagedOlean.pathExists) || !(← stagedC.pathExists) then
      IO.eprintln "PS0-NATIVE-ARTIFACT-MISSING"
      return 1
    -- stage and final output are siblings, so the directory rename is
    -- atomic on the same filesystem. No verified-executable claim is made.
    IO.FS.rename stage out
    IO.println s!"PS0 native bundle (UNCERTIFIED): {out}"
    return 0
  finally
    if ← stage.pathExists then
      IO.FS.removeDirAll stage

/-- Compile an ordinary .lean module using the *native external Lean
process*. Do not inject #pscv_gate, PS0.Policy or v7 parser restrictions.
The native output is not a PSCV0 certificate. -/
private def buildUnrestrictedLean (path moduleName outputDir : String) : IO UInt32 := do
  unless path.endsWith ".lean" do
    IO.eprintln "PS0-LEAN-INPUT: expected .lean"
    return 2
  unless validModuleName moduleName do
    IO.eprintln "PS0-LEAN-MODULE: invalid native module name"
    return 2
  let out := System.FilePath.mk outputDir
  if ← out.pathExists then
    IO.eprintln s!"PS0-OUTPUT-EXISTS: refusing to replace {out}"
    return 2
  let parent := out.parent.getD "."
  IO.FS.createDirAll parent
  -- Host output safety is not a restriction on Lean source. Use a sibling
  -- path so successful publication stays on the same filesystem.
  let nonce ← IO.monoMsNow
  let stage := parent / s!".ps0-lean-stage-{moduleName}-{nonce}"
  IO.FS.createDir stage
  try
    let olean := stage / s!"{moduleName}.olean"
    let c := stage / s!"{moduleName}.c"
    let status ← runUnrestrictedLean
      ["-o", olean.toString, "-c", c.toString, path]
    if status != 0 then return status
    if !(← olean.pathExists) || !(← c.pathExists) then
      IO.eprintln "PS0-LEAN-NATIVE-ARTIFACT-MISSING"
      return 1
    IO.FS.rename stage out
    IO.println s!"PS0 native Lean bundle (ordinary Lean semantics): {out}"
    return 0
  finally
    if ← stage.pathExists then
      IO.FS.removeDirAll stage

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
    | ["module-header", path] => inspectModuleHeader path
    | "lean" :: nativeArgs => runUnrestrictedLean nativeArgs
    | ["check", path] =>
        if path.endsWith ".lean" then
          runUnrestrictedLean [path]
        else
          checkFile path
    | ["build", path, moduleName, outputDir] =>
        if path.endsWith ".lean" then
          buildUnrestrictedLean path moduleName outputDir
        else
          buildFile path moduleName outputDir
    | ["syntax-kinds", path] => syntaxKinds path
    | _ =>
        IO.eprintln "usage: ps0 {environment|module-header FILE.ps|check FILE.ps/FILE.lean|build FILE.ps/FILE.lean ModuleName OUT_DIR|syntax-kinds FILE.ps|lean [native Lean arguments...]}"
        return 2
  catch ex =>
    IO.eprintln s!"PSCV0 error: {ex}"
    return 1

end PS0

def main (args : List String) : IO UInt32 := PS0.cli args
