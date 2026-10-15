# Lean 4 ↔ ProofScript `ps0` v1 — Standalone Language Reference

**Status:** normative language-design target; not evidence of compiler conformance.  
**Edition:** PS0 v1 · **Document revision:** consistency revision R2, standalone Markdown edition, 2026-10-16.  
**Semantic and upstream grammar pin:** official Lean **4.35.0**, commit `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.  
**Scope:** language features, syntax, grammar ownership, static semantics, examples, type/library capabilities, and assurance distinctions.

> **Language identity.** PS0 v1 combines Lean's programming, proof, metaprogramming, and runtime-interface capabilities with an application-oriented ProofScript surface in `.ps` files. It uses Lean's type theory and elaboration semantics; it does not define a second proof kernel. Ordinary `.lean` files remain genuine, unrestricted Lean.
>
> **Standalone authority.** This document contains the PS0-specific rules, including definition aliases, binder groups, calls, braces, module defaults, contracts, and assurance boundaries. No rule is inherited by reference from another ProofScript language document. Historical references in Appendix C are provenance only, not required reading or normative fallback.
>
> **Reading convention.** Each feature provides its category/semantic basis, paired Lean and ProofScript grammar sketches, paired examples, and the differences that affect meaning. Grammar sketches use `?` for optional, `*` for repetition, `+` for nonempty repetition, and `|` for alternatives; they explain the pinned category model rather than replacing Lean's extensible parser with a separate universal EBNF. `term`, `command`, `binder`, `tactic`, and `doSeq` are explained in §0B.
>
> **Example status.** Examples are design illustrations, not tested compiler results. Unless an example group is explicitly identified as a “complete module,” examples are independent fragments with the indicated imports and local variables supplied. Placeholders such as `term`, `pat`, `P`, or `C` in grammar and schematic examples are metavariables of this document, not automatically valid declarations. Examples containing proof holes are development examples only. An example using assumptions can support only the explicitly qualified, policy-identified claim defined in §12; no such qualification is established merely by printing the example.

A statement that a form is **admitted** means the language has that form, subject to its imports, scope, types, staging, and native semantic conditions. It does not mean that the current PS0 implementation supports it, that it succeeds for arbitrary arguments, or that it establishes a verified runtime behavior.

## Executive syntax map — one interpretation per context

| Concern | Native Lean 4.35.0 | ProofScript `ps0` v1 |
|---|---|---|
| Definition | `def f (x : A) : B := e` | Native `def` plus comma-binder form `def f(x: A): B := e` |
| Function alias | `def f (x : A) : B := e` | `function f(x: A): B := e`; same definition semantics |
| Named value | `def x : A := e` | `const x: A := e`; no source parameter telescope |
| Nullary function | `def f (_ : Unit) : A := e` | `function f(): A := e`; a required `Unit` parameter, not a zero-arity kernel function |
| Multiple arguments | `f x y` | `f(x, y)` or `f x y` |
| One tuple argument | `f (x, y)` | `f((x, y))` |
| Explicit Unit argument | `f ()` | `f(())`; `f()` has a separate completion rule |
| Empty call | No independent zero-argument-call construct | `f()` only completes declared defaults/automatic arguments or exactly one remaining required `Unit` |
| Gap before parenthesized operand | `f (x)` | Rejected in ordinary host terms; not a ban on binders or fresh grouped terms |
| Mixed application | Native parser decides grouping | `f g(x, y)` means `f (g x y)`; `(f g)(x, y)` means `(f g) x y` |
| Lambda/quantifier binders | Native binder grammar | Same; declaration comma binders do not become lambda binders |
| Source module default | Written `module` selects native modern modules | Headerless `.ps`: implicit modern module, public names by default; written `module`: native module defaults |
| Body visibility | Public name does not necessarily expose body | Same; `@[expose]`, `abbrev`, and public interfaces keep their native distinctions |
| Blocks | Native layout and category-specific braces | Native forms plus owned braced forms; braces do not turn records into statement blocks |
| Conditional | `if p then a else b` | Native form or `if (p) { a } else { b }`; both keep Lean `if` semantics |
| Proofs | `by` and native tactic sequences | Native form or `by { ... }`; full registered proof tools |
| Recursion | Total, partial, and fixed-point facilities | All admitted with distinct meanings; no automatic termination claim |
| Effects | Generic monads, `ST`, `IO`, tasks, runtime facilities | Same capabilities; contracts do not prove external implementations by typing them |
| Specifications | `given`, `requires`, `ensures`, `assert`, loop annotations | Same intrinsic mechanisms with PS surface lowering and explicit proof requirements |
| Erased state | `erased`, `erased mut`, `erased x ← action` | Same; an erased-result action still executes |
| Language extensions | Syntax, macros, elaborators, tactics, attributes | All admitted; native quotations retain their own grammar rather than receiving textual rewrites |
| Runtime interfaces | `unsafe`, `extern`, `implemented_by`, `@&` | Admitted; logical interface and native implementation remain distinct |
| Assumptions / holes | `axiom`, `sorry`, generated assumptions | Syntax exists; assumptions must be disclosed, holes never count as completed proofs |
| Mathematics | `∀`/`forall`, `∃`/`exists`, `λ`/`fun`, `→`/`->` | Retained native meanings; no invented singular `exist` keyword |

**Canonical source style:** use `function name(...)`, adjacent calls, and braced imperative/proof bodies for application code. Native layout and genuine Lean mathematical aliases remain legal; the formatter must not change argument partition, binder order, staging, or proof meaning.

## Contents

- [0. Language identity, semantic scope, and authority](#0-language-identity-semantic-scope-and-authority)
- [0A. One language, distinct evidence outcomes](#0a-one-language-distinct-evidence-outcomes)
- [0B. Grammar-category and ownership registry](#0b-grammar-category-and-ownership-registry)
- [1. Files, lexical structure, modules, and name scope](#1-files-lexical-structure-modules-and-name-scope)
- [2. Declarations, functions, binders, and arguments](#2-declarations-functions-binders-and-arguments)
- [3. Expressions, monadic blocks, and control flow](#3-expressions-monadic-blocks-and-control-flow)
- [4. Data declarations, records, classes, and pattern matching](#4-data-declarations-records-classes-and-pattern-matching)
- [5. Recursion, termination, partiality, and fixed points](#5-recursion-termination-partiality-and-fixed-points)
- [6. Proof terms, tactics, automation, and logical notation](#6-proof-terms-tactics-automation-and-logical-notation)
- [7. Contracts, verification conditions, and erased state](#7-contracts-verification-conditions-and-erased-state)
- [7A. Diagnostics, interactive development, and evaluation](#7a-diagnostics-interactive-development-and-evaluation)
- [7B. Runtime effects, foreign interfaces, and unsafe programming](#7b-runtime-effects-foreign-interfaces-and-unsafe-programming)
- [8. Type foundation and concrete type catalog](#8-type-foundation-and-concrete-type-catalog)
- [8A. Application libraries and import-driven capability scope](#8a-application-libraries-and-import-driven-capability-scope)
- [9. Notation, syntax extensions, macros, and quotations](#9-notation-syntax-extensions-macros-and-quotations)
- [10. Elaborator, compiler, and reflection programming](#10-elaborator-compiler-and-reflection-programming)
- [11. Attributes, options, initialization, documentation, and bootstrap](#11-attributes-options-initialization-documentation-and-bootstrap)
- [12. Logical assumptions and assurance boundaries](#12-logical-assumptions-and-assurance-boundaries)
- [13. Source examples and acceptance/refusal reference](#13-source-examples-and-acceptancerefusal-reference)
- [14. Environment closure, source fidelity, and conformance meaning](#14-environment-closure-source-fidelity-and-conformance-meaning)
- [Appendix A. Source-to-feature review register](#appendix-a-source-to-feature-review-register)
- [Appendix B. Reader glossary](#appendix-b-reader-glossary-and-syntax-context-distinctions)
- [Appendix C. Pinned sources and optional provenance](#appendix-c-pinned-sources-and-optional-historical-provenance)
- [Appendix D. Concrete boundary witnesses](#appendix-d-concrete-boundary-witnesses-and-qualification-oracles)

## 0. Language identity, semantic scope, and authority

**PS0V1-CORE-01.** PS0 v1 is a Lean-backed programming and proving language with ProofScript surface forms. Every ordinary typed expression, declaration, and proof must have the meaning assigned by the pinned Lean elaborator and logical environment after the explicitly specified surface transformation. Compile-time programs, unsafe definitions, external implementations, and partial functions retain Lean's distinct treatment; they are not all reclassified as total, kernel-reducible functions.

The intended coverage includes the Lean source-language mechanisms used in `src/Init`, `src/Std`, `src/Lean`, and the Lean-written parts of `src/lake`. It includes mechanisms for defining new syntax and elaboration, not just syntax that an application consumes. Relevant upstream tests enlarge the conformance corpus but do not turn intentionally invalid test inputs into valid programs. [L-INIT] [L-STD] [L-LEAN] [L-LAKE]

C, C++, CMake, shell, Python, JavaScript, and other languages present in the repository remain **host implementation or tooling languages**. Their existence does not add C++ templates, C pointer syntax, JavaScript object semantics, or shell commands to PS0. Their interfaces are covered through Lean's runtime, foreign-function, and metaprogramming facilities. This specification does not require LLVM, Lake, npm, or any particular package manager merely because an upstream component uses one.

**PS0V1-CLOSURE-01.** The admitted feature set is the closure of:

- the pinned Lean built-in language categories and their elaboration rules;
- syntax, notation, tactic, deriving, attribute, option, and elaborator registrations supplied by resolved imports;
- valid registrations introduced earlier in the same source module;
- the owned ProofScript surface rules in this reference.

The catalog in Appendix A is an audit register, **not an exclusion list**. An upstream feature omitted from that catalog is not thereby banned. A missing feature found in the pinned production sources is a coverage defect to record and implement, not grounds for narrowing the meaning of “source-complete.” Availability remains subject to its actual imports, scopes, stage, types, and upstream prerequisites.

This is **capability completeness**, not a promise that renaming every `.lean` file to `.ps` preserves its bytes or behavior. ProofScript's calls, default source-module convention, and some braced forms intentionally differ. Native `.lean` remains the byte-for-byte source-compatibility route. Supporting `.lean` pass-through alone does not establish `.ps` v1 implementation completeness.

### Authority without an external ProofScript dependency

The precedence of rules is: (1) explicit PS0 v1 surface and assurance decisions in this document; (2) pinned Lean syntax/elaboration/library behavior for native constructs; (3) explanatory examples. Examples cannot override either rule set. There is **no predecessor-document fallback**. A missing PS0-owned rule is a defect in this reference, not permission to ask a reader to reconstruct the language from a previous edition.

Pinned upstream sources supply precise implementation anchors and the extensible native facilities. The explanations here state the language-facing meaning; consulting another ProofScript reference is unnecessary. The source pin is immutable for this edition. Newer upstream releases, unspecified imported plugins, and `latest` documentation do not silently change the language.

“Full capability” concerns Lean's source-language mechanisms and available registrations, not unconditional execution of every bootstrap command or support for every foreign platform. It does not turn C/C++/shell files in Lean's repository into PS0 grammar.

## 0A. One language, distinct evidence outcomes

| Outcome | Requirements and meaning | Not implied |
|---|---|---|
| Development state | Parsing/elaboration may retain holes, diagnostics, or incomplete goals for editing | Completed proof, executable qualification, or absence of errors |
| Ordinary checked program/module | Valid edition-specific source and completed checking of the relevant declarations; assumptions and runtime boundaries retain their classifications | Totality of `partial` computation, a functional specification, or verified machine code |
| Checked theorem | The actual elaborated statement has a checked proof relative to its disclosed dependency assumptions | An unconditional result under an unstated foundation |
| Source-verified program | Checked source specification and required coverage/effect/assumption/erasure/termination obligations, with an identified policy and stated trust boundary | Proved backend, runtime or foreign implementation correspondence |
| Execution-correspondence-verified program | The source-verified obligations plus checked correspondence to an identified execution artifact/layer | Evidence beyond the specifically covered layer or an unstated external-world guarantee |

A general-purpose language may admit partial or unsafe runtime code without calling that code verified. A declaration is not completed merely because a tactic returned successfully or an error-recovery environment contains its name. A conditional theorem is not an unconditional theorem. Section 12 gives the claim boundary in full.

**Error categories:** **LEX** = invalid source encoding/token/trivia; **PARSE** = invalid category, delimiter, ordering, or host-call adjacency; **ENV** = missing/incompatible import or registration; **ELAB** = type, coercion, binder, pattern, or instance failure; **ELAB/VC-PROOF** = an unclosed generated obligation; **KERNEL** = invalid submitted logical declaration/term; **ASSURANCE** = an unmet claim-level dependency or evidence condition. An earlier unrelated lexer failure does not demonstrate the intended later rule.

## 0B. Grammar-category and ownership registry

| Category | Meaning and ownership in this document |
|---|---|
| `command` | A top-level or nested command recognized by the current imported/registered environment; native commands and PS declaration forms are both available |
| `term` / `psTerm` | In this document’s PS-column sketches, `term` abbreviates a host expression. In an actual `syntax` declaration or named quotation, literal category `term` is Lean’s native category; explicit category `psTerm` is the host category. Host code, types, standard tactic arguments and contracts enter `psTerm`. See the binding rules immediately below. |
| `nativeTerm` | Explanatory name for literal native category `term`, not a separately required source alias. Never selected as a silent fallback for a malformed `psTerm`. |
| `declId` | Lean declaration name, with permitted universe-parameter suffixes |
| `nativeBinder` | Lean's declaration, lambda, quantifier, or field binder in its actual context; these contexts are not interchangeable |
| `psParam` | One explicitly typed declaration parameter, with a native default or automatic-parameter suffix where valid |
| `psExplicitGroup` | `(` one or more comma-separated `psParam`s `)`; one trailing comma is allowed; zero entries are not a generic declaration binder |
| `psNonExplicitBinder` | Native implicit, strict-implicit, or instance binder; preserves its position and dependencies |
| `psFunctionBinders` | The `function` alias telescope defined fully in §2, including its dedicated final nullary `()` alternative |
| `psCallArgs` | Positional host terms followed by named `name := term` arguments, comma-separated, at most one trailing comma; an empty list uses the completion rule |
| `pattern` | Native pattern grammar, plus the explicitly defined PS constructor-pattern adapter in §4; never arbitrary function-call elaboration |
| `psTermBeforeBlock` | Host expression with the marker-free control-header delimiter policy in §3; it never consumes the unprotected body-opening brace as an argument |
| `declVal` | Native value/equation/structure-where form for the declaration kind, plus the defined PS braced-body form |
| `psWhere` | Braced local helpers and optional native finally subsections; its helpers use the dedicated `psLocalDeclVal`, not the top-level `psDeclVal`. See §2 for scope and lowering. |
| `tactic` / `tacticSeq` | Registered native tactic grammar and goal-control structures; terms embedded as ordinary proof arguments are `psTerm`s |
| `doElem` / `doSeq` | Native registered effect/control grammar, with PS braced control alternatives; a complete sequence includes its native delimiters/layout |
| `psDoItems` / `psTacticItems` | Bare contents of a PS braced do/tactic block, not another complete `doSeq`/`tacticSeq`. Do contents use the nonempty `Term.doSeqItem` repetition; tactic contents use native semicolon/newline-separated tactics and native goal-closure checks. |
| `psContractSeq` | `given? requires? ensures?` in that order and once each, on eligible definition/function declarations |
| `structField` / `structInstField` | Type-level field declarations versus value-level field initializers; their separators and binders differ |
| `quotation` | Syntax data in its explicitly/native-owned category; host-text substitutions do not rewrite quoted argument trees |
| `extensionCategory` | A registered embedded language with its own grammar contract, precedence, and import/staging requirements |

**No category shortcut.** A parenthesis can start a binder, tuple, fresh term, native configuration field, pattern, or PS postfix call. The parser must determine its category before applying a spacing or lowering rule. Statements such as “same as Lean” elsewhere refer to the native category just described, not to an unrestricted fallback that changes a PS-owned construct's meaning.

### Category identities and source-entry rules

**PS0V1-CATEGORY-01.** The following are concrete PS0 v1 category names, specified as language-extension interfaces even before an implementation supplies them: `psTerm`, `psCommand`, `psTactic`, and `psDoSeq`. Their corresponding native categories are `term`, `command`, `tactic`, and `doSeq`. Native category names and syntax-kind identities are not renamed. `nativeTerm` elsewhere is explanatory prose, not another required token or category.

| Position | Selected category and observable syntax |
|---|---|
| A `.ps` module body | `psCommand`; its standard value/type/proof/control operands use the host categories |
| Standard declaration signatures, expressions, contracts, interpolation holes and configuration **values** | `psTerm`; surrounding binders, literal tokens and configuration delimiters keep their own productions |
| Standard `by` proofs and standard tactic term operands | `psTactic` / `psTerm`; tactic keywords and locations are not treated as callable heads |
| Standard effect/control sequences | `psDoSeq`, with host expression and pattern operands |
| Literal `term`, `command`, `tactic`, `doSeq` in a user `syntax`/`macro`/`elab` declaration | The named native category, independent of whether the declaration was written in `.ps` or `.lean` |
| Explicit `psTerm`, `psCommand`, `psTactic`, `psDoSeq` in an extension declaration | The named host category; its raw PS syntax is visible to that extension |
| Unannotated quotation, or named native quotation such as `` `(term|...) `` | Native quotation grammar and native ambiguity priorities; any explicitly embedded extension category retains its declared ownership |
| Named PS quotation such as `` `(psTerm| f(x, y)) `` | Host syntax data, without running the quoted program or performing type-directed call completion |
| Antiquotation expression `$(e)` | The metaprogram’s host expression in `.ps`; its **resulting syntax data** retains the destination category contract of the splice |
| Independently declared DSL categories, parser-description syntax and documentation markup | Their declared grammar; no token-wise conversion to PS expressions |

Here and elsewhere, an **ordinary host operand** means a pinned standard host operand or an explicitly declared PS-category operand. An extension’s explicitly native/custom operand is not implicitly included by phrases such as “the same rule in code and proofs.” Its category remains visible in that extension’s declaration.

**Standard adaptation is pinned, not heuristic.** The standard host front end adapts the object-language operand slots of the pinned built-in and `Init`/`Std`/`Lean` source productions: declaration values/types, binder types/defaults, proof terms, tactic expressions, do expressions, match motives/inaccessible terms, collection/interpolation expressions, and configuration value terms. Nested binder and pattern *structure* remains native except for the explicit adapters in this reference. Attributes with expression arguments adapt those expression slots, not their literal names or schemas. Parser-descriptor categories, quotations as syntax data, and independently owned DSL categories are not recursively reclassified as host terms. These rules identify obligations by pinned production identity and operand role, not by arbitrary namespace prefixes or the spelling `term` in raw text. A conformance implementation must enumerate that mapping when qualifying standard adaptation (§14).

**Extension declarations are explicit.** For a new extension, `syntax "echoNative " term : term` consumes a native operand and creates a native term extension; it is also available as an extension-owned production at a host term site. `syntax "echoPS " psTerm : term` consumes a host operand while still creating a native-result term extension. An extension declared `: psTerm` is available only in host terms and PS quotations. Merely parsing a production does not give it an elaborator or macro. This makes operand and result categories independently selectable without a new quoting punctuation or a second logical language.

New imported/user productions retain their explicit operand categories. They are not added to the pinned standard-adaptation map by matching a function name. A custom low-level parser that obscures its operand structure retains its native/custom grammar; it can be used within its declared category, and can explicitly call the host-category parser for host operands. Its mere import is not rejected. A custom extension that needs ordinary PS arguments declares them as `psTerm`; a native syntax-inspecting extension need not be rewritten to capture host trees it never promised to accept.

**PS0V1-CATEGORY-02 — dispatch and lowering boundary.** Keep the original host syntax tree and its source ranges through source validation. Before invoking an unchanged standard native handler, lower only the host operand slots owned by the standard adapter. The handler receives the native-shaped declaration/application/control tree described by the lowering rules. An independently owned extension receives its declared raw syntax: a `psTerm` capture is not secretly normalized before that extension inspects it. Descending into native quotations or independently owned DSL data is forbidden unless their explicit category contract calls for it. Native-generated syntax is checked according to its generating category; synthetic native applications are not rejected merely because pretty-printing them would use spaced parentheses.

The explicit normalizer used by extension authors is the **specified, not yet evidenced as implemented** interface `PS0.Syntax.lower : Lean.Name → Lean.Syntax → Lean.MacroM Lean.Syntax`, supplied by the `PS0.Syntax` module at the appropriate meta stage. Its first argument is one of the four PS category names above. It validates that category, lowers its PS-owned nodes, and returns syntax for the corresponding native elaboration entry. An unsupported category, missing registered lowering, or malformed source tree is an error. It does not parse strings, run tactics, resolve ordinary term names, synthesize typeclass instances, or check a proof. Native subtrees and explicitly opaque syntax data remain unchanged. The syntax inspection and residual-node rules in §9 complete this contract.

**PS0V1-CATEGORY-03 — malformed source is not repaired.** Real source gaps are checked before lowering; generated native syntax is tracked separately. Losing source provenance is not a license to qualify a rewritten source file. Manually constructing a `Syntax` value does not certify that it came from a valid PS parse. Missing or falsified source provenance disqualifies a source-fidelity claim even if the resulting logical term independently type-checks.

**Auxiliary sketch names.** `psTermOrBodyWrapper` is an ordinary host term or the direct-body wrapper owned by §1; `psInstanceFields` is the bare instance/record field-initializer list in §4, not a second declaration type. `psInvariant` and `psDecreasing` have the native clause binder/order shape in §7 with the marker-free block boundary of §3. `psDoConditionBeforeBlock` is a native named-proposition or pure/monadic if-let condition whose expression uses `psTermBeforeBlock`; `nativePatternAndEvidence` is the native optional `h :` plus iteration pattern. `nativeHighPostfix` and `nativeAtomicOrPostfixHead` denote the pinned high-binding native categories and extension forms, not an invented blanket precedence class. All these are specification aliases; only the four concrete PS category names and the `PS0.Syntax.lower` interface in §0B are new extension interfaces.

## 1. Files, lexical structure, modules, and name scope

### Source text, identifiers, comments, and literal tokens

**Feature / profile:** Shared native lexical families; PS host application distinction  
**Rule family:** `PS0V1-LEX`  
**Source basis:** [L-TERM], [L-CMD], [L-MODULE]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
sourceFile ::= header command* EOF
identifier ::= Lean.ident
comment ::= "--" lineText | "/-" nestedComment "-/"
docComment ::= "/--" documentation "-/"
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psSourceFile ::= psHeader command* EOF
identifier ::= Lean.ident
comment ::= Lean.comment
// Host-term call adjacency is checked after tokenization.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- Unicode names and nested comments
/- outer /- inner -/ comment -/
def αCount : Nat := 2
def «two words» : Nat := αCount
```

**ProofScript `ps0` v1**

```proofscript
-- Unicode names and nested comments
/- outer /- inner -/ comment -/
const αCount: Nat := 2
const «two words»: Nat := αCount
```

**Source language distinction and static meaning.**

Use pinned Lean tokenization for Unicode identifiers, escaped identifiers such as `«name»`, hierarchical names, literals, punctuation, and comments. Preserve `--` comments, nested `/- ... -/` comments, declaration `/-- ... -/` documentation, and module `/-! ... -/` documentation. Do not add JavaScript comment or interpolation semantics by analogy.

Admit natural/scientific numeric literal syntax, characters, strings and escapes, raw strings, string interpolation, name literals, and registered literal notations. Interpretation is type-directed where Lean makes it so; `1` is not necessarily a `Nat`, and a scientific literal does not universally mean IEEE `Float`. Embedded expressions are parsed in the category specified by their notation. [L-TERM] [L-INIT]

PS0 uses UTF-8 source and the pinned Lean scanner's treatment of source whitespace, line endings, and literal escapes. This edition does not import a narrower tab/ASCII-space rule from an older profile. Any normalization used by an implementation must preserve source spans and the native token stream. There is no JavaScript automatic semicolon insertion. The spellings `/* ... */` and `// ...` are not Lean comment delimiters; tests must not confuse invalid comment syntax with a call-adjacency error.

### Source kinds, module headers, and imports

**Feature / profile:** Full native module capabilities; explicit PS default visibility  
**Rule family:** `PS0V1-MOD`  
**Source basis:** [L-MODULE], [L-CMD]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
header ::= "module"? "prelude"? importCommand*
importCommand ::= "public"? "meta"? "import" "all"? moduleName
// Legality restrictions are checked, not all combinations succeed.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psHeader ::= "module"? "prelude"? importCommand*
// Omitted module: implicit modern module + public-name default.
// Written module: native modern visibility default.
// .lean always uses unmodified native source semantics.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
module
public import Std

public def answer : Nat := 42
```

**ProofScript `ps0` v1**

```proofscript
public import Std

const answer: Nat := 42
-- This fragment's implicit module has public names.
```

**Source language distinction and static meaning.**

**PS0V1-SOURCE-01.** `.ps` uses the PS0 v1 host grammar; `.lean` uses ordinary pinned Lean without injected PS syntax or source-policy restrictions. A project containing both source kinds must retain that distinction. A native Lean dependency does not automatically receive a PS verified-executable label.

**PS0V1-MODULE-01.** Without a written `module`, a `.ps` file denotes a modern Lean module with public names by default. A written `module` selects native modern visibility defaults instead. A `private` declaration overrides a public default. A public name and an exposed definition body are different properties. The written header does not disable PS calls.

`prelude` occurs before imports and suppresses the implicit ordinary **and meta** `Init` imports. [L-IMPORT] It does not synthesize `Nat`, `Unit`, or helper libraries. A bootstrap module cannot use nullary `function` sugar before its `Unit` dependency exists; enabling the PS parser must not secretly import `Init`/`Lean` into such a module.

Admit the pinned header forms: `import M`, `public import M`, `meta import M`, `public meta import M`, `import all M`, and valid combinations of meta and all permitted by Lean. Preserve header ordering and actual module-system restrictions. In particular, **`public import all M` is not valid**: public re-export and private/all access require separate imports as Lean specifies. Missing modules, unsupported artifact versions, and invalid visibility dependencies remain errors. [L-MODULE]

A `meta` import controls compile-time availability, not proof unsafety. Importing a library for ordinary execution does not necessarily make all its declarations available to downstream metaprograms. Preserve the distinction between a local `meta import` and `public meta import` needed by exported metaprograms. [L-CMD]

| Source shape | Admission / meaning |
|---|---|
| `import M` | Module-local import under modern module rules |
| `public import M` | Public re-export of the permitted public scope |
| `meta import M` | Compile-time availability under native staging rules |
| `public meta import M` | Compile-time availability required by exported metaprograms |
| `import all M` | Native all/private access, subject to restrictions |
| `meta import all M` | The native combination, where its module prerequisites hold |
| `public import all M` | Refused; split public re-export from separate all/private access |
| Imports following ordinary commands | Refused as misplaced header commands |

The dependency graph must identify module names and source kinds unambiguously. Ordinary native handling of legacy dependencies is inherited rather than globally banned; a specific modern import still must satisfy Lean's actual compatibility rules. No package layout or command-line edition flag is specified here.

### Namespaces, sections, variables, open, and export

**Feature / profile:** Shared scope and generalization semantics  
**Rule family:** `PS0V1-SCOPE`  
**Source basis:** [L-CMD]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
command ::= "namespace" ident | "section" ident? | "end" ident?
          | "variable" binder+ | "universe" ident+
          | "include" ident+ | "omit" (ident | instBinder)+
          | "open" openDecl | "export" ident "(" ident+ ")"
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
command ::= same native command families
// Binder parentheses are not term applications.
// open/option ... in scopes one command, term, or tactic as defined.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
namespace MathOps
  def twice (n : Nat) : Nat := n + n
end MathOps
open MathOps
section
  variable (n : Nat)
  def result : Nat := twice n
end
#check result
```

**ProofScript `ps0` v1**

```proofscript
namespace MathOps
  function twice(n: Nat): Nat := n + n
end MathOps
open MathOps
section
  variable (n: Nat)
  def result: Nat := twice(n)
end
#check result
```

**Source language distinction and static meaning.**

Admit namespaces, nested sections, named/unnamed `end`, `variable`, `universe`, `include`, `omit`, all native `open` forms, `open scoped`, namespace `export`, scoped `... in`, and `with_weak_namespace`.

Name lookup, protected names, aliases, local/scoped registrations, and section generalization follow Lean. A theorem's proof body must not silently add section variables to its public statement. Public names and exposed definition bodies are distinct. Admit `@[expose]` and section-level exposure with their pinned semantics; do not infer exposure from public naming. `abbrev` follows Lean's own transparency and exposure behavior rather than a blanket “all public bodies hidden” rule. [L-CMD] [L-DEFS]

In this example `result` acquires an explicit `Nat` parameter because its body uses the section variable; the local name `n` disappears at `end`, while `result` survives. A theorem is different: proof-only variable usage must not change its statement; only statement dependencies and the applicable `include`/instance rules determine its parameters.

`open N hiding x`, `open N (x y)`, `open N renaming x → x'`, and `open scoped N` have distinct effects. `open scoped` activates scoped registrations without opening all ordinary names. Namespace `export N (x)` creates a naming alias; it is not foreign-symbol `@[export]`. `with_weak_namespace` changes the effective namespace without ordinary scope delimitation. Preserve ambiguities and native name-resolution errors, not a new PS search-order algorithm.

### Layout, braces, separators, and category ownership

**Feature / profile:** Native alternatives plus owned braced surface  
**Rule family:** `PS0V1-LAYOUT`  
**Source basis:** [L-TERM], [L-DO], [L-SYNTAX]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
declVal ::= ":=" term | equations | "where" structFields
doSeq ::= nativeIndentedDoSeq | "{" doElem+ "}"
tacticSeq ::= nativeIndentedTactics | "{" tactics "}"
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psDeclVal ::= nativeDeclVal | ":=" "{" psTerm "}"
psMatch ::= "match" discrs "with" "{" matchAlts "}"
psDo ::= "do" "{" psDoItems "}"
// Native layout forms remain admitted.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def next (n : Nat) : Id Nat := do
  let x := n + 1
  return x

theorem reflN (n : Nat) : n = n := by
  rfl
```

**ProofScript `ps0` v1**

```proofscript
function next(n: Nat): Id Nat := do {
  let x := n + 1
  return x
}
theorem reflN(n: Nat): n = n := by { rfl }
```

**Source language distinction and static meaning.**

**PS0V1-LAYOUT-01.** V1 retains the braced declaration, proof, `match`, `do`, and control-flow sugar. It additionally admits native Lean layout alternatives and native semicolon uses. Semicolons are category-specific: a tactic combinator is not interchangeable with a `do` statement separator. Braces are not an unconditional indentation switch for every embedded language.

A declaration `:= { term }` contains one term; multiple imperative statements require a `do` term. Record instances and updates retain their distinct syntax nodes. The parser must not reinterpret a malformed record as a successful generic braced body, or a malformed `do` statement as an unrelated expression just to continue.

**PS0V1-GRAMMAR-01.** Native Lean grammar categories are the model; this document does not invent an independent universal EBNF. Its grammar descriptions are schemata. Actual registered parser combinators and the owned PS0 delta determine acceptance.

The ordinary `.ps` host-term application rules apply to executable terms, propositions, contracts, and normal proof-term arguments. Quoted syntax is **syntax data**, not an already executing host term. A registered embedded language may own its delimiters and category productions. Its literal tokens and native-category quotations must not be rewritten with a text-level “replace calls/braces” pass. The concrete grammar context must be known before applying a ProofScript transformation.

For new extensions, literal native category names and explicit `psTerm`/`psCommand`/`psTactic`/`psDoSeq` select the operand and result contracts in §0B. Standard host adapters are pinned there; other extensions keep their declared native or custom operands. No failed host parse is retried as native input. Explicit native operands are an intentional syntax-data/DSL boundary, not a relaxation of proof or assurance checking.

These requirements are important because Lean's grammar changes after imports and elaborated declarations. The pinned module parser expressly notes that most Lean files cannot be parsed without elaboration. [L-MODULE] [L-SYNTAX]

PS braced structure/instance field lists admit newline separation and the explicitly defined comma/semicolon form for their category (§4); arbitrary whitespace is not a separator between declarations. An outer `:= { e }` wrapper only groups one term. A record `{ x := e }`, a subtype `{x : A // P x}`, an implicit binder `{x : A}`, and a block are different nodes. A plain tactic `;` separates sequential tactics, just as a permitted newline does. The different combinator `tac₁ <;> tac₂` applies `tac₂` to each goal produced by `tac₁`. Bracketed tactic sequences retain native focusing and goal-closure behavior. Canonical examples prefer newlines, but semicolons are not globally forbidden.

### Declaration-body braces and record ownership

**PS0V1-BRACE-01.** The optional one-term wrapper is recognized only at a declaration/local-definition `:=` body slot that explicitly admits it. It is not a new arbitrary `{term}` expression everywhere. Already-owned `do`, tactic, match, control, structure-field and local-helper braces keep their own grammar. At an eligible direct `:= { ... }` slot, determine ownership **before typing or coercion insertion**:

1. If the entire braced fragment is a valid native structure instance/update or subtype shape (with host expression operands), it belongs to that native term form. This includes `{x}`, `{x,y}`, `{}`, `{x : T}`, and `{ p with x := e }` when syntactically applicable, even if typing subsequently fails. Native extension competition within that term category remains subject to §9.
2. A fragment committed to a record/update/subtype by its field assignment, update `with`, subtype `//`, or actual outer field-list separator must report an error if malformed; it cannot recover as a successful one-term wrapper. Tokens inside a nested term, literal or quotation do not count as outer field syntax.
3. Otherwise the wrapper accepts exactly one complete host term, with no recovery or leftover tokens. If both wrapper and record parses succeed, the record wins. If genuinely different non-record extension parses remain, use the normal category/conflict rules rather than choosing by successful typing.

Thus `const y: Box := {x}` is a record-punning attempt, not a coercion of the term `x` to `Box`. To request the wrapper interpretation explicitly, write `:= { (x) }`, or simply `:= x`. For a term whose own syntax could participate in record update, `:= { (e) }` is recognized as the wrapper only when that outer fragment is not a record/update form; a programmer can always use plain `:= (e)` to supply the grouped term. A malformed record does not become a wrapper merely because a coercion makes the wrapper alternative type-correct.

| Direct declaration RHS | Owned interpretation |
|---|---|
| `:= {x}` | Punned structure term; a failed field/type check remains a record error |
| `:= { (x) }` | One-term wrapper around `x` when the entire braces have no record/update tail |
| `:= { x + 1 }` | One-term wrapper around the expression |
| `:= { x := 1 }` | Structure instance |
| `:= { p with x := 1 }` | Structure update |
| `:= { (p) with x := 1 }` | Structure update, not a wrapper ending after `(p)` |
| `:= do { ... }` | Native/PS do-sequence grammar, not this wrapper rule |

**PS0V1-LIST-BOUNDARY.** In a PS braced field list, one field is parsed using its declared type/default/equation category before an outer comma/semicolon is treated as a separator. Quantifier commas, tuple commas and call commas belong to their nested productions. Equivalent native/comma parse alternatives with the same field/binder partition can be coalesced; two successful parses with different partitions are a PARSE ambiguity, not a type-directed choice. Parenthesizing a complete field type/value disambiguates such an extension-induced overlap. Empty structure/class and instance-field lists are syntactically permitted where their native category allows them; missing required fields is then a typing issue, not a universal nonempty-list rule.

## 2. Declarations, functions, binders, and arguments

### Ordinary definitions and declaration families

**Feature / profile:** Native declaration semantics with explicit PS aliases  
**Rule family:** `PS0V1-DECL`  
**Source basis:** [L-CMD], [L-DECL], [L-PREDEF]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
command ::= modifiers (defDecl | abbrevDecl | opaqueDecl
          | theoremDecl | exampleDecl | axiomDecl | instanceDecl)
defDecl ::= "def" declId nativeTelescope type? contractSeq? declVal
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
command ::= nativeDeclaration | functionDecl | constDecl
functionDecl ::= modifiers "function" declId psFunctionBinders
                 type? psContractSeq psDeclVal
constDecl ::= modifiers "const" declId type? psDeclVal
// Alias modifiers must be legal for the corresponding native def.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def double (n : Nat) : Nat := n + n
def inferred (n : Nat) := n + n
abbrev Count := Nat
example : 1 = 1 := rfl
```

**ProofScript `ps0` v1**

```proofscript
def double(n: Nat): Nat := { n + n }
function inferred(n: Nat) := n + n
abbrev Count := Nat
example : 1 = 1 := rfl
```

**Source language distinction and static meaning.**

`def` declares a typed value; functions are values with dependent function types. `abbrev` has its native transparency behavior. `theorem` declares checked evidence of its actual statement, while `example` checks an anonymous example. `opaque`, `axiom`, and `instance` are described in their own subsections below. A native declaration may use its original explicit telescopes, equation right-hand sides, and supported deriving clauses.

A result type may be inferred where Lean permits an omitted type. A written type constrains elaboration; it is not erased as a formatting hint. `:= { e }` lowers to `:= e` as one expression, subject to the syntax-only record/body ownership rule in §1. A block containing multiple effectful statements must be a `do` expression.

**PS0V1-DECL-ALIAS.** `function` lowers to a native `def`, preserving its name, universes, allowed modifiers, binder order, type, contracts, body, termination information, and local declarations. `const` lowers to a native `def` with no source telescope; section generalization may still add parameters. A function-valued `const` can be callable because of its type, not because `const` implies a new calling convention. Neither alias creates a new kernel declaration kind.

### Named values and function-valued constants

**Feature / profile:** Parameterless source definition alias  
**Rule family:** `PS0V1-CONST`  
**Source basis:** [L-CMD], [L-DECL]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
valueDecl ::= modifiers "def" declId type? ":=" term
// A term can itself be a lambda or have a function type.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
constDecl ::= modifiers "const" declId type? psDeclVal
// No source parameter telescope or intrinsic contract clauses.
// Use def/function for declared parameters and contracts.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def answer : Nat := 42
def inc : Nat → Nat := fun n => n + 1
#check inc 2
```

**ProofScript `ps0` v1**

```proofscript
const answer: Nat := 42
const inc: Nat → Nat := fun n => n + 1
#check inc(2)
```

**Source language distinction and static meaning.**

`const` means a named definition, not JavaScript constant storage or a mutable binding with reassignment disabled. It has no parameter binder list in its declaration. `const inc: Nat → Nat := ...` is legal because the right-hand side is a function. A source `const answer(x: Nat) := ...` is not this alias; use `function` or `def`.

Ordinary local binding uses `let` or `have`, not `const`. In a section, source-parameterlessness does not suppress Lean's generalization: a `const` whose type/body uses an eligible section variable may receive an elaborated parameter. That must be shown by the actual type, not hidden behind the word “constant.”

### Explicit, implicit, strict-implicit, instance, and interleaved binders

**Feature / profile:** Native telescopes plus function-alias comma groups  
**Rule family:** `PS0V1-BIND`  
**Source basis:** [L-CMD], [L-TERM]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
binder ::= "(" ident+ ":" term default? ")"
         | "{" ident+ ":" term "}"
         | "⦃" ident+ ":" term "⦄" | "{{" ident+ ":" term "}}"
         | "[" (ident ":")? term "]"
telescope ::= nativeBinder*
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psParam ::= ident ":" psTerm nativeDefaultOrAutoParam?
psExplicitGroup ::= "(" psParam ("," psParam)* ","? ")"
psNonExplicitBinder ::= implicitBinder | strictImplicitBinder | instBinder
psAliasTelescope ::= psNonExplicitBinder*
                    (psExplicitGroup psNonExplicitBinder+)* psExplicitGroup?
psFunctionBinders ::= nonempty(psAliasTelescope)
                   | psNonExplicitBinder* "()"
// A final () is function-only. Native def telescopes remain available.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def same {α : Type} [BEq α] (x y : α) : Bool := x == y

def choose (n : Nat) [Decidable (n = 0)]
    (x : Fin (n + 1)) : Nat := x.val
```

**ProofScript `ps0` v1**

```proofscript
function same {α: Type}[BEq α](x: α, y: α): Bool := x == y

function choose(n: Nat)[Decidable(n = 0)]
    (x: Fin(n + 1)): Nat := x.val
```

**Source language distinction and static meaning.**

An explicit parameter normally appears at application; an implicit parameter is synthesized/inferred according to Lean's binder rules; a strict implicit binder follows Lean's stricter insertion conditions; an instance binder requests instance synthesis. These are typing distinctions, not runtime argument decorations. Named and unnamed instance binders remain distinct native forms.

**PS0V1-BIND-ORDER.** Preserve the original ordered telescope. A later type/default may depend on earlier binders. Implicit and instance binders may occur before, between, or after explicit groups. Do not reorder them to simplify lowering.

**PS0V1-BIND-ALIAS.** In the owned `function` spelling, consecutive explicit parameters belong in one comma group; adjacent explicit groups require an intervening nonexplicit binder. Each comma parameter supplies its own type. Native declarations such as `def f (x y : Nat)` and `def f (x : Nat) (y : Nat)` remain available in v1; the `function` alias does not erase those native capabilities. Native binders and the PS comma extension compose by `psMixedTelescope` and the explicit context matrix below. Identical normalized binder partitions coalesce; different successful partitions are a PARSE ambiguity. Typing is not used to choose one.

A normal explicit group is nonempty. The final `()` exception is restricted to `function` as described next. Lambdas, quantifiers, section variables, and patterns use their own native binder grammar, not the declaration alias grammar. `fun (x : Nat) => x` is legal; `fun (x: Nat, y: Nat) => ...` is not introduced as a lambda-binder alias by this reference.

The grammar does not relax native well-formedness: for example, an instance type still must elaborate appropriately, and default/automatic parameters must satisfy their actual native constraints.

### Telescope composition and head/context matrix

**PS0V1-BIND-MATRIX.** `psMixedTelescope` is the original native telescope for its particular signature position, extended by allowing one PS explicit comma group wherever that telescope accepts an explicit bracketed parameter group. Groups are processed left to right. A comma group expands into its ordered explicit binders; every named comma parameter supplies its own type, and may have its own native default or automatic-parameter suffix. Native identifier-only, shared-type, anonymous and inferred binders stay available through the native alternatives; they are **not** newly permitted as untyped/anonymous entries of a PS comma group. The `function` alias continues to use its stricter `psAliasTelescope`, not the mixed grammar.

```text
psParam          ::= ident ':' psTerm (nativeBinderTactic | nativeBinderDefault)?
psExplicitGroup  ::= '(' psParam (',' psParam)* ','? ')'
psMixedBinder    ::= nativeBinderInThisSignature | psExplicitGroup
psMixedTelescope ::= psMixedBinder*   // only at native telescope positions
psBasicFun       ::= native basicFun binder/arrow structure with host type/body operands
psLocalDeclVal   ::= localSimple | localEquations | localStructValue  // detailed below
```

The last two names are descriptive categories, not source keywords. Defaults are parsed with Lean’s **ordered choice** [L-TERM-BASIC]: unparenthesized `:= by tactics` is the native automatic-parameter form, whereas `:= (by tactics)` is an ordinary default term. A PS comma group must preserve that distinction. The body of a quantified type consumes its own comma before an outer parameter separator is considered. An existing native group and a one-parameter PS group yielding exactly the same binder data are one interpretation. When two complete parses yield different binder partitions, reject before elaboration; parentheses around the type/default can resolve such a conflict.

| Context / declaration head | Telescope rule | Empty `()` inserts Unit? |
|---|---|---|
| `def`, `abbrev`, `opaque`, `theorem`, `example`, `axiom`, `instance`, and `recall` signature | Native signature requirements plus `psMixedTelescope` | No |
| `inductive`, `coinductive`, `class inductive`, `structure`, `class` parameters | Native signature requirements plus `psMixedTelescope` | No |
| Constructor parameters after its constructor name | Native constructor signature plus `psMixedTelescope` | No |
| Named structure/class field's **method parameters**, and instance/record initializer method parameters | Native field-specific telescope plus PS explicit groups; field declaration versus field initializer remains distinct | No |
| Structure constructor-name specification before `::` | Native constructor binder positions plus PS explicit groups | No |
| Named local `let` / `let rec` function parameters; braced `where` local `def` helpers | Native local signature plus `psMixedTelescope` | No |
| `function` | Exactly `psFunctionBinders` and its nonadjacent explicit-group restriction | Only its final dedicated nullary alternative |
| `const` | No source telescope | No |
| `variable`, quantifier/lambda binders, `given`, invariant/basicFun binders and pattern binders | Their native binder categories; host expressions in their type/body slots | No |
| A grouped field declaration such as `(x y : A)` | Native field-group form; not a comma list of method parameters | No |
| An arbitrary user DSL | Only the binders explicitly declared by that DSL | No implicit extension |

A context whose native signature requires a result type still requires it; this table does not relax theorem, opaque, axiom or instance signatures. Computed fields use their pinned field-name/type/equations syntax, not an invented general telescope. The table does not add declaration heads where Lean has no such declaration.

For example `def f (x y : Nat) (z: Nat, w: Nat) := x + y + z + w` is mixed source and expands to four explicit native parameters. `function f(x: Nat)(y: Nat) := ...` still fails its intentional alias grammar. `fun (x: Nat, y: Nat) => ...` is not a new two-parameter lambda abbreviation; a native tuple/pattern interpretation, where legal, keeps its different native meaning. An empty `def f()` is not repaired with a hidden parameter.

### Nullary function declarations and required Unit

**Feature / profile:** Owned source sugar; ordinary Pi type  
**Rule family:** `PS0V1-NULLARY`  
**Source basis:** [L-CMD], [L-TERM], [L-DECL]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
defDecl ::= "def" ident "(" ident ":" "Unit" ")" type? declVal
// No new logical zero-arity function kind.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
nullaryFunction ::= "function" declId psNonExplicitBinder* "()"
                    type? psContractSeq psDeclVal
// Lower to a fresh required (_u : Unit) binder at the final position.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def tick (_u : Unit) : Nat := 1
def unitUse (u : Unit) : Nat := 1
#check tick ()
```

**ProofScript `ps0` v1**

```proofscript
function tick(): Nat := 1
function unitUse(u: Unit): Nat := 1
#check tick()
#check unitUse(())
```

**Source language distinction and static meaning.**

**PS0V1-NULLARY-01.** `function tick(): Nat := 1` denotes a definition of type `Unit → Nat`, using a fresh hygienic unused `Unit` parameter. The inserted binder is required, not an optional parameter with a default value. It occurs after any preceding permitted nonexplicit binders. `()` must be the terminal function binder group; an explicit parameter before or after it is not a source-nullary declaration.

No other declaration, constructor, instance field, lambda, or alias acquires a hidden Unit argument because it contains an empty-looking group. `def f()`, `abbrev T()`, `structure S()`, constructor declaration `| nil()`, and field declaration `method()` do not receive this lowering. They must satisfy their own native grammar; the empty nullary spelling itself is not added to them. A source constructor **pattern** `Ctor()` is separately governed by §4 and is not a declaration.

`function f {α: Type}(): Nat := ...` still has its implicit type parameter before the Unit argument. Type inference must resolve that parameter normally at a call; an empty call is not permission to guess it. A `prelude` module requires the actual `Unit` declaration before using this sugar.

### Calls, grouping, tuple arguments, and postfix precedence

**Feature / profile:** Owned host term grammar; Lean curried application  
**Rule family:** `PS0V1-CALL`  
**Source basis:** [L-TERM]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
application ::= head argument+
argument ::= termAtArgumentPrecedence | namedArgument | ".."
// Native f (a,b) supplies one tuple argument.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psPostfix ::= nativeAtomicOrPostfixHead (nativeHighPostfix | adjacentCall)*
// nativeHighPostfix includes projection, explicit universes and indexing.
adjacentCall ::= "(" psCallArgs? ")"  // zero trivia gap after head
psCallArgs ::= positional* named*      // comma-separated, one trailing comma
named ::= ident ":=" psTerm
// Whitespace application consumes completed postfix terms.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def add (x y : Nat) : Nat := x + y
def sumPair (p : Nat × Nat) : Nat := p.1 + p.2
#check add 1 2
#check sumPair (1, 2)
```

**ProofScript `ps0` v1**

```proofscript
function add(x: Nat, y: Nat): Nat := x + y
function sumPair(p: Nat × Nat): Nat := p.1 + p.2
#check add(1, 2)
#check sumPair((1, 2))
```

**Source language distinction and static meaning.**

**PS0V1-APP-01.** In ordinary host `.ps` terms:

| Source | Interpretation |
|---|---|
| `f(x, y)` | Two explicit source arguments; Lean curried application |
| `f x y` | Native unparenthesized left-associated application |
| `f((x, y))` | One tuple argument |
| `f(())` | One explicitly written `Unit` argument |
| `f()` | Empty explicit source argument list; completion rule below |
| `f (x)`, `f (x, y)`, `f ()` | Rejected as gap-parenthesized host applications |
| `variable (x : A)`, `fun (x : A) => x` | Binding syntax, not a call; admitted |
| `exact (h)`, `#check (f x)`, `a + (b * c)` | Fresh grouped terms in their categories; admitted |

Comments between a completed application head and `(` count as a gap; comments inside an adjacent call do not. This remains a syntax-tree/category rule, not an identifier-space-parenthesis regular expression. Native quotations and explicitly owned embedded categories follow §1 and §9. Ordinary `.lean` keeps all native application spellings.

**PS0V1-APP-02.** Empty invocation first establishes a callable Pi/`CoeFun` head. Perform Lean's permitted implicit, instance, default, and automatic-parameter completion. Accept only if no required explicit binder remains, or exactly one remains whose instantiated type is definitionally `Unit`; insert `()` only in the latter case. Do not guess `Unit` for an unsolved type, synthesize arbitrary `Inhabited` values, accept a non-callable value, or silently fill two required `Unit` arguments.

`function f(): R := body` introduces a **required** `Unit` binder, so `f : Unit → R`. It is not parameterless `def f : R`. Nonempty partial application remains ordinary Lean partial application.

**PS0V1-APP-03.** Postfix calls bind to their immediate atomic/postfix head before surrounding whitespace application: `f g(x, y)` means `f (g x y)`, whereas `(f g)(x, y)` means `(f g) x y`. Preserve named-argument rules, explicit universes, dependent binder instantiation, and the argument tree in formatting.

**PS0V1-POSTFIX-01.** An adjacent call can follow any completed atomic/high-binding postfix head that the native application grammar admits, including a grouped term, explicit-universe constant, field/numeric projection, indexed collection element, or compatible extension-produced atomic term. Native high-binding postfix operations keep their pinned precedence; PS calls bind before surrounding whitespace application as stated above. A lower-precedence compound expression is grouped to make it the head. Therefore `f.{u}(x)`, `fs[i](x)`, and `(if p then f else g)(x)` are legitimate source shapes when their types and index obligations fit. These rules do not turn all native trailing operators, such as arrows or low-precedence pipelines, into high-precedence postfixes.

**Argument-list closure.** Adjacent calls admit positional arguments, then named arguments, separated by commas. One trailing comma is allowed after a nonempty list. A leading comma, repeated comma, missing argument between commas, duplicate name, or positional argument after a named argument is invalid. `f(,)` is not an empty call. Unknown or duplicate names fail no later than application elaboration; syntax-order failures are parse errors. Named arguments identify actual declaration binders, not arbitrary object properties.

**Context-uniformity.** The same host application rule applies to theorem statements, contracts, ordinary term arguments of tactics, diagnostics, and executable code. `exact h(p)` is legal when typed; `exact h (p)` is a rejected host application; `exact (hp)` is legal because the parenthesis starts the tactic's fresh term argument. Native binders, operator operands, patterns, and explicitly category-owned quoted/configuration syntax are not accidentally included in this ban.

| Source | Required interpretation / result |
|---|---|
| `f g(x, y)` | `f (g x y)`, not `(f g) x y` |
| `(f g)(x, y)` | `(f g) x y` |
| `f(x) y` | `(f x) y` |
| `obj.method(x) y` | Complete postfix call, then native application; receiver insertion stays type-directed |
| `f/- gap -/(x)` | Rejected: a comment is a nonempty gap |
| `f(/- inside -/ x)` | Accepted if typed: the head is adjacent to `(` |
| `f((x, y))` | One tuple argument |
| `f(())` | One explicitly written Unit argument |
| `f(x,)` | One argument; trailing comma does not create a tuple or extra parameter |

A formatter must preserve the argument tree. It cannot turn `f((x, y))` into `f(x, y)` or insert a gap after the callable head. Source-position tracking is required for the adjacency check; a token-only reconstruction cannot infer whether comments separated a call.

### Defaults, named arguments, CoeFun, and empty invocation

**Feature / profile:** Type-directed Lean application with explicit completion boundary  
**Rule family:** `PS0V1-DEFAULT`  
**Source basis:** [L-TERM], [L-ELAB]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
binder ::= "(" name ":" type (":=" defaultOrTactic)? ")"
namedArgument ::= "(" name ":=" term ")"
// Native application uses optParam/autoParam elaboration where valid.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psParam ::= name ":" psTerm (":=" defaultOrTactic)?
psNamedArgument ::= name ":=" psTerm
emptyCall ::= callableHead "()"
// Empty-call completion is the algorithm stated below, not a default value.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def greet (name : String := "world") : String := name
#check greet (name := "Ada")
def useUnit (u : Unit) : Nat := 1
#check useUnit ()
```

**ProofScript `ps0` v1**

```proofscript
function greet(name: String := "world"): String := name
#check greet(name := "Ada")
#check greet()
function useUnit(u: Unit): Nat := 1
#check useUnit()
```

**Source language distinction and static meaning.**

**PS0V1-EMPTY-01.** To elaborate `f()`: establish that `f` is callable by a Pi/function type, possibly through an available native `CoeFun` instance; resolve implicit/instance arguments and declared default/automatic arguments using Lean's rules; inspect the remaining required explicit telescope. Accept when nothing required remains, or when exactly one required explicit binder remains and its instantiated type is definitionally equal to `Unit`, in which case insert `()`.

Do not guess that an unsolved metavariable is Unit. Do not synthesize an arbitrary `Inhabited` value. Do not stop counting required parameters after encountering a first Unit parameter. Two required Units, Unit followed by a required Nat, or any other missing required value must fail. A bare value `answer : Nat` is not callable as `answer()`.

Default expressions are declared in lexical scope and may depend on preceding parameters; they are instantiated in that telescope at application. Automatic proof parameters use their actual native elaboration context and may fail. Caller-local values are not invented defaults. An unresolved instance remains an error. Native use of a function without call punctuation still follows expected-type-directed elaboration; it is not universally equivalent to writing `f()`.

Nonempty calls may be partial applications: `add(1)` may have type `Nat → Nat`. The strict empty-call rule does not require all **nonempty** calls to saturate the function.

| Callable declaration | Invocation | Outcome |
|---|---|---|
| `function tick(): Nat := 1` | `tick()` / `tick(())` | Same Unit application when types resolve |
| `function greet(name: String := "world"): String := name` | `greet()` | Use the declared default |
| `function two(a: Unit, b: Unit): Nat := 0` | `two()` | Reject: two required arguments |
| `function one(n: Nat): Nat := n` | `one()` | Reject: no required-Nat synthesis |
| `const answer: Nat := 42` | `answer()` | Reject: not callable |
| `function add(x: Nat, y: Nat): Nat := x + y` | `add(1)` | Ordinary nonempty partial application |

A callable object's instance-based coercion obeys these same checks. Importing a CoeFun instance changes the elaboration environment, not the source meaning of an empty list.

**PS0V1-EMPTY-02 — completion order and higher-order results.** The rule concerns the **whole remaining Pi telescope**, not the number of parameters originally written before a declaration’s result colon. Retain Lean’s implicit/instance/default/automatic-parameter elaboration order, expected-type propagation and explicit `@` mode. Completion may be postponed while legitimate constraints are solved; it must not assign a metavariable to `Unit` merely to make this rule succeed. Opening a required binder symbolically is not supplying its value. A default or instance depending on a later-permitted Unit insertion is checked after the actual insertion, under its instantiated type. Reinspect the resulting type after insertion: if it exposes another required explicit binder, fail. No eta-expanded function is accepted as an empty invocation simply because its expected type is functional. Failed/default/automatic proof obligations remain genuine elaboration failures.

Under explicit `@` mode, implicit/instance arguments exposed as explicit follow the native application rules, including native suppression of optional/automatic insertion. They count as required when not supplied; `@id()` does not synthesize its explicit type argument. Expected types may determine otherwise inferable implicit arguments, but cannot supply a missing required explicit value by an undeclared default. The elaborated head must have a callable type **before** consuming the completion’s arguments; a value cannot become callable by coercing an arbitrary result after the fact. Available native `CoeFun` resolution remains permitted.

```proofscript
function makeAdder(): Nat → Nat := fun n => n + 1
#check makeAdder(())  -- valid nonempty partial application: Nat → Nat
-- makeAdder() is refused: the whole telescope is Unit → Nat → Nat.
-- A new declared-arity exception is intentionally not introduced here.
```

A returned function or callable object is not repeatedly invoked through new `CoeFun` steps after the selected head’s invocation completes. Pi binders actually exposed in the resulting function type are still counted as above. The distinction is type-directed and independent of the declaration alias. Solved placeholders and implicit inference retain their native semantics; arbitrary required-argument synthesis does not.

### Visibility, meta, noncomputable, nonrec, and modifier legality

**Feature / profile:** Native declaration modifiers, not arbitrary permutations  
**Rule family:** `PS0V1-MODIFIERS`  
**Source basis:** [L-CMD]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
declModifiers ::= doc? attributes? visibility? protected?
                  ("meta" | "noncomputable")? "unsafe"?
                  ("partial" | "nonrec")?
// The declaration family imposes further conditions.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
declModifiers ::= same native modifier ordering
// Apply only when legal for the lowered declaration family.
// const/function lower to def; no duplicate modifier aliases.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
private def helper (n : Nat) : Nat := n
protected def Exported.helper (n : Nat) : Nat := n
noncomputable def selected {α : Sort u} (h : Nonempty α) : α :=
  Classical.choice h
```

**ProofScript `ps0` v1**

```proofscript
private function helper(n: Nat): Nat := n
protected def Exported.helper(n: Nat): Nat := n
noncomputable def selected {α : Sort u}(h: Nonempty α): α :=
  Classical.choice(h)
```

**Source language distinction and static meaning.**

Admit native visibility, `protected`, `meta`, `noncomputable`, `unsafe`, `partial`, and `nonrec`, as applicable. **The set is not freely compositional.** The command parser orders modifiers and has alternatives such as `meta` versus `noncomputable`, and `partial` versus `nonrec`; the elaborator applies additional legality checks. Preserve those constraints instead of accepting arbitrary modifier permutations. [L-CMD]

`meta` is a staging/module-availability distinction, not an alias for `unsafe`. `noncomputable` permits logical definitions that need not have executable code; it does not provide an executable implementation. `nonrec` controls the declaration's recursive/name-resolution interpretation, not its proof status.

A logical/proof use of a noncomputable declaration can be valid even though using it in runtime-relevant code requires an executable implementation that may not exist. `meta` declarations are compile-time-only in the native module system; ordinary runtime definitions cannot acquire access merely by ignoring the modifier. `public meta import` requirements propagate for exported metaprograms. `nonrec` avoids treating a reference as recursion to the newly declared name where the native declaration rules apply; it is not a proof of termination.

### Opaque definitions, omitted bodies, and explicit axioms

**Feature / profile:** Three different declaration meanings  
**Rule family:** `PS0V1-OPAQUE`  
**Source basis:** [L-CMD], [L-DECL], [L-DEFS]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
opaqueDecl ::= "opaque" declId telescope ":" term (":=" term)?
axiomDecl ::= "axiom" declId telescope ":" term
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
opaqueDecl ::= same native forms with host PS terms
axiomDecl ::= same native form with host PS terms
// Body omission is not reinterpreted as axiom syntax.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
opaque hiddenCount : Nat := 7
opaque defaultCount : Nat
axiom assumedLaw : ∀ n : Nat, n = n
```

**ProofScript `ps0` v1**

```proofscript
opaque hiddenCount: Nat := 7
opaque defaultCount: Nat
axiom assumedLaw: ∀ n : Nat, n = n
```

**Source language distinction and static meaning.**

**PS0V1-OPAQUE-01.** Admit both a checked-body `opaque` and the native body-omission form. A bodyless `opaque` is **not automatically an axiom**. Lean attempts to supply an inhabitant, including through its `Inhabited`/`Nonempty` machinery, under the actual elaborator and compilation constraints. If the prerequisites fail, the declaration fails. Its opaque logical value, available executable implementation, and any external implementation must not be conflated. [L-DEFS]

`axiom` separately introduces an assumption with a well-formed type. Allowing its syntax does not prove that assumption, establish consistency of an arbitrary axiom set, or add it to an existing verified-build foundation. An imported theorem's assumption closure must remain visible in any claim about it.

A theorem about a public opaque interface cannot rely on its body unfolding as a regular definition. An omitted body's inhabitant synthesis may use the native default/nonempty machinery, and compilation may impose additional restrictions. An `extern` implementation is another separate issue (§7B). Do not turn failure to find an inhabitant into an automatically admitted axiom or a hidden `sorry`.

### Local definitions, equation bodies, and where/finally tails

**Feature / profile:** Native local recursion plus braced local-def surface  
**Rule family:** `PS0V1-WHERE`  
**Source basis:** [L-TERM], [L-CMD], [L-PREDEF]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
declVal ::= ":=" term terminationSuffix? whereDecls?
          | equations terminationSuffix? whereDecls?
whereDecls ::= "where" localRecDecl* finallyTail?
finallyTail ::= "finally" tacticSeq? ("|" ident "=>" tacticSeq)*
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psWhere ::= "where" "{" psLocalDecl* psFinally? "}"
psLocalDecl ::= doc? attributes? "def" ident psMixedTelescope type?
                psLocalDeclVal nativeTerminationSuffix?
psLocalDeclVal ::= ":=" psTermOrBodyWrapper | nativeLocalEquations
                 | "where" "{" psInstanceFields "}"
psFinally ::= "finally" "{" tacticSeq?
              ("|" ident "=>" "{" psTacticItems "}")* "}"
// Native where forms are also accepted. Only local sugar loses its def head.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def plusOne (n : Nat) : Nat := helper n
where
  helper (x : Nat) : Nat := x + 1
```

**ProofScript `ps0` v1**

```proofscript
function plusOne(n: Nat): Nat := helper(n)
where {
  def helper(x: Nat): Nat := x + 1
}
```

**Source language distinction and static meaning.**

A local `where` definition is not a new top-level export. It receives its native scope, captured parameters, recursion analysis, and termination requirements. The `def` in the PS braced form is deliberate surface sugar: the lowering below forms Lean’s local-recursive declaration syntax; it does not copy a `def` token into a native `where` slot.

A native `where` used to construct a structure value (`instance ... where field := ...`) is a different grammar role from local helper definitions; do not confuse them by stripping every `where` identically. Definitions by equations remain available, including pattern lambdas and local equation-style functions.

A native `finally` tail solves the supported named holes/obligations in the definition. It is distinct from effectful `try ... finally`. `spec` is the intrinsic-contract subsection (§7), not the sole possible native subsection. Empty/missing proof tails do not make generated obligations disappear. Multiple arbitrary `where` wrappers are not automatically admitted by nesting punctuation.

**PS0V1-LOCAL-01 — value and tail ownership.** A braced local helper uses `psLocalDeclVal`, not the top-level declaration-value union. A simple RHS (including the resolved optional body wrapper) becomes a native local `letIdDecl`; local equations become `letEqnsDecl`. The convenience structure-value body `def h ... : T where { fields }` becomes `h ... : T := { fields }`, converting field separators structurally and retaining method/proof field semantics. Preserve local doc comments, permitted attributes and the one native termination suffix after the helper value. All helpers of the enclosing braced `where` are supplied together to native local-recursion elaboration; do not turn mutually visible helpers into sequential nonrecursive lets.

A second attached `where` or `finally` on an individual local helper is **not** part of native `letRecDecl` and is not introduced by the local alias. Further helpers are expressible by native `let rec` in that helper's RHS. Proof-solving `finally` belongs to the owning enclosing declaration’s one `where` tail, with native scoped-hole behavior; use a local `by` expression for a local proof. This removes the erroneous inference that a broad top-level sketch grants arbitrary recursive helper tails, while preserving the complete native local-recursion and local-proof capabilities. A structure-value `where` immediately after a helper signature owns fields; a later enclosing `finally` owns proof obligations, not fields. Do not silently reattach a malformed local tail to the enclosing definition.

```proofscript
function localPoint(n: Nat): Nat := helper(n).x
where {
  def helper(k: Nat): Point where { x := k; y := 0 }
}
-- Requires Point with fields x and y. helper lowers to a local RHS record.
```

## 3. Expressions, monadic blocks, and control flow

### Lambdas, quantifiers, operators, tuples, and projections

**Feature / profile:** Shared typed expressions with PS application at embedded term positions  
**Rule family:** `PS0V1-EXPR`  
**Source basis:** [L-TERM], [L-INIT]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
term ::= "fun" funBinders "=>" term
       | "∀" binders "," term | term "→" term
       | "(" term ":" type ")" | "⟨" terms "⟩"
       | term "." field | registeredNotation
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psTerm ::= same native expression families + PS call syntax
// Declaration comma binders do not redefine fun/forall binders.
// Fields still use native type-directed receiver insertion.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def inc : Nat → Nat := fun n => n + 1
def fst (p : Nat × Nat) : Nat := p.1
def mapped (xs : List Nat) := xs.map (fun n => n + 1)
example : ∀ n : Nat, n = n := fun _ => rfl
```

**ProofScript `ps0` v1**

```proofscript
const inc: Nat → Nat := fun n => n + 1
function fst(p: Nat × Nat): Nat := p.1
function mapped(xs: List Nat) := xs.map(fun n => n + 1)
example : ∀ n : Nat, n = n := fun _ => rfl
```

**Source language distinction and static meaning.**

Admit native lambdas and pattern lambdas, dependent arrows, `forall`/`∀`, `exists`/`∃` notation, named and anonymous constructors, tuple notation, field projections and numeric projections, generalized field notation, pipeline forms, operators, type ascriptions, local definitions, proof expressions, and registered term notations.

Generalized field notation performs type-directed receiver insertion; it is not prototype lookup or universally first-argument method invocation. `e.f`, `e.1`, and a dotted declaration name must be resolved as Lean resolves them. Admit explicit universe suffixes on the forms allowed by the parser. [L-TERM]

Retain native `if ... then ... else ...` and the ProofScript braced conditional. Both use the intended Lean conditional elaboration; a Boolean condition must not silently select a different `bif` semantics. Native `bif` remains available as its own registered notation.

Native aliases `fun`/`λ`, `=>`/`↦` where registered, `forall`/`∀`, `exists`/`∃`, and `->`/`→` retain their genuine meanings and precedences. Operator precedence comes from actual registrations, not JavaScript conventions. `(· + 1)` is a native placeholder lambda; it does not create a new runtime placeholder object. `@f` exposes normally implicit arguments according to the native explicit-application rules. Leading-dot constructor names and numeric projections are resolved by their expected/type context.

Collections and products have real Lean types. `(x,y,z)` has Lean's nested product meaning, while `⟨x,y⟩` uses the expected single-constructor/dependent type. Neither is an untyped JavaScript array.

### Local definitions, hypotheses, local instances, and configuration

**Feature / profile:** Full native let/have family  
**Rule family:** `PS0V1-LET`  
**Source basis:** [L-TERM]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
term ::= "let" letConfig? letDecl separator term
       | "have" letConfig? letDecl separator term
       | "letI" letDecl separator term | "haveI" letDecl separator term
       | "let rec" letRecDecls separator term
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psTerm ::= same forms using PS terms in host positions
separator ::= native newline/semicolon when required by category
// let/have are not top-level const aliases.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def compute (n : Nat) : Nat :=
  let x := n + 1
  have y := x + 1
  y + 1
```

**ProofScript `ps0` v1**

```proofscript
function compute(n: Nat): Nat := {
  let x := n + 1
  have y := x + 1
  y + 1
}
```

**Source language distinction and static meaning.**

Admit `let`, `have`, pattern/equation bindings, `let rec`, `letI`, `haveI`, native local-binding configuration such as `+nondep`, `+postponeValue`, `+usedOnly`, `+zeta`, `+generalize`, and `(eq := h)`. Deprecated but still supported forms such as `let_fun`/`let_λ`, `let_delayed`, and `let_tmp` retain their pinned availability and warnings.

Admit record construction, field punning, typed instances, field methods/equations, inherited fields, and native update forms including supported multiple sources. These are typed Lean operations, not mutable JavaScript objects or unrestricted spread. Tuple and anonymous-constructor notation preserve their dependent/type-directed behavior.

`let` normally exposes a dependent local definition; `have` creates a nondependent local binding with its native elaboration behavior. They are not universally interchangeable in dependent types. `(eq := h)` preserves a local defining equality where supported. `letI`/`haveI` use the native local-instance/inlining elaboration rather than a new global instance declaration. Configuration switches control elaboration, not a user-defined evaluation order for arbitrary effects.

### Term conditionals, named condition proofs, and if-let

**Feature / profile:** Native conditional elaboration; PS braces are punctuation  
**Rule family:** `PS0V1-IF`  
**Source basis:** [L-TERM], [L-INIT], [L-DO]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
ifTerm ::= "if" (ident ":")? term "then" term "else" term
ifLetTerm ::= "if let" pattern ":=" term "then" term "else" term
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psIfTerm ::= "if" "(" psCondition ")" "{" term "}"
             "else" "{" term "}"
psCondition ::= (ident ":")? term
psIfLetTerm ::= "if let" pattern ":=" psTermBeforeBlock "{" term "}"
               "else" "{" term "}"
// Native then/else forms remain available.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def pick (n : Nat) : Nat := if n = 0 then 1 else n
def unopt (x : Option Nat) : Nat :=
  if let some n := x then n else 0
```

**ProofScript `ps0` v1**

```proofscript
function pick(n: Nat): Nat := if (n = 0) { 1 } else { n }
function unopt(x: Option Nat): Nat :=
  if let some n := x { n } else { 0 }
```

**Source language distinction and static meaning.**

A term conditional requires both branches and a compatible expected/result type. A proposition needs the applicable Decidable instance; a Boolean condition follows the actual Lean conditional/coercion mechanism. PS does not replace every `if` with `bif` or `cond`. Native `bif` remains its own notation.

`if (h : p) { ... } else { ... }` binds the native evidence for the selected condition in each branch. The colon is part of condition grammar, not a comma parameter declaration. Pattern bindings from `if let` exist in the appropriate success branch; failure takes the other branch. Native matching/elimination restrictions still apply.

A `do` conditional is different: its branches are sequences, an `else` may be omitted, and control-flow effects target the appropriate surrounding do block. It is not implemented by wrapping branch statements in an arbitrary pure term.

### Expressions immediately before PS control blocks

**PS0V1-HEADER-01.** The marker-free PS forms `if let p := e { ... }`, `if let p ← e { ... }`, `for p in e { ... }`, and `while c { ... }` parse their header expression in the category `psTermBeforeBlock`. This is `psTerm` with an explicit delimiter boundary: the first unquoted opening `{` at the header's current delimiter depth begins the **control body**, not a record/application operand of the header. Parenthesis and square-bracket nesting protect braces inside them; strings, comments, escaped identifiers and complete quotation payloads are consumed by their own lexer/parser and do not expose their internal braces. A native explicit-universe suffix `.{...}` is consumed as one suffix and is not the control-body opener. This rule is a parser-context operation, not string substitution.

A brace belonging to a header term must therefore be inside an explicit parenthesis/call/bracket group. Use `f({ x := 1 })`, `({ x := 1 })`, or `(do { ... })` as appropriate. A lambda with an implicit braced binder at this unprotected depth must likewise be grouped. Native `then`/`do` control forms keep their original marked header grammar; they provide the full native alternatives. The grouping requirement does not change which values/computations a header can denote.

For a zipped `for`, the outer comma separates complete `forDecl`s. `invariant` and `decreasing`, when present at the loop-header level, end the preceding header item as in the pinned loop parser. Their predicate/measure bodies also use this block boundary until the body opener or next permitted clause. Their binder grammar and order are otherwise native. An identifier spelling a clause keyword can still be used under the native escaping/grouping rules. A record-taking function is not allowed to consume the control body as one of its arguments.

For PS `if (condition) { ... }`, the matching `)` explicitly ends the condition; this boundary is not guessed from its type. For a PS block that omits native `then`/`do`, commit to the block boundary once it is selected; a malformed body must not fall back to an application of the header expression. Layout, nested `else`, returns, and monadic binds continue to follow their owning control category. Native forms and PS forms are distinguished by the explicit marker or the selected PS opener, not by which alternative elaborates successfully.

| Source fragment | Header and body partition |
|---|---|
| `for x in make({ n := 2 }) { use(x) }` | Collection is `make` applied to one record; second brace starts body |
| `if let some x := probe({ n := 2 }) { x } else { 0 }` | Record belongs to adjacent call, not to success body |
| `while test({ n := 2 }) { step }` | Condition is the completed call |
| `for x in (do { return xs }) { use(x) }` | Inner do is grouped; second block is loop body, subject to typing |
| `for x in f { x := 1 }` | Header is `f`; braces are a loop body, never an implicit record argument |
| `for x in f/-comment-/({ n := 2 }) { use(x) }` | Reject the host application gap; comment is not adjacency |

These are partition rules, not claims that the arbitrary names have suitable types. The concrete fixtures in Appendix D supply the missing contexts.

### Monadic sequencing, nested actions, mutable locals, and refutable binds

**Feature / profile:** Full native do family, both braced and layout forms  
**Rule family:** `PS0V1-DO`  
**Source basis:** [L-DO], [L-INIT]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
doTerm ::= "do" doSeq
doElem ::= letDecl | "let" "mut"? pattern "←" action fallback?
         | assignment | "have" letDecl | "let rec" localDefs
         | "return" term? | term | nestedDo | registeredDoElem
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psDo ::= "do" "{" doElem+ "}" | nativeLayoutDo
// Host terms use PS calls; bind/control nodes keep native semantics.
// Newline and native semicolon separators are category-specific.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def sumTwo (a b : Nat) : Id Nat := do
  let mut total := a
  total := total + b
  return total
```

**ProofScript `ps0` v1**

```proofscript
function sumTwo(a: Nat, b: Nat): Id Nat := do {
  let mut total := a
  total := total + b
  return total
}
```

**Source language distinction and static meaning.**

Admit generic Lean monads and transformers, `Id`, reader/state/error computations, `ST`, `BaseIO`, `EIO`, `IO`, tasks, and other imported effect facilities. `do` elaborates through the actual monad/control classes and return type. An arbitrary monad need not have the verification rules required by §7.

Admit braced and native-layout `do`, local `let`/`have`, local recursion, pure and monadic pattern bindings, fallback branches for refutable bindings, nested actions `←`, `let mut`, assignments including supported destructuring/monadic reassignment, and nested `do`. Preserve evaluation order, lexical mutable-variable scope, and native control-flow elaboration. [L-DO]

`let x := e` binds an ordinary value; `let x ← act` executes a monadic action. A nested `(← act)` is executed at the native elaboration-defined point, not deferred like an ordinary lambda. Refutable `let` patterns may have a native fallback branch (`| ...`) that returns/exits as required by their surrounding control context. Mutation is limited to variables introduced as mutable; ordinary `let` bindings cannot be assigned merely because an assignment parser exists.

Destructuring updates, array/field update sugar when registered, and local recursive declarations retain their native requirements. A reference cell (`ST.Ref` or IO reference) is a library object with aliasing/effect semantics; it is not identical to a syntactically mutable local.

### Do conditionals, monadic if-let, and unless

**Feature / profile:** Control-flow sequence grammar, not pure-term if  
**Rule family:** `PS0V1-DOIF`  
**Source basis:** [L-DO]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
doIf ::= "if" doCondition "then" doSeq
         ("else if" doCondition "then" doSeq)* ("else" doSeq)?
doCondition ::= (ident ":")? term | "let" pattern (":=" | "←") term
unless ::= "unless" term "do" doSeq
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psDoIf ::= "if" "(" psCondition ")" "{" psDoItems "}"
           ("else if" "(" psCondition ")" "{" psDoItems "}")*
           ("else" "{" psDoItems "}")?
psDoIfLet ::= "if let" pattern (":=" | "←") psTermBeforeBlock
             "{" psDoItems "}" ("else" "{" psDoItems "}")?
// Native forms, including unless ... do, remain valid.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def guarded (x : Option Nat) : Id Nat := do
  if let some n := x then
    return n
  return 0
```

**ProofScript `ps0` v1**

```proofscript
function guarded(x: Option Nat): Id Nat := do {
  if let some n := x {
    return n
  }
  return 0
}
```

**Source language distinction and static meaning.**

Do branches may contain multiple bindings, assignments, and early exits. Omitted `else` has the native no-op branch behavior where valid. Monadic `if let ... ← action` is included; it is not restricted to a pure `:=` condition. Native `unless ... do` uses its own parser and expected monadic context. Grouping must preserve which `else` belongs to which conditional. A malformed do conditional must not silently fall back to a pure-term conditional with different control flow.

### For, zipped iteration, while, repeat, and repeat-until

**Feature / profile:** All native iteration families; annotations are separate obligations  
**Rule family:** `PS0V1-LOOP`  
**Source basis:** [L-DO], [L-INIT]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
forLoop ::= "for" forDecl ("," forDecl)* invariant? decreasing? "do" doSeq
whileLoop ::= "while" doCondition invariant? decreasing? "do" doSeq
repeatLoop ::= "repeat" invariant? decreasing? doSeq ("until" term)?
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psFor ::= "for" psForDecl ("," psForDecl)* psInvariant? psDecreasing? "{" psDoItems "}"
psForDecl ::= nativePatternAndEvidence "in" psTermBeforeBlock
psWhile ::= "while" psDoConditionBeforeBlock psInvariant? psDecreasing? "{" psDoItems "}"
// Native do-delimited for/while and repeat forms also admitted.
// Invariants/measures have their native predicate/term shape (§7).
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def total (xs : List Nat) : Id Nat := do
  let mut n := 0
  for x in xs do
    n := n + x
  return n
```

**ProofScript `ps0` v1**

```proofscript
function total(xs: List Nat): Id Nat := do {
  let mut n := 0
  for x in xs {
    n := n + x
  }
  return n
}
```

**Source language distinction and static meaning.**

Admit proposition/Boolean conditionals, named condition proofs, `if let` with `:=` **and monadic `←`**, optional `else` in `do`, `else if`, and `unless`.

Admit single-source `for`, dependent membership/proof binders where provided, and zipped `for x in xs, y in ys` iteration. The zipped form progresses in parallel and stops when an input is exhausted according to the pinned `ForIn`/stream mechanism; it is not nested Cartesian-product iteration.

Admit `while`, `repeat`, and `repeat ... until`, together with `break` and `continue`. Native optional invariant and decreasing clauses remain optional for **ordinary** program admission. Do not impose a blanket mandatory-annotation restriction on every v1 loop. Conversely, omitting the annotation does not discharge termination or correctness obligations for a stronger claim. [L-DO]

Native `for h : x in xs` membership/evidence binders and supported stream/range forms are included. The relevant ForIn/ForIn' or stream instances determine semantics; PS does not create a universal mutable iterator object. `break` exits the appropriate loop and `continue` advances it under native rules. They are invalid outside a suitable control context.

A repeat loop may be nonterminating. A syntactically written decreasing annotation is not itself a proof. For a total verified claim, the actual obligations must be proved. The ordinary grammar does not demand every program carry explicit invariants. The `repeat` keyword in a tactic has a different category and meaning from a do-loop.

### Return, control forwarding, try/catch/finally

**Feature / profile:** Native control targets and typed effects  
**Rule family:** `PS0V1-FORWARD`  
**Source basis:** [L-DO]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
doForward ::= "do←" doSeq | "do<-" doSeq
tryElem ::= "try" doSeq catchClause* ("finally" doSeq)?
catchClause ::= "catch" binder type? "=>" doSeq | "catch" matchAlts
returnElem ::= "return" sameLineTerm?
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psDoForward ::= native forwarding syntax with PS host terms
psTry ::= "try" "{" psDoItems "}" catchClause*
          ("finally" "{" psDoItems "}")?
// Final-argument and surrounding-do restrictions are preserved.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- IO fragment; err has the caught error type.
def runAction (action : IO Unit) : IO Unit := do
  try
    action
  catch err =>
    IO.println (toString err)
  finally
    pure ()
```

**ProofScript `ps0` v1**

```proofscript
function runAction(action: IO Unit): IO Unit := do {
  try { action }
  catch err => { IO.println(toString(err)) }
  finally { pure(()) }
}
```

**Source language distinction and static meaning.**

Admit `return` with native early-exit meaning, including its native term forms and omitted result where permitted. Loop/body `do` delimiters do not necessarily introduce a fresh return target.

Admit **`do←` / `do<-`**, including supported wrapper-lambda forms. It forwards control-flow effects to the surrounding `do` context under the pinned final-argument/statement restrictions. It is not equivalent to an eagerly evaluated nested action `(← action)`, and a generic comma-call lowering must preserve its recognized application shape.

Admit `throw`, `try`, multiple typed/pattern `catch` forms, and `finally` through the relevant effect classes. Preserve exception types, cleanup semantics, and control flow rather than substituting JavaScript or C++ exceptions. Native standalone `for`, `unless`, `try`, and `return` term sugar is also admitted. [L-DO]

For an appropriate imported wrapper `withResource`, a native-shaped statement `withResource resource (fun r => do← body)` maps to a host call such as `withResource(resource, fun r => do← { body })`, subject to the native recognized final-argument shape. This is a **schematic** translation, not a claim that every higher-order function supports forwarding.

`do←` passes a body whose control effects target the surrounding do context; the wrapper decides when to execute it. `(← body)` instead executes a nested action eagerly in the surrounding context. An effectful cleanup `finally` is unrelated to a proof-solving definition-tail `where ... finally`.

Exception facilities require the appropriate `MonadExceptOf`/cleanup/control instances of the concrete monad. Their type is not implicitly a JavaScript `Error`. Native term forms of `for`, `unless`, `try`, and `return` are also available with the ordinary upstream meaning.

## 4. Data declarations, records, classes, and pattern matching

### Inductive types, indexed families, structures, and classes

**Feature / profile:** Native logical data capabilities; braced PS declarations  
**Rule family:** `PS0V1-DATA`  
**Source basis:** [L-CMD], [L-DECL]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
inductiveDecl ::= "inductive" declId telescope type? "where" ctor*
structureDecl ::= ("structure" | "class") declId telescope type?
                  extends? "where" ctorName? structFields deriving?
classInductive ::= "class inductive" declId telescope type? ctor*
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psInductive ::= ("inductive" | "coinductive") declId telescope type?
                "where" "{" ctor* "}" computedFields? deriving? monotonicityBy?
psStructure ::= ("structure" | "class") declId telescope type?
                extends? "where" "{" structCtor? structFields "}" deriving?
// Native declaration forms remain admitted.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
inductive Color where
  | red
  | blue
  deriving Repr, BEq
structure Point where
  x : Nat
  y : Nat
```

**ProofScript `ps0` v1**

```proofscript
inductive Color where {
  | red
  | blue
} deriving Repr, BEq
structure Point where {
  x: Nat
  y: Nat
}
```

**Source language distinction and static meaning.**

Admit inductive types and indexed families, nested/mutual inductives, constructor arguments and result indices, structures, classes, `class inductive`, inheritance and named parents, constructor-name specifications, field defaults, implicit/instance/proof fields, and native field declaration forms.

Admit computed fields and the native coinductive predicate declaration forms, including monotonicity proof clauses where supported. Coinductive/lattice constructions must retain their elaboration into the pinned logical foundations; this edition does not add an unchecked coinductive kernel primitive. Positivity, universe, index, eliminator, and monotonicity conditions remain Lean's. [L-CMD] [L-DECL] [L-PREDEF]

For the braced PS structure/class field surface, fields are nonempty native field declarations separated by a newline, semicolon, or an outer field-separator comma; one trailing comma/semicolon is permitted. A comma **inside a field type/term or binder** belongs to that nested category, not the outer field list. Canonical formatting uses one field per line. Constructors of an inductive remain bar-introduced alternatives rather than record fields.

Structure inheritance preserves generated parent projections and dependent field instantiation. A constructor-name specification remains the native constructor form, not a method named `new`. Record proof fields are ordinary proposition-valued fields with proof irrelevance; no trailing `invariant self => ...` sugar is implied.

Indexed family constructor result types and universes constrain pattern matching. Strict positivity, constructor well-formedness, mutual groups, nested inductives, recursor generation, and elimination out of Prop remain enforced by Lean. Admitting all these declarations does not authorize arbitrary negative recursive types.

**PS0V1-DATA-TAIL.** In a PS braced inductive/coinductive, the braces delimit exactly the constructor list; any native `with` computed-fields tail follows the closing brace, then native `deriving`, then native `monotonicity_by`, in that order and only where the pinned head admits them. `class inductive` has its own native constructor/deriving form and does not acquire a coinductive monotonicity suffix. In a braced structure/class, a native constructor-name specification such as `mk ::` occurs **inside** the braces before the first field; the trailing deriving clause is **outside** the braces. Constructor-name binders and field-method binders use the matrix in §2. No extra kernel data constructor is added by this layout mapping. The native unbraced forms remain legal with their pinned tails. [L-CMD]

```proofscript
structure NamedPoint where {
  mk ::
  x: Nat
  y: Nat
} deriving Repr
```

### Instances, native value bodies, priorities, and deriving

**Feature / profile:** Full registered native machinery; no class allowlist  
**Rule family:** `PS0V1-INSTANCE`  
**Source basis:** [L-CMD], [L-ELAB]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
instanceDecl ::= attributes? ("local" | "scoped")? "instance" priority?
                 declId? telescope ":" term declVal
derivingCmd ::= "deriving" "noncomputable"? "instance"
                classTerms "for" typeTerms
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psInstance ::= same header + nativeDeclVal or "where" "{" fields "}"
// Native instance ... := value is admitted.
// Priorities use the registered native priority grammar.
derivingCmd ::= same native command with PS host terms
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
instance : Inhabited Color := ⟨Color.red⟩
instance : BEq Point where
  beq p q := p.x == q.x && p.y == q.y
-- A standalone deriving command uses an available handler:
deriving instance Repr for Point
```

**ProofScript `ps0` v1**

```proofscript
instance : Inhabited Color := ⟨Color.red⟩
instance : BEq Point where {
  beq p q := p.x == q.x && p.y == q.y
}
deriving instance Repr for Point
```

**Source language distinction and static meaning.**

Admit native trailing deriving where supported, standalone `deriving instance`, `deriving noncomputable instance`, and registered custom deriving handlers. Deriving is not limited to a fixed shortlist of classes. Requested classes still need valid handlers, imports, and instance prerequisites. Generated declarations and executable handler effects remain subject to the appropriate checks; deriving a class is not a blanket semantic-law proof.

Instance declarations require an instance type; optional names and universe suffixes keep native meaning. Anonymous instances do not gain a nullary Unit parameter. Both `:= value` and structure-field bodies are included. Local/scoped instances and priorities affect the actual search environment; source declaration order is not an invented universal priority algorithm.

Instance methods use their native field binder production extended by the `psMixedTelescope` rule in §2. Method declarations do not acquire the nullary `function` exception. A requested deriving handler can fail for unsupported recursive shapes or missing instances. The permitted trailing position depends on the native declaration family; deriving is not appended indiscriminately to every theorem or command. `Repr`, `BEq`, `DecidableEq`, `Inhabited`, and `Hashable` are examples, not the complete language.

### Record construction, update, proof fields, and refined values

**Feature / profile:** Typed native construction, not mutable object spread  
**Rule family:** `PS0V1-RECORD`  
**Source basis:** [L-TERM], [L-CMD], [L-INIT]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
structInst ::= "{" (sources "with")? structInstFields ellipsis? type? "}"
subtype ::= "{" ident ":" type "//" predicate "}"
anonCtor ::= "⟨" term ("," term)* "⟩"
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
structInst ::= same native category with PS host terms
subtype ::= same native category with PS host terms
// Commas in field values stay in their nested expression category.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def origin : Point := { x := 0, y := 0 }
def move (p : Point) : Point := { p with x := p.x + 1 }
def zeroBounded : { n : Nat // n < 1 } := ⟨0, by decide⟩
```

**ProofScript `ps0` v1**

```proofscript
const origin: Point := { x := 0, y := 0 }
function move(p: Point): Point := { p with x := p.x + 1 }
const zeroBounded: { n : Nat // n < 1 } := ⟨0, by { decide }⟩
```

**Source language distinction and static meaning.**

A structure instance fills fields under its inferred/annotated structure type, using native defaults and inherited fields where allowed. Punning `{ x, y }` uses in-scope values with those names. Updating `{ p with x := e }` constructs the native updated value; it is not an assignment to all aliases of `p`. Supported multiple update sources, private field initializers, nested updates, and equation-style field definitions keep their native restrictions.

A subtype packages a value and proof. `Fin n` packages a bounded natural with its specific native API. Structure proof fields express invariants without a separate invariant-declaration language. Projection `.val`, `.property`, or a field accessor only exists when provided by the actual type; PS does not invent universal accessor names.

Dependent updates must satisfy changed-field dependencies. An omitted required field, failed proof field, or ill-typed update is an error even though the braces parse successfully. An `Inhabited` default is used only where the native construction mechanism calls for it, not as a global repair for missing values.

### Pattern grammar, dependent matching, and empty elimination

**Feature / profile:** Native checked elimination with explicit PS pattern adaptation  
**Rule family:** `PS0V1-PATTERN`  
**Source basis:** [L-TERM], [L-DO]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
matchTerm ::= "match" generalizing? motive? discr ("," discr)*
              "with" matchAlt+
matchAlt ::= "|" patterns ("|" patterns)* "=>" term
pattern ::= constructorPattern | literal | wildcard | alias | inaccessible
nomatch ::= "nomatch" term ("," term)*
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psMatch ::= "match" generalizing? motive? discr ("," discr)*
            "with" "{" matchAlt+ "}"
psCtorPattern ::= ctor adjacent "(" (pattern ("," pattern)* ","?)? ")"
// Native pattern syntax remains; the adapter is not term-call elaboration.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def predecessor (n : Nat) : Nat :=
  match n with
  | 0 => 0
  | k + 1 => k

def value (x : Option Nat) : Nat :=
  match x with
  | some n => n
  | none => 0
```

**ProofScript `ps0` v1**

```proofscript
function predecessor(n: Nat): Nat := match n with {
  | 0 => 0
  | k + 1 => k
}
function value(x: Option Nat): Nat := match x with {
  | some(n) => n
  | none => 0
}
```

**Source language distinction and static meaning.**

Admit constructor and qualified/leading-dot patterns, literals where supported, variables, wildcards, aliases `x@p` and native equality-binding variants, inaccessible patterns `.(e)`, multiple discriminants, alternatives sharing a right-hand side, and dependent matches with named equations, motive, and generalization controls.

Retain Lean `Nat` successor-pattern sugar such as `n + 1` and `n + 2`; this does not admit arbitrary arithmetic expressions as invertible patterns. Constructor comma-call sugar in PS0 is only a surface transformation of the corresponding constructor application, not a different matching algorithm.  [L-TERM]

Admit pattern `let`, `if let`, `matches`, `nomatch`, `nofun`, pattern lambdas, equation-style functions, and the corresponding native `do` forms. Preserve exhaustiveness, inaccessible-index checks, elimination restrictions, and binder scopes. `nomatch` must be justified by impossible constructors/indices, not by an unchecked “unreachable” assertion.

`match_expr` and `let_expr` inspect metaprogramming expressions with the native special matching protocol. Syntax-quotation patterns match syntax, not runtime algebraic values. They must not be reduced to the ordinary constructor-pattern grammar or assumed to compare every raw token: the pinned quotation matcher has particular treatment of syntax atoms and identifiers. [L-TERM]

**PS0V1-PATTERN-ADAPTER.** `Ctor(p₁, p₂)` is a positional constructor-pattern adapter that lowers to the corresponding native constructor application pattern, preserving each subpattern and its binders. The head must resolve as an admissible native pattern constructor/matching form, not an arbitrary function or a CoeFun value. The adapter accepts positional subpatterns, not named entries, and performs no PS empty-call completion. For a **nonempty** adapter, lower the written subpatterns to the native constructor application and let Lean handle its native implicit parameters, optional/automatic fields and applicable matching definitions. Thus `K(n)` and native `K n` have the same native pattern-default behavior; the adapter does not invent or suppress native defaults. Native named-pattern and ellipsis forms remain available in native pattern syntax. [L-APP] For the **empty** adapter `Ctor()`, require zero explicit constructor fields in the instantiated native constructor telescope, counting even defaulted and automatic fields; then lower to the bare constructor. A constructor with a Unit field or only defaulted explicit fields does not qualify. No Unit is inserted. Bare `none`/`nil` remains canonical.

The opening parenthesis of this adapter must be adjacent to its constructor head: whitespace or comments select native pattern syntax instead, not a PS call-adjacency error. One trailing comma is permitted after a nonempty subpattern list; `Ctor(,)` is invalid. Native pattern syntax and the PS adapter preserve the same relative nesting rule as their respective categories. `Ctor((p,q))` supplies one tuple subpattern; `Ctor(p,q)` supplies two positional subpatterns. A comma at the match-alternative level separates discriminants, not constructor arguments. Pattern-category parentheses retain native matching grammar; the **host term** gap ban is not applied to constructor pattern syntax. Expressions inside inaccessible patterns or explicit motives are host terms and follow their own term rules.

The native `match h : e with ...` equation is available in branches as specified by Lean. `(motive := ...)` and `(generalizing := true)` are configuration productions, not PS function calls. A motive changes dependent result typing, not runtime branch selection. `nomatch`/`nofun` require actually impossible constructor/index cases. `unreachable!` is a runtime facility with a default-value interpretation and is not equivalent to empty logical elimination.

## 5. Recursion, termination, partiality, and fixed points

### Structural and well-founded recursive definitions

**Feature / profile:** Native checked recursion, mutual groups, and local recursion  
**Rule family:** `PS0V1-REC`  
**Source basis:** [L-PREDEF], [L-DECL], [L-TERM]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
recursiveDecl ::= defDecl terminationSuffix? whereDecls?
terminationSuffix ::= "termination_by" "structural"? binders? term
                    | "termination_by?"
decreasingProof ::= "decreasing_by" tacticSeq
mutual ::= "mutual" command+ "end"
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psRecursiveDecl ::= defOrFunction terminationSuffix? psWhere?
psMutual ::= "mutual" "{" command+ "}" | nativeMutual
// Each lowered declaration keeps its original telescope and hints.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def lengthN : List Nat → Nat
  | [] => 0
  | _ :: xs => lengthN xs + 1
termination_by structural xs => xs
```

**ProofScript `ps0` v1**

```proofscript
def lengthN: List Nat → Nat
  | [] => 0
  | _ :: xs => lengthN(xs) + 1
termination_by structural xs => xs
```

**Source language distinction and static meaning.**

Admit structural and well-founded recursion, inferred termination, explicit `termination_by`, `termination_by structural`, `termination_by?`, and `decreasing_by`; include mutual and local recursive definitions. Preserve strongly connected recursive groups, fixed parameters, generated equations/induction principles, and termination-hint compatibility.

A total declaration must satisfy Lean's requirements. The kernel does not gain a new arbitrary recursive-definition constructor just because a frontend accepts recursive surface syntax. The pinned elaborator constructs admissible definitions through the appropriate recursors/fixed-point facilities. [L-DECL] [L-PREDEF]

A recursive call must satisfy the selected structural or well-founded construction; type-correct self-application is not sufficient. Structural recursion can recognize native definitional-equality forms of a strict subterm according to the pinned algorithm. Well-founded recursion uses an actual relation/measure and proofs, not only syntactic decrement.

`termination_by structural` chooses a structural parameter and is incompatible with an unnecessary `decreasing_by` proof under the native rules. Ordinary `termination_by` and `decreasing_by` select the applicable well-founded mechanism. A mutually recursive group must use compatible hints; one declaration cannot silently opt into a different recursion mode while remaining in the same recursive clique. Generated equation and functional-induction theorems follow Lean's actual construction.

The braced `mutual { ... }` form only replaces the outer group delimiters; it does not authorize declarations disallowed in the corresponding native group. Local `let rec` and `where` helpers participate in the proper capture and recursion analysis.

### Partial recursive functions

**Feature / profile:** Native opaque logical interface and recursive executable implementation  
**Rule family:** `PS0V1-PARTIAL`  
**Source basis:** [L-PREDEF], [L-DECL]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
partialDecl ::= legalModifiers "partial" "def" declId telescope type? declVal
// Function shape, inhabitance, and mutual-group conditions are checked.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
partialDecl ::= same native def form
              | legalModifiers "partial" "function" declId
                psFunctionBinders type? psDeclVal
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
partial def spin (n : Nat) : Nat := spin n
-- No totality claim is made.
```

**ProofScript `ps0` v1**

```proofscript
partial function spin(n: Nat): Nat := spin(n)
-- No totality claim is made.
```

**Source language distinction and static meaning.**

**PS0V1-PARTIAL-01.** Admit `partial` functions and native compatible mutual groups. Lean supplies an opaque logical interface using an inhabitant and separately compiles the recursive program. Do not expose the implementation's arbitrary recursive equations as definitional equality, or infer a termination proof from successful compilation. The result-type and function-shape requirements remain those of Lean. [L-PREDEF]

An ordinary PS0 native program may contain partial computation. A claim of total executable correctness must separately establish the required termination and implementation correspondence; source typing alone cannot do so.

The opaque logical interface prevents arbitrary recursive unfolding in kernel proofs. The native recursive implementation can still execute indefinitely. A result being inhabited is a consistency prerequisite for the interface, not a behavioral specification of the loop. `partial` is not a synonym for `unsafe`; both retain distinct native declaration classifications. Trying to add a total-function termination suffix to an incompatible partial declaration must follow the native rejection, not be silently ignored.

### Partial, inductive, and coinductive fixed points

**Feature / profile:** Native ordered fixed-point constructions  
**Rule family:** `PS0V1-FIXPOINT`  
**Source basis:** [L-TERM], [L-PREDEF], [L-CMD]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
fixpointSuffix ::= "partial_fixpoint" monotonicityProof?
                 | "inductive_fixpoint" monotonicityProof?
                 | "coinductive_fixpoint" monotonicityProof?
monotonicityProof ::= "monotonicity" term
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
fixpointSuffix ::= same native suffix with host PS terms
// Braced by proofs are allowed as the proof term.
// Coinductive predicate declarations keep native constructor/monotonicity rules.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def loopOption (n : Nat) : Option Nat := loopOption n
partial_fixpoint
-- This is a fixed-point design example, not a termination proof.
```

**ProofScript `ps0` v1**

```proofscript
function loopOption(n: Nat): Option Nat := loopOption(n)
partial_fixpoint
-- This is a fixed-point design example, not a termination proof.
```

**Source language distinction and static meaning.**

Admit `partial_fixpoint` and its explicit monotonicity proof form. It uses the pinned ordered/fixed-point infrastructure, including the applicable completeness and monotonicity requirements, and supplies checked equation theorems. These equations do not say every execution terminates. It is not synonymous with `partial`, and neither keyword grants a proof hole. [L-TERM] [L-PREDEF]

Admit `inductive_fixpoint`, `coinductive_fixpoint`, coinductive predicate declarations, and applicable `monotonicity_by` forms. Preserve least versus greatest fixed-point meaning and native monotonicity checking. These forms are not a license for arbitrary cyclic values or an unproved productivity rule.

Do not combine incompatible termination and fixed-point suffixes. Native parser acceptance of a suffix is not sufficient when elaboration rejects its combination with the declaration or mutual group.

The relevant ordered return type/monad must supply the required structure. Tail-recursive inhabited cases and supported monotone monadic compositions are important special cases, not a permission to define every arbitrary recursive body. The monotonicity proof can be inferred or supplied through the native suffix. Coinductive predicate syntax includes the native `monotonicity_by` form where supported. These elaborator constructions do not add unrestricted cyclic proof terms to the kernel.

## 6. Proof terms, tactics, automation, and logical notation

### Theorems, by proofs, bullets, cases, and tactic composition

**Feature / profile:** Full registered proof-language capabilities  
**Rule family:** `PS0V1-PROOF`  
**Source basis:** [L-TERM], [L-TACTIC], [L-INIT]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
proof ::= term | "by" tacticSeq
tacticSeq ::= tactic (nativeSeparator tactic)*
tactic ::= "exact" term | "apply" term | "intro" binders
         | cases | induction | case | next | goalBullet | registeredTactic
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
proof ::= psTerm | "by" "{" psTacticItems "}" | nativeBy
// Ordinary tactic term arguments use psTerm.
// Goal bullets and tactical separators retain native categories.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
theorem andSwap (p q : Prop) : p ∧ q → q ∧ p := by
  intro h
  exact ⟨h.2, h.1⟩
```

**ProofScript `ps0` v1**

```proofscript
theorem andSwap(p: Prop, q: Prop): p ∧ q → q ∧ p := by {
  intro h
  exact ⟨h.2, h.1⟩
}
```

**Source language distinction and static meaning.**

A theorem states exactly the proposition in its elaborated type, including all generalized parameters and assumptions. A tactic program attempts to construct an inhabitant of that type. It does not change the logical meaning of implication, conjunction, quantification, equality, or proof irrelevance.

Term proofs, `show`, `have`, `suffices`, `calc`, equality transport `▸`, and anonymous constructors remain available. `case`, `next`, native `·`/ASCII goal bullets, focusing, alternatives, sequencing, tactic `match`, locations, and configuration syntax preserve native goal handling. A plain `;` sequences tactics in the resulting proof state; it does not itself distribute the second tactic over every generated goal. The distinct `<;>` combinator performs that distribution. Tactic and do sequencing operate on different kinds of state. [L-TERM-BASIC] [L-INIT-TACTICS]

Ordinary `.ps` term arguments of tactics obey the same application rule as code. The tactic keyword itself is not a callable term: `exact (h)` is a grouped fresh term, while `exact h (p)` contains a rejected spaced application. Native tactic configuration items and quoted tactic syntax have their own categories.

### Simplification, rewriting, arithmetic, decision procedures, and custom tactics

**Feature / profile:** Import-driven proof tools; not a finite tactic allowlist  
**Rule family:** `PS0V1-AUTO`  
**Source basis:** [L-INIT], [L-STD], [L-ELAB], [L-DECIDE], [L-NATIVE]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
tactic ::= "simp" config? simpArgs? location?
         | "rw" rewriteRules location? | "conv" convSeq
         | "decide" config? | "omega" config? | registeredTactic
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
tactic ::= same native tactic productions
// Registered arguments keep their category; host proof terms use PS calls.
// A successful tactic is not a substitute for final proof/assumption checking.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
theorem addZero (n : Nat) : n + 0 = n := by
  simp
example : 2 + 3 = 5 := by decide
```

**ProofScript `ps0` v1**

```proofscript
theorem addZero(n: Nat): n + 0 = n := by { simp }
example : 2 + 3 = 5 := by { decide }
```

**Source language distinction and static meaning.**

The imported environment may supply `simp`, `dsimp`, `simpa`, `rw`, `conv`, congruence, cases/induction, contradiction, `omega`, `grind`, `decide`, bitvector automation such as `bv_decide`, and verification tactics such as `vcgen`/`mvcgen`. Their presence in this catalog does not make them available from every minimal import. Local/scoped registrations, `[simp]` lemmas, simprocs, priorities, and tactic extensions affect actual behavior. A custom tactic is permitted through the extension machinery rather than special admission of its spelling.

Ordinary proof-producing tactics still submit their resulting evidence for checking. Native-assisted decision mechanisms require extra care: the pinned `nativeEqTrue` infrastructure compiles/evaluates a closed Boolean and introduces an axiom for a successful result. `native_decide` and `decide +native` use that path. A bitvector tactic's assurance must be assessed from the actual selected proof-construction path, not its short name. Any generated native-computation assumptions remain in the dependency accounting. Historical kernel trust primitives from older releases are not substituted for this pinned behavior.

Resource limits, tactic search heuristics, and a timeout can affect whether a proof is found; they do not change the proposition's meaning. Failed automation is not permission to emit a proof hole as a theorem.

### Metavariables, placeholders, sorry, and incomplete development

**Feature / profile:** Development syntax versus completed evidence  
**Rule family:** `PS0V1-HOLES`  
**Source basis:** [L-TERM], [L-PREDEF], [L-DECL]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
term ::= "_" | "?" ident | "sorry" | ordinaryTerm
// The elaborator may solve placeholders or retain diagnostics.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psTerm ::= same development forms
// Completed logical claims and qualifying output reject unresolved holes.
// Generated/recovery/transitive sorry dependencies count too.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- Incomplete development example, intentionally not proved:
theorem unfinished : True := by
  sorry
```

**ProofScript `ps0` v1**

```proofscript
-- Incomplete development example, intentionally not proved:
theorem unfinished: True := by {
  sorry
}
```

**Source language distinction and static meaning.**

A placeholder can be acceptable when elaboration solves it and the resulting term checks. Mathematical uniqueness of the solution is not an additional requirement. An unresolved metavariable is not an arbitrary existential assumption for a completed theorem. `sorry` explicitly creates incomplete evidence; automatically inserted recovery sorries have the same claim-level consequence even when the source did not spell the keyword.

The editor may retain incomplete syntax trees, goals, and diagnostic declarations. That is not a successful hole-free build. A completed claim must inspect relevant generated and imported dependencies, including `sorryAx`, rather than searching only handwritten tokens. An incomplete theorem cannot be legitimized by passing through an unrestricted `.lean` module.

`#eval!` is an explicit native development override of the ordinary sorry-dependent evaluation check; it does not remove the hole from the logical dependency graph. The exact publication and verification requirements are in §12.

## 7. Contracts, verification conditions, and erased state

### Given, requires, ensures, and generated specification proofs

**Feature / profile:** Native intrinsic contract mechanism with PS definition aliases  
**Rule family:** `PS0V1-CONTRACT`  
**Source basis:** [L-CMD], [L-TERM], [L-STD]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
contractSeq ::= givenClause? requiresClause? ensuresClause?
givenClause ::= "given" binder+
requiresClause ::= "requires" (term | basicFun)
ensuresClause ::= "ensures" basicFun
// Clauses precede a definition value; basicFun binds its arguments.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
psContractSeq ::= psGiven? psRequires? psEnsures?
psGiven ::= "given" nativeLogicalBinder+
psRequires ::= "requires" (psTerm | psBasicFun)
psEnsures ::= "ensures" psBasicFun
// def/function only; fixed order and no repetition.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- Requires the pinned Std.WP environment; proof obligations omitted here.
def increment (n : Nat) : Id Nat
    requires n < 100
    ensures r => r = n + 1 := do
  return n + 1
```

**ProofScript `ps0` v1**

```proofscript
-- Requires the pinned Std.WP environment; proof obligations omitted here.
function increment(n: Nat): Id Nat
  requires n < 100
  ensures r => r = n + 1 := do {
  return n + 1
}
```

**Source language distinction and static meaning.**

Retain `given? requires? ensures?` in that exact order, at most once each, on the eligible `def`/`function` declarations. `given` introduces specification-only binders; `requires` accepts its pinned term/predicate form; `ensures` requires its result-binding form. These are not ignored comments or runtime parameter additions.  [L-CMD]

Their elaboration requires the pinned verification environment, including `Std.WP.Triple` for intrinsic contracts and the relevant assertion gadgets/registrations. Importing a type named `Triple` from an unrelated library is not equivalent. Generated specifications such as `f.spec` must have the appropriate names, universes, visibility, and checked proofs.

Admit the **full native `where ... finally` mechanism**, including the `spec` subsection and other native subsections for supported holes and obligations. Admit the braced `where { ... finally { | spec => { ... } } }` surface. Do not invent an additional `verify target :=` command as a supposed Lean feature. [L-TERM]

**PS0V1-CONTRACT-BIND.** A logical binder is an identifier or native bracketed binder: `given (target: Nat)` is typed binder syntax; `given target: Nat` is not an alternative typed-binder spelling. Logical given variables scope over the specification, not the runtime body as additional executable parameters. `requires s => P s` binds the assertion's state arguments where the effect model demands them. `ensures r => Q r` binds the result and any applicable assertion arguments using native basic-function syntax; a bare `ensures Q` is not silently supplied a result binder.

Contract clauses attach to eligible `def`/`function` forms, including source-nullary `function` declarations whose runtime Unit parameter has the defined lowering. They do not become arbitrary attributes on `const`, a theorem, a constructor, or an instance. Repeated or reordered clauses are parse errors. Missing verification environment is an environment failure, not a reason to treat the contract as a comment.

**Proof tail shape.** A braced example tail is `where { finally { | spec => { tacticSeq } } }`; `tacticSeq` here is schematic and must be replaced by a genuine proof. Its native counterpart is `where ... finally | spec => ...`. No unproved `f.spec` name is sufficient evidence. The spec theorem's scope, universes, assumptions, and public visibility are checked alongside the original definition.

**PS0V1-CONTRACT-CHECK.** At this pin the contract macro generates the ordinary definition and an `@[spec]` theorem proved through `vcgen`; the optional `spec` tail works on remaining verification conditions. A contract-free definition is not silently converted into a required behavioral specification, but a written intrinsic contract cannot be retained merely as unchecked metadata in an ordinary **completed checked** module. Its generated proof must close, or the module remains failed/development state. A standalone `assert` gadget without an enclosing verified specification is still an annotation, not an independently established fact. The checking and qualification scopes remain distinct. [L-CONTRACT]

**Default clauses and proof-tail uniqueness.** Omitted `requires` has the pinned top precondition and omitted `ensures` the pinned top postcondition; this does not mean missing *written* obligations are ignored. A contract may have at most one `spec` subsection; duplicate subsections fail during macro expansion/elaboration as the pinned `extractSpecSection` requires. Other native named-hole sections retain their own native rules. A generated name collision such as a preexisting `f.spec` is not resolved by silently overwriting that declaration. [L-CONTRACT]

### Assertions, loop invariants, and decreasing measures

**Feature / profile:** Verification annotations distinct from runtime assertions  
**Rule family:** `PS0V1-VC`  
**Source basis:** [L-DO], [L-STD]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
assertion ::= "assert" (term | basicFun)
forInvariant ::= "invariant" prefixBinder suffixBinder stateBinders? "=>" term
loopInvariant ::= "invariant" exitBinder stateBinders? "=>" term
decreasing ::= "decreasing" (term | basicFun)
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
annotation ::= same native predicate/measure forms
// for/while body delimiters may use PS braces.
// Written annotations must be elaborated and proved for verified claims.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- Schematic: P and the proof-capable effect environment must be supplied.
-- do
--   assert P
--   return result
```

**ProofScript `ps0` v1**

```proofscript
-- Schematic: P and the proof-capable effect environment must be supplied.
-- do {
--   assert P
--   return result
-- }
```

**Source language distinction and static meaning.**

Keep these operations distinct:

| Form | Meaning |
|---|---|
| `assert P` / predicate-binder form | Verification annotation/gadget read by the verification mechanism; no corresponding runtime test is implied |
| `assert! condition` | Native runtime assertion behavior, including panic behavior on failure |
| `debug_assert! condition` | Native runtime assertion conditional on the debug-assertion configuration |

Merely writing `assert P` does not mean `P` has already been proved. Required verification conditions must be generated and closed for the claimed program/specification.

For-loop invariants use the native consumed-prefix/remaining-suffix binder convention; while/repeat invariants use the native exit-state convention. Additional binders represent the assertion's state arguments where applicable. `decreasing` uses the actual loop-state measure semantics, not a text-level requirement that a variable's spelling become smaller. [L-DO]

For-loop annotations bind the consumed prefix and remaining suffix; repeat/while annotations bind the native exit flag, with further binders representing state arguments as appropriate. Mutation variables are referenced according to the native annotation scope. A programmer must not replace this with an invented invariant expression that has no required binders.

A `decreasing` clause represents a measure over the relevant loop state. It must be justified by the verification construction for a total claim. The existence of a `ForIn` instance alone does not prove iterator laws or termination of all supplied user actions. `break`, `continue`, early return, and exceptional paths are part of the proof obligations, not excluded cases.

`assert!` and `debug_assert!` retain runtime panic/debug-option behavior; they are not proofs of proposition-valued invariants. Conversely, proof-only `assert` does not insert a runtime validation merely because a user writes it.

### Erased definitions, erased mutation, and erased-result actions

**Feature / profile:** Native verification-only state with preserved effects  
**Rule family:** `PS0V1-ERASED`  
**Source basis:** [L-DO], [L-STD]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
erasedDecl ::= "erased" "mut"? ident type? ":=" term
erasedBind ::= "erased" "mut"? ident type? "←" action
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
erasedDecl ::= same native form with PS host terms
erasedBind ::= same native form with PS host terms
// Erase the permitted verification-only result, not an effectful action.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- Schematic verified-do fragment:
-- erased before := xs.length
-- erased observed ← observe
-- return ()
```

**ProofScript `ps0` v1**

```proofscript
-- Schematic verified-do fragment:
-- erased before := xs.length
-- erased observed ← observe
-- return ()
```

**Source language distinction and static meaning.**

Admit `erased`, `erased mut`, pure erased definitions, erased monadic bindings, and supported updates. Erased information must not improperly determine runtime-relevant results.

**Crucially, `erased x ← action` still runs `action`; it hides its result in verification-only state.** It is incorrect to erase the entire effectful computation merely because the binder is erased. Erasure correctness and effect preservation remain separate obligations. [L-DO]

Verification applies to a stated specification and effect model. It must account for coverage, exceptional exits, iterator laws, mutable state, logical assumptions, erased data, and any foreign/runtime dependencies relevant to that statement. Syntax acceptance, a generated theorem name, or the presence of loop annotations is insufficient.

`reads`, `modifies`, and `errors` are not part of the intrinsic contract grammar specified here. An imported extension can define additional specification languages under §9, but their meaning and evidence are then owned by that extension.

Erased logical state may help express a pre-state, history, or loop invariant, but ordinary runtime outputs cannot illicitly depend on an erased value. Native typing/erasure checks and the claimed effect semantics both matter. A result-erased action can still read/write state, fail, or diverge according to its action type; deleting it changes behavior. No alternative `ghost` keyword or separate phantom runtime is introduced.

## 7A. Diagnostics, interactive development, and evaluation

### Check, print, reduce, evaluation, and diagnostic extensions

**Feature / profile:** Native diagnostic commands; no proof authority implied  
**Rule family:** `PS0V1-DIAG`  
**Source basis:** [L-CMD], [L-TERM], [L-ELAB]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
command ::= "#check" term | "#synth" term | "#eval" term
          | "#eval!" term | "#reduce" term
          | "#print" printQuery | registeredDiagnostic
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
command ::= same commands with host PS terms
// Pure-only restrictions are not imposed on ordinary native diagnostic use.
// Proof and qualifying-output checks are independent.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
#check (fun n : Nat => n + 1)
#eval (2 + 3 : Nat)
#eval IO.println "hello"
```

**ProofScript `ps0` v1**

```proofscript
#check (fun n : Nat => n + 1)
#eval (2 + 3 : Nat)
#eval IO.println("hello")
```

**Source language distinction and static meaning.**

Admit all valid registered diagnostic commands, including the pinned families below:

| Family | Examples |
|---|---|
| Typing and synthesis | `#check`, `#check_failure`, `#synth` |
| Evaluation and reduction | `#eval`, `#eval!`, `#reduce`, registered evaluation forms |
| Declaration inspection | `#print`, `#print sig`, `#print axioms`, `#print equations` / `eqns` |
| Scope and version | `#where`, `#version`, `#exit` |
| Imports and dependency assertions | `#import_path`, `assert_not_exists`, `assert_not_imported`, `#check_assertions` and its diagnostic variant |
| Restatement | `recall`, `recall?` |
| Diagnostics testing | Registered guard/message/testing commands and tactics |
| Internal inspection | `#with_exporting`, `#dump_async_env_state` |
| Deprecation | `deprecated_syntax`, `deprecated_module`, `#show_deprecated_modules` |

`#eval` may execute IO and supported elaboration monads; v1 does not impose a pure-total-only diagnostic restriction. Native `#eval` ordinarily refuses sorry-dependent execution; `#eval!` has a different explicit development meaning. Neither form is a proof certificate, and permitting the development grammar does not qualify hole-dependent program output. [L-CMD]

`#check` reports an elaborated type; `#reduce` uses reduction rather than arbitrary compiled execution; `#eval` compiles/evaluates using the applicable native instances and monad adaptation. Their outputs answer different questions. `#print axioms` is useful dependency information, not a proof of native runtime correspondence. `#check_failure` and guard-message commands are testing tools, not a way to insert an invalid expression into a theorem.

Native exit/version/scope/recall/import-assertion facilities retain their context restrictions. A diagnostic command may execute code or affect the module-processing state. A valid test that expects a failure must establish the intended error phase, not simply receive any failure.

## 7B. Runtime effects, foreign interfaces, and unsafe programming

### IO, references, tasks, and system effects

**Feature / profile:** Native runtime and imported library capabilities  
**Rule family:** `PS0V1-RUNTIME`  
**Source basis:** [L-INIT], [L-STD], [L-LEAN], [L-RUNTIME]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
type ::= IO α | EIO ε α | BaseIO α | ST σ α | Task α | importedType
term ::= nativeCallsAndEffects
// These are types/libraries, not a new imperative kernel calculus.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
type ::= same native types with PS type-call syntax where used
term ::= PS calls + native do/control/effect forms
// Available APIs depend on imports and runtime support.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def hello : IO Unit := do
  IO.println "hello"
```

**ProofScript `ps0` v1**

```proofscript
def hello: IO Unit := do {
  IO.println("hello")
}
```

**Source language distinction and static meaning.**

Admit local mutation and the actual reference-based facilities used by Lean, including `ST.Ref`, IO references, `StateRefT`, tasks, and imported synchronization/process/filesystem/network interfaces. This explicitly goes beyond a pure/local-state-only boundary for ordinary programs.

Proofs about a pure model do not automatically establish behavior of mutable references, scheduling, external processes, filesystems, networking, or native primitives. Availability on a host, resource use, and successful linking are separate from source-language acceptance. The reference does not promise all platform libraries on every operating system or backend. [L-RUNTIME] [L-STD]

The sample is a parameterless IO action value, not a source-nullary `function`. Calling syntax `hello()` must not be invented unless its actual type is callable. Running an IO action from a do block uses it as an action (`hello`), while a function returning IO may be called to construct an action. This distinction prevents JavaScript-style “every action is a zero-argument function” assumptions.

Tasks and shared references have native scheduling/ownership/effect behavior. The language does not promise deterministic interleavings, external filesystem state, or network availability. A library's imported specification can describe those effects without proving the host environment satisfies every precondition.

### Extern, foreign export, implemented_by, and borrowed parameters

**Feature / profile:** Logical definitions and executable replacements are separate  
**Rule family:** `PS0V1-FFI`  
**Source basis:** [L-TERM], [L-DECL], [L-VALIDATE]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
attribute ::= externAttribute | exportAttribute | implementedByAttribute
borrowedType ::= "@&" term
// Actual symbol/ABI forms are those of the pinned attribute handlers.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
attribute ::= same native registered forms
borrowedType ::= same annotation with a PS host type
// No Rust-style borrow checker is added to logical types.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- Illustrative native ABI shape; not a supplied foreign implementation.
@[extern "host_count"]
opaque hostCount (s : @& String) : IO Nat
```

**ProofScript `ps0` v1**

```proofscript
-- Illustrative native ABI shape; not a supplied foreign implementation.
@[extern "host_count"]
opaque hostCount(s: @& String): IO Nat
```

**Source language distinction and static meaning.**

Admit `@[extern ...]`, `@[export ...]`, `@[implemented_by ...]`, native ownership/borrowing annotations such as `@&`, and the associated runtime interfaces. Namespace `export` and foreign-symbol `@[export]` are different constructs.

The `@&` annotation affects the ABI/reference-ownership convention of the relevant compiled foreign calls; it does **not** add a Rust-style borrow checker to Lean's logical type system. External code must obey the runtime ABI, object representation, ownership, initialization, and exception conventions. [L-TERM] [L-DECL]

A safe logical definition may have a different compiled implementation supplied by `extern` or `implemented_by`. Its Lean theorem concerns the logical declaration unless additional correspondence evidence justifies the native implementation. Do not silently turn a foreign function's type or contract into proof that the external implementation satisfies it. [L-VALIDATE]

A valid declaration does not supply the foreign symbol or demonstrate its ABI correctness. Linking and execution may require a library and initialization routine. A definition supplied as the logical body or through an inhabitant is not necessarily the compiled foreign implementation. Reference-count borrowing governs who consumes/decrements the value at that ABI boundary; it has no general effect on functions without the applicable foreign convention.

Compiler optimization attributes also belong to their registered semantics. A formally stated source theorem remains about the source logical function unless evidence connects every substituted implementation on the relevant execution path.

### Unsafe declarations and expressions, panic, tracing, and debugging

**Feature / profile:** Native non-logical runtime facilities and interface separation  
**Rule family:** `PS0V1-UNSAFE`  
**Source basis:** [L-TERM], [L-PREDEF], [L-DO]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
unsafeDecl ::= legalModifiers "unsafe" declaration
unsafeTerm ::= "unsafe" term
term ::= "panic!" term | "unreachable!" | "dbg_trace" term separator term
       | "idbg" term separator term
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
unsafeDecl ::= same native declaration families
unsafeTerm ::= "unsafe" psTerm
// PS aliases lower to legal native definitions.
// Runtime diagnostics remain distinct from proof annotations.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
unsafe def rawId (n : Nat) : Nat := n
-- A panic needs an appropriate result type/default context.
def fallback : Nat := panic! "not available"
```

**ProofScript `ps0` v1**

```proofscript
unsafe def rawId(n: Nat): Nat := n
-- A panic needs an appropriate result type/default context.
def fallback: Nat := panic! "not available"
```

**Source language distinction and static meaning.**

Admit unsafe declarations and native unsafe expressions. An unsafe expression can generate an auxiliary implementation behind a safe interface when Lean's inhabitance conditions hold; therefore checking only public signatures for the word `unsafe` is insufficient to audit runtime correspondence.

Admit `panic!`, `unreachable!`, tracing, and debugging with native behavior. `panic!` has a logical default-value interpretation and runtime behavior controlled by the runtime's panic settings; it must not be summarized as universally throwing an exception or universally terminating the process. [L-TERM]

A simple-looking unsafe body remains classified unsafe. A safe logical declaration cannot freely depend on an unsafe declaration in a proof-relevant way. An unsafe expression can construct an auxiliary unsafe implementation behind a safe inhabited interface, so auditing only exported type signatures does not reveal every runtime replacement. Type safety, memory safety, and logical consistency are not identical claims.

Debug traces and `idbg` can have IO/editor execution requirements and experimental limitations. Their syntax is available where registered, but they need not succeed in a headless or unsupported runtime. Runtime diagnostics are neither required proof steps nor an assurance certificate.

## 8. Type foundation and concrete type catalog

### Universes, dependent functions, equality, quotients, and core data

**Feature / profile:** One Lean type theory with imported named types  
**Rule family:** `PS0V1-TYPES`  
**Source basis:** [L-TERM], [L-DECL], [L-INIT]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
type ::= "Prop" | "Type" universe? | "Sort" universe?
       | binder "→" type | term
universe ::= parameter | nativeLevelExpression
// Type names are ordinary declarations, not a universal reserved keyword list.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
type ::= same foundation using PS host applications
// Examples: Fin(n), Vector(α,n), or native unparenthesized applications.
// No additional kernel type constructors are introduced.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
universe u v
structure Pair (α : Type u) (β : Type v) where
  first : α
  second : β
#check Pair.{u, v}
```

**ProofScript `ps0` v1**

```proofscript
universe u v
structure Pair (α: Type u) (β: Type v) where {
  first: α
  second: β
}
#check Pair.{u, v}
```

**Source language distinction and static meaning.**

Admit `Sort u`, `Prop`, `Type u`, universe variables and explicit universe application, dependent function types, polymorphism, inductive families, dependent records, equality and heterogeneous equality, propositions, and quotient facilities with their pinned semantics. `Prop = Sort 0` and `Type u = Sort (u + 1)` retain their Lean meaning. Proof irrelevance and restrictions on eliminating propositions are not relaxed.

Products, sums, dependent pairs, `Subtype`, `Fin`, `Option`, `Except`, and collection types are Lean declarations and notation, not additional kernel constructs. Refinement-style programming uses propositions, subtypes, indexed types, and proof fields. This edition adds no separate `refine type`, `ghost`, or automatic structure-invariant language. [L-TERM] [L-DECL]

Use pinned Lean expected-type propagation, universe inference, implicit insertion, typeclass search, coercions, overloaded notation, default arguments, metavariable assignment, and postponed elaboration. Admit `@`, named arguments, placeholders, `..` where defined, type ascription including `(e :)`, `inferInstance`, and `inferInstanceAs` with its actual wrapping/transparency behavior.

`autoImplicit`, transparency, instance priorities, and other elaboration options retain registered semantics. Do not promise a new globally deterministic overload-selection algorithm inconsistent with Lean. Record the effective environment when reproducibility matters. Unresolved metavariables, error-recovery terms, and successful parsing alone do not qualify a declaration as checked and complete. [L-TERM] [L-PREDEF]

A higher universe is not an automatic coercion between all values. `Type`, `Sort`, and universe-polymorphic declarations follow native universe constraints. `Prop` is impredicative with proof irrelevance and native elimination restrictions. `Eq`/`HEq`, recursors, and quotients do not acquire unchecked casts or equality reflection. Definitional equality is not every theorem-proved equality. Propositional rewriting uses checked equality evidence.

### Explicit type inventory and semantic distinctions

The table gives the named foundation and principal native library families a PS0 programmer must distinguish. Availability is import-dependent; the full registered environment is not limited to this list. Qualified spellings and actual signatures are supplied by their defining modules, not guessed from a family label. [L-INIT] [L-STD] [L-LEAN]

| Family | Types / facilities | Required interpretation |
|---|---|---|
| Universes | `Prop`, `Type u`, `Sort u` | Native universe hierarchy; propositions are not runtime Booleans |
| Truth and evidence | `True`, `False`, `And`, `Or`, `Not`, `Iff`, `Exists`, `Nonempty` | Proof constructions; elimination restrictions and proof erasure matter |
| Equality | `Eq`, `HEq`, native equality recursors | Definitional equality and proved equality remain different |
| Natural/integer | `Nat`, `Int` | Native arbitrary-precision mathematical semantics, including native truncation/division conventions |
| Fixed-width unsigned | `UInt8`, `UInt16`, `UInt32`, `UInt64`, `USize` | Finite-width/machine-width operations and conversions; not arbitrary Nat arithmetic |
| Fixed-width signed | `Int8`, `Int16`, `Int32`, `Int64`, `ISize` | Pinned signed operation semantics; machine sizes may be target-dependent |
| Floating point | `Float`, `Float32` | Native floating behavior, NaNs, signed zero, rounding and runtime boundaries; not exact real arithmetic |
| Boolean | `Bool`, `Decidable p` | A Boolean value is not a proposition/proof; decidability provides its logical bridge |
| Unit/empty | `Unit`, `PUnit`, `Empty`, `PEmpty` | Inhabitance and universe distinctions; only definitionally `Unit` triggers the PS empty-call insertion |
| Products and sums | `Prod`, `PProd`, `Sum`, `PSum` | Typed constructors and dependent context; tuple notation is not an untyped array |
| Dependent packages | `Sigma`, `PSigma`, `Subtype`, `Fin n` | Data/proof dependencies; construction and projection obey the actual types |
| Optional/error | `Option`, `Except` | Explicit typed alternatives; no implicit JS null/undefined or generic exception coercion |
| Linear collections | `List`, `Array`, `Vector`, `ByteArray` | Native persistent/logical values with specific optimized implementations and bounds rules |
| Text | `Char`, `String`, native positions/slices/iterators | Unicode/encoding and indexed-position validity follow the pinned API; not interchangeable byte/code-point indices |
| Maps/sets | Native `Std` hash/tree/dependent collections | Comparator, equality, hashing, law and instance prerequisites determine behavior |
| Functions/classes | Pi types; classes such as `BEq`, `DecidableEq`, `Repr`, `Inhabited`, `ToString` | Static typeclass-driven operations; `BEq` alone does not establish equality laws |
| Coercions/indexing | `Coe`, `CoeFun`, `CoeSort`, `GetElem` and related registered classes | Native elaboration protocols; an imported instance is not an unchecked cast |
| Effects | `Id`, reader/state/error transformers, `ST`, `BaseIO`, `EIO`, `IO` | Concrete state/error/effect semantics; no automatic WP instance for every monad |
| Concurrency | `Task`, native promises, references, synchronization types | Runtime scheduling/state; not a default deterministic proof model |
| Metaprogramming | `Lean.Name`, `Lean.Level`, `Lean.Expr`, `Lean.Syntax`, `Lean.TSyntax`, `Lean.Environment` | Representations of names/syntax/core expressions/environments, not interchangeable stages |
| Meta contexts | `MacroM`, `CoreM`, `MetaM`, `TermElabM`, `CommandElabM`, tactic state | Native staged effects and context ownership |
| Quotients | `Quot`, `Quotient` and their native constructors/lifts | Native quotient reasoning and audited foundation assumptions |

**Numeric and textual fidelity.** Literal overloading uses registered instances (`OfNat` and the relevant literal mechanisms); a token does not globally fix a runtime type. Integer conversion, shifts, overflow, division by zero, NaN equality, string slicing, and indexing must not be assigned TypeScript/Rust semantics by analogy. The pinned declaration and its documented runtime counterpart determine them. A backend/runtime correspondence claim must cover those exact operations (§12).

### Collection indexing, array literals, strings, and interpolation

**Feature / profile:** Native notation and distinct bounds/panic outcomes  
**Rule family:** `PS0V1-INDEX`  
**Source basis:** [L-INIT], [L-TERM]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
term ::= "#[" terms "]" | "[" terms "]"
       | term "[" index "]" | term "[" index "]?"
       | term "[" index "]!" | term "[" index "]'" proof
       | stringInterpolation | rawString
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
term ::= same native notation with PS embedded terms
// Array/list syntax does not use comma-call arity semantics.
// Embedded expressions are parsed in the notation's declared category.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def xs : Array Nat := #[10, 20]
#check xs[0]?
#check s!"length={xs.size}"
#check r#"raw text"#
```

**ProofScript `ps0` v1**

```proofscript
const xs: Array Nat := #[10, 20]
#check xs[0]?
#check s!"length={xs.size}"
#check r#"raw text"#
```

**Source language distinction and static meaning.**

`xs[i]` uses the appropriate GetElem operation with its required proof/instance machinery; `xs[i]?` returns an optional result where the selected notation defines it; `xs[i]!` has the native panic/default behavior; `xs[i]'h` supplies explicit evidence. These are not mutually interchangeable and a `!` suffix is not a proof of safety. Dynamic arrays and length-indexed vectors retain different types.

`s!"...{e}..."` uses the native interpolation mechanism and required rendering instances. Raw string delimiters use native hash-delimiter rules. Literal text, escapes, and embedded host terms must not be changed by a global punctuation pass. String positions/slices use the actual native API; code-point, byte, and validated position values cannot be freely substituted.

## 8A. Application libraries and import-driven capability scope

Replace a finite language-level API allowlist with import-driven availability. The target includes the relevant exported and legitimately accessible facilities of the pinned `Init`, `Std`, `Lean`, and optional `Lake` libraries. A full root import is not mandatory for every module, and private/internal APIs retain their real visibility.

Required capability families include arbitrary-precision naturals/integers; fixed-width signed/unsigned integers and machine sizes; floating point; Boolean and character/string operations; lists, arrays, byte arrays, vectors, ranges, maps, sets, dependent containers, iterators, parsers, JSON/serialization, state/error transformers, runtime/system IO, synchronization, time/network facilities, tasks, and the compiler/metaprogramming types in §10. A type family is not necessarily a kernel primitive or part of every minimal prelude. [L-INIT] [L-STD] [L-LEAN]

Preserve the exact pinned type and operation semantics, including bounds proofs, optional and panic-indexing variants, numeric conversions, string positions/encoding, and target-dependent machine representations. `xs[i]`, `xs[i]?`, `xs[i]!`, and `xs[i]'h` have different obligations; a `!` suffix is not a proof of absence of failure.

| Capability | PS0 v1 requirement | Evidence / portability boundary |
|---|---|---|
| Collections and algorithms | Expose applicable pinned list/array/vector/map/set/iterator APIs through imports | Equality/order/hash laws and indexing preconditions remain explicit |
| Parsing and serialization | Native parser, JSON, text/binary serialization facilities | A parsing result does not prove an external document follows an application schema |
| Files, paths, processes | Native system paths, handles, filesystem/process interfaces | Host permissions, failures, race behavior, and external state are effects |
| Time and networking | Applicable `Std.Time`/`Std.Net` and supporting interfaces | Availability and external-world behavior are not guaranteed by source typing |
| Concurrency | Native tasks, references, synchronization and cancellation mechanisms | Scheduling/termination/resource claims need appropriate semantics |
| Mathematics and proofs | Native foundational libraries and compatible imported theorem packages | Import identity, assumptions, and proof environment must be tracked |
| Compiler and language tooling | Native syntax/core-expression/environment/parser/elaborator/compiler/server APIs | Some code is meta-only, unsafe, internal, or runtime-dependent |
| Verification | Pinned WP/triple/gadget/VC machinery for supported effects | Having a monad instance is not having a sound complete application specification |
| Lake language extensions | Optional imported Lake DSL, including package/dependency/target/script families | A package DSL is an extension, not mandatory core PS0 build infrastructure |
| Third-party extensions | Compatible imported Lean/PS modules with their declared categories and handlers | Not an automatic approval of new logical assumptions or native code |

No `P1` staging label from a previous language profile controls this edition. An API is available when its actual module/registration and typing prerequisites are present. A missing concrete symbol is an environment error; a capability family in this table does not manufacture names such as a universal `fetch`, `Promise`, or filesystem specification. This reference is a language reference, not a complete signature listing for every standard-library declaration.

A `.ps` module importing `.lean` source depends on its actual compiled declarations and environment. Imported sources keep their own source grammar; host PS rules apply to the importing `.ps` expressions. Logical assumptions, external implementations, initialization, and erased/runtime dependencies must still be considered for verified claims.

## 9. Notation, syntax extensions, macros, and quotations

### Notation, mixfix, syntax categories, and binder predicates

**Feature / profile:** Full native language-extension vocabulary  
**Rule family:** `PS0V1-SYNTAX`  
**Source basis:** [L-SYNTAX], [L-TERM]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
command ::= notationDecl | mixfixDecl | syntaxDecl | syntaxAbbrev
          | "declare_syntax_cat" ident behavior?
          | binderPredicateDecl
syntaxItem ::= category precedence? | stringAtom | combinator | groupedItems
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
command ::= same native extension declarations
// Literal grammar tokens are syntax data, not PS host calls.
// Embedded host expressions and native-owned categories are distinguished.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- Requires the native syntax/elaboration environment.
syntax "twiceTerm " term : term
macro_rules
  | `(twiceTerm $x) => `($x + $x)
```

**ProofScript `ps0` v1**

```proofscript
-- Requires the native syntax/elaboration environment.
syntax "twiceTerm " term : term
macro_rules
  | `(twiceTerm $x) => `($x + $x)
```

**Source language distinction and static meaning.**

Admit `notation`, `prefix`, `postfix`, `infix`, `infixl`, `infixr`, local/scoped variants, explicit names and priorities, precedence declarations/expressions, `syntax`, syntax abbreviations, `declare_syntax_cat`, and `binder_predicate`.

Admit grammar descriptors and registered combinators: category references, grouping, alternatives, repetition, optional fragments, separated lists, trailing-separator policies, reserved/nonreserved token distinctions, Unicode/ASCII alternatives, and formatting/parenthesization annotations. Admit native `leading_parser` and `trailing_parser` programming and registration hooks used by Lean's own parser. [L-SYNTAX] [L-TERM]

Notation can be local or scoped, and can specify name, priority, and precedence. `prefix`, `postfix`, `infix`, `infixl`, and `infixr` determine different associativity/binding behavior. `syntax` declares a production/category; it does not itself give every newly parsed term a type or executable semantics. A macro or elaborator (or another native mechanism) must supply its meaning.

Syntax abbreviations name reusable parser descriptions. `declare_syntax_cat` creates a category with native behavior settings where supported. `binder_predicate` extends native binder-predicate notation, not arbitrary function parameter semantics. Text in quoted token strings is literal grammar data; a string resembling `f(x)` is not a host invocation to normalize.

### Grammar descriptors, combinators, precedence, and parser registration

**Feature / profile:** Native parser implementation capabilities used by Lean itself  
**Rule family:** `PS0V1-PARSER`  
**Source basis:** [L-SYNTAX], [L-TERM], [L-CMD]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
parserTerm ::= "leading_parser" precedence? options? term
             | "trailing_parser" precedence? lhsPrecedence? term
syntaxItem ::= cat | atom | grouped | unaryCombinator | binaryCombinator
             | "sepBy(" items "," string options? ")"
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
parserTerm ::= same native parser construction syntax
// Helper-call operands that are ordinary PS host terms use PS calls.
// The syntax-description DSL retains its native category grammar.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- Schematic parser-definition fragment under Lean.Parser:
-- def tokenParser := leading_parser "token"
-- def commaItems := leading_parser sepBy termParser ","
```

**ProofScript `ps0` v1**

```proofscript
-- Schematic parser-definition fragment under Lean.Parser:
-- def tokenParser := leading_parser "token"
-- def commaItems := leading_parser sepBy(termParser, ",")
```

**Source language distinction and static meaning.**

Lean-written parsers use category parsers, precedence, sequence/choice combinators, optional/repeated/separated fragments, reserved and nonreserved atoms, Unicode alternatives, and native formatting/parenthesization annotations. PS0 admits those capabilities, including builtin/dynamic parser attributes and parser aliases where their environment/stage permits them.

A parser priority controls grammar competition, not logical priority of the resulting theorem. A malformed branch cannot be accepted merely by selecting a fallback with different PS argument meaning. Recovery syntax can support editor diagnostics, but source qualification requires the intended completed parse. Parser caches, source positions, quotation depth, and macro hygiene information remain meaningful data for metaprograms.

The `sepBy(...)` spelling inside a syntax-description DSL is not automatically the same production as a PS value-level comma call. The category identifies which parser consumes it. Extension documentation and adapters must preserve that distinction.

### Macro rules, syntax quotations, antiquotations, splices, and hygiene

**Feature / profile:** Syntax data keeps its declared category contract  
**Rule family:** `PS0V1-QUOTE`  
**Source basis:** [L-TERM], [L-CMD], [L-SYNTAX]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
command ::= "macro" macroArgs ":" category "=>" term
          | "macro_rules" kind? matchAlts
quotation ::= "`(" category? "|"? categorySyntax ")"
// Native plain/resolved name literals and prechecked quotes are distinct.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
command ::= same native declarations with host PS macro-body terms
quotation ::= native category quotation | explicitly PS-owned quotation
// Native payloads do not undergo global comma-call or brace rewriting.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- Native term syntax data, not an evaluated function call:
-- `(f (x, y))
-- The quoted application has one tuple argument.
```

**ProofScript `ps0` v1**

```proofscript
-- Native term syntax data, not an evaluated host call:
-- `(f (x, y))
-- It still has one tuple argument; it is not a two-argument PS call.
```

**Source language distinction and static meaning.**

Admit `macro`, `macro_rules`, native kind/priority/scoping options, syntax quotation, typed category quotation, command sequences, tactic quotations, prechecked quotations, antiquotation, optional/repeated splices, and quotation patterns. Preserve syntax kinds, source information, identifier resolution, macro scopes, and hygiene.

A plain name literal and a resolved double-quoted name literal are not interchangeable. A `Syntax` tree is not the same as an elaborated `Expr`, and quoted text is not already a proof term. Preserve these distinctions in APIs and examples. [L-TERM] [L-CMD]

**PS0V1-QUOTE-01.** Native Lean-category quotations retain their native grammar contract, including the declared categories of extensions they contain. A native quoted `f (x, y)` is a one-tuple native application, not a PS two-argument call. Use the concrete named category quotation `` `(psTerm| f(x, y)) `` to construct the host call tree. The parallel `psCommand`, `psTactic`, and `psDoSeq` quotations use the corresponding registered PS categories. These interfaces are normative design requirements, not claims of current compiler support.

Do not globally rename Lean's native syntax kinds to PS0 names or rewrite string tokens in syntax declarations. An extension may deliberately treat its captured input as syntax data. The host application rules must not be applied blindly inside that data. A port that changes source punctuation must also review any macro that inspects those concrete syntax shapes.

The spelling `` `name `` denotes a native name literal, while the double-quoted resolved-name form checks resolution in the native context. A name is not an expression constant with inferred universe arguments. Antiquotation `$x`, category annotations, and optional/repeated splices insert syntax under their native typing and hygiene rules. A macro that duplicates syntax can duplicate evaluation; hygienic identifiers prevent unintended capture but do not prove evaluate-once semantics.

A named PS quotation returns a quotation action producing the corresponding typed syntax, for example ``m (Lean.TSyntax `psTerm)`` under the native quotation-monad requirements; it is not an already evaluated expression. In a quotation pattern, the same category parses the pattern before native syntax matching. A native quotation does not match a raw PS call node as if it were a native application. An author must explicitly normalize first to inspect the lowered tree, or use a PS quotation pattern to inspect source syntax.

Imported syntax and earlier commands affect later parsing. Preserve parser precedence, ambiguity handling, scoped activation, macro dispatch, expansion errors, and generated declarations. A generic finite pre-elaboration token ban is not a conforming v1 extension mechanism.

Native extensions can require explicit adapters at host-language boundaries. Such an adapter must preserve the declared category contract and document where PS0 syntax is accepted. It must not silently reinterpret a native tuple application as multiple arguments, or erase source provenance needed by diagnostics and macro behavior.

### Quotation, splicing, and normalized syntax observations

**PS0V1-SPLICE-01.** A native-category splice accepts syntax for the specified native category; a PS-category splice accepts syntax for that PS category. At the declared quotation/category interface, there is no automatic PS/native syntax coercion. A type annotation or a manual `TSyntax` constructor is not a semantic conversion. Because native `Syntax` and `TSyntax` are inspectable, their raw constructors remain available; deliberately built trees must still meet the destination category's handler and validation rules and do not acquire source-provenance claims by casting.

Use `PS0.Syntax.lower` to cross from a PS tree to its normalized elaboration tree. Native-to-PS reconstruction is not silently performed: a syntax producer constructs an explicit PS quotation or invokes an appropriate source-conversion tool. It can continue to generate native syntax in a native extension, so this is not a ban on native metaprogramming. Direct splices preserve identifier scopes, original subtree references and source information as native quotation does [L-QUOTE-ELAB]; generated wrapper tokens receive synthetic references to the producing node. Lowering never reparses a pretty-printed string to obtain identifiers.

**Canonical structural observations.** A nonempty host `f(a,b)` lowers to native application structure with two ordered positional arguments; `f((a,b))` lowers to one native tuple argument. Named entries lower to native named-argument nodes without reordering binders. Native application and grouping remain native nodes. PS declaration aliases, comma binders, braced control and helper forms lower as specified in §§1–5. A PS quotation keeps those PS nodes until explicitly lowered or dispatched through a standard host adapter. Syntax matching on raw PS quotations sees original PS argument lists, not their future elaborated implicit arguments.

**Empty invocation is not a purely syntactic translation.** Within standard host operand slots actually normalized, the sole type-directed core PS residual is `PS0.Syntax.emptyCall`, containing exactly the normalized head and no invented explicit arguments. Its original source reference is retained. The compiler-owned handler enforces §2’s strict completion rule and emits an ordinary Lean term; no residual syntax enters the kernel. A native macro inspecting the normalized tree can observe this residual node, and must not pretend it is already an ordinary saturated application. `PS0.Syntax.lower` therefore returns syntax for native **elaboration with this registered PS handler**, not a promise that an unextended upstream executable can parse or elaborate every returned node. A native-only source export must first resolve this obligation or report unsupported conversion, never erase `()`.

For the four supported input categories, the normalizer preserves independently owned extension nodes and does not inspect their native/custom data. Explicit PS captures inside such nodes remain raw until that extension elects to lower them. Any additional user-defined PS syntax must have its own registered macro/elaborator semantics; lowering does not invent them. Standard dispatch recursively lowers host operands only when it reaches their owning standard handler. A normalization result may therefore contain extension nodes as well as the specified empty-call residual. Applying the same normalizer again to an already normalized native-shaped subtree is a no-op; in particular, the residual empty-call node is neither nested nor completed again, and no identifier renaming or hidden Unit duplication is permitted. Raw PS captures deliberately retained inside independently owned extension nodes remain governed by that extension, not by a blanket recursive conversion.

**Example of an explicit bridge (design example; requires the `PS0.Syntax` meta interface):**

```proofscript
macro "psIdentity " x:psTerm : term => do {
  let y: Lean.TSyntax `term := ⟨← PS0.Syntax.lower(`psTerm, x.raw)⟩
  `(id $y)
}
```

Here `x` is raw host syntax, `y` is explicitly normalized elaboration syntax, and the surrounding quotation is native. The bridge neither evaluates `x` nor proves the resulting program. An empty call in `x` remains the specified residual until term elaboration. A raw-PS identity extension can instead be declared with PS input/result categories and return the raw capture without crossing categories.

### Parsing after extensions and host-term boundaries

Commands can register grammar used later in the same file. Imports can load syntax categories, macro rules, instances, attributes, and elaborators. Consequently a one-pass text scanner over a frozen initial grammar cannot establish full-language conformance. The module's environment and staging must be updated as required between commands.

A new extension consuming an ordinary host expression declares `psTerm`; one declaring literal `term` consumes a native expression. Its result category is an independent choice. The pinned standard host adapters and their dispatch boundary are defined in §0B. There is no source-level promise that every occurrence of `term` inside an independently owned DSL is automatically converted into a PS production.

This boundary is about grammar and syntax data, not about weakening logical checking. Generated declarations still have their actual typing, assumptions, effects, and assurance requirements. A macro expansion does not obtain a verified label by avoiding the handwritten source's visible keywords.

### Protected PS productions and extension conflicts

**PS0V1-EXT-OWNER.** At ordinary host sites, PS-owned productions have fixed ownership of (a) the `function`/`const` declaration heads in their legal modifier context; (b) a postfix call continuation after a completed host atom/postfix head; (c) the braced declaration/control/data/helper adapters in their specified contexts; and (d) the explicit PS-category interfaces. Native binders, native/custom DSL operands, native quotation data and unrelated operator spellings are outside this ownership. The distinction is by parse role, not by searching every token substring for `f(`.

An extension cannot change an already selected PS production's argument partition, source-gap rule, or block boundary by registering a higher native priority. Standard host parsing recognizes those productions before competing generic continuations; their malformed forms report the owned diagnostic rather than falling through to another grammar. A native or custom category can still define identical-looking tokens with its declared meaning, since entering that category is explicit. All nonconflicting extension competition keeps the pinned native precedence and ambiguity rules.

**Token-boundary preservation.** An extension token such as a combined literal `"f("` must not hide an otherwise protected ordinary host identifier-plus-call boundary by changing longest-token matching. At an ordinary host site, recognize the pinned identifier/escaped-identifier and owned punctuation boundaries before offering a compound extension token that crosses those boundaries. A competing compound token claiming that same protected span is a `PS0V1-EXT-CONFLICT`, not a new lexical spelling of a valid PS call. Strings, comments, quoted identifiers, native quotations and explicitly entered native/custom operands are scanned in their own categories and retain their original token tables. The rule applies only to an actual owned host boundary, not to every parenthesis occurring in arbitrary DSL text. A compound token unrelated to a protected host boundary remains a valid extension token. This source-level lexical ownership is part of the host adapter contract, not permission to change the native scanner globally. Lean’s pinned lexer-less parser, token-table and longest-match behavior motivate this explicit boundary; the ownership rule itself is a PS design decision. [L-PARSER-BASIC]

Compatibility is checked at the **particular host use**, not by deciding whether two arbitrary parser programs accept intersecting languages. If an extension claims the same protected host span with a different ownership/argument partition, that use must fail with `PS0V1-EXT-CONFLICT` at PARSE, or be diagnosed earlier at ENV when the conflict is explicit from its registration. A redundant candidate with the same normalized ownership tree is not a conflict. No maximum-priority trick can turn a known conflicting interpretation into valid host source. A resource limit or nonterminating parser is a failed/uncompleted parse, not evidence that no conflict exists.

Native extensions remain importable and usable in their declared native/custom categories; a conflicting **host spelling** can be exposed through a distinct prefix or explicit category operand. This preserves extension capability without promising that every native concrete spelling is an ordinary PS host spelling. Low-level code that directly forges syntax or mutates registries does not override this source-qualification contract; its execution and logical result remain separately auditable. Scoping and leaving a local/scoped registration restore the prior active grammar normally.

## 10. Elaborator, compiler, and reflection programming

### Elab rules, custom tactics, deriving handlers, and expression construction

**Feature / profile:** Full native elaboration and metaprogramming contexts  
**Rule family:** `PS0V1-ELAB`  
**Source basis:** [L-SYNTAX], [L-ELAB], [L-LEAN]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
command ::= "elab" elabArgs ":" category relation? "=>" term
          | "elab_rules" kind? category? relation? matchAlts
          | registeredHandlerDeclaration
term ::= nativeMetaProgram
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
command ::= same native elaborator declarations
// Host code uses PS calls; quotation/category data stays owned.
// Availability follows module/meta import staging.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- Requires Lean and the appropriate meta import context.
elab "trivialProof" : tactic => do
  Lean.Elab.Tactic.evalTactic (← `(tactic| exact True.intro))
```

**ProofScript `ps0` v1**

```proofscript
-- Requires Lean and the appropriate meta import context.
elab "trivialProof" : tactic => do {
  Lean.Elab.Tactic.evalTactic(← `(tactic| exact True.intro))
}
```

**Source language distinction and static meaning.**

Admit `elab`, `elab_rules`, term/command/tactic elaborator registrations, declaration-specific elaborators, registered deriving handlers, coercion/elaboration extensions, and the native expected-type/configuration mechanisms. Preserve `MacroM`, command and term elaboration contexts, `MetaM`, core contexts, tactic state, and their actual effect/staging requirements.

The language must be able to express and use the upstream APIs for:

- names, levels, expressions, syntax trees, source spans, messages, and typed syntax;
- local contexts, metavariables, substitutions, unification, reduction, instance synthesis, and proof construction;
- declarations, environments, persistent/scoped environment extensions, imports, options, attributes, and registrations;
- pretty printers, parenthesizers, formatters, delaborators, documentation, editor information, and diagnostic extensions;
- compiler intermediate representations and passes, runtime interfaces, server tasks, serialization, and related Lean-written infrastructure.

These are **library capabilities**, not a promise that every API is safe, pure, public, or available from every import. Respect the distinction between elaborating an object-language term, evaluating a metaprogram, and publishing a logical declaration. `meta` availability must be preserved transitively. [L-LEAN] [L-CMD] [L-DECL]

Admit native reflection/evaluation helpers, `run_cmd`, `run_tac`, and equivalent registered facilities when actually available. Reading environment state, compiling code, or constructing a declaration does not automatically make it admissible as a completed checked proof. Strong assurance must consider the final statement, declaration dependencies, and checks performed, not just the visible tactic script.

The example is an illustrative tactic elaborator body, not a complete standalone module; it must run under the actual tactic/elaboration monad and meta imports. `Expr` construction, metavariable assignments, quotation elaboration, and command execution require their native contexts. A compiled meta program can execute effects, fail, or create new declarations; the final theorem statement and evidence must still be checked at the claimed boundary.

### Low-level elaboration helpers and reflection syntax

**Feature / profile:** Native percent-suffixed and context-control families  
**Rule family:** `PS0V1-INTERNAL`  
**Source basis:** [L-TERM], [L-ELAB], [L-DO]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
term ::= "decl_name%" | "type_of%" term | "value_of%" ident
       | "no_implicit_lambda%" term | "match_expr" term "with" alts
       | registeredInternalTerm
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
term ::= same native helper productions with category-aware host operands
// Fixed grammar arguments/configuration tokens do not become arbitrary calls.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- Schematic context-preserving source forms:
-- def currentName := decl_name%
-- type_of% expression
-- match_expr e with | Some.constant x => body | _ => fallback
```

**ProofScript `ps0` v1**

```proofscript
-- Schematic context-preserving source forms:
-- def currentName := decl_name%
-- type_of% expression
-- match_expr e with | Some.constant x => body | _ => fallback
```

**Source language distinction and static meaning.**

The following families are explicitly included rather than dismissed as “internal”:

| Family | Representative pinned forms |
|---|---|
| Elaboration control | `no_implicit_lambda%`, `type_of%`, `ensure_type_of%`, `ensure_expected_type%`, `value_of%`, `clear%` |
| Metavariable scheduling | `let_mvar%`, `wait_if_type_mvar%`, `wait_if_type_contains_mvar%`, `wait_if_contains_mvar%`, `wait_for_expected_type%` |
| Declaration context | `decl_name%`, `private_decl%`, `with_decl_name%` |
| Operator elaboration | `binrel%`, `binrel_no_prop%`, `binop%`, `binop_lazy%`, `leftact%`, `rightact%`, `unop%` |
| Generated/default terms | `default_or_ofNonempty%`, `struct_inst_default%`, `no_error_if_unused%`, `no_index` |
| Iteration support | `for_in%`, `for_in'%`, registered iterator helpers |
| Expression inspection | `match_expr`, `let_expr`, `show_term_elab`, metadata diagnostic syntax |
| Named diagnostics | `throwNamedError`, `throwNamedErrorAt`, `logNamedError`, `logNamedErrorAt`, warning counterparts |

Their exact category, arity, scope, and restrictions come from the pinned parser/elaborator, not from their suggestive spelling. In a native owned production, a parenthesized configuration item is not an ordinary PS0 function-call argument. [L-TERM]

A helper such as `wait_for_expected_type%` controls elaboration scheduling, not runtime waiting. `private_decl%` changes the generated declaration context; it is not a runtime private-field access modifier. `match_expr` inspects elaborated expression patterns under the native reflection mechanism, while syntax quotation patterns inspect syntax trees. Applying the ordinary algebraic-data pattern grammar to either would lose their intended semantics.

Native `run_cmd`, `run_tac`, evaluation helpers, builtin handler attributes, and registered configuration evaluators are available when their imports/stages permit them. Their execution may lie outside a pure logical proof term. A source reference to an internal helper is not itself evidence that a lower-trust environment was rechecked independently.

## 11. Attributes, options, initialization, documentation, and bootstrap

### Attributes, priorities, reducibility, and configuration

**Feature / profile:** Registered native metadata and executable handlers  
**Rule family:** `PS0V1-ATTR`  
**Source basis:** [L-CMD], [L-DECL], [L-ELAB]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
attributes ::= "@[" attrInstance ("," attrInstance)* "]"
command ::= "attribute" "[" attrChanges "]" ident+
          | "set_option" ident value ("in" command)?
configItem ::= "+" ident | "-" ident | "(" ident ":=" term ")"
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
attributes ::= same native forms
command ::= same forms; host term/tactic/command variants retain scope
// No finite attribute allowlist defines PS0 v1.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
def keepN (n : Nat) : Nat := n
@[simp] theorem keepN_eq (n : Nat) : keepN n = n := rfl
set_option pp.universes true in
#check keepN_eq
```

**ProofScript `ps0` v1**

```proofscript
def keepN(n: Nat): Nat := n
@[simp] theorem keepN_eq(n: Nat): keepN(n) = n := rfl
set_option pp.universes true in
#check keepN_eq
```

**Source language distinction and static meaning.**

Admit declaration attribute lists, the `attribute` command including erasure, local/scoped attributes, custom attribute registration, and all applicable imported attributes. This includes instance, simplification, reducibility, exposure, compiler optimization, foreign interface, parser/elaborator, formatter, and documentation attributes.

Examples include `simp`, `instance`, `default_instance`, `reducible`, `irreducible`, `expose`, `inline`, `specialize`, `extern`, `export`, `implemented_by`, and the builtin parser hooks. The existence of a spelling in this table does not waive its target-kind or import requirements. Attribute handlers may execute code and produce declarations; they are not necessarily passive metadata. [L-CMD] [L-DECL]

Kernel reducibility hints and elaborator reducibility attributes must not be conflated. In the pinned declaration representation, hints guide the kernel's unfolding strategy; they are not identical to user transparency attributes, nor is a reducibility-hint constructor named `opaque` identical to an `opaque` declaration. [L-DECL]

Admit `set_option` with registered values and scoped command/term/tactic forms, option registrations, trace-class registrations, configuration-elaborator declarations such as `declare_config_elab`, and native configuration items such as `+option`, `-option`, and `(option := value)`. Configuration evaluation must preserve the declared schema, expected types, defaults, and stage requirements. [L-DECIDE] [L-ELAB] Admit `unlock_limits` in the language with its native meaning; an external execution budget may still stop computation.

An option that changes checking or evaluation must be reflected in the evidence for a stronger claim. A language-level permission to use `set_option` is not permission to present an unchecked environment as independently kernel-checked.

Attribute names and argument schemas must actually be registered; a familiar spelling is not sufficient. Erasing an attribute (`attribute [-simp] name`) changes the registered environment, not the underlying theorem's truth. `local`/`scoped` activation is preserved. A native configuration parenthesis `(priority := ...)` is a configuration production and is not banned as an ordinary gap-parenthesized host argument.

Checked-source reports must identify options that affect proof checking or declaration validation. Allowing the `set_option` grammar does not justify a stronger claim if checking was disabled or bypassed by an effectful extension.

### Initialize and builtin_initialize

**Feature / profile:** Native startup effects and environment registration  
**Rule family:** `PS0V1-INIT`  
**Source basis:** [L-CMD], [L-SYNTAX], [L-LEAN]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
initializeCmd ::= modifiers ("initialize" | "builtin_initialize")
                  (ident ":" type "←")? doSeq
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
initializeCmd ::= same native startup command
// Braced bodies and host PS calls are available where the category permits.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- Illustrative startup reference; requires native IO facilities.
initialize counter : IO.Ref Nat ← IO.mkRef 0
```

**ProofScript `ps0` v1**

```proofscript
-- Illustrative startup reference; requires native IO facilities.
initialize counter: IO.Ref Nat ← IO.mkRef(0)
```

**Source language distinction and static meaning.**

Admit `initialize` and `builtin_initialize`, including named initialized objects and native effectful bodies. Preserve their distinct startup/registration timing and module behavior. Environment extensions, parser tables, option/attribute registries, and mutable runtime state used by Lean depend on these facilities.

Do not erase an initializer because its exported value appears unused, or treat initialization as a pure theorem declaration. Reproducible/verified claims must account for the relevant initialization effects and environment identity. [L-CMD] [L-SYNTAX]

The named initializer binds the resulting initialized object according to the native module machinery. Registration initializers can affect parsing/elaboration of following or importing modules. A source-normalization pass must not reorder them or omit them because their named values appear unused. Builtin initialization has its own bootstrap timing; replacing every builtin initializer with an ordinary function call is not equivalent.

### Documentation, Verso, tags, error explanations, and deprecation

**Feature / profile:** Native documentation and diagnostic extension forms  
**Rule family:** `PS0V1-DOC`  
**Source basis:** [L-CMD], [L-TERM], [L-ELAB]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
command ::= moduleDoc | docComment declaration
          | docComment "add_decl_doc" ident
          | "recommended_spelling" ... | "register_tactic_tag" ...
          | "register_error_explanation" ident term | deprecationCmd
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
command ::= same native documentation/registration forms
// Ellipses in this sketch denote the native command-specific productions.
// Doc markup and code-bearing syntax retain their declared categories.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
/-- Returns its natural-number argument. -/
def identityN (n : Nat) : Nat := n
/-! Module-level explanatory documentation. -/
```

**ProofScript `ps0` v1**

```proofscript
/-- Returns its natural-number argument. -/
function identityN(n: Nat): Nat := n
/-! Module-level explanatory documentation. -/
```

**Source language distinction and static meaning.**

Admit native Markdown/plain and Verso documentation syntax and the registered supporting facilities, including `add_decl_doc`, `recommended_spelling`, `register_tactic_tag`, `tactic_extension`, `register_error_explanation`, and documentation extension hooks. Preserve source attachment, declaration ownership, and diagnostic behavior. Documentation parsers are part of the source-extension ecosystem, not always ignorable whitespace. [L-CMD] [L-TERM]

Admit `dbg_trace`, assertion debugging, and experimental `idbg` syntax at the pinned version. Runtime/editor execution requirements and experimental limitations remain upstream requirements. Interactive debugging is neither mandatory during compilation nor evidence of functional correctness.

A documentation comment forms part of the relevant syntax/metadata rather than ordinary ignored trivia. Verso-enabled documentation is parsed according to the active native option and registration environment. `add_decl_doc` respects native declaration ownership, and deprecation commands have their actual warning/import behavior. Pretty printers, parenthesizers, formatters, delaborators, and info-tree hooks are extension capabilities; their output must preserve a PS source's argument partition when used as a round-trip formatter.

### Quotient, parser, and other bootstrap commands

**Feature / profile:** Native internal forms under actual initialization preconditions  
**Rule family:** `PS0V1-BOOT`  
**Source basis:** [L-CMD], [L-SYNTAX], [L-DECL]

**Lean 4 grammar family → ProofScript surface (schematic).**

**Lean 4 grammar (schematic)**

```text
command ::= "init_quot" | "gen_injective_theorems%" ident
          | "docs_to_verso" names | registeredBootstrapCommand
// Builtin parser hooks/aliases are native registration facilities.
```

**ProofScript `ps0` v1 grammar (schematic)**

```text
command ::= same native bootstrap forms
// Availability is not permission to repeat foundation initialization.
// prelude/import and stage requirements still apply.
```

**Paired examples — illustrative, not execution receipts.**

**Lean 4.35.0**

```lean
-- Schematic bootstrap-only source; not an ordinary ready-made module:
-- init_quot
-- gen_injective_theorems% SomeInductive
```

**ProofScript `ps0` v1**

```proofscript
-- Schematic bootstrap-only source; not an ordinary ready-made module:
-- init_quot
-- gen_injective_theorems% SomeInductive
```

**Source language distinction and static meaning.**

Include `init_quot`, `gen_injective_theorems%`, `docs_to_verso`, builtin parser-attribute hooks, parser aliases, and internal scoped commands such as `end_local_scope` under their actual native scope and preconditions. Their presence in the language target does not make them ordinary application recommendations.

Bootstrap operations cannot run indiscriminately in an already initialized environment. In particular, quotient initialization and generated foundational declarations must obey the same uniqueness, environment, and checking requirements as Lean. “All features” does not mean every command succeeds at every point in every file.

An internal syntax form can be scoped or accessible only with a specific import. Full-language capability includes expressing the upstream implementation's legitimate use, not invoking its commands in every user context. Generated foundation declarations still have their real uniqueness, typing, and trust requirements.

## 12. Logical assumptions and assurance boundaries

A report about a PS0 module must distinguish:

1. **Language acceptance:** did the selected edition parse/elaborate the source under the intended imports and options?
2. **Logical checking:** which final statements and definitions were checked, and relative to which assumptions?
3. **Executable availability:** does the relevant program have compiled code and valid runtime/link dependencies?
4. **Verified claim:** what specification, effects, termination property, erasure behavior, assumptions, and execution layer does the evidence actually establish?

This is one language with different evidence outcomes, not a second unchecked proof kernel. A conditional theorem may be valid relative to stated axioms without being an unconditional theorem under an approved foundation. A program may compile without being claimed to satisfy a functional specification.

### Construct-by-construct interpretation

| Construct | Admitted use | What admission does not establish |
|---|---|---|
| Ordinary total `def` | Lean-checked logical function and applicable compiled code | Native compiler correctness or an unstated functional specification |
| `theorem` | Checked proof of its actual elaborated statement | Truth under an undisclosed or inconsistent assumption set |
| `axiom` | Explicit typed assumption | Proof of the assumption or approval in an existing foundation |
| Bodyless `opaque` | Native inhabitant-synthesis form when valid | That it is an axiom, or that an external implementation is correct |
| `partial` | Native opaque interface and partial recursive implementation | Termination or definitional recursive equations |
| `partial_fixpoint` | Native fixed-point semantics and checked equations | Total execution of the compiled function |
| `noncomputable` | Logical definition without a required executable body | Executable availability in runtime-relevant code |
| Unsafe declaration | Native unsafe programming | Admissibility as an ordinary safe logical dependency |
| Unsafe expression / `implemented_by` | Native interface/implementation separation | Safe memory behavior or implementation correspondence |
| `extern` | Native ABI binding | Correctness of the foreign code from its type alone |
| `sorry` / recovery holes | Incomplete development state | A completed proof or hole-free qualifying artifact |
| Native-assisted decision | The pinned proof-construction/trust mechanism | Elimination of its generated assumptions by merely renaming the tactic |
| `meta` / custom elaborator | Compile-time program under stage rules | Purity, sandboxing, or automatic assurance of every generated declaration |
| Erased binding | Native verification-only state operation | Permission to drop effects of an erased-result action |
| Imported `.lean` module | Genuine Lean compilation | Automatic admission into a verified dependency closure |

### Mandatory conditions for stronger claims

**PS0V1-ASSURANCE-01.** Incomplete source is permitted for development, but unresolved metavariables, source/generated/transitive `sorryAx`, and error-recovery declarations cannot qualify as completed proofs or hole-free checked output. Imported dependencies and generated declarations count; inspecting only handwritten tokens is insufficient.

**PS0V1-ASSURANCE-02.** PS0 v1 supplies **no implicit application-assumption approval policy**. A policy-qualified claim must name and identify its supplied policy and check the actual transitive assumption closure, including generated native-computation axioms, against it. Without a supplied policy, report a checked theorem conditionally with its assumption closure and `policy approval: not assessed`; never infer approval from the language version or from another project. A supplied policy accepting the closure and one rejecting it produce different qualification outcomes. The policy is data for qualification, not a second source-language reference.

**PS0V1-ASSURANCE-03.** Full metaprogramming and IO mean compilation can execute code. Logical checking is not an operating-system sandbox. An independent assurance claim must not trust arbitrary extension code merely because it ran inside a Lean process; it must establish the final statement/environment identity and the checks supporting the claim. [L-VALIDATE]

**PS0V1-ASSURANCE-04.** Neither qualified verification label below may be issued while mandatory specification-coverage, effect, assumption, erasure, or required termination obligations remain unresolved. Use `source-verified program` for evidence about source semantics and `execution-correspondence-verified program` only when the additional stated artifact/layer correspondence is checked. The unqualified phrase `verified executable` is not a standalone assurance result. Source proof checking alone does not verify the C compiler, runtime, machine code, or external system.

**PS0V1-ASSURANCE-05.** Restricting a particular verified claim is not the same as banning a language feature from all ordinary programs. For example, a partial-correctness theorem must not be advertised as total correctness, and an unsafe runtime implementation cannot be promoted to verified merely because its logical interface is safe.

### Required qualification information

**PS0V1-CLAIM-01.** Qualification is parameterized by an explicit claim, not by a hidden default specification. A report using either verification label must state:

| Field | Required content |
|---|---|
| Subject | Source/module/root-declaration identity and the effective environment identity |
| Verified statement | Actual elaborated specification, including its parameters, preconditions, allowed effects and exceptional behavior |
| Coverage | Named roots and dependency/operation scope, plus the criterion that made each required specification obligation mandatory |
| Correctness kind | Partial correctness or total correctness; termination premises and exclusions must be explicit |
| Evidence | Checked declarations/proofs and the checking process; incomplete goals, recovery terms and `sorryAx` dependencies are disqualifying |
| Logical assumptions | The actual relevant transitive axiom closure and the identified approval policy, or a conditional theorem report with approval not assessed |
| Execution boundary | Source semantics only, or the exact IR/C/native/other artifact and layer connected by correspondence evidence |
| Trusted components | Toolchain, runtime, foreign implementations and external-world assumptions not discharged by the evidence |
| Erasure and effects | Applicable erasure/effect model and any checked correspondence needed by the stated claim |
| Result | One of the two qualified labels, a conditional checked-theorem result, ordinary checked output, or a refusal identifying unresolved obligations |

No serialization format, signing mechanism or package manager is mandated. These are the minimum semantic fields needed to interpret the claim. A deliberately weak specification is not a proof of unstated behavior; its weakness must remain visible. A partial-correctness result does not silently become a total one. An identified trusted compiler/runtime is a legitimate boundary for source verification, but is not proved correspondence.

For an `extern`/`implemented_by` replacement, a source-only claim explicitly identifies the logical model and unproved replacement boundary. To claim execution correspondence, provide correspondence evidence covering the actual replacement and the selected artifact/layer, or make the relevant external premise part of the explicit conditional statement and label it as assumed, not proved. A policy accepting a logical axiom does not also approve arbitrary runtime/ABI assumptions by implication.

The language contains conditional proofs and general programming independently of these reporting labels. Failure of qualification does not retroactively ban valid native source. It does block publication **under the stronger label** and does not permit an artifact to be mislabeled as verified.

### Completed checking is not a silent restriction of language capability

This reference admits the full native programming/extension mechanisms, but labels their evidence accurately. The language can express axioms without calling them proved; it can express partial programs without calling them total; it can express unsafe/runtime-replaced implementations without pretending a logical signature proves their behavior.

For a completed ordinary checked-output claim, the relevant source and transitive generated proof dependencies must be free of unresolved metavariables and `sorryAx`; native development artifacts that deliberately contain holes remain development artifacts, not this completed outcome. The relevant scope of the claim (module, root theorem, or executable dependency closure) must be stated. Disclosing an axiom is necessary for a conditional logical claim; admitting its syntax is not approval of a stronger foundation.

An effectful elaborator can change the environment or invoke low-level declaration APIs. Accordingly, a **kernel-checked** or **independently checked** label requires evidence that the intended final statements and dependencies actually underwent the corresponding checks. Merely loading an environment that contains declaration names is insufficient. Native `.lean` files remain unrestricted by PS source grammar, but their use as dependencies does not erase these assurance obligations.

No claim of source-level correctness automatically proves semantic preservation through compiler intermediate representations, generated C, a system compiler, runtime, foreign library, operating system, or hardware. A report under either qualified verification label must identify exactly which of those layers its evidence covers. Failure to cover a layer must be disclosed rather than hidden by a stronger-sounding label.

## 13. Source examples and acceptance/refusal reference

This section specifies outcomes for **candidate conformance cases**, using paired Lean and ProofScript examples. It is not a record of executed tests. Each case requires the indicated types/imports, isolated source context, and a recorded actual result before it can become evidence. Positive language admission is not a verified-executable certificate. The error labels are defined in §0A.

### Complete-module illustrations

The paired module below states and proves a simple source equality; it makes no backend/foreign-runtime claim.

**Lean 4.35.0**

```lean
module
public import Init
public section

def add (x y : Nat) : Nat := x + y

theorem add_zero (x : Nat) : add x 0 = x := by
  rfl
```

**ProofScript `ps0` v1**

```proofscript
public import Init

function add(x: Nat, y: Nat): Nat := x + y

theorem add_zero(x: Nat): add(x, 0) = x := by {
  rfl
}
```

The next paired module shows the native explicit-module/metaprogramming stage shape. Native syntax quotations retain native grammar; the macro duplicates syntax and therefore is not an evaluate-once effect abstraction.

**Lean 4.35.0**

```lean
module
import Lean
meta import Lean
public section

syntax "twiceTerm " term : term
macro_rules
  | `(twiceTerm $x) => `($x + $x)
```

**ProofScript `ps0` v1**

```proofscript
module
import Lean
meta import Lean
public section

syntax "twiceTerm " term : term
macro_rules
  | `(twiceTerm $x) => `($x + $x)
```

### Positive source/evidence-boundary cases

| ID | Source or setup | Required interpretation | Rule location |
|---|---|---|---|
| PS0-P-DECL-01 | `const count: Nat := 3` | Parameterless source `def` alias. | §2 |
| PS0-P-DECL-02 | `function add(x: Nat, y: Nat): Nat := x + y` | Comma explicit telescope, native curried meaning. | §2 |
| PS0-P-DECL-03 | `function tick(): Nat := 1` | Insert exactly one final required Unit parameter. | §2 |
| PS0-P-DECL-04 | `def f (x y : Nat) := x + y` | Full native declaration telescope remains valid in v1. | §2 |
| PS0-P-DECL-05 | `function same {α: Type}[BEq α](x: α, y: α) := x == y` | Implicit/instance/explicit order is preserved. | §2 |
| PS0-P-DECL-06 | `function choose(n: Nat)[Decidable(n = 0)](x: Fin(n + 1)) := x.val` | Interleaved dependent binders. | §2 |
| PS0-P-DECL-07 | `opaque value: Nat := 1` | Checked opaque body, not transparent def. | §2 |
| PS0-P-DECL-08 | `opaque value: Nat` | Native inhabitant synthesis where available. | §2 |
| PS0-P-DECL-09 | `axiom assumed: True` | An explicit assumption, not a proved theorem. | §2, §12 |
| PS0-P-DECL-10 | `noncomputable def pick {α: Sort u}(h: Nonempty α): α := Classical.choice(h)` | Logical use under native noncomputability conditions. | §2 |
| PS0-P-CALL-01 | `add(1, 2)` / `add 1 2` | Two arguments, same intended curried application. | §2 |
| PS0-P-CALL-02 | `sumPair((1, 2))` | One tuple argument. | §2 |
| PS0-P-CALL-03 | `tick()` / `tick(())` | Unit completion or explicit Unit for this function type. | §2 |
| PS0-P-CALL-04 | `greet(name := "Ada")` | A declared named parameter; type must agree. | §2 |
| PS0-P-CALL-05 | `greet()` | Complete the declared default, not a guessed value. | §2 |
| PS0-P-CALL-06 | `add(1)` | A nonempty partial application when the expected type permits it. | §2 |
| PS0-P-CALL-07 | `f(x,)` | A single argument with one trailing comma. | §2 |
| PS0-P-CALL-08 | `f g(x, y)` | Required tree `f (g x y)`; types must support it. | §2 |
| PS0-P-CALL-09 | `(f g)(x, y)` | Required tree `(f g) x y`; not CALL-08. | §2 |
| PS0-P-CALL-10 | `f(/- inside -/ x)` | Comment inside the adjacent argument list. | §2 |
| PS0-P-SCOPE-01 | `variable (n: Nat)` | A native explicit section binder, not application. | §1 |
| PS0-P-SCOPE-02 | `#check (f x)` / `exact (hp)` | Fresh grouped terms in command/tactic argument positions. | §1, §2 |
| PS0-P-SCOPE-03 | `module` with `public section` | Native explicit-module visibility. | §1 |
| PS0-P-SCOPE-04 | Headerless `.ps` with `public import Init` | Implicit modern module and public-name default. | §1 |
| PS0-P-SCOPE-05 | `meta import Lean` / `public meta import Lean` | Stage availability under native module rules. | §1 |
| PS0-P-SCOPE-06 | `import all M` | Native all/private access where valid. | §1 |
| PS0-P-SCOPE-07 | `open scoped N` / `open N renaming x → y` | Distinct scoped/naming behavior. | §1 |
| PS0-P-SCOPE-08 | `prelude` in a proper bootstrap module | No injected ordinary prelude dependency. | §1, §11 |
| PS0-P-DATA-01 | Braced/native `structure` and `inductive` | Same typed data declarations with surface delimiters. | §4 |
| PS0-P-DATA-02 | `instance : Inhabited Color := ⟨Color.red⟩` | Native instance value form included. | §4 |
| PS0-P-DATA-03 | `deriving instance Repr for Point` | Standalone deriving when a handler exists. | §4 |
| PS0-P-DATA-04 | `{ p with x := p.x + 1 }` | Typed structure update, not alias mutation. | §4 |
| PS0-P-DATA-05 | `{ n: Nat // n < 10 }` | Native subtype, with proof required at construction. | §4, §8 |
| PS0-P-PAT-01 | `match n with { \| 0 => 0 \| k + 1 => k }` | Native successor-pattern meaning under braced syntax. | §4 |
| PS0-P-PAT-02 | `some(n)` in an Option constructor-pattern position | Constructor-only adapter, not ordinary term call completion. | §4 |
| PS0-P-PAT-03 | Named equation/motive/generalizing match | Native dependent elimination and configuration categories. | §4 |
| PS0-P-PAT-04 | `nomatch impossible` | Only when the indexed/empty type makes all cases impossible. | §4 |
| PS0-P-REC-01 | Total recursion with a valid `termination_by` | Native proof-backed recursive construction. | §5 |
| PS0-P-REC-02 | `partial function spin(n: Nat): Nat := spin(n)` | Partial program, no totality claim. | §5, §12 |
| PS0-P-REC-03 | A valid `partial_fixpoint` definition | Checked fixed-point equations, not automatic termination. | §5 |
| PS0-P-REC-04 | Valid inductive/coinductive monotone fixed points | Native lattice construction, no new unchecked kernel primitive. | §5 |
| PS0-P-DO-01 | `do { let mut n := 0; n := n + 1; return n }` | Native do separators and mutable-local semantics. | §3 |
| PS0-P-DO-02 | `for x in xs, y in ys do { body }` | Zipped iteration, not nested Cartesian product. | §3 |
| PS0-P-DO-03 | Native `repeat`, `while`, `repeat ... until` | General ordinary loops; claim-specific termination separate. | §3 |
| PS0-P-DO-04 | Monadic `if let ... ← action` | Included with actual monad and pattern prerequisites. | §3 |
| PS0-P-DO-05 | A correctly placed final-argument `do←` | Forward enclosing control effects through supported wrapper. | §3 |
| PS0-P-DO-06 | Typed/pattern `catch` with `finally` | Native exception/cleanup semantics. | §3 |
| PS0-P-PROOF-01 | `by { intro h; exact h }` for `p → p` | A completed proof when context/type are correct. | §6 |
| PS0-P-PROOF-02 | A registered custom proof-producing tactic | Generated evidence and assumptions still checked. | §6, §10 |
| PS0-P-PROOF-03 | `native_decide` with its actual native-computation assumptions | Native language admission; not assumption-free qualification. | §6, §12 |
| PS0-P-VC-01 | Ordered `given` / `requires` / `ensures r => ...` | Requires pinned WP environment and actual spec proof. | §7 |
| PS0-P-VC-02 | Braced `where { finally { \| spec => { ... } } }` | A genuine proof must replace the schematic ellipsis. | §7 |
| PS0-P-VC-03 | `erased x ← action` | Action still executes; result is verification-only. | §7 |
| PS0-P-EXT-01 | `syntax`, `macro`, `macro_rules`, `elab`, `elab_rules` | Admitted under category/stage/handler conditions. | §9, §10 |
| PS0-P-EXT-02 | Native quotation containing `f (x, y)` | Syntax data keeps the one-tuple native application. | §9 |
| PS0-P-EXT-03 | Custom deriving, attributes, simprocs, parser categories | Registration-driven feature closure. | §4, §6, §9 |
| PS0-P-META-01 | `initialize` / `builtin_initialize` | Preserve stage and registration effects. | §11 |
| PS0-P-META-02 | Native `%` elaboration helpers | Actual arity, category, and stage restrictions apply. | §10 |
| PS0-P-RUN-01 | `IO.println("hello")` in an appropriate do block | Native effectful IO call. | §7B |
| PS0-P-RUN-02 | Unsafe declaration or valid unsafe expression | Native safety classification; no runtime-proof promotion. | §7B |
| PS0-P-RUN-03 | Properly linked `extern` / `implemented_by` / borrowed ABI | Native runtime boundary, separate correspondence evidence. | §7B |
| PS0-P-DIAG-01 | `#check`, `#eval`, `#print axioms`, guard commands | Diagnostic outcomes only. | §7A |
| PS0-P-DOC-01 | Native Markdown/Verso documentation and bootstrap forms | Actual import/initialization conditions, not universal execution. | §11 |
| PS0-P-ENV-01 | Compatible imported native/Lake extension | Full extension availability, not automatic approved assumptions. | §8A, §14 |

### Negative source and disallowed-claim cases

| ID | Source or attempted claim | Expected stage / category | Reason |
|---|---|---|---|
| PS0-N-CALL-01 | `f (x)` in an ordinary host application | PARSE | PS host gap-parenthesized application. |
| PS0-N-CALL-02 | `f (x, y)` in an ordinary host application | PARSE | Must preserve one tuple by writing `f((x,y))`. |
| PS0-N-CALL-03 | `f ()` in an ordinary host application | PARSE | Use explicit `f(())` or the qualified empty-call rule. |
| PS0-N-CALL-04 | `f/- gap -/(x)` | PARSE | Valid comment trivia still breaks adjacency. |
| PS0-N-CALL-05 | `answer()` for `answer : Nat` | ELAB | A noncallable value has no empty invocation. |
| PS0-N-CALL-06 | `one()` with a required Nat parameter | ELAB | No invented Nat/Inhabited argument. |
| PS0-N-CALL-07 | `two()` with two required Unit parameters | ELAB | Exactly one required Unit is the only insertion exception. |
| PS0-N-CALL-08 | `f()` with unresolved required argument type | ELAB | Do not guess Unit to resolve an unknown binder type. |
| PS0-N-CALL-09 | `f(name := x, y)` | PARSE | Positional argument after a named argument. |
| PS0-N-CALL-10 | `f(name := x, name := y)` | PARSE or ELAB | Duplicate named argument must reject no later than elaboration. |
| PS0-N-CALL-11 | `f(unknownName := x)` | ELAB | Unknown parameter name. |
| PS0-N-CALL-12 | `f(,)` / `f(x,,y)` | PARSE | No empty argument entries or repeated separator. |
| PS0-N-BIND-01 | `function f(x: Nat)(y: Nat) := x + y` | PARSE | Alias requires one comma group or intervening nonexplicit binder; native def remains available. |
| PS0-N-BIND-02 | `function f()(x: Nat) := x` | PARSE | Nullary group must be final and cannot mix with explicit parameters. |
| PS0-N-BIND-03 | Assuming `def f()` inserts Unit | PARSE | No nullary-function sugar on ordinary def. |
| PS0-N-BIND-04 | `const f(x: Nat) := x` | PARSE | Const has no source telescope. |
| PS0-N-MOD-01 | `public import all M` | ENV/PARSE | Native header restriction: separate public import from all/private access. |
| PS0-N-MOD-02 | Import following an ordinary declaration | PARSE | Imports belong in the header. |
| PS0-N-MOD-03 | A runtime reference to a meta-only definition | ELAB | Native staging restriction. |
| PS0-N-MOD-04 | Leaking a private declaration in a prohibited public signature | ELAB/ENV | Native module visibility rule. |
| PS0-N-LEX-01 | Treating `/* ... */` as a Lean comment | LEX/PARSE | Not a comment delimiter; never evidence of a valid-trivia adjacency check. |
| PS0-N-DATA-01 | Negative inductive occurrence violating positivity | KERNEL/ELAB | Data declaration does not qualify merely by parsing. |
| PS0-N-DATA-02 | Missing/ill-typed dependent proof field | ELAB | Native dependent construction obligations. |
| PS0-N-PAT-01 | Using arbitrary function calls as inverse constructor patterns | ELAB | Pattern adapter does not execute arbitrary functions backwards. |
| PS0-N-PAT-02 | Using PS term-empty-call completion to supply a missing pattern field | ELAB/PARSE | PS Unit/default completion is not a pattern operation; native nonempty-pattern defaults remain native. |
| PS0-N-PAT-03 | `nomatch` on an inhabited ordinary type without impossible indices | ELAB | Empty elimination is unjustified. |
| PS0-N-REC-01 | Incompatible structural and decreasing hints | ELAB | Native termination-mode consistency. |
| PS0-N-REC-02 | Unproved termination of a required total recursive definition | ELAB/VC-PROOF | No partial fallback that hides an error. |
| PS0-N-REC-03 | A fixed-point body lacking required monotonicity/structure | ELAB/VC-PROOF | No arbitrary cyclic definition admission. |
| PS0-N-DO-01 | Assignment to a nonmutable ordinary local | ELAB | Mutation requires the native mutable context. |
| PS0-N-DO-02 | `break`/`continue` outside a valid surrounding loop | ELAB | Native control target is absent. |
| PS0-N-DO-03 | `do←` in an unsupported nonfinal argument context | ELAB | Forwarding syntax has placement requirements. |
| PS0-N-VC-01 | Reordered or repeated intrinsic contract clauses | PARSE | Fixed `given? requires? ensures?` ordering. |
| PS0-N-VC-02 | A bare postcondition without its required result binder | PARSE | Ensures uses the basic-function production. |
| PS0-N-VC-03 | `given target: Nat` as an intended typed logical binder | PARSE | Use `given (target: Nat)`. |
| PS0-N-VC-04 | A contract/assertion without the necessary registered WP environment | ENV/ELAB | No silent metadata-only fallback. |
| PS0-N-VC-05 | A required unproved spec/loop/erasure obligation | ELAB/VC-PROOF or ASSURANCE | Cannot qualify the stronger claim. |
| PS0-N-ASSURE-01 | Claiming a theorem depending on source/generated/imported sorry is completed | ASSURANCE | The hole remains in the relevant dependency closure. |
| PS0-N-ASSURE-02 | Hiding a native-computation or user axiom in an assumption-free claim | ASSURANCE | A tactic spelling does not remove generated assumptions. |
| PS0-N-ASSURE-03 | Calling a partial program total because it compiled | ASSURANCE | Compilation is not termination evidence. |
| PS0-N-ASSURE-04 | Dropping the effects of `erased x ← action` | ASSURANCE/semantic mismatch | Erased result is not erased execution. |
| PS0-N-ASSURE-05 | Treating extern/implemented_by typing as native correspondence proof | ASSURANCE | Implementation behavior is a separate obligation. |
| PS0-N-ASSURE-06 | Counting `.lean` pass-through as implemented `.ps` grammar | ASSURANCE/evidence error | Different source lanes. |
| PS0-N-EXT-01 | Rewriting native quotation tuple calls into PS multiple arguments | semantic mismatch | Preserve syntax-data argument partition. |
| PS0-N-EXT-02 | Falling back to unrestricted native parsing for malformed host terms | PARSE/semantic mismatch | No invisible grammar-contract change. |
| PS0-N-EXT-03 | Assuming a name alone registers an attribute/deriving/tactic handler | ENV | Actual compatible import/registration is required. |
| PS0-N-BOOT-01 | Repeating quotient/bootstrap initialization in an invalid environment | ENV/KERNEL | Full capability preserves native preconditions. |

**Oracle convention.** A single phase is an exact required classification; `PARSE or ELAB` and slash-separated alternatives denote an allowed set, not permission for an unrelated earlier error. `ELAB/VC-PROOF` is the named VC-proof subcategory of elaboration, not an either/or expression. A semantic mismatch is a comparison failure, and ASSURANCE is a claim-qualification failure; neither is an ordinary parsing phase. Unknown named arguments use ELAB because their validity depends on the resolved callable; duplicate-name detection may occur at PARSE or ELAB.

Some negative rows give a native diagnostic boundary rather than one compiler-specific error string. A concrete test must refine that boundary against the pinned parser/elaborator and record its actual expected message. Semantic-mismatch and assurance rows require checking output/claims; they are not all ordinary parse-error fixtures. No earlier-profile result is relabeled as a v1 test result.

## 14. Environment closure, source fidelity, and conformance meaning

### Effective language environment

A PS0 v1 module's environment includes resolved imports, source kinds, module visibility, compile-time staging, notation/precedence, parser categories, macros/elaborators, typeclass/coercion/deriving handlers, attributes, options, tactic/simplifier registries, initialization, and required runtime interfaces. The compiler version pin alone is not a complete environment identity. Newly imported or locally declared extensions change what subsequent source means.

The native pinned grammar is the baseline; PS-owned rules in this document specify the source differences. A finite command-token allowlist cannot define v1. Arbitrary API names are not admitted merely by appearing in prose, and an unavailable handler remains an environment error. The host term versus quoted/native category distinction is explicit (§0B, §9).

### Grammar and formatting invariants

| Invariant | Required preservation |
|---|---|
| Binder order | Dependencies and implicit/instance visibility do not change during comma-group lowering |
| Application tree | Tuple versus multiple arguments, mixed postfix/whitespace grouping, and Unit completion remain distinct |
| Source context | Call adjacency is checked in host application continuations, not binders/configuration/quoted payloads |
| Scope/staging | Module/public/private/meta imports and local/scoped registrations retain their actual lifetime |
| Proof statement | Section generalization, generated specs, and macro elaboration do not silently strengthen/weaken the asserted proposition |
| Pattern meaning | Constructor matching, motives, inaccessible patterns, and exhaustiveness are not replaced by arbitrary call evaluation |
| Control targets | Return/break/continue and forwarding do target the same native control scopes |
| Effects/erasure | Dropping verification-only results does not delete effectful actions |
| Runtime correspondence | Logical interfaces and external/unsafe/substituted code retain separate evidence accounting |
| Diagnostics | Error recovery supports editing but does not qualify a failed declaration |

Native syntax and PS-specific forms can both be formatted, but a formatter cannot fix invalid source through an unannounced meaning-changing transformation. A conversion tool can propose a source migration explicitly; that is not ordinary pretty-printing.

### What full source-capability conformance requires

A source-completeness claim must:

1. Pin and enumerate the physical production `.lean` files in the declared corpus, recording paths and content identities. Separately classify tests, examples, generated stage artifacts, and non-Lean files; do not inflate coverage with generated duplicates.
2. Resolve the exact imports/options and interleave parsing with elaboration as required by Lean's evolving grammar. Record encountered syntax kinds and relevant category, notation, attribute, deriving, macro, and elaborator registrations.
3. Distinguish actual source occurrences, quoted syntax data, macro-generated declarations, and forms present only in intentionally failing tests. Lexical searches are discovery aids, not evidence of grammatical use or acceptance.
4. Map each relevant native construct to its PS0 host form or explicit category-owned form, recording semantic and visibility differences. Ordinary `.lean` fallback cannot stand in for a missing `.ps` feature.
5. Validate the transformed module graph with the pinned Lean implementation, preserving statements, binder order, argument partition, assumptions, public/private exposure, stage availability, and the specified runtime observations.
6. Report every uncovered family/production, expected failure, unsupported platform prerequisite, and unexecuted case. Require exact source/compiler revisions and reproducible test results before claiming qualification.

Syntax-kind enumeration alone is insufficient: the same kind can encode multiple important alternatives, and arbitrary registered extensions are not bounded by the initial builtin kind set.

### Evidence status and limits

The feature register in Appendix A is a **requirement inventory**, not measured implementation coverage. Track specified, implemented, fixture-linked, executed-at-exact-commit, and qualified-for-the-stated-outcome separately. A source count, syntax-kind count, or successful `.lean` pass-through run is not a percentage of `.ps` implementation completeness.

This standalone R2 document incorporates a full-reference consistency revision and exact-pin source checks. The accompanying revision report records the passes and remaining evidence limits. It does not claim an executed census of every upstream file. Examples, candidate cases and Appendix D witnesses remain specifications unless a separate exact-commit execution receipt says otherwise; structural document validation is not PS0 compiler qualification.

The work is a language-reference revision. It does not change compiler code, previously selected source profiles, library approval policies, the logical foundation, or CI acceptance criteria. Self-hosting, native linking, IDE round trips, backend correctness, all-platform execution, and independently checked verified output require their own implementation and evidence.

## Appendix A. Source-to-feature review register

These **100 review families** preserve the full capability inventory of PS0 v1. They are not a finite exclusion list and are not test PASS records. Sources are pinned in Appendix C; internal section references point to complete descriptions within this document. A newly encountered pinned production/registration that does not fit a row is a coverage finding, not permission to omit it.

| ID | Required family | Source / semantic anchor |
|---|---|---|
| V1-001 | Unicode and escaped/hierarchical identifiers | L-TERM, L-CMD |
| V1-002 | Comments and documentation comments | L-TERM, L-CMD |
| V1-003 | Numeral, scientific, character, string and registered literals | L-TERM, L-INIT |
| V1-004 | Raw/interpolated strings and embedded expressions | [feature](#collection-indexing-array-literals-strings-and-interpolation), L-INIT, L-DO |
| V1-005 | Universes, `Sort`, `Type`, `Prop`, explicit level parameters | L-TERM, L-CMD |
| V1-006 | Explicit, implicit, strict implicit and instance binders | L-TERM, [feature](#explicit-implicit-strict-implicit-instance-and-interleaved-binders) |
| V1-007 | Dependent/interleaved binders and section generalization | L-CMD, [feature](#namespaces-sections-variables-open-and-export) |
| V1-008 | Default/automatic parameters and type-directed completion | [feature](#defaults-named-arguments-coefun-and-empty-invocation), L-DEFS |
| V1-009 | Pi types, lambdas and pattern lambdas | L-TERM |
| V1-010 | Classes, instances, coercions and overloaded operations | L-CMD, L-TERM |
| V1-011 | Modern/implicit PS modules and explicit native headers | L-MODULE, [feature](#source-kinds-module-headers-and-imports), §1 |
| V1-012 | `prelude` and bootstrap import suppression | L-MODULE, L-INIT |
| V1-013 | Public/private imports and re-export | L-MODULE |
| V1-014 | Meta imports and public meta availability | L-MODULE, L-CMD |
| V1-015 | `import all` and its invalid combinations | L-MODULE |
| V1-016 | Namespace/section/end and include/omit | L-CMD |
| V1-017 | Open/hiding/renaming/only/scoped and namespace export | L-CMD |
| V1-018 | Public/private/protected/expose and body visibility | L-CMD, L-DEFS |
| V1-019 | `meta`, `noncomputable`, `nonrec` and modifier legality | L-CMD |
| V1-020 | Definition, theorem, example and abbreviation declarations | L-CMD, L-DECL |
| V1-021 | `function`/`const` and required-Unit nullary lowering | [feature](#nullary-function-declarations-and-required-unit) |
| V1-022 | Opaque bodies and bodyless inhabitant synthesis | L-DEFS, L-DECL |
| V1-023 | Explicit axiom declarations and assumptions | L-CMD, L-DECL |
| V1-024 | Inductive types/families and generated eliminators | L-CMD, L-DECL |
| V1-025 | Mutual/nested inductives and positivity requirements | L-DECL, L-REF |
| V1-026 | Structures, inheritance, named parents and constructor specifications | L-CMD |
| V1-027 | Implicit/instance/proof/default fields and computed fields | L-CMD |
| V1-028 | Classes and class inductives | L-CMD |
| V1-029 | Trailing and standalone deriving | L-CMD |
| V1-030 | Custom deriving and generated-instance checking | L-LEAN, L-CMD |
| V1-031 | PS comma calls, tuple/Unit distinction and argument ownership | [feature](#calls-grouping-tuple-arguments-and-postfix-precedence), §2 |
| V1-032 | Native unparenthesized application and explicit `@` | L-TERM, [feature](#calls-grouping-tuple-arguments-and-postfix-precedence) |
| V1-033 | Named arguments, placeholders, ellipsis and partial application | L-TERM, [feature](#defaults-named-arguments-coefun-and-empty-invocation) |
| V1-034 | Field/numeric projections and generalized receiver insertion | L-TERM |
| V1-035 | Type ascription, expected-type control and anonymous constructors | L-TERM |
| V1-036 | Let/have, local instances and binding configurations | L-TERM |
| V1-037 | Native local-binding aliases and deprecation semantics | L-TERM |
| V1-038 | Records, updates, punning and field equations | L-TERM |
| V1-039 | Conditional terms and braced PS conditionals | L-INIT, [feature](#term-conditionals-named-condition-proofs-and-if-let) |
| V1-040 | Constructor, literal, successor and inaccessible patterns | L-TERM, [feature](#pattern-grammar-dependent-matching-and-empty-elimination) |
| V1-041 | Multi-discriminant/dependent match, motive and generalization | L-TERM |
| V1-042 | Pattern aliases and named match equations | L-TERM |
| V1-043 | `if let`, pattern bindings, `matches`, `nomatch`, `nofun` | L-TERM, [feature](#pattern-grammar-dependent-matching-and-empty-elimination) |
| V1-044 | Equation-style definitions and mutual function groups | L-CMD, L-PREDEF |
| V1-045 | Local recursion and complete where/finally facilities | L-TERM, L-PREDEF |
| V1-046 | Structural recursion and structural hints | L-PREDEF, L-TERM |
| V1-047 | Well-founded recursion, measures and decreasing proofs | L-PREDEF, L-TERM |
| V1-048 | Partial functions and opaque logical interfaces | L-PREDEF |
| V1-049 | Partial fixed points and monotonicity | L-TERM, L-PREDEF |
| V1-050 | Inductive/coinductive fixed points and predicate declarations | L-CMD, L-TERM |
| V1-051 | Braced/native layout and category-specific semicolons | L-CMD, L-DO, §1 |
| V1-052 | Generic do, monad operations and nested actions | L-DO |
| V1-053 | Mutable locals and pure/monadic reassignment | L-DO |
| V1-054 | Refutable let bindings and fallback control flow | L-DO |
| V1-055 | Do-if, monadic if-let and unless | L-DO |
| V1-056 | Single and zipped for iteration | L-DO |
| V1-057 | While, repeat and repeat-until | L-DO |
| V1-058 | Break, continue and early return | L-DO |
| V1-059 | Forwarding `do←` and wrapper control effects | L-DO |
| V1-060 | Typed/pattern catch, try/finally and term sugar | L-DO |
| V1-061 | Term proofs, by blocks and full goal-control syntax | L-TERM, L-TACTIC |
| V1-062 | Imported tactics, configuration and proof construction | L-INIT, L-STD, L-LEAN |
| V1-063 | Simplifiers, simprocs, conversion and registered proof tools | L-INIT, L-LEAN |
| V1-064 | Arithmetic/bitvector/grind and decision procedures | L-INIT, L-STD, L-DECIDE, L-NATIVE |
| V1-065 | Custom tactics and compile-time proof programs | L-SYNTAX, L-LEAN |
| V1-066 | Development holes and error-recovery separation | L-TERM, L-PREDEF |
| V1-067 | Ordered contracts and logical given binders | L-CMD, [feature](#given-requires-ensures-and-generated-specification-proofs) |
| V1-068 | Generated spec proofs and native finally subsections | L-TERM, [feature](#local-definitions-equation-bodies-and-wherefinally-tails) |
| V1-069 | Verification-only assert versus runtime assertions | L-DO |
| V1-070 | Loop invariants/decreasing annotations and WP facilities | L-DO, L-STD, [feature](#assertions-loop-invariants-and-decreasing-measures) |
| V1-071 | Erased state, erased mutation and effectful erased-result bindings | L-DO |
| V1-072 | Notation/mixfix, local/scoped precedence and priorities | L-SYNTAX |
| V1-073 | Syntax categories, syntax abbreviations and binder predicates | L-SYNTAX |
| V1-074 | Parser descriptors/combinators and leading/trailing parsers | L-SYNTAX, L-TERM |
| V1-075 | Macro declarations/rules and dispatch | L-SYNTAX |
| V1-076 | Quotations, antiquotations, splices, patterns and hygiene | L-TERM, L-CMD, L-SYNTAX |
| V1-077 | Native/PS category ownership and extension compatibility | L-MODULE, L-SYNTAX, §9 |
| V1-078 | Elab/elab_rules and term/command/tactic elaborators | L-SYNTAX, L-LEAN |
| V1-079 | Names, levels, Expr, Syntax and metaprogramming contexts | L-DECL, L-LEAN |
| V1-080 | Environment extensions, declarations and registration APIs | L-LEAN, L-DECL |
| V1-081 | Reduction, unification, metavariables and elaboration scheduling | L-TERM, L-PREDEF |
| V1-082 | Match_expr/let_expr and reflection/evaluation facilities | L-TERM, L-DO |
| V1-083 | Low-level percent-suffixed and diagnostic helper syntax | L-TERM |
| V1-084 | Attribute declaration/use/removal and custom handlers | L-CMD, L-LEAN |
| V1-085 | Reducibility hints versus elaborator transparency | L-DECL |
| V1-086 | Options/configuration, scoped settings and trace registration | L-CMD, L-PREDEF, L-DECIDE |
| V1-087 | Initialize/builtin_initialize and startup effects | L-CMD, L-SYNTAX |
| V1-088 | Primitive/data types, collections and indexed access | L-INIT, L-STD, [feature](#universes-dependent-functions-equality-quotients-and-core-data) |
| V1-089 | Standard effects, IO and system APIs | L-INIT, L-STD |
| V1-090 | References, StateRefT, tasks and synchronization | L-TERM, L-INIT, L-STD |
| V1-091 | Extern/export/implemented_by and borrowed ABI arguments | L-TERM, L-DECL |
| V1-092 | Unsafe declarations/expressions and runtime correspondence | L-TERM, L-PREDEF |
| V1-093 | Panic, unreachable, tracing and runtime debugging | L-TERM, L-DO |
| V1-094 | Check/eval/reduce/print and native diagnostic extension closure | L-CMD, L-INIT |
| V1-095 | Import assertions, recall, version and scope diagnostics | L-CMD |
| V1-096 | Documentation, Verso, tags, recommendations and error explanations | L-TERM, L-CMD |
| V1-097 | Quotient/parser/documentation bootstrap commands and internal scopes | L-CMD, L-SYNTAX |
| V1-098 | Pretty printers, editor/server and compiler-source library capabilities | L-LEAN |
| V1-099 | Lake DSL capability as an optional imported extension | L-LAKE |
| V1-100 | Open-ended pinned registration and production-source closure | §0, §14 |

## Appendix B. Reader glossary and syntax-context distinctions

| Term | Meaning in this reference |
|---|---|
| Surface syntax | The text and grammar a programmer writes, before elaboration |
| Lowering | A meaning-preserving translation of an owned PS spelling into the appropriate native Lean syntax/term/declaration form |
| Elaboration | Resolution of names, binders, overloads, implicit parameters, instances, expected types, and generated obligations |
| Kernel checking | Validation of the relevant logical declarations/terms under the stated environment and assumptions |
| Telescope | An ordered sequence of binders, where later types/defaults may depend on earlier binders |
| Definitional equality | Equality by the kernel's native computation/conversion rules, not arbitrary equality theorems |
| Propositional equality | Equality stated as a type/proposition and justified by evidence |
| Native category | A pinned Lean parser contract, used by ordinary Lean and explicitly owned embedded/quoted syntax |
| Host term | A `.ps` expression obeying the PS call/adjacency rules even inside ordinary proof/specification arguments |
| Registered extension | Syntax, notation, handler, tactic, deriving rule, attribute, or other environment facility supplied by a compatible import or earlier command |
| Quotation | A representation of syntax data; not an already evaluated host expression or a checked proof |
| Hygiene | Native handling of generated identifiers/scopes to avoid unintended capture; not a proof of functional correctness |
| Partial | A native opaque logical interface with a potentially nonterminating compiled recursive implementation |
| Partial fixed point | A native ordered fixed-point construction with its proof/monotonicity requirements and equation theorems |
| Noncomputable | A logically meaningful declaration that need not have an executable implementation |
| Unsafe | Native runtime-programming classification; not permission to use arbitrary untrusted terms as checked proofs |
| Exposed body | An implementation body available for appropriate imported elaboration/unfolding, distinct from public naming |
| Assumption closure | The relevant transitive assumptions of a claimed statement, including generated/imported ones |
| Erased state | Verification-only data with native erasure restrictions; an effectful computation producing it can still run |
| Verified claim | A statement qualified by its actual specification, effects, assumptions, termination property, erasure behavior, and covered execution layer |

**Six uses of parentheses that must not be conflated:** `(x: A)` in a binder introduces a variable; `(e)` in an initial term groups an expression; `(x,y)` is native tuple syntax; `f(x,y)` is a host PS multiple-argument call; `(motive := e)` in match syntax is a configuration production; a parenthesis inside a native quotation belongs to that quoted category. The grammar context, not a regular expression over spacing, decides its role.

## Appendix C. Pinned sources and optional historical provenance

The PS0-specific language rules are contained in this document. Upstream references identify the immutable semantic/category implementation being described; they are not an instruction to read a previous ProofScript edition. Where a source imports additional native modules, the actual compatible imported definitions/registrations retain their native visibility and stage requirements. Upstream copyright/license notices remain those of their source files.

**Optional history only.** This standalone edition replaces the PS0 v1 language reference at repository blob `6bb07effd0ac2f89e79f16c07ce5c1881e3f4cb5`, originally added at commit `732b1f354fdc25c839693d7462af3615b89fc536` in `dwijayuda/lean4`. Its paired presentation was modeled on the PSCV0 v7 reference. Neither predecessor supplies additional normative rules: all PS-owned decisions needed for this edition have been restated here. Historical edition differences are not compiler-conformance results.

[L-CMD]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Parser/Command.lean
[L-TERM]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Parser/Term.lean
[L-MODULE]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Parser/Module.lean
[L-DO]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Parser/Do.lean
[L-SYNTAX]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Parser/Syntax.lean
[L-TACTIC]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Parser/Tactic.lean
[L-DECL]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Declaration.lean
[L-PREDEF]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/PreDefinition/Main.lean
[L-INIT]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Init.lean
[L-STD]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Std.lean
[L-LEAN]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean.lean
[L-LAKE]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/lake/Lake/DSL.lean
[L-ELAB]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab.lean
[L-DECIDE]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Tactic/Decide.lean
[L-NATIVE]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Meta/Native.lean
[L-TERM-BASIC]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Parser/Term/Basic.lean
[L-INIT-TACTICS]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Init/Tactics.lean
[L-APP]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/App.lean
[L-QUOTE-ELAB]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Quotation.lean
[L-IMPORT]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Import.lean

[L-CONTRACT]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Tactic/Do/Contract.lean

[L-PARSER-BASIC]: https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Parser/Basic.lean
[L-REF]: https://lean-lang.org/doc/reference/4.35.0/
[L-DEFS]: https://lean-lang.org/doc/reference/4.35.0/Definitions/Definitions/
[L-RUNTIME]: https://lean-lang.org/doc/reference/4.35.0/Run-Time-Code/
[L-VALIDATE]: https://lean-lang.org/doc/reference/4.35.0/ValidatingProofs/

| Reference | Implementation/semantic anchor |
|---|---|
| [Command parser][L-CMD] | Declarations, modifier ordering, contracts, scopes, diagnostics, initialization, documentation, bootstrap |
| [Term parser][L-TERM] | Applications/binders, patterns, records, termination suffixes, quotations, low-level helpers, borrowed ABI syntax |
| [Module parser][L-MODULE] | Header parsing, public/meta/all checks, interleaved parsing/elaboration requirements |
| [Do parser][L-DO] | Mutation, loops, forwarding do, assertions, erased actions, exceptions and control |
| [Syntax parser][L-SYNTAX] | Syntax categories, notation, macros, elaborators, combinators and binder predicates |
| [Tactic parser][L-TACTIC] | Native tactic categories and tactic-match/sequence facilities |
| [Declaration representation][L-DECL] | Declaration kinds, safety, opacity, reducibility hints, typed foreign exports |
| [Recursive definition elaboration][L-PREDEF] | Recursive groups, termination hints, partial interfaces, fixed-point dispatch and error recovery |
| [Elaborator entry][L-ELAB] | Imported declaration, syntax, notation, deriving, diagnostic, configuration and proof elaborators |
| [Init entry][L-INIT] | Core notation, proofs, data, effects, system interfaces, meta facilities and task support |
| [Std entry][L-STD] | Standard data, WP/verification, synchronization, time, networking and tactics |
| [Lean entry][L-LEAN] | Compiler, parser, elaborator, environments, runtime, server and extension APIs |
| [Lake DSL entry][L-LAKE] | Optional imported package/dependency/target/script language extensions |
| [Decision tactic][L-DECIDE] | Native versus kernel/elaborator decision paths and tactic registration |
| [Native decision infrastructure][L-NATIVE] | Closed native evaluation and generated computation assumptions |
| [Pinned reference manual][L-REF] | Supporting native logical and language concepts |
| [Definitions manual][L-DEFS] | Definition transparency, opaque inhabitant synthesis and computability |
| [Runtime manual][L-RUNTIME] | Runtime representation and foreign execution conventions |
| [Proof-validation manual][L-VALIDATE] | Proof assumptions, native evaluation and the limits of checking claims |

## Appendix D. Concrete boundary witnesses and qualification oracles

The following isolated `.ps` modules make the repaired source boundaries testable. **Every case is NOT RUN in this document revision.** `accept` is a required design outcome, not an execution receipt. A future run must record compiler commit, this specification identity, source bytes, effective imports/options and actual messages/declarations. Setup must succeed before a later-stage negative result is counted. Missing `PS0.Syntax` or unavailable PS category support is **not** a successful negative test; it is unimplemented/unavailable prerequisite evidence.

For accepted theorem examples, require the actual checked statement and no relevant `sorryAx` or unsolved goals. For AST cases, inspect the specified category and argument partition rather than treating a `#check` message alone as sufficient. The old §13 rows remain an overview; these witnesses supplement, not replace, the production-source census required by §14. Tests that create a custom grammar must run in isolated environments so they cannot change unrelated cases.

### R2-01. Plain semicolon leaves the second goal

**Expected:** `ELAB`. **Execution status:** NOT RUN.

```proofscript
public import Init

example : True ∧ True := by { constructor; exact True.intro }
```

**Oracle:** One conjunct remains unsolved; a successful finished theorem is not permitted.

### R2-02. Two sequential tactics close two goals

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

example : True ∧ True := by {
  constructor
  exact True.intro
  exact True.intro
}
```

**Oracle:** Completed proof of True ∧ True, without sorryAx.

### R2-03. Distributing combinator closes both goals

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

example : True ∧ True := by { constructor <;> exact True.intro }
```

**Oracle:** Both generated goals close.

### R2-04. Empty and nonempty constructor adapters

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

function readOption(x: Option Nat): Nat := match x with {
  | none() => 0
  | some(n) => n
}
example : readOption(none) = 0 := rfl
example : readOption(some(7)) = 7 := rfl
```

**Oracle:** none() lowers to a bare constructor; no Unit insertion.

### R2-05. A Unit field is still a constructor field

**Expected:** `ELAB`. **Execution status:** NOT RUN.

```proofscript
public import Init

inductive K where { | mk(u: Unit) }
function bad(k: K): Nat := match k with { | K.mk() => 0 }
```

**Oracle:** Reject the empty adapter: K.mk has one explicit field.

### R2-06. Native defaults in a nonempty pattern adapter

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

inductive Packet where { | mk(n: Nat, flag: Bool := true) }
function readPacket(p: Packet): Nat := match p with {
  | Packet.mk(n) => n
  | Packet.mk(_, false) => 0
}
example : readPacket(Packet.mk(7, true)) = 7 := rfl
example : readPacket(Packet.mk(7, false)) = 0 := rfl
```

**Oracle:** K(n) keeps native default matching; explicit false reaches the second branch.

### R2-07. Defaulted fields do not qualify an empty pattern adapter

**Expected:** `ELAB`. **Execution status:** NOT RUN.

```proofscript
public import Init

inductive Defaulted where { | mk(flag: Bool := true) }
function bad(x: Defaulted): Nat := match x with { | Defaulted.mk() => 0 }
```

**Oracle:** Reject: there is an explicit field, even though it has a default.

### R2-08. Braced data tails and constructor names

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

inductive Shade where { | light | dark } deriving Repr, BEq
structure NamedPoint where {
  mk ::
  x: Nat
  y: Nat
} deriving Repr
#check NamedPoint.mk
#check (inferInstance : Repr Shade)
#check (inferInstance : Repr NamedPoint)
```

**Oracle:** Deriving attaches outside the constructor/field braces; mk is the constructor name.

### R2-09. Native operand ownership of a custom extension

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Lean
public meta import Lean

macro "echoNative " x:term : term => pure x
function sumPair(p: Nat × Nat): Nat := p.1 + p.2
const result: Nat := echoNative sumPair (2, 3)
example : result = 5 := rfl
```

**Oracle:** The extension explicitly consumes native term; its spaced tuple application has one argument.

### R2-10. Explicit host operand ownership of a custom extension

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Lean
public meta import Lean

macro "echoPS " x:psTerm : psTerm => pure x
function add(x: Nat, y: Nat): Nat := x + y
const result: Nat := echoPS add(2, 3)
example : result = 5 := rfl
```

**Oracle:** Raw host capture is returned in the same category and elaborates to the two-argument call.

### R2-11. A host operand cannot fall back to native tuple syntax

**Expected:** `PARSE`. **Execution status:** NOT RUN.

```proofscript
public import Lean
public meta import Lean

macro "echoPS " x:psTerm : psTerm => pure x
function sumPair(p: Nat × Nat): Nat := p.1 + p.2
const result: Nat := echoPS sumPair (2, 3)
```

**Oracle:** Reject the gap within the explicit psTerm operand; do not retry term.

### R2-12. Explicit syntax bridge from PS capture to native result

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Lean
public meta import Lean
public meta import PS0.Syntax

macro "psIdentity " x:psTerm : term => do {
  let y: Lean.TSyntax `term := ⟨← PS0.Syntax.lower(`psTerm, x.raw)⟩
  `(id $y)
}
function add(x: Nat, y: Nat): Nat := x + y
const result: Nat := psIdentity add(2, 3)
example : result = 5 := rfl
```

**Oracle:** After the specified PS0.Syntax API is implemented, explicit lowering preserves the argument list and this result is 5.

### R2-13. Quotation ownership is visible to syntax inspection

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Lean
public meta import Lean

def nativeQ : Lean.MacroM(Lean.TSyntax `term) := `(f (x, y))
def hostQ : Lean.MacroM(Lean.TSyntax `psTerm) := `(psTerm| f(x, y))
def hostTupleQ : Lean.MacroM(Lean.TSyntax `psTerm) := `(psTerm| f((x, y)))
```

**Oracle:** Inspect the generated syntax actions: nativeQ has one tuple argument; hostQ has two PS arguments; hostTupleQ has one tuple PS argument. This is an AST oracle, not a run-time assertion.

### R2-14. A competing parser cannot override a PS call

**Expected:** `ENV or PARSE`. **Execution status:** NOT RUN.

```proofscript
public import Lean
public meta import Lean

macro:1024 f:term:max "(" a:term "," b:term ")" : term => `($f $b $a)
function sub(a: Nat, b: Nat): Nat := a - b
const result: Nat := sub(7, 2)
```

**Oracle:** Detect the incompatible protected host-call span; do not select argument reversal at a higher native priority. The registration remains available in an explicitly native category.

### R2-15. Record punning and body wrapping differ before coercion

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

structure Box where { x: Nat }
instance : Coe Nat Box where { coe n := { x := n + 1 } }
const x: Nat := 0
const recordValue: Box := {x}
const wrappedValue: Box := { (x) }
example : recordValue.x = 0 := rfl
example : wrappedValue.x = 1 := rfl
```

**Oracle:** Record syntax wins the {x} overlap; explicit grouped wrapper invokes the coercion.

### R2-16. Malformed record cannot become a successful body wrapper

**Expected:** `PARSE`. **Execution status:** NOT RUN.

```proofscript
public import Init

structure Box where { x: Nat }
const bad: Box := { x := }
```

**Oracle:** The field-assignment commitment reports the missing value; no fallback.

### R2-17. A record inside a call in a marker-free loop header

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

structure Count where { n: Nat }
function make(c: Count): List Nat := [c.n]
def total: Nat := Id.run do {
  let mut n := 0
  for x in make({ n := 2 }) { n := n + x }
  return n
}
example : total = 2 := by { decide }
```

**Oracle:** Inner braces belong to make argument; the later braces own loop statements.

### R2-18. The same header boundary in if-let

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

structure Count where { n: Nat }
function probe(c: Count): Option Nat := some(c.n)
def result: Nat := if let some n := probe({ n := 2 }) { n } else { 0 }
example : result = 2 := rfl
```

**Oracle:** The record is an argument of probe, not the conditional body.

### R2-19. Native and comma binders compose in order

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

def mixed (x y : Nat) (z: Nat, w: Nat): Nat := x + y + z + w
example : mixed(1, 2, 3, 4) = 10 := rfl
function choose(n: Nat)[Decidable(n = 0)](x: Fin(n + 1)): Nat := x.val
#check choose
```

**Oracle:** mixed has four ordered explicit Nat binders; choose retains the intervening dependent instance.

### R2-20. Function alias keeps its existing telescope restriction

**Expected:** `PARSE`. **Execution status:** NOT RUN.

```proofscript
public import Init

function bad(x: Nat)(y: Nat): Nat := x + y
```

**Oracle:** No intervening nonexplicit binder: use one comma group or native def.

### R2-21. Default proof term versus automatic parameter syntax

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

def ordinaryDefault (h: True := (by { trivial })): True := h
def automatic (h: True := by { trivial }): True := h
#check ordinaryDefault()
#check automatic()
```

**Oracle:** Inspect binder annotations: ordinaryDefault is optParam, automatic is autoParam. Both calls close their respective permitted completions.

### R2-22. Local record-valued helper has explicit lowering

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

structure Point where { x: Nat; y: Nat }
function localPoint(n: Nat): Nat := helper(n).x
where {
  def helper(k: Nat): Point where { x := k; y := 0 }
}
example : localPoint(7) = 7 := rfl
```

**Oracle:** The helper becomes a native local let-rec declaration with a record RHS.

### R2-23. Nested local recursion remains expressible

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

function nested(n: Nat): Nat := helper(n)
where {
  def helper(k: Nat): Nat :=
    let rec inner (j : Nat) : Nat := j + 1
    inner(k)
}
example : nested(7) = 8 := rfl
```

**Oracle:** Nested helper capability uses native let rec in the RHS; no top-level helper-tail grammar is borrowed.

### R2-24. Duplicate named argument uses the allowed phase set

**Expected:** `PARSE or ELAB`. **Execution status:** NOT RUN.

```proofscript
public import Init

function one(n: Nat): Nat := n
#check one(n := 1, n := 2)
```

**Oracle:** Must diagnose duplicate n; a different earlier error does not satisfy this case.

### R2-25. Function-valued result preserves strict whole-Pi completion

**Expected:** `ELAB`. **Execution status:** NOT RUN.

```proofscript
public import Init

function makeAdder(): Nat → Nat := fun n => n + 1
#check makeAdder(())
#check makeAdder()
```

**Oracle:** First check is valid; the second fails because the full telescope still requires a Nat.

### R2-26. Two Unit binders are not an empty call

**Expected:** `ELAB`. **Execution status:** NOT RUN.

```proofscript
public import Init

function two(a: Unit, b: Unit): Nat := 0
#check two()
```

**Oracle:** Neither a declared-arity exception nor repeated Unit synthesis is allowed.

### R2-27. Named contract and proof-generation positive candidate

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Std.WP

function plusOne(n: Nat): Id Nat
  requires True
  ensures r => r = n + 1 := do { return n + 1 }
#check plusOne.spec
#print axioms plusOne.spec
```

**Oracle:** The pinned intrinsic macro must generate a completed checked plusOne.spec using its VC procedure. The name alone is not a PASS; inspect goals, messages and assumptions.

### R2-28. A false written contract cannot be ordinary completed output

**Expected:** `ELAB/VC-PROOF`. **Execution status:** NOT RUN.

```proofscript
public import Std.WP

function wrong(n: Nat): Id Nat
  requires True
  ensures r => r = n := do { return n + 1 }
```

**Oracle:** Generated contract theorem must fail; no sorry-dependent or metadata-only ordinary checked result.

### R2-29. Indexing can produce a callable postfix head

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

def fs: Array(Nat → Nat) := #[fun n => n + 1]
#check fs[0](2)
example : fs[0](2) = 3 := by { decide }
```

**Oracle:** Indexing is completed before the PS call; bounds checking and the native array semantics remain in force.

### R2-30. Explicit universe suffix can precede a PS call

**Expected:** `accept`. **Execution status:** NOT RUN.

```proofscript
public import Init

universe u
def identU {α : Type u} (x : α) : α := x
#check identU.{0}(2)
```

**Oracle:** Universe suffix remains a suffix of the constant; no separate callable or header block is created.

### R2-31. Real source gaps are not repaired by normalization

**Expected:** `PARSE`. **Execution status:** NOT RUN.

```proofscript
public import Init

function inc(n: Nat): Nat := n + 1
#check inc/-gap-/(2)
```

**Oracle:** The recorded source gap is rejected before standard lowering.

### Claim-classification witnesses (not source parser tests)

| Witness | Supplied facts | Required report |
|---|---|---|
| Q1 | Checked source theorem, explicit accepted policy, no artifact correspondence proof | Source-verified program with the trusted execution boundary named; never unqualified verified executable |
| Q2 | Same source plus an unproved `implemented_by`/foreign replacement | Source-only verification with that runtime replacement listed as unproved/assumed; no proved correspondence label |
| Q3 | Same source plus checked correspondence to a specifically identified IR/C/native artifact | Execution-correspondence-verified program at that exact layer, with remaining trusted components explicit |
| Q4 | Checked theorem with enumerated axioms but no supplied approval policy | Conditional checked theorem; policy approval not assessed |
| Q5 | Supplied policy excludes one actual axiom in that theorem's closure | Policy-qualified claim refused, without falsely declaring the conditional Lean theorem ill-typed |

A full-source-capability receipt also needs the complete pinned source/registration census and cross-module/bootstrap tests. Neither this finite witness set nor absence of new textual findings substitutes for those execution results.

**End of the standalone PS0 v1 language reference.**