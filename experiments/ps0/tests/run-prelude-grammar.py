#!/usr/bin/env python3
"""Exercise syntax-only PS grammar in real prelude modules via native Lake."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('prelude-grammar-' + os.environ['GITHUB_RUN_ID'] + os.environ.get('PS0_TEST_TAG', ''))
source = work / 'src/PreludePS'
source.mkdir(parents=True, exist_ok=False)
(source / 'Core.ps').write_text('''module
prelude
public import Init
public section
function plus(left: Nat, right: Nat := 1): Nat := left + right
const answer: Nat := plus(41)
def function : Nat := 3
def nativeStrict {{a : Type}} (x : a) : a := x
function psStrict {{a : Type}}(x: a): a := x
const strictAnswer: Nat := psStrict(3)
''')
(source / 'Main.ps').write_text('''module
prelude
public import PreludePS.Core
public section
def main : IO Unit := IO.println s!"PS0_PRELUDE_GRAMMAR:{answer}:{strictAnswer}"
''')
(source / 'Quoted.ps').write_text('''module
prelude
public meta import Lean
public section
meta def quotedCommand : Lean.MacroM(Lean.TSyntax `command) :=
  `(command| def function (x : Nat) : Nat := x)
meta def quotedTerm : Lean.MacroM(Lean.TSyntax `term) := `(term| fn (1, 2))
meta def quotedBinder : Lean.MacroM(Lean.TSyntax ``Lean.Parser.Term.bracketedBinder) :=
  `(bracketedBinder| {{x : Nat}})
run_cmd do
  let cmd ← Lean.Elab.liftMacroM quotedCommand
  unless cmd.raw.isOfKind ``Lean.Parser.Command.declaration do
    Lean.throwError "PS command routing escaped into native command quotation"
  let term ← Lean.Elab.liftMacroM quotedTerm
  unless term.raw.isOfKind ``Lean.Parser.Term.app do
    Lean.throwError "PS term routing escaped into native term quotation"
''')
driver = Path(os.environ.get('PS0_TEST_DRIVER', str(ROOT / '.lake/build/bin/ps0'))).resolve()

def run(args, label, ok=True):
    r = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=600)
    (work / (label + '.log')).write_text(r.stdout)
    print(r.stdout, end='', flush=True)
    assert (r.returncode == 0) == ok, (label, r.returncode)
    return r.stdout

args = ['lake', '-R', '-f', 'lakefile.project.lean',
        '-KsourceRoot=' + str(source.parent), '-Kroots=PreludePS',
        '-KmoduleNames=PreludePS.Core,PreludePS.Main,PreludePS.Quoted',
        '-KrootModule=PreludePS.Main', '-Kdriver=' + str(driver)]
control = run([*args, '-KprojectBuildDir=' + str(work / 'native-control'), 'build',
     'PreludePS.Core'], 'native-control', ok=False)
assert 'unexpected identifier; expected command' in control
build = work / 'grammar'
run([*args, '-KsourceGrammar=true', '-KprojectBuildDir=' + str(build),
     'build', 'PS0Project:static', 'ps0project'], 'grammar-build')
assert 'PS0_PRELUDE_GRAMMAR:42:3' in run([build / 'bin/ps0project'], 'runtime')
stage = work / 'compiler-stage'
run([*args, '-KsourceGrammar=true', '-Kbootstrap=true',
     '-KprojectBuildDir=' + str(stage), 'build', 'PreludePS.Core', 'PreludePS.Quoted'],
    'compiler-stage')
for name in ['Core', 'Quoted']:
    setup = json.loads((stage / 'ir/PreludePS' / (name + '.setup.json')).read_text())
    assert setup['options']['interpreter.prefer_native'] is False
    assert setup['options']['ps0.sourceGrammar'] is True
evidence = {}
for name, expected in [('Core', ['Init']), ('Main', ['PreludePS.Core']), ('Quoted', ['Lean'])]:
    rel = Path('PreludePS') / name
    stem = build / 'lib/lean' / rel
    census = json.loads(stem.with_suffix('.ilean.ps0-source-census.json').read_text())
    origins = json.loads(stem.with_suffix('.ilean.ps0-source-map.json').read_text())
    raw = (source / (name + '.ps')).read_text()
    assert census['imports'] == expected, (name, census['imports'])
    assert census['nativeSource'] == origins['nativeSource'] == origins['source'] == raw
    assert all(s['kind'] == 'original' for s in origins['segments'])
    assert all(not x.startswith('PS0.') for x in census['environmentDeclNames'])
    evidence[name] = {'imports': expected, 'source_sha256': hashlib.sha256(raw.encode()).hexdigest()}
assert any(c['declaration'] and c['declaration']['mode'] == 'mapped-ps'
           for c in json.loads((build / 'lib/lean/PreludePS/Core.ilean.ps0-source-census.json').read_text())['commands'])
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'modules': evidence,
    'oracle': 'PS0_PRELUDE_GRAMMAR:42:3', 'verified_execution': False,
    'compiler_stage_options': {'interpreter.prefer_native': False, 'ps0.sourceGrammar': True},
    'scope': 'finite prelude grammar and native quotation isolation; not full corpus migration',
}, indent=2) + '\n')
print('PS0_PRELUDE_GRAMMAR_NO_HIDDEN_IMPORTS: PASS', flush=True)
