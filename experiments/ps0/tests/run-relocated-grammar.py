#!/usr/bin/env python3
"""Qualify native prefix metadata publication for a relocated PS grammar host."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
tag = os.environ.get('PS0_PACKAGE_TAG', '')
work = ROOT / 'build' / ('relocated-grammar-' + os.environ['GITHUB_RUN_ID'] + tag)
work.mkdir(parents=True, exist_ok=False)
driver = Path(os.environ.get('PS0_PACKAGE_DRIVER', str(ROOT / '.lake/build/bin/ps0'))).resolve()
metadata = Path(os.environ.get('PS0_PACKAGE_METADATA', str(ROOT / '.lake/build/lib/lean'))).resolve()
prefix = work / 'prefix'
published = prefix / 'bin/ps0'
published.parent.mkdir(parents=True)
shutil.copy2(driver, published)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(published) == sha(driver)


def probe(label, ok):
    env = {**os.environ, 'PS0_TEST_DRIVER': str(published),
           'PS0_TEST_TAG': '-relocated-' + label + tag}
    result = subprocess.run(['python3', 'tests/run-prelude-grammar.py'], env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
    (work / (label + '.log')).write_text(result.stdout)
    print(result.stdout, end='', flush=True)
    assert (result.returncode == 0) == ok, (label, result.returncode)
    return result.stdout


missing = probe('missing-host', False)
assert 'PS0' in missing and any(s in missing for s in ['unknown module prefix', 'object file', 'not found'])
files = {}
for item in sorted(metadata.rglob('*')):
    if not item.is_file() or not any(s in item.name for s in ['.olean', '.ir']):
        continue
    relative = item.relative_to(metadata)
    if relative.parts[0] != 'PS0' and not relative.name.startswith('PS0.'):
        continue
    target = prefix / 'lib/lean' / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(item, target)
    files[str(relative)] = {'source_sha256': sha(item), 'published_sha256': sha(target)}
    assert files[str(relative)]['source_sha256'] == files[str(relative)]['published_sha256']
assert 'PS0/StandardAdapters.olean' in files
assert not (prefix / 'lib/lean/Init.olean').exists(), 'SDK dependencies must remain explicit'
positive = probe('with-host', True)
assert 'PS0_PRELUDE_GRAMMAR_NO_HIDDEN_IMPORTS: PASS' in positive
(work / 'evidence.json').write_text(json.dumps({
    'source': os.environ['PS0_SOURCE_SHA'], 'driver_sha256': sha(published),
    'host_metadata': files,
    'dependencies': 'explicit pinned Lean SDK metadata plus byte-preserved native PS0 host metadata in bin/../lib/lean',
    'scope': 'relocated native prefix, missing-host negative, PS prelude build/link/runtime and compiler stage options; not whole canonical compiler migration',
    'verified_execution': False,
}, indent=2) + '\n')
print('PS0_RELOCATED_GRAMMAR_HOST: PASS', flush=True)
