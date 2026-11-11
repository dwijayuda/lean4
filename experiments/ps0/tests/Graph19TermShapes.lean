import PS0.StandardAdapters

/-! Parser/lowering regressions for the six failures in compiler run 42770353333. -/

open Lean

private partial def difference (native ps : Syntax) : Option String := Id.run do
  if native.isOfKind choiceKind && !ps.isOfKind choiceKind then
    -- Importing the PS host also registers its legacy native-category body sugar.
    -- That PS-only branch is not a native Lean collection alternative.
    let alternatives := native.getArgs.filter (! ·.isOfKind `PS0.pscvBracedExpression)
    if alternatives.isEmpty then return some "no native control alternative"
    for alternative in alternatives do
      if let some d := difference alternative ps then return some d
    return none
  if native.getKind != ps.getKind then return some s!"kind {native.getKind}/{ps.getKind}"
  if native.isOfKind `hygieneInfo then return none
  if native.isIdent && native.getId != ps.getId then return some "identifier"
  if native.isAtom && native.getAtomVal != ps.getAtomVal then return some "atom"
  if native.getArgs.size != ps.getArgs.size then return some "arity"
  for i in [:native.getArgs.size] do
    if let some d := difference native[i] ps[i] then return some s!"{i}/{d}"
  return none

private partial def shape (source : Syntax) (depth : Nat) : String :=
  if depth == 0 then source.getKind.toString
  else s!"{source.getKind}[{String.intercalate "," (source.getArgs.toList.map (fun child => shape child (depth - 1)))}]"

open scoped PS0.StandardAdapters

run_cmd do
  let cases := #[
    ("direct-local-body-wrapper", "do\n  let singleton : FVarIdSet := (params[targetParamIdx]!.fvarId)\n  pure singleton",
      "do\n  let singleton : FVarIdSet := { params[targetParamIdx]!.fvarId }\n  pure singleton"),
    ("direct-mut-local-body-wrapper", "do\n  let mut singleton : FVarIdSet := (params[targetParamIdx]!.fvarId)\n  pure singleton",
      "do\n  let mut singleton : FVarIdSet := { params[targetParamIdx]!.fvarId }\n  pure singleton"),
    ("protected-singleton-local-value", "do\n  let singleton : FVarIdSet := ({ params[targetParamIdx]!.fvarId })\n  pure singleton",
      "do\n  let singleton : FVarIdSet := ({ params[targetParamIdx]!.fvarId })\n  pure singleton"),
    ("protected-singleton-mut-local-value", "do\n  let mut singleton : FVarIdSet := ({ params[targetParamIdx]!.fvarId })\n  pure singleton",
      "do\n  let mut singleton : FVarIdSet := ({ params[targetParamIdx]!.fvarId })\n  pure singleton"),
    ("do-arrow", "fun vars body => do←\n  unless vars.size = args.size do\n    return (.rfl, inst)\n  mkLambdaFVars vars p",
      "fun vars body => do←\n  unless vars.size = args.size do\n    return (.rfl, inst)\n  mkLambdaFVars vars p"),
    ("forwarding-lambda-call", "forwardStep value (flag := true) (fun x => do← return x)",
      "forwardStep(value, fun x => do← return x, flag := true)"),
    ("forwarding-bare-call", "forwardStep value (flag := true) (do← return x)",
      "forwardStep(value, do← return x, flag := true)"),
    ("forwarding-grouped-lambda-call", "forwardStep value (flag := true) (fun x => do← return x)",
      "forwardStep(value, (fun x => do← return x), flag := true)"),
    ("inline-do-call", "withLocalDeclD `_a α fun a => do isDefEq (← inferType (eAbst.instantiate1 a)) eType",
      "withLocalDeclD(`_a, α, fun a => do isDefEq((← inferType((eAbst.instantiate1 a))), eType))"),
    ("unless-inline-do-call", "do\n  unless (← withLocalDeclD `_a α fun a => do isDefEq (← inferType (eAbst.instantiate1 a)) eType) do\n    pure ()",
      "do\n  unless (← withLocalDeclD(`_a, α, fun a => do isDefEq((← inferType((eAbst.instantiate1 a))), eType))) do\n    pure(())"),
    ("nested-do-continuation-calls", "do\n  step x fun x => do\n  step x fun x => do\n  step x fun x => do\n  withContext x do\n  step x fun x => do\n  withContext x do\n    pure x",
      "do\n  step(x, fun x => do\n  step(x, fun x => do\n  step(x, fun x => do\n  withContext(x, do\n  step(x, fun x => do\n  withContext(x, do\n    pure(x)))))))"),
    ("inline-do-pattern", "do let ⟨mvar', fvars⟩ ← nCasesProd n mv h\n       let mvar'' ← mvar'.tryClear fvars.getLast!\n       pure ⟨mvar'', fvars⟩",
      "do let ⟨mvar', fvars⟩ ← nCasesProd n mv h\n       let mvar'' ← mvar'.tryClear fvars.getLast!\n       pure ⟨mvar'', fvars⟩"),
    ("nested-do-condition", "do\n  while (← do\n    let fullName := (← getCurrNamespace) ++ name\n    hasConst fullName <||> (withoutExporting <| hasConst (mkPrivateName (← getEnv) fullName))) do\n    pure ()",
      "do\n  while (← do\n    let fullName := (← getCurrNamespace) ++ name\n    hasConst fullName <||> (withoutExporting <| hasConst((mkPrivateName((← getEnv), fullName))))) do\n    pure(())")]
  let mut failures : Nat := 0
  for (label, nativeText, psText) in cases do
    try
      let native ← match Parser.runParserCategory (← getEnv) `term nativeText with
        | .ok stx => pure stx
        | .error message => throwError "native control: {message}"
      let source ← match Parser.runParserCategory (← getEnv) `psTerm psText with
        | .ok stx => pure stx
        | .error message => throwError "PS parse: {message}"
      logInfo m!"GRAPH19_PARSED {label}: {shape source 5}"
      let lowered ← Elab.liftMacroM <| PS0.Syntax.lower `psTerm source
      if label.startsWith "forwarding-" then
        unless (Lean.Elab.Do.Forward.matchApp? ⟨native⟩).isSome do
          throwError "native forwarding control is not recognized"
        unless (Lean.Elab.Do.Forward.matchApp? ⟨lowered⟩).isSome do
          throwError "native forwarding protocol no longer recognizes the PS application"
      else if label != "inline-do-call" && label != "unless-inline-do-call" && label != "nested-do-condition" then
        if let some d := difference native lowered then throwError "native syntax differs: {d}"
      logInfo m!"GRAPH19_TERM {label}: PASS"
    catch error =>
      logInfo m!"GRAPH19_TERM {label}: FAIL {error.toMessageData}"
      match error with
      | .error ref _ => logInfo m!"GRAPH19_ERROR_SOURCE {label}: {ref.getKind}: {ref.reprint}"
      | _ => pure ()
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
  logInfo "GRAPH19_REGRESSIONS: PASS 15 cases"
