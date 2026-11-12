module
public meta import Lean
public meta import Lean.Compiler.ExternAttr
public meta import Lean.Compiler.ImplementedByAttr
public meta import PS0.Verified.Emit

public meta section

/-!
Untrusted proof-producing extraction candidate from the ADMITTED Lean body.
No source-text expression rewriting and no signature-only approval.
A later, independently replayed theorem must equate this exact IR to the
selected source definition. This command writes only private .lake staging.
-/
open Lean Meta Elab Command
namespace PS0.Verified

private def selectedOp (name : Name) : Option (Name × (NatExpr → NatExpr → NatExpr) × Nat) :=
  if name == `Nat.add then some (`Nat.add, NatExpr.add, 2)
  else if name == `Nat.mul then some (`Nat.mul, NatExpr.mul, 2)
  else if name == `Nat.sub then some (`Nat.sub, NatExpr.sub, 2)
  else if name == `HAdd.hAdd then some (`Nat.add, NatExpr.add, 6)
  else if name == `HMul.hMul then some (`Nat.mul, NatExpr.mul, 6)
  else if name == `HSub.hSub then some (`Nat.sub, NatExpr.sub, 6)
  else none

private def extractExpr (input0 input1 : Expr) (fuel : Nat) (value : Expr) : MetaM NatExpr := do
  match fuel with
  | 0 => throwError "PS0-VEXEC-DEPTH: expression exceeds the slice budget"
  | fuel + 1 =>
    let value := value.consumeMData
    if value.hasMVar then throwError "PS0-VEXEC-MVAR: unresolved expression"
    if value == input0 then return .first
    if value == input1 then return .second
    match value with
    | .lit (.natVal n) => return .literal n
    | _ => pure ()
    let head := value.getAppFn
    let args := value.getAppArgs
    let .const name _ := head
      | throwError "PS0-VEXEC-EXPR: unsupported expression; no fallback"
    if name == `OfNat.ofNat && args.size == 3 then
      if let .lit (.natVal n) := args[1]! then
        unless (← isDefEq value (mkNatLit n)) do
          throwError "PS0-VEXEC-LITERAL: nonstandard Nat literal instance"
        return .literal n
    let some (native, makeNode, arity) := selectedOp name
      | throwError "PS0-VEXEC-PRIMITIVE: unsupported constant {name}"
    unless args.size == arity do
      throwError "PS0-VEXEC-ARITY: unsupported primitive application"
    let left := args[arity - 2]!
    let right := args[arity - 1]!
    -- Check the resolved dictionary, not just the spelling of +, * or -.
    unless (← isDefEq value (mkApp2 (mkConst native) left right)) do
      throwError "PS0-VEXEC-INSTANCE: operation is not the canonical Nat primitive"
    return makeNode (← extractExpr input0 input1 fuel left)
      (← extractExpr input0 input1 fuel right)

private def extractRoot (root : Name) : MetaM NatExpr := do
  let env ← getEnv
  if (getExternAttrData? env root).isSome ||
      (Compiler.getImplementedBy? env root).isSome then
    throwError "PS0-VEXEC-REPLACEMENT: root has an external/replacement implementation"
  let .defnInfo decl ← getConstInfo root
    | throwError "PS0-VEXEC-ROOT: expected an ordinary definition"
  unless decl.safety == .safe && decl.levelParams.isEmpty do
    throwError "PS0-VEXEC-SAFETY: expected safe monomorphic definition"
  lambdaTelescope decl.value fun parameters body => do
    unless parameters.size == 2 do
      throwError "PS0-VEXEC-SIGNATURE: this slice requires exactly two Nat inputs"
    for parameter in parameters do
      unless (← isDefEq (← inferType parameter) (mkConst `Nat)) do
        throwError "PS0-VEXEC-TYPE: parameter must be Nat"
    unless (← isDefEq (← inferType body) (mkConst `Nat)) do
      throwError "PS0-VEXEC-TYPE: result must be Nat"
    extractExpr parameters[0]! parameters[1]! 64 body

elab "#ps0_extract " root:ident : command => do
  let name := root.getId
  let ir ← liftTermElabM do extractRoot name
  unless ir.withinOutputBudget do
    throwError "PS0-VEXEC-SIZE: candidate expansion exceeds the slice budget"
  let js := emit ir false
  let ts := emit ir true
  if js.utf8ByteSize > 65536 || ts.utf8ByteSize > 65536 then
    throwError "PS0-VEXEC-SIZE: candidate output exceeds the slice budget"
  let directory : System.FilePath := ".lake/ps0-candidate"
  IO.FS.createDirAll directory
  let data := Json.mkObj [
    ("schema", Json.str "ps0-nat2-candidate/1"),
    ("root", Json.str name.toString),
    ("ir", ir.json)
  ]
  IO.FS.writeFile (directory / "ir.json") (data.compress ++ "\n")
  IO.FS.writeFile (directory / "inventory.js") js
  IO.FS.writeFile (directory / "inventory.ts") ts
  logInfo "PS0-VEXEC-CANDIDATE: staged only; proof replay and publication policy remain required"

end PS0.Verified
