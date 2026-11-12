# PS0 proof-linked JS/TS slice — implementation candidate

Date: 2026-10-29 (Asia/Jakarta). Status: source committed for Linux CI;
no successful compiler/proof/runtime execution is claimed by this document.

## Scope and fixed example

The example computes inventory remaining after a request, with saturating
Nat subtraction. Its separate Lean proof states the exact mathematical
function, plus a stock bound and a conservation lemma. The required release
statement is fixed independently by the host: the output equals
`stock - requested`. The candidate cannot replace that property with `True`.

Only a safe monomorphic function with two Nat inputs is eligible. The IR
admits those inputs, Nat literals, addition, multiplication and subtraction.
No unknown call, recursive function, effect, foreign operation, universe
parameter, unsafe/partial root or root replacement implementation is accepted.
The extractor checks resolved overloaded operations against canonical Nat
operations; an operator spelling is not semantic evidence.

## Files

| Path | Responsibility |
|---|---|
| `PS0/Verified/Core.lean` | Nat2 IR, restricted target model and generic lowering theorem |
| `PS0/Verified/Extract.lean` | Actual admitted-body extraction to private candidates |
| `PS0/Verified/Emit.lean` | Lean-written JS and genuine TypeScript source emission |
| `examples/verified-inventory/src/Inventory.ps` | Executable source |
| `examples/verified-inventory/proofs/Inventory.lean` | Full-Lean proofs of that definition |
| `scripts/proof_linked.py` | Trusted reviewed-fixture host, proof challenges, validation and publication |
| `tests/test-proof-linked-host.py` | Host schema, corruption, policy and no-overwrite tests |
| `tests/proof-linked-qualification.py` | Positive end-to-end and intended semantic refusals |
| `tests/proof-linked-runtime.mjs` | Arithmetic, large BigInt and hostile-input regressions |
| `tests/run-proof-linked.sh` | Exact-pin Linux integration entry point |
| `.github/workflows/ps0-proof-linked-js-ts.yml` | Independent host job and full Linux qualification job |

The previous work state is archived without byte changes. Existing PS0
frontend/backend source, R2 and the 242-row conformance ledger are unchanged.

## Evidence chain

1. Snapshot source/proof/compiler inputs; preserve original .ps body bytes.
2. Exercise the existing `ps0 check` on the source snapshot. This is not a
   proof receipt and does not authorize output.
3. Construct a private import-free modern-module harness with the actual
   PS0 parser/macros. Full module-resolution/source-fidelity qualification
   is explicitly NOT claimed for this small harness.
4. Official `lake comparator` builds and exports in its own sandbox, checks
   the exact source specification and replays through the official kernel.
   Only `propext`, `Quot.sound` and `Classical.choice` are policy-permitted.
5. The untrusted command inspects the admitted logical body, not source
   expression text, and emits IR plus JS/TS into `.lake/ps0-candidate`.
6. An independent host validates the bounded IR and regenerates the exact
   expected target spelling. A consistent but wrong IR STILL needs proof.
7. Generate an extraction theorem equating that literal IR to the exact
   source definition, a target-model theorem and the fixed output property.
   A second official comparator pass checks all three statements/proofs.
8. Recheck snapshots; actually compile a TS consumer, emit JS from TS,
   compare the emitted fragment, and execute direct JS and TS-generated JS.
9. Publish one immutable bundle using Linux `renameat2(RENAME_NOREPLACE)`;
   failed checks cannot replace an earlier bundle or expose a partial one.

The emitter itself never publishes a verified result. The final host never
trusts a candidate-supplied `verified: true` field or a saved success receipt.

## Precise assurance boundary

The generic Lean theorem concerns a restricted NONNEGATIVE BigInt model:
subtraction outside its nonnegative domain is undefined, and the lowering
proves that generated conditionals avoid it. It is not a formalization or
proof of all ECMAScript, V8, Node, TypeScript or their runtime libraries.

The only supported publication profile is explicitly selected
`conditional-nat2-reviewed-v0`; output includes `strict_verified_execution:
false` and the exact assumptions/tool identities. The stronger
`verified-portable` request fails rather than silently downgrading.

Remaining trusted pieces include the PS0 frontend/harness interpretation,
Python host/canonical-byte validator, actual target realization and resource
availability. There is no completed formal serialization proof. The host
is for reviewed source/proof fixtures, not adversarial macro/elaborator
execution or untrusted proof marketplaces. The original preliminary
`ps0 check` still runs the existing frontend; its broader process-isolation
problem is not solved by this slice.

Current historical `build` and `build-js` commands retain their UNCERTIFIED
behavior. This new experiment does not silently adopt a global CLI policy.

## Candidate test matrix (not observed results)

- A real positive .ps → proof → IR → JS/TS bundle.
- Same-signature wrong source body, missing proof, irrelevant proof,
  development `sorry`, and a bespoke axiom must fail the source proof gate.
- A self-consistent same-signature wrong IR must fail the extraction proof.
- Modified JS/TS, duplicate JSON keys, unknown primitives, invalid literals,
  missing/extra artifacts, wrong roots and symlinks must fail host validation.
- A stronger unsupported profile must not downgrade automatically.
- Existing output, including an empty output directory, must not be replaced.
- Runtime tests cover a small exhaustive input grid, values above 2^53 and
  large BigInts, saturation/conservation, and rejection without object coercion.
- Actual tsc positive/negative consumers exercise the public bigint ABI.

Toolchain choices for this experiment: Lean 4.35.0 exact source pin;
Node 22.23.3; TypeScript 5.7.3. The CI records npm lockfile integrity and
tool identities. These are experiment pins, not universal platform support.

## Acceptance and next work

Do not call MB0, MB1, MB2 or MB3 complete until exact-commit CI logs are
inspected. A source-level generic theorem script is not evidence that Lean
accepted it. A passing host test job alone cannot qualify any Lean proof.
A green end-to-end run would qualify only the documented conditional slice,
not complete R2, hostile-build security or verified machine/runtime behavior.

First obtain actual Linux execution and repair concrete baseline/API errors.
Then remove the limited harness via the canonical mixed-source module path,
prove/qualify the serializer boundary, harden compilation isolation, and
expand runtime families only after this foundation has evidence.
