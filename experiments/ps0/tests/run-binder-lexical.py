#!/usr/bin/env python3
"""Check that PS binder adapters preserve native braces and quotation grammar."""
from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('binder-lexical-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
fixture = work / 'NativeBraces.lean'
fixture.write_text('''import PS0.Policy
/-! Importing the adapters must preserve adjacent native record braces and strict binders. -/
structure Inner where
  n : Nat
structure Outer where
  inner : Inner
def adjacent : Outer := { inner := { n := 3 }}
example : adjacent.inner.n = 3 := by rfl
def nativeAscii {{α : Type}} (x : α) : α := x
def nativeUnicode ⦃α : Type⦄ (x : α) : α := x
example : nativeAscii 3 = nativeUnicode 3 := by rfl
meta def nativeQuote : Lean.MacroM (Lean.TSyntax `term) :=
  `(term| { inner := { n := 3 }})
meta def strictQuote : Lean.MacroM (Lean.TSyntax `term) :=
  `(term| fun {{α : Type}} (x : α) => x)
macro "assertLegacyStrict " b:pscvNonExplicitBinder : term => do
  unless b.raw.getArgs.size == 5 && b.raw[1].isIdent && b.raw[3].isOfKind ``Lean.Parser.Term.type do
    Lean.Macro.throwError "PS0_LEGACY_STRICT_BINDER_SHAPE"
  `(True)
example : assertLegacyStrict {{α : Type}} := by trivial
example : assertLegacyStrict ⦃α : Type⦄ := by trivial
macro "forceLegacyStrict " name:ident b:pscvNonExplicitBinder : command =>
  `(pscvImplicitFunction| function $name:ident $b:pscvNonExplicitBinder (x: Nat): Nat := x)
forceLegacyStrict legacyAscii {{α : Type}}
forceLegacyStrict legacyUnicode ⦃α : Type⦄
example : @legacyAscii Nat 3 = @legacyUnicode Nat 3 := by rfl
run_cmd do
  let record ← Lean.Elab.liftMacroM nativeQuote
  let strict ← Lean.Elab.liftMacroM strictQuote
  unless record.raw.isOfKind ``Lean.Parser.Term.structInst && strict.raw.isOfKind ``Lean.Parser.Term.fun do
    Lean.throwError "PS0_NATIVE_QUOTATION_GRAMMAR"
#eval IO.println "PS0_BINDER_NATIVE_LEXICAL:3"
''')
result = subprocess.run(['lake', 'env', 'lean', str(fixture)], text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
(work / 'native-braces.log').write_text(result.stdout)
print(result.stdout, end='', flush=True)
assert result.returncode == 0, result.returncode
assert 'PS0_BINDER_NATIVE_LEXICAL:3' in result.stdout
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'],
    'scope': 'native host nested records, ASCII/Unicode strict binders and native quotations after PS0.Policy import',
    'verified_execution': False,
}, indent=2) + '\n')
print('PS0_BINDER_LEXICAL_FIDELITY: PASS', flush=True)
