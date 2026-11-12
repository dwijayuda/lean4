# PS0 Verified Multi-Backend Architecture

**Status: research proposal, not an adopted language specification or an implemented verified compiler.**

- Research date: 2026-10-29, Asia/Jakarta.
- Repository: `dwijayuda/lean4`; project: `experiments/ps0/`.
- Audited base: `775f03481bcf4636c6a5e3730353f00823b1bfec` on `feature/ps0-lean435-stable-v1`.
- Design branch: `research/ps0-verified-multibackend-20261029`.
- Semantic pin retained: official Lean 4.35.0, `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.
- Existing normative authority retained: [PS0 v1 R2](PS0_V1_LANGUAGE_REFERENCE.md), Git blob `c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`.
- This document proposes execution profiles, proof obligations, compilation architecture and delivery gates. It does not silently narrow R2, replace existing commands, implement backends, change PSC0/PSC1, or certify examples.

## 1. Executive decision

Build **a small proof-linked executable profile inside the existing Lean-backed PS0 language**, not a second theorem prover and not a claim that all Lean programs can be translated to five runtimes.

Use full Lean in `proofs/` for specifications, tactics, mathematical libraries and extraction proofs. Elaborate `.ps` and eligible `.lean` definitions into the same pinned Lean environment. Select runtime roots explicitly. Extract only a mechanically checked, semantically specified fragment into a common typed intermediate representation. Connect that IR to the exact checked declarations with kernel-checked correspondence theorems. Lower it to restricted target ASTs for JavaScript, TypeScript, Python, PHP and Rust. Publish only after the chosen proof, dependency, boundary and target-correspondence policy succeeds.

The practical product is a **verified domain core with explicit platform adapters**. Existing frameworks continue handling hosting, UI, HTTP, databases and deployment. PS0 initially owns algorithms, validation, authorization decisions, accounting rules, state transitions and data transformations where precise specifications are valuable.

The user-facing guarantee should be:

> A successful verified build establishes the reviewed properties of the exact exported program and its identified artifacts, under the explicitly recorded logical, runtime, foreign-interface and resource assumptions.

This is intentionally not “all possible bugs have been eliminated.” A wrong or incomplete specification remains wrong or incomplete even when proved.

### Recommended decisions

| ID | Proposed decision | Rationale |
|---|---|---|
| ADR-01 | Preserve R2; add a versioned `verified-portable` emission profile | A small executable subset must not redefine ordinary `.ps` acceptance |
| ADR-02 | One Lean semantic environment; full `.lean` proofs | Avoid duplicate definitions, proof languages and kernels |
| ADR-03 | Extract from resolved Lean declarations, not reparsed source spelling | Bind generated behavior to the object actually proved |
| ADR-04 | Proof-producing extraction plus restricted target translation validation | Keep evolving optimizers outside the logical trust boundary where possible |
| ADR-05 | Share JavaScript/TypeScript runtime semantics and AST infrastructure | TypeScript is not a separate runtime or a proof system |
| ADR-06 | Start with total, value-oriented, first-order programs | Minimize aliasing, erasure, lifetime and termination obligations |
| ADR-07 | Interop through explicit capability interfaces and generated adapters | Package availability is not evidence of functional correctness |
| ADR-08 | Default publication is fail-closed; no automatic assurance downgrade | Preserve the meaning of a successful verified build |
| ADR-09 | Reuse Lean 4.35 proof replay and statement comparison | Do not build another proof-admission service without need |
| ADR-10 | Deliver JS/TS, then Python, Rust, PHP through independent gates | Reuse the existing experiment while exposing semantic differences early |

All decisions remain proposals until reviewed. A genuinely smaller source language, rather than an emission profile, would require an explicit edition migration and separate compatibility plan.

## 2. Current implementation and evidence baseline

The branch head was re-read through GitHub. It still identifies the base above; its last commit timestamp is 2026-10-15 22:57:54 UTC, or October 16 in Jakarta. Existing source previously inspected in this conversation was identity-checked against the current PS0 tree. The branch-wide Actions query returned `total_count: 0`. This is an observation about this branch, not a claim that the whole repository has no workflow history.

| Area | Observed implementation | Qualification boundary |
|---|---|---|
| Frontend | `PS0Main.lean` invokes official `Elab.runFrontend` | No observed successful exact-base PS0 build |
| Native output | Official frontend plus `Compiler.LCNF.emitC`; staged `.olean` and `.c` | Not complete native linking or a verified-machine-code theorem |
| Source adapters | `PS0/Syntax.lean` includes function/const, binder, contract and selected control adapters | Standard operand ownership is incomplete |
| Host categories | `psTerm`, `psCommand`, `psTactic`, `psDoSeq`; selected identifier-head calls | Not full R2 category closure, quotation ownership or postfix coverage |
| Proof reporting | `#ps0_evidence` counts local classifications | Informational, not transitive assumption approval or certification |
| JS experiment | Nat expression IR, BigInt emission, `.d.ts`, source maps | Source-AST lowering plus checked-signature matching; no body-correspondence proof |
| Modules | Modern header preparation and import flags | Complete mixed-source graph, body exposure and `prelude` isolation remain open |
| Tests | Full and focused Linux workflow definitions | Definitions are not executed receipts |
| Coverage | 242 R2 obligations: 100 families, 64 positive, 47 negative, 31 witnesses | All pending in the audited ledger; not a percentage of implementation work |

Repository anchors: [implementation plan](PS0_V1_IMPLEMENTATION_PLAN.md), [work state](AI_WORK_STATE.md), [conformance](CONFORMANCE.md), [source boundaries](SOURCE_PROFILE_BOUNDARY.md), [frontend](PS0Main.lean), [host categories](PS0/HostCategories.lean), [syntax](PS0/Syntax.lean), [JS lowering](PS0/Backend/Js/Lower.lean), [JS emission](PS0/Backend/Js/Emit.lean), [tests](tests/), and [coverage ledger](v1-coverage.json). Historical observations refer to the immutable base, not future moving-branch content.

Important audit findings for this proposal:

1. `buildJs` retains the checked environment, but its backend reparses the original source and checks export safety/type signatures. A declaration with the right type need not have the same body as an independently generated program. Replace this assurance gap with exact declaration-to-IR correspondence; do not describe signature checks as translation validation.
2. The current frontend executes Lean initializers. Arbitrary macros, elaborators and package setup therefore need process isolation; an in-process success message is not an independent proof receipt.
3. R2 permits full native language capabilities. Runtime eligibility must be checked on the selected elaborated dependency closure rather than enforced by a global source-token blacklist.
4. Existing `.d.ts` tests inspect text, not an actual TypeScript consumer compilation. Source-map checks are structural. Neither establishes target semantics.
5. Some historical documentation still mentions retired policy gates or already-superseded restrictions. Source and exact execution receipts take precedence for implementation claims; R2 remains authoritative for language meaning.

No implementation completion percentage is assigned. The old v7 41% figure is unrelated to this proposal.

## 3. Goals, non-goals and architecture alternatives

### Goals

Make verified components usable inside established ecosystems; retain readable source and generated artifacts; preserve one logical foundation; require explicit specifications and assumptions; make AI-generated changes cheap to check but difficult to falsely certify; and grow features only with reusable semantic and boundary evidence.

### Non-goals for the first releases

Do not compile all of Lean, all Mathlib, arbitrary metaprograms, every foreign package API or every concurrency model. Do not claim verified operating systems, network services, TLS implementations, target compilers or hardware. Do not require self-hosting, a new kernel, a package-manager replacement, or migration of an entire application before PS0 is useful.

### Alternatives considered

| Architecture | Strengths | Main costs and correctness risks | Decision |
|---|---|---|---|
| A. Official Lean native code, with wrappers or a Wasm/native shared runtime | Maximum native reuse; one execution implementation | Does not deliver genuine Python/PHP/Rust/TS source semantics; runtime/ABI deployment; native compiler still needs its own trust account | Keep as an optional native lane, not the five-backend answer |
| B. Resolved Lean subset to proof-linked portable IR to restricted targets | Shared logic; one portable model; precise eligibility; independent backend growth | Extraction, erasure and target correspondence must actually be proved | Recommended |
| C. Lean specifications translated into Dafny/F*/Why3, then existing extraction | Reuses mature verification or extraction tooling | A new logic/specification bridge, extra toolchains and target limits; successful external verification is not automatically a Lean proof | Study algorithms and use as optional cross-checks, not mandatory production path |
| D. Add five emitters directly to Lean compiler IR/LCNF | Reuses native compilation lowering and optimization | Runtime representations, proof erasure and substitutions may already be implicit; no automatic proof link to the source | Possible performance experiment after a proved reference path, not initial authority |

Selection criterion: the easiest architecture to generate code is not necessarily the easiest architecture to justify. Prefer one small, executable semantic model and an explicit extraction relation over five independently interpreted source languages.

The fallback when a backend is unfinished is **refusal or a clearly requested native lane**, not silently exporting unverified target code. An optional IR interpreter could be compared with direct generation as an experiment; it would still need an interpreter-correctness argument and would not remove foreign-runtime assumptions.

## 4. Research lessons and available infrastructure

These are source-supported lessons, not claims that other systems already solve PS0's complete problem.

| System / source | Relevant finding | PS0 consequence |
|---|---|---|
| Lean 4.35 release and proof validation [U01, U02] | `lake check` and `lake comparator` support sandboxed export/replay and statement/assumption checking; Linux is the relevant sandbox platform | Integrate and qualify these exact-pin facilities before inventing a custom admission protocol |
| Lean compiler / replacement attributes [U03, U04] | Logical definitions, compiler execution and replacement implementations have different trust boundaries | Audit `extern`, `implemented_by`, compiler substitutions and proof-computation assumptions separately |
| F* extraction [U05] | Extracted callers can lose source refinements at an unverified-language boundary | Generate checked boundary adapters; an erased proof is not a runtime guard |
| Dafny [U06] | Verification-aware development, multiple targets and extern interfaces demonstrate a practical workflow | Borrow workflow ideas, not an unsupported blanket backend-verification claim |
| CompCert [U07] | Compiler correctness is a relationship between defined source and target behaviors | State the exact semantic relation and assumptions for every target |
| CakeML [U08] | Proof-producing translation and a verified backend are distinct composable components | Separate source-to-IR proof production from target compilation |
| Verus / Creusot [U09, U10] | External specifications introduce assumptions about unverified implementations | Keep foreign-contract assumptions first-class and transitive |
| Why3 / Viper [U11, U12] | Intermediate verification languages and specialized reasoning support modular tooling | Reuse design lessons; do not make an SMT solver result sufficient for Lean-kernel admission |
| Idris 2 / Agda [U13, U14] | Backend-specific FFI and type-directed programming do not make foreign implementations proved | Separate interface generation, representation validation and semantic evidence |
| Rocq extraction [U15] | Logical proof-oriented development and executable extraction are separate concerns | Account explicitly for erasure and realization of extracted constants |

Lean 4.35 is particularly relevant: its release notes describe proof checking in a separate process and comparison against a challenge module. Use the official kernel as the baseline. Bundled independent checkers may provide optional diversity; PS0 does not need to create another kernel. Exact command availability and flags must be exercised on the project's pinned binary in MB0. Documentation is not a successful PS0 integration test. [U01]

A version-sensitive trap: checking only for the old name `Lean.trustCompiler` is insufficient. Current Lean documentation describes dedicated axioms for native computation, and the 4.35 release removes the older machinery. Audit the entire actual axiom closure against an explicit policy. [U01, U16]

## 5. Language versus executable profiles

Preserve three distinctions:

- **Language:** R2 defines ordinary `.ps`; `.lean` remains unrestricted native Lean.
- **Executable profile:** a checked subset of resolved declarations and operations eligible for a target family.
- **Assurance policy:** the reviewed properties, admissible assumptions, termination/effect requirements and output evidence needed for publication.

A valid `.ps` module can fail executable-profile selection without becoming invalid source. Proofs can use constructs excluded from runtime extraction. A `.lean` definition is eligible only by the same semantic checks as a `.ps` definition, not because of its file extension.

### Proposed feature staging

| Feature | First vertical slice, VExec-0 | Practical portable core, VExec-1 | Later / explicit capability |
|---|---|---|---|
| Functions | Named first-order total functions; explicit export roots | Finite specialization of parametric functions | Closures/higher-order values after proved conversion |
| Values | Unit, Bool, Nat; add Int with explicit arithmetic lemmas | Records, finite ADTs, tuples, Option/Except | Runtime-dependent representations only with witnesses |
| Control | Let, conditionals, direct calls | Exhaustive matching, structural recursion, bounded iteration | General well-founded recursion when extraction is qualified |
| Mutation | None in IR | Local mutable syntax lowered to explicit pure state | Shared mutable heaps and aliasing deferred |
| Collections | Small fixed records/products as needed | Value-oriented lists, arrays and bytes; maps as libraries | Specialized mutable/zero-copy collections |
| Text | Defer until boundary model is ready | Unicode-scalar text with explicit encoding operations | Locale/normalization/regex packages as capabilities |
| Generics | Monomorphic instances | Finite monomorphization with size limits | Dictionary passing or higher-rank runtime abstractions later |
| Typeclasses | Resolve during Lean elaboration | Exact selected dictionaries captured in closure | Runtime dispatch only through a proved representation |
| Proofs / dependent types | Full proof layer; erase only justified proof arguments | Refinements and indices with known runtime representations | Arbitrary runtime type computation deferred |
| Errors | Explicit tagged results | `Except`-style propagation | Host exceptions normalized at adapters |
| Effects | Pure functions | Explicit capability calls with trace models | Async, cancellation and concurrency separately qualified |
| Modules | One selected closed module | Mixed `.ps`/`.lean` graph with exact identities | Dynamic loading outside strict portable profile |
| Numeric extras | No floats or implicit machine overflow | Explicit bounded-word/checked conversion libraries | Floating-point policies, decimal and platform intrinsics |

This is Go-like in simplicity and reviewability, not an attempt to copy Go's type system, scheduler or memory model. Prefer one idiom per task, explicit results and small interfaces. Avoid making inheritance, implicit dynamic coercions, reflection, arbitrary operator replacement or concurrency primitives necessary for ordinary application logic.

Library mechanisms should supply maps, parsers, codecs, validation combinators, domain types, mathematics and most effect protocols. A library that introduces an executable primitive must supply a representation, semantics and target evidence; “optional extension” is not a bypass around verification.

## 6. Full Lean proof integration and dependency graphs

Use the exact elaborated definitions produced by the PS0 frontend. Do not generate a handwritten Lean model that can drift independently from executable source.

Recommended graph:

```text
shared logical types / reviewed interfaces
              |
     src/*.ps + eligible src/*.lean
              |
      exact admitted Lean declarations
         /                       \
proofs/*.lean                  runtime root closure
(full Lean / tactics)           eligible extraction
         \                       /
        checked correspondence + specification receipts
                       |
              backend publication gate
```

`proofs/` is a convention, not a trust boundary. A runtime definition cannot smuggle an unsupported operation into an artifact merely by importing it from another directory. Conversely, a proof may use substantial Mathlib without making Mathlib a target runtime dependency, provided only erased logical evidence depends on it.

Maintain separate graphs for source imports, logical proof dependencies, executable reachability, foreign capabilities and build-time code execution. An ordinary source import is not identical to the set of runtime declarations.

### Avoiding proof/runtime cycles

Runtime modules do not import their downstream proof modules. The build reads a manifest connecting exports to separate proof obligations. A proof imports the admitted runtime module; the publisher loads both and checks exact declaration identities. Imported specifications and interfaces can be shared upstream.

An extraction proof can depend on the implementation without requiring the implementation to depend on extraction artifacts. For useful recursive verification, generate named obligations into a deterministic interface module, then let `proofs/` supply their proofs.

### Source and theorem identity

Record declaration names, universe parameters, types, bodies, relevant import identities, options and resolved instances. Freeze the reviewed specification independently of the candidate implementation. Compare propositions against that challenge rather than trusting the candidate to print a theorem name or success message. Human-readable source maps and pretty-printed statements supplement, but do not replace, exact checked identity.

Full tactics, macros and elaborators remain available during development. Their returned proof terms must survive independent kernel replay under the selected axiom policy. A tactic using unapproved native-computation axioms may be valid ordinary Lean and still fail the stricter release policy. [U02, U16]

## 7. Proof-linked intermediate representation

Create a small **PS0 executable IR**, implemented and given semantics in Lean. This is an IR well-formedness checker, not a replacement Lean typechecker or proof kernel.

The first IR should have explicit typed locals, immutable values, constants, primitive operations, let bindings, conditionals and direct calls. Add tagged constructors, exhaustive cases and certified recursion only when needed. Use resolved declaration identities, never source strings, for callees and primitives.

Every primitive entry needs:

- An exact Lean declaration or proved logical model.
- A runtime representation relation.
- Evaluation, failure and resource behavior.
- Supported target implementations and evidence.
- Dependency/assumption classification.

### Extraction boundary

Input is an admitted environment plus explicit roots and a profile. An untrusted extractor proposes an IR program and correspondence proof. Lean checks a theorem relating the selected source declaration to the IR denotation. The proof must use the exact declaration from the admitted environment and the exact IR value intended for emission.

Start with syntax-directed extraction supported by reusable correctness lemmas. Do not rely on unrestricted normalization until it happens to resemble the desired IR. Opaque constants, unknown recursors, unsafe replacements, noncomputable runtime data and missing representations produce specific refusal diagnostics.

All transformations that can change execution need evidence: specialization, closure conversion, effect lowering, erasure, ANF conversion, common-subexpression elimination and target peepholes. Initially omit optimizations whose proof burden exceeds their measured benefit.

### Erasure requirements

Proof fields in `Prop` are erased only through an explicit extraction theorem. Runtime data cannot be deleted because it has a proof-like name or resides in `proofs/`. A function producing an erased result may still perform effects; preserve those effects. Dependent indices may be erased only when runtime representation and all remaining operations are defined without guessing the missing value.

The first profile admits only representation-stable dependent uses. Classical reasoning can help prove properties without supplying executable choices; a runtime use of noncomputable choice remains ineligible.

### Reference semantics

The IR interpreter in Lean is the semantic reference, not Rust, Python or the existing JS emitter. Separate pure value semantics from later effect traces. Specify evaluation order before adding effects. Treat resource exhaustion explicitly: mathematical totality does not prove a concrete runtime has enough stack or memory.

## 8. End-to-end compilation and its theorem obligations

Proposed pipeline:

```text
source snapshot + lockfiles + profile + reviewed obligations
  -> official Lean elaboration
  -> sandboxed export and independent proof replay
  -> exact root/dependency/assumption inventory
  -> proof-producing extraction to typed IR
  -> evidence-backed normalization
  -> target-specific restricted AST
  -> exact target text + correspondence evidence
  -> target syntax/type/runtime regression checks
  -> independent release policy evaluation
  -> atomic artifact bundle publication
```

The proof-generating compiler is not permitted to approve its own claims merely by returning `true`. The final process consumes the checked exports, exact artifacts and policy identity. Reuse official Lean replay and comparator infrastructure where it fits; any PS0-specific surrounding validator has a small documented role and must itself be tested and reviewed.

### Required relationships

For source declaration `f`, IR program `p`, target program `t`, bytes `b`, specification `S`, input relation `Rin` and output relation `Rout`, establish distinct obligations:

1. **Specification:** the reviewed theorem states the required property of `f`, under explicit preconditions and assumptions.
2. **Extraction:** interpreting `p` corresponds to executing the eligible definition of `f`.
3. **Target translation:** target executions of `t` match the modeled IR results/traces, including relevant errors and effects.
4. **Serialization:** the actual emitted bytes decode to the target AST covered by that theorem.
5. **Deployment boundary:** the identified runtime, libraries and execution configuration satisfy the declared realization assumptions.

For a pure total function, the intended result is schematically:

```text
approved assumptions + valid input representation + resource conditions
  => target evaluation of exact artifact terminates with an output
     related to f(input), and the reviewed specification holds.
```

A one-way simulation that permits target divergence is not enough for a total-correctness label. Require progress/termination preservation or explicitly publish a weaker safety/partial-correctness claim. For effectful services, prove trace properties and state invariants; do not claim a server loop must terminate.

### Translation validation strategy

Use a small target subset and prove reusable compiler rules in Lean. Per-build certificates instantiate those rules for the concrete program. An independent validator can reparse the restricted emitted text and prove it matches the expected AST. Parsing/printing round-trip correctness is necessary for byte identity but insufficient for semantic preservation; both relationships are required.

A target-language typechecker, test suite, AST hash or type-signature match cannot replace these obligations. Hashes support integrity and cache indexing, not mathematical equivalence. Where feasible, checked proof statements refer to literal decoded program values as well as manifests.

The first target models may cover only a small emitted fragment. State that limitation prominently. A theorem about a restricted JavaScript model is not a proof about every JavaScript engine, and Rust source correspondence is not a verified `rustc` or machine-code theorem.

## 9. The fail-closed publication policy

Separate authoring, checking and publishing. The following command names are proposed, not implemented CLI guarantees.

| Proposed operation | Permitted result | Not permitted |
|---|---|---|
| `ps0 check` | Diagnostics, ordinary Lean classification, unresolved obligations | A verified label just because checking completed |
| `ps0 prove` | Replayed specification proofs and dependency report | Approving changed specifications silently |
| `ps0 build --profile verified-portable` | Exact target bundle after source and target obligations satisfy policy | Missing proof, unsupported primitive, unknown assumption or automatic fallback |
| `ps0 audit` | Human/machine report of evidence and remaining assumptions | Converting a test result into a proof |
| Explicit conditional profile | A proof-bearing artifact with enumerated, approved realization/FFI assumptions | Calling it unconditional or strict-profile equivalent |

Normal executable emission requires the source obligations to be proved. Private target candidates may be staged after source verification to produce/check correspondence evidence, but they are not published release artifacts. Failed validation removes staging and preserves any previous valid output. There is no normal `--skip-proof` release option.

Existing historical PS0 `build`/`build-js` commands remain unchanged by this documentation commit. Adoption requires a separate CLI migration decision: retain them as clearly labeled experimental commands or move them under an explicit legacy namespace. Do not retroactively call their outputs verified.

### Policy manifest

A release policy fixes required properties per export, allowed logical axioms, executable profile/version, target model, runtime realizations, approved foreign contracts, effect/resource assumptions, required proof replay and correspondence receipts, and permitted build transformations.

Do not require a separate handwritten theorem for every helper. The checker must establish complete coverage compositionally: reusable library theorems and enclosing verified control flow may discharge helper obligations. However, every reachable operation must be covered by the semantics and every exported requirement must be accounted for.

Reject `sorryAx`, unapproved bespoke axioms, unfinished generated VCs, altered challenge statements, unsupported runtime dependencies, unaccounted replacements and mismatched artifacts. Approved standard axioms such as `propext`, `Classical.choice` and `Quot.sound` are an explicit policy choice, not a claim of zero assumptions.

### Assurance is multidimensional

Report source proof, extraction proof, target-model correspondence, foreign realization, resource scope and actual runtime qualification separately. A single green badge hides important differences. Conditional profiles must require deliberate selection and exact assumption approval; they cannot be chosen automatically when a strict build fails.

## 10. Trusted computing base and security boundaries

| Layer | What can be checked | Residual trust / required disclosure |
|---|---|---|
| Logical result | Official kernel replay of exact statements and proof terms | Logic, kernel implementation and approved axioms |
| Specification identity | Challenge/solution comparison and reviewed definition closure | Human intent and correctness of the chosen specification |
| Extraction | Checked source-to-IR theorem | Adequacy of the IR semantic model and statement binding |
| Target source | Checked IR-to-target relation and serialization identity | Adequacy of target semantics relative to deployed implementations |
| Compiler/runtime | Versioned runtime model, tests and optional external evidence | JS engine, Python/PHP runtime, Rust toolchain, system libraries, OS/hardware as applicable |
| Foreign operations | Proven adapter behavior or explicit assumed contracts | Actual package/service behavior beyond proved or validated properties |
| Artifact handling | Exact identity, dependency locks and atomic publication | Small publisher, filesystem/process isolation and cryptographic assumptions |

Build processes can execute arbitrary code through Lean metaprograms, package scripts, Python build hooks, Composer plugins or Rust build scripts/procedural macros. Resolve approved dependencies separately, then perform verification with restricted network access, read-only source snapshots and no deployment credentials. The proof-checking process must not execute untrusted project initializers. Reuse and qualify upstream sandbox facilities rather than assuming a directory boundary is isolation. [U01, U02]

Same-process foreign code is not automatically adversarially isolated. JS monkey-patching, Python dynamic behavior, PHP extensions and Rust/C undefined behavior can violate a cooperative model. For hostile dependencies use process/service boundaries with validated messages, or explicitly assume noninterference. An HTTP contract never proves that the remote service is honest or available.

The threat model distinguishes compiler bugs, malicious generated proof/source code, stale artifacts, unreviewed specification changes and hostile runtime packages. Formal functional correctness is not automatically secrecy, constant-time behavior, availability or supply-chain safety.

## 11. Portable semantic and representation contract

The table is a proposed implementation policy. Native-language facts are anchored in [U17–U25]; choices about PS0 are design decisions, not upstream guarantees.

| Concern | Portable meaning | JS / TS | Python | PHP | Rust |
|---|---|---|---|---|---|
| Nat / Int | Mathematical integers; explicit exact operations | BigInt, never implicit Number | Built-in integer with validated boundary | Explicit arbitrary-precision representation; never overflowing native int | Explicit arbitrary-precision representation or proved bounded specialization |
| Nat subtraction | Saturates at zero | Checked helper | Checked helper | Checked helper | Checked helper |
| Division / remainder | Use the exact pinned Lean operation or a separately named checked API | Do not inherit target defaults | Do not inherit floor-division behavior accidentally | No implicit float division | Explicit signed/zero semantics |
| Bounded words | Named width and overflow mode | Certified emulation/conversion | Range-checked conversion | Range-checked conversion | Explicit checked/wrapping operations matching source |
| Bool | Only two Boolean values | No truthiness | Do not accept integer/Boolean confusion | No loose comparison/coercion | Native bool with matching ABI |
| Text | Unicode scalar sequence; explicit byte encoding | Validate surrogate boundaries; no implicit UTF-16 indexing semantics | Validate imported text representation | Validate UTF-8 in byte strings; no byte-as-character substitution | Explicit scalar/byte indexing APIs |
| Bytes | Sequence of 0..255 values | Copy/own typed-array views | Immutable bytes or owned copy | Binary string/owned buffer adapter | Owned byte vector/slice contract |
| Records / ADTs | Value semantics and explicit tags | No prototype-dependent dispatch in core | No arbitrary subclass behavior in core | Generated final/value-oriented representations | Structs/enums; structural mapping |
| Option / Except | Explicit tags including nested absence | Not accidental null/undefined conflation | Not accidental None conflation | Not accidental null conflation | Defined enum mapping |
| Collections | Defined iteration/equality/update semantics | Avoid ambient mutation/identity assumptions | Avoid aliasing and subclass hooks | Avoid native array key coercion as portable semantics | Explicit ownership and iteration order |
| Generic equality | Chosen logical operation | No implicit JS identity | No arbitrary `__eq__` dispatch | No loose `==` | No unreviewed foreign trait-law assumption |
| Errors | Typed results in core | Catch/normalize declared host failures | Catch declared exceptions | Catch/normalize modeled Throwable paths | Map Result; classify panics separately |
| Recursion / loops | Proven semantic termination or explicit trace model | Stack bound or proved iterative lowering | Stack bound or proved iterative lowering | Stack bound or proved iterative lowering | Stack bound or proved iterative lowering |
| Resources | No silent assertion of infinite memory | OOM/engine failure boundary | OOM/process failure boundary | Memory/time limits boundary | OOM/abort boundary |

JavaScript BigInt and Python integers provide useful representations, but representation selection alone is not a proof of every helper. PHP native integer overflow can become floating-point, so it cannot implement unbounded Nat faithfully. PHP strings are byte sequences; JS strings use code units. These differences drive explicit adapters. [U17, U18, U19, U20]

Select the exact PHP/Rust big-integer runtime only after a measured experiment. Candidates may include mature packages or a small generated limb implementation. Package maturity is not formal verification: its semantic realization is either proved, independently checked, or listed as an assumption. Do not make an unqualified package selection a hidden hard dependency.

For performance, allow bounded integer specializations when a checked range theorem justifies them. Preserve an exact reference implementation and differential corpus. Floating point, decimal rounding, locale-sensitive text, time, randomness and map iteration order require distinct explicit policies rather than inherited target accidents.

## 12. Backend architecture and delivery order

Retain implementation ownership in Lean initially. Reuse `PS0/Backend/Js` instead of renaming existing packages gratuitously. Add shared `RuntimeIR`, `Extract`, `Evidence` and target modules only as the implementation reaches them. Small host scripts can run ecosystem tools but cannot authorize proofs.

### JavaScript and TypeScript: one runtime family

Generate ESM JavaScript from a shared restricted ECMAScript AST and generate a genuine optional `.ts` form plus `.d.ts` interfaces. A `.d.ts` file alone is not a TypeScript backend. Type annotations do not prove runtime refinements; TS intentionally admits some unsound compatibility rules. [U21]

Prefer a canonical JS runtime artifact. Define and validate a restricted TS erasure relation to that AST. If downstream `tsc`, a bundler or minifier changes executable code, either validate the actual transformed output or add the transformation tool to the disclosed trust boundary. Do not certify one file and publish a different bundled file.

Generate explicit package exports and module type. ESM and CommonJS need separate consumer tests; browser, Node and Bun are different qualification environments even when they consume the same ECMAScript. Source maps must refer to original `.ps` spans without pretending proof bodies are runtime code. [U22]

### Python

Generate readable modules, type annotations and optional `.pyi` interfaces. Use exact integers and explicit tagged records/results. Type annotations are tooling, not runtime enforcement. [U23]

Avoid invoking arbitrary user-defined numeric/string magic methods inside the portable core. At ingress, normalize into owned built-in representations. Qualify imports, package layout, exception conversion and recursion behavior against a pinned runtime. Emit standard packaging metadata without making the compiler itself depend on Python for proof checking.

### Rust

Generate safe Rust where possible, with owned data and explicit borrowing adapters. Do not introduce a full Rust lifetime language into `.ps`. Begin with by-value and copy-in/copy-out boundaries, then add scoped borrows whose lifetimes cannot escape.

Finite generic specialization simplifies the first backend. Rich trait interop uses reviewed wrappers with selected trait implementations, not an assumption that any matching trait satisfies semantic laws. Build scripts, features, target triple, `rustc` version and Cargo resolution participate in identity. Safe Rust source is not a proof of business correctness or immunity to unsafe dependency behavior. [U24, U25]

### PHP

Generate namespaced classes/functions and Composer metadata. Require explicit coercion boundaries, bigint operations and owned value representations. Do not implement portable maps by inheriting all PHP array key conversions. Use generated adapters for object APIs and error paths.

Qualify CLI execution separately from web-server/worker integration. PHPStan/Psalm information can assist binding generation but cannot serve as proof of a package contract. Composer autoloading and platform extensions must appear in the deployment identity. [U19, U20, U26]

### Order

1. JS plus TS share the first semantic/emission work because a small JS experiment already exists.
2. Python tests whether the IR is genuinely portable without immediately imposing ownership complexity.
3. Rust tests representation, bounded specialization and ownership assumptions.
4. PHP tests bigint, coercion and byte/text boundaries explicitly.

Each backend gets its own passing release gate. Completion of one does not automatically qualify another. The portable IR remains the semantic reference throughout.

## 13. Foreign-library interoperability

### Architecture

```text
package metadata / type stubs / reviewed API inventory
  -> untrusted binding proposal
  -> human-reviewed logical interface + representation contract
  -> generated target-specific adapter
  -> adapter proof / explicit realization assumptions
  -> versioned binding package + consumer tests
```

Use native package managers for resolution: npm, Python packaging/PyPI, Composer and Cargo. A PS0 manifest records selected bindings, targets, effects and assurance rules; ecosystem lockfiles and artifact hashes record actual resolution. A lockfile is identity evidence, not a correctness theorem.

Prefer ordinary source imports such as `import Bindings.Http` and target selections in the manifest. Initially avoid inventing four different executable import grammars. Prefixes like `npm:`, `pypi:`, `composer:` and `cargo:` can be accepted as manifest identifiers without redefining Lean import syntax.

A library available only on one target is a target-specific capability. Importing a Python library does not make it callable in the JS runtime. A shared portable interface may have several separately qualified adapters; missing adapters are compile-time refusals, not automatic subprocess bridges.

### Binding contract fields

Record logical input/output types, representation conversion, package/export identity, target availability, allowed effects, error/exception mapping, mutability and ownership, callback cardinality/reentrancy, async cancellation semantics, allocation/resource conditions, actual law assumptions and evidence status. Include imported type metadata identity but do not treat it as a theorem.

### Four foreign assurance modes

| Mode | What is established | Required warning / limitation |
|---|---|---|
| Proven realization | A checked relation links the implementation/model to the contract | State the covered execution layer and remaining runtime assumptions |
| Explicit assumed contract | The core theorem is conditional on a reviewed foreign contract | Package behavior is not proved; strict no-extra-assumption policy can reject it |
| Adversarial-data interface | The core is proved safe for all responses admitted by a validator | Does not establish authenticity, freshness, availability or service side effects |
| Unclassified foreign code | No usable evidence or approved contract | Refuse verified publication |

Do not create arbitrary global Lean axioms for imported functions. Prefer explicit capability parameters and law hypotheses. At build time either provide a realization proof or record the exact hypothesis as an approved assumption. A proof-producing binding importer remains untrusted until its result is checked.

Runtime validation can prove that an accepted value is within a local domain if the validator itself is correct. It cannot retroactively prevent a foreign function from corrupting state, leaking a secret or sending an unauthorized request before returning. Validate inputs before calls, own/copy values at boundaries and model observable effects.

### Ecosystem details

- **JS/TS:** inspect `.d.ts` for candidate types; explicitly model `this`, callbacks, promises, ESM/CJS and object ownership. Avoid treating getters/proxies as passive data. Separate serializable data ingress from cooperative same-process object APIs.
- **Python:** use annotations/`.pyi` only as binding hints. Normalize built-in values, distinguish Boolean from integer input, classify C-extension dependencies, exceptions, context-manager cleanup and event-loop ownership.
- **PHP:** inspect native types and optional static-analysis metadata; model namespaces, interfaces, by-reference parameters, mutation, Throwable behavior and autoload side effects. Strict typing does not prove semantic laws.
- **Rust:** pin crate features and selected APIs. Model moves, borrows, destructor effects, callbacks, panics and async executor requirements. Do not expose arbitrary borrowed references as portable retained handles.

### Concrete research candidates, not approved dependencies

Zod provides JS/TS schema validation; HTTPX provides Python HTTP interfaces; Guzzle provides PHP HTTP interfaces; reqwest provides Rust HTTP interfaces. Their official documentation establishes these roles, not their correctness for PS0. [U27–U30]

Use them as adapter experiments with exact versions selected later. Do not assume their HTTP behavior is interchangeable: redirects, retries, errors, cancellation, TLS, proxies and timeouts need explicit contract choices. Begin with response validation and deterministic domain logic, not a proof of an entire HTTP stack.

Example manifest fragment, **proposed schema and placeholders, not an installable lockfile**:

```toml
[bindings.schema]
module = "Bindings.Schema"
package = "npm:zod"
targets = ["js", "ts"]
contract = "SchemaValidation.acceptedValue"
assurance = "explicit-assumption"
lock_ref = "REQUIRED_EXACT_RESOLUTION"

[bindings.httpPython]
module = "Bindings.HttpPython"
package = "pypi:httpx"
targets = ["python"]
effects = ["network"]
assurance = "adversarial-response-with-reviewed-transport-boundary"
lock_ref = "REQUIRED_EXACT_RESOLUTION"

[bindings.httpPhp]
module = "Bindings.HttpPhp"
package = "composer:guzzlehttp/guzzle"
targets = ["php"]
lock_ref = "REQUIRED_EXACT_RESOLUTION"

[bindings.httpRust]
module = "Bindings.HttpRust"
package = "cargo:reqwest"
targets = ["rust"]
lock_ref = "REQUIRED_EXACT_RESOLUTION"
```

The last two intentionally omit contracts to illustrate incomplete proposals: the publisher must refuse them until their contracts, effects, realization status and exact locks are supplied. No placeholder is a default approval.

## 14. Effects, asynchronous code and stateful applications

A useful first application can keep framework orchestration outside the verified core. For example, a host reads a request, a generated adapter validates it, a verified function decides an allowed state transition, and the host performs the requested operation under an explicit integration contract.

Next, represent a small capability effect language in Lean. Prove its protocol and trace properties using full Lean. Supply target handlers separately. Do not lower arbitrary `IO` by erasing the monad and mapping names to host calls.

Mutable local variables can lower to explicit state or SSA when a checked transformation preserves the source meaning. Shared mutable objects require aliasing/frame reasoning and should not be introduced accidentally through foreign handles.

For database work, prove the decision/transition function first. Atomicity, isolation and durability depend on the database transaction boundary; an adapter must identify its required isolation level and failure model. A postcondition saying “saved” is not proof that a remote commit happened.

Defer a universal async/concurrency model. Promise, coroutine and Future APIs differ. A first async capability should specify whether callbacks run once, cancellation timing, permitted reentrancy, state after failure and which scheduler assumptions are needed. Add data-race or linearizability claims only with a matching model. Protocol safety can be proved without pretending to prove fairness or eventual service availability.

## 15. Worked design example

All snippets here are **illustrative proposals, not executed compiler receipts**. They use existing-style PS syntax where possible; generated proof interfaces and publication commands are new work.

### Runtime definition

`src/Allocation.ps`:

```lean
function grant(requested: Nat, available: Nat): Nat :=
  Nat.min(requested, available)
```

### Full Lean proof module

`proofs/AllocationProofs.lean`:

```lean
import Allocation

 theorem grant_le_available (requested available : Nat) :
     grant requested available <= available := by
   exact Nat.min_le_right requested available

 theorem grant_le_requested (requested available : Nat) :
     grant requested available <= requested := by
   exact Nat.min_le_left requested available

 theorem grant_exact (requested available : Nat) :
     grant requested available = Nat.min requested available := by
   rfl
```

The final generated module names/import visibility must be qualified by the mixed-source module implementation. The example is not a claim that those imports currently work in PS0. Broader proofs may use any compatible, pinned Lean library; no backend needs to implement the proof tactics.

### Independent obligations

The reviewed policy binds the exact exported declaration `grant` to these requirements and to a source-to-IR correspondence theorem. The required claim is stronger than a theorem merely stating that the result is a Nat. A deliberately wrong implementation returning zero would satisfy the two upper bounds but fail the exact-allocation requirement for many inputs.

A malicious edit replacing the contract with `True`, changing `Nat.min` through a different resolved environment, or pointing the export at another declaration must fail specification/identity checks even if some proof succeeds.

### Target-facing boundary

A JS/TS adapter validates nonnegative BigInt inputs before calling the internal function. Python rejects negative/non-integer values and does not treat Boolean input as an accepted Nat. PHP and Rust use the selected exact Nat representation. External callers do not acquire the source refinement merely because a generated signature says `bigint` or `int`.

The target certificate must cover the actual min implementation and the boundary behavior. The source proof alone does not authorize replacing min with a host floating-point operation. Resource and runtime realization assumptions remain explicit.

### Foreign data example

A Python HTTPX adapter or PHP Guzzle adapter may obtain a proposed available balance. A verified parser can prove that accepted balance data is a nonnegative integer. It cannot prove that the remote balance is truthful or current. To prove no overdraft across real requests, the application also needs a specified authoritative storage/transaction protocol. This distinction is central to useful, honest interoperability.

## 16. Project layout, packages and build artifacts

Proposed application layout:

```text
project/
  src/                 # .ps and eligible .lean runtime declarations
  spec/                # reviewed interfaces and requirements
  proofs/              # unrestricted Lean proving modules
  bindings/            # reviewed logical interfaces and target adapters
  tests/               # semantic, negative, boundary and consumer tests
  proofscript.toml     # proposed profiles, roots and obligation mapping
  lakefile.toml        # pinned Lean proof/build dependencies
  lean-toolchain
  locks/               # actual target dependency resolutions
  build/private/       # unpublished intermediate artifacts
  dist/<target>/       # only policy-approved bundles
```

Keep the compiler in one Lake project initially. Logical module boundaries need not become separate registry packages immediately:

```text
PS0/
  Syntax/ or existing Syntax.lean
  Extract/
  RuntimeIR/
  Evidence/
  Interop/
  Backend/Js/          # retained namespace, shared JS/TS runtime support
  Backend/TypeScript/
  Backend/Python/
  Backend/Php/
  Backend/Rust/
```

These are proposed additions, not a filesystem migration performed by this document. Do not duplicate the independent PSC0/PSC1 package architecture here.

A distributable compiler should be a standalone Lake package or qualified native binary with the required pinned Lean sysroot/modules. Users should not need a complete clone/build of the Lean fork merely to use PS0. Proving requires Lean; generated target applications should not require the Lean elaborator or tactics. Source-oriented target output still requires its target runtime/toolchain.

Artifact families:

| Target | Intended outputs |
|---|---|
| JS | ESM modules, package metadata, source maps, evidence manifest |
| TS | Restricted `.ts`, matching canonical JS or validated downstream output, `.d.ts`, maps, evidence |
| Python | Modules, annotations/stubs, packaging metadata, source-location sidecar, evidence |
| PHP | Namespaced source, Composer/autoload metadata, source-location sidecar, evidence |
| Rust | Crate source, Cargo metadata, resolved build configuration, source-location sidecar, evidence |

Do not call a Python/PHP/Rust location sidecar a standard JavaScript source map. Each debugger integration must declare what it actually supports.

### Release identity

Bind the bundle to source bytes, Lean pin, PS0 revision, reference/profile versions, proof/specification closures, elaborated declaration identities, IR, target AST and bytes, adapter/runtime identities, lockfiles, target flags, resource policy and evidence scope. Signatures identify an issuer but do not replace kernel proofs.

Use deterministic manifests and stable ordering. Avoid timestamps inside reproducible code content. Publish through a fresh staging directory and atomic rename; define crash recovery, concurrent writers and overwrite policy. Recheck artifact identity immediately before publication. A dependency update invalidates any certificate whose assumptions or realization identity changed.

## 17. Performance, maintainability and AI-assisted workflow

### Performance policy

Measure cold proof build, incremental edit, extraction, certificate replay, target validation, target compile/startup and runtime throughput separately. Do not invent latency targets before a representative workload exists.

Cache by exact source/environment/profile/target identity. Cache proof terms and checked artifacts, not just a Boolean “passed” flag. The final admission path must still establish validity for the exact candidate. An unchanged certificate can be reused through a justified validation path; a stale manifest cannot authorize changed code.

Reuse proof libraries and generic compiler-correctness lemmas so per-program proofs remain small. Benchmark monomorphization growth, proof term size, IR size, bigint overhead, conversion/copy costs and recursion depth. Add optimization only after profiling and require the same semantic gate for optimized output.

A full new grammar or parser rewrite is not a prerequisite for the first bounded profile. Qualify the precise source slice used, including negative ownership tests, while tracking full R2 conformance independently. Conversely, `.lean` pass-through is not evidence that the equivalent `.ps` frontend is complete.

### AI workflow

1. A human or accountable owner approves requirements, threat/resource scope and permitted assumptions.
2. Freeze a challenge/specification snapshot. AI implementation agents may not weaken it during repair.
3. AI proposes executable code, proofs, binding descriptions and extraction hints as untrusted inputs.
4. The system returns machine-readable goals and counterexamples where available, classified by phase.
5. Independent replay, correspondence checking and policy evaluation determine acceptance.
6. Review target artifacts, changed assumptions and specification coverage before publication.

Diagnostics should identify declaration, source span, obligation, target, unsupported operation, relevant dependency, expected statement, actual statement and evidence status. Distinguish `SOURCE`, `PROOF`, `PROFILE`, `EXTRACTION`, `BACKEND`, `FOREIGN`, `RESOURCE` and `PUBLICATION` failures.

Counterexamples, mutation tests and specification satisfiability witnesses help detect weak or vacuous contracts; they are not substitutes for proof. A precondition of `False` can make a theorem trivial, and a theorem about a substituted function can be irrelevant. Require explicit review of these changes and keep the candidate proof environment separate from the trusted challenge.

Refactoring and dependency updates must preserve the applicable statement/extraction relation or trigger re-verification. Do not optimize for theorem count, token count or the number of green generated tests. Measure useful reviewed properties discharged and regressions prevented.

## 18. Main risks and decision experiments

| Risk | Concrete experiment | Stop / change decision |
|---|---|---|
| Current PS0 does not compile | Run focused and full exact-pin Linux workflows | Fix baseline before feature expansion; no inferred PASS |
| Proof refers to a different declaration | Mutate body, namespace, import and export binding | Gate must reject mismatches despite valid unrelated proofs |
| Extraction is too broad | Admit a small Nat/Bool fragment, reject unknown constants | Reduce profile rather than silently trust unsupported lowering |
| Native replacement breaks source correspondence | Use a safe signature with `implemented_by`/extern replacement | Require explicit primitive realization or refusal |
| TS output diverges from JS | Compare restricted erasure and actual emitted JS | Refuse unvalidated bundling/transforms |
| Integer/text semantics differ | Huge integers, negative division, zero divisor, non-BMP text, invalid encodings | No backend release until policies and relations are explicit |
| Foreign contract hides state/effects | Callback twice, reentrancy, stale data, mutation-after-validation, exceptions | Tighten adapter ownership or use isolation |
| Generic/closure compilation explodes | Measure representative higher-order libraries and specialized graph size | Keep higher-order feature optional until bounded strategy is proved |
| Recursive program overflows host stack | Deep input corpus and iterative/trampoline candidate | State resource limit or prove stack-safe lowering |
| Proof erasure deletes computation | Erased-result effect fixture and dependent representation fixture | Reject unsafe erasure rules |
| “Correct” specification is vacuous | Mutate preconditions/specification and introduce shadowed meanings | Require challenge binding and human specification review |
| Certification gate is bypassed | Forged receipts, changed bytes, stale caches, unknown runtime version | Fail closed and preserve previous output |

The central research uncertainty is not whether a tiny verified vertical slice can be designed; it is the cost of scaling useful extraction and target semantics without an oversized compiler or false guarantees. Resolve that with prototypes and exact proof/runtime evidence, not broad completion percentages.

## 19. Phased roadmap and measurable gates

These MB stages are new proposal milestones, not replacements for the existing R2 G0–G4 plan. No stage is marked completed by writing this document.

| Stage | Deliverable | Acceptance evidence |
|---|---|---|
| MB0 — Baseline and trust harness | Exact-pin PS0 build; upstream replay/comparator integration experiment; documented runtime inventory | Inspected Linux Actions logs at exact commits; correct positive/negative outcomes; unchanged R2 identity |
| MB1 — Proof-bound executable slice | Nat/Bool functions, explicit exports, separate full-Lean proofs, immutable challenge mapping | Correct program accepted; missing/false/irrelevant proofs, body swaps and unapproved axioms rejected; no release artifact on failure |
| MB2 — Extraction theorem | Typed IR semantics and proof-producing extraction for the slice | Kernel-checked per-program correspondence; unknown primitives refused; source and IR mutations rejected |
| MB3 — JS/TS vertical release | Restricted target semantics, emitter/serialization evidence, checked entry wrappers, real TS consumer | Exact-byte correspondence; JS/TS relation; runtime differential corpus; hostile inputs; deterministic output; policy-approved package |
| MB4 — Practical core and modules | ADTs, records, collections, structural recursion, selected generics, mixed-source graph | Family-specific source/extraction proofs, module visibility tests, erasure and resource negatives; independent R2 ledger remains honest |
| MB5 — Python backend | Same eligible IR with Python representations and adapters | Cross-backend semantic corpus plus Python-specific type/exception/stack/boundary gates; no inference from JS results |
| MB6 — Rust then PHP | Owned Rust adapters and exact PHP representations | Separate source-correspondence/runtime matrices, Cargo/Composer consumer builds, integer/text/ownership regressions |
| MB7 — Capability applications | One real foreign-library integration per ecosystem and a specified effect protocol | Explicit assumption receipts or realization proofs; injected foreign failures; reviewed end-to-end claim and deployment scope |

Start with the allocation example or another similarly small business rule, not a universal language translation project. MB3 is the first meaningful multi-output vertical product milestone; MB4 expands usefulness without waiting for all five backends. Shipping an unfinished backend is not needed to demonstrate the architecture.

For every stage record five independent fields: specified, implemented, fixture-linked, executed at exact identity, and qualified for a named outcome. Coverage denominators must be stable and scoped. Positive and negative tests need intended phase/diagnostic oracles, not “any failure counts.”

### Mandatory test families

- Logical: standard-axiom policy, `sorryAx`, bespoke native-computation axioms, changed propositions and altered dependency closure.
- Extraction: same signature/different body, swapped instances, unsafe substitutions, unsupported recursion and runtime noncomputability.
- Target semantics: overflow, subtraction, division/zero, Unicode, tags, map ordering, aliasing, evaluation order and large recursion depth.
- Interop: forged type metadata, invalid values, unexpected mutation, callback lifetime/cardinality, exceptions, cancellation and dependency mismatch.
- Publication: stale certificate, altered output bytes, unsupported runtime tuple, collision-safe structural checks, race/crash cleanup and no partial bundle.
- Consumers: actual `tsc` checks, Python import/execution, PHP syntax/Composer consumer, Cargo build/test and JS ESM/CJS cases where supported.

Testing is qualification evidence, not a replacement for the semantic theorems required by the policy.

## 20. Research sources and validation receipt

### Source discipline

Repository claims are tied to the immutable audit base. External references below are primary documentation, standards, project-maintainer documentation or project publications, consulted on 2026-10-29. Mutable `latest` pages inform this design; they do not change the Lean 4.35 semantic pin. Specific implementation API details must be rechecked against that pin before coding. No ecosystem version mentioned on a live page is automatically a supported PS0 target.

The discussion uses short source-derived findings; architecture choices, policy rules and roadmap decisions are original proposals. No other verifier's correctness result is imported into Lean by citation alone.

### Primary references

- [U01] Lean 4.35.0 release notes, proof checking/comparator and compiler-trust changes: https://lean-lang.org/doc/reference/latest/releases/v4.35.0/
- [U02] Lean, Validating a Lean Proof: https://lean-lang.org/doc/reference/latest/ValidatingProofs/
- [U03] Lean, Elaboration and Compilation: https://lean-lang.org/doc/reference/latest/Elaboration-and-Compilation/
- [U04] Lean, ImplementedByAttr API: https://lean-lang.org/doc/api/Lean/Compiler/ImplementedByAttr.html
- [U05] F*, Executing programs and extraction boundary: https://fstar-lang.org/tutorial/book/part1/part1_execution.html
- [U06] Dafny reference manual, verification/compilation/extern interfaces: https://dafny.org/dafny/DafnyRef/DafnyRef
- [U07] CompCert C correctness overview: https://compcert.org/man/manual001.html
- [U08] CakeML project, proof-producing frontend and verified backend: https://cakeml.org/
- [U09] Verus, assumptions and trusted components: https://verus-lang.github.io/verus/guide/tcb.html
- [U10] Creusot maintained changelog, external specifications: https://github.com/creusot-rs/creusot/blob/master/CHANGELOG.md
- [U11] Why3 tools and extraction: https://why3.org/doc/manpages.html
- [U12] Viper verification infrastructure: https://viper.ethz.ch/tutorial/introduction.html
- [U13] Idris 2 FFI: https://idris2.readthedocs.io/en/latest/ffi/ffi.html
- [U14] Agda FFI and compiler pragmas: https://agda.readthedocs.io/en/latest/language/foreign-function-interface.html
- [U15] Rocq 9.0 extraction documentation: https://rocq-prover.org/doc/V9.0.0/refman/addendum/extraction.html
- [U16] Lean axioms and native-evaluation assumptions: https://lean-lang.org/doc/reference/latest/Axioms
- [U17] ECMAScript data types and values, String/BigInt: https://tc39.es/ecma262/multipage/ecmascript-data-types-and-values.html
- [U18] Python built-in types: https://docs.python.org/3/library/stdtypes.html
- [U19] PHP integers and overflow: https://www.php.net/manual/en/language.types.integer.php
- [U20] PHP string representation: https://www.php.net/manual/en/language.types.string.php
- [U21] TypeScript compatibility and soundness limitations: https://www.typescriptlang.org/docs/handbook/type-compatibility
- [U22] Node package/module interpretation: https://nodejs.org/api/packages.html
- [U23] Python typing and runtime enforcement boundary: https://docs.python.org/3/library/typing.html
- [U24] Rust undefined-behavior boundary: https://doc.rust-lang.org/reference/behavior-considered-undefined.html
- [U25] Cargo dependency specifications: https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html
- [U26] Composer dependency locking and autoloading: https://getcomposer.org/doc/01-basic-usage.md
- [U27] Zod official documentation: https://zod.dev/
- [U28] HTTPX official documentation: https://www.python-httpx.org/
- [U29] Guzzle official documentation: https://docs.guzzlephp.org/en/stable/
- [U30] reqwest maintainer API documentation: https://docs.rs/reqwest/latest/reqwest/

### Validation status at authorship

| Check | Evidence obtained | Does not establish |
|---|---|---|
| Live base identity | GitHub branch read returned `775f03481bcf4636c6a5e3730353f00823b1bfec` | A successful compiler run |
| Normative identity | PS0 tree records R2 blob `c50203f8e4cb79b3e6680088a07c1d1e145b8f0b` | Full source conformance |
| Existing CI | Branch-wide Actions query returned zero runs | That every compiler feature is broken or absent |
| Research | Repository source audit plus primary-source review above | Formal proof of this architecture |
| Example code | Design illustrations only | Tested Lean or backend execution |
| New architecture | Documentation proposal | Implemented profile, binding package, target semantics or certificate checker |

A documentation-only Linux workflow may validate this document's structure, references and preserved baseline identities. Its success would be documentation validation only. Compiler, proof and runtime results must be reported separately with actual run IDs and inspected logs. No local compiler build, package publication, main-branch merge or change to the existing normative reference is part of this task.
