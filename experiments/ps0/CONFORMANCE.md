# PS0 v1 — Implementation and Conformance Ledger

## Complete native compiler census: stage one PASS, stage two running

Pinned source **`abf3585d99c921fe02697b679867a0a55e433168`**, runner **`e78cd4479ba5b1433e8879c14de79ba27427dfdc`**, [run 42517718338](https://github.com/dwijayuda/pskernel/actions/runs/42517718338): stage one **128844671227 PASS**. All **2,566 modules** (**2,546 pinned compiler + 20 PS0**) build/link through **5,136 native Lake jobs**. Source smoke passes. Every module passes the actual-frontend/original-byte census join. There are **72,790 selected source declaration rows, all native-compatible; zero mapped-PS rows** at this checkpoint. This establishes the native-compatible baseline and full census, **not** the required canonical PS source migration.

[Stage-one artifact 13632838932](https://github.com/dwijayuda/pskernel/actions/runs/42517718338/artifacts/13632838932), ZIP SHA-256 **`2395167f3782944cf4291efe55a10d1185f9eec6244493e0df985132e30e7308`**, retains the exact migrated executable, full source-command snapshots and joined hash summary. Stage two **128852603767** is **IN PROGRESS** using that exact executable. A fresh fixed-point result is not yet available.


## Finite prelude PS grammar step PASS; real compiler head parity pending

Source **`eb71f33b2fa0ff2e53bdd7dd9e73b96f63b593d1`**, runner **`dc03ae543bc2bc050a6c62034aee2cb4bc80a56b`**, [run 42520414613](https://github.com/dwijayuda/pskernel/actions/runs/42520414613), project job **128852573466**: **PS0_PRELUDE_GRAMMAR:42:3** and **PS0_PRELUDE_GRAMMAR_NO_HIDDEN_IMPORTS: PASS**. Native Lake builds/links/runs the actual PS prelude source, preserves exact raw bytes and direct imports, retains native quotation AST ownership and contextual identifiers, and accepts owned ASCII strict binders. It also compiles under native bootstrap/stage options. Exact project artifact digest is retained below and in the JSON ledgers.

**The overall project job FAILS later in a separate real-compiler-head probe.** The three-head edit plan is produced from captured native signature AST/ranges, but its native baseline could not find SDK sibling modules because its target `Lean` prefix shadowed the SDK root; its root-module setting also selected that module as an executable entry. No C/public-olean comparison was reached. Native/proof-linked/host jobs PASS; this is **not an all-four-jobs PASS checkpoint**.

[Project artifact 13633535255](https://github.com/dwijayuda/pskernel/actions/runs/42520414613/artifacts/13633535255), ZIP SHA-256 `8a10e7724b03e031fcb2063db4066814c34a0899e3f49cfedc48a323fffc3b7f`.

Candidate source **`263eb3f8693e0b2f9f57ea0418e1babdfce192f7`**, runner **`087035c38c30ad1a959d6279abdefe4bfe2536cc`**, corrects only that finite probe's native SDK metadata layout and entry-module selection; Linux qualification is pending. Dependency metadata stays pinned SDK data, while target artifacts are built fresh by native Lake. Compiler-head conversion remains limited to three typed heads; native bodies are retained. Goal remains ACTIVE / NOT COMPLETE.


## Earlier prelude source grammar candidate — superseded by the finite step evidence above

[Source PR #12](https://github.com/dwijayuda/lean4/pull/12), source **`eb71f33b2fa0ff2e53bdd7dd9e73b96f63b593d1`**; [runner PR #227](https://github.com/dwijayuda/pskernel/pull/227), runner **`dc03ae543bc2bc050a6c62034aee2cb4bc80a56b`**; Linux [run 42520414613](https://github.com/dwijayuda/pskernel/actions/runs/42520414613) is **IN PROGRESS**.

The candidate uses Lean's native parser categories, parser descriptors, builtin macro/term-elaborator registrations and root category dispatch. `-KsourceGrammar=true` reaches the frontend through native Lake setup options. A separate compiler-host environment loads syntax metadata beside the compiler executable and restores target module lookup before compilation. No target prelude source or logical import is inserted. Only the selected PS productions are registered; the root dispatch consumes its flag in a fresh native parser context/cache so native command/term/binder quotations retain their category ownership.

The finite test requires PS function/default/const declarations, a contextual `function` identifier, native strict binders, native quotation AST identity, exact source bytes/direct imports and **PS0_PRELUDE_GRAMMAR:42:3** from a Lake-linked executable. It first requires native-only prelude compilation to reject the PS command. The test-first run **42518050363** was superseded/cancelled and is **not red test evidence**. Actual failed candidates are retained in both JSON ledgers: namespace/token API errors, native persistent-map API mismatch, then missing compiler-host metadata under target-only module lookup.

The candidate also tests Lean's pinned `Lean.Compiler.ClosedTermCache` source (blob **20b7acf5d684789ab52b81dda7def4b19568213c**). A finite planner uses native signature AST/ranges to change three typed declaration heads to PS function/comma syntax, preserving native bodies and all unedited bytes. The test requires native-only rejection, actual PS grammar compilation, original direct imports and identical generated C/public olean. **This is pending; bodies are not canonicalized and no whole-module grammar closure is claimed.** Compiler-host stage options and lifetime, native strict-bracket parsers, fresh target initializer execution and native fallback AST/macro-scope preservation are included in the candidate. All failed-source/runner/job/artifact digests are retained in the JSON ledgers.

**Not yet qualified.** Full canonical source conversion, remaining nested PS operands/signatures, host metadata packaging for relocated migrated compilers and full fresh compiler closure remain open. Independent full compiler/census run **42517718338** continues at the earlier stage-option checkpoint. Goal remains **ACTIVE / NOT COMPLETE**.


## Native Lake compiler-stage evaluation recovery — 9 November 2026

Source **`abf3585d99c921fe02697b679867a0a55e433168`**, runner **`f5eea9af18a6c6a04ee92ef47ce36311f2d95e15`**, Linux [run 42517518674](https://github.com/dwijayuda/pskernel/actions/runs/42517518674): **all four jobs PASS** — project/binder/census **128843676094**, native **128843675964**, proof-linked **128843675694**, host **128843675945**.

Native Lake bootstrap builds now receive **`interpreter.prefer_native=false` through `leanOptions`**, matching [pinned Lean CMake stage builds](https://github.com/dwijayuda/lean4/blob/eb6cafb7290e8bd5f2937522d8d804f58f02bafc/src/CMakeLists.txt). This makes compile-time evaluation use the current IR while rebuilding declarations already linked in the running compiler. The original binder parsers are retained. Normal project options retain their existing defaults.

Focused [run 42517552265](https://github.com/dwijayuda/pskernel/actions/runs/42517552265), runner **`f5fb141be25251c6b8d55f21ac342df7d02218c5`**, job **128843778154**, verifies the actual native Lake setup option and successfully rebuilds `PS0.Binders` with the exact prior stage-one migrated executable. C and public olean hashes match the SDK-driver build. Oracles **PS0_BINDER_STAGE_OPTIONS_AND_OUTPUTS: PASS** and **PS0_BINDER_SELF_REBUILD: PASS**. Focused [artifact 13632032709](https://github.com/dwijayuda/pskernel/actions/runs/42517552265/artifacts/13632032709) SHA-256 `b7bcc738cddc05afe2c2345e6e15a7bbaf992289ce881f881d02def1b25ab84a`.

| Evidence | Artifact | ZIP SHA-256 |
|---|---|---|
| external | [13631689156](https://github.com/dwijayuda/pskernel/actions/runs/42517518674/artifacts/13631689156) | `2ae2a4b513c506da1f014740e31724bd4123d487948e2635f810fc7659d987a8` |
| project | [13631639193](https://github.com/dwijayuda/pskernel/actions/runs/42517518674/artifacts/13631639193) | `1bdb60aa39e7acc3fee61e597493227acd43ac021553c583e153cc9b7b6de461` |
| native | [13631368600](https://github.com/dwijayuda/pskernel/actions/runs/42517518674/artifacts/13631368600) | `58341095eb56d6ec63ab964d73ad1125098b5040ee3a30e009564e5cbc11dc59` |

The inline-descriptor candidate `a21ecd55fa1b40d66ae5e8ccce64cc04ab5a0c30` was **reverted** after regular run **42517158082** / job **128842586950** rejected changed suffix AST shapes and focused run **42517187718** / job **128842672919** exposed old linked descriptors referencing removed `binderSuffix`. The final change reuses upstream infrastructure rather than changing binder syntax.

Independent [full compiler/census run 42517718338](https://github.com/dwijayuda/pskernel/actions/runs/42517718338), [runner PR #226](https://github.com/dwijayuda/pskernel/pull/226), runner **`e78cd4479ba5b1433e8879c14de79ba27427dfdc`**, is **IN PROGRESS** at this source. It requires both fresh complete compiler stages, all generated C/public olean comparisons, and actual-source census joins. This is still a native-compatible forest regression; canonical ProofScript source grammar migration remains **ACTIVE / NOT COMPLETE**.


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

The inline-descriptor candidate was subsequently reverted; see the stage-evaluation recovery evidence above.

**Goal ACTIVE / NOT COMPLETE.** Required next: resolve/requalify the compiler self-rebuild, run the full actual-source census, provide bootstrap/prelude PS grammar without hidden logical imports/cycles, implement remaining owned operand/signature contexts and checked ProofScript source conversion, then build/link and compare the entire transformed corpus through a fresh migrated compiler. Diagnostic/IDE remapping and full provenance remain open. All broad obligations remain PENDING; `grammarMigrationComplete` and `verified_execution` remain false.


**Sole normative reference:** [PS0_V1_LANGUAGE_REFERENCE.md](PS0_V1_LANGUAGE_REFERENCE.md), edition R2, 2026-10-16. Uploaded Git blob `c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`.
**Lean:** official 4.35.0, `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.

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

## Historical complete compiler-source checkpoint

**Status at that checkpoint:** exact source `fb86cc425f0688bf3c6e98ff6c7adb8e899fe883`, runner
`0bca62aefdb00992d891f57c1a608dc0dacd60a3`, Linux
[run 42488162021](https://github.com/dwijayuda/pskernel/actions/runs/42488162021):
recursive/category `128754567397`, native `128754567736`, proof-linked
`128754567672`, host `128754567546` and compiler stage one `128754834515` PASS.
Stage two `128763580779` PASS: a fresh migrated-compiler build matches every C/public-olean hash across all 2,564 modules. All six workflow jobs passed.
Full v1 grammar closure remains open.

Both compiler stages compiled **all 2,546 pinned compiler-source Git blobs plus 18 PS0 modules**
from actual PS program inputs, completed **5,132 native Lake jobs**, audited every
generated C/olean and linked/ran a migrated compiler including an actual PS source check.
Its [artifact 13622010384](https://github.com/dwijayuda/pskernel/actions/runs/42488162021/artifacts/13622010384)
has ZIP SHA-256 `de68e47310d1a58631c98072d4c786eede503f282c18830c3d0f13c2f422b23b`;
it retains the binary, all per-module input/output hashes and native link map.
Stage-two artifact `13621859608` has ZIP SHA-256
`dae31cf63a2098b2cfa67940936424fa16fd361c700d202b54c934ad24eb3827`.
Its result records zero C differences and zero public olean differences. Both stages
pass the migrated environment/source smoke checks. This tests a generated source
forest, not an upstream/main source cutover.

Independent Linux [link/ELF audit 42491501152](https://github.com/dwijayuda/pskernel/actions/runs/42491501152),
runner `54a3d0356609a24ec94090adedcc0a1645134f6b`, job `128764669538` PASS:
rebuilt frontend, LCNF emitter and PS0 objects/native symbols; zero SDK Lean/Init/Std
source-archive entries; zero SDK Lean shared-library dependencies. Migrated executable
SHA-256 `3c7371ca39e9689dd55c1b6fa1fbd3821f10c584a96c81f605e8350380bd339a`.
The pinned C++ runtime remains reused infrastructure.
Audit artifact `13621487247` has ZIP SHA-256
`8c9159eefd30f5204d277c888ea64eb40b5618beacca8a6825515f202637f6b6`.

Project artifact `13619929692` has ZIP SHA-256
`d1ea345719129239bf82acf92b543546e513e375d9e4211dfca815577edd759d`.
Executed fixtures cover recursive/meta imports, native dependencies/runtime, warm reuse,
source/native/driver invalidation, publication, prelude isolation, local entry,
source collisions, cycles and private visibility. Mapped category cases retain
native tuple DSL/quotation ownership and reject order/duplicate/gap errors.
These finite cases do not qualify all host operand roles. Older failures and
their exact evidence remain in AI_WORK_STATE.md and v1-coverage.json.

## Current exact-evidence policy

`v1-coverage.json` records the exact source, Lean/reference identity, fixture,
diagnostic/semantic oracle and CI run for each qualified finite case. A PASS
at an earlier source is historical evidence; changed implementations require
fresh exact-source qualification. Broad capability families remain PENDING
when only a subset has executable evidence.

The current category adapter registry is `standard-adapter-map.json`. The
recursive project fixtures are under `tests/project/`; `tests/run-project.py`
checks imported ps syntax, mixed native imports, source-kind ambiguity,
cycles, visibility and transitive invalidation. `tests/run-categories.py`
checks the selected mapped operands and native quotation/DSL ownership.

`tests/run-compiler-ps.py` is the compiler-source migration gate. It inventories
all 2,546 pinned `src/**/*.lean` Git blobs plus PS0 modules, compiles a program source tree with no
lean files, builds a migrated compiler executable and, in a second clean
job, requests full C/olean fixed-point comparison. Conversion, native source
admission, C/object compilation, executable behavior and a full compiler
fixed point are distinct outcomes. The two stages now PASS only at the recorded source/scope. Native-prelude coverage does not qualify all PS-owned bootstrap sugar.

## Implemented migration changes

| Layer | Current code | Remaining gap |
|---|---|---|
| Canonical document | Complete 4,163-line standalone v1 reference in PS0 | No normative predecessor fallback |
| Syntax adapters | Existing `function`/`const`, comma binders/calls, selected braced forms and Lean-native elaboration | All `psTerm`/`psCommand`/`psTactic`/`psDoSeq` ownership and `PS0.Syntax.lower` (`0B/`9) |
| Grammar | Removed frozen command/attribute/tactic/loop/source-token denial list; diagnostic-only syntax-kind inventory | Full interleaved host grammar and category-aware adaptation |
| Declaration policy | No mandatory v7 axioms/unsafe/partial/IO ban; `#ps0_evidence` is informational | Transitive claim-specific assumptions and evidence `12` |
| Imports/Standard | Native registered/imported extensions determine availability; no v7 finite Standard allowlist | Complete effective module/stage/extension identity and `prelude` isolation |
| Modules | Native Lake recursive PS/public/meta module graph, mixed native imports, invalidation, collision/cycle/private/local-entry negatives passed at the checkpoint | Broader package/options/plugin/bootstrap qualification and full grammar/source fidelity |
| `.lean` | Official Lean process unchanged and unrestricted | Routine exact-commit CI qualification |
| JS backend | Lean typed Nat-only IR, ESM/`.d.ts`/Source Map v3 | Validated build, more types, modules, runtime semantics proof |

**Important:** A v1 feature may be *admitted by the normative
language* but remain *not yet implemented by PS0*. Neither sentence
means it is guaranteed to compile in the current branch.

## New evidence baseline

[v1-coverage.json](v1-coverage.json) records **242** items:
100 capability families, 64 positive source cases, 47 negative
source/disallowed-claim cases, and 31 R2 boundary witnesses.
Every item initially has `PENDING` status. It is not a numeric
implementation-completion percentage.

`PASS` requires real evidence at the exact source, Lean,
compiler and imported environment identity. A static syntax-kind
count or availability via unchanged `.lean` does not qualify PS
source capability. The old PSCV0 v7 registry is not imported
and does not supply a fallback test outcome.

## Distinct validation outcomes

1. **Development:** native editor/elaboration may retain errors or
   `sorry`; not completed proof.
2. **Ordinary checked source:** complete relevant checking, with
   declared assumptions/runtime interfaces classified.
3. **Checked theorem:** precise elaborated proposition and actual
   kernel evidence, conditional on transitive assumptions.
4. **Source-verified:** named policy/spec, evidence for required
   coverage/effects/erasure/termination and assumption closure.
5. **Execution-correspondence-verified:** additional checked
   correspondence to a specified generated artifact/layer.

`#ps0_evidence` does not issue any verified label. A stronger
verified-output policy may refuse an otherwise valid ordinary
unsafe, partial, effectful or axiomatic program; that refusal
must not redefine the PS0 v1 source language.

## High-priority conformance probes

- Native `axiom`, unsafe/partial/`noncomputable`, bodyless
  `opaque` and development `sorry` (native classification).
- Macros, syntax categories, custom elaborators, dynamic
  attribute/deriving registrations, and quotations whose native
  category data must not be globally PS-rewritten.
- Explicit and implicit modern modules, `prelude`, public/meta/all
  import flags and hidden vs exposed public bodies.
- Native value-form instances, imported priority handlers,
  structural and nonstructural recursion, monadic `if let ←`,
  zipped loops, native tactics and semicolon control.
- ProofScript comma-call/tuple/nullary and binder-specific
  source ownership, matching and braced syntax (``0B–5).
- Source/claim boundary tests and the R2 witnesses, including
  per-phase diagnostic or AST semantics checks.

## Backend acceptance (separate from v1 language)

The Nat-only JS backend emits `.js`, `.d.ts` and `.js.map`
from a deliberately closed runtime IR. It is **not** a full
v1 language implementation and does not issue a verified JS
certificate. CI must demonstrate exact Nat arithmetic, type
signatures, source-map positions, deterministic emission,
refusal of unsupported constructs and runtime semantics.

See [PS0_V1_IMPLEMENTATION_PLAN.md](PS0_V1_IMPLEMENTATION_PLAN.md)
for remaining architecture gates and [AI_WORK_STATE.md](AI_WORK_STATE.md)
for the latest development handoff.


## Historical adapter milestones

The dated entries below preserve the earlier candidate scope. Their pending
wording is historical; current qualification, generalized mapped operands and
compiler-source fixed-point results are recorded above and in the exact JSON ledgers.

### PS0 v1 host psTerm postfix-call extension — 16 October 2026

Implemented a first PS-owned, **nonempty identifier-head** adjacent-call
source production in `PS0/HostCategories.lean`. It uses Lean's
`noWs` lexical/position-sensitive parser to distinguish a PS postfix
from a spaced native application. The separate `psCallArg` category
captures positional and named host operands.

The explicit `PS0.Syntax.lower` bridge lowers this source category
recursively to a native `Lean.Parser.Term.app` node, preserving the
argument tree. Named parameters use the genuine
`Lean.Parser.Term.namedArgument` category and reject duplicate names
or positional arguments after named parameters. No source-string
transpilation, name resolution or typechecker fork was added.
Native subtrees remain unmodified and other native, quotation and
DSL categories retain their own syntax ownership.

**Bounded scope:** identifier-head calls with nonempty argument lists
in **explicit host-category extension operands**. Full standard
declaration/tactic/do `psTerm` operand wiring, generalized callable
postfix heads, source-nullary completion, optional trailing commas,
parser ambiguity reconciliation and source-provenance verification
remain pending. Existing native term macros may support some source
forms but do not qualify the v1 host-category contract by themselves.

Candidate tests: `tests/v1/host_postfix_calls.ps` exercises
two-argument, nested, tuple-preserving and named calls, and an
extension verifying it receives the raw host-call syntax before
lowering. Separate negative fixtures assert the expected
`PS0V1-CALL-ORDER` and `PS0V1-CALL-NAMED` diagnostic categories.
Five relevant `v1-coverage.json` cases have new candidate links;
all remain `PENDING` until actually qualified by pinned Lean CI.

The canonical normative PS0 v1 R2 document remains unchanged.


### Standard declaration-body psTerm integration — 16 October 2026

PS0 now provides owned source-command forms for **typed** `function` and
`const` bodies whose RHS category is `psTerm` rather than silently taking a
native `term` operand. These forms have higher source-parser priority than
the older partial native-term-backed alias forms. They call the shared
`PS0.Syntax.lower` bridge, constructing real native Lean declarations with
the existing source binder/Unit sugar and ordinary Lean elaboration.

`tests/v1/standard_host_declarations.ps` exercises composed and nested
adjacent calls, reordered named arguments, trailing commas, a
partially applied function, and const initializers. Negative fixtures
`standard_host_order_negative.ps` and
`standard_host_duplicate_negative.ps` demand their specific
`PS0V1-CALL-ORDER`/`PS0V1-CALL-NAMED` rejections; a separate comma-only
fixture must not pass. These tests are **not** current CI PASS receipts.

The Lean-native Nat-only JS backend now recognizes the same new
`psTerm` body nodes, lowering only prior, exact-arity, monomorphic Nat
function calls and constant references into its closed typed IR.
`tests/js/nat_mvp.ps` includes calls with trailing commas in typed
`function` and `const` source forms, with a Node/TypeScript check in CI.
Broader JS semantics or proof-of-runtime-preservation are not claimed.

**Unfinished:** inferred-result declarations, dependent type/binder
slots, standard native `def` and `theorem` RHS, native tactic/do/contract
operands, complete high-postfix call heads, empty-call type-directed
completion inside `psTerm`, ambiguous parse coalescence, expression
source-provenance proof, and imported extension/DSL boundaries.
Only these two typed declaration aliases have migrated standard
body operands. Native `.lean` is unaffected.

The v1 coverage ledger has seven additional **standard-operand
candidate fixture links** on existing call-case IDs, not seven new
requirements or qualifying PASS records. All 242 entries remain
unqualified until an exact-commit Lean 4.35.0 CI result is examined.


### Inferred-result and private source alias parity

The same explicit `psTerm` standard-body adapter now covers
`function` and `const` with either a declared result type or Lean-inferred
result, plus typed/inferred `private function` and `private const`.
Inferred declarations reuse the official Lean elaborator, while source
`function f()` retains the synthetic required `Unit` binder; ordinary
native `def` and `.lean` remain unchanged.

`tests/v1/standard_host_declarations.ps` includes Lean `rfl`
oracles for the public/private and inferred variants, typed
host-call composition, and the source-nullary Unit conversion.
The existing Nat-only JS backend continues to accept the checked
typed/public subset and explicitly rejects inferred/private exports
until its IR/export contract is widened. This split is backend
capability, not a PS0 v1 language restriction.

**Implementation code and test fixtures are committed but still
unqualified:** no actual Lean 4.35.0 build or test run has been observed
for the branch. No v1 requirement was promoted to PASS.

