# PS0 — AI Work State (16 October 2026)

## Repository and authority

- Repository: `dwijayuda/lean4`.
- Branch: `feature/ps0-lean435-stable-v1`; draft PR #5.
- This continuation began at `99c825d01eac4a15025974213afb6440232d7da6`.
- Latest code/workflow checkpoint before this state update:
  `6120a40370fba616c77449137352d8530e781dff`.
- Re-read live HEAD before further writes. No force-push, merge or branch deletion.
- Sole language authority: `PS0_V1_LANGUAGE_REFERENCE.md`, PS0 v1 R2,
  Git blob `c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`.
- Official Lean semantic pin: 4.35.0,
  `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.
- PSCV0 v7 is superseded without backward compatibility. Its 41% estimate
  and 181-item ledger must not be reused for v1.
- Keep the independent PSC0 compiler and historical PSCVL experiment unchanged.
  Ordinary `.lean` remains native and unrestricted.

## Typed standard host RHS integration — 16 October 2026

- The PS0 v1 parser now owns the typed `function` and typed `const`
  right-hand-side syntax through `psTerm`. Each source form delegates
  to the existing `PS0.Syntax.lower` bridge before constructing the
  official Lean `def` declaration; binder ordering and nullary Unit
  sugar still use the existing Lean-backed declaration adapter.
- This is the first migration of actual **standard declaration body**
  operand slots from native `term` to PS-owned `psTerm`. The source
  adapter is higher priority than the previous native-body alias,
  while native `.lean` syntax remains unchanged.
- New `tests/v1/standard_host_declarations.ps` checks nested,
  named, trailing-comma, partial and constant-initializer source
  calls. Three negative sources cover named-before-positional,
  duplicate named arguments and comma-only calls. The full PS0
  CI workflow includes target-specific checks.
- The existing Nat-only, Lean-written JS IR lowerer was extended
  to accept the new `psTerm` body nodes. It continues to reject
  unsupported argument semantics and only emits exact-arity calls
  to earlier checked Nat functions. JS tests now include a host
  trailing-comma function call and const initializer, with Node
  BigInt and TypeScript declaration checks.
- Seven existing v1 call acceptance cases gained **additional
  standard-host candidate fixtures**; none has been marked PASS.
  The normative 242-item inventory remains unchanged.
- Work is committed directly in the existing draft branch.
  **No exact-commit Lean/Lake build or Actions test execution
  has been observed**. Earlier branch-wide Actions and check-runs
  returned zero, and the working container has no Lean/Lake or
  working GitHub DNS access.
- Significant work remains: inferred-result source aliases,
  native `def`/`theorem` body slots, proof/tactic/do/contract
  expression slots, generalized postfix/tuple/head ownership,
  empty calls, priority collision resolution and source
  identity/provenance. This is an initial source-category
  integration, not complete PS0 v1 language conformance.

**Next critical gate:** qualify a real pinned Lean 4.35.0 build,
correct any actual macro quotation/parser ambiguities, and
systematically cover other standard expression operand positions
without rewriting unrelated DSLs or native syntax quotations.

## New PS0 v1 implementation checkpoint — 16 October 2026

- Migrated the **standard source declaration-body** operand from
  native `term` to the specified PS-owned `psTerm` category in
  source `function` and `const` aliases. Typed and inferred
  result types, plus typed/inferred private variants, now invoke
  `PS0.Syntax.lower` before building official Lean `def` syntax.
  Existing Lean elaboration and nullary Unit sugar are reused;
  this is not a second typechecker or a source-text transpiler.
- Added `tests/v1/standard_host_declarations.ps` with Lean
  theorem oracles for nested, named, trailing-comma and partial
  application, public constants, private functions/constants,
  inferred results and source-nullary Unit behavior. Three
  source-invalid cases exercise duplicate named parameters,
  invalid positional-after-named order and comma-only calls.
- Added a family CI step in the full PS0 workflow with exact
  intended diagnostic assertions for named argument errors.
- Updated the Lean-authored Nat JS lowering to recognize the
  new typed standard `psTerm` RHS syntax, maintaining its
  closed IR contract: exact-arity calls to earlier Nat functions,
  native Nat operators and constants only; other sources fail
  closed. Expanded the JS runtime and TypeScript regression
  to cover trailing-comma calls and const initializer exports.
- Seven already-existing v1 call requirements gained an
  additional **standard-host operand candidate** mapping in
  `v1-coverage.json`. These are not new requirements or PASS
  evidence. The 242-item normative registry remains unqualified.
- **Remaining G1 work:** general high-postfix call heads,
  type-directed empty-call completion, source-gap provenance,
  full native `def`, theorem/proof, binder/type, tactic, do,
  contract/configuration operand slot selection, and imported
  extension/quotation disambiguation. The current contribution
  closes only the standard `function`/`const` BODY family.
- The GitHub Actions endpoint returned **zero recorded branch
  workflow runs** before these edits, and this environment
  has no accessible pinned Lean/Lake toolchain. The code was
  committed through the authorized GitHub connection but
  **has not passed an observed Lean 4.35.0 compiler run**.
  Keep PR #5 draft; do not infer language completion percentages.

**Next critical path:** obtain the focused/full Lean CI results
and correct any actual macro parser/API errors in one coherent
family; then extend the same category-owner pattern to standard
types, theorem statements, tactic and effectful `do` slots,
while preserving native quotations and independent DSL operands.

## This continuation: real host-category implementation and fixture repairs

1. `PS0/HostCategories.lean` now gives the owned adjacent-call production
   higher parser priority than the native-capture bridge for an equal input
   span. Unresolved `choice` nodes are explicitly refused by the lowerer;
   this is not a complete ambiguity-coalescing implementation.
2. Nonempty host calls now use pinned Lean's
   `sepBy1(psCallArg, ",", allowTrailingSep)` grammar. One trailing comma
   is allowed without manufacturing an extra argument. Comma-only and
   repeated-comma inputs have negative regression fixtures.
3. Generated native application nodes retain the complete source-call range
   as **synthetic** source info. Native captured subtrees are returned
   unchanged. This improves diagnostic provenance but does not prove a
   source-fidelity claim or validate fabricated syntax provenance.
4. Fixed concrete regression-fixture problems: C-style `//` comments in a
   purported positive `.ps` fixture, a macro returning raw `Syntax` where
   the native macro command expects `TSyntax term`, and reserved-looking
   local names. Test setup must succeed before a language rejection is
   meaningful.
5. Strengthened the positive host fixture with checked examples for nested,
   named, tuple, partial and trailing-comma calls. A macro inspects the raw
   host syntax, native application argument count and original source range.
   Native capture identity is checked with Lean's `Syntax.eqWithInfo`.
6. Added `tests/run-host-categories.sh` and the independent
   `.github/workflows/ps0-host-categories.yml` job. It checks the exact
   Lean git hash, builds only `+PS0.HostCategories`, and runs the same
   committed fixtures through a minimal native harness. This isolates
   component failures from unfinished PS0.Syntax/CLI/JS backend work.
   It checks 2 positive fixtures and 4 intended negative fixtures, retains
   diagnostic logs as a workflow artifact, and does not replace full PS0 CI.

## Evidence obtained, not inferred

- Confirmed GitHub reads and successful file-update/create commit responses.
- `bash -n tests/run-host-categories.sh`: PASS in the working container.
- Focused workflow YAML parse and job-configuration assertions: PASS locally.
- Lean/Lake execution: NOT RUN successfully. Neither executable is installed
  in the working container, public GitHub DNS resolution failed, and the
  separate download attempt did not supply a toolchain.
- The branch-wide Actions GET at the starting checkpoint returned
  `total_count: 0`. This query did not filter to pull-request events.
- No Lean compilation, kernel proof, JS runtime, or exact-commit full PS0
  conformance PASS has been claimed. The new workflow is a test definition
  until an actual run and its logs are inspected.
- `v1-coverage.json` was not promoted or rescaled: its 242 requirements and
  existing candidate links retain their previous qualification status.
  Adding a fixture or parser rule is not a new conformance percentage.

## Current architecture carried forward

- Four explicit extension categories exist: `psTerm`, `psCommand`,
  `psTactic`, `psDoSeq`, with `PS0.Syntax.lower` as the explicit bridge.
- Owned nonempty identifier-head calls work by syntactic lowering to the
  native Lean application AST; positional/named ordering is enforced.
- Full standard declaration, proof, tactic and do operand slots are NOT
  systematically mapped to host categories. Native term macros do not
  establish the complete v1 category contract.
- `check` and native `build` prepare modern Lean modules, preserve imported
  public/meta/all flags, and give implicit `.ps` modules public-name defaults.
  Full mixed-source module graphs, body exposure and source-origin fidelity
  remain unqualified.
- `prelude` is valid v1 source. The current implementation explicitly refuses
  its unsupported bootstrap path rather than secretly importing Init.
- `#ps0_evidence` is informational, not a policy approval or certificate.
  Native axioms, unsafe/partial source, IO, extensions and development holes
  are not globally banned by the v1 language.
- The all-Lean JS backend remains a bounded Nat/BigInt implementation with
  typed IR, `.js`, `.d.ts` and Source Map v3 output. Full runtime preservation
  and wider language/backend support are still unqualified.

## Next implementation priorities

1. Inspect the new focused host-category workflow. Fix its first real
   compiler/parser/quotation failure before expanding this component again.
   A green focused job is only component evidence, not full `.ps` conformance.
2. Run full `ps0-lean435.yml` and fix blocking API/grammar errors by coherent
   families. Keep negative tests tied to their intended diagnostic.
3. Implement the pinned standard host operand-slot map without entering
   native quotations, independently owned extensions or DSL syntax.
4. Complete generalized high-postfix heads, host empty-call completion,
   host-gap rejection without native fallback, and ambiguity coalescence.
5. Complete bootstrap isolation, actual project graphs/public-body exposure,
   imported registration identity and claim-specific assurance.

Do not mark a v1 requirement PASS without the exact fixture, source/compiler
identity, intended semantic or diagnostic oracle, and inspected CI evidence.
Earlier development narrative is retained in Git history.
