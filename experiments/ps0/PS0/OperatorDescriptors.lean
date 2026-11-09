/-
Copyright (c) 2026 Dwijayuda. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
-/
module
public import Lean
public section

/-! Validate native binary parser roles for both parsing and original-source observation. -/
open Lean Lean.Parser
namespace PS0.OperatorDescriptors

private def label : Name → String
  | .str _ s => s
  | _ => ""

private partial def roles : ParserDescr → Option (Array Nat)
  | .symbol _ | .nonReservedSymbol .. | .unicodeSymbol .. => some #[0]
  | .cat `term _ => some #[1]
  | .const n => if #["ppSpace", "ppLine", "ppHardLine", "ppAllowUngrouped"].contains (label n) then some #[] else none
  | .unary n p =>
      if #["ppGroup", "ppRealGroup", "withoutPosition", "withPosition"].contains (label n) then roles p else none
  | .binary n p q => if n == `andthen then do return (← roles p) ++ (← roles q) else none
  | _ => none

private unsafe def binaryKindsImpl (env : Environment) (opts : Options) : Array Name := Id.run do
  let mut result := #[``Lean.Parser.Term.arrow]
  let some category := getParserCategory? env `term | return result
  let names := category.kinds.foldl (fun names name _ => names.push name) (#[] : Array Name)
  for name in names do
    if let some info := env.find? name then
      if info.type.getAppFn.isConstOf ``TrailingParserDescr then
        if let .ok (.trailingNode kind _ _ body) := env.evalConst TrailingParserDescr opts name then
          if roles body == some #[0, 1] then result := result.push kind
  return result

@[implemented_by binaryKindsImpl]
opaque binaryKinds (env : Environment) (opts : Options) : Array Name

end PS0.OperatorDescriptors
