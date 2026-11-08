#!/usr/bin/env python3
"""Verify the census comes from the actual native frontend's source-command stream."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('source-census-' + os.environ.get('GITHUB_RUN_ID', str(os.getpid())))
work.mkdir(parents=True, exist_ok=False)

def run(args, ok=True):
    r = subprocess.run([str(x) for x in args], text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=300)
    print(r.stdout, end='', flush=True)
    assert (r.returncode == 0) == ok, (args, r.returncode)
    return r.stdout

fixture = ROOT / 'tests/v1/source_census.ps'
output = work / 'source.json'
run(['lake', 'exe', 'ps0', 'census-source', fixture, 'CensusFixture', output])
census = json.loads(output.read_text())
mapping = json.loads(subprocess.check_output(['lake', 'exe', 'ps0', 'source-map', str(fixture)], text=True))
assert census['schema'] == 'ps0-native-source-census/1'
assert census['leanCommit'] == 'eb6cafb7290e8bd5f2937522d8d804f58f02bafc'
assert census['nativeSource'] == mapping['nativeSource']
names = [x['declaration']['sourceName'] for x in census['commands'] if x['declaration'] is not None]
assert set(names) == {'add', 'counted', 'quotedDeclaration', 'main'}, names
assert 'censusGenerated' in census['environmentDeclNames']
assert 'censusGenerated' not in names and 'onlyQuoted' not in names
native = census['nativeSource'].encode()
for command in census['commands']:
    if command['range'] is not None:
        start, end = command['range']['start'], command['range']['end']
        assert 0 <= start <= end <= len(native)
    declaration = command['declaration']
    if declaration is not None:
        span = declaration['keywordRange']
        keyword = native[span['start']:span['end']].decode()
        assert keyword in ['function', 'const', 'def'], (declaration, keyword)
        assert declaration['mode'] == 'mapped-ps'

prelude = work / 'bootstrap.ps'
prelude.write_text('module\nprelude\npublic import Init\ndef bootstrapValue : Nat := 7\n')
run(['lake', 'exe', 'ps0', 'census-source', prelude, 'BootstrapCensus', work / 'bootstrap.json'])
bootstrap = json.loads((work / 'bootstrap.json').read_text())
assert bootstrap['nativeSource'] == prelude.read_text()
decls = [x['declaration'] for x in bootstrap['commands'] if x['declaration'] is not None]
assert len(decls) == 1 and decls[0]['sourceName'] == 'bootstrapValue'
assert decls[0]['mode'] == 'native-compatible'
assert 'PS0.Policy' not in bootstrap['imports']

invalid = work / 'invalid.ps'
invalid.write_text('def bad : Nat := false\n')
run(['lake', 'exe', 'ps0', 'census-source', invalid, 'InvalidCensus', work / 'invalid.json'], ok=False)
assert not (work / 'invalid.json').exists(), 'failed elaboration cannot publish census evidence'
(work / 'census-evidence.json').write_text(json.dumps({
    'source': os.environ.get('PS0_SOURCE_SHA'),
    'native_source_sha256': hashlib.sha256(native).hexdigest(),
    'source_declarations': names,
    'oracle': 'PS0_NATIVE_SOURCE_CENSUS: PASS',
    'grammar_migration_complete': False,
}, indent=2) + '\n')
print('PS0_NATIVE_SOURCE_CENSUS: PASS', flush=True)
