# PSCV0 Lean 4.35.0-rc4 native language frontend

This independent language-only experiment preserves official Lean parsing, elaboration,
typeclasses, tactics, theorem checking, and **native code generation**. It is copied
from the working PSCVL prototype in the user's Lean fork, which itself originated
from `dwijayuda/pskernel` branch `feature/pscvl-lean-frontend`.

The separate TypeScript backend and slim-distribution experiments remain on their
existing branches and are NOT dependencies of this project. Source is `.ps`.
No Lean C++, kernel, bootstrap or stage0 files are changed.

From this directory:

    lake build PSCVL psc
    lake exe psc check tests/pass/basic.ps
    lake exe psc build tests/pass/native_math.ps NativeMath build/native

`psc check` validates the selected PSCV0 syntax and uses Lean's ordinary
elaboration/kernel checking. `psc build` first performs the same gate, then
uses Lean.Elab.runFrontend to write .olean module metadata and
Lean.Compiler.LCNF.emitC to emit native C. Compile/link with Lean's
official `leanc`. The CI tests the compiled PSCV0 module through a small
Lean native executable harness.

The source profile is NOT fully conformant with the 2026-10-11 PSCV0 language
reference. In particular, controlled user imports, full native syntax grammar
restrictions, rich braced match/structure/inductive forms, deriving allowlist,
#eval effect restrictions, full default/named argument semantics, source maps,
and complete verification policy are pending.

This profile reports `UNCERTIFIED`. It does not issue verified-executable
certificates or assert native backend semantic preservation proofs.
