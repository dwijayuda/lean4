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
| `PS0/HostCategories.lean` | Initial four PS v1 host-category interfaces and `PS0.Syntax.lower` native capture bridge; full host operand lowering pending |
| `PS0/Syntax.lean` | Owned PS surface adaptations; full category-aware call/quote/record lowering pending |
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

**CI qualification is not confirmed.** No successful exact-commit
Lean 4.35.0 PS0 workflow was obtained through the connected GitHub
checks in this conversation. The presence of code or tests is not
evidence that they currently compile or pass.
