#!/usr/bin/env python3
# Copyright (c) 2026 Dwijayuda. All rights reserved.
# Released under Apache 2.0 license as described in LICENSE.
"""Plan finite typed declaration-head edits from actual native frontend syntax."""
from pathlib import Path
import argparse
import hashlib
import json

parser = argparse.ArgumentParser()
parser.add_argument('census', type=Path)
parser.add_argument('source', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--plan', type=Path, required=True)
args = parser.parse_args()
snapshot = json.loads(args.census.read_text())
raw = args.source.read_bytes()
assert snapshot['nativeSource'].encode() == raw, 'planner requires exact captured native source bytes'
edits, declarations = [], []

def span(node):
    value = node['range']
    assert value is not None
    start, end = value['start'], value['end']
    assert 0 <= start <= end <= len(raw)
    return start, end

def edit(start, end, replacement, role):
    assert 0 <= start <= end <= len(raw)
    edits.append({'start': start, 'end': end, 'old': raw[start:end].decode(),
                  'new': replacement, 'role': role})

for command in snapshot['commands']:
    decl = command['declaration']
    if decl is None or decl['mode'] != 'native-compatible':
        continue
    if decl['production'] != 'Lean.Parser.Command.definition':
        continue
    signature = decl['signatureSyntax']
    assert signature['kind'] == 'Lean.Parser.Command.optDeclSig'
    binders = signature['args'][0]['args']
    if not binders:
        continue
    # This first planner supports exactly one typed identifier in each explicit
    # group. Shared/inferred/default/implicit forms await their own source rules.
    for binder in binders:
        assert binder['kind'] == 'Lean.Parser.Term.explicitBinder', decl['sourceName']
        parts = binder['args']
        assert len(parts) == 5 and len(parts[1]['args']) == 1
        assert parts[1]['args'][0]['ident'] is not None
        assert len(parts[2]['args']) == 2 and not parts[3]['args']
        start, end = span(binder)
        assert raw[start:start + 1] == b'(' and raw[end - 1:end] == b')'
    kw = decl['keywordRange']
    assert raw[kw['start']:kw['end']] == b'def'
    edit(kw['start'], kw['end'], 'function', 'owned PS declaration keyword')
    name_end = decl['nameRange']['end']
    first, _ = span(binders[0])
    assert raw[name_end:first].isspace(), 'head trivia must be whitespace; comments are never discarded'
    edit(name_end, first, '', 'PS head adjacency')
    for previous, following in zip(binders, binders[1:]):
        _, end = span(previous)
        start, _ = span(following)
        assert raw[end:start].isspace(), 'group trivia must be whitespace; comments are never discarded'
        edit(end - 1, start + 1, ', ', 'merge consecutive typed groups in source order')
    declarations.append(decl['sourceName'])

assert declarations, 'no supported native declaration heads'
edits.sort(key=lambda e: e['start'])
assert all(a['end'] <= b['start'] for a, b in zip(edits, edits[1:])), 'overlapping native source edits'
chunks, cursor = [], 0
for change in edits:
    chunks += [raw[cursor:change['start']], change['new'].encode()]
    cursor = change['end']
chunks.append(raw[cursor:])
converted = b''.join(chunks)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_bytes(converted)
args.plan.write_text(json.dumps({
    'schema': 'ps0-compiler-head-migration/1', 'source_sha256': hashlib.sha256(raw).hexdigest(),
    'result_sha256': hashlib.sha256(converted).hexdigest(), 'declarations': declarations, 'edits': edits,
    'scope': 'typed declaration heads only; native bodies and non-declaration commands preserved byte for byte',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_COMPILER_HEAD_MIGRATION: planned ' + str(len(declarations)), flush=True)
