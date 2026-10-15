# PS0 — AI Work State (16 October 2026)

## New implementation checkpoint — 16 October 2026

- **Actual work committed:** `PS0/HostCategories.lean` defines the four
  concrete v1 extension-category names (`psTerm`, `psCommand`,
  `psTactic`, `psDoSeq`) plus an initial `PS0.Syntax.lower`
  meta-stage bridge for native-compatible captures. It returns
  the original syntax tree unchanged rather than printing/reparsing
  expressions or recursively modifying quotations/DSLs.
  PS-owned postfix call/category adaptation remains a significant
  next feature. This is **foundation, not full `0B closure**.
- Source admission `check FILE.ps` now passes a modern Lean module,
  reconstructed from its exact native header AST, to official
  `Elab.runFrontend`. It preserves `public`, `meta` and `all`
  import flags; native grammar extensions are interleaved with
  elaboration. Headerless sources are wrapped in `public section`
  while an explicitly written `module` retains native visibility.
- Native `build FILE.ps ...` also consumes that modern module
  input. Existing Lean-native import dependencies may now
  produce the requested native module without conversion to
  legacy/re-exported imports. Complete source origins, .ps project
  import resolution, module graph reproducibility and checked
  artifact provenance remain unqualified.
- Actual v1 `prelude` is **valid by specification** but cannot yet
  be compiled by this frontend without PS0's current policy/module
  source dependency importing full Lean/Init. The frontend now
  refuses that unsupported *implementation* path with the explicit
  `PS0V1-PRELUDE-PENDING` diagnostic instead of violating native
  bootstrap semantics.
- Added `tests/v1/host_category_bridge.ps`,
  `implicit_public_module.ps`, `explicit_private_module.ps` and
  `prelude_implementation_pending.ps`, and candidate CI checks for
  actual parsed module flags, native module emission, the category
  bridge and the prelude refusal.
- Five applicable v1 source/feature requirements have **candidate**
  fixtures in `v1-coverage.json`; statuses remain `PENDING`.
  CI accepts a future `PASS` only with a fixture and actual
  commit/run evidence. **0 of 242 currently qualified**, not a
  measured feature implementation percentage.
- All work stays under `experiments/ps0/**` and its single CI
  workflow. Ordinary `.lean` still routes through the unmodified
  external Lean compiler. The independent PSC0 compiler and
  historical PSCVL experiment remain untouched.

**Next:** obtain real stable Lean 4.35.0 CI/build diagnostics and
fix actual compilation/API mismatches, then complete owned PS host
operand dispatch and `PS0.Syntax.lower` (including calls and
residual empty-call elaboration) without flattening native quotation
syntax. Fully implement v1 prelude isolation and project graphs.

## Authoritative language edition

**PS0 v1 R2** is now the sole normative programming-language target.
The user's complete uploaded 4,163-line Markdown reference was
installed **byte-for-byte** as
[PS0_V1_LANGUAGE_REFERENCE.md](PS0_V1_LANGUAGE_REFERENCE.md).
Its exact Git blob is
`c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`.

Official Lean semantic pin remains **4.35.0**,
`eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.

The PS0 reference supersedes PSCV0 v7 **without backward compatibility,
normative fallback, or inherited v7 profile restrictions**.
The independent compiler `dwijayuda/pskernel` and the prior
`experiments/pscv0-lean-native` experiment remain unchanged.

## Current branch, PR, safety

- Repository: `dwijayuda/lean4`
- Branch: `feature/ps0-lean435-stable-v1`
- Draft PR: [#5](https://github.com/dwijayuda/lean4/pull/5)
- Re-read live GitHub HEAD before any future write; preserve history
  and do not merge/force-push without an explicit request.

## Work implemented in this migration

1. Replaced the existing smaller `PS0_V1_LANGUAGE_REFERENCE.md` with
   the exact uploaded standalone R2 language document.
2. Replaced frozen v7 grammar-command/attribute/keyword exclusions with
   native registered grammar and a **diagnostic-only** static
   syntax-kind inspector. Official Lean's interleaved
   parse/elaboration is the language-checking authority.
3. Replaced the blanket v7 proof gate with informational
   `#ps0_evidence`. Ordinary `axiom`, `unsafe`, `partial`, IO,
   native meta features and development `sorry` are language
   capabilities; this reporting command issues no verification claims.
4. Updated source headers to admit written native `module` and
   implicit headerless modules with distinct source visibility
   defaults. Imports are no longer governed by a v7 Standard allowlist.
   Full module export, public-body/exposure and prelude semantics
   are still unfinished.
5. Changed instance-priority source adapters to use registered
   Lean priority grammar rather than a closed named list.
6. Replaced `PS0_STANDARD_ENV.json` and `PS0/StandardEnv.lean`
   finite allowlist metadata with a v1 environment-identity
   placeholder. A complete imported registration digest is
   still required for reproducible stronger claims.
7. Created `v1-coverage.json` from the new reference, covering
   **100** capability families, **64** positive source cases,
   **47** negative source/disallowed-claim cases, and **31** R2
   boundary witnesses: **242** requirements, all `PENDING`
   qualification.
8. Added selected native-capability v1 source candidates under
   `tests/v1` and replaced active CI v7 acceptance tests with
   v1 source/registry and bounded JS backend checks.
9. Wrote [PS0_V1_IMPLEMENTATION_PLAN.md](PS0_V1_IMPLEMENTATION_PLAN.md)
   and updated README, CONFORMANCE and SOURCE_PROFILE_BOUNDARY.

## Important limitations and known gaps

- No exact-commit, successful Lean 4.35.0 PS0 CI run has been
  independently observed. **Do not claim the compiler is green.**
- The full `psTerm`, `psCommand`, `psTactic`, `psDoSeq`
  category architecture and `PS0.Syntax.lower` normalizer
  remain unimplemented. This is the main language-completeness gap.
- The actual frontend currently imports `PS0.Policy` as a host
  parsing environment, so the v1 `prelude` guarantee of
  **no hidden ordinary/meta Init** requires further architectural
  separation and targeted qualification.
- Public-by-default names, actual native modern-module compilation,
  exported body transparency and mixed `.ps`/`.lean` graphs
  are not yet fully implemented. Import-era native emission may
  still refuse unsupported paths; that is a compiler limitation,
  **not** a v1 source-language ban.
- The old source adapter code contains some internal `pscv*`
  identifiers, but these are historical *implementation names*
  only. No v7 semantics or v7 admission policy should be inferred
  from their spelling. Refactor them cleanly when adapting
  the host-category grammar.
- The Lean-native Nat-only JS backend remains a selected
  executable backend subset. Its unsupported types and effects
  do not narrow the PS0 v1 source-language definition.
  JS correctness/semantics-preservation remains unqualified.
- **No v1 completion percentage is established.** The former
  41% estimate and 181-case v7 ledger are retired. The new
  242-item registry is a requirements inventory, not a test PASS
  count or measured implementation percentage.

## Next critical implementation work

1. Obtain the actual official 4.35.0 build result; fix API/grammar
   compile errors at the family level. Test the new native
   v1 source cases and basic JS backend.
2. Implement native-vs-PS category ownership and the `PS0.Syntax.lower`
   meta interface without losing syntax data or provenance.
3. Implement source call/brace/binder/record ownership, the PS
   extension dispatch boundary and exact v1 negative oracles.
4. Complete module/stage/import/public-body behavior and
   prelude isolation via pinned Lean module APIs.
5. Expand native language families, effect/erasure/contract
   support and claim-specific assurance `12`, then qualify
   v1-coverage entries one by one with real CI evidence.

No background work, implicit approval policy, certification or
verified-runtime result has been promised. All committed work
remains on the draft branch.
