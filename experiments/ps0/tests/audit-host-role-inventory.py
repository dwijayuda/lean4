#!/usr/bin/env python3
# Copyright (c) 2026 Dwijayuda. All rights reserved.
# Released under Apache 2.0 license as described in LICENSE.
"""Inventory retained native operand trees; observations do not establish ownership."""
from pathlib import Path
from collections import Counter, defaultdict
import argparse
import hashlib
import json

parser = argparse.ArgumentParser()
parser.add_argument('root', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--expected-captures', type=int, default=2087)
args = parser.parse_args()
counts = Counter()
modules = defaultdict(set)
examples = defaultdict(list)
captures = []


def nodes(source, ancestry=()):
    if not isinstance(source, dict) or 'kind' not in source:
        return
    yield source, ancestry
    for child in source['args']:
        yield from nodes(child, (*ancestry[-6:], source['kind']))


def commands(rows):
    for row in rows:
        yield row
        yield from commands(row.get('nestedCommands', []))


for file in sorted(args.root.rglob('native-census.json')):
    data = file.read_bytes()
    census = json.loads(data)
    module = census['module']
    raw = census['nativeSource'].encode()
    captures.append(dict(module=module, sha256=hashlib.sha256(data).hexdigest()))
    for command in commands(census['commands']):
        declaration = command.get('declaration')
        if declaration is None:
            continue
        for role, tree in [('signature', declaration.get('signatureSyntax')),
                           ('value', declaration.get('valueSyntax'))]:
            for node, ancestry in nodes(tree):
                kind = node['kind']
                if not kind.startswith('Lean.Parser.Term.'):
                    continue
                key = role + ':' + kind
                counts[key] += 1
                modules[key].add(module)
                if len(examples[key]) < 3 and node.get('range'):
                    span = node['range']
                    examples[key].append(dict(module=module, declaration=declaration.get('sourceName'),
                        ancestry=ancestry, range=span,
                        source=raw[span['start']:span['end']].decode()[:320]))
assert len(captures) == args.expected_captures, len(captures)
result = dict(schema='ps0-native-host-role-inventory/1', retained_captures=len(captures),
    captures=captures, observations=[dict(role_kind=key, occurrences=counts[key],
        module_count=len(modules[key]), examples=examples[key]) for key in sorted(counts)],
    scope='native signature/value syntax inventory including native pattern and DSL ancestors; no claim of PS ownership or conformance',
    grammar_migration_complete=False, verified_execution=False)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2) + '\n')
for key, count in counts.most_common():
    print(f'{key}: {count} occurrences / {len(modules[key])} modules')
print('PS0_NATIVE_HOST_ROLE_INVENTORY: PASS', flush=True)
