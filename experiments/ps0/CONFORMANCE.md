# PS0 standalone Lean 4.35.0 v7 conformance and migration ledger

**Branch:** `feature/ps0-lean435-stable-v1`. **Goal:** standalone PSCV0 v7 `.ps` compiler with official Lean 4.35.0 elaborator/kernel/native backend. **Status:** implementation committed, new stable CI not yet verified. Do not count previous RC4 results as stable-PS0 qualification.

## Review of migrated modules

| Module | Adaptation, not an unchanged copy | Remaining acceptance |
| --- | --- | --- |
| `PS0/Syntax.lean` | Own namespace/syntax registration, type-directed calls; nullary Unit sugar **only for function**, not def/theorem/ctor; non-callable `f()` rejected | Full v7 source grammar and call correspondence |
| `PS0/Grammar.lean` | Own selected command kinds, conservatively require **all** ambiguous command alternatives to satisfy allowlist rather than accepting any one | Full resolved-alternative/expansion audit; measure possible legitimate rejections |
| `PS0/Policy.lean` | Own `#pscv_gate` and registered attributes; retain explicitly disclosed `Classical.choice` in inherited permitted foundations | Complete imported axioms/verification coverage/effect/erasure |
| `PS0/Effect.lean` | Own Lean-grounded `Std.WP` pure/ReaderM/StateM/Except semantics and proof theorems | Full verified effect cases and external world capability contracts |
| `PS0/StandardEnv.lean` | Own stable 4.35.0 identity and provisional module/deriving/eval manifest | Full registries, instance/notation/tactic/effect/module digests |
| `PS0Main.lean` | Local PS0 imports only, one source read and one authoritative native Lean elaboration; staged C/olean bundle published by same-filesystem directory rename | Immutable project/environment graph digest, path-race controls and release claim manifest open |
| `lakefile.toml`, CI | No sibling `require`; workflow checks out only `experiments/ps0` and links `PS0:static` | Confirm independent exact-commit Lean stable build and native execution |
| `tests/` | PS0-owned positive/negative source fixtures, original native correspondence harness adapted; new call tests | Not full inherited 37 positive/56 negative corpus or complete v7 rule matrix |

The original `experiments/pscv0-lean-native` experiment was restored to its RC4 state on this PR branch. The independent `dwijayuda/pskernel` PSC0 compiler and PR #109 remain unchanged.

## Existing bounded capabilities and open requirements

| Area | Implemented slice | Missing final v7 closure |
| --- | --- | --- |
| Source language | `function`/`const`, selected dependent calls, data/matches, braced proofs/control, macros lowering to Lean syntax | Complete `0B` source/category grammar and all `13`/`14` acceptance cases |
| Logical meaning | Official Lean elaborator and kernel, Lean-native tactics and termination | Full Lean-Core translation correspondence evidence for each surface feature |
| Project/imports | Selected native Std import allowlist | `.ps` module/public-import graph, public default names/opaque body mapping |
| Standard environment | Stable pin + provisional local JSON | Tokens, notation, instances, deriving, tactics, capabilities, axioms and API inventory |
| Verification | Local source axiom/unsafe/partial/sorry preflight; selected `Std.WP` contracts | Full generated and imported VC/spec/effect/assumption/erasure coverage and certificates |
| Native build | One Lean `runFrontend` checks the source and produces C/olean in private staging; published output cannot silently overwrite a prior bundle | Full multi-module identity/provenance, race-resistance, native preservation evidence remain |
| Tooling | CLI source errors and PS syntax | Original `.ps` InfoTree spans, LSP, formatter, readable Lean/PS source views |

**New conformance regression cases:** `tests/fail/noncallable_empty.ps` must reject a Nat value used as `answer()`; `tests/fail/def_nullary.ps` must reject source `def name()`. `tests/pass/unit_alias.ps` checks definitionally Unit empty calls and `default_empty.ps` checks optional parameter completion. All new cases must pass exact native Lean stable CI before being considered qualified.

## Current milestone gates

- [ ] Stable 4.35.0 PS0 native build and checked CI for this exact HEAD.
- [ ] PS0-only sparse checkout and no sibling source dependency.
- [ ] Source positive and phase-specific negative cases, including ambiguous syntax and nullary semantics.
- [ ] Local Standard JSON matches PS0's environment.
- [ ] Invalid source/proof blocks output and native example compiles/links/runs.
- [ ] Port and adapt missing historical 37/56 source cases as appropriate, with phase-specific diagnostics.
- [ ] Complete PS0-01..PS0-11 in the [full v7 plan](PS0_FULL_PSCV0_V7_IMPLEMENTATION_PLAN.md).

Do not label standalone build, bounded CI or native source kernel acceptance as full PSCV0 v7, verified source contract closure, or verified machine semantics.
