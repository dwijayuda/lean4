import Lean
import Std.WP
import PSCVL.Effect
import Lean.Compiler.NoncomputableAttr
import Lean.Util.FoldConsts
import PSCVL.Syntax

/-!
Experimental, fail-closed *preflight*, not PSCV-CERT-v1.
The frontend never issues a verified-executable certificate or native artifact.
Lean elaboration/kernel checking is delegated to the pinned official Lean build.
-/

open Lean Elab Command

namespace PSCVL

initialize pscvExportAttr : TagAttribute ←
  registerTagAttribute `pscv_export "Marks a candidate executable root for PSCVL preflight."

initialize pscvTypeSpecAttr : TagAttribute ←
  registerTagAttribute `pscv_type_spec
    "Developer-declared type-as-specification candidate (NOT an approved spec identity)."

private def permittedFoundationAxiom (n : Name) : Bool :=
  n == ``propext || n == ``Quot.sound || n == ``Classical.choice

syntax (name := pscvGate) "#pscv_gate" : command

@[command_elab pscvGate]
def elabPscvGate : CommandElab := fun _ => do
  let env ← getEnv
  -- The pinned Lean environment enumerates this module's elaborated constants,
  -- including generated sub-declarations, not text-matched source keywords.
  let locals ← env.getLocalConstantInfos
  let mut roots : Nat := 0
  for c in locals do
    let info := c.toConstantInfo
    if info.isUnsafe then
      throwError "PSCVL rejects unsafe declaration: {c.name}"
    if info.isPartial then
      throwError "PSCVL rejects partial declaration: {c.name}"
    if let .axiomInfo _ := info then
      throwError "PSCVL rejects source axiom: {c.name}"
    if pscvExportAttr.hasTag env c.name then
      if Lean.isNoncomputable env c.name then
        throwError "PSCVL executable export {c.name} is noncomputable"
      if info.type.getUsedConstants.contains ``IO then
        throwError "PSCVL closed export {c.name} uses raw IO (no verified effect model)"
      roots := roots + 1
      unless pscvTypeSpecAttr.hasTag env c.name do
        throwError "PSCVL export {c.name} is missing @[pscv_type_spec]"
      match info with
      | .defnInfo _ => pure ()
      | _ => throwError "PSCVL candidate executable root {c.name} must be a def"
  -- Every local declaration must have permitted logical foundations, not only
  -- exported roots: an unexported theorem or helper cannot silently carry sorry.
  for c in locals do
    let axioms ← collectAxioms c.name
    for ax in axioms do
      unless permittedFoundationAxiom ax do
        throwError "PSCVL declaration {c.name} depends on disallowed axiom {ax}"
  if roots == 0 then
    logInfo "PSCVL: ordinary checked source (no annotated executable roots); UNCERTIFIED"
  logInfo m!"PSCVL preflight: {roots} candidate root(s) passed; NO PSCV-CERT-v1 claim or executable emission"

end PSCVL
