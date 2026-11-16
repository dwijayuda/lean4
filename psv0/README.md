# PSV0 — ProofScript Verified Transpiler (independent prototype)

**Status:** experimental restricted transpiler, **not** a verified multi-target compiler. This directory is independent of PS0; it does not import, update, build or depend on the PS0 experiment.

## Goal

Make ProofScript a low-latency source-to-source language, using the original Lean compiler/checker as the optional independent logical authority. The target correctness problem is separate: successfully checking generated Lean does **not** imply generated TypeScript/JavaScript/Rust preserves source behavior.

## Scope of first implementation

A deliberately narrow subset: optional single namespace; one or more single-line declarations of the form

\`\`\`text
function remaining(stock: Nat, requested: Nat): Nat := stock - requested
\`\`\`

Names and parameters must be simple identifiers. Expressions support Nat decimal literals, parameters, parentheses, \`+\`, \`-\` and \`*\`. Operators follow ordinary left associativity and multiplication precedence. Nat subtraction saturates at zero. No imports, user macros, arbitrary Lean syntax, function calls, effects, recursion, proof terms or other types are accepted. Invalid input is rejected instead of passed through as unchecked source. This subset is not claimed to implement PS0 v1 or all of ProofScript.

Generated JS and TS use bigint and perform entry-point nonnegative bigint checks. They have candidate-level semantics tests, not a formal proof against ECMAScript or TypeScript. The Lean emitter is a syntax-directed proposal; no source-to-Lean semantic equivalence theorem is yet established.

## Commands

Requires Node.js 22+ for the CLI and tests. No npm dependencies.

\`\`\`sh
node psv0/src/cli.mjs psv0/examples/Inventory.ps --out /tmp/psv0-fast --target lean,ts,js --mode fast
node --test psv0/test/*.test.mjs
\`\`\`

For an independent Lean check, install a compatible Lean binary and run:

\`\`\`sh
node psv0/src/cli.mjs psv0/examples/Inventory.ps --out /tmp/psv0-strict --target lean,ts,js --mode strict --lean lean --tsc tsc
\`\`\`

Strict mode invokes the selected original Lean binary on generated Lean (and an optional \`--proof FILE.lean\` appended into its checker module), and invokes \`tsc\` and Node syntax checks for requested targets. The chosen Lean binary and imported proof files are **not sandboxed** by this CLI: use only trusted proof inputs or isolate the build externally. Output is atomically staged and the destination must not already exist. It is labeled \`lean-checked-target-unverified\`, never verified. Lean/checker availability is required for strict mode. The tool does not install or ship Lean.

The \`verified\` mode deliberately **fails** until source/IR, IR/target, serialization and runtime correspondence evidence can be checked. It must never auto-downgrade.

## Source and target assurance

| Lane | Actually checked | Not established |
| --- | --- | --- |
| fast | Restricted grammar; deterministic .lean/.ts/.js emission | Lean acceptance, semantic proof, runtime correspondence |
| strict | Same, plus original Lean acceptance and target type/syntax checks | ProofScript-to-Lean equivalence or target behavioral preservation |
| verified | Not implemented; refusal | No verified-execution claim |

A manually supplied Lean theorem may prove properties of the *generated Lean definition* but not, alone, a relationship to the original .ps or the compiled .ts/.js target.

## Next research milestones

1. Formalize independent PSV0 source semantics and define an explicit typed IR.
2. Prove/check the source-to-Lean relation, using reviewed source obligations rather than candidate-generated tautologies.
3. Prove IR-to-target semantics for a restricted BigInt target model; validate concrete emitted bytes against target AST.
4. Develop an independently replayed certificate bound to source, assumptions, backend/toolchain versions and artifact hashes.
5. Add Rust only after specifying its exact integer model and runtime boundary.
6. Benchmark cold/warm fast vs strict; add incremental verification caches without assuming that the Lean kernel dominates cost.

No PS0 code or CI is modified by this experiment.
