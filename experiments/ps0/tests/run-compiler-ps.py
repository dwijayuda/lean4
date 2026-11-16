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
from native_census_cache import NativeCensusCache, needs_head_lexical_refresh, needs_initializer_refresh, needs_data_refresh, OPERATOR_SCOPE
from native_compiler_prefix import source_identity_counts, verify_compiler_prefix
from canonical_compiler_sources import definition_digest, read_canonical_corpus, stage_canonical_corpus
from compiler_build_checkpoint import (
    compiler_part_targets, graph_run_id as checkpoint_graph_run_id,
    seal as seal_checkpoint, verify as verify_checkpoint,
)

parser = argparse.ArgumentParser()
parser.add_argument('--driver', type=Path)
parser.add_argument('--compare', type=Path)
parser.add_argument('--source-plans', type=Path)
parser.add_argument('--plan-source')
parser.add_argument('--native-censuses', type=Path)
parser.add_argument('--census-source')
parser.add_argument('--prepare-only', action='store_true')
parser.add_argument('--stage-artifact', type=Path)
parser.add_argument('--stage-source')
parser.add_argument('--canonical-corpus', action='store_true', help='Build the tracked .ps compiler corpus')
parser.add_argument('--bootstrap-artifact', type=Path, help='Verified previous compiler used to seed canonical stage one')
parser.add_argument('--bootstrap-source')
parser.add_argument('--build-slice', choices=['base', 'compiler', 'finish'], default='finish')
parser.add_argument('--resume-build', type=Path)
parser.add_argument('--checkpoint-run-id', help='Producer run ID when resuming across workflows')
parser.add_argument('--compiler-part', choices=['early', 'middle', 'late'])
parser.add_argument('--compiler-target-plan', type=Path)
parser.add_argument('--workspace', type=Path, help='Pinned compiler source checkout for a separately pinned harness')
args = parser.parse_args()
source_grammar = bool(args.source_plans or args.canonical_corpus)
if bool(args.bootstrap_artifact) != bool(args.bootstrap_source):
    parser.error('--bootstrap-artifact and --bootstrap-source must be supplied together')
if args.bootstrap_artifact and not args.canonical_corpus:
    parser.error('--bootstrap-artifact requires --canonical-corpus')
if args.canonical_corpus and (args.source_plans or args.plan_source or args.native_censuses or args.prepare_only or
                              args.driver or args.compare or bool(args.bootstrap_artifact) == bool(args.stage_artifact)):
    parser.error('canonical corpus requires exactly one verified bootstrap or previous-stage artifact')
if bool(args.native_censuses) != bool(args.census_source):
    parser.error('--native-censuses and --census-source must be supplied together')
if (args.native_censuses or args.prepare_only) and not args.source_plans:
    parser.error('native census reuse and preparation-only require --source-plans')
if bool(args.stage_artifact) != bool(args.stage_source):
    parser.error('--stage-artifact and --stage-source must be supplied together')
if args.stage_artifact and (args.driver or args.compare or args.prepare_only or not source_grammar):
    parser.error('verified stage artifact requires full PS grammar build without separate driver/compare/prepare-only options')
if args.resume_build and (args.prepare_only or args.build_slice == 'base' or not source_grammar):
    parser.error('checkpoint resume requires PS grammar compiler/finish slice')
if args.build_slice == 'compiler' and not args.resume_build:
    parser.error('compiler slice requires verified base checkpoint')
if args.build_slice != 'finish' and (args.prepare_only or not source_grammar):
    parser.error('partial slices require PS grammar and cannot be preparation-only')
if args.checkpoint_run_id and not args.resume_build:
    parser.error('--checkpoint-run-id requires --resume-build')
if bool(args.compiler_part) != bool(args.compiler_target_plan) or (args.compiler_part and args.build_slice != 'compiler'):
    parser.error('compiler partitions require --compiler-part and --compiler-target-plan in the compiler slice')
ROOT = args.workspace.resolve() if args.workspace else Path(__file__).resolve().parents[1]
os.chdir(ROOT)
target_plan = json.loads(args.compiler_target_plan.read_text()) if args.compiler_target_plan else None
stage = verify_compiler_prefix(args.stage_artifact, args.stage_source) if args.stage_artifact else None
bootstrap = verify_compiler_prefix(args.bootstrap_artifact, args.bootstrap_source) if args.bootstrap_artifact else None
if stage:
    args.driver, args.compare = Path(stage['driver']), Path(stage['migration'])
elif bootstrap:
    args.driver = Path(bootstrap['driver'])
baseline = json.loads(args.compare.read_text()) if args.compare else None
driver = (args.driver or ROOT / '.lake/build/bin/ps0').resolve()
evidence = ROOT / 'build/compiler-evidence'
evidence.mkdir(parents=True, exist_ok=True)
if stage:
    (evidence / 'stage-prefix-verification.json').write_text(json.dumps(stage, indent=2) + '\n')
    # GitHub artifact extraction does not preserve executable permission bits.
    driver.chmod(driver.stat().st_mode | 0o100)
if bootstrap:
    (evidence / 'bootstrap-prefix-verification.json').write_text(json.dumps(bootstrap, indent=2) + '\n')
    driver.chmod(driver.stat().st_mode | 0o100)
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
checkpoint_history = []
run_id = os.environ.get('GITHUB_RUN_ID', str(os.getpid()))
graph_run_id = baseline.get('native_lake_graph_run_id', run_id) if baseline else run_id
checkpoint_parent_run_id = args.checkpoint_run_id or run_id
if args.resume_build:
    previous = 'base' if args.build_slice == 'compiler' and args.compiler_part in (None, 'early') else 'compiler'
    checkpoint = verify_checkpoint(ROOT, args.resume_build, source=os.environ['PS0_SOURCE_SHA'],
        phase=previous, run_id=checkpoint_parent_run_id, driver=driver)
    state = checkpoint['state']
    if args.compiler_part == 'middle':
        assert state.get('compiler_part') == 'early', 'middle partition requires early checkpoint'
    elif args.compiler_part == 'late':
        expected_part = 'middle' if isinstance(target_plan, dict) else 'early'
        assert state.get('compiler_part') == expected_part, 'late partition has an unexpected predecessor'
    elif args.build_slice == 'finish':
        assert state.get('compiler_part') in (None, 'late'), 'final link requires every compiler partition'
    graph_run_id = checkpoint_graph_run_id(state)
    checkpoint_history = state['history']
    print('PS0_NATIVE_LAKE_CHECKPOINT_VERIFIED: ' + previous +
          '; producer_run=' + checkpoint_parent_run_id + '; graph_run=' + graph_run_id +
          '; files=' + str(len(checkpoint['files'])), flush=True)
assert graph_run_id.isascii() and graph_run_id.isdecimal(), graph_run_id
work = ROOT / 'build' / ('compiler-ps-' + graph_run_id)
source = work / 'src'
if args.canonical_corpus:
    catalog = ROOT / 'compiler-canonical-sources.json'
    pinned_inventory = json.loads((ROOT / 'compiler-source-inventory.json').read_text())
    canonical = read_canonical_corpus(ROOT.parent.parent, catalog, pinned_inventory)
    assert len(canonical) == 2569
if args.resume_build:
    inputs = json.loads((evidence / 'input-inventory.json').read_text())['inputs']
    assert len(inputs) == 2569
    source_plans = {}
    for module in inputs:
        if args.canonical_corpus:
            source_plans[module] = canonical[module]
            assert inputs[module]['canonical_path'] == canonical[module]['path']
            assert inputs[module]['ps_sha256'] == canonical[module]['ps_sha256']
        else:
            candidates = [evidence / name / module / 'plan.json'
                          for name in ['current-source-plans', 'self-source-plans']]
            plans = [path for path in candidates if path.is_file()]
            assert len(plans) == 1, (module, plans)
            source_plans[module] = json.loads(plans[0].read_text())
        assert digest(source / Path(*module.split('.')).with_suffix('.ps')) == inputs[module]['ps_sha256']
    assert not list(source.rglob('*.lean'))
    identity_counts = source_identity_counts(inputs)
elif args.canonical_corpus:
    source_plans = canonical
    inputs = stage_canonical_corpus(ROOT.parent.parent, canonical, source)
    shutil.copytree(source, evidence / 'transformed-source')
    shutil.copy2(catalog, evidence / 'canonical-source-catalog.json')
    identity_counts = source_identity_counts(inputs)
    (work / 'modules.txt').write_text('\n'.join(sorted(inputs)) + '\n')
    (evidence / 'input-inventory.json').write_text(json.dumps({
        'source_commit': os.environ['PS0_SOURCE_SHA'], 'lean_commit': LEAN,
        'stage_driver_sha256': digest(driver), 'module_count': len(inputs), 'inputs': inputs,
        'source_identity_counts': identity_counts,
    }, indent=2) + '\n')
    (evidence / 'source-plan-summary.json').write_text(json.dumps({
        'input_mode': 'canonical-git', 'catalog_sha256': digest(catalog),
        'planner_source': os.environ['PS0_SOURCE_SHA'], 'module_count': len(inputs), 'source_grammar': True,
        'stage_compiler': 'retained-ps-built-prefix' if stage else 'retained-audited-bootstrap-prefix',
        'stage_driver_sha256': digest(driver),
    }, indent=2) + '\n')
    print('PS0_COMPILER_CANONICAL_INPUTS: ' + str(len(inputs)) + '; catalog_sha256=' + digest(catalog), flush=True)
else:
    source.mkdir(parents=True, exist_ok=False)
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
        def missing_declaration_view(commands):
            return any((command['headKind'] in ['Lean.Parser.Command.instance', 'Lean.Parser.Command.example']
                        and command['declaration'] is None)
                       or missing_declaration_view(command.get('nestedCommands', [])) for command in commands)
        refreshed = []
        reused_censuses = []
        native_cache = (NativeCensusCache(args.native_censuses, args.census_source, LEAN)
                        if args.native_censuses else None)
        def refresh_plan(item):
            module = item['module']
            cached = report_path.parent / 'modules' / module
            original, census = cached / 'original.ps', cached / 'native-census.json'
            folder = evidence / 'current-source-plans' / module
            folder.mkdir(parents=True, exist_ok=False)
            captured = json.loads(census.read_text())
            if (needs_head_lexical_refresh(captured) or needs_initializer_refresh(captured) or needs_data_refresh(captured) or
                    missing_declaration_view(captured['commands']) or
                    captured.get('operatorDescriptorScope') != OPERATOR_SCOPE):
                prior = (native_cache.find(module, original.read_bytes(), digest(sdk / entries[module]['sdkPath']))
                         if native_cache else None)
                if prior is not None and needs_head_lexical_refresh(json.loads(prior.read_text())):
                    prior = None
                census = folder / 'native-census.json'
                if prior is None:
                    run([driver, 'census-source', original, module, census], 'refresh-census-' + module)
                    refreshed.append(module)
                else:
                    shutil.copy2(prior, census)
                    reused_censuses.append({'module': module, 'census_sha256': digest(census)})
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
        if stage:
            # Every PS0 import during next-stage planning uses the verified PS-built host.
            self_metadata = Path(stage['metadata'])
        else:
            # Converted modern headers require matching modern dependency metadata.
            # This isolated stage-one preparation never enters the final graph directory.
            native_metadata = work / 'self-native-metadata'
            run(['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceRoot=' + str(source),
                 '-Kbootstrap=true', '-Kroots=PS0,PS0Main', '-KrootModule=PS0Main',
                 '-Kdriver=' + str(driver), '-KmoduleNames=' + ','.join(self_modules),
                 '-KprojectBuildDir=' + str(native_metadata), 'build', 'PS0Project'], 'self-native-metadata')
            self_metadata = native_metadata / 'lib/lean'
        self_env = {**os.environ, 'LEAN_PATH': str(self_metadata)}
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
            'refreshed_declaration_censuses': sorted(refreshed), 'planner_evidence_sha256': digest(report_path),
            'reused_native_censuses': sorted(reused_censuses, key=lambda item: item['module']),
            'native_census_cache': native_cache.provenance if native_cache else None,
            'module_count': len(source_plans), 'source_grammar': True,
            'self_census_metadata': {
                'mode': 'retained-ps-built-prefix' if stage else 'isolated-sdk-assisted-preparation',
                'path': str(self_metadata), 'driver_sha256': digest(driver),
                'stage_source': stage['source'] if stage else None,
            },
            'definitions': sum(len(plan['declarations']) for plan in source_plans.values()),
            'data_declarations': sum(plan.get('data_declarations', 0) for plan in source_plans.values()),
            'initialization_commands': sum(plan.get('initialization_commands', 0) for plan in source_plans.values()),
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
    identity_counts = source_identity_counts(inputs)
    (evidence / 'input-inventory.json').write_text(json.dumps({
        'source_commit': os.environ['PS0_SOURCE_SHA'], 'lean_commit': LEAN,
        'stage_driver_sha256': digest(driver), 'module_count': len(inputs), 'inputs': inputs,
        'source_identity_counts': identity_counts,
    }, indent=2) + '\n')
    print('PS0_COMPILER_PS_INPUTS: ' + str(len(inputs)) + '; ' +
          '; '.join(key + '=' + str(value) for key, value in identity_counts.items() if key != 'total_inputs'), flush=True)
    if args.prepare_only:
        (evidence / 'preparation-only.json').write_text(json.dumps({
            'source_commit': os.environ['PS0_SOURCE_SHA'], 'lean_commit': LEAN,
            'module_count': len(inputs), 'source_grammar': True,
            'source_identity_counts': identity_counts,
            'scope': 'prepared transformed source and plans only; target dependency graph is not compiled',
            'compiled_graph': False, 'grammar_migration_complete': False, 'verified_execution': False,
        }, indent=2) + '\n')
        print('PS0_COMPILER_PS_PREPARATION_ONLY: ' + str(len(inputs)), flush=True)
        raise SystemExit(0)
if baseline:
    assert baseline.get('native_lake_graph_run_id', graph_run_id) == graph_run_id, 'fixed-point graph path changed'
    assert digest(driver) == baseline['driver_sha256'], 'stage driver differs from the uploaded stage-one executable'
    assert {k: (v['original_sha256'], v['ps_sha256']) for k, v in inputs.items()} == {
        k: (v['original_sha256'], v['ps_sha256']) for k, v in baseline['inputs'].items()}, 'stage original/PS source identities changed'

build = work / 'artifacts'
if not args.resume_build:
    shutil.copytree(sysroot / 'include', build / 'include')
build_command = ['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceRoot=' + str(source),
     '-Kbootstrap=true',
     *(['-KsourceGrammar=true'] if source_grammar else []),
     '-Kroots=Init,Std,Lean,Lake,LeanChecker,LeanExport,LeanIR,Leanc,LakeMain,PS0,PS0Main', '-KrootModule=PS0Main',
     '-Kdriver=' + str(driver), '-KmoduleNames=' + ','.join(sorted(inputs)),
     '-KlinkMap=' + str(evidence / 'compiler-link.map'),
     '-KprojectBuildDir=' + str(build), 'build']
if args.build_slice == 'finish':
    build_command += ['PS0Project:static', 'ps0project']
else:
    namespaces = ['Init', 'Std'] if args.build_slice == 'base' else ['Lean']
    selected = [module for module in sorted(inputs)
                if any(module == name or module.startswith(name + '.') for name in namespaces)]
    if args.compiler_part:
        prior_targets = sorted(module for phase in checkpoint_history if phase['phase'] == 'compiler'
                               for module in phase['targets'])
        selected = compiler_part_targets(selected, target_plan, args.compiler_part, prior_targets)
    assert selected
    # Native module facets own dependency scheduling, compilation and traces.
    # The package, complete module inventory, options and workspace stay fixed.
    build_command += ['+' + module + ':c.o' for module in selected]
try:
    log_name = 'compiler-build'
    if args.build_slice != 'finish':
        log_name += '-' + (args.compiler_part or args.build_slice)
    run(build_command, log_name, timeout=19800)
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
        'module_count': len(inputs), 'source_grammar': source_grammar,
        'completed_census_modules': sorted(completed), 'status': 'FAILED',
        'grammar_migration_complete': False, 'verified_execution': False,
    }, indent=2) + '\n')
    raise

if args.build_slice != 'finish':
    history = checkpoint_history + [dict(phase=args.build_slice, targets=selected,
        compiler_part=args.compiler_part, producer_run_id=run_id,
        source_commit=os.environ['PS0_SOURCE_SHA'], driver_sha256=digest(driver),
        options={'interpreter.prefer_native': False, 'ps0.sourceGrammar': True})]
    state = dict(source_commit=os.environ['PS0_SOURCE_SHA'], lean_commit=LEAN,
        run_id=run_id, graph_run_id=graph_run_id, phase=args.build_slice, compiler_part=args.compiler_part,
        driver=str(driver), driver_sha256=digest(driver), source_grammar=True,
        work=work.relative_to(ROOT).as_posix(), history=history)
    sealed = seal_checkpoint(ROOT, ROOT / 'build/compiler-checkpoint.json', state,
        ['.lake', work.relative_to(ROOT).as_posix(), evidence.relative_to(ROOT).as_posix()])
    print('PS0_NATIVE_LAKE_BUILD_SLICE: ' + args.build_slice + '; targets=' + str(len(selected)) +
          '; checkpoint_files=' + str(len(sealed['files'])) + '; full compiler qualification PENDING', flush=True)
    raise SystemExit(0)

outputs = {}
for module, data in inputs.items():
    rel = Path(*module.split('.'))
    receipt = json.loads((build / 'ps0-inputs' / (module + '.json')).read_text())
    assert receipt['source'] == data['ps'], (module, receipt)
    setup = json.loads((build / 'ir' / rel.with_suffix('.setup.json')).read_text())
    assert setup['options']['interpreter.prefer_native'] is False, (module, setup['options'])
    if source_grammar:
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
        if args.canonical_corpus:
            sequence = [(declaration['sourceName'], keyword) for declaration in definitions
                        for keyword, kind in productions.items() if declaration['production'] == kind]
            assert len(sequence) == len(definitions) == canonical[module]['definition_count'], module
            assert definition_digest(sequence) == canonical[module]['definition_sha256'], module
            assert all(declaration['mode'] == 'mapped-ps' for declaration in definitions), module
        else:
            assert len(definitions) == len(source_plans[module]['strategies']), module
            for strategy, declaration in zip(source_plans[module]['strategies'], definitions):
                assert declaration['sourceName'] == strategy['sourceName'], (module, strategy, declaration)
                assert declaration['mode'] == 'mapped-ps'
                assert declaration['production'] == productions[strategy['targetKeyword']], declaration
        assert not any(declaration['mode'] == 'native-compatible' for declaration in mapped), (module, mapped)
        def operand_captures(commands, field):
            for command in commands:
                if command.get(field) is not None:
                    yield command[field]
                yield from operand_captures(command.get('nestedCommands', []), field)
        for field, counter in [('dataDeclaration', 'data_declarations'),
                               ('initialization', 'initialization_commands')]:
            captures = list(operand_captures(observed['commands'], field))
            assert len(captures) == source_plans[module].get(counter, 0), (module, field)
            assert all(capture['mode'] == 'mapped-ps' for capture in captures), (module, field)
        retained = evidence / 'source-census' / rel.with_suffix('.json')
        retained.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(census_file, retained)
    olean = build / 'lib/lean' / rel.with_suffix('.olean')
    cfile = build / 'ir' / rel.with_suffix('.c')
    assert olean.is_file() and cfile.is_file(), module
    outputs[module] = {'olean_sha256': digest(olean), 'c_sha256': digest(cfile)}

migrated = build / 'bin/ps0project'
result = {
    'schema': 'ps0-compiler-source-migration/1', 'source_commit': os.environ['PS0_SOURCE_SHA'],
    'lean_commit': LEAN, 'module_count': len(inputs), 'inputs': inputs, 'outputs': outputs,
    'source_identity_counts': identity_counts,
    'driver_sha256': digest(migrated), 'verified_execution': False,
    'bootstrap_package_identity': None,
    'compiler_build_timeout_seconds': 19800,
    'native_lake_graph_run_id': graph_run_id,
    'build_harness_source': os.environ.get('PS0_BUILD_HARNESS_SHA', os.environ['PS0_SOURCE_SHA']),
    'native_lake_build_slices': checkpoint_history + [{'phase': 'finish', 'targets': ['PS0Project:static', 'ps0project']}],
    'stage_lean_options': {'interpreter.prefer_native': False,
                           **({'ps0.sourceGrammar': True} if source_grammar else {})},
    'runtime_smoke': 'PENDING',
    'runtime_grammar_host': {'status': 'PENDING'},
    'lean_header_sha256': digest(build / 'include/lean/lean.h'),
    'source_input_mode': 'canonical-git' if args.canonical_corpus else 'generated',
    'scope': ('All tracked compiler .ps sources compiled with PS grammar enabled' if args.canonical_corpus else
              'All pinned upstream and PS0 source plans compiled with PS grammar enabled' if args.source_plans else
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
# A subsequent compiler stage needs the actual PS-built host metadata beside
# this exact executable. Retain the already exercised native prefix, rather
# than replacing its metadata with an SDK-assisted rebuild in another runner.
prefix = evidence / 'compiler-prefix'
shutil.copytree(host_file.parent / 'prefix', prefix)
assert digest(prefix / 'bin/ps0') == result['driver_sha256']
for relative, hashes in host['host_metadata'].items():
    assert digest(prefix / 'lib/lean' / relative) == hashes['source_sha256']
result['compiler_prefix'] = {
    'driver': 'compiler-prefix/bin/ps0', 'metadata': 'compiler-prefix/lib/lean',
    'driver_sha256': result['driver_sha256'],
    'metadata_sha256': {relative: hashes['source_sha256']
                        for relative, hashes in host['host_metadata'].items()},
    'dependencies': 'explicit pinned Lean SDK; PS0 metadata is the actual all-PS graph output',
}
(prefix / 'compiler-prefix.json').write_text(json.dumps({
    'schema': 'ps0-compiler-prefix/1', 'source_commit': result['source_commit'], 'lean_commit': LEAN,
    **result['compiler_prefix'], 'verified_execution': False,
}, indent=2) + '\n')
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
