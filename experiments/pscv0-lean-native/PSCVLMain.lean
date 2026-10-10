import Lean
import Lean.Elab.Frontend
import Lean.Compiler.LCNF.EmitC
import PSCVL.Grammar
import PSCVL.Policy

/-!
PSCV0 Lean-native frontend. Lean performs all declaration elaboration, proof
checking, compiler lowering and C emission. No alternative typechecker.
-/

open Lean

namespace PSCVL

private def options : Options :=
  ({} : Options)
    |>.setBool `experimental.vcgen true
    |>.setBool `experimental.intrinsic true

private def checkFile (path : String) : IO UInt32 := do
  unless path.endsWith ".ps" do
    IO.eprintln "PSCV0 expects a .ps source file"
    return 2
  let source ← IO.FS.readFile path
  initSearchPath (← findSysroot)
  unsafe enableInitializersExecution
  let env ← importModules #[{ module := `PSCVL.Policy }] {} (trustLevel := 0) (loadExts := true)
  match validateSourceSyntax source path env options with
  | .error msg =>
      IO.eprintln s!"PSCV0 source-profile error: {msg}"
      return 1
  | .ok () => pure ()
  let (_, messages) ← Elab.process (source ++ "\n\n#pscv_gate\n") env options (some path)
  for msg in messages.markAllReported.reported do
    IO.eprintln (← msg.toString)
  if messages.hasErrors then
    IO.eprintln "PSCV0: Lean checking failed; no artifacts emitted"
    return 1
  IO.println "PSCV0: Lean checking passed (UNCERTIFIED)"
  return 0

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
  let status ← checkFile path
  if status != 0 then return status
  let raw ← IO.FS.readFile path
  let src := "import PSCVL.Policy\n" ++ raw ++ "\n\n#pscv_gate\n"
  let out := System.FilePath.mk outputDir
  IO.FS.createDirAll out
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
    IO.eprintln "PSCV0 expects a .ps source file"
    return 2
  let source ← IO.FS.readFile path
  initSearchPath (← findSysroot)
  unsafe enableInitializersExecution
  let env ← importModules #[{ module := `PSCVL.Policy }] {} (trustLevel := 0) (loadExts := true)
  match auditSourceSyntax source path env options with
  | .ok kinds =>
      for kind in kinds do IO.println kind
      return 0
  | .error msg =>
      IO.eprintln s!"PSCV0 source-profile error: {msg}"
      return 1

def cli (args : List String) : IO UInt32 := do
  try
    match args with
    | ["check", path] => checkFile path
    | ["build", path, moduleName, outputDir] => buildFile path moduleName outputDir
    | ["syntax-kinds", path] => syntaxKinds path
    | _ =>
        IO.eprintln "usage: psc check FILE.ps | psc build FILE.ps ModuleName OUTPUT_DIR | psc syntax-kinds FILE.ps"
        return 2
  catch ex =>
    IO.eprintln s!"PSCV0 error: {ex}"
    return 1

end PSCVL

def main (args : List String) : IO UInt32 := PSCVL.cli args
