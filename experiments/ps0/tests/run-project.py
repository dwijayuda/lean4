#!/usr/bin/env python3
"""Qualify recursive .ps modules using Lake's native module and link facets."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
WORK = ROOT / 'build' / ('project-test-' + os.environ.get('GITHUB_RUN_ID', str(os.getpid())))
WORK.mkdir(parents=True, exist_ok=False)
src = WORK / 'src'
shutil.copytree(ROOT / 'tests/project', src)
driver = WORK / 'ps0-driver'
shutil.copy2(ROOT / '.lake/build/bin/ps0', driver)

def run(args, ok=True, timeout=600):
    r = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=timeout)
    print(r.stdout, end='', flush=True)
    assert (r.returncode == 0) == ok, (args, r.returncode)
    return r.stdout

def build(module='Demo.Main', ok=True):
    return run(['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceRoot=' + str(src),
                '-Kroots=Demo,NativeSupport,Bootstrap,Cycle,Leak', '-KrootModule=' + module,
                '-Kdriver=' + str(driver), 'build', 'ps0project'], ok=ok)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

build()
exe = ROOT / '.lake/project/bin/ps0project'
assert 'PS0_PROJECT:42:7:2' in run([exe, 'a', 'b'])
records = list((ROOT / '.lake/project/ps0-inputs').rglob('*.json'))
selected = [json.loads(p.read_text()) for p in records]
assert any(x['module'] == 'Demo.Notation' and x['source'].endswith('.ps') for x in selected)
maps = list((ROOT / '.lake/project/lib/lean').rglob('*.ilean.ps0-source-map.json'))
assert maps, 'native Lake compilation must retain source origin sidecars'
for path in maps:
    mapping = json.loads(path.read_text())
    original = Path(mapping['file']).read_bytes()
    prepared = mapping['source'].encode()
    recovered = b''.join(prepared[s['preparedStart']:s['preparedEnd']]
                         for s in mapping['segments'] if s['kind'] == 'original')
    assert recovered == original
print('PS0_PROJECT_SOURCE_ORIGINS: PASS', flush=True)
before = (sha(exe), exe.stat().st_mtime_ns)
build()
assert before == (sha(exe), exe.stat().st_mtime_ns)
print('PS0_PROJECT_RECURSIVE_META_AND_WARM: PASS', flush=True)

old_inputs = {x['module']: x['input_hash'] for x in selected}
with driver.open('ab') as binary:
    binary.write(b'PS0_DRIVER_TRACE_INVALIDATION')
r = build()
new_inputs = {json.loads(p.read_text())['module']: json.loads(p.read_text())['input_hash'] for p in records}
assert all(new_inputs[m] != h for m, h in old_inputs.items())
assert 'Built Demo.Words' in r
assert 'PS0_PROJECT:42:7:0' in run([exe])
print('PS0_PROJECT_DRIVER_INVALIDATION: PASS', flush=True)

words = src / 'Demo/Words.ps'
words.write_text(words.read_text().replace('x + y', 'x + y + 1').replace('= 3 := by rfl', '= 4 := by rfl', 1))
library = src / 'Demo/Library.ps'
library.write_text(library.read_text().replace('= 42 := by rfl', '= 45 := by rfl'))
build()
assert 'PS0_PROJECT:45:7:0' in run([exe])
native = src / 'NativeSupport.lean'
native.write_text(native.read_text().replace(':= 7', ':= 9'))
build()
assert 'PS0_PROJECT:45:9:0' in run([exe])
print('PS0_PROJECT_TRANSITIVE_INVALIDATION: PASS', flush=True)

out = WORK / 'published'
run(['lake', 'exe', 'ps0', 'build-project', src, 'Demo.Main', out])
assert 'PS0_PROJECT:45:9:0' in run([out / 'ps0project'])
saved = sha(out / 'ps0project')
run(['lake', 'exe', 'ps0', 'build-project', src, 'Demo.Main', out], ok=False)
assert saved == sha(out / 'ps0project')

bootstrap = src / 'Bootstrap.ps'
bootstrap.write_text('module\nprelude\naxiom marker : Sort 1\n')
header = json.loads(run([driver, 'lake-header', bootstrap]))
assert header['imports'] == [] and header['isModule'] is True
bootstrap.write_text('module\nprelude\ndef bad := Nat.zero\n')
r = run([driver, 'check', bootstrap], ok=False)
assert 'Nat.zero' in r
print('PS0_PROJECT_PRELUDE_NO_HIDDEN_IMPORTS: PASS', flush=True)

(src / 'NoMain.ps').write_text('const value: Nat := 42\n')
missing_main = WORK / 'no-main'
r = run(['lake', 'exe', 'ps0', 'build-project', src, 'NoMain', missing_main], ok=False)
assert 'PS0-NATIVE-MAIN' in r and not missing_main.exists()
print('PS0_PROJECT_LOCAL_ENTRY: PASS', flush=True)

collision = src / 'Demo/Words.lean'
collision.write_text('def wrongSource : Nat := 100\n')
r = build(ok=False)
assert 'PS0-SOURCE-COLLISION' in r
collision.unlink()
(src / 'Cycle').mkdir()
(src / 'Cycle/A.ps').write_text('import Cycle.B\ndef main : IO Unit := pure ()\n')
(src / 'Cycle/B.ps').write_text('import Cycle.A\n')
r = build('Cycle.A', ok=False)
assert 'cycle' in r.lower()
(src / 'Leak').mkdir()
(src / 'Leak/Private.ps').write_text('module\nprivate def hidden : Nat := 7\n')
(src / 'Leak/Main.ps').write_text('import Leak.Private\ndef main : IO Unit := IO.println hidden\n')
run(['lake', 'exe', 'ps0', 'build-project', src, 'Leak.Main', WORK / 'private-refused'], ok=False)
assert not (WORK / 'private-refused').exists()
print('PS0_PROJECT_COLLISION_CYCLE_AND_VISIBILITY: PASS', flush=True)
(WORK / 'project-evidence.json').write_text(json.dumps({
    'schema': 'ps0-recursive-project-test/1',
    'source_commit': os.environ.get('PS0_SOURCE_SHA'),
    'driver_sha256': sha(driver), 'published_sha256': saved,
    'module_inputs': selected,
    'checks': ['recursive-public-and-meta-imports', 'mixed-native-source', 'warm-reuse', 'driver-invalidation',
               'transitive-ps-and-native-invalidation', 'publication-no-replacement',
               'prelude-no-hidden-imports', 'local-entry', 'source-collision', 'cycle', 'private-visibility'],
    'verified_execution': False,
}, indent=2) + '\n')
print('PS0_RECURSIVE_PROJECT: PASS', flush=True)
