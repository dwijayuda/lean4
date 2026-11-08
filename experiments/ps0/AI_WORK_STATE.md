# PS0 — AI Work State (8 November 2026)

## Active goal: compiler-source replacement with ps

The goal remains replacing all handwritten Lean compiler program sources with `.ps` while reusing Lean's parser/elaborator/kernel/LCNF/C infrastructure and Lake's dependency, artifact, native object and link machinery. Source work is on draft [Lean-fork PR #8](https://github.com/dwijayuda/lean4/pull/8), branch `feat/ps0-recursive-projects-20261108`; Linux qualification is draft [pskernel PR #220](https://github.com/dwijayuda/pskernel/pull/220), branch `ci/ps0-recursive-projects-20261108`.

### Current candidate

Source **`fb86cc425f0688bf3c6e98ff6c7adb8e899fe883`**, runner **`0bca62aefdb00992d891f57c1a608dc0dacd60a3`**, Linux [run 42488162021](https://github.com/dwijayuda/pskernel/actions/runs/42488162021): project/category **128754567397**, native **128754567736**, proof-linked **128754567672**, host **128754567546** all PASS. The shared native driver-input target additionally passes **PS0_PROJECT_DRIVER_INVALIDATION** after changing actual compiler bytes; normal warm reuse and source/native dependency invalidation still pass. Compiler stage one **128754834515** is running with the corrected migrated library search path and early retention of its executable/output hashes. No stage-one/fixed-point PASS is claimed yet.

Project [artifact 13619929692](https://github.com/dwijayuda/pskernel/actions/runs/42488162021/artifacts/13619929692) ZIP SHA-256 `d1ea345719129239bf82acf92b543546e513e375d9e4211dfca815577edd759d`; native [13620303005](https://github.com/dwijayuda/pskernel/actions/runs/42488162021/artifacts/13620303005) `b7e489f9fa186b0fe31a64830a02fdb9ad07dab8eb5b430529001ea1d4c03a99`; proof-linked [13620970053](https://github.com/dwijayuda/pskernel/actions/runs/42488162021/artifacts/13620970053) `9f0e5517f1f8947ff73a97603855728a6adb630dd1262ef0bc95302151052900`.

The separate Linux [link-map audit 42488039370](https://github.com/dwijayuda/pskernel/actions/runs/42488039370), runner **`3dddb837c8b29b7619c945bcc3d4304ef7d47ff3`**, job **128754113727 PASS**, inspected prior source `46541521a95ac7829279faf441f922a977061f6f` artifact `13620495494`. It found rebuilt frontend/emitter/PS0 objects and **zero SDK Lean/Std/Init source-archive entries**. Audit [artifact 13620281682](https://github.com/dwijayuda/pskernel/actions/runs/42488039370/artifacts/13620281682) ZIP SHA-256 `95dbb7bc8665da8cf269c9fb7e7ae5bc60d7480c8a67b0b3e42ef0198f5c97bf`. This is link-map provenance only: the prior harness failure prevented retaining its binary, so ELF dependencies/runtime smoke remain unqualified at that checkpoint.

### Historical initial recursive/category checkpoint

- Implementation/test source: **`b842b26fa2dffaee6a73f03fb70ca77683ccaf31`**; runner head: **`a2ff849cd861a32e52dbfee94f0283c749f37040`**. The runner selector pins that exact source.
- Linux [run 42483607627](https://github.com/dwijayuda/pskernel/actions/runs/42483607627): recursive/category job **128740672990 PASS**, native job **128740672968 PASS**, proof-linked job **128740672770 PASS**, host-contract **128740672920 PASS**. Compiler-source stage one failed; the overall workflow is not PASS.
- Official Lean 4.35.0 commit **`eb6cafb7290e8bd5f2937522d8d804f58f02bafc`** and normative R2 blob **`c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`** are unchanged.
- Project [artifact 13618347877](https://github.com/dwijayuda/pskernel/actions/runs/42483607627/artifacts/13618347877), ZIP SHA-256 `1676b6c5b5da9d84f24a569bf53877fc424824018337fca8caf814baebc71980`, retains build/category/project logs, exact identities, publication receipt and native source-input selection receipt.
- Native [artifact 13618945967](https://github.com/dwijayuda/pskernel/actions/runs/42483607627/artifacts/13618945967), ZIP SHA-256 `af1386f8c90e7a630cb85b12e101b76fda5b30bf4b120aefac76a44425c721af`, retains the rerun of the single-module qualification.
- Proof-linked [artifact 13619080687](https://github.com/dwijayuda/pskernel/actions/runs/42483607627/artifacts/13619080687), ZIP SHA-256 `9a8e13f6a9126b1739c8f4a71fb5f37ad8dd6953cb54d1404a7d9462e496ceb0`, retains the existing bounded sandbox/comparator/runtime qualification.

Recursive `build-project SOURCE_ROOT Dotted.Module OUT_DIR` now uses native Lake module input and `leanArts` facet adapters. The frontend consumes Lake's actual `ModuleSetup`; native dependencies use the official Lean process. There is no separate dependency graph, artifact format, optimizer or linker. The fixture executes **42:7**, then **45:7** after a transitive PS edit, then **45:9** after a native dependency edit. Warm executable hash and mtime remain unchanged. Native meta imports, no-replacement publication, native prelude with no hidden imports, absent local compiled main, source-kind collision, dependency cycle and private import visibility all pass their explicit oracles. The native `expose` rule is used explicitly for the imported definition needed by a proof.

The mapped category fixture executes **PS0_CATEGORY_SLOTS:3:3:3:3:3** and passes declaration result/value/proof slots, general/chained/closure calls, selected conditional/single-return do/braced exact operands, opaque native tuple DSL/quotation data and order/duplicate/gap negatives. `standard-adapter-map.json` records the pinned map and exact evidence. Remaining binder/default, mixed declaration, multi-statement do, tactic, match, collection/interpolation and configuration/attribute roles remain open. Registrations alone are not conformance; apply/refine do not yet have dedicated executed probes. Broad ledger families remain pending.

### Compiler-source gate remains open

The bootstrap checkpoint is source **`46541521a95ac7829279faf441f922a977061f6f`**, runner **`8f31edbc9012876b9b0024f97f5db6e972e938d1`**, Linux [run 42484334810](https://github.com/dwijayuda/pskernel/actions/runs/42484334810). Its project/category **128742816345**, native **128742815964**, proof-linked **128742816265** and host **128742816215** jobs all PASS. Compiler stage one **128743130971** completed **5,131 native Lake jobs**, built/linked the full 2,564-module forest, audited every PS input and generated C/olean, and ran the migrated environment command. Its final smoke check failed because the harness omitted the built PS0 library from `LEAN_PATH`; therefore this is **build/link evidence, not a full stage-one PASS**, and stage two was skipped. The project artifact **13618417596** has ZIP SHA-256 `3afec24187928ff6612d82a83e9d1a649f0e3bb5e48ffe3cf139db6f692045e8`; native artifact **13619106570** has `b2606413204ed50d1baba66b0e3f7f85b84db5ca7db858e457e81140bf96d5d0`; proof-linked artifact **13618907619** has `8d01f936943a3d4026802436cec9cba03234ff63adf6f448c0ab198702cceb01`. Compiler [artifact 13620495494](https://github.com/dwijayuda/pskernel/actions/runs/42484334810/artifacts/13620495494) has ZIP SHA-256 `c0afd12a60321f83d1ff7bbf1810c77c2fd90d3cc5a988b2cfb28df228706749` and retains exact input inventory, full build log, migrated environment output, failed smoke log and native link map.

The next candidate supplies the rebuilt native library search path to the smoke process and retains the migrated executable and output hashes before smoke checks. Driver input hashing is shared through a native Lake target rather than repeated once per module; a Linux test must prove that changing driver bytes invalidates module inputs and re-elaborates actual code. Candidate run `42487933465` caught an invalid unused-binder spelling in that target declaration; the corrected candidate requires fresh execution. A separate read-only Linux artifact audit is on `ci/ps0-compiler-audit-20261108`, initially inspecting the retained link map without claiming unavailable ELF/runtime evidence.

`compiler-source-inventory.json` enumerates **2,546 pinned src/**/*.lean Git blobs**, including Init/Std/Lean/Lake, LeanIR, Leanc, LeanChecker, LeanExport and LakeMain. The Linux test verified every source blob and converted **2,564 modules including PS0**, **2,541 byte-identical**. Stage one (**job 128741050411**) built into Init, then failed at `Init/Coe.ps` because ordinary package identity generated `lp_ps0_String_hash`; the native bootstrap runtime exports the unprefixed symbol. Failure [artifact 13618597372](https://github.com/dwijayuda/pskernel/actions/runs/42483607627/artifacts/13618597372), ZIP SHA-256 `c52865ecad9ffe006e8c34c06128dc2e0672cb6b10f67594c99bd2cfcda14c57`, retains the inventory and build log. The next candidate uses Lake's existing bootstrap package mode and pinned SDK headers; it remains unqualified. The test still requires every actual PS input, generated olean/C artifacts, a migrated native compiler/link map and a second clean C/olean comparison. No compiler-source replacement or fixed-point PASS is claimed.

Earlier failed candidates remain failures, including incorrect use of newer fork APIs instead of the pinned SDK's `leanArts` API, malformed implicit import context, and missing native definition exposure in the fixture. The previous afda739 checkpoint's project/native jobs passed, but its workflow/compiler stages were cancelled for the local-entry safeguard; it is not a full compiler qualification. No local compiler/proof/runtime tests, main merge, force push, publication or trust relaxation occurred.

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

