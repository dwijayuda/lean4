import Lean
import PS0.HostCategories

/-! Compare the registered native dependent-if binder role and macro with the PS adapter. -/

open Lean

run_cmd do
  let env ← getEnv
  for binder in ["h", "_"] do
    let nativeText := s!"if {binder} : n = 0 then add n 3 else add n 1"
    let psText := s!"if {binder} : n = 0 then add(n, 3) else add(n, 1)"
    let native ← IO.ofExcept <| Parser.runParserCategory env `term nativeText
    let parsed ← IO.ofExcept <| Parser.runParserCategory env `psTerm psText
    let lowered ← Elab.liftMacroM <| PS0.Syntax.lower `psTerm parsed
    unless native.getKind == lowered.getKind && native.getArgs.size == lowered.getArgs.size &&
        native[1].getKind == lowered[1].getKind && native[1].getArgs.size == lowered[1].getArgs.size do
      throwError s!"PS0_NATIVE_DEPENDENT_IF_SHAPE: {repr native[1]} / {repr lowered[1]}"
    let baselineExpansion ← Elab.liftMacroM <| Macro.expandMacro? native
    let psExpansion ← Elab.liftMacroM <| Macro.expandMacro? lowered
    unless baselineExpansion.isSome && psExpansion.isSome do
      throwError s!"PS0_NATIVE_DEPENDENT_IF_MACRO: {binder}"
    logInfo s!"PS0_NATIVE_DEPENDENT_IF_CONTROL:{binder}:{native[1].getKind}"
