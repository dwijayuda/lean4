# PSV0 — ProofScript Verified Transpiler (independent prototype)

**Status:** experimental restricted transpiler, **not** a verified multi-target compiler. This directory is independent of PS0; it does not import, update, build or depend on the PS0 experiment.

## Goal

Make ProofScript a low-latency source-to-source language, using the original Lean compiler/checker as the optional independent logical authority. The target correctness problem is separate: successfully checking generated Lean does **not** imply generated TypeScript/JavaScript/Rust preserves source behavior.

## Scope of first implementation

A deliberately narrow subset: optional single namespace; one or more single-line declarations of the form

```text
function remaining(stock: Nat, requested: Nat): Nat := stock - requested
```

Names and parameters must be simple identifiers. Expressions support Nat decimal literals, parameters, parentheses, `+`, `-` and `*`. Operators follow ordinary left associativity and multiplication precedence. Nat subtraction saturates at zero. No imports, user macros, arbitrary Lean syntax, function calls, effects, recursion, proof terms or other types are accepted. Invalid input is rejected instead of passed through as unchecked source. This subset is not claimed to implement PS0 v1 or all of ProofScript.

Generated JS and TS use bigint and perform entry-point nonnegative bigint checks. They have candidate-level semantics tests, not a formal proof against ECMAScript or TypeScript. The Lean emitter is a syntax-directed proposal. Strict builds now append an independent PSV0 Nat IR reference semantics and generate an exact-body correspondence obligation for each emitted Lean function; each obligation must pass Lean's kernel via `by rfl`. That obligation connects the *parser's IR* to generated Lean, **not** the original source's independently formalized meaning, so no complete source-to-Lean equivalence claim is made.

## Commands

Requires Node.js 22+ for the CLI and tests. No npm dependencies for fast mode. Strict mode requires a separately installed compatible Lean binary, plus a TypeScript checker if the TypeScript target is requested. The standalone `psv0/lean-toolchain` pins the Lean 4.35.0 reference-model experiment without changing the fork's root toolchain.

```sh
node psv0/src/cli.mjs psv0/examples/Inventory.ps --out /tmp/psv0-fast --target lean,ts,js --mode fast
node --test psv0/test/*.test.mjs
cd psv0 && lake build && cd ..  # requires elan and the PSV0 Lean toolchain
```

For an independent Lean check, install a compatible Lean binary and run:

```sh
node psv0/src/cli.mjs psv0/examples/Inventory.ps --out /tmp/psv0-strict --target lean,ts,js --mode strict --lean lean --tsc tsc
```

Strict mode invokes the selected original Lean binary on a retained `PSV0Check.lean` source containing independently maintained `formal/Reference.lean` semantics, the generated Lean definitions, generated exact-IR correspondence theorems, and an optional `--proof FILE.lean`. It invokes `tsc` and Node syntax checks for requested targets. The chosen Lean binary and imported proof files are **not sandboxed** by this CLI: use only trusted proof inputs or isolate the build externally. Output is staged in a temporary directory and renamed into place on success. A pre-existing destination is refused in ordinary use; this is **not** a concurrency-safe `RENAME_NOREPLACE` guarantee against an adversarial filesystem race. It is labeled `lean-checked-target-unverified`, never verified. Lean/checker availability is required for strict mode. The tool does not install or ship Lean.

The `verified` mode deliberately **fails** until independently checked source/IR, IR/target, serialization and runtime correspondence evidence can be checked. `formal/Reference.lean` includes a theorem about a restricted mathematical Nat target model, not a theorem about deployed JavaScript/TypeScript engines. It must never auto-downgrade.

## Source and target assurance

| Lane | Actually checked | Not established |
| --- | --- | --- |
| fast | Restricted grammar; deterministic .lean/.ts/.js emission | Lean acceptance, semantic proof, runtime correspondence |
| strict | Same, plus original Lean checking of exact IR-to-generated-Lean obligations, and target type/syntax checks | Trusted parsing of source to IR, target behavioral preservation, production runtime/model adequacy |
| verified | Not implemented; refusal | No verified-execution claim |

A manually supplied Lean theorem may prove properties of the *generated Lean definition* but not, alone, a relationship to the original .ps or the compiled .ts/.js target.

## Next research milestones

1. Formalize PSV0 source spelling and parsing semantics independently of the JS parser; tie the precise source bytes to the IR actually checked.
2. Qualify the generated Lean IR bridge with exact pinned Lean CI receipts; the bridge is currently candidate code until a successful Lean run is observed.
3. Prove IR-to-target semantics for a restricted BigInt target model; validate concrete emitted bytes against target AST.
4. Develop an independently replayed certificate bound to source, assumptions, backend/toolchain versions and artifact hashes.
5. Add Rust only after specifying its exact integer model and runtime boundary.
6. Benchmark cold/warm fast vs strict; add incremental verification caches without assuming that the Lean kernel dominates cost.

No PS0 code or CI is modified by this experiment.
