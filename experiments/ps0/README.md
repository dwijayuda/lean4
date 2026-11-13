# PS0 — Lean 4.35-backed ProofScript v1

**Edition:** PS0 v1 R2 (2026-10-16). **Implementation:** in progress;
not a completed v1 compiler or a verified executable compiler.


## Canonical compiler source

The pinned compiler source is tracked as `.ps` in `src/` and in the PS0
implementation directory. The canonical catalog preserves the correspondence
between upstream paths, Lake module names, and the audited ProofScript bytes.

On Linux x86-64 with the pinned Lean 4.35.0 SDK, download the [audited bootstrap bundle](https://github.com/dwijayuda/pskernel/releases/tag/ps0-bootstrap-lean4.35.0-978d594a-linux-x86_64).
The download script verifies the published `SHA256SUMS` against the digest
pinned in the checkout and checks the archive before extracting it. Use a new
output directory for the download.

```bash
cd experiments/ps0
test "$(lean --githash)" = eb6cafb7290e8bd5f2937522d8d804f58f02bafc
bootstrap="$(pwd)/build/release-bootstrap"
mkdir -p build
bash tests/fetch-canonical-bootstrap.sh "$bootstrap"
export PS0_SOURCE_SHA="$(git rev-parse HEAD)"
python3 tests/run-compiler-ps.py --canonical-corpus \
  --bootstrap-artifact "$bootstrap/compiler-evidence" \
  --bootstrap-source 978d594a10fac8f6e5687190a22d70334b331dab
```

The build verifies the retained seed prefix and stages the checked-out PS
bytes under Lake's logical module paths. Native Lake builds the archive and
executable. The Linux two-stage workflow uses a fresh checkout for the second
stage and supplies the first linked PS-built prefix through `--stage-artifact`
and `--stage-source`.

## Compiler-source grammar mode

Native Lake project builds may opt into the finite syntax-only compiler host with
`-KsourceGrammar=true` in addition to their existing `lakefile.project.lean` source,
root and module configurations. Selected PS function/const/signature operands then
work in a `prelude` module without inserting logical PS0 imports or changing its
source bytes. The host loads its own sibling compiler metadata and pinned SDK
separately from target module lookup. Keep that metadata beside the native driver.

This is partial grammar support. The qualified finite tests include native
quotation ownership, contextual alias words, strict/default binders, modern
runtime hook startup and three typed heads from the pinned real compiler module
`Lean.Compiler.ClosedTermCache`, with matching native C/public olean.
Its native bodies remain unchanged. See [AI_WORK_STATE.md](AI_WORK_STATE.md),
[CONFORMANCE.md](CONFORMANCE.md) and both JSON ledgers for exact Linux source,
runner, job and artifact digests, failed candidates and remaining gates.

Compiler bootstrap builds use native Lake `leanOptions` with
`interpreter.prefer_native=false`, as in the pinned upstream Lean CMake stage
configuration. Native frontend/kernel/code generation, graph/artifact/cache,
native object compilation and linking remain Lean/Lake responsibilities.
The generated compiler corpus and its fixed point were qualified before the
source cutover. The work state and conformance ledger record the corresponding
generated and canonical build evidence.

## Sole normative authority

**[PS0_V1_LANGUAGE_REFERENCE.md](PS0_V1_LANGUAGE_REFERENCE.md)** is the
complete, standalone PS0 v1 language specification. Its exact uploaded
Git blob is `c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`.
PSCV0 v7 is superseded and is **not** a fallback or a backward
compatibility target. Native semantics and registration behavior are
pinned to official Lean 4.35.0,
`eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.

PS0 adds application-oriented source forms to Lean. These include
`function`, `const`, adjacent comma calls, comma binder groups,
braced proofs/control, and v1 source-module defaults.
The native Lean programming, tactics, metaprogramming, attributes,
instance bodies, effects, partial and unsafe programs, axioms and
extension facilities are part of the language **where their real
import/stage/type requirements are satisfied**. Their presence is not
automatically evidence of a verified executable.

`.ps` follows PS0 v1, `.lean` remains full unmodified Lean.
The existing PS0 project remains separate from the independent PSC0
multibackend compiler and from the earlier PSCVL experiment.

## Build and development commands

Native executable build (run from this package directory):

```sh
lake exe ps0 build-native tests/native/Main.ps NativeMain build/native-main
./build/native-main/NativeMain one two
```

For incremental development, use the underlying Lake target directly:

```sh
lake -R -f lakefile.native.lean -Ksource=tests/native/Main.ps -Kps0Module=NativeMain build app
./.lake/build/bin/NativeMain
```

The target composes the existing `.ps` adapters and official Lean frontend/LCNF C emitter with Lake's imported-module link information, C-to-object build and executable linker. Lake tracks source bytes, the PS0 compiler, imported Lean modules, native options and the toolchain. Use `-R` so the configuration's `get_config?` values reflect the supplied source/module; compiled artifacts still use Lake's incremental cache. The CLI supplies this flag and publishes an executable and `native-build.json` only after successful linking, refusing an existing output directory. No intermediate textual `.lean` program is generated.

Recursive projects use the native Lake module graph:

```sh
lake exe ps0 build-project tests/project Demo.Main build/project-demo
./build/project-demo/ps0project one two
```

The source root supplies dotted-module paths such as `Demo/Library.ps`. Native `.lean` dependencies, public/meta imports, imported syntax, incremental traces, C/object generation and linking retain Lake's existing implementations. A sibling `.lean` and `.ps` for the same module is an error. Executable entries require their own compiled `main`; publication refuses an existing directory. The output contains `ps0project` and `project-build.json`, whose `verified_execution` remains false.

`lakefile.project.lean` exposes the input/`leanArts` adapters for direct incremental use. The CLI supplies `-R` and source/root/driver configuration. Native `prelude` sources retain their explicit imports and receive no hidden Init or PS0 import. Compiler bootstrap qualification additionally uses Lake's native bootstrap package identity and pinned include headers.

This is native build integration, not complete PS0 conformance or verified runtime execution. Recursive/meta imports, source/native invalidation, cache reuse, prelude isolation, collisions, cycles, visibility and local-entry negatives have finite Linux evidence in `AI_WORK_STATE.md`. Full host operand closure and source-origin fidelity remain open.

`cd experiments/ps0`

`lake build PS0 ps0`

`lake exe ps0 check tests/v1/native_capabilities.ps`

`lake exe ps0 check tests/v1/registered_syntax.ps`

`lake exe ps0 module-header tests/v1/explicit_module.ps`

`lake exe ps0 check tests/lean/unrestricted.lean`

`lake exe ps0 lean [native Lean args]`

The `module-header` subcommand is an introspection aid. `lake-header` emits the native module-header JSON used by Lake's input adapter. `convert-native SOURCE.lean TARGET.ps` and `convert-native-tree SOURCE_DIR TARGET_DIR` retain native bodies and adapt legacy headers with the native header parser. These conversion commands alone do not qualify source replacement. `tests/run-compiler-ps.py` and `compiler-source-inventory.json` require every pinned source blob, actual PS inputs and artifacts, a migrated executable and a second clean C/olean comparison. The pinned compiler-source gate now passes both stages: all 2,546 compiler source files plus 18 PS0 modules compile from PS inputs, and the migrated native compiler rebuilds every module with identical C/public-olean hashes. This remains distinct from complete PS-specific grammar conformance or formal execution verification.

### Small JS backend, entirely in Lean

`lake exe ps0 build-js tests/js/nat_mvp.ps NatMvp build/js-nat`

The selected Nat runtime subset is implemented under
`PS0/Backend/Js/*.lean`. Its candidate outputs are `NatMvp.js`,
`NatMvp.d.ts`, and `NatMvp.js.map` (Source Map v3). It uses exact
BigInt Nat operations and guarded argument boundaries; it refuses
unimplemented runtime constructs. This backend does **not** limit
ordinary valid PS0 v1 source and is not an execution-correctness proof.
See [PS0_JS_BACKEND_MVP.md](PS0_JS_BACKEND_MVP.md).

## Architecture

| Lean implementation | Responsibility |
|---|---|
| `PS0/HostCategories.lean` | Four PS host interfaces, selected owned calls/grouping/control/proof operands and AST lowering; native/DSL subtrees stay opaque |
| `PS0/Syntax.lean` | Typed/inferred public/private `function` and `const` bodies now lower through PS-owned `psTerm`; full native declaration/proof/tactic/do operand adaptation pending |
| `PS0/StandardAdapters.lean` | Scoped ordinary declaration result/value/proof operands; pinned partial map in `standard-adapter-map.json` |
| `PS0/LakeFrontend.lean` | Native header parsing, ModuleSetup/frontend/C protocol, bootstrap source conversion |
| `lakefile.project.lean` | Thin module input/compiler invocation adapters over native Lake graph/artifacts/objects/linking |
| `PS0/Grammar.lean` | Non-normative static syntax-kind inspection; official interleaved Lean parser is authoritative |
| `PS0/Policy.lean` | Local declaration **information only**, no implicit axiom approval or source-language bans |
| `PS0/StandardEnv.lean` | Pinned edition/source metadata, not an import/tactic/attribute allowlist |
| `PS0/Effect.lean` | Candidate Lean-native proof/effect library helpers |
| `PS0/Backend/Js/*.lean` | Typed runtime IR and Lean-based JS/TS/map backend |
| `PS0Main.lean` | CLI, source-profile routing, Lean elaboration and artifact staging |

Language acceptance, ordinary checked source, checked theorems,
source verification and verified execution correspondence are separate
evidence outcomes (`0A and `12). `#ps0_evidence` is informational and
issues no certification. PS0 v1 does not supply a hidden global
axiom-approval policy.

## Actual progress and acceptance

[PS0_V1_IMPLEMENTATION_PLAN.md](PS0_V1_IMPLEMENTATION_PLAN.md) defines
the architectural critical path. [v1-coverage.json](v1-coverage.json)
tracks **242 v1 obligations**: 100 source-capability families,
64 positive cases, 47 negative cases and 31 detailed boundary
witnesses. All start `PENDING`, not `PASS`.

The old PSCV0 v7 readiness score of 41% and v7's 181-case ledger
are obsolete; **do not use either number for v1**.
See [CONFORMANCE.md](CONFORMANCE.md) for implemented-vs-qualified
status and [AI_WORK_STATE.md](AI_WORK_STATE.md) for development state.

The prior bounded proof-linked and host-contract baseline at source
`39b8f4cecd8e60b2297c1d01f81d8840c3dc3715` passed external Linux
run [40772012597](https://github.com/dwijayuda/pskernel/actions/runs/40772012597).
The native continuation at `07a1da68aacf2462e9723a79242c322a21ca3c83`
passed all three jobs in Linux [run 42474108191](https://github.com/dwijayuda/pskernel/actions/runs/42474108191): native build/link/runtime, proof-linked regression and host-contract checks.
This does not qualify all 242 language obligations or verified runtime execution.
The recursive continuation at `b842b26fa2dffaee6a73f03fb70ca77683ccaf31` passed recursive/category, native, proof-linked and host-contract jobs in Linux [run 42483607627](https://github.com/dwijayuda/pskernel/actions/runs/42483607627). The exact continuation at `fb86cc425f0688bf3c6e98ff6c7adb8e899fe883` passed all six jobs in [run 42488162021](https://github.com/dwijayuda/pskernel/actions/runs/42488162021), including both complete compiler-source stages and zero C/public-olean differences. A separate native link/ELF audit passed at the same source. Earlier failures remain historical evidence. See `AI_WORK_STATE.md` for exact identities, artifacts and limits.

## PS operand and source-origin continuation

The finite grammar/origin increment at `1d76c795edbbaa79fe4d938f073114e5bd76a3ae` passes all four jobs in Linux [run 42507413045](https://github.com/dwijayuda/pskernel/actions/runs/42507413045). It adds native-lowered braced multi-statement do operands (identifier let/mut/bind/reassignment, statement and return), dedicated apply/refine probes and opaque native doSeq DSL coverage. Native Lean and Lake still perform elaboration, code generation, native build and linking.

`lake exe ps0 source-map FILE.ps` exports the exact prepared source, native CRLF-normalized input and half-open UTF-8 original/generated byte ranges. Header/body bytes and comments remain recoverable. `lake exe ps0 source-origin FILE.ps NATIVE_BYTE_OFFSET` uses native FileMaps to return an original byte offset or null; the file must match the captured bytes. Actual Lake invocations retain `*.ilean.ps0-source-map.json` sidecars. Diagnostics and ilean references retain native prepared-source positions; automatic IDE/diagnostic remapping and sidecar cache recovery remain open.

See AI_WORK_STATE.md, CONFORMANCE.md, v1-coverage.json and standard-adapter-map.json for exact tests, jobs, artifact IDs/digests and remaining roles. This increment does not rerun or extend the separately recorded complete compiler-source/fixed-point qualification, or claim full PS grammar/source fidelity.

## Binder/default checkpoint and active compiler grammar goal

Source `9826bdd9dc422fe021de953a570972d7b85df2f4` passes all four jobs in Linux [run 42511067847](https://github.com/dwijayuda/pskernel/actions/runs/42511067847). Ordered mixed binder/default slots reuse native binder nodes and automatic/default parameter semantics; selected declaration heads, source ranges, native DSL ownership, CoeFun and strict empty-call behavior have executed probes. The goal remains **all compiler sources in ProofScript syntax/grammar**, not renamed native sources. Full grammar/corpus migration and source/IDE fidelity remain active requirements; the independent full compiler regression is tracked in [runner PR #223](https://github.com/dwijayuda/pskernel/pull/223). Exact finite scope, artifacts and remaining work are recorded in AI_WORK_STATE.md and the conformance ledgers.

The newer origin-artifact continuation at `863da731fc5957000d4633d13a9711d8d14ae126` passes all four jobs in [run 42512184970](https://github.com/dwijayuda/pskernel/actions/runs/42512184970). Native Lake job composition restores deleted/corrupted origin sidecars without relinking the warm executable. Complete compiler migration to ProofScript grammar and diagnostic/IDE fidelity remain active work; exact evidence is in AI_WORK_STATE.md and the conformance ledgers.
