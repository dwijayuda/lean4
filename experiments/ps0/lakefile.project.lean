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
  buildDir := FilePath.mk ((get_config? projectBuildDir).getD ".lake/project")

lean_lib PS0

def projectSource : FilePath := FilePath.mk ((get_config? sourceRoot).getD "tests/project")
def projectRoots : Array Name := (((get_config? roots).getD "Demo,NativeSupport").splitOn ",").toArray.map String.toName
def projectMain : Name := ((get_config? rootModule).getD "Demo.Main").toName
def projectDriver : FilePath := FilePath.mk ((get_config? driver).getD ".lake/build/bin/ps0")

lean_lib PS0Project where
  srcDir := projectSource
  roots := projectRoots

@[default_target]
lean_exe ps0project where
  root := projectMain
  srcDir := projectSource
  supportInterpreter := true

def ps0Input (mod : Module) : FetchM (Job ModuleInput) := do
  let path := mod.leanFile.withExtension "ps"
  if !(← path.pathExists) then return ← Module.inputFacetConfig.run mod
  if ← mod.leanFile.pathExists then error s!"PS0-SOURCE-COLLISION: {path} and {mod.leanFile}"
  if mod.name.toString.contains '/' || mod.name.toString.contains '\\' then
    error "PS0-MODULE-PATH: invalid source module component"
  Job.async do
    addTrace (← computeTrace (TextFilePath.mk path))
    addTrace (← computeTrace projectDriver)
    let result ← IO.Process.output {
      cmd := projectDriver.toString
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
      ("driver", toJson projectDriver.toString), ("input_hash", toJson trace.hash.toString),
      ("header", toJson header)]).pretty
    return {path, header, imports, trace}

@[module_facet]
def ps0InputFacet : ModuleFacetDecl :=
  .mk Module.inputFacet (mkFacetJobConfig ps0Input (buildable := false))

def ps0CompilerContext (ctx : BuildContext) : BuildContext :=
  let ws := ctx.toContext.workspace
  let lean := {ws.lakeEnv.lean with lean := projectDriver}
  let ws : Workspace := {ws with lakeEnv := {ws.lakeEnv with lean := lean}}
  {ctx with opaqueWs := ws}

@[module_facet]
def ps0ElabFacet : ModuleFacetDecl :=
  .mk Module.elabArtsFacet (mkFacetJobConfig fun mod => do
    if ← (mod.leanFile.withExtension "ps").pathExists then
      withTheReader BuildContext ps0CompilerContext (Module.elabArtsFacetConfig.run mod)
    else
      Module.elabArtsFacetConfig.run mod)
