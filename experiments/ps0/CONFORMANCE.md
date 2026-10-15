# PS0 standalone Lean 4.35.0 v7 conformance and migration ledger

**Branch:** `feature/ps0-lean435-stable-v1`. **Goal:** standalone PSCV0 v7 `.ps` compiler with official Lean 4.35.0 elaborator/kernel/native backend. **Status:** implementation committed, new stable CI not yet verified. Do not count previous RC4 results as stable-PS0 qualification.

## Review of migrated modules

| Module | Adaptation, not an unchanged copy | Remaining acceptance |
| --- | --- | --- |
| `PS0/Syntax.lean` | Own namespace/syntax registration, type-directed calls; nullary Unit sugar **only for function**, not def/theorem/ctor; non-callable `f()` rejected | Full v7 source grammar and call correspondence |
| `PS0/Grammar.lean` | Own selected command kinds, conservatively require **all** ambiguous command alternatives to satisfy allowlist rather than accepting any one | Full resolved-alternative/expansion audit; measure possible legitimate rejections |
| `PS0/Policy.lean` | Own `#pscv_gate` and registered attributes; retain explicitly disclosed `Classical.choice` in inherited permitted foundations | Complete imported axioms/verification coverage/effect/erasure |
| `PS0/Effect.lean` | Own Lean-grounded `Std.WP` pure/ReaderM/StateM/Except semantics and proof theorems | Full verified effect cases and external world capability contracts |
| `PS0/StandardEnv.lean` | Own stable 4.35.0 identity and provisional module/deriving/eval manifest | Full registries, instance/notation/tactic/effect/module digests |
| `PS0Main.lean` | Local PS0 imports only, one source read and one authoritative native Lean elaboration; staged C/olean bundle published by same-filesystem directory rename | Immutable project/environment graph digest, path-race controls and release claim manifest open |
| `lakefile.toml`, CI | No sibling `require`; workflow checks out only `experiments/ps0` and links `PS0:static` | Confirm independent exact-commit Lean stable build and native execution |
| `tests/` | PS0-owned positive/negative source fixtures, original native correspondence harness adapted; new call tests | Not full inherited 37 positive/56 negative corpus or complete v7 rule matrix |

The original `experiments/pscv0-lean-native` experiment was restored to its RC4 state on this PR branch. The independent `dwijayuda/pskernel` PSC0 compiler and PR #109 remain unchanged.

## Existing bounded capabilities and open requirements

| Area | Implemented slice | Missing final v7 closure |
| --- | --- | --- |
| Source language | `function`/`const`, selected dependent calls, data/matches, braced proofs/control, macros lowering to Lean syntax | Complete `0B` source/category grammar and all `13`/`14` acceptance cases |
| Logical meaning | Official Lean elaborator and kernel, Lean-native tactics and termination | Full Lean-Core translation correspondence evidence for each surface feature |
| Project/imports | Selected native Std import allowlist | `.ps` module/public-import graph, public default names/opaque body mapping |
| Standard environment | Stable pin + provisional local JSON | Tokens, notation, instances, deriving, tactics, capabilities, axioms and API inventory |
| Verification | Local source axiom/unsafe/partial/sorry preflight; selected `Std.WP` contracts | Full generated and imported VC/spec/effect/assumption/erasure coverage and certificates |
| Native build | One Lean `runFrontend` checks the source and produces C/olean in private staging; published output cannot silently overwrite a prior bundle | Full multi-module identity/provenance, race-resistance, native preservation evidence remain |
| Tooling | CLI source errors and PS syntax | Original `.ps` InfoTree spans, LSP, formatter, readable Lean/PS source views |

**New conformance regression cases:** `tests/fail/noncallable_empty.ps` must reject a Nat value used as `answer()`; `tests/fail/def_nullary.ps` must reject source `def name()`. `tests/pass/unit_alias.ps` checks definitionally Unit empty calls and `default_empty.ps` checks optional parameter completion. All new cases must pass exact native Lean stable CI before being considered qualified.


## New PS0-00/PS0-01 implementation slice — 15 October 2026

**Implementation state: committed, exact-commit stable Lean CI not yet observed.**

- The native `build` entry now reads `.ps` bytes once and performs **one full Lean elaboration** via the very `runFrontend` that controls C and olean emission. The source validator still runs first, but no second check-only Lean elaboration precedes emission.
- The generated native C and `.olean` are placed in a newly created sibling staging directory, then committed as a single directory rename into a **previously absent** destination. Failure during Lean elaboration, proof policy, or C emission must leave no final directory. Existing published bundles are rejected rather than overwritten; CI compares their SHA-256 digests after an attempted overwrite.
- Module policy now inspects actual pinned `Lean.Parser.Module` header AST, rather than relying solely on imported module flags: `module`, `prelude` and `public import` explicitly refuse until PS0-03; `meta import`, `import all` and unapproved modules refuse by their corresponding environment rule.
- `Grammar.forbiddenSyntax` now rejects source `opaque` without a checked value and Lean value-form `instance : T := value` before elaboration, in keeping with the v7 selected grammar.
- CI has exact-reason negative fixtures for source-module/import guards, bodyless opaque, instance value form, Unicode proof bullet, typed-error braces and non-callable `f()`. The native harness checks a nullary Unit → Nat correspondence with an actual Lean `rfl` proof and runs the compiled result.

**Still open:** source code to generated Lean correspondence for all v7 categories; complete environment/module/scope metadata; verified `f.spec`/effect/erasure closure; origin-preserving diagnostics; imported assumption-policy closure; multi-module checked graph; signed/reproducible output provenance; proof of native compiler/runtime preservation; and green stable CI at the current PR HEAD. A same-filesystem directory rename prevents partially *published* C/olean files in the no-concurrent-mutation case, but is not yet a complete hardened/crash-recovery build protocol.

## Current milestone gates

- [ ] Stable 4.35.0 PS0 native build and checked CI for this exact HEAD.
- [ ] PS0-only sparse checkout and no sibling source dependency.
- [ ] Source positive and phase-specific negative cases, including ambiguous syntax and nullary semantics.
- [ ] Local Standard JSON matches PS0's environment.
- [ ] Invalid source/proof blocks output and native example compiles/links/runs.
- [ ] Port and adapt missing historical 37/56 source cases as appropriate, with phase-specific diagnostics.
- [ ] Complete PS0-01..PS0-11 in the [full v7 plan](PS0_FULL_PSCV0_V7_IMPLEMENTATION_PLAN.md).

Do not label standalone build, bounded CI or native source kernel acceptance as full PSCV0 v7, verified source contract closure, or verified machine semantics.

## Normative coverage inventory (unqualified)

`v7-coverage.json` captures **150 exact `13` case IDs**, including 72 P-positive
and 78 N-negative cases, and records E1–E4, F01–F22 and C01–C05. A Node
validator rejects incomplete/duplicate inventories, unsafe or missing fixture
references, drifting canonical spec/Lean pin, and any PASS without exact commit,
CI run and corresponding positive or phase-specific negative fixture.
The inventory has candidate fixture references for ten cases; these links are
not PASS evidence. All 181 tracked requirements currently remain PENDING and
`--require-complete` must fail until a fully qualified exact-commit v7 run exists.

## Source-language isolation — `.ps` restricted, `.lean` unrestricted

**Policy decision (15 October 2026): PSCV0 v7 applies ONLY to `.ps`.**
Ordinary `.lean` is not a source dialect of PSCV0 and must remain full
official Lean 4.35.0. PS0 now routes `check *.lean`, `build *.lean` and
`lean ...` through a **separate native Lean OS process** resolved from the
exact pinned sysroot. It does not inject `PS0.Policy`, `PS0.Syntax`,
`#pscv_gate` or the selected v7 Standard into native Lean.

The standalone native fixture
[tests/lean/unrestricted.lean](tests/lean/unrestricted.lean) contains native
`axiom`, `unsafe`, `partial`, `sorry`, and unrestricted `#eval` with
`IO.println`. CI checks both the direct native pass-through and the
`.lean` check/build routes, including C and olean output. In contrast,
new `.ps` negative fixtures for source axiom and partial join the existing
unsafe/sorry refusals. **Not qualified yet**: stable-4.35 exact-commit CI
has not been observed succeeding in this conversation.

Separate language semantics from build publication policy: the wrapper
still avoids overwriting existing native bundles, but restricts no valid
Lean language feature. For arbitrary native Lean CLI flags use
`ps0 lean ...` directly. Mixed `.ps` importing `.lean` will require
explicit imported-assumption/effect obligations at the `.ps` boundary;
the native file remains unrestricted. See
[SOURCE_PROFILE_BOUNDARY.md](SOURCE_PROFILE_BOUNDARY.md).

**Percentage treatment:** this does not increase `.ps` feature readiness
(the earlier 37% estimate (now 38% following the new binder implementation)) or strict PSCV0 v7 qualified acceptance
(0/181). Lean already had full expressive power; PS0 is preserving it
rather than implementing those features as ProofScript capabilities.


## Implemented .ps signature additions — 15 October 2026

**Source forms added:**

- `function sum(x: Nat, y: Nat) := x + y` and `def triple(x: Nat) := ...` infer their return types through Lean's native declaration elaborator. Inference also covers `private function`, implicit/instance-headed functions, and source-nullary `function zero() := ...` (retaining the required Unit binder).
- Ordered telescopes such as `function choose(n: Nat)[Decidable(n = 0)](x: Fin(n + 1)): Nat := ...` and `def select {α: Type}(x: α)[Inhabited α](y: α): α := ...` preserve Lean's dependent argument and class-search order.
- The same ordering applies to v7 `theorem` declarations with selected explicit, implicit and instance groups.
- Source `{{α: Type}}` strict-implicit spelling maps to Lean's strict-implicit binder.
- `PSCV0-BIND-02` refuses adjacent explicit groups both in the PS0 overlay and selected native `def`/`theorem` alternatives inside `.ps`; unrestricted `.lean` is unchanged.

**Evidence status:** PS0-owned positive, negative and independent native-Lean reference fixtures and CI definitions are committed. They are **unqualified** until an observed stable-Lean exact-commit CI success; normalized expression/type equivalence for all selected binder permutations is still open. `v7-coverage.json` stores candidates without assigning PASS.

**Readiness rubric:** binder family 3/5 (formerly 2/5), estimated overall `.ps` readiness **38%**. The strict v7 acceptance ledger remains **0/181 CI-qualified**, not 38% tested/proven. `ps0 lean` and the `check/build *.lean` routes continue using official Lean without PSCV0 source restrictions.


## PSCV0-TERM-01 — measured recursion family (unqualified implementation)

Official pinned Lean 4.35.0 provides `Termination.terminationBy`,
`Termination.decreasingBy` and its native termination elaborator. PS0
has added `function f(n: Nat): Nat := body termination_by n` and the v7
`decreasing_by by { omega }` proof wrapper. The source wrapper lowers
to native Lean termination hints; Lean owns the actual decrease proof.
No new recursion axiom or evaluator is introduced.

PS0 source admission now refuses native-only `termination_by structural`,
`termination_by?`, the other native fixpoint hints and `decreasing_by`
without a preceding measure. These refusals affect only `.ps`, never
ordinary `.lean` sources. Positive and negative tests are under
`tests/pass/termination_total.ps` and `tests/fail/termination_*.ps`.
Native Lean comparison cases are in `tests/lean/termination_reference.lean`
and `tests/lean/termination_native_extensions.lean`.

**Qualification:** no exact-commit green Lean 4.35.0 PS0 CI run
verified. The feature syntax, source refusals and CI definitions are
committed but their successful compilation remains unconfirmed.
Engineering readiness **39%** (was 38%; recursion family 2/5 → 3/5),
strict v7 conformance **0/181 qualified**. Complete mutual/local
recursion, all termination suffix variants selected by v7, and full
Lean-Core correspondence remain open.


## PSCV0-INSTANCE-01 — braced native-Lean instance adapter (unqualified)

PS0 now has source syntax for `instance : C where { field := value }`
and `instance chosen : C where { field := value }`, including selected
ordered binder telescopes on parametric instances. It lowers these
to the equivalent native Lean `instance : C := { field := value }`,
so all typeclass inference, class field elaboration, and proof checking
remain Lean-owned. The source-only `.ps` profile rejects arbitrary
`where value`, native unbraced instance fields and source value-form
instance definitions; `.lean` retains those official Lean forms.

**Source and tests:** `PS0/Syntax.lean`, `PS0/Grammar.lean`,
`tests/pass/instance_braced_fields.ps`,
`tests/fail/instance_fields_not_record.ps`,
`tests/fail/instance_unbraced_fields.ps` and
`tests/lean/instance_reference.lean`. The CI checks named source
diagnostics and compares the corresponding native Lean reference.
No successful exact-commit build has been observed yet.

**Remaining v7 instance requirements:** optional selected priority
atoms, numeric priorities, all constructor/method binder and
class/instance registration details, frozen priority ordering and
source/environment identity. These must not be marked complete merely
because native Lean possesses the underlying features.

**Progress:** estimated `.ps` language readiness **40%** (previous 39%;
classes/instances/deriving family 3/5); normative CI-qualified
acceptance **0/181 (0%)**, unchanged.


## PSCV0-INSTANCE-PRIO-01 — source priority variants (pending qualification)

Following the first named/anonymous braced instance adapter, PS0 now owns
selected priority-bearing variants with and without parameter telescopes:
`instance (priority := high) : C where { ... }`,
`instance (priority := 750) chosen : C where { ... }`, and
`instance (priority := low) {α: Type}[Inhabited α] : C(α) where { ... }`.
The source syntax now uses a closed `pscvSelectedPriority` grammar (`low`, `mid`, `default`, `high`, or a decimal), and translates the
instance into a native declaration. Lean remains responsible for priority
interpretation, instance registration, and typeclass search. It has **not**
implemented a separate instance-ordering algorithm.

Positive and negative candidate fixtures:
`tests/pass/instance_priority.ps`,
`tests/fail/instance_priority_expression.ps`,
`tests/fail/instance_priority_unknown.ps`,
`tests/fail/instance_header_missing_type.ps`,
`tests/fail/instance_header_nullary.ps` and
`tests/fail/instance_header_adjacent.ps`. The native counterpart in
`tests/lean/instance_priority_reference.lean` confirms the intended
unrestricted Lean spelling. The separate source theorem in `tests/pass/instance_priority_order.ps`
checks that high-priority typeclass evidence wins over an overlapping
low-priority instance. It has a manual official Lean comparison in
`tests/lean/instance_priority_order_reference.lean`. CI runs both.
This validates selection **only if they actually pass**; do not claim
priority-order conformance merely from the syntax adapters.

The v7 inventory has **32 candidate IDs**
and **zero** confirmed PASS receipts.

**Important qualification limit:** no stable Lean 4.35 CI run has been
retrieved for this branch. The native parser and custom source syntax
must be tested together before claiming that every form elaborates or
rejects at its specified phase. The source atom allowlist is now
explicit, while the frozen imported instance/priority registry and
exact semantic correspondence remain unfinished. Language implementation readiness remains **40%**, not 41%
merely for adding another syntax variant.


## PS0-03 — implicit v7 module parser and import metadata (candidate)

**Normative source rule:** A `.ps` file is *implicitly* a module.
Users do not write `module`. Plain `import M` is module-private;
`public import M` re-exports M's public scope. This differs from
official Lean's *legacy* module imports, which are exported.

PS0 now parses the exact `.ps` bytes through official pinned Lean
`Parser.parseHeader` with a synthetic `module\n` header, then removes
the synthetic UTF-8 prefix from the command-body byte offset.
`HeaderSyntax.imports (includeInit := false)` retains Lean's actual
`isExported`/`isMeta`/`importAll` metadata; `module-header FILE.ps`
prints that information as JSON with `compile_ready=false`.
Literal user-written `module` in `.ps` is rejected by the native
header AST check. Pinned source:
`Lean/Parser/Module.lean` and `Lean/Elab/Import.lean`.

The implementation corrected a concrete diagnostic-order defect:
Lean rejects `public import`, `meta import` or `import all` in legacy
source without `module`. Previously this generic header error could
mask the intended PSCV0-specific diagnostic. PS0's new synthetic
module parse allows these directives to be classified correctly:
`public import` remains **pending full v7 visibility semantics**,
while `meta import` and `import all` are refused by the selected
environment policy. Source `prelude` and literal `module` are refused.

**Native emission boundary:** The source profile's module-private imports
must not be accidentally rebuilt as legacy exported imports. Until
PS0-03 implements native module-mode output, public-by-default
declaration names, and non-exposed definition bodies, `ps0 build`
refuses to publish native artifacts for `.ps` inputs with imports
(`PSCV0-MODULE-BUILD-PENDING`). Ordinary syntax/typechecking can
still run as **UNCERTIFIED**; module-interface conformance is not claimed.

Fixtures: `tests/headers/modern_imports.ps`,
`legacy_import.ps`, `modern_meta.ps`,
`invalid_public_legacy.ps`, plus
`tests/pass/implicit_module_import_utf8.ps`. CI checks actual
import flag identities, refuses the forbidden source module header,
verifies that public imports cannot yet be compiled, and requires
no emitted artifact for unsupported module imports.

**Progress:** module family 0/5 → 1/5 (**foundation only**);
overall estimated `.ps` readiness **41%** (previous 40%).
Strict v7 qualification remains **0/181**, pending an observed
exact-commit Lean 4.35.0 stable build and successful semantic checks.
The .lean route remains the unrestricted native toolchain.


## JS target MVP — source checked, backend still unqualified

The new `build-js` command is a deliberately **small real backend**, not
a demo that prints a JavaScript example. It has independent Lean modules
for typed Nat runtime IR, closed source AST lowering, deterministic
ESM/`.d.ts` emission, and signed VLQ Source Map v3. Runtime Nat values
use exact nonnegative BigInt with input guards and saturating subtraction.
The .js/.d.ts/.js.map bundle is staged and published together after the
existing Lean source elaboration/kernel/`#pscv_gate` succeeds.

The eligible runtime subset is limited to public explicitly typed Nat
constants/functions, numeric literals, formal Nat variables, parentheses,
source braced grouping and Nat `+`/`*`/`-`. The backend refuses all
unhandled constructs, including source modules/imports, instead of
silently changing semantics. Source code is not emitted until those
checks succeed. No compiler implementation .js/.mjs files are added.

`tests/js/nat_mvp.ps` and PS0 CI specify checks for JS execution,
Nat arithmetic beyond 2^53, TypeScript exports, Source Map v3 source
identity, unsupported-source refusal, deterministic artifacts, staged
publication and non-overwrite. **These are configured tests but no
exact-commit Lean 4.35.0 green CI run has been observed**. A typechecked
Lean source is *not* a proof of JS backend semantic preservation; this
MVP issues no verified JS certificate.

See [PS0_JS_BACKEND_MVP.md](PS0_JS_BACKEND_MVP.md). The separate PSCV0
v7 language-feature engineering readiness metric remains **41%**;
adding a backend is not completing new v7 grammar/semantic families.
