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
