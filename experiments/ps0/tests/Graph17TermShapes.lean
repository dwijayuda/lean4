import PS0.StandardAdapters

/-! Native syntax and source-origin controls for the four terminal graph-seventeen failures. -/

open Lean
open scoped PS0.StandardAdapters

private partial def shape (source : Syntax) : Json :=
  Json.mkObj [
    ("kind", toJson source.getKind.toString),
    ("ident", if source.isIdent then toJson source.getId.toString else .null),
    ("atom", if source.isAtom then toJson source.getAtomVal else .null),
    ("args", toJson (if source.isOfKind `hygieneInfo then #[] else source.getArgs.map shape))]

private partial def firstDifference (native ps : Syntax) (path : List Nat := []) : Option String := Id.run do
  let here := s!"{path.reverse}: native={native.getKind} ps={ps.getKind}"
  if native.getKind != ps.getKind then return some here
  if native.isOfKind `hygieneInfo then return none
  if native.isIdent && native.getId != ps.getId then return some here
  if native.isAtom && native.getAtomVal != ps.getAtomVal then return some here
  if native.getArgs.size != ps.getArgs.size then
    return some s!"{here} arity={native.getArgs.size}/{ps.getArgs.size}"
  for i in [:native.getArgs.size] do
    if let some difference := firstDifference native[i] ps[i] (i :: path) then return some difference
  return none

run_cmd do
  let cases := #[
    ("binary-rhs-indexed-call", "acc + step xs[i]! (i == 0)", "acc + step(xs[i]!, (i == 0))"),
    ("binary-rhs-simple-call", "acc + step n true", "acc + step(n, true)"),
    ("indexed-matches", "xs[i]! matches some _ | none", "xs[i]! matches some _ | none"),
    ("call-matches", "choose xs[i]! matches some (some _) | none", "choose(xs[i]!) matches some (some _) | none"),
    ("projection-matches", "(← getEnv).find? key matches some _ | none", "(← getEnv).find?(key) matches some _ | none"),
    ("sepBy-callee", "sepBy p sep", "sepBy(p, sep)"),
    ("sepBy1-callee", "sepBy1 p sep", "sepBy1(p, sep)"),
    ("do-reassign", "do\n  let mut acc := 0\n  acc := acc + step xs[i]! (i == 0)\n  return acc",
      "do\n  let mut acc := 0\n  acc := acc + step(xs[i]!, (i == 0))\n  return acc"),
    ("do-if-reassign", "do\n  let mut acc := 0\n  if xs[i]! matches .separator then\n    acc := 0\n  acc := acc + step xs[i]! (i == 0)\n  return acc",
      "do\n  let mut acc := 0\n  if xs[i]! matches .separator then\n    acc := 0\n  acc := acc + step(xs[i]!, (i == 0))\n  return acc"),
    ("do-for-reassign", "do\n  let mut acc := 0\n  for i in [:xs.size] do\n    if (i != 0) && xs[i]! matches .separator then\n      acc := 0\n    acc := acc + step xs[i]! (i == 0)\n  return acc",
      "do\n  let mut acc := 0\n  for i in [:xs.size] do\n    if (i != 0) && xs[i]! matches .separator then\n      acc := 0\n    acc := acc + step(xs[i]!, (i == 0))\n  return acc")]
  let mut failures : Nat := 0
  for (label, nativeText, psText) in cases do
    let native ← match Parser.runParserCategory (← getEnv) `term nativeText with
      | .ok source => pure source
      | .error message => throwError "GRAPH17_NATIVE_CONTROL {label}: {message}"
    match Parser.runParserCategory (← getEnv) `psTerm psText with
    | .error message =>
        logInfo m!"GRAPH17_TERM_SHAPE {label}: PS_REJECTED {message}"
        failures := failures + 1
    | .ok source =>
        let lowered ← Elab.liftMacroM <| PS0.Syntax.lower `psTerm source
        if let some difference := firstDifference native lowered then
          logInfo m!"GRAPH17_TERM_SHAPE {label}: DIFFERENT {difference}"
          failures := failures + 1
        else
          logInfo m!"GRAPH17_TERM_SHAPE {label}: PASS"
  unless failures == 0 do
    throwError "GRAPH17_TERM_SHAPES: {failures} failures"
  logInfo "GRAPH17_TERM_SHAPES: PASS 10 cases"
