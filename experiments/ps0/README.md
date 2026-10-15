# PS0 — Lean-backed ProofScript PSCV0 v7 variant

**Status: implemented experimental frontend, NOT full v7 conformance or verified-executable certification.**

PS0 keeps `.ps` as the authoritative application source and reuses the existing
`experiments/pscv0-lean-native/PSCVL` grammar, syntax macros, source admission
checks, effect support and proof-policy gate. It does **not** copy a parser or
elaborator into another compiler. After source syntax admission, official
**Lean 4.35.0 stable**, git `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`,
owns elaboration, dependent typing, tactic elaboration, kernel checking and
native code generation.

This experiment lives in **dwijayuda/lean4** on
`feature/ps0-lean435-stable-v1`, based on the preserved Lean-native PSCV0
experimental branch. The independent `dwijayuda/pskernel` PSC0 compiler,
its backend work, PR #109 and all existing PSKernel branches are unchanged.

## Architecture

```text
source.ps
  -> existing PSCVL closed .ps grammar + Lean hygienic syntax macros
  -> selected Lean syntax tree / validated imports
  -> official Lean 4.35.0 elaborator + tactics + kernel
  -> PS0 preflight policy (no source unsafe/partial/axioms/sorry)
  -> check: report UNCERTIFIED; no executable output
  -> build: official Lean frontend + LCNF.emitC (.olean, C, UNCERTIFIED)
```

The main adapter is `PS0Main.lean`. Its CLI host logic currently follows
the previously qualified PSCVL native entrypoint, but imports the existing
PSCVL grammar and policy rather than maintaining another PSCV0 language engine.
The pin guard rejects execution with a mismatched Lean toolchain.
The sibling PSCVL source, toolchain and provisional environment manifest
were advanced to the exact stable Lean 4.35.0 pin *only on this branch*.

## Run

From `experiments/ps0`:

```sh
lake build ps0
lake exe ps0 environment
lake exe ps0 syntax-kinds tests/pass/basic.ps
lake exe ps0 check tests/pass/basic.ps
lake exe ps0 build ../pscv0-lean-native/tests/pass/native_math.ps NativeMath build/native
```

A successful `build` produces `build/native/NativeMath.olean` and
`build/native/NativeMath.c`. Linking an executable with the official
`leanc` and imported PSCVL static library is a separate integration check.
Use only supported inputs; PS0 must not treat Lean source acceptance as proof
of full PSCV0 source-profile acceptance.

The pinned provisional `environment` manifest reports selected imports,
deriving and scalar-evaluation types; it is **not** a complete transitive
instance, notation, tactic, effect or axiom inventory.

## Assurance and exact limits

- `.ps` syntax is the existing **bounded** PSCVL v7 implementation, not
  complete coverage of the current PSCV0 v7 normative reference.
- Source `partial`, `unsafe`, `axiom`, `sorry` and disallowed grammar
  must fail before artifact emission. Additional source/trust checks remain open.
- `#pscv_gate` is a source/axiom preflight, **not** a proof that every
  executable function satisfies a complete formal contract.
- `Classical.choice` remains in the inherited Lean-native policy allowance.
  A stricter verified PSCV0 profile needs a versioned, independently audited
  permitted-assumption closure before certification.
- Multi-module `.ps` project imports, precise source/IDE positions, full
  verification/effect and erasure obligations, complete pattern/termination
  syntax, and certified executable semantics are NOT implemented.
- Only native Lean targets are built. PS0 does not claim JS, TS, Rust, direct
  Wasm support or translation correctness. The existing PSC0 compiler owns
  those independently.

Development acceptance is tracked in [CONFORMANCE.md](CONFORMANCE.md).
Any failing/pending feature must reject rather than silently pass through
unrestricted Lean syntax. Do not merge this branch into upstream Lean master,
rebase away the preserved experiment, or replace PSC0 without an explicit
future decision.
