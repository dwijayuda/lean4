#!/usr/bin/env python3
"""Test-first rejection probes for ordinary host bodies beneath borrowed native syntax."""
from pathlib import Path
import argparse
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
parser = argparse.ArgumentParser()
parser.add_argument('--cases', default='match,pattern-lambda,record-field,do-if')
selected = set(parser.parse_args().cases.split(','))
work = ROOT / 'build' / ('host-island-gaps-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
native_prefix = ('module\nprelude\npublic import Init\npublic section\n'
                 'def pairSum (p : Nat × Nat) : Nat := p.1 + p.2\n'
                 'structure IslandCell where\n  value : Nat\n')
ps_prefix = ('module\nprelude\npublic import Init\npublic section\n'
             'function pairSum(p: Nat × Nat): Nat := p.1 + p.2\n'
             'structure IslandCell where\n  value : Nat\n')
cases = [
    ('structure-field-type', 'structure FieldType where\n  value : Fin (pairSum (1, 2))',
     'structure FieldType where\n  value : Fin (pairSum (1, 2))'),
    ('structure-field-default', 'structure FieldDefault where\n  value : Nat := pairSum (1, 2)',
     'structure FieldDefault where\n  value : Nat := pairSum (1, 2)'),
    ('class-field-default', 'class FieldClass where\n  value : Nat := pairSum (1, 2)',
     'class FieldClass where\n  value : Nat := pairSum (1, 2)'),
    ('inductive-constructor-type', 'inductive ConstructorType where\n  | mk (value : Fin (pairSum (1, 2))) : ConstructorType',
     'inductive ConstructorType where\n  | mk (value : Fin (pairSum (1, 2))) : ConstructorType'),
    ('inductive-parameter-type', 'inductive ParameterType (value : Fin (pairSum (1, 2))) where\n  | mk',
     'inductive ParameterType (value : Fin (pairSum (1, 2))) where\n  | mk'),
    ('structure-parameter-type', 'structure ParameterStructure (value : Fin (pairSum (1, 2))) where\n  dummy : Nat',
     'structure ParameterStructure (value : Fin (pairSum (1, 2))) where\n  dummy : Nat'),
    ('initialize-value', 'initialize initialValue : Nat ← pure (pairSum (1, 2))',
     'initialize initialValue : Nat ← pure <| pairSum (1, 2)'),
    ('builtin-initialize-value', 'builtin_initialize initialValue : Nat ← pure (pairSum (1, 2))',
     'builtin_initialize initialValue : Nat ← pure <| pairSum (1, 2)'),
    ('nested-action', 'def pairSumM (p : Nat × Nat) : Id Nat := pure (pairSum p)\ndef bad (n : Nat) : Id Nat := do\n  let result := (← pairSumM (n, 1))\n  return result',
     'function pairSumM(p: Nat × Nat): Id(Nat) := pure(pairSum(p))\nfunction bad(n: Nat): Id(Nat) := do\n  let result := (← pairSumM (n, 1))\n  return result'),
    ('term-return', 'def bad (n : Nat) : Id Nat := return pairSum (n, 1)',
     'function bad(n: Nat): Id(Nat) := return pairSum (n, 1)'),
    ('term-try', 'def bad (n : Nat) : IO Nat := try\n  return pairSum (n, 1)\ncatch _ =>\n  return n',
     'function bad(n: Nat): IO(Nat) := try\n  return pairSum (n, 1)\ncatch _ =>\n  return n'),
    ('term-for', 'def bad (n : Nat) : IO Unit := for _ in [0:1] do\n  IO.println (pairSum (n, 1))',
     'function bad(n: Nat): IO(Unit) := for _ in [0:1] do\n  IO.println (pairSum (n, 1))'),
    ('bound-if-then', 'def bad (n : Nat) : Id Nat := do\n  let result ← if n == 0 then\n    pure <| pairSum (n, 1)\n  else\n    pure n\n  return result',
     'function bad(n: Nat): Id(Nat) := do\n  let result ← if n == 0 then\n    pure <| pairSum (n, 1)\n  else\n    pure n\n  return result'),
    ('bound-if-else', 'def bad (n : Nat) : Id Nat := do\n  let result ← if n == 0 then\n    pure n\n  else\n    pure <| pairSum (n, 1)\n  return result',
     'function bad(n: Nat): Id(Nat) := do\n  let result ← if n == 0 then\n    pure n\n  else\n    pure <| pairSum (n, 1)\n  return result'),
    ('suffices-body', 'def bad (n : Nat) : Nat := suffices h : Nat from pairSum (h, 1); n',
     'function bad(n: Nat): Nat := suffices h : Nat from pairSum (h, 1); n'),
    ('suffices-type', 'def bad (n : Nat) : Nat := suffices h : (fun (_ : Nat) => Nat) (pairSum (n, 1)) from h; n',
     'function bad(n: Nat): Nat := suffices h : (fun (_ : Nat) => Nat) (pairSum (n, 1)) from h; n'),
    ('suffices-continuation', 'def bad (n : Nat) : Nat := suffices h : Nat from h; pairSum (n, 1)',
     'function bad(n: Nat): Nat := suffices h : Nat from h; pairSum (n, 1)'),
    ('match', 'def bad (n : Nat) : Nat := match n with | 0 => pairSum (1, 2) | k => k',
     'function bad(n: Nat): Nat := match n with | 0 => pairSum (1, 2) | k => k'),
    ('pattern-lambda', 'def bad (n : Nat) : Nat := (fun | 0 => pairSum (1, 2) | k => k) n',
     'function bad(n: Nat): Nat := (fun | 0 => pairSum (1, 2) | k => k)(n)'),
    ('record-field', 'def bad (n : Nat) : IslandCell := { value := pairSum (n, 1) }',
     'function bad(n: Nat): IslandCell := { value := pairSum (n, 1) }'),
    ('do-if', 'def bad (n : Nat) : Id Nat := do\n  if n == 0 then return pairSum (n, 1)\n  return n',
     'function bad(n: Nat): Id(Nat) := do\n  if n == 0 then return pairSum (n, 1)\n  return n'),
    ('do-match', 'def bad (n : Nat) : Id Nat := do\n  match n with\n  | 0 => return pairSum (n, 1)\n  | k => return k',
     'function bad(n: Nat): Id(Nat) := do\n  match n with\n  | 0 => return pairSum (n, 1)\n  | k => return k'),
    ('do-for', 'def bad (n : Nat) : Id Nat := do\n  let mut result := n\n  for k in [0:1] do\n    result := pairSum (k, 1)\n  return result',
     'function bad(n: Nat): Id(Nat) := do\n  let mut result := n\n  for k in [0:1] do\n    result := pairSum (k, 1)\n  return result'),
    ('do-have', 'def bad (n : Nat) : Id Nat := do\n  have k : Nat := pairSum (n, 1)\n  return k',
     'function bad(n: Nat): Id(Nat) := do\n  have k : Nat := pairSum (n, 1)\n  return k'),
    ('proof-if', 'def bad (n : Nat) : Nat := if h : n = 0 then pairSum (n, 1) else n',
     'function bad(n: Nat): Nat := if h : n = 0 then pairSum (n, 1) else n'),
    ('typed-term', 'def bad (n : Nat) : Nat := (pairSum (n, 1) : Nat)',
     'function bad(n: Nat): Nat := (pairSum (n, 1) : Nat)'),
    ('tactic-body', 'def bad (n : Nat) : Nat := by exact pairSum (n, 1)',
     'function bad(n: Nat): Nat := by exact pairSum (n, 1)'),
    ('do-try', 'def bad (n : Nat) : IO Nat := do\n  try return pairSum (n, 1)\n  catch _ => return n',
     'function bad(n: Nat): IO(Nat) := do\n  try return pairSum (n, 1)\n  catch _ => return n'),
    ('pattern-if', 'def bad (n : Nat) : Nat := if let some (Nat.succ k) := some n then pairSum (k, 1) else 0',
     'function bad(n: Nat): Nat := if let some (Nat.succ k) := some n then pairSum (k, 1) else 0'),
    ('tuple-element', 'def bad (n : Nat) : Nat × Nat := (pairSum (n, 1), n)',
     'function bad(n: Nat): Nat × Nat := (pairSum (n, 1), n)'),
    ('list-element', 'def bad (n : Nat) : List Nat := [pairSum (n, 1)]',
     'function bad(n: Nat): List(Nat) := [pairSum (n, 1)]'),
    ('array-element', 'def bad (n : Nat) : Array Nat := #[pairSum (n, 1)]',
     'function bad(n: Nat): Array(Nat) := #[pairSum (n, 1)]'),
    ('interpolation', 'def bad (n : Nat) : String := s!"value:{pairSum (n, 1)}"',
     'function bad(n: Nat): String := s!"value:{pairSum (n, 1)}"'),
    ('forall-domain', 'def bad (n : Nat) : Type := ∀ (_ : Fin (pairSum (n, 1))), Nat',
     'function bad(n: Nat): Type := ∀ (_ : Fin (pairSum (n, 1))), Nat'),
    ('forall-body', 'def bad (n : Nat) : Type := ∀ (_ : Nat), Fin (pairSum (n, 1))',
     'function bad(n: Nat): Type := ∀ (_ : Nat), Fin (pairSum (n, 1))'),
    ('pattern-let', 'def bad (n : Nat) : Nat := let (a, b) := (n, 1); pairSum (a, b)',
     'function bad(n: Nat): Nat := let (a, b) := (n, 1); pairSum (a, b)'),
    ('anonymous-constructor', 'def bad (n : Nat) : Nat × Nat := ⟨pairSum (n, 1), n⟩',
     'function bad(n: Nat): Nat × Nat := ⟨pairSum (n, 1), n⟩'),
    ('show-body', 'def bad (n : Nat) : Nat := show Nat from pairSum (n, 1)',
     'function bad(n: Nat): Nat := show Nat from pairSum (n, 1)'),
    ('show-type', 'def bad (n : Nat) : Nat := show (fun (_ : Nat) => Nat) (pairSum (n, 1)) from 0',
     'function bad(n: Nat): Nat := show (fun (_ : Nat) => Nat) (pairSum (n, 1)) from 0'),
    ('pure-have', 'def bad (n : Nat) : Nat := have k : Nat := pairSum (n, 1); k',
     'function bad(n: Nat): Nat := have k : Nat := pairSum (n, 1); k'),
    ('while-body', 'def bad (n : Nat) : IO Nat := do\n  while false do\n    return pairSum (n, 1)\n  return n',
     'function bad(n: Nat): IO(Nat) := do\n  while false do\n    return pairSum (n, 1)\n  return n'),
    ('while-condition', 'def bad (n : Nat) : IO Nat := do\n  while pairSum (n, 1) == 0 do\n    break\n  return n',
     'function bad(n: Nat): IO(Nat) := do\n  while pairSum (n, 1) == 0 do\n    break\n  return n'),
    ('repeat-body', 'def bad (n : Nat) : IO Nat := do\n  let mut result := n\n  repeat\n    result := pairSum (result, 1)\n  until true\n  return result',
     'function bad(n: Nat): IO(Nat) := do\n  let mut result := n\n  repeat\n    result := pairSum (result, 1)\n  until true\n  return result'),
    ('repeat-condition', 'def bad (n : Nat) : IO Nat := do\n  repeat\n    pure Unit.unit\n  until pairSum (n, 1) == 0\n  return n',
     'function bad(n: Nat): IO(Nat) := do\n  repeat\n    pure Unit.unit\n  until pairSum (n, 1) == 0\n  return n'),
    ('loop-for-invariant', 'def bad (n : Nat) : Id Nat := do\n  let mut result := n\n  for k in [n]\n  invariant pref suff => pairSum (n, 1) = n + 1\n  do result := k\n  return result',
     'function bad(n: Nat): Id(Nat) := do\n  let mut result := n\n  for k in [n]\n  invariant pref suff => pairSum (n, 1) = n + 1\n  do result := k\n  return result'),
    ('loop-invariant-type', 'def bad (n : Nat) : Id Nat := do\n  let mut result := n\n  for k in [n]\n  invariant (pref : (fun (_ : Nat) => List Nat) (pairSum (n, 1))) suff => True\n  do result := k\n  return result',
     'function bad(n: Nat): Id(Nat) := do\n  let mut result := n\n  for k in [n]\n  invariant (pref : (fun (_ : Nat) => List Nat) (pairSum (n, 1))) suff => True\n  do result := k\n  return result'),
    ('loop-while-invariant', 'def bad (n : Nat) : Id Nat := do\n  let mut result := n\n  while false\n  invariant exit => pairSum (n, 1) = n + 1\n  do result := n\n  return result',
     'function bad(n: Nat): Id(Nat) := do\n  let mut result := n\n  while false\n  invariant exit => pairSum (n, 1) = n + 1\n  do result := n\n  return result'),
    ('loop-while-measure', 'def bad (n : Nat) : Id Nat := do\n  let mut result := n\n  while false\n  decreasing pairSum (n, 1)\n  do result := n\n  return result',
     'function bad(n: Nat): Id(Nat) := do\n  let mut result := n\n  while false\n  decreasing pairSum (n, 1)\n  do result := n\n  return result'),
]
observations = []
assert selected and selected <= {name for name, _, _ in cases}, selected
for name, native, ps in cases:
    if name not in selected:
        continue
    baseline = work / (name + '-native.ps')
    native_header = native_prefix.replace('public import Init', 'public import Std.WP') if name.startswith('loop-') else native_prefix
    ps_header = ps_prefix.replace('public import Init', 'public import Std.WP') if name.startswith('loop-') else ps_prefix
    baseline.write_text(native_header + native + '\n')
    native_result = subprocess.run([str(ROOT / '.lake/build/bin/ps0'), 'census-source', str(baseline),
                                    'HostIslandBaseline', str(work / (name + '-native-census.json'))],
                                   capture_output=True, text=True, timeout=300)
    (work / (name + '-native.log')).write_text(native_result.stdout + native_result.stderr)
    if native_result.returncode != 0:
        observations.append(dict(case=name, native_baseline_passed=False,
                                 native_exit_code=native_result.returncode, ps_exit_code=None,
                                 diagnostic_excerpt=(native_result.stdout + native_result.stderr).splitlines()[:8],
                                 invalid_host_gap_rejected=False))
        print('PS0_HOST_ISLAND_OBSERVATION:' + json.dumps(observations[-1], sort_keys=True), flush=True)
        continue
    source_root = work / (name + '-source')
    source_root.mkdir()
    source = source_root / 'HostIslandProbe.ps'
    source.write_text(ps_header + ps + '\n')
    result = subprocess.run(['lake', '-R', '-f', 'lakefile.project.lean',
                            '-KsourceRoot=' + str(source_root), '-Kroots=HostIslandProbe',
                            '-KmoduleNames=HostIslandProbe', '-Kbootstrap=true', '-KsourceGrammar=true',
                            '-Kdriver=' + str(ROOT / '.lake/build/bin/ps0'),
                            '-KprojectBuildDir=' + str(work / (name + '-build')),
                            'build', 'HostIslandProbe'],
                            capture_output=True, text=True, timeout=300)
    diagnostic = result.stdout + result.stderr
    (work / (name + '-ps.log')).write_text(diagnostic)
    print(diagnostic, end='', flush=True)
    observations.append(dict(case=name, native_baseline_passed=True, ps_exit_code=result.returncode,
                             diagnostic_excerpt=diagnostic.splitlines()[:8],
                             invalid_host_gap_rejected=result.returncode != 0 and 'PS0V1-CALL-GAP' in diagnostic))
    print('PS0_HOST_ISLAND_OBSERVATION:' + json.dumps(observations[-1], sort_keys=True), flush=True)
(work / 'evidence.json').write_text(json.dumps(dict(source=os.environ['PS0_SOURCE_SHA'],
    observations=observations, scope='selected ordinary host operands; native baseline failures recorded separately',
    grammar_migration_complete=False, verified_execution=False), indent=2) + '\n')
assert all(row['invalid_host_gap_rejected'] for row in observations), 'ordinary host bodies must not silently accept native-only parenthesized application'
print('PS0_HOST_ISLAND_GAPS: PASS', flush=True)
