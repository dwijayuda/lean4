#!/usr/bin/env python3
"""Verify runtime startup of metacompiler hooks through a modern native Lake root."""
from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('modern-frontend-startup-' + os.environ['GITHUB_RUN_ID'])
source = work / 'src'
(source / 'StartupProbe').mkdir(parents=True, exist_ok=False)
driver = ROOT / '.lake/build/bin/ps0'

def run(args, label):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=600)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert result.returncode == 0, (label, result.returncode)

run([driver, 'convert-native', ROOT / 'PS0/SourceCensus.lean', source / 'PS0/SourceCensus.ps'], 'convert')
(source / 'StartupProbe/Main.ps').write_text('''module
prelude
public import Lean
public import PS0.SourceCensus
public section
def main : IO Unit := do
  let arguments ← IO.getArgs
  let some output := arguments[0]? | throw (IO.userError "missing output path")
  Lean.initSearchPath (← Lean.findSysroot)
  unsafe Lean.enableInitializersExecution
  let options := ({} : Lean.Options).set `ps0.sourceCensusPath output
  let env ← Lean.Elab.runFrontend
    "module\\nprelude\\npublic import Init\\ndef observedValue : Nat := 7\\n"
    options "StartupInput.ps" `StartupInput (trustLevel := 0)
  unless env.isSome do throw (IO.userError "modern metacompiler rejected source")
  let data ← IO.FS.readFile output
  let _ ← IO.ofExcept (Lean.Json.parse data)
  IO.println "PS0_MODERN_FRONTEND_HOOKS: PASS"
''')
build = work / 'native'
run(['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceRoot=' + str(source),
     '-Kroots=PS0,StartupProbe', '-KmoduleNames=PS0.SourceCensus,StartupProbe.Main',
     '-KrootModule=StartupProbe.Main', '-Kdriver=' + str(driver),
     '-KprojectBuildDir=' + str(build), 'build', 'ps0project'], 'build')
output = work / 'actual-census.json'
run([build / 'bin/ps0project', output], 'runtime')
data = json.loads(output.read_text())
assert data['schema'] == 'ps0-native-source-census/1'
assert data['imports'] == ['Init']
assert any(c['declaration'] and c['declaration']['sourceName'] == 'observedValue'
           for c in data['commands'])
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'oracle': 'PS0_MODERN_FRONTEND_HOOKS: PASS',
    'scope': 'modern native executable runtime option and module-linter initialization; SDK-linked finite probe',
    'verified_execution': False,
}, indent=2) + '\n')
