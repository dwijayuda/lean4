/-
Copyright (c) 2026. Released under Apache 2.0 license.
-/
module

import Lean

public section

namespace LeanTs

open Lean Elab Command

private def natName : Name := .str .anonymous "Nat"
private def natOp (suffix : String) : Name := .str natName suffix

/-- The MVP accepts only direct Nat arguments and primitive Nat expressions. -/
private partial def collectParams (e : Expr) (params : Array String := #[]) :
    Except String (Array String × Expr) := do
  match e with
  | .lam _ ty body _ =>
    unless ty.isConstOf natName do
      throw "only explicit Nat parameters are supported"
    collectParams body (params.push s!"n{params.size}")
  | _ => pure (params, e)

private partial def checkNatType (ty : Expr) (n : Nat) : Bool :=
  match n with
  | 0 => ty.isConstOf natName
  | k + 1 =>
    match ty with
    | .forallE _ domain body _ => domain.isConstOf natName && checkNatType body k
    | _ => false

private partial def emitNat (params : Array String) (e : Expr) : Except String String := do
  match e with
  | .bvar idx =>
    match params[params.size - idx - 1]? with
    | some p => pure p
    | none => throw s!"unknown bound variable {idx}"
  | .lit (.natVal n) => pure s!"{n}n"
  | .mdata _ inner => emitNat params inner
  | _ =>
    let fn := e.getAppFn
    let args := e.getAppArgs
    match fn with
    | .const name _ =>
      if name == natOp "add" && args.size == 2 then
        return s!"({← emitNat params args[0]!} + {← emitNat params args[1]!})"
      if name == natOp "mul" && args.size == 2 then
        return s!"({← emitNat params args[0]!} * {← emitNat params args[1]!})"
      if name == natOp "sub" && args.size == 2 then
        return s!"natSub({← emitNat params args[0]!}, {← emitNat params args[1]!})"
      if name == natOp "succ" && args.size == 1 then
        return s!"({← emitNat params args[0]!} + 1n)"
      throw s!"unsupported executable constant: {name}"
    | _ => throw "unsupported expression (only Nat literals, parameters and primitive arithmetic)"

private def emitDefinition (name : Name) (d : DefinitionVal) : Except String String := do
  unless d.safety == .safe do
    throw "unsafe and partial declarations are not supported"
  unless d.levelParams.isEmpty do
    throw "polymorphic declarations are not supported"
  let .str .anonymous label := name
    | throw "export only unqualified top-level identifiers in this MVP"
  let (params, body) ← collectParams d.value
  if params.isEmpty then
    throw "exported declaration must have at least one Nat parameter"
  unless checkNatType d.type params.size do
    throw "function must have type Nat -> ... -> Nat"
  let result ← emitNat params body
  let arguments := String.intercalate ", " (params.toList.map fun p => p ++ ": bigint")
  let guards := String.join (params.toList.map fun p =>
    "  if (typeof " ++ p ++ " !== \"bigint\" || " ++ p ++ " < 0n) {\n" ++
    "    throw new RangeError(\"Nat requires a nonnegative bigint\");\n" ++
    "  }\n")
  return "// Generated from kernel-checked Lean declarations; JS semantics not formally verified.\n" ++
    "function natSub(a: bigint, b: bigint): bigint {\n" ++
    "  return a >= b ? a - b : 0n;\n" ++
    "}\n\n" ++
    "export function " ++ label ++ "(" ++ arguments ++ "): bigint {\n" ++
    guards ++ "  return " ++ result ++ ";\n}\n"

/-- Generate TypeScript after the preceding Lean declarations and proofs are checked. -/
elab "#lean_ts_export " decl:ident : command => do
  if (← hasErrors) then
    throwError "Lean reported errors; refusing TypeScript emission"
  let name := decl.getId
  let some (.defnInfo d) := (← getEnv).find? name
    | throwError m!"{name} is not an executable definition"
  let ts ← match emitDefinition name d with
    | .ok ts => pure ts
    | .error msg => throwError m!"cannot emit {name}: {msg}"
  let .str .anonymous label := name
    | throwError "only top-level names can be exported"
  liftIO <| IO.FS.createDirAll "generated"
  liftIO <| IO.FS.writeFile ("generated/" ++ label ++ ".ts") ts

end LeanTs
