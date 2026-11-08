# PS0 — AI Work State (9 November 2026)

## Current same-frontend census and compiler regression — 9 November 2026

Qualified source **`4d2b7204c0afab86e6f7dfc306b0d53fee6cd15a`**, runner **`189be356819cec9d2d56f3592207ffbe98f3ea6f`**, Linux [run 42515763246](https://github.com/dwijayuda/pskernel/actions/runs/42515763246): **all four jobs PASS**. Exact jobs: project/binder/census **128838311309**, native **128838311805**, proof-linked **128838303330**, host **128838316475**. Official Lean and normative R2 pins are unchanged.

The native `addModuleLinter` callback captures commands from the same frontend execution used for code generation. Census sidecars retain normalized source, original top-level command kinds/head kinds/ranges, imports and local environment names. Fixtures distinguish original declarations, macro-generated declarations and quoted declaration data. Actual recursive Lake module compilations retain matching census and origin sidecars. The corpus join verifies input equality and recovery of every original byte; its **one-module fixture subset** passes and mismatched provenance is rejected. **The full 2,546-module census has not run.** Prelude inputs remain native-compatible, without hidden logical imports or PS grammar support.

Scoped signature priority now exceeds the legacy alias priority. New `function` type/default and `const` type gap negatives reach the intended **PS0V1-CALL-GAP** adapter diagnostic. Executed oracles include **PS0_NATIVE_SOURCE_CENSUS: PASS**, **PS0_PROJECT_SAME_FRONTEND_CENSUS: PASS** and **PS0_NATIVE_SOURCE_CENSUS_JOIN: PASS**.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| Proof-linked | [13631910233](https://github.com/dwijayuda/pskernel/actions/runs/42515763246/artifacts/13631910233) | `31686112db3cd8b940f201c63c9100867f0d16a0a5fc18c1a798954f6ddc7ba0` |
| Project/binder/census | [13631805505](https://github.com/dwijayuda/pskernel/actions/runs/42515763246/artifacts/13631805505) | `85f09423b3d2ea0deb845f3843bdbc5d3d6ff460cbfaaa8a94fa95838937a43a` |
| Native | [13631216761](https://github.com/dwijayuda/pskernel/actions/runs/42515763246/artifacts/13631216761) | `f8f20668e1ed032a1308189fc7dd97a1ea9fb35e0eb404d528a454bd8f836d16` |

The independent full compiler [run 42511359592](https://github.com/dwijayuda/pskernel/actions/runs/42511359592), source **`9826bdd9dc422fe021de953a570972d7b85df2f4`**, runner **`332ed8372583f2c1a2b08ed3aacd182aa3aa95d2`**, finished: stage one **128825446119 PASS**, building/linking **2,565 modules / 5,134 native Lake jobs** and passing source smoke; stage two **128831905726 FAIL**, native exit **139** while recompiling **PS0.Binders.ps**. Fixed-point comparison was not reached. Stage-one [artifact 13630277856](https://github.com/dwijayuda/pskernel/actions/runs/42511359592/artifacts/13630277856) SHA-256 `9cd6ca6db18c631390bcd4f6b762c38c8227f60a21a84d3eee52fac2a2f0ccf2`; failure [artifact 13631615771](https://github.com/dwijayuda/pskernel/actions/runs/42511359592/artifacts/13631615771) SHA-256 `6261b2be9f790dd8fdf07f17bc070fb934119281bf18a0e7ad78d3d5aa33cbb9`.

Focused diagnostic [run 42516632944](https://github.com/dwijayuda/pskernel/actions/runs/42516632944), runner **`e8b085b551a5de8c6c0a2e42b895627bd8be4832`**, job **128840967358**, reproduced the crash in Lean's native parser-constant evaluator. Setting the existing native option `interpreter.prefer_native=false` for that diagnostic alone succeeded, with identical generated C and public olean to the SDK build. Diagnostic [artifact 13631362254](https://github.com/dwijayuda/pskernel/actions/runs/42516632944/artifacts/13631362254) SHA-256 `7afffc436a768af054d2a32b3710307148a4a4d9a46b1db669ce7b4c7f5ca0ae`. This is diagnosis, not compiler qualification.

Candidate source **`a21ecd55fa1b40d66ae5e8ccce64cc04ab5a0c30`** removes the two closed custom Parser constants and uses inline native parser descriptors for ordinary/default tactic alternatives. It is **PENDING Linux qualification** in the regular suite and [focused migrated-rebuild PR #225](https://github.com/dwijayuda/pskernel/pull/225), runner **`b88296fa6219a92fcc4aa8fc0ac7be9fa8c283a5`**. No compiler-wide evaluation setting was changed.

**Goal ACTIVE / NOT COMPLETE.** Required next: resolve/requalify the compiler self-rebuild, run the full actual-source census, provide bootstrap/prelude PS grammar without hidden logical imports/cycles, implement remaining owned operand/signature contexts and checked ProofScript source conversion, then build/link and compare the entire transformed corpus through a fresh migrated compiler. Diagnostic/IDE remapping and full provenance remain open. All broad obligations remain PENDING; `grammarMigrationComplete` and `verified_execution` remain false.


## Current origin-artifact recovery checkpoint — 9 November 2026

Source **`863da731fc5957000d4633d13a9711d8d14ae126`**, runner **`710e9d296ddd344e6f559717c4aee0b0568e3e6c`**, Linux [run 42512184970](https://github.com/dwijayuda/pskernel/actions/runs/42512184970): **completed SUCCESS; all four jobs PASS**. Exact jobs: project **128827500492**, native **128827500249**, proof-linked **128827500080**, host **128827500317**. This newer source retains the binder/signature probes below and adds **PS0_PROJECT_SOURCE_ORIGIN_CACHE_RECOVERY: PASS**.

The adapter composes a native `Job.mapM` continuation after successful `leanArts`, verifies/recreates the exact source-origin JSON and records its content in the native Lake trace. Deleting or corrupting an ilean origin sidecar is repaired to identical bytes on the next warm build, while the executable's SHA-256 and mtime remain unchanged. Native compilation/elaboration, artifact reuse, object code and linking remain Lean/Lake responsibilities.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| Native regression | [13629788351](https://github.com/dwijayuda/pskernel/actions/runs/42512184970/artifacts/13629788351) | `403bca4db145582fa92f08f91f5ea8feb9f82efabe021d2983fc2454e409c107` |
| Project/binder/origin recovery | [13629683793](https://github.com/dwijayuda/pskernel/actions/runs/42512184970/artifacts/13629683793) | `1c60c6b9b98a6cceed3b99e2b3377a6fe36e4799e86f77c460e6c75e9637875d` |
| Proof-linked regression | [13629454560](https://github.com/dwijayuda/pskernel/actions/runs/42512184970/artifacts/13629454560) | `49c8bddc8739c988a0ab4ffa4fd407fcc50c280da9abd4a8daea8fb7fea877b5` |

Test-first source **89af6cc1d3aecf6cfa81f0a8adf59afb430a0e73**, run **42511729740**, job **128826050067**, failed because warm builds did not restore missing maps. Candidate **6d0c3f5c546e2ca15c2b52187d7ad353ad725781**, run **42511971440**, job **128826860303**, exposed a Bool return escaping the native artifact continuation; the passing source preserves the native artifact result.

The full compiler regression run **42511359592** has finished: stage one **128825446119 PASS**, stage two **128831905726 FAIL** with exit **139** in **PS0.Binders**. See the current evidence above; no fixed-point qualification was reached.

**The project goal remains ACTIVE.** Next: collect actual compiler command syntax through Lean's native module-linter API, distinguish original/quoted/DSL/generated forms, implement checked source migration and bootstrap/prelude grammar support without hidden logical imports or cycles, then qualify the entire transformed corpus through native Lake builds, migrated source checks and fixed-point evidence. Diagnostic/IDE remapping and full provenance also remain open. No broad v1 family is promoted; no verified-execution certificate is issued.

## Active goal and qualified binder/default checkpoint — 9 November 2026

**Goal remains ACTIVE:** compile the entire pinned Lean4 compiler corpus as `.ps` using ProofScript syntax and grammars. Renaming native sources, or building only native-compatible bodies, is insufficient. The earlier full native-compatible source-forest milestone is historical evidence, not completion of this stronger requirement.

Qualified source **`9826bdd9dc422fe021de953a570972d7b85df2f4`**, runner **`523c9e600ade3fdd6bba4a6bc203383477389837`**, [source PR #10](https://github.com/dwijayuda/lean4/pull/10), [runner PR #222](https://github.com/dwijayuda/pskernel/pull/222). Linux [run 42511067847](https://github.com/dwijayuda/pskernel/actions/runs/42511067847) is **completed SUCCESS; all four jobs PASS**: binder/project **128824034975**, native **128824034894**, proof-linked **128824034872**, host-contract **128824034957**. The official Lean **eb6cafb7290e8bd5f2937522d8d804f58f02bafc** and normative R2 **c50203f8e4cb79b3e6680088a07c1d1e145b8f0b** pins are unchanged.

`PS0/Binders.lean` lowers ordered mixed telescopes to genuine native binder nodes. It preserves native shared, anonymous and inferred binders, PS comma groups, dependency order, type/default operands, strict/implicit/instance/universe parameters and trailing commas. Equivalent native/single-comma parses coalesce by binder syntax structure; different structures fail before typing. The `function` alias retains its typed-group/adjacency/nullary restrictions. Native `binderTactic` is tried before ordinary PS defaults, preserving **autoParam versus optParam**, inspected in the actual Lean environment.

Mapped signatures now include simple def/abbrev/theorem/example, opaque, axiom and instance forms, native optional instance name/priority and omitted example result types. Function/const aliases retain native modifiers and source operands. Equation, contract, termination, constructor/field/local and remaining signature contexts are still required. The binder fixture checks exact identifier source information and type/default ranges; native `bracketedBinder` DSL operands retain native syntax.

Empty calls preserve the callable head before native optional completion, allow native CoeFun, and reject a remaining required telescope after Unit insertion, including returned functions and explicit `@id()`. The deriving adapter now forwards native identifiers to registered handlers instead of reserving class names globally. The executed oracles are **PS0_BINDERS:3:3:2:3:3:3**, **PS0_SIGNATURE_HEADS:3:3:3**, **PS0_BINDER_OPERANDS: PASS**, plus the existing recursive/category/origin/native/proof-linked regressions.

`mixed_signature_heads.ps` deliberately includes **one unused axiom** to exercise that declaration grammar; it is reported, not approved as a proof assumption. These are finite syntax/native-execution tests, not formal source or execution certificates. All broad v1 families remain PENDING and receipts retain `verified_execution: false`.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| Proof-linked regression | [13629691688](https://github.com/dwijayuda/pskernel/actions/runs/42511067847/artifacts/13629691688) | `28f5a6346c3265732e378d6f2a0a4ebca210d8e4d63ad2e4cadfb398c3f08aad` |
| Native regression | [13629307964](https://github.com/dwijayuda/pskernel/actions/runs/42511067847/artifacts/13629307964) | `79a047113f70d353403457d308c70228b484c908d10bcae5cfc06f5cf756bf54` |
| Binder/project/source origins | [13629118835](https://github.com/dwijayuda/pskernel/actions/runs/42511067847/artifacts/13629118835) | `37843bed9b6446cf4243287990fced81b3997e7acf4d42fbb85ebb070571e191` |

The separate full native-compatible compiler regression run **42511359592** finished with stage one PASS and stage two FAIL in PS0.Binders. It does not establish canonical ProofScript source migration or a fixed point.

Next required work: source-origin sidecar cache recovery/diagnostic integration; a native-parser-driven syntax census and source migration; bootstrap/prelude PS adapters without hidden logical imports or dependency cycles; remaining PS operand/signature roles; then full transformed-corpus Lake build/link, migrated-compiler source checks and fixed-point evidence. No main merge, force push, package publication, pin change or trust relaxation occurred.

Resolved candidate failures and exact identities remain in `v1-coverage.json`. In particular, run **42509432717** job **128819138702** found parser-name ambiguity, run **42509906650** job **128820493639** found legacy deriving token pollution/default-head completion, and run **42510946874** job **128823659857** found the native optional-priority quotation shape. The passing checkpoint retains the intended native diagnostics.

## Previous grammar and source-origin increment — 9 November 2026

Qualified source **`1d76c795edbbaa79fe4d938f073114e5bd76a3ae`**, runner **`cd3d6862abc86d3d4371147cd516f2a1dfd1c9a5`**, draft [source PR #9](https://github.com/dwijayuda/lean4/pull/9) and [runner PR #221](https://github.com/dwijayuda/pskernel/pull/221). Linux [run 42507413045](https://github.com/dwijayuda/pskernel/actions/runs/42507413045) is **completed SUCCESS; all four jobs PASS**: project/grammar/origins **128812930802**, native **128812930996**, proof-linked **128812930942**, host-contract **128812930963**. The official Lean and normative R2 pins below are unchanged. Later documentation-only commits do not change the qualified implementation/test bytes.

Thin PS do adapters now lower a nonempty braced sequence to native `doSeqBracketed`/`doSeqItem` nodes. Identifier let/type/value, mutable let, reassignment, identifier monadic bind, expression statement and return slots lower through `psTerm`; Lean retains state, monad and type semantics. The fixture executes **`PS0_DO_OPERANDS:12:3`** and checks dedicated `apply`/`refine` proof operands. A native `doSeq` DSL preserves tuple application. Do-gap/order negatives reach **PS0V1-CALL-GAP/ORDER**, and a non-Unit intermediate action reaches Lean's actual **IO Nat versus IO Unit** error. The adapter reuses Lean's expression-token exclusion parser to keep `return` out of the generic do-expression alternative.

Header preparation now inserts generated policy/scope/evidence text around the original header and body, retaining every original UTF-8 byte in order. `source-map FILE.ps` exports **ps0-source-map/1**: half-open byte ranges distinguish original/generated spans, `source` retains original CRLF/trivia, and `nativeSource` is Lean's CRLF-normalized input. `source-origin FILE.ps NATIVE_BYTE_OFFSET` maps a native parser position back through Lean's own `FileMap` conversions and returns an original byte offset or JSON null for generated/no-origin positions. Use the same file bytes as the captured map. Native Lake compilation retains **`<module>.ilean.ps0-source-map.json`** sidecars.

Executed evidence: `tests/run-source-fidelity.py` passes implicit/explicit/prelude/empty/EOF-comment byte recovery, Unicode/nested/header/module comments, CRLF normalization lookup, exact CRLF/Unicode native-conversion body preservation, and an **actual native Syntax.getPos?** probe. The five source cases also pass official checking. `tests/run-project.py` validates and retains actual ilean sidecars while recursive build/invalidation/publication/module-boundary regressions pass. `tests/run-categories.py` passes both category fixtures and intended negatives. All build/proof/runtime tests ran on Linux Actions.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| Project/grammar/origin maps | [13628415674](https://github.com/dwijayuda/pskernel/actions/runs/42507413045/artifacts/13628415674) | `990006cc3ad062fb57d930af70cb9bf703c815246c7a1b3c367c443b73e953ba` |
| Proof-linked regression | [13627967800](https://github.com/dwijayuda/pskernel/actions/runs/42507413045/artifacts/13627967800) | `6aea337c3e5c7f7b526be7fe7a431e7e2a854d72deb8f3ea10468ef40d94619b` |
| Native regression | [13627079788](https://github.com/dwijayuda/pskernel/actions/runs/42507413045/artifacts/13627079788) | `958adce04a4da8527811de3c7f91b55c9bbbc0d69798d4a44705e2184086abc9` |

This is finite grammar/origin-map qualification. Diagnostics and ilean references still use native prepared-source positions; automatic diagnostic/IDE presentation, sidecar cache recovery/facet tracking, arbitrary generated-syntax provenance and full source fidelity remain open. Binder/default/mixed signatures, remaining do control/pattern/configuration/native-layout slots, remaining tactic operands, match, collections/interpolation and configuration/attribute roles remain open. The 242 broad obligations are not promoted by these finite tests. Receipts retain `verified_execution: false`.

The complete compiler-source stage-one/stage-two test was **not rerun for this increment**. Its prior exact-source qualification remains recorded separately below. No main merge, force push, publication, pin change or trust relaxation occurred.

Resolved failed candidates remain in `v1-coverage.json`: source `74be717b036c8c01f971b5ba09a4553ba344a8a3`, run **42506026417**, job **128808825962**, exposed the native doElem splice requirement; source `1061a612067c1a9c88dee56eab30891ec68a0be2`, run **42506852635**, job **128811284072**, exposed return competition and normalized/raw CRLF offsets; source `133fcf9a0196597cd6ef62990bbef6483357cd61`, run **42507173849**, job **128812202395**, passed do cases but rejected CRLF headers when normalization was disabled. The passing implementation keeps native normalization and translates positions with native FileMaps.

## Previously qualified pinned compiler-source replacement capability

The earlier extension-replacement milestone is qualified for the exact **Lean 4.35.0 source snapshot**: every one of its **2,546 src/**/*.lean Git blobs** plus **18 PS0 implementation modules** builds from actual `.ps` program inputs through the reused Lean frontend/kernel/LCNF/C backend and native Lake graph/artifact/object/link machinery. A migrated native compiler then rebuilds the same **2,564-module** forest in a fresh Linux job, with **zero generated C differences and zero public olean differences**. This is a generated source-forest capability test, not an upstream/main source cutover, complete PS-specific grammar closure, a C++ runtime rewrite or a formal execution-correspondence proof.

### Exact source, runner and Linux results

- Qualified implementation/test source: **`fb86cc425f0688bf3c6e98ff6c7adb8e899fe883`**, draft [Lean-fork PR #8](https://github.com/dwijayuda/lean4/pull/8), branch `feat/ps0-recursive-projects-20261108`. Later documentation-only commits record these results without changing compiler/test bytes.
- Runner: **`0bca62aefdb00992d891f57c1a608dc0dacd60a3`**, draft [pskernel PR #220](https://github.com/dwijayuda/pskernel/pull/220), branch `ci/ps0-recursive-projects-20261108`. Its immutable selector remains pinned to the qualified source.
- Official semantic pin: **`eb6cafb7290e8bd5f2937522d8d804f58f02bafc`**. Normative R2 reference blob: **`c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`**.
- Linux [run 42488162021](https://github.com/dwijayuda/pskernel/actions/runs/42488162021) is **completed SUCCESS; all six jobs PASS**: project/category **128754567397**, native **128754567736**, proof-linked **128754567672**, host-contract **128754567546**, compiler stage one **128754834515**, compiler stage two **128763580779**.
- Each compiler stage completes **5,132 native Lake jobs**. Stage one builds/links the migrated compiler and passes its pinned environment command and actual PS source check with rebuilt libraries. Stage two downloads that exact executable, verifies its binary identity and all input hashes, rebuilds from scratch, repeats the runtime smoke and asserts every C/public-olean hash matches.
- The compiler input inventory verifies all 2,546 original Git blobs. Across the full 2,564-module forest, **2,541 inputs are byte-identical**; the others retain native bodies with native-parser header adaptation. The forest contains no `.lean` program inputs.
- Migrated stage-one native compiler SHA-256: **`3c7371ca39e9689dd55c1b6fa1fbd3821f10c584a96c81f605e8350380bd339a`**.

### Retained exact artifacts

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| Native executable regression | [13620303005](https://github.com/dwijayuda/pskernel/actions/runs/42488162021/artifacts/13620303005) | `b7e489f9fa186b0fe31a64830a02fdb9ad07dab8eb5b430529001ea1d4c03a99` |
| Recursive/category/driver invalidation | [13619929692](https://github.com/dwijayuda/pskernel/actions/runs/42488162021/artifacts/13619929692) | `d1ea345719129239bf82acf92b543546e513e375d9e4211dfca815577edd759d` |
| Existing bounded proof-linked regression | [13620970053](https://github.com/dwijayuda/pskernel/actions/runs/42488162021/artifacts/13620970053) | `9f0e5517f1f8947ff73a97603855728a6adb630dd1262ef0bc95302151052900` |
| Compiler stage one: binary, inventories, all output hashes, link map, passing smoke | [13622010384](https://github.com/dwijayuda/pskernel/actions/runs/42488162021/artifacts/13622010384) | `de68e47310d1a58631c98072d4c786eede503f282c18830c3d0f13c2f422b23b` |
| Compiler stage two: clean migrated-compiler rebuild and zero-difference result | [13621859608](https://github.com/dwijayuda/pskernel/actions/runs/42488162021/artifacts/13621859608) | `dae31cf63a2098b2cfa67940936424fa16fd361c700d202b54c934ad24eb3827` |

### Native link provenance

Independent Linux [audit 42491501152](https://github.com/dwijayuda/pskernel/actions/runs/42491501152), audit runner **`54a3d0356609a24ec94090adedcc0a1645134f6b`**, job **128764669538 PASS**, checks the exact stage-one artifact. It verifies the executable hash, rebuilt frontend/LCNF-emitter/PS0 objects and native symbols, **zero SDK Lean/Init/Std source-archive entries**, and **zero SDK Lean shared-library dependencies**. The linked archives are C++ runtime/native dependencies, including `libleancpp.a`, `libleanrt.a`, GMP and libuv. ELF dynamic dependencies are libc, the ELF loader, pthread, dl, rt and m. The pinned C++ runtime remains the reused infrastructure.

Audit [artifact 13621487247](https://github.com/dwijayuda/pskernel/actions/runs/42491501152/artifacts/13621487247) ZIP SHA-256: `8c9159eefd30f5204d277c888ea64eb40b5618beacca8a6825515f202637f6b6`. The audit is isolated on `ci/ps0-compiler-audit-20261108`, so it does not repin or restart compiler qualification.

### Implemented and executed behavior

`build-project SOURCE_ROOT Dotted.Module OUT_DIR` composes native Lake input and `leanArts` facets with actual `ModuleSetup`. Native dependencies retain the official Lean process. It executes the recursive/meta-import fixture as **42:7**, then **45:7** after a transitive PS edit, then **45:9** after a native dependency edit. Warm executable hash/mtime reuse, actual compiler-byte invalidation and re-elaboration, no-replacement publication, native prelude/no hidden imports, local compiled main, source collisions, native dependency cycles and private import visibility all pass.

Compiler identity is a shared native Lake input target, rather than a per-module full executable rehash. Changing actual driver bytes changes every PS input trace and re-elaborates real code. Bootstrap builds use native Lake bootstrap package identity and pinned include headers, preserving native extern symbol names. Migrated source checks use the newly built library search path. Binary and per-module hashes are retained before smoke checks, including on later failures.

The mapped category fixture executes **PS0_CATEGORY_SLOTS:3:3:3:3:3**. Ordinary declaration result/value/proof slots, general/chained/closure calls, selected conditional/single-return do/braced exact operands, opaque native tuple DSL/quotation data and order/duplicate/gap negatives pass. `standard-adapter-map.json` records the exact finite map; `v1-coverage.json` retains case-level and compiler-gate evidence.

### Remaining scope

At the compiler checkpoint, binder/default and mixed signatures, multi-statement do, remaining tactic operands, match/collection/interpolation and configuration/attribute roles, extension competition and full source fidelity were open. The current increment above qualifies selected multi-statement do and dedicated apply/refine cases; the remaining roles stay open. Broad v1 capability families remain PENDING; the compiler-source result does not promote all 242 obligations.

The result is Linux x86-64/C-backend qualification against the pinned snapshot. It does not claim every tool's runtime behavior, all target backends/platforms, whole-kernel metatheory, complete language self-hosting or verified execution. Receipts retain `verified_execution: false`; no trust restrictions, proof assumptions or normative language rules were relaxed. No local compiler/proof/runtime tests, main merge, force push or package publication occurred.

## Historical qualification and failed candidates

The following records preserve earlier finite evidence and failures. They are not the current completion status.

### Historical initial recursive/category checkpoint

- Implementation/test source: **`b842b26fa2dffaee6a73f03fb70ca77683ccaf31`**; runner head: **`a2ff849cd861a32e52dbfee94f0283c749f37040`**. The runner selector pins that exact source.
- Linux [run 42483607627](https://github.com/dwijayuda/pskernel/actions/runs/42483607627): recursive/category job **128740672990 PASS**, native job **128740672968 PASS**, proof-linked job **128740672770 PASS**, host-contract **128740672920 PASS**. Compiler-source stage one failed; the overall workflow is not PASS.
- Official Lean 4.35.0 commit **`eb6cafb7290e8bd5f2937522d8d804f58f02bafc`** and normative R2 blob **`c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`** are unchanged.
- Project [artifact 13618347877](https://github.com/dwijayuda/pskernel/actions/runs/42483607627/artifacts/13618347877), ZIP SHA-256 `1676b6c5b5da9d84f24a569bf53877fc424824018337fca8caf814baebc71980`, retains build/category/project logs, exact identities, publication receipt and native source-input selection receipt.
- Native [artifact 13618945967](https://github.com/dwijayuda/pskernel/actions/runs/42483607627/artifacts/13618945967), ZIP SHA-256 `af1386f8c90e7a630cb85b12e101b76fda5b30bf4b120aefac76a44425c721af`, retains the rerun of the single-module qualification.
- Proof-linked [artifact 13619080687](https://github.com/dwijayuda/pskernel/actions/runs/42483607627/artifacts/13619080687), ZIP SHA-256 `9a8e13f6a9126b1739c8f4a71fb5f37ad8dd6953cb54d1404a7d9462e496ceb0`, retains the existing bounded sandbox/comparator/runtime qualification.

Recursive `build-project SOURCE_ROOT Dotted.Module OUT_DIR` now uses native Lake module input and `leanArts` facet adapters. The frontend consumes Lake's actual `ModuleSetup`; native dependencies use the official Lean process. There is no separate dependency graph, artifact format, optimizer or linker. The fixture executes **42:7**, then **45:7** after a transitive PS edit, then **45:9** after a native dependency edit. Warm executable hash and mtime remain unchanged. Native meta imports, no-replacement publication, native prelude with no hidden imports, absent local compiled main, source-kind collision, dependency cycle and private import visibility all pass their explicit oracles. The native `expose` rule is used explicitly for the imported definition needed by a proof.

The mapped category fixture executes **PS0_CATEGORY_SLOTS:3:3:3:3:3** and passes declaration result/value/proof slots, general/chained/closure calls, selected conditional/single-return do/braced exact operands, opaque native tuple DSL/quotation data and order/duplicate/gap negatives. `standard-adapter-map.json` records the pinned map and exact evidence. Remaining binder/default, mixed declaration, multi-statement do, tactic, match, collection/interpolation and configuration/attribute roles remain open. Registrations alone are not conformance; apply/refine do not yet have dedicated executed probes. Broad ledger families remain pending.

### Earlier compiler-source gate failures

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

