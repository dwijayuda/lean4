# PS0 stable-Lean acceptance and follow-up

## Implemented starting point

| Dimension | Current evidence/implementation |
| --- | --- |
| Identity | Independent `ps0` CLI/package in the Lean fork |
| Source | Original `.ps` bytes retained; existing PSCVL grammar and hygienic macros used by reference |
| Elaboration | Lean 4.35.0 stable elaborates and checks terms; no second custom type checker |
| Proof | Lean tactic elaboration and official kernel, including explicit `#pscv_gate` preflight |
| Native artifact | Upstream `Lean.Elab.runFrontend` and `Lean.Compiler.LCNF.emitC`; uncertified `.olean`/C only |
| Pin | `leanprover/lean4:v4.35.0` plus runtime check for `eb6cafb7290e8bd5f2937522d8d804f58f02bafc` |
| Isolation | PSC0 in `dwijayuda/pskernel` untouched; existing PSCVL experiment retained |

The inherited RC4 experiment previously passed 37 positive and 56 negative
source cases and produced a native executable. Those historic receipts do
**not** qualify the new stable-Lean PS0 package. New branch CI must pass
before claiming stable-Pin parity.

## Exit criteria to finish this implementation

- [ ] Stable 4.35.0 `ps0` CI: all selected positive/negative `.ps` fixtures
- [ ] Stable 4.35.0 `.olean`/C production, rejection without new artifacts
- [ ] Native link/execute representative `.ps` program
- [ ] Full v7 syntax category and forbidden-syntax closure (no arbitrary Lean escape)
- [ ] Complete module/public-import and pinned environment semantics
- [ ] Complete v7 `given/requires/ensures`, verified `do`, termination and effects
- [ ] Source/Lean Core correspondence, origins/IDE diagnostics, proof/erasure coverage
- [ ] Separate verified-executable certification and runtime-correctness evidence

**Explicit claim boundary:** A green initial CI establishes a native,
Lean-checked *subset*. It does not certify v7 completeness or formally
prove correct native execution.
