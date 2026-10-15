# PS0 v1 — Implementation and Conformance Ledger

**Sole normative reference:** [PS0_V1_LANGUAGE_REFERENCE.md](PS0_V1_LANGUAGE_REFERENCE.md), edition R2, 2026-10-16. Uploaded Git blob `c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`.
**Lean:** official 4.35.0, `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.

**Status:** migration to v1 implemented at the specification/source-policy
foundation; full v1 language closure NOT implemented; exact-commit
Lean CI NOT observed passing. The old v7 41% estimate, fixed
191/181-style progress measures and v7 test assertions are retired.

## Implemented migration changes

| Layer | Current code | Remaining gap |
|---|---|---|
| Canonical document | Complete 4,163-line standalone v1 reference in PS0 | No normative predecessor fallback |
| Syntax adapters | Existing `function`/`const`, comma binders/calls, selected braced forms and Lean-native elaboration | All `psTerm`/`psCommand`/`psTactic`/`psDoSeq` ownership and `PS0.Syntax.lower` (`0B/`9) |
| Grammar | Removed frozen command/attribute/tactic/loop/source-token denial list; diagnostic-only syntax-kind inventory | Full interleaved host grammar and category-aware adaptation |
| Declaration policy | No mandatory v7 axioms/unsafe/partial/IO ban; `#ps0_evidence` is informational | Transitive claim-specific assumptions and evidence `12` |
| Imports/Standard | Native registered/imported extensions determine availability; no v7 finite Standard allowlist | Complete effective module/stage/extension identity and `prelude` isolation |
| Modules | Explicit native `module` parsed; implicit headerless PS module recognized | Full modern module compilation, public-name defaults, hidden bodies and project graph |
| `.lean` | Official Lean process unchanged and unrestricted | Routine exact-commit CI qualification |
| JS backend | Lean typed Nat-only IR, ESM/`.d.ts`/Source Map v3 | Validated build, more types, modules, runtime semantics proof |

**Important:** A v1 feature may be *admitted by the normative
language* but remain *not yet implemented by PS0*. Neither sentence
means it is guaranteed to compile in the current branch.

## New evidence baseline

[v1-coverage.json](v1-coverage.json) records **242** items:
100 capability families, 64 positive source cases, 47 negative
source/disallowed-claim cases, and 31 R2 boundary witnesses.
Every item initially has `PENDING` status. It is not a numeric
implementation-completion percentage.

`PASS` requires real evidence at the exact source, Lean,
compiler and imported environment identity. A static syntax-kind
count or availability via unchanged `.lean` does not qualify PS
source capability. The old PSCV0 v7 registry is not imported
and does not supply a fallback test outcome.

## Distinct validation outcomes

1. **Development:** native editor/elaboration may retain errors or
   `sorry`; not completed proof.
2. **Ordinary checked source:** complete relevant checking, with
   declared assumptions/runtime interfaces classified.
3. **Checked theorem:** precise elaborated proposition and actual
   kernel evidence, conditional on transitive assumptions.
4. **Source-verified:** named policy/spec, evidence for required
   coverage/effects/erasure/termination and assumption closure.
5. **Execution-correspondence-verified:** additional checked
   correspondence to a specified generated artifact/layer.

`#ps0_evidence` does not issue any verified label. A stronger
verified-output policy may refuse an otherwise valid ordinary
unsafe, partial, effectful or axiomatic program; that refusal
must not redefine the PS0 v1 source language.

## High-priority conformance probes

- Native `axiom`, unsafe/partial/`noncomputable`, bodyless
  `opaque` and development `sorry` (native classification).
- Macros, syntax categories, custom elaborators, dynamic
  attribute/deriving registrations, and quotations whose native
  category data must not be globally PS-rewritten.
- Explicit and implicit modern modules, `prelude`, public/meta/all
  import flags and hidden vs exposed public bodies.
- Native value-form instances, imported priority handlers,
  structural and nonstructural recursion, monadic `if let ←`,
  zipped loops, native tactics and semicolon control.
- ProofScript comma-call/tuple/nullary and binder-specific
  source ownership, matching and braced syntax (``0B–5).
- Source/claim boundary tests and the R2 witnesses, including
  per-phase diagnostic or AST semantics checks.

## Backend acceptance (separate from v1 language)

The Nat-only JS backend emits `.js`, `.d.ts` and `.js.map`
from a deliberately closed runtime IR. It is **not** a full
v1 language implementation and does not issue a verified JS
certificate. CI must demonstrate exact Nat arithmetic, type
signatures, source-map positions, deterministic emission,
refusal of unsupported constructs and runtime semantics.

See [PS0_V1_IMPLEMENTATION_PLAN.md](PS0_V1_IMPLEMENTATION_PLAN.md)
for remaining architecture gates and [AI_WORK_STATE.md](AI_WORK_STATE.md)
for the latest development handoff.
