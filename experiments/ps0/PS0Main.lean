import Lean
import Lean.Elab.Frontend
import Lean.Elab.Import
import Lean.Compiler.LCNF.EmitC
import PS0.Grammar
import PS0.Policy
import PS0.StandardEnv
import PS0.Backend.Js

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

/-- Preserve the original header's meaning. Headerless .ps source is
    parsed as a modern Lean module with public names by default; a
    written 'module' header follows native modern-module defaults.
    Source provenance tracks the synthetic prefix length, if any. -/
private def parsePsModuleHeader (src filename : String) :
    IO (Except String (Lean.Elab.HeaderSyntax × Parser.ModuleParserState × Nat)) := do
  let original := Parser.mkInputContext src filename
  let (sourceHeader, sourceState, sourceMessages) ← Parser.parseHeader original
  if Lean.Elab.HeaderSyntax.isModule sourceHeader then
    if sourceMessages.hasErrors then
      return .error "PS0V1-MODULE: invalid explicit native module header"
    return .ok (sourceHeader, sourceState, 0)
  let prefix := "module\n"
  let injected := Parser.mkInputContext (prefix ++ src) filename
  let (header, state, diagnostics) ← Parser.parseHeader injected
  if diagnostics.hasErrors then
    return .error "PS0V1-MODULE: invalid implicit module import header"
  return .ok (header, state, prefix.utf8ByteSize)

/-- Import-driven v1 native language, not a finite Standard allowlist.
    Source imports remain subject to the official Lean 4.35.0 header
    semantics, availability and stage/visibility checks. -/
private def approvedSource (src filename : String) :
    IO (Except String (Array Import × String)) := do
  let (header, state, prefixBytes) ← match ← parsePsModuleHeader src filename with
    | .ok answer => pure answer
    | .error why => return .error why
  let imports := Lean.Elab.HeaderSyntax.imports header (includeInit := false)
  if state.pos.byteIdx < prefixBytes then
    return .error "PS0V1-MODULE: invalid source offset after module header"
  let start := state.pos.byteIdx - prefixBytes
  let bytes := src.toByteArray.extract start src.utf8ByteSize
  let some body := bytes.utf8Decode?
    | return .error "PS0V1-MODULE: invalid UTF-8 source boundary"
  return .ok (imports, String.ofList body.toList)

/-- First PS0-03 primitive: inspect *Lean's actual parsed module header*
    without authorizing its use as a v1 checked source. This preserves
    isModule/isExported/isMeta/importAll identities instead of inferring them
    by searching header text. The eventual project compiler must still enforce
    default-public names and non-exposed bodies before emitting any artifacts.
    Native .lean continues through an unrestricted external Lean process. -/
private def inspectModuleHeader (path : String) : IO UInt32 := do
  unless path.endsWith ".ps" do
    IO.eprintln "PS0-MODULE-INFO: expects a .ps file"
    return 2
  let source ← IO.FS.readFile path
  let (header, _, prefixBytes) ← match ← parsePsModuleHeader source path with
    | .ok answer => pure answer
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
    ("implicit_module", toJson (prefixBytes != 0)),
    ("imports", toJson entries),
    ("compile_ready", toJson false)
  ]
  IO.println result.pretty
  return 0

/-- One official elaboration is the authority for both source acceptance
    and checked-runtime export signatures. Do not certify a separate
    independently parsed IR without retaining the accepted Lean environment. -/
private def checkSourceEnvironment (path source : String) :
    IO (Option Environment) := do
  let (approved, body) ← match ← approvedSource source path with
    | .ok v => pure v
    | .error err =>
        IO.eprintln s!"PS0V1 source-profile error: {err}"
        return none
  initSearchPath (← findSysroot)
  unsafe enableInitializersExecution
  let env ← importModules (#[{ module := `PS0.Policy : Import }] ++ approved) {}
    (trustLevel := 0) (loadExts := true)
  -- PS0 v1 grammar can change after each registered syntax/elab command.
  -- Lean's interleaved elaboration is authoritative; a frozen-source
  -- syntax audit cannot decide the full import-driven language.
  let (checked, messages) ← Elab.process (body ++ "\n\n#ps0_evidence\n")
    env options (some path)
  for msg in messages.markAllReported.reported do
    IO.eprintln (← msg.toString)
  if messages.hasErrors then
    IO.eprintln "PS0V1: Lean checking failed; no artifacts emitted"
    return none
  return some checked

private def checkSource (path source : String) : IO UInt32 := do
  let some _ ← checkSourceEnvironment path source
    | return 1
  IO.println "PS0V1: Lean checking passed (UNCERTIFIED)"
  return 0

/-- Run ordinary .lean with the official external Lean executable, not through
PS0.Policy or PS0.Syntax. An OS child process gives Lean its unmodified parser,
tactics, attributes, source imports, and usual unsafe/partial/axiom/sorry rules.
This output is native Lean, never a PS0V1 verified-source certificate. -/
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
    IO.eprintln "PS0V1 native module name must be a simple identifier"
    return 2
  -- Freeze user-authored source once. No source re-read or duplicate Lean
  -- elaboration is permitted in this single-module native build.
  unless path.endsWith ".ps" do
    IO.eprintln "PS0 expects a .ps source file"
    return 2
  let raw ← IO.FS.readFile path
  -- The build does *one* full Lean elaboration: the same runFrontend that
  -- produces the checked environment also executes #ps0_evidence before emission.
  -- Parsing/source-policy admission occurs first but does not create output.
  let (approved, body) ← match ← approvedSource raw path with
    | .ok v => pure v
    | .error err => IO.eprintln s!"PS0V1 source-profile error: {err}"; return 1
  initSearchPath (← findSysroot)
  unsafe enableInitializersExecution
  let sourceEnv ← importModules (#[{ module := `PS0.Policy : Import }] ++ approved) {}
    (trustLevel := 0) (loadExts := true)
  -- Native runFrontend performs the interleaved source parse/elaboration.
  -- Full modern export/expose semantics still require the project graph.
  -- A .ps module's imports are private by default. Re-emitting them in a
  -- legacy Lean header would silently re-export those dependencies, and
  -- v7 also requires public-name/hidden-body checking. Until PS0-03
  -- native module emission is complete, refuse artifacts for source imports.
  -- check / module-header remain available as unqualified analysis modes.
  unless approved.isEmpty do
    IO.eprintln "PS0V1-MODULE-BUILD-PENDING: module-style imports require checked v1 export/body lowering"
    return 1
  let imports := String.join (approved.toList.map fun im => s!"import {im.module}\n")
  let src := "import PS0.Policy\n" ++ imports ++ body ++ "\n\n#ps0_evidence\n"
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

/-- Checked .ps → minimal real JS target. Source is read once; the same
bytes are checked by official Lean (including #ps0_evidence) before selected
runtime declarations lower into typed IR. Unsupported semantics fail closed.
This does NOT certify JS backend semantic preservation or arbitrary v1 code. -/
private def buildJs (path moduleName outputDir : String) : IO UInt32 := do
  unless path.endsWith ".ps" do
    IO.eprintln "PS0-JS-INPUT: expected .ps"
    return 2
  -- The output stem occurs in the sourceMappingURL and file names. Restrict
  -- it to one ASCII JS-safe atom, not arbitrary CLI text or file paths.
  unless validModuleName moduleName && Backend.Js.safePublicName moduleName do
    IO.eprintln "PS0-JS-MODULE: invalid output module name"
    return 2
  let raw ← IO.FS.readFile path
  let (imports, _) ← match ← approvedSource raw path with
    | .ok x => pure x
    | .error e => IO.eprintln s!"PS0-JS-HEADER: {e}"; return 1
  unless imports.isEmpty do
    IO.eprintln "PS0-JS-IMPORTS: module linkage is not yet implemented"
    return 1
  let some checked ← checkSourceEnvironment path raw
    | return 1
  -- Reuse the actual environment that passed Lean checking, rather than
  -- importing a different declaration/assumption environment for emission.
  let env := checked
  -- Parse the ORIGINAL source (not a header-stripped copy) to retain
  -- exact declaration locations, leading trivia and sourcesContent.
  let program ← match Backend.Js.lower path raw env options with
    | .ok p => pure p
    | .error e => IO.eprintln e; return 1
  match Backend.Js.validateCheckedExports checked program with
  | .error e => IO.eprintln e; return 1
  | .ok () => pure ()
  let artifacts := Backend.Js.emit program moduleName
  let out := System.FilePath.mk outputDir
  if ← out.pathExists then
    IO.eprintln s!"PS0-OUTPUT-EXISTS: refusing to replace {out}"
    return 2
  let parent := out.parent.getD "."
  IO.FS.createDirAll parent
  let nonce ← IO.monoMsNow
  let stage := parent / s!".ps0-js-stage-{moduleName}-{nonce}"
  IO.FS.createDir stage
  try
    IO.FS.writeFile (stage / s!"{moduleName}.js") artifacts.js
    IO.FS.writeFile (stage / s!"{moduleName}.d.ts") artifacts.dts
    IO.FS.writeFile (stage / s!"{moduleName}.js.map") artifacts.jsMap
    IO.FS.rename stage out
    IO.println s!"PS0 JS Nat subset emitted (UNCERTIFIED): {out}"
    return 0
  finally
    if ← stage.pathExists then IO.FS.removeDirAll stage

/-- Compile an ordinary .lean module using the *native external Lean
process*. Do not inject #ps0_evidence, PS0.Policy or v1 parser restrictions.
The native output is not a PS0V1 certificate. -/
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
    | .error err => IO.eprintln s!"PS0V1 source-profile error: {err}"; return 1
  initSearchPath (← findSysroot)
  unsafe enableInitializersExecution
  let env ← importModules (#[{ module := `PS0.Policy : Import }] ++ approved) {}
    (trustLevel := 0) (loadExts := true)
  match auditSourceSyntax body path env options with
  | .ok kinds =>
      for kind in kinds do IO.println kind
      return 0
  | .error msg =>
      IO.eprintln s!"PS0V1 source-profile error: {msg}"
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
    | ["build-js", path, moduleName, outputDir] =>
        buildJs path moduleName outputDir
    | ["syntax-kinds", path] => syntaxKinds path
    | _ =>
        IO.eprintln "usage: ps0 {environment|module-header FILE.ps|check FILE.ps/FILE.lean|build FILE.ps/FILE.lean ModuleName OUT_DIR|build-js FILE.ps ModuleName OUT_DIR|syntax-kinds FILE.ps|lean [native Lean arguments...]}"
        return 2
  catch ex =>
    IO.eprintln s!"PS0V1 error: {ex}"
    return 1

end PS0

def main (args : List String) : IO UInt32 := PS0.cli args
