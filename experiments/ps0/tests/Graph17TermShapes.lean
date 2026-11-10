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

run_cmd do
  let cases := #[
    ("binary-rhs-indexed-call", "acc + step xs[i]! (i == 0)", "acc + step(xs[i]!, (i == 0))"),
    ("binary-rhs-simple-call", "acc + step n true", "acc + step(n, true)"),
    ("indexed-matches", "xs[i]! matches some _ | none", "xs[i]! matches some _ | none"),
    ("call-matches", "choose xs[i]! matches some (some _) | none", "choose(xs[i]!) matches some (some _) | none"),
    ("projection-matches", "(getEnv ()).find? key matches some _ | none", "(getEnv()).find?(key) matches some _ | none"),
    ("sepBy-callee", "sepBy p sep", "sepBy(p, sep)"),
    ("sepBy1-callee", "sepBy1 p sep", "sepBy1(p, sep)")]
  let mut failures := 0
  for (label, nativeText, psText) in cases do
    let native ← match Parser.runParserCategory (← getEnv) `term nativeText with
      | .ok source => pure source
      | .error message => throwError "GRAPH17_NATIVE_CONTROL {label}: {message}"
    match Parser.runParserCategory (← getEnv) `psTerm psText with
    | .error message =>
        logInfo "GRAPH17_TERM_SHAPE {label}: PS_REJECTED {message}"
        failures := failures + 1
    | .ok source =>
        let lowered ← Elab.liftMacroM <| PS0.Syntax.lower `psTerm source
        if shape native != shape lowered then
          logInfo "GRAPH17_TERM_SHAPE {label}: DIFFERENT native={shape native} ps={shape lowered}"
          failures := failures + 1
        else
          logInfo "GRAPH17_TERM_SHAPE {label}: PASS"
  unless failures == 0 do
    throwError "GRAPH17_TERM_SHAPES: {failures} failures"
  logInfo "GRAPH17_TERM_SHAPES: PASS 7 cases"
