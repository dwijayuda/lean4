# PS0 — Full PSCV0 v7 Implementation Plan on Lean 4.35.0

**Status:** source-grounded implementation plan, not a completion, successful stable-build, or verified-native-execution claim.  
**Prepared:** 2026-10-15. **Project:** `dwijayuda/lean4`, `experiments/ps0/`, draft [PS0 PR #5](https://github.com/dwijayuda/lean4/pull/5), branch `feature/ps0-lean435-stable-v1`.  
**Pinned official Lean:** `v4.35.0`, commit `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.  
**Normative language authority:** [PSCV0 v7 reference in dwijayuda/pskernel](https://github.com/dwijayuda/pskernel/blob/f79d334ef922eb7f71f7527dbc798ebb0dbeb610/psc0/PSCV0_LANGUAGE_REFERENCE.md) (Git blob `25e1ef788794db175a2183679e37ff8c8e9b6a2e`). The **2026-10-14 stable pin amendment** at its beginning supersedes the historical RC4 pin cited in older sections. Source grammar ownership is ``0A/0B`; detailed language semantics ``1–12`; normative test/evidence matrix ``13–14`.
**Isolation:** PS0 lives in the user's Lean fork. Preserve the current independent multi-backend PSC0 in `dwijayuda/pskernel` and its PR #109. Do not replace, rewrite, merge or discard PSC0. Preserve the older PS0 parent experiment branch and upstream Lean sources.

## Source-extension boundary amendment — 15 October 2026

**Normative PS0 direction:** v7 source-language policy applies **only**
to `.ps` files. An ordinary `.lean` source is always delegated to the
official Lean 4.35.0 executable and is not filtered through ProofScript
grammar, `#pscv_gate`, source axioms, effect restrictions, or
PSCV0-only declarations. Thus native Lean `axiom`, `sorry`, `unsafe`,
`partial`, imports, user tactics/macros and unrestricted `#eval` retain
ordinary Lean behavior. Source extension classification must occur
*before* selecting a compiler frontend.

PS0 implements `ps0 lean <native arguments...>`, `ps0 check file.lean`
and `ps0 build file.lean Name out/` through a separate OS process that
executes the Lean binary inside the selected sysroot. This prevents the
PS0 executable's imported syntax/policy registrations from leaking into
a native Lean module. The ordinary native route produces no PSCV0
verified-source claim. The `.ps` route continues to enforce all selected
v7 restrictions. See [SOURCE_PROFILE_BOUNDARY.md](SOURCE_PROFILE_BOUNDARY.md).

**Acceptance obligation:** CI must demonstrate unrestricted native
`.lean` with `axiom`, `unsafe`, `partial`, `sorry`, and effectful
`#eval`, while the corresponding `.ps` inputs fail closed. Any future
mixed-module graph keeps `.lean` semantics unrestricted but audits
its imported dependencies when a `.ps` verified executable uses them.
The 20-family v7 completion rubric applies only to `.ps`; do not count
native Lean capabilities or this routing improvement as completed v7
language features.

## 1. Objective, guarantees and deliberate non-goals

Build a **complete PSCV0 v7 compiler variant called PS0** with authoritative `.ps` files, precisely v7-selected syntax and Lean-compatible semantics. Use the **PS0-owned, reviewed adaptation** of the historical Lean-native PSCVL syntax macros and grammar validator now in `experiments/ps0/PS0/` (not the independent PSC0 portable parser), while the **official Lean 4.35.0 elaborator, type system, termination checker, tactics, kernel and native compiler** perform their real work. No second PS0 typechecker, no new dependent unification engine, no separate kernel, and no parallel JS/Rust/Wasm backend.

```text
source .ps + project manifest + pinned Standard/profile
  -> immutable source/module graph and UTF-8 origin spans
  -> PS0-owned v7 syntax-category validator (adapted from PSCVL; Lean parser)
  -> hygienic source-syntax-to-native-Lean-Syntax lowering
  -> official Lean elaboration + tactic and VC generation + kernel
  -> original checked declarations + transitive assumptions/spec/effects audit
      -> ordinary: kernel-checked SOURCE, native compiler assumptions declared
      -> verified: all mandatory SOURCE proofs/obligations closed and audited
  -> official Lean LCNF/C/native compilation via checked session
  -> output staging, provenance/identity verification, fail-closed publication
```

**Separate finish-line claims:**

1. **Full v7 source conformance**: every selected P0 grammar/semantic rule (and every P1 requirement mandated by the normative v7 product profile) has positive AND intended-phase negative tests; elaborated Lean Core and proof term semantics are equivalent to source rules; all selected library and module registrations are frozen.
2. **Full v7 native-capable implementation**: every v7 feature that is computationally executable has a qualified native interpretation through the official Lean compiler, with explicit effects/FFI contracts and no silent alternate runtime.
3. **Full v7 verification-policy implementation**: every mandatory source spec/proof/VC/effect/assumption/erasure obligation is enforced, including transitive imports and generated proof terms, before a verified **source-contract** claim is issued. Native executable fidelity is a separate assurance property: without compiler/runtime refinement evidence, say **verified source, Lean-native compiler/runtime assumed**, NOT universally verified machine code.

A green bounded test suite, a printed `UNCERTIFIED` label, or kernel-checking a theorem is not completion of all three claims. Do not quietly weaken v7 to become an easier Lean subset. Deferred P2 async/ownership/UI syntax is **not** an automatic v7 blocker unless reclassified as normative by an explicit specification revision.

## 2. Audited starting point (not a newly validated release)

| Existing source / receipt | What actually exists | Critical gap |
| --- | --- | --- |
| `experiments/ps0/PS0Main.lean` + `lakefile.toml` | Separate PS0 CLI with `check`, `build`, `environment`, `syntax-kinds`, and a stable toolchain guard | New stable-4.35 PS0 CI not independently confirmed green at plan creation |
| `PS0/Syntax.lean` | Owns the adapted Lean-native syntax bridge. Nullary Unit sugar now applies only to `function`; non-callable `f()` is rejected; head-specific `def`/theorem/ctor binders are tightened. | Full v7 semantic coverage and stable-4.35 qualification remain open |
| `PS0/Grammar.lean` | Owns closed command syntax. Ambiguous `choice` now requires *every* candidate to be permitted, rather than accepting any one. | Conservative rule may reject some valid source; exact resolved-parser choice audit remains open |
| `PS0/Policy.lean` | PS0-owned local `#pscv_gate`, prohibition of source `unsafe`/`partial`/`axiom`/`sorry` and local-transitive assumption checks | Imported provenance/spec/effect/erasure closure incomplete; inherited `Classical.choice` allowance is explicitly disclosed |
| `PS0/Effect.lean` | PS0-owned Lean-grounded relations and proofs for pure, reader, state and typed-error WP | Not complete P0/P1 effect capability or external-world boundary model |
| `PS0/StandardEnv.lean` + `PS0_STANDARD_ENV.json` | Local pinned 4.35.0 Standard manifest, no sibling package dependency | No complete modules/instances/notations/tactics/effects/axioms/priority/exposure snapshot |
| Historic [Lean-native RC4 workflow](https://github.com/dwijayuda/lean4/actions/runs/38112654962) | 37 accepted, 56 rejected `.ps` fixtures, native executable, two basic `rfl` correspondences | **RC4** run is not a new stable PS0 acceptance or full normative v7 coverage |
| `.github/workflows/ps0-lean435.yml` | PS0 branch CI definition for stable toolchain, selected tests and C/olean artifact checks | Exact-commit passing CI and end-to-end native linker execution still require confirmation |
| Current `PS0Main.buildFile` | Separate `checkFile` and `runFrontend` calls; direct output creation | Need immutable checked source snapshot and staged atomic/recoverable publication; no assumptions about source unchanged between checks |

**Important distinct ownership:** PSC0's portable syntax parser, independent elaborator and JS/TS/Rust/Wasm backends stay in `dwijayuda/pskernel`. PS0 owns an **independent adapted copy** of the historical Lean-native PSCVL frontend and uses the official Lean native backend. Do not carry over PSC0 differential/runtime qualification receipts into PS0.


### 2.1 Standalone implementation checkpoint (2026-10-15)

Following this roadmap's creation, PS0 gained source-owned `PS0/Syntax.lean`, `Grammar.lean`, `Policy.lean`, `Effect.lean`, and `StandardEnv.lean`; a root `PS0.lean` and local `PS0_STANDARD_ENV.json`; no sibling Lake dependency; and a PS0-only sparse-checkout CI. The historical PSCVL package's original RC4 toolchain/manifest were restored, so this branch does not need to change its source to compile PS0. See [CONFORMANCE.md](CONFORMANCE.md) for each module's actual adaptation and gap classification.

Specific semantic fixes: head-specific Unit insertion only for nullary `function`, rejection of empty calls on non-callable values, refusal of ambiguous command parses unless every alternative meets the command allowlist. Current native `build` validates syntax then uses a **single authoritative Lean frontend run**, staging C and olean before one directory-level rename; it forbids replacing an existing bundle. CI now asserts previously published output hashes survive a rejected overwrite. These are **implementation candidates awaiting exact-commit CI**, not full v7 source/parser closure or verified runtime evidence. Multi-module checked-graph identity, source-position correspondence and versioned release manifests remain PS0-09/10 blockers.

## 3. Lean 4.35.0 source concordance and reuse constraints

Every substantial feature must begin with a short pin-specific source/test note: what Lean's exact parser/elaborator/compiler does; what v7 permits/forbids; whether a hygienic macro is sufficient or a targeted Lean term elaborator is necessary; corresponding kernel/negative tests. Prefer the native API; never implement a second semantic solver.

| Stable pinned Lean file | PS0 application |
| --- | --- |
| [`src/Lean/Parser/Basic.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Parser/Basic.lean) and [`Parser/Term.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Parser/Term.lean) | Lexer, comments, UTF-8/trivia, application positions, type syntax, matching, records, syntax quotations |
| [`Parser/Command.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Parser/Command.lean), [`Parser/Do.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Parser/Do.lean) | Declaration grammar, modifiers, braced `do`/try/while/for, selected verified-do forms. Lean also parses indentation forms; PS0 explicitly refuses v7-disallowed ones |
| [`Parser/Module.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Parser/Module.lean), [`Elab/Import.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Import.lean) | Actual module header/import flags; `public import`, public vs private module declarations and body exposure, no textual import replacement |
| [`Elab/Term.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Term.lean), [`Elab/Command.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Command.lean), [`Elab/Match.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Match.lean) | Lean expression/type elaboration, dependent motives, pattern coverage, universe and metavariable solving |
| [`Elab/Structure.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Structure.lean), [`Elab/Inductive.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Inductive.lean), [`Elab/Deriving/Basic.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Deriving/Basic.lean) | Structures, indexed inductives, classes, instances, deriving handlers |
| [`Elab/MutualDef.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/MutualDef.lean) | Definition termination, structural/WF/mutual recursion, optional local equations |
| [`Elab/Tactic/Do/Contract.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Tactic/Do/Contract.lean), [`VCGen.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Tactic/Do/VCGen.lean), [`Std/WP/Basic.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Std/WP/Basic.lean) | Contract expansion to real `f.spec` theorem, `@[spec]` registration, `vcgen`/WP, proof of total/error-state and other selected verification effects |
| [`Elab/Frontend.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Elab/Frontend.lean), [`Compiler/LCNF/EmitC.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Compiler/LCNF/EmitC.lean) | Official checked frontend path to native code; not a verified compiler-preservation theorem |
| [`Compiler/NoncomputableAttr.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Compiler/NoncomputableAttr.lean), [`Server/FileWorker.lean`](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Lean/Server/FileWorker.lean) | Noncomputable executable restriction and Lean-native InfoTree/LSP task/source handling |

Official supplemental docs: [Lean 4.35.0 release notes](https://lean-lang.org/doc/reference/latest/releases/v4.35.0/) (introduces `vcgen` and `lake check`/`lake comparator`), [syntax/macros](https://lean-lang.org/doc/reference/latest/Notations-and-Macros/Macros/), [elaborators](https://lean-lang.org/doc/reference/latest/Notations-and-Macros/Elaborators/), [modules](https://lean-lang.org/doc/reference/latest/Source-Files-and-Modules/), [`vcgen` reference](https://lean-lang.org/doc/reference/latest/The--vcgen--tactic/). Code at the exact stable pin wins over moving documentation.

## 4. Core architecture and trust boundaries

### 4.1 One source/grammar authority

The migration is now self-contained: `PS0/{Syntax,Grammar,Policy,Effect,StandardEnv}.lean` and `PS0Main.lean` live in one Lake package; there is no sibling `require`. The prior PSCVL code is historical provenance only, not a second runtime or grammar authority. Proposed future decomposition: `SourceProfile.lean` (finite category registry), `Parse.lean` (source bytes/trivia), `Lower.lean` (hygienic quotations), `Modules.lean` (imports/visibility), `Standard.lean` (environment identity), `Contracts.lean` and `ProofPolicy.lean` (verified claim gates), `Compile.lean` (checked compilation session), `Publication.lean` (staging), `Diagnostics.lean` (origins/InfoTree). These are **target file names**, not asserted existing modules.

- Source grammar is `0B`'s closed Lean-category overlay. Select a **resolved** AST alternative, not “any alternative is allowed”; forbid source-supplied new macros, arbitrary attributes, tactics, parsers, elaborators and `run_tac/run_cmd` before execution.
- After macro expansion, audit produced syntax/handler identities and check real Core. Do not turn a validator into a separate elaborator.
- Native Lean may execute imported tactic/initializer code during elaboration: in-process parser restrictions alone are not a security sandbox. Only audited trusted handlers; isolate untrusted extension execution with OS/resource controls where applicable.
- Forbid user `sorry`/`sorryAx`, `partial`, `unsafe`, `axiom`, unchecked casts and unapproved meta syntax, including nested code. Keep Lean-generated `_unsafe_rec` helpers for safe total parent declarations distinct from source unsafe; do not silently confer verified machine-runtime status.

### 4.2 One immutable checked project snapshot

Before parsing, freeze exact source bytes, paths, UTF-8 spans, module IDs, import closure, selected pinned module metadata, environment/option/notation/tactic/deriving registrations, approved effect/foreign capabilities and requested claim. Hash the canonical ordered graph. Parse and elaborate against this snapshot; no reading new source bytes between `check` and `build`.

`PS0Main.buildFile` currently calls `checkFile`, reads input again, then calls `runFrontend` with text-constructed imports plus `#pscv_gate`. Replace this with one checked source graph/environment handed to the official compiler. If distinct frontend invocations are unavoidable, require exact checked-declaration graph/scope/assumption/option identity before emission, not mere text equality.

**State machine:** `OPEN → SNAPSHOTTED → GRAMMAR_CHECKED → ELABORATED → KERNEL_CHECKED → POLICY_CHECKED → OUTPUT_STAGED → VERIFIED_FOR_CLAIM → PUBLISHED`; any failure = `DECLINED` and zero new published outputs. Include checked hashes of generated `.olean`, C, objects/executable, maps and manifests. Use private staging, destination/path/symlink/collision checks, crash recovery and prior-output preservation.

### 4.3 Lean modules versus ProofScript exports

Pinned Lean 4.35 modules support `public import`, `meta import`, `import all` and exposure modifiers. PSCV0 v7 instead specifies **source declarations public by default, but their implementation bodies unexposed by default**. Lower this rule into Lean's real module/public-scope AST. Do not simply treat imported module names as strings or use unrestricted public Lean syntax to bypass v7 profile restrictions. Preserve imported `f.spec` and theorem visibility correctly.

### 4.4 Ordinary source versus verified output

**Both** normal and verified output share the same v7 source language and official Lean kernel. The normal compile route admits only selected total typed source and declared external boundaries but makes no proof of application behavior. The stricter verified route checks all required contracts, caller preconditions, loop invariants/termination, specification coverage, imported trust assumptions, effect/frame models and erasure semantics. The inherited policy currently admits `Classical.choice` along with `propext`/`Quot.sound`; log and review its presence, and freeze a separate stricter verified assumption profile instead of pretending PS0 equals PSC0's more restrictive portable environment.

**No unjustified runtime correctness claim:** Lean kernel checking proves source propositions relative to the trusted assumptions; it does not prove the generated native executable preserves those propositions. Output claims must distinguish source proof, policy-verified source, native-compiler/runtime/FFI assumption, and separately established semantic refinement.

## 5. Full normative feature inventory (source + semantics + acceptance)

**Status below refers only to partial historical Lean-native PSCVL coverage**, not an independently passed stable PS0 v7 release.

| Requirement (v7 reference) | Status | Correct implementation ownership and minimum evidence |
| --- | --- | --- |
| S01 lexing, identifiers, comments, source layout (`1/`12`) | Partial | Lean lexer and UTF-8 spans; valid nested comments, invalid C-style lexing; role-specific trivia acceptance |
| S02 `def/function/const/theorem`, attributes and modifiers (`2, `11.3`) | Partial | Hygienic native declaration lowering; distinct nullary/function rules, `noncomputable` proof-only restrictions |
| S03 ordered explicit/implicit/strict/instance binders (BIND-01/02; `0B`) | Partial | Lean binder elaboration plus canonical group/adjacency validators; dependent defaults and section variables |
| S04 adjacent/mixed/named/default/partial/`Unit` calls (APP-01..04) | Partial | Lean term elaboration `elabAppArgs`; no-gap semantics; `f()` only defaults or one required definitionally-`Unit` |
| S05 namespaces/sections/`open`/`include/omit`/visibility (`1`) | Partial | Native Lean generalization, theorem-header and fixed recursion variable rules |
| S06 `.ps` modules, `public import`, source-public names and hidden bodies (MODULE-01/02) | Missing | Lean module AST and import closure, path-safe project graph and actual public/exposure checks |
| S07 universes/Prop/Type/Sort/Pi/quantifiers/coercions (`3`) | Partial | Native universe and dependent elaboration, genuine `∀/forall` and `∃/exists` spellings |
| S08 literals, Float/words/BitVec/strings/arrays/tuples (`3/`8`) | Partial | Exact pinned Lean values/conversions, native scalar semantics and boundary fixtures |
| S09 dependent `if`, `if let`, `matches`, pattern let (`3/4`) | Partial | Native dependent branching, selected braces and necessary surface-only sugar |
| S10 structures/records/updates/classes/instances/inheritance (`4`) | Partial | Native structure and class elaboration; defaults/dependent fields and instance priority/coherence |
| S11 indexed inductives, motives, patterns, multi-match, `nomatch` (`4`, PATTERN-01) | Partial | Lean recursors/Match, constructor vs call grammar separation, `k+1`/`k+2` and impossible cases |
| S12 total structural/mutual/WF/equation recursion (`5`) | Partial | Native Lean termination and mutual-definition APIs; explicit negative nontermination |
| S13 theorem syntax, tactics, `·` bullets, `#check/#reduce/#eval` (`6/`7A`) | Partial | Lean kernel/tactics and selected pure diagnostic evaluator; forbid ASCII dot bullet and unregistered extensions |
| S14 braced base `do`, `let mut`, verified loops, `assert`/`erased` (`3/`7`, DO-SELECT-01) | Partial | Native Parser.Do and experimental verification; mandated loop invariants/decreasing proof |
| S15 `given/requires/ensures`, `where finally | spec` and `vcgen` (`7`) | Partial | Native `Contract.lean` generates real `f.spec`; check exact generated theorem, proof discharge and cross-module ownership |
| S16 typed `throw/try/catch/finally`, reader/state/error/foreign effects (`7B`) | Partial | Native `Std.WP`, selected P1 effect module identities, typed successes/failures and frame proofs |
| S17 P0 collections/String/ByteArray/basic APIs and required P1 map/set/JSON/codecs (`8A`) | Partial | Pinned actual Lean modules/APIs, no invented symbols, explicit runtime/boundary signatures |
| S18 selected deriving, notation, instance ordering, tactic/module/axiom snapshots (`0B`/`8/`14`) | Provisional | Complete reproducible environment identity, not just a module-name JSON file |
| S19 fail-closed verified policy and original-source/native output (`7B`/`14`) | Partial | Full import/VC/effect/assumption/erasure evidence and single authority to publish |
| S20 source maps, formatter/Lean projection, InfoTree/IDE (`7A`/`14`) | Missing | Source byte-origin, Lean correspondence, parse-print-parse and LSP proof-state positions |

**P0/P1 decision:** P0 selected language/verification and minimal practical API are mandatory. P1 capabilities specifically required by `7B` and `8A` (typed exceptional paths, selected map/set/JSON codec and declared world-boundary interfaces) must be supplied as actual audited libraries or formally classified as optional/conditional by the authoritative spec, never silently skipped. P2 async/ownership/UI syntactic extensions remain outside initial v7 closure.


## 6. Milestone execution plan (PS0-specific, acceptance-gated)

These milestones **PS0-00 to PS0-11 are separate from** PSC0's original M0–M5/A–E and backend C0–C5 milestone sequence. The aim is to finish **all v7 language coverage with the fewest architecture changes**, not to rerun completed research, port another kernel or repeat massive CI on every edit. Each milestone should be delivered as one or more coherent source-family PRs. Require exact-commit evidence before marking it complete.

| Milestone | Ordered implementation tasks and reusable Lean owner | Acceptance / exit evidence |
| --- | --- | --- |
| **PS0-00 — stable baseline and CI** | Inspect current branch/PR/CI; pin stable 4.35.0 in the PS0-owned toolchain/manifest (leave the old PSCVL RC4 experiment untouched); compile the actual source and resolve RC4→stable incompatibilities from pinned Lean source. Execute inherited 37 positive and 56 negative fixtures, native build plus `leanc` link/run and resource baseline. Never label old RC4 results as stable-qualified. | One exact commit has successful full PS0 CI; logs record Lean commit, full positive/negative count, rejection reasons, native program execution, selected environment identity and cold/warm startup baseline. |
| **PS0-01 — closed syntax/grammar ownership** | From v7 `0B` enumerate selected `command`, `term`, `binder`, `tactic`, `doSeqItem`, `match_pattern`, `structField`. Resolve parser `choice` to the actual admitted branch, eliminate silent unselected Lean fallbacks, restrict imports' handler registrations, inspect post-macro trees. Extend source trivia, braces and initial source offset tracking. | Every `APP-01..04`, `BIND-01/02`, `DECL-01`, `PATTERN-01` and ownership rule's malformed cases reject at the **correct stage**; valid binder/fresh-term grouping unaffected. |
| **PS0-02 — syntax sugar / Lean Core parity** | Complete head-specific `const/def/function/theorem`, typed/default/named args, unit/nullary `f()`, adjacent and native juxtaposition calls, lambda/forall/universes/coercion, source position, `section` generalization. Use Lean `elabAppArgs` and native defeq, not another unifier. | `f(x,y)`, `f((x,y))`, `f(())`, `f()`, `useAlias()`, `f x(y)` and named defaults have the intended Lean Core, with precise error-phase tests for spaced applications/comment gaps and non-callable values. |
| **PS0-03 — source graph / multi-module visibility** | True `.ps` modules, `public import`/plain `import`, optional allowed `module` header, namespace/name identities, default-public-name/non-exposed-body translation to real Lean module AST; paths/lockfile/graph and Lake integration. | Multi-file app and import/export theorem cases pass, cross-module `f.spec` preserved, public name/private/exposure/cycle/path/duplicate-name/version refusals qualify. No unrestricted Lean imports. |
| **PS0-04 — dependent data / total recursion** | Finish structures/classes/instances and field/default/inheritance, indexed inductives/universes, constructor syntax, record updates, generalized/multiple `match`, inaccessible/as patterns, `nomatch`/`matches`, pattern-`let`, structural/mutual/WF/equation-style recursion. All type/termination logic remains Lean-native. | Real dependent Vec, impossible-match, named motives, shadowing and structurally decreasing examples pass; incorrect motives/index equalities/nontermination fail with correct ELAB/VC reason. No source `partial` escape. |
| **PS0-05 — Standard/P0 and source semantics snapshot** | Select exact Lean `Init`/`Std` module APIs and docs, Lean syntax/notational registry, instances/priorities/defaults, coercions, deriving handlers, tactics, proof assumptions; scalars/Float/BitVec/Word, List/Array/Option/Except/ByteArray/String/GetElem; curated conversion/formatting. P1 map/set and typed JSON/codec requirements must be named and versioned separately. | Deterministic digest over actual source/runtime-relevant and proof-environment state. Namespace/priority/handler drift refuses. Every required P0 API has positive/negative behaviors and pinned symbol identities; no fabricated platform functions. |
| **PS0-06 — proof language, intrinsic contracts and VC** | Complete selected proof/tactic grammar, bullets and inspection commands; `given/requires/ensures` clauses, `f.spec` generation, exact `where finally | spec`, `@[spec]` import/export/goal association; reuse `Std.WP` and `vcgen`, track generated proof/assumption closure. | Every mandatory VC really discharges; false specifications, missing `spec`, wrong theorem identity, open goals, wrong import or extra unregistered tactic are rejected and do not produce verified approval. |
| **PS0-07 — verified control, effects and P1** | Selected braced `do`, typed `let mut`/assignment, `if/if let` branches, `for`/`while` with required invariant/decreasing, `assert`/`erased`, typed `throw/try/catch/finally`; pure/reader/state/error WP and frame/effect semantics; real map/set/JSON and typed IO boundary adapters where required. | Normal/exceptional paths, loop variants, erasure and frame theorems checked; missing decrease, fake effects, incomplete error postconditions, unmodelled IO and unsupported foreign data refuse verified status. |
| **PS0-08 — full source assurance gate** | Freeze scope and policy for all source/transitive imported/generated constants; reject forbidden axioms/proof holes/unsafe/partial and executable noncomputable paths; build coverage ledger for contracts, assertions, effects, erasure and approved logical foundations, with distinct ordinary/verified outputs. | Inject each unsound/incomplete dependency in a source and imported module: explicit ASSURANCE/ELAB/VC refusal, no new verified artifact and no unauthorized widening of the assumption roster. |
| **PS0-09 — checked native build authority** | Replace double frontend/source read with one immutable snapshot and checked declaration graph; call official native Lean compiler; validate C/olean/linked outputs and effects/profile; secure private staging with digest/provenance and rollback-safe publication. Add platform and resource admission. | Representative project executes the intended observable results; invalid VC/changed source/unsafe import/link failure never replaces a valid published bundle; exact toolchain and checked graph bound to output. |
| **PS0-10 — developer experience and PS/Lean views** | Preserve original `.ps` spans through macros, generated spec/recursor names, emit optional read-only Lean source/Core view and PS formatter, Lean InfoTree/goal/LSP integration, stable diagnostic phases/IDs. Retain original files as authority. | Source-target mappings for Unicode, nested `by`, `where finally`, dependent matches and modules; parse-print-parse and elaborated-equivalence checks; editor displays correct original `.ps` positions. |
| **PS0-11 — full conformance and release** | `v7-coverage.json` from all normative selected IDs, independent Lean stable references, clean Linux/native and optional Windows smoke, reproducible environment/output manifests, regression/performance/license review, documentation. Separate language/native/verified-source release receipts. | **All normative mandatory cases and acceptance criteria** have exact-commit PASS evidence; no incomplete must-have category or incorrectly elevated machine-execution claim. Only then consider v7 language complete. |

### 6.1 Dependency graph / parallel work

```text
PS0-00 Stable baseline
   |
PS0-01 Closed categories / parse
   |
PS0-02 Core source lowering
   +--------------------+--------------------+
   |                    |                    |
PS0-03 Projects      PS0-04 Data        PS0-05 Standard registry
   |                    |                    |
   +-------------+------+--------------------+
                 |
        PS0-06 Contracts / specs
                 |
        PS0-07 Effects / verified do
                 |
        PS0-08 Mandatory assurance
                 |
        PS0-09 Native emission
                 |
        PS0-10 Origins / IDE / views
                 |
        PS0-11 Full v7 acceptance
```

Source positions and syntax provenance should be **retained from PS0-01 onward**, even though IDE release acceptance closes later. Data, Standard and modules can proceed in parallel after the source-category model stabilizes; contracts depend on correct import/instance identities. Avoid a second elaborator, a second grammar owner, or independent overlapping proof-trust allowlists.

**Development speed:** build coherent feature families first; use cheap parser/Lean-Core tests while implementing, then perform full CI at milestone gates. No repeatedly rerunning completed broad research or patching individual tests without addressing the underlying parser/semantic invariant. Preserve known-good branch checkpoints.

## 7. Machine-readable conformance and test strategy

**Generate** `experiments/ps0/v7-coverage.json` (target artifact) from the canonical `0B` syntax selection, `13` accepted/refused fixture table, `14.1A` P0/P1 acceptance, `14.1B` E1–E4 errata, and `14.1C` F01–F22 source-policy supplements. A test passing just because Lean accepts some semantically different program is **not** conformance.

For each normative requirement record:
- stable ID and canonical spec section; source AST category; pinned Lean parser/elaborator file and tests;
- implementing PS0 module; exact selected Standard/environment version and assumptions;
- **positive fixture(s)**, **negative fixture(s)** with intended **phase + rule ID**, and status (PENDING/PASS/FAIL);
- Lean-Core declaration/type/effect/proof correspondence method and meaningful independent evidence;
- CI commit/run, toolchain digest and actual observable result, not a manually assigned completion percentage.

Example target record (schema proposal, not a test report):

```json
{
  "requirement": "PSCV0-APP-02",
  "spec": ["0B", "2", "13", "14.1B"],
  "category": "psCallArgs",
  "leanSource": "src/Lean/Parser/Term.lean",
  "positives": ["P-CALL-1", "P-CALL-21"],
  "negatives": ["N-CALL-3", "N-CALL-6"],
  "expectedRejectionPhase": "PARSE",
  "expectedRejectionCode": "PSCV0-APP-02",
  "coreCorrespondence": "required",
  "status": "PENDING",
  "qualifiedCommit": null
}
```

**Normative failure taxonomy:** `LEX`, `PARSE`, `ELAB`, `ELAB/VC-PROOF`, `ENV`, `KERNEL` (only submitted invalid checked terms), `ASSURANCE` (trust/contract/effect/erasure/publish). Require an intended error code; e.g. an invalid C-style comment is **not** a valid test for a spaced parenthesized Lean application, and an unknown tactic import is **not** proof of a VC failure.

### 7.1 High-priority conformance families

| Group | Positive tests to cover | Correct negative tests / semantic checks |
| --- | --- | --- |
| **Application** | `f(x,y)`, `f((x,y))`, `f(())`, `f()`, defaulted `greet()`, `f x(y)`, named/partial, type-directed definitional Unit alias, comment inside parentheses | `f (x)`, `f /-gap-/ (x)`, C-style comment LEX distinction, duplicate named args, missing Nat arg, callable-type failures, incorrect tuple reclassification |
| **Binders / scopes** | Dependent/interleaved implicit/strict/instance binders, `function()` required Unit, `variable (n : Nat)`, `section`/`include`/`omit`, theorem signature generalization | Adjacent explicit groups, duplicate modifiers, `def()` Unit confusion, theorem proof-only free parameters, shadowing capture |
| **Types / patterns** | Indexed Vec application, constructor `k+1`/`k+2`, dependent motive, impossible branches, `nomatch`, multi-discriminant match and `matches` | `1+k` and `k+m` not reinterpreted as constructor patterns, ill-typed indices/motive, feasible missing case, out-of-scope match binders |
| **Syntax ownership** | Braced `by/do/if/match/struct/where/mutual`, valid proof middle-dot `·`, nested typed `try/catch/finally` | Layout-only selected bodies, ASCII `.` as goal bullet, misplaced constructor commas, unregistered alternative semicolons or metaprograms |
| **Contracts / effects** | Pure function `f.spec`, StateM/ReaderM/Except WP, `given`/`requires`/`ensures`, `assert`/`erased`, valid for/while with invariant and decreasing | Missing/false spec, wrong `@[spec]` reference, unsolved VC, no invariant/decrease, erroneous exceptional postcondition, unsafe foreign effect, erased value use |
| **Library / project** | `List`/`Array`/`ByteArray`, GetElem proof/optional/bang; strings/Unicode/raw/interpolation, type-indexed scalars, map/set/JSON; public import and private bodies | Unknown native symbol/instance, unregistered deriving, exposure leak, import cycle/duplicate/path escape, unvalidated JSON/refined constructor |
| **Assurance / output** | Approved proof closures, semantic comparison of generated Lean code, source/native observable agreement with scoped assumptions | Transitive sorry/unsafe/axiom/noncomputable, compiler helpers hidden as source authority, stale environment, source race, path/symlink collision, incomplete staged write |

### 7.2 Semantic correspondence: beyond “both compile”

For each syntax sugar family, write a **manual Lean reference expression/proof** under the same pinned environment, then compare normalized Lean Core expressions, universes, dependent binder metadata, constant dependencies and proof terms under an explicit name/section mapping and kernel-admissible definitional equality (or a proved proposition if the transformation is non-definitional). A pair of independently typechecking artifacts is not sufficient to prove same semantics. In addition, execute representative total computations using the official Lean evaluator and compiled native program, comparing outputs and error cases, while labeling this evidence bounded differential testing rather than a universal correctness theorem.

For imported specifications, prove the right target declaration is cited; for effect semantics, prove the actual WP/contract consequence, not the existence of any theorem named `spec`. Use positive and negative metamorphic tests for whitespace, comments, qualified names, Unicode, modes of function application, and import order.

### 7.3 CI tiers and budget policy

1. **Fast local gate:** parser categories, selected syntax grammar, phase diagnostics, a small dependent call/proof/VC smoke. Cheap incremental Lake build.
2. **Coherent feature gate:** the complete changed semantic family, native Lean reference and kernel replay, source/Standard digest, cross-module and native execution where relevant; preserve all older fixture families.
3. **Release gate:** clean-source reproducible build; all `0B/`13/`14` acceptance IDs and regressions; projects/lockfile/visibility; complete assumptions/effects; native artifact integration, output/refusal/recovery/resource tests, source maps/IDE; optional `lake check` and `lake comparator` as secondary independent kernel checks where supported. Both can strengthen kernel assurance but do **not** establish C/native semantic preservation.

Every release artifact binds to the exact source commit and test run. Test size and performance thresholds must be measured using the current runner; do not invent time budgets or hide resource failures.

## 8. Native compilation, runtime/FFI boundary and claim hierarchy

The selected runtime is **Lean native**, not PSC0 JS/TS/Rust/direct Wasm. Lean `runFrontend` and `LCNF.emitC`/`leanc` are the reference codegen, but the verification policy must report what this proves.

Suggested evidence levels (draft terminology, explicitly distinct):
- `SYNTAX_ACCEPTED` — passes closed PSCV0 parse; no claim about typing.
- `KERNEL_CHECKED` — Lean accepted actual elaborated declarations relative to the recorded assumptions.
- `POLICY_CHECKED` — selected imported source/assumption/effect/totality profile closed.
- `SOURCE_CONTRACT_VERIFIED` — all *required* specified VCs and contract/spec/erasure obligations proved and audited.
- `NATIVE_COMPILED_UNCERTIFIED` — native compilation succeeded; source/runtime behavior not formally related by this fact.
- `NATIVE_EXECUTION_QUALIFIED` — selected differential/ABI/runtime cases passed; still not a universal preservation proof.
- `MACHINE_SEMANTICS_VERIFIED` — **unavailable unless** an actual separate Lean-to-native compiler/runtime/FFI preservation result is supplied and checked.

The v7 phrase “verified executable” must never silently equate the fourth and seventh levels. For a practical first release, present exact *source-verified + native compiler assumed* metadata, or restrict publication claims until its assurance profile permits them; do not falsify soundness or suppress the remaining obligation.

Native execution contracts: typed integer widths/overflow, Float nan/signed zero and conversions, UTF-8/String/Char, persistent array/list aliasing, valid exotic/sized/erased values, user-defined ADTs, direct/closure calls, selected monads/errors, IO/FFI typed boundaries, target-sized word behavior, diagnostics and panic/error behavior. Respect pinned Lean runtime rather than inventing TypeScript semantics. Runtime effects which are not verifiable from source alone stay external assumptions, clearly enumerated per API.

## 9. Full source/environment closure and reproducibility

### 9.1 Standard environment snapshot

`PS0.StandardEnv` currently records a **provisional** local JSON roster. To finish v7, generate and validate a canonical complete selected-semantic snapshot containing:

- exact Lean toolchain/commit; source/library module digests and public/private import/re-export/expose graph;
- selected tokens/notation identities, precedence, source syntax categories and approved custom sugar;
- ordered classes/instances with priority, universe parameters, default values, coercions and search limits;
- deriving handlers (v7 selected `Repr`, `BEq`, `DecidableEq`, `Inhabited`, `Hashable`) and their real Lean origins;
- versioned `simp`/`omega`/`grind` and proof/tactic registrations, generated/spec attributes and allowable custom extensions;
- all exact P0/P1 API signatures plus verified contract/effect implementations/assumptions, JS/native/foreign boundary classifications if applicable;
- transitive axioms, `sorryAx`, noncomputable/unsafe model, trusted kernel/toolchain identity, and a canonical cryptographic digest;
- actual selected build options, `experimental.vcgen`/`experimental.intrinsic` settings and limits.

An import of `Std` does not automatically authorize every macro, instance, tactic, foreign capability or public name added by the upstream package. An environment drift must fail with a reproducible first mismatch and cannot be repaired by auto-repinning.

### 9.2 Source graph and native Lean module translation

Freeze absolute input root, normalized relative POSIX source paths, case-insensitive collisions, duplicate `module` names, public/private scopes, cycles, topological order, declaration/expose identities, license/provenance and all `.ps` import bytes. Lower using the official Lean module header/command AST, not a regexp or simple textual `import` rewriting. Preserve original source maps. A full multi-file project must rebuild only affected dependent nodes when cache IDs match full closure, and re-check after relevant semantics/manifest changes.

Check that ProofScript public-by-default names with non-exposed bodies translate to the precise pinned Lean module semantics; a successful import with a publicly visible theorem but an unintentionally unfoldable private body is a conformance failure.

## 10. Publication / artifact protocol

Target CLI syntax (**proposed** extensions, not all currently implemented):

```text
ps0 check path/Main.ps
ps0 check --project ps0.json
ps0 build path/Main.ps Main out/
ps0 build --project ps0.json --verified
ps0 audit --project ps0.json
ps0 environment
ps0 syntax-kinds path/Main.ps
ps0 test-conformance --profile v7
ps0 emit-lean path/Main.ps out/Main.lean  # optional view, .ps remains authoritative
```

Staged artifacts for a selected module may include `.olean`, C, object/native executable, originating `.ps` spans/source projection and a machine-readable evidence manifest. Example target manifest structure (**illustrative, not certified evidence**):

```json
{
  "schema": "ps0-build-evidence/1",
  "languageProfile": "pscv0-v7",
  "toolchainCommit": "eb6cafb7290e8bd5f2937522d8d804f58f02bafc",
  "sourceGraphSha256": "<computed>",
  "environmentSha256": "<computed>",
  "checkedDeclGraphSha256": "<computed>",
  "assumptions": ["<audited, profile-specific>"],
  "specAndEffectClosure": "<measured>",
  "compiledTarget": "lean-native",
  "claims": ["kernel-checked-source", "native-compiled-compiler-assumed"],
  "outputs": [{"path": "<validated>", "sha256": "<computed>"}]
}
```

Failure at ANY stage (syntax, dependencies, source drift, proof/VC, kernel, assumptions, unsupported effect/erasure, compiler/linker, resource, output path) **must not publish newly successful artifacts** or overwrite the last qualified bundle. Store in a private staging location, validate names and hashes before commit, and use a versioned/crash-consistent release-pointer protocol; multi-file rename is not automatically atomic. Avoid using a serializable acceptance token as proof authority. The host controls both acceptance and publication identity.

## 11. Risk register and cheapest correct mitigations

| Risk | Grounded cause | Action |
| --- | --- | --- |
| R1 — invalid Lean parser alternatives admitted | Current command validator can admit `choice` if *any* alternative is allowed; source parser is extensible | Resolve/admit exact intended alternative and expansion, validate category and trusted syntax/handlers before execution |
| R2 — silently wrong PSCV0 module visibility | V7 public-by-name defaults differ from Lean 4.35 modules | Explicit AST mapping and imported proof/body-exposure conformance tests |
| R3 — check/build TOCTOU and partial publication | Current adapter checks/reads again, then writes directly to outputs | One immutable source snapshot, checked graph equivalence, private staging and durable release transaction |
| R4 — compile-time plugin side effects | Lean tactics/attributes/initializers may run code | Narrow registered handlers, capability/resource isolation; do not treat source allowlist as OS sandbox |
| R5 — assumed complete proof coverage | Existing `#pscv_gate` handles selected local declarations/axioms, not complete import/effect/spec obligations | Build full transitive coverage/assumption ledger, true generated spec proof and negative VC matrix |
| R6 — assurance overclaim | Lean kernel source acceptance != verified emitted C/native behavior | Explicit layered evidence labels and separate preservation/FFI obligations |
| R7 — costly duplicated compiler design | PSC0 has separate parser/elab/backend, Lean-native PSCVL already exists | One **PS0-local** grammar owner, native Lean elaboration/compiler, retain PSC0 and historical PSCVL separately |
| R8 — inaccurate milestone credit | RC4 37/56 historical tests do not qualify stable 4.35 | Re-run stable exact-commit gates; map every v7 normative ID, no unsupported completion percentage |
| R9 — performance drift/churn | Repeated full-repo Lean test loops slow feature delivery | Incremental three-tier CI, architecture-family edits, measured cold/warm build and native runtime baselines |
| R10 — incompatible import or hidden foundational axiom | Pinned Lean imports can include `Classical.choice` and handlers | Explicit per-profile assumption roster, no silent widening; package/CI digest guards |

## 12. Release acceptance criteria (do not shortcut)

Mark `PS0 FULL PSCV0 V7` complete **only** when:

- [ ] A. Stable 4.35.0 PS0 exact-commit full CI passes, with a linked/running native executable (not merely emitted C/olean).
- [ ] B. Every selected `0B` category and v7 ``1–12` rule has correct source grammar and Lean semantic acceptance.
- [ ] C. All required `13` positives/negatives, `14.1A` P0/P1 acceptance, `14.1B` E1–E4 and `14.1C` F01–F22 have machine-linked source IDs, expected phase diagnostics and actual positive/negative evidence.
- [ ] D. Full `.ps` project graph/import/re-export and public-name/hidden-body semantics qualified.
- [ ] E. Actual pinned Standard/P0 and required P1 modules/APIs, notations/instances/tactics/deriving/effect/assumption manifest complete and reproducible.
- [ ] F. Each PSCV-only syntax transformation is supported by same-environment Lean-Core/kernel-correspondence evidence, not simply “both programs compile.”
- [ ] G. Complete `given/requires/ensures`, `where finally | spec`, verified `do`, loops/totality, exceptional/effect frame, proof obligation and erasure checks.
- [ ] H. Transitive imported/generated `sorryAx`/source axiom/`unsafe`/`partial`/noncomputable/external effects and dishonest-assumption routes fail closed.
- [ ] I. Native compiler/output/ABI and complete selected execution differential gates qualified; machine-code preservation remains explicit assumption absent independent theorem.
- [ ] J. Source snapshot/checked environment/output identity, fail-safe publication, collision/path/resource/abort recovery validated.
- [ ] K. Original `.ps` diagnostics, UTF-8 source positions, proof-goal LSP/IDE and source reconstruction have qualified semantic preservation for required authoring UX.
- [ ] L. Clean release, documentation, conformity matrix and independently verified CI receipts all point at the same exact commit.

A row cannot be marked done by merely editing this document, by passing one example, or by labeling a tentative artifact “verified.” **100% of mandatory in-scope requirements** must have real PASS evidence; scope changes require a separate normative v7 decision and cannot be disguised as implementation.

## 13. Immediate critical-path PR sequence and working method

1. **Stable-baseline PR:** verify/repair actual PS0 stable 4.35 build and inherited suite, link/run a native `.ps` application, record exact commit and negative classifications. No broad rewrite.
2. **Grammar ownership PR:** enforce `0B` closure, resolved AST choices and `APP/BIND/DECL` rule matrix; preserve existing syntax/test selection.
3. **Project/import PR:** implement real multi-module `.ps` import/`public import` graph and public-name/hidden-body semantics; strict manifest.
4. **Language semantics PR groups:** dependent data/recursion/deriving/instances and P0 Standard, checked against pinned Lean Core and native behavior.
5. **Verification PR groups:** full `Std.WP`/`vcgen`/contracts, typed exceptional/reader/state/verified-`do`, spec/effect/assumption/erasure gates.
6. **Build/tooling/release PR groups:** immutable checked native source session, private staging, complete source origins and InfoTree, full normative conformance matrix, then release.

At each coherent checkpoint: inspect current branch HEAD/CI before writes; preserve branch and upstream Lean history; implement complete semantic families rather than test-fix hunting; run targeted checks followed by full exact-commit CI at milestones; update `CONFORMANCE.md` and the coverage registry with successes, failures, and unqualified items. Do **not** force-push, merge into Lean master, delete PSC0, or silently weaken proof obligations for speed.

**End-state:** ProofScript `.ps` v7 syntax/semantics + official Lean 4.35 elaboration/kernel/compiler + PS0's strict source/environment/effect/assurance/build policies. PS0 is a fully separate Lean-native compiler variant; PSC0 remains the independent multi-backend compiler.

## 14. Inspected sources and evidence honesty

- Normative [current PSCV0 v7 source with stable-pin amendment](https://github.com/dwijayuda/pskernel/blob/f79d334ef922eb7f71f7527dbc798ebb0dbeb610/psc0/PSCV0_LANGUAGE_REFERENCE.md) ``0A/0B, 1–15`.
- Existing PS0 [README](README.md), [conformance status](CONFORMANCE.md), `PS0Main.lean` and [PS0 draft PR #5](https://github.com/dwijayuda/lean4/pull/5).
- Reused `../pscv0-lean-native/PSCVL/` syntax, grammar, policy, effects, [historic conformance ledger](../pscv0-lean-native/CONFORMANCE.md) and [historic RC4 CI](https://github.com/dwijayuda/lean4/actions/runs/38112654962) (not stable-4.35 PS0 qualification).
- Exact stable source locations in `3`, [Lean 4.35.0 release](https://lean-lang.org/doc/reference/latest/releases/v4.35.0/), [Lean macros](https://lean-lang.org/doc/reference/latest/Notations-and-Macros/Macros/), [Lean elaborators](https://lean-lang.org/doc/reference/latest/Notations-and-Macros/Elaborators/), [Lean modules](https://lean-lang.org/doc/reference/latest/Source-Files-and-Modules/), [`vcgen` reference](https://lean-lang.org/doc/reference/latest/The--vcgen--tactic/) and [tutorial](https://lean-lang.org/doc/tutorials/latest/vcgen/).
- The official Lean contract implementation synthesizes `f.spec` with `vcgen`; an actual checkable theorem is the authority, **not** the presence of the keyword `ensures`.

**Plan/research evidence limit:** this document reflects inspected GitHub sources and official pinned Lean implementation, **not** a new stable PS0 CI pass, full v7 translator proof, complete environment registry, or formal semantics-preserving native compiler. Those results must be generated and inspected before the corresponding claims are promoted.

### Machine-readable implementation update (15 October 2026)

The [v7 conformance inventory](v7-coverage.json) has been committed with **150
normative `13` IDs** (72 positive and 78 negative) and **31 additional audit IDs**
(E1–E4, F01–F22, C01–C05). A standalone Node validator in
`scripts/validate-v7-coverage.mjs` runs in PS0 CI. No case has been promoted to
PASS without exact-commit CI; `--require-complete` currently intentionally
refuses. This is conformance infrastructure, **not proof that v7 features have
been fully implemented**.
