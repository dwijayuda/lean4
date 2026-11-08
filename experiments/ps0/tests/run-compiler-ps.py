#!/usr/bin/env python3
"""Compile the pinned Lean/Init/Std/Lake and PS0 source forest from .ps files."""
from pathlib import Path
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

assert not list(source.rglob('*.lean'))
inputs = {}
for relative, original in sorted(originals.items()):
    target = source / Path(relative).with_suffix('.ps')
    module = str(Path(relative).with_suffix('')).replace('/', '.').replace(os.sep, '.')
    assert target.is_file(), target
    inputs[module] = {
        'original': str(original), 'ps': str(target),
        'original_sha256': digest(original), 'ps_sha256': digest(target),
        'body_mode': 'byte-identical' if original.read_bytes() == target.read_bytes() else 'native-header-adapter',
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
run(['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceRoot=' + str(source),
     '-Kbootstrap=true',
     '-Kroots=Init,Std,Lean,Lake,LeanChecker,LeanExport,LeanIR,Leanc,LakeMain,PS0,PS0Main', '-KrootModule=PS0Main',
     '-Kdriver=' + str(driver), '-KmoduleNames=' + ','.join(sorted(inputs)),
     '-KlinkMap=' + str(evidence / 'compiler-link.map'),
     '-KprojectBuildDir=' + str(build), 'build', 'PS0Project:static', 'ps0project'], 'compiler-build')

outputs = {}
for module, data in inputs.items():
    rel = Path(*module.split('.'))
    receipt = json.loads((build / 'ps0-inputs' / (module + '.json')).read_text())
    assert receipt['source'] == data['ps'], (module, receipt)
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
    'runtime_smoke': 'PENDING',
    'lean_header_sha256': digest(build / 'include/lean/lean.h'),
    'scope': 'All pinned src/**/*.lean Git blobs and repository PS0 modules compiled from .ps with native headers',
}
shutil.copy2(migrated, evidence / 'migrated-ps0')
(evidence / 'migration.json').write_text(json.dumps(result, indent=2) + '\n')
migrated_env = {**os.environ, 'LEAN_PATH': str(build / 'lib/lean')}
run([migrated, 'environment'], 'migrated-environment', env=migrated_env)
assert LEAN in (evidence / 'migrated-environment.log').read_text()
run([migrated, 'check', ROOT / 'tests/project/Demo/Words.ps'], 'migrated-source-check', env=migrated_env)
result['runtime_smoke'] = 'PASS'
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
