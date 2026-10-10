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

/-- PSCV0 comma applications are curried Lean applications. Named arguments are
native Lean binder names and must follow all source positional arguments. -/
declare_syntax_cat pscvCallArg
syntax ident " := " term : pscvCallArg
syntax term : pscvCallArg
syntax:max (name := pscvCall) term:max noWs "(" pscvCallArg,* ")" : term

macro_rules (kind := pscvCall)
  | `($f:term($[$args:pscvCallArg],*)) => do
    if args.isEmpty then
      return (← `($f:term ()))
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

macro_rules (kind := pscvBracedMatch)
  | `(match $discrs:matchDiscr,* with { $alts:pscvMatchAlt* }) => do
    let mut native : Array (TSyntax ``Lean.Parser.Term.matchAlt) := #[]
    for alt in alts do
      match alt with
      | `(pscvMatchAlt| | $pats:term,* => $rhs:term) =>
        native := native.push (← `(matchAltExpr| | $pats:term,* => $rhs:term))
      | _ => Macro.throwUnsupported
    `(match $discrs:matchDiscr,* with $native:matchAlt*)

/-- PSCV pure conditional with explicit grouping and braces. It lowers to
Lean's ordinary typed `if`, and retains proof obligations. -/
syntax (name := pscvBracedIf)
  "if" "(" term ")" "{" term "}" "else" "{" term "}" : term

macro_rules
  | `(if ($condition:term) { $onTrue:term } else { $onFalse:term }) =>
    `(if $condition then $onTrue else $onFalse)

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
