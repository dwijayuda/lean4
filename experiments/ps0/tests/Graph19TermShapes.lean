import PS0.StandardAdapters

/-! Parser/lowering regressions for the six failures in compiler run 42770353333. -/

open Lean

private partial def difference (native ps : Syntax) : Option String := Id.run do
  if native.getKind != ps.getKind then return some s!"kind {native.getKind}/{ps.getKind}"
  if native.isOfKind `hygieneInfo then return none
  if native.isIdent && native.getId != ps.getId then return some "identifier"
  if native.isAtom && native.getAtomVal != ps.getAtomVal then return some "atom"
  if native.getArgs.size != ps.getArgs.size then return some "arity"
  for i in [:native.getArgs.size] do
    if let some d := difference native[i] ps[i] then return some s!"{i}/{d}"
  return none

open scoped PS0.StandardAdapters

run_cmd do
  let cases := #[
    ("singleton-local-value", "do\n  let singleton : FVarIdSet := { params[targetParamIdx]!.fvarId }\n  pure singleton",
      "do\n  let singleton : FVarIdSet := { params[targetParamIdx]!.fvarId }\n  pure singleton"),
    ("singleton-mut-local-value", "do\n  let mut singleton : FVarIdSet := { params[targetParamIdx]!.fvarId }\n  pure singleton",
      "do\n  let mut singleton : FVarIdSet := { params[targetParamIdx]!.fvarId }\n  pure singleton"),
    ("do-arrow", "fun vars body => do←\n  unless vars.size = args.size do\n    return (.rfl, inst)\n  mkLambdaFVars vars p",
      "fun vars body => do←\n  unless vars.size = args.size do\n    return (.rfl, inst)\n  mkLambdaFVars vars p"),
    ("inline-do-call", "withLocalDeclD `_a α fun a => do isDefEq (← inferType (eAbst.instantiate1 a)) eType",
      "withLocalDeclD(`_a, α, fun a => do isDefEq((← inferType((eAbst.instantiate1 a))), eType))"),
    ("inline-do-pattern", "do let ⟨mvar', fvars⟩ ← nCasesProd n mv h\n       let mvar'' ← mvar'.tryClear fvars.getLast!\n       pure ⟨mvar'', fvars⟩",
      "do let ⟨mvar', fvars⟩ ← nCasesProd n mv h\n       let mvar'' ← mvar'.tryClear fvars.getLast!\n       pure ⟨mvar'', fvars⟩"),
    ("nested-do-condition", "do\n  while (← do\n    let fullName := (← getCurrNamespace) ++ name\n    hasConst fullName <||> (withoutExporting <| hasConst (mkPrivateName (← getEnv) fullName))) do\n    pure ()",
      "do\n  while (← do\n    let fullName := (← getCurrNamespace) ++ name\n    hasConst fullName <||> (withoutExporting <| hasConst((mkPrivateName((← getEnv), fullName))))) do\n    pure ()")]
  let mut failures : Nat := 0
  for (label, nativeText, psText) in cases do
    try
      let native ← match Parser.runParserCategory (← getEnv) `term nativeText with
        | .ok stx => pure stx
        | .error message => throwError "native control: {message}"
      let source ← match Parser.runParserCategory (← getEnv) `psTerm psText with
        | .ok stx => pure stx
        | .error message => throwError "PS parse: {message}"
      let lowered ← Elab.liftMacroM <| PS0.Syntax.lower `psTerm source
      if label == "singleton-local-value" || label == "singleton-mut-local-value" ||
          label == "do-arrow" || label == "inline-do-pattern" then
        if let some d := difference native lowered then throwError "native syntax differs: {d}"
      logInfo m!"GRAPH19_TERM {label}: PASS"
    catch error =>
      logInfo m!"GRAPH19_TERM {label}: FAIL {error.toMessageData}"
      failures := failures + 1
  for (label, text) in #[
      ("instance-prefix-comma-signature", "function modifyReferencesM [Monad m] (rd : ReferenceData, f : References → m References) : m ReferenceData := do return rd"),
      ("ordinary-comma-signature", "function modifyReferencesM(rd : ReferenceData, f : References → m References) : m ReferenceData := do return rd")] do
    match Parser.runParserCategory (← getEnv) `command text with
    | .ok _ => logInfo m!"GRAPH19_COMMAND {label}: PASS"
    | .error message =>
        logInfo m!"GRAPH19_COMMAND {label}: FAIL {message}"
        failures := failures + 1
  unless failures == 0 do throwError "GRAPH19_REGRESSIONS: {failures} failures"
  logInfo "GRAPH19_REGRESSIONS: PASS 8 cases"
