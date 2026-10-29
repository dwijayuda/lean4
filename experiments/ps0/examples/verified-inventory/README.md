# First proof-linked inventory slice

Status: implemented candidate; no successful Lean/Actions run is claimed.

`src/Inventory.ps` contains the actual executable definition. Full native
Lean proofs live in `proofs/Inventory.lean`. The slice supports only two
Nat inputs and literals/addition/multiplication/saturating subtraction.
It is an executable profile experiment, not a restriction of PS0 v1 R2.

The existing `ps0 check` path checks the original source. A private
headerless-module harness places the SAME source bytes after the same
modern-module/public-section setup, using the unchanged PS0 syntax
adapters. This harness is limited to this import-free example: it is not a
new general .ps module resolver or a claim of complete source fidelity.
The separately replayed solution environment is the authoritative proof
and extraction environment; an earlier CLI success is not reused as a
certificate for a different body.

`#ps0_extract` inspects the admitted Lean definition and stages a Nat2 IR
and genuine JS/TS sources. It is an untrusted candidate producer. A
second Lean module proves the proposed IR equal to that exact definition.
The generic `lower_correct` theorem proves preservation into a restricted
nonnegative-BigInt target MODEL. Independent official `lake comparator`
passes check the source specification and the final correspondence
statements, with only explicitly listed standard axioms permitted.

The host independently regenerates the expected target spelling from
validated IR and rejects changed bytes. This validator is trusted code;
there is no claimed formal parser/serializer theorem. Actual tsc consumer
checking and target execution are additional tests, not substitutes for
the Lean proofs. Strict verified-runtime publication is NOT available.

The only publication profile is explicitly selected
`conditional-nat2-reviewed-v0`. It records trust in the reviewed source
adapters, host validator, exact runtime/compiler, BigInt realization and
sufficient resources. It is NOT qualified for hostile compile-time code,
untrusted proof marketplaces, arbitrary FFI or arbitrary PS0 source.
There is no silent fallback from a stricter policy.

Linux CI entry point, from `experiments/ps0`:

```sh
bash tests/run-proof-linked.sh
```

The command requires the exact Lean 4.35.0 pin, working bubblewrap,
Node and a TypeScript compiler supplied via `PS0_TSC`. It refuses to
disable the official replay sandbox. Missing tools or unavailable
namespaces are failures, never a reason to accept unchecked code.

The dedicated workflow also runs host-only validator tests independently
of the existing PS0 baseline. Neither workflow definitions nor committed
proof scripts count as PASS evidence before an actual run is inspected.
