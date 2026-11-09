#!/usr/bin/env python3
# Copyright (c) 2026 Dwijayuda. All rights reserved.
# Released under Apache 2.0 license as described in LICENSE.
"""Compare retained native parser roles with the PS adapter's diagnostic output."""
from pathlib import Path
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('native', type=Path)
parser.add_argument('mapped', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
native, mapped = [json.loads(file.read_text()) for file in [args.native, args.mapped]]


def definitions(commands):
    result = {}
    for command in commands:
        declaration = command.get('declaration')
        if declaration and declaration['production'] == 'Lean.Parser.Command.definition':
            name = declaration['sourceName']
            assert name not in result, name
            result[name] = declaration
        for name, declaration in definitions(command.get('nestedCommands', [])).items():
            assert name not in result, name
            result[name] = declaration
    return result


def tree(source):
    if source is None:
        return None
    return dict(kind=source['kind'], ident=source['ident'], atom=source['atom'],
                args=[tree(child) for child in source['args']])


def first_difference(a, b, path=''):
    if type(a) is not type(b):
        return dict(path=path, native=a, ps=b)
    if isinstance(a, dict):
        for key in ['kind', 'ident', 'atom', 'args']:
            difference = first_difference(a[key], b[key], path + '.' + key)
            if difference:
                return difference
    elif isinstance(a, list):
        if len(a) != len(b):
            return dict(path=path + '.length', native=len(a), ps=len(b))
        for index, (left, right) in enumerate(zip(a, b)):
            difference = first_difference(left, right, path + f'[{index}]')
            if difference:
                return difference
    elif a != b:
        return dict(path=path, native=a, ps=b)
    return None


left = definitions(native['commands'])
right = definitions(mapped['loweredCommands'])
assert left and left.keys() == right.keys(), (left.keys(), right.keys())
rows = []
for name, declaration in left.items():
    row = dict(name=name)
    for role in ['signatureSyntax', 'valueSyntax']:
        row[role] = first_difference(tree(declaration.get(role)), tree(right[name].get(role)))
    rows.append(row)
result = dict(scope='native command-adapter output before further native macro expansion; ranges and operator-census flags excluded',
    definitions=len(rows), equal_syntax=sum(all(row[role] is None for role in ['signatureSyntax', 'valueSyntax']) for row in rows),
    differences=[row for row in rows if row['signatureSyntax'] or row['valueSyntax']],
    grammar_migration_complete=False, verified_execution=False)
args.output.write_text(json.dumps(result, indent=2) + '\n')
print('PS0_LOWERED_NATIVE_SYNTAX:' + json.dumps(result, sort_keys=True), flush=True)
