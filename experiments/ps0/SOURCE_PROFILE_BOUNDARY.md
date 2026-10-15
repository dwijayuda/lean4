# PS0 source profile boundary — PSCV0 v7 applies only to .ps

**Decision (15 October 2026):** PSCV0 v7 syntax restrictions, banned
source forms, environment selection, proof-policy gates and eventual verified
source certificates apply **only to `.ps` files**. Ordinary `.lean` files
retain the **full, unrestricted language supported by official Lean 4.35.0**.
This is a source-language boundary, not permission to treat any .lean proof
as an accepted v7 verified application.

## Routing

| Source/command | Compiler frontend | PSCV0 source restrictions? | Status |
| --- | --- | --- | --- |
| `ps0 check file.ps` | PS0 grammar + official Lean + `#pscv_gate` | **Yes** | Checked v7 *subset*, uncertified |
| `ps0 build file.ps Name out/` | Same PS0 admission + official Lean native compiler | **Yes** | Native output, uncertified |
| `ps0 syntax-kinds file.ps` | PS0-owned grammar auditor | **Yes** | Source investigation |
| `ps0 check file.lean` | **External official Lean executable** | **No** | Ordinary Lean diagnostics/semantics |
| `ps0 build file.lean Name out/` | **External official Lean compiler** | **No** | Ordinary Lean `.olean` and C (output-safety staging only) |
| `ps0 lean [native args...]` | Direct, unmodified official Lean CLI args | **No** | Native Lean toolchain pass-through |

The native executable is resolved from the pinned Lean **sysroot**
(`leanprover/lean4:v4.35.0`,
`eb6cafb7290e8bd5f2937522d8d804f58f02bafc`). It runs in a
**separate OS process**. The host's imported `PS0.Syntax` /
`PS0.Policy` modules cannot accidentally register v7 command elaborators
in that native process's imported environment.

### Native .lean remains genuine Lean

The `.lean` pass-through does not reject any otherwise valid Lean source
construct based on PSCV0 rules, including:

- native whitespace application, indentation-sensitive terms and native
  module imports or `public import`;
- Lean `axiom`, `unsafe`, `partial`, and `sorry` (subject to ordinary
  Lean compiler semantics and warnings);
- unselected v7 attributes, syntax extensions, elaborators, tactics and
  ordinary `#eval` effects such as `IO.println`.

This is not a claim that Lean accepts *ill-typed* programs: Lean's own
parser, elaborator, kernel and compiler still apply exactly as normal.
The optional `ps0 build ... out/` wrapper validates its output path and
avoids overwriting an existing output bundle; this is a file-publication
policy, **not** a restriction on source language features. For arbitrary
native compiler arguments, use `ps0 lean ...` directly.

### The .ps side is unchanged

The v7 `.ps` grammar remains restricted by `PS0/Grammar.lean` and
`PS0/Policy.lean`. It rejects user-written unsafe/partial/axiom/sorry and
unsupported imports/commands (subject to its incomplete v7 feature matrix).
The `.ps` build still runs `#pscv_gate` and cannot use the unrestricted
`.lean` route to bypass its mandatory proof/spec/effect obligations.

A project may contain both source types. For future mixed-module imports,
**each `.lean` file is compiled by Lean without PSCV0 restrictions**.
But a `.ps` verified executable depending on an imported `.lean` module
must still prove/audit the imported assumption, specification, effect and
runtime dependencies **at the `.ps` boundary**. Native Lean acceptance is
not a PSCV0 verified-executable certificate; such imports remain gated
until the planned PS0-03 module graph and PS0-08 assurance closure exist.

## Acceptance tests

`tests/lean/unrestricted.lean` exercises a native Lean axiom, an unsafe
function, a partial function, a theorem with `sorry`, and an IO diagnostic
that prints `PS0_LEAN_UNRESTRICTED_OK`. GitHub CI runs:

```sh
lake exe ps0 check tests/lean/unrestricted.lean
lake exe ps0 lean tests/lean/unrestricted.lean
lake exe ps0 build tests/lean/unrestricted.lean NativeUnrestricted build/lean-native
```

In parallel, `tests/fail/unsafe.ps`, `sorry.ps` and other v7 negatives
must still be refused by the `.ps` policy.

**Evidence status:** commands and fixtures are committed; until an
exact-commit stable-Lean CI run is inspected and green, their successful
execution remains unverified. Do not count native `.lean` features toward
the separate 20-family PSCV0 v7 language-readiness percentage.
