import Lean
import PSCVL.Syntax

/-!
Pre-elaboration gate for the **currently implemented** PSCVL command fragment.

Lean's extensible grammar is intentionally *not* a PSCV grammar. We accept
an explicit set of top-level command AST kinds, reject other commands BEFORE
running their elaborators, and refuse errors/recovery. This is not yet the
full recursive A.18 source-grammar conformance validator or a security sandbox.
-/

open Lean

namespace PSCVL

private def allowedDeclarationKind (kind : String) : Bool :=
  ([
    "Lean.Parser.Command.definition",
    "Lean.Parser.Command.theorem",
    "Lean.Parser.Command.example",
    "Lean.Parser.Command.abbrev",
    "Lean.Parser.Command.opaque",
    "Lean.Parser.Command.instance"
  ] : List String).contains kind

/-- Only the finite PSCV/Lean Standard and PSCVL bookkeeping attributes are
admitted on declarations. Checking the elaborated declaration afterward is
not sufficient: a registered Lean attribute may run user-visible code. -/
private partial def attributeIdentifiers (s : Syntax) : List Name :=
  match s with
  | .ident _ _ val _ => [val]
  | .node _ _ args => args.toList.flatMap attributeIdentifiers
  | _ => []

private def rejectAttributes (s : Syntax) : Option String := Id.run do
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
    return some s!"PSCVL rejects undeclared attribute '{bad}'"
  return none

private partial def allowedCommand (s : Syntax) : Bool :=
  let k := s.getKind.toString
  if s.isOfKind choiceKind then
    s.getArgs.all allowedCommand
  else if k == "Lean.Parser.Command.declaration" then
    allowedDeclarationKind s[1].getKind.toString
  else
    ([
      "PSCVL.pscvConst", "PSCVL.pscvConstInferred",
      "PSCVL.pscvFunction", "PSCVL.pscvImplicitFunction", "PSCVL.pscvTheorem",
      "PSCVL.pscvDefinition", "PSCVL.pscvBracedStructure", "PSCVL.pscvBracedInductive",
      "PSCVL.pscvFunctionContract", "PSCVL.pscvFunctionEnsures", "PSCVL.pscvFunctionRequires",
      
      "Lean.Parser.Command.namespace", "Lean.Parser.Command.section",
      "Lean.Parser.Command.end", "Lean.Parser.Command.open",
      "Lean.Parser.Command.variable", "Lean.Parser.Command.universe",
      "Lean.Parser.Command.include", "Lean.Parser.Command.omit",
      "Lean.Parser.Command.check", "Lean.Parser.Command.print",
      "Lean.Parser.Command.printAxioms"
    ] : List String).contains k

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

private partial def forbiddenSyntax (s : Syntax) : Option String :=
  match s with
  | .node _ kind args =>
    let k := kind.toString
    if kind == ``Lean.Parser.Term.match then
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
         "run_cmd", "deriving", "scoped", "assert!"] : List String).contains value then
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
      return .error s!"PSCVL prohibits import/exit commands: {stx.getKind}"
    if next.pos == parserState.pos then
      return .error "PSCVL parser did not advance"
    unless allowedCommand stx do
      return .error s!"PSCVL closed command profile rejects: {stx.getKind}, alternatives: {stx.getArgs.toList.map (fun t => t.getKind)}"
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

end PSCVL
