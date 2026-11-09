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
    previous = None
    for command in commands:
        yield previous, command
        yield from original_commands(command.get('nestedCommands', []))
        previous = command

def binary_operand(operand):
    return operand.get('nativeBinaryOperator', False) or operand['kind'] in [
        'Lean.Parser.Term.arrow', 'Lean.Parser.Term.subst']


def owns_postfix(operand):
    kind, parts = operand['kind'], operand['args']
    if kind in ['«term__[_]»', "«term__[_]'_»", '«term__[_]_?»', '«term__[_]_!»',
                'Array.«term__[_:_]»', 'Array.«term__[_:]»', 'Array.«term__[:_]»',
                'Lean.Parser.Term.pipeProj']:
        return True
    if kind == 'Lean.Parser.Term.proj':
        return True
    if kind == 'Lean.Parser.Term.paren':
        return owns_postfix(parts[1])
    if kind == 'Lean.Parser.Term.app':
        return owns_postfix(parts[0]) or any(owns_postfix(arg) for arg in parts[1]['args'])
    if kind == 'Lean.Parser.Term.namedArgument':
        return owns_postfix(parts[3])
    if binary_operand(operand):
        return owns_postfix(parts[0]) or owns_postfix(parts[2])
    return False


def call_head_needs_group(operand):
    if operand['kind'] == 'Lean.Parser.Term.pipeProj':
        return True
    if operand['kind'] in ['Lean.Parser.Term.proj', '«term__[_]»', "«term__[_]'_»",
                           '«term__[_]_?»', '«term__[_]_!»', 'Array.«term__[_:_]»',
                           'Array.«term__[_:]»', 'Array.«term__[:_]»']:
        return call_head_needs_group(operand['args'][0])
    return False


def single_type_call(operand, role='owned binder type'):
    # Follow only the native roles which the owned parser recursively adapts.
    # Quotation, DSL and other native syntax remain opaque.
    slice_shapes = {'Array.«term__[_:_]»': (6, [2, 4]),
                    'Array.«term__[_:]»': (5, [2]), 'Array.«term__[:_]»': (5, [3])}
    if operand['kind'] in slice_shapes:
        arity, bounds = slice_shapes[operand['kind']]
        assert len(operand['args']) == arity
        single_type_call(operand['args'][0], role + ' slice subject')
        for index in bounds:
            single_type_call(operand['args'][index], role + ' slice bound')
        return
    index_arities = {'«term__[_]»': 4, "«term__[_]'_»": 5,
                     '«term__[_]_?»': 7, '«term__[_]_!»': 7}
    if operand['kind'] in index_arities:
        assert len(operand['args']) == index_arities[operand['kind']]
        single_type_call(operand['args'][0], role + ' indexed subject')
        index = 3 if index_arities[operand['kind']] == 7 else 2
        single_type_call(operand['args'][index], role + ' index operand')
        if operand['kind'] == "«term__[_]'_»":
            single_type_call(operand['args'][4], role + ' index proof')
        return
    if operand['kind'] == 'choice':
        pending = len(edits)
        alternatives = []
        for alternative in operand['args']:
            del edits[pending:]
            single_type_call(alternative, role)
            alternatives.append(edits[pending:].copy())
        assert alternatives and all(changes == alternatives[0] for changes in alternatives), 'native alternatives require identical source edits'
        del edits[pending:]
        edits.extend(alternatives[0])
        return
    if operand['kind'] == 'Lean.Parser.Term.pipeProj':
        assert len(operand['args']) == 5
        single_type_call(operand['args'][0], role + ' pipeline subject')
        for argument in operand['args'][4]['args']:
            if argument['kind'] == 'Lean.Parser.Term.namedArgument':
                single_type_call(argument['args'][3], role + ' pipeline named argument')
            else:
                single_type_call(argument, role + ' pipeline argument')
        return
    if operand['kind'] == 'Lean.Parser.Term.paren':
        single_type_call(operand['args'][1], role)
        return
    if operand['kind'] == 'Lean.Parser.Term.proj':
        assert len(operand['args']) == 3
        single_type_call(operand['args'][0], role + ' projection subject')
        return
    if operand['kind'] == 'Lean.Parser.Term.do':
        assert len(operand['args']) == 2
        do_sequence(operand['args'][1])
        return
    if operand['kind'] == 'Lean.Parser.Term.letrec':
        assert len(operand['args']) == 4
        recursive_declarations(operand['args'][1])
        single_type_call(operand['args'][3], role + ' local recursive continuation')
        return
    if operand['kind'] == 'Lean.Parser.Term.let':
        parts = operand['args']
        assert len(parts) == 5 and parts[2]['kind'] == 'Lean.Parser.Term.letDecl'
        declaration = parts[2]['args'][0]
        if declaration['kind'] == 'Lean.Parser.Term.letIdDecl':
            local_id_value(declaration)
            single_type_call(parts[4], role + ' named local continuation')
        return
    if operand['kind'] == 'Lean.Parser.Term.termUnless':
        unless_operands(operand)
        return
    if operand['kind'] == 'termIfThenElse':
        parts = operand['args']
        assert len(parts) == 6 and [parts[i]['atom'] for i in [0, 2, 4]] == ['if', 'then', 'else']
        for index in [1, 3, 5]:
            single_type_call(parts[index], role + ' conditional operand')
        return
    if operand['kind'] == 'Lean.Parser.Term.match':
        parts = operand['args']
        assert len(parts) == 6 and len(parts[2]['args']) <= 1
        if parts[2]['args']:
            motive = parts[2]['args'][0]
            assert motive['kind'] == 'Lean.Parser.Term.motive' and len(motive['args']) == 5
            single_type_call(motive['args'][3], role + ' match motive')
        for discriminant in parts[3]['args']:
            if discriminant['atom'] is not None:
                continue
            assert discriminant['kind'] == 'Lean.Parser.Term.matchDiscr' and len(discriminant['args']) == 2
            single_type_call(discriminant['args'][1], role + ' match discriminant')
        match_alternatives(parts[5], role + ' match alternative')
        return
    if operand['kind'] == 'Lean.Parser.Term.structInst':
        parts = operand['args']
        assert len(parts) == 6
        if parts[1]['args']:
            assert len(parts[1]['args']) == 2
            for source in parts[1]['args'][0]['args']:
                if source['atom'] is None:
                    single_type_call(source, role + ' record update source')
        record_fields(parts[2], role)
        if parts[4]['args']:
            assert len(parts[4]['args']) == 2
            single_type_call(parts[4]['args'][1], role + ' record result type')
        return
    if operand['kind'] == 'Lean.Parser.Term.fun':
        body = operand['args'][1]
        if body['kind'] == 'Lean.Parser.Term.basicFun':
            for binder in body['args'][0]['args']:
                if binder['kind'] == 'Lean.Parser.Term.typeAscription':
                    assert len(binder['args']) == 5 and len(binder['args'][3]['args']) <= 1
                    if binder['args'][3]['args']:
                        single_type_call(binder['args'][3]['args'][0], role + ' lambda binder type')
                elif binder['kind'] in ['Lean.Parser.Term.implicitBinder',
                                       'Lean.Parser.Term.strictImplicitBinder',
                                       'Lean.Parser.Term.instBinder']:
                    telescope([binder])
            optional_local_type(body['args'][1], role + ' lambda result type')
            single_type_call(body['args'][3], role + ' lambda body')
        elif body['kind'] == 'Lean.Parser.Term.matchAlts':
            match_alternatives(body, role + ' pattern lambda alternative')
        return
    if binary_operand(operand):
        assert len(operand['args']) == 3 and operand['args'][1]['atom'] is not None
        single_type_call(operand['args'][0], role)
        single_type_call(operand['args'][2], role)
        return
    if operand['kind'] != 'Lean.Parser.Term.app':
        return
    function, arguments = operand['args']
    arguments = arguments['args']
    pending = len(edits)
    single_type_call(function, role + ' call head')
    for argument in arguments:
        if argument['kind'] == 'Lean.Parser.Term.namedArgument':
            assert len(argument['args']) == 5
            single_type_call(argument['args'][3], role + ' named argument value')
        else:
            single_type_call(argument, role)
    if len(edits) == pending and not owns_postfix(operand) and not any(argument['kind'] in [
            'Lean.Parser.Term.paren', 'Lean.Parser.Term.tuple', 'Lean.Parser.Term.fun',
            'Lean.Parser.Term.do'] for argument in arguments):
        return
    if any(a['kind'] == 'Lean.Parser.Term.namedArgument' for a in arguments):
        # PS calls put named arguments last. Native elaboration resolves names
        # independently of their written positions; parity is checked by Lake.
        nested = sorted(edits[pending:], key=lambda change: change['start'])
        del edits[pending:]
        def rewritten(left, right):
            chunks, cursor = [], left
            for change in nested:
                if left <= change['start'] and change['end'] <= right:
                    assert cursor <= change['start']
                    chunks += [raw[cursor:change['start']], change['new'].encode()]
                    cursor = change['end']
            chunks.append(raw[cursor:right])
            return b''.join(chunks)
        positional, named = [], []
        previous_end = span(function)[1]
        for argument in arguments:
            start, end = span(argument)
            assert previous_end <= start
            trivia = raw[previous_end:start]
            previous_end = end
            is_named = argument['kind'] == 'Lean.Parser.Term.namedArgument'
            left, right = (start + 1, end - 1) if is_named else (start, end)
            rewritten_argument = rewritten(left, right)
            if not is_named and argument['kind'] == 'Lean.Parser.Term.do':
                rewritten_argument = b'(' + rewritten_argument + b')'
            (named if is_named else positional).append(trivia + rewritten_argument)
        start, end = span(operand)
        function_start, function_end = span(function)
        head = rewritten(function_start, function_end)
        if call_head_needs_group(function):
            head = b'(' + head + b')'
        replacement = head + b'(' + b','.join(positional + named) + b')'
        edit(start, end, replacement.decode(), role + ' call with named arguments last; preserve original argument terms')
        return
    _, end = span(function)
    start, _ = span(arguments[0])
    assert end <= start
    grouped_head = call_head_needs_group(function)
    if grouped_head:
        function_start, _ = span(function)
        edit(function_start, function_start, '(', role + ' group low-precedence native call head')
    gap = raw[end:start]
    # Reuse a leading head-gap blank for the delimiter so first-argument native
    # layout anchors keep their original column. Comments and line breaks stay.
    retained_gap = gap[1:] if gap.startswith(b' ') else gap
    edit(end, start, (')(' if grouped_head else '(') + retained_gap.decode(),
         role + ' call opening delimiter; retain argument parentheses, comments and line breaks')
    for previous, following in zip(arguments, arguments[1:]):
        _, end = span(previous)
        start, _ = span(following)
        assert end <= start
        edit(end, start, ',' + raw[end:start].decode(), role + ' call argument separator; preserve original trivia')
    _, argument_end = span(arguments[-1])
    edit(argument_end, argument_end, ')', role + ' call closing delimiter; preserve original argument parentheses')


def match_alternatives(source, role):
    assert source['kind'] == 'Lean.Parser.Term.matchAlts' and len(source['args']) == 1
    for alternative in source['args'][0]['args']:
        assert alternative['kind'] == 'Lean.Parser.Term.matchAlt' and len(alternative['args']) == 4
        single_type_call(alternative['args'][3], role + ' body')


def record_fields(source, role):
    assert source['kind'] == 'Lean.Parser.Term.structInstFields' and len(source['args']) == 1
    for field in source['args'][0]['args']:
        if field['atom'] is not None or field['kind'] == 'null':
            continue
        assert field['kind'] == 'Lean.Parser.Term.structInstField' and len(field['args']) == 2
        def index_role(part):
            if part['kind'] == 'Lean.Parser.Term.structInstArrayRef':
                assert len(part['args']) == 3
                single_type_call(part['args'][1], role + ' record lvalue index')
            elif part['kind'] == 'null':
                for child in part['args']:
                    index_role(child)
        for part in field['args'][0]['args']:
            index_role(part)
        body = field['args'][1]['args']
        if not body:
            continue
        assert len(body) == 3
        telescope(body[0]['args'])
        optional_local_type(body[1], role + ' record field type')
        rhs = body[2]
        if rhs['kind'] == 'Lean.Parser.Term.structInstFieldDef':
            assert len(rhs['args']) == 3
            single_type_call(rhs['args'][2], role + ' record field value')
        else:
            assert rhs['kind'] == 'Lean.Parser.Term.structInstFieldEqns' and len(rhs['args']) == 2
            match_alternatives(rhs['args'][1], role + ' record field equation')


def alias_binder(binder):
    kind, parts = binder['kind'], binder['args']
    if kind in ['Lean.Parser.Term.implicitBinder', 'Lean.Parser.Term.strictImplicitBinder',
                'Lean.Parser.Term.instBinder']:
        return True
    return (kind == 'Lean.Parser.Term.explicitBinder' and len(parts) == 5
            and len(parts[1]['args']) == 1 and parts[1]['args'][0]['ident'] is not None
            and len(parts[2]['args']) == 2)


def optional_local_type(node, role):
    if node['args']:
        assert len(node['args']) == 1
        spec = node['args'][0]
        assert spec['kind'] == 'Lean.Parser.Term.typeSpec' and len(spec['args']) == 2
        single_type_call(spec['args'][1], role)


def local_id_value(declaration):
    parts = declaration['args']
    assert len(parts) == 5
    telescope(parts[1]['args'])
    optional_local_type(parts[2], 'owned local result type')
    single_type_call(parts[4], 'owned local value')


def do_element(element):
    if element['kind'] == 'Lean.Parser.Term.doLetElse':
        parts = element['args']
        assert len(parts) == 9 and len(parts[8]['args']) <= 1
        single_type_call(parts[5], 'owned pattern let value')
        do_sequence(parts[7])
        if parts[8]['args']:
            do_sequence(parts[8]['args'][0])
        return
    kind, parts = element['kind'], element['args']
    if kind == 'Lean.Parser.Term.doIf':
        assert len(parts) == 6
        for part in parts:
            do_if_role(part)
    elif kind == 'Lean.Parser.Term.doLetRec':
        assert len(parts) == 2
        recursive_declarations(parts[1])
    elif kind == 'Lean.Parser.Term.doUnless':
        unless_operands(element)
    elif kind == 'Lean.Parser.Term.doExpr':
        assert len(parts) == 1
        single_type_call(parts[0], 'owned do expression')
    elif kind == 'Lean.Parser.Term.doReturn':
        assert len(parts) == 2 and len(parts[1]['args']) <= 1
        if parts[1]['args']:
            single_type_call(parts[1]['args'][0], 'owned return value')
    elif kind == 'Lean.Parser.Term.doNested':
        assert len(parts) == 2
        do_sequence(parts[1])
    elif kind == 'Lean.Parser.Term.doLet':
        assert len(parts) == 4
        wrapper = parts[3]
        assert wrapper['kind'] == 'Lean.Parser.Term.letDecl' and len(wrapper['args']) == 1
        if wrapper['args'][0]['kind'] == 'Lean.Parser.Term.letIdDecl':
            local_id_value(wrapper['args'][0])
    elif kind == 'Lean.Parser.Term.doReassign':
        assert len(parts) == 1
        if parts[0]['kind'] == 'Lean.Parser.Term.letIdDeclNoBinders':
            local_id_value(parts[0])
    elif kind == 'Lean.Parser.Term.doLetArrow':
        assert len(parts) == 4
        declaration = parts[3]
        if declaration['kind'] == 'Lean.Parser.Term.doIdDecl':
            assert len(declaration['args']) == 4
            optional_local_type(declaration['args'][1], 'owned binding type')
            do_element(declaration['args'][3])
        elif declaration['kind'] == 'Lean.Parser.Term.doPatDecl':
            binding = declaration['args']
            assert len(binding) == 5
            do_element(binding[3])
            branches = binding[4]['args']
            if branches:
                assert len(branches) == 3 and len(branches[2]['args']) <= 1
                do_sequence(branches[1])
                if branches[2]['args']:
                    do_sequence(branches[2]['args'][0])
    # Native patterns, registered DSL elements and unsupported control operands
    # retain their independent parser ownership.


def do_if_role(source):
    kind, parts = source['kind'], source['args']
    if kind == 'Lean.Parser.Term.doIfProp':
        assert len(parts) == 2
        single_type_call(parts[1], 'owned do-if proposition')
    elif kind == 'Lean.Parser.Term.doIfLet':
        assert len(parts) == 3 and parts[2]['kind'] in [
            'Lean.Parser.Term.doIfLetPure', 'Lean.Parser.Term.doIfLetBind']
        assert len(parts[2]['args']) == 2
        single_type_call(parts[2]['args'][1], 'owned do-if pattern value')
    elif kind in ['Lean.Parser.Term.doSeqIndent', 'Lean.Parser.Term.doSeqBracketed']:
        do_sequence(source)
    elif kind == 'null':
        for child in parts:
            do_if_role(child)
    else:
        assert source['atom'] is not None or kind == 'Lean.Parser.Term.elseIf', kind


def recursive_declarations(group):
    assert group['kind'] == 'Lean.Parser.Term.letRecDecls' and len(group['args']) == 1
    for declaration in group['args'][0]['args']:
        if declaration['atom'] is not None or declaration['kind'] == 'null':
            continue
        assert declaration['kind'] == 'Lean.Parser.Term.letRecDecl' and len(declaration['args']) == 4
        wrapper = declaration['args'][2]
        assert wrapper['kind'] == 'Lean.Parser.Term.letDecl' and len(wrapper['args']) == 1
        value = wrapper['args'][0]
        if value['kind'] == 'Lean.Parser.Term.letIdDecl':
            local_id_value(value)
        else:
            assert value['kind'] == 'Lean.Parser.Term.letEqnsDecl' and len(value['args']) == 4
            telescope(value['args'][1]['args'])
            optional_local_type(value['args'][2], 'owned recursive local result type')
            assert value['args'][3]['kind'] == 'Lean.Parser.Term.matchAlts'
            for alternative in value['args'][3]['args'][0]['args']:
                assert alternative['kind'] == 'Lean.Parser.Term.matchAlt' and len(alternative['args']) == 4
                single_type_call(alternative['args'][3], 'owned recursive local equation value')


def unless_operands(element):
    parts = element['args']
    assert len(parts) == 4 and [parts[i]['atom'] for i in [0, 2]] == ['unless', 'do']
    single_type_call(parts[1], 'owned unless condition')
    do_sequence(parts[3])


def do_sequence(sequence):
    assert sequence['kind'] in ['Lean.Parser.Term.doSeqIndent', 'Lean.Parser.Term.doSeqBracketed']
    index = 0 if sequence['kind'] == 'Lean.Parser.Term.doSeqIndent' else 1
    for item in sequence['args'][index]['args']:
        assert item['kind'] == 'Lean.Parser.Term.doSeqItem' and len(item['args']) == 2
        do_element(item['args'][0])


def declaration_value(value):
    if value is None:
        return
    if value['kind'] == 'null':
        if value['args']:
            declaration_value(value['args'][0])
    elif value['kind'] == 'Lean.Parser.Command.declValSimple':
        single_type_call(value['args'][1], 'owned declaration body')
        where_declarations(value['args'][3])
    elif value['kind'] == 'Lean.Parser.Command.declValEqns':
        equation_values(value['args'][0]['args'][0])
        where_declarations(value['args'][0]['args'][2])
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
        where_declarations(value['args'][2])


def where_declarations(optional):
    if not optional['args']:
        return
    assert len(optional['args']) == 1
    clause = optional['args'][0]
    assert clause['kind'] == 'Lean.Parser.Term.whereDecls' and len(clause['args']) == 3
    recursive_declarations({'kind': 'Lean.Parser.Term.letRecDecls', 'args': [clause['args'][1]]})
    if clause['args'][2]['args']:
        tail = clause['args'][2]['args'][0]
        assert tail['kind'] == 'Lean.Parser.Term.whereFinally' and len(tail['args']) == 3
        if tail['args'][1]['args']:
            where_tactics(tail['args'][1]['args'][0])
        for section in tail['args'][2]['args']:
            assert section['kind'] == 'Lean.Parser.Term.whereFinallySubsection'
            where_tactics(section['args'][3])


def where_tactics(sequence):
    assert sequence['kind'] == 'Lean.Parser.Tactic.tacticSeq' and len(sequence['args']) == 1
    inner = sequence['args'][0]
    if inner['kind'] == 'Lean.Parser.Tactic.tacticSeqBracketed':
        assert len(inner['args']) == 3
        group = inner['args'][1]
    else:
        assert inner['kind'] == 'Lean.Parser.Tactic.tacticSeq1Indented' and len(inner['args']) == 1
        group = inner['args'][0]
    for item in group['args']:
        if item['kind'] in ['Lean.Parser.Tactic.exact', 'Lean.Parser.Tactic.apply', 'Lean.Parser.Tactic.refine'] and len(item['args']) == 2:
            single_type_call(item['args'][1], 'owned where-finally tactic operand')


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


for previous_command, command in original_commands(snapshot['commands']):
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
    # Contextual aliases remain valid native identifiers. Keep the reserved R2
    # head after native commands whose identifier/field lists could consume it.
    boundary_hazard = previous_command is not None and previous_command['headKind'] in {
        'Lean.Parser.Command.attribute', 'Lean.Parser.Command.structure',
        'Lean.Parser.Command.inductive', 'Lean.Parser.Command.coinductive',
        'Lean.Parser.Command.classInductive',
        'Lean.Parser.commandSeal__',
        'Lean.Parser.Command.section',
    }
    if boundary_hazard:
        use_alias = False
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
                       'reason': ('typed alias telescope' if use_alias else
                                  'preserve reserved R2 head after native identifier/field list' if boundary_hazard else
                                  'preserve R2 native telescope grouping/inference or original head trivia'),
                       'previousCommandHeadKind': previous_command['headKind'] if previous_command else None})
    if use_alias:
        edit(kw['start'], kw['end'], keyword, 'owned PS declaration keyword')
    if use_alias and binders and binders[0]['kind'] == 'Lean.Parser.Term.explicitBinder':
        assert snapshot.get('adjacentHeadLexicalScope') == 'native-environment/1' and \
            'adjacentCallSpelling' in decl and 'nameIdentifierRange' in decl, \
            'native adjacent declaration lexer observation required before removing head trivia'
        adjacent_spelling = decl['adjacentCallSpelling']
        identifier = decl['nameIdentifierRange']
        name_start, identifier_end = identifier['start'], identifier['end']
        if raw[name_start:identifier_end].decode() != adjacent_spelling:
            edit(name_start, identifier_end, adjacent_spelling,
                 'native lexer requires escaped declaration identifier before adjacent binder group')
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
