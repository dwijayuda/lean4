#!/usr/bin/env python3
"""Inventory every pinned SDK module through native census and PS source planning.

This reports planning gaps; it does not certify parsing, compilation or parity.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import hashlib
import json
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
inventory_path = ROOT / 'compiler-source-inventory.json'
inventory = json.loads(inventory_path.read_text())
assert subprocess.check_output(['lean', '--githash'], text=True).strip() == inventory['leanCommit']
sdk = Path(subprocess.check_output(['lean', '--print-prefix'], text=True).strip()) / 'src/lean'
driver = ROOT / '.lake/build/bin/ps0'
work = ROOT / 'build' / ('corpus-source-plan-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
sha = lambda data: hashlib.sha256(data).hexdigest()

# Reject a source identity mismatch before any corpus result is reported.
for entry in inventory['entries']:
    data = (sdk / entry['sdkPath']).read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert actual == entry['blob'], (entry['module'], actual, entry['blob'])
assert len(inventory['entries']) == inventory['count'] == 2546

def inspect(entry):
    started = time.monotonic()
    directory = work / 'modules' / entry['module']
    directory.mkdir(parents=True, exist_ok=False)
    original, census = directory / 'original.ps', directory / 'native-census.json'
    converted, plan = directory / 'converted.ps', directory / 'plan.json'
    result = dict(entry, original_sha256=sha((sdk / entry['sdkPath']).read_bytes()))
    commands = [
        ('header', [driver, 'convert-native', sdk / entry['sdkPath'], original]),
        ('census', [driver, 'census-source', original, entry['module'], census]),
        ('plan', ['python3', ROOT / 'tests/migrate-compiler-heads.py', census, original,
                  converted, '--plan', plan, '--allow-empty']),
    ]
    for label, command in commands:
        try:
            with (directory / (label + '.log')).open('w') as log:
                process = subprocess.run([str(x) for x in command], stdout=log,
                                         stderr=subprocess.STDOUT, timeout=600)
            if process.returncode:
                result.update(status=label + '-gap', returncode=process.returncode)
                break
        except subprocess.TimeoutExpired:
            result.update(status=label + '-timeout')
            break
    else:
        planned = json.loads(plan.read_text())
        result.update(status='planned-unvalidated', definitions=len(planned['declarations']),
                      edits=len(planned['edits']), strategies=planned.get('strategies', []),
                      converted_sha256=sha(converted.read_bytes()),
                      census_sha256=sha(census.read_bytes()))
    result['elapsed_seconds'] = round(time.monotonic() - started, 3)
    (directory / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return result

results = []
with ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(inspect, entry) for entry in inventory['entries']]
    for future in as_completed(futures):
        results.append(future.result())
        if len(results) % 50 == 0:
            print('PS0_CORPUS_SOURCE_PLAN_PROGRESS:' + str(len(results)), flush=True)
results.sort(key=lambda value: value['module'])
counts = {}
for result in results:
    counts[result['status']] = counts.get(result['status'], 0) + 1
report = dict(schema='ps0-corpus-source-plan/1', source=os.environ['PS0_SOURCE_SHA'],
              lean_commit=inventory['leanCommit'], inventory_sha256=sha(inventory_path.read_bytes()),
              count=len(results), status_counts=counts, modules=results,
              dependencies='pinned SDK sibling olean/IR; each module censused independently',
              scope='source identity, native frontend census and source planning only; converted sources are not yet qualified',
              grammar_migration_complete=False, verified_execution=False)
(work / 'evidence.json').write_text(json.dumps(report, indent=2) + '\n')
print('PS0_CORPUS_SOURCE_PLAN_COMPLETE:' + json.dumps(counts, sort_keys=True), flush=True)
