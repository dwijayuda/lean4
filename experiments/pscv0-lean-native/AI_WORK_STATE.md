# PSCV0 AI WORK STATE — Lean-native frontend

**Canonical repository:** [dwijayuda/lean4](https://github.com/dwijayuda/lean4)
**Active branch:** `experiment/pscv0-native-language-closure-v1`
**Parent integration branch:** `experiment/pscv0-native-language-rc4`
**Draft PR:** [#4](https://github.com/dwijayuda/lean4/pull/4) (stacked, do not merge until accepted)
**Target:** ProofScript `pscv0` grammar and semantics, pinned to upstream **Lean 4.35.0-rc4** (`c29b6dda4f7c20e3eeaa717c4e565663c5cfa364`).
**Authority:** `PSCV0_LANGUAGE_REFERENCE.md` copied from the user's latest Lean-first language reference. It is a design target, not implemented conformance.
**Last full green baseline CI:** [38112451935](https://github.com/dwijayuda/lean4/actions/runs/38112451935), commit `75c8a207b718c0f1433c59a76087ae41da68400a`; 37 accepted PSCV0 examples, 56 expected rejections, pinned Standard JSON verification and a Lean-linked native executable all passed. The additional differential/no-artifact tests below require their own green CI before counting as verified.

## Non-negotiable intent
- **Focus only on completing the PSCV0 language and reusing native Lean codegen/proofs.** Do not add TypeScript backends, slim distributions, an independent kernel or new codegen. No regression-work churn in unrelated experiments.
- Use GitHub and cloud CI only. Preserve branch/commit history and concurrent contributions. Read live HEAD immediately before any write; use non-force expected-HEAD leases.
- Think by grammar and elaboration families, not patching individual tests without a semantic explanation. Prefer native Lean parser/elaborator/runtime utilities over duplicate PSCV0 code.
- For user-originated `.ps`, prevent fallback to unselected unrestricted Lean syntax. Preserve no false proofs, no `sorry`/source axioms, no source `unsafe`/`partial`. `UNCERTIFIED` must remain explicit until full verified closure.

## Architecture
- All files in `experiments/pscv0-lean-native`.
- `PSCVL/Syntax.lean`: owned source grammar + hygienic Lean syntax lowering.
- `PSCVL/Grammar.lean`: closed source-category admission, explicit rejection before elaboration; limited and under refinement.
- `PSCVL/Policy.lean`: post-elaboration checks for unsafe/partial/source axioms and allowed proof foundations. Special-cases only official Lean-generated `_unsafe_rec` helpers when the parent declaration is total and safe, because upstream emits them for structurally recursive safe declarations; these helpers are excluded from logical axiom proof checks, NOT certified.
- `PSCVL/Effect.lean`: earlier Lean-grounded experimental effect relations; not yet full coverage.
- `PSCVL/StandardEnv.lean` + `PSCV0_STANDARD_ENV.json`: frozen provisional Lean RC4 import/deriving/eval-scalar selection, whose compiled and checked-in representations match under CI. Not a complete semantic instance/notation digest.
- `PSCVLMain.lean`: CLI `psc check FILE.ps`, `psc syntax-kinds FILE.ps`, `psc build FILE.ps Name output-dir`. The build calls Lean's `runFrontend` and `LCNF.emitC`, writing `.olean` and C, linking via native Lean `leanc` with the generated static PSCVL library. Native execution path tested in CI.
- `tests/pass/*.ps`, `tests/fail/*.ps`, `tests/NativeHarness.lean`: conformance inputs; GitHub workflow `.github/workflows/pscv0-native-language.yml`.
- `PSCV0_LANGUAGE_REFERENCE.md`: authoritative user-supplied target in this branch.
- `CONFORMANCE.md`: live feature evidence/gap ledger.

## Current verified behavior
At full green CI above there were **37 passing `.ps` examples, 56 rejected `.ps` examples, matched compiled Standard environment manifest, and a successful Lean-native binary**. Always inspect HEAD and latest CI before further writes; do not assume future commits remain green.

Language accepted and tested:
`const`, `def`, `function`, comma-binder `theorem`; exact/unit/defaulted `f()`, named/default `f(a, b := c)`, positional and unparenthesized Lean application; braced `if`, dependent `if`, `if let`, `match` with multiple/named/generalized discriminants; Nat successor patterns; structs/classes/typeclasses/inductives/allowlisted deriving; namespaces/sections, private declarations; native `mutual { ... }` and local `where { ... }`; selected tactics and guarded scalar `#eval`/`#check`/`#print axioms`/`#reduce`; `Std`, arrays/strings/quantifiers/subtypes and intrinsic `given`/`requires`/`ensures`, StateM `for` contracts and total verified `while` loops.

Source rejection includes unsafe/partial, axioms/sorry, old `ghost`/`refine type`, unexpected imports, unsupported grammar, bad function call spacing, unbraced `by`/`do`/matching/structures/mutual/where, and **ASCII `.` goal bullets**. Lean defines the ASCII bullet as a native alternative (`Init/NotationExtra.lean`); PSCV0's source validator deliberately rejects it under the `Lean.cdot` AST only, without blocking field projections.

**Latest grammar fix:** RC4's `Lean.Parser.Term.doTry` permits layout-only `doSeqIndent` in `try` and `catch`. PSCV0 now rejects it with `PSCV0-TRY-BRACES`; the positive typed-error example and three negative unbraced variants are tested. A positive/negative `finally` case and complete exception grammar audit remain pending.

## Follow-up instructions
1. Read GitHub live branch/PR/CI first (new commits may exist); identify failing step and root architectural family. Do not chase individual test errors by weakening grammar.
2. Read `CONFORMANCE.md` and reference §13/§14; check upstream 4.35.0-rc4 pinned parser rather than moving `master` code.
3. Implement remaining P0 families and robust positive/negative tests, then full P1 application library/verification rules as needed for stated language target.
4. Keep upstream `master` and external language backend branches untouched. Check expected HEAD before all writes, never force push.
5. Only report completion if full specification-to-conformance matrix and independent language/native tests justify it. Kernel-checked proofs do not certify generated runtime semantics or external effect behavior.

## New work in this checkpoint

- The native harness now proves (with `rfl`, kernel checked) the generated PSCV0 arithmetic definitions correspond to direct reference Lean definitions and executes compiled operations under the official RC4 toolchain.
- Native negative-path CI checks that malformed proof/source and a false StateM postcondition produce neither `.olean` nor C artifacts. The tests were added after the last green baseline and must be re-verified.
- Next key gaps: full `.ps` module/import graph and `public import`, exact function-call/source-position metamorphic corpus, stable full Lean environment identity, additional verification/effect/loop combinations, full proof and erasure obligations. Do not call this spec complete.
