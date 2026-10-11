# PSCV0 conformance ledger — Lean 4.35.0-rc4

**Source of requirements:** [PSCV0_LANGUAGE_REFERENCE.md](PSCV0_LANGUAGE_REFERENCE.md), the user's 2,888-line Lean-first unified language reference dated 2026-10-11. This ledger reflects **implemented/tested functionality**, not mere capability present somewhere in upstream Lean. The Lean runtime and kernel are upstream 4.35.0-rc4 at commit `c29b6dda4f7c20e3eeaa717c4e565663c5cfa364`.

**Last verified checkpoint:** GitHub Actions [38110308510](https://github.com/dwijayuda/lean4/actions/runs/38110308510), commit `e74437f1ee377b1e7f04244257c20bcfa02b46dc` — the PSCV0 parser/frontend, 30 positive tests, 45 expected negative tests, and native linked executable all passed. This is finite example coverage, not complete language conformance.

## Source and semantics matrix

| Area | Verified in our source tests | Missing / not certified |
| --- | --- | --- |
| Lean native type theory & kernel | Lean checks elaborated terms; proof tests and axiom preflight | Differential proof-term comparison at scale; imported environment trust inventory |
| `const`, `def`, `function`, `theorem` | Typed and inferred definitions, named parameters, selected implicit/instance binders, non-explicit default parameters | All declaration modifiers, trailing comma, all native declaration signatures |
| Function application | Adjacent `f(x, y)`, curried `f x y`, named/default arguments, strict `f()` completion including Unit; negative spacing, arity, duplicate/out-of-order/unknown names | Systematic whitespace/trivia, projections, source macro expansion and type-directed elaboration equivalence tests |
| Scopes and visibility | `namespace`, `section`, `variable`, private `const` and `function`, native private theorem | `public import` re-export/visibility and full project module graph |
| Control and patterns | Braced `if`, dependent `if (h : P)`, braced `if let`, `nomatch`, one/two-discriminant `match`, named and generalized match, Nat successor patterns | All dependent indexed patterns, alternate motives, `matches` and patterns in `let`, complete pattern grammar |
| Data | Braced structures and inductives, parameterized structure/class, typeclass `instance`, selected deriving handlers, records, subtype | Indexed/parameterized inductives, every structure/class field form, rest of native `deriving` identity |
| Libraries | Explicit `import Std` only, basic `List`/`Array`/`Option`, `GetElem` with proofs and option lookup, strings and interpolation | Manifest-backed Std submodules/project imports, exact API inventory/digests, typed-world boundary libraries |
| Theorems and tactics | Native braced `by`, `rfl`, `exact`, middle-dot goals, `simp`, `omega`, `grind`, `case`, `next`, `all_goals`, `<;>`, `calc`, `show`, `#print axioms`, `#reduce` | Versioned tactic-extension environment, exhaustive source grammar and goal/info source positions |
| Totality & recursion | Native Lean checking, braced `mutual` and `where`; reject source `partial`, `unsafe`, `sorry`, axioms; Lean compiler-generated `_unsafe_rec` exception for total parent | Systematic structural/well-founded termination, `termination_by` and `decreasing_by` surface tests; compiler runtime-helper semantic assurance |
| Intrinsic verification | Basic RC4 `requires`/`ensures` source example checked | `given`, loops with invariant/decreasing, verified state/reader/error effects, `erased`, full VC closure and verification-only build gate |
| Diagnostics | `#check`, `#print axioms`, `#reduce` | Sound pure-total `#eval` allowlist; source mapping, interactive proof goal tree and IDE parity |
| Compiled native programs | Checked `.ps` to Lean-generated `.olean` and C via `runFrontend`/`LCNF.emitC`; `leanc` linked and ran example | Multi-module packaging, native semantic differential suite, runtime-assumption attestation |
| Verified executable status | No PSCV certificate is issued; output is labeled `UNCERTIFIED` | Complete source/spec/proof/effect/axiom/erasure checks and evidence identity, with blockers on unresolved requirements |

## Conformance rules

- **GREEN** means the corresponding fixture and native pipeline passed against the pinned Lean RC4 CI, *not* that the entire feature family is complete.
- **PENDING** means a required feature is unimplemented or untested. Treat it as absent; never silently interpret arbitrary `.lean` source as valid `.ps`.
- **FAIL** means the compiler accepted malformed source or rejected intended source; correct the grammar family or its policy rather than hiding the case.
- No native executable, user import or proof tactic becomes *certified* merely by succeeding at ordinary Lean checking.
- Every new grammar family must add: at least one positive source test, matching negative tests, exact Lean lowering, proof/axiom checks where relevant, and a native regression.
- The current negative test harness confirms **nonzero exit** for all 45 cases, but also checks exact error IDs for the ASCII `.` bullet and unbraced `try`/`catch` syntax. Extend diagnostic-class checks for other critical negative families.
- The parser's `choice` alternatives and pinned token/notation environment need a dedicated source grammar audit. Current selection relies on a finite allowlist and recursive token restrictions; this is **not** proven complete or a security sandbox.

## Typed exception syntax checkpoint

Lean RC4 permits both indented and braced `doSeq` in the `doTry` parser family. PSCV0 selects braces for `try` and `catch` bodies; the frontend validates the native AST before elaboration, reports `PSCV0-TRY-BRACES`, and retains Lean's typed `Except` elaboration. `typed_error.ps` and `throw_typed.ps` pass; `typed_error_unbraced.ps`, `typed_error_try_unbraced.ps`, and `typed_error_catch_unbraced.ps` must reject. `finally`, nested exception-handler grammar, and full typed effect/assumption closure remain incomplete.

## Immediate acceptance priorities

1. Stabilize type-directed empty calls and mixed named/default arguments with metamorphic elaboration tests.
2. Finish explicit module/import closure, including `public import` and trusted `.ps`-built module identities, using Lean's native import parser.
3. Support P0 language constructs still absent: `matches`, let patterns, recursive/equation-style declarations, all agreed brace ownership, pure-total `#eval`, indexed inductives/structures, and RC4 verified `do`/loops.
4. Pin a machine-readable standard-environment manifest of allowed `Std` modules, deriving handlers, attributes, tactic registrations, defaulting and instances. Include a digest and negative checks for unpinned expansion.
5. Enforce full assurance profile only after exact cross-module proof, effect, assumption, noncomputable and erased obligations are traced and checked. Until then, remain `UNCERTIFIED`.
6. Measure source-to-source Lean semantic correspondence, source ranges, compile/link behavior and cost without adding independent backends.

**Explicit non-goals for this branch:** TypeScript/JavaScript/WebAssembly/Rust backends, a slim Lean distribution, independent PSKernel work, changes under `src/` or `stage0/`, or claiming verified runtime semantics from these finite tests.
