#!/usr/bin/env python3
"""Exact-toolchain integration and intended-failure checks. Run only in CI.

Every semantic negative must first reach its expected gate. Missing tools,
baseline compilation errors and unrelated parser errors are not accepted
as evidence of a correct refusal.
"""
import json
from pathlib import Path
import runpy
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
M = runpy.run_path(str(ROOT / 'scripts/proof_linked.py'))
Refusal = M['Refusal']
OUT = ROOT / 'build/proof-linked'
EXAMPLE = ROOT / 'examples/verified-inventory'
OUT.mkdir(parents=True, exist_ok=True)

positive = M['build'](ROOT, EXAMPLE, OUT / 'inventory', M['PROFILE'])
evidence = json.loads((positive / 'evidence.json').read_text())
assert evidence['strict_verified_execution'] is False
assert evidence['profile'] == M['PROFILE']
for name, expected in evidence['artifacts'].items():
    assert M['digest']((positive / name).read_bytes()) == expected

original_source = (EXAMPLE / 'src/Inventory.ps').read_text()
original_proof = (EXAMPLE / 'proofs/Inventory.lean').read_text()
proof_header = 'module\npublic import Admitted\nimport all Admitted\npublic section\nnamespace InventoryProof\n'
cases = [
    ('wrong-body', original_source.replace('stock - requested', 'stock + requested'), original_proof, ['rfl']),
    ('proof-hole', original_source, original_proof.replace('  rfl', '  sorry', 1), ['sorryAx']),
    ('unapproved-axiom', original_source,
     proof_header +
     'axiom cheat (stock requested : Nat) : Inventory.remaining stock requested = stock - requested\n'
     'theorem remaining_spec (stock requested : Nat) : Inventory.remaining stock requested = stock - requested := cheat stock requested\n'
     'end InventoryProof\n', ['cheat', 'axiom']),
    ('irrelevant-proof', original_source,
     proof_header +
     'theorem remaining_spec : True := True.intro\nend InventoryProof\n', ['remaining_spec']),
    ('missing-proof', original_source,
     proof_header + 'end InventoryProof\n', ['remaining_spec']),
]
refusals = []
for name, source, proof, markers in cases:
    example = OUT / ('input-' + name)
    (example / 'src').mkdir(parents=True)
    (example / 'proofs').mkdir()
    (example / 'src/Inventory.ps').write_text(source)
    (example / 'proofs/Inventory.lean').write_text(proof)
    output = OUT / name
    try:
        M['build'](ROOT, example, output, M['PROFILE'])
        raise AssertionError('Incorrectly published ' + name)
    except Refusal as exc:
        assert 'PS0-SOURCE-PROOF' in str(exc), (name, str(exc))
        log = (OUT / (name + '-logs') / 'source-proof.log').read_text()
        for marker in markers:
            assert marker.lower() in log.lower(), (name, marker, log[-4000:])
        assert not output.exists()
        refusals.append(name)

# The source proof is valid, and the proposed artifact is self-consistent,
# but the IR has the same type and the wrong body. Only the exact extraction
# theorem should reject this. This is not an emission-text mutation test.
with tempfile.TemporaryDirectory(prefix='.wrong-ir-', dir=OUT) as tmp:
    work = Path(tmp) / 'work'
    logs = OUT / 'wrong-ir-logs'
    M['prepare_workspace'](ROOT, work, original_source.encode(), original_proof.encode())
    M['run'](['lake', 'update'], work, logs / 'resolve.log', 'PS0-RESOLVE')
    M['run'](['lake', 'comparator', '--config', 'source-comparator.json'], work,
             logs / 'source-proof.log', 'PS0-SOURCE-PROOF')
    candidate = work / '.lake/ps0-candidate'
    wrong = ['add', ['first'], ['second']]
    (candidate / 'ir.json').write_text(json.dumps({'schema': M['SCHEMA'], 'root': M['ROOT'], 'ir': wrong}))
    for name, typed in [('inventory.js', False), ('inventory.ts', True)]:
        (candidate / name).write_bytes(M['expected_source'](wrong, typed))
    assert M['read_candidate'](candidate)[0] == wrong
    M['write_correspondence'](work, wrong)
    try:
        M['run'](['lake', 'comparator', '--config', 'target-comparator.json'], work,
                 logs / 'target-proof.log', 'PS0-TARGET-PROOF')
        raise AssertionError('Same-signature wrong IR was accepted')
    except Refusal as exc:
        assert 'PS0-TARGET-PROOF' in str(exc)
        text = (logs / 'target-proof.log').read_text().lower()
        assert 'rfl' in text or 'type mismatch' in text, text[-4000:]
        refusals.append('same-signature-wrong-ir')

before = {p.name: p.read_bytes() for p in positive.iterdir()}
try:
    M['build'](ROOT, EXAMPLE, positive, M['PROFILE'])
    raise AssertionError('Existing bundle was overwritten')
except Refusal as exc:
    assert 'PS0-OUTPUT-EXISTS' in str(exc)
assert before == {p.name: p.read_bytes() for p in positive.iterdir()}
refusals.append('existing-bundle')

(OUT / 'qualification.json').write_text(json.dumps({
    'scope': 'reviewed Nat2 example, not full PS0 or verified runtime',
    'positive_bundle': str(positive.relative_to(ROOT)),
    'intended_refusals': refusals,
    'evidence_sha256': M['digest']((positive / 'evidence.json').read_bytes()),
}, indent=2) + '\n')
print('PS0_PROOF_LINKED_SLICE: PASS (conditional scope; inspected runtime/Lean logs still required)')
