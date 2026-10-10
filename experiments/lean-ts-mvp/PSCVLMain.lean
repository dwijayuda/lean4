import Lean
import Lean.Elab.Frontend
import PSCVL.Grammar
import PSCVL.Policy

/-!
In-process Lean parser, elaborator, and kernel-backed preflight for .ps files.
No translated text, temporary source file, sidecar script, or custom typechecker.
-/

open Lean

namespace PSCVL

private def checkFile (path : String) : IO UInt32 := do
  unless path.endsWith ".ps" do
    IO.eprintln "PSCVL expects a .ps source file"
    return 2
  let source ← IO.FS.readFile path
  initSearchPath (← findSysroot)
  -- Matches the official Lean frontend's initialization sequence.
  unsafe enableInitializersExecution
  let env ← importModules #[{ module := `PSCVL.Policy }] {} (trustLevel := 0) (loadExts := true)
  -- PSCV fixes the experiment options as part of its frontend identity;
  -- user `set_option` commands cannot change them.
  let opts := ({} : Options)
    |>.setBool `experimental.vcgen true
    |>.setBool `experimental.intrinsic true
  match validateSourceSyntax source path env opts with
  | .error msg =>
    IO.eprintln s!"PSCVL source-profile error: {msg}"
    return 1
  | .ok () => pure ()
  -- The gate is injected by the driver, not opt-in source syntax. Append it
  -- only after the user input has been completely parsed/elaborated.
  let checkedSource := source ++ "\n\n#pscv_gate\n"
  let (_, messages) ← Elab.process checkedSource env opts (some path)
  for message in messages.markAllReported.reported do
    IO.eprintln (← message.toString)
  if messages.hasErrors then
    IO.eprintln "PSCVL: preflight FAILED; no artifact emitted"
    return 1
  IO.println "PSCV0: Lean elaboration and preliminary policy check passed (UNCERTIFIED)"
  return 0

/-- Parse-only diagnostic: enumerate all Lean syntax kinds present in
accepted PSCVL source, without invoking source elaborators. -/
private def syntaxKinds (path : String) : IO UInt32 := do
  unless path.endsWith ".ps" do
    IO.eprintln "PSCVL expects a .ps source file"
    return 2
  let source ← IO.FS.readFile path
  initSearchPath (← findSysroot)
  unsafe enableInitializersExecution
  let env ← importModules #[{ module := `PSCVL.Policy }] {} (trustLevel := 0) (loadExts := true)
  let opts := ({} : Options)
    |>.setBool `experimental.vcgen true
    |>.setBool `experimental.intrinsic true
  match auditSourceSyntax source path env opts with
  | .ok kinds =>
    for kind in kinds do
      IO.println kind
    return 0
  | .error msg =>
    IO.eprintln s!"PSCVL source-profile error: {msg}"
    return 1

def cli (args : List String) : IO UInt32 := do
  try
    match args with
    | ["check", path] => checkFile path
    | ["syntax-kinds", path] => syntaxKinds path
    | _ =>
      IO.eprintln "usage: lake exe pscvl {check|syntax-kinds} <source.ps>"
      IO.eprintln "No PSCV certified compilation or executable emission exists in this prototype."
      return 2
  catch e =>
    IO.eprintln s!"PSCVL error: {e}"
    return 1

end PSCVL

def main (args : List String) : IO UInt32 := PSCVL.cli args
