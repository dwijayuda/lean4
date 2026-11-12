#!/usr/bin/env python3
"""Exercise actual Linux Lake builds, dependency invalidation and publication."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
WORK = ROOT / 'build' / ('native-test-' + os.environ.get('GITHUB_RUN_ID', str(os.getpid())))
WORK.mkdir(parents=True, exist_ok=False)
source = WORK / 'Main.ps'
support = WORK / 'PS0NativeSupport.lean'
source.write_bytes((ROOT / 'tests/native/Main.ps').read_bytes())
support.write_bytes((ROOT / 'tests/native/PS0NativeSupport.lean').read_bytes())

def run(args, ok=True):
    result = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=300)
    print(result.stdout, end='', flush=True)
    if (result.returncode == 0) != ok:
        raise AssertionError((args, result.returncode))
    return result.stdout

def lake_build():
    return run(['lake', '-R', '-f', 'lakefile.native.lean', '-Ksource=' + str(source),
                '-Kps0Module=NativeMain', '-KsupportDir=' + str(WORK), 'build', 'app'])

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

lake_build()
exe = ROOT / '.lake/build/bin/NativeMain'
c = ROOT / '.lake/build/ps0-native/NativeMain/NativeMain.c'
assert 'PS0_NATIVE:42:7:15:2' in run([exe, 'one', 'two'])
assert 'lean/lean.h' in c.read_text()
assert not (c.parent / 'NativeMain.lean').exists()
before = (digest(exe), exe.stat().st_mtime_ns, c.stat().st_mtime_ns)
lake_build()
assert before == (digest(exe), exe.stat().st_mtime_ns, c.stat().st_mtime_ns)
print('PS0_NATIVE_WARM_REUSE: PASS', flush=True)

source.write_text(source.read_text().replace('twice(21)', 'twice(22)').replace('answer = 42', 'answer = 44'))
lake_build()
assert 'PS0_NATIVE:44:7:15:0' in run([exe])
assert digest(exe) != before[0]
support.write_text(support.read_text().replace(':= 7', ':= 9'))
lake_build()
assert 'PS0_NATIVE:44:9:15:0' in run([exe])
print('PS0_NATIVE_SOURCE_AND_IMPORT_INVALIDATION: PASS', flush=True)

# CLI publication is independent of Lake's replaceable development cache.
# Its default support module is the original checked-in fixture.
published = WORK / 'published'
run(['lake', 'exe', 'ps0', 'build-native', source, 'NativeCli', published])
assert 'PS0_NATIVE:44:7:15:0' in run([published / 'NativeCli'])
receipt = json.loads((published / 'native-build.json').read_text())
assert receipt['schema'] == 'ps0-lake-native/1'
assert receipt['verified_execution'] is False
published_hash = digest(published / 'NativeCli')
out = run(['lake', 'exe', 'ps0', 'build-native', source, 'NativeCli', published], ok=False)
assert 'PS0-OUTPUT-EXISTS' in out
assert digest(published / 'NativeCli') == published_hash

invalid = WORK / 'Invalid.ps'
invalid.write_text('def main : IO Unit := doesNotExist\n')
refused = WORK / 'refused'
run(['lake', 'exe', 'ps0', 'build-native', invalid, 'NativeInvalid', refused], ok=False)
assert not refused.exists()

no_main = WORK / 'NoMain.ps'
no_main.write_text('const value: Nat := 42\n')
no_main_out = WORK / 'no-main'
out = run(['lake', 'exe', 'ps0', 'build-native', no_main, 'NativeNoMain', no_main_out], ok=False)
assert 'PS0-NATIVE-MAIN' in out
assert not no_main_out.exists()

missing_extern = WORK / 'MissingExtern.ps'
missing_extern.write_text('@[extern "ps0_missing_external_71ad"] opaque missingExternal : UInt32 → UInt32\n'
                          'def main : IO UInt32 := pure(missingExternal(0))\n')
extern_out = WORK / 'missing-extern'
out = run(['lake', 'exe', 'ps0', 'build-native', missing_extern, 'NativeExtern', extern_out], ok=False)
assert 'ps0_missing_external_71ad' in out
assert not extern_out.exists()

invalid_call = WORK / 'InvalidCall.ps'
invalid_call.write_text('function f(x: Nat, y: Nat): Nat := x + y\nconst value: Nat := f(x := 1, 2)\n')
out = run(['lake', 'exe', 'ps0', 'build-native', invalid_call, 'NativeCall', WORK / 'bad-call'], ok=False)
assert 'PS0V1-CALL-ORDER' in out
assert not (WORK / 'bad-call').exists()
bad_alias = WORK / 'BadAlias.ps'
bad_alias.write_text('function f(x: Nat)(y: Nat): Nat := x + y\n')
out = run(['lake', 'exe', 'ps0', 'check', bad_alias], ok=False)
assert 'PS0V1-BIND-02' in out
private_leak = WORK / 'PrivateLeak.ps'
private_leak.write_text('private const hidden: Nat := 42\ntheorem leak: hidden = 42 := by rfl\n')
out = run(['lake', 'exe', 'ps0', 'check', private_leak], ok=False)
assert 'private declaration' in out
print('PS0_NATIVE_ELAB_LINK_AND_PUBLICATION_NEGATIVES: PASS', flush=True)

print('PS0_LAKE_NATIVE: PASS', flush=True)
