/-
Copyright (c) 2026 Dwijayuda. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
import Lake
open Lake DSL System Lean

package ps0 where
  version := v!"0.2.0"

lean_lib PS0

@[default_target]
lean_exe ps0 where
  root := `PS0Main
  supportInterpreter := true

-- The fixture library also demonstrates ordinary Lake-managed Lean imports.
lean_lib PS0NativeSupport where
  srcDir := FilePath.mk ((get_config? supportDir).getD "tests/native")

def psSource : FilePath := FilePath.mk ((get_config? source).getD "tests/native/Main.ps")
def psModule : String := (get_config? ps0Module).getD "NativeMain"

def nativeDir (pkg : Package) : FilePath := pkg.buildDir / "ps0-native" / psModule

def validPsModule : Bool :=
  let letter (c : Char) := ('a' ≤ c && c ≤ 'z') || ('A' ≤ c && c ≤ 'Z') || c == '_'
  match psModule.toList with
  | [] => false
  | c :: cs => letter c && cs.all (fun c => letter c || ('0' ≤ c && c ≤ '9'))

def psImportInfo (compiler : FilePath) : FetchM (Job ModuleLinkInfo) := do
  unless validPsModule && psSource.extension == some "ps" do
    error "PS0-NATIVE-INPUT: expected a .ps file and a simple ASCII module identifier"
  let result ← IO.Process.output {
    cmd := compiler.toString
    args := #["module-header", psSource.toString]
    env := (← getWorkspace).augmentedEnvVars
  }
  unless result.exitCode == 0 do
    error s!"PS0-NATIVE-HEADER: {result.stdout}{result.stderr}"
  let header ← match Json.parse result.stdout with
    | .ok v => pure v
    | .error e => error s!"PS0-NATIVE-HEADER: {e}"
  let imports ← match header.getObjValAs? (Array Json) "imports" with
    | .ok v => pure v
    | .error e => error s!"PS0-NATIVE-HEADER: {e}"
  let mut names := #[`PS0.Policy]
  for entry in imports do
    let name ← match entry.getObjValAs? String "module" with
      | .ok v => pure v.toName
      | .error e => error s!"PS0-NATIVE-HEADER: {e}"
    unless names.contains name do names := names.push name
  let mut jobs := #[]
  for name in names do
    if let some mod ← findModule? name then
      jobs := jobs.push (← mod.linkInfoNoExport.fetch)
  (Job.collectArray jobs "ps0 imports").mapM fun infos => do
    let mut result : ModuleLinkInfo := {objs := #[], libs := #[], args := #[]}
    for info in infos do
      for obj in info.objs do
        unless result.objs.contains obj do
          result := {result with objs := result.objs.push obj}
      for lib in info.libs do
        unless result.libs.any (·.name == lib.name) do
          result := {result with libs := result.libs.push lib}
      result := {result with args := result.args ++ info.args}
    return result

target nativeC pkg : FilePath := do
  let some exe := pkg.findLeanExe? `ps0
    | error "PS0-NATIVE-PROJECT: missing ps0 executable target"
  let compilerJob ← exe.exe.fetch
  let compiler ← compilerJob.await
  let sourceJob ← inputBinFile psSource
  let importsJob ← psImportInfo compiler
  let deps := (compilerJob.mix sourceJob).mix importsJob
  let cFile := nativeDir pkg / s!"{psModule}.c"
  let env := (← getWorkspace).augmentedEnvVars
  buildFileAfterDep cFile deps (fun _ => do
    let stage := nativeDir pkg / s!"emit-{← IO.monoMsNow}"
    try
      proc {
        cmd := compiler.toString
        args := #["build-executable-module", psSource.toString, psModule, stage.toString]
        env := env
      }
      for entry in ← stage.readDir do
        IO.FS.rename entry.path (nativeDir pkg / entry.fileName)
    finally
      if ← stage.pathExists then IO.FS.removeDirAll stage)
    (extraDepTrace := do
      addLeanTrace
      addPureTrace (psSource.toString, psModule, "ps0-native-c/1") "PS0 source identity"
      return ← getTrace)

target nativeO pkg : FilePath := do
  buildLeanO (nativeDir pkg / s!"{psModule}.o") (← nativeC.fetch)
    (traceArgs := #["-O3", "-DNDEBUG"])

target app pkg : FilePath := do
  let some exe := pkg.findLeanExe? `ps0
    | error "PS0-NATIVE-PROJECT: missing ps0 executable target"
  let compiler ← (← exe.exe.fetch).await
  let imports ← psImportInfo compiler
  let obj ← nativeO.fetch
  let out := pkg.binDir / FilePath.addExtension psModule FilePath.exeExtension
  imports.bindM (sync := true) fun info =>
    obj.mapM fun obj =>
      buildLeanExeSync out (#[obj] ++ info.objs) info.libs info.args
