# Lean 4.35.0-rc4 headless distribution experiment

This is a custom distribution of *unmodified* official Lean binaries and compiled
artifacts, not a fork of the Lean kernel, elaborator, or compiler. Only Linux x86_64
is tested in the first MVP.

The headless profile includes:
- Official bin/lean and lib/lean shared libraries.
- Compiled Init, Lean, and Std module data (.olean, .olean.server, .olean.private, .ir and .ir.sig).
- No Lake and standalone compiler-helper module families; importing excluded modules is unsupported.
- Compiled LeanTs plugin artifacts, so downstream users can import LeanTs.
- Runtime support shared libraries, licenses, relocatable bin/lean-ts-lean script.

The package omits Lake, leanc, Clang, LLVM, static libraries, headers,
compiler sources and editor .ilean data. Lean RC4 also requires .olean.server
and .olean.private files during this tested import path, so headless retains
both. No-IR and no-private profiles are only experimental.

From experiments/lean-ts-mvp with elan and Node.js installed:

    lake build LeanTs
    python3 slim-dist/build_slim.py --output slim-dist-output/lean-ts-headless
    bash slim-dist/smoke.sh slim-dist-output/lean-ts-headless headless

The GitHub workflow measures the official and trimmed directories, publishes
a Zstandard-compressed tarball plus JSON metrics, and verifies the copied standalone lean
binary without relying on elan or Lake. It checks simp, omega, grind, #eval,
the tiny Lean-to-TypeScript backend, proof rejection and Node.js execution.

Extract the GitHub Action tarball with tar --zstd -xf lean-ts-headless.tar.zst.
The extracted directory is named lean-ts-headless. CI tests that archive after
moving it to another directory; this establishes relocation within the same
Linux runner environment.

Use bin/lean-ts-lean on an unpacked distribution to launch Lean with the
correct bundled module and library directories, without a separately installed
Lean toolchain. This does not include Node.js/TypeScript 7: install those
separately to compile the generated TypeScript.

Measured on GitHub Actions Ubuntu 24.04 x86_64, 10 October 2026:

| Measure | Official RC4 | Headless distro | Reduction |
| --- | ---: | ---: | ---: |
| Uncompressed regular files | 3,137,199,455 B | 2,250,732,419 B | 28.26% |
| Compressed tar.zst | 594,452,193 B | 524,706,069 B | 11.73% |

The official compressed size comes from the GitHub v4.35.0-rc4 release asset;
slim figures are from CI run 38031649336. Values will vary if files change or
zstd settings differ. Github Actions wraps the tarball inside a ZIP artifact.


Caveats: not a universal Lean distribution, not evaluated for Mathlib, native
plugins, Lean4Checker, language-server/editor functionality, or all tactics.
The Lean kernel checks the source; generated JavaScript is not formally proven
correct by these smoke tests. Sizes are Linux platform-specific measured bytes.

Optional intentionally risky candidate:

    python3 slim-dist/build_slim.py --output slim-dist-output/lean-ts-no-ir --mode no-ir --no-archive
    bash slim-dist/smoke.sh slim-dist-output/lean-ts-no-ir no-ir

The no-ir candidate **fails** the pinned smoke tests: Lean reports a missing
module-data file for Init.Data.Iterators.Lemmas.Monadic.Basic. It must not be
distributed as proof-host compatible. The no-private candidate also fails
module imports on this Lean release. The standard headless profile keeps both.
