module
meta import Lean
meta import PS0.StandardAdapters

/-! Capture native local-helper and enclosing proof-tail layouts before adapting their operands. -/
open Lean Elab.Command
meta section
partial def whereLocalLayout (stx : Syntax) : String :=
  toString stx.getKind ++ "[" ++ toString stx.getArgs.size ++ "](" ++
    String.intercalate "," (stx.getArgs.toList.map whereLocalLayout) ++ ")"
run_cmd do
  let env ← getEnv
  for input in [
      "def f (n : Nat) : Nat := helper n\nwhere\n  helper (x : Nat) (y : Nat := 3) : Nat := x + y",
      "def f (n : Nat) : Nat := helper n\nwhere\n  /-- local documentation -/\n  @[inline] helper (x : Nat) : Nat := x + n",
      "def f (n : Nat) : Nat := helper 0 n 0\nwhere\n  helper (x y : Nat) : Nat → Nat\n    | 0 => x + y\n    | Nat.succ k => helper x y k",
      "def f (n : Nat) : Nat := helper n\nwhere\n  helper (x : Nat) : Point := { x := x, y := 0 }",
      "def f : Nat := ?value\nwhere\nfinally\n| value => exact 1"] do
    match Parser.runParserCategory env `command input with
    | .ok stx => logInfo m!"PS0_NATIVE_WHERE_LOCAL_LAYOUT {input}: {whereLocalLayout stx}"
    | .error error => throwError "native where control failed: {input}: {error}"
