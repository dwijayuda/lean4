# PS0 — Lean-native JavaScript backend MVP

**Status:** implemented as a restricted *unqualified* slice of the
independent PS0 compiler. All backend implementation modules are written
in Lean, not JavaScript/MJS. Stable Lean 4.35.0 CI has not been observed
passing and emitted JS is not formally verified machine code.

## Command and artifacts

`lake exe ps0 build-js tests/js/nat_mvp.ps NatMvp build/js-nat`

Produces these three files as **one** atomically published bundle:

- `NatMvp.js` — standard ECMAScript module (ESM)
- `NatMvp.d.ts` — TypeScript declarations matching the ESM exports
- `NatMvp.js.map` — Source Map v3 with genuine signed Base64 VLQ,
  original `.ps` sourcesContent and honest declaration-line mappings

Requires an ES2020+ JavaScript runtime with native `bigint`. The source
compiler does not require Node, npm, TypeScript, or a JavaScript package.

## Smallest end-to-end semantic slice

Exports supported:

- `const x: Nat := expression`
- `function f(x: Nat, y: Nat): Nat := expression`
- `function f(): Nat := expression` (selected v7 Unit nullary call)
- Nat literals, parameters, parentheses, one-term braces and Nat `+`,
  `*`, `-` (saturating subtraction); exact-arity calls to earlier eligible
  Nat functions, source-nullary calls, and references to earlier Nat constants

Nat is represented by **nonnegative JS bigint**, not floating-point
number, preserving integers greater than 2^53. Generated functions
reject negative or non-bigint arguments. TypeScript uses `bigint`
because its type system cannot itself express the nonnegative refinement.

All other runtime types/commands, imported modules, nested namespaces,
recursive functions, pattern matching, typeclass/implicit/defaulted
arguments, effects and foreign calls are currently **explicitly rejected**
for the JS backend. Do not silently transpile unknown constructs.

## Architecture — scalable rather than throwaway

| Lean module | Role |
|---|---|
| `PS0/Backend/Js/IR.lean` | Explicit typed portable-runtime Nat expression/declaration IR and original source origin |
| `PS0/Backend/Js/Lower.lean` | PS0 source syntax AST → closed supported IR, rejecting unsupported behavior |
| `PS0/Backend/Js/SourceMap.lean` | Source Map v3 Base64 VLQ with original-source positions |
| `PS0/Backend/Js/Emit.lean` | Deterministic ESM, TS declaration and map output from typed IR |
| `PS0/Backend/Js.lean` | Backend composition |
| `PS0Main.lean` | One source read, Lean check/policy gate, lowering, staged publication |

`build-js` obtains and retains one accepted Lean environment from
 the same checking pass; every JS export is matched against a safe Core
 definition with an exact Nat (or nullary Unit → Nat) telescope.

 `build-js` runs the existing source admission path first: official pinned Lean
elaboration/kernel checking and `#pscv_gate`. Only then does it lower
the exact original `.ps` source to typed runtime IR and emit artifacts.
Unsupported source or failed proof checks cause **no output bundle**.
The native Lean backend and unrestricted `.lean` CLI are unchanged.

**Semantic assurance distinction:** official Lean checking of source
does not constitute a proof of JS semantic preservation. This slice
keeps a finite, reviewable Nat mapping and adds differential runtime
tests against its expected source behavior, but it is not a verified
compiler and carries no verified-executable certificate.

**Output safety:** assemble all three files in a sibling staging
directory, then publish by a directory rename. Refuse overwriting
an existing bundle. Fine-grained source maps, cross-module checked
identity and hardened crash/race handling remain future gates.

## Extension path

1. Qualify actual Lean 4.35.0 build and JS/TS/map execution in CI.
2. Expand typed IR with Bool, String, arrays, ADTs, pattern matches,
   total recursion and portable calls — **not** source-text substitution.
3. Introduce checked Lean Core correspondence and systematic runtime
   semantic-preservation evidence for each new operation.
4. Integrate `PS0-03` source modules, imported visibility, re-export
   identities and typed `.d.ts` references before JS module linking.
5. Extend provenance from declaration-line mappings to expression
   spans, names and optional `.d.ts.map`.
6. Add explicit effect/interop capabilities with audited runtime
   semantics; never infer verified native execution from a proof alone.

## Qualification

`tests/js/nat_mvp.ps` and the CI workflow exercise large Nat arithmetic,
saturating subtraction, runtime argument checking, ESM execution,
TypeScript declaration shape, Source Map v3 integrity, unsupported
source rejection, reproducible output and safe publication.

No generated `.js`/`.mjs` implementation sources are checked in.
The existing `language-feature-progress.json` readiness score is for
PSCV0 v7 language features, not backends: adding this JS backend alone
must not inflate that percentage.
