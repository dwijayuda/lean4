# PS0 v1 Language Reference

## Lean-source-complete capabilities with the ProofScript surface

**Edition:** PS0 v1  
**Date:** 2026-10-15  
**Status:** normative **design target**, with a source-grounded research rationale; not a claim that the current PS0 compiler implements this edition.  
**Upstream semantic and syntax pin:** official Lean **4.35.0**, commit `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.  
**Predecessor:** PSCV0 language-reference revision **v7**, `dwijayuda/pskernel`, `psc0/PSCV0_LANGUAGE_REFERENCE.md`, commit `f79d334ef922eb7f71f7527dbc798ebb0dbeb610`, blob `25e1ef788794db175a2183679e37ff8c8e9b6a2e`.  
**PS0 implementation inspected:** `dwijayuda/lean4`, branch `feature/ps0-lean435-stable-v1`, commit `22f6078dbcfb6335390915c3c7ae9a3566ad0ce0`, folder `experiments/ps0`.

**Publication context:** the branch had advanced to `d2a2b541367bf59fde35218fd46d2aa55057e938` when rechecked before publication. The policy audit citations remain pinned to the inspected baseline above; this document does not infer new implementation results from the later commit.

> PS0 v1 retains ProofScript's useful `.ps` surface and adopts the Lean-language capabilities needed to express Lean's own implementation: ordinary programs, proofs, language extensions, elaborators, compiler code, runtime interfaces, and bootstrap declarations. It does not introduce a second type theory or kernel. Language admission, logical assumptions, executable availability, and verified-executable claims are separate questions.

This document creates a **new edition**. It does not rewrite PSCV0 v7, remove current compiler checks, change `.lean` processing, certify existing tests, or authorize additional assumptions in any existing verified-build policy. All unqualified “must” statements below are requirements on an implementation claiming **PS0 v1** conformance.

## Contents

1. [Scope, authority, and completeness](#1-scope-authority-and-completeness)
2. [What changes from PSCV0 v7](#2-what-changes-from-pscv0-v7)
3. [Source kinds, modules, and visibility](#3-source-kinds-modules-and-visibility)
4. [Lexical syntax, layout, and grammar ownership](#4-lexical-syntax-layout-and-grammar-ownership)
5. [Types, universes, binders, and elaboration](#5-types-universes-binders-and-elaboration)
6. [Declarations and data definitions](#6-declarations-and-data-definitions)
7. [Applications and expression forms](#7-applications-and-expression-forms)
8. [Patterns and dependent elimination](#8-patterns-and-dependent-elimination)
9. [Recursion, partiality, and fixed points](#9-recursion-partiality-and-fixed-points)
10. [Monadic programming and control flow](#10-monadic-programming-and-control-flow)
11. [Proofs, tactics, and proof automation](#11-proofs-tactics-and-proof-automation)
12. [Contracts, verification conditions, and erased state](#12-contracts-verification-conditions-and-erased-state)
13. [Notation, syntax extensions, and macros](#13-notation-syntax-extensions-and-macros)
14. [Elaborator and compiler metaprogramming](#14-elaborator-and-compiler-metaprogramming)
15. [Attributes, options, and initialization](#15-attributes-options-and-initialization)
16. [Libraries, runtime facilities, and foreign interfaces](#16-libraries-runtime-facilities-and-foreign-interfaces)
17. [Diagnostics, documentation, and bootstrap commands](#17-diagnostics-documentation-and-bootstrap-commands)
18. [Assumptions and assurance boundaries](#18-assumptions-and-assurance-boundaries)
19. [Examples and migration rules](#19-examples-and-migration-rules)
20. [Source-to-feature coverage register](#20-source-to-feature-coverage-register)
21. [Conformance requirements and evidence status](#21-conformance-requirements-and-evidence-status)
22. [Research findings and implementation consequences](#22-research-findings-and-implementation-consequences)
23. [Pinned sources](#23-pinned-sources)

## 1. Scope, authority, and completeness

### 1.1 Language identity

**PS0V1-CORE-01.** PS0 v1 is a Lean-backed programming and proving language with ProofScript surface forms. Every ordinary typed expression, declaration, and proof must have the meaning assigned by the pinned Lean elaborator and logical environment after the explicitly specified surface transformation. Compile-time programs, unsafe definitions, external implementations, and partial functions retain Lean's distinct treatment; they are not all reclassified as total, kernel-reducible functions.

The intended coverage includes the Lean source-language mechanisms used in `src/Init`, `src/Std`, `src/Lean`, and the Lean-written parts of `src/lake`. It includes mechanisms for defining new syntax and elaboration, not just syntax that an application consumes. Relevant upstream tests enlarge the conformance corpus but do not turn intentionally invalid test inputs into valid programs. [L-INIT] [L-STD] [L-LEAN] [L-LAKE]

C, C++, CMake, shell, Python, JavaScript, and other languages present in the repository remain **host implementation or tooling languages**. Their existence does not add C++ templates, C pointer syntax, JavaScript object semantics, or shell commands to PS0. Their interfaces are covered through Lean's runtime, foreign-function, and metaprogramming facilities. This specification does not require LLVM, Lake, npm, or any particular package manager merely because an upstream component uses one.

### 1.2 Normative closure, not a finite allowlist

**PS0V1-CLOSURE-01.** The admitted feature set is the closure of:

- the pinned Lean built-in language categories and their elaboration rules;
- syntax, notation, tactic, deriving, attribute, option, and elaborator registrations supplied by resolved imports;
- valid registrations introduced earlier in the same source module;
- the owned ProofScript surface rules in this reference.

The catalog in §20 is an audit register, **not an exclusion list**. An upstream feature omitted from that catalog is not thereby banned. A missing feature found in the pinned production sources is a coverage defect to record and implement, not grounds for narrowing the meaning of “source-complete.” Availability remains subject to its actual imports, scopes, stage, types, and upstream prerequisites.

This is **capability completeness**, not a promise that renaming every `.lean` file to `.ps` preserves its bytes or behavior. ProofScript's calls, default source-module convention, and some braced forms intentionally differ. Native `.lean` remains the byte-for-byte source-compatibility route. Supporting `.lean` pass-through alone does not establish `.ps` v1 implementation completeness.

### 1.3 Authority and conflict resolution

Use this order:

1. Explicit PS0 v1 decisions, particularly its source punctuation and assurance labels.
2. Pinned Lean grammar, elaborator, kernel, and registered-library semantics for inherited constructs.
3. PSCV0 v7 for retained ProofScript-specific rules not replaced here.
4. Examples and explanatory prose, which cannot override a rule.

The stable-pin amendment in the v7 source supersedes its historical RC3/RC4 references. Neither `master`, `latest`, nor a later release is normative for this edition. An observed conflict must produce a specification finding and a reproducible case; an implementation must not silently choose whichever interpretation is easier. [V7]

### 1.4 Evidence limitation

This reference was prepared by reading the pinned command, term, module, syntax-extension, `do`, and tactic parsers; declaration and recursive-definition machinery; library entry modules; PS0 policy code; and relevant v7 passages. This was a **targeted source audit**, not a completed parse/elaborate census of every source file. The examples and proposed conformance checks below were not run as PS0 v1 programs. The completeness rule above defines the target; §21 defines the evidence required to substantiate implementation coverage.

## 2. What changes from PSCV0 v7

The original v7 remains a deliberately selected profile. PS0 v1 removes that finite feature-selection boundary while preserving the distinction between ordinary programs and stronger verified claims.

| Area | PSCV0 v7 baseline | PS0 v1 decision |
|---|---|---|
| Logical foundation | Lean semantics with selected source features | Same Lean foundation; full relevant source capabilities |
| Source extension | `.ps` with owned punctuation | Retained; `.lean` remains genuine Lean |
| `function` / `const` | Definition aliases | Retained, including the required-`Unit` nullary function rule |
| Applications | Comma calls; native unparenthesized application; application-gap restriction | Retained for ordinary host `.ps` terms; category-owned syntax is handled explicitly (§4, §13) |
| Bodies and layout | Selected braced forms; many native layout forms excluded | Existing braced forms retained; native layout bodies and native separators also admitted where their grammar defines them |
| Modules | Selected modern imports; public names by default | Add explicit native module headers, `prelude`, meta imports, `import all`, exposure, and complete visibility rules |
| Declarations | Selected `def`, theorem, data, instance forms | Add full declaration forms, modifiers, standalone deriving, coinduction, and bootstrap declarations |
| `partial` / `unsafe` | Banned in ordinary `.ps` source | Admitted with Lean semantics; not automatically verified or total |
| `axiom` | Banned in ordinary `.ps` source | Admitted as an explicit assumption; no automatic approved-foundation status |
| Proof holes | Editor development only; not qualifying output | Development acceptance retained; holes never qualify as completed proofs or hole-free outputs |
| Metaprogramming | User syntax/macros/elaborators largely excluded | Full syntax, macros, elaborators, tactics, reflection, and environment extensions |
| Attributes / deriving | Small allowlists | All properly registered forms; semantics and execution effects retained |
| Loops | Selected `for`; constrained `while`; no repeat family | Native single/zipped iteration, while, repeat, repeat-until, forwarding `do`, and their proof annotations |
| Effects | Selected pure/reader/state/typed-error verification model | Full Lean runtime and effect libraries for ordinary code; stronger claims still need specifications |
| Diagnostics | Selected pure/total evaluation and commands | Native diagnostic, evaluation, documentation, and development facilities |
| Foreign code | Selected/deferred boundaries | Native `extern`, `export`, `implemented_by`, borrowed arguments, runtime APIs |
| Standard environment | Curated subset | Import-driven pinned environment; an import is not an assurance certificate |

These are **intentional edition changes**, not corrections claiming v7 always permitted the new forms. In particular, v7 negative tests for `partial`, standalone deriving, custom macros, native layout, or multiple `for` collections must not be relabeled as old-v7 successes. [V7] [P-GRAMMAR]

## 3. Source kinds, modules, and visibility

### 3.1 Source-kind boundary

**PS0V1-SOURCE-01.** `.lean` is processed by ordinary official Lean without PS0 source bans or injected PS0 syntax/policy registrations. Existing PS0 uses a separate official Lean process to preserve this property. A source-language certificate for `.ps` is not granted merely because an imported `.lean` module compiled. [P-BOUNDARY]

A future compiler must explicitly identify whether a `.ps` module selects PSCV0 v7 or PS0 v1. This reference does **not** assert that an edition-selection command or configuration field already exists. Until implemented and adopted, the current `.ps` route remains the existing selected-v7 implementation.

### 3.2 Module headers

**PS0V1-MODULE-01.** Headerless PS0 v1 `.ps` retains the v7 convention: an implicit modern Lean `module` with publicly named source declarations by default. A written **`module` header** is newly admitted and selects the pinned native module-default visibility instead. Thus translating an upstream modern module can preserve its explicit `public section` and private-by-default behavior without accidentally exporting all helpers.

This is a deliberate new distinction with no effect on old v7 files, which did not admit a written module header. The source module's syntax kind remains `.ps` in both cases: a written `module` does not disable ProofScript term rules.

| Source header | Module interpretation | Unmarked declaration visibility |
|---|---|---|
| `.ps`, no written `module` | Implicit modern module | Public-name v7 convention |
| `.ps`, written `module` | Explicit pinned modern module | Native Lean module default |
| `.lean`, written `module` | Unmodified modern Lean | Native Lean default |
| `.lean`, no written `module` | Unmodified legacy Lean handling | Native Lean legacy behavior |

Admit `prelude` in its native header position. It suppresses the implicit prelude; it does not synthesize missing foundational types. A bootstrap file cannot use `Unit`, `Nat`, `PS0` libraries, or a nullary-`function` lowering before the required declarations exist. Merely enabling the `.ps` parser must not inject a full `Init` or `Lean` import into a `prelude` module.

### 3.3 Import forms

Admit the pinned header forms: `import M`, `public import M`, `meta import M`, `public meta import M`, `import all M`, and valid combinations of meta and all permitted by Lean. Preserve header ordering and actual module-system restrictions. In particular, **`public import all M` is not valid**: public re-export and private/all access require separate imports as Lean specifies. Missing modules, unsupported artifact versions, and invalid visibility dependencies remain errors. [L-MODULE]

A `meta` import controls compile-time availability, not proof unsafety. Importing a library for ordinary execution does not necessarily make all its declarations available to downstream metaprograms. Preserve the distinction between a local `meta import` and `public meta import` needed by exported metaprograms. [L-CMD]

### 3.4 Names, scopes, and exposure

Admit namespaces, nested sections, named/unnamed `end`, `variable`, `universe`, `include`, `omit`, all native `open` forms, `open scoped`, namespace `export`, scoped `... in`, and `with_weak_namespace`.

Name lookup, protected names, aliases, local/scoped registrations, and section generalization follow Lean. A theorem's proof body must not silently add section variables to its public statement. Public names and exposed definition bodies are distinct. Admit `@[expose]` and section-level exposure with their pinned semantics; do not infer exposure from public naming. `abbrev` follows Lean's own transparency and exposure behavior rather than a blanket “all public bodies hidden” rule. [L-CMD] [L-DEFS]

## 4. Lexical syntax, layout, and grammar ownership

### 4.1 Lexical baseline

Use pinned Lean tokenization for Unicode identifiers, escaped identifiers such as `«name»`, hierarchical names, literals, punctuation, and comments. Preserve `--` comments, nested `/- ... -/` comments, declaration `/-- ... -/` documentation, and module `/-! ... -/` documentation. Do not add JavaScript comment or interpolation semantics by analogy.

Admit natural/scientific numeric literal syntax, characters, strings and escapes, raw strings, string interpolation, name literals, and registered literal notations. Interpretation is type-directed where Lean makes it so; `1` is not necessarily a `Nat`, and a scientific literal does not universally mean IEEE `Float`. Embedded expressions are parsed in the category specified by their notation. [L-TERM] [L-INIT]

### 4.2 Layout and separators

**PS0V1-LAYOUT-01.** V1 retains v7's braced declaration, proof, `match`, `do`, and control-flow sugar. It additionally admits native Lean layout alternatives and native semicolon uses. Semicolons are category-specific: a tactic combinator is not interchangeable with a `do` statement separator. Braces are not an unconditional indentation switch for every embedded language.

A declaration `:= { term }` contains one term; multiple imperative statements require a `do` term. Record instances and updates retain their distinct syntax nodes. The parser must not reinterpret a malformed record as a successful generic braced body, or a malformed `do` statement as an unrelated expression just to continue.

### 4.3 Category ownership

**PS0V1-GRAMMAR-01.** Native Lean grammar categories are the model; this document does not invent an independent universal EBNF. Its grammar descriptions are schemata. Actual registered parser combinators and the owned PS0 delta determine acceptance.

The ordinary `.ps` host-term application rules apply to executable terms, propositions, contracts, and normal proof-term arguments. Quoted syntax is **syntax data**, not an already executing host term. A registered embedded language may own its delimiters and category productions. Its literal tokens and native-category quotations must not be rewritten with a text-level “replace calls/braces” pass. The concrete grammar context must be known before applying a ProofScript transformation.

For new extension syntax, each embedded term position must identify whether it consumes the PS0 host term or a native/extension-owned category. There must be no “try restricted parsing, then silently retry unrestricted Lean” rule. Existing native extension definitions keep their registered grammar contract; a PS0 adapter or explicitly PS0-specific category is needed where a different surface is intended. This is an explicit v1 extension boundary, not a way to bypass the v7 source gate.

These requirements are important because Lean's grammar changes after imports and elaborated declarations. The pinned module parser expressly notes that most Lean files cannot be parsed without elaboration. [L-MODULE] [L-SYNTAX]

## 5. Types, universes, binders, and elaboration

### 5.1 Logical types

Admit `Sort u`, `Prop`, `Type u`, universe variables and explicit universe application, dependent function types, polymorphism, inductive families, dependent records, equality and heterogeneous equality, propositions, and quotient facilities with their pinned semantics. `Prop = Sort 0` and `Type u = Sort (u + 1)` retain their Lean meaning. Proof irrelevance and restrictions on eliminating propositions are not relaxed.

Products, sums, dependent pairs, `Subtype`, `Fin`, `Option`, `Except`, and collection types are Lean declarations and notation, not additional kernel constructs. Refinement-style programming uses propositions, subtypes, indexed types, and proof fields. This edition adds no separate `refine type`, `ghost`, or automatic structure-invariant language. [L-TERM] [L-DECL]

### 5.2 Binder forms

Admit explicit `(x : A)`, implicit `{x : A}`, strict implicit `⦃x : A⦄` and its native alternatives, instance `[C α]`, named instance, dependent/interleaved, default, and automatic proof parameters wherever Lean admits them. Preserve binding order and dependency; never group all implicit parameters at the front as a convenience transformation.

ProofScript comma-separated explicit binder groups are retained. Empty binder-group sugar belongs only to the specified nullary `function` form. It does not turn an empty `def`, theorem, constructor, or instance binder group into an implicit runtime argument. Native binders containing spaces before `(` are not application-gap errors. [V7] [L-TERM]

### 5.3 Inference and elaboration behavior

Use pinned Lean expected-type propagation, universe inference, implicit insertion, typeclass search, coercions, overloaded notation, default arguments, metavariable assignment, and postponed elaboration. Admit `@`, named arguments, placeholders, `..` where defined, type ascription including `(e :)`, `inferInstance`, and `inferInstanceAs` with its actual wrapping/transparency behavior.

`autoImplicit`, transparency, instance priorities, and other elaboration options retain registered semantics. Do not promise a new globally deterministic overload-selection algorithm inconsistent with Lean. Record the effective environment when reproducibility matters. Unresolved metavariables, error-recovery terms, and successful parsing alone do not qualify a declaration as checked and complete. [L-TERM] [L-PREDEF]

## 6. Declarations and data definitions

### 6.1 Definition families

Admit `def`, `abbrev`, `opaque`, `theorem`, `example`, `axiom`, `instance`, and the ProofScript aliases `function` and `const`. Admit simple right-hand sides, definitions by equations, structure-value `where` forms, local `where` declarations, local recursion, and mutual declaration blocks according to the underlying declaration family.

`function` is a `def` alias, not a JavaScript procedure. `const` is a parameterless `def` alias, not a distinct runtime storage class. Retain their v7 restrictions on where those aliases make sense. Contracts continue to attach only to the declaration forms supported by the pinned intrinsic contract mechanism and its `function` lowering.

### 6.2 Modifiers

Admit native visibility, `protected`, `meta`, `noncomputable`, `unsafe`, `partial`, and `nonrec`, as applicable. **The set is not freely compositional.** The command parser orders modifiers and has alternatives such as `meta` versus `noncomputable`, and `partial` versus `nonrec`; the elaborator applies additional legality checks. Preserve those constraints instead of accepting arbitrary modifier permutations. [L-CMD]

`meta` is a staging/module-availability distinction, not an alias for `unsafe`. `noncomputable` permits logical definitions that need not have executable code; it does not provide an executable implementation. `nonrec` controls the declaration's recursive/name-resolution interpretation, not its proof status.

### 6.3 Opaque declarations and assumptions

**PS0V1-OPAQUE-01.** Admit both a checked-body `opaque` and the native body-omission form. A bodyless `opaque` is **not automatically an axiom**. Lean attempts to supply an inhabitant, including through its `Inhabited`/`Nonempty` machinery, under the actual elaborator and compilation constraints. If the prerequisites fail, the declaration fails. Its opaque logical value, available executable implementation, and any external implementation must not be conflated. [L-DEFS]

`axiom` separately introduces an assumption with a well-formed type. Allowing its syntax does not prove that assumption, establish consistency of an arbitrary axiom set, or add it to an existing verified-build foundation. An imported theorem's assumption closure must remain visible in any claim about it.

### 6.4 Inductive and structure families

Admit inductive types and indexed families, nested/mutual inductives, constructor arguments and result indices, structures, classes, `class inductive`, inheritance and named parents, constructor-name specifications, field defaults, implicit/instance/proof fields, and native field declaration forms.

Admit computed fields and the native coinductive predicate declaration forms, including monotonicity proof clauses where supported. Coinductive/lattice constructions must retain their elaboration into the pinned logical foundations; this edition does not add an unchecked coinductive kernel primitive. Positivity, universe, index, eliminator, and monotonicity conditions remain Lean's. [L-CMD] [L-DECL] [L-PREDEF]

### 6.5 Deriving

Admit native trailing deriving where supported, standalone `deriving instance`, `deriving noncomputable instance`, and registered custom deriving handlers. Do not restrict the language to v7's five deriving classes. Requested classes still need valid handlers, imports, and instance prerequisites. Generated declarations and executable handler effects remain subject to the appropriate checks; deriving a class is not a blanket semantic-law proof.

## 7. Applications and expression forms

### 7.1 Preserved ProofScript call rules

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

Comments between a completed application head and `(` count as a gap; comments inside an adjacent call do not. This remains a syntax-tree/category rule, not an identifier-space-parenthesis regular expression. Native quotations and explicitly owned embedded categories follow §4 and §13. Ordinary `.lean` keeps all native application spellings.

**PS0V1-APP-02.** Empty invocation first establishes a callable Pi/`CoeFun` head. Perform Lean's permitted implicit, instance, default, and automatic-parameter completion. Accept only if no required explicit binder remains, or exactly one remains whose instantiated type is definitionally `Unit`; insert `()` only in the latter case. Do not guess `Unit` for an unsolved type, synthesize arbitrary `Inhabited` values, accept a non-callable value, or silently fill two required `Unit` arguments.

`function f(): R := body` introduces a **required** `Unit` binder, so `f : Unit → R`. It is not parameterless `def f : R`. Nonempty partial application remains ordinary Lean partial application.

**PS0V1-APP-03.** Postfix calls bind to their immediate atomic/postfix head before surrounding whitespace application: `f g(x, y)` means `f (g x y)`, whereas `(f g)(x, y)` means `(f g) x y`. Preserve named-argument rules, explicit universes, dependent binder instantiation, and the argument tree in formatting. [V7]

### 7.2 General expressions

Admit native lambdas and pattern lambdas, dependent arrows, `forall`/`∀`, `exists`/`∃` notation, named and anonymous constructors, tuple notation, field projections and numeric projections, generalized field notation, pipeline forms, operators, type ascriptions, local definitions, proof expressions, and registered term notations.

Generalized field notation performs type-directed receiver insertion; it is not prototype lookup or universally first-argument method invocation. `e.f`, `e.1`, and a dotted declaration name must be resolved as Lean resolves them. Admit explicit universe suffixes on the forms allowed by the parser. [L-TERM]

Retain native `if ... then ... else ...` and the ProofScript braced conditional. Both use the intended Lean conditional elaboration; a Boolean condition must not silently select a different `bif` semantics. Native `bif` remains available as its own registered notation.

### 7.3 Local bindings and records

Admit `let`, `have`, pattern/equation bindings, `let rec`, `letI`, `haveI`, native local-binding configuration such as `+nondep`, `+postponeValue`, `+usedOnly`, `+zeta`, `+generalize`, and `(eq := h)`. Deprecated but still supported forms such as `let_fun`/`let_λ`, `let_delayed`, and `let_tmp` retain their pinned availability and warnings.

Admit record construction, field punning, typed instances, field methods/equations, inherited fields, and native update forms including supported multiple sources. These are typed Lean operations, not mutable JavaScript objects or unrestricted spread. Tuple and anonymous-constructor notation preserve their dependent/type-directed behavior.

## 8. Patterns and dependent elimination

Admit constructor and qualified/leading-dot patterns, literals where supported, variables, wildcards, aliases `x@p` and native equality-binding variants, inaccessible patterns `.(e)`, multiple discriminants, alternatives sharing a right-hand side, and dependent matches with named equations, motive, and generalization controls.

Retain Lean `Nat` successor-pattern sugar such as `n + 1` and `n + 2`; this does not admit arbitrary arithmetic expressions as invertible patterns. Constructor comma-call sugar in PS0 is only a surface transformation of the corresponding constructor application, not a different matching algorithm. [V7] [L-TERM]

Admit pattern `let`, `if let`, `matches`, `nomatch`, `nofun`, pattern lambdas, equation-style functions, and the corresponding native `do` forms. Preserve exhaustiveness, inaccessible-index checks, elimination restrictions, and binder scopes. `nomatch` must be justified by impossible constructors/indices, not by an unchecked “unreachable” assertion.

`match_expr` and `let_expr` inspect metaprogramming expressions with the native special matching protocol. Syntax-quotation patterns match syntax, not runtime algebraic values. They must not be reduced to the ordinary constructor-pattern grammar or assumed to compare every raw token: the pinned quotation matcher has particular treatment of syntax atoms and identifiers. [L-TERM]

## 9. Recursion, partiality, and fixed points

### 9.1 Total definitions

Admit structural and well-founded recursion, inferred termination, explicit `termination_by`, `termination_by structural`, `termination_by?`, and `decreasing_by`; include mutual and local recursive definitions. Preserve strongly connected recursive groups, fixed parameters, generated equations/induction principles, and termination-hint compatibility.

A total declaration must satisfy Lean's requirements. The kernel does not gain a new arbitrary recursive-definition constructor just because a frontend accepts recursive surface syntax. The pinned elaborator constructs admissible definitions through the appropriate recursors/fixed-point facilities. [L-DECL] [L-PREDEF]

### 9.2 `partial`

**PS0V1-PARTIAL-01.** Admit `partial` functions and native compatible mutual groups. Lean supplies an opaque logical interface using an inhabitant and separately compiles the recursive program. Do not expose the implementation's arbitrary recursive equations as definitional equality, or infer a termination proof from successful compilation. The result-type and function-shape requirements remain those of Lean. [L-PREDEF]

An ordinary PS0 native program may contain partial computation. A claim of total executable correctness must separately establish the required termination and implementation correspondence; source typing alone cannot do so.

### 9.3 `partial_fixpoint`

Admit `partial_fixpoint` and its explicit monotonicity proof form. It uses the pinned ordered/fixed-point infrastructure, including the applicable completeness and monotonicity requirements, and supplies checked equation theorems. These equations do not say every execution terminates. It is not synonymous with `partial`, and neither keyword grants a proof hole. [L-TERM] [L-PREDEF]

### 9.4 Lattice-based inductive and coinductive definitions

Admit `inductive_fixpoint`, `coinductive_fixpoint`, coinductive predicate declarations, and applicable `monotonicity_by` forms. Preserve least versus greatest fixed-point meaning and native monotonicity checking. These forms are not a license for arbitrary cyclic values or an unproved productivity rule.

Do not combine incompatible termination and fixed-point suffixes. Native parser acceptance of a suffix is not sufficient when elaboration rejects its combination with the declaration or mutual group.

## 10. Monadic programming and control flow

### 10.1 Effects and sequencing

Admit generic Lean monads and transformers, `Id`, reader/state/error computations, `ST`, `BaseIO`, `EIO`, `IO`, tasks, and other imported effect facilities. `do` elaborates through the actual monad/control classes and return type. An arbitrary monad need not have the verification rules required by §12.

Admit braced and native-layout `do`, local `let`/`have`, local recursion, pure and monadic pattern bindings, fallback branches for refutable bindings, nested actions `←`, `let mut`, assignments including supported destructuring/monadic reassignment, and nested `do`. Preserve evaluation order, lexical mutable-variable scope, and native control-flow elaboration. [L-DO]

### 10.2 Conditionals and loops

Admit proposition/Boolean conditionals, named condition proofs, `if let` with `:=` **and monadic `←`**, optional `else` in `do`, `else if`, and `unless`.

Admit single-source `for`, dependent membership/proof binders where provided, and zipped `for x in xs, y in ys` iteration. The zipped form progresses in parallel and stops when an input is exhausted according to the pinned `ForIn`/stream mechanism; it is not nested Cartesian-product iteration.

Admit `while`, `repeat`, and `repeat ... until`, together with `break` and `continue`. Native optional invariant and decreasing clauses remain optional for **ordinary** program admission. Do not impose v7's source-level mandatory-annotation restriction on every v1 loop. Conversely, omitting the annotation does not discharge termination or correctness obligations for a stronger claim. [L-DO]

### 10.3 Control forwarding and exceptions

Admit `return` with native early-exit meaning, including its native term forms and omitted result where permitted. Loop/body `do` delimiters do not necessarily introduce a fresh return target.

Admit **`do←` / `do<-`**, including supported wrapper-lambda forms. It forwards control-flow effects to the surrounding `do` context under the pinned final-argument/statement restrictions. It is not equivalent to an eagerly evaluated nested action `(← action)`, and a generic comma-call lowering must preserve its recognized application shape.

Admit `throw`, `try`, multiple typed/pattern `catch` forms, and `finally` through the relevant effect classes. Preserve exception types, cleanup semantics, and control flow rather than substituting JavaScript or C++ exceptions. Native standalone `for`, `unless`, `try`, and `return` term sugar is also admitted. [L-DO]

## 11. Proofs, tactics, and proof automation

Admit term proofs and the full pinned, imported tactic environment. This includes `by`, exact/application/refinement and introductions, local facts, cases/induction, rewriting, simplification, congruence, conversion, equality calculation, contradiction, decision procedures, arithmetic/bitvector automation, verification-condition tactics, and registered custom tactics. No fixed tactic-name allowlist defines v1.

Retain native goal bullets, case labels, `case`, `next`, focusing, tactic sequencing and alternatives, tactic `match`, local option/namespace changes, configuration syntax, locations, and native indentation/braces. The ASCII goal-bullet alias is newly admitted where Lean defines it; its acceptance is separate from the dot-placeholder lambda syntax. [L-TACTIC] [L-INIT] [L-STD]

Available families include the imported `simp`/`dsimp`/`simpa`, `rw`, `conv`, `calc`, `omega`, `grind`, `decide`, `bv_decide`, `vcgen`, `mvcgen`, and native supporting tactics/notations. This list does not claim all are available from every minimal import. Simprocs, simplifier extensions, theorem registries, tactic extensions, and user proof-producing programs are included through registration closure.

**PS0V1-PROOF-01.** A tactic is a program that attempts to construct evidence. Its name, successful execution, or source annotation is not proof authority. Completed logical claims require the appropriate final declaration/term check and an explicit assumption interpretation. Custom metaprograms may also execute effects while building those terms.

`decide`-style proof construction and native-evaluation-assisted proof construction have different trust consequences. Under this Lean pin, `native_decide` is registered by `Lean.Elab.Tactic.Decide`; `decide +native` also uses its native path. `Lean.Meta.nativeEqTrue` compiles and evaluates a closed Boolean expression, then adds an axiom asserting equality to `true` on success. Native-assisted decision facilities must retain these generated assumptions in their assurance accounting. Do not describe the removed historical `Lean.trustCompiler` mechanism as the current 4.35 mechanism. [L-DECIDE] [L-NATIVE] [L-VALIDATE]

`_`, `?name`, `sorry`, and admitted proof-development forms may support an incomplete editor state. They do not become completed evidence through error recovery, macro expansion, or importing a file with warnings. See §18.

## 12. Contracts, verification conditions, and erased state

### 12.1 Intrinsic contracts

Retain `given? requires? ensures?` in that exact order, at most once each, on the eligible `def`/`function` declarations. `given` introduces specification-only binders; `requires` accepts its pinned term/predicate form; `ensures` requires its result-binding form. These are not ignored comments or runtime parameter additions. [V7] [L-CMD]

Their elaboration requires the pinned verification environment, including `Std.WP.Triple` for intrinsic contracts and the relevant assertion gadgets/registrations. Importing a type named `Triple` from an unrelated library is not equivalent. Generated specifications such as `f.spec` must have the appropriate names, universes, visibility, and checked proofs.

Admit the **full native `where ... finally` mechanism**, including named subsections for the holes it supports, not only the v7 selected `spec` tail. Retain the v7 braced `where { ... finally { | spec => { ... } } }` surface. Do not invent an additional `verify target :=` command as a supposed Lean feature. [L-TERM]

### 12.2 Assertions and loop annotations

Keep these operations distinct:

| Form | Meaning |
|---|---|
| `assert P` / predicate-binder form | Verification annotation/gadget read by the verification mechanism; no corresponding runtime test is implied |
| `assert! condition` | Native runtime assertion behavior, including panic behavior on failure |
| `debug_assert! condition` | Native runtime assertion conditional on the debug-assertion configuration |

Merely writing `assert P` does not mean `P` has already been proved. Required verification conditions must be generated and closed for the claimed program/specification.

For-loop invariants use the native consumed-prefix/remaining-suffix binder convention; while/repeat invariants use the native exit-state convention. Additional binders represent the assertion's state arguments where applicable. `decreasing` uses the actual loop-state measure semantics, not a text-level requirement that a variable's spelling become smaller. [L-DO]

### 12.3 Erased state

Admit `erased`, `erased mut`, pure erased definitions, erased monadic bindings, and supported updates. Erased information must not improperly determine runtime-relevant results.

**Crucially, `erased x ← action` still runs `action`; it hides its result in verification-only state.** It is incorrect to erase the entire effectful computation merely because the binder is erased. Erasure correctness and effect preservation remain separate obligations. [L-DO]

### 12.4 Scope of a verified claim

Verification applies to a stated specification and effect model. It must account for coverage, exceptional exits, iterator laws, mutable state, logical assumptions, erased data, and any foreign/runtime dependencies relevant to that statement. Syntax acceptance, a generated theorem name, or the presence of loop annotations is insufficient.

The earlier non-native `reads`, `modifies`, and `errors` clause proposals are not silently added as Lean syntax by this edition. An imported extension can define additional specification languages under §13, but their meaning and evidence are then owned by that extension.

## 13. Notation, syntax extensions, and macros

### 13.1 Full extension vocabulary

Admit `notation`, `prefix`, `postfix`, `infix`, `infixl`, `infixr`, local/scoped variants, explicit names and priorities, precedence declarations/expressions, `syntax`, syntax abbreviations, `declare_syntax_cat`, and `binder_predicate`.

Admit grammar descriptors and registered combinators: category references, grouping, alternatives, repetition, optional fragments, separated lists, trailing-separator policies, reserved/nonreserved token distinctions, Unicode/ASCII alternatives, and formatting/parenthesization annotations. Admit native `leading_parser` and `trailing_parser` programming and registration hooks used by Lean's own parser. [L-SYNTAX] [L-TERM]

### 13.2 Macros and quotations

Admit `macro`, `macro_rules`, native kind/priority/scoping options, syntax quotation, typed category quotation, command sequences, tactic quotations, prechecked quotations, antiquotation, optional/repeated splices, and quotation patterns. Preserve syntax kinds, source information, identifier resolution, macro scopes, and hygiene.

A plain name literal and a resolved double-quoted name literal are not interchangeable. A `Syntax` tree is not the same as an elaborated `Expr`, and quoted text is not already a proof term. Preserve these distinctions in APIs and examples. [L-TERM] [L-CMD]

**PS0V1-QUOTE-01.** Native Lean-category quotation payloads retain the native grammar contract used by upstream metaprograms. In particular, a native quoted `f (x, y)` denotes the native one-tuple application syntax, not a PS0 two-argument comma call. A quotation intended to construct PS0-owned syntax must explicitly use the appropriate PS0-specific category/quotation facility when that facility is provided. This specification does not claim such a facility is already implemented.

Do not globally rename Lean's native syntax kinds to PS0 names or rewrite string tokens in syntax declarations. An extension may deliberately treat its captured input as syntax data. The host application rules must not be applied blindly inside that data. A port that changes source punctuation must also review any macro that inspects those concrete syntax shapes.

### 13.3 Extension semantics and compatibility

Imported syntax and earlier commands affect later parsing. Preserve parser precedence, ambiguity handling, scoped activation, macro dispatch, expansion errors, and generated declarations. A generic finite pre-elaboration token ban is not a conforming v1 extension mechanism.

Native extensions can require explicit adapters at host-language boundaries. Such an adapter must preserve the declared category contract and document where PS0 syntax is accepted. It must not silently reinterpret a native tuple application as multiple arguments, or erase source provenance needed by diagnostics and macro behavior.

## 14. Elaborator and compiler metaprogramming

Admit `elab`, `elab_rules`, term/command/tactic elaborator registrations, declaration-specific elaborators, registered deriving handlers, coercion/elaboration extensions, and the native expected-type/configuration mechanisms. Preserve `MacroM`, command and term elaboration contexts, `MetaM`, core contexts, tactic state, and their actual effect/staging requirements.

The language must be able to express and use the upstream APIs for:

- names, levels, expressions, syntax trees, source spans, messages, and typed syntax;
- local contexts, metavariables, substitutions, unification, reduction, instance synthesis, and proof construction;
- declarations, environments, persistent/scoped environment extensions, imports, options, attributes, and registrations;
- pretty printers, parenthesizers, formatters, delaborators, documentation, editor information, and diagnostic extensions;
- compiler intermediate representations and passes, runtime interfaces, server tasks, serialization, and related Lean-written infrastructure.

These are **library capabilities**, not a promise that every API is safe, pure, public, or available from every import. Respect the distinction between elaborating an object-language term, evaluating a metaprogram, and publishing a logical declaration. `meta` availability must be preserved transitively. [L-LEAN] [L-CMD] [L-DECL]

Admit native reflection/evaluation helpers, `run_cmd`, `run_tac`, and equivalent registered facilities when actually available. Reading environment state, compiling code, or constructing a declaration does not automatically make it admissible as a completed checked proof. Strong assurance must consider the final statement, declaration dependencies, and checks performed, not just the visible tactic script.

### 14.1 Low-level term facilities used by Lean

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

## 15. Attributes, options, and initialization

### 15.1 Attributes

Admit declaration attribute lists, the `attribute` command including erasure, local/scoped attributes, custom attribute registration, and all applicable imported attributes. This includes instance, simplification, reducibility, exposure, compiler optimization, foreign interface, parser/elaborator, formatter, and documentation attributes.

Examples include `simp`, `instance`, `default_instance`, `reducible`, `irreducible`, `expose`, `inline`, `specialize`, `extern`, `export`, `implemented_by`, and the builtin parser hooks. The existence of a spelling in this table does not waive its target-kind or import requirements. Attribute handlers may execute code and produce declarations; they are not necessarily passive metadata. [L-CMD] [L-DECL]

Kernel reducibility hints and elaborator reducibility attributes must not be conflated. In the pinned declaration representation, hints guide the kernel's unfolding strategy; they are not identical to user transparency attributes, nor is a reducibility-hint constructor named `opaque` identical to an `opaque` declaration. [L-DECL]

### 15.2 Options and configuration

Admit `set_option` with registered values and scoped command/term/tactic forms, option registrations, trace-class registrations, configuration-elaborator declarations such as `declare_config_elab`, and native configuration items such as `+option`, `-option`, and `(option := value)`. Configuration evaluation must preserve the declared schema, expected types, defaults, and stage requirements. [L-DECIDE] [L-ELAB] Admit `unlock_limits` in the language with its native meaning; an external execution budget may still stop computation.

An option that changes checking or evaluation must be reflected in the evidence for a stronger claim. A language-level permission to use `set_option` is not permission to present an unchecked environment as independently kernel-checked.

### 15.3 Initialization

Admit `initialize` and `builtin_initialize`, including named initialized objects and native effectful bodies. Preserve their distinct startup/registration timing and module behavior. Environment extensions, parser tables, option/attribute registries, and mutable runtime state used by Lean depend on these facilities.

Do not erase an initializer because its exported value appears unused, or treat initialization as a pure theorem declaration. Reproducible/verified claims must account for the relevant initialization effects and environment identity. [L-CMD] [L-SYNTAX]

## 16. Libraries, runtime facilities, and foreign interfaces

### 16.1 Standard and compiler libraries

Replace v7's language-level curated API boundary with import-driven availability. The target includes the relevant exported and legitimately accessible facilities of the pinned `Init`, `Std`, `Lean`, and optional `Lake` libraries. A full root import is not mandatory for every module, and private/internal APIs retain their real visibility.

Required capability families include arbitrary-precision naturals/integers; fixed-width signed/unsigned integers and machine sizes; floating point; Boolean and character/string operations; lists, arrays, byte arrays, vectors, ranges, maps, sets, dependent containers, iterators, parsers, JSON/serialization, state/error transformers, runtime/system IO, synchronization, time/network facilities, tasks, and the compiler/metaprogramming types in §14. A type family is not necessarily a kernel primitive or part of every minimal prelude. [L-INIT] [L-STD] [L-LEAN]

Preserve the exact pinned type and operation semantics, including bounds proofs, optional and panic-indexing variants, numeric conversions, string positions/encoding, and target-dependent machine representations. `xs[i]`, `xs[i]?`, `xs[i]!`, and `xs[i]'h` have different obligations; a `!` suffix is not a proof of absence of failure.

### 16.2 State, IO, concurrency, and execution

Admit local mutation and the actual reference-based facilities used by Lean, including `ST.Ref`, IO references, `StateRefT`, tasks, and imported synchronization/process/filesystem/network interfaces. This explicitly goes beyond v7's selected no-unmodeled-shared-state boundary for ordinary programs.

Proofs about a pure model do not automatically establish behavior of mutable references, scheduling, external processes, filesystems, networking, or native primitives. Availability on a host, resource use, and successful linking are separate from source-language acceptance. The reference does not promise all platform libraries on every operating system or backend. [L-RUNTIME] [L-STD]

### 16.3 Foreign interfaces

Admit `@[extern ...]`, `@[export ...]`, `@[implemented_by ...]`, native ownership/borrowing annotations such as `@&`, and the associated runtime interfaces. Namespace `export` and foreign-symbol `@[export]` are different constructs.

The `@&` annotation affects the ABI/reference-ownership convention of the relevant compiled foreign calls; it does **not** add a Rust-style borrow checker to Lean's logical type system. External code must obey the runtime ABI, object representation, ownership, initialization, and exception conventions. [L-TERM] [L-DECL]

A safe logical definition may have a different compiled implementation supplied by `extern` or `implemented_by`. Its Lean theorem concerns the logical declaration unless additional correspondence evidence justifies the native implementation. Do not silently turn a foreign function's type or contract into proof that the external implementation satisfies it. [L-VALIDATE]

### 16.4 Unsafe and diagnostic runtime behavior

Admit unsafe declarations and native unsafe expressions. An unsafe expression can generate an auxiliary implementation behind a safe interface when Lean's inhabitance conditions hold; therefore checking only public signatures for the word `unsafe` is insufficient to audit runtime correspondence.

Admit `panic!`, `unreachable!`, tracing, and debugging with native behavior. `panic!` has a logical default-value interpretation and runtime behavior controlled by the runtime's panic settings; it must not be summarized as universally throwing an exception or universally terminating the process. [L-TERM]

## 17. Diagnostics, documentation, and bootstrap commands

### 17.1 Interactive and diagnostic commands

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

`#eval` may execute IO and supported elaboration monads; v1 does not impose v7's pure-total-only diagnostic restriction. Native `#eval` ordinarily refuses sorry-dependent execution; `#eval!` has a different explicit development meaning. Neither form is a proof certificate, and permitting the development grammar does not qualify hole-dependent program output. [L-CMD]

### 17.2 Documentation and editor support

Admit native Markdown/plain and Verso documentation syntax and the registered supporting facilities, including `add_decl_doc`, `recommended_spelling`, `register_tactic_tag`, `tactic_extension`, `register_error_explanation`, and documentation extension hooks. Preserve source attachment, declaration ownership, and diagnostic behavior. Documentation parsers are part of the source-extension ecosystem, not always ignorable whitespace. [L-CMD] [L-TERM]

Admit `dbg_trace`, assertion debugging, and experimental `idbg` syntax at the pinned version. Runtime/editor execution requirements and experimental limitations remain upstream requirements. Interactive debugging is neither mandatory during compilation nor evidence of functional correctness.

### 17.3 Bootstrap and internal facilities

Include `init_quot`, `gen_injective_theorems%`, `docs_to_verso`, builtin parser-attribute hooks, parser aliases, and internal scoped commands such as `end_local_scope` under their actual native scope and preconditions. Their presence in the language target does not make them ordinary application recommendations.

Bootstrap operations cannot run indiscriminately in an already initialized environment. In particular, quotient initialization and generated foundational declarations must obey the same uniqueness, environment, and checking requirements as Lean. “All features” does not mean every command succeeds at every point in every file.

## 18. Assumptions and assurance boundaries

### 18.1 Independent questions

A report about a PS0 module must distinguish:

1. **Language acceptance:** did the selected edition parse/elaborate the source under the intended imports and options?
2. **Logical checking:** which final statements and definitions were checked, and relative to which assumptions?
3. **Executable availability:** does the relevant program have compiled code and valid runtime/link dependencies?
4. **Verified claim:** what specification, effects, termination property, erasure behavior, assumptions, and execution layer does the evidence actually establish?

This is one language with different evidence outcomes, not a second unchecked proof kernel. A conditional theorem may be valid relative to stated axioms without being an unconditional theorem under an approved foundation. A program may compile without being claimed to satisfy a functional specification.

### 18.2 Construct-specific interpretation

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
| Imported `.lean` module | Genuine Lean compilation | Automatic admission into a v7 or v1 verified dependency closure |

### 18.3 Minimum restrictions on stronger claims

**PS0V1-ASSURANCE-01.** Incomplete source is permitted for development, but unresolved metavariables, source/generated/transitive `sorryAx`, and error-recovery declarations cannot qualify as completed proofs or hole-free checked output. Imported dependencies and generated declarations count; inspecting only handwritten tokens is insufficient.

**PS0V1-ASSURANCE-02.** No new axiom is silently approved by this document. Existing approved foundations remain unchanged. A stronger claim must identify and check the applicable transitive assumptions, including native-computation assumptions, against its declared policy. A conditional claim must say what it assumes.

**PS0V1-ASSURANCE-03.** Full metaprogramming and IO mean compilation can execute code. Logical checking is not an operating-system sandbox. An independent assurance claim must not trust arbitrary extension code merely because it ran inside a Lean process; it must establish the final statement/environment identity and the checks supporting the claim. [L-VALIDATE]

**PS0V1-ASSURANCE-04.** A verified executable claim must not be issued while mandatory specification-coverage, effect, assumption, erasure, or required termination obligations remain unresolved. It must state whether it concerns source semantics only or includes any native/foreign execution correspondence. Source proof checking alone does not verify the C compiler, runtime, machine code, or external system.

**PS0V1-ASSURANCE-05.** Restricting a particular verified claim is not the same as banning a language feature from all ordinary programs. For example, a partial-correctness theorem must not be advertised as total correctness, and an unsafe runtime implementation cannot be promoted to verified merely because its logical interface is safe.

## 19. Examples and migration rules

All snippets in this section are **illustrative, unexecuted design examples**. They are not test receipts. Imports and names must be resolved in a real fixture; examples with intentional assumptions or partiality are not verified-executable examples.

### 19.1 Retained definition and call surface

Native Lean:

```lean
def add (x y : Nat) : Nat := x + y
def tick (_ : Unit) : Nat := 1
#check add 2 3
#check tick ()
```

PS0 v1:

```proofscript
function add(x: Nat, y: Nat): Nat := x + y
function tick(): Nat := 1
#check add(2, 3)
#check tick()
```

`tick()` and `tick(())` may elaborate to the same application under the rule in §7. The constant `const one: Nat := 1` is not callable as `one()`.

### 19.2 Native module and metaprogramming shape

The following shape is newly within the v1 target:

```proofscript
module
import Lean
meta import Lean

public section

syntax "twiceTerm " term : term
macro_rules
  | `(twiceTerm $x) => `($x + $x)
```

The quotation payload uses its native syntax category. This example illustrates extension availability and module staging, not a guarantee that a syntactic duplication macro evaluates an effectful expression only once. A semantics-preserving “evaluate once” macro must bind the expression appropriately.

### 19.3 Partial and unsafe declarations

```proofscript
partial function spin(n: Nat): Nat := spin(n)

unsafe def runtimeIdentity(n: Nat): Nat := n

axiom applicationAssumption : True
```

These illustrate three different capabilities. `spin` provides no termination evidence. The unsafe definition is subject to Lean's safety classification even when its body happens to be simple. The axiom is an assumption, not a theorem proved by its declaration. None is retroactively admitted by the old v7 gate.

### 19.4 Effects and zipped iteration

```proofscript
function reportPairs(xs: List Nat, ys: List Nat): IO Unit := do {
  for x in xs, y in ys do {
    IO.println(s!"{x}, {y}")
  }
}
```

This uses the newly admitted runtime IO and native zipped-iteration family. It does not claim anything about filesystem/terminal effects beyond the imported runtime's semantics.

### 19.5 Proof and diagnostic separation

```proofscript
theorem identity(n: Nat): n = n := by {
  rfl
}

#check identity
#print axioms identity
```

A diagnostic can inspect the theorem, but it does not establish that an unrelated emitted program meets an application specification. Replacing the proof body by `sorry` changes the evidence outcome even when an editor continues to display the declaration.

### 19.6 Migration checklist

When porting an upstream `.lean` module into `.ps`, preserve explicit native `module`/visibility intent; translate ordinary grouped applications into the correct PS0 argument partition; retain native quotation/DSL category contracts; preserve binder order, instances, priorities, and stage imports; and keep assumptions and runtime replacements explicit.

Do not perform global substitutions such as “every `f (x, y)` becomes `f(x, y)`,” “every `where` body acquires `def`,” “every erased action disappears,” or “every partial function becomes a total `def`.” Such substitutions change meaning or grammar.

## 20. Source-to-feature coverage register

The rows below enumerate **100 review families**, not 100 indivisible Lean features. **Every row is a v1 requirement; none is a v1 test PASS.** “Source” identifies the pinned parser/implementation or imported-library entry supporting the family. Entry-module coverage requires inspecting the actual registered implementation during conformance work; it is not a claim that every transitively imported file was individually audited here.

| ID | Required family | Source / semantic anchor |
|---|---|---|
| V1-001 | Unicode and escaped/hierarchical identifiers | L-TERM, L-CMD |
| V1-002 | Comments and documentation comments | L-TERM, L-CMD |
| V1-003 | Numeral, scientific, character, string and registered literals | L-TERM, L-INIT |
| V1-004 | Raw/interpolated strings and embedded expressions | V7, L-INIT, L-DO |
| V1-005 | Universes, `Sort`, `Type`, `Prop`, explicit level parameters | L-TERM, L-CMD |
| V1-006 | Explicit, implicit, strict implicit and instance binders | L-TERM, V7 |
| V1-007 | Dependent/interleaved binders and section generalization | L-CMD, V7 |
| V1-008 | Default/automatic parameters and type-directed completion | V7, L-DEFS |
| V1-009 | Pi types, lambdas and pattern lambdas | L-TERM |
| V1-010 | Classes, instances, coercions and overloaded operations | L-CMD, L-TERM |
| V1-011 | Modern/implicit PS modules and explicit native headers | L-MODULE, V7, §3 |
| V1-012 | `prelude` and bootstrap import suppression | L-MODULE, L-INIT |
| V1-013 | Public/private imports and re-export | L-MODULE |
| V1-014 | Meta imports and public meta availability | L-MODULE, L-CMD |
| V1-015 | `import all` and its invalid combinations | L-MODULE |
| V1-016 | Namespace/section/end and include/omit | L-CMD |
| V1-017 | Open/hiding/renaming/only/scoped and namespace export | L-CMD |
| V1-018 | Public/private/protected/expose and body visibility | L-CMD, L-DEFS |
| V1-019 | `meta`, `noncomputable`, `nonrec` and modifier legality | L-CMD |
| V1-020 | Definition, theorem, example and abbreviation declarations | L-CMD, L-DECL |
| V1-021 | `function`/`const` and required-Unit nullary lowering | V7 |
| V1-022 | Opaque bodies and bodyless inhabitant synthesis | L-DEFS, L-DECL |
| V1-023 | Explicit axiom declarations and assumptions | L-CMD, L-DECL |
| V1-024 | Inductive types/families and generated eliminators | L-CMD, L-DECL |
| V1-025 | Mutual/nested inductives and positivity requirements | L-DECL, L-REF |
| V1-026 | Structures, inheritance, named parents and constructor specifications | L-CMD |
| V1-027 | Implicit/instance/proof/default fields and computed fields | L-CMD |
| V1-028 | Classes and class inductives | L-CMD |
| V1-029 | Trailing and standalone deriving | L-CMD |
| V1-030 | Custom deriving and generated-instance checking | L-LEAN, L-CMD |
| V1-031 | PS comma calls, tuple/Unit distinction and argument ownership | V7, §7 |
| V1-032 | Native unparenthesized application and explicit `@` | L-TERM, V7 |
| V1-033 | Named arguments, placeholders, ellipsis and partial application | L-TERM, V7 |
| V1-034 | Field/numeric projections and generalized receiver insertion | L-TERM |
| V1-035 | Type ascription, expected-type control and anonymous constructors | L-TERM |
| V1-036 | Let/have, local instances and binding configurations | L-TERM |
| V1-037 | Native local-binding aliases and deprecation semantics | L-TERM |
| V1-038 | Records, updates, punning and field equations | L-TERM |
| V1-039 | Conditional terms and braced PS conditionals | L-INIT, V7 |
| V1-040 | Constructor, literal, successor and inaccessible patterns | L-TERM, V7 |
| V1-041 | Multi-discriminant/dependent match, motive and generalization | L-TERM |
| V1-042 | Pattern aliases and named match equations | L-TERM |
| V1-043 | `if let`, pattern bindings, `matches`, `nomatch`, `nofun` | L-TERM, V7 |
| V1-044 | Equation-style definitions and mutual function groups | L-CMD, L-PREDEF |
| V1-045 | Local recursion and complete where/finally facilities | L-TERM, L-PREDEF |
| V1-046 | Structural recursion and structural hints | L-PREDEF, L-TERM |
| V1-047 | Well-founded recursion, measures and decreasing proofs | L-PREDEF, L-TERM |
| V1-048 | Partial functions and opaque logical interfaces | L-PREDEF |
| V1-049 | Partial fixed points and monotonicity | L-TERM, L-PREDEF |
| V1-050 | Inductive/coinductive fixed points and predicate declarations | L-CMD, L-TERM |
| V1-051 | Braced/native layout and category-specific semicolons | L-CMD, L-DO, §4 |
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
| V1-067 | Ordered contracts and logical given binders | L-CMD, V7 |
| V1-068 | Generated spec proofs and native finally subsections | L-TERM, V7 |
| V1-069 | Verification-only assert versus runtime assertions | L-DO |
| V1-070 | Loop invariants/decreasing annotations and WP facilities | L-DO, L-STD, V7 |
| V1-071 | Erased state, erased mutation and effectful erased-result bindings | L-DO |
| V1-072 | Notation/mixfix, local/scoped precedence and priorities | L-SYNTAX |
| V1-073 | Syntax categories, syntax abbreviations and binder predicates | L-SYNTAX |
| V1-074 | Parser descriptors/combinators and leading/trailing parsers | L-SYNTAX, L-TERM |
| V1-075 | Macro declarations/rules and dispatch | L-SYNTAX |
| V1-076 | Quotations, antiquotations, splices, patterns and hygiene | L-TERM, L-CMD, L-SYNTAX |
| V1-077 | Native/PS category ownership and extension compatibility | L-MODULE, L-SYNTAX, §13 |
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
| V1-088 | Primitive/data types, collections and indexed access | L-INIT, L-STD, V7 |
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
| V1-100 | Open-ended pinned registration and production-source closure | §1, §21 |

## 21. Conformance requirements and evidence status

### 21.1 Required evidence states

Track at least **specified**, **implemented**, **fixture-linked**, **executed at exact commit**, and **qualified for the stated outcome** separately. None implies the next. The 100 review families are not a measured percentage of the language.

The inspected PS0 implementation is a selected-v7 frontend with known restrictions, and its v7 registry has 181 pending named rows. This document does not change that registry or claim new results. V1 needs a separate inventory with explicit expectation changes; `.lean` pass-through results cannot populate `.ps` implementation PASS rows. [P-README] [P-COVERAGE]

### 21.2 Corpus-based completeness procedure

A source-completeness claim must:

1. Pin and enumerate the physical production `.lean` files in the declared corpus, recording paths and content identities. Separately classify tests, examples, generated stage artifacts, and non-Lean files; do not inflate coverage with generated duplicates.
2. Resolve the exact imports/options and interleave parsing with elaboration as required by Lean's evolving grammar. Record encountered syntax kinds and relevant category, notation, attribute, deriving, macro, and elaborator registrations.
3. Distinguish actual source occurrences, quoted syntax data, macro-generated declarations, and forms present only in intentionally failing tests. Lexical searches are discovery aids, not evidence of grammatical use or acceptance.
4. Map each relevant native construct to its PS0 host form or explicit category-owned form, recording semantic and visibility differences. Ordinary `.lean` fallback cannot stand in for a missing `.ps` feature.
5. Validate the transformed module graph with the pinned Lean implementation, preserving statements, binder order, argument partition, assumptions, public/private exposure, stage availability, and the specified runtime observations.
6. Report every uncovered family/production, expected failure, unsupported platform prerequisite, and unexecuted case. Require exact source/compiler revisions and reproducible test results before claiming qualification.

Syntax-kind enumeration alone is insufficient: the same kind can encode multiple important alternatives, and arbitrary registered extensions are not bounded by the initial builtin kind set.

### 21.3 Minimum positive/negative test families

The following are **requirements, not executed tests**:

| Group | Required positive coverage | Required negative / claim-boundary coverage |
|---|---|---|
| Source routing | v7 `.ps`, v1 `.ps`, native `.lean` remain distinguishable | No silent promotion of v7 input or leakage of PS0 registrations into `.lean` |
| Calls | Comma/tuple/Unit/named/default/partial calls and mixed precedence | Gap applications, noncallable empty calls, guessed Unit, argument regrouping |
| Modules | Native/implicit defaults, prelude, public/meta/all imports | Public-import-all conflict, private leakage, unavailable stage dependency |
| Data | Indexed/mutual data, structures/classes, computed fields, deriving | Positivity/type failures; unsupported handler or missing instance |
| Recursion | Structural/WF/partial/fixed-point/local/mutual forms | Incompatible hints, missing inhabitance, false termination/correspondence claim |
| Do/control | Zipped loops, repeat/while, forwarding do, monadic if-let, catch/finally | Wrong return target, Cartesian interpretation, invalid forwarding position |
| Verification | Contracts, generated spec proofs, erased state and loop obligations | Hole-dependent proofs, reordered clauses, erased action dropped, unsupported effect proof |
| Extensions | Custom categories, macros, elaborators, hygiene, deriving and attributes | Token rewriting inside quotes, wrong grammar-context fallback, captured identifiers |
| Staging/init | Public meta dependencies, builtin/ordinary initialization | Lost registrations/effects or runtime reference to meta-only code |
| Runtime/FFI | IO/ref/task families, extern/export/implemented_by/@& | ABI mismatch, hidden runtime replacement, unsupported platform claim |
| Diagnostics | Native evaluation, development holes and message tests | Treating evaluation or error recovery as proof qualification |
| Corpus closure | All encountered production/registration families accounted for | Any silently omitted production or use of `.lean` results as `.ps` coverage |

For source/core comparisons, compare actual declarations and meaningful semantic properties, not formatted text alone. For metaprograms that inspect source syntax, source positions or names, define the intended correspondence explicitly; translating punctuation need not produce identical raw syntax data. Native runtime correspondence needs its own tests or proofs at the claimed layer.

### 21.4 Release and implementation nonclaims

This reference does not claim self-hosting, complete `.ps` parsing, complete native builds, backend semantic preservation, all-platform support, finished IDE support, or exact-commit CI qualification. Those require implementation and evidence. Adding features to a language reference must never be reported as percentage progress in implementing them.

## 22. Research findings and implementation consequences

### 22.1 Why a small keyword expansion is insufficient

Lean's parser and compiler are written using the language's extension facilities. `Command.lean` and `Syntax.lean` themselves depend on parser definitions, quotation, attributes, initialization, scoping, and stage imports. The module parser's repeated parse/elaborate dependency means that adding `unsafe` and `partial` to a token list would leave the central self-description capability missing. [L-CMD] [L-SYNTAX] [L-MODULE]

### 22.2 Important semantic distinctions found in the pinned source

The expansion must preserve these distinctions: bodyless opaque versus axiom; partial versus partial fixed point; meta staging versus unsafety; public names versus exposed bodies; native safe interfaces versus substituted runtime code; verification assertions versus runtime assertions; erased results versus erased effects; and ordinary completed proof checking versus compiler-assisted assumptions. The corresponding rules appear explicitly above rather than being hidden behind “same as Lean.”

### 22.3 Consequences for the current PS0 design

`PS0/Grammar.lean` currently has a closed command/attribute selection and explicit exclusions for metaprogramming, unsafe/partial constructs, runtime effects, source loops, and other forms. That is evidence of the **current v7 implementation boundary**, not the v1 target. A v1 implementation must provide an edition-specific, category-aware frontend and move claim-specific restrictions to appropriately checked evidence boundaries. It must not simply delete bans while continuing to advertise the previous assurance guarantees. [P-GRAMMAR]

Reusing official Lean parsing/elaboration/compilation wherever the surface permits is the natural architectural consequence. This document does not prescribe replacing the current compiler, changing other branches, removing Lake, adopting npm, or implementing a new kernel. Those are separate engineering decisions.

### 22.4 What is added by this document

This edition makes the full pinned feature/registration closure a language requirement, supplies explicit rules for the major source families and v7 differences, defines their logical/runtime boundaries, and provides a source-linked coverage register and qualification procedure. It preserves the current implementation and older reference as separate artifacts. The next implementation must be judged against the requirements, not credited merely for importing this document.

## 23. Pinned sources

Source links below are part of the reference. Repository sources are pinned by commit; manual links are pinned to 4.35.0. Upstream Lean code carries its existing copyright and license notices. This document summarizes and references that implementation rather than copying its source bodies.

### Primary predecessor and PS0 implementation

[V7]: https://github.com/dwijayuda/pskernel/blob/f79d334ef922eb7f71f7527dbc798ebb0dbeb610/psc0/PSCV0_LANGUAGE_REFERENCE.md
[P-README]: https://github.com/dwijayuda/lean4/blob/22f6078dbcfb6335390915c3c7ae9a3566ad0ce0/experiments/ps0/README.md
[P-BOUNDARY]: https://github.com/dwijayuda/lean4/blob/22f6078dbcfb6335390915c3c7ae9a3566ad0ce0/experiments/ps0/SOURCE_PROFILE_BOUNDARY.md
[P-GRAMMAR]: https://github.com/dwijayuda/lean4/blob/22f6078dbcfb6335390915c3c7ae9a3566ad0ce0/experiments/ps0/PS0/Grammar.lean
[P-COVERAGE]: https://github.com/dwijayuda/lean4/blob/22f6078dbcfb6335390915c3c7ae9a3566ad0ce0/experiments/ps0/v7-coverage.json

- [V7 — authoritative predecessor][V7]: retained ProofScript rules, explicit bans, contract syntax, and historical conformance cases.
- [PS0 README][P-README] and [source-profile boundary][P-BOUNDARY]: current implementation and unrestricted `.lean` lane.
- [Current source gate][P-GRAMMAR] and [v7 evidence registry][P-COVERAGE]: implementation restrictions and existing qualification status.

### Pinned upstream code

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

| Source | Particularly relevant anchors |
|---|---|
| [Command parser][L-CMD] | `declModifiers`, `contractDeclVal`, declarations/deriving, scopes, diagnostics, initialization, bootstrap commands |
| [Term parser][L-TERM] | application/binders/match, `Termination.suffix`, `whereFinally`, `unsafe`, quotations, parser helpers, ABI borrowing |
| [Module parser][L-MODULE] | `parseHeader`, `parseCommand`, native header checks, parse/elaborate dependence |
| [Do parser][L-DO] | `doErasedArrow`, `doFor`, `doForward`, `doRepeat`, `doWhile`, assertions and exceptions |
| [Syntax-extension parser][L-SYNTAX] | syntax categories, notation, macros, elaborators, binder predicates |
| [Tactic parser][L-TACTIC] | tactic category, tactic matches and registered sequence grammar |
| [Declaration representation][L-DECL] | `DefinitionSafety`, `OpaqueVal`, `Declaration`, reducibility hints, foreign exports |
| [Recursive definitions][L-PREDEF] | `addAndCompilePartial`, recursive-group partitioning, `checkTerminationByHints`, `addPreDefinitions`, error recovery |
| [Init entry][L-INIT] | notation, tactics, control, data, system, meta, tasks and registrations |
| [Std entry][L-STD] | data, verification, synchronization, time, networking, tactics and `Std.WP` |
| [Lean entry][L-LEAN] | compiler, environment, parser, elaborator, meta, runtime, server and extension APIs |
| [Lake DSL entry][L-LAKE] | imported build-language extension families, without making Lake mandatory |
| [Elaborator entry][L-ELAB] | registered syntax/notation, declarations, diagnostics, configuration and intrinsic elaboration families |
| [Decision tactic][L-DECIDE] | `evalDecideCore`, native versus kernel/elaborator paths, actual `native_decide` registration |
| [Native decision infrastructure][L-NATIVE] | `nativeEqTrue`, closed-expression compilation/evaluation and generated computation axioms |

### Pinned manual

[L-REF]: https://lean-lang.org/doc/reference/4.35.0/
[L-DEFS]: https://lean-lang.org/doc/reference/4.35.0/Definitions/Definitions/
[L-RUNTIME]: https://lean-lang.org/doc/reference/4.35.0/Run-Time-Code/
[L-VALIDATE]: https://lean-lang.org/doc/reference/4.35.0/ValidatingProofs/

- [Lean 4.35.0 reference][L-REF]: supporting type, language, library and metaprogramming reference.
- [Definitions][L-DEFS]: definition transparency, opacity, inhabitant synthesis and executable distinctions.
- [Run-time code][L-RUNTIME]: runtime representation and foreign execution context.
- [Validating proofs][L-VALIDATE]: assumptions, native-assisted decisions, metaprogram execution and limits of a proof-checking claim.

**End of PS0 v1 language reference.**
