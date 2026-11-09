module
meta import Lean
meta import PS0.StandardAdapters

/-! Inspect native indexing dispatch and PS operands before elaboration. -/
open Lean Elab.Command
meta section
partial def kinds (stx : Syntax) : String :=
  toString stx.getKind ++ "(" ++ String.intercalate "," (stx.getArgs.toList.map kinds) ++ ")"
open scoped PS0.StandardAdapters
run_cmd do
  let env ← getEnv
  let some native := Parser.getParserCategory? env `term | throwError "missing native terms"
  for (token, parsers) in native.tables.trailingTable do
    if token == `«[» then
      for (parser, _) in parsers do
        logInfo m!"PS0_NATIVE_INDEX_PARSER {repr ((parser.info.collectKinds {}).toArray)}"
  for input in ["#[2, 3]", "xs[0]", "xs[chooseIndex(0)]", "xs[chooseIndex(0)]?",
      "#[2, 3][0]", "#[2, 3][chooseIndex(0)]",
      "#[2, 3][chooseIndex(0)]?", "#[2, 3][chooseIndex(0)]!",
      "#[2, 3][0]'(bound(1))", "(makeStore(2) |>.entries)[chooseIndex(1)]!",
      "makeStore(2) |>.entries[chooseIndex(1)]?", "#[Nat.succ][chooseIndex(0)]!(2)",
      "#[2, 3][chooseIndex(0):chooseIndex(2)]", "#[2, 3][chooseIndex(1):]",
      "#[2, 3][:chooseIndex(1)]", "l.unattach[i] = (l[i]'(by simpa using h)).1"] do
    match Parser.runParserCategory env `psTerm input with
    | .ok stx => logInfo m!"PS0_INDEX_PARSE {input}: {kinds stx}"
    | .error error => logInfo m!"PS0_INDEX_PARSE_ERROR {input}: {error}"
  let retained : System.FilePath := "build/retained-index-signature.txt"
  if ← retained.pathExists then
    let input ← IO.FS.readFile retained
    let (_, parser) ← (Parser.mkParserOfConstant (Parser.parserExtension.getState env).categories
      `PS0.StandardAdapters.ps0StandardTheorem).run {env, opts := {}}
    let ictx := Parser.mkInputContext input "retained-index-signature"
    let parsed := parser.fn.run ictx {env, options := {}} (Parser.getTokenTable env)
      (Parser.mkParserState input)
    if !parsed.allErrors.isEmpty then
      logInfo m!"PS0_INDEX_DECLARATION_ERROR: {parsed.toErrorMsg ictx}"
    else
      logInfo m!"PS0_INDEX_DECLARATION_PARSE: {parsed.stxStack.back.getKind}"
