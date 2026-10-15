# PS0 — Full PSCV0 v7 Implementation Plan on Lean 4.35.0

**Status:** source-grounded implementation plan, not a completion, successful stable-build, or verified-native-execution claim.  
**Prepared:** 2026-10-15. **Project:** `dwijayuda/lean4`, `experiments/ps0/`, draft [PS0 PR #5](https://github.com/dwijayuda/lean4/pull/5), branch `feature/ps0-lean435-stable-v1`.  
**Pinned official Lean:** `v4.35.0`, commit `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.  
**Normative language authority:** [PSCV0 v7 reference in dwijayuda/pskernel](https://github.com/dwijayuda/pskernel/blob/f79d334ef922eb7f71f7527dbc798ebb0dbeb610/psc0/PSCV0_LANGUAGE_REFERENCE.md) (Git blob `25e1ef788794db175a2183679e37ff8c8e9b6a2e`). The **2026-10-14 stable pin amendment** at its beginning supersedes the historical RC4 pin cited in older sections. Source grammar ownership is ``0A/0B`; detailed language semantics ``1–12`; normative test/evidence matrix ``13–14`.
**Isolation:** PS0 lives in the user's Lean fork. Preserve the current independent multi-backend PSC0 in `dwijayuda/pskernel` and its PR #109. Do not replace, rewrite, merge or discard PSC0. Preserve the older PS0 parent experiment branch and upstream Lean sources.

## 1. Objective, guarantees and deliberate non-goals

Build a **complete PSCV0 v7 compiler variant called PS0** with authoritative `.ps` files, precisely v7-selected syntax and Lean-compatible semantics. Reuse the **existing Lean-native PSCVL syntax macros and grammar validator** in `experiments/pscv0-lean-native/` (not the independent portable PSC0 parser), while the **official Lean 4.35.0 elaborator, type system, termination checker, tactics, kernel and native compiler** perform their real work. No second PS0 typechecker, no new dependent unification engine, no separate kernel, and no parallel JS/Rust/Wasm backend.

```text
source .ps + project manifest + pinned Standard/profile
  -> immutable source/module graph and UTF-8 origin spans
  -> one closed PSCV0 syntax-category validator (reuse PSCVL/Lean parser)
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
| `../pscv0-lean-native/PSCVL/Syntax.lean` | Existing Lean-native `.ps` syntax bridge, macro quotations, typed `f()` elaboration, contracts, records, control | Bounded syntax selections; many v7 forms and forbidden alternatives not fully covered |
| `PSCVL/Grammar.lean` | Command-family whitelist and nested source-pattern refusals | Some `choice` alternatives accepted based on *any* acceptable branch, not proven selected elaborated branch; dynamic grammar safety not closed |
| `PSCVL/Policy.lean` | Source `unsafe`/`partial`/`axiom`/`sorry` checking, `#pscv_gate` and transitive axiom checks for local declarations | Imported provenance/assumptions, spec/effect/erasure coverage and verified-build policies incomplete; inherited `Classical.choice` allowance differs from PSC0 |
| `PSCVL/Effect.lean` | Genuine Lean-grounded relations for pure, reader, state and typed-error WP and proofs | Not complete P0/P1 effect capability or external-world boundary model |
| `PSCVL/StandardEnv.lean` + `PSCV0_STANDARD_ENV.json` | Provisional selected imports/deriving/pure scalar manifest, updated stable version in PS0 branch | No complete modules/instances/notations/tactics/effects/axioms/priority/exposure snapshot |
| Historic [Lean-native RC4 workflow](https://github.com/dwijayuda/lean4/actions/runs/38112654962) | 37 accepted, 56 rejected `.ps` fixtures, native executable, two basic `rfl` correspondences | **RC4** run is not a new stable PS0 acceptance or full normative v7 coverage |
| `.github/workflows/ps0-lean435.yml` | PS0 branch CI definition for stable toolchain, selected tests and C/olean artifact checks | Exact-commit passing CI and end-to-end native linker execution still require confirmation |
| Current `PS0Main.buildFile` | Separate `checkFile` and `runFrontend` calls; direct output creation | Need immutable checked source snapshot and staged atomic/recoverable publication; no assumptions about source unchanged between checks |

**Important distinct ownership:** PSC0's portable syntax parser, independent elaborator and JS/TS/Rust/Wasm backends stay in `dwijayuda/pskernel`. PS0 only reuses the historical **Lean-native PSCVL** frontend and official Lean native backend. Do not carry over PSC0 differential/runtime qualification receipts into PS0.

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

Keep the existing `PSCVL` syntax owners until their consumers have migrated; do **not** duplicate them under `PS0`. Proposed eventual PS0 modules: `SourceProfile.lean` (finite category registry), `Parse.lean` (source bytes/trivia), `Lower.lean` (hygienic quotations), `Modules.lean` (imports/visibility), `Standard.lean` (environment identity), `Contracts.lean` and `ProofPolicy.lean` (verified claim gates), `Compile.lean` (checked compilation session), `Publication.lean` (staging), `Diagnostics.lean` (origins/InfoTree). These are **target file names**, not asserted existing modules.

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

