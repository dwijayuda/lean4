# PS0 — standalone Lean-backed PSCV0 v7 compiler experiment

**Status: independent, selected-v7 Lean-native frontend. Not full v7, not a verified-executable certificate.**

PS0 is an independently buildable Lake package in `experiments/ps0`. It keeps
authoritative `.ps` files, the selected ProofScript surface grammar, and the
official Lean 4.35.0 stable elaborator/kernel/native compiler. It **does not
depend on `../pscv0-lean-native` or on `dwijayuda/pskernel`** at build time.

**Historical provenance:** the earlier PSCVL Lean-native experiment at
`experiment/pscv0-native-language-closure-v1` provided the reviewed starting
point. Its five implementation modules were **adapted**, not copied as an
untouched opaque dependency; the original experiment remains unchanged.

## Two source modes — v7 restrictions apply only to .ps

**`.ps`: PSCV0 v7 profile.** The selected syntax/grammar, source bans,
`#pscv_gate`, permitted imports and verification requirements apply.

**`.lean`: full ordinary Lean 4.35.0.** No PSCV0 source restrictions.
PS0 invokes the official Lean sysroot executable in a separate process so
ordinary Lean `unsafe`, `partial`, `axiom`, `sorry`, imports, tactics,
user macros and unrestricted native `#eval` behave as Lean defines them.

```sh
lake exe ps0 check tests/pass/basic.ps               # v7-checked ProofScript
lake exe ps0 check tests/lean/unrestricted.lean      # unrestricted Lean
lake exe ps0 lean tests/lean/unrestricted.lean       # exact native Lean pass-through
lake exe ps0 build tests/lean/unrestricted.lean NativeUnrestricted build/lean-native
```

The command `ps0 lean ...` passes all arguments to the official Lean CLI
without parsing or translating source in PS0. Native `.lean` compilation
does not automatically receive a ProofScript source-verification certificate.

See [SOURCE_PROFILE_BOUNDARY.md](SOURCE_PROFILE_BOUNDARY.md) for the full
language/trust-boundary contract, including future mixed `.ps`/`.lean`
project imports. **The v7 completion percentage counts only `.ps` features.**

## Small scalable JavaScript backend (written in Lean)

PS0 now includes a deliberately narrow `build-js` backend, implemented
exclusively through Lean modules, not a JavaScript/.mjs transpiler.
It typechecks and applies the existing `.ps` policy before emitting:

`lake exe ps0 build-js tests/js/nat_mvp.ps NatMvp build/js-nat`

The resulting bundle contains `NatMvp.js` (ESM), `NatMvp.d.ts`
(TypeScript declarations), and `NatMvp.js.map` (Source Map v3,
signed Base64-VLQ declaration mappings). The initial runtime fragment
is publicly exported `Nat` constants and selected `Nat` functions
(literals, explicit Nat parameters, `+`, `*` and saturating `-`).
`Nat` values are exact JS `bigint` and runtime inputs are guarded as
nonnegative bigints. Everything else — including module imports,
effects, patterns and JS platform interop — is explicitly unsupported
rather than guessed.

The architecture separates source AST lowering, typed portable
runtime IR, JS/TS emission, and source-map construction under
`PS0/Backend/Js/*.lean`. The files are atomically staged and
publication refuses overwrites. Future typed IR cases can add
ADTs, calls, total recursion and audited effects without replacing
the backend. See [PS0_JS_BACKEND_MVP.md](PS0_JS_BACKEND_MVP.md)
for feature boundaries, assurance caveats, CLI and expansion plan.

**Qualification:** CI includes generated Node BigInt execution,
`.d.ts`/source-map validation, deterministic output and negative
tests, but a successful exact-commit Lean 4.35.0 run has not been
independently observed. This is ordinary checked-source emission,
**not** a proof of JS semantic preservation or a verified JS backend.
The existing v7 **language** completion score is not increased
by adding a separate backend. Native `.lean` remains unrestricted.

## Owned source layout

| Source | Responsibility |
| --- | --- |
| `PS0/Syntax.lean` | ProofScript-specific function/const syntax, calls, braces and contracts lowered through hygienic Lean syntax |
| `PS0/Grammar.lean` | Closed command-family source validation and forbidden syntax/attribute checks; ambiguous command choices are conservatively refused unless all alternatives qualify |
| `PS0/Policy.lean` | Post-elaboration kernel/axiom preflight, selected diagnostic `#eval`, candidate root validation; not full verified-output coverage |
| `PS0/Effect.lean` | Lean-grounded pure/reader/state/typed-error relations and WP theorems |
| `PS0/StandardEnv.lean` | Stable Lean pin and provisional curated import/deriving/eval environment |
| `PS0Main.lean` | Standalone `ps0` CLI, source preflight and official Lean native emission |
| `PS0_STANDARD_ENV.json` | Exact local provisional environment snapshot |
| `tests/` | PS0-owned positive/negative source and native executable correspondence fixtures |

`lakefile.toml` has one local `lean_lib PS0` and `lean_exe ps0`, **no
`require` dependency**. The CI uses a **PS0-only sparse checkout**, verifies
the sibling source tree is absent, builds the library and executable, runs
positive/negative fixtures, checks emission refusal, and links/runs a native
program with the local `PS0:static` library.

## Design changes made during the migration

- Namespaces, imports and source validator category names now belong to PS0.
- The older PSCVL experiment stays pinned to its original RC4 version on its
  own branch, while PS0 uses official stable Lean 4.35.0 commit
  `eb6cafb7290e8bd5f2937522d8d804f58f02bafc`.
- Empty source binder groups only insert a `Unit` parameter for nullary
  **`function`**, not ordinary `def`, `theorem` or constructors.
- `f()` rejects non-callable values and delegates default/definitionally
  `Unit` resolution to Lean. New positive/negative fixtures cover this.
- Ambiguous command parse alternatives are **all required** to satisfy the
  closed command policy, rather than accepting whenever one happens to be
  allowed. This is deliberately conservative and may need finer resolution
  during PS0-01 grammar closure.
- `build` reads its user `.ps` source bytes **once**, validates source syntax,
  and uses one official `runFrontend` elaboration for policy checking and C/olean
  emission. Output is produced in a same-filesystem sibling staging directory
  and atomically renamed into the requested **previously absent** bundle
  directory only after both outputs exist. Existing bundles are never overwritten.
  Complete module/environment identity, race-resistant path policy and a signed
  claim manifest remain PS0-09 work.

These are bounded improvements, **not** an assurance proof, complete grammar
closure, semantic correspondence theorem, or a security sandbox.

## Build and check

```sh
cd experiments/ps0
lake build PS0 ps0
lake exe ps0 environment
lake exe ps0 syntax-kinds tests/pass/basic.ps
lake exe ps0 check tests/pass/basic.ps
lake exe ps0 build tests/pass/native_math.ps NativeMath build/native
```

The last command uses one official `Lean.Elab.runFrontend` /
`Lean.Compiler.LCNF.emitC` and produces `.olean` and C (both **UNCERTIFIED**).
The CI also tests native linking/execution using the PS0-owned harness.
The source's `partial`, `unsafe`, `axiom`, `sorry` and unselected syntax
are refused in supported cases; this does not yet establish all transitive
source/ABI/effect/erasure conditions.

The inherited assumption policy currently admits `Classical.choice`,
`propext`, and `Quot.sound`; do not conflate it with PSC0's portable
`propext`/`Quot.sound` policy. Full environment locking, imports/public
modules, IDE source maps, complete verification and binary publication are
future milestones. **Lean source proofs do not prove native machine-code
semantic preservation**.

## Current v7 declaration progress

The PS0-owned source grammar now includes **return-type inference** for `def`,
`function`, private `function`, and implicit/instance-headed functions, all
lowered to official Lean definitions rather than independently typechecked.
The new `pscvTelescopeSegment` accepts source binder telescopes with ordered
explicit comma groups separated by implicit, strict-implicit or instance
groups, preserving native Lean dependency and instance elaboration. Two
adjacent explicit groups are rejected under `PSCV0-BIND-02`, including the
selected native `def`/`theorem` alternatives in a `.ps` source.

Examples are in [inferred_signatures.ps](tests/pass/inferred_signatures.ps)
and [interleaved_binders.ps](tests/pass/interleaved_binders.ps); a separate
[native Lean reference](tests/lean/v7_signature_reference.lean) exercises the
corresponding native semantics. New forbidden-group fixtures test both
source-owned and native declaration parsing. This raises the binder family's
**estimated readiness from 2/5 to 3/5**, but does not record any new
CI-qualified v7 requirements: a stable exact-commit CI receipt is pending.

## Implicit PSCV0 v7 module headers (PS0-03 foundation)

The v7 source specification does **not** require users to write `module`
in a `.ps` file: every `.ps` file is **implicitly** a native Lean module.
`import M` is module-private; `public import M` exports the public
scope of M. To avoid Lean's *legacy* transitive-import semantics, PS0
uses a synthetic `module\n` **only in the official Lean header parser**
and subtracts that prefix from the source byte offset before any body
admission. Literal `module` in a `.ps` source is refused.

```sh
lake exe ps0 module-header tests/headers/modern_imports.ps
```

This returns an inspectable JSON of Lean's actual import flags
(`isExported`, `isMeta`, `importAll`) and marks
`"compile_ready": false`. Positive inspection of `public import`
**does not** authorize compilation: public names, hidden definition
bodies, project graph imports and deterministic environment identity
are still pending. In particular, `ps0 build` now rejects `.ps`
source modules with imports rather than accidentally publishing
legacy Lean re-export behavior. Ordinary `.lean` remains unrestricted.

Tests cover plain/private and exported/public import flags, meta
classification, forbidden literal module headers, and UTF-8 source
body boundaries. No exact-commit stable Lean CI receipt is available.

## Braced v7 instance declarations

The source profile now adapts selected `instance : C where { ... }` and
`instance chosen : C where { ... }`, including ordered binder
telescopes and native Lean priority annotations such as
`instance (priority := high)` or `instance (priority := 750)`,
to the equivalent official Lean typeclass declarations.
`.ps` requires genuine braced fields; native `.lean` keeps its broader
instance syntax, including `instance : C := value`.

See `tests/pass/instance_braced_fields.ps`, corresponding native
`tests/lean/instance_reference.lean`, and
[CONFORMANCE.md](CONFORMANCE.md). This implementation is currently
**unqualified until exact-commit stable-Lean CI**. The source priority syntax now has a finite allowlist (low/mid/default/high
or a decimal literal) mapped into Lean's native priority grammar. The
frozen instance/typeclass registry and successful stable CI qualification
remain pending.

## Language-feature completion estimate (October 15, 2026)

PS0 reports **41% estimated v7 language-feature readiness** across
20 equally weighted source/semantic feature families. This is a subjective,
evidence-linked implementation-readiness rubric, **not** measured code coverage
or language acceptance. Strict normative v7 qualification remains
**0/181 (0%)**, because an exact-commit stable Lean 4.35.0 CI pass and full
per-case evidence are not available.

The breakdown is: source/declarations/calls/scopes **52% (13/25)**;
types/data/conditionals/patterns/recursion **46% (16/35)**;
proofs/do/contracts/effects **40% (8/20)**; and modules/selected libraries/
environment/assurance **20% (4/20)**.

See [language-feature-progress.json](language-feature-progress.json) for
the per-family score and grounded code paths. PS0 CI executes
`node scripts/report-language-progress.mjs`; the stricter
[v7-coverage.json](v7-coverage.json) maintains all 150 normative source
cases plus 31 audit requirements as PENDING until real exact-commit evidence
is recorded. New `matches`/`if let`/`nomatch` fixtures are *candidate*
tests only and do not by themselves increase qualified completion.

## Implementation roadmap

The [full v7 research and execution plan](PS0_FULL_PSCV0_V7_IMPLEMENTATION_PLAN.md)
defines PS0-00 through PS0-11, including source grammar/Lean-Core conformance,
modules, Standard, contracts, effects, checked sessions, IDE and release gates.
[CONFORMANCE.md](CONFORMANCE.md) records the current limited evidence and gaps.

Current isolated PR: [dwijayuda/lean4 #5](https://github.com/dwijayuda/lean4/pull/5),
draft, not merged. The independent PSC0 multi-backend compiler and PR #109
remain separate and untouched.

## Normative v7 conformance inventory

The [machine-readable v7 inventory](v7-coverage.json) extracts the 150 named
`13` acceptance/refusal cases from the pinned PSCV0 v7 source reference
(72 positive, 78 negative), plus 4 E1–E4 errata, 22 F01–F22 findings and
5 C01–C05 corrections. The local [validator](scripts/validate-v7-coverage.mjs)
checks integrity and fixture provenance:

```sh
node scripts/validate-v7-coverage.mjs
node scripts/validate-v7-coverage.mjs --require-complete  # expected to refuse today
```

All 181 named rows currently remain **PENDING**. Selected source examples
have candidate fixture links, **not** verified PASS status. A PASS must cite an
actual fixture, required negative diagnosis, exact commit and CI run. CI now
checks the registry integrity but does not falsely demand full v7 acceptance
from the current bounded native frontend.
