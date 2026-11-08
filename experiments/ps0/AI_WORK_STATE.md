# PS0 — AI Work State (8 November 2026)

## Active continuation: Lake native executable integration

- Source branch: `feat/ps0-lake-native-20261108`, based on PR #6 source `39b8f4cecd8e60b2297c1d01f81d8840c3dc3715`; history preserved.
- Added `build-native FILE.ps ModuleName OUT_DIR` and `lakefile.native.lean` targets composing the existing `.ps` adapters, official Lean `runFrontend`/LCNF C emission, imported-module `linkInfoNoExport`, `buildLeanO`, and `buildLeanExeSync`.
- No new typechecker, proof kernel, optimizer, runtime or native emitter. Official Lean 4.35.0 pin and normative R2 reference remain unchanged.
- The development target traces source, compiler, imported native modules, build options and Lean/toolchain; publication occurs only after successful linking and refuses an existing output directory.
- Tests authored before implementation cover real executable behavior (IO, source calls, collections/closures and imported Lean code), warm reuse, source and native import invalidation, malformed host calls, elaboration failure, missing entry point/link failure, and no-replacement publication.
- Validation pending: execute the exact new source on Linux GitHub Actions via an immutable source selector in the Actions-enabled `dwijayuda/pskernel` runner. No local compiler/proof/runtime execution or passing native result is claimed at this checkpoint.
- Initial Linux run `42472928133` built clean PS0 (28 jobs) but found the implicit PS0 import hid `psTerm` from source extension declarations. The injected import is now public, retaining native module staging while exposing the specified host category interface. Native tests had not yet executed in that failed run. Push run `42472924581` failed during Elan download with HTTP 503 before compilation.
- Run `42473126320` then exposed two pre-existing adapter defects: the host separator used zero-width `ppSpace` instead of consuming a comma, and the function-only consecutive-group restriction incorrectly applied to native `def`/`theorem` telescopes. Both are corrected against R2; the function alias still rejects consecutive explicit groups. The run also caught a Lake record-field syntax error, now corrected. These failures remain failed evidence.
- Subsequent Linux execution passed host-call AST/arity/source-span witnesses. The standard private-alias witnesses incorrectly used public theorems to refer to private declarations under modern Lean modules; those witnesses are now private, and a negative test retains the real prohibition on public leakage. The Lake process record now uses aligned multiline fields. Runner bootstrap retries actual HTTP 503 download failures without changing the Lean pin.
- Existing baseline was independently read back: external Linux run https://github.com/dwijayuda/pskernel/actions/runs/40772012597 passed proof-linked and host-contract jobs for exact source `39b8f4cecd8e60b2297c1d01f81d8840c3dc3715`.
- Scope: one `.ps` executable entry module, ordinary toolchain and Lake-declared `.lean` dependencies. General recursive `.ps` project dependency discovery, complete host operand adaptation, bootstrap `prelude`, source-origin fidelity and verified runtime execution remain open. The 242-item conformance ledger is not promoted by these tests.
- No main merge, force push, npm publication, normative language change, or changes to independent PSC0/PSC1 source.

The sections below retain the earlier proof-linked checkpoint and its observed failures as historical evidence; they are superseded only where the exact-source results above say so.

## Active work and identities

- Repository: `dwijayuda/lean4`; project: `experiments/ps0`.
- Implementation branch: `feature/ps0-proof-linked-js-ts-20261029`; draft PR #6.
- Architecture base: `60ca3b645e0fc05c6b6416b7f9ea46afa10b46fc`.
- Current implementation checkpoint: `811487dbf0434c384ccfa1de35d28043e8f34af7`.
- Semantic pin: Lean 4.35.0, `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.
- Unchanged R2 reference blob: `c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`.
- Historical handoff remains in `AI_WORK_STATE_20261016.md`, original blob
  `c2898d38b8cf0c53b43c021a64c4175cbec33b8f`.
- Re-read live HEAD before writes; preserve history and use expected-SHA updates.

## CI activation: working external runner, not an unverified local substitute

The Lean fork did not record PS0 branch workflows. Its activation cause is
still unestablished. An isolated CI-only branch in the existing Actions-enabled
`dwijayuda/pskernel` repository now checks out **immutable Lean-fork commits**:

- Runner branch: `ci/ps0-proof-linked-runner-20261029`; draft PR #210.
- Workflow: `.github/workflows/ps0-external-proof-linked.yml`.
- Source selector: `ci/ps0-source.json`; no moving source branch is trusted.
- No PSC0/PSC1 source is changed. No main merge or package publication.
- Host tests run on Ubuntu 24.04; proof replay runs on Ubuntu 22.04.
  The 24.04 runner rejected Bubblewrap loopback setup before proof execution;
  22.04 supports the original isolation. No sandbox-disable flag or global
  security relaxation was introduced.
- Runner commit, source commit and CI run identity must always be distinguished.

## Executed evidence, not inferred milestones

Run https://github.com/dwijayuda/pskernel/actions/runs/40770867836 tested source
`e1fed198e43ef84ddf6fa740b8acac257c7ce68e` using runner commit
`b766064ca662b575575af5edc127396f0aaa36b3`.

Observed and inspected:

- Full PS0 executable, existing libraries and Verified model/emitter/extractor:
  **31 build jobs completed successfully** with the exact Lean pin.
- Host contract suite: **27/27 passed**.
- Resource-bound Lean regressions: passed; the deep saturation property uses
  induction rather than increasing elaboration limits or trusting native_decide.
- Bubblewrap isolation probe: passed, without disabling network namespaces.
- Actual inventory `.ps` checking through `lake exe ps0 check`: passed.
- Official `lake comparator --config source-comparator.json` began sandboxed
  builds, then correctly failed a public-name visibility error in the generated
  challenge. Neither proof comparator nor runtime qualification is yet claimed
  successful at this checkpoint.

Evidence artifact: `12853080469`, ZIP SHA-256
`d2617f0ee57b7e859f268eaeada3d7827afd6932aa1dc1359a8f40c186c6454e`.
The earlier `proof-linked-status-20261029.json` records the initial unexecuted
state only; it is not the current execution status.

## Repairs already made from actual logs

Committed the missing dependency-free Lake manifest; corrected the pinned
trailing-separator parser descriptor, MacroM diagnostics, JSON names, explicit
native quotation categories, compound syntax atoms, numeric counter inference,
native implementation signatures and a reserved local identifier. Converted
the source-support dependency chain to modern modules with actual meta staging;
kept semantic model/effect definitions ordinary and exposed where their proof
interfaces require definitional access.

The original compiler implementation therefore HAS changed in this continuation;
older documents saying all compiler sources are unchanged describe the earlier
candidate commit, not this checkpoint. No normative R2 revision is made.

The host now bounds file reads and potentially exponential target expansion,
binds all source/challenge/configuration inputs across both proof phases,
revalidates after target execution, records host/tool identities, and refuses
wrong target versions. The emitter checks its size budget before expanding the
candidate AST/text. Nine additional host regressions cover these boundaries.

The current checkpoint fixes the observed visibility failure with separate
`public import` and `import all` declarations in generated and authored proof
modules. It does not use forbidden `public import all` or bypass the comparator.
Run 40771430923 is the next qualification attempt for source `811487db...`;
inspect its completed logs before recording further PASS claims.

## Scope and next gate

Continue until the bounded `.ps` → full-Lean proof → exact Nat2 IR → JS/TS
pipeline and intended refusal tests execute successfully. Then retain the exact
conditional artifact and receipts, and add focused regression evidence for the
frontend/module repairs. Do not mark the entire MB0–MB3 roadmap or R2 complete
from a single example.

The only publication profile remains `conditional-nat2-reviewed-v0`;
`verified-portable` is refused. Source/extraction/target-model proofs do not
prove the complete JS engine, TypeScript compiler, serializer, arbitrary
compile-time-code isolation or foreign libraries. Full language closure,
modules, richer types, effects and Python/PHP/Rust backends remain separate.

All actual validation in this continuation is Linux GitHub Actions. No local
compiler build, force push, main merge, registry publication or new proof kernel.

