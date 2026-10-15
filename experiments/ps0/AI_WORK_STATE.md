# PS0 — AI work state (15 October 2026)

## Braced instance family — 15 October 2026

PS0 implementation continued under draft PR #5. Read current live HEAD before
any further write. **The stable Lean 4.35.0 native build has not been verified
passing** for this new family; all tests remain unqualified.

- Studied official Lean 4.35.0 `src/Lean/Parser/Command.lean`:
  native `instance` uses the class declaration elaborator; value-form
  `:= { fields }` is valid in native Lean. The v7 `.ps` surface instead
  selects `instance [name] : Class where { fields }`, not native
  `instance : Class := value` or unbraced `where`.
- Implemented PS0-owned source macros in `PS0/Syntax.lean` for anonymous
  and named class instances, plus ordered explicit/implicit/instance binder
  telescopes. Native Lean elaborates class fields and the actual instance
  declarations, including typeclass evidence; PS0 adds no new checker.
- Added pre-elaboration `PSCV0-INSTANCE-FIELDS` for non-record `where`
  bodies and `PSCV0-INSTANCE-BRACES` for unbraced native instance field
  declarations embedded in `.ps`. `PSCV0-INSTANCE-VALUE-REFUSED` remains.
  All these restrictions apply exclusively to `.ps`; `.lean` retains
  full native instance grammar.
- Added `tests/pass/instance_braced_fields.ps` with anonymous, named,
  polymorphic and ordered binder cases and kernel-checkable properties,
  `tests/fail/instance_fields_not_record.ps` and
  `instance_unbraced_fields.ps`, and matched native declarations in
  `tests/lean/instance_reference.lean`. CI gates these cases with
  specific negative diagnostic codes.
- Linked P-INSTANCE-HDR-ANON, P-INSTANCE-HDR-NAMED,
  N-INSTANCE-HDR-VALUE and N-INSTANCE-VALUE to **candidate** fixtures
  in `v7-coverage.json` without promoting them to PASS.
- Estimated 20-family `.ps` readiness: **40%**, up from 39% as the
  classes/instances/deriving family rose 2/5 → 3/5. Strict qualified
  completion: **0/181**, unchanged. The percentage is a planning
  estimate, not CI-tested language coverage.

**Next critical path:** obtain genuine stable-4.35 build/CI logs and
fix any parser/quotation/type-checking failures. Then complete v7
instance priorities (selected priority names and nonnegative numeric
literals), ordinary field/method binders, and frozen instance registry;
continue module/import visibility and full source assurance.
Native `.lean` remains unrestricted and is not included in v7 scoring.

## Well-founded recursion implementation — 15 October 2026

**Code checkpoint before this log entry:** `046797c9f88f041b96554c3ace1dc4fc83faa983`. Re-read live PR #5 HEAD before further commits.

- Source study against stable Lean 4.35.0 commit `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`: `src/Lean/Parser/Term.lean`, `Lean.Parser.Termination.terminationBy` / `decreasingBy` / `suffix`, `src/Lean/Parser/Command.lean` `declValSimple`, and `src/Lean/Elab/PreDefinition/TerminationHint.lean`. Native Lean performs well-founded recursion construction and checks the decrease proof; PS0 must not reimplement it.
- Implemented selected `.ps` `function f(n: Nat): Nat := body termination_by n` and `decreasing_by by { omega }` source proof adapter in `PS0/Syntax.lean`, lowering to the pinned Lean termination hints and tactic elaborator. The source grammar owns the `by { ... }` wrapper and native Lean owns the proof obligation.
- Tightened `PS0/Grammar.lean` source closure so native Lean declaration parsing inside `.ps` cannot silently admit `termination_by structural`, `termination_by?`, partial/coinductive/inductive fixpoint modes or `decreasing_by` without a preceding selected measure. These remain allowed in native `.lean` wherever official Lean allows them.
- Added source-positive `tests/pass/termination_total.ps`, negative non-decreasing/missing-measure tests, additional negative native-source alternative tests, and native `tests/lean/termination_reference.lean` / `termination_native_extensions.lean`. CI invokes the family, checks named `PSCV0-TERM-01` refusals, and verifies that the corresponding unrestricted Lean syntax remains native.
- **No new PASS evidence:** the stable PS0 workflow is still not independently confirmed running/passing at this HEAD; all new fixtures are unqualified.
- Engineering readiness estimate: **39%** across twenty equal-weight `.ps` feature families (recursion 2/5 → 3/5). Strict qualified v7 acceptance remains **0/181 (0%)**. This does not count native `.lean` capabilities.

**Next:** get exact-commit stable Lean CI evidence; fix the first actual parser/quotation/compilation failure rather than adjusting test expectations, then close the complete v7 termination/call/dependent-pattern families and source-to-Lean semantic correspondence. Prefer architecture-wide fixes and feature gates over one-test patch loops.

## Inferred signatures and ordered v7 binders — 15 October 2026

**New implementation checkpoint before this log update:** `8f5c4e9ebe11aa6758f0f8866a0e13fdcd222018`. Read live branch HEAD before further commits.

- PS0 now implements `.ps` **inferred result types** in comma-bound `function`/`def` and private/implicit function declarations, delegating inference to official Lean 4.35.0.
- Introduced an explicitly ordered `pscvTelescopeSegment` for mixed explicit parameter groups, implicit/strict-implicit type parameters, named/anonymous typeclass instance binders, and corresponding `function`, `def`, `theorem` forms. Binder order and dependent types are passed to Lean; no new solver or kernel.
- `PSCV0-BIND-02` enforces no consecutive explicit binder groups both in PS0's owned syntax and in native Lean `def`/`theorem` parse alternatives when embedded in `.ps`. This does **not** change native `.lean` behavior.
- Positive `inferred_signatures.ps` and `interleaved_binders.ps`, negative `adjacent_explicit_groups.ps`, `native_def_adjacent_groups.ps`, `native_theorem_adjacent_groups.ps`, and nullary `def`/`theorem` negatives added; native official-Lean companion source in `tests/lean/v7_signature_reference.lean`. New tests are **candidate fixtures**, not independently qualified.
- Added `P-BINDER-INTERLEAVED`, `N-BINDER-ADJACENT` and `N-BINDER-NULLARY` candidate links in `v7-coverage.json`; all canonical IDs remain PENDING until exact-commit CI.
- **Estimated `.ps` language feature readiness is now 38/100 = 38%** (previously 37%) using a 20-family rubric. Binder family moves 2/5 → 3/5; foundation category 13/25 = 52%; data 14/35 = 40%; proofs/effects 8/20 = 40%; modules/libraries/assurance 3/20 = 15%. **Strict qualified: 0/181 = 0%**, unchanged. This 38% is an *engineering readiness estimate*, not measured test coverage.
- Next qualification gate is a real stable Lean 4.35.0 GitHub workflow run for PR #5, fixing any compile failures and then qualifying the new grammar family. No matching green workflow run was observed prior to this checkpoint.

## User decision: v7 applies only to `.ps` (15 October 2026)

**Implementation checkpoint before this documentation update:** `4bacc4b612db05554a0be7b651e23e2e2c2df4cc`. Check current GitHub PR #5 HEAD before new writes.

- Official Lean **4.35.0** is the unchanged semantic authority. `.ps` continues through PS0's selected v7 parser, local `PS0.Policy` and generated `#pscv_gate` on checked source.
- **Unrestricted `.lean` route implemented:** `ps0 check file.lean`, `ps0 build file.lean Name out/`, and `ps0 lean <args>` now spawn the official native Lean executable from the selected Lean sysroot in a **separate process**, with no `PS0.Policy`/PSCV0 syntax profile injected. Windows chooses `lean.exe`. Arbitrary native Lean syntax and standard Lean compiler assumptions remain available.
- Created `tests/lean/unrestricted.lean` containing native `axiom`, `unsafe`, `partial`, `sorry`, and effectful IO `#eval`. GitHub CI includes positive native-mode check/build/pass-through and compares output to unrestricted native Lean; `.ps` has additional axiom and partial negative emission tests alongside existing unsafe/sorry refusals.
- `ps0 build file.lean` retains host publication-safety behavior (staging, refusal to overwrite) but **does not restrict source syntax, tactics, axioms, imports or effects**. For full native compiler options, `ps0 lean ...` forwards all arguments.
- Detailed [SOURCE_PROFILE_BOUNDARY.md](SOURCE_PROFILE_BOUNDARY.md) documents separate source and assurance semantics, including eventual mixed `.ps` dependencies on unrestricted `.lean` modules, which must be audited **when incorporated in verified `.ps` emission**, not by restricting `.lean`.
- **Language readiness remains 37% subjective `.ps` coverage, strict qualification 0/181 pending stable CI.** The native Lean route is not included in v7 feature scoring. All new regression results remain unqualified until a successful stable-4.35 CI run is inspected.

**Next critical gate:** independently qualify compilation of both PS0 `.ps` and unrestricted `.lean` lanes, and fix any exact-commit CI errors; continue v7 grammar only on `.ps`. Preserve draft PR, original PSCVL and independent PSC0.

## Language-feature continuation — 15 October 2026

**Latest inspected code checkpoint:** `47b3bca21fc8b8b55f9da766479cdc9baea4619e`. Read live HEAD before new writes.

- **Estimated language-feature readiness: 37%**, produced by [language-feature-progress.json](language-feature-progress.json) and [report-language-progress.mjs](scripts/report-language-progress.mjs). This is a **subjective, equal-weight 20-family rubric** (37 points of 100), **not** measured code coverage or normative acceptance.
- **Strict v7 qualification: 0/181 = 0%**. These are the 150 §13 source cases + 31 v7 audit/erratum/correction IDs in [v7-coverage.json](v7-coverage.json). No current stable PS0 exact-commit CI pass is independently confirmed. The completion validator refuses any unsupported PASS record.
- Readiness breakdown: source/declaration/call/scope foundation **12/25 = 48%**; dependent types/data/control **14/35 = 40%**; tactics/verified do/contracts/typed effects **8/20 = 40%**; modules/selected libraries/environment/assurance **3/20 = 15%**.
- Added candidate [pattern_predicates.ps](tests/pass/pattern_predicates.ps) for Lean-native `matches` and braced `if let` with `rfl` proofs, [empty_elimination.ps](tests/pass/empty_elimination.ps) for checked `Empty` elimination by `nomatch`, and negative `nomatch_nonempty.ps` / `iflet_escape.ps`. Normative P-IFLET, P-NOMATCH, N-IFLET-SCOPE and N-NOMATCH are now linked to candidate fixtures but remain pending.
- Studied official pinned [Init/NotationExtra.lean](https://github.com/leanprover/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/Init/NotationExtra.lean): Lean itself lowers `e matches p` to a Bool-returning match. PS0 must use that checked semantics rather than implement an independent pattern matching primitive.
- Implemented explicit `PSCV0-DO-IFLET-ARROW` source refusal for Lean's `doIfLetBind` parser form (pinned `Parser/Do.lean`), preserving v7's staged P1 distinction and binding N-DO-IFLET-ARROW to a negative source fixture. Added an exact diagnostic check in PS0 CI; positive v7 do-if-let lowering remains a separate grammar implementation task.
- CI now runs the machine-readable language-readiness validator as well as the v7 inventory integrity checker. It must report readiness and qualified percentages **separately**.
- **No stable Lean CI evidence yet.** All new positive/negative fixtures are committed **unqualified**, and a green build remains PS0-00's first acceptance gate.

**Next:** independently obtain a stable Lean build/CI receipt; correct any compiler/fixture failures; complete parser §0B and phase-specific negative tests; implement v7 statement-level braced `do if`/ `if let`, modules/imports and dependent patterns with real Lean semantic correspondence. Do not infer a new percent solely from adding tests; reassess the 20-family rubric only after meaningful implementation.
  
## Exact live checkpoint

- Repository: [dwijayuda/lean4](https://github.com/dwijayuda/lean4); branch: `feature/ps0-lean435-stable-v1`.
- Draft [PR #5](https://github.com/dwijayuda/lean4/pull/5) targets `experiment/pscv0-native-language-closure-v1`; preserve the base, draft status and unrelated history. Do not merge or force-push.
- Last inspected implementation/plan HEAD before this handoff update: `4a19c4001739a0783ee26378a8220c19d337e9ef`. **Read live GitHub HEAD again before any new write.**
- Toolchain: official Lean **4.35.0** at `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.
- **CI qualification: NOT VERIFIED.** The connected GitHub workflow/status inspection returned no runs/statuses at this HEAD. Do not claim a green stable PS0 build, full language conformance, or machine-code proof.
- All changed files in draft PR #5 remain under `experiments/ps0/**` or `.github/workflows/ps0-lean435.yml`. The independent PSC0 and historical RC4 PSCVL experiment remain untouched.

## Implemented source checkpoints

1. Standalone Lake package with PS0-owned Syntax, Grammar, Policy, Effect, StandardEnv and CLI; no sibling `[[require]]` or imported `PSCVL.*`.
2. V7 head-specific nullary `Unit`/defaulted function calls and source-specific declaration restrictions; PS0 refuses a non-callable `f()`. Selected native Lean Core correspondence harness has a Unit nullary theorem.
3. V7 source-policy checks for module/public-import/prelude/meta-import/import-all declarations, bodyless `opaque` and unselected value-form `instance`, with specific negative fixtures and CI assertion of diagnostic labels.
4. Native build now uses one user-source read and one authoritative official Lean `runFrontend` elaboration, then emits C from its accepted environment. C and olean are staged in a sibling directory, published only when both exist, and existing destination bundles are not overwritten. This is bounded, not yet a full transitive module identity / crash-safe publication protocol.
5. [Normative coverage inventory](v7-coverage.json): **150** v7 §13 cases (72 positive, 78 negative) and **31** erratum/finding/correction identifiers (4 E, 22 F, 5 C). All remain **PENDING**, including ten cases with candidate fixture links. [Validator](scripts/validate-v7-coverage.mjs) rejects missing IDs, drift, nonexistent candidate fixtures, unsupported PASS evidence and intentionally fails `--require-complete`. CI runs this check.

## Immediate critical path

1. **Obtain actual exact-commit stable Lean CI evidence.** The workflow `.github/workflows/ps0-lean435.yml` has push/PR/workflow_dispatch triggers, but this chat's available GitHub connector has no workflow-dispatch action and did not expose any new runs. Determine in GitHub Actions whether the fork's Actions are enabled, locate exact run/job logs, and fix the **first genuine compile/test failure** before declaring baseline PS0-00 complete. Do not invent CI receipts.
2. Resolve parser-`choice` conservatism only using the **actual Lean-selected alternative** and complete v7 source category registry; correct semantic family root causes, not individual negative tests.
3. Add all missing v7 §13 fixture IDs and attach actual Lean-Core correspondence and error-phase diagnosis. After exact CI, promote each case to PASS with the recorded fixture, commit and run; never bulk-promote based on historical RC4 tests.
4. Implement PS0-03 module/public-import/visibility semantics with real pinned Lean module AST, then dependent language, Standard/P0/P1, contracts/verified effects, transitive assurance, and source tooling per [full plan](PS0_FULL_PSCV0_V7_IMPLEMENTATION_PLAN.md).
5. Improve staged publication to a canonical checked graph/environment digest, hardened no-replace safety, provenance manifest, and native compiler/runtime evidence. Keep verified SOURCE obligations separate from machine semantic preservation.

**Non-goals:** no independent typechecker/kernel, no PSKernel-C0 integration, no compiler self-hosting or PSC0 backend reimplementation in PS0 at this stage.

## Useful acceptance commands (to run in GitHub Linux CI)

```sh
cd experiments/ps0
node scripts/validate-v7-coverage.mjs
node scripts/validate-v7-coverage.mjs --require-complete  # expected to fail while pending
lake build PS0 ps0
lake exe ps0 check tests/pass/basic.ps
lake exe ps0 check tests/pass/default_empty.ps
lake exe ps0 check tests/pass/unit_alias.ps
lake exe ps0 build tests/pass/native_math.ps NativeMath build/native
```

The workflow also executes scoped negative fixtures and links the compiled `NativeMath` executable. Test success **must be observed**, not inferred from these commands' presence in a file.
