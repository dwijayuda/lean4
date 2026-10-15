# PS0 — AI work state (15 October 2026)

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
