import Lean
import PS0.HostCategories
import PS0.Effect

/-!
PS0-owned Lean-syntax adapter, migrated from the earlier PSCVL experiment. It always lowers to genuine Lean
4.35.0 commands/terms; no separate typing rules or proof axioms.
All source forms absent from this file remain unsupported, even when their
keywords resemble facilities from the normative PSCV language reference.
-/

open Lean
open Lean.Parser.Term
open Lean.Parser.Command
open Lean.Elab.Term
open Lean.Meta

namespace PS0

syntax (name := pscvConst) "const " ident ":" term ":=" term : command
syntax (name := pscvConstInferred) "const " ident ":=" term : command

macro_rules
  | `(const $name:ident : $ty:term := $value:term) =>
    `(def $name : $ty := $value)
  | `(const $name:ident := $value:term) =>
    `(def $name := $value)

declare_syntax_cat pscvBinder
syntax ident ":" term : pscvBinder
syntax ident ":" term ":=" term : pscvBinder

declare_syntax_cat pscvNonExplicitBinder
syntax "{" ident ":" term "}" : pscvNonExplicitBinder
syntax "⦃" ident ":" term "⦄" : pscvNonExplicitBinder
syntax "[" ident ":" term "]" : pscvNonExplicitBinder
syntax "[" term "]" : pscvNonExplicitBinder
syntax "{{" ident ":" term "}}" : pscvNonExplicitBinder

private def explicitLeanBinders (bs : Array (TSyntax `pscvBinder))
    (nullaryFunction : Bool := false) :
    MacroM (Array (TSyntax ``Lean.Parser.Term.bracketedBinder)) := do
  let mut result := #[]
  for b in bs do
    match b with
    | `(pscvBinder| $x:ident : $t:term := $d:term) =>
        result := result.push (← `(bracketedBinder| ($x:ident : $t:term := $d:term)))
    | `(pscvBinder| $x:ident : $t:term) =>
        result := result.push (← `(bracketedBinder| ($x:ident : $t:term)))
    | _ => Macro.throwUnsupported
  if bs.isEmpty && nullaryFunction then
    -- Exact PSCV zero-source-parameter sugar: a required Unit binder,
    -- NOT a distinct JavaScript-style zero-arity function.
    result := result.push (← `(bracketedBinder| (_unit : Unit)))
  return result

private def nonExplicitLeanBinders (bs : Array (TSyntax `pscvNonExplicitBinder)) :
    MacroM (Array (TSyntax ``Lean.Parser.Term.bracketedBinder)) := do
  let mut result := #[]
  for b in bs do
    match b with
    | `(pscvNonExplicitBinder| {$x:ident : $t:term}) =>
        result := result.push (← `(bracketedBinder| {$x:ident : $t:term}))
    | `(pscvNonExplicitBinder| ⦃$x:ident : $t:term⦄) =>
        result := result.push (← `(bracketedBinder| ⦃$x:ident : $t:term⦄))
    | `(pscvNonExplicitBinder| [$x:ident : $t:term]) =>
        result := result.push (← `(bracketedBinder| [$x:ident : $t:term]))
    | `(pscvNonExplicitBinder| [$t:term]) =>
        result := result.push (← `(bracketedBinder| [$t:term]))
    | `(pscvNonExplicitBinder| {{$x:ident : $t:term}}) =>
        result := result.push (← `(bracketedBinder| ⦃$x:ident : $t:term⦄))
    | _ => Macro.throwUnsupported
  return result


/-- Comma-separated explicit binders on normal 'def' preserve Lean semantics. -/
syntax (name := pscvDefinition)
  "def " ident "(" pscvBinder,+ ")" ":" term ":=" term : command

macro_rules
  | `(def $f:ident ($[$bs:pscvBinder],*) : $result:term := $body:term) => do
    let binders ← explicitLeanBinders bs
    `(def $f:ident $binders:bracketedBinder* : $result:term := $body:term)

syntax (name := pscvFunction) "function " ident "(" pscvBinder,* ")" ":" term ":=" term : command
macro_rules
  | `(function $f:ident ($[$bs:pscvBinder],*) : $result:term := $body:term) => do
    let binders ← explicitLeanBinders bs true
    `(def $f:ident $binders:bracketedBinder* : $result:term := $body:term)

/-!
PS0 v1 standard host operand adaptation: typed function/const value
positions consume psTerm, not an implicit native category fallback.
The host tree reaches the explicit lowering boundary before Lean's
normal definition elaboration. All native declaration APIs are reused.
-/
syntax (name := ps0V1HostFunction) (priority := high)
  "function " ident "(" pscvBinder,* ")" ":" term ":=" psTerm : command
syntax (name := ps0V1HostConst) (priority := high)
  "const " ident ":" term ":=" psTerm : command

macro_rules (kind := ps0V1HostFunction)
  | `(function $f:ident ($[$bs:pscvBinder],*) : $result:term :=
      $body:psTerm) => do
    let binders ← explicitLeanBinders bs true
    let lowered ← PS0.Syntax.lower `psTerm body.raw
    let nativeBody : TSyntax `term := ⟨lowered⟩
    `(def $f:ident $binders:bracketedBinder* : $result:term := $nativeBody:term)

macro_rules (kind := ps0V1HostConst)
  | `(const $name:ident : $ty:term := $value:psTerm) => do
    let lowered ← PS0.Syntax.lower `psTerm value.raw
    let nativeValue : TSyntax `term := ⟨lowered⟩
    `(def $name:ident : $ty:term := $nativeValue:term)

/-- PS0 v1's other ordinary declaration aliases share the same
    host value-category boundary: implicit result inference and private
    visibility do not silently switch a body back to native term syntax. -/
syntax (name := ps0V1HostFunctionInferred) (priority := high)
  "function " ident "(" pscvBinder,* ")" ":=" psTerm : command
syntax (name := ps0V1HostConstInferred) (priority := high)
  "const " ident ":=" psTerm : command
syntax (name := ps0V1HostPrivateFunction) (priority := high)
  "private " "function " ident "(" pscvBinder,* ")" ":" term
  ":=" psTerm : command
syntax (name := ps0V1HostPrivateFunctionInferred) (priority := high)
  "private " "function " ident "(" pscvBinder,* ")" ":=" psTerm : command
syntax (name := ps0V1HostPrivateConst) (priority := high)
  "private " "const " ident ":" term ":=" psTerm : command
syntax (name := ps0V1HostPrivateConstInferred) (priority := high)
  "private " "const " ident ":=" psTerm : command

macro_rules (kind := ps0V1HostFunctionInferred)
  | `(function $f:ident ($[$bs:pscvBinder],*) := $body:psTerm) => do
    let binders ← explicitLeanBinders bs true
    let lowered ← PS0.Syntax.lower `psTerm body.raw
    let nativeBody : TSyntax `term := ⟨lowered⟩
    `(def $f:ident $binders:bracketedBinder* := $nativeBody:term)

macro_rules (kind := ps0V1HostConstInferred)
  | `(const $name:ident := $value:psTerm) => do
    let lowered ← PS0.Syntax.lower `psTerm value.raw
    let nativeValue : TSyntax `term := ⟨lowered⟩
    `(def $name:ident := $nativeValue:term)

macro_rules (kind := ps0V1HostPrivateFunction)
  | `(private function $f:ident ($[$bs:pscvBinder],*) :
      $result:term := $body:psTerm) => do
    let binders ← explicitLeanBinders bs true
    let lowered ← PS0.Syntax.lower `psTerm body.raw
    let nativeBody : TSyntax `term := ⟨lowered⟩
    `(private def $f:ident $binders:bracketedBinder* : $result:term := $nativeBody:term)

macro_rules (kind := ps0V1HostPrivateFunctionInferred)
  | `(private function $f:ident ($[$bs:pscvBinder],*) := $body:psTerm) => do
    let binders ← explicitLeanBinders bs true
    let lowered ← PS0.Syntax.lower `psTerm body.raw
    let nativeBody : TSyntax `term := ⟨lowered⟩
    `(private def $f:ident $binders:bracketedBinder* := $nativeBody:term)

macro_rules (kind := ps0V1HostPrivateConst)
  | `(private const $name:ident : $ty:term := $body:psTerm) => do
    let lowered ← PS0.Syntax.lower `psTerm body.raw
    let nativeBody : TSyntax `term := ⟨lowered⟩
    `(private def $name:ident : $ty:term := $nativeBody:term)

macro_rules (kind := ps0V1HostPrivateConstInferred)
  | `(private const $name:ident := $body:psTerm) => do
    let lowered ← PS0.Syntax.lower `psTerm body.raw
    let nativeBody : TSyntax `term := ⟨lowered⟩
    `(private def $name:ident := $nativeBody:term)

/-- PS0 v1 permits inference of the result type for both def and function.
    The native Lean elaborator still decides every implicit type/term. -/
syntax (name := pscvDefinitionInferred)
  "def " ident "(" pscvBinder,+ ")" ":=" term : command
syntax (name := pscvFunctionInferred)
  "function " ident "(" pscvBinder,* ")" ":=" term : command

macro_rules (kind := pscvDefinitionInferred)
  | `(def $f:ident ($[$bs:pscvBinder],*) := $body:term) => do
    let binders ← explicitLeanBinders bs
    `(def $f:ident $binders:bracketedBinder* := $body:term)

macro_rules (kind := pscvFunctionInferred)
  | `(pscvFunctionInferred| function $f:ident ($[$bs:pscvBinder],*) := $body:term) => do
    let binders ← explicitLeanBinders bs true
    `(def $f:ident $binders:bracketedBinder* := $body:term)



/-!
PS0 v1 uses native total and well-founded recursion with a measure
when the source uses the optional proof wrapper.
Lean's termination elaborator and all native partial/fixpoint forms remain
available according to their actual declaration and modifier categories.
-/
syntax (name := pscvFunctionTermination)
  "function " ident "(" pscvBinder,+ ")" ":" term ":=" term
  "termination_by " term : command

macro_rules (kind := pscvFunctionTermination)
  | `(function $f:ident ($[$bs:pscvBinder],*) : $ty:term := $body:term
      termination_by $measure:term) => do
    let binders ← explicitLeanBinders bs
    `(def $f:ident $binders:bracketedBinder* : $ty:term := $body:term
        termination_by $measure:term)

syntax (name := pscvFunctionTerminationProof)
  "function " ident "(" pscvBinder,+ ")" ":" term ":=" term
  "termination_by " term "decreasing_by " "by " tacticSeq : command

macro_rules (kind := pscvFunctionTerminationProof)
  | `(function $f:ident ($[$bs:pscvBinder],*) : $ty:term := $body:term
      termination_by $measure:term decreasing_by by $proof:tacticSeq) => do
    let binders ← explicitLeanBinders bs
    `(def $f:ident $binders:bracketedBinder* : $ty:term := $body:term
        termination_by $measure:term
        decreasing_by $proof:tacticSeq)

/-- Visibility maps to Lean's native private declaration modifier. -/
syntax (name := pscvPrivateConst)
  "private " "const " ident ":" term ":=" term : command
syntax (name := pscvPrivateConstInferred)
  "private " "const " ident ":=" term : command
syntax (name := pscvPrivateFunction)
  "private " "function " ident "(" pscvBinder,* ")" ":" term ":=" term : command
syntax (name := pscvPrivateFunctionInferred)
  "private " "function " ident "(" pscvBinder,* ")" ":=" term : command

macro_rules
  | `(pscvPrivateConst| private const $name:ident : $ty:term := $val:term) =>
    `(private def $name:ident : $ty:term := $val:term)
  | `(pscvPrivateConstInferred| private const $name:ident := $val:term) =>
    `(private def $name:ident := $val:term)
  | `(pscvPrivateFunction| private function $f:ident ($[$bs:pscvBinder],*) : $ret:term := $body:term) => do
    let binders ← explicitLeanBinders bs true
    `(private def $f:ident $binders:bracketedBinder* : $ret:term := $body:term)
  | `(pscvPrivateFunctionInferred| private function $f:ident ($[$bs:pscvBinder],*) := $body:term) => do
    let binders ← explicitLeanBinders bs true
    `(private def $f:ident $binders:bracketedBinder* := $body:term)

/-- Local where definitions use the explicit PS0V1 def grammar and are
lowered to Lean's native recursive local declarations. -/
declare_syntax_cat pscvWhereDef
syntax "def " ident "(" pscvBinder,+ ")" ":" term ":=" term : pscvWhereDef

syntax (name := pscvFunctionWhere)
  "function " ident "(" pscvBinder,* ")" ":" term ":=" term
  "where " "{" pscvWhereDef+ "}" : command

macro_rules (kind := pscvFunctionWhere)
  | `(function $f:ident ($[$bs:pscvBinder],*) : $ret:term := $body:term
      where { $locals:pscvWhereDef* }) => do
    let binders ← explicitLeanBinders bs true
    let mut nativeLocals : Array (TSyntax ``Lean.Parser.Term.letRecDecl) := #[]
    for localStx in locals do
      match localStx with
      | `(pscvWhereDef| def $n:ident ($[$args:pscvBinder],*) : $ty:term := $value:term) =>
        let explicit ← explicitLeanBinders args
        let localBinders : Array (TSyntax ``Lean.Parser.Term.letIdBinder) :=
          explicit.map fun binder => ⟨binder.raw⟩
        nativeLocals := nativeLocals.push
          (← `(letRecDecl| $n:ident $localBinders* : $ty:term := $value:term))
      | _ => Macro.throwUnsupported
    `(def $f:ident $binders:bracketedBinder* : $ret:term := $body:term
      where
        $nativeLocals:letRecDecl*)

/-- Theorem comma-binders are source-only sugar; Lean elaborates the same proof. -/
syntax (name := pscvTheorem)
  "theorem " ident "(" pscvBinder,+ ")" ":" term ":=" term : command

macro_rules
  | `(theorem $name:ident ($[$bs:pscvBinder],*) : $statement:term := $proof:term) => do
    let binders ← explicitLeanBinders bs
    `(theorem $name:ident $binders:bracketedBinder* : $statement:term := $proof:term)

/-- Non-explicit PSCV binders share Lean's implicit, strict-implicit, and
instance elaborator, rather than emulating the semantics in a new compiler. -/
syntax (name := pscvImplicitFunction)
  "function " ident pscvNonExplicitBinder+ "(" pscvBinder,* ")" ":" term ":=" term : command
syntax (name := pscvImplicitFunctionInferred)
  "function " ident pscvNonExplicitBinder+ "(" pscvBinder,* ")" ":=" term : command

macro_rules
  | `(function $f:ident $implicitBs:pscvNonExplicitBinder* ($[$bs:pscvBinder],*) : $result:term := $body:term) => do
    let imps ← nonExplicitLeanBinders implicitBs
    let args ← explicitLeanBinders bs true
    `(def $f:ident $imps:bracketedBinder* $args:bracketedBinder* : $result:term := $body:term)
  | `(function $f:ident $implicitBs:pscvNonExplicitBinder* ($[$bs:pscvBinder],*) := $body:term) => do
    let imps ← nonExplicitLeanBinders implicitBs
    let args ← explicitLeanBinders bs true
    `(def $f:ident $imps:bracketedBinder* $args:bracketedBinder* := $body:term)


/-!
PS0 v1's ordered binder telescope can mix explicit comma-groups with implicit,
strict-implicit and instance binders. The order is semantically significant:
dependent binder types are resolved by the native Lean declaration elaborator.
The source restriction forbids two adjacent explicit groups (BIND-02).
-/
declare_syntax_cat pscvTelescopeSegment
syntax "(" pscvBinder,+ ")" : pscvTelescopeSegment
syntax pscvNonExplicitBinder : pscvTelescopeSegment

private def orderedLeanBinders
    (parts : Array (TSyntax `pscvTelescopeSegment)) :
    MacroM (Array (TSyntax ``Lean.Parser.Term.bracketedBinder)) := do
  let mut result := #[]
  let mut precedingExplicit := false
  for part in parts do
    match part with
    | `(pscvTelescopeSegment| ($[$bs:pscvBinder],*)) =>
        if precedingExplicit then
          Macro.throwError "PS0V1-BIND-02: adjacent explicit groups must be joined by commas"
        let native ← explicitLeanBinders bs
        result := result ++ native
        precedingExplicit := true
    | `(pscvTelescopeSegment| $b:pscvNonExplicitBinder) =>
        let native ← nonExplicitLeanBinders #[b]
        result := result ++ native
        precedingExplicit := false
    | _ => Macro.throwUnsupported
  return result

syntax (name := pscvTelescopeFunction)
  "function " ident pscvTelescopeSegment+ ":" term ":=" term : command
syntax (name := pscvTelescopeFunctionInferred)
  "function " ident pscvTelescopeSegment+ ":=" term : command
syntax (name := pscvTelescopeDefinition)
  "def " ident pscvTelescopeSegment+ ":" term ":=" term : command
syntax (name := pscvTelescopeDefinitionInferred)
  "def " ident pscvTelescopeSegment+ ":=" term : command
syntax (name := pscvTelescopeTheorem)
  "theorem " ident pscvTelescopeSegment+ ":" term ":=" term : command

macro_rules (kind := pscvTelescopeFunction)
  | `(function $f:ident $parts:pscvTelescopeSegment* : $ty:term := $body:term) => do
    let native ← orderedLeanBinders parts
    `(def $f:ident $native:bracketedBinder* : $ty:term := $body:term)

macro_rules (kind := pscvTelescopeFunctionInferred)
  | `(function $f:ident $parts:pscvTelescopeSegment* := $body:term) => do
    let native ← orderedLeanBinders parts
    `(def $f:ident $native:bracketedBinder* := $body:term)

macro_rules (kind := pscvTelescopeDefinition)
  | `(def $f:ident $parts:pscvTelescopeSegment* : $ty:term := $body:term) => do
    let native ← orderedLeanBinders parts
    `(def $f:ident $native:bracketedBinder* : $ty:term := $body:term)

macro_rules (kind := pscvTelescopeDefinitionInferred)
  | `(def $f:ident $parts:pscvTelescopeSegment* := $body:term) => do
    let native ← orderedLeanBinders parts
    `(def $f:ident $native:bracketedBinder* := $body:term)

macro_rules (kind := pscvTelescopeTheorem)
  | `(theorem $f:ident $parts:pscvTelescopeSegment* : $ty:term := $proof:term) => do
    let native ← orderedLeanBinders parts
    `(theorem $f:ident $native:bracketedBinder* : $ty:term := $proof:term)

/-- Contracted functions use the proof-producing intrinsic Lean 4.35
WP semantics: `f.spec` must be discharged by pinned `vcgen`. -/
syntax (name := pscvFunctionContract)
  "function " ident "(" pscvBinder,* ")" ":" term
  "requires" term "ensures" ident "=>" term ":=" term : command

macro_rules
  | `(function $f:ident ($[$bs:pscvBinder],*) : $result:term
      requires $pre:term ensures $rv:ident => $post:term := $body:term) => do
    let binders ← explicitLeanBinders bs true
    `(def $f:ident $binders:bracketedBinder* : $result:term
        requires $pre:term
        ensures $rv:ident => $post:term := $body:term)

/-- Lean RC4 given binds logical specification parameters, not runtime
arguments. This syntax uses precisely the native given/contract elaborator. -/
syntax (name := pscvFunctionGivenContract)
  "function " ident "(" pscvBinder,* ")" ":" term
  "given" "(" ident ":" term ")" "requires" term
  "ensures" ident "=>" term ":=" term : command

macro_rules (kind := pscvFunctionGivenContract)
  | `(function $f:ident ($[$bs:pscvBinder],*) : $result:term
      given ($logical:ident : $logicTy:term)
      requires $pre:term ensures $rv:ident => $post:term := $body:term) => do
    let binders ← explicitLeanBinders bs true
    `(def $f:ident $binders:bracketedBinder* : $result:term
        given ($logical:ident : $logicTy:term)
        requires $pre:term
        ensures $rv:ident => $post:term := $body:term)

/-- A function over StateM/ReaderM/Except may bind the pre/post-state in
native Lean basicFun clauses. VC generation and proof remain upstream. -/
syntax (name := pscvFunctionEffectContract)
  "function " ident "(" pscvBinder,* ")" ":" term
  "requires" basicFun "ensures" basicFun ":=" term : command

macro_rules (kind := pscvFunctionEffectContract)
  | `(function $f:ident ($[$bs:pscvBinder],*) : $result:term
      requires $pre:basicFun ensures $post:basicFun := $body:term) => do
    let binders ← explicitLeanBinders bs true
    `(def $f:ident $binders:bracketedBinder* : $result:term
        requires $pre:basicFun
        ensures $post:basicFun := $body:term)

/-- Empty source calls use Lean's own optional-argument elaboration. A source
nullary function is a required Unit binder, not a second function type. -/
syntax:max (name := pscvEmptyCall) term:max noWs "(" ")" : term

@[term_elab pscvEmptyCall]
def elabPscvEmptyCall : TermElab := fun stx expectedType? => do
  let f : Term := ⟨stx[0]⟩
  let fn ← elabTerm f none
  -- Explicit empty-call punctuation is not a no-op on a non-callable value.
  -- Lean elaborates the head and determines whether it has a Pi telescope.
  let fnType ← whnf (← inferType fn)
  match fnType with
  | .forallE .. => pure ()
  | _ => throwError "PS0V1-CALL-EMPTY: head is not callable"
  let applied ← elabAppArgs fn #[] #[] expectedType? false false
  let restType ← whnf (← inferType applied)
  match restType with
  | .forallE binderName domain _ binderInfo =>
    unless binderInfo.isExplicit do
      throwError "PS0V1-CALL-EMPTY: unresolved implicit argument"
    let domain ← instantiateMVars domain
    if domain.hasMVar || !(← isDefEq domain (mkConst `Unit)) then
      throwError "PS0V1-CALL-EMPTY: unresolved required non-Unit argument"
    let unitValue ← elabTerm (← `(term| ())) (some domain)
    let completed := mkApp applied unitValue
    let remaining ← whnf (← inferType completed)
    if binderName != `_unit then
      match remaining with
      | .forallE nextName _ _ nextInfo =>
        if nextInfo.isExplicit && !nextName.isAnonymous then
          throwError "PS0V1-CALL-EMPTY: more than one required argument"
      | _ => pure ()
    return completed
  | _ =>
    return applied

/-- PS0V1 comma applications are curried Lean applications. Named arguments are
native Lean binder names and must follow all source positional arguments. -/
declare_syntax_cat pscvCallArg
syntax ident " := " term : pscvCallArg
syntax term : pscvCallArg
syntax:max (name := pscvCall) term:max noWs "(" pscvCallArg,+ ")" : term

macro_rules (kind := pscvCall)
  | `($f:term($[$args:pscvCallArg],*)) => do
    let mut parsedArgs : Array Syntax := #[]
    let mut seenNamed := false
    let mut used : Array Name := #[]
    for arg in args do
      match arg with
      | `(pscvCallArg| $n:ident := $v:term) =>
        if used.contains n.getId then
          Macro.throwError "PS0V1-CALL-NAMED: duplicate argument name"
        seenNamed := true
        used := used.push n.getId
        let named ← `(Lean.Parser.Term.namedArgument| ($n:ident := $v:term))
        parsedArgs := parsedArgs.push named.raw
      | `(pscvCallArg| $v:term) =>
        if seenNamed then
          Macro.throwError "PS0V1-CALL-ORDER: positional arguments cannot follow named arguments"
        parsedArgs := parsedArgs.push v.raw
      | _ => Macro.throwUnsupported
    -- A single Lean application node keeps defaults and named arguments in the
    -- same elaboration pass, rather than prematurely applying partial calls.
    return mkNode ``Lean.Parser.Term.app #[f.raw, mkNullNode parsedArgs]

/-- Use the native Lean structure-field parser inside PS0V1 braces. -/
syntax (name := pscvBracedStructure)
  "structure " ident " where " "{" structFields "}" : command

macro_rules (kind := pscvBracedStructure)
  | `(structure $s:ident where { $fields:structFields }) =>
    `(structure $s:ident where $fields:structFields)


/-- Parameterized data declarations reuse Lean's dependent structure elaborator. -/
syntax (name := pscvParameterizedStructure)
  "structure " ident "(" pscvBinder,+ ")" " where " "{" structFields "}" : command

macro_rules (kind := pscvParameterizedStructure)
  | `(structure $name:ident ($[$args:pscvBinder],*) where { $fields:structFields }) => do
    let binders ← explicitLeanBinders args
    `(structure $name:ident $binders:bracketedBinder* where $fields:structFields)

/-- Classes are native Lean type classes; the braces own only field layout. -/
syntax (name := pscvBracedClass)
  "class " ident " where " "{" structFields "}" : command
syntax (name := pscvParameterizedClass)
  "class " ident "(" pscvBinder,+ ")" " where " "{" structFields "}" : command

macro_rules
  | `(class $name:ident where { $fields:structFields }) =>
    `(class $name:ident where $fields:structFields)
  | `(class $name:ident ($[$args:pscvBinder],*) where { $fields:structFields }) => do
    let binders ← explicitLeanBinders args
    `(class $name:ident $binders:bracketedBinder* where $fields:structFields)

/-!
PS0 v1 includes braced instance initializers alongside native value-form
instance syntax. We reuse Lean's `structInst` term elaboration and
native instance declaration checker, including value-form instances.
-/

syntax (name := pscvBracedInstanceAnonymous)
  "instance " ":" term " where " term : command
syntax (name := pscvBracedInstanceNamed)
  "instance " ident ":" term " where " term : command

macro_rules (kind := pscvBracedInstanceAnonymous)
  | `(instance : $classTy:term where $fields:term) =>
      `(instance : $classTy:term := $fields:term)

macro_rules (kind := pscvBracedInstanceNamed)
  | `(instance $name:ident : $classTy:term where $fields:term) =>
      `(instance $name:ident : $classTy:term := $fields:term)

/-- Instance headers have the same ordered, Lean-grounded binder telescope
as PS0V1 definitions. They never acquire a synthetic Unit parameter. -/
syntax (name := pscvBracedInstanceTelescopeAnonymous)
  "instance " pscvTelescopeSegment+ ":" term " where " term : command
syntax (name := pscvBracedInstanceTelescopeNamed)
  "instance " ident pscvTelescopeSegment+ ":" term " where " term : command

macro_rules (kind := pscvBracedInstanceTelescopeAnonymous)
  | `(instance $parts:pscvTelescopeSegment* : $classTy:term where $fields:term) => do
    let binders ← orderedLeanBinders parts
    `(instance $binders:bracketedBinder* : $classTy:term := $fields:term)

macro_rules (kind := pscvBracedInstanceTelescopeNamed)
  | `(instance $name:ident $parts:pscvTelescopeSegment* :
      $classTy:term where $fields:term) => do
    let binders ← orderedLeanBinders parts
    `(instance $name:ident $binders:bracketedBinder* : $classTy:term := $fields:term)

/-!
PS0 v1: reuse Lean.Parser.Priority's native priority
parser and native instance typeclass registration, preserving imported
priority extensions and user-defined attributes.
-/
/-- PS0 v1 uses the *registered native Lean priority grammar*, not a
    frozen source-level shortlist. Imports and extensions can register
    additional valid priority forms under Lean's own rules. -/
syntax (name := pscvPrioritizedInstanceAnonymous)
  "instance " "(" &"priority" ":=" prio ")" ":" term " where " term : command
syntax (name := pscvPrioritizedInstanceNamed)
  "instance " "(" &"priority" ":=" prio ")" ident ":" term
  " where " term : command
syntax (name := pscvPrioritizedInstanceTelescopeAnonymous)
  "instance " "(" &"priority" ":=" prio ")" pscvTelescopeSegment+ ":" term
  " where " term : command
syntax (name := pscvPrioritizedInstanceTelescopeNamed)
  "instance " "(" &"priority" ":=" prio ")" ident pscvTelescopeSegment+ ":" term
  " where " term : command

macro_rules (kind := pscvPrioritizedInstanceAnonymous)
  | `(instance (priority := $sourcePriority:prio) : $ty:term where $fields:term) => do
        `(instance (priority := $sourcePriority:prio) : $ty:term := $fields:term)

macro_rules (kind := pscvPrioritizedInstanceNamed)
  | `(instance (priority := $sourcePriority:prio) $name:ident :
      $ty:term where $fields:term) => do
        `(instance (priority := $sourcePriority:prio) $name:ident :
        $ty:term := $fields:term)

macro_rules (kind := pscvPrioritizedInstanceTelescopeAnonymous)
  | `(instance (priority := $sourcePriority:prio) $parts:pscvTelescopeSegment* :
      $ty:term where $fields:term) => do
    let binders ← orderedLeanBinders parts
    `(instance (priority := $sourcePriority:prio) $binders:bracketedBinder* :
      $ty:term := $fields:term)

macro_rules (kind := pscvPrioritizedInstanceTelescopeNamed)
  | `(instance (priority := $sourcePriority:prio) $name:ident
      $parts:pscvTelescopeSegment* : $ty:term where $fields:term) => do
    let binders ← orderedLeanBinders parts
    `(instance (priority := $sourcePriority:prio) $name:ident $binders:bracketedBinder* :
      $ty:term := $fields:term)

/-- Mutual recursion is only a braced grouping of the official Lean mutual
declaration elaborator and termination checker. -/
syntax (name := pscvBracedMutual)
  "mutual " "{" command+ "}" : command

macro_rules (kind := pscvBracedMutual)
  | `(mutual { $cmds:command* }) =>
    `(mutual
      $cmds:command*
    end)

/-- PS0V1 constructors preserve Lean's original positivity and recursor rules. -/
declare_syntax_cat pscvConstructor
syntax "| " ident ":" term : pscvConstructor
syntax "| " ident "(" pscvBinder,+ ")" ":" term : pscvConstructor

syntax (name := pscvBracedInductive)
  "inductive " ident " where " "{" pscvConstructor+ "}" : command

macro_rules (kind := pscvBracedInductive)
  | `(inductive $s:ident where { $ctors:pscvConstructor* }) => do
    let mut native : Array (TSyntax ``Lean.Parser.Command.ctor) := #[]
    for c in ctors do
      match c with
      | `(pscvConstructor| | $ctor:ident : $ty:term) =>
        native := native.push (← `(ctor| | $ctor:ident : $ty:term))
      | `(pscvConstructor| | $ctor:ident ($[$bs:pscvBinder],*) : $ty:term) =>
        let bs ← explicitLeanBinders bs
        native := native.push (← `(ctor| | $ctor:ident $bs:bracketedBinder* : $ty:term))
      | _ => Macro.throwUnsupported
    `(inductive $s:ident where $native:ctor*)


/-- The PS0 alias derives through Lean's native registered handlers. -/
declare_syntax_cat pscvDeriver
syntax "Repr" : pscvDeriver
syntax "BEq" : pscvDeriver
syntax "DecidableEq" : pscvDeriver
syntax "Inhabited" : pscvDeriver
syntax "Hashable" : pscvDeriver

private def pscvDeriverIdent (d : TSyntax `pscvDeriver) : MacroM Ident := do
  match d with
  | `(pscvDeriver| Repr) => pure <| mkIdent `Repr
  | `(pscvDeriver| BEq) => pure <| mkIdent `BEq
  | `(pscvDeriver| DecidableEq) => pure <| mkIdent `DecidableEq
  | `(pscvDeriver| Inhabited) => pure <| mkIdent `Inhabited
  | `(pscvDeriver| Hashable) => pure <| mkIdent `Hashable
  | _ => Macro.throwUnsupported

syntax (name := pscvBracedStructureDeriving)
  "structure " ident " where " "{" structFields "}" " deriving " pscvDeriver,+ : command

macro_rules (kind := pscvBracedStructureDeriving)
  | `(structure $s:ident where { $fields:structFields } deriving $[$ds:pscvDeriver],*) => do
    let names ← ds.mapM pscvDeriverIdent
    `(structure $s:ident where
      $fields:structFields
      deriving $[$names:ident],*)

syntax (name := pscvBracedInductiveDeriving)
  "inductive " ident " where " "{" pscvConstructor+ "}" " deriving " pscvDeriver,+ : command

macro_rules (kind := pscvBracedInductiveDeriving)
  | `(inductive $s:ident where { $ctors:pscvConstructor* } deriving $[$ds:pscvDeriver],*) => do
    let mut native : Array (TSyntax ``Lean.Parser.Command.ctor) := #[]
    for c in ctors do
      match c with
      | `(pscvConstructor| | $ctor:ident : $ty:term) =>
        native := native.push (← `(ctor| | $ctor:ident : $ty:term))
      | `(pscvConstructor| | $ctor:ident ($[$bs:pscvBinder],*) : $ty:term) =>
        let bs ← explicitLeanBinders bs
        native := native.push (← `(ctor| | $ctor:ident $bs:bracketedBinder* : $ty:term))
      | _ => Macro.throwUnsupported
    let names ← ds.mapM pscvDeriverIdent
    `(inductive $s:ident where
      $native:ctor*
      deriving $[$names:ident],*)

/-- PS0V1 matches use a braced alternative sequence while keeping Lean's
native discriminants, pattern elaborator, motive inference, and exhaustiveness. -/
declare_syntax_cat pscvMatchAlt
syntax "| " term,+ " => " term : pscvMatchAlt

syntax (name := pscvBracedMatch)
  "match " matchDiscr,+ " with " "{" pscvMatchAlt+ "}" : term

private def pscvMatchAltsToLean
    (alts : Array (TSyntax `pscvMatchAlt)) :
    MacroM (Array (TSyntax ``Lean.Parser.Term.matchAlt)) := do
  let mut native := #[]
  for alt in alts do
    match alt with
    | `(pscvMatchAlt| | $pats:term,* => $rhs:term) =>
      native := native.push (← `(matchAltExpr| | $pats:term,* => $rhs:term))
    | _ => Macro.throwUnsupported
  return native

macro_rules (kind := pscvBracedMatch)
  | `(match $discrs:matchDiscr,* with { $alts:pscvMatchAlt* }) => do
    let native ← pscvMatchAltsToLean alts
    `(match $discrs:matchDiscr,* with $native:matchAlt*)

/-- Explicit generalization is the exact native Lean dependent-match flag. -/
syntax (name := pscvBracedGeneralizedMatch)
  "match " generalizingParam matchDiscr,+
  " with " "{" pscvMatchAlt+ "}" : term

macro_rules (kind := pscvBracedGeneralizedMatch)
  | `(match (generalizing := true) $discrs:matchDiscr,*
      with { $alts:pscvMatchAlt* }) => do
    let native ← pscvMatchAltsToLean alts
    `(match (generalizing := true) $discrs:matchDiscr,* with $native:matchAlt*)

/-- The type family of a dependent match remains Lean's checked motive. -/
syntax (name := pscvBracedMotiveMatch)
  "match " motive matchDiscr,+ " with " "{" pscvMatchAlt+ "}" : term

macro_rules (kind := pscvBracedMotiveMatch)
  | `(match (motive := $result:term) $discrs:matchDiscr,*
      with { $alts:pscvMatchAlt* }) => do
    let native ← pscvMatchAltsToLean alts
    `(match (motive := $result:term) $discrs:matchDiscr,*
      with $native:matchAlt*)

/-- PSCV pure conditional with explicit grouping and braces. It lowers to
Lean's ordinary typed `if`, and retains proof obligations. -/
syntax (name := pscvBracedIf)
  "if" "(" term ")" "{" term "}" "else" "{" term "}" : term

macro_rules
  | `(if ($condition:term) { $onTrue:term } else { $onFalse:term }) =>
    `(if $condition then $onTrue else $onFalse)

/-- Dependent if-binders use Lean's native proposition and branch hypotheses. -/
syntax (name := pscvBracedDependentIf)
  "if" "(" ident ":" term ")" "{" term "}" "else" "{" term "}" : term

macro_rules (kind := pscvBracedDependentIf)
  | `(if ($h:ident : $p:term) { $yes:term } else { $no:term }) =>
    `(if $h:ident : $p:term then $yes:term else $no:term)

/-- Pattern-binding conditional lowers to Lean's exhaustive match. -/
syntax (name := pscvBracedIfLet)
  "if " "let " term " := " term:max "{" term "}" "else" "{" term "}" : term

macro_rules (kind := pscvBracedIfLet)
  | `(pscvBracedIfLet| if let $pat:term := $discr:term { $success:term } else { $failure:term }) =>
    `(if let $pat:term := $discr:term then $success:term else $failure:term)

/-!
Source-only PS0V1 do-conditionals.  The pinned Lean Parser.Do.doIf already
owns typed statements and pattern-binding scope.  We only replace v7's
parenthesized condition and braced doSeq spelling with that native syntax.
Do NOT reimplement branch typing or pattern matching.
-/

syntax (name := pscvDoIfElse)
  "if" "(" term ")" doSeq "else" doSeq : doElem
syntax (name := pscvDoIf)
  "if" "(" term ")" doSeq : doElem

macro_rules (kind := pscvDoIfElse)
  | `(doElem| if ($cond:term) $yes:doSeq else $no:doSeq) =>
      `(doElem| if $cond:term then $yes:doSeq else $no:doSeq)

macro_rules (kind := pscvDoIf)
  | `(doElem| if ($cond:term) $yes:doSeq) =>
      `(doElem| if $cond:term then $yes:doSeq)

-- This is the doSeqItem form, distinct from the term-level if-let:
-- do branches are *sequences*, may omit else, and preserve Lean's pattern scope.
syntax (name := pscvDoIfLetElse)
  "if " "let " term " := " term:max doSeq "else" doSeq : doElem
syntax (name := pscvDoIfLet)
  "if " "let " term " := " term:max doSeq : doElem

macro_rules (kind := pscvDoIfLetElse)
  | `(doElem| if let $pat:term := $value:term $yes:doSeq else $no:doSeq) =>
      `(doElem| if let $pat:term := $value:term then $yes:doSeq else $no:doSeq)

macro_rules (kind := pscvDoIfLet)
  | `(doElem| if let $pat:term := $value:term $yes:doSeq) =>
      `(doElem| if let $pat:term := $value:term then $yes:doSeq)

/-- A one-term braced body is grouping, not a record/object literal. -/
syntax (name := pscvBracedExpression) "{" term "}" : term

macro_rules (kind := pscvBracedExpression)
  | `({ $inside:term }) => `(($inside:term))

/-- Pure/verified function declarations can have one-sided contracts. A missing
side is the true/top predicate in the pinned Lean WP contract semantics. -/
syntax (name := pscvFunctionEnsures)
  "function " ident "(" pscvBinder,* ")" ":" term
  "ensures" ident "=>" term ":=" term : command

macro_rules
  | `(function $f:ident ($[$bs:pscvBinder],*) : $result:term
      ensures $rv:ident => $post:term := $body:term) => do
    let binders ← explicitLeanBinders bs true
    `(def $f:ident $binders:bracketedBinder* : $result:term
        ensures $rv:ident => $post:term := $body:term)

syntax (name := pscvFunctionRequires)
  "function " ident "(" pscvBinder,* ")" ":" term
  "requires" term ":=" term : command

macro_rules
  | `(function $f:ident ($[$bs:pscvBinder],*) : $result:term
      requires $pre:term := $body:term) => do
    let binders ← explicitLeanBinders bs true
    `(def $f:ident $binders:bracketedBinder* : $result:term
        requires $pre:term := $body:term)


end PS0
