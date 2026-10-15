# PS0 v1 — Source and Assurance Boundaries

**Normative authority:** [PS0_V1_LANGUAGE_REFERENCE.md](PS0_V1_LANGUAGE_REFERENCE.md), ``0, 0A, 0B, 1, 12.

## Two distinct source grammars

`.ps` is the full **PS0 v1** language target: native Lean 4.35.0
capabilities plus its explicitly specified ProofScript surface adapters
and context/category rules. A written `module` is valid with native
modern module defaults; a headerless file denotes an implicit modern
module with public-name defaults. `prelude`, `public import`,
`meta import`, `import all` and stage/visibility restrictions follow
actual Lean semantics.

`.lean` is completely native Lean 4.35.0 with no PS grammar or
assurance-policy injection. It can keep its normal imports, macros,
unsafe/partial definitions and foreign runtime features.

**PS0 v1 is not PSCV0 v7 with a different filename.** Native
`unsafe`, `partial`, `noncomputable`, `axiom`, `sorry` during development,
IO, custom attributes, syntax/elaborators, instance value bodies,
fixed points, registered tactics and proof/diagnostic tools are admitted
in ordinary `.ps` source when valid under native Lean types/imports.
They must **not** be forbidden merely because they prevent a particular
stronger verified-program claim.

## Separate evidence outcomes

The language reference distinguishes development, ordinary checked
modules, checked theorems with disclosed assumptions, source-verified
programs, and execution-correspondence-verified programs.

`#ps0_evidence` is an informational declaration-classification
command. It does not certify completeness, prove transitive
assumption closure, approve axioms, or establish compiled artifact
semantics. A stronger claim requires an explicitly identified
claim/policy, actual checked evidence, proof/spec/effect/erasure/
termination coverage, and an identified runtime boundary.

A `sorry` may remain in development source, but a relevant
`sorryAx` dependency disqualifies a completed proof. An ordinary
unsafe or partial program can compile without asserting total
correctness or formal execution correspondence.

## Current implementation boundaries

- `check FILE.ps` delegates term/proof elaboration to official Lean,
  but complete PS-owned host grammar/category adaption and module
  visibility remain outstanding.
- `module-header FILE.ps` preserves actual native module/import metadata;
  this is inspection, not proof of complete public/private module
  lowering.
- `build FILE.ps …` is bounded native compilation and currently
  refuses imported modern PS modules where output visibility is
  not yet faithfully implemented. Such rejection is an
  **implementation limitation**, not a language restriction.
- `build-js FILE.ps …` supports only a typed Nat runtime subset.
  A valid PS0 v1 program may be rejected for JavaScript emission
  without becoming invalid PS0 source.
- `check FILE.lean`, `build FILE.lean`, and `lean …` retain the
  standalone native Lean process path without PS source rules.

See [PS0_V1_IMPLEMENTATION_PLAN.md](PS0_V1_IMPLEMENTATION_PLAN.md)
for the unimplemented v1 coverage and [v1-coverage.json](v1-coverage.json)
for 242 independent traceable requirements. None of the former
v7 language bans or v7 pass counts apply.
