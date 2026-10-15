import Lean
import PS0.Backend.Js.SourceMap

/-!
Deterministic ESM JavaScript + TypeScript declarations from the typed
portable IR. Exact Lean Nat semantics are represented by BigInt, including
saturating Nat subtraction. The backend contains no handwritten JavaScript
source files, npm compiler dependencies, or Lean-to-JS string rewriting.
-/

namespace PS0.Backend.Js

private partial def emitNat : NatExpr → String
  | .literal n => toString n ++ "n"
  | .local x => x
  | .globalConst name => name
  | .call name args =>
      name ++ "(" ++ String.intercalate ", "
        (args.toList.map emitNat) ++ ")"
  | .add l r => "(" ++ emitNat l ++ " + " ++ emitNat r ++ ")"
  | .mul l r => "(" ++ emitNat l ++ " * " ++ emitNat r ++ ")"
  | .sub l r =>
      let a := emitNat l
      let b := emitNat r
      "((" ++ a ++ ") >= (" ++ b ++ ") ? (" ++ a ++ ") - (" ++ b ++ ") : 0n)"

structure Artifacts where
  js : String
  dts : String
  jsMap : String

def emit (p : Program) (moduleName : String) : Artifacts := Id.run do
  let jsFile := moduleName ++ ".js"
  let mut jsLines : Array String :=
    #["// Generated from checked ProofScript .ps by PS0 (selected Nat MVP)."]
  let mut sources : Array (Option Origin) := #[none]
  let mut dtsLines : Array String := #[]
  for decl in p.declarations do
    let origin := some decl.origin
    if decl.isConst then
      jsLines := jsLines.push ("export const " ++ decl.name ++
        " = " ++ emitNat decl.body ++ ";")
      sources := sources.push origin
      dtsLines := dtsLines.push ("export declare const " ++ decl.name ++ ": bigint;")
    else
      jsLines := jsLines.push ("export function " ++ decl.name ++
        "(" ++ String.intercalate ", " decl.params.toList ++ ") {")
      sources := sources.push origin
      for param in decl.params do
        jsLines := jsLines.push (
          "  if (typeof " ++ param ++ " !== \"bigint\" || " ++
          param ++ " < 0n) throw new TypeError(" ++
          (Lean.Json.str ("Expected Nat bigint: " ++ param)).compress ++ ");")
        sources := sources.push origin
      jsLines := jsLines.push ("  return " ++ emitNat decl.body ++ ";")
      sources := sources.push origin
      jsLines := jsLines.push "}"
      sources := sources.push origin
      let params := String.intercalate ", "
        (decl.params.toList.map fun n => n ++ ": bigint")
      dtsLines := dtsLines.push ("export declare function " ++ decl.name ++
        "(" ++ params ++ "): bigint;")
  jsLines := jsLines.push ("//# sourceMappingURL=" ++ jsFile ++ ".map")
  sources := sources.push none
  return {
    js := String.intercalate "\n" jsLines.toList ++ "\n"
    dts := String.intercalate "\n" dtsLines.toList ++ "\n"
    jsMap := sourceMap p jsFile sources
  }

end PS0.Backend.Js
