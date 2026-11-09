#!/usr/bin/env python3
"""Compile real pinned compiler declaration heads through the native PS grammar."""
from pathlib import Path
from collections import Counter
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
parser.add_argument('--sdk-source', action='store_true')
parser.add_argument('--roots', default='Lean.Compiler')
parser.add_argument('--bootstrap', action='store_true')
args = parser.parse_args()
work = ROOT / 'build' / ('compiler-heads-' + os.environ['GITHUB_RUN_ID'] + '-' + args.fixture)
work.mkdir(parents=True, exist_ok=False)
sysroot = Path(subprocess.check_output(['lean', '--print-prefix'], text=True).strip())
fixture = (sysroot / 'src/lean' / Path(*args.module.split('.')).with_suffix('.lean')
           if args.sdk_source else ROOT / 'tests/pinned' / (args.fixture + '.lean'))
blob = hashlib.sha1(b'blob ' + str(len(fixture.read_bytes())).encode() + b'\0' + fixture.read_bytes()).hexdigest()
assert blob == args.blob
module = args.module
relative_module = Path(*module.split('.'))
driver = ROOT / '.lake/build/bin/ps0'

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
boundary_kind = {'NatLinear': 'Lean.Parser.Command.attribute',
                 'GrindAC': 'Lean.Parser.Command.attribute',
                 'IteratorEmpty': 'Lean.Parser.Command.structure'}.get(args.fixture)
boundary_heads = [s for s in plan['strategies']
                  if s.get('reason') == 'preserve reserved R2 head after native identifier/field list']
if boundary_kind:
    assert any(s['previousCommandHeadKind'] == boundary_kind and s['targetKeyword'] == 'def'
               for s in boundary_heads), (args.fixture, boundary_heads)
scoped_binary_kinds = []
if args.fixture == 'SPredLaws':
    for name in ['and_curry', 'or_curry', 'imp_curry']:
        declaration = next(d for d in original_declarations if d['sourceName'] == name)
        result = declaration['signatureSyntax']['args'][1]['args'][1]
        assert result['nativeBinaryOperator'], (name, result)
        scoped_binary_kinds.append(result['kind'])

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
    build_args = ['lake', '-R', '-f', 'lakefile.project.lean',
            '-KsourceRoot=' + str(source.parents[len(module.split('.')) - 1]), '-Kroots=' + args.roots,
            '-KmoduleNames=' + module, '-KrootModule=CompilerHeadProbeMain',
            '-Kdriver=' + str(driver), '-KprojectBuildDir=' + str(directory)]
    if grammar:
        build_args += ['-KsourceGrammar=true']
    if args.bootstrap:
        build_args += ['-Kbootstrap=true']
    run([*build_args, 'build', module], directory.name, ok)

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
family_productions = {'Lean.Parser.Command.abbrev': 'PS0.StandardAdapters.ps0StandardAbbrev',
                      'Lean.Parser.Command.theorem': 'PS0.StandardAdapters.ps0StandardTheorem',
                      'Lean.Parser.Command.opaque': 'PS0.StandardAdapters.ps0StandardOpaque',
                      'Lean.Parser.Command.axiom': 'PS0.StandardAdapters.ps0StandardAxiom',
                      'Lean.Parser.Command.instance': 'PS0.StandardAdapters.ps0StandardInstance',
                      'Lean.Parser.Command.example': 'PS0.StandardAdapters.ps0StandardExample'}
expected_other = Counter((d['sourceName'], family_productions[d['production']])
                         for d in original_declarations if d['production'] in family_productions)
productions = {'function': 'PS0.StandardAdapters.ps0StandardFunction',
               'const': 'PS0.StandardAdapters.ps0StandardConst',
               'def': 'PS0.StandardAdapters.ps0StandardDef'}
expected_mapped = expected_other + Counter((s['sourceName'], productions[s['targetKeyword']])
                                           for s in plan['strategies'])
actual_mapped = Counter((d['sourceName'], d['production'])
                       for d in declarations if d['mode'] == 'mapped-ps')
assert actual_mapped == expected_mapped, (actual_mapped, expected_mapped)
assert all(d['mode'] == 'mapped-ps' for d in declarations)
native_definitions = [d for d in original_declarations if d['production'] == 'Lean.Parser.Command.definition']
mapped_definitions = [d for d in declarations if d['production'] in productions.values()]
assert [d['sourceName'] for d in native_definitions] == plan['declarations']
assert len(native_definitions) == len(mapped_definitions) == len(plan['strategies'])
for native, strategy, mapped in zip(native_definitions, plan['strategies'], mapped_definitions):
    assert native['sourceName'] == strategy['sourceName'] == mapped['sourceName']
    assert mapped['production'] == productions[strategy['targetKeyword']]
    if native.get('valueSyntax', {}).get('kind') == 'Lean.Parser.Command.declValEqns':
        assert mapped['declarationValueKind'] == 'PS0.StandardAdapters.ps0DeclEqns', mapped
        assert mapped['equationBodyKinds'], mapped
equation_definitions = {d['sourceName'] for d in original_declarations
                        if d['production'] == 'Lean.Parser.Command.definition'
                        and d.get('valueSyntax', {}).get('kind') == 'Lean.Parser.Command.declValEqns'}
assert observed['imports'] == json.loads(census.read_text())['imports']
owned_value_calls = [name for name in args.owned_value_calls.split(',') if name]
for name in owned_value_calls:
    declaration = next(d for d in declarations if d['sourceName'] == name)
    assert declaration['ownedValueCall'], declaration
    assert any('term_&&_' in kind for kind in declaration['ownedOperatorKinds']), declaration
    assert any('term_!=_' in kind for kind in declaration['ownedOperatorKinds']), declaration
if args.fixture == 'EmitUtil':
    assert next(d for d in declarations if d['sourceName'] == 'collectUsedDecls')['nativeWhereTail']
if args.fixture == 'DeclarationForms':
    assert sum(d['production'] == 'PS0.StandardAdapters.ps0StandardExample' for d in declarations) == 2
    assert next(d for d in declarations if d['sourceName'] == 'make')['whereFieldCount'] == 3
    assert next(d for d in declarations if d['sourceName'] == 'boolTransform')['whereFieldCount'] == 1
    assert next(d for d in declarations if d['sourceName'] == 'natTransform')['whereFieldCount'] == 1
    assert next(d for d in declarations if d['sourceName'] == 'boolRefl')['equationBodyKinds']
if args.fixture == 'DoLayoutProbe':
    for name in ['layoutValue', 'nestedValue', 'localDefault', 'localShared', 'unitReturn']:
        declaration = next(d for d in declarations if d['sourceName'] == name)
        assert declaration['valueRootKind'] == 'ps0HostDo', declaration
        assert declaration['doSequenceKind'] == 'Lean.Parser.Term.doSeqIndent', declaration
        assert declaration['doElementKinds'], declaration
    layout = next(d for d in declarations if d['sourceName'] == 'layoutValue')
    assert layout['doElementKinds'] == [
        'Lean.Parser.Term.doLet', 'Lean.Parser.Term.doLet', 'Lean.Parser.Term.doReassign',
        'Lean.Parser.Term.doLetArrow', 'Lean.Parser.Term.doExpr', 'Lean.Parser.Term.doReturn'], layout
if args.fixture in ['UnlessProbe', 'InlineAttrs']:
    name = 'bodyValue' if args.fixture == 'UnlessProbe' else 'isValidMacroInline'
    declaration = next(d for d in declarations if d['sourceName'] == name)
    assert 'Lean.Parser.Term.doUnless' in declaration['doElementKinds'], declaration
    if args.fixture == 'UnlessProbe':
        assert declaration['doUnlessConditionKinds'] == ['ps0HostAdjacentCall', 'ps0HostAdjacentCall'], declaration
        assert declaration['doUnlessBlockKinds'] == ['Lean.Parser.Term.doSeqIndent', 'Lean.Parser.Term.doSeqIndent'], declaration
        assert next(d for d in declarations if d['sourceName'] == 'termValue')['valueRootKind'] == 'Lean.Parser.Term.termUnless'
    else:
        assert 'PS0.Operators.ownedBinary' in declaration['doUnlessConditionKinds'], declaration
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'lean_commit': observed['leanCommit'],
    'pinned_blob': blob, 'module': module, 'comparisons': comparisons,
    'converted_declarations': plan['declarations'], 'unchanged_abbrev_adapters': sorted(unchanged_abbrevs),
    'source_strategies': plan.get('strategies', []),
    'contextual_boundary_heads': boundary_heads,
    'scoped_binary_kinds': scoped_binary_kinds,
    'operator_descriptor_scope': json.loads(census.read_text()).get('operatorDescriptorScope'),
    'equation_definitions': sorted(equation_definitions),
    'owned_value_calls': owned_value_calls,
    'non_definition_source_roles': [{key: d.get(key) for key in ['sourceName', 'production', 'mode', 'declarationValueKind', 'equationBodyKinds', 'whereFieldCount']}
                                    for d in declarations if d['production'] in family_productions.values()],
    'mapped_source_roles': [{key: d.get(key) for key in ['sourceName', 'valueRootKind', 'ownedValueCall', 'ownedOperatorKinds', 'nativeWhereTail', 'declarationValueKind', 'equationBodyKinds', 'doSequenceKind', 'doElementKinds', 'doUnlessConditionKinds', 'doUnlessBlockKinds', 'termUnlessConditionKind']}
                            for d in declarations if d['sourceName'] in plan['declarations']],
    'dependencies': 'pinned SDK sibling olean/IR metadata; target artifacts are built afresh by native Lake',
    'scope': 'real typed compiler declaration heads and explicit owned type/body roles; unselected local/quoted/DSL syntax retained; not whole grammar migration',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_PINNED_COMPILER_HEADS_NATIVE_PARITY: PASS', flush=True)
