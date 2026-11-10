#!/usr/bin/env python3
# Copyright (c) 2026 Dwijayuda. All rights reserved.
# Released under Apache 2.0 license as described in LICENSE.
"""Inventory native bridge roots in mapped PS operands without inspecting their native descendants."""
from pathlib import Path
from collections import Counter, defaultdict
import argparse
import hashlib
import json

parser = argparse.ArgumentParser()
parser.add_argument('root', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--capture-source', required=True)
parser.add_argument('--auditor-source', required=True)
args = parser.parse_args()
bridges = {'ps0NativeTermBridge', 'ps0NativeHeadBridge', 'ps0NativeTacticBridge',
           'ps0NativeDoBridge', 'ps0NativeDoElemBridge', 'ps0NativeFunBinderBridge',
           'ps0LoopNativeBinderBridge'}
counts, owners, modules, examples = Counter(), defaultdict(set), defaultdict(set), defaultdict(list)
captures, mapped_owners, skipped, incomplete_mapped_commands = [], 0, 0, 0


def commands(rows):
    for row in rows:
        yield row
        yield from commands(row.get('nestedCommands', []))


def roots(tree, path=()):
    if not isinstance(tree, dict) or 'kind' not in tree:
        return
    kind, children = tree['kind'], tree['args']
    if kind in bridges:
        assert len(children) == 1, (kind, len(children))
        yield kind, children[0], path
        return  # An independently owned native category is opaque to this inventory.
    for index, child in enumerate(children):
        yield from roots(child, (*path[-7:], kind + '/' + str(index)))


files = sorted(set(args.root.rglob('*.ilean.ps0-source-census.json')) |
               {p for folder in ['partial-source-census', 'source-census']
                for directory in args.root.rglob(folder) for p in directory.rglob('*.json')})
assert files, 'no actual mapped source-census files'
seen = set()
for file in files:
    raw_file = file.read_bytes()
    census = json.loads(raw_file)
    if census.get('schema') == 'ps0-compiler-source-census/1':
        assert file.name == 'summary.json', file
        continue
    assert census['schema'] == 'ps0-native-source-census/1'
    assert census['leanCommit'] == 'eb6cafb7290e8bd5f2937522d8d804f58f02bafc'
    rows = list(commands(census['commands']))
    if not any(capture is not None and capture.get('mode') == 'mapped-ps'
               for row in rows for capture in [row.get('declaration'), row.get('initialization'),
                                               row.get('dataDeclaration')]):
        continue
    module = census['module']
    assert module not in seen, ('duplicate capture module', module)
    seen.add(module)
    captures.append(dict(module=module, sha256=hashlib.sha256(raw_file).hexdigest()))
    source = census['nativeSource'].encode()
    for index, command in enumerate(rows):
        selections = []
        declaration = command.get('declaration')
        if declaration is not None:
            if declaration['mode'] == 'mapped-ps':
                owner = declaration['sourceName']
                if 'mappedCommandSyntax' in declaration:
                    assert census['mappedOperandSyntaxScope'] == 'raw-command-before-native-lowering/1'
                    selections.append(('mappedCommand', declaration['mappedCommandSyntax'], owner))
                else:
                    incomplete_mapped_commands += 1
                    selections.extend((role, declaration.get(field), owner) for role, field in
                                      [('legacy-telescope', 'signatureSyntax'), ('legacy-value', 'valueSyntax')])
            else:
                skipped += 1
        for field in ['initialization', 'dataDeclaration']:
            capture = command.get(field)
            if capture is not None and capture['mode'] == 'mapped-ps':
                selections.append((field, capture['syntax'], 'command-' + str(index)))
        if selections:
            mapped_owners += 1
        for role, tree, owner in selections:
            for bridge, native, ancestry in roots(tree):
                key = role + ':' + bridge + ':' + native['kind']
                counts[key] += 1
                modules[key].add(module)
                owners[key].add((module, owner))
                if len(examples[key]) < 3:
                    span = native.get('range')
                    excerpt = source[span['start']:span['end']].decode()[:400] if span else None
                    examples[key].append(dict(module=module, owner=owner, ancestry=ancestry,
                                              range=span, source=excerpt))
result = dict(schema='ps0-mapped-native-bridge-inventory/1', capture_source=args.capture_source,
    auditor_source=args.auditor_source, retained_captures=len(captures), captures=captures,
    mapped_command_owners=mapped_owners, skipped_native_declarations=skipped,
    mapped_commands_without_complete_operand_capture=incomplete_mapped_commands,
    observations=[dict(role_bridge_native_kind=key, occurrences=counts[key],
        module_count=len(modules[key]), owner_count=len(owners[key]), examples=examples[key])
        for key in sorted(counts)],
    scope='Observed native bridge roots in captured mapped PS operands; traversal stops at each native category boundary. Frequencies do not establish ownership correctness or conformance.',
    grammar_migration_complete=False, verified_execution=False)
assert mapped_owners and counts
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2) + '\n')
for key, count in counts.most_common():
    print(f'{key}: {count} occurrences / {len(modules[key])} modules')
print('PS0_MAPPED_NATIVE_BRIDGE_INVENTORY: PASS', flush=True)
