#!/usr/bin/env python3
"""Compile real pinned compiler declaration heads through the native PS grammar."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
parser = argparse.ArgumentParser()
parser.add_argument('--fixture', default='ClosedTermCache')
parser.add_argument('--module', default='Lean.Compiler.ClosedTermCache')
parser.add_argument('--blob', default='20b7acf5d684789ab52b81dda7def4b19568213c')
parser.add_argument('--declarations', default='cacheClosedTermName,getClosedTermName?,isClosedTermName')
args = parser.parse_args()
work = ROOT / 'build' / ('compiler-heads-' + os.environ['GITHUB_RUN_ID'] + '-' + args.fixture)
work.mkdir(parents=True, exist_ok=False)
fixture = ROOT / 'tests/pinned' / (args.fixture + '.lean')
blob = hashlib.sha1(b'blob ' + str(len(fixture.read_bytes())).encode() + b'\0' + fixture.read_bytes()).hexdigest()
assert blob == args.blob
module = args.module
relative_module = Path(*module.split('.'))
driver = ROOT / '.lake/build/bin/ps0'
sysroot = Path(subprocess.check_output(['lean', '--print-prefix'], text=True).strip())

def run(args, label, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=600)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout

original = work / 'original/src' / relative_module.with_suffix('.ps')
original.parent.mkdir(parents=True)
shutil.copy2(fixture, original)
census = work / 'original-census.json'
run([driver, 'census-source', original, module, census], 'native-census')
converted = work / 'converted/src' / relative_module.with_suffix('.ps')
plan_file = work / 'plan.json'
run(['python3', 'tests/migrate-compiler-heads.py', census, original, converted,
     '--plan', plan_file], 'plan')
plan = json.loads(plan_file.read_text())
assert set(plan['declarations']) == set(args.declarations.split(',')), plan['declarations']

def build(source, directory, grammar=False, ok=True):
    # Native module lookup resolves a namespace prefix in one library root. The
    # finite SDK-backed probe supplies sibling metadata without shadowing it.
    sdk_lib = sysroot / 'lib/lean'
    for item in sdk_lib.rglob('*'):
        if not item.is_file() or not any(x in item.name for x in ['.olean', '.ir']):
            continue
        relative = item.relative_to(sdk_lib)
        if relative.parent == relative_module.parent and item.name.startswith(relative_module.name + '.'):
            continue
        target = directory / 'lib/lean' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(item)
    args = ['lake', '-R', '-f', 'lakefile.project.lean',
            '-KsourceRoot=' + str(source.parents[len(module.split('.')) - 1]), '-Kroots=Lean.Compiler',
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
for path in [Path('ir') / relative_module.with_suffix('.c'), Path('lib/lean') / relative_module.with_suffix('.olean')]:
    path = str(path)
    comparisons[path] = {'native': sha(baseline / path), 'ps': sha(migrated / path)}
    assert comparisons[path]['native'] == comparisons[path]['ps'], (path, comparisons[path])
observed = json.loads((migrated / 'lib/lean' / relative_module.with_suffix('.ilean.ps0-source-census.json')).read_text())
def source_declarations(commands):
    for command in commands:
        if command['declaration'] is not None:
            yield command['declaration']
        yield from source_declarations(command.get('nestedCommands', []))
declarations = list(source_declarations(observed['commands']))
assert {d['sourceName'] for d in declarations if d['mode'] == 'mapped-ps'} == set(plan['declarations'])
assert observed['imports'] == json.loads(census.read_text())['imports']
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'lean_commit': observed['leanCommit'],
    'pinned_blob': blob, 'module': module, 'comparisons': comparisons,
    'dependencies': 'pinned SDK sibling olean/IR metadata; target artifacts are built afresh by native Lake',
    'scope': 'real typed compiler declaration heads, including explicit nested commands; native bodies retained; not whole grammar migration',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_PINNED_COMPILER_HEADS_NATIVE_PARITY: PASS', flush=True)
