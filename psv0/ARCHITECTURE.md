# PSV0 architecture decisions (draft 2026-11-17)

## Isolation

PSV0 lives only in \`psv0/\` and is not a dependency of or replacement for PS0. Future experiments are separate opt-in modules and branches.

## Trusted boundary

PSV0 fast emission accepts only the explicitly bounded grammar. The parser, IR generation and printers remain untrusted until their semantics are proved. The exact parse result is now retained as a hashed `.ir.json` artifact. \`strict\` invokes official Lean as a checker of *generated Lean* and optionally a user-supplied theorem. Neither Lean acceptance nor target compilation proves cross-language semantic preservation. Full \`verified\` must refuse until a separate evidence-checking path is implemented.

## Semantic obligations

Define \`SemPS(source)\`, \`SemIR(ir)\` and \`SemTarget(target, runtime)\` as actual formal semantics and establish the following relations for exact source and output artifacts:

1. Source lowering: \`SemPS(source) ≃ SemIR(ir)\`.
2. Lean elaboration: generated Lean's elaborated declaration faithfully denotes the corresponding source/IR meaning.
3. Extraction: an independently checked correspondence theorem ties exact Lean declarations to selected IR roots.
4. Target emission: emitted target AST's modeled behavior refines IR behavior, including resource, error and effect conditions.
5. Serialization and runtime: target bytes denote that AST and the versioned deployed runtime realizes the formal model, or any residual assumptions are explicitly recorded.

Type-checking TS or checking Lean independently is necessary in selected profiles but insufficient for (1)-(5). Source, proof challenges and exact receipts must be bound by cryptographic digests; source macros/elaborators and arbitrary proof scripts may execute code during elaboration and require sandboxing.

## Fast path

A bounded parser and deterministic emitters run without Lean. Unsupported constructs fail closed; no fake trusted status is attached. Shared language-neutral AST is intentionally small and will be converted to a typed IR once explicit source semantics exist.

## Strict path

Generate candidates privately, independently run Lean, then compile/check targets. A separate publisher enforces all required checks, never invents results, and does not create the requested destination on failure.

## Scope

V0 intentionally supports only first-order pure Nat arithmetic, to make precedence, Nat saturating subtraction and BigInt representation explicit. Preserve generated TypeScript as a real implementation, not just a declaration file. Rust is a planned target, not an output advertised by the current CLI.

## Non-goals

No Lean fork-wide compiler changes, no PS0 modifications, no full Lean surface fidelity, no target runtime verification, no arbitrary FFI, no byte-identical generated executable claim, and no silent downgrade from verified to checked.

## Evidence status

A local Node 22 run passed 4 unit tests of the standalone reference evaluator and bridge renderer. The differential and CLI regression tests are committed, but no successful full-suite or Lean build is claimed. The separate PSV0 CI workflow runs Node regressions and requests a pinned Lean 4.35 reference-model build plus strict-mode check. GitHub Actions receipts must be inspected before qualifying either lane. The published `manifest.json` intentionally keeps `source_to_lean_equivalence_proven` and `target_semantics_proven` set to `false`.
