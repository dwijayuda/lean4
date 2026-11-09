#!/usr/bin/env python3
"""Compile real pinned compiler declaration heads through the native PS grammar."""
from pathlib import Path
import argparse
import difflib
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
parser.add_argument('--owned-value-calls', default='')
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

def source_declarations(commands):
    for command in commands:
        if command['declaration'] is not None:
            yield command['declaration']
        yield from source_declarations(command.get('nestedCommands', []))


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
if args.fixture == 'TelescopeProbe':
    for marker in ['PS0_HEAD_TRIVIA', 'PS0_GROUP_TRIVIA', 'PS0_CALL_TRIVIA',
                   'PS0_ARG_TRIVIA', 'PS0_TYPE_TRIVIA', 'PS0_NAMED_TRIVIA']:
        assert original.read_bytes().count(marker.encode()) == converted.read_bytes().count(marker.encode()) == 1
    assert original.read_bytes().count(b'\n') == converted.read_bytes().count(b'\n')
original_declarations = list(source_declarations(json.loads(census.read_text())['commands']))
expected = ({d['sourceName'] for d in original_declarations
             if d['production'] == 'Lean.Parser.Command.definition'}
            if args.declarations == 'ALL' else set(args.declarations.split(',')))
assert set(plan['declarations']) == expected, plan['declarations']

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
    if comparisons[path]['native'] != comparisons[path]['ps'] and path.endswith('.c'):
        difference = ''.join(difflib.unified_diff((baseline / path).read_text().splitlines(True),
                                                 (migrated / path).read_text().splitlines(True),
                                                 fromfile='native.c', tofile='ps.c'))
        (work / 'native-c.diff').write_text(difference)
        print(difference[:12000], flush=True)
    if comparisons[path]['native'] != comparisons[path]['ps'] and path.endswith('.olean'):
        run(['lake', 'env', 'lean', '--run', 'tests/compare-compiler-olean.lean',
             baseline / path, migrated / path], 'olean-diagnostic')
    assert comparisons[path]['native'] == comparisons[path]['ps'], (path, comparisons[path])
observed = json.loads((migrated / 'lib/lean' / relative_module.with_suffix('.ilean.ps0-source-census.json')).read_text())
declarations = list(source_declarations(observed['commands']))
unchanged_abbrevs = {d['sourceName'] for d in original_declarations
                     if d['production'] == 'Lean.Parser.Command.abbrev'}
mapped = {d['sourceName'] for d in declarations if d['mode'] == 'mapped-ps'}
family_productions = {'Lean.Parser.Command.abbrev': 'PS0.StandardAdapters.ps0StandardAbbrev',
                      'Lean.Parser.Command.theorem': 'PS0.StandardAdapters.ps0StandardTheorem',
                      'Lean.Parser.Command.opaque': 'PS0.StandardAdapters.ps0StandardOpaque',
                      'Lean.Parser.Command.axiom': 'PS0.StandardAdapters.ps0StandardAxiom'}
expected_other = {d['sourceName']: family_productions[d['production']]
                  for d in original_declarations if d['production'] in family_productions}
expected_mapped = set(plan['declarations']) | set(expected_other)
assert mapped == expected_mapped, (sorted(mapped), sorted(expected_mapped))
strategies = {d['sourceName']: d['targetKeyword'] for d in plan.get('strategies', [])}
productions = {'function': 'PS0.StandardAdapters.ps0StandardFunction',
               'const': 'PS0.StandardAdapters.ps0StandardConst',
               'def': 'PS0.StandardAdapters.ps0StandardDef'}
for declaration in declarations:
    if declaration['sourceName'] in expected_other:
        assert declaration['mode'] == 'mapped-ps'
        assert declaration['production'] == expected_other[declaration['sourceName']], declaration
    if declaration['sourceName'] in plan['declarations']:
        keyword = strategies.get(declaration['sourceName'], 'function')
        assert declaration['mode'] == 'mapped-ps'
        assert declaration['production'] == productions[keyword], declaration
equation_definitions = {d['sourceName'] for d in original_declarations
                        if d['production'] == 'Lean.Parser.Command.definition'
                        and d.get('valueSyntax', {}).get('kind') == 'Lean.Parser.Command.declValEqns'}
for declaration in declarations:
    if declaration['sourceName'] in equation_definitions:
        assert declaration['declarationValueKind'] == 'PS0.StandardAdapters.ps0DeclEqns', declaration
        assert declaration['equationBodyKinds'], declaration
assert observed['imports'] == json.loads(census.read_text())['imports']
owned_value_calls = [name for name in args.owned_value_calls.split(',') if name]
for name in owned_value_calls:
    declaration = next(d for d in declarations if d['sourceName'] == name)
    assert declaration['ownedValueCall'], declaration
    assert any('term_&&_' in kind for kind in declaration['ownedOperatorKinds']), declaration
    assert any('term_!=_' in kind for kind in declaration['ownedOperatorKinds']), declaration
if args.fixture == 'EmitUtil':
    assert next(d for d in declarations if d['sourceName'] == 'collectUsedDecls')['nativeWhereTail']
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'lean_commit': observed['leanCommit'],
    'pinned_blob': blob, 'module': module, 'comparisons': comparisons,
    'converted_declarations': plan['declarations'], 'unchanged_abbrev_adapters': sorted(unchanged_abbrevs),
    'source_strategies': plan.get('strategies', []),
    'equation_definitions': sorted(equation_definitions),
    'owned_value_calls': owned_value_calls,
    'mapped_source_roles': [{key: d.get(key) for key in ['sourceName', 'valueRootKind', 'ownedValueCall', 'ownedOperatorKinds', 'nativeWhereTail', 'declarationValueKind', 'equationBodyKinds']}
                            for d in declarations if d['sourceName'] in plan['declarations']],
    'dependencies': 'pinned SDK sibling olean/IR metadata; target artifacts are built afresh by native Lake',
    'scope': 'real typed compiler declaration heads and explicit owned type/body roles; unselected local/quoted/DSL syntax retained; not whole grammar migration',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_PINNED_COMPILER_HEADS_NATIVE_PARITY: PASS', flush=True)
