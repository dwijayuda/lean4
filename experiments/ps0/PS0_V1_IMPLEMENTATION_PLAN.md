# PS0 v1 — Canonical Implementation Plan

**Only normative language authority:** [PS0_V1_LANGUAGE_REFERENCE.md](PS0_V1_LANGUAGE_REFERENCE.md), uploaded R2 file, exact Git blob `c50203f8e4cb79b3e6680088a07c1d1e145b8f0b`.

**Pinned semantic basis:** official Lean 4.35.0, commit `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`. No PSCV0 v7 compatibility, fallback or borrowed implicit assumption policy. Language acceptance is not verified-program qualification.

## Architectural invariants

- `.ps` uses PS0 v1 grammar with native Lean capabilities and its explicitly owned surface rules; `.lean` stays unrestricted Lean.
- Lean owns elaboration, kernel, typeclasses, recursion, metaprogramming and native codegen. PS0 owns category-aware source translation, evidence reporting and backends.
- Native `unsafe`, `partial`, `axiom`, bodyless `opaque`, `sorry` during development, IO, custom syntax, `meta`, dynamic attributes, deriving, native instance bodies, fixed points and diagnostic commands are LANGUAGE CAPABILITIES, never blanket source bans. A stronger *verification claim* must justify its actual assumptions and runtime/effect boundaries.
- Source imports, stage and scope derive from the pinned modern Lean module implementation. Headerless `.ps` uses implicit modern modules/public names by default; written `module` uses native defaults, `prelude` suppresses implicit Init, and body exposure is distinct from public naming.
- Imported/user registrations extend the grammar; no finite initial-grammar command/tactic/attribute whitelist may define v1.

## Fastest critical path

### G0 — Qualify a complete standalone build

Compile the PS0 Lake package with the exact Lean pin. Run v1 ordinary source tests for axioms, partial, unsafe, effectful evaluation, user macros, native value instances, and declared development holes. Verify `.lean` stays entirely native. Repair actual compiler errors by architectural family.

### G1 — Core PS category ownership and lowering

Extend the new native-capture foundation `psTerm`, `psCommand`, `psTactic`, `psDoSeq` and `PS0.Syntax.lower` with actual PS-owned host lowering. Preserve native syntax quotations, distinct DSL categories, and token/source spans. Extend the newly migrated typed/inferred public/private `function`/`const` `psTerm` body adapters through the remaining standard operand slots (native declarations, theorem/type/binder, tactic, `do`, contracts, configuration and imported standard expressions). It already constructs a native Lean application from owned positional/named arguments and preserves native syntax subtrees, but does not cover arbitrary postfix heads, source-nullary calls, trailing commas or all standard host entry positions. Then complete strict gap/tuple/Unit completion, type-directed defaults, quotation ownership, and the standard operand-slot registration map. No regex transpiler, typechecker fork or silent native fallback.

### G2 — Full declaration, data, recursion, proof and effect families

Adapt native/comma mixed binders without losing order, defaults or automatic parameters. Finish record-vs-body brace ownership, structures, classes, field binders, native deriving and instance forms. Adapt dependent pattern syntax and full total/partial/fixed-point recursion. Support native and braced proof/do/layout, loops, monadic if-let, forwarding do, contracts, erased state, FFI and metaprogramming via Lean's original machinery.

### G3 — Modules and effective environment identity

Build the full module dependency graph: current check/native build now use official modern Lean headers and imported stages, but source-file kinds, .ps import resolution, cycle/path rejection, complete public-name/body exposure and native `@[expose]` distinctions still need qualification. Preserve explicit/implicit module defaults; never inject implicit prelude into a `prelude` source. Record applicable imported registries, axioms, source hashes and effective options.

### G4 — Qualified evidence and runtime backends

Keep ordinary checking distinct from theorem evidence, source verification and execution-correspondence verification (spec ``0A, 12). Require explicit approval policy/claim before issuing stronger labels; account for transitive assumptions, holes, erasure, effects and extern/runtime replacements. Grow Lean-implemented JS backend through typed IR, with explicit semantic-preservation evidence; do not infer verified JS from Lean source proof alone.

## New normative coverage ledger

[v1-coverage.json](v1-coverage.json) contains **100** capability-review families (Appendix A), **64 positive** source/evidence examples, **47 negative** source/claim cases (`13), and **31** R2 concrete witnesses (Appendix D), **242** traceable items in total. Every item is initially `PENDING`. A `PASS` must record an exact PS0/Lean/reference source identity, relevant fixture, intended semantic/diagnostic oracle and executed CI evidence. The former v7 181-case acceptance count and 41% estimate are obsolete; neither is inherited.

Work in draft PR #5, preserve history and the independent PSC0 and historical PSCVL compilers. Record precise gaps in [CONFORMANCE.md](CONFORMANCE.md) and progress in [AI_WORK_STATE.md](AI_WORK_STATE.md). Implement coherent language families, not scattered test patches.
