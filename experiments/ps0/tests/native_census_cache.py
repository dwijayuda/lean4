#!/usr/bin/env python3
# Copyright (c) 2026 Dwijayuda. All rights reserved.
# Released under Apache 2.0 license as described in LICENSE.
"""Validate exact pinned native syntax captures; never reuse converted plans or objects."""
from pathlib import Path
import hashlib
import json
import re

SCHEMA = 'ps0-native-source-census/1'
# Native capture role changes require a new contract marker before reuse.
OPERATOR_SCOPE = 'active-and-captured-kinds/1'
ADJACENT_HEAD_SCOPE = 'native-environment/1'


def declarations(commands):
    for command in commands:
        if command['declaration'] is not None:
            yield command['declaration']
        yield from declarations(command.get('nestedCommands', []))


def needs_head_lexical_refresh(snapshot):
    for declaration in declarations(snapshot['commands']):
        if declaration.get('production') != 'Lean.Parser.Command.definition':
            continue
        binders = declaration['signatureSyntax']['args'][0]['args']
        if binders and binders[0]['kind'] == 'Lean.Parser.Term.explicitBinder':
            if (snapshot.get('adjacentHeadLexicalScope') != ADJACENT_HEAD_SCOPE or
                    'adjacentCallSpelling' not in declaration or
                    'nameIdentifierRange' not in declaration):
                return True
    return False


class NativeCensusCache:
    def __init__(self, directory, source, lean_commit):
        assert re.fullmatch('[0-9a-f]{40}', source), source
        paths = list(Path(directory).rglob('source-plan-summary.json'))
        assert len(paths) == 1, paths
        self.root = paths[0].parent
        summary = json.loads(paths[0].read_text())
        inventory_path = self.root / 'input-inventory.json'
        inventory = json.loads(inventory_path.read_text())
        assert summary['planner_source'] == inventory['source_commit'] == source
        assert summary['source_grammar'] is True
        assert summary['module_count'] == inventory['module_count'] == 2569
        assert inventory['lean_commit'] == lean_commit
        assert re.fullmatch('[0-9a-f]{64}', inventory['stage_driver_sha256'])
        self.inputs = inventory['inputs']
        self.lean_commit = lean_commit
        sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        self.provenance = {
            'producer_source': source, 'lean_commit': lean_commit,
            'producer_driver_sha256': inventory['stage_driver_sha256'],
            'source_plan_summary_sha256': sha(paths[0]),
            'input_inventory_sha256': sha(inventory_path),
            'scope': 'native AST preparation only; current planner and fresh native Lake graph remain mandatory',
        }

    def find(self, module, original, sdk_sha256):
        path = self.root / 'current-source-plans' / module / 'native-census.json'
        if not path.is_file():
            return None
        assert self.inputs[module]['original_sha256'] == sdk_sha256, module
        data = json.loads(path.read_text())
        assert data['schema'] == SCHEMA, module
        assert data['leanCommit'] == self.lean_commit and data['module'] == module, module
        assert data['operatorDescriptorScope'] == OPERATOR_SCOPE, module
        assert data['nativeSource'].encode() == original, module
        assert all(d['mode'] == 'native-compatible' for d in declarations(data['commands'])), module
        return path
