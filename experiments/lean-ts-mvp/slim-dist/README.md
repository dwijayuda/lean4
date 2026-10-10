# Lean 4.35.0-rc4 headless distribution experiment

This is a custom distribution of *unmodified* official Lean binaries and compiled
artifacts, not a fork of the Lean kernel, elaborator, or compiler. Only Linux x86_64
is tested in the first MVP.

The headless profile includes:
- Official bin/lean and lib/lean shared libraries.
- Every Lean .olean, .ir, and .ir.sig artifact needed for importable runtime code.
- Compiled LeanTs plugin artifacts, so downstream users can import LeanTs.
- Runtime support shared libraries, licenses, relocatable bin/lean-ts-lean script.

The package omits Lake, leanc, Clang, LLVM, static .a archives, C headers, Lean
sources, editor .ilean files, private
olean payloads. Lean 4.35 also requires .olean.server for ordinary imports. Removal of .olean.private and .ir is an experimentally testable
claim, not an assumption that every Lean feature works.

From experiments/lean-ts-mvp with elan and Node.js installed:

    lake build LeanTs
    python3 slim-dist/build_slim.py --output slim-dist-output/lean-ts-headless
    bash slim-dist/smoke.sh slim-dist-output/lean-ts-headless headless

The GitHub workflow measures the official and trimmed directories, publishes
a compressed tarball plus JSON metrics, and verifies the copied standalone lean
binary without relying on elan or Lake. It checks simp, omega, grind, #eval,
the tiny Lean-to-TypeScript backend, proof rejection and Node.js execution.

Use bin/lean-ts-lean on an unpacked distribution to launch Lean with the
correct bundled module and library directories, without a separately installed
Lean toolchain. This does not include Node.js/TypeScript 7: install those
separately to compile the generated TypeScript.

Caveats: not a universal Lean distribution, not evaluated for Mathlib, native
plugins, Lean4Checker, language-server/editor functionality, or all tactics.
The Lean kernel checks the source; generated JavaScript is not formally proven
correct by these smoke tests. Sizes are Linux platform-specific measured bytes.

Optional intentionally risky candidate:

    python3 slim-dist/build_slim.py --output slim-dist-output/lean-ts-no-ir --mode no-ir --no-archive
    bash slim-dist/smoke.sh slim-dist-output/lean-ts-no-ir no-ir

The no-ir profile is non-production and only accepted if the same tests pass.
