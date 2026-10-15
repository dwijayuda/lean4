import Lean
import PS0.Syntax

/-!
PS0 v1: native Lean 4.35.0 registered command grammar plus owned PS0 syntax.

Do NOT define language admission by a frozen list of command names,
attributes, syntax extensions or source tokens. The new v1 language
reference includes Lean's imported and locally registered syntax, tactics,
macros, IO and unsafe/partial programming.

For language checking, use Lean's interleaved parser/elaborator. This file
provides a read-only initial-grammar syntax inventory only. It is not
proof evidence, a source security sandbox or a complete extension census.
-/

open Lean

namespace PS0

private partial def syntaxNodeKinds (s : Syntax) : Array String :=
  match s with
  | .node _ k args =>
      args.foldl (fun names child => names ++ syntaxNodeKinds child) #[k.toString]
  | _ => #[]

/-- Diagnostic-only static syntax inventory. Local command registrations
    may change the grammar during elaboration: this command intentionally
    cannot substitute for actual Lean checking of a complete source file. -/
def auditSourceSyntax (source fileName : String) (env : Environment)
    (opts : Options) : Except String (Array String) := Id.run do
  let input := Parser.mkInputContext source fileName
  let mut parserState : Parser.ModuleParserState := {}
  let mut messages : MessageLog := {}
  let mut encountered : Array String := #[]
  repeat
    let (cmd, next, nextMessages) :=
      Parser.parseCommand input
        { env := env, options := opts, currNamespace := .anonymous, openDecls := [] }
        parserState messages
    if nextMessages.hasErrors then
      return .error s!"PS0V1-PARSE: static grammar cannot parse source at {parserState.pos}..{next.pos}; use the official interleaved frontend"
    if cmd.isOfKind ``Parser.Command.eoi then
      return .ok encountered
    if next.pos == parserState.pos then
      return .error "PS0V1-PARSE: native parser did not advance"
    for kind in syntaxNodeKinds cmd do
      unless encountered.contains kind do
        encountered := encountered.push kind
    if Parser.isTerminalCommand cmd then
      return .ok encountered
    parserState := next
    messages := nextMessages

/-- Native command grammar may change after each command; only the
    official interleaved parse/elaboration frontend can qualify source. -/
def validateSourceSyntax (source fileName : String) (env : Environment)
    (opts : Options) : Except String Unit := do
  let _ ← auditSourceSyntax source fileName env opts
  return ()

end PS0
