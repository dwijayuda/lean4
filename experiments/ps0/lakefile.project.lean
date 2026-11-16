/-
Copyright (c) 2026 Dwijayuda. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
import Lake
import Lake.Build.Module
import Lean.Setup
open Lake DSL System Lean

package ps0 where
  version := v!"0.2.0"
  bootstrap := (get_config? bootstrap).isSome
  -- Match pinned src/CMakeLists.txt: stage builds must evaluate their current IR,
  -- rather than resolve same-named constants in the running compiler executable.
  leanOptions := (if (get_config? bootstrap).isSome then
    #[⟨`interpreter.prefer_native, false⟩] ++
      (if (get_config? sourceGrammar).isSome then #[⟨`ps0.sourceGrammar, true⟩] else #[])
    else if (get_config? sourceGrammar).isSome then #[⟨`ps0.sourceGrammar, true⟩] else #[]) ++
      (if (get_config? loweredCensus).isSome then #[⟨`ps0.loweredCensus, true⟩] else #[]) ++
      (if (get_config? separateCompiler).isSome then #[⟨`compiler.postponeCompile, true⟩] else #[])
  buildDir := FilePath.mk ((get_config? projectBuildDir).getD ".lake/project")

def projectSource : FilePath := FilePath.mk ((get_config? sourceRoot).getD "tests/project")
def projectRoots : Array Name := (((get_config? roots).getD "Demo,NativeSupport").splitOn ",").toArray.map String.toName
def projectMain : Name := ((get_config? rootModule).getD "Demo.Main").toName
def projectDriver : FilePath := FilePath.mk ((get_config? driver).getD ".lake/build/bin/ps0")

target ps0DriverInput : FilePath := inputBinFile projectDriver

def projectModules : Array Name :=
  (((get_config? moduleNames).getD "").splitOn ",").toArray.filterMap fun (line : String) =>
    if line.isEmpty then none else some line.toName

def canonicalPS0 : Bool := run_io (FilePath.mk "PS0.ps").pathExists

lean_lib PS0 where
  roots := if projectModules.isEmpty then #[`PS0] else #[]
  globs := if projectModules.isEmpty then #[Glob.one `PS0] else #[]
  -- The bundled library is canonical PS even when the user project selects
  -- the ordinary module frontend. Explicit corpus inventories own their roots.
  leanOptions := if projectModules.isEmpty && canonicalPS0 then
    #[⟨`ps0.sourceGrammar, true⟩, ⟨`interpreter.prefer_native, false⟩] else #[]

lean_lib PS0Project where
  srcDir := projectSource
  roots := projectRoots
  globs := (if projectModules.isEmpty then projectRoots else projectModules).map Glob.one

@[default_target]
lean_exe ps0project where
  root := projectMain
  srcDir := projectSource
  supportInterpreter := true
  moreLeanArgs := #["--ps0-entry"]
  moreLinkArgs := match get_config? linkMap with
    | some path => #["-Wl,-Map," ++ path]
    | none => #[]

def ps0Input (mod : Lake.Module) : FetchM (Job ModuleInput) := do
  let path := mod.leanFile.withExtension "ps"
  if !(← path.pathExists) then return ← Lake.Module.inputFacetConfig.run mod
  if ← mod.leanFile.pathExists then error s!"PS0-SOURCE-COLLISION: {path} and {mod.leanFile}"
  if mod.name.toString.contains '/' || mod.name.toString.contains '\\' then
    error "PS0-MODULE-PATH: invalid source module component"
  let driver ← ps0DriverInput.fetch
  driver.mapM fun compiler => do
    addTrace (← computeTrace (TextFilePath.mk path))
    let result ← IO.Process.output {
      cmd := compiler.toString
      args := #["lake-header", path.toString]
      env := (← getWorkspace).augmentedEnvVars
    }
    unless result.exitCode == 0 do error s!"PS0-PROJECT-HEADER: {result.stdout}{result.stderr}"
    let header : ModuleHeader ← match Json.parse result.stdout >>= fromJson? with
      | .ok h => pure h
      | .error e => error s!"PS0-PROJECT-HEADER: {e}"
    let imports ← header.imports.mapM fun imp => do
      return ⟨imp, (← findModule? imp.module)⟩
    let trace ← getTrace
    let receipt := mod.pkg.buildDir / "ps0-inputs" / s!"{mod.name}.json"
    IO.FS.createDirAll (receipt.parent.getD ".")
    IO.FS.writeFile receipt (Json.mkObj [
      ("schema", toJson ("ps0-module-input/1" : String)),
      ("module", toJson mod.name.toString), ("source", toJson path.toString),
      ("driver", toJson compiler.toString), ("input_hash", toJson trace.hash.toString),
      ("header", toJson header)]).pretty
    return {path, header, imports, trace}

@[«module_facet»]
def ps0InputFacet : ModuleFacetDecl :=
  .mk Lake.Module.inputFacet (mkFacetJobConfig ps0Input (buildable := false))

def ps0CompilerContext (ctx : BuildContext) : BuildContext :=
  let ws := ctx.toContext.workspace
  let lean := {ws.lakeEnv.lean with lean := projectDriver}
  let ws : Workspace := {ws with lakeEnv := {ws.lakeEnv with lean := lean}}
  {ctx with opaqueWs := ws}

@[«module_facet»]
def ps0ElabFacet : ModuleFacetDecl :=
  .mk Lake.Module.leanArtsFacet (mkFacetJobConfig fun (mod : Lake.Module) => do
    if ← (mod.leanFile.withExtension "ps").pathExists then
      let native ← withTheReader BuildContext ps0CompilerContext (Lake.Module.leanArtsFacetConfig.run mod)
      native.mapM fun arts => do
        let source := mod.leanFile.withExtension "ps"
        let sidecar := mod.ileanFile.addExtension "ps0-source-map.json"
        let result ← IO.Process.output {
          cmd := projectDriver.toString
          args := #["source-map", source.toString]
          env := (← getWorkspace).augmentedEnvVars
        }
        unless result.exitCode == 0 do
          error s!"PS0-PROJECT-SOURCE-MAP: {result.stderr}"
        let expected := result.stdout.trimAscii.toString
        match Json.parse expected with
        | .error e => error s!"PS0-PROJECT-SOURCE-MAP: {e}"
        | .ok _ => pure ()
        let mut valid := false
        if ← sidecar.pathExists then
          valid := (← IO.FS.readFile sidecar) == expected
        unless valid do
          IO.FS.writeFile sidecar expected
        addTrace (← computeTrace (TextFilePath.mk sidecar))
        return arts
    else
      Lake.Module.leanArtsFacetConfig.run mod)
