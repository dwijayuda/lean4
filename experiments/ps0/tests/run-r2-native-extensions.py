#!/usr/bin/env python3
"""Check native extensions, diagnostics, registration and native ABI execution."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

CASES = {
    'V1-063': ('''public import Lean
public meta import Lean
open Lean Meta
def simplifiableR2 : Nat := 42
dsimproc_decl simplifyR2 (simplifiableR2) := fun _ => return .done (mkNatLit 42)
example : simplifiableR2 = 42 := by
  conv => lhs; dsimp only [simplifyR2]
example (n : Nat) : n + 0 = n := by { simp }
''', None),
    'V1-072': ('''namespace R2Notation
scoped infixl:62 " ⊕₀ " => Nat.add
scoped infixr:65 " ⊗₀ " => Nat.mul
end R2Notation
section
open scoped R2Notation
local notation:max "firstOf[" x "," y "]" => Prod.fst (x, y)
example : 1 ⊕₀ 2 ⊗₀ 3 = 7 := rfl
example : firstOf[4, 5] = 4 := rfl
end
''', None),
    'V1-073': ('''public meta import Lean
declare_syntax_cat r2number
syntax "answer" : r2number
syntax r2numberAlias := r2number
syntax "readR2[" r2numberAlias "]" : term
macro_rules | `(readR2[answer]) => `(42)
example : readR2[answer] = (42 : Nat) := rfl
binder_predicate x " ≪₀ " y:term => `($x < $y)
example : (∀ x ≪₀ 0, x = (23 : Nat)) := by { intro x h; omega }
''', None),
    'V1-074': ('''public import Lean
public meta import Lean
open Lean Parser
meta def r2Operand : Parser := leading_parser Lean.Parser.Term.num
syntax (name := r2Prefix) "r2Prefix " r2Operand : term
syntax:70 (name := r2Tail) term:70 " r2Tail " num : term
macro_rules
  | `(r2Prefix $n:num) => pure n
  | `($lhs r2Tail $n:num) => `($lhs + $n)
example : (r2Prefix 20 r2Tail 22) = (42 : Nat) := rfl
''', None),
    'V1-075': ('''public meta import Lean
syntax "chooseR2 " term : term
macro_rules
  | `(chooseR2 true) => `(17)
  | `(chooseR2 $x) => `(if $x then 17 else 31)
macro "wrappedR2 " x:term : term => `(chooseR2 $x)
example : (wrappedR2 true) = (17 : Nat) := rfl
example : (wrappedR2 false) = (31 : Nat) := rfl
''', None),
    'V1-076': ('''public meta import Lean
macro "letR2 " x:term : term => `(let value := 9; $x + value)
macro "sizeR2[" xs:term,* "]" : term => `((#[$xs,*] : Array Nat).size)
function proof(value: Nat): Nat := letR2 value
example : proof(3) = 12 := rfl
example : sizeR2[3, 4, 5] = 3 := rfl
''', None),
    'V1-078': ('''public meta import Lean
open Lean Elab in
elab "sevenR2" : term => do
  Term.elabTerm (← `(7)) none
open Lean Elab Command in
elab "declareR2 " name:ident : command => do
  elabCommand (← `(def $name : Nat := 9))
open Lean Elab Tactic in
elab "finishR2" : tactic => do
  evalTactic (← `(tactic| exact True.intro))
syntax "elevenR2" : term
elab_rules : term
  | `(elevenR2) => do Lean.Elab.Term.elabTerm (← `(11)) none
declareR2 nineR2
example : sevenR2 + nineR2 + elevenR2 = 27 := rfl
example : True := by { finishR2 }
''', None),
    'V1-077': ('''public meta import Lean
macro "psOperandR2 " x:psTerm : term => do
  return ⟨← PS0.Syntax.lower `psTerm x.raw⟩
function add(x: Nat, y: Nat): Nat := x + y
example : (psOperandR2 add(20, 22)) = 42 := rfl
meta def nativeSyntax : Lean.MacroM(Lean.TSyntax `term) := `(term| add (20, 22))
open Lean in
run_cmd do
  let tree ← Elab.liftMacroM nativeSyntax
  let args := tree.raw[1].getArgs
  unless args.size == 1 && args[0]!.isOfKind ``Parser.Term.tuple do
    throwError "native syntax lost tuple ownership"
''', None),
    'V1-079': ('''public meta import Lean
open Lean in
run_cmd do
  let level := Level.succ Level.zero
  let expr := Expr.sort level
  unless expr == mkSort levelOne do throwError "universe construction"
  let syntaxTree ← Elab.liftMacroM `(term| (42 : Nat))
  unless syntaxTree.raw.getKind == ``Parser.Term.typeAscription do throwError "syntax kind"
  unless (Name.str `R2 "member").toString == "R2.member" do throwError "name construction"
''', None),
    'V1-081': ('''public meta import Lean
open Lean Elab Command Meta
abbrev R2Number := Nat
run_cmd liftTermElabM do
  let mvar ← mkFreshExprMVar (some (mkConst ``Nat))
  unless (← isDefEq mvar (mkNatLit 42)) do throwError "unification failed"
  let resolved ← instantiateMVars mvar
  unless resolved == mkNatLit 42 do throwError "unassigned metavariable"
  unless (← whnf (mkConst ``R2Number)).isConstOf ``Nat do
    throwError "weak head reduction failed"
''', None),
    'V1-082': ('''public meta import Lean
open Lean Elab Command Meta
run_cmd liftTermElabM do
  let input := mkApp (mkConst ``Nat.succ) (mkNatLit 41)
  let_expr Nat.succ pred := input | throwError "reflective let mismatch"
  unless pred == mkNatLit 41 do throwError "unexpected argument"
  match_expr input with
  | Nat.succ n => unless n == mkNatLit 41 do throwError "reflective match mismatch"
  | _ => throwError "reflective match failed"
#eval Nat.succ 41
''', None),
    'V1-083': ('''public import Lean
example : binop% HAdd.hAdd 20 22 = (42 : Nat) := rfl
theorem declaredR2 : decl_name% = `declaredR2 := rfl
#check_failure thereIsNoR2Declaration
''', None),
    'V1-085': ('''abbrev AliasR2 := Nat
def OrdinaryR2 := Nat
opaque OpaqueR2 : Type := Nat
open Lean Elab Command Meta in
run_cmd liftTermElabM do
  unless (← withReducible (isDefEq (mkConst ``AliasR2) (mkConst ``Nat))) do
    throwError "abbreviation is not reducible"
  if (← withReducible (isDefEq (mkConst ``OrdinaryR2) (mkConst ``Nat))) then
    throwError "ordinary definition unfolded under reducible transparency"
  unless (← isDefEq (mkConst ``OrdinaryR2) (mkConst ``Nat)) do
    throwError "ordinary definition did not unfold"
  if (← isDefEq (mkConst ``OpaqueR2) (mkConst ``Nat)) then
    throwError "opaque definition unfolded"
''', None),
    'V1-088': ('''const digits: Array UInt8 := #[1, 2, 3]
const nested: List(Option Nat) := [some(9), none]
example : digits[1] = (2 : UInt8) := rfl
example : digits[9]? = none := rfl
example : nested.head? = some(some(9)) := rfl
example : ('a').toNat = 97 := rfl
''', None),
    'V1-089': ('''def stateStep : StateM Nat Nat := do
  let before ← get
  modify Nat.succ
  return before
example : stateStep.run(10) = (10, 11) := rfl
def readStep : ReaderT(Nat, Except(String), Nat) := do
  let n ← read
  if n == 0 then throw "empty" else return n + 1
example : readStep.run(2) = .ok(3) := rfl
example : readStep.run(0) = .error("empty") := rfl
#eval show IO Unit from do
  let path ← IO.currentDir
  if path.toString.isEmpty then throw (IO.userError "missing cwd")
''', None),
    'V1-090': ('''public import Lean
def synchronized : IO Nat := do
  let ref ← IO.mkRef 20
  let task ← IO.asTask do
    ref.modify fun n => n + 22
    ref.get
  let result ← IO.ofExcept task.get
  let current ← ref.get
  if result != current then throw(IO.userError("task synchronization"))
  return current
def mutateR2 : StateRefT Nat IO Nat := do
  modify Nat.succ
  get
#eval show IO Unit from do
  let observed ← synchronized
  let (state, final) ← mutateR2.run 41
  unless observed == 42 && state == 42 && final == 42 do
    throw (IO.userError "reference or task oracle")
''', None),
    'V1-094': ('''def diagnosticR2 : Nat := 19
#check diagnosticR2
#eval diagnosticR2
#reduce diagnosticR2
#print diagnosticR2
#check_failure diagnosticR2.noSuchProjection
''', None),
    'V1-095': ('''public meta import Lean
assert_not_exists NoR2Decl
assert_not_imported Mathlib
def answerR2 : Nat := 42
recall answerR2 : Nat := 42
#check_assertions
open Lean in
run_cmd do
  unless Lean.versionString.startsWith "4.35.0" do throwError "unexpected pinned Lean version"
''', None),
    'V1-096': ('''public meta import Lean
/-- A Markdown docstring. -/
def markdownR2 : Nat := 1
set_option doc.verso true in
/-- A *Verso* docstring. -/
def versoR2 : Nat := 2
recommended_spelling "markdownR2" for "R2" in [markdownR2]
/-- An R2 diagnostic explanation. -/
register_error_explanation lean.r2Fixture {
  summary := "R2 diagnostic fixture."
  sinceVersion := "4.35.0"
}
open Lean in
run_cmd do
  let env ← getEnv
  let some (.inl _) ← findInternalDocString? env ``markdownR2 | throwError "Markdown missing"
  let some (.inr _) ← findInternalDocString? env ``versoR2 | throwError "Verso missing"
  let some _ ← getErrorExplanation? `lean.r2Fixture | throwError "explanation missing"
''', None),
    'V1-098': ('''public meta import Lean
public meta import Lean.Server
open Lean Elab Command Meta
run_cmd liftTermElabM do
  let pretty ← PrettyPrinter.ppExpr (mkNatLit 42)
  unless pretty.pretty == "42" do throwError "pretty printer changed"
#check Lean.Server.FileWorker.workerMain
#check Lean.Compiler.LCNF.Decl
''', None),
    'V1-097': ('''public import Lean
public meta import Lean
open Lean Parser
meta def r2BootOperand : Parser := leading_parser Lean.Parser.Term.num
syntax "r2Boot " r2BootOperand : term
macro_rules | `(r2Boot $n:num) => pure n
set_option doc.verso true in
/-- A *scoped* bootstrap documentation fixture. -/
def scopedR2 : Nat := r2Boot 42
example : scopedR2 = 42 := rfl
open Lean in
run_cmd do
  let some (.inr _) ← findInternalDocString? (← getEnv) ``scopedR2 |
    throwError "missing scoped Verso registration"
''', None),
    'V1-097-duplicate-quotient': ('''public import Init
init_quot
''', r'quotient initialization is already present'),
    'V1-099': ('''public import Lake
public meta import Lake
open Lake DSL
package optionalR2 where
  version := v!"0.4.0"
lean_lib OptionalR2 where
  roots := #[`OptionalR2]
example : _package.origName = `optionalR2 := rfl
example : _package.config.version = v!"0.4.0" := rfl
example : OptionalR2.config.roots = #[`OptionalR2] := rfl
''', None),
    'V1-099-no-import': ('''package noLakeR2
''', r'unexpected identifier|expected command|unknown identifier'),
    'V1-092': ('''unsafe def runtimeUnsafe : IO Nat := do
  let value ← IO.mkRef 40
  value.modify fun n => n + 2
  value.get
#eval! show IO Unit from do
  let result ← runtimeUnsafe
  unless result == 42 do throw (IO.userError "unsafe runtime result")
open Lean in
run_cmd do
  unless ((← getEnv).find? ``runtimeUnsafe).any ConstantInfo.isUnsafe do
    throwError "missing unsafe tag"
''', None),
    'V1-093': ('''def debugValue : Nat :=
  dbg_trace "PS0_RUNTIME_DEBUG"
  42
def guarded (flag : Bool) : Nat :=
  if flag then debugValue else unreachable!
def fatal : Nat := panic! "R2 deliberate panic branch"
#eval guarded true
#check fatal
''', None),
    'PS0-P-EXT-03': ('''public import Lean
public meta import Lean
open Lean Elab Command
class ReportCode (α : Type) where
  code : Nat
meta def deriveReportCode : DerivingHandler := fun names => do
  for name in names do
    elabCommand (← `(instance : ReportCode $(mkIdent name) := ⟨42⟩))
  return true
builtin_initialize registerDerivingHandler ``ReportCode deriveReportCode
builtin_initialize r2Marked : TagAttribute ← registerTagAttribute `r2_marked "R2 tag"
inductive Derived where
  | marker
  deriving ReportCode
@[r2_marked] def marker : Nat := 0
declare_syntax_cat r2literal
syntax "fortyTwo" : r2literal
syntax "readR2 " r2literal : term
macro_rules | `(readR2 fortyTwo) => `(42)
def simplifiable : Nat := 42
dsimproc_decl simplifyR2 (simplifiable) := fun _ => return .done (mkNatLit 42)
private example : simplifiable = 42 := by dsimp only [simplifyR2]
private example : readR2 fortyTwo = (42 : Nat) := rfl
private example : ReportCode.code (α := Derived) = 42 := rfl
run_cmd do
  unless r2Marked.hasTag (← getEnv) ``marker do throwError "custom attribute missing"
''', None),
    'PS0-P-EXT-01': ('''public meta import Lean
syntax "identityTerm " term : term
macro_rules | `(identityTerm $x) => pure x
macro "forty " : term => `(40)
elab "checkedForty" : term => do
  Lean.Elab.Term.elabTerm (← `(40)) none
syntax "checkedTwo" : term
elab_rules : term
  | `(checkedTwo) => do Lean.Elab.Term.elabTerm (← `(2)) none
private example : (identityTerm forty) + checkedTwo = 42 := rfl
private example : checkedForty = 40 := rfl
''', None),
    'PS0-P-EXT-02': ('''public meta import Lean
meta def pairQuote : Lean.MacroM(Lean.TSyntax `term) := `(term| f (x, y))
open Lean in
run_cmd do
  let syntaxTree ← Elab.liftMacroM pairQuote
  unless syntaxTree.raw.isOfKind ``Parser.Term.app &&
      syntaxTree.raw[1].getArgs.size == 1 && syntaxTree.raw[1][0].isOfKind ``Parser.Term.tuple do
    throwError "tuple partition changed"
''', None),
    'PS0-N-EXT-01': ('''public meta import Lean
meta def nativeQuote : Lean.MacroM(Lean.TSyntax `term) := `(term| f (x, y))
open Lean in
run_cmd do
  let tree ← Elab.liftMacroM nativeQuote
  let args := tree.raw[1].getArgs
  unless args.size == 1 && args[0]!.isOfKind ``Parser.Term.tuple do
    throwError "native tuple application was rewritten as a PS comma call"
''', None),
    'PS0-N-EXT-02': ('''public meta import Lean
macro "hostOperand " x:psTerm : psTerm => pure x
function sumPair(p: Nat × Nat): Nat := p.1 + p.2
const bad: Nat := hostOperand sumPair (1, 2)
''', r':4:\d+: error: PS0V1-CALL-GAP'),
    'PS0-P-ENV-01': ('''public import Lake
public meta import Lake
open Lake DSL
package r2example where
  version := v!"0.2.0"
lean_lib R2Library where
  roots := #[`R2Library]
example : _package.origName = `r2example := rfl
example : _package.config.version = v!"0.2.0" := rfl
example : R2Library.config.roots = #[`R2Library] := rfl
''', None),
    'PS0-N-ASSURE-03': ('''partial function loop(n: Nat): Nat := loop(n)
open Lean in
run_cmd do
  let env ← getEnv
  let some (.opaqueInfo _) := env.find? ``loop | throwError "missing opaque interface"
  unless (env.find? (Compiler.mkUnsafeRecName ``loop)).any ConstantInfo.isPartial do
    throwError "expected compiled partial implementation"
''', None),
    'PS0-N-ASSURE-04': ('''public import Std.WP
def effect (counter : IO.Ref Nat) : IO Nat := do
  counter.modify Nat.succ
  return 37
def observe : IO Nat := do
  let counter ← IO.mkRef 0
  erased _witness ← effect counter
  counter.get
#eval show IO Unit from do
  let n ← observe
  if n == 1 then IO.println "PS0_EFFECT_RETAINED" else throw (IO.userError "erased effect missing")
''', None),
    'PS0-P-META-02': ('''public import Lean
private example : binop% HAdd.hAdd 20 22 = (42 : Nat) := rfl
''', None),
    'PS0-P-RUN-02': ('''unsafe def raw : Nat := 42
open Lean in
run_cmd do
  unless ((← getEnv).find? ``raw).any ConstantInfo.isUnsafe do throwError "missing unsafe classification"
''', None),
    'PS0-P-DIAG-01': ('''theorem proven : True := True.intro
#check proven
#print axioms proven
#eval IO.println "PS0_DIAGNOSTIC_EVAL"
#guard 4 + 5 == 9
''', None),
    'PS0-P-DOC-01': ('''public meta import Lean
/-- A Markdown docstring. -/
def markdownDocumented : Nat := 1
set_option doc.verso true in
/-- A *Verso* docstring. -/
def versoDocumented : Nat := 2
open Lean in
run_cmd do
  let env ← getEnv
  let some (.inl _) ← findInternalDocString? env ``markdownDocumented | throwError "Markdown missing"
  let some (.inr _) ← findInternalDocString? env ``versoDocumented | throwError "Verso missing"
''', None),
    'PS0-P-RUN-01': ('''function say(): IO Unit := do
  IO.println("PS0_R2_IO:hello")
#eval say ()
''', None),
    'PS0-N-EXT-03': ('''@[unregistered_r2_attribute] def value : Nat := 1
''', r'Unknown attribute.*unregistered_r2_attribute'),
}

NATIVE_ABI = '''module
prelude
public import Init
public section
@[extern "lean_uint32_of_nat"] opaque borrowed (n : @& Nat) : UInt32
def replacement (n : UInt32) : UInt32 := n + 2
@[implemented_by replacement] def model (n : UInt32) : UInt32 := n + 1
def main : IO Unit := do
  IO.println(s!"PS0_R2_ABI:{model(borrowed(40))}")
'''
INITIALIZERS = '''module
prelude
public import Init
public section
initialize ordinaryRef : IO.Ref Nat ← IO.mkRef 17
builtin_initialize earlyRef : IO.Ref Nat ← IO.mkRef 23
def main : IO Unit := do
  let first ← ordinaryRef.get
  let second ← earlyRef.get
  unless first == 17 && second == 23 do throw(IO.userError("initializer result"))
  IO.println "PS0_R2_INITIALIZERS:17:23"
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('driver', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True)
    passed, failures, fixtures = [], [], {}

    def run(label, command):
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=240)
        (out / (label + '.log')).write_text(result.stdout, encoding='utf-8')
        print(label, result.returncode, result.stdout, flush=True)
        return result.returncode, result.stdout

    for case, (source, diagnostic) in CASES.items():
        path = out / (case + '.ps')
        path.write_text(source, encoding='utf-8')
        fixtures[case] = hashlib.sha256(path.read_bytes()).hexdigest()
        code, log = run(case, [args.driver, 'check', path])
        ok = code == 1 and re.search(diagnostic, log, re.I) if diagnostic else code == 0
        if case == 'PS0-P-DIAG-01':
            ok = ok and 'does not depend on any axioms' in log and 'PS0_DIAGNOSTIC_EVAL' in log
        if case == 'PS0-P-RUN-01':
            ok = ok and 'PS0_R2_IO:hello' in log
        if case == 'V1-093':
            ok = ok and 'PS0_RUNTIME_DEBUG' in log and re.search(r'^42$', log, re.M)
        if case == 'PS0-N-ASSURE-03':
            ok = ok and 'UNCERTIFIED' in log and 'no verified certificate issued' in log
        if case == 'PS0-N-ASSURE-04':
            ok = ok and 'PS0_EFFECT_RETAINED' in log
        (passed if ok else failures).append(case)

    if 'V1-099' in passed and 'V1-099-no-import' not in passed:
        passed.remove('V1-099')
        failures.append('V1-099')
    if 'V1-097' in passed and 'V1-097-duplicate-quotient' not in passed:
        passed.remove('V1-097')
        failures.append('V1-097')
    src = out / 'src'
    src.mkdir()
    deriving_support = src / 'R2Deriving.ps'
    deriving_support.write_text('''module
prelude
public import Lean
public meta import Lean
public section
open Lean Elab Command
class R2Report (α : Type) where
  code : Nat
private meta def deriveR2Report : DerivingHandler := fun names => do
  for name in names do
    elabCommand (← `(instance : R2Report $(mkIdent name) := ⟨42⟩))
  return true
initialize registerDerivingHandler ``R2Report deriveR2Report
''', encoding='utf-8')
    deriving_user = src / 'R2DerivingUser.ps'
    deriving_user.write_text('''module
prelude
public import Lean
public meta import Lean
public import R2Deriving
public meta import R2Deriving
public section
inductive R2Derived where
  | marker
  deriving R2Report
example : R2Report.code (α := R2Derived) = 42 := rfl
''', encoding='utf-8')
    fixtures['R2Deriving'] = hashlib.sha256(deriving_support.read_bytes()).hexdigest()
    fixtures['V1-030'] = hashlib.sha256(deriving_user.read_bytes()).hexdigest()
    derive_code, _ = run('V1-030', ['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceGrammar=true',
                                  f'-KsourceRoot={src}', '-Kroots=R2DerivingUser',
                                  '-KmoduleNames=R2Deriving,R2DerivingUser', f'-Kdriver={args.driver.resolve()}',
                                  f'-KprojectBuildDir={out / "deriving"}', 'build', 'R2DerivingUser'])
    (passed if derive_code == 0 else failures).append('V1-030')
    registration = src / 'R2Registration.ps'
    registration.write_text('''module
prelude
public import Lean
public meta import Lean
public section
open Lean
initialize stateR2 : SimplePersistentEnvExtension(Name, List Name) ←
  registerSimplePersistentEnvExtension {
    addEntryFn := fun entries name => name :: entries
    addImportedFn := fun _ => []
  }
initialize tagR2 : TagAttribute ← registerTagAttribute `r2_tag "R2 tag attribute"
initialize registerTraceClass `R2.options
''', encoding='utf-8')
    for case, source, expected in [
        ('V1-080', '''open Lean Elab Command
def valueR2 : Nat := 42
run_cmd do
  modifyEnv fun env => stateR2.addEntry env ``valueR2
  unless (stateR2.getState (← getEnv)).contains ``valueR2 do
    throwError "missing registered declaration"
''', ''),
        ('V1-084', '''open Lean Elab Command
@[r2_tag] def markedR2 : Nat := 17
run_cmd do
  unless tagR2.hasTag (← getEnv) ``markedR2 do throwError "tag missing"
@[simp] theorem addedR2 : 0 + (0 : Nat) = 0 := rfl
attribute [-simp] addedR2
''', ''),
        ('V1-086', '''open Lean Elab Command
set_option pp.universes true in
run_cmd do
  unless pp.universes.get (← getOptions) do throwError "scoped option missing"
set_option trace.R2.options true in
run_cmd do trace[R2.options] "PS0_R2_TRACE"
run_cmd do
  if pp.universes.get (← getOptions) then throwError "scoped option leaked"
''', 'PS0_R2_TRACE'),
    ]:
        module = case.replace('-', '_')
        path = src / (module + '.ps')
        path.write_text('module\nprelude\npublic import Lean\npublic meta import Lean\n'
                        'public import R2Registration\npublic meta import R2Registration\n'
                        'public section\n' + source, encoding='utf-8')
        fixtures[case] = hashlib.sha256(path.read_bytes()).hexdigest()
        fixtures['R2Registration'] = hashlib.sha256(registration.read_bytes()).hexdigest()
        code, log = run(case, ['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceGrammar=true',
                              f'-KsourceRoot={src}', f'-Kroots={module}', f'-KmoduleNames={module},R2Registration',
                              f'-Kdriver={args.driver.resolve()}', f'-KprojectBuildDir={out / "registrations"}',
                              'build', module])
        (passed if code == 0 and expected in log else failures).append(case)
    for case, module, source, expected in [
        ('PS0-P-RUN-03', 'NativeABI', NATIVE_ABI, 'PS0_R2_ABI:42'),
        ('PS0-P-META-01', 'NativeInitializers', INITIALIZERS, 'PS0_R2_INITIALIZERS:17:23'),
        ('V1-087', 'NativeR2Initializers', INITIALIZERS, 'PS0_R2_INITIALIZERS:17:23'),
        ('V1-091', 'NativeR2ABI', NATIVE_ABI.replace(
            'def replacement', '@[export ps0_r2_exported_replacement] def replacement'),
            'PS0_R2_ABI:42'),
    ]:
        path = src / (module + '.ps')
        path.write_text(source, encoding='utf-8')
        fixtures[case] = hashlib.sha256(path.read_bytes()).hexdigest()
        build = out / module
        code, _ = run(case, ['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceGrammar=true',
                            f'-KsourceRoot={src}', f'-Kroots={module}', f'-KrootModule={module}',
                            f'-KmoduleNames={module}', f'-Kdriver={args.driver.resolve()}',
                            f'-KprojectBuildDir={build}', 'build', 'ps0project'])
        ok = code == 0
        if ok:
            code, log = run(case + '-runtime', [build / 'bin/ps0project'])
            ok = code == 0 and log.strip() == expected
        if case == 'V1-091' and ok:
            code, log = run(case + '-symbol', ['nm', '-g', build / 'bin/ps0project'])
            ok = code == 0 and re.search(r'\bT ps0_r2_exported_replacement$', log, re.M) is not None
        (passed if ok else failures).append(case)
        if case == 'PS0-P-RUN-03':
            control = out / 'PS0-N-ASSURE-05.ps'
            control.write_text('public import Init\n' +
                'def replacement (n : UInt32) : UInt32 := n + 2\n' +
                '@[implemented_by replacement] def model (n : UInt32) : UInt32 := n + 1\n' +
                'private example : model(40) = 41 := rfl\n', encoding='utf-8')
            fixtures['PS0-N-ASSURE-05'] = hashlib.sha256(control.read_bytes()).hexdigest()
            logical, log = run('PS0-N-ASSURE-05', [args.driver, 'check', control])
            (passed if ok and logical == 0 and 'UNCERTIFIED' in log else failures).append('PS0-N-ASSURE-05')
    native = out / 'PS0-N-ASSURE-06.lean'
    proofscript = out / 'PS0-N-ASSURE-06.ps'
    source = 'def nativeOnly (x : Nat) : Nat := x\ndef checked : Nat := nativeOnly (42)\n'
    for path in (native, proofscript):
        path.write_text(source, encoding='utf-8')
    fixtures['PS0-N-ASSURE-06'] = hashlib.sha256(proofscript.read_bytes()).hexdigest()
    native_code, native_log = run('native-pass-through', [args.driver, 'check', native])
    ps_code, ps_log = run('PS0-N-ASSURE-06', [args.driver, 'check', proofscript])
    (passed if native_code == 0 and 'PS0V1:' not in native_log and ps_code == 1 and
        'PS0V1-CALL-GAP' in ps_log else failures).append('PS0-N-ASSURE-06')
    evidence = {'passed': passed, 'failures': failures, 'fixtures': fixtures,
                'driver_sha256': hashlib.sha256(args.driver.read_bytes()).hexdigest()}
    (out / 'result.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('PS0_R2_NATIVE_EXTENSIONS', json.dumps(evidence), flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
