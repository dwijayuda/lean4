# Lean 4.35.0-rc4 PSCV0 thin frontend MVP

Status: **experimental syntax and elaboration frontend**, not full PSCV0 conformance or certified executable compilation. No Lean kernel or compiler internals are changed. Lives beside the LeanTs MVP.

## Source provenance

Copied and adapted from user-owned dwijayuda/pskernel,
branch feature/pscvl-lean-frontend, commit be03e8b792447e24d1661a02b10f898452bac26e.
Source directory: PSCVL/, files PSCVL/Syntax.lean, Grammar.lean,
Policy.lean, Effect.lean, root PSCVL.lean, and Main.lean
(renamed PSCVLMain.lean).

Target: user-provided 2026-10-11 Lean-first pscv0 reference,
Lean 4.35.0-rc4 commit c29b6dda4f7c20e3eeaa717c4e565663c5cfa364.
Reference examples are design targets, not conformance evidence.

## Architecture

PSCV0 syntax macros emit *Lean syntax trees*, not textual Lean. Lean
elaborates and checks the results with its own typechecker and kernel.
A source-profile validator runs before elaboration, and a final policy gate
runs on elaborated declarations. CLI reports UNCERTIFIED and emits no
executable artifacts.

Targeted MVP fragment:
- const to def; comma-binder function to def.
- Adjacent f(x,y) to curried Lean application.
- function clock() to required Unit and invocation clock().
- Braced single-term expressions, pure if, native by {...}.
- Selected native declarations and #check.
- Rejection of unsafe/partial source, sorry, user axioms, unknown macros.
- A grammar-category-aware ban on spaced parenthesized applications.

Incomplete: source imports and manifests, full nested grammar restrictions,
structure/inductive/match brace lowering, deriving allowlist, typed named or
default empty-call completion, controlled pure #eval, source maps, and the
complete RC4 intrinsic verification discipline. This does not implement
general PSCV0 TypeScript/JavaScript compilation or verified-executable
certification; the adjacent LeanTs Nat backend remains independent.

RC3-specific ghost, refine type, and custom errors syntax were removed,
as the 2026-10-11 reference instead uses Lean erased, Subtype, and
theorems/contracts.

## Validate

Run in experiments/lean-ts-mvp:

    lake build PSCVL pscv0
    lake exe pscv0 check pscv0-tests/pass_minimal.ps
    lake exe pscv0 check pscv0-tests/pass_braced_if.ps

The GitHub workflow tests these and fail-closed grammar cases.
No proof of JavaScript semantics or unrestricted Lean conformance is claimed.
