# PS0 — Lean 4.35-backed ProofScript v1

**Edition:** PS0 v1 R2 (2026-10-16). **Implementation:** in progress;
not a completed v1 compiler or a verified executable compiler.

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

This is native build integration, not complete PS0 source conformance or verified runtime execution. It currently supports one `.ps` entry module with toolchain and Lake-managed `.lean` dependencies. Recursive `.ps` project dependency discovery, full host operand adaptation, bootstrap `prelude` and source-origin fidelity remain open. Dependencies must be declared in the Lake configuration; `PS0NativeSupport` is the integration fixture. Linux qualification is recorded in `AI_WORK_STATE.md`.

`cd experiments/ps0`

`lake build PS0 ps0`

`lake exe ps0 check tests/v1/native_capabilities.ps`

`lake exe ps0 check tests/v1/registered_syntax.ps`

`lake exe ps0 module-header tests/v1/explicit_module.ps`

`lake exe ps0 check tests/lean/unrestricted.lean`

`lake exe ps0 lean [native Lean args]`

The `module-header` subcommand is an introspection aid, not a
module-completion certificate. Native module-mode checking/building and imported Lean module flags
are now wired. Complete PS project graph, body exposure,
source-origin fidelity and bootstrap `prelude` isolation remain
implementation milestones.

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
| `PS0/HostCategories.lean` | Four PS v1 host categories, a selected adjacent `psTerm` identifier-call parser, and `PS0.Syntax.lower` to native Lean application AST; full standard operand adaptation pending |
| `PS0/Syntax.lean` | Typed/inferred public/private `function` and `const` bodies now lower through PS-owned `psTerm`; full native declaration/proof/tactic/do operand adaptation pending |
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
See `AI_WORK_STATE.md` for exact source/runner identities, artifacts and limits.

