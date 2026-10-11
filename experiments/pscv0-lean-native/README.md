# ProofScript `pscv0` — Lean-native language frontend

**Purpose:** complete the ProofScript `pscv0` source language as a semantic subset of Lean 4.35.0-rc4, with small, TypeScript-friendly syntax deviations and reuse of Lean's parser, elaborator, tactics, kernel and native compiler. This is a **language-conformance workstream**, not a new typechecker, Lean distro, or JavaScript compiler.

**Pinned upstream:** `leanprover/lean4:v4.35.0-rc4`, git `c29b6dda4f7c20e3eeaa717c4e565663c5cfa364`.
**Specification:** [PSCV0_LANGUAGE_REFERENCE.md](PSCV0_LANGUAGE_REFERENCE.md).
**Verified functionality vs. gaps:** [CONFORMANCE.md](CONFORMANCE.md).
**Continuation state:** [AI_WORK_STATE.md](AI_WORK_STATE.md).

## Workflow

From `experiments/pscv0-lean-native` with the pinned official Lean toolchain:

```sh
lake build PSCVL psc
lake exe psc check tests/pass/basic.ps
lake exe psc check tests/pass/contract_pure.ps
lake exe psc syntax-kinds tests/pass/match_named_generalized.ps
lake exe psc build tests/pass/native_math.ps NativeMath build/native
```

`psc environment` reports the provisional pinned Standard module/deriving/eval registry; CI compares it with `PSCV0_STANDARD_ENV.json`. This is not a full Lean semantic registry digest.

`psc check` accepts a selected `.ps` grammar, lowers PSCV0 sugar into **native Lean syntax trees**, then elaborates and checks with Lean. It reports **UNCERTIFIED**, never a verified-executable certificate.

`psc build` performs the same source and proof preflight and delegates to the official `Lean.Elab.runFrontend`/`Lean.Compiler.LCNF.emitC` APIs to generate `.olean` and C. Linking uses the installed `leanc` toolchain; see `.github/workflows/pscv0-native-language.yml` for the end-to-end native executable test.

## Example

```lean
structure Point where {
  x: Nat
  y: Nat
}

private function sum(p: Point): Nat := { p.x + p.y }

theorem sumZero: sum({ x := 0, y := 0 }) = 0 := by {
  rfl
}
```

Native Lean-dependent types, tactics, pattern matching and code generation remain the source of truth. The current tests also include `mutual { ... }`, local `where { ... }`, Lean-native deriving, named/default function calls, sections, dependent conditionals, native `given`, verified `while`, StateM `for` contracts, `function` contract aliases, guarded scalar `#eval`, pinned Std/Init imports, and braced typed `try`/`catch` with rejection of native layout-only handler bodies.

## Assurance and limitations

The source gate rejects user `partial`/`unsafe`/`axiom`/`sorry` and intentionally rejects ordinary Lean aliases incompatible with PSCV0's canonical source, such as ASCII `.` goal bullets and spaced parenthesized applications. For recursively defined, logically total Lean functions, native compilation may generate compiler-specific `_unsafe_rec` helpers. The policy treats those separately from user-written unsafe definitions and does not give them proof authority.

**Not fully implemented:** complete language-reference grammar closure, first-class `.ps` project imports and re-exports, versioned environment/deriving/tactic registries, pure-total `#eval`, complete indexed pattern/equation and verification forms, precise source/IDE mapping, total proof/effect/erasure closure and verified-executable certification. Refer to CONFORMANCE.md rather than inferring support merely from Lean's upstream capabilities.

CI is evidence for a finite corpus of examples and a single native execution path, not formal proof of compiler translation correctness or foreign runtime semantics. Current frontend is a copy/refinement of the user's earlier PSCVL experiment; all upstream Lean kernel and compiler source remains unchanged.

**Out of scope in this branch:** TypeScript 7 output, WebAssembly, Rust, a slim Lean distribution, independent PSKernel metatheory or self-hosting.
