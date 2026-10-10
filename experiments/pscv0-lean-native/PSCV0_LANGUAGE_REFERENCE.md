# Lean 4 ↔ ProofScript `pscv0` — Lean-First Unified Language Features, Syntax, Grammar, and Examples

**Status:** Revised `pscv0` language-feature specification and side-by-side research reference — **design target, not evidence of compiler conformance** · **Revision focus:** richer selected native Lean programming/proof features, practical application-library capabilities, one-language/two-assurance outcomes, and restrained TypeScript migration ergonomics · **Edition:** `pscv0` (one language identity) · **Lean pin:** [`v4.35.0-rc4`](https://github.com/leanprover/lean4/releases/tag/v4.35.0-rc4), commit `c29b6dda4f7c20e3eeaa717c4e565663c5cfa364` · **Revision date:** 2026-10-11 · **Upstream release status:** prerelease (the newest published Lean release candidate on this date; newest stable is 4.34.1).

**Source provenance:** This revision derives the ProofScript feature choices from the uploaded *ProofScript PSCV Language Reference NORMATIVE RC-v2 (Lean 4.35.0-rc3)* and the preceding side-by-side `pscv0` document. **New decisions** in this edition (nullary function lowering, command adoption, type catalog, parser safeguards, native `Nat` successor pattern admission, Lean section-variable fidelity, and IDE parity goals) are marked as proposals rather than silently attributed to that earlier RC. The *actual* Lean syntax/semantics pin for the revised language is RC4.

> **Design identity — precise subset statement.** **ProofScript `pscv0` is designed as a *semantic subset of Lean 4*, with a small owned application-friendly surface syntax.** Every admitted `pscv0` form must elaborate/desugar to ordinary well-typed Lean terms, declarations, proof terms or Lean-grounded verified-effect/library specifications. ProofScript is **not a character-for-character subset of Lean's source grammar**: `function`, `const`, comma-argument calls `f(x, y)`, and braced control forms are intentional surface modifications; Lean-native `erased`, `Subtype`, proof bullets, and quantifiers are retained unchanged. They do **not** define a second type theory or proof kernel.
>
> **Assurance interpretation.** One `pscv0` source language admits ordinary type-checked programs and more strictly verified-executable programs. This is a difference in checked evidence and emission claims, **not** separate logical languages. Proof terms and declaration typing always require kernel-compatible checking; external effects never prove their own implementation merely by being typed. `partial`/`unsafe` stay excluded from ordinary `pscv0` source pending a separately justified non-certified boundary facility.
>
> **Scope.** Language features, syntax, grammar, examples, and the static meaning necessary to distinguish valid source. Excludes implementation architecture, CLI, package formats, release gates, build certificates, deployment and AI work management. The original uploaded release candidate retains its historical identities; the new name **`pscv0` is the user's proposed revision**, not an upstream Lean edition or an assertion that a compiler implements it.
>
> **Grammar policy (revised).** **Lean 4 grammar is the one grammar model used throughout this document.** Both comparison columns now use Lean’s grammar-reference categories and *schematic* syntax (`command`, `term`, `binder`, `tactic`, `doSeqItem`, `structField`, `structInstField`). A `pscv0` syntax rule is presented only as a **Lean grammar selection, restriction, or punctuation/layout transformation**. This **discontinues** the previous separately specified ProofScript EBNF model: the new document references Lean syntax categories and states only `pscv0` surface deltas. It retains a finite *selection* of Lean features without claiming the full Lean language is accepted. Lean’s actual parser-combinator declarations at the pinned commit—not a reconstructed standalone EBNF—define the upstream categories. ProofScript’s new tokens are not natively accepted by Lean until transformed; examples are design illustrations unless explicitly tested.

## Executive syntax map — one rule per ambiguity

**Design rule:** follow Lean 4.35.0-rc4 unless ProofScript syntax delivers clear programming ergonomics; for the few syntactic modifications that remain, allow **one canonical `pscv0` spelling** for ambiguous constructs. Lean `.lean` files keep normal Lean source syntax unchanged.

| Concern | Native Lean 4.35.0-rc4 | `pscv0` choice | Status |
|---|---|---|---|
| Ordinary definition | `def f (x : A) : R := t` | `def f(x: A): R := t` | admitted; Lean semantics |
| Named programming function | `def f (x : A) : R := t` | `function f(x: A): R := t` | keep ergonomic alias |
| Named value | `def x : A := t` | `const x: A := t` | keep parameterless alias; not JS `const` |
| Source call | `f x y` | `f(x, y)` for call punctuation; **also retain** `f x y` as native unparenthesized mathematical application | no change to Pi/application semantics |
| Parenthesized-argument gap | `f (x)`, `f (x, y)`, `f ()` are Lean applications | **reject all three in `.ps` application positions**; use `f(x)`, `f((x, y))`, `f(())` | grammatical restriction, not an indiscriminate whitespace ban |
| Typed binder parentheses | `variable (n : Nat)`, `def f (n : Nat)`, `fun (x : Nat) => ...` | **accept** selected native Lean binder syntax; these are NOT term applications | preserve Lean scopes, dependent binders and proofs |
| Standalone grouped terms | `#check (f x)`, `exact (hp)`, `(1 + 2 : Nat)` | **accept**; `(` begins an expected term and does NOT follow a completed application head | avoid false positive diagnostics |
| Uniformity across contexts | `#check f (x)`, `exact h (p)` may be Lean applications | **reject in `.ps`**, just like executable code; `#check f(x)`, `exact h(p)` | one `.ps` term grammar for code and proofs |
| Empty call | Lean uses a value such as `f ()` or default insertion | `f()` only means zero explicit source arguments, with narrowly defined completion | zero-argument syntax; not `f ()` |
| Unit argument | `f ()` | `f(())` | one explicit Unit spelling in `.ps` |
| Tuple argument | `f (x, y)` | `f((x, y))` | one tuple-argument spelling in `.ps` |
| Nullary declaration | `def f (_ : Unit) : R := t` | `function f(): R := t` | required Unit lowering, no second runtime arity |
| Conditional | `if p then a else b` | `if (p) { a } else { b }` | one canonical `.ps` expression form |
| `match`, `do`, proof, declarations | Lean layout-sensitive bodies; braced alternatives may be available | choose precisely defined **braced bodies** in `.ps` | no duplicate indentation-only form for those bodies |
| Proof branches | `· exact hp`, `case ... => ...`, `next ... => ...` | **same native Lean syntax inside `by { ... }`** | no ASCII `.` bullet alias |
| Proof relevance | Lean `erased`, `erased mut`, `erased x ← action` | **exactly `erased`**, not `ghost` | native Lean RC4 vocabulary |
| Refined values | Lean `Subtype`, `{x : A // P x}` | **same `Subtype` and `{x : A // P x}`** | no `refine type` declaration |
| Data invariants | Lean structure proof fields | explicit **proof fields** inside `structure ... where { ... }` | no trailing `invariant self =>` sugar |
| Verification proof attachment | Lean theorem / checked proof / `vcgen` | `theorem`, `by { ... }`, selected `vcgen` | no `verify target :=` alias |
| Contracts and assertions | RC4 experimental `given`, `requires`, `ensures`, `assert`, loop `invariant`/`decreasing` | same Lean heads with PSCV totality/proof restrictions | selected native forms |
| Mathematics | `∀`/`forall`, `∃`/`exists`, `λ`/`fun`, `→`/`->`, and standard notation | retain **both genuine Lean aliases**, because they are already one meaning and useful for math | no fabricated `exist` keyword |
| Successor patterns for `Nat` | `| k + 1 => ...`, `| .succ k => ...`, `| k + 2 => ...` | **accept native Lean successor-pattern sugar**; prefer `k + 1` in arithmetic examples | `1 + k`, arbitrary variable addition, and subtraction are not constructor patterns |
| Shared theorem/program parameters | `section`, `variable (n : Nat)`, `variable {α : Type}` | keep **Lean `variable`** with exactly its binder visibility and section generalization | not a mutable/local runtime variable; not redundant function sugar |
| Lean interactive proof development | `#check`, tactic goals, `#print axioms`, `#eval` | support selected commands and expose cursor-position proof state in the editor | language syntax and IDE capabilities are separate from verified acceptance |
| Inspecting code | `#check`, `#eval`, `#reduce`, `#print`, `#print axioms` | identical selected commands; pure-total `#eval` only | diagnostic, not proof authority |
| Type foundation | `Prop`, `Type`, `Sort`, `Nat`, `Int`, `UInt8`... `Subtype`, `Fin`, `List`, `Array`, etc. | same Lean type names and semantics | explicit inventory in §8 |
| Pattern matching | Multi-discriminant, dependent/generalized match, `if let`, `nomatch`, pattern `let`, `matches` | adopt selected Lean grammar and checked eliminator semantics; canonical `.ps` braces where applicable | expanded `pscv0` baseline (§3, §4) |
| Deriving | Lean native `deriving` handlers | allow selected **pinned** handlers (`Repr`, `BEq`, `DecidableEq`, `Inhabited`, `Hashable`) | no new user keyword or unchecked proof authority (§4) |
| Collection access | Lean `GetElem`, `xs[i]`, `xs[i]?`, `xs[i]!`, `xs[i]'h` | adopt native forms and their precise proof/optional/panic meanings | baseline; `!` is not a verified safety claim (§3, §10) |
| Strings | Lean `s!"..."` interpolation and `r#"..."#` raw strings | native notation and `.ps`-checked embedded terms | baseline (§3) |
| Monadic errors | Lean `throw`, `try`, `catch`, `finally` in `do` | native meanings under admitted typed effect classes; `.ps` braced body selection | staged, no JS exceptions (§7) |
| Maps, JSON, filesystem, async | Lean library/effect families and external runtime adapters | curated API and boundary requirements, **no new global grammar** | application libraries, not core syntax (§8A) |
| Theorem libraries | pinned Lean tactics and notation registrations | broaden built-ins and enable explicitly pinned proof-producing extensions | checked proof terms; audited assumptions (§6) |
| Assurance | Lean typing/proofs plus runtime-world boundaries | ordinary checked output vs verified executable output | one language; only verified output requires complete certificate (§7B) |

**Canonicalization principle:** aliases native to Lean's logical notation (e.g. `∀`/`forall`) are retained; confusing differences in callable syntax are removed. All omitted Lean syntax remains outside the closed `.ps` source profile; it is not silently borrowed from arbitrary Lean extensions.

### RC4 upstream delta relevant to `pscv0`

The official [Lean 4.35.0-rc4 notes](https://lean-lang.org/doc/reference/latest/releases/v4.35.0/) document experimental erased state in `do` (`erased`, `erased mut`, erased monadic binds), `given` logical contract variables, and new/adjusted VC and loop tooling. They also describe improved kernel reductions for several `Array`/`Vector` operations and array equality. **Impact:** target the RC4 parser and proof/verification library exactly; do not copy RC3's assumed built-in registry or claim stable intrinsic-verification syntax. All such constructs still require independently checked final proof terms.

### RC4 pin and unified `pscv0` decisions

1. **Keep `const` and `function`** alongside `def` because they communicate application-programming intent. `const` is a parameterless `def`; `function` provides a comma-separated explicit parameter list. They do not change Lean typing or runtime data semantics.
2. **Keep Lean mathematics, not duplicate syntax for mathematics.** In `.ps`, retain `∀` and `forall`, `∃` and `exists`, `λ` and `fun`, `->` and `→`, plus the other applicable pinned mathematical notations. The requested singular `exist` is **not** a Lean quantifier token; the native word is `exists`.
3. **Eliminate ambiguous parenthesis whitespace only in term application.** `f (x)`, `f (x, y)` and `f ()` are **parse errors in `.ps` when used as applications**, whether in an executable expression, proposition, tactic argument, contract, or `#check`/`#eval`. Write `f(x)`, `f((x, y))`, or `f(())`. Retain unparenthesized Lean application `f x y`. Crucially, **do not apply this restriction to native binder grammar** (`variable (n: Nat)`, `fun (x: Nat) => ...`) **or to a term that starts with grouping parentheses** (`#check (f x)`, `exact (hp)`, `(1 + 2)`).
4. **`function f()` means a required Lean `Unit` binder** and the source call `f()` supplies that `Unit` under the strict empty-call rule. A `Unit`-typed parameter named explicitly in `function g(u: Unit)` is passed as `g(())`; `g ()` is never accepted. Defaults may permit `greet()` where the declared parameters are optional.
5. **Use exactly one braced form for each ProofScript-owned body.** `by { ... }`, `do { ... }`, `match ... with { ... }`, `structure ... where { ... }`, `where { ... }`, and `if (p) { a } else { b }` are the designated `.ps` forms. Source `.lean` retains Lean layout syntax.
6. **Use Lean's actual proof language** inside braces: native middle-dot bullet `·`, `case`, `next`, and selected proof automation. ASCII `.` is **not** a bullet. Goal focus and proof sequencing mean the same thing as their selected Lean counterparts.
7. **Adopt native Lean verification vocabulary.** `erased` replaces `ghost`; `Subtype` and subtype notation replace `refine type`; explicit structure proof fields replace a redundant `invariant self` suffix; `theorem`/`vcgen` replaces the extra `verify` command. Intrinsic verification is experimental in RC4, so this is a proposed pinned subset rather than a compiler-conformance claim.
8. **Keep diagnostics and type families Lean-native.** `#check`, `#print`, `#reduce` and bounded `#eval` belong to source analysis, not verified executable meaning. Types are `Nat`, `Int`, `Bool`, `UInt*`, `Int*`, `String`, `List`, `Array`, `Fin`, `Subtype`, etc., never ambient JS `number` or `any`.
9. **Retain Lean's meaningful native pattern sugar.** In `Nat` patterns, `k + 1` and `.succ k` are both allowed because the pinned Lean elaborator recognizes the former as a constructor pattern. Do not reclassify arbitrary `k + m`, `1 + k`, or `n - 1` arithmetic as a pattern. Prefer `k + 1` for parity, predecessor, and arithmetic-recursion examples; prefer `.succ k` when teaching the underlying constructor.
10. **Retain native Lean `variable`/`section` behavior.** Section variables used in definitions become function parameters of matching visibility and dependency; they are not mutable data. Theorems generalize section variables from the theorem statement, plus explicit `include` policy, rather than arbitrary use inside the proof. Recursion-changing inputs must appear as explicit declaration parameters, not be treated as varying section variables.
11. **Support Lean's interactive proof-workflow model.** `#check` already belongs to the language command selection. A future `.ps` VS Code integration should expose Lean-like goals, InfoView, diagnostics, type inspection and tactic feedback, with accurate `.ps` source positions; selected proof-syntax restrictions mean the project must not claim every Lean tactic or macro is available.
12. **Expand native Lean language features before adding punctuation.** Admit the selected RC4 multi-discriminant and dependent `match` families, `if let`, `nomatch`, and pattern tests. Preserve the `.ps` braced-match/conditional convention; never replace constructor reasoning with TypeScript dynamic narrowing.
13. **Enable native `deriving` through a frozen allowlist.** Derivation is an elaboration operation producing declarations/instances; its handler identity and resulting declarations enter the environment, and any claimed laws remain checked evidence.
14. **Guarantee safe everyday APIs.** Support Lean array/list syntax and native `GetElem` variants, interpolation/raw strings, and a usable `List`/`Array`/`Option`/`Except` API baseline; maps/sets/JSON belong to curated libraries.
15. **Admit useful Lean `do` exception constructs carefully.** `throw`, `try`/`catch`, and conditional `finally` have monadic class requirements and typed effects; they do **not** copy JavaScript exceptions, and foreign/world effects remain explicit boundaries.
16. **Broaden theorem-authoring without broadening proof trust.** Pin built-in goal control and useful tactics; offer explicit, versioned import of proof-producing tactic/notation environments after review. No extension adds an axiom, proof hole, or verified certificate merely by being loaded.
17. **Separate ordinary checking from verified claims.** Under `pscv0` all source is Lean-grounded and checked. Ordinary executable programs may use permitted typed external capabilities, but only a closed and fully proved dependency closure can claim verified executable status; classify external assumptions separately.


**Conformance scope:** The chapter comparisons describe intentional surface rules, not evidence that a finished `pscv0` parser or verifier implements them. The original RC3 specification remains separate historical source material; the choices above supersede its redundant aliases only for this new `pscv0` design.

## Comparison guide and sources

| Marker | Meaning |
|---|---|
| **Shared Lean** | Already has the same or restricted native Lean source form and Lean meaning |
| **PSCV0 sugar** | Owned notation that desugars to a named Lean expression/declaration family |
| **PSCV0 verification** | Selected Lean-native contract/erased/loop/refinement forms with logic represented by Lean propositions and checked proof terms |
| **Restricted** | Lean can express more; `pscv0` deliberately recognizes a closed subset |
| **Lean encoding** | Lean example expresses the semantic equivalent but may not share PSCV0 syntax |
| **Illustrative** | Code shapes used to describe the design; no claim of compilation or proof closure |

**Sources of rule content:** the uploaded release candidate’s language chapters and selected PSCV verification proposals, plus the directly inspected pinned Lean 4.35.0-rc4 parser families and published Lean reference. `pscv0` additions are marked as surface deltas or proposed proof-language encodings rather than silently attributed to Lean. The authoritative Lean pin is the Git commit above; relevant exact Lean source links appear in the source concordance near the end. The public Lean language reference can explain parser behavior, but its `/latest/` pages are not a normative version pin.


### Reading schematic grammar, not an invented EBNF

The grammar tables are **selective Lean-4-style sketches**, modeled on its documented syntactic categories; they deliberately omit alternatives with `...`. They are *not* literal extracts of Lean parser combinator code and should not be used as a complete parser-generator specification. The `pscv0` column records what changes to source punctuation or accepted subfamilies, while typechecking and verification remain Lean-based. The specific syntax for PSCV0-only forms is a proposed design, not a claim that native Lean parses it.

## 0A. Adoption contract — language core, libraries, proof environment, and assurance

This revision implements the decisions proposed in the companion *PSCV0 Lean-First Language Feature Review* (2026-10-11) **as specification changes only**. It does not say that all Lean 4.35.0-rc4 programs parse as `.ps`, nor that the compiler can already execute/verify them. Source-derived facts retain the previous RC3/RC4 provenance; newly accepted families in this edition are explicitly proposed `pscv0` requirements.

| Ownership | Guaranteed direction | Not an implication |
|---|---|---|
| Lean-grounded language/core | `Prop`, `Type`, dependent functions, inductives, equality, kernel-checkable proofs, `Subtype`, `Fin` | no second logic, dynamic JS types, or unsound casts |
| **Selected** Lean source grammar | Multi-discriminant/dependent `match`, `if let`, `nomatch`, native `deriving`, `GetElem`, strings, goal control, `do`/exceptions where admitted | not unrestricted Lean parser/macros/attributes |
| ProofScript surface | `const`, `function`, adjacent `f(x, y)`, canonical braced bodies | no new function type/tuple semantics or truthiness |
| Curated first-party library | Practical `List`, `Array`, `Option`, `Except`, map/set, parsers/JSON, typed IO capabilities, as specified by manifest | library functions do not automatically register new notation/tactics |
| Named proof extension environment | Versioned, explicitly opted-in proof-producing tactics/notations and their registered declarations | no extension is an independent logical oracle; no silent dependency-based grammar expansion |
| **Ordinary checked output** | Valid source typing, total admitted definitions and explicit typed runtime boundaries; proof terms still checked | not a verified behavioral guarantee |
| **Verified executable output** | All specified required contracts, call obligations, termination, proof/assumption/effect/erasure closure satisfied | not an automatic guarantee that foreign systems or backends behave as specified |

**A binding rule:** every new feature must have an exact Lean parser/elaborator/lowering locator at the RC4 pin, a selected `pscv0` grammar form, source examples, positive/negative acceptance cases, and an environment/assurance classification. Items labeled **P1 API** are product requirements, not permission to fabricate unspecified Lean/Std library symbols. If the exact signature/handler/registration cannot be pinned, the particular API remains *pending* despite the capability requirement.

**No hidden profile rollback.** The `pscv0` verification discipline remains stronger than ordinary Lean programming. `partial`, `unsafe`, ordinary user axioms in closed verification, `sorry` as evidence, and unmodeled foreign semantics do not become valid in a verified closure simply because `pscv0` now supports more application features. A weaker executable mode must never inherit a verified label or certificate.

**Compatibility cost to watch:** rejecting `f (x)` inside `.ps` means some Lean proof terms and macro expansions require transcription, even as more Lean proof features become available. This is an explicit usability tradeoff; source-preserving conversion tools are preferable to silently changing the rule.

## 1. Files, lexical structure, and name scope

### Source text, identifiers, comments, and line breaks

**Feature / profile:** Shared lexical families; PSCV0 sugar whitespace restrictions  
**Source basis:** Ch. 5; A.1.1, A.3; Appendix I.4

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>sourceFile ::= importHeader command* EOF
identifier ::= Lean.ident
literal ::= Lean.numeral | Lean.string | Lean.char | ...
comment ::= &quot;--&quot; lineText | &quot;/-&quot; nestedComment &quot;-/&quot;</code></pre></td><td valign="top"><pre><code>sourceFile ::= importHeader command* EOF
identifier ::= Lean.ident
literal ::= Lean.literalRestricted
comment ::= Lean.comment
// Modification: UTF-8; ASCII-space/LF layout profile; no ASI</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>-- UTF-8 source; line comments
/- nested /- block -/ comments -/
def answer : Nat := 42</code></pre></td><td valign="top"><pre><code>-- UTF-8 .ps source; line comments
/- nested /- block -/ comments -/
const answer: Nat := 42</code></pre></td></tr></tbody></table>

**Source language distinction.** Standard ProofScript requires UTF-8, permits one leading BOM, normalizes CRLF to LF, rejects lone CR and horizontal tabs outside literals/comments, and uses only ASCII SPACE/LF as structural whitespace. Lean’s scanner is less restricted; neither language imports JavaScript automatic semicolon insertion. Lean-defined identifier and literal tokens are referenced, not redefined.

### Modules, imports, and public imports

**Feature / profile:** Shared with tighter ProofScript module grammar  
**Source basis:** Ch. 6; A.2; [module.import-header]

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>importHeader ::= importCommand*
importCommand ::= &quot;import&quot; moduleName
                | &quot;public&quot; &quot;import&quot; moduleName
command ::= Lean.command</code></pre></td><td valign="top"><pre><code>importHeader ::= importCommand*
importCommand ::= &quot;import&quot; moduleName
                | &quot;public&quot; &quot;import&quot; moduleName
command ::= selectedLeanCommand | psCommand
// Modification: imports restricted to top-level header</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>import Std.Data.List
public import MyProject.API

def value : Nat := 1</code></pre></td><td valign="top"><pre><code>import Std.Data.List
public import MyProject.API

const value: Nat := 1</code></pre></td></tr></tbody></table>

**Source language distinction.** Both admit module imports; ProofScript requires all imports in the top-level header, forbids imports nested in sections/namespaces, and distinguishes ordinary imports from re-exporting public imports. `.ps` and `.lean` files are distinct source kinds; a file-name collision is not a language syntax overload.

### Namespace, sections, open, variables, include / omit

**Feature / profile:** Shared names/scopes with PS deterministic resolution  
**Source basis:** Ch. 7; A.2; Appendix I `LEAN-SCOPE-SECTION`

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;namespace&quot; ident | &quot;section&quot; ident?
          | &quot;end&quot; ident? | &quot;open&quot; ident+
          | &quot;variable&quot; binder+ | &quot;include&quot; ident+
          | &quot;omit&quot; ident+ | &quot;universe&quot; ident+</code></pre></td><td valign="top"><pre><code>command ::= &quot;namespace&quot; ident | &quot;section&quot; ident?
          | &quot;end&quot; ident? | &quot;open&quot; ident+
          | &quot;variable&quot; psBinder+ | &quot;include&quot; ident+
          | &quot;omit&quot; ident+ | &quot;universe&quot; ident+
// Modification: selected Lean commands; same scoping model</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>namespace MathOps
  def twice (n : Nat) : Nat := n + n
end MathOps

open MathOps
section
  variable (n : Nat)
  def result : Nat := twice n
  #check n
end

#check result
#eval result 7  -- 14</code></pre></td><td valign="top"><pre><code>namespace MathOps
  function twice(n: Nat): Nat := n + n
end MathOps

open MathOps
section
  variable (n: Nat)
  def result: Nat := twice(n)
  #check n
end

#check result
#eval result(7) -- 14</code></pre></td></tr></tbody></table>

**Source language distinction.** Namespace prefixes affect declaration names; sections do not. ProofScript's unqualified-name lookup has deterministic local/current/enclosing/opened/imported tiers; ambiguities reject. `#check` is an **admitted diagnostic command** in `pscv0` Standard, not an unknown command; detailed restrictions appear in §7A.

**Why `variable (n: Nat)`?** This declares one **explicit section parameter** shared by subsequent declarations. When `def result: Nat := twice(n)` uses `n`, Lean inserts an explicit `(n : Nat)` parameter into the definition's final signature: conceptually `result : Nat → Nat`. Accordingly `#check result` displays its parameterized type and `#eval result(7)` evaluates to `14`; the `result` declaration survives `end`, while the local section variable `n` does not. `open MathOps` only permits the unqualified name `twice`; it does not import or copy the definition. For a single declaration, the clearer equivalent is `function result(n: Nat): Nat := MathOps.twice(n)` without a `section`.

**Binder visibility is Lean-native.** `variable (n : Nat)` is explicit, `variable {α : Type}` is implicit, and `variable [Decidable p]` is an instance parameter where valid. These parentheses occur in a **command binder position**, not after a callable term, so the application adjacency restriction cannot reject them. For theorems, only dependencies in the theorem *statement* (plus `include`-forced dependencies) become theorem parameters: mentioning a section variable solely in a proof body must not silently change the theorem's statement. For recursion, a section variable is fixed within the definition body, so a decreasing recursive argument such as `n` in `even`/`odd` belongs in the function header. These are Lean 4.35.0-rc4 semantics, not new ProofScript rules. See [Lean section variables](https://lean-lang.org/doc/reference/4.35.0-rc4/Namespaces-and-Sections/).

## 2. Declarations, functions, and arguments

### Ordinary `def`

**Feature / profile:** Shared semantics; PSCV0 sugar parameter and body forms  
**Source basis:** Ch. 8; A.2, A.7–A.8

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= modifiers? &quot;def&quot; declId declSig? declVal
declSig ::= binder* (&quot;:&quot; term)?
declVal ::= &quot;:=&quot; term termination? whereDecls? | equations</code></pre></td><td valign="top"><pre><code>command ::= modifiers? &quot;def&quot; declId psBinders (&quot;:&quot; term)? psDeclVal
psDeclVal ::= &quot;:=&quot; term termination? psWhere?
          | &quot;:=&quot; &quot;{&quot; term &quot;}&quot; termination? psWhere?
// Modification: comma explicit binders; optional one-term braces</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def double (n : Nat) : Nat :=
  n + n</code></pre></td><td valign="top"><pre><code>def double(n: Nat): Nat := {
  n + n
}</code></pre></td></tr></tbody></table>

**Source language distinction.** ProofScript explicit parameters are comma-separated inside one group; `:= { term }` is a **single-term wrapper**, not a multi-statement block. Plain `:= term` is also valid. Braced record literals are separately parsed as terms. In declarations, `(n: Nat)` is parsed as an **explicit binder group**, not a call: `def double (n: Nat): Nat := n + n` is admitted by the selected declaration grammar, although the canonical formatter writes `def double(n: Nat): Nat := n + n`. For `function`, the canonical spelling is `function double(n: Nat)`. This allowance has no `f ()` consequence because a call after an expression head uses the separate term grammar.

### Value declaration: `const` versus Lean `def`

**Feature / profile:** PSCV0 sugar  
**Source basis:** Ch. 8 (`const`); A.2; Appendix H.1

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;def&quot; declId (&quot;:&quot; term)? &quot;:=&quot; term</code></pre></td><td valign="top"><pre><code>command ::= modifiers? &quot;const&quot; declId (&quot;:&quot; term)? psDeclVal
// Lowers to parameterless Lean def; not JS/TS const</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def answer : Nat := 42
def inc : Nat → Nat := fun n =&gt; n + 1</code></pre></td><td valign="top"><pre><code>const answer: Nat := 42
const inc: Nat -&gt; Nat := { fun n =&gt; n + 1 }</code></pre></td></tr></tbody></table>

**Source language distinction.** `const` is a top-level/namespace **parameterless definition alias**—not TypeScript `const` and not a distinct Lean kernel constructor. In the provided design RC it is retained even though other ProofScript design discussions may have considered removing it.

### Function declaration: `function` versus `def`

**Feature / profile:** PSCV0 sugar declaration alias  
**Source basis:** Ch. 8–9; A.7

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;def&quot; declId binder* (&quot;:&quot; term)? declVal</code></pre></td><td valign="top"><pre><code>command ::= modifiers? &quot;function&quot; declId psBinders
            (&quot;:&quot; term)? psContract* psDeclVal
// Modification: &#x27;function&#x27; =&gt; Lean &#x27;def&#x27;; comma binder group</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def add (x : Nat) (y : Nat) : Nat :=
  x + y</code></pre></td><td valign="top"><pre><code>function add(x: Nat, y: Nat): Nat := {
  x + y
}</code></pre></td></tr></tbody></table>

**Source language distinction.** Lean application remains curried at the core level; ProofScript's comma-grouped source parameters and calls do not make a new noncurried type theory.

### Explicit, implicit, strict-implicit, instance binders

**Feature / profile:** Shared binders with PS explicit-group grammar  
**Source basis:** Ch. 9; A.7; Appendix I `LEAN-BINDER-*`

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>binder ::= &quot;(&quot; ident+ &quot;:&quot; term &quot;)&quot; | &quot;{&quot; ident+ &quot;:&quot; term &quot;}&quot;
         | &quot;⦃&quot; ident+ &quot;:&quot; term &quot;⦄&quot; | &quot;[&quot; term &quot;]&quot;
// ASCII {{x : T}} is also a strict-implicit Lean spelling</code></pre></td><td valign="top"><pre><code>psBinders ::= psNonExplicitBinder* psExplicitGroup?
psExplicitGroup ::= &quot;(&quot; psParam (&quot;,&quot; psParam)* &quot;,&quot;? &quot;)&quot;
psParam ::= ident &quot;:&quot; term (&quot;:=&quot; term)?
psNonExplicitBinder ::= Lean.implicitBinder
                    | Lean.strictImplicitBinder | Lean.instBinder</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def same {α : Type} [BEq α] (x : α) (y : α) : Bool :=
  x == y

def retain {{α : Type}} (x : α) : α := x</code></pre></td><td valign="top"><pre><code>function same {α: Type}[BEq α](x: α, y: α): Bool := {
  x == y
}
function retain {{α: Type}}(x: α): α := x</code></pre></td></tr></tbody></table>

**Source language distinction.** ProofScript reuses Lean binder semantics, but explicit groups require commas; one trailing comma is optional. `{{α: Type}}` is the admitted strict-implicit ASCII form. Closed PSCV0 restricts instance synthesis to a deterministic registry.

### Default/optional arguments and named arguments

**Lean family:** Lean declaration binders, named arguments, optional/default binders, and dependent function application. **`pscv0` delta:** comma-separated explicit parameters and no-gap call parentheses. Default insertion preserves Lean's declared-term scope; it is not runtime overloading.

| Lean 4.35.0-rc4 | ProofScript `pscv0` |
|---|---|
| `def greet (name : String := "world") : String := name` | `function greet(name: String := "world"): String := name` |
| `greet (name := "Ada")` | `greet(name := "Ada")` |
| `greet` can be elaborated with a default in an expected-result context | `greet()` explicitly requests completion of all optional explicit arguments |
| `def add (x y : Nat) := x + y` | `function add(x: Nat, y: Nat): Nat := x + y` |

**Lean grammar (schematic):** `binder ::= ... | '(' ident ':' term (':=' term)? ')'`; native named arguments are supplied through Lean's application elaborator. **ProofScript modification (schematic):** an adjacent `(` after a call head begins a comma-separated list of positional arguments followed by optional named arguments. One optional trailing comma is permitted. A positional argument after a named argument or an unknown/duplicate name rejects.

### Zero-source-argument functions and `f()`

The Lean kernel has only unary application and dependent/Pi-function types; a source-nullary function is not a second core function kind.

| Source | `pscv0` acceptance | Desugaring / explanation |
|---|---|---|
| `function clock(): Nat := 42` | yes | Lean `def clock (_u : Unit) : Nat := 42` |
| `clock()` | yes | Lean `clock ()` through zero-source-argument completion |
| `clock(())` | yes when a `Unit` argument is required | an explicit one-argument application; may have the same Lean core term as `clock()` |
| `clock ()` | **no** | forbidden gap-parenthesized application in `.ps` |
| `function useUnit(u: Unit): Nat := 1` | yes | regular explicit parameter |
| `useUnit(())` | yes | explicitly pass `Unit` |
| `useUnit()` | yes under **exactly-one-Unit** completion rule | no general missing-argument inference |
| `function greet(name: String := "world"): String := name` / `greet()` | yes | inserts declared default |
| `greet ()` | **no** | parse error, regardless of expected type |
| `function add(x: Nat, y: Nat): Nat := x + y` / `add()` | **no** | unresolved required arguments |

**Empty-source-argument rule (proposed):** After inserting Lean implicit/instance binders, `f()` is admitted only if (a) every remaining explicit binder is provided by a declared/default/automatic parameter, or (b) after that completion, exactly one remaining required explicit parameter has type definitionally equal to `Unit`, and the elaborator inserts `()`. All other required values reject. No arbitrary `Inhabited` value is guessed. This is an **elaboration rule**, not a proof or a runtime arity model; the semantics of a function *value* remains its Lean Pi type. First-class function values do not carry special JS zero-arity semantics.

### Parenthesized calls, native Lean application, and tuple arguments

**Adopted `pscv0` source rule `PSCV0-APP-01`.** `pscv0` keeps Lean's curried application semantics and supports two intentional spellings: adjacent comma calls `f(x, y)` and native *unparenthesized* Lean application `f x y`. It rejects **gap-parenthesized application** in `.ps`, which is the hazardous third possibility. This is a grammar/source-acceptance rule, not merely a formatter preference; `.lean` modules retain their normal Lean grammar.

| Expression | Lean meaning or comparison | `pscv0` acceptance |
|---|---|---|
| `f x y` | two Lean unary applications | **accept** |
| `f(x)` | one ProofScript call argument | **accept**; lowers to Lean `f x` |
| `f(x, y)` | two ProofScript call arguments | **accept**; lowers to Lean `f x y` |
| `f (x)` | one grouped argument in `.lean` | **reject**; use `f(x)` |
| `f (x, y)` | **one tuple** in `.lean`, not two arguments | **reject**; use `f((x, y))` |
| `f((x, y))` | one tuple argument | **accept**; lowers to Lean `f (x, y)` |
| `f()` | zero source arguments, type-directed completion | **accept only if** `PSCV0-APP-03` closes every required explicit argument |
| `f ()` | one explicit Unit value in Lean | **reject**; use `f(())` |
| `f(())` | one explicitly supplied `Unit` value | **accept** where parameter type is `Unit` |
| `h (g x)` | application to one grouped argument in `.lean` | **reject**; use `h(g x)` or `h(g(x))` |
| `(h) (x)` | grouped function applied to grouped argument in `.lean` | **reject**; use `(h)(x)` or `h(x)` |
| `f/* comment */(x)` | trivia-separated Lean application | **reject** if parsed as a gap-parenthesized application |
| `x + (y * z)` | `(` begins an operand after infix `+`, not an application head | **accept** |
| `(f x)` | grouped *standalone term* | **accept** |
| `#check (f x)` | `(` starts the command's term | **accept** |
| `exact (hp)` | `(` starts a tactic argument term | **accept** |
| `variable (n: Nat)` | `(` starts a typed command binder | **accept** |
| `fun (n: Nat) => n` | `(` starts a typed lambda binder | **accept** |

**`PSCV0-APP-02` — source-position and grammar-category test.** A parser should first determine whether it is parsing a **binder**, an **initial/grouped term**, or a **continuation of an already-completed expression**. Only in the last category is a parenthesis after a nonempty trivia gap banned as an application operand. The rule is not the text-level regex `identifier + space + '('`: such a rule would incorrectly reject `variable (n: Nat)`, theorem and `def` binders, `#check (term)`, `exact (proof)`, and infix grouping.

Within an application expression:

1. If an immediately adjacent `(` follows a callable, parse a ProofScript postfix **comma-argument call**. One trailing comma is allowed; positional arguments precede any named arguments.
2. If a Lean application argument begins with any ordinary **non-parenthesized** admitted term, keep Lean's normal left-associative application semantics (for example `f x y`).
3. If a **nonzero space/comment/newline gap** would join an existing callable expression to an argument whose first source token is `(`, report `PSCV0-APP-02` and reject that application. Comments never count as adjacency. A newline also follows the independent enclosing layout rules; if it separates two independent `do` statements, do not silently reinterpret them as one call.
4. Nested parentheses *inside an adjacent call argument list* remain ordinary Lean grouping/tuple/Unit syntax: `f((x, y))`, `f(())`, `f((g x))` are legal. Other ordinary grouped expressions remain legal wherever the surrounding Lean grammar expects a fresh term.

**`PSCV0-APP-03` — empty invocation.** `f()` means **no explicitly written arguments**; it does not mean “apply a zero-arity JavaScript function” and does not automatically produce a partially applied function. After inserting ordinary implicit/instance binders and any declared explicit defaults, it must have **no required explicit argument remaining**, or **exactly one required explicit `Unit` argument remaining**, in which case the elaborator inserts `()` and completes the call. Unknown/unsolved required explicit arguments, two required `Unit` arguments, and arbitrary `Inhabited`-based filling reject. `f()` cannot gain different meaning through a caller-local default: defaults are elaborated at declaration scope.

`function f(): R := body` lowers to a **required** Lean `Unit` binder with type `Unit → R`. Hence `f()` is accepted under the exactly-one-Unit case. `f(())` is also an explicitly written application of `Unit` when appropriate, and may elaborate to the *same Lean term*: this harmless equivalence is distinct from the dangerous spacing confusion between `f(x, y)` and `f (x, y)`.

**No separate call grammar in proofs or diagnostics.** The same rules govern function bodies, theorem propositions, `by { ... }` term arguments, `do` elements, `requires`/`ensures` clauses, match branches, `#check`, `#eval`, and `#reduce`. For example, `exact h(p)` and `#check f(())` are valid when types fit; `exact h (p)` and `#check f ()` must fail as applications. A tactic head such as `exact` is not itself an applicative term; consequently `exact (hp)` remains a valid grouped *initial tactic argument*.

**Formatter/IDE requirement.** Formatting must preserve the same elaborated Lean term and argument partition. It must never insert a gap into `f(...)`, turn `f((x, y))` into `f(x, y)`, or auto-correct an invalid gap-parenthesized expression without explicit user action. Source spans, diagnostics, completion and hover types should operate on the exact `.ps` term grammar, not a fallback unrestricted `.lean` parser.

### Binder grammar is independent of term application (`PSCV0-BIND-01`)

Lean's native `variable`/`section` commands, function/theorem/definition signatures, lambda binders, quantifier binders, and instance binders are **binding constructs**. Their delimiters specify a variable with a type or implicit-argument status; they are not a function being applied to `()` or to `(n: Nat)`.

```proofscript
namespace MathOps
  function twice(n: Nat): Nat := n + n
end MathOps

open MathOps
section
  variable (n: Nat)  -- native Lean explicit section binder: VALID
  def result: Nat := twice(n)
  #check result      -- resulting signature has an explicit (n : Nat)
end

#check result
#eval result(7)      -- 14

const idNat: Nat -> Nat := fun (x: Nat) => x
#check (idNat 3)     -- parentheses start a grouped term, VALID
#check idNat(3)     -- adjacent ProofScript call, VALID
```

`variable (n: Nat)` stays valid even though `result (7)` and `twice (n)` are rejected in `.ps`. Parser decisions depend on **grammar category**, not on whether a space happens to occur before `(`. A source formatter should prefer `function twice(n: Nat)` and `result(7)` but preserve the native `variable (n: Nat)` syntax.

This reference intentionally retains a small amount of harmless duplicate notation (`f x` and `f(x)`, selected Unicode/text mathematical aliases) rather than introducing false equivalence with Lean's spaced parenthesized arguments. **Soundness still requires faithful elaboration, type checking and independent proof checking; the adjacency restriction primarily improves source predictability and refactoring safety.**

### Generalized field/method notation

**Feature / profile:** Shared semantics; PS method call syntax  
**Source basis:** Ch. 10; A.6; [elab.field]

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= term &quot;.&quot; ident | term argument+ | ...
// Lean generalized field notation uses type-directed elaboration</code></pre></td><td valign="top"><pre><code>term ::= term &quot;.&quot; ident | psCallable &quot;(&quot; psCallArgs? &quot;)&quot;
// Unchanged field lookup; new comma-call postfix only</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def stringLength (s : String) : Nat := s.length</code></pre></td><td valign="top"><pre><code>function stringLength(s: String): Nat := s.length
-- If mapped method exists: users.map(toName)</code></pre></td></tr></tbody></table>

**Source language distinction.** Both use *static, type-directed* field/method resolution, not JS prototype lookup. The `users.map(toName)` example presumes a visible admitted mapping and is illustrative, not a promise about every Standard library API.

### Single-term declaration body and local `where` definitions

**Feature / profile:** PSCV0 single-term body sugar; Lean-native `where` introducer  
**Original-source cross-check:** Ch. 8; A.8, A.12; Appendix B

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>declVal ::= &quot;:=&quot; term termination? whereDecls?
whereDecls ::= &quot;where&quot; localDeclaration+
// Lean supports indentation and certain semicolon variants</code></pre></td><td valign="top"><pre><code>psDeclVal ::= &quot;:=&quot; term termination? psWhere?
          | &quot;:=&quot; &quot;{&quot; term &quot;}&quot; termination? psWhere?
psWhere ::= &quot;where&quot; &quot;{&quot; psLocalDeclaration+ &quot;}&quot;
// Braces wrap one expression; where explicitly keeps Lean keyword</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def plusOne (n : Nat) : Nat := helper n
where
  helper (x : Nat) : Nat := x + 1</code></pre></td><td valign="top"><pre><code>-- PSCV0: explicit local where with braced local definitions
function plusOne(n: Nat): Nat := helper(n)
where {
  def helper(x: Nat): Nat := x + 1
}</code></pre></td></tr></tbody></table>

**Source language distinction.** **PSCV0-D-WHERE correction:** the original source omitted the `"where"` token in its `WhereBody` grammar even though its prose and examples required it. This edition keeps Lean’s required `where` introducer and permits the ProofScript grouping `where { ... }`. It is a deliberate source-syntax change rather than an independent grammar production. `where` field separators are newline-only; local theorem/instance/command forms are excluded.

### Aliases and opacity: `abbrev` and `opaque`

**Feature / profile:** Shared Lean declaration families  
**Source basis:** Ch. 8, 17; A.2; Appendix I.5

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;abbrev&quot; declId declSig? declVal
          | &quot;opaque&quot; declId declSig declVal?</code></pre></td><td valign="top"><pre><code>command ::= &quot;abbrev&quot; declId psBinders (&quot;:&quot; term)? psDeclVal
          | &quot;opaque&quot; declId psBinders &quot;:&quot; term psDeclVal
// Same Lean declaration kinds and transparency policies</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>abbrev UserId := Nat
opaque secret : Nat := 42</code></pre></td><td valign="top"><pre><code>abbrev UserId := Nat
opaque secret: Nat := 42</code></pre></td></tr></tbody></table>

**Source language distinction.** `abbrev` remains definitionally reducible, whereas `opaque` does not unfold under ordinary source conversion. In PSCV, a public executable `opaque` declaration still needs approved specification coverage and proof evidence; the source form is not an exemption from validity.

### Visibility: `private` and declarations exported through modules

**Feature / profile:** Shared visibility concept, PS constrained module surface  
**Source basis:** Ch. 6–7; A.2

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>modifiers ::= docComment? attributes? visibility? ...
visibility ::= &quot;private&quot; | &quot;public&quot;</code></pre></td><td valign="top"><pre><code>modifiers ::= psAttributes? &quot;private&quot;?
command ::= modifiers? selectedLeanDeclaration
          | modifiers? psDeclaration
// Deliberately restricted modifiers; not new visibility semantics</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>private def secret : Nat := 7
def publicValue : Nat := 3</code></pre></td><td valign="top"><pre><code>private const secret: Nat := 7
const publicValue: Nat := 3</code></pre></td></tr></tbody></table>

**Source language distinction.** ProofScript ordinary top-level declarations are public unless `private`; `public import` re-exports public declarations while ordinary import does not. It has no TypeScript declaration merging or selective-export syntax.

## 3. Type theory, expressions, and everyday data

### `Prop`, `Type`, `Sort`, universes and dependent Pi

**Feature / profile:** Shared core logic  
**Source basis:** Ch. 4, 9, 16; A.6; Appendix I

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= &quot;Prop&quot; | &quot;Type&quot; level? | &quot;Sort&quot; level
     | &quot;(&quot; ident &quot;:&quot; term &quot;)&quot; &quot;→&quot; term
     | term &quot;→&quot; term</code></pre></td><td valign="top"><pre><code>term ::= &quot;Prop&quot; | &quot;Type&quot; level? | &quot;Sort&quot; level
     | &quot;(&quot; ident &quot;:&quot; term &quot;)&quot; (&quot;→&quot; | &quot;-&gt;&quot;) term
     | term (&quot;→&quot; | &quot;-&gt;&quot;) term
// No new universe or Pi forms</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>universe u
def id {α : Type u} (x : α) : α := x
-- Dependent result type: (n : Nat) → Fin n → Nat</code></pre></td><td valign="top"><pre><code>universe u
function id {α: Type u}(x: α): α := x
-- Dependent result type: (n: Nat) -&gt; Fin n -&gt; Nat</code></pre></td></tr></tbody></table>

**Source language distinction.** `Prop = Sort 0`, `Type u = Sort (u+1)`. Function arrows denote dependent Pi. The result type may reference prior arguments. The source grammar for universe-level terms is delegated to a pinned Lean parser category (not fully expanded in the uploaded text).

### Lambda terms, type ascription, and `let`

**Feature / profile:** Shared term families; PS tighter layout  
**Source basis:** Ch. 9–10; A.6

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= &quot;fun&quot; binder+ &quot;=&gt;&quot; term
     | &quot;(&quot; term &quot;:&quot; term &quot;)&quot;
     | &quot;let&quot; ident (&quot;:&quot; term)? &quot;:=&quot; term separator term</code></pre></td><td valign="top"><pre><code>term ::= &quot;fun&quot; psLambdaBinder+ &quot;=&gt;&quot; term
     | &quot;(&quot; term &quot;:&quot; term &quot;)&quot;
     | &quot;let&quot; ident (&quot;:&quot; term)? &quot;:=&quot; term separator term
// These remain Lean term families; not TS arrow lambdas</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def increment : Nat → Nat := fun n =&gt; n + 1

def two : Nat :=
  let x := 1
  x + 1</code></pre></td><td valign="top"><pre><code>const increment: Nat -&gt; Nat := fun n =&gt; n + 1

function two(): Nat := {
  let x := 1
  x + 1
}</code></pre></td></tr></tbody></table>

**Source language distinction.** Lambdas retain the `fun ... => ...` spelling rather than TypeScript's bare `x => ...`. `let` has immutable logical meaning. In ProofScript a `let ...` followed by its body is **one term**, not a general statement list. The `TermBodySep` is a completed-value newline.

### Natural/scientific/string/char/Boolean/Unit literals

**Feature / profile:** Shared token families, constrained PS elaboration  
**Source basis:** Ch. 5, 22.2, 24.3; A.3, A.6

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= Lean.numeral | Lean.scientific | Lean.string
     | Lean.char | &quot;true&quot; | &quot;false&quot; | &quot;()&quot;</code></pre></td><td valign="top"><pre><code>term ::= Lean.numeral | Lean.scientific | Lean.string
     | Lean.char | &quot;true&quot; | &quot;false&quot; | &quot;()&quot;
// Lexical classes and overloaded numeral semantics inherited</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def count : Nat := 42
def fraction : Float := 1.25
def text : String := &quot;Ada&quot;
def enabled : Bool := true
def letter : Char := &#x27;A&#x27;
def empty : Unit := ()</code></pre></td><td valign="top"><pre><code>const count: Nat := 42
const fraction: Float := 1.25
const text: String := &quot;Ada&quot;
const enabled: Bool := true
const letter: Char := &#x27;A&#x27;
const empty: Unit := ()</code></pre></td></tr></tbody></table>

**Source language distinction.** Token scanners are pinned Lean families. Numeric meaning is type-directed by instances; defaulting can select `Nat`, `Float` or an applicable signed type under the ProofScript Standard environment. The uploaded reference says its Lean-4.35-rc3 manifest/digest is still pending; no finalized registry is implied.

### Native interpolated/raw strings and string formatting

`pscv0` now requires Lean's **native** `s!"...{expr}..."` interpolation and raw-string lexical family `r"..."`, `r#"..."#` (with matching delimiter hashes), alongside ordinary escaped strings. No additional TypeScript template literal or `String.raw` grammar is introduced.

| Lean 4 | `pscv0` |
|---|---|
| `def greeting (name : String) : String := s!"Hello, {name}!"` | `function greeting(name: String): String := s!"Hello, {name}!"` |
| `def path : String := r#"C:\tmp\"quoted"#` | `const path: String := r#"C:\tmp\"quoted"#` |

Interpolation requires the pinned `ToString` behavior and parses `{expr}` with the same `.ps` expression grammar, including `f (x)` rejection. Raw-string contents are **not** parsed as terms. String conversion is typeclass-directed, not unrestricted JavaScript coercion. The exact RC4 lexer/parser and initial `ToString` instances must be part of the environment conformance suite. [Lean strings](https://lean-lang.org/doc/reference/latest/Basic-Types/Strings/).

### Native collection literals and bounds-aware indexing

`pscv0` guarantees Lean-native `List` literals `[x, y]`, `Array` literals `#[x, y]`, and the standard `GetElem` lookup variants. This is an admission of **existing Lean syntax**; it does not infer an array type from an untyped JavaScript object literal.

| Notation | Meaning in `pscv0` | Verification consequence |
|---|---|---|
| `xs[i]` | Lean `GetElem`; requires `valid xs i` proof | proof side-condition must be discharged (or type-checking fails) |
| `xs[i]'h` | Lean lookup with explicit proof `h : valid xs i` | checked evidence supplied explicitly |
| `xs[i]?` | optional `Option α` lookup | no required in-bounds proof; handle `none` |
| `xs[i]!` | panic/default `GetElem?` path | **not** bounds-safe proof; may panic at runtime |
| `#[a, b]` | `Array` literal | retains Lean array semantics |
| `[a, b]` | `List` literal under admitted expected type/notation | retains inductive list meaning |

```proofscript
function lookup(xs: Array Nat, i: Nat): Option Nat := xs[i]?

function readChecked(xs: Array Nat, i: Nat, h: i < xs.size): Nat := {
  xs[i]'h
}

#check lookup
#eval lookup(#[10, 20], 1)  -- some 20
```

`GetElem` class instances, `get_elem_tactic` behavior, and any source-derived proof discharge paths must be pinned and are **not** replaced by unchecked JavaScript indexing. A verified closure must reject unresolved index validity proofs; the `!` operator's panic/default path is a behavior to model explicitly if admitted, not a proof of bounds. [Lean basic classes / GetElem](https://lean-lang.org/doc/reference/latest/Type-Classes/Basic-Classes/), [arrays](https://lean-lang.org/doc/reference/latest/Basic-Types/Arrays/).

### Tuples/products and explicit grouping

**Feature / profile:** Shared product semantics; PSCV0 sugar tuple comma policy  
**Source basis:** Ch. 10, 26; A.6; Appendix B

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= &quot;(&quot; term &quot;)&quot; | &quot;(&quot; term &quot;,&quot; term (&quot;,&quot; term)* &quot;)&quot;</code></pre></td><td valign="top"><pre><code>term ::= &quot;(&quot; term &quot;)&quot; | &quot;(&quot; term &quot;,&quot; term (&quot;,&quot; term)* &quot;,&quot;? &quot;)&quot;
// Tuple is one term; f((x,y)) passes one tuple in comma-call</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def pair : Nat × Bool := (4, true)
def left : Nat := pair.1</code></pre></td><td valign="top"><pre><code>const pair: Nat × Bool := (4, true,)
const left: Nat := Prod.fst(pair)</code></pre></td></tr></tbody></table>

**Source language distinction.** ProofScript tuple terms require **at least two elements**, mandatory commas between elements, and allow one trailing comma. Type-level products are still `Prod`/`×`, not TypeScript tuples. Direct `.1` numeric projection syntax is Lean; ProofScript’s `FieldSuffix` grammar requires an **Identifier** and does not explicitly promise numeric projections—use `Prod.fst(pair)` in ProofScript if available, or named structures.

### Propositions, quantifiers, proof versus Boolean equality

**Lean family:** the same native `Prop` declarations, Pi quantifier and `Exists` notation. **`pscv0` rule:** adopt the native spelling families intact: ASCII forms are not newly invented fallback grammar, and Unicode forms are first-class source syntax. The context decides whether an expression is a `Prop` or `Bool`.

| Lean 4.35.0-rc4 | ProofScript `pscv0` |
|---|---|
| `theorem same (n : Nat) : n = n := by rfl` | `theorem same(n: Nat): n = n := by { rfl }` |
| `example : ∃ n : Nat, n = 0 := ⟨0, rfl⟩` | `example : exists n : Nat, n = 0 := by { exact ⟨0, rfl⟩ }` |
| `example : ∀ n : Nat, n = n := by intro n; rfl` | `example : forall n : Nat, n = n := by { intro n
  rfl
}` (illustrative layout) |

#### Native mathematical symbol and text pairs

| Mathematical spelling | Lean-native textual / term equivalent | `pscv0` acceptance | Semantics / caution |
|---|---|---|---|
| `∀ x : A, P x` | `forall x : A, P x` | **both** | dependent Pi / universal quantifier |
| `∃ x : A, P x` | `exists x : A, P x` | **both** | `Exists`; the keyword is **`exists`**, not `exist` |
| `∃! x : A, P x` | `ExistsUnique (fun x : A => P x)` | when available in pinned Standard environment | unique existence; do not invent an `existUnique` keyword |
| `λ x => body` | `fun x => body` | **both** | ordinary lambda |
| `A → B` | `A -> B` | **both** | (non)dependent Pi arrow |
| `P ∧ Q` | `And P Q` | **both** | logical and, not Boolean `&&` |
| `P ∨ Q` | `Or P Q` | **both** | logical or, not Boolean `||` |
| `¬ P` | `Not P` | **both** | logical negation, not Boolean `!` |
| `P ↔ Q` | `Iff P Q` | **both** | logical equivalence |
| `a ≠ b` | `a = b → False` | standard not-equal notation | proposition; **different from** Boolean `!=` |
| `a ≤ b` | `a <= b` | **both** where a typeclass instance exists | proposition-valued comparison |
| `a ≥ b` | `a >= b` | **both** where a typeclass instance exists | proposition-valued comparison |
| `A × B` | `Prod A B` | **both** | ordinary product type |
| `Σ x : A, B x` | `Sigma (fun x : A => B x)` | both only when admitted library/profile provides `Sigma` | dependent data pair |
| `⟨a, h⟩` | type-directed constructor term | admit Lean constructor notation | useful for `Subtype`, `Exists`, structures |
| `x ∈ s`, `x ∉ s` | Lean membership/not-membership notation | admit **only if** required library/instances are present | do not globally invent set syntax |

**Token policy:** Unicode notation and existing Lean ASCII forms are **native aliases**, not unnecessary ProofScript sugar. Textual constant applications such as `And P Q` are Lean expressions, not extra infix keywords `and`/`or`. The singular `exist` is not an accepted quantifier. `=` is propositional equality, while `==` is Boolean equality through `BEq`; `≠` and `!=` are not interchangeable. Native input shortcuts (`\forall`, `\exists`, `\l`, `\to`, etc.) are editor conveniences, not source-token alternates.

**Relevant Lean docs:** [Quantifiers](https://lean-lang.org/doc/reference/latest/Basic-Propositions/Quantifiers/), [Subtype](https://lean-lang.org/doc/reference/latest/Basic-Types/Subtypes/), [The Tactic Language](https://lean-lang.org/doc/reference/latest/Tactic-Proofs/The-Tactic-Language/).

### Boolean/propositional `if`, dependent `if`, and `if let`

**Lean family:** `ite`, dependent `dite`, and native pattern-matching conditional `if let`. **`pscv0` modification:** one braced conditional spelling, without TypeScript truthiness or unbraced `then`/`else` variants in `.ps`. The Lean `.lean` source column retains native spelling. The binder `h : P` is a **proof binder**, not a spaced function-call argument.

| Lean 4.35.0-rc4 | `pscv0` canonical form |
|---|---|
| `if b then 1 else 0` | `if (b) { 1 } else { 0 }` |
| `if h : i < xs.size then some xs[i]'h else none` | `if (h : i < xs.size) { some(xs[i]'h) } else { none }` |
| `if let some n := value then n else 0` | `if let .some n := value { n } else { 0 }` |

**Lean 4 grammar (schematic):**

```text
term ::= ... | 'if' condition 'then' term 'else' term
            | 'if' binderIdent ':' condition 'then' term 'else' term
            | 'if' 'let' pattern ':=' term 'then' term 'else' term
```

**`pscv0` modification (schematic):**

```text
term ::= ... | 'if' '(' term ')' '{' term '}' 'else' '{' term '}'
            | 'if' '(' binderIdent ':' term ')' '{' term '}' 'else' '{' term '}'
            | 'if' 'let' selectedLeanPattern ':=' term
                    '{' term '}' 'else' '{' term '}'
```

`if let` is not a duplicate of an ordinary Boolean condition; it **binds the pattern's variables in the successful branch**, expanding to Lean `match ... with | pattern => ... | _ => ...`. The dependent `if (h : P)` form provides `h : P` to the first branch and `h : ¬P` to the second, as Lean's `dite` does. Ordinary `if` accepts `Bool` or decidable `Prop` according to the Lean-grounded elaboration rules, without JS truthiness. The body braces each enclose **one term**, not a statement list.

**Proposed `pscv0` example:**

```proofscript
function fromOption(x: Option Nat): Nat := {
  if let .some n := x {
    n
  } else {
    0
  }
}
```

**Important:** `if p then a else b` continues to be **invalid `.ps` conditional syntax**; it is not silently re-enabled by the new Lean-first feature selection. A parsed `if` in a proof tactic (as opposed to a term) remains a distinct *tactic* grammar category subject to the pinned tactic environment. [Lean conditionals](https://lean-lang.org/doc/reference/latest/Terms/Conditionals/).

### `nomatch`, `matches`, and term-level pattern bindings

Lean's `nomatch e` constructs a value from an impossible case only when exhaustiveness proves the absence of alternatives. `e matches p` is a Boolean pattern test, not a general dynamic cast. Adopt both native term forms, subject to the selected pattern grammar and checked Lean elaboration. Pattern `let` bindings are admitted where Lean can determine an irrefutable or properly handled pattern; do not allow silent runtime match failure.

| Lean 4.35.0-rc4 | `pscv0` |
|---|---|
| `def impossible (e : Empty) : Nat := nomatch e` | `function impossible(e: Empty): Nat := nomatch e` |
| `def isSome (x : Option Nat) : Bool := x matches some _` | `function isSome(x: Option Nat): Bool := x matches .some _` |
| native pattern `let` in a supported term or `do` context | same selected Lean binding grammar inside canonical `.ps` braces |

There is no new `as`, `typeof`, structural-union narrowing, or unsafe cast syntax. The pattern's constructor families are checked against the scrutinee's admitted Lean type, and impossible matches must truly be empty. [Lean pattern matching](https://lean-lang.org/doc/reference/latest/Terms/Pattern-Matching/).

### Base `do`: monadic bind, simple `let`, `pure`, `return`

**Feature / profile:** Shared monadic semantics; a selected Lean `do` grammar subset  
**Source basis:** Ch. 10 (basic do); A.14; Appendix B

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= &quot;do&quot; doSeq
doSeqItem ::= &quot;let&quot; ident &quot;:=&quot; term | &quot;let&quot; ident &quot;←&quot; term
            | term | &quot;return&quot; term | ...</code></pre></td><td valign="top"><pre><code>term ::= &quot;do&quot; &quot;{&quot; psDoSeq &quot;}&quot;
psDoItem ::= &quot;let&quot; ident &quot;:=&quot; term
           | &quot;let&quot; ident &quot;←&quot; term | term | &quot;return&quot; term
// Lean monadic semantics; braced/newline restricted subset</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def compute : Id Nat := do
  let x ← pure 1
  pure (x + 1)</code></pre></td><td valign="top"><pre><code>function compute(): Id Nat := do {
  let x ← pure 1
  pure(x + 1)
}</code></pre></td></tr></tbody></table>

**Source language distinction.** This is **base ProofScript** (`PSCV0`) syntax, distinct from the richer PSCV0 verified `do`. The base subset has term statements, simple immutable `let`, identifier/wildcard monadic bind, and `pure`/`return`. Its separator is a normalized newline; Lean permits a larger `do` language and certain semicolon spellings.

### Type-directed coercions

**Feature / profile:** Shared class-based coercions; PS deterministic bounded algorithm  
**Source basis:** Ch. 12, 16.7, 22.10; A.12

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;instance&quot; declSig declVal
term ::= term | ...  // coercions are type-directed, not term syntax</code></pre></td><td valign="top"><pre><code>command ::= &quot;instance&quot; psBinders? &quot;:&quot; term &quot;where&quot; &quot;{&quot; psField* &quot;}&quot;
term ::= selectedLeanTerm  // no extra cast syntax
// Coercions limited by selected Lean instance environment</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>structure Wrapped where
  value : Nat
instance : Coe Wrapped Nat where
  coe x := x.value</code></pre></td><td valign="top"><pre><code>structure Wrapped where {
  value: Nat
}
instance : Coe Wrapped Nat where {
  coe(x: Wrapped): Nat := x.value
}</code></pre></td></tr></tbody></table>

**Source language distinction.** Coercions are **compile-time/type-directed** insertion, not runtime casts or JS coercion. ProofScript Standard may try one direct ordinary coercion, `CoeFun` to function, or `CoeSort` to sort; it excludes arbitrary chains and implicit auto-lifting. The actual instance declarations must belong to the visible bounded Standard registry.

## 4. Structures, records, classes, and algebraic data

### Structure declarations

**Feature / profile:** Shared structures; PSCV0 sugar outer braces  
**Source basis:** Ch. 11; A.2, A.10; Appendix B

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;structure&quot; declId declSig? (&quot;where&quot; structFields)?
structFields ::= structField*  // indentation-sensitive</code></pre></td><td valign="top"><pre><code>command ::= &quot;structure&quot; declId psBinders &quot;where&quot; &quot;{&quot; structFields &quot;}&quot;
// Reuse Lean&#x27;s structField, structFields, dependent field checking
// Modification: braces delimit the original Lean field layout</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>structure User where
  id : Nat
  name : String
  active : Bool</code></pre></td><td valign="top"><pre><code>structure User where {
  id: Nat
  name: String
  active: Bool
}</code></pre></td></tr></tbody></table>

**Source language distinction.** Both have nominal structure types and Lean-grounded fields. Structure **declaration fields are not comma-separated** in ProofScript; braces only group the Lean-like layout fields. Commas belong in structure **values**, not declarations.

### Record construction and record updates

**Feature / profile:** Shared record syntax under tighter ProofScript elaboration  
**Source basis:** Ch. 11; A.6, A.10

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= &quot;{&quot; structInstField (&quot;,&quot; structInstField)* &quot;}&quot;
     | &quot;{&quot; term &quot;with&quot; structInstField (&quot;,&quot; structInstField)* &quot;}&quot;
// Lean also supports inferred shorthand, omitted fields and type annotation</code></pre></td><td valign="top"><pre><code>term ::= &quot;{&quot; psRecordField (&quot;,&quot; psRecordField)* &quot;,&quot;? &quot;}&quot;
     | &quot;{&quot; term &quot;with&quot; psRecordField (&quot;,&quot; psRecordField)* &quot;,&quot;? &quot;}&quot;
psRecordField ::= ident &quot;:=&quot; term
// Same nominal Lean structure, stricter field syntax</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def alice : User := { id := 1, name := &quot;Alice&quot;, active := false }
def activate (u : User) : User := { u with active := true }</code></pre></td><td valign="top"><pre><code>const alice: User := {
  id := 1,
  name := &quot;Alice&quot;,
  active := false,
}
function activate(u: User): User := {
  { u with active := true }
}</code></pre></td></tr></tbody></table>

**Source language distinction.** Record **values** and updates require commas between fields and allow a final comma. ProofScript requires an expected structure type to elaborate a record construction and permits defaults only if declared; it does not guess a shape or fill missing fields through `Inhabited`. Dependent updates must type-check after reconstruction.

### Projections and static method selection

**Feature / profile:** Shared  
**Source basis:** Ch. 11, 22.11; A.6

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= term &quot;.&quot; ident | ...
// Lean generalized field notation; same structure projections</code></pre></td><td valign="top"><pre><code>term ::= term &quot;.&quot; ident
     | term &quot;.&quot; ident &quot;(&quot; psCallArgs? &quot;)&quot;
// Call postfix is PSCV0 sugar; resolution stays static</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def nameOf (u : User) : String := u.name</code></pre></td><td valign="top"><pre><code>function nameOf(u: User): String := u.name</code></pre></td></tr></tbody></table>

**Source language distinction.** Both resolve a declared structure field statically. ProofScript's static generalized field search is deterministic, and method-call parentheses remain adjacency-sensitive.

### Classes and typeclass instances

**Feature / profile:** Shared typeclass semantics; PS outer-brace grammar  
**Source basis:** Ch. 12; A.2, A.10, A.12

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;class&quot; declId declSig? &quot;where&quot; structFields
          | &quot;instance&quot; declSig &quot;where&quot; structInstFields</code></pre></td><td valign="top"><pre><code>command ::= &quot;class&quot; declId psBinders &quot;where&quot; &quot;{&quot; structFields &quot;}&quot;
          | &quot;instance&quot; psInstanceHeader &quot;where&quot; &quot;{&quot; psInstanceFields &quot;}&quot;
// Class fields are Lean structFields; instance fields use Lean categories</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>class Sized (α : Type) where
  size : α → Nat

instance : Sized String where
  size s := s.length</code></pre></td><td valign="top"><pre><code>class Sized(α: Type) where {
  size: α -&gt; Nat
}

instance : Sized String where {
  size(s: String): Nat := s.length
}</code></pre></td></tr></tbody></table>

**Source language distinction.** Classes are Lean typeclasses, **not** OO classes. ProofScript class declarations preserve field layout and instance fields are **newline-only** sequences (no comma/semicolon), checked against the class field telescope. Lean additionally admits syntaxes and semicolon forms outside the ProofScript Standard grammar.

### Instance-implicit arguments and instance priorities

**Feature / profile:** Shared binders; PS deterministic instance resolution  
**Source basis:** Ch. 12, 22.9; A.2

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>binder ::= &quot;[&quot; term &quot;]&quot;
command ::= &quot;instance&quot; (&quot;(&quot; &quot;priority&quot; &quot;:=&quot; nat &quot;)&quot;)?
            declSig &quot;where&quot; structInstFields</code></pre></td><td valign="top"><pre><code>binder ::= Lean.instBinder
command ::= &quot;instance&quot; psPriority? psInstanceHeader
            &quot;where&quot; &quot;{&quot; psInstanceFields &quot;}&quot;
// Retain Lean class resolution; restrict priority and field separators</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def sizeOf {α : Type} [Sized α] (x : α) : Nat :=
  Sized.size x</code></pre></td><td valign="top"><pre><code>function sizeOf {α: Type}[Sized α](x: α): Nat := {
  Sized.size(x)
}</code></pre></td></tr></tbody></table>

**Source language distinction.** Instance-implicit Pi binders work in both. ProofScript freezes candidate order (lexical locals before prioritized visible globals), with `low=100`, `mid=500`, `default=1000`, `high=10000`. This is a source-observable constraint, not a new `class` syntax.

### Law fields in classes and structures

**Feature / profile:** Shared expressivity; PSCV0 encourages verified abstractions  
**Source basis:** Ch. 12 (`pscv.class.laws`)

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;class&quot; declId declSig? &quot;where&quot; structFields
structField ::= ident &quot;:&quot; term | ...</code></pre></td><td valign="top"><pre><code>command ::= &quot;class&quot; declId psBinders &quot;where&quot; &quot;{&quot; structFields &quot;}&quot;
structField ::= Lean.structField
// Law: any field with a Prop-typed result, checked by Lean</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>class IdentityCodec (α : Type) where
  encode : α → α
  roundTrip : ∀ x : α, encode x = x</code></pre></td><td valign="top"><pre><code>class IdentityCodec(α: Type) where {
  encode: α -&gt; α
  roundTrip: forall x : α, encode(x) = x
}</code></pre></td></tr></tbody></table>

**Source language distinction.** A law is an ordinary field of a proposition type. An instance must supply proof evidence for it just as it supplies executable operations; this adds no novel kernel primitive.

### Inductive types and constructor declarations

**Feature / profile:** Shared inductive theory; PS constructor/header grammar  
**Source basis:** Ch. 13; A.2, A.11

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;inductive&quot; declId declSig? &quot;where&quot; ctor*
ctor ::= &quot;|&quot; ident binder* (&quot;:&quot; term)?</code></pre></td><td valign="top"><pre><code>command ::= &quot;inductive&quot; declId psBinders (&quot;:&quot; term)?
            &quot;where&quot; &quot;{&quot; psCtor* &quot;}&quot;
psCtor ::= &quot;|&quot; ident (psExplicitGroup | Lean.binder)* (&quot;:&quot; term)?
// Constructors checked by Lean inductive type checker</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>inductive Outcome (ε : Type) (α : Type) where
  | ok (value : α)
  | error (error : ε)</code></pre></td><td valign="top"><pre><code>inductive Outcome(ε: Type, α: Type) where {
  | ok(value: α)
  | error(error: ε)
}</code></pre></td></tr></tbody></table>

**Source language distinction.** ProofScript uses a comma-grouped parameter telescope and *canonically* braces the `|` alternatives. The `.ps` grammar requires the selected braced form; ordinary `.lean` syntax retains native Lean layout. Constructor fields reuse unified explicit parameter groups. Strict positivity, parameters/indices, and recursors remain Lean-grounded; this is still not Lean’s unrestricted equation compiler.

### Qualified and shorthand constructors

**Feature / profile:** Shared constructor semantics; PSCV0 sugar call suffix  
**Source basis:** Ch. 13; A.6; [elab.constructor]

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= ident argument* | &quot;.&quot; ident argument* | ...
// Elaborator resolves anonymous-namespace constructor notation</code></pre></td><td valign="top"><pre><code>term ::= ident &quot;(&quot; psCallArgs? &quot;)&quot;
     | &quot;.&quot; ident &quot;(&quot; psCallArgs? &quot;)&quot;
     | selectedLeanConstructorTerm
// Both lower to ordinary Lean constructor applications</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def ok : Outcome String Nat := Outcome.ok 42
def short : Outcome String Nat := .ok 42</code></pre></td><td valign="top"><pre><code>const ok: Outcome String Nat := Outcome.ok(42)
const short: Outcome String Nat := .ok(42)</code></pre></td></tr></tbody></table>

**Source language distinction.** Shorthand requires a known expected inductive type and a uniquely determined constructor. Neither language thereby uses dynamic enum-string dispatch.

### Native `deriving` and checked generated instances

**Decision P0:** add Lean's native trailing `deriving` clause for supported `structure` and `inductive` declarations. Do not introduce TypeScript decorators, an implicit universal structural-equality operator, or a new `@derive` alias.

| Lean 4.35.0-rc4 | `pscv0` |
|---|---|
| <pre>structure User where
  id : Nat
  name : String
  deriving Repr, BEq</pre> | <pre>structure User where {
  id: Nat
  name: String
} deriving Repr, BEq</pre> |
| <pre>inductive Status where
  | ok (n : Nat)
  | error (s : String)
  deriving Repr, BEq</pre> | <pre>inductive Status where {
  | ok(n: Nat)
  | error(message: String)
} deriving Repr, BEq</pre> |

**Lean grammar (schematic):** `derivingClause ::= ('deriving' derivingClass (',' derivingClass)*)?`; `pscv0` adds this *same native trailing clause after the closing structural braces*. The parser's exact declaration ownership and instance derivation results are fixed to RC4.

**Initial allowlist:** `Repr`, `BEq`, `DecidableEq`, `Inhabited`, `Hashable`, subject to each handler's actual applicability and typeclass instance prerequisites. Additional built-ins (e.g. `LawfulBEq`, `Ord`, `SizeOf`) can be added via an explicitly revised environment snapshot after semantic review. The fact that Lean supports deriving a class does **not** mean all classes can always be derived for all user types.

**Safety:** the deriving handler is elaboration machinery. All emitted declarations and proof terms must satisfy normal Lean-grounded kernel checking, and registration affects the deterministic environment. Generated executable methods are *not* proofs of unspecified algebraic laws. Standalone native `deriving instance ... for ...` may be admitted in a later explicit environment revision; the initial canonical `.ps` form is the trailing declaration clause. [Lean deriving instances](https://lean-lang.org/doc/reference/latest/Type-Classes/Deriving-Instances/).

### Indexed/dependent inductive families

**Feature / profile:** Shared dependent inductives; restricted PS source forms  
**Source basis:** Ch. 13; A.11; Appendix I `LEAN-CORE-IND`

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;inductive&quot; declId binder* &quot;:&quot; term &quot;where&quot; ctor*
ctor ::= &quot;|&quot; ident binder* &quot;:&quot; term</code></pre></td><td valign="top"><pre><code>command ::= &quot;inductive&quot; declId psBinders &quot;:&quot; term
            &quot;where&quot; &quot;{&quot; psCtor* &quot;}&quot;
psCtor ::= &quot;|&quot; ident psBinders? &quot;:&quot; term
// Preserve Lean parameters/indices and dependent result types</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>inductive Vec (α : Type) : Nat → Type where
  | nil : Vec α 0
  | cons (n : Nat) (value : α) (tail : Vec α n) : Vec α (n + 1)</code></pre></td><td valign="top"><pre><code>inductive Vec(α: Type): Nat -&gt; Type where {
  | nil : Vec α 0
  | cons(n: Nat, value: α, tail: Vec α n) : Vec α (n + 1)
}</code></pre></td></tr></tbody></table>

**Source language distinction.** Indices may occur in constructor result types. The **new** `pscv0` selection explicitly admits Lean's named/generalizing discriminants for selected dependent matches (§4), but still does not promise that every unrestricted Lean equation-compiler/motive inference variant is supported. Each admitted dependent elimination must elaborate to checked Lean terms.

### Rich selected native Lean patterns and pattern syntax

**Decision:** replace the earlier restricted `psc2` single-pattern grammar with the *selected RC4 Lean pattern family*. `pscv0` adopts Lean's constructor, nested, tuple, wildcard, variable, `Nat`/`Bool` literal, built-in list-style, and admitted type-specific pattern notations (including the pinned `Nat` successor form `k + 1`). Type-specific built-in patterns are required only when their precise handler/notation is included in the frozen environment; arbitrary imported `@[match_pattern]` handlers do not silently become active in the closed default grammar.

**Lean grammar (schematic):**

```text
pattern ::= Lean.pattern                  -- selected pinned cases only
matchAlt ::= '|' pattern (',' pattern)* '=>' term
          | '|' alternativePatternLists '=>' term
```

**`pscv0` grammar selection (schematic):**

```text
pattern ::= selectedLeanPattern
matchAlt ::= '|' selectedLeanPattern (',' selectedLeanPattern)* '=>' term
matchTerm ::= 'match' selectedLeanDiscriminants 'with' '{' matchAlt+ '}'
```

A scrutinee's family determines which constructors and patterns are admissible. In particular, `k + 1` in `Nat` pattern position is inherited Lean successor-pattern sugar rather than general arithmetic pattern matching: `1 + k`, `k + m` with arbitrary variable `m`, or `k - 1` are not accepted as equivalent constructor patterns. The same `.ps` term grammar governs patterns nested in other terms; dependent patterns may induce proof obligations and elaborated motive information.

### Exhaustive multi-discriminant and dependent `match`

**Decision:** the new `pscv0` baseline admits Lean's **multiple match discriminants, named discriminants, and explicit dependent generalization** in the selected term grammar, instead of the previous single-discriminant subset. This is essential for dependent algorithms and theorem proving, not merely syntax comfort. `pscv0` retains the one **braced** body form and source-order alternatives; it does not add a separate runtime matching model.

| Lean 4.35.0-rc4 | `pscv0` modified punctuation |
|---|---|
| <pre>def choose (x : Option Nat) (fallback : Nat) : Nat :=
  match x with
  | none => fallback
  | some n => n</pre> | <pre>function choose(x: Option Nat, fallback: Nat): Nat := {
  match x with {
    | .none => fallback
    | .some n => n
  }
}</pre> |
| <pre>def both (x y : Option Nat) : Bool :=
  match x, y with
  | some _, some _ => true
  | _, _ => false</pre> | <pre>function both(x: Option Nat, y: Option Nat): Bool := {
  match x, y with {
    | .some _, .some _ => true
    | _, _ => false
  }
}</pre> |

**Dependent match forms (schematic):** `match (generalizing := true) discriminants with { alternatives }` and `match h : discriminant with { alternatives }` select Lean's actual dependent elaboration and optional equality-hypothesis behavior. The `(generalizing := true)` after the `match` keyword belongs to Lean's **match syntax category**, not to a function call; it does not violate `PSCV0-APP-02`. The exact motive/generalization rules and accepted syntactic placement must be checked against the pinned parser.

**Acceptance conditions:** check all patterns against corresponding discriminants; require the same number of pattern positions per alternative; preserve first-matching-alternative semantics; reject inexhaustive matches, duplicate binders, unsupported pattern modifiers, and unprovable dependent elaboration. Lower successful terms to ordinary Lean recursor/equation-compiler output, then check them with the Lean-grounded kernel acceptance relation. **Do not claim arbitrary user-defined pattern macros or unlimited equation syntax without registered, pinned expansion rules.**

### Equation-style definitions

Lean supports convenient equation-style declarations. Adopt the **selected native Lean equation compiler family** in `pscv0` as a P1 proof/programming enhancement once its exact grammar and restrictions are mapped to `pscv0` declaration binders and canonical body braces. This family has **no new `function` equation keyword** beyond the established alias; direct syntax acceptance remains *pending* until complete positive/negative parser, termination, and elaboration cases are added. Multi-discriminant `match` is P0 and must not wait for P1 equation-style syntax.

**Source:** [Lean 4.35 pattern matching](https://lean-lang.org/doc/reference/latest/Terms/Pattern-Matching/) and [recursive definitions](https://lean-lang.org/doc/reference/latest/Definitions/Recursive-Definitions/).

## 5. Recursion and computability

### Total structural recursion

**Feature / profile:** Shared total recursion; stricter PS base checker  
**Source basis:** Ch. 18.1–18.7; Ch. 27 `List.length` example

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;def&quot; declId declSig? declVal
// Recursive definitions may be accepted using recursor/termination proof</code></pre></td><td valign="top"><pre><code>command ::= &quot;def&quot; declId psBinders (&quot;:&quot; term)? psDeclVal
          | &quot;function&quot; declId psBinders (&quot;:&quot; term)? psDeclVal
// Recursive calls require an admitted Lean-checkable termination proof</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def length {α : Type} (xs : List α) : Nat :=
  match xs with
  | [] =&gt; 0
  | _ :: tail =&gt; 1 + length tail</code></pre></td><td valign="top"><pre><code>function length {α: Type}(xs: List α): Nat := {
  match xs with {
    | .nil =&gt; 0
    | .cons _ tail =&gt; 1 + length(tail)
  }
}</code></pre></td></tr></tbody></table>

**Source language distinction.** The inherited base reference allowed only structural recursion; this `pscv0` revision also retains the already proposed bounded `termination_by` well-founded path. In the structural case, recursive calls must pass a designated strict constructor subterm. An arithmetic expression such as `n - 1` is not accepted as *structural-subterm evidence*. Lean offers more termination elaboration routes.

### Mutual recursion

**Feature / profile:** Shared mutual definitions with PS structural restrictions  
**Source basis:** Ch. 18.6; A.2

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;mutual&quot; declaration+ &quot;end&quot;
// Lean mutual groups are declaration groups</code></pre></td><td valign="top"><pre><code>command ::= &quot;mutual&quot; (psDef | psFunction)+ &quot;end&quot;
// Members lower to Lean mutual declarations</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>mutual
  def even (n : Nat) : Bool :=
    match n with
    | 0 =&gt; true
    | k + 1 =&gt; odd k
  def odd (n : Nat) : Bool :=
    match n with
    | 0 =&gt; false
    | k + 1 =&gt; even k
end</code></pre></td><td valign="top"><pre><code>mutual
  function even(n: Nat): Bool := {
    match n with {
      | 0 =&gt; true
      | k + 1 =&gt; odd(k)
    }
  }
  function odd(n: Nat): Bool := {
    match n with {
      | 0 =&gt; false
      | k + 1 =&gt; even(k)
    }
  }
end</code></pre></td></tr></tbody></table>

**Source language distinction.** ProofScript demands one designated structural argument for each member of the recursive strongly connected component, strictly decreasing across every recursive edge. Both `| .succ k => ...` and `| k + 1 => ...` are permitted on `Nat`: Lean elaborates the second to an equivalent successor-constructor pattern, so the call on `k` is a call on a strict subterm. **This is not permission to recursively call on `n - 1` without separate termination evidence.** The two spellings belong to the same native Lean semantics; arithmetic-oriented examples prefer `k + 1`. See the [Lean recursive-definition reference](https://lean-lang.org/doc/reference/latest/Definitions/Recursive-Definitions/).

### Well-founded recursion, `termination_by`, and `decreasing_by`

**Feature / profile:** PSCV0 verification addition over shared well-founded foundation  
**Source basis:** Ch. 18.8; A.18

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>declVal ::= &quot;:=&quot; term terminationSuffix? whereDecls?
terminationSuffix ::= &quot;termination_by&quot; term
                    (&quot;decreasing_by&quot; tacticSeq)?</code></pre></td><td valign="top"><pre><code>psDeclVal ::= &quot;:=&quot; term psTermination? psWhere?
psTermination ::= &quot;termination_by&quot; term
                  (&quot;decreasing_by&quot; psProof)?
// Use Lean&#x27;s decreasing proof kernel checks</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def down (n : Nat) : Nat :=
  if n == 0 then 0 else down (n - 1)
termination_by n
decreasing_by omega</code></pre></td><td valign="top"><pre><code>function down(n: Nat): Nat := {
  if (n == 0) { 0 } else { down(n - 1) }
}
termination_by n
decreasing_by by {
  omega
}</code></pre></td></tr></tbody></table>

**Source language distinction.** PSCV0 extends the base structural-only profile with explicit well-founded/measure recursion. Each call must produce an accepted decrease proof; `decreasing_by` is proof-construction syntax. Unlike Lean's richer termination forms (for example, `termination_by structural`), this draft selects the native `termination_by term` and optional `decreasing_by` proof route. The precise acceptance restrictions remain profile choices rather than an alternative core recursion theory. The example is intended PSCV0 syntax; its verification is not execution-tested.

### `partial`, `unsafe`, `axiom`, `noncomputable`

**Feature / profile:** Restricted / excluded in PSCV0  
**Source basis:** Ch. 8, 18, 25; A.2, A.18; Appendix F

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;partial&quot; &quot;def&quot; ... | &quot;unsafe&quot; &quot;def&quot; ...
          | &quot;axiom&quot; declId declSig | &quot;noncomputable&quot; &quot;def&quot; ...</code></pre></td><td valign="top"><pre><code>command ::= &quot;noncomputable&quot;? psDefOrFunction
          | selectedLeanTheorem | selectedLeanAbbrev | ...
// Remove user axiom, unsafe and partial source alternatives</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>partial def loopForever : Nat := loopForever
axiom unproved : 2 = 3
noncomputable def choice (h : ∃ n : Nat, n = n) : Nat := Classical.choose h</code></pre></td><td valign="top"><pre><code>-- INVALID in pscv0:
-- partial function forever(): Nat := forever()
-- axiom arbitrary : False
-- unsafe def unchecked := ...
-- noncomputable executable dependency
-- Allowed: noncomputable in proof/spec-only declarations
-- where it is well typed and policy permitted.</code></pre></td></tr></tbody></table>

**Source language distinction.** Lean permits language constructs that `pscv0` deliberately rejects as `.ps` source (`partial`, `unsafe`), even for ordinary checked programs. The older historical ProofScript reference admitted some `partial` syntax, but **this revised `pscv0` language does not**. Separate non-PSCV/Lean runtime adapters may be used only as classified external boundaries. Imported assumptions and classical/noncomputable data are bounded by the selected proof/verified-executable policy. The Lean block demonstrates **syntax**, not a proof of sensible/safe code; the `Classical.choice` example is schematic.

## 6. Proof language, tactics, and attributes

### Theorems, proofs, and explicit subgoal ownership

**Lean family:** `theorem`, `example`, `by` tactic sequences, Lean proof terms. **`pscv0` modification:** comma-separated explicit declaration binders and **mandatory `by { ... }`** for a multi-tactic proof. We adopt Lean's actual tactic **middle-dot** bullet `·` (U+00B7). The ASCII period `.` is field notation or punctuation, **not a Lean goal bullet**.

| Lean 4.35.0-rc4 | ProofScript `pscv0` |
|---|---|
| <pre>theorem andProof (P Q : Prop) (hp : P) (hq : Q) : P ∧ Q := by
  constructor
  · exact hp
  · exact hq</pre> | <pre>theorem andProof(P: Prop, Q: Prop, hp: P, hq: Q): P ∧ Q := by {
  constructor
  · exact hp
  · exact hq
}</pre> |

**Why subgoal bullets matter:** `constructor` on `P ∧ Q` introduces two proof goals. `· exact hp` focuses the first and requires it to close; `· exact hq` handles the second. Unfocused sequential `exact hp` then `exact hq` can happen to work, but provides weaker local proof structure. Native `case` and `next` are alternative **Lean** ways to focus goals when identifying constructor/case names is clearer. They are not new ProofScript keywords.

**Lean grammar (schematic):**

```text
term    ::= ... | 'by' tacticSeq
tactic  ::= ... | '·' tacticSeq | 'case' caseName '=>' tacticSeq
                 | 'next' binders? '=>' tacticSeq
                 | selectedLeanTactic
```

**ProofScript restriction:**

```text
term ::= ... | 'by' '{' selectedLeanTacticSeq '}'
-- selectedLeanTacticSeq accepts native `·`, `case`, `next` for goal ownership
-- no separate `.` ASCII bullet production
```

The *source* tactic set is fixed/versioned rather than extended by arbitrary installed macros. Tactics generate proof terms, which are checked by the Lean-grounded kernel. `case`/`next` are permitted **only** with the native pinned parsing and goal-focusing behavior; no JS-like switch-case interpretation. **The tactic grammar is not an escape from `PSCV0-APP-02`:** `exact (hp)` may start a grouped tactic-argument term, and `exact h(hp)` may apply a proof function, but `exact h (hp)` must not be accepted as a spaced parenthesized application in `.ps`.

### Proof terms, `have`, `show`, `suffices`, `calc`

| Lean 4.35.0-rc4 | ProofScript `pscv0` |
|---|---|
| <pre>theorem trans (a b c : Nat) (h1 : a = b) (h2 : b = c) : a = c := by
  calc
    a = b := h1
    _ = c := h2</pre> | <pre>theorem trans(a: Nat, b: Nat, c: Nat, h1: a = b, h2: b = c): a = c := by {
  calc
    a = b := h1
    _ = c := h2
}</pre> |

Adopt Lean `have`, `show`, `suffices`, and `calc` with their native checked meanings. `calc` need not be restricted to equality-only if a fixed, pinned Lean relation/transitivity instance is present; arbitrary custom notation/attributes remain outside the closed source grammar. Do not create alternative ProofScript spellings for these facilities.

### Selected native Lean tactics and goal control

| Group | Accepted native Lean tactic heads / combinators | `pscv0` decision |
|---|---|---|
| Intro & constructors | `intro`, `intros`, `constructor`, `constructor!`, `apply`, `exact`, `refine`, `assumption`, `rfl` | native spellings; proof term checked |
| Elimination | `cases`, `induction`, `rcases`, `rintro`, `obtain` | selected pinned forms |
| Rewriting / simplification | `rw`, `simp`, `simp only`, `simpa`, `simp_all`, `dsimp`, `change`, `unfold` | native spellings |
| Logical methods | `by_cases`, `by_contra`, `exfalso`, `use`, `ext`, `decide` | native spellings |
| Automation | `omega`, `grind`, `exact?` | proof-producing, no oracle acceptance |
| Intermediate facts | `have`, `show`, `suffices`, `calc`, `classical` | native Lean constructs |
| Goal focus | **`·`**, `case`, `next`, `all_goals`, `any_goals`, `<;>` | accept selected pinned control forms, never ASCII dot bullet |
| Arbitrary syntax plugins | `syntax`, `macro_rules`, user-defined tactic parsers | not available in closed `.ps`; an **explicit pinned proof environment** may admit selected proof-producing registrations |

**Important:** Lean's `;` inside the tactic language means tactic composition, **not** an ordinary program statement separator. The canonical `.ps` proof uses newline-separated tactics and `·` bullets. If a pinned native tactic combinator is admitted, its Lean meaning is preserved; it is not reinterpreted as JavaScript `;`.

**Examples (two native Lean goal-selection mechanisms in `.ps`):**

```proofscript
-- Canonical branch bullets
theorem pairLaw(P: Prop, Q: Prop, hp: P, hq: Q): P ∧ Q := by {
  constructor
  · exact hp
  · exact hq
}

-- Native case selection can also be used when there is a case name
theorem orLaw(P: Prop, Q: Prop, hp: P): P ∨ Q := by {
  exact Or.inl hp
}
```

`· exact` is one tactic branch and can contain a nested tactic sequence when required by Lean's proof grammar; a bullet must discharge the focused subgoal. Subgoal ownership is important for sound human/AI proof maintenance but is not a kernel axiom.

### Versioned proof-producing extension environment (without extending proof trust)

**Decision P1:** `pscv0` should be usable with substantial theorem libraries rather than only its initial small tactic list. Lean proof packages sometimes require custom tactic syntax, notation, attributes, and proof macros. The native proof extension mechanism is useful, but the default closed grammar must not be modified silently by an arbitrary ordinary import.

| Mode | Source-level admission | Proof acceptance |
|---|---|---|
| **Standard `pscv0`** | Frozen selected Lean tactic/notation and declaration registrations | Independently check the elaborated proof term and active axiom closure |
| **Explicit pinned proof environment** | Selected additional tactic/notation syntax declared by named exact extension manifest (package revision, handlers, parser registrations, imported theorems, priorities) | Same kernel/axiom policy; loaded code cannot grant verified status |
| **Unsupported/unpinned extension** | Reject source syntax or registry mutation that is not in the active environment identity | Never accept due to a plugin's “success” flag |

**No blanket imports of Lean's unrestricted Meta language.** An ordinary source package must not invoke ambient `register...` commands to change the certified grammar behind the compiler's back. A consciously chosen theorem-development extension is an explicit environment choice, and its generated proof obligations undergo exactly the same checks as ordinary proofs. The fact that Lean tactics construct kernel-checkable proof terms does not make plugin execution or generated axioms independently trustworthy.

**Proof language capability target:** native `·`, `case`, `next`, `focus`, `all_goals`, `any_goals`, admitted tactic combinators (`<;>` where pinned), structured `calc` (not arbitrarily equality-only), `simp`/`simp only`, `omega`, `grind`, selected named rewrite locations, and proof-term syntax required by supported libraries. Syntax not present in RC4 Standard is opt-in, **not** magically part of the default. In particular, `aesop`, `linarith`, or mathlib-specific tactics require their defining libraries/registered environment and are not guaranteed merely by mentioning their names.

**Term grammar remains uniform.** An extension that accepts a term inside a tactic argument or quoted source must either parse that term using the same `pscv0` application rule or be explicitly isolated under a different, auditable syntax category; it must not silently turn `f (x)` back into a legal ordinary `.ps` application. String interpolation and editor quick fixes are covered by the same policy.

Lean research: [custom tactics](https://lean-lang.org/doc/reference/latest/Tactic-Proofs/Custom-Tactics/), [tactic proof states](https://lean-lang.org/doc/reference/latest/Tactic-Proofs/), [validating proofs and axioms](https://lean-lang.org/doc/reference/latest/ValidatingProofs/).

### Source attributes and instance/default-instance registrations

**Feature / profile:** Shared base attributes; PS closed registry  
**Source basis:** Ch. 24.5–24.6; A.2

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>attributes ::= &quot;@[&quot; attr (&quot;,&quot; attr)* &quot;]&quot;
command ::= attributes? declaration</code></pre></td><td valign="top"><pre><code>attributes ::= &quot;@[&quot; (&quot;simp&quot; | &quot;instance&quot; | &quot;default_instance&quot;)
                (&quot;,&quot; (&quot;simp&quot; | &quot;instance&quot; | &quot;default_instance&quot;))* &quot;]&quot;
command ::= attributes? psDeclaration
// Select Lean attribute semantics, not arbitrary plugin handlers</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>@[simp] theorem add_zero_right (n : Nat) : n + 0 = n := by
  simp</code></pre></td><td valign="top"><pre><code>@[simp] theorem addZeroRight(n: Nat): n + 0 = n := by {
  simp
}</code></pre></td></tr></tbody></table>

**Source language distinction.** Only `simp`, `instance`, and `default_instance` are exposed as user attributes by the ProofScript Standard grammar. Imported source may add admitted instance and simp entries but not arbitrary syntax or proof authority. `set_option`, `syntax`, `macro`, `deriving`, and custom attribute handlers are outside Standard source.

## 7. PSCV0 verification syntax beside Lean verification forms

### Pure function contracts: `requires` and `ensures`

**Feature / profile:** PSCV0 verification contract syntax; Lean intrinsic prototype (experimental)  
**Source basis:** Ch. 21.1–21.7; A.16, A.18; Appendix I.8A

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;def&quot; declId declSig
            &quot;given&quot;? &quot;requires&quot;? &quot;ensures&quot;? declVal
// Lean 4.35-rc4 experimental intrinsic contracts</code></pre></td><td valign="top"><pre><code>command ::= (&quot;def&quot; | &quot;function&quot;) declId psBinders
            (&quot;:&quot; term)? psContract* psDeclVal
psContract ::= &quot;requires&quot; term | &quot;ensures&quot; ident &quot;=&gt;&quot; term | ...
// Pinned Lean-inspired contract lowering; PS clause policy is narrower</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>-- Lean intrinsic verification, version-sensitive example
-- requires a suitable verification-capable effect / pure mode
def increment (n : Nat) : Id Nat
    requires n &lt; 100
    ensures r =&gt; r = n + 1 := do
  return n + 1</code></pre></td><td valign="top"><pre><code>-- PSCV0 proposed syntax: mathematical contract, not runtime assertion
function increment(n: Nat): Id Nat
  requires n &lt; 100
  ensures r =&gt; r = n + 1 := do {
  return n + 1
}</code></pre></td></tr></tbody></table>

**Source language distinction.** Both styles use preconditions and a bound result in the postcondition. PSCV0 retains the **same Lean RC4 contract keywords and binder shapes** under a closed, version-pinned acceptance policy. RC4 intrinsic verification remains experimental, and no additional ProofScript contract grammar is implied. The examples show syntax and require a valid verified-effect specification and proof to be accepted as verified programs.

### Logical contract binders: `given`

**Feature / profile:** PSCV0 verification; Lean 4.35 intrinsic counterpart  
**Source basis:** Ch. 21.3; A.18 [pscv.grammar.contract-order]

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;def&quot; declId declSig &quot;given&quot; binder+ ...
// Pinned Lean&#x27;s experimental givenClause</code></pre></td><td valign="top"><pre><code>psContract ::= &quot;given&quot; psQuantBinder+ | ...
// Not a runtime parameter; mirrors Lean logical contract binder</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>-- Lean syntax outline (details depend on verification environment)
def take (xs : List Nat) : Id Nat
    given target : Nat
    requires target = xs.length
    ensures r =&gt; r = target := do
  return xs.length</code></pre></td><td valign="top"><pre><code>-- PSCV0 proposed syntax outline
function take(xs: List Nat): Id Nat
  given target: Nat
  requires target = xs.length
  ensures r =&gt; r = target := do {
  return xs.length
}</code></pre></td></tr></tbody></table>

**Source language distinction.** `given` introduces specification-only logical variables, never runtime arguments. PSCV0 retains the selected Lean RC4 `given`/`requires`/`ensures` clause ordering; the earlier non-native `reads`/`modifies`/`errors` extensions are **deferred**. The Lean example is **illustrative** and not presented as tested; intrinsic `given` syntax is tied to pinned 4.35 RC semantics.

### Verification-only `assert`

**Feature / profile:** PSCV0 verification; Lean 4.35 experimental analogue  
**Source basis:** Ch. 10 (`pscv.assert`), Ch. 21.10; A.18

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>doSeqItem ::= &quot;assert&quot; term | ...
// Pinned Lean 4.35 experimental intrinsic verification</code></pre></td><td valign="top"><pre><code>psDoItem ::= &quot;assert&quot; term | selectedLeanDoItem
// Requires Prop; generates proof obligation; no JS runtime assert</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>-- Lean 4.35 verification context; illustrative
-- def check (n : Nat) : Id Nat := do
--   assert 0 ≤ n
--   return n</code></pre></td><td valign="top"><pre><code>-- PSCV0 verification context; illustrative
-- function check(n: Nat): Id Nat := do {
--   assert 0 &lt;= n
--   return n
-- }</code></pre></td></tr></tbody></table>

**Source language distinction.** `assert P` has `P : Prop`; it creates proof obligations and contributes proved facts to later verification, with **no required runtime check**. It is not JavaScript's throwing `assert`. A bare `assert` in an unverified/effect-unsupported context is not automatically a verified executable.

### Local `let mut`, assignment, and early `return`

**Feature / profile:** PSCV0 verification practical do (Lean shares mainstream form)  
**Source basis:** Ch. 10 `pscv.do`, A.18; Appendix B

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>doSeqItem ::= &quot;let&quot; &quot;mut&quot; ident &quot;:=&quot; term
            | ident &quot;:=&quot; term | &quot;return&quot; term | ...</code></pre></td><td valign="top"><pre><code>psDoItem ::= &quot;let&quot; &quot;mut&quot; ident (&quot;:&quot; term)? &quot;:=&quot; term
           | ident &quot;:=&quot; term | &quot;return&quot; term | ...
// Retain Lean local-mutation translation; no unmodeled aliasing</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def next (n : Nat) : Id Nat := do
  let mut x := n
  x := x + 1
  return x</code></pre></td><td valign="top"><pre><code>function next(n: Nat): Id Nat := do {
  let mut x := n
  x := x + 1
  return x
}</code></pre></td></tr></tbody></table>

**Source language distinction.** Local mutability is translated into a total stateful `do` computation. PSCV0 does **not** thereby admit mutable aliases/shared heap references. Early return must satisfy all applicable postconditions. `do` sequencing is line-based in ProofScript, not semicolon-separated.

### `for` loops, iterator specifications, `break`, and `continue`

**Lean family:** native `for`/`break`/`continue` `do` statements. **`pscv0` surface modification:** replace the outer Lean `do` loop-body delimiter with braced grouping, not another iterator or termination model. A verified effectful loop must have a checked invariant/iterator specification appropriate to the **actual Lean RC4 loop semantics**; no new bare `invariant term` syntax is introduced merely because the earlier RC3 ProofScript draft proposed one.

| Lean 4.35.0-rc4 | ProofScript `pscv0` |
|---|---|
| <pre>def count (xs : List Nat) : Id Nat := do
  let mut total := 0
  for x in xs do
    total := total + x
  return total</pre> | <pre>function count(xs: List Nat): Id Nat := do {
  let mut total := 0
  for x in xs {
    total := total + x
  }
  return total
}</pre> |

The plain loops above demonstrate **syntax only**. For a verified executable result, a proof-capable iterator semantics, invariants or verified iterator lemmas, and all relevant termination obligations are still required. If an upstream selected Lean `for` invariant annotation is used, its binder/shape must follow the **pinned Lean 4.35.0-rc4 parser**, not the old invented `invariant total = prefixSum` spelling. `break`/`continue` retain Lean control-flow meaning and their verified proof obligations.

### `while` loops with RC4-native `invariant` and `decreasing`

**Lean family:** Lean 4.35 RC4's experimental intrinsic `while` verification syntax. RC4 changed `while` invariants to predicates over the loop exit flag and state; this is **not equivalent** to the older bare `invariant 0 <= i` syntax. **`pscv0` uses the native `invariant exit => ...` binder shape** with braced loop bodies.

**Lean grammar (schematic):**

```text
doSeqItem ::= ... | 'while' term 'invariant' binder '=>' term
                     'decreasing' term 'do' doSeq
```

**`pscv0` modification (schematic):**

```text
psDoItem ::= 'while' term 'invariant' binder '=>' term
             'decreasing' term '{' selectedLeanDoSeq '}'
```

| Lean 4.35.0-rc4 (release-note source shape) | ProofScript `pscv0` |
|---|---|
| <pre>def countDown (n : Nat) : Id Nat
    ensures r => r = 0 := do
  let mut i := n
  while i > 0
      invariant exit => if exit then i = 0 else True
      decreasing i
    do
    i := i - 1
  return i</pre> | <pre>function countDown(n: Nat): Id Nat
  ensures r => r = 0 := do {
  let mut i := n
  while i > 0
    invariant exit => if (exit) { i = 0 } else { True }
    decreasing i
  {
    i := i - 1
  }
  return i
}</pre> |

A verified while loop must establish invariant initialization, preservation, exit cases, `break`/`continue` obligations as relevant, and well-founded descent. The example is a proposed braced translation of [the RC4 release-note example](https://lean-lang.org/doc/reference/latest/releases/v4.35.0/); final executable acceptance remains dependent on the pinned experimental verifier and an independently checked proof. The **absence of an extra ProofScript invariant grammar** is intentional.

### Verification-only `erased` state — use Lean's word

Lean 4.35.0-rc4 adds experimental `erased x := e`, `erased mut x := e`, and `erased x ← action` inside `do`. **`pscv0` adopts `erased` unchanged; `ghost` is not a keyword, not an accepted synonym, and not needed.**

| Lean RC4 source family | `pscv0` braced source |
|---|---|
| <pre>def f (n : Nat) : Id Nat := do
  erased mut visited : Nat := 0
  return n</pre> | <pre>function f(n: Nat): Id Nat := do {
  erased mut visited : Nat := 0
  return n
}</pre> |

**Lean grammar (schematic):** `doSeqItem ::= ... | 'erased' ident ':=' term | 'erased' 'mut' ident ':=' term | 'erased' ident '←' term`. ProofScript changes only the **outer `do { ... }` grouping**, and keeps the same Lean item grammar. Assignment/invariant/proof rules ensure that erased information cannot affect runtime return values, branches, or effects. These snippets illustrate syntax; the experimental Lean verification context must be enabled for actual acceptance. Source: [RC4 release notes](https://lean-lang.org/doc/reference/latest/releases/v4.35.0/).

### Refined data — native Lean `Subtype`, no new `refine type` declaration

A Lean `Subtype` is exactly a value accompanied by evidence of its property. It already has a readable and established source notation: `{x : A // P x}`. There is **no** `pscv0` `refine type` syntax.

| Lean 4.35.0-rc4 | ProofScript `pscv0` |
|---|---|
| <pre>abbrev Positive := {n : Nat // n > 0}
def onePositive : Positive := ⟨1, by decide⟩</pre> | <pre>abbrev Positive := {n : Nat // n > 0}
const onePositive: Positive := ⟨1, by { decide }⟩</pre> |

**Lean grammar (schematic):** `term ::= ... | '{' ident ':' term '//' term '}' | 'Subtype' term`. **ProofScript delta:** none for these terms, apart from the enclosing `const` alias and optional proof grouping. This avoids another syntax family and preserves Lean's existing proof erasure / coercion story. This `Subtype` brace form must be recognized **before** general record/body brace parsing in its type-expression context.

### Structure invariants — native proof fields, no suffix sugar

A proof-valued field is enough to express an invariant, so `invariant self => ...` after a `structure` declaration is **not** a `pscv0` language form.

| Lean 4.35.0-rc4 | ProofScript `pscv0` |
|---|---|
| <pre>structure Account where
  balance : Int
  nonnegative : balance >= 0</pre> | <pre>structure Account where {
  balance: Int
  nonnegative: balance >= 0
}</pre> |

Every constructor and update must supply an appropriate checked proof term. The `nonnegative` field lives in `Prop` and can be erased as Lean permits. No hidden constructor or unchecked proof obligation is introduced by alternative source syntax.

### Contract verification — native theorems and `vcgen`, no `verify` command

**Decision:** discard the proposed `verify withdraw := by { ... }` declaration. Use the contract-generated obligation/theorem and a normal Lean `by` proof (including `vcgen` when the exact pinned intrinsic verification model supports it). Attaching evidence is a verifier/module identity relationship, not a second proof-declaration grammar.

```proofscript
-- Schematic: when `withdraw_spec` is a generated or explicit proposition
-- theorem withdraw_spec: WithdrawalContract := by {
--   vcgen
--   omega
-- }
```

This is a *shape*, not a runnable file: the obligation proposition and compatible effect model must actually be declared. Lean theorems remain the final checked proof objects. `verify` is not a `pscv0` keyword.

### Effect/frame vocabulary — defer additional keywords until needed

The older PSCV design proposed `reads`, `modifies`, contract-only `old(...)`, and `errors` as new language syntax. **These are not part of the minimal Lean-native `pscv0` grammar in this revision.** They are deferred candidate features, not alternate required spellings for native Lean facilities. Their intended ideas—frame conditions, pre-state access, and typed error postconditions—can already be expressed with ordinary Lean predicates and checked WP/Hoare libraries; later source sugar should be accepted only if it materially improves programming effort and comes with an exact model.

| Need | Native Lean-style representation | `pscv0` rule |
|---|---|---|
| State pre/post | `State → Prop`, `Result → State → Prop` | use explicit predicates / `requires`, `ensures` in admitted verification contexts |
| Unchanged components | equality in a postcondition / checked frame lemma | no global `modifies` keyword yet |
| Old state | explicit `before` logical binder in a theorem/effect contract | no `old` syntax yet |
| Errors | typed `Except E A`, propositions for `.ok` and `.error` results | no separate `errors` clause yet |

**Boundary:** `IO`, FFI, external service behavior, mutable aliasing, and concurrency are not silently accepted as closed verified semantics. Effect models must have checked laws; arbitrary `Monad` instances are not enough.

### Verified effect families: pure, state, reader, typed error

**Feature / profile:** Shared monadic notation; PSCV0 verified-effect restrictions  
**Source basis:** Ch. 10, 21.14–21.18; A.18

**Lean 4 grammar family → ProofScript surface selection (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= &quot;do&quot; doSeq
// Lean library effect families include StateM / ReaderT / Except</code></pre></td><td valign="top"><pre><code>term ::= &quot;do&quot; &quot;{&quot; psDoSeq &quot;}&quot;
psDoItem ::= Lean.doSeqItemRestricted | psVerifiedDoItem
// Original Lean effect types; checked WP law evidence required</code></pre></td></tr></tbody></table>

**Side-by-side examples.**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def pureAdd (a b : Nat) : Id Nat := do
  return a + b

def checkedDiv (n d : Nat) : Except String Nat :=
  if d == 0 then .error &quot;zero&quot; else .ok (n / d)</code></pre></td><td valign="top"><pre><code>function pureAdd(a: Nat, b: Nat): Id Nat := do {
  return a + b
}

function checkedDiv(n: Nat, d: Nat): Except String Nat := {
  if (d == 0) { .error(&quot;zero&quot;) }
  else { .ok(n / d) }
}</code></pre></td></tr></tbody></table>

**Source language distinction.** PSCV0 requires proof-capable semantics for at least identity/pure, state, reader, and typed error effects. The existence of a `Monad`/`StateM` class instance alone does not verify effects. Raw `IO` and external world operations remain outside closed verified computation without an accepted model. This is a **language/effect-profile** distinction, not backend design.


## 7A. Lean-native inspection and development commands in `pscv0`

**Retained decision:** The current `pscv0` design already admits `#check`, `#eval`, `#print`, and `#reduce` as native Lean diagnostic/inspection commands (the older RC3 Standard proposal treated several tooling commands differently). They are **not** new kernel semantics, proof axioms, or deployment entry points. They can be supported by the same Lean parser/term-elaboration services without weakening the kernel.

### Command family and intended grammar

| Lean native command | `pscv0` accepted form | Meaning / gate |
|---|---|---|
| `#check term` | **yes** | elaborate a term and report its type; may report unresolved metavariables in a development diagnostic |
| `#print ident` | **yes** | inspect declaration/signature and selected definition information |
| `#print axioms ident` | **yes** | inspect the transitive axiom/dependency set of a named proposition/declaration; not a replacement for the release assurance audit |
| `#reduce term` | **yes** | kernel-style definitional reduction/normalization for inspection, subject to resource limits |
| `#eval term` | **yes, restricted** | evaluate a pure, total executable term for feedback; printing is not proof |
| `#eval!`, unrestricted `#eval` of `IO` | **no** in closed `pscv0` | no bypass around effect/axiom/partial policy |
| `#check_failure`, `#synth`, `#guard`, `#eval_msgs`, `#print commands` | **not in minimum closed grammar** | may be added only after a separately versioned source-feature decision |
| `set_option` (source-affecting) | **not in minimum closed grammar** | configure a tool session separately; formatter/diagnostic output controls are not proof authority |

**Lean grammar (schematic):**

```text
command ::= ... | "#check" term | "#print" ident
          | "#print" "axioms" ident | "#reduce" term | "#eval" term
```

The important feature is **not** a special parser just for `#check`: `#check` receives a normal ProofScript term, including a function call such as `MathOps.twice(7)`, and elaborates it using the **same selected Lean typing environment** as other terms. `#check MathOps.twice (7)` and `#eval result ()` are rejected **as applications** by `PSCV0-APP-02`, but `#check (MathOps.twice 7)` and `#eval (1 + 2 : Nat)` are valid grouped term arguments. This is the same rule as in ordinary code and `by` blocks. In the full Lean syntax this command is available during editing without introducing a global declaration or runtime effect.

**ProofScript overlay:** same command heads and ordinary `pscv0` term grammar inside the command; `#eval` additionally has a pure-total/allowed-dependency static predicate. Diagnostic commands are valid among ordinary commands in files, sections, and namespaces, subject to standard import-header rules. A command's output is neither a declaration nor an export and is not a verified proof term.

### Side-by-side runnable-intent examples

| Lean 4.35.0-rc4 | ProofScript `pscv0` |
|---|---|
| `#check Nat.succ` | `#check Nat.succ` |
| `#check Nat.add 1 2` | `#check Nat.add(1, 2)` |
| `#eval (1 + 2 : Nat)` | `#eval (1 + 2 : Nat)` |
| `#reduce (Nat.succ 2)` | `#reduce Nat.succ(2)` |
| `#print Nat.add` | `#print Nat.add` |
| `#print axioms Nat.add_comm` | `#print axioms Nat.add_comm` |

**Security and soundness boundary:** Native Lean `#eval` can run `IO` actions; PSCV0’s closed-source `#eval` intentionally **cannot**. `#eval` must not execute a term with forbidden `partial`/`unsafe`/`noncomputable` executable dependencies or unapproved world effects. A development mode can offer `#eval` of boundary code under an **explicit weaker identity**, never as evidence for a verified executable. `#reduce`, `#check`, and `#print` may fail with resource limits but may not mark an open proof as discharged. `#print axioms` is a useful warning/audit surface, not the formal certificate.

Sources: [Lean Interacting with Lean](https://lean-lang.org/doc/reference/latest/Interacting-with-Lean/), pinned [Lean Parser/Command.lean](https://github.com/leanprover/lean4/blob/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/Lean/Parser/Command.lean), pinned [Init/Notation.lean](https://github.com/leanprover/lean4/blob/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/Init/Notation.lean).

### `#check`, scopes and practical proof interaction

Use Lean's command **unchanged** in `.ps`:

```proofscript
namespace MathOps
  function twice(n: Nat): Nat := n + n
end MathOps

#check MathOps.twice  -- signature includes (n : Nat) : Nat
#check MathOps.twice(7)  -- result type: Nat
#eval MathOps.twice(7)   -- 14

open MathOps
section
  variable (n: Nat)
  def result: Nat := twice(n)
  #check n               -- valid here: n is a section parameter
end

#check result             -- has explicit parameter (n : Nat)
#eval result(7)           -- 14
```

`#check` is a **typed inspection** tool, `#eval` runs admitted executable code, `#print` displays declarations, and `#print axioms` reports transitive logical assumptions. **None is a proof tactic or a substitute for proof closure.** An editor may show a partly elaborated goal while a file has unsolved work; a verified build must still reject unsolved obligations and disallowed assumptions. The distinction between an incomplete *editor buffer* and a *verified executable artifact* is mandatory.

### `pscv0` VS Code / LSP theorem-proving experience (informative target)

The language design should enable **the Lean-style development experience**, not merely accept a few `#` commands. Required user-visible capabilities for an eventual `.ps` language server/extension are: cursor-position tactic goals with local hypotheses; goals before and after each tactic, including `·`, `case`, `next`, `rw`, `simp`, `omega` and `grind`; expected/inferred types; syntax and elaboration diagnostics; completion, hover, go to definition, references and namespace lookup; theorem/instance exploration; `#check`/`#eval` output; and clearly marked unresolved proof obligations.

The best reuse path is to integrate with Lean's pinned elaboration and **InfoTree/Infoview interaction model** while retaining exact `.ps` source spans for user-facing navigation. Rewriting a `.ps` file to `.lean` text without accurate source-position mappings is insufficient for a high-quality proof editor. See the [Lean VS Code extension](https://github.com/leanprover/vscode-lean4) and [Infoview embedding notes](https://github.com/leanprover/vscode-lean4/tree/master/lean4-infoview).

**Important distinction:** proof-editor *experience parity* does not automatically mean *feature parity* with unrestricted Lean. The selected `pscv0` proof grammar may exclude some Lean macros, imported tactics or syntax extensions. For broadly comparable theorem proving, prioritize native Lean tactic grammar and proof-producing libraries, with explicitly versioned/approved environments and final kernel checking, rather than reinventing a smaller, incompatible tactic language. Do not claim complete Lean tactic/library coverage before it is tested.


## 7B. Lean `do` exceptions and ordinary-versus-verified execution

### Typed error handling with selected native `do` forms

**Decision:** add typed Lean monadic `throw`, `try`/`catch`, and `finally` to the admitted `do` capability *where the required class instances and elaboration rules exist*. Unlike JavaScript `throw`, these are not ambient unchecked exceptions: the surrounding monad chooses the error type/handling semantics, and a `try`/`finally` clause requires the appropriate `MonadFinally` support.

**Lean grammar family (schematic):**

```text
doSeqItem ::= ... | 'try' doSeq ('catch' catchAlt)* ('finally' doSeq)?
                   | 'throw' term | 'let' pattern '←' term
```

**`pscv0` modification (schematic):** select **the corresponding pinned RC4 `do` categories** and use canonical braced do/catch/finally sub-bodies. No `new Error`, JavaScript exception object or implicit `Promise` semantics are added. Exact accepted delimiters and catch binder alternatives must be confirmed against the pinned `Lean.Parser.Do` grammar; the examples are proposed `pscv0` shapes, not compiler-tested parser fixtures.

**Lean 4 idiom:**

```lean
def recover (action : Except String Nat) : Except String Nat := do
  try
    let n ← action
    return n
  catch _ =>
    return 0
```

**Proposed `pscv0` braced equivalent:**

```proofscript
function recover(action: Except String Nat): Except String Nat := do {
  try {
    let n ← action
    return n
  } catch _ => {
    return 0
  }
}
```

The `catch` handler here is typed via `Except String`, not inferred from JS runtime values. `finally` is **only valid** when the effect model has an admitted `MonadFinally` instance with known semantics; it is not guaranteed for every monad. `assert P` remains proof-only and must not be conflated with throwing an ordinary typed error.

### Ordinary checked programs, external boundaries, and verified executable proofs

| Source/action | Ordinary type-checked program | Closed verified executable | Explicit boundary verified executable |
|---|---|---|---|
| Pure total `def`/`function` | allowed after checking | allowed with mandatory accepted specifications/proofs | allowed under same checked rules |
| Typed `Except`/`State`/`Reader` | allowed when admitted | allowed only with checked WP/effect laws and required proof closure | allowed with checked models or explicitly declared assumptions as policy permits |
| `IO`, clock, files, network, FFI adapters | allowed only through **identified typed runtime capabilities**; no behavioral-proof claim | not closed-verified without a complete accepted model/proof relating required behavior | possible only with named audited assumptions/validation evidence; **not** kernel proof of foreign behavior |
| `xs[i]!` (possible panic) | allowed when its runtime behavior is admitted | does not prove in-bounds safety; use `xs[i]` or `xs[i]?` for stronger specifications | same caveat |
| `partial`/`unsafe` | **still rejected in `pscv0` source** | rejected | only outside `pscv0` through a separately modeled non-certified foreign/Lean boundary, never transmuted to checked proof |
| `sorry`/unchecked axiom in formal evidence | never counts as checked evidence | blocks verified emission | blocks unless a specifically approved assumption policy genuinely permits the axiom's use; proof holes cannot be pretended closed |

**One grammar, two assurance outcomes.** The ordinary checked path may generate executable artifacts when its language/type/effect acceptance succeeds, without requiring a behavioral proof of every application. A verified path requires its independently approved specification coverage and proof/effect/assumption/erasure gates to succeed. Both paths use the same `pscv0` grammar and Lean-grounded type checking; the output identity prevents passing off an ordinary executable as a verified one. Backends' semantic preservation and foreign system behavior require separately reported evidence.

**PSCV0 verification invariants:** a theorem must have a kernel-accepted proof term relative to an audited environment; a program's behavioral postcondition must be checked under its exact approved specification; a foreign API's logical type does not prove its runtime implementation satisfies that model. Source `partial` is not quietly enabled to make ordinary applications easier. Raw IO dependencies do not acquire “closed verified” status merely from a successful `#eval` or an imported typeclass instance.

**Research basis:** [Lean monadic exception classes](https://lean-lang.org/doc/reference/latest/Functors___-Monads-and--do--Notation/Varieties-of-Monads/), [Lean `do` syntax](https://lean-lang.org/doc/reference/latest/Functors___-Monads-and--do--Notation/Syntax/), [Lean 4.35 RC4 verification additions](https://lean-lang.org/doc/reference/latest/releases/v4.35.0/).


## 8. Operators, basis types, and language subset

### Operator precedence and associativity

The table below reproduces ProofScript Standard's exact **source operator notation** and binding strengths from Chapter 24.2. It is **not** a claim that Lean's full, extensible notation table uses precisely the same precedence. Both languages share much of the spelling and Lean-grounded target meaning. `L` = left-associative, `R` = right-associative, `N` = non-associative. Parenthesized calls/field suffixes bind more tightly than these infix operators.

| Source | Kind | Prec. | Semantic target |
|---|---:|---:|---|
| `->`, `→` | R | 25 | Pi/non-dependent arrow |
| `∨`, `\/` | R | 30 | `Or` |
| `\|\|` | L | 30 | Boolean `or` |
| `∧`, `/\\` | R | 35 | `And` |
| `&&` | L | 35 | Boolean `and` |
| `×` | R | 35 | `Prod` |
| `<`, `<=`, `≤`, `>`, `>=`, `≥` | N | 50 | `LT`/`LE`/`GT`/`GE` |
| `=` | N | 50 | `Eq` propositional equality |
| `≠` | N | 50 | `Not (Eq ...)` |
| `==` | N | 50 | `BEq.beq` Boolean equality |
| `!=` | N | 50 | pinned `bne`, definitionally `!(a == b)` |
| `+`, binary `-`, `++` | L | 65 | add/sub/append |
| `::` | R | 67 | `List.cons` |
| `*`, `/`, `%` | L | 70 | mul/div/mod |
| prefix `-` | prefix | 75 | negation |
| `<<<`, `>>>` | L | 75 | shifts |
| `^` | R | 80 | power |
| prefix `¬` | prefix | operand 40 | `Not` |
| prefix `!` | prefix | operand 40 | Boolean `not` |

**Spelling examples (side by side):**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def arith (a b : Nat) : Nat := a + b * 2
def equal (a b : Nat) : Prop := a = b
def sameBool (a b : Nat) : Bool := a == b</code></pre></td><td valign="top"><pre><code>function arith(a: Nat, b: Nat): Nat := a + b * 2
function equal(a: Nat, b: Nat): Prop := a = b
function sameBool(a: Nat, b: Nat): Bool := a == b</code></pre></td></tr></tbody></table>

ProofScript forbids user-defined Standard notation and rejects unparenthesized chaining of nonassociative precedence-50 comparisons (`a < b < c`, `a = b = c`). Its `&&` and `||` are Boolean operations, while `∧`, `∨`, `¬` are propositional connectives. `≠` is `Not (Eq ...)`, `!=` is Boolean inequality; `Nat`/`Int` arithmetic retains exact Lean-grounded meaning.

### Complete `pscv0` type inventory: foundational, scalar, algebraic, and proof-indexed

This section makes a **closed intended `pscv0` baseline** explicit rather than relying on the vague phrase “Lean-compatible data types.” It distinguishes **core/kernel language constructors**, **Lean prelude/basic data**, and **curated Lean libraries**. “Required” is a design requirement for a future conforming `pscv0` environment, **not evidence the compiler already implements the type**. Lean is the semantic and library source, not JavaScript/TypeScript.

#### A. Core type-theory and logical forms (not ordinary runtime primitives)

| Family | `pscv0` status | Description / distinction |
|---|---|---|
| `Prop`, `Sort u`, `Type u` | **required — Lean core** | propositions and universes; `Type u = Sort (u+1)` |
| dependent Pi `(x : A) → B x`, `A → B` | **required — Lean core** | dependent and ordinary function types, not a JS arity system |
| `Eq` / `=`, `HEq` where explicitly imported | `Eq` **required**; `HEq` library-gated | propositional proof families, not Boolean `==` |
| `True`, `False`, `And`, `Or`, `Not`, `Exists` | **required — Lean prelude** | propositions; their proofs are computationally irrelevant where the Lean theory permits |
| `Quot` logical foundation | **required semantic support, restricted source use** | Lean kernel-provided quotient machinery, no new PSCV0 quotient axiom |
| `Subtype p` | **required — dependent data** | value plus proof; `{x : A // p x}` is selected Lean notation |

#### B. Required scalar/basic executable families

| Type | Kind | `pscv0` guarantee / example | Special care |
|---|---|---|---|
| `Unit` | inductive single-value type | `()` | a value, not a JS zero-arity call marker |
| `Bool` | inductive data | `true`, `false` | separate from `Prop`; `== : Bool` when `BEq` is available |
| `Nat` | exact naturals | `(42 : Nat)` | unbounded; subtraction saturates at 0 |
| `Int` | exact signed integers | `(-42 : Int)` | unbounded; never silently JS `number` |
| `UInt8`, `UInt16`, `UInt32`, `UInt64` | fixed unsigned | `(255 : UInt8)` | modulo-width literal/arithmetic semantics per Lean |
| `USize` | target-word unsigned | `(1 : USize)` | target word size is a defined platform assumption |
| `Int8`, `Int16`, `Int32`, `Int64` | fixed signed | `(-1 : Int8)` | two's-complement Lean model |
| `ISize` | target-word signed | `(1 : ISize)` | platform-specific word-width model |
| `Float`, `Float32` | floating-point | `(1.25 : Float)` | Lean pinned IEEE-related semantics, not mathematical reals |
| `Char` | Unicode character type | `'a'` | character validity follows Lean, not JS UTF-16 units |
| `String` | Lean string abstraction | `"Ada"` | source string operations must preserve Lean semantics |
| `ByteArray` | packed byte array | `(ByteArray.empty : ByteArray)` | distinct from `Array UInt8` in operational representation and API |

Do **not** call every row a **kernel primitive**. For example, `Bool`, signed fixed-width numbers, and strings have Lean declarations and implementations; some have compiler/runtime optimizations, and only a smaller core subset has special kernel treatment. The exact **closed initial instances/operators** must be frozen in a `pscv0` environment manifest before a toolchain can claim complete conformance.

#### C. Required algebraic/container/dependent families

| Type/family | Kind | Canonical Lean / `pscv0` syntax | Notes |
|---|---|---|---|
| `Empty` | empty inductive | `Empty` | **newly adopted** first-party type; differs from `False : Prop` |
| `Prod α β` | binary product | `(a, b)` | right-nested tuples where applicable; one tuple is one argument |
| `Sum α β` | tagged sum | `Sum.inl a`, `Sum.inr b` | not TS union type |
| `Option α` | option | `.some(x)`, `.none` in PSCV0 calls | no ambient JS null/undefined |
| `Except ε α` | typed result/error | `.ok(x)`, `.error(e)` | not JS thrown exception |
| `List α` | persistent inductive list | `[1, 2, 3]` | Lean notation, not automatically an `Array` |
| `Array α` | array abstraction | `#[1, 2, 3]` | Lean array syntax and API |
| `Fin n` | bounded natural | `Fin n` | carries proof of range bound |
| `BitVec n` | fixed-width bitvector | `BitVec 8` | **newly adopted required curated Lean library family** for bit-precise verification; not a kernel primitive |
| `Subtype p` | proof-carrying subset | `{x : Nat // x > 0}` | compile-time proof requirement |

`Empty` and `BitVec n` are **explicit `pscv0` design additions** relative to the uploaded RC-v2's Section 26 guaranteed basis. Their Lean semantics and source syntax are adopted, not reinvented. Actual distribution of their declarations, coercions, theorem sets, and reducibility must be verified against the frozen RC4 environment.

#### D. Supported only when explicitly imported from a named Lean-derived library / profile

| Family | Intended treatment |
|---|---|
| `Vector α n`, dependent `Sigma` | curated first-party dependent containers; valuable but not part of the minimum guaranteed scalar registry |
| `Std.HashMap`, `Std.HashSet`, `Std.TreeMap`, `Std.TreeSet`, map/set APIs | opt-in approved library declarations and instances, not new grammar |
| `Range`, iterators, `ForIn` | opt-in or standard-library API; verified loops require the selected iterator's correctness/termination specifications |
| `StateM`, `ReaderT`, `ExceptT`, `Id`, monad transformers | library-defined effect families; PSCV verification additionally requires a proved weakest-precondition model |
| `IO`, platform handles, networking, raw FFI | explicit world/boundary profile only, never closed verified semantics by merely importing a type |
| user `structure`, `class`, `inductive` types | fully available under the selected Lean formation/positivity rules; their library APIs are user-defined |

A library import may provide declarations, functions, theorems, instances, and allowed attributes without adding new grammar to the closed source edition.

#### E. Source literals, infix operators, and side-by-side types

| Lean 4.35.0-rc4 | ProofScript `pscv0` |
|---|---|
| `def xs : List Nat := [1, 2, 3]` | `const xs: List Nat := [1, 2, 3]` |
| `def ys : Array Nat := #[1, 2, 3]` | `const ys: Array Nat := #[1, 2, 3]` |
| `def bytes : ByteArray := ByteArray.empty` | `const bytes: ByteArray := ByteArray.empty` |
| `def mask : BitVec 8 := 0xff` | `const mask: BitVec 8 := 0xff` (provided selected numeral instance) |
| `def small : UInt8 := 255` | `const small: UInt8 := 255` |
| `def maybeN : Option Nat := some 3` | `const maybeN: Option Nat := .some(3)` |
| `def pair : Nat × Bool := (1, true)` | `const pair: Nat × Bool := (1, true)` |

**Literal caveat:** natural/scientific tokens are elaborated using selected `OfNat` / `OfScientific` instances; a float token without an expected type requires a pinned default. `Nat`/`Int` are exact, fixed-width integers wrap as Lean specifies, and floats preserve pinned floating semantics. `= : Prop` and `== : Bool` remain separate. `[x,y]` and `#[x,y]` are **not interchangeable**. `BitVec n` numeral syntax and `ByteArray` APIs need source/instance verification, not speculative compiler intrinsics.

Primary sources: [Lean Basic Types](https://lean-lang.org/doc/reference/latest/Basic-Types/), [Fixed-Precision Integers](https://lean-lang.org/doc/reference/latest/Basic-Types/Fixed-Precision-Integers/), [Function Application](https://lean-lang.org/doc/reference/latest/Terms/Function-Application/), and the uploaded original RC-v2 Chapter 26.

### Feature admission: selected Lean syntax, PSCV0 overlay, and exclusions

| Feature | Native Lean 4.35.0-rc4 | `pscv0` decision |
|---|---|---|
| `def`, `abbrev`, `opaque`, `theorem`, `example` | ordinary Lean declarations | retain selected native meaning; `.ps` binder groups are comma-separated |
| `function`, `const` | not Lean declaration heads | **keep** as identity-bearing programming sugar for `def` |
| `Prop`, `Type`, `Sort`, Pi, equality, inductives | native type foundation | adopt without alternative type system |
| Scalar and container families | Lean prelude/Std declarations | require explicit roster in §8; preserve exact semantics |
| `if let`, `nomatch`, multi-discriminant `match` | native Lean eliminator/pattern grammar | selected **P0** source families, braced `.ps` clauses |
| Native `deriving` | pinned deriving handlers | **P0** allowlist for structures/inductives, checked generated instances |
| `GetElem` notation | native `xs[i]`, `xs[i]?`, `xs[i]!`, `xs[i]'h` | **P0**; proof/Option/panic distinctions maintained |
| Strings | native `s!` interpolation, raw literals | **P0**, including `.ps`-checked embedded terms |
| Monadic `try`/`catch`/`finally` | Lean `do` exception/`MonadFinally` semantics | **P1 staged**; exact braced parser tests pending |
| Maps, sets, JSON, HTTP, tasks | Std/runtime API families | **P1 library or explicit boundary**, not new grammar |
| Proof extensions | tactic/notation registrations | **P1** opt-in exact environment; kernel/assumptions remain authoritative |
| Ordinary checked versus verified executable | same Lean-grounded terms | one grammar, different evidence/emission claims (§7B) |
| Native math notation | `∀`/`forall`, `∃`/`exists`, `λ`/`fun`, `→`/`->`, etc. | **accept actual Lean aliases**, not new `exist` or `and` keywords |
| Native application `f x y` | Lean curried application | keep; type/proof terms remain Lean-like |
| Adjacent `f(x, y)` | new ProofScript surface call | retain two-argument call lowering |
| Gap parenthesized argument `f (x)`, `f (x, y)`, `f ()` | meaningful Lean application forms | **reject in `.ps`**; use unambiguous `f(x)`, `f((x, y))`, `f(())` |
| `f()` | source-empty call sugar | allowed only for defaults/automatics or exactly one required Unit |
| `if`, `match`, `do`, `by`, `where` bodies | native Lean layout syntax | **one braced `.ps` form** per family; `.lean` unchanged |
| Proof `·`, `case`, `next` | native Lean tactic goal control | **admit** selected pinned forms, not ASCII dot alias |
| Subtype/proof fields | native `Subtype`, `{x // P x}`, structure proofs | **retain native Lean**, remove `refine type` / invariant suffix |
| Verification-only state | RC4 native experimental `erased` | use `erased`, `erased mut`, erased bind (not `ghost`) |
| Intrinsic contracts | RC4 `given`, `requires`, `ensures`, `assert`, `invariant`, `decreasing` | retain selected native spellings under strict proof policy |
| Verification proof | Lean `theorem` / `by` / `vcgen` | no redundant `verify` keyword |
| Frame/error sugar | no confirmed direct equivalent in RC4 language grammar | **deferred**, use Lean predicates/effect models for now |
| `#check`, `#print`, `#reduce`, bounded `#eval` | native diagnostics | accept as non-authoritative inspection commands |
| `unsafe`, `partial` | Lean supports their own source forms | remain **rejected in `pscv0` source**; separate external/Lean boundary only |
| user `axiom`, proof holes | Lean permits explicit logical assumptions | user axioms rejected in closed verification; `sorry` never proof closure; audit imported assumptions |
| Raw `IO`, `extern`, aliased/concurrent mutable state | Lean runtime/FFI constructs | permitted only through typed, declared boundary capability where selected; never silently closed verified |
| User `syntax`, macros, custom elaborators | Lean source extensibility | not part of closed `.ps`; separate named extensible profile only |

## 8A. First-party application-library capability surface (no new keywords)

**Why this section exists:** a catalog of Lean data type *names* is not enough to make ProofScript practical for TypeScript developers. The distinction is between **syntax guarantees** already selected above and **curated APIs** that must actually ship or be reachable through frozen, versioned imports. The latter are not automatic additions to `pscv0`'s parser.

| Application task | Lean-grounded `pscv0` capability | Ownership / release evidence |
|---|---|---|
| Arrays and lists | `Array`, `List`, constructors/literals, `map`, `fold`, `filter`, `push`, `append`, iteration, safe indexing | native notation plus pinned library types/functions/instances; check signatures |
| Maps and sets | `Std.HashMap`, `Std.HashSet`, appropriate tree variants, lookup/insert/erase/iteration | curated P1 Std library; import and exact API signatures required |
| Optional and typed failures | `Option`, `Except`, `ExceptT`, `OptionT`, `getD`, `map`, monadic propagation | standard data types + verified effect specs when applicable |
| Strings, bytes, formatting | `String`, `Char`, `ByteArray`, UTF-8 conversion, `s!` strings, raw strings, string APIs | native lexing plus versioned `ToString`/other instances |
| JSON and validation | versioned JSON tree and **checked decoders** into structures/inductives/refinement values | library-only P1; no ambient `unknown`/unchecked `as` |
| Codecs/serialization | explicit encoders, decoders, schema/round-trip theorems where required | libraries; errors typed and foreign data untrusted |
| State, read-only environment, exceptions | `StateM`/`StateT`, `ReaderT`, `Except`, relevant WP/Hoare models | effect libraries and, for verified status, checked laws |
| Files, network, clocks, randomness | typed `IO`/capability wrappers and auditable signatures | explicit world-boundary P1; no closed-world proof by fiat |
| Tasks, async, cancellation | use Lean-grounded `Task`/effect abstractions initially; explicit scheduling/exception semantics | P1/P2 libraries; **do not** invent TS `async`/`await` keywords yet |
| JavaScript/TypeScript interop | typed adapter APIs and declaration import with runtime checking where needed | external boundary/tooling; `.d.ts` is not proof of JS implementation |
| Proof/theorem libraries | imported declarations, lemmas, registered tactics and notation | pinned proof environment with replay and axiom closure |

**Required release manifests:** specify imported module identities, public API declarations, builtin `GetElem`/`ToString`/numeric instances, notation and deriving handler entries, proof extension registrations, effect model and axiom dependencies. Importing a library whose type `Std.HashMap` exists does not guarantee that every recent convenience method or notation exists at the pinned RC4 commit. Unknown API names should be treated as **pending** until a compiler/reference check confirms them.

### Minimal P0 API guarantees

The P0 `pscv0` environment MUST select and document concrete members for: constructing/iterating/converting `List`/`Array`, safe `GetElem`, mapping/folding/filtering, handling `Option` and `Except`, `String` formatting/encoding, and common `Nat`/`Int`/fixed-width conversions. Failure to name a stable operation is a *release gap* rather than an invitation to add syntax. At least one map/set implementation and typed JSON codec become P1 application-prelude requirements.

### Why not copy TypeScript structural typing?

The Lean alternatives are nominal structures and inductives with explicit adapter functions. A `structure` cannot be silently assigned another structure based solely on equal field names. This deliberate difference provides stable declaration identity and proof-friendly APIs. Code actions or generated adapters can reduce migration friction without redefining type soundness. Similarly, `Option` avoids nullable semantics, and a checked JSON decoder avoids uncontrolled `any` or assertions. Preserve the difference in diagnostics and examples rather than hiding it behind a superficially familiar keyword.

## 9. ProofScript identity, Lean fidelity, and deliberate deviations

`pscv0` is a **Lean-semantic subset**, not a forked type theory. The canonical surface stays TypeScript-friendly exactly where it earns its cost: `function`, `const`, comma-separated parameter groups and calls, expression-block braces, and braced control/proof bodies. Avoid extra spellings when Lean already provides readable, kernel-compatible syntax.

| Design tradeoff | Final `pscv0` choice | Why |
|---|---|---|
| `function` / `const` versus `def` | keep all three but give distinct **roles**: functional programming, parameterless values, general Lean definitions | user-facing identity; all lower to Lean declarations |
| Unicode vs text `∀`/`forall`, `∃`/`exists` | keep both native Lean notations | existing Lean syntax, common mathematical workflow |
| `ghost` vs `erased` | **erased only** | Lean RC4 already supplies meaning and token |
| `refine type` vs `Subtype` | **Subtype only** | Lean already provides concise `{x : A // P x}` |
| `verify target` vs theorem/proof | **theorem / checked proof only** | one proof language is easier to audit |
| Structure-invariant suffix vs proof field | **proof fields only** | avoids hidden semantic fields and extra grammar |
| `f ()` vs `f()` vs `f(())` | reject `f ()`, use `f()` for source-empty and `f(())` for explicit Unit | fewer confused calls |
| `f (x, y)` vs `f(x, y)` | reject first **in `.ps`**, use `f((x, y))` for tuple | no whitespace-caused arity changes |
| Lean native layout vs `.ps` braced layout | one braced `.ps` form | fewer representations of the same construct |
| Tactic bullets | native middle dot **`·`** | does not collide with field selection `.` |
| Frames/typed error contracts | lean on predicates now, reevaluate new sugar later | avoid extra keywords without proven benefit |

### 9.1 A narrower and safer call rule

**Issue:** In Lean, `f (x, y)` applies `f` to *one tuple*, but ProofScript `f(x, y)` applies two arguments. Keeping both valid in `.ps` makes an ordinary space insertion potentially change meaning and typecheck accidentally.

**Resolution:** allow Lean unparenthesized application `f x y` and ProofScript adjacent `f(x, y)`, but **reject whitespace/comment/newline-separated parenthesized applications**. Use `f((x, y))` for one tuple and `f(())` for explicit Unit. This sacrifices a small fragment of Lean's exact source grammar to make `.ps` editing/formatting safer. The `.lean` compatibility path is intentionally unaffected.

### 9.2 One braced spelling for body-like source constructs

`pscv0` uses `by { ... }`, `do { ... }`, `match ... with { ... }`, `if (p) { ... } else { ... }`, `structure ... where { ... }`, `class ... where { ... }`, and braced `where` local declarations. We no longer promise a second, indentation-only Lean layout form in `.ps`; native Lean layout remains available when compiling `.lean` files under a separate bounded compatibility profile. All braces have **construct-specific Lean meaning**, never generic JS statement semantics.

### 9.3 Lean-native proof vocabulary and data semantics

Keep `erased`, `Subtype`, `Fin`, constructors, typeclass notation, theorems, tactic bullets, and mathematical symbols unchanged. `Nat`, `Int`, fixed-width integers, `Float`/`Float32`, `Bool`, `String`, `Char`, `ByteArray`, `Option`, `Except`, `List`, `Array`, `Prod`, `Sigma` (when imported), and `Subtype` retain the exact pinned type meaning rather than TypeScript/JavaScript value semantics.

## 10. Additional Lean-alignment comparisons

### Type-indexed safe indices (`Fin n`)

**Category:** Shared Lean dependent type  
**Basis:** Source Ch. 16, 26; Appendix I `LEAN-TYPE-FIN`

**Lean 4 grammar family → ProofScript overlay (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>command ::= &quot;def&quot; declId binder* (&quot;:&quot; term)? declVal
term ::= ... | &quot;Fin&quot; term | term &quot;.&quot; ident</code></pre></td><td valign="top"><pre><code>command ::= &quot;function&quot; declId psBinder* (&quot;:&quot; term)? psBody
term ::= ... | &quot;Fin&quot; term | term &quot;.&quot; ident
// Same dependent type and bounds proof as Lean</code></pre></td></tr></tbody></table>

**Side-by-side example**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def atMost {n : Nat} (i : Fin n) : Nat := i.val</code></pre></td><td valign="top"><pre><code>function atMost {n: Nat}(i: Fin n): Nat := i.val</code></pre></td></tr></tbody>
</table>

**Meaning and boundary.** `Fin n` is Lean's dependent index/bounded-natural family. ProofScript inherits the same type; the syntax change is only the explicit binder group. The index proof is not a new runtime type or unchecked numeric cast.

### Proof-relevant subtypes, retaining native Lean syntax

**Lean grammar (schematic)** already includes `Subtype`, `{x : A // P x}`, and constructor notation `⟨value, proof⟩`. **`pscv0` adopts these same constructs without the unnecessary `refine type` alternate spelling.**

| Lean 4.35.0-rc4 | ProofScript `pscv0` |
|---|---|
| <pre>abbrev Positive := {n : Nat // n > 0}
def p : Positive := ⟨1, by decide⟩</pre> | <pre>abbrev Positive := {n : Nat // n > 0}
const p: Positive := ⟨1, by { decide }⟩</pre> |

The base value needs a proof that it satisfies the predicate; the proof is computationally irrelevant according to native Lean `Subtype` semantics. No special ProofScript proof field, runtime check, or extra cast is introduced.

### Partial application and currying remain fundamental

**Category:** Shared curried semantics  
**Basis:** Lean Function Application; source Ch. 9–10, 22.3

**Lean 4 grammar family → ProofScript overlay (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= ... | term argument+
argument ::= term | &quot;(&quot; ident &quot;:=&quot; term &quot;)&quot;</code></pre></td><td valign="top"><pre><code>term ::= ... | term argument+
            | callable &quot;(&quot; psArgs? &quot;)&quot;
// Both elaborate to nested Lean unary applications</code></pre></td></tr></tbody></table>

**Side-by-side example**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def add (x y : Nat) : Nat := x + y
def plusOne : Nat → Nat := add 1</code></pre></td><td valign="top"><pre><code>function add(x: Nat, y: Nat): Nat := x + y
const plusOne: Nat -&gt; Nat := add(1)</code></pre></td></tr></tbody>
</table>

**Meaning and boundary.** `f(x)` can return a function when more explicit binders remain, exactly as Lean's `f x`. An *empty* `f()` asks for bounded empty-invocation completion: defaults/automatics or exactly one required explicit `Unit`. In `.ps`, `f ()` is always rejected; the only explicit Unit call is `f(())`.

### Boolean condition versus proposition condition

**Category:** PSCV0 braced sugar over Lean conditions  
**Basis:** Lean Terms/Conditionals; source Ch. 10, 22.2

**Lean 4 grammar family → ProofScript overlay (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= ... | &quot;bif&quot; term &quot;then&quot; term &quot;else&quot; term
            | &quot;if&quot; term &quot;then&quot; term &quot;else&quot; term</code></pre></td><td valign="top"><pre><code>term ::= ... | &quot;if&quot; &quot;(&quot; term &quot;)&quot; &quot;{&quot; term &quot;}&quot;
            &quot;else&quot; &quot;{&quot; term &quot;}&quot;
// Bool =&gt; bif/Bool, Prop =&gt; ite/Decidable</code></pre></td></tr></tbody></table>

**Side-by-side example**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def boolChoice (b : Bool) : Nat := bif b then 1 else 0
def propChoice (n : Nat) : Nat := if n = 0 then 1 else 0</code></pre></td><td valign="top"><pre><code>function boolChoice(b: Bool): Nat := if (b) { 1 } else { 0 }
function propChoice(n: Nat): Nat := if (n = 0) { 1 } else { 0 }</code></pre></td></tr></tbody>
</table>

**Meaning and boundary.** A `Bool` is data; `p : Prop` needs `Decidable p`. Conditional parsing never treats an integer/string/option as truthy, and no implicit arbitrary TypeScript/JavaScript conversion is allowed. These `if` branches each hold one term.

### `assert!` runtime check is NOT PSCV0 proof-only `assert`

**Category:** PSCV0 verification  
**Basis:** Pinned Parser/Term.lean `assert!`; Parser/Do; source §21.10

**Lean 4 grammar family → ProofScript overlay (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= ... | &quot;assert!&quot; term ...    // runtime assertion
// &#x27;assert&#x27; is available only in pinned intrinsic verification</code></pre></td><td valign="top"><pre><code>psDoItem ::= ... | &quot;assert&quot; term
// Lean proof obligation required; `assert!` not substituted</code></pre></td></tr></tbody></table>

**Side-by-side example**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>-- Native Lean term-level runtime assertion (not formal proof):
-- assert! (n &gt; 0); n</code></pre></td><td valign="top"><pre><code>function checked(n: Nat): Id Nat := do {
  assert n = n
  return n
}</code></pre></td></tr></tbody>
</table>

**Meaning and boundary.** `assert` requires a provable proposition and contributes proof/VC semantics; Lean's `assert!` is a runtime checking mechanism. Neither proves a specification merely by running. The PSCV0 example still requires an admitted verification context and discharged obligation.

### List and array families are types, not implicit JS arrays

**Category:** Shared Lean basis type families  
**Basis:** Source Ch. 26–27; Lean Prelude/List/Array

**Lean 4 grammar family → ProofScript overlay (schematic).**

<table>
<thead><tr><th width="50%">Lean 4 grammar (schematic)</th><th width="50%">ProofScript `pscv0` modification (same Lean grammar family)</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>term ::= ... | ident argument+ | ident &quot;.&quot; ident
// `List`/`Array` are Lean data families, not grammar additions</code></pre></td><td valign="top"><pre><code>term ::= ... | ident argument+
            | callable &quot;(&quot; psArgs? &quot;)&quot;
// Reuse Lean List / Array types and constructors</code></pre></td></tr></tbody></table>

**Side-by-side example**

<table>
<thead><tr><th width="50%">Lean 4.35.0-rc4</th><th width="50%">ProofScript `pscv0`</th></tr></thead>
<tbody><tr><td valign="top"><pre><code>def single : List Nat := List.cons 1 List.nil
def emptyArray : Array Nat := Array.empty</code></pre></td><td valign="top"><pre><code>const single: List Nat := List.cons(1, List.nil)
const emptyArray: Array Nat := Array.empty</code></pre></td></tr></tbody>
</table>

**Meaning and boundary.** The *historical source* guaranteed the basis types without a complete API/literal catalog. **This revised `pscv0` design explicitly admits native Lean list literals `[a, b]`, array literals `#[a, b]`, and indexed `GetElem` syntax** (see §3), while requiring the actual constructors, instances and convenience APIs to be frozen in the RC4 environment. No JavaScript array behavior is imported. A complete application-library API is a separate, explicit requirement in §8A.

## 10A. TypeScript-to-ProofScript migration capability matrix

The objective is **not source-level JavaScript compatibility**. A general-purpose ProofScript project should nevertheless offer a practical, discoverable equivalent for common TypeScript work, even when it requires writing a proof, handling an `Option`, using a typed effect, or declaring a checked boundary.

| TypeScript programming need | `pscv0` alternative | Is language syntax missing? |
|---|---|---|
| `function` / top-level `const` | existing `function`, `const` (both Lean `def` meanings) | no |
| `interface` / structural object types | `structure`; typeclass for generic behavior, explicit adapters for related structures | **no**, intentional nominal typing |
| `type A = ...` | native Lean `abbrev`/`def` for appropriate type aliases | no new `type` alias keyword |
| `enum`, tagged union, discriminated union | `inductive` constructors + exhaustive multi-discriminant `match`, `if let` | no duplicate union syntax |
| Optional fields / nullish data | `Option α`, `.some`, `.none`, `getD`, checked matching | no `null`/`undefined` truthiness |
| Errors and `Result<T,E>` | `Except ε α`, `throw`, typed `try`/`catch` under admitted monad | **need selected Lean `do` error syntax**, not JS exceptions |
| Generic functions/interfaces | `{α : Type}`, `[C α]`, dependent Pi, typeclasses | no, but IDE explanation needed |
| Array indexing | `xs[i]` (proof), `xs[i]?` (Option), `xs[i]!` (panic) | native Lean syntax, now guaranteed |
| Arrays / lists / iterators | `Array`, `List`, `do` loops, `ForIn` and standard collections | library/pinned instance completeness needed |
| Map / Set / dictionaries | `Std.HashMap`, `Std.HashSet`, explicit typed lookup | P1 library guarantee, not syntax |
| Template strings | Lean `s!"...{expr}..."`; raw strings `r#"..."#` | now native syntax guarantee |
| `as`, `any`, unchecked coercion | checked type ascription `(x : T)`, explicit adapter/decoders, `Subtype`, proof obligations | intentionally no unsafe alias |
| `readonly`, ordinary mutable variables | immutable `let`/`def`, `let mut` and scoped assignment in `do`, verified effects | no copied JS reference semantics |
| `switch` / narrow-by-tag | selected Lean `match`, `if let`, `matches`, proof-level case analysis | now richer native feature coverage |
| `Promise` / `async` / event handling | typed task/effect libraries and IO boundaries | async *capability* P1, syntax P2 pending evidence |
| JSON response/request handling | typed JSON AST and validated decoders returning typed `Except` | P1 library/tooling, no `unknown` import as proof |
| Classes / method-call syntax | structures and typeclasses; type-directed `x.method(y)` notation | OO inheritance/prototype semantics intentionally absent |
| Importing npm/FFI libraries | explicit typed adapter and validation/boundary evidence | P1 package/runtime tooling, no magical TS semantic admission |
| Formal specifications/tests | dependent/refinement types, contracts, assertions, theorems, native Lean tactics, runtime tests separately | stronger than TS typing; tests do not stand in for proofs |

**Concrete example: discriminate a typed result without a TypeScript union.**

```proofscript
inductive Response where {
  | ok(value: Nat)
  | error(message: String)
} deriving Repr, BEq

function describe(x: Response): String := {
  match x with {
    | .ok n => s!"ok: {n}"
    | .error msg => msg
  }
}
```

**Concrete example: safe optional indexing.**

```proofscript
function getOrZero(xs: Array Nat, i: Nat): Nat := {
  match xs[i]? with {
    | .some n => n
    | .none => 0
  }
}
```

All examples remain *proposed `.ps` examples*, not actual compiler-conformance evidence. Their Lean equivalents rely on pinned selected constructors, notation, `ToString`/typeclass instances, and approved derivation handlers. The semantics of `match` and array indexing are not copied from TypeScript.

### Migration ergonomics that belong in tooling rather than grammar

The editor and converter should offer checked code actions for `f (x)` → `f(x)`, discriminated union → `inductive`, nullable fields → `Option`, JSON decoding → typed codec, index access → explicit `?`/proof path, and `switch` → `match`. Diagnostics should show **why** a proof is needed (bounds, exhaustiveness, totality, precondition), not merely report a parser failure. A conversion tool must preserve intended call arity and not change a tuple argument into two arguments.

### Language-extension threshold

A new surface keyword is justified only when an ordinary Lean feature or curated library produces repeated measurable pain across representative applications; the sugar must have one obvious lowering to Lean, preserve proofs/effects and erasure, and avoid two dangerously similar spellings. This is why `function`, `const`, and adjacent calls stay while `ghost`, `refine type`, `verify`, JS truthiness, `any`, `as`, `?.`, `??`, global JSX and premature `async`/`await` remain out of the guaranteed core.

## 11. Lean 4 grammar (schematic) → `pscv0` selected modifications

### 11.1 Grammar authority, subset meaning, and labels

The actual [Lean 4.35.0-rc4 parser](https://github.com/leanprover/lean4/tree/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/Lean/Parser) determines native categories. The following **schematic** fragments document **selected native Lean productions and ProofScript's limited surface modifications**, not a separate comprehensive EBNF. `command`, `term`, `binder`, `tactic`, `doSeqItem`, `matchAlt`, `structField`, `structInstField`, `ctor`, `ident`, `level` stand for upstream Lean categories, subject to this document's closed `pscv0` selection. Ellipses represent omitted pinned alternatives, **not** permission to import all Lean syntax.

The following representation is used consistently in all language comparisons:

```text
Lean 4 grammar (schematic):
command ::= ... | 'def' declId declSig declVal
term    ::= ... | 'by' tacticSeq | term argument

pscv0 modification (schematic):
command ::= selectedLeanCommand | psFunction | psConst
term    ::= selectedLeanTerm | psParenthesizedCall | psBracedTerm

-- Negative source constraints are part of grammar acceptance, not style hints.
```

The grammar is valid only in the sense of a language *design* until executable conformance tests confirm the acceptance and desugaring rules. The selected Lean source families in §3/§4 (strings, `GetElem`, `if let`, multi-match, `nomatch`, `deriving`) are part of this grammar overlay and do not create a second independent EBNF. A new syntax family may change formatting but never the Lean proof kernel's accepted term semantics.

### 11.2 Source files, scope, and diagnostic commands

**Lean grammar (schematic):** `command ::= import | namespace | section | open | variable | declaration | #check | #print | #reduce | #eval | ...`. `pscv0` retains the selected Lean module and scope families; declaration header imports remain before non-import commands; ordinary dependencies do not register new parser grammars. `.ps` source remains UTF-8.

| Lean 4.35.0-rc4 | ProofScript `pscv0` |
|---|---|
| <pre>import Std
namespace Math
def one : Nat := 1
end Math
#check Nat.succ
#print axioms Nat.add_comm</pre> | <pre>import Std
namespace Math
const one: Nat := 1
end Math
#check Nat.succ
#print axioms Nat.add_comm</pre> |

`#eval` is admitted only for a pure/total executable expression supported by the pinned closed evaluation surface. Diagnostic evaluation does **not** prove contract obligations or contribute logical authority.

### 11.3 Definitions, binders, and `const` / `function`

**Lean grammar (schematic):**

```text
command ::= ... | 'def' declId declSig declVal
                  | 'theorem' declId declSig declVal
                  | 'abbrev' declId declSig declVal
binder  ::= ... | '(' ident ':' term ')' | '{' ident ':' term '}'
                  | '{{' ident ':' term '}}' | '[' classTerm ']'
```

**`pscv0` modification (schematic):**

```text
command ::= selectedLeanDeclaration
          | 'const' ident (':' term)? ':=' term
          | 'function' ident psNonExplicitBinders* psExplicitGroup (':' term)? ':=' term
psExplicitGroup ::= '(' (psParam (',' psParam)* ','?)? ')'
psParam ::= ident ':' term (':=' term)?
```

These schematics describe surface shape, not complete parser precedence or all Lean modifiers. `function` and `const` lower to Lean `def`. A zero-argument group for `function f()` lowers to one hidden required `Unit` binder. Non-explicit implicit/strict-implicit/instance binders remain selected Lean-native notation. `theorem` and `example` produce ordinary checked proof terms, not JS declarations.

| Lean 4.35.0-rc4 | ProofScript `pscv0` |
|---|---|
| <pre>def add (a b : Nat) : Nat := a + b
def limit : Nat := 10</pre> | <pre>function add(a: Nat, b: Nat): Nat := a + b
const limit: Nat := 10</pre> |

### 11.4 Application — precise Lean grammar overlay and restrictions

The native Lean [term parser](https://github.com/leanprover/lean4/blob/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/Lean/Parser/Term.lean) recognizes juxtaposition application. Native `f (x, y)` therefore supplies one tuple, while native `f ()` supplies one `Unit` value. `pscv0` **preserves the same elaborated unary applications but rejects the spaced parenthesized argument spelling** at a completed callable expression. It also adds adjacent comma calls. The changes below are **schematic selections/constraints on Lean's grammar**, not a second independent grammar.

```text
Lean 4 grammar (schematic):
  term ::= ... | term argument | '(' term ')' | '(' term ',' term ... ')'
  binder ::= ... | '(' ident ':' term ')' | '{' ident ':' term '}'

pscv0 term overlay (schematic):
  application := selectedLeanApplication except gapParenthesizedOperand
  postfixCall := callable '(' callArg (',' callArg)* ','? ')'
              | callable '()'            -- subject to PSCV0-APP-03
  callArg := term | ident ':=' term

Source constraints, not new core constructors:
  PSCV0-APP-01: allow f x y and f(x, y); elaborate to Lean application.
  PSCV0-APP-02: reject completedCallable + trivia + '(' as an application.
  PSCV0-APP-03: f() completes only declared defaults/automatic binders
                 or one remaining required Unit argument; otherwise reject.
  PSCV0-BIND-01: do not apply APP-02 to binder or fresh-term positions.
```

| Valid `.ps` expression | Lean-equivalent meaning |
|---|---|
| `add(1, 2)` / `add 1 2` | `add 1 2` |
| `tupleFn((1, 2))` | `tupleFn (1, 2)` |
| `unitFn(())` | `unitFn ()` |
| `function now(): Nat := 42` / `now()` | hidden required Unit parameter; `now ()` in generated Lean |
| `f(g x)` / `f(g(x))` | grouped or nested argument of one call |
| `x + (y * z)` | expression grouping, **not** application |
| `variable (n: Nat)` | native typed section **binder**, **not** application |
| `fun (x: Nat) => x` | native typed lambda **binder** |
| `#check (add 1 2)` | command's first term is grouped |
| `by { exact (hp) }` | grouped proof term after the `exact` tactic head |

| Rejected `.ps` expression | Required equivalent or remedy |
|---|---|
| `add (1, 2)` | `add((1, 2))` for a tuple, or `add(1, 2)` for two arguments |
| `tupleFn (1, 2)` | `tupleFn((1, 2))` |
| `unitFn ()` | `unitFn(())` |
| `now ()` | `now()` (or explicit `now(())`) |
| `add (1)` | `add(1)` |
| `f /* gap */ (x)` | `f(x)` |
| `exact h (hp)` inside `by { ... }` | `exact h(hp)` or `exact (h hp)` |
| `#check f (x)` | `#check f(x)` or `#check (f x)` |
| `#eval now ()` | `#eval now()` |

**Parser decision:** do **not** tokenize a blanket rule like “identifier followed by whitespace and `(` is invalid.” Instead, the selected Lean grammar first identifies the context (`binder`, `term-start`, `term-continuation`). Reject the gap-parenthesized term only in `term-continuation` when it would serve as an application argument. A fresh parenthesized term following an operator, binder head, tactic head, or diagnostic-command head remains valid. Use this same policy throughout executable code, declarations, propositions, tactic argument expressions, contract terms, and diagnostic commands.

This rule blocks invisible changes in argument count on whitespace edits while retaining dependent function types, section parameters, Lean's theorem-proving grammar and ordinary term grouping. It does not add a new runtime arity model or affect `.lean` files. See the full accepted-source decision procedure and examples in §2 (`PSCV0-APP-01` through `PSCV0-BIND-01`).

### 11.5 Terms, records, and mathematical symbols

**Lean grammar (schematic):** `term ::= 'fun' binders '=>' term | 'λ' binders '=>' term | 'forall' ... | '∀' ... | 'exists' ... | '∃' ... | '{' ident ':' term '//' term '}' | ...`.

**`pscv0` decisions:** accept native mathematics and `Subtype` notation unchanged. `exist` (singular) and a new `refine type` declaration are **not** accepted. Keep Lean's `Prod`, `Fin`, `Option`, `Except`, `List`, `Array`, structure constructors/projections, and user-annotated `Prop` terms with the selected pinned library profile. Record values (`{ field := value, ... }`) preserve Lean's nominal-structure meaning. A declaration body wrapper `:= { oneTerm }` does not introduce arbitrary JavaScript statements.

| Lean | `pscv0` |
|---|---|
| <pre>abbrev Positive := {n : Nat // n > 0}
example : ∃ x : Nat, x = 0 := ⟨0, rfl⟩</pre> | <pre>abbrev Positive := {n : Nat // n > 0}
example : exists x : Nat, x = 0 := by {
  exact ⟨0, rfl⟩
}</pre> |

### 11.6 Conditionals, multi-discriminant matching, structures, inductives, and deriving

**Lean grammar family (schematic):**

```text
term ::= ...
       | 'if' term 'then' term 'else' term
       | 'if' binderIdent ':' term 'then' term 'else' term
       | 'if' 'let' pattern ':=' term 'then' term 'else' term
       | 'nomatch' term (',' term)*
       | term 'matches' pattern
       | 'match' matchDiscriminants 'with' matchAlt+
matchAlt ::= '|' pattern (',' pattern)* '=>' term
command ::= ... | 'structure' declId ... 'where' structFields derivingClause?
               | 'inductive' declId ... 'where' ctor+ derivingClause?
```

**`pscv0` selected modification (schematic):**

```text
term ::= ...
       | 'if' '(' term ')' '{' term '}' 'else' '{' term '}'
       | 'if' '(' binderIdent ':' term ')' '{' term '}' 'else' '{' term '}'
       | 'if' 'let' selectedLeanPattern ':=' term
                    '{' term '}' 'else' '{' term '}'
       | 'nomatch' selectedLeanDiscriminants
       | term 'matches' selectedLeanPattern
       | 'match' selectedLeanDiscriminants 'with' '{' selectedLeanMatchAlt+ '}'
selectedLeanMatchAlt ::= '|' selectedLeanPattern
                            (',' selectedLeanPattern)* '=>' term
command ::= ...
          | 'structure' declId ... 'where' '{' selectedLeanStructFields '}'
                selectedDerivingClause?
          | 'class' declId ... 'where' '{' selectedLeanClassFields '}'
          | 'inductive' declId ... 'where' '{' selectedLeanCtorAlts '}'
                selectedDerivingClause?
selectedDerivingClause ::= 'deriving' allowedClass (',' allowedClass)*
```

The **new selected Lean matching surface** includes more than one discriminant, optional names, dependent match generalization, and relevant constructor/tuple/list-style patterns where their pinned Lean `match_pattern` expansion and chosen environment permit them. A named `match h : x` or `match (generalizing := true) x` is native **match syntax**, not a spaced function application. Pattern sequences must align with discriminant counts; exhaustive checking, dependent motive formation, structural recursion, and checked recursor lowering remain required. `k + 1` is still **Nat-specific successor-pattern syntax**, not a general arithmetic pattern solver.

The `deriving` clause reuses native Lean class names and registered deriving-handler semantics; the initial allowlist is `Repr`, `BEq`, `DecidableEq`, `Inhabited`, `Hashable`. It does **not** grant arbitrary user handler registration, nor turn a typeclass declaration into a proven law without evidence. A derivation can fail if the required type or members do not support it.

| Lean 4.35.0-rc4 | ProofScript `pscv0` (illustrative) |
|---|---|
| <pre>def both (x y : Option Nat) : Bool :=
  match x, y with
  | some _, some _ => true
  | _, _ => false</pre> | <pre>function both(x: Option Nat, y: Option Nat): Bool := {
  match x, y with {
    | .some _, .some _ => true
    | _, _ => false
  }
}</pre> |
| <pre>structure Point where
  x : Nat
  y : Nat
  deriving Repr, BEq</pre> | <pre>structure Point where {
  x: Nat
  y: Nat
} deriving Repr, BEq</pre> |

Record *values* use commas; structure/class *field declarations* retain Lean-style newline sequencing. The brackets are **grammar-specific grouping**, not JavaScript object scopes. The corresponding unbraced native layout is used in `.lean`, not as a second `.ps` control-body form.

### 11.7 `do`, typed errors, `erased`, contracts, loops, and termination

**Lean grammar family (schematic):** `term ::= ... | 'do' doSeq | 'by' tacticSeq`. `doSeqItem` includes Lean's ordinary `let`, `let mut`, assignment, pattern binding, `return`, loops, selected `throw`/`try`/`catch`/`finally`, and RC4 experimental erased verification state. The RC4 intrinsic-verification parser/elaborator supplies experimental `given`, `requires`, `ensures`, `assert`, loop `invariant`/`decreasing`, and `vcgen` proof-construction facilities.

**`pscv0` modification (schematic):**

```text
term ::= ... | 'do' '{' selectedLeanDoSeq '}'
selectedLeanDoSeqItem ::= selectedLeanDoBinding
                        | selectedLeanReturnOrThrow
                        | selectedLeanForOrWhile
                        | selectedLeanTryCatchFinally
                        | selectedLeanErasedOrAssert
                        | selectedLeanTermStatement
```

The **outer braces and newline sequencing** are the `pscv0` overlay; the typed monadic meaning must match the pinned Lean elaborator. `catch`/`finally` are only admitted when the corresponding `MonadExcept`/`MonadFinally` class requirements and exact parser forms are available. The grammar line is schematic, not an assertion that the illustrative `{}` catch bodies below are already parsed by RC4. A `Monad` instance alone never certifies the effect as verified.

**Vocabulary kept from Lean:** `erased` (not `ghost`), `Subtype` (not `refine type`), `termination_by`, `decreasing_by`, `given`, `requires`, `ensures`, proof-only `assert`, loop `invariant`, `decreasing`, and `vcgen` where provided by the pinned selected prover. Do **not** introduce `verify`, `old`, `reads`, `modifies`, or `errors` into the guaranteed core merely because those spellings appear in the older PSCV candidate. In typed error models, write checked Lean-grounded propositions over successful/error post-states first.

### 11.8 Tactics: native bullets and native focus, inside ProofScript braces

**Lean grammar (schematic):**

```text
term   ::= ... | 'by' tacticSeq
tactic ::= ... | 'constructor' | 'exact' term | '·' tacticSeq
                 | 'case' caseName '=>' tacticSeq | 'next' binders? '=>' tacticSeq
```

**`pscv0` modification (schematic):** `term ::= ... | 'by' '{' selectedLeanTacticSeq '}'`. Source tactic text uses the native Lean tokens and syntax, with a fixed selected (not arbitrary import-extensible) tactic surface. The goal bullet **`·`** is U+00B7 middle dot; `.` remains field notation and is **not** a bullet.

| Lean (native) | ProofScript (same goal behavior) |
|---|---|
| <pre>theorem andProof (P Q : Prop) (hp : P) (hq : Q) : P ∧ Q := by
  constructor
  · exact hp
  · exact hq</pre> | <pre>theorem andProof(P: Prop, Q: Prop, hp: P, hq: Q): P ∧ Q := by {
  constructor
  · exact hp
  · exact hq
}</pre> |

`case`, `next`, `all_goals`, and `<;>` are supported only where the selected pinned Lean tactic parser and proof-producing semantics recognize them. A tactic `;` does not become a general statement separator. No ASCII-dot bullet alias is introduced.

### 11.9 Source modifiers, types, literals, indexing, deriving handlers, and default environment

Attributes such as `@[simp]`, `@[instance]`, and `@[default_instance]` are selected from Lean's native attribute grammar under fixed initial registrations. The P0 `deriving` allowlist consists only of named, versioned Lean handlers. **`GetElem`** (`xs[i]`, `xs[i]?`, `xs[i]!`, `xs[i]'h`), `List`/`Array` literals, `s!`/raw strings and `if let` are now required selected Lean source syntax, not imported TypeScript conveniences.

The required basis-type inventory in §8 includes `Unit`, `Bool`, `Nat`, `Int`, fixed-width signed/unsigned integer families, `Float`/`Float32`, `Char`, `String`, `ByteArray`, `Prod`, `Sum`, `Option`, `Except`, `List`, `Array`, `Fin`, `Subtype`, and the explicitly adopted candidate `Empty`/`BitVec n` families. **These are different from JavaScript `number`, `string`, object, or array semantics**; some have kernel/runtime special support, others are ordinary library-defined Lean families. Map/set/JSON/io APIs belong to the versioned library/boundary capability surface in §8A, not to the grammar.

The Standard environment snapshot must freeze the source-observable instances, tactics, priority/defaulting behavior, deriving handlers, notation/attributes, imported modules and proof-extension registration identities. The Lean git commit pins upstream **source**, not the full custom `pscv0` environment digest. Until the snapshot is generated and tested, final conformance must not be claimed.

### 11.10 End-to-end side-by-side program

**Lean 4.35.0-rc4:**

```lean
structure User where
  id : Nat
  name : String

def label (u : User) (fallback : String := "anonymous") : String :=
  if u.name == "" then fallback else u.name

theorem andProof (P Q : Prop) (hp : P) (hq : Q) : P ∧ Q := by
  constructor
  · exact hp
  · exact hq

#check label
#check ∀ n : Nat, n = n
#eval label { id := 1, name := "Ada" }
```

**ProofScript `pscv0` (design illustration):**

```proofscript
structure User where {
  id: Nat
  name: String
}

function label(u: User, fallback: String := "anonymous"): String := {
  if (u.name == "") { fallback } else { u.name }
}

theorem andProof(P: Prop, Q: Prop, hp: P, hq: Q): P ∧ Q := by {
  constructor
  · exact hp
  · exact hq
}

#check label
#check forall n : Nat, n = n
#eval label({ id := 1, name := "Ada" })
```

The paired source is illustrative; exact acceptance depends on admitted static method/instance sets, RC4 experimental language bindings, and actual parser/typechecker conformance.

### 11.11 Rejection examples and what schematic grammar does not prove

| Rejected `.ps` source | Reason / replacement |
|---|---|
| `f ()` | forbidden Lean spaced Unit application; write `f(())` |
| `f (x)` | forbidden spaced parenthesized application; write `f(x)` |
| `f (x, y)` | forbidden tuple/arity whitespace trap; write `f((x, y))` |
| `theorem t(P: Prop, hp: P): P := by { . exact hp }` | ASCII `.` is not Lean goal bullet; use `· exact hp` |
| `ghost mut n := 0` | no `ghost` keyword; use RC4 `erased mut n := 0` in admitted `do` context |
| `refine type Positive := Nat where n => n > 0` | no `refine type`; use `abbrev Positive := {n : Nat // n > 0}` |
| `verify f := by { omega }` | no extra declaration head; use Lean theorem/checkable VC |
| `exist x : Nat, x = x` | singular `exist` is not a Lean quantifier; use `exists` or `∃` |
| `if b then 1 else 2` | native Lean layout is not `.ps` conditional; write `if (b) {1} else {2}` |
| `by
  rfl` | `.ps` uses braced `by { rfl }`; native `.lean` remains unaffected |

No statement here proves actual compiler implementation or complete Lean parser compatibility. The reference is a **closed design overlay**, not a claim that arbitrary upstream Lean notation, macros, tactic parsers, or library definitions have become part of `pscv0`.

## 12. Separator, whitespace, and brace ownership

The separator policy follows Lean syntax **within** each selected construct but chooses only one source spelling for ambiguous `pscv0` bodies and argument application. There is **no universal JavaScript automatic semicolon insertion**.

| Construct | Lean 4 | `pscv0` | Separator / ownership |
|---|---|---|---|
| Explicit declaration parameter group | Lean binder telescope `(x : A) (y : B)` | `function f(x: A, y: B)` | commas inside the single group; one optional trailing comma |
| Two arguments | `f x y` | `f(x, y)` **or** Lean unparenthesized `f x y` | curry semantics; adjacent parentheses mean comma list |
| One tuple | `f (x, y)` | `f((x, y))` | one tuple term enclosed as one call argument |
| Explicit Unit | `f ()` | `f(())` | no gap-parenthesized call permitted |
| Source-empty call | not a separate native core arity | `f()` | defaults/automatics or exactly-one-Unit completion only |
| Values | `{ x := a, y := b }` | same | comma-separated nominal record fields |
| `Subtype` | `{x : T // P x}` | same | native double slash, not a record value |
| Structure/class declarations | Lean `where` layout | `where { ... }` | newline/layout fields, **not commas** |
| Instance fields | Lean `where` layout | `where { ... }` | native field declarations, no general comma/semicolon list |
| Match cases | `match x with | ...` | `match x with { | ... }` | Lean `|` alternatives |
| Inductive constructors | `where | ctor ...` | `where { | ctor... }` | Lean `|` alternatives |
| Braced declaration body | `:= term` | `:= { oneTerm }` or `:= term` | one term only, not a JS statement block |
| `if` | `if p then a else b` | `if (p) { a } else { b }` | exactly one term in each branch |
| `do` | `do` layout/brackets | `do { ... }` | native selected `doSeqItem` newline layout |
| `by` | `by` layout/brackets | `by { ... }` | selected native tactic grammar; `·` and `case` for subgoals |
| `where` locals | Lean layout | `where { ... }` | local declaration grammar |
| Mathematical symbols | `∀`, `∃`, `∧`, `↔`, `λ`, `→` | same | their native Lean counterpart spellings coexist |

### 12.1 No space before a parenthesized argument

**This is a parse rule rather than a linter preference.** Both `f(x, y)` and Lean `f (x, y)` can be meaningful, but with different arities. Therefore the latter is **not valid `.ps` when the parentheses would be an application operand**. Likewise `f ()` is rejected in that role; explicit `Unit` is `f(())`. **The rule is categorically limited to term application** and does not reject `variable (n: Nat)`, `fun (n: Nat) => ...`, `#check (f x)`, `exact (hp)`, or `x + (y * z)`. A formatter must not introduce an application gap or silently rewrite `f((x, y))` to `f(x, y)`.

### 12.2 Brace ownership

| Source | Selected grammar family | Precise meaning |
|---|---|---|
| `:= { x + 1 }` | definition body expression wrapper | exactly one term |
| `:= { id := 1, name := "Ada" }` | structure instance term | nominal expected structure, not a JS object |
| `:= {{ id := 1 }}` | body wrapper around a record value | still one structure value, not nested objects |
| `{ n : Nat // n > 0 }` | native subtype term | refined Lean type, not an expression block |
| `if (b) { a } else { c }` | conditional branches | one term per branch |
| `do { ... }` | selected Lean monadic sequencing | multiple `doSeqItem`s, no generic JS statements |
| `by { constructor
  · exact hp
  · exact hq }` | Lean tactic sequencing with focused goals | proof term construction, not ordinary runtime block |
| `structure S where { x: Nat }` | structure field sequence | Lean-dependent/nominal fields |
| `match x with { | .some(y) => y | .none => 0 }` | match alternatives | exhaustive selected Lean pattern checking |

### 12.3 Delimiter and Unicode hygiene

Whitespace or comments may occur between normal Lean tokens where its selected lexical rules permit them. **Only continuation of an already-completed callable with a parenthesized operand is special:** a space, line break, or comment between callable and `(` invalidates **that application** in `.ps`. This is not a global adjacency rule for binder declarations or standalone grouping. Mathematical Unicode tokens such as `∀`, `∃`, `·`, `λ`, and `→` are recognized as genuine source tokens, not editor decoration. The ASCII `.` for field notation does not become the distinct Unicode tactic bullet `·`.

## 13. Language acceptance, rejection, and minimal conformance cases

These are **proposed conformance cases**, not executed checks. Positive cases still need elaboration and proof verification under the pinned RC4 environment; negative cases define grammar/type/profile rejection criteria.

| ID | `.ps` fragment | Expected result | Why |
|---|---|---|---|
| P-DECL-1 | `const count: Nat := 3` | accept | parameterless `def` sugar |
| P-DECL-2 | `function add(x: Nat, y: Nat): Nat := x + y` | accept | comma explicit binders |
| P-DECL-3 | `function now(): Nat := 42` | accept | required `Unit` binder lowering |
| P-CALL-1 | `add(1, 2)` | accept | two explicit arguments |
| P-CALL-2 | `add 1 2` | accept | unchanged Lean unparenthesized application |
| P-CALL-3 | `tupleFn((1, 2))` | accept for suitable tupleFn | one tuple argument |
| P-CALL-4 | `unitFn(())` | accept for suitable unitFn | one explicit `Unit` argument |
| P-CALL-5 | `now()` | accept | inserts required `Unit` from empty-call rule |
| P-CALL-6 | `greet()` with all-explicit-defaulted parameter list | accept | declared defaults applied |
| P-CALL-7 | `f(g x)` with suitable `f`, `g` | accept | Lean application inside adjacent comma call |
| P-CALL-8 | `(f)(x)` with suitable `f`, `x` | accept | grouped callable immediately followed by postfix call |
| P-CALL-9 | `f(())` applied to `function f(): Nat` | accept | explicit Unit may coincide with source-empty Unit completion |
| P-CALL-10 | `#check (f x)` with suitable `f`, `x` | accept | grouped initial term for diagnostic |
| P-CALL-11 | `x + (y * z)` with suitable operands | accept | fresh operand grouping after infix |
| P-CALL-12 | `exact (hp)` in a proof goal `P` with `hp : P` | accept | grouped initial tactic argument, not application |
| P-CALL-13 | `exact h(p)` in a proof with `h : P → Q`, `p : P` and goal `Q` | accept | same adjacent-call grammar in tactic term |
| P-CALL-14 | `#eval now()` where `now` is source-nullary/pure | accept | diagnostic uses same `f()` completion |
| P-CALL-15 | `variable (n: Nat)` | accept | grammar category is a binder, not application |
| P-CALL-16 | `fun (n: Nat) => n` | accept | grammar category is typed lambda binder |
| P-PROOF-1 | `by { constructor
  · exact hp
  · exact hq }` in `P ∧ Q` proof | accept | native Lean subgoal bullets |
| P-PROOF-2 | `by { exact ⟨0, rfl⟩ }` | accept with `∃ x, x = 0` expected | native constructor syntax |
| P-MATH-1 | `forall n : Nat, n = n` | accept | native ASCII quantifier |
| P-MATH-2 | `∀ n : Nat, n = n` | accept | native Unicode quantifier |
| P-MATH-3 | `exists n : Nat, n = 0` / `∃ n : Nat, n = 0` | accept | native existence notations |
| P-TYPE-1 | `abbrev Positive := {n : Nat // n > 0}` | accept | Lean `Subtype` notation |
| P-TYPE-2 | `const p: Positive := ⟨1, by { decide }⟩` | accept with appropriate imports | native subtype witness/proof |
| P-ERASED-1 | `erased mut steps : Nat := 0` inside admitted verified `do` | accept when RC4 model available | native Lean verification state |
| P-DIAG-1 | `#check Nat.succ` | accept | native diagnostic |
| P-DIAG-2 | `#eval (1 + 2 : Nat)` | accept in pure subset | no proof authority |
| P-PAT-NAT-1 | `match n with { | 0 => 0 | k + 1 => k }` where `n : Nat` | accept | pinned Lean Nat successor pattern |
| P-PAT-NAT-2 | `match n with { | 0 => 0 | .succ k => k }` where `n : Nat` | accept | equivalent constructor syntax |
| P-PAT-NAT-3 | `match n with { | 0 => 0 | 1 => 1 | k + 2 => k }` where `n : Nat` | accept | fixed positive literal successor count |
| P-SECTION-1 | `variable (n: Nat)` and `def r: Nat := n + 1` on separate lines inside `section ... end`, then `#check r` | accept | `r` has an explicit `Nat` parameter; commands are newline-separated |
| P-DIAG-SECTION | `#check MathOps.twice(7)` after defining `MathOps.twice` | accept | native inspection over PSCV0 calls |
| N-PAT-NAT-1 | `| 1 + k => ...` in `Nat` match | **elaboration reject** | not reducible to accepted binder-constructor pattern |
| N-PAT-NAT-2 | `| k + m => ...` with unconstrained `m` | **reject** | no arbitrary arithmetic pattern unification |
| N-PAT-NAT-3 | `| k - 1 => ...` in `Nat` match | **reject** | subtraction is not Nat predecessor pattern syntax |
| N-CALL-1 | `now ()` | **parse reject** | spaced `Unit` application forbidden |
| N-CALL-2 | `unitFn ()` | **parse reject** | explicit unit must be `unitFn(())` |
| N-CALL-3 | `add (1, 2)` | **parse reject** | gap before parenthesized argument |
| N-CALL-4 | `tupleFn (1, 2)` | **parse reject** | tuple ambiguity removed |
| N-CALL-5 | `add (1)` | **parse reject** | only adjacent `add(1)` accepted |
| N-CALL-6 | `add/* c */(1, 2)` | **parse reject** | trivia breaks call adjacency |
| N-CALL-7 | `add()` with two required `Nat` parameters | **elaboration reject** | no arbitrary filler |
| N-CALL-8 | `f(x := 1, 2)` | **reject** | positional after named |
| N-CALL-9 | `h (g x)` in an expression | **parse reject** | parenthesized Lean application argument, use `h(g x)` |
| N-CALL-10 | `(h) (x)` in an expression | **parse reject** | gap-parenthesized application after grouped callable |
| N-CALL-11 | `#check f ()` | **parse reject** | commands share `.ps` term grammar, use `#check f(())` |
| N-CALL-12 | `#eval now ()` | **parse reject** | diagnostic expression cannot bypass gap rule |
| N-CALL-13 | `by { exact h (hp) }` when `h` is callable | **parse reject** | tactic argument cannot bypass gap rule |
| N-CALL-14 | `f()` with two required `Unit` parameters | **elaboration reject** | empty call cannot synthesize two required Unit values |
| N-CALL-15 | `f()` with an unresolved required non-Unit explicit parameter | **elaboration reject** | no arbitrary default or implicit partial application |
| N-PROOF-1 | `by { constructor
  . exact hp
  . exact hq }` | **parse reject** | `.` is not Lean `·` bullet |
| N-PROOF-2 | `theorem bad(P: Prop): P := by { sorry }` | **reject verified status** | admitted proof holes not checked evidence |
| N-MATH-1 | `exist n : Nat, n = n` | **parse reject** | native word is `exists` |
| N-ERASED-1 | `ghost mut steps := 0` | **parse reject** | use `erased` |
| N-TYPE-1 | `refine type Positive := Nat where n => n > 0` | **parse reject** | use native `Subtype` |
| N-TYPE-2 | `structure A where { x: Nat } invariant self => ...` | **parse reject** | use explicit proof field |
| N-PROOF-3 | `verify f := by { omega }` | **parse reject** | use `theorem` / accepted VC proof |
| N-CONTROL-1 | `if b then 1 else 0` | **parse reject in `.ps`** | one braced conditional spelling |
| N-CONTROL-2 | `by
  rfl` | **parse reject in `.ps`** | one `by { ... }` spelling |
| N-DIAG-1 | `#eval IO.println "hi"` | **reject closed source** | world effect not pure diagnostic |
| N-TRUST-1 | user `axiom h : False` | **reject closed verified profile** | unapproved assumption |
| N-TRUST-2 | `partial def ...` | **reject in all `.ps` source**, including ordinary mode | separate non-PSCV runtime adapter if unavoidable |

### New P0/P1 acceptance and rejection cases (required tests, not recorded results)

| Case | `.ps` source / scenario | Expected result / invariant | Priority |
|---|---|---|---|
| P-MATCH-2 | `match x, y with { | .some a, .some b => a + b | _, _ => 0 }` on `Option Nat` | accepted; same two-discriminant Lean elaboration as native `match` | P0 |
| P-MATCH-DEPENDENT | `match (generalizing := true) index with { ... }` with an indexed scrutinee/motive | accepted only if pinned Lean elaboration succeeds; core evidence checked | P0 |
| P-MATCH-NAMED | `match h : value with { ... }` | binds correct equality hypothesis, not a function call | P0 |
| N-MATCH-ARITY | two discriminants but a branch provides one pattern | reject | P0 |
| N-MATCH-COVERAGE | incomplete constructor coverage | reject, no runtime `match failure` fallback | P0 |
| P-IFLET | `if let .some n := x { n } else { 0 }` where `x: Option Nat` | accepted, bound `n` visible only in success branch | P0 |
| P-DITE | `if (h : i < xs.size) { xs[i]'h } else { ... }` with matching result types | check `h`/`¬h` scopes against Lean dependent `if` | P0 |
| N-IFLET-SCOPE | reference bound `n` from success arm in else arm | reject | P0 |
| P-NOMATCH | `nomatch e` for `e: Empty` | accepted via checked empty elimination | P0 |
| N-NOMATCH | `nomatch n` where `n: Nat` | reject: constructors remain | P0 |
| P-DERIVING | `structure P where { x: Nat } deriving Repr, BEq` | accepted only under allowlisted versioned handlers; generated declarations checked | P0 |
| N-DERIVING-UNKNOWN | `deriving SomeUnregisteredClass` | reject or explicit unregistered-handler error | P0 |
| P-INDEX-PROOF | `xs[i]'h` with `h: i < xs.size` | accepted, proof-checked `GetElem` | P0 |
| P-INDEX-OPTION | `xs[i]?` with out-of-bounds index | returns `none`, not a JS `undefined` | P0 |
| N-INDEX-PROOF | `xs[i]` with unresolved validity obligation | elaboration rejects or leaves blocking goal; never silently checked | P0 |
| P-STR-INTERP | `s!"x = {f(x)}"` | `ToString` insertion, same `.ps` call grammar inside interpolation | P0 |
| N-STR-GAP | `s!"x = {f (x)}"` | reject `.ps` gap-parenthesized application inside interpolation | P0 |
| P-STR-RAW | `r#"unescaped \n and "quotes""#` | raw string literal, no expression interpolation | P0 |
| P-EXCEPT | `try`/`catch` in `Except String` `do` block | typed handler semantics checked; exact `.ps` delimiters validated | P1 |
| N-FINALLY | `finally` without an admitted `MonadFinally` instance | typeclass/elaboration reject | P1 |
| P-PROOF-ENV | import pinned named tactic manifest and produce proof term | accepted **only** with checked proof and approved axiom closure | P1 |
| N-PROOF-ENV | unpinned installed plugin injects new notation or axiom | reject environment/verified status | P1 |
| P-ORDINARY-IO | declared `IO` boundary in ordinary checked output | allowed as ordinary executable only, with explicit effect identity | P1 |
| N-VERIFIED-IO | the same IO output claims closed verified certificate with no model | block verified emission | P0 |
| N-PARTIAL | `partial def` in `.ps` source | reject under current `pscv0` grammar, including ordinary mode | P0 |
| N-TRUST-DERIVE | deriving handler claims a law but generated proof has hole/axiom outside policy | no closed verified acceptance | P0 |

All rows require executable implementation tests before any conformance claim. The strings shown in source/examples remain design fixtures until the formatter/parser/elaborator and Lean-reference lanes run them.

**Metamorphic assertions to execute:** `function now()` + `now()` must elaborate to the corresponding pinned Lean `def now (_u : Unit)` + `now ()`, while `now ()` is invalid **as `.ps`**; `f((x,y))` must elaborate to the same core term as Lean `f (x,y)`; `f(x,y)` must elaborate to Lean `f x y`; `#check (f x)` and `exact (hp)` must remain valid fresh-term groupings; `variable (n: Nat)` and `fun (n: Nat) => n` must remain legal binders; and **the same** `PSCV0-APP-02` rejection must apply to `#check f (x)` and `by { exact h (p) }`. The native `·` bullet must produce the same focused subgoals as Lean; `forall`/`∀` and `exists`/`∃` must elaborate identically; `erased` must preserve verified noninterference; `Subtype` must use Lean's normal proof term/erasure meaning; error cases must be rejected without fallback to unrestricted Lean parser extensions.

## 14. Research outcome, decisions, and remaining conformance work

The design criterion was **maximum Lean semantic/syntactic reuse with only high-value ProofScript surface differences**. The following are user-requested design decisions; they are *not* claims that the compiler currently implements every feature.

| Question | Decision | Support / remaining risk |
|---|---|---|
| Lean baseline | pin **`v4.35.0-rc4`**, SHA `c29b6dda4f7c20e3eeaa717c4e565663c5cfa364` | GitHub RC4 release/tag and official release notes; prerelease |
| Language identity | keep `const`, `function`, `def`; names lower to Lean declarations | distinctive but logically conservative |
| `f ()` vs `f()` | **reject `f ()` in `.ps` application positions** | avoids visually indistinguishable Unit application / empty call; preserve binder parentheses |
| `f (x,y)` vs `f(x,y)` | **reject `f (x,y)` in `.ps`** | prevents changing argument arity by a whitespace edit |
| `f(())` | valid explicit `Unit` argument | maps to ordinary Lean `f ()` |
| Native `f x y` | retain | useful for mathematical applications; unambiguous without parenthesized operand |
| Proof branch `. exact` | **reject ASCII `.`**; use native `· exact` | confirmed Lean tactic-language bullet is U+00B7 |
| Goal control | native `·`, `case`, `next`, selected `all_goals`, `<;>` | use upstream fixed tactic parser, never a new bullet language |
| `ghost` | **drop**; use RC4 `erased` | upstream syntax present, albeit experimental |
| `refine type` | **drop**; use `Subtype` and `{x : A // P x}` | native Lean type and notation |
| Structure `invariant self` | **drop**; use proof field | avoids hidden semantic changes and redundant grammar |
| `verify target` | **drop**; use theorem / `by` / VC proof | one proof language, checked evidence |
| `∀`/`forall`, `∃`/`exists` | **both admitted** as native Lean notation | text forms are real Lean syntax; singular `exist` excluded |
| Braced vs Lean indentation body | one `.ps` braced spelling | user-facing consistency; Lean `.lean` remains native |
| `requires`, `ensures`, `given`, `invariant`, `decreasing` | retain selected Lean RC4 intrinsic verification vocabulary | upstream experimental; require pinned proof semantics |
| `old` / `reads` / `modifies` / `errors` | defer as distinct language keywords | no confirmed native RC4 equivalents; can start with Lean propositions/WP effects |
| Types / literals | preserve named Lean scalar, container, dependent and proof-indexed families | catalog §8; freeze exact Std environment for conformance |
| `Nat` successor matching | accept both `| k + 1 => ...` and `| .succ k => ...`; prefer arithmetic form in examples | pinned Lean built-in match-pattern expansion; **not** general arithmetic pattern solving |
| `variable (n : Nat)` | retain Lean section-parameter generalization under `PSCV0-BIND-01` | command binder is a different grammar category from term application; theorem statement generalization rules apply |
| Lean-style `#check` / proof editing | already accepted; specify full useful editor feedback and source spans | future VS Code/LSP InfoView target, **not** proof or unrestricted Lean feature parity |
| Multi-discriminant/dependent `match` | **adopt selected Lean RC4 features** | preserves mathematical elaboration, proof terms and exhaustiveness; complete parser tests still pending |
| `if let`, `nomatch`, `matches`, let-patterns | **adopt selected Lean native terms**, with `.ps` braces where relevant | do not substitute TS union narrowing or unchecked cast semantics |
| Native `deriving` | **P0** trailing handler allowlist (`Repr`, `BEq`, `DecidableEq`, `Inhabited`, `Hashable`) | frozen handler provenance; no arbitrary dependency-based handlers |
| Strings and indexing | **P0** `s!`/raw strings, `GetElem`, `xs[i]`, `xs[i]?`, `xs[i]!`, array/list literals | pin lexer/parser and instance availability; `!` may panic |
| Monadic exceptions | **P1** admit selected `try`/`catch`/`finally` and `throw` under typed effects | exact proposed `.ps` brace mapping needs conformance; no JS exception model |
| Maps/sets, JSON, codecs, IO, HTTP, task APIs | **P1 library/boundary** guarantee, not added keywords | require stable actual Std/module signatures; distinguish external validation from proof |
| Proof tactics and theorem libraries | selected expanded native tactic grammar + **opt-in pinned extension environment** | kernel-checked output, no arbitrary proof authority; digest/registration audit |
| Ordinary versus verified artifacts | **one language; separate assurance/emission status** | ordinary typed boundaries remain unverified; mandatory proof obligations block verified output |
| Types and API completeness | preserve §8 type roster; guarantee practical P0 standard APIs in §8A | avoid “type exists therefore ergonomic library exists” false inference |

### 14.1 Primary remaining checks

1. **Parser acceptance closure.** Confirm selected Lean grammar categories and differentiate binder, fresh-term, and application-continuation positions. Exercise `PSCV0-APP-01`, `PSCV0-APP-02`, `PSCV0-APP-03`, `PSCV0-BIND-01` in ordinary functions, theorem propositions, tactic terms, `do`, contracts and diagnostic commands. Also check Lean-native `Nat` patterns `k + 1`/`k + 2`, codepoint `·` versus `.`, and `exists` versus `exist`. Verify `1 + k`/`k + m` do not silently become structural constructor patterns.
2. **Elaboration correspondence.** Differentially compare `const`, `function`, named/default parameters, `f()`, `f(())`, `f((x,y))`, `f(x,y)`, type ascription, `Subtype`, constructors and Unicode/text quantifier spellings to Lean RC4 core terms.
3. **Lean tactic integration.** Validate `by { constructor; · exact hp; · exact hq }` under actual RC4 brace/newline parser rules; check `case`, `next`, `all_goals`, `<;>` and selected tactic variants without silently enabling arbitrary import-provided tactic macros.
4. **Lean 4.35 intrinsic verification.** Verify exact RC4 semantics of `given`, `requires`, `ensures`, `assert`, `erased`, `invariant`, `decreasing` and `vcgen`. Upstream explicitly marks this family experimental.
5. **Totality, dependencies and erasure.** Verify executable closure excludes unsupported `partial`, `unsafe`, open proof holes, noncomputable executable terms and unmodeled foreign effects. Validate erased state noninterference.
6. **Source formatter.** Round-trip `f(x,y)`, `f((x,y))`, `f(())`, native `f x y`, `variable (n: Nat)`, `#check (f x)`, `exact (hp)`, and tactic bullet `·` without altering parse trees/Lean elaborated meaning. Confirm a whitespace-only edit never changes a well-formed two-argument call into a well-formed one-tuple call.
7. **Source provenance and Standard registry.** Pin RC4 parser references, notation/token families, built-in `match_pattern` expansions (especially `Nat.add`), numerics, signed/fixed-width values, `BitVec`, `Empty`, and supported libraries to exact generated declarations and registries; don't claim a completed Standard environment digest before it has been built.

8. **Scope and Lean tooling.** Check explicit/implicit/instance `variable` elaboration, especially theorem statement dependency selection and recursive definitions' fixed section variables. Exercise `#check`/`#eval` with `.ps` names, section-generated parameters, and unresolved proof states. Preserve InfoTree/Infoview source positions for `.ps` in the future editor/LSP integration; never infer verified status from an editor's proof-goal display.

### 14.1A Prioritized evidence and release acceptance

| Priority | Design acceptance / deliverable | Explicit unverified status |
|---|---|---|
| **P0** | `function`, `const`, braced ownership, `PSCV0-APP-*` invariants, Lean binder/section syntax, native math/proofs | source design chosen, conformance corpus not yet executed |
| **P0** | selected multi-discriminant/dependent `match`, built-in patterns, `if let`, `nomatch`, `matches` | native Lean capability verified from docs; `.ps` parser/Lean-lowering still untested |
| **P0** | trailing `deriving` with exact allowed handler registry | native Lean supported; `pscv0` braces and handler snapshot need conformance |
| **P0** | string interpolation/raw literals, list/array literals, `GetElem` variants and P0 application APIs | source grammar/instances/behavior require final environment freeze |
| **P0** | theorem goals, `·`/case/next, `simp`/`omega`/`grind`, `#check`/`#print axioms`, genuine proof validation | broader proof grammar/IDE coverage and axiom audit tests required |
| **P0** | ordinary checked vs verified executable evidence identities; no proof holes, unsafe/partial leaks, incorrect effects | mandatory verified build gates require executable negative tests |
| **P1** | typed `try`/`catch`/`finally`, map/set/JSON codecs, IO/boundary APIs, named proof environments | precise sources and extension manifests to be pinned; no hidden JS semantics |
| **P2** | async/ownership/resource/UI sugar beyond Lean libraries | defer until measured gain and verified lowering |

**Verification corpus to construct:** positive and negative parsing; differential Lean RC4 elaboration and generated proof terms; real-world TS migration examples (JSON/collections/errors); theorem proofs including dependent matches and library tactics; specification and effect-boundary tests; formatter/source-map tests for `f(x, y)` vs `f((x, y))`; backend semantic preservation tests. Unmeasured scores or simulated passing tests are not conformance evidence.

### 14.2 What this revision does not do

It does **not** turn `pscv0` into unrestricted Lean 4, add new kernel primitives, equate runtime testing with proof evidence, reclassify raw `IO` as closed verified computation, or claim implementation/conformance tests were executed. It deliberately removes some *proposed* RC3 ProofScript conveniences because native Lean syntax already expresses the same thing more simply. It also restricts a small part of native Lean parenthesized application **only in `.ps`**, so the semantic-subset claim remains precise.

### 14.3 Design outcome and unresolved exact-source checks

This revision's answer to “more or fewer features?” is **richer native Lean coverage and stronger libraries, but fewer redundant ProofScript sugars**. The new P0 features above are adopted as proposed source-profile requirements, not as proven implementation status. P1 proof/IO/JSON extensions require explicit environment and boundary identities. P2 new keywords require real ergonomic evidence.

The highest remaining language-design risks are: (1) keeping `f()`/defaults/`Unit` completion unambiguous in all contexts; (2) faithfully mapping multi-scrutinee and dependent match syntax, plus `if let`, to the RC4 elaborator; (3) giving braces one clear grammar owner alongside record literals/`Subtype`/implicit binders; (4) ensuring `deriving` and tactics cannot alter accepted source meaning without a new environment identity; (5) exact `try`/`catch`/`finally` syntax and registered `MonadFinally` availability; and (6) preventing ordinary IO/boundary behavior from being mislabeled formally verified.

Native Lean features confirmed in current official reference: [Pattern Matching](https://lean-lang.org/doc/reference/latest/Terms/Pattern-Matching/), [Conditionals](https://lean-lang.org/doc/reference/latest/Terms/Conditionals/), [Deriving Instances](https://lean-lang.org/doc/reference/latest/Type-Classes/Deriving-Instances/), [GetElem](https://lean-lang.org/doc/reference/latest/Type-Classes/Basic-Classes/), [Strings](https://lean-lang.org/doc/reference/latest/Basic-Types/Strings/), [Do Notation](https://lean-lang.org/doc/reference/latest/Functors___-Monads-and--do--Notation/Syntax/), [Monadic Exceptions](https://lean-lang.org/doc/reference/latest/Functors___-Monads-and--do--Notation/Varieties-of-Monads/), [Custom Tactics](https://lean-lang.org/doc/reference/latest/Tactic-Proofs/Custom-Tactics/), and the [4.35 RC4 notes](https://lean-lang.org/doc/reference/latest/releases/v4.35.0/). The immutable git commit, not a moving documentation URL, remains the specified semantic-source pin.

## 15. Exact Lean 4.35.0-rc4 source concordance and research provenance

**Immutable pin:** [leanprover/lean4 release v4.35.0-rc4](https://github.com/leanprover/lean4/releases/tag/v4.35.0-rc4) → commit [`c29b6dda4f7c20e3eeaa717c4e565663c5cfa364`](https://github.com/leanprover/lean4/commit/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364). This tag was released October 6, 2026. As checked October 11, 2026, it is the newest published **RC**, while 4.34.1 is the newest **stable**. An RC4 commit pin does not imply the eventual 4.35.0 final release has identical syntax/semantics.

| Lean source family | Pinned source / reference | Relevance and restrictions |
|---|---|---|
| Term parsing, `match`, `field`, records, application | [`src/Lean/Parser/Term.lean`](https://github.com/leanprover/lean4/blob/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/Lean/Parser/Term.lean) | Lean terms and whitespace application; PSCV0 adjacent comma calls are additional sugar |
| Declaration heads, `def`, structure, class, instance | [`src/Lean/Parser/Command.lean`](https://github.com/leanprover/lean4/blob/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/Lean/Parser/Command.lean) | native headers; `const` and `function` are PSCV0 aliases |
| Basic parser/identifiers/trivia | [`src/Lean/Parser/Basic.lean`](https://github.com/leanprover/lean4/blob/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/Lean/Parser/Basic.lean) | select Lean lexing rather than reconstruct lexical regexes |
| Binder terms and syntax | [`src/Lean/Parser/Term/Basic.lean`](https://github.com/leanprover/lean4/blob/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/Lean/Parser/Term/Basic.lean) | selected explicit, implicit, strict implicit, instance binder forms |
| `do`, mutable/erased state, loops | [`src/Lean/Parser/Do.lean`](https://github.com/leanprover/lean4/blob/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/Lean/Parser/Do.lean) | PS selected `do` grammar and experimental verification parallels |
| `#check` and `#eval` command parsing | [`src/Lean/Parser/Command.lean`](https://github.com/leanprover/lean4/blob/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/Lean/Parser/Command.lean) | same command spelling; PSCV0 restricts evaluation effects |
| `#reduce` syntax | [`src/Init/Notation.lean`](https://github.com/leanprover/lean4/blob/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/Init/Notation.lean) | reducibility diagnostic, not proof authority |
| Lean intrinsic contract elaboration | [`src/Lean/Elab/Tactic/Do/Contract.lean`](https://github.com/leanprover/lean4/blob/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/Lean/Elab/Tactic/Do/Contract.lean) | experimental `given`/`requires`/`ensures` proof construction |
| Lean verification-condition generation | [`src/Lean/Elab/Tactic/Do/VCGen.lean`](https://github.com/leanprover/lean4/blob/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/Lean/Elab/Tactic/Do/VCGen.lean) | source reference for checkable VCs, not a trusted oracle |
| Lean primitive kernel foundations | [`src/kernel`](https://github.com/leanprover/lean4/tree/c29b6dda4f7c20e3eeaa717c4e565663c5cfa364/src/kernel) | selected core theory, definitional equality, inductives, judgment checks |

**Official explanatory research (moving pages; pinned code above is normative for this proposal):**

- [Lean 4.35 RC4 release notes](https://lean-lang.org/doc/reference/latest/releases/v4.35.0/): especially erased state, `given`, VC/loop updates and upstream experimental warnings.
- [Function Application](https://lean-lang.org/doc/reference/latest/Terms/Function-Application/): juxtaposition/curried core, named/implicit/optional arguments.
- [Lean pattern matching](https://lean-lang.org/doc/reference/latest/Terms/Pattern-Matching/): `match_pattern` reduction and `Nat` syntax `k + 1` versus the invalid reversed form `1 + k`.
- [RC4 Namespaces and Sections](https://lean-lang.org/doc/reference/4.35.0-rc4/Namespaces-and-Sections/): generalization of explicit/implicit/instance section variables, theorem-header dependency rules, fixed section variables in recursive functions.
- [Lean tactic proofs](https://lean-lang.org/doc/reference/latest/Tactic-Proofs/): goal states, bullets, `case`, `next`, and tactic proof terms.
- [Lean Infoview](https://github.com/leanprover/vscode-lean4/tree/master/lean4-infoview): practical proof-state inspection and language-server integration.
- [Headers and Signatures](https://lean-lang.org/doc/reference/latest/Definitions/Headers-and-Signatures/): `declSig`, binder scopes, optional and automatic parameters.
- [Interacting with Lean](https://lean-lang.org/doc/reference/latest/Interacting-with-Lean/): distinction among `#check`, `#print`, `#reduce`, `#eval` and limits of execution as proof.
- [Basic Types](https://lean-lang.org/doc/reference/latest/Basic-Types/) and [Fixed-Precision Integers](https://lean-lang.org/doc/reference/latest/Basic-Types/Fixed-Precision-Integers/): data families, 8/16/32/64/word signed/unsigned types, wrapping behavior.
- [Terms](https://lean-lang.org/doc/reference/latest/Terms/), [Definitions](https://lean-lang.org/doc/reference/latest/Definitions/), [Monads and do-notation](https://lean-lang.org/doc/reference/latest/Functors___-Monads-and--do--Notation/): selected source syntax and elaboration context.

**Historical document attribution:** The uploaded *ProofScript PSCV Language Reference NORMATIVE RC-v2* (originally pinned to Lean 4.35.0-rc3) supplies the selected feature catalog and the older PSCV verification obligations. The earlier `pscv0` Lean-grammar-first comparison supplies the original topic pairings. **This revision** retains the RC4 pin but proposes a stricter `.ps` surface: required-Unit nullary lowering, admission of native Lean inspection commands and type families, rejection of gap-parenthesized application and duplicate unbraced body forms, native Lean tactic bullets, and removal of redundant ghost/refinement/verification aliases. It does **not** claim those changes were present in the earlier RC or already implemented in `psc0`.

**Research limitation:** Directly pinned source URLs anchor future verification; they do not automatically constitute successful parser/elaborator/kernel conformance runs. A released conforming `pscv0` would need a frozen environment manifest and executable positive/negative tests and proof replay as specified in §14.
