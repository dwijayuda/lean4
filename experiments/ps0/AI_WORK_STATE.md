# PS0 — AI work state (15 October 2026)

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
