import Lean
import PS0.Syntax

/-!
Standalone PS0 pre-elaboration gate for the **currently implemented** v7 command fragment.

Lean's extensible grammar is intentionally *not* a PSCV grammar. We accept
an explicit set of top-level command AST kinds, reject other commands BEFORE
running their elaborators, and refuse errors/recovery. This is not yet the
full recursive A.18 source-grammar conformance validator or a security sandbox.
-/

open Lean

namespace PS0

private def allowedDeclarationKind (kind : String) : Bool :=
  ([
    "Lean.Parser.Command.definition",
    "Lean.Parser.Command.theorem",
    "Lean.Parser.Command.example",
    "Lean.Parser.Command.abbrev",
    "Lean.Parser.Command.opaque",
    "Lean.Parser.Command.instance"
  ] : List String).contains kind

/-- Only the finite PSCV/Lean Standard and PS0 bookkeeping attributes are
admitted on declarations. Checking the elaborated declaration afterward is
not sufficient: a registered Lean attribute may run user-visible code. -/
private partial def attributeIdentifiers (s : Syntax) : List Name :=
  match s with
  | .ident _ _ val _ => [val]
  | .node _ _ args => args.toList.flatMap attributeIdentifiers
  | _ => []

private partial def rejectAttributes (s : Syntax) : Option String := Id.run do
  if s.isOfKind choiceKind then
    return s.getArgs.toList.findSome? rejectAttributes
  unless s.getKind.toString == "Lean.Parser.Command.declaration" do
    return none
  -- declaration[0] is declModifiers; its optional attribute block is field 1.
  let attrs := s[0][1]
  let permitted : List String := [
    "simp", "instance", "default_instance", "priority",
    "pscv_export", "pscv_type_spec"
  ]
  if let some bad := (attributeIdentifiers attrs).find? (fun id =>
      !permitted.contains id.toString) then
    return some s!"PS0 rejects undeclared attribute '{bad}'"
  return none

private partial def allowedCommand (s : Syntax) : Bool :=
  let k := s.getKind.toString
  if s.isOfKind choiceKind then
    -- PS0 cannot know which ambiguous alternative Lean will elaborate.
    -- Refuse the whole choice unless every candidate satisfies the closed
    -- command policy; this may reject additional valid source until the
    -- parser choice is explicitly resolved in PS0-01.
    !s.getArgs.isEmpty && s.getArgs.all allowedCommand
  else if k == "Lean.Parser.Command.declaration" then
    allowedDeclarationKind s[1].getKind.toString
  else
    ([
      "PS0.pscvConst", "PS0.pscvConstInferred",
      "PS0.pscvFunctionWhere",
      "PS0.pscvPrivateConst", "PS0.pscvPrivateConstInferred", "PS0.pscvPrivateFunction",
      "PS0.pscvFunction", "PS0.pscvImplicitFunction", "PS0.pscvTheorem",
      "PS0.pscvDefinition", "PS0.pscvFunctionInferred",
      "PS0.pscvDefinitionInferred", "PS0.pscvPrivateFunctionInferred",
      "PS0.pscvFunctionTermination", "PS0.pscvFunctionTerminationProof",
      "PS0.pscvImplicitFunctionInferred",
      "PS0.pscvTelescopeFunction", "PS0.pscvTelescopeFunctionInferred",
      "PS0.pscvTelescopeDefinition", "PS0.pscvTelescopeDefinitionInferred",
      "PS0.pscvTelescopeTheorem",
      "PS0.pscvBracedStructure", "PS0.pscvBracedInductive",
      "PS0.pscvParameterizedStructure", "PS0.pscvBracedClass", "PS0.pscvParameterizedClass",
      "PS0.pscvBracedInstanceAnonymous", "PS0.pscvBracedInstanceNamed",
      "PS0.pscvBracedInstanceTelescopeAnonymous",
      "PS0.pscvBracedInstanceTelescopeNamed",
      "PS0.pscvPrioritizedInstanceAnonymous",
      "PS0.pscvPrioritizedInstanceNamed",
      "PS0.pscvPrioritizedInstanceTelescopeAnonymous",
      "PS0.pscvPrioritizedInstanceTelescopeNamed",
      "PS0.pscvBracedMutual",
      "PS0.pscvBracedStructureDeriving", "PS0.pscvBracedInductiveDeriving",
      "PS0.pscvFunctionGivenContract", "PS0.pscvFunctionEffectContract", "PS0.pscvFunctionContract", "PS0.pscvFunctionEnsures", "PS0.pscvFunctionRequires",
      
      "Lean.Parser.Command.namespace", "Lean.Parser.Command.section",
      "Lean.Parser.Command.end", "Lean.Parser.Command.open",
      "Lean.Parser.Command.variable", "Lean.Parser.Command.universe",
      "Lean.Parser.Command.include", "Lean.Parser.Command.omit",
      "Lean.Parser.Command.check", "Lean.Parser.Command.eval", "Lean.Parser.Command.print",
      "Lean.Parser.Command.printAxioms", "Lean.reduceCmd"
    ] : List String).contains k

/-- Lean 4.35.0 Parser.Command.optDeclSig and declSig each store
    native binders in their first repetition child. V7 selects at most one
    consecutive explicit group; all intervening implicit/instance groups
    preserve the ordinary native binder telescope. This also covers
    unrestricted Lean *declaration* alternatives accepted by our overlay,
    rather than relying only on PS0 macro syntax to reject the gap. -/
private def hasAdjacentNativeExplicitGroups (decl : Syntax) : Bool := Id.run do
  let kind := decl.getKind.toString
  unless (["Lean.Parser.Command.definition",
           "Lean.Parser.Command.theorem",
           "Lean.Parser.Command.abbrev",
           "Lean.Parser.Command.opaque"] : List String).contains kind do
    return false
  let binders := decl[2][0].getArgs
  let mut lastExplicit := false
  for binder in binders do
    let isExplicit := binder.getKind == ``Lean.Parser.Term.explicitBinder
    if isExplicit && lastExplicit then
      return true
    lastExplicit := isExplicit
  return false

/-- Reject known metaprogramming and proof escapes before the Lean elaborator
runs. Ordinary strings and comments are syntax leaves, not command text. -/
private def excludedName (name : Name) : Bool :=
  let value := name.toString
  (["sorry", "sorryAx", "unsafeCast", "unsafePerformIO",
    "native_decide", "run_tac", "run_cmd",
    "partial_fixpoint", "unsafe", "macro", "macro_rules",
    "extern", "nativeDecide", "evalConst", "EIO", "BaseIO",
    "IO"] : List String).any (fun banned =>
      value == banned || value.endsWith ("." ++ banned))

/- An identifier is different from a keyword token in Lean's syntax tree.
Apply the source exclusions to both; otherwise imported built-in primitives
can bypass restrictions that checked only `Syntax.atom` keywords. -/
/-- The PSCV A.18 while grammar requires both an invariant and a
decreasing measure. Lean accepts weaker loop surface forms; parse-time
normalization must NOT silently promote those forms to PSCV. -/
private partial def forbiddenLoop (s : Syntax) : Option String :=
  match s with
  | .node _ kind args =>
    if kind == ``Lean.Parser.Term.doWhile then
      if s[2].isNone then
        some "PSCV while requires an explicit invariant"
      else if s[3].isNone then
        some "PSCV while requires an explicit decreasing measure"
      else
        args.toList.findSome? forbiddenLoop
    else if kind == ``Lean.Parser.Term.doRepeat ||
            kind == ``Lean.Parser.Term.doRepeatUntil then
      some "PSCV does not admit Lean repeat/repeat-until loops"
    else if kind == ``Lean.Parser.Term.doFor then
      if s[1].getSepArgs.size != 1 then
        some "PSCV for requires exactly one collection"
      else if !(s[3].isNone) then
        some "PSCV for loops do not take a decreasing clause"
      else
        args.toList.findSome? forbiddenLoop
    else
      args.toList.findSome? forbiddenLoop
  | _ => none

/-- Forbid Lean's spaced grouped operands at application positions only.
    Other term-start parentheses and native binder syntax stay valid. -/
private partial def groupedApplicationArg (s : Syntax) : Bool :=
  if s.isOfKind ``Lean.Parser.Term.paren ||
     s.isOfKind ``Lean.Parser.Term.namedArgument then
    true
  else if s.getKind == nullKind then
    s.getArgs.any groupedApplicationArg
  else
    false

/-- Determine only the first (outer) syntax sequence, not nested tactic branches.
The native Lean parser emits distinct nodes for braced and indented sequences. -/
private partial def firstSeqIsBraced (s : Syntax) (braced indented : Name) : Option Bool :=
  if s.getKind == braced then some true
  else if s.getKind == indented then some false
  else s.getArgs.toList.findSome? fun arg => firstSeqIsBraced arg braced indented

/-- Lean's try/catch parser accepts either indented or braced do sequences.
    The PSCV0 source profile selects only the braced alternative. -/
private partial def containsUnbracedDoSeq (s : Syntax) : Bool :=
  match s with
  | .node _ k args =>
    k == ``Lean.Parser.Term.doSeqIndent || args.any containsUnbracedDoSeq
  | _ => false

/-- Lean's native tactic cdot accepts "." as an ASCII synonym for "·".
PSCV0 deliberately selects only the actual Unicode goal bullet. -/
private partial def hasAsciiDotToken (s : Syntax) : Bool :=
  match s with
  | .atom _ "." => true
  | .node _ _ children => children.any hasAsciiDotToken
  | _ => false

/-- Restricted v7 measure-first source policy. Native Lean 4.35.0 supports
additional termination modes; preserve those in .lean but do not admit them
through native command alternatives inside .ps. -/
private partial def hasSourceAtom (s : Syntax) (value : String) : Bool :=
  match s with
  | .atom _ v => v == value
  | .node _ _ args => args.any (hasSourceAtom · value)
  | _ => false

/-- The source `where` of a v7 instance must contain an actual native
record-field initializer, not an arbitrary term. This rejects semantically
incompatible `where value` before the generated Lean `:=` declaration runs. -/
private partial def sourceInstanceFields (term : Syntax) : Bool :=
  if term.getKind == ``Lean.Parser.Term.structInst then true
  else if term.isOfKind choiceKind then
    !term.getArgs.isEmpty && term.getArgs.all sourceInstanceFields
  else false

private partial def forbiddenSyntax (s : Syntax) : Option String :=
  match s with
  | .node _ kind args =>
    let k := kind.toString
    -- Pinned Lean Command.opaque has an optional declaration value at [3].
    -- v7 never admits a bodyless opaque assumption as ordinary .ps source.
    if k == "Lean.Parser.Termination.suffix" &&
        s[0].isNone && !s[1].isNone then
      some "PSCV0-TERM-01: decreasing_by requires a preceding termination_by measure"
    else if (["Lean.Parser.Termination.terminationBy?",
              "Lean.Parser.Termination.partialFixpoint",
              "Lean.Parser.Termination.coinductiveFixpoint",
              "Lean.Parser.Termination.inductiveFixpoint"] : List String).contains k then
      some "PSCV0-TERM-01: non-measure recursion modes are not selected v7 .ps syntax"
    else if k == "Lean.Parser.Termination.terminationBy" &&
        hasSourceAtom s "structural" then
      some "PSCV0-TERM-01: structural termination_by spelling is excluded from selected v7 .ps"
    else if (k == "PS0.pscvBracedInstanceAnonymous" ||
             k == "PS0.pscvBracedInstanceNamed" ||
             k == "PS0.pscvBracedInstanceTelescopeAnonymous" ||
             k == "PS0.pscvBracedInstanceTelescopeNamed" ||
             k == "PS0.pscvPrioritizedInstanceAnonymous" ||
             k == "PS0.pscvPrioritizedInstanceNamed" ||
             k == "PS0.pscvPrioritizedInstanceTelescopeAnonymous" ||
             k == "PS0.pscvPrioritizedInstanceTelescopeNamed") &&
        (s.getArgs.isEmpty ||
          !sourceInstanceFields s[s.getArgs.size - 1]) then
      some "PSCV0-INSTANCE-FIELDS: instance where requires a braced record field initializer"
    else if hasAdjacentNativeExplicitGroups s then
      some "PSCV0-BIND-02: adjacent explicit binder groups are not selected v7 source"
    else if k == "Lean.Parser.Command.opaque" && s[3].isNone then
      some "PSCV0-OPAQUE-BODY-REQUIRED: opaque declarations need a checked value"
    -- Native value-form instance := is intentionally excluded by the v7
    -- selected instance header/field grammar; require the where-field form.
    else if k == "Lean.Parser.Command.instance" &&
        s[5].isOfKind ``Lean.Parser.Command.declValSimple then
      some "PSCV0-INSTANCE-VALUE-REFUSED: use selected instance where fields"
    else if k == "Lean.Parser.Command.instance" then
      some "PSCV0-INSTANCE-BRACES: instance field declarations require where { ... }"
    else if (kind == ``PS0.pscvDoIfElse || kind == ``PS0.pscvDoIf ||
             kind == ``PS0.pscvDoIfLetElse || kind == ``PS0.pscvDoIfLet) &&
             containsUnbracedDoSeq s then
      some "PSCV0-DO-IF-BRACES: do conditional branches must be braced do sequences"
    else if kind == ``Lean.Parser.Term.doIfLetBind then
      some "PSCV0-DO-IFLET-ARROW: v7 Standard admits :=, not a monadic left-arrow condition"
    else if kind == ``Lean.Parser.Term.doTry && containsUnbracedDoSeq s then
      some "PSCV0-TRY-BRACES: try, catch and finally bodies must use { ... }"
    else if kind == ``Lean.cdot && hasAsciiDotToken s[0] then
      some "PSCV0-BULLET: use the native '·' goal bullet, not ASCII '.'"
    else if kind == ``Lean.Parser.Term.byTactic &&
        firstSeqIsBraced s ``Lean.Parser.Tactic.tacticSeqBracketed
          ``Lean.Parser.Tactic.tacticSeq1Indented != some true then
      some "PSCV0-BY: source tactic proofs must use by { ... }"
    else if kind == ``Lean.Parser.Term.do &&
        firstSeqIsBraced s ``Lean.Parser.Term.doSeqBracketed
          ``Lean.Parser.Term.doSeqIndent != some true then
      some "PSCV0-DO: source monadic blocks must use do { ... }"
    else if kind == ``Lean.Parser.Term.match then
      some "PSCV0-MATCH: native unbraced match is not a valid .ps term; use match ... with { ... }"
    else if kind == ``Lean.Parser.Term.app && s[1].getArgs.any groupedApplicationArg then
      some "PSCV0-APP-02: spaced parenthesized application is forbidden; use f(x) or f((x, y))"
    else if k == "Lean.Parser.Term.runTactic" || k == "Lean.Parser.Tactic.runTac"
        || k == "Lean.Parser.Term.runTactic" then
      some s!"untrusted metaprogramming syntax `{k}`"
    else
      args.toList.findSome? forbiddenSyntax
  | .ident _ _ name _ =>
    if excludedName name then some s!"forbidden PSCV identifier '{name}'"
    else none
  | .atom _ value =>
    if value == ";" then
      some "PSCV does not admit Lean semicolon statement/tactic separators"
    else if (["run_tac", "native_decide", "sorry", "unsafe", "partial",
         "macro", "macro_rules", "elab", "initialize", "set_option",
         "syntax", "declare_syntax_cat", "implemented_by", "extern",
         "run_cmd", "scoped", "assert!", "then"] : List String).contains value then
      some s!"forbidden PSCV source token `{value}`"
    else none
  | _ => none

/-- Inspect a closed set of command kinds with Lean's actual parser. Do not
elaborate anything before this check. Every source import is rejected as a
top-level terminal command until a versioned dependency manifest exists. -/
private partial def syntaxNodeKinds (s : Syntax) : Array String :=
  match s with
  | .node _ k args =>
      args.foldl (fun names child => names ++ syntaxNodeKinds child) #[k.toString]
  | _ => #[]

/-- Return every distinct syntax-node kind encountered by the *accepted*
fragment. This is a development aid to mechanize Appendix A compatibility
rather than inferring allowed syntax from text or tests. No elaboration runs. -/
def auditSourceSyntax (source fileName : String) (env : Environment)
    (opts : Options) : Except String (Array String) := Id.run do
  let input := Parser.mkInputContext source fileName
  let mut parserState : Parser.ModuleParserState := {}
  let mut messages : MessageLog := {}
  let mut encountered := #[]
  repeat
    let (stx, next, nextMessages) :=
      Parser.parseCommand input
        { env := env, options := opts, currNamespace := .anonymous, openDecls := [] }
        parserState messages
    if nextMessages.hasErrors then
      return .error s!"Lean parser rejected source at input bytes {parserState.pos}..{next.pos}, syntax kind {stx.getKind}"
    if stx.isOfKind ``Parser.Command.eoi then
      return .ok encountered
    if Parser.isTerminalCommand stx then
      return .error s!"PS0 prohibits import/exit commands: {stx.getKind}"
    if next.pos == parserState.pos then
      return .error "PS0 parser did not advance"
    unless allowedCommand stx do
      return .error s!"PS0 closed command profile rejects: {stx.getKind}, alternatives: {stx.getArgs.toList.map (fun t => t.getKind)}"
    if let some why := forbiddenSyntax stx then
      return .error why
    if let some why := forbiddenLoop stx then
      return .error why
    if let some why := rejectAttributes stx then
      return .error why
    for kind in syntaxNodeKinds stx do
      unless encountered.contains kind do
        encountered := encountered.push kind
    parserState := next
    messages := nextMessages

def validateSourceSyntax (source fileName : String) (env : Environment)
    (opts : Options) : Except String Unit := do
  let _ ← auditSourceSyntax source fileName env opts
  return ()

end PS0
