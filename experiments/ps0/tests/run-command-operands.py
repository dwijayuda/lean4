#!/usr/bin/env python3
"""Qualify explicit native scoped/mutual command operands using PS grammar."""
from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('command-operands-' + os.environ['GITHUB_RUN_ID'])
source = work / 'src/ScopedPS'
source.mkdir(parents=True, exist_ok=False)
(source / 'Main.ps').write_text('''module
prelude
public import Init
public section
set_option pp.universes true in
function scoped(n: Nat): Nat := n + 1
open Nat in
function opened(n: Nat): Nat := succ(n)
set_option pp.universes true in open Nat in
function nested(n: Nat): Nat := succ(n)
mutual
  function first(n: Nat): Nat := n
  function second(n: Nat): Nat := first(n)
end
const scopedValue: Nat := scoped(2)
const openedValue: Nat := opened(2)
const nestedValue: Nat := nested(2)
const mutualValue: Nat := second(3)
def main : IO Unit := IO.println s!"PS0_COMMAND_OPERANDS:{scopedValue}:{openedValue}:{nestedValue}:{mutualValue}"
''')
(source / 'Quoted.ps').write_text('''module
prelude
public meta import Lean
public section
meta def scopedQuote : Lean.MacroM(Lean.TSyntax `command) :=
  `(command| set_option pp.universes true in def function (x : Nat) : Nat := x)
meta def mutualQuote : Lean.MacroM(Lean.TSyntax `command) :=
  `(command| mutual def function (x : Nat) : Nat := x end)
run_cmd do
  let scoped ← Lean.Elab.liftMacroM scopedQuote
  unless scoped.raw.isOfKind ``Lean.Parser.Command.in &&
      scoped.raw[2].isOfKind ``Lean.Parser.Command.declaration do
    Lean.throwError "scoped native quotation was reinterpreted as PS"
  let mutual ← Lean.Elab.liftMacroM mutualQuote
  unless mutual.raw.isOfKind ``Lean.Parser.Command.mutual &&
      mutual.raw[1].getArgs.all (fun c => c.isOfKind ``Lean.Parser.Command.declaration) do
    Lean.throwError "mutual native quotation was reinterpreted as PS"
''')
driver = ROOT / '.lake/build/bin/ps0'

def run(args, label, ok=True):
    r = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=600)
    (work / (label + '.log')).write_text(r.stdout)
    print(r.stdout, end='', flush=True)
    assert (r.returncode == 0) == ok, (label, r.returncode)
    return r.stdout

build = work / 'native'
base = ['lake', '-R', '-f', 'lakefile.project.lean',
        '-KsourceRoot=' + str(source.parent), '-Kroots=ScopedPS',
        '-KmoduleNames=ScopedPS.Main,ScopedPS.Quoted', '-KrootModule=ScopedPS.Main',
        '-KsourceGrammar=true', '-Kdriver=' + str(driver), '-KprojectBuildDir=' + str(build)]
run([*base, 'build', 'PS0Project:static', 'ps0project'], 'build')
assert 'PS0_COMMAND_OPERANDS:3:3:3:3' in run([build / 'bin/ps0project'], 'runtime')
data = json.loads((build / 'lib/lean/ScopedPS/Main.ilean.ps0-source-census.json').read_text())
assert data['imports'] == ['Init']
rows = []

def collect(commands):
    for command in commands:
        rows.append(command)
        collect(command.get('nestedCommands', []))

collect(data['commands'])
mapped = {c['declaration']['sourceName'] for c in rows if c['declaration'] and c['declaration']['mode'] == 'mapped-ps'}
assert {'scoped', 'opened', 'nested', 'first', 'second'} <= mapped, mapped
for name, code, diagnostic in [
    ('scoped-gap', 'set_option pp.universes true in\nfunction bad(n: Nat := add (1, 2)): Nat := n', 'PS0V1-CALL-GAP'),
    ('open-gap', 'open Nat in\nfunction bad(n: Nat := add (1, 2)): Nat := n', 'PS0V1-CALL-GAP'),
    ('mutual-order', 'mutual\nfunction bad(n: Nat := add(x := 1, 2)): Nat := n\nend', 'PS0V1-CALL-ORDER'),
]:
    path = source / 'Bad.ps'
    path.write_text('module\nprelude\npublic import Init\npublic section\nfunction add(x: Nat, y: Nat): Nat := x + y\n' + code + '\n')
    args = [x for x in base if not x.startswith('-KmoduleNames=')]
    args += ['-KmoduleNames=ScopedPS.Bad', 'build', 'ScopedPS.Bad']
    assert diagnostic in run(args, name, ok=False)
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'imports': data['imports'], 'mapped_source_names': sorted(mapped),
    'oracle': 'PS0_COMMAND_OPERANDS:3:3:3:3',
    'scope': 'explicit native in/mutual operand routing and original nested-source census; quoted native commands stay opaque',
    'verified_execution': False,
}, indent=2) + '\n')
print('PS0_SCOPED_MUTUAL_COMMAND_OPERANDS: PASS', flush=True)
