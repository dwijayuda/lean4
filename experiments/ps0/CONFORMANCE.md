# PS0 v1 — Implementation and Conformance Ledger

**Sole normative reference:** [PS0_V1_LANGUAGE_REFERENCE.md](PS0_V1_LANGUAGE_REFERENCE.md), edition R2, 2026-10-16. Uploaded Git blob `c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`.
**Lean:** official 4.35.0, `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.

**Status:** migration to v1 implemented at the specification/source-policy
foundation; full v1 language closure NOT implemented; exact-commit
Lean CI NOT observed passing. The old v7 41% estimate, fixed
191/181-style progress measures and v7 test assertions are retired.

## Implemented migration changes

| Layer | Current code | Remaining gap |
|---|---|---|
| Canonical document | Complete 4,163-line standalone v1 reference in PS0 | No normative predecessor fallback |
| Syntax adapters | Existing `function`/`const`, comma binders/calls, selected braced forms and Lean-native elaboration | All `psTerm`/`psCommand`/`psTactic`/`psDoSeq` ownership and `PS0.Syntax.lower` (`0B/`9) |
| Grammar | Removed frozen command/attribute/tactic/loop/source-token denial list; diagnostic-only syntax-kind inventory | Full interleaved host grammar and category-aware adaptation |
| Declaration policy | No mandatory v7 axioms/unsafe/partial/IO ban; `#ps0_evidence` is informational | Transitive claim-specific assumptions and evidence `12` |
| Imports/Standard | Native registered/imported extensions determine availability; no v7 finite Standard allowlist | Complete effective module/stage/extension identity and `prelude` isolation |
| Modules | Explicit native `module` parsed; implicit headerless PS module recognized | Full modern module compilation, public-name defaults, hidden bodies and project graph |
| `.lean` | Official Lean process unchanged and unrestricted | Routine exact-commit CI qualification |
| JS backend | Lean typed Nat-only IR, ESM/`.d.ts`/Source Map v3 | Validated build, more types, modules, runtime semantics proof |

**Important:** A v1 feature may be *admitted by the normative
language* but remain *not yet implemented by PS0*. Neither sentence
means it is guaranteed to compile in the current branch.

## New evidence baseline

[v1-coverage.json](v1-coverage.json) records **242** items:
100 capability families, 64 positive source cases, 47 negative
source/disallowed-claim cases, and 31 R2 boundary witnesses.
Every item initially has `PENDING` status. It is not a numeric
implementation-completion percentage.

`PASS` requires real evidence at the exact source, Lean,
compiler and imported environment identity. A static syntax-kind
count or availability via unchanged `.lean` does not qualify PS
source capability. The old PSCV0 v7 registry is not imported
and does not supply a fallback test outcome.

## Distinct validation outcomes

1. **Development:** native editor/elaboration may retain errors or
   `sorry`; not completed proof.
2. **Ordinary checked source:** complete relevant checking, with
   declared assumptions/runtime interfaces classified.
3. **Checked theorem:** precise elaborated proposition and actual
   kernel evidence, conditional on transitive assumptions.
4. **Source-verified:** named policy/spec, evidence for required
   coverage/effects/erasure/termination and assumption closure.
5. **Execution-correspondence-verified:** additional checked
   correspondence to a specified generated artifact/layer.

`#ps0_evidence` does not issue any verified label. A stronger
verified-output policy may refuse an otherwise valid ordinary
unsafe, partial, effectful or axiomatic program; that refusal
must not redefine the PS0 v1 source language.

## High-priority conformance probes

- Native `axiom`, unsafe/partial/`noncomputable`, bodyless
  `opaque` and development `sorry` (native classification).
- Macros, syntax categories, custom elaborators, dynamic
  attribute/deriving registrations, and quotations whose native
  category data must not be globally PS-rewritten.
- Explicit and implicit modern modules, `prelude`, public/meta/all
  import flags and hidden vs exposed public bodies.
- Native value-form instances, imported priority handlers,
  structural and nonstructural recursion, monadic `if let ←`,
  zipped loops, native tactics and semicolon control.
- ProofScript comma-call/tuple/nullary and binder-specific
  source ownership, matching and braced syntax (``0B–5).
- Source/claim boundary tests and the R2 witnesses, including
  per-phase diagnostic or AST semantics checks.

## Backend acceptance (separate from v1 language)

The Nat-only JS backend emits `.js`, `.d.ts` and `.js.map`
from a deliberately closed runtime IR. It is **not** a full
v1 language implementation and does not issue a verified JS
certificate. CI must demonstrate exact Nat arithmetic, type
signatures, source-map positions, deterministic emission,
refusal of unsupported constructs and runtime semantics.

See [PS0_V1_IMPLEMENTATION_PLAN.md](PS0_V1_IMPLEMENTATION_PLAN.md)
for remaining architecture gates and [AI_WORK_STATE.md](AI_WORK_STATE.md)
for the latest development handoff.


## PS0 v1 host psTerm postfix-call extension — 16 October 2026

Implemented a first PS-owned, **nonempty identifier-head** adjacent-call
source production in `PS0/HostCategories.lean`. It uses Lean's
`noWs` lexical/position-sensitive parser to distinguish a PS postfix
from a spaced native application. The separate `psCallArg` category
captures positional and named host operands.

The explicit `PS0.Syntax.lower` bridge lowers this source category
recursively to a native `Lean.Parser.Term.app` node, preserving the
argument tree. Named parameters use the genuine
`Lean.Parser.Term.namedArgument` category and reject duplicate names
or positional arguments after named parameters. No source-string
transpilation, name resolution or typechecker fork was added.
Native subtrees remain unmodified and other native, quotation and
DSL categories retain their own syntax ownership.

**Bounded scope:** identifier-head calls with nonempty argument lists
in **explicit host-category extension operands**. Full standard
declaration/tactic/do `psTerm` operand wiring, generalized callable
postfix heads, source-nullary completion, optional trailing commas,
parser ambiguity reconciliation and source-provenance verification
remain pending. Existing native term macros may support some source
forms but do not qualify the v1 host-category contract by themselves.

Candidate tests: `tests/v1/host_postfix_calls.ps` exercises
two-argument, nested, tuple-preserving and named calls, and an
extension verifying it receives the raw host-call syntax before
lowering. Separate negative fixtures assert the expected
`PS0V1-CALL-ORDER` and `PS0V1-CALL-NAMED` diagnostic categories.
Five relevant `v1-coverage.json` cases have new candidate links;
all remain `PENDING` until actually qualified by pinned Lean CI.

The canonical normative PS0 v1 R2 document remains unchanged.


## Standard declaration-body psTerm integration — 16 October 2026

PS0 now provides owned source-command forms for **typed** `function` and
`const` bodies whose RHS category is `psTerm` rather than silently taking a
native `term` operand. These forms have higher source-parser priority than
the older partial native-term-backed alias forms. They call the shared
`PS0.Syntax.lower` bridge, constructing real native Lean declarations with
the existing source binder/Unit sugar and ordinary Lean elaboration.

`tests/v1/standard_host_declarations.ps` exercises composed and nested
adjacent calls, reordered named arguments, trailing commas, a
partially applied function, and const initializers. Negative fixtures
`standard_host_order_negative.ps` and
`standard_host_duplicate_negative.ps` demand their specific
`PS0V1-CALL-ORDER`/`PS0V1-CALL-NAMED` rejections; a separate comma-only
fixture must not pass. These tests are **not** current CI PASS receipts.

The Lean-native Nat-only JS backend now recognizes the same new
`psTerm` body nodes, lowering only prior, exact-arity, monomorphic Nat
function calls and constant references into its closed typed IR.
`tests/js/nat_mvp.ps` includes calls with trailing commas in typed
`function` and `const` source forms, with a Node/TypeScript check in CI.
Broader JS semantics or proof-of-runtime-preservation are not claimed.

**Unfinished:** inferred-result declarations, dependent type/binder
slots, standard native `def` and `theorem` RHS, native tactic/do/contract
operands, complete high-postfix call heads, empty-call type-directed
completion inside `psTerm`, ambiguous parse coalescence, expression
source-provenance proof, and imported extension/DSL boundaries.
Only these two typed declaration aliases have migrated standard
body operands. Native `.lean` is unaffected.

The v1 coverage ledger has seven additional **standard-operand
candidate fixture links** on existing call-case IDs, not seven new
requirements or qualifying PASS records. All 242 entries remain
unqualified until an exact-commit Lean 4.35.0 CI result is examined.


### Inferred-result and private source alias parity

The same explicit `psTerm` standard-body adapter now covers
`function` and `const` with either a declared result type or Lean-inferred
result, plus typed/inferred `private function` and `private const`.
Inferred declarations reuse the official Lean elaborator, while source
`function f()` retains the synthetic required `Unit` binder; ordinary
native `def` and `.lean` remain unchanged.

`tests/v1/standard_host_declarations.ps` includes Lean `rfl`
oracles for the public/private and inferred variants, typed
host-call composition, and the source-nullary Unit conversion.
The existing Nat-only JS backend continues to accept the checked
typed/public subset and explicitly rejects inferred/private exports
until its IR/export contract is widened. This split is backend
capability, not a PS0 v1 language restriction.

**Implementation code and test fixtures are committed but still
unqualified:** no actual Lean 4.35.0 build or test run has been observed
for the branch. No v1 requirement was promoted to PASS.
