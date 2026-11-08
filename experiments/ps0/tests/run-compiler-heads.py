#!/usr/bin/env python3
"""Compile real pinned compiler declaration heads through the native PS grammar."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('compiler-heads-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
fixture = ROOT / 'tests/pinned/ClosedTermCache.lean'
blob = hashlib.sha1(b'blob ' + str(len(fixture.read_bytes())).encode() + b'\0' + fixture.read_bytes()).hexdigest()
assert blob == '20b7acf5d684789ab52b81dda7def4b19568213c'
module = 'Lean.Compiler.ClosedTermCache'
driver = ROOT / '.lake/build/bin/ps0'
sysroot = Path(subprocess.check_output(['lean', '--print-prefix'], text=True).strip())

def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=600)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout

original = work / 'original/src/Lean/Compiler/ClosedTermCache.ps'
original.parent.mkdir(parents=True)
shutil.copy2(fixture, original)
census = work / 'original-census.json'
run([driver, 'census-source', original, module, census], 'native-census')
converted = work / 'converted/src/Lean/Compiler/ClosedTermCache.ps'
plan_file = work / 'plan.json'
run(['python3', 'tests/migrate-compiler-heads.py', census, original, converted,
     '--plan', plan_file], 'plan')
plan = json.loads(plan_file.read_text())
assert set(plan['declarations']) == {'cacheClosedTermName', 'getClosedTermName?', 'isClosedTermName'}

def build(source, directory, grammar=False, ok=True):
    # Native module lookup resolves a namespace prefix in one library root. The
    # finite SDK-backed probe supplies sibling metadata without shadowing it.
    sdk_lib = sysroot / 'lib/lean'
    for item in sdk_lib.rglob('*'):
        if not item.is_file() or not any(x in item.name for x in ['.olean', '.ir']):
            continue
        relative = item.relative_to(sdk_lib)
        if relative.parent == Path('Lean/Compiler') and item.name.startswith('ClosedTermCache.'):
            continue
        target = directory / 'lib/lean' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(item)
    args = ['lake', '-R', '-f', 'lakefile.project.lean',
            '-KsourceRoot=' + str(source.parents[2]), '-Kroots=Lean.Compiler',
            '-KmoduleNames=' + module, '-KrootModule=CompilerHeadProbeMain',
            '-Kdriver=' + str(driver), '-KprojectBuildDir=' + str(directory)]
    if grammar:
        args += ['-KsourceGrammar=true']
    run([*args, 'build', module], directory.name, ok)

baseline, migrated = work / 'baseline', work / 'migrated'
build(original, baseline)
build(converted, work / 'native-rejects-converted', ok=False)
build(converted, migrated, grammar=True)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
comparisons = {}
for path in ['ir/Lean/Compiler/ClosedTermCache.c', 'lib/lean/Lean/Compiler/ClosedTermCache.olean']:
    comparisons[path] = {'native': sha(baseline / path), 'ps': sha(migrated / path)}
    assert comparisons[path]['native'] == comparisons[path]['ps'], (path, comparisons[path])
observed = json.loads((migrated / 'lib/lean/Lean/Compiler/ClosedTermCache.ilean.ps0-source-census.json').read_text())
declarations = [c['declaration'] for c in observed['commands'] if c['declaration'] is not None]
assert {d['sourceName'] for d in declarations if d['mode'] == 'mapped-ps'} == set(plan['declarations'])
assert observed['imports'] == ['Lean.Environment']
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'lean_commit': observed['leanCommit'],
    'pinned_blob': blob, 'module': module, 'comparisons': comparisons,
    'dependencies': 'pinned SDK sibling olean/IR metadata; target artifacts are built afresh by native Lake',
    'scope': 'three real typed compiler declaration heads; native bodies retained; not whole grammar migration',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_PINNED_COMPILER_HEADS_NATIVE_PARITY: PASS', flush=True)
