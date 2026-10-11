import Lean
import PSCVL.Effect

/-!
A finite, ProofScript-owned syntax bridge. It always lowers to genuine Lean
4.35.0-rc4 commands/terms; no separate typing rules or proof axioms.
All source forms absent from this file remain unsupported, even when their
keywords resemble facilities from the normative PSCV language reference.
-/

open Lean
open Lean.Parser.Term
open Lean.Parser.Command
open Lean.Elab.Term
open Lean.Meta

namespace PSCVL

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

private def explicitLeanBinders (bs : Array (TSyntax `pscvBinder)) :
    MacroM (Array (TSyntax ``Lean.Parser.Term.bracketedBinder)) := do
  let mut result := #[]
  for b in bs do
    match b with
    | `(pscvBinder| $x:ident : $t:term := $d:term) =>
        result := result.push (← `(bracketedBinder| ($x:ident : $t:term := $d:term)))
    | `(pscvBinder| $x:ident : $t:term) =>
        result := result.push (← `(bracketedBinder| ($x:ident : $t:term)))
    | _ => Macro.throwUnsupported
  if bs.isEmpty then
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
    | _ => Macro.throwUnsupported
  return result


/-- Comma-separated explicit binders on normal 'def' preserve Lean semantics. -/
syntax (name := pscvDefinition)
  "def " ident "(" pscvBinder,* ")" ":" term ":=" term : command

macro_rules
  | `(def $f:ident ($[$bs:pscvBinder],*) : $result:term := $body:term) => do
    let binders ← explicitLeanBinders bs
    `(def $f:ident $binders* : $result:term := $body:term)

syntax (name := pscvFunction) "function " ident "(" pscvBinder,* ")" ":" term ":=" term : command
macro_rules
  | `(function $f:ident ($[$bs:pscvBinder],*) : $result:term := $body:term) => do
    let binders ← explicitLeanBinders bs
    `(def $f:ident $binders* : $result:term := $body:term)


/-- Visibility maps to Lean's native private declaration modifier. -/
syntax (name := pscvPrivateConst)
  "private " "const " ident ":" term ":=" term : command
syntax (name := pscvPrivateConstInferred)
  "private " "const " ident ":=" term : command
syntax (name := pscvPrivateFunction)
  "private " "function " ident "(" pscvBinder,* ")" ":" term ":=" term : command

macro_rules
  | `(private const $name:ident : $ty:term := $val:term) =>
    `(private def $name:ident : $ty:term := $val:term)
  | `(private const $name:ident := $val:term) =>
    `(private def $name:ident := $val:term)
  | `(private function $f:ident ($[$bs:pscvBinder],*) : $ret:term := $body:term) => do
    let binders ← explicitLeanBinders bs
    `(private def $f:ident $binders* : $ret:term := $body:term)

/-- Local where definitions use the explicit PSCV0 def grammar and are
lowered to Lean's native recursive local declarations. -/
declare_syntax_cat pscvWhereDef
syntax "def " ident "(" pscvBinder,+ ")" ":" term ":=" term : pscvWhereDef

syntax (name := pscvFunctionWhere)
  "function " ident "(" pscvBinder,* ")" ":" term ":=" term
  "where " "{" pscvWhereDef+ "}" : command

macro_rules (kind := pscvFunctionWhere)
  | `(function $f:ident ($[$bs:pscvBinder],*) : $ret:term := $body:term
      where { $locals:pscvWhereDef* }) => do
    let binders ← explicitLeanBinders bs
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
    `(def $f:ident $binders* : $ret:term := $body:term
      where
        $nativeLocals:letRecDecl*)

/-- Theorem comma-binders are source-only sugar; Lean elaborates the same proof. -/
syntax (name := pscvTheorem)
  "theorem " ident "(" pscvBinder,* ")" ":" term ":=" term : command

macro_rules
  | `(theorem $name:ident ($[$bs:pscvBinder],*) : $statement:term := $proof:term) => do
    let binders ← explicitLeanBinders bs
    `(theorem $name:ident $binders* : $statement:term := $proof:term)

/-- Non-explicit PSCV binders share Lean's implicit, strict-implicit, and
instance elaborator, rather than emulating the semantics in a new compiler. -/
syntax (name := pscvImplicitFunction)
  "function " ident pscvNonExplicitBinder+ "(" pscvBinder,* ")" ":" term ":=" term : command

macro_rules
  | `(function $f:ident $implicitBs:pscvNonExplicitBinder* ($[$bs:pscvBinder],*) : $result:term := $body:term) => do
    let imps ← nonExplicitLeanBinders implicitBs
    let args ← explicitLeanBinders bs
    `(def $f:ident $imps* $args* : $result:term := $body:term)

/-- Contracted functions use the proof-producing intrinsic Lean 4.35
WP semantics: `f.spec` must be discharged by pinned `vcgen`. -/
syntax (name := pscvFunctionContract)
  "function " ident "(" pscvBinder,* ")" ":" term
  "requires" term "ensures" ident "=>" term ":=" term : command

macro_rules
  | `(function $f:ident ($[$bs:pscvBinder],*) : $result:term
      requires $pre:term ensures $rv:ident => $post:term := $body:term) => do
    let binders ← explicitLeanBinders bs
    `(def $f:ident $binders* : $result:term
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
    let binders ← explicitLeanBinders bs
    `(def $f:ident $binders* : $result:term
        given ($logical:ident : $logicTy:term)
        requires $pre:term
        ensures $rv:ident => $post:term := $body:term)

/-- Empty source calls use Lean's own optional-argument elaboration. A source
nullary function is a required Unit binder, not a second function type. -/
syntax:max (name := pscvEmptyCall) term:max noWs "(" ")" : term

@[term_elab pscvEmptyCall]
def elabPscvEmptyCall : TermElab := fun stx expectedType? => do
  let f : Term := ⟨stx[0]⟩
  let fn ← elabTerm f none
  let applied ← elabAppArgs fn #[] #[] expectedType? false false
  let restType ← whnf (← inferType applied)
  match restType with
  | .forallE binderName domain _ binderInfo =>
    unless binderInfo.isExplicit do
      throwError "PSCV0-CALL-EMPTY: unresolved implicit argument"
    let domain ← instantiateMVars domain
    if domain.hasMVar || !(← isDefEq domain (mkConst `Unit)) then
      throwError "PSCV0-CALL-EMPTY: unresolved required non-Unit argument"
    let unitValue ← elabTerm (← `(term| ())) (some domain)
    let completed := mkApp applied unitValue
    let remaining ← whnf (← inferType completed)
    if binderName != `_unit then
      match remaining with
      | .forallE nextName _ _ nextInfo =>
        if nextInfo.isExplicit && !nextName.isAnonymous then
          throwError "PSCV0-CALL-EMPTY: more than one required argument"
      | _ => pure ()
    return completed
  | _ =>
    return applied

/-- PSCV0 comma applications are curried Lean applications. Named arguments are
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
          Macro.throwError "PSCV0-CALL-NAMED: duplicate argument name"
        seenNamed := true
        used := used.push n.getId
        let named ← `(Lean.Parser.Term.namedArgument| ($n:ident := $v:term))
        parsedArgs := parsedArgs.push named.raw
      | `(pscvCallArg| $v:term) =>
        if seenNamed then
          Macro.throwError "PSCV0-CALL-ORDER: positional arguments cannot follow named arguments"
        parsedArgs := parsedArgs.push v.raw
      | _ => Macro.throwUnsupported
    -- A single Lean application node keeps defaults and named arguments in the
    -- same elaboration pass, rather than prematurely applying partial calls.
    return mkNode ``Lean.Parser.Term.app #[f.raw, mkNullNode parsedArgs]

/-- Use the native Lean structure-field parser inside PSCV0 braces. -/
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
    `(structure $name:ident $binders* where $fields:structFields)

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
    `(class $name:ident $binders* where $fields:structFields)

/-- Mutual recursion is only a braced grouping of the official Lean mutual
declaration elaborator and termination checker. -/
syntax (name := pscvBracedMutual)
  "mutual " "{" command+ "}" : command

macro_rules (kind := pscvBracedMutual)
  | `(mutual { $cmds:command* }) =>
    `(mutual
      $cmds:command*
    end)

/-- PSCV0 constructors preserve Lean's original positivity and recursor rules. -/
declare_syntax_cat pscvConstructor
syntax "| " ident ":" term : pscvConstructor
syntax "| " ident "(" pscvBinder,* ")" ":" term : pscvConstructor

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
        native := native.push (← `(ctor| | $ctor:ident $bs* : $ty:term))
      | _ => Macro.throwUnsupported
    `(inductive $s:ident where $native:ctor*)


/-- Deriving is restricted to the selected Lean RC4 handlers. -/
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
        native := native.push (← `(ctor| | $ctor:ident $bs* : $ty:term))
      | _ => Macro.throwUnsupported
    let names ← ds.mapM pscvDeriverIdent
    `(inductive $s:ident where
      $native:ctor*
      deriving $[$names:ident],*)

/-- PSCV0 matches use a braced alternative sequence while keeping Lean's
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
    let binders ← explicitLeanBinders bs
    `(def $f:ident $binders* : $result:term
        ensures $rv:ident => $post:term := $body:term)

syntax (name := pscvFunctionRequires)
  "function " ident "(" pscvBinder,* ")" ":" term
  "requires" term ":=" term : command

macro_rules
  | `(function $f:ident ($[$bs:pscvBinder],*) : $result:term
      requires $pre:term := $body:term) => do
    let binders ← explicitLeanBinders bs
    `(def $f:ident $binders* : $result:term
        requires $pre:term := $body:term)


end PSCVL
