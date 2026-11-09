module
public meta import Lean
public import PS0.Operators

public meta section

/-! PS-owned category adapters; independently owned native and DSL syntax stays opaque. -/

open Lean

declare_syntax_cat psTerm
declare_syntax_cat psCommand
declare_syntax_cat psTactic (behavior := both)
declare_syntax_cat psDoSeq
declare_syntax_cat psCallArg
declare_syntax_cat psHead
declare_syntax_cat psFunBinder
declare_syntax_cat psDoElem
declare_syntax_cat psDoItem
declare_syntax_cat psLocalBinder
declare_syntax_cat psStructInstFieldDecl

namespace PS0.DoLayout
open Lean.Parser

private def redirect (roles : Array (Name × Name)) (ctx : ParserContextCore) : ParserContextCore := Id.run do
  let native := categoryParserFnExtension.getState ctx.env
  let restore := fun (child : ParserContextCore) => {child with env := categoryParserFnExtension.setState child.env native}
  let dispatch : CategoryParserFn := fun category =>
    match roles.find? (fun role => role.1 == category) with
    | some (_, target) => adaptUncacheableContextFn restore (native target)
    | none => adaptUncacheableContextFn restore (native category)
  return {ctx with env := categoryParserFnExtension.setState ctx.env dispatch}

private def operands (roles : Array (Name × Name)) (parser : Parser) : Parser :=
  withFn (adaptUncacheableContextFn (redirect roles)) parser

@[run_parser_attribute_hooks] def sequence : Parser :=
  operands #[(`doElem, `psDoElem)] Lean.Parser.Term.doSeq

@[run_parser_attribute_hooks] def returnElem : Parser :=
  operands #[(`term, `psTerm)] Lean.Parser.Term.doReturn

@[run_parser_attribute_hooks] def expressionElem : Parser :=
  operands #[(`term, `psTerm)] Lean.Parser.Term.doExpr

private def letPrefix : Parser :=
  symbol "let " >> optional (symbol "mut ") >> Lean.Parser.Term.letConfig

@[run_parser_attribute_hooks] def localBinder : Parser :=
  operands #[(`term, `psTerm)] Lean.Parser.Term.letIdBinder

@[run_parser_attribute_hooks] def localLhs : Parser :=
  Lean.Parser.Term.letId >> many (ppSpace >> categoryParser `psLocalBinder 0) >>
    operands #[(`term, `psTerm)] Lean.Parser.Term.optType

@[run_parser_attribute_hooks] def whereFinally : Parser :=
  operands #[(`tactic, `psTactic)] Lean.Parser.Term.whereFinally

@[run_parser_attribute_hooks] def argumentValue : Parser :=
  withoutPosition (categoryParser `psTerm 0)

@[run_parser_attribute_hooks] def ascriptionTerm : Parser :=
  operands #[(`term, `psTerm)] Lean.Parser.Term.typeAscription

@[run_parser_attribute_hooks] def byTerm : Parser :=
  operands #[(`tactic, `psTactic)] Lean.Parser.Term.byTactic

@[run_parser_attribute_hooks] def dependentIfTerm : Parser :=
  leadingNode `termDepIfThenElse leadPrec <|
    ppRealGroup (ppRealFill (ppIndent ("if " >> node `Lean.binderIdent Lean.Parser.Term.binderIdent >> " : " >>
      categoryParser `psTerm 0 >> " then") >> ppSpace >> categoryParser `psTerm 0) >>
      ppDedent ppSpace >> ppRealFill ("else " >> categoryParser `psTerm 0))

@[run_parser_attribute_hooks] def matchTerm : Parser :=
  leadingNode ``Lean.Parser.Term.«match» leadPrec <|
    "match " >> optional Lean.Parser.Term.generalizingParam >>
      optional (operands #[(`term, `psTerm)] Lean.Parser.Term.motive) >>
      sepBy1 (operands #[(`term, `psTerm)] Lean.Parser.Term.matchDiscr) ", " >>
      " with" >> ppDedent (Lean.Parser.Term.matchAlts (categoryParser `psTerm 0))

@[run_parser_attribute_hooks] def patternLambda : Parser :=
  leadingNode ``Lean.Parser.Term.«fun» maxPrec <|
    ppAllowUngrouped >> unicodeSymbol "λ" "fun" (preserveForPP := true) >>
      Lean.Parser.Term.matchAlts (categoryParser `psTerm 0)

@[run_parser_attribute_hooks] def recordTerm : Parser :=
  operands #[(`term, `psTerm), (`structInstFieldDecl, `psStructInstFieldDecl)]
    Lean.Parser.Term.structInst

@[run_parser_attribute_hooks] def fieldDefinition : Parser :=
  operands #[(`term, `psTerm)] Lean.Parser.Term.structInstFieldDef

@[run_parser_attribute_hooks] def fieldEquations : Parser :=
  node ``Lean.Parser.Term.structInstFieldEqns <|
    optional "private" >> Lean.Parser.Term.matchAlts (categoryParser `psTerm 0)

private def ifCondition : Parser :=
  node ``Lean.Parser.Term.doIfLet
      ("let " >> termParser >>
        (operands #[(`term, `psTerm)] Lean.Parser.Term.doIfLetPure <|>
         operands #[(`term, `psTerm)] Lean.Parser.Term.doIfLetBind)) <|>
    operands #[(`term, `psTerm)] Lean.Parser.Term.doIfProp

@[run_parser_attribute_hooks] def ifElem : Parser :=
  leadingNode ``Lean.Parser.Term.doIf maxPrec <| withResetCache <|
    withPositionAfterLinebreak <| ppRealGroup <|
      ppRealFill (ppIndent ("if " >> ifCondition >> " then") >> ppSpace >> sequence) >>
      many (checkColGe "'else if' in 'do' must be indented" >>
        group (ppDedent ppSpace >> ppRealFill
          (Lean.Parser.Term.elseIf >> ifCondition >> " then " >> sequence))) >>
      optional (checkColGe "'else' in 'do' must be indented" >>
        ppDedent ppSpace >> ppRealFill ("else " >> sequence))

def namedDeclaration : Parser :=
  node ``Lean.Parser.Term.letDecl <|
    notFollowedBy (nonReservedSymbol "rec") "rec" >>
      node ``Lean.Parser.Term.letIdDecl
        (atomic (localLhs >> " := ") >> categoryParser `psTerm 0)

@[run_parser_attribute_hooks] def letElem : Parser :=
  leadingNode ``Lean.Parser.Term.doLet maxPrec <|
    letPrefix >> namedDeclaration

@[run_parser_attribute_hooks] def haveElem : Parser :=
  leadingNode ``Lean.Parser.Term.doHave maxPrec <|
    "have " >> Lean.Parser.Term.letConfig >> namedDeclaration

@[run_parser_attribute_hooks] def matchElem : Parser :=
  leadingNode ``Lean.Parser.Term.doMatch leadPrec <|
    "match " >> optional Lean.Parser.Term.dependentParam >>
      optional Lean.Parser.Term.generalizingParam >>
      optional (operands #[(`term, `psTerm)] Lean.Parser.Term.motive) >>
      sepBy1 (operands #[(`term, `psTerm)] Lean.Parser.Term.matchDiscr) ", " >>
      " with" >> ppDedent (Lean.Parser.Term.matchAlts sequence)

def forDeclaration : Parser :=
  node ``Lean.Parser.Term.doForDecl <|
    optional (atomic (ident >> " : ")) >> termParser >> " in " >>
      withForbiddens #["do", "invariant", "decreasing"] (categoryParser `psTerm 0)

@[run_parser_attribute_hooks] def forElem : Parser :=
  leadingNode ``Lean.Parser.Term.doFor maxPrec <|
    "for " >> sepBy1 forDeclaration ", " >> optional Lean.Parser.Term.doLoopInvariant >>
      optional Lean.Parser.Term.doLoopDecreasing >> " do " >> sequence

def catchElem : Parser :=
  node ``Lean.Parser.Term.doCatch <|
    ppDedent ppLine >> atomic ("catch " >> Lean.Parser.Term.binderIdent) >>
      optional (" : " >> categoryParser `psTerm 0) >> darrow >> sequence

def catchMatchElem : Parser :=
  node ``Lean.Parser.Term.doCatchMatch <|
    ppDedent ppLine >> "catch " >> ppDedent (Lean.Parser.Term.matchAlts sequence)

def finallyElem : Parser :=
  node ``Lean.Parser.Term.doFinally <| ppDedent ppLine >> "finally " >> sequence

@[run_parser_attribute_hooks] def tryElem : Parser :=
  leadingNode ``Lean.Parser.Term.doTry maxPrec <|
    "try " >> sequence >> many (catchElem <|> catchMatchElem) >> optional finallyElem

@[run_parser_attribute_hooks] def namedLetTerm : Parser :=
  leadingNode ``Lean.Parser.Term.«let» leadPrec <|
    withPosition ("let" >> Lean.Parser.Term.letConfig >> namedDeclaration) >>
      Lean.Parser.Term.optSemicolon (categoryParser `psTerm 0)

def recursiveDeclaration : Parser :=
  node ``Lean.Parser.Term.letRecDecl <|
    optional Lean.Parser.Command.docComment >> optional Lean.Parser.Term.attributes >>
    node ``Lean.Parser.Term.letDecl
      (notFollowedBy (nonReservedSymbol "rec") "rec" >>
        (node ``Lean.Parser.Term.letIdDecl
          (atomic (localLhs >> " := ") >>
            categoryParser `psTerm 0) <|>
         node ``Lean.Parser.Term.letEqnsDecl
          (localLhs >>
            Lean.Parser.Term.matchAlts (categoryParser `psTerm 0)))) >>
    Lean.Parser.Termination.suffix

def recursiveDeclarations : Parser :=
  node ``Lean.Parser.Term.letRecDecls <| sepBy1 recursiveDeclaration ", "

def recursivePrefix : Parser :=
  group (symbol "let " >> nonReservedSymbol "rec ")

@[run_parser_attribute_hooks] def recursiveElem : Parser :=
  leadingNode ``Lean.Parser.Term.doLetRec maxPrec <| recursivePrefix >> recursiveDeclarations

@[run_parser_attribute_hooks] def recursiveTerm : Parser :=
  leadingNode ``Lean.Parser.Term.letrec leadPrec <|
    withPosition (recursivePrefix >> recursiveDeclarations) >>
      Lean.Parser.Term.optSemicolon (categoryParser `psTerm 0)

@[run_parser_attribute_hooks] def bindElem : Parser :=
  leadingNode ``Lean.Parser.Term.doLetArrow maxPrec <| withPosition <|
    letPrefix >> operands #[(`term, `psTerm), (`doElem, `psDoElem)] Lean.Parser.Term.doIdDecl

@[run_parser_attribute_hooks] def patternBindElem : Parser :=
  operands #[(`doElem, `psDoElem)] Lean.Parser.Term.doLetArrow

@[run_parser_attribute_hooks] def patternLetElseElem : Parser :=
  leadingNode ``Lean.Parser.Term.doLetElse leadPrec <| withPosition <|
    letPrefix >> termParser >> " := " >> categoryParser `psTerm 0 >>
      (checkColGe >> " | " >> operands #[(`doElem, `psDoElem)] Lean.Parser.Term.doSeqIndent) >>
      optional (checkColGe >> operands #[(`doElem, `psDoElem)] Lean.Parser.Term.doSeqIndent)

@[run_parser_attribute_hooks] def reassignElem : Parser :=
  leadingNode ``Lean.Parser.Term.doReassign maxPrec <|
    Lean.Parser.Term.notFollowedByRedefinedTermToken >>
      operands #[(`term, `psTerm)] Lean.Parser.Term.letIdDeclNoBinders

@[run_parser_attribute_hooks] def nestedElem : Parser :=
  operands #[(`doElem, `psDoElem)] Lean.Parser.Term.doNested

@[run_parser_attribute_hooks] def unlessElem : Parser :=
  operands #[(`term, `psTerm), (`doElem, `psDoElem)] Lean.Parser.Term.doUnless

@[run_parser_attribute_hooks] def unlessTerm : Parser :=
  operands #[(`term, `psTerm), (`doElem, `psDoElem)] Lean.Parser.Term.termUnless

private def manyPunningFields (source : Syntax) : Bool := Id.run do
  unless source.isOfKind ``Lean.Parser.Term.structInst && source.getArgs.size == 6 &&
      source[1].getArgs.isEmpty && source[4].getArgs.isEmpty &&
      source[3].getArgs.size == 1 && source[3][0].getArgs.isEmpty &&
      source[2].isOfKind ``Lean.Parser.Term.structInstFields do return false
  let fields := source[2][0].getSepArgs
  return fields.size >= 2 && fields.all fun field =>
    field.isOfKind ``Lean.Parser.Term.structInstField && field.getArgs.size == 2 &&
      field[1].getArgs.isEmpty && field[0].getArgs.size == 2 &&
      field[0][0].isIdent && field[0][1].getArgs.isEmpty

@[run_parser_attribute_hooks] def punningBraces : Parser :=
  withFn (fun _ ctx initial =>
    let parsed := Lean.Parser.Term.structInst.fn ctx initial
    if parsed.hasError then parsed
    else if manyPunningFields parsed.stxStack.back then PS0.Operators.leading.fn ctx initial
    else initial.mkUnexpectedError "PS0V1-PUNNING-BRACES: expected a native punning field list")
    Lean.Parser.Term.structInst

end PS0.DoLayout

@[psTerm_parser low]
def ps0NativeTermBridge : Lean.Parser.Parser := PS0.Operators.leading
@[psTerm_parser]
def ps0NativeOperatorParser : Lean.Parser.TrailingParser := PS0.Operators.trailing
syntax (name := ps0NativeCommandBridge) command : psCommand
syntax (name := ps0NativeTacticBridge) (priority := low) tactic : psTactic
syntax (name := ps0NativeDoBridge) (priority := low) doSeq : psDoSeq
syntax (name := ps0NativeLayoutDoSeq) PS0.DoLayout.sequence : psDoSeq
syntax (name := ps0NativeLocalBinder) PS0.DoLayout.localBinder : psLocalBinder
syntax (name := ps0NativeDoElemBridge) (priority := low) doElem : psDoElem
@[psDoElem_parser 20000]
def ps0NativeDoReturn : Lean.Parser.Parser := PS0.DoLayout.returnElem
@[psDoElem_parser 20000]
def ps0NativeDoExpression : Lean.Parser.Parser := PS0.DoLayout.expressionElem
@[psDoElem_parser 20000]
def ps0NativeDoLet : Lean.Parser.Parser := PS0.DoLayout.letElem
@[psDoElem_parser 20000]
def ps0NativeDoHave : Lean.Parser.Parser := PS0.DoLayout.haveElem
@[psDoElem_parser 20000]
def ps0NativeDoMatch : Lean.Parser.Parser := PS0.DoLayout.matchElem
@[psDoElem_parser 20000]
def ps0NativeDoFor : Lean.Parser.Parser := PS0.DoLayout.forElem
@[psDoElem_parser 20000]
def ps0NativeDoTry : Lean.Parser.Parser := PS0.DoLayout.tryElem
@[psDoElem_parser 20000]
def ps0NativeDoLetRec : Lean.Parser.Parser := PS0.DoLayout.recursiveElem
@[psTerm_parser 20000]
def ps0NativeTermLetRec : Lean.Parser.Parser := PS0.DoLayout.recursiveTerm
@[psTerm_parser 20000]
def ps0NativeTermLet : Lean.Parser.Parser := PS0.DoLayout.namedLetTerm
@[psDoElem_parser 20000]
def ps0NativeDoBind : Lean.Parser.Parser := PS0.DoLayout.bindElem
@[psDoElem_parser 10000]
def ps0NativeDoPatternBind : Lean.Parser.Parser := PS0.DoLayout.patternBindElem
@[psDoElem_parser 30000]
def ps0NativeDoPatternLetElse : Lean.Parser.Parser := PS0.DoLayout.patternLetElseElem
@[psDoElem_parser 20000]
def ps0NativeDoReassign : Lean.Parser.Parser := PS0.DoLayout.reassignElem
@[psDoElem_parser 20000]
def ps0NativeDoNested : Lean.Parser.Parser := PS0.DoLayout.nestedElem
@[psDoElem_parser 20000]
def ps0NativeDoUnless : Lean.Parser.Parser := PS0.DoLayout.unlessElem
@[psTerm_parser 20000]
def ps0NativeTermUnless : Lean.Parser.Parser := PS0.DoLayout.unlessTerm
@[psTerm_parser 20000]
def ps0NativeTermMatch : Lean.Parser.Parser := PS0.DoLayout.matchTerm
@[psTerm_parser 20000]
def ps0NativeTypeAscription : Lean.Parser.Parser := PS0.DoLayout.ascriptionTerm
@[psTerm_parser 20000]
def ps0NativeBy : Lean.Parser.Parser := PS0.DoLayout.byTerm
@[psTerm_parser 20000]
def ps0NativeDependentIf : Lean.Parser.Parser := PS0.DoLayout.dependentIfTerm
@[psTerm_parser 20000]
def ps0NativePatternLambda : Lean.Parser.Parser := PS0.DoLayout.patternLambda
@[psTerm_parser 20000]
def ps0NativeRecord : Lean.Parser.Parser := PS0.DoLayout.recordTerm
@[psStructInstFieldDecl_parser]
def ps0NativeFieldDefinition : Lean.Parser.Parser := PS0.DoLayout.fieldDefinition
@[psStructInstFieldDecl_parser]
def ps0NativeFieldEquations : Lean.Parser.Parser := PS0.DoLayout.fieldEquations
@[psDoElem_parser 20000]
def ps0NativeDoIf : Lean.Parser.Parser := PS0.DoLayout.ifElem
@[psTerm_parser 30000]
def ps0NativePunningBraces : Lean.Parser.Parser := PS0.DoLayout.punningBraces
syntax (name := ps0PositionalArg) PS0.DoLayout.argumentValue : psCallArg
syntax (name := ps0NamedArg) ident " := " PS0.DoLayout.argumentValue : psCallArg
syntax (name := ps0NativeEllipsisArg) Lean.Parser.Term.ellipsis : psCallArg

syntax (name := ps0NativeFunBinderBridge) (priority := low) Lean.Parser.Term.funBinder : psFunBinder
syntax (name := ps0FunExplicit) (priority := high)
  "(" Lean.Parser.Term.binderIdent+ ":" psTerm ")" : psFunBinder
syntax (name := ps0FunImplicit) (priority := high)
  "{" Lean.Parser.Term.binderIdent+ (":" psTerm)? "}" : psFunBinder
syntax (name := ps0FunStrict) (priority := high)
  Lean.Parser.Term.strictImplicitLeftBracket Lean.Parser.Term.binderIdent+
  (":" psTerm)? Lean.Parser.Term.strictImplicitRightBracket : psFunBinder
syntax (name := ps0FunInstance) (priority := high)
  "[" Lean.Parser.Term.optIdent psTerm "]" : psFunBinder
def ps0LambdaToken := Lean.Parser.unicodeSymbol "λ" "fun" (preserveForPP := true)
def ps0LambdaArrow := Lean.Parser.unicodeSymbol " ↦" " =>" (preserveForPP := true)
syntax:max (name := ps0HostLambda) (priority := high)
  ps0LambdaToken psFunBinder+ (":" psTerm)? ps0LambdaArrow psTerm : psTerm

syntax:max (name := ps0HostAdjacentCall) (priority := high)
  ident noWs "(" sepBy1(psCallArg, ",", "," ppSpace, allowTrailingSep) ")" : psTerm

@[psHead_parser low]
def ps0NativeHeadBridge : Lean.Parser.Parser := PS0.Operators.headLeading
@[psHead_parser]
def ps0NativeHeadProjectionParser : Lean.Parser.TrailingParser := PS0.Operators.projection
syntax:max (name := ps0ParenthesizedHead) Lean.Parser.Term.hygienicLParen psTerm ")" : psHead
syntax:max (name := ps0HeadCall) psHead:max noWs
  "(" sepBy1(psCallArg, ",", "," ppSpace, allowTrailingSep) ")" : psHead
syntax:max (name := ps0HeadEmptyCall) psHead:max noWs "(" ")" : psHead
syntax (name := ps0HostHeadTerm) psHead : psTerm
syntax:max (name := ps0HostParens) (priority := high)
  Lean.Parser.Term.hygienicLParen PS0.DoLayout.argumentValue ")" : psTerm
syntax:max (name := ps0HostBraces) (priority := high) "{" psTerm "}" : psTerm
syntax (name := ps0HostIf) (priority := high) "if " psTerm " then " psTerm " else " psTerm : psTerm
syntax (name := ps0HostExact) (priority := high) "exact " psTerm : psTactic
syntax (name := ps0HostApply) (priority := high) "apply " psTerm : psTactic
syntax (name := ps0HostRefine) (priority := high) "refine " psTerm : psTactic
syntax (name := ps0HostBy) (priority := high)
  "by " "{" sepBy1(psTactic, ";", ";" ppSpace, allowTrailingSep) "}" : psTerm
syntax (name := ps0HostDoLet) (priority := high)
  "let " ident (":" psTerm)? ":=" psTerm : psDoElem
syntax (name := ps0HostDoLetMut) (priority := high)
  "let " "mut " ident (":" psTerm)? ":=" psTerm : psDoElem
syntax (name := ps0HostDoBind) (priority := high)
  "let " ident "←" psTerm : psDoElem
syntax (name := ps0HostDoReassign) (priority := high) ident ":=" psTerm : psDoElem
syntax (name := ps0HostDoExpr) (priority := high)
  Lean.Parser.Term.notFollowedByRedefinedTermToken psTerm : psDoElem
syntax (name := ps0HostDoItem) ppLine psDoElem ";"? : psDoItem
syntax (name := ps0HostDoSeq) (priority := high) "{" psDoItem+ ppLine "}" : psDoSeq
syntax (name := ps0HostDo) (priority := high) "do " psDoSeq : psTerm

namespace PS0.Syntax

private def loweringInfo (source : Lean.Syntax) : SourceInfo :=
  match source.getRange? with
  | some span => .synthetic span.start span.stop false
  | none => .none

private partial def punningIdentifier? (source : Lean.Syntax) : Option Lean.Syntax :=
  if source.isIdent then some source else
  if #[`ps0NativeTermBridge, `ps0HostHeadTerm, `ps0NativeHeadBridge].contains source.getKind &&
      source.getArgs.size == 1 then punningIdentifier? source[0]
  else none

private partial def nativeBraceOrigins (source native : Lean.Syntax) : MacroM Lean.Syntax := do
  if native.isOfKind choiceKind then
    let alternatives ← native.getArgs.mapM (nativeBraceOrigins source)
    return .node (loweringInfo source) choiceKind alternatives
  let args := native.getArgs
  unless args.size >= 2 && args[0]!.isAtom && args[0]!.getAtomVal == "{" &&
      args.back!.isAtom && args.back!.getAtomVal == "}" do
    Macro.throwError s!"PS0V1-NATIVE-BRACES: unexpected native alternative {native.getKind}"
  let native := (native.setArg 0 source[0]).setArg (args.size - 1) source[2]
  return .node (loweringInfo source) native.getKind native.getArgs

private def rejectHostGap (source : Lean.Syntax) : MacroM Unit := do
  if let .node (.synthetic ..) _ _ := source then return ()
  if source.isOfKind ``Lean.Parser.Term.app then
    for arg in source[1].getArgs do
      if arg.isOfKind ``Lean.Parser.Term.paren || arg.isOfKind ``Lean.Parser.Term.tuple then
        if let some start := arg.getPos? then
          if let some stop := source[0].getTailPos? then
            if stop < start then
              withRef arg do Macro.throwError "PS0V1-CALL-GAP: parenthesized host arguments require adjacency"

private partial def checkProjectionSubject (source : Lean.Syntax) : MacroM Unit := do
  if let .node (.synthetic ..) _ _ := source then return ()
  rejectHostGap source
  if source.isOfKind ``Lean.Parser.Term.paren then
    checkProjectionSubject source[1]
  else if source.isOfKind ``Lean.Parser.Term.proj then
    checkProjectionSubject source[0]
  else if source.isOfKind ``Lean.Parser.Term.app then
    checkProjectionSubject source[0]
    for argument in source[1].getArgs do
      checkProjectionSubject
        (if argument.isOfKind ``Lean.Parser.Term.namedArgument then argument[3] else argument)

set_option maxHeartbeats 800000 in
mutual
partial def lower (category : Name) (source : Lean.Syntax) :
    MacroM Lean.Syntax := withRef source <| Macro.withIncRecDepth source do
  if source.isOfKind choiceKind then
    Macro.throwError "PS0V1-HOST-AMBIGUITY: resolve host syntax before lowering"
  if category == `psTerm then
    if source.isOfKind `termDepIfThenElse then
      unless source.getArgs.size == 8 do Macro.throwError "PS0V1-DEPENDENT-IF: unexpected native condition"
      let source := source.setArg 3 (← lower `psTerm source[3])
      let source := source.setArg 5 (← lower `psTerm source[5])
      return source.setArg 7 (← lower `psTerm source[7])
    if source.isOfKind ``Lean.Parser.Term.typeAscription then
      unless source.getArgs.size == 5 && source[3].getArgs.size <= 1 do
        Macro.throwError "PS0V1-ASCRIPTION: unexpected native value/type roles"
      let source := source.setArg 1 (← lower `psTerm source[1])
      if source[3].getArgs.isEmpty then return source
      return source.setArg 3 (source[3].setArg 0 (← lower `psTerm source[3][0]))
    if source.isOfKind ``Lean.Parser.Term.byTactic then
      unless source.getArgs.size == 2 do Macro.throwError "PS0V1-BY: unexpected native tactic term"
      return source.setArg 1 (← lowerNativeTacticSequence source[1])
    if source.isOfKind ``Lean.Parser.Term.structInst then
      return ← lowerNativeRecord source
    if source.isOfKind ``Lean.Parser.Term.«match» then
      return ← lowerNativeMatch source
    if source.isOfKind ``Lean.Parser.Term.«fun» && source.getArgs.size == 2 &&
        source[1].isOfKind ``Lean.Parser.Term.matchAlts then
      return source.setArg 1 (← lowerNativeMatchAlternatives source[1])
    if source.isOfKind ``Lean.Parser.Term.«let» then
      unless source.getArgs.size == 5 && source[2].isOfKind ``Lean.Parser.Term.letDecl &&
          source[2].getArgs.size == 1 do
        Macro.throwError "PS0V1-LOCAL-LET: unexpected native term shape"
      let source := source.setArg 2 (source[2].setArg 0 (← lowerNativeLocalId source[2][0]))
      return source.setArg 4 (← lower `psTerm source[4])
    if source.isOfKind ``Lean.Parser.Term.letrec then
      unless source.getArgs.size == 4 do
        Macro.throwError "PS0V1-LOCAL-REC: unexpected native term shape"
      let source := source.setArg 1 (← lowerNativeRecursiveDeclarations source[1])
      return source.setArg 3 (← lower `psTerm source[3])
    if source.isOfKind ``Lean.Parser.Term.termUnless then
      return ← lowerNativeUnless source
    if source.isOfKind ``ps0NativeTermBridge then
      let native := source[0]
      rejectHostGap native
      if native.isOfKind ``Lean.Parser.Term.proj then
        checkProjectionSubject native[0]
      return native
    if source.isOfKind `PS0.Operators.ownedBinary then
      let native := source[0]
      if native.isOfKind choiceKind then
        let alternatives ← native.getArgs.mapM fun alternative =>
          lower `psTerm (.node .none `PS0.Operators.ownedBinary #[alternative])
        return native.setArgs alternatives
      unless native.getArgs.size == 3 do Macro.throwError "PS0V1-OP-LOWER: invalid owned operator"
      let lhs ← lower `psTerm native[0]
      let rhs ← lower `psTerm native[2]
      return (native.setArg 0 lhs).setArg 2 rhs
    if source.isOfKind `PS0.Operators.ownedPostfix then
      let native := source[0]
      if (PS0.Operators.indexArity? native.getKind).isSome then
        return ← lowerNativeIndex native false
      if (PS0.Operators.sliceShape? native.getKind).isSome then
        return ← lowerNativeSlice native false
      if native.isOfKind ``Lean.Parser.Term.pipeProj && native.getArgs.size == 5 then
        let arguments ← native[4].getArgs.mapM fun argument => do
          if argument.isOfKind ``Lean.Parser.Term.ellipsis then return argument
          if argument.isOfKind ``Lean.Parser.Term.namedArgument then
            return argument.setArg 3 (← lower `psTerm argument[3])
          return ← lower `psTerm argument
        return (native.setArg 0 (← lower `psTerm native[0])).setArg 4 (native[4].setArgs arguments)
      unless native.isOfKind ``Lean.Parser.Term.proj && native.getArgs.size == 3 do
        Macro.throwError "PS0V1-PROJECTION-SHAPE: unexpected native projection"
      return native.setArg 0 (← lower `psTerm native[0])
    match source with
    | `(psTerm| $head:ident($[$args:psCallArg],*)) => lowerCall head.raw args source
    | `(psTerm| $head:psHead) => lowerHead head.raw
    | `(psTerm| ($body:psTerm)) => do
        return .node (loweringInfo source) ``Lean.Parser.Term.paren
          #[source[0], ← lower `psTerm body.raw, source[2]]
    | `(psTerm| { $body:psTerm }) => do
        if let some identifier := punningIdentifier? body.raw then
          let field : TSyntax `ident := ⟨identifier⟩
          let record ← `({ $field:ident })
          return ← nativeBraceOrigins source record.raw
        let body : TSyntax `term := ⟨← lower `psTerm body.raw⟩
          let collection ← `({ $body:term })
          return ← nativeBraceOrigins source collection.raw
    | `(psTerm| if $cond:psTerm then $yes:psTerm else $no:psTerm) => do
        let cond : TSyntax `term := ⟨← lower `psTerm cond.raw⟩
        let yes : TSyntax `term := ⟨← lower `psTerm yes.raw⟩
        let no : TSyntax `term := ⟨← lower `psTerm no.raw⟩
        return (← `(if $cond then $yes else $no)).raw
    | `(psTerm| fun $binders:psFunBinder* $[: $ty:psTerm]? => $body:psTerm) => do
        let binders ← binders.mapM fun binder => lowerFunBinder binder.raw
        let ty ← ty.mapM fun t => do return (⟨← lower `psTerm t.raw⟩ : TSyntax `term)
        let body : TSyntax `term := ⟨← lower `psTerm body.raw⟩
        let native ← `(fun $binders:funBinder* $[: $ty:term]? => $body:term)
        return .node (loweringInfo source) ``Lean.Parser.Term.fun
          #[source[0], native.raw[1].setArg 2 source[3]]
    | `(psTerm| by { $[$items:psTactic];* }) => do
        let items ← items.mapM fun item => do
          return (⟨← lower `psTactic item.raw⟩ : TSyntax `tactic)
        return (← `(by { $[$items:tactic];* })).raw
    | `(psTerm| do $seq:psDoSeq) => do
        let seq : TSyntax ``Lean.Parser.Term.doSeq := ⟨← lower `psDoSeq seq.raw⟩
        return (← `(do $seq:doSeq)).raw
    | _ => do
        if let some expanded ← Macro.expandMacro? source then
          lower category expanded
        else Macro.throwError s!"PS0V1-HOST-LOWER: unsupported psTerm {source.getKind} / {source.getArgs.size}"
  else if category == `psCommand then
    match source with
    | `(psCommand| $native:command) => return native.raw
    | _ => Macro.throwError "PS0V1-HOST-LOWER: unsupported psCommand"
  else if category == `psTactic then
    match source with
    | `(psTactic| exact $body:psTerm) => do
        let body : TSyntax `term := ⟨← lower `psTerm body.raw⟩
        let native ← `(tactic| exact $body)
        return .node (loweringInfo source) native.raw.getKind (native.raw.setArg 0 source[0]).getArgs
    | `(psTactic| apply $body:psTerm) => do
        let body : TSyntax `term := ⟨← lower `psTerm body.raw⟩
        let native ← `(tactic| apply $body)
        return .node (loweringInfo source) native.raw.getKind (native.raw.setArg 0 source[0]).getArgs
    | `(psTactic| refine $body:psTerm) => do
        let body : TSyntax `term := ⟨← lower `psTerm body.raw⟩
        let native ← `(tactic| refine $body)
        return .node (loweringInfo source) native.raw.getKind (native.raw.setArg 0 source[0]).getArgs
    | `(psTactic| $native:tactic) => return native.raw
    | _ => Macro.throwError "PS0V1-HOST-LOWER: unsupported psTactic"
  else if category == `psDoSeq then
    if source.isOfKind ``ps0NativeLayoutDoSeq then
      return ← lowerNativeDoSequence source[0]
    match source with
    | `(psDoSeq| { $items:psDoItem* }) => do
        let mut nativeItems := #[]
        for item in items do
          let native ← lowerDoElem item.raw[0]
          nativeItems := nativeItems.push <| .node (loweringInfo item.raw)
            ``Lean.Parser.Term.doSeqItem #[native, item.raw[1]]
        return .node (loweringInfo source) ``Lean.Parser.Term.doSeqBracketed
          #[source[0], mkNullNode nativeItems, source[2]]
    | `(psDoSeq| $native:doSeq) => return native.raw
    | _ => Macro.throwError "PS0V1-HOST-LOWER: unsupported psDoSeq"
  else Macro.throwError s!"PS0V1-HOST-LOWER: unrecognized PS category {category}"

partial def lowerBodyValue (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  if source.isOfKind ``ps0HostBraces && (punningIdentifier? source[1]).isNone then
    let body : TSyntax `term := ⟨← lower `psTerm source[1]⟩
    let native ← `(($body))
    unless native.raw.isOfKind ``Lean.Parser.Term.paren && native.raw.getArgs.size == 3 &&
        native.raw[0].isOfKind ``Lean.Parser.Term.hygienicLParen && native.raw[0].getArgs.size == 2 do
      Macro.throwError "PS0V1-BODY-WRAPPER: unexpected native parenthesis shape"
    let opening : Lean.Syntax := .node (loweringInfo source[0]) ``Lean.Parser.Term.hygienicLParen
      #[.atom (loweringInfo source[0]) "(", native.raw[0][1]]
    return .node (loweringInfo source) native.raw.getKind
      #[opening, body.raw, .atom (loweringInfo source[2]) ")"]
  lower `psTerm source

partial def lowerDoElem (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  if source.isOfKind ``Lean.Parser.Term.doFor then
    unless source.getArgs.size == 6 do Macro.throwError "PS0V1-DO-FOR: unexpected native loop"
    let declarations ← source[1].getArgs.mapM fun declaration => do
      if declaration.isAtom then return declaration
      unless declaration.isOfKind ``Lean.Parser.Term.doForDecl && declaration.getArgs.size == 4 do
        Macro.throwError "PS0V1-DO-FOR: unexpected native pattern/collection roles"
      return declaration.setArg 3 (← lower `psTerm declaration[3])
    -- Loop contract annotations retain their native grammar in this finite stage.
    return (source.setArg 1 (source[1].setArgs declarations)).setArg 5
      (← lowerNativeDoSequence source[5])
  if source.isOfKind ``Lean.Parser.Term.doTry then
    return ← lowerNativeTry source
  if source.isOfKind ``Lean.Parser.Term.doMatch then
    unless source.getArgs.size == 7 do
      Macro.throwError "PS0V1-DO-MATCH: unexpected native match shape"
    let view := source.setArgs #[source[0], source[2], source[3], source[4], source[5], source[6]]
    let lowered ← lowerNativeMatch view true
    return source.setArgs #[lowered[0], source[1], lowered[1], lowered[2], lowered[3], lowered[4], lowered[5]]
  if source.isOfKind ``Lean.Parser.Term.doHave then
    unless source.getArgs.size == 3 && source[2].isOfKind ``Lean.Parser.Term.letDecl &&
        source[2].getArgs.size == 1 do
      Macro.throwError "PS0V1-DO-HAVE: unexpected native named declaration"
    return source.setArg 2 (source[2].setArg 0 (← lowerNativeLocalId source[2][0]))
  if source.isOfKind ``Lean.Parser.Term.doIf then
    unless source.getArgs.size == 6 do
      Macro.throwError "PS0V1-DO-IF: unexpected native branch shape"
    return source.setArgs (← source.getArgs.mapM lowerNativeIfRole)
  if source.isOfKind ``Lean.Parser.Term.doLetElse then
    unless source.getArgs.size == 9 && source[8].getArgs.size <= 1 do
      Macro.throwError "PS0V1-DO-PATTERN-LET: unexpected native fallback/continuation"
    let source := source.setArg 5 (← lower `psTerm source[5])
    let source := source.setArg 7 (← lowerNativeDoSequence source[7])
    if source[8].getArgs.isEmpty then return source
    return source.setArg 8 (source[8].setArg 0 (← lowerNativeDoSequence source[8][0]))
  if source.isOfKind ``Lean.Parser.Term.doLetRec then
    unless source.getArgs.size == 2 do
      Macro.throwError "PS0V1-LOCAL-REC: unexpected native do shape"
    return source.setArg 1 (← lowerNativeRecursiveDeclarations source[1])
  if source.isOfKind ``Lean.Parser.Term.doUnless then
    return ← lowerNativeUnless source
  if source.isOfKind ``Lean.Parser.Term.doLet then
    unless source.getArgs.size == 4 && source[3].isOfKind ``Lean.Parser.Term.letDecl &&
        source[3].getArgs.size == 1 do
      Macro.throwError "PS0V1-DO-LET: unexpected native ID declaration"
    return source.setArg 3 (source[3].setArg 0 (← lowerNativeLocalId source[3][0]))
  if source.isOfKind ``Lean.Parser.Term.doReassign then
    unless source.getArgs.size == 1 do Macro.throwError "PS0V1-DO-ASSIGN: unexpected native ID assignment"
    return source.setArg 0 (← lowerNativeLocalId source[0])
  if source.isOfKind ``Lean.Parser.Term.doLetArrow then
    unless source.getArgs.size == 4 do Macro.throwError "PS0V1-DO-BIND: unexpected native binding"
    let decl := source[3]
    if decl.isOfKind ``Lean.Parser.Term.doPatDecl then
      return source.setArg 3 (← lowerNativePatternBind decl)
    unless decl.isOfKind ``Lean.Parser.Term.doIdDecl && decl.getArgs.size == 4 do
      Macro.throwError "PS0V1-DO-BIND: unexpected native ID binding"
    let decl := decl.setArg 1 (← lowerNativeOptionalType decl[1])
    return source.setArg 3 (decl.setArg 3 (← lowerDoElem decl[3]))
  if source.isOfKind ``Lean.Parser.Term.doNested then
    unless source.getArgs.size == 2 do Macro.throwError "PS0V1-DO-NESTED: unexpected native block"
    return source.setArg 1 (← lowerNativeDoSequence source[1])
  if source.isOfKind ``Lean.Parser.Term.doReturn then
    unless source.getArgs.size == 2 && source[1].getArgs.size <= 1 do
      Macro.throwError "PS0V1-DO-RETURN: unexpected native return"
    if source[1].getArgs.isEmpty then return source
    return source.setArg 1 (source[1].setArg 0 (← lower `psTerm source[1][0]))
  if source.isOfKind ``Lean.Parser.Term.doExpr then
    unless source.getArgs.size == 1 do Macro.throwError "PS0V1-DO-EXPRESSION: unexpected native expression"
    return source.setArg 0 (← lower `psTerm source[0])
  match source with
  | `(psDoElem| let mut $name:ident $[: $ty:psTerm]? := $value:psTerm) => do
      let ty ← ty.mapM fun t => do return (⟨← lower `psTerm t.raw⟩ : TSyntax `term)
      let value : TSyntax `term := ⟨← lowerBodyValue value.raw⟩
      return (← `(doElem| let mut $name:ident $[: $ty:term]? := $value)).raw
  | `(psDoElem| let $name:ident $[: $ty:psTerm]? := $value:psTerm) => do
      let ty ← ty.mapM fun t => do return (⟨← lower `psTerm t.raw⟩ : TSyntax `term)
      let value : TSyntax `term := ⟨← lowerBodyValue value.raw⟩
      return (← `(doElem| let $name:ident $[: $ty:term]? := $value)).raw
  | `(psDoElem| let $name:ident ← $value:psTerm) => do
      let value : TSyntax `term := ⟨← lower `psTerm value.raw⟩
      let action : TSyntax `doElem := ⟨.node (loweringInfo source)
        ``Lean.Parser.Term.doExpr #[value.raw]⟩
      return (← `(doElem| let $name:ident ← $action:doElem)).raw
  | `(psDoElem| $name:ident := $value:psTerm) => do
      let value : TSyntax `term := ⟨← lower `psTerm value.raw⟩
      return (← `(doElem| $name:ident := $value:term)).raw
  | `(psDoElem| $value:psTerm) => do
      let value : TSyntax `term := ⟨← lower `psTerm value.raw⟩
      return (← `(doElem| $value:term)).raw
  | `(psDoElem| $native:doElem) => return native.raw
  | _ => Macro.throwError "PS0V1-HOST-LOWER: unsupported psDoElem"

partial def lowerFunType (optionalType : Lean.Syntax) : MacroM Lean.Syntax := do
  if optionalType.getArgs.isEmpty then return optionalType
  return optionalType.setArg 1 (← lower `psTerm optionalType[1])

partial def lowerNativeMatchAlternatives (source : Lean.Syntax) (sequence : Bool := false) : MacroM Lean.Syntax := withRef source do
  unless source.isOfKind ``Lean.Parser.Term.matchAlts && source.getArgs.size == 1 do
    Macro.throwError "PS0V1-MATCH-ALTERNATIVES: unexpected native alternatives"
  let alternatives ← source[0].getArgs.mapM fun alternative => do
    unless alternative.isOfKind ``Lean.Parser.Term.matchAlt && alternative.getArgs.size == 4 do
      Macro.throwError "PS0V1-MATCH-ALTERNATIVE: unexpected native pattern/body roles"
    let rhs ← if sequence then lowerNativeDoSequence alternative[3] else lower `psTerm alternative[3]
    return alternative.setArg 3 rhs
  return source.setArg 0 (source[0].setArgs alternatives)

partial def lowerNativeIfRole (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  if source.isOfKind ``Lean.Parser.Term.doIfProp && source.getArgs.size == 2 then
    return source.setArg 1 (← lower `psTerm source[1])
  if source.isOfKind ``Lean.Parser.Term.doIfLet && source.getArgs.size == 3 then
    let value := source[2]
    unless (value.isOfKind ``Lean.Parser.Term.doIfLetPure ||
        value.isOfKind ``Lean.Parser.Term.doIfLetBind) && value.getArgs.size == 2 do
      Macro.throwError "PS0V1-DO-IF-LET: unexpected native value role"
    return source.setArg 2 (value.setArg 1 (← lower `psTerm value[1]))
  if source.isOfKind ``Lean.Parser.Term.doSeqIndent ||
      source.isOfKind ``Lean.Parser.Term.doSeqBracketed then
    return ← lowerNativeDoSequence source
  if source.isOfKind nullKind || source.isOfKind `group then
    return source.setArgs (← source.getArgs.mapM lowerNativeIfRole)
  if source.isAtom || source.isOfKind ``Lean.Parser.Term.elseIf then return source
  Macro.throwError s!"PS0V1-DO-IF-ROLE: unexpected native condition/sequence role {source.getKind}"

partial def lowerNativeTry (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  unless source.getArgs.size == 4 && source[3].getArgs.size <= 1 do
    Macro.throwError "PS0V1-DO-TRY: unexpected native try/catch/finally"
  let source := source.setArg 1 (← lowerNativeDoSequence source[1])
  let catches ← source[2].getArgs.mapM fun branch => do
    if branch.isOfKind ``Lean.Parser.Term.doCatchMatch && branch.getArgs.size == 2 then
      return branch.setArg 1 (← lowerNativeMatchAlternatives branch[1] true)
    unless branch.isOfKind ``Lean.Parser.Term.doCatch && branch.getArgs.size == 5 do
      Macro.throwError "PS0V1-DO-CATCH: unexpected native catch"
    let branch ← if branch[2].getArgs.isEmpty then pure branch else do
      unless branch[2].getArgs.size == 2 do Macro.throwError "PS0V1-DO-CATCH: unexpected exception type"
      pure <| branch.setArg 2 (branch[2].setArg 1 (← lower `psTerm branch[2][1]))
    return branch.setArg 4 (← lowerNativeDoSequence branch[4])
  let source := source.setArg 2 (source[2].setArgs catches)
  if source[3].getArgs.isEmpty then return source
  let finalizer := source[3][0]
  unless finalizer.isOfKind ``Lean.Parser.Term.doFinally && finalizer.getArgs.size == 2 do
    Macro.throwError "PS0V1-DO-FINALLY: unexpected native finalizer"
  return source.setArg 3 (source[3].setArg 0
    (finalizer.setArg 1 (← lowerNativeDoSequence finalizer[1])))

partial def lowerNativeRecordField (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  unless source.isOfKind ``Lean.Parser.Term.structInstField && source.getArgs.size == 2 do
    Macro.throwError "PS0V1-RECORD-FIELD: unexpected native field"
  let lvalue := source[0]
  let components ← lvalue.getArgs.mapM fun part => do
    if part.isOfKind ``Lean.Parser.Term.structInstArrayRef then
      return part.setArg 1 (← lower `psTerm part[1])
    if part.isOfKind nullKind then
      return part.setArgs (← part.getArgs.mapM fun child => do
        if child.isOfKind ``Lean.Parser.Term.structInstArrayRef then
          return child.setArg 1 (← lower `psTerm child[1])
        return child)
    return part
  let source := source.setArg 0 (lvalue.setArgs components)
  if source[1].getArgs.isEmpty then return source
  unless source[1].getArgs.size == 3 do
    Macro.throwError "PS0V1-RECORD-FIELD: unexpected native binder/type/value roles"
  let body := source[1]
  let binders ← body[0].getArgs.mapM lowerNativeLocalBinder
  let body := body.setArg 0 (body[0].setArgs binders)
  let body := body.setArg 1 (← lowerNativeOptionalType body[1])
  let rhs := body[2]
  let rhs ← if rhs.isOfKind ``Lean.Parser.Term.structInstFieldDef && rhs.getArgs.size == 3 then
      pure <| rhs.setArg 2 (← lower `psTerm rhs[2])
    else if rhs.isOfKind ``Lean.Parser.Term.structInstFieldEqns && rhs.getArgs.size == 2 then
      pure <| rhs.setArg 1 (← lowerNativeMatchAlternatives rhs[1])
    else Macro.throwError "PS0V1-RECORD-FIELD: unexpected native field declaration"
  return source.setArg 1 (body.setArg 2 rhs)

partial def lowerNativeRecord (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  unless source.getArgs.size == 6 && source[2].isOfKind ``Lean.Parser.Term.structInstFields do
    Macro.throwError "PS0V1-RECORD: unexpected native structure instance"
  let update := source[1]
  let source ← if update.getArgs.isEmpty then pure source else do
    unless update.getArgs.size == 2 do Macro.throwError "PS0V1-RECORD: unexpected native update sources"
    let values ← update[0].getArgs.mapM fun value => do
      if value.isAtom then return value
      lower `psTerm value
    pure <| source.setArg 1 (update.setArg 0 (update[0].setArgs values))
  let fields ← source[2][0].getArgs.mapM fun field => do
    if field.isAtom || field.isOfKind nullKind then return field
    lowerNativeRecordField field
  let source := source.setArg 2 (source[2].setArg 0 (source[2][0].setArgs fields))
  if source[4].getArgs.isEmpty then return source
  unless source[4].getArgs.size == 2 do Macro.throwError "PS0V1-RECORD: unexpected native result type"
  return source.setArg 4 (source[4].setArg 1 (← lower `psTerm source[4][1]))

partial def lowerNativeMatch (source : Lean.Syntax) (sequence : Bool := false) : MacroM Lean.Syntax := withRef source do
  unless source.getArgs.size == 6 && source[2].getArgs.size <= 1 do
    Macro.throwError "PS0V1-MATCH-SHAPE: unexpected native match"
  let source ← if source[2].getArgs.isEmpty then pure source else do
    let motive := source[2][0]
    unless motive.isOfKind ``Lean.Parser.Term.motive && motive.getArgs.size == 5 do
      Macro.throwError "PS0V1-MATCH-MOTIVE: unexpected native motive"
    pure <| source.setArg 2 (source[2].setArg 0 (motive.setArg 3 (← lower `psTerm motive[3])))
  let discriminants ← source[3].getArgs.mapM fun discriminant => do
    if discriminant.isAtom then return discriminant
    unless discriminant.isOfKind ``Lean.Parser.Term.matchDiscr && discriminant.getArgs.size == 2 do
      Macro.throwError "PS0V1-MATCH-DISCRIMINANT: unexpected native discriminant"
    return discriminant.setArg 1 (← lower `psTerm discriminant[1])
  return (source.setArg 3 (source[3].setArgs discriminants)).setArg 5
    (← lowerNativeMatchAlternatives source[5] sequence)

partial def lowerNativeDoSequence (native : Lean.Syntax) : MacroM Lean.Syntax := do
  let index ← if native.isOfKind ``Lean.Parser.Term.doSeqIndent then pure 0
    else if native.isOfKind ``Lean.Parser.Term.doSeqBracketed then pure 1
    else Macro.throwError "PS0V1-DO-LAYOUT: unexpected native sequence"
  let items ← native[index].getArgs.mapM fun item => do
    unless item.isOfKind ``Lean.Parser.Term.doSeqItem && item.getArgs.size == 2 do
      Macro.throwError "PS0V1-DO-LAYOUT: unexpected native sequence item"
    return item.setArg 0 (← lowerDoElem item[0])
  return native.setArg index (native[index].setArgs items)

partial def lowerNativeTacticSequence (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  unless source.isOfKind ``Lean.Parser.Tactic.tacticSeq && source.getArgs.size == 1 do
    Macro.throwError "PS0V1-TACTIC-SEQUENCE: unexpected native sequence"
  let inner := source[0]
  let index ← if inner.isOfKind ``Lean.Parser.Tactic.tacticSeqBracketed && inner.getArgs.size == 3 then
      pure 1
    else if inner.isOfKind ``Lean.Parser.Tactic.tacticSeq1Indented && inner.getArgs.size == 1 then
      pure 0
    else Macro.throwError "PS0V1-TACTIC-LAYOUT: unexpected native tactic layout"
  let items ← inner[index].getArgs.mapM fun item => do
    if item.isAtom || item.isMissing || item.isOfKind nullKind then return item
    lower `psTactic item
  return source.setArg 0 (inner.setArg index (inner[index].setArgs items))

partial def lowerNativePatternBind (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  unless source.getArgs.size == 5 do
    Macro.throwError "PS0V1-DO-PATTERN-BIND: unexpected native pattern binding"
  let source := source.setArg 3 (← lowerDoElem source[3])
  let branches := source[4]
  if branches.getArgs.isEmpty then return source
  unless branches.getArgs.size == 3 && branches[2].getArgs.size <= 1 do
    Macro.throwError "PS0V1-DO-PATTERN-BRANCHES: unexpected native fallback/continuation"
  let branches := branches.setArg 1 (← lowerNativeDoSequence branches[1])
  let branches ← if branches[2].getArgs.isEmpty then pure branches else
    pure <| branches.setArg 2 (branches[2].setArg 0 (← lowerNativeDoSequence branches[2][0]))
  return source.setArg 4 branches

partial def lowerNativeUnless (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  unless source.getArgs.size == 4 && source[0].isAtom && source[0].getAtomVal == "unless" &&
      source[2].isAtom && source[2].getAtomVal == "do" do
    Macro.throwError "PS0V1-UNLESS-SHAPE: unexpected native control node"
  let source := source.setArg 1 (← lower `psTerm source[1])
  return source.setArg 3 (← lowerNativeDoSequence source[3])

partial def lowerNativeOptionalType (source : Lean.Syntax) : MacroM Lean.Syntax := do
  if source.getArgs.isEmpty then return source
  unless source.getArgs.size == 1 && source[0].isOfKind ``Lean.Parser.Term.typeSpec &&
      source[0].getArgs.size == 2 do Macro.throwError "PS0V1-LOCAL-TYPE: unexpected native type specification"
  return source.setArg 0 (source[0].setArg 1 (← lower `psTerm source[0][1]))

partial def lowerNativeLocalBinder (source : Lean.Syntax) : MacroM Lean.Syntax := do
  if source.isIdent || source.isOfKind ``Lean.Parser.Term.hole then return source
  if source.isOfKind ``Lean.Parser.Term.instBinder then
    return source.setArg 2 (← lower `psTerm source[2])
  unless source.isOfKind ``Lean.Parser.Term.explicitBinder ||
      source.isOfKind ``Lean.Parser.Term.implicitBinder ||
      source.isOfKind ``Lean.Parser.Term.strictImplicitBinder do
    Macro.throwError "PS0V1-LOCAL-BINDER: unexpected native binder"
  let source := source.setArg 2 (← lowerFunType source[2])
  if source.isOfKind ``Lean.Parser.Term.explicitBinder && !source[3].getArgs.isEmpty &&
      source[3][0].isOfKind ``Lean.Parser.Term.binderDefault then
    return source.setArg 3 (source[3].setArg 0
      (source[3][0].setArg 1 (← lower `psTerm source[3][0][1])))
  return source

partial def lowerLocalBinder (source : Lean.Syntax) : MacroM (Array Lean.Syntax) := withRef source do
  if source.isOfKind choiceKind then
    let mut result? : Option (Array Lean.Syntax) := none
    for alternative in source.getArgs do
      let candidate ← lowerLocalBinder alternative
      if let some previous := result? then
        unless sameLocalBinders previous candidate do
          Macro.throwError "PS0V1-BINDER-AMBIGUITY: different successful binder partitions"
        -- Coalescing keeps the original native delimiters/source information.
        -- Every alternative is still normalized and checked before elaboration.
        if alternative.isOfKind ``ps0NativeLocalBinder then result? := some candidate
      else result? := some candidate
    return result?.getD #[]
  if source.isOfKind ``ps0NativeLocalBinder then
    return #[← lowerNativeLocalBinder source[0]]
  if let some expanded ← Macro.expandMacro? source then
    return expanded.getArgs
  Macro.throwError "PS0V1-LOCAL-BINDER: missing local telescope adapter"

partial def sameLocalTree (a b : Lean.Syntax) : Bool :=
  match a, b with
  | .missing, .missing => true
  | .atom _ x, .atom _ y => x == y
  | .ident _ _ x _, .ident _ _ y _ => x == y
  | .node _ k xs, .node _ j ys =>
      k == j && xs.size == ys.size && (xs.zip ys).all (fun (x, y) => sameLocalTree x y)
  | _, _ => false

partial def sameLocalBinders (a b : Array Lean.Syntax) : Bool :=
  a.size == b.size && (a.zip b).all (fun (x, y) => sameLocalTree x y)

partial def lowerLocalTelescope (parts : Array Lean.Syntax) : MacroM (Array Lean.Syntax) := do
  let mut result := #[]
  for part in parts do
    result := result ++ (← lowerLocalBinder part)
  return result

partial def retainLocalGroup (source : Lean.Syntax) (binders : Array Lean.Syntax) : Lean.Syntax :=
  let group := source.setArgs binders
  if group.getRange? == source.getRange? then group
  else .node (loweringInfo source) source.getKind binders

partial def lowerNativeLocalId (source : Lean.Syntax) : MacroM Lean.Syntax := do
  unless (source.isOfKind ``Lean.Parser.Term.letIdDecl ||
      source.isOfKind ``Lean.Parser.Term.letIdDeclNoBinders) && source.getArgs.size == 5 do
    Macro.throwError "PS0V1-LOCAL-ID: unexpected native declaration"
  let binders ← lowerLocalTelescope source[1].getArgs
  let source := source.setArg 1 (retainLocalGroup source[1] binders)
  let source := source.setArg 2 (← lowerNativeOptionalType source[2])
  let value ← if source.isOfKind ``Lean.Parser.Term.letIdDecl then
      lowerBodyValue source[4]
    else lower `psTerm source[4]
  return source.setArg 4 value

partial def lowerNativeRecursiveDeclarations (source : Lean.Syntax) : MacroM Lean.Syntax := do
  unless source.isOfKind ``Lean.Parser.Term.letRecDecls && source.getArgs.size == 1 do
    Macro.throwError "PS0V1-LOCAL-REC: unexpected native declaration group"
  let items ← source[0].getArgs.mapM fun declaration => do
    if declaration.isAtom || declaration.isOfKind nullKind then return declaration
    unless declaration.isOfKind ``Lean.Parser.Term.letRecDecl && declaration.getArgs.size == 4 &&
        declaration[2].isOfKind ``Lean.Parser.Term.letDecl && declaration[2].getArgs.size == 1 do
      Macro.throwError "PS0V1-LOCAL-REC: unexpected native recursive declaration"
    let value := declaration[2][0]
    let value ← if value.isOfKind ``Lean.Parser.Term.letIdDecl then
        lowerNativeLocalId value
      else do
        unless value.isOfKind ``Lean.Parser.Term.letEqnsDecl && value.getArgs.size == 4 &&
            value[3].isOfKind ``Lean.Parser.Term.matchAlts do
          Macro.throwError "PS0V1-LOCAL-REC: unexpected native recursive value"
        let binders ← lowerLocalTelescope value[1].getArgs
        let value := value.setArg 1 (retainLocalGroup value[1] binders)
        let value := value.setArg 2 (← lowerNativeOptionalType value[2])
        let alternatives ← value[3][0].getArgs.mapM fun alternative => do
          unless alternative.isOfKind ``Lean.Parser.Term.matchAlt && alternative.getArgs.size == 4 do
            Macro.throwError "PS0V1-LOCAL-REC: unexpected native equation alternative"
          return alternative.setArg 3 (← lower `psTerm alternative[3])
        pure <| value.setArg 3 (value[3].setArg 0 (value[3][0].setArgs alternatives))
    return declaration.setArg 2 (declaration[2].setArg 0 value)
  return source.setArg 0 (source[0].setArgs items)

partial def lowerFunBinder (source : Lean.Syntax) :
    MacroM (TSyntax ``Lean.Parser.Term.funBinder) := withRef source do
  if source.isOfKind ``ps0NativeFunBinderBridge then return ⟨source[0]⟩
  if source.isOfKind ``ps0FunExplicit then
    let names := source[1].getArgs
    let head := if names.size == 1 then names[0]! else
      .node (loweringInfo source) ``Lean.Parser.Term.app #[names[0]!, mkNullNode (names.extract 1 names.size)]
    let head : TSyntax `term := ⟨head⟩
    let ty : TSyntax `term := ⟨← lower `psTerm source[3]⟩
    return ⟨(← `(($head:term : $ty:term))).raw⟩
  if source.isOfKind ``ps0FunImplicit || source.isOfKind ``ps0FunStrict then
    let kind := if source.isOfKind ``ps0FunImplicit then
      ``Lean.Parser.Term.implicitBinder else ``Lean.Parser.Term.strictImplicitBinder
    return ⟨.node (loweringInfo source) kind
      #[source[0], source[1], ← lowerFunType source[2], source[3]]⟩
  if source.isOfKind ``ps0FunInstance then
    return ⟨.node (loweringInfo source) ``Lean.Parser.Term.instBinder
      #[source[0], source[1], ← lower `psTerm source[2], source[3]]⟩
  Macro.throwError "PS0V1-LAMBDA-BINDER: unsupported owned lambda binder"

partial def lowerHead (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  if source.isOfKind `PS0.Operators.ownedPostfix then
    let native := source[0]
    if (PS0.Operators.indexArity? native.getKind).isSome then
      return ← lowerNativeIndex native true
    if (PS0.Operators.sliceShape? native.getKind).isSome then
      return ← lowerNativeSlice native true
    unless native.isOfKind ``Lean.Parser.Term.proj && native.getArgs.size == 3 do
      Macro.throwError "PS0V1-PROJECTION-SHAPE: unexpected native head projection"
    return native.setArg 0 (← lowerHead native[0])
  match source with
  | `(psHead| $head:psHead($[$args:psCallArg],*)) =>
      lowerCall (← lowerHead head.raw) args source
  | `(psHead| $head:psHead()) =>
      return .node (loweringInfo source) `PS0.pscvEmptyCall
        #[← lowerHead head.raw, mkAtom "(", mkAtom ")"]
  | `(psHead| ($body:psTerm)) => do
      return .node (loweringInfo source) ``Lean.Parser.Term.paren
        #[source[0], ← lower `psTerm body.raw, source[2]]
  | `(psHead| $native:term) => do
      rejectHostGap native.raw
      if native.raw.isOfKind ``Lean.Parser.Term.proj then
        checkProjectionSubject native.raw[0]
      return native.raw
  | _ => Macro.throwError "PS0V1-HOST-LOWER: unsupported postfix head"

partial def lowerNativeSlice (source : Lean.Syntax) (head : Bool) : MacroM Lean.Syntax := do
  let some (arity, bounds) := PS0.Operators.sliceShape? source.getKind
    | Macro.throwError "PS0V1-SLICE-SHAPE: unsupported native array slice"
  unless source.getArgs.size == arity && source[1].isAtom && source[1].getAtomVal == "[" do
    Macro.throwError "PS0V1-SLICE-SHAPE: unexpected native array slice"
  let subject ← if head then lowerHead source[0] else lower `psTerm source[0]
  let mut result := source.setArg 0 subject
  for index in bounds do
    result := result.setArg index (← lower `psTerm source[index])
  return result

partial def lowerNativeIndex (source : Lean.Syntax) (head : Bool) : MacroM Lean.Syntax := do
  let some arity := PS0.Operators.indexArity? source.getKind
    | Macro.throwError "PS0V1-INDEX-SHAPE: unsupported native indexed access"
  let index := if arity == 7 then 3 else 2
  unless source.getArgs.size == arity && source[index - 1].isAtom &&
      source[index - 1].getAtomVal == "[" do
    Macro.throwError "PS0V1-INDEX-SHAPE: unexpected native indexed access"
  let subject ← if head then lowerHead source[0] else lower `psTerm source[0]
  let source := (source.setArg 0 subject).setArg index (← lower `psTerm source[index])
  if source.isOfKind `«term__[_]'_» then
    return source.setArg 4 (← lower `psTerm source[4])
  return source

partial def lowerCall (head : Lean.Syntax) (args : Array (TSyntax `psCallArg))
    (source : Lean.Syntax) : MacroM Lean.Syntax := withRef source do
  let mut positional := true
  let mut seen : Array Name := #[]
  let mut nativeArgs : Array Lean.Syntax := #[]
  for arg in args do
    if arg.raw.isOfKind ``ps0NativeEllipsisArg then
      unless positional do
        withRef arg do Macro.throwError "PS0V1-CALL-ORDER: positional argument after named argument"
      let completion := arg.raw[0]
      unless completion.isOfKind ``Lean.Parser.Term.ellipsis && completion.getArgs.size == 1 do
        Macro.throwError "PS0V1-CALL-ELLIPSIS: unexpected native completion argument"
      nativeArgs := nativeArgs.push completion
      continue
    match arg with
    | `(psCallArg| $name:ident := $value:psTerm) =>
        let n := name.getId
        if seen.contains n then
          withRef name do Macro.throwError s!"PS0V1-CALL-NAMED: duplicate named argument {n}"
        positional := false
        seen := seen.push n
        let value : TSyntax `term := ⟨← lower `psTerm value.raw⟩
        nativeArgs := nativeArgs.push (← `(Lean.Parser.Term.namedArgument| ($name := $value))).raw
    | `(psCallArg| $value:psTerm) =>
        unless positional do
          withRef arg do Macro.throwError "PS0V1-CALL-ORDER: positional argument after named argument"
        nativeArgs := nativeArgs.push (← lower `psTerm value.raw)
    | _ => Macro.throwError "PS0V1-HOST-LOWER: malformed psCallArg"
  -- Native expandArgs reads a final ellipsis before separating named arguments.
  -- Keep PS named arguments last on the surface and preserve all native nodes.
  if let some index := nativeArgs.findIdx? (·.isOfKind ``Lean.Parser.Term.namedArgument) then
    if index > 0 && nativeArgs[index - 1]!.isOfKind ``Lean.Parser.Term.ellipsis then
      let completion := nativeArgs[index - 1]!
      nativeArgs := nativeArgs.extract 0 (index - 1) ++
        nativeArgs.extract index nativeArgs.size ++ #[completion]
  return .node (loweringInfo source) ``Lean.Parser.Term.app #[head, mkNullNode nativeArgs]
end
end PS0.Syntax
