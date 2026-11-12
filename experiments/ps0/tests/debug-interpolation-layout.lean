module
meta import Lean
meta import PS0.StandardAdapters

/-! Compare pinned native and PS parsing before assigning interpolation ownership. -/
open Lean Elab.Command
meta section
run_cmd do
  let env ← getEnv
  for input in ["s!\"{value}\"", "s!\"{Id.run(value)}\"", "s!\"{(Id.run value)}\""] do
    for category in [`term, `psTerm] do
      match Parser.runParserCategory env category input with
      | .ok stx => logInfo m!"PS0_INTERPOLATION_CONTROL_OK {category} {input}: {stx.getKind}"
      | .error error => logInfo m!"PS0_INTERPOLATION_CONTROL_ERROR {category} {input}: {error}"
