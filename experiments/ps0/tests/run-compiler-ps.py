#!/usr/bin/env python3
"""Compile the pinned Lean/Init/Std/Lake and PS0 source forest from .ps files."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--driver', type=Path)
parser.add_argument('--compare', type=Path)
parser.add_argument('--source-plans', type=Path)
parser.add_argument('--plan-source')
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
driver = (args.driver or ROOT / '.lake/build/bin/ps0').resolve()
evidence = ROOT / 'build/compiler-evidence'
evidence.mkdir(parents=True, exist_ok=True)
work = ROOT / 'build' / ('compiler-ps-' + os.environ.get('GITHUB_RUN_ID', str(os.getpid())))
source = work / 'src'
source.mkdir(parents=True, exist_ok=False)
LEAN = 'eb6cafb7290e8bd5f2937522d8d804f58f02bafc'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(cmd, name, timeout=14400, env=None):
    start = time.monotonic()
    with (evidence / (name + '.log')).open('w') as log:
        p = subprocess.Popen([str(x) for x in cmd], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
        for line in p.stdout:
            print(line, end='', flush=True)
            log.write(line)
            log.flush()
            if time.monotonic() - start > timeout:
                p.kill()
                raise TimeoutError(name)
        code = p.wait(timeout=60)
        assert code == 0, (name, code)

assert subprocess.check_output(['lean', '--githash'], text=True).strip() == LEAN
sysroot = Path(subprocess.check_output(['lean', '--print-prefix'], text=True).strip())
sdk = sysroot / 'src/lean'
originals = {}
for namespace in ['Init', 'Std', 'Lean']:
    folder = sdk / namespace
    assert folder.is_dir(), folder
    run([driver, 'convert-native-tree', folder, source / namespace], 'convert-' + namespace)
    for p in folder.rglob('*.lean'):
        originals[namespace + '/' + str(p.relative_to(folder)).replace(os.sep, '/')] = p
    top = sdk / (namespace + '.lean')
    assert top.is_file(), top
    run([driver, 'convert-native', top, source / (namespace + '.ps')], 'convert-root-' + namespace)
    originals[namespace + '.lean'] = top

lake_src = sdk / 'lake'
assert (lake_src / 'Lake').is_dir(), lake_src
run([driver, 'convert-native-tree', lake_src / 'Lake', source / 'Lake'], 'convert-Lake')
run([driver, 'convert-native', lake_src / 'Lake.lean', source / 'Lake.ps'], 'convert-root-Lake')
for p in (lake_src / 'Lake').rglob('*.lean'):
    originals['Lake/' + str(p.relative_to(lake_src / 'Lake')).replace(os.sep, '/')] = p
originals['Lake.lean'] = lake_src / 'Lake.lean'

run([driver, 'convert-native-tree', sdk / 'LeanExport', source / 'LeanExport'], 'convert-LeanExport')
for p in (sdk / 'LeanExport').rglob('*.lean'):
    originals['LeanExport/' + str(p.relative_to(sdk / 'LeanExport')).replace(os.sep, '/')] = p
for name in ['LeanChecker', 'LeanExport', 'LeanIR', 'Leanc', 'LakeMain']:
    original = (lake_src if name == 'LakeMain' else sdk) / (name + '.lean')
    run([driver, 'convert-native', original, source / (name + '.ps')], 'convert-root-' + name)
    originals[name + '.lean'] = original

manifest = json.loads((ROOT / 'compiler-source-inventory.json').read_text())
assert manifest['leanCommit'] == LEAN
assert len(originals) == manifest['count']
for entry in manifest['entries']:
    relative = entry['module'].replace('.', '/') + '.lean'
    original = sdk / entry['sdkPath']
    assert originals[relative] == original, entry
    data = original.read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert blob == entry['blob'], ('SDK source differs from exact Git blob', entry, blob)

run([driver, 'convert-native-tree', ROOT / 'PS0', source / 'PS0'], 'convert-PS0')
for p in (ROOT / 'PS0').rglob('*.lean'):
    originals['PS0/' + str(p.relative_to(ROOT / 'PS0')).replace(os.sep, '/')] = p
for name in ['PS0', 'PS0Main']:
    run([driver, 'convert-native', ROOT / (name + '.lean'), source / (name + '.ps')], 'convert-root-' + name)
    originals[name + '.lean'] = ROOT / (name + '.lean')

source_plans = {}
if args.source_plans:
    assert args.plan_source, 'the exact source-planner commit must be explicit'
    reports = [path for path in args.source_plans.rglob('evidence.json')
               if path.parent.name.startswith('corpus-source-plan-')]
    assert len(reports) == 1, reports
    report_path = reports[0]
    report = json.loads(report_path.read_text())
    assert report['source'] == args.plan_source
    assert report['lean_commit'] == LEAN
    assert report['inventory_sha256'] == digest(ROOT / 'compiler-source-inventory.json')
    assert report['count'] == manifest['count'] == len(report['modules'])
    assert report['status_counts'] == {'planned-unvalidated': manifest['count']}, report['status_counts']
    entries = {entry['module']: entry for entry in manifest['entries']}
    assert {item['module'] for item in report['modules']} == set(entries)
    for item in report['modules']:
        module = item['module']
        assert item['blob'] == entries[module]['blob']
        original = sdk / entries[module]['sdkPath']
        assert digest(original) == item['original_sha256']
        folder = report_path.parent / 'modules' / module
        target = source / Path(*module.split('.')).with_suffix('.ps')
        assert target.read_bytes() == (folder / 'original.ps').read_bytes()
        plan = json.loads((folder / 'plan.json').read_text())
        census = folder / 'native-census.json'
        assert digest(census) == item['census_sha256']
        raw = target.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == plan['source_sha256']
        cursor, chunks = 0, []
        for change in plan['edits']:
            assert cursor <= change['start'] <= change['end'] <= len(raw)
            assert raw[change['start']:change['end']].decode() == change['old']
            assert change['old'].count('\n') == change['new'].count('\n')
            chunks += [raw[cursor:change['start']], change['new'].encode()]
            cursor = change['end']
        chunks.append(raw[cursor:])
        converted = b''.join(chunks)
        assert converted == (folder / 'converted.ps').read_bytes()
        assert hashlib.sha256(converted).hexdigest() == item['converted_sha256'] == plan['result_sha256']
        target.write_bytes(converted)
        source_plans[module] = plan
    def missing_instance_view(commands):
        return any((command['headKind'] == 'Lean.Parser.Command.instance' and command['declaration'] is None)
                   or missing_instance_view(command.get('nestedCommands', [])) for command in commands)
    refreshed = []
    def refresh_plan(item):
        module = item['module']
        cached = report_path.parent / 'modules' / module
        original, census = cached / 'original.ps', cached / 'native-census.json'
        folder = evidence / 'current-source-plans' / module
        folder.mkdir(parents=True, exist_ok=False)
        if missing_instance_view(json.loads(census.read_text())['commands']):
            census = folder / 'native-census.json'
            run([driver, 'census-source', original, module, census], 'refresh-census-' + module)
            refreshed.append(module)
        target = source / Path(*module.split('.')).with_suffix('.ps')
        plan_file = folder / 'plan.json'
        run(['python3', 'tests/migrate-compiler-heads.py', census, original, target,
             '--plan', plan_file, '--allow-empty'], 'refresh-plan-' + module)
        plan = json.loads(plan_file.read_text())
        assert digest(target) == plan['result_sha256']
        return module, plan
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(refresh_plan, item) for item in report['modules']]
        for future in as_completed(futures):
            module, plan = future.result()
            source_plans[module] = plan
    self_relatives = sorted(set(originals) - {name.replace('.', '/') + '.lean' for name in entries})
    self_modules = [str(Path(relative).with_suffix('')).replace('/', '.') for relative in self_relatives]
    # Converted modern headers require matching modern dependency metadata.
    # This SDK-assisted preparation does not enter the final graph's build directory.
    self_metadata = work / 'self-native-metadata'
    run(['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceRoot=' + str(source),
         '-Kbootstrap=true', '-Kroots=PS0,PS0Main', '-KrootModule=PS0Main',
         '-Kdriver=' + str(driver), '-KmoduleNames=' + ','.join(self_modules),
         '-KprojectBuildDir=' + str(self_metadata), 'build', 'PS0Project'], 'self-native-metadata')
    self_env = {**os.environ, 'LEAN_PATH': str(self_metadata / 'lib/lean')}
    # The compiler's own modules must also enter the transformed graph.
    # Use their original native syntax and the same source planner, not a fallback.
    for relative in self_relatives:
        module = str(Path(relative).with_suffix('')).replace('/', '.')
        target = source / Path(relative).with_suffix('.ps')
        folder = evidence / 'self-source-plans' / module
        folder.mkdir(parents=True, exist_ok=False)
        original, census, converted, plan_file = [folder / name for name in
                                                ['original.ps', 'native-census.json', 'converted.ps', 'plan.json']]
        shutil.copy2(target, original)
        run([driver, 'census-source', original, module, census], 'self-census-' + module, env=self_env)
        run(['python3', 'tests/migrate-compiler-heads.py', census, original, converted,
             '--plan', plan_file, '--allow-empty'], 'self-plan-' + module)
        plan = json.loads(plan_file.read_text())
        assert digest(target) == plan['source_sha256']
        assert digest(converted) == plan['result_sha256']
        shutil.copy2(converted, target)
        source_plans[module] = plan
    assert len(source_plans) == len(originals)
    shutil.copytree(source, evidence / 'transformed-source')
    (evidence / 'source-plan-summary.json').write_text(json.dumps({
        'input_census_source': args.plan_source, 'planner_source': os.environ['PS0_SOURCE_SHA'],
        'refreshed_instance_censuses': sorted(refreshed), 'planner_evidence_sha256': digest(report_path),
        'module_count': len(source_plans), 'source_grammar': True,
        'definitions': sum(len(plan['declarations']) for plan in source_plans.values()),
        'grammar_migration_complete': False, 'verified_execution': False,
    }, indent=2) + '\n')

assert not list(source.rglob('*.lean'))
inputs = {}
for relative, original in sorted(originals.items()):
    target = source / Path(relative).with_suffix('.ps')
    module = str(Path(relative).with_suffix('')).replace('/', '.').replace(os.sep, '.')
    assert target.is_file(), target
    inputs[module] = {
        'original': str(original), 'ps': str(target),
        'original_sha256': digest(original), 'ps_sha256': digest(target),
        'body_mode': ('planned-ps-grammar' if args.source_plans else
                      'byte-identical' if original.read_bytes() == target.read_bytes() else 'native-header-adapter'),
    }
modules = work / 'modules.txt'
modules.write_text('\n'.join(sorted(inputs)) + '\n')
(evidence / 'input-inventory.json').write_text(json.dumps({
    'source_commit': os.environ['PS0_SOURCE_SHA'], 'lean_commit': LEAN,
    'stage_driver_sha256': digest(driver), 'module_count': len(inputs), 'inputs': inputs,
}, indent=2) + '\n')
print('PS0_COMPILER_PS_INPUTS: ' + str(len(inputs)) + '; byte_identical=' +
      str(sum(x['body_mode'] == 'byte-identical' for x in inputs.values())), flush=True)
baseline = json.loads(args.compare.read_text()) if args.compare else None
if baseline:
    assert digest(driver) == baseline['driver_sha256'], 'stage driver differs from the uploaded stage-one executable'
    assert {k: v['ps_sha256'] for k, v in inputs.items()} == {
        k: v['ps_sha256'] for k, v in baseline['inputs'].items()}, 'stage inputs changed'

build = work / 'artifacts'
shutil.copytree(sysroot / 'include', build / 'include')
build_command = ['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceRoot=' + str(source),
     '-Kbootstrap=true',
     *(['-KsourceGrammar=true'] if args.source_plans else []),
     '-Kroots=Init,Std,Lean,Lake,LeanChecker,LeanExport,LeanIR,Leanc,LakeMain,PS0,PS0Main', '-KrootModule=PS0Main',
     '-Kdriver=' + str(driver), '-KmoduleNames=' + ','.join(sorted(inputs)),
     '-KlinkMap=' + str(evidence / 'compiler-link.map'),
     '-KprojectBuildDir=' + str(build), 'build', 'PS0Project:static', 'ps0project']
try:
    run(build_command, 'compiler-build')
except Exception:
    completed = []
    for module in inputs:
        rel = Path(*module.split('.'))
        census = build / 'lib/lean' / rel.with_suffix('.ilean.ps0-source-census.json')
        if census.is_file():
            retained = evidence / 'partial-source-census' / rel.with_suffix('.json')
            retained.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(census, retained)
            completed.append(module)
    (evidence / 'failed-build.json').write_text(json.dumps({
        'source_commit': os.environ['PS0_SOURCE_SHA'], 'lean_commit': LEAN,
        'module_count': len(inputs), 'source_grammar': bool(args.source_plans),
        'completed_census_modules': sorted(completed), 'status': 'FAILED',
        'grammar_migration_complete': False, 'verified_execution': False,
    }, indent=2) + '\n')
    raise

outputs = {}
for module, data in inputs.items():
    rel = Path(*module.split('.'))
    receipt = json.loads((build / 'ps0-inputs' / (module + '.json')).read_text())
    assert receipt['source'] == data['ps'], (module, receipt)
    setup = json.loads((build / 'ir' / rel.with_suffix('.setup.json')).read_text())
    assert setup['options']['interpreter.prefer_native'] is False, (module, setup['options'])
    if args.source_plans:
        assert setup['options']['ps0.sourceGrammar'] is True, (module, setup['options'])
        census_file = build / 'lib/lean' / rel.with_suffix('.ilean.ps0-source-census.json')
        observed = json.loads(census_file.read_text())
        def declarations(commands):
            for command in commands:
                if command['declaration'] is not None:
                    yield command['declaration']
                yield from declarations(command.get('nestedCommands', []))
        mapped = list(declarations(observed['commands']))
        productions = {'function': 'PS0.StandardAdapters.ps0StandardFunction',
                       'const': 'PS0.StandardAdapters.ps0StandardConst',
                       'def': 'PS0.StandardAdapters.ps0StandardDef'}
        definition_kinds = set(productions.values()) | {'Lean.Parser.Command.definition'}
        definitions = [declaration for declaration in mapped if declaration['production'] in definition_kinds]
        assert len(definitions) == len(source_plans[module]['strategies']), module
        for strategy, declaration in zip(source_plans[module]['strategies'], definitions):
            assert declaration['sourceName'] == strategy['sourceName'], (module, strategy, declaration)
            assert declaration['mode'] == 'mapped-ps'
            assert declaration['production'] == productions[strategy['targetKeyword']], declaration
        assert not any(declaration['mode'] == 'native-compatible' for declaration in mapped), (module, mapped)
    olean = build / 'lib/lean' / rel.with_suffix('.olean')
    cfile = build / 'ir' / rel.with_suffix('.c')
    assert olean.is_file() and cfile.is_file(), module
    outputs[module] = {'olean_sha256': digest(olean), 'c_sha256': digest(cfile)}

migrated = build / 'bin/ps0project'
result = {
    'schema': 'ps0-compiler-source-migration/1', 'source_commit': os.environ['PS0_SOURCE_SHA'],
    'lean_commit': LEAN, 'module_count': len(inputs), 'inputs': inputs, 'outputs': outputs,
    'driver_sha256': digest(migrated), 'verified_execution': False,
    'bootstrap_package_identity': None,
    'stage_lean_options': {'interpreter.prefer_native': False,
                           **({'ps0.sourceGrammar': True} if args.source_plans else {})},
    'runtime_smoke': 'PENDING',
    'runtime_grammar_host': {'status': 'PENDING'},
    'lean_header_sha256': digest(build / 'include/lean/lean.h'),
    'scope': ('All pinned upstream and PS0 source plans compiled with PS grammar enabled' if args.source_plans else
              'All pinned src/**/*.lean Git blobs and repository PS0 modules compiled from .ps with native headers'),
    'grammar_migration_complete': False,
}
shutil.copy2(migrated, evidence / 'migrated-ps0')
(evidence / 'migration.json').write_text(json.dumps(result, indent=2) + '\n')
migrated_env = {**os.environ, 'LEAN_PATH': str(build / 'lib/lean')}
run([migrated, 'environment'], 'migrated-environment', env=migrated_env)
assert LEAN in (evidence / 'migrated-environment.log').read_text()
run([migrated, 'check', ROOT / 'tests/project/Demo/Words.ps'], 'migrated-source-check', env=migrated_env)
result['runtime_smoke'] = 'PASS'
(evidence / 'migration.json').write_text(json.dumps(result, indent=2) + '\n')
host_tag = '-compiler-built'
run(['python3', 'tests/run-relocated-grammar.py'], 'migrated-grammar-host', env={
    **migrated_env, 'PS0_PACKAGE_DRIVER': str(migrated),
    'PS0_PACKAGE_METADATA': str(build / 'lib/lean'), 'PS0_PACKAGE_TAG': host_tag,
})
host_file = ROOT / 'build' / ('relocated-grammar-' + os.environ['GITHUB_RUN_ID'] + host_tag) / 'evidence.json'
host = json.loads(host_file.read_text())
assert host['source'] == result['source_commit']
assert host['driver_sha256'] == result['driver_sha256']
assert all(v['source_sha256'] == v['published_sha256'] for v in host['host_metadata'].values())
shutil.copy2(host_file, evidence / 'native-grammar-host.json')
result['runtime_grammar_host'] = {
    'status': 'PASS', 'driver_sha256': host['driver_sha256'],
    'evidence_sha256': digest(host_file), 'metadata_files': len(host['host_metadata']),
    'provenance': 'fresh all-.ps compiler output metadata; explicit pinned Lean SDK dependencies',
}
print('PS0_PS_BUILT_COMPILER_GRAMMAR_HOST: PASS; metadata_files=' + str(len(host['host_metadata'])), flush=True)
if baseline:
    changed_c = [m for m in outputs if outputs[m]['c_sha256'] != baseline['outputs'][m]['c_sha256']]
    changed_olean = [m for m in outputs if outputs[m]['olean_sha256'] != baseline['outputs'][m]['olean_sha256']]
    result['fixed_point'] = {'changed_c': changed_c, 'changed_olean': changed_olean}
    (evidence / 'migration.json').write_text(json.dumps(result, indent=2) + '\n')
    assert not changed_c and not changed_olean, result['fixed_point']
    print('PS0_COMPILER_PS_FIXED_POINT: PASS', flush=True)
else:
    (evidence / 'migration.json').write_text(json.dumps(result, indent=2) + '\n')
print('PS0_COMPILER_PS_SOURCE: PASS; modules=' + str(len(inputs)), flush=True)
