#!/usr/bin/env python3
# Copyright (c) 2026 Dwijayuda. All rights reserved.
# Released under Apache 2.0 license as described in LICENSE.
"""Plan ProofScript declaration operand edits from actual native frontend syntax."""
from pathlib import Path
import argparse
import hashlib
import json

parser = argparse.ArgumentParser()
parser.add_argument('census', type=Path)
parser.add_argument('source', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--plan', type=Path, required=True)
parser.add_argument('--allow-empty', action='store_true')
args = parser.parse_args()
snapshot = json.loads(args.census.read_text())
raw = args.source.read_bytes()
assert snapshot['nativeSource'].encode() == raw, 'planner requires exact captured native source bytes'
edits, declarations, strategies = [], [], []

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
    # Follow only the native roles which the owned parser recursively adapts.
    # Quotation, DSL and other native syntax remain opaque.
    if operand['kind'] == 'Lean.Parser.Term.paren':
        single_type_call(operand['args'][1], role)
        return
    if operand['kind'] == 'Lean.Parser.Term.proj':
        assert len(operand['args']) == 3
        single_type_call(operand['args'][0], role + ' projection subject')
        return
    if operand['kind'] == 'termIfThenElse':
        parts = operand['args']
        assert len(parts) == 6 and [parts[i]['atom'] for i in [0, 2, 4]] == ['if', 'then', 'else']
        for index in [1, 3, 5]:
            single_type_call(parts[index], role + ' conditional operand')
        return
    if operand['kind'] == 'Lean.Parser.Term.fun':
        body = operand['args'][1]
        if body['kind'] == 'Lean.Parser.Term.basicFun':
            single_type_call(body['args'][3], role + ' lambda body')
        return
    if operand.get('nativeBinaryOperator', False):
        assert len(operand['args']) == 3 and operand['args'][1]['atom'] is not None
        single_type_call(operand['args'][0], role)
        single_type_call(operand['args'][2], role)
        return
    if operand['kind'] != 'Lean.Parser.Term.app':
        return
    function, arguments = operand['args']
    arguments = arguments['args']
    if not any(argument['kind'] in ['Lean.Parser.Term.paren', 'Lean.Parser.Term.tuple',
                                   'Lean.Parser.Term.fun'] for argument in arguments):
        return
    if any(a['kind'] == 'Lean.Parser.Term.namedArgument' for a in arguments):
        # PS calls put named arguments last. Native elaboration resolves names
        # independently of their written positions; parity is checked by Lake.
        pending = len(edits)
        for argument in arguments:
            if argument['kind'] == 'Lean.Parser.Term.namedArgument':
                assert len(argument['args']) == 5
                single_type_call(argument['args'][3], role + ' named argument value')
            else:
                single_type_call(argument, role)
        nested = sorted(edits[pending:], key=lambda change: change['start'])
        del edits[pending:]
        positional, named = [], []
        previous_end = span(function)[1]
        for argument in arguments:
            start, end = span(argument)
            assert previous_end <= start
            trivia = raw[previous_end:start]
            previous_end = end
            is_named = argument['kind'] == 'Lean.Parser.Term.namedArgument'
            left, right = (start + 1, end - 1) if is_named else (start, end)
            chunks, cursor = [], left
            for change in nested:
                if left <= change['start'] and change['end'] <= right:
                    assert cursor <= change['start']
                    chunks += [raw[cursor:change['start']], change['new'].encode()]
                    cursor = change['end']
            chunks.append(raw[cursor:right])
            (named if is_named else positional).append(trivia + b''.join(chunks))
        start, end = span(operand)
        function_start, function_end = span(function)
        replacement = raw[function_start:function_end] + b'(' + b','.join(positional + named) + b')'
        edit(start, end, replacement.decode(), role + ' call with named arguments last; preserve original argument terms')
        return
    _, end = span(function)
    start, _ = span(arguments[0])
    assert end <= start
    edit(end, start, '(' + raw[end:start].decode(), role + ' call opening delimiter; preserve argument parentheses and trivia')
    for previous, following in zip(arguments, arguments[1:]):
        _, end = span(previous)
        start, _ = span(following)
        assert end <= start
        edit(end, start, ',' + raw[end:start].decode(), role + ' call argument separator; preserve original trivia')
    _, argument_end = span(arguments[-1])
    edit(argument_end, argument_end, ')', role + ' call closing delimiter; preserve original argument parentheses')
    for argument in arguments:
        single_type_call(argument, role)


def alias_binder(binder):
    kind, parts = binder['kind'], binder['args']
    if kind in ['Lean.Parser.Term.implicitBinder', 'Lean.Parser.Term.strictImplicitBinder',
                'Lean.Parser.Term.instBinder']:
        return True
    return (kind == 'Lean.Parser.Term.explicitBinder' and len(parts) == 5
            and len(parts[1]['args']) == 1 and parts[1]['args'][0]['ident'] is not None
            and len(parts[2]['args']) == 2)


def declaration_value(value):
    if value is None:
        return
    if value['kind'] == 'null':
        if value['args']:
            declaration_value(value['args'][0])
    elif value['kind'] == 'Lean.Parser.Command.declValSimple':
        single_type_call(value['args'][1], 'owned declaration body')
    elif value['kind'] == 'Lean.Parser.Command.declValEqns':
        equation_values(value['args'][0]['args'][0])
    elif value['kind'] == 'Lean.Parser.Command.whereStructInst':
        fields = value['args'][1]['args'][0]['args']
        for field in fields:
            if field['kind'] != 'Lean.Parser.Term.structInstField':
                continue
            body = field['args'][1]['args']
            if not body:
                continue
            assert len(body) == 3
            # Field binders retain their native grouping. Type/default roles are
            # handled by the same telescope traversal as declaration signatures.
            telescope(body[0]['args'])
            if body[1]['args']:
                single_type_call(body[1]['args'][0]['args'][1], 'owned field result type')
            rhs = body[2]
            if rhs['kind'] == 'Lean.Parser.Term.structInstFieldDef':
                single_type_call(rhs['args'][2], 'owned field value')
            else:
                assert rhs['kind'] == 'Lean.Parser.Term.structInstFieldEqns'
                equation_values(rhs['args'][1])


def equation_values(alternatives):
    for alternative in alternatives['args'][0]['args']:
        assert alternative['kind'] == 'Lean.Parser.Term.matchAlt'
        assert len(alternative['args']) == 4
        single_type_call(alternative['args'][3], 'owned equation right-hand side')


def telescope(binders):
    for binder in binders:
        parts = binder['args']
        if binder['kind'] in ['ident', 'Lean.Parser.Term.hole']:
            continue
        if binder['kind'] == 'Lean.Parser.Term.instBinder':
            assert len(parts) == 4
            single_type_call(parts[2])
            continue
        if binder['kind'] in ['Lean.Parser.Term.implicitBinder', 'Lean.Parser.Term.strictImplicitBinder']:
            assert len(parts) == 4
            if parts[2]['args']:
                assert len(parts[2]['args']) == 2
                single_type_call(parts[2]['args'][1])
            continue
        assert binder['kind'] == 'Lean.Parser.Term.explicitBinder', binder
        assert len(parts) == 5 and parts[1]['args']
        assert len(parts[2]['args']) in [0, 2]
        if parts[2]['args']:
            single_type_call(parts[2]['args'][1])
        suffix = parts[3]['args']
        if suffix:
            assert len(suffix) == 1
            if suffix[0]['kind'] == 'Lean.Parser.Term.binderTactic':
                continue
            assert suffix[0]['kind'] == 'Lean.Parser.Term.binderDefault'
            assert len(suffix[0]['args']) == 2
            single_type_call(suffix[0]['args'][1], 'owned binder default')
        start, end = span(binder)
        assert raw[start:start + 1] == b'(' and raw[end - 1:end] == b')'


for command in original_commands(snapshot['commands']):
    decl = command['declaration']
    if decl is None or decl['mode'] != 'native-compatible':
        continue
    supported = ['Lean.Parser.Command.definition', 'Lean.Parser.Command.abbrev',
                 'Lean.Parser.Command.theorem', 'Lean.Parser.Command.opaque', 'Lean.Parser.Command.axiom',
                 'Lean.Parser.Command.instance', 'Lean.Parser.Command.example']
    if decl['production'] not in supported:
        continue
    is_definition = decl['production'] == 'Lean.Parser.Command.definition'
    signature = decl['signatureSyntax']
    assert signature['kind'] in ['Lean.Parser.Command.optDeclSig', 'Lean.Parser.Command.declSig']
    binders = signature['args'][0]['args']
    result_type = ([signature['args'][1]] if signature['kind'] == 'Lean.Parser.Command.declSig'
                   else signature['args'][1]['args'])
    if result_type:
        assert len(result_type) == 1 and result_type[0]['kind'] == 'Lean.Parser.Term.typeSpec'
        single_type_call(result_type[0]['args'][1], 'owned declaration result type')
    use_alias = is_definition and all(alias_binder(binder) for binder in binders)
    if use_alias and binders and binders[0]['kind'] == 'Lean.Parser.Term.explicitBinder':
        name_end = decl['nameRange']['end']
        first, _ = span(binders[0])
        if any(byte not in b' \t' for byte in raw[name_end:first]):
            use_alias = False
    # Native definition syntax preserves shared/inferred/anonymous binder
    # elaboration; it still goes through the owned PS signature/value adapters.
    for binder in binders:
        parts = binder['args']
        if binder['kind'] in ['ident', 'Lean.Parser.Term.hole']:
            continue
        if binder['kind'] == 'Lean.Parser.Term.instBinder':
            assert len(parts) == 4
            single_type_call(parts[2])
            continue
        if binder['kind'] in ['Lean.Parser.Term.implicitBinder', 'Lean.Parser.Term.strictImplicitBinder']:
            assert len(parts) == 4
            if parts[2]['args']:
                assert len(parts[2]['args']) == 2
                single_type_call(parts[2]['args'][1])
            continue
        assert binder['kind'] == 'Lean.Parser.Term.explicitBinder', decl['sourceName']
        assert len(parts) == 5 and parts[1]['args']
        assert len(parts[2]['args']) in [0, 2]
        if parts[2]['args']:
            single_type_call(parts[2]['args'][1])
        suffix = parts[3]['args']
        if suffix:
            assert len(suffix) == 1
            if suffix[0]['kind'] == 'Lean.Parser.Term.binderTactic':
                continue
            assert suffix[0]['kind'] == 'Lean.Parser.Term.binderDefault'
            assert len(suffix[0]['args']) == 2
            single_type_call(suffix[0]['args'][1], 'owned binder default')
        start, end = span(binder)
        assert raw[start:start + 1] == b'(' and raw[end - 1:end] == b')'
    kw = decl['keywordRange']
    if not is_definition:
        declaration_value(decl.get('valueSyntax'))
        continue
    assert raw[kw['start']:kw['end']] == b'def'
    keyword = ('function' if binders else 'const') if use_alias else 'def'
    strategies.append({'sourceName': decl['sourceName'], 'keywordRange': kw,
                       'targetKeyword': keyword,
                       'reason': 'typed alias telescope' if use_alias else 'preserve R2 native telescope grouping/inference or original head trivia'})
    if use_alias:
        edit(kw['start'], kw['end'], keyword, 'owned PS declaration keyword')
    if use_alias and binders and binders[0]['kind'] == 'Lean.Parser.Term.explicitBinder':
        name_end = decl['nameRange']['end']
        first, _ = span(binders[0])
        assert first == name_end or raw[name_end:first].isspace(), 'head trivia must be whitespace; comments are never discarded'
        if first != name_end:
            edit(name_end, first, '', 'PS head adjacency')
    for previous, following in zip(binders, binders[1:]) if use_alias else []:
        if previous['kind'] != 'Lean.Parser.Term.explicitBinder' or following['kind'] != 'Lean.Parser.Term.explicitBinder':
            continue
        _, end = span(previous)
        start, _ = span(following)
        assert end <= start
        edit(end - 1, start + 1, ',' + raw[end:start].decode(),
             'merge consecutive typed groups; preserve original intervening whitespace and line breaks')
    declaration_value(decl.get('valueSyntax'))
    declarations.append(decl['sourceName'])

assert declarations or args.allow_empty, 'no supported native declaration heads'
edits.sort(key=lambda e: e['start'])
assert all(a['end'] <= b['start'] for a, b in zip(edits, edits[1:])), 'overlapping native source edits'
assert all(change['old'].count('\n') == change['new'].count('\n') for change in edits), 'source edits must preserve original line breaks'
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
    'strategies': strategies,
    'line_count_preserved': raw.count(b'\n') == converted.count(b'\n'),
    'scope': 'R2 alias/native telescopes, standard family signatures, equation RHS and explicit owned type/default/result/call/conditional roles; native grouping/inference and independently owned syntax retained',
    'grammar_migration_complete': False, 'verified_execution': False,
}, indent=2) + '\n')
print('PS0_COMPILER_HEAD_MIGRATION: planned ' + str(len(declarations)), flush=True)
