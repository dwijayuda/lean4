import Lean
import Std.WP
import PSCVL.Effect
import Lean.Compiler.NoncomputableAttr
import Lean.Compiler.Old
import Lean.Util.FoldConsts
import PSCVL.Syntax

/-!
Experimental, fail-closed *preflight*, not PSCV-CERT-v1.
The frontend never issues a verified-executable certificate. Ordinary Lean-native
compilation remains a distinct, explicitly UNCERTIFIED operation.
Lean elaboration/kernel checking is delegated to the pinned official Lean build.
-/

open Lean Elab Command Meta

namespace PSCVL

initialize pscvExportAttr : TagAttribute ←
  registerTagAttribute `pscv_export "Marks a candidate executable root for PSCVL preflight."

initialize pscvTypeSpecAttr : TagAttribute ←
  registerTagAttribute `pscv_type_spec
    "Developer-declared type-as-specification candidate (NOT an approved spec identity)."

private def permittedFoundationAxiom (n : Name) : Bool :=
  n == ``propext || n == ``Quot.sound || n == ``Classical.choice

/-- Lean emits an unsafe runtime helper for some logically total,
kernel-checked recursive declarations. Such helpers are not source-level
permissions and are not logical proof dependencies. -/
private def compilerRecursiveHelper (env : Environment) (n : Name) : Bool :=
  match Lean.Compiler.isUnsafeRecName? n with
  | none => false
  | some parent =>
    match env.find? parent with
    | some parentInfo =>
      !parentInfo.isUnsafe && !parentInfo.isPartial &&
        (match parentInfo with | .defnInfo _ => true | _ => false)
    | none => false


/-- Pure diagnostic evaluation is restricted to concrete scalar value types. -/
private def pscvDiagnosticType (ty : Expr) : Bool :=
  match ty with
  | .const n _ => [`Nat, `Int, `Bool, `String, `Char, `Unit].contains n
  | _ => false

/-- Prevent Lean's general-purpose #eval from executing arbitrary monadic
commands under a PSCV0 source profile. No verification certificate is issued. -/
@[command_elab Lean.Parser.Command.eval]
def elabPscvPureEval : CommandElab
  | `(#eval%$tk $term) => do
    withoutModifyingEnv <| runTermElabM fun _ => Term.withDeclName `Q_pscv_eval do
      let e ← Term.elabTerm term none
      Term.synthesizeSyntheticMVarsNoPostponing
      withRef tk <| Meta.check e
      if e.hasSyntheticSorry then
        throwError "PSCV0-EVAL-HOLE: diagnostic has an unsolved proof or placeholder"
      let ty ← whnf (← inferType e)
      unless pscvDiagnosticType ty do
        throwError "PSCV0-EVAL-TYPE: #eval requires a pure scalar result"
      for used in e.getUsedConstants do
        if let some ci := (← getEnv).find? used then
          if ci.isUnsafe || ci.isPartial || Lean.isNoncomputable (← getEnv) used then
            throwError "PSCV0-EVAL-UNSAFE: unsafe, partial or noncomputable dependency"
    Lean.Elab.Command.elabEvalCore false tk term none
  | _ => throwUnsupportedSyntax

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
    unless compilerRecursiveHelper env c.name do
      if info.isUnsafe then
        throwError "PSCVL rejects unsafe declaration: {c.name}"
      if info.isPartial then
        throwError "PSCVL rejects partial declaration: {c.name}"
      if let .axiomInfo _ := info then
        throwError "PSCVL rejects source axiom: {c.name}"
    if pscvExportAttr.hasTag env c.name then
      if compilerRecursiveHelper env c.name then
        throwError "PSCVL cannot export a compiler-generated recursive helper"
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
    unless compilerRecursiveHelper env c.name do
      let axioms ← collectAxioms c.name
      for ax in axioms do
        unless permittedFoundationAxiom ax do
          throwError "PSCVL declaration {c.name} depends on disallowed axiom {ax}"
  if roots == 0 then
    logInfo "PSCVL: ordinary checked source (no annotated executable roots); UNCERTIFIED"
  logInfo m!"PSCVL preflight: {roots} candidate root(s) passed; NO PSCV-CERT-v1 claim or executable emission"

end PSCVL
