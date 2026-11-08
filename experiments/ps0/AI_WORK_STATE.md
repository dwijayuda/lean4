# PS0 — AI Work State (8 November 2026)

## Qualified continuation: thin adapters and Lake native executables

- Source branch: `feat/ps0-lake-native-20261108`; draft [Lean-fork PR #7](https://github.com/dwijayuda/lean4/pull/7), based on PR #6 source `39b8f4cecd8e60b2297c1d01f81d8840c3dc3715`.
- Qualified implementation/test commit: **`07a1da68aacf2462e9723a79242c322a21ca3c83`**. The documentation follow-up records this result without changing compiler or test bytes.
- Semantic pin: official Lean 4.35.0, `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`. Normative R2 blob remains `c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`.
- Runner branch: `ci/ps0-lake-native-20261108`; draft [pskernel PR #219](https://github.com/dwijayuda/pskernel/pull/219).
- Exact runner commit: **`b0742c8ed34125838155851a979fe80cbc36d369`**. Its immutable `ci/ps0-source.json` selects the qualified Lean-fork commit above.
- **Linux run [42474108191](https://github.com/dwijayuda/pskernel/actions/runs/42474108191) completed successfully on 8 November 2026.** All three jobs passed: native-build `128711492870`, proof-linked `128711492711`, host-contract `128711492922`. Source and runner commit identities are distinct.

### Implemented behavior

`lake exe ps0 build-native FILE.ps ModuleName OUT_DIR` now produces an actual executable through the existing PS0 syntax adapters and official Lean frontend/kernel/LCNF C emission, followed by Lake's imported-module `linkInfoNoExport`, `buildLeanO` and `buildLeanExeSync`. There is no intermediate textual `.lean` program and no new typechecker, proof kernel, optimizer, runtime or native emitter.

`lakefile.native.lean` supplies incremental development targets. The CLI passes `-R` so Lake's configuration reflects each source/module selection while compiled artifacts retain their incremental traces. Source bytes, compiler, native dependencies, options and Lean/toolchain participate in the build. Executable emission requires a local compiled `main` in Lean's LCNF declaration inventory. The CLI publishes the linked executable plus `native-build.json` only after success and refuses an existing output directory; the receipt explicitly records `verified_execution: false`.

Thin adapter corrections expose the specified PS host categories through the implicit public PS0 import, consume actual commas in the owned host-call parser, and retain native `def`/`theorem` binder groups while preserving the stricter `function` alias rule. Private-alias witnesses obey native modern-module visibility; a negative test retains the prohibition on public leakage.

### Executed Linux evidence

- Clean PS0 build: **28 jobs passed**; native target builds: **31 jobs passed** for the executable fixture.
- All seven selected adapter/native-language fixtures passed, including extension registration, host-category identity, call AST/argument partition/source spans, declaration bodies, and implicit/explicit modern modules.
- Actual executable behavior passed: IO and arguments, host calls, collection/closure code and a separately compiled Lean dependency returned `PS0_NATIVE:42:7:15:2`.
- Warm build retained executable hash and executable/C mtimes. Editing `.ps` source changed runtime output to `44:7`; editing the imported native Lean module changed it to `44:9`. CLI source/module selection and publication returned `44:7` with the original support library.
- No-replacement publication, unknown source identifier, absent local entry point, malformed host call, consecutive explicit groups on `function`, and public use of a private declaration all rejected as intended.
- The unresolved extern reached the actual linker: `ld.lld: error: undefined symbol: ps0_missing_external_71ad`; no executable directory was published.
- The existing sandboxed proof-linked JS/TS qualification and host-contract suite passed at the same exact source. Its result remains a bounded conditional target-model/runtime result, not whole-language verified execution.
- Native [artifact 13613899151](https://github.com/dwijayuda/pskernel/actions/runs/42474108191/artifacts/13613899151), ZIP SHA-256 `536de5c71bb3031af5edc2722ff0a1b9574c99ccf889117ec475dab2e63b3a52`, retains build/adapter/native logs, source/runner identities and the publication receipt.
- Proof-linked [artifact 13614103254](https://github.com/dwijayuda/pskernel/actions/runs/42474108191/artifacts/13614103254), ZIP SHA-256 `e7580d036e6a34f3a5c8ffdf1540c2ef5e3f57925e0899053b1a17c951a507d6`, retains the existing comparator/runtime evidence.
- No compiler, proof or runtime tests were executed locally; the evidence above is actual Linux GitHub Actions execution.

### Scope and remaining work

This qualification covers one `.ps` executable entry module with toolchain and Lake-declared `.lean` dependencies. Recursive `.ps` project dependency discovery, complete host operand adaptation, bootstrap `prelude`, source-origin fidelity and verified runtime execution remain open. The 242-item conformance ledger is not promoted by these tests. No whole-compiler preservation or cross-platform native-release claim is made.

History is preserved. No main merge, force push, npm publication, normative language change, or independent PSC0/PSC1 source change was made.

### Earlier attempts and diagnostics

Earlier failed/cancelled attempts remain recorded as such: `42472928133` exposed private host-category visibility; `42473126320` exposed binder/separator defects and a Lake record-layout error; `42473650349`/`42473644127` demonstrated native execution/invalidation before CLI configuration refresh failed; `42473838785` demonstrated publication before the missing-main negative exposed a library-main fallback. HTTP 503/504 installer failures were infrastructure failures before compilation; bounded installer/toolchain retries retain the exact Lean semantic pin. None of those partial results substitutes for the successful full run above.

The following sections preserve the 29 October proof-linked checkpoint and its original evidence boundaries.

## Prior proof-linked work and identities

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

