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

def original_commands(commands):
    for command in commands:
        yield command
        yield from original_commands(command.get('nestedCommands', []))

def single_type_call(operand, role='owned binder type'):
    # Only this explicitly owned type operand is adapted. Quotation, DSL and
    # arbitrary application descendants are never traversed by the planner.
    if operand['kind'] != 'Lean.Parser.Term.app':
        return
    function, arguments = operand['args']
    if len(arguments['args']) != 1:
        return
    argument = arguments['args'][0]
    if argument['kind'] != 'Lean.Parser.Term.paren':
        return
    _, end = span(function)
    start, _ = span(argument)
    if start == end:
        return
    assert raw[end:start].isspace(), 'type-call trivia contains comments; no edit is permitted'
    edit(end, start, '(', role + ' call opening delimiter; preserve original argument parentheses')
    _, argument_end = span(argument)
    edit(argument_end, argument_end, ')', role + ' call closing delimiter; preserve original argument parentheses')

for command in original_commands(snapshot['commands']):
    decl = command['declaration']
    if decl is None or decl['mode'] != 'native-compatible':
        continue
    if decl['production'] != 'Lean.Parser.Command.definition':
        continue
    signature = decl['signatureSyntax']
    assert signature['kind'] == 'Lean.Parser.Command.optDeclSig'
    binders = signature['args'][0]['args']
    # Preserve instance groups in place. Only consecutive single-identifier
    # explicit groups are merged; no binder is reordered or inferred here.
    for binder in binders:
        parts = binder['args']
        if binder['kind'] == 'Lean.Parser.Term.instBinder':
            assert len(parts) == 4
            single_type_call(parts[2])
            continue
        assert binder['kind'] == 'Lean.Parser.Term.explicitBinder', decl['sourceName']
        assert len(parts) == 5 and len(parts[1]['args']) == 1
        assert parts[1]['args'][0]['ident'] is not None
        assert len(parts[2]['args']) == 2
        single_type_call(parts[2]['args'][1])
        suffix = parts[3]['args']
        if suffix:
            assert len(suffix) == 1 and suffix[0]['kind'] == 'Lean.Parser.Term.binderDefault'
            assert len(suffix[0]['args']) == 2
            single_type_call(suffix[0]['args'][1], 'owned binder default')
        start, end = span(binder)
        assert raw[start:start + 1] == b'(' and raw[end - 1:end] == b')'
    kw = decl['keywordRange']
    assert raw[kw['start']:kw['end']] == b'def'
    edit(kw['start'], kw['end'], 'function' if binders else 'const', 'owned PS declaration keyword')
    if binders and binders[0]['kind'] == 'Lean.Parser.Term.explicitBinder':
        name_end = decl['nameRange']['end']
        first, _ = span(binders[0])
        assert raw[name_end:first].isspace(), 'head trivia must be whitespace; comments are never discarded'
        edit(name_end, first, '', 'PS head adjacency')
    for previous, following in zip(binders, binders[1:]):
        if previous['kind'] != 'Lean.Parser.Term.explicitBinder' or following['kind'] != 'Lean.Parser.Term.explicitBinder':
            continue
        _, end = span(previous)
        start, _ = span(following)
        assert raw[end:start].isspace(), 'group trivia must be whitespace; comments are never discarded'
        edit(end - 1, start + 1, ', ', 'merge consecutive typed groups in source order')
    root = decl.get('valueApplication')
    applications = []
    if root is not None and any(a['kind'] == 'Lean.Parser.Term.paren' for a in root['arguments']):
        applications = [root, *decl.get('lambdaBodyApplications', [])]
    for application in applications:
        if application is None or not any(a['kind'] == 'Lean.Parser.Term.paren' for a in application['arguments']):
            continue
        arguments = application['arguments']
        assert all(a['kind'] != 'Lean.Parser.Term.namedArgument' for a in arguments), 'named body arguments need their own source role'
        function_end = application['functionRange']['end']
        first_start, _ = span(arguments[0])
        assert raw[function_end:first_start].isspace(), 'body call trivia contains comments; no edit is permitted'
        edit(function_end, first_start, '(', 'owned value root application opening delimiter')
        for previous, following in zip(arguments, arguments[1:]):
            _, end = span(previous)
            start, _ = span(following)
            assert raw[end:start].isspace(), 'body argument trivia contains comments; no edit is permitted'
            edit(end, start, ', ', 'owned value root application argument separator')
        _, last_end = span(arguments[-1])
        edit(last_end, last_end, ')', 'owned value root application closing delimiter')
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
    'scope': 'typed explicit/default/instance telescopes and named values in explicit source declaration slots, single type/default-call adjacency, and owned root value calls plus direct lambda-body call roots within their arguments; original argument nodes, quotations and unrelated native commands preserved',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_COMPILER_HEAD_MIGRATION: planned ' + str(len(declarations)), flush=True)
