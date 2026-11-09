#!/usr/bin/env python3
"""Compare native match/pattern-lambda semantics and the syntax-only PS prelude route."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
work = ROOT / 'build' / ('match-host-' + os.environ['GITHUB_RUN_ID'])
work.mkdir(parents=True, exist_ok=False)
header = 'module\nprelude\npublic import Init\npublic section\n'
native = '''def add (x y : Nat) : Nat := x + y
def pairSum (p : Nat × Nat) : Nat := p.1 + p.2
def unary (n : Nat) : Nat := match n with
  | 0 => add 1 2
  | Nat.succ k => add k 1
def multi (n m : Nat) : Nat := match n, m with
  | 0, 0 => add 1 2
  | a, b => add a b
def named (n : Nat) : Nat := match h : n with
  | 0 => add 1 2
  | Nat.succ k => add k 1
def withMotive (n : Nat) : Nat := match (motive := fun _ => Nat) n with
  | 0 => add 1 2
  | Nat.succ k => add k 1
def options (n : Nat) : Nat := match some n with
  | some (Nat.succ k) => add k 1
  | some 0 => 0
  | none => 0
def alternatives (n : Nat) : Nat := match n with
  | 0 | 1 => add 1 2
  | k => k
def pattern (n : Nat) : Nat := (fun | 0 => add 1 2 | Nat.succ k => add k 1) n
'''
ps = '''function add(x: Nat, y: Nat): Nat := x + y
function pairSum(p: Nat × Nat): Nat := p.1 + p.2
function unary(n: Nat): Nat := match n with
  | 0 => add(1, 2)
  | Nat.succ k => add(k, 1)
function multi(n: Nat, m: Nat): Nat := match n, m with
  | 0, 0 => add(1, 2)
  | a, b => add(a, b)
function named(n: Nat): Nat := match h : n with
  | 0 => add(1, 2)
  | Nat.succ k => add(k, 1)
function withMotive(n: Nat): Nat := match (motive := fun _ => Nat) n with
  | 0 => add(1, 2)
  | Nat.succ k => add(k, 1)
function options(n: Nat): Nat := match some n with
  | some (Nat.succ k) => add(k, 1)
  | some 0 => 0
  | none => 0
function alternatives(n: Nat): Nat := match n with
  | 0 | 1 => add(1, 2)
  | k => k
function pattern(n: Nat): Nat := (fun | 0 => add(1, 2) | Nat.succ k => add(k, 1))(n)
'''
guards = '''theorem unaryZero : unary 0 = 3 := rfl
theorem unaryFour : unary 4 = 4 := rfl
theorem multiZero : multi 0 0 = 3 := rfl
theorem multiValues : multi 2 3 = 5 := rfl
theorem namedValue : named 2 = 2 := rfl
theorem motiveValue : withMotive 0 = 3 := rfl
theorem optionValue : options 3 = 3 := rfl
theorem alternativeValue : alternatives 1 = 3 := rfl
theorem patternValue : pattern 3 = 3 := rfl
'''


def run(args, label):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, timeout=300)
    text = result.stdout + result.stderr
    (work / (label + '.log')).write_text(text)
    print(text, end='', flush=True)
    assert result.returncode == 0, (label, result.returncode)


comparisons = {}
for label, body in [('baseline', native), ('migrated', ps)]:
    source_root = work / (label + '-source')
    source_root.mkdir()
    source = source_root / 'MatchHostBootstrap.ps'
    source.write_text(header + body + guards)
    shutil.copy2(source, work / (label + '-MatchHostBootstrap.ps'))
    directory = work / (label + '-build')
    args = ['lake', '-R', '-f', 'lakefile.project.lean', '-KsourceRoot=' + str(source_root),
            '-Kroots=MatchHostBootstrap', '-KmoduleNames=MatchHostBootstrap', '-Kbootstrap=true',
            '-Kdriver=' + str(ROOT / '.lake/build/bin/ps0'), '-KprojectBuildDir=' + str(directory)]
    if label == 'migrated':
        args.append('-KsourceGrammar=true')
    run([*args, 'build', 'MatchHostBootstrap'], label)
    mapping = directory / 'lib/lean/MatchHostBootstrap.ilean.ps0-source-map.json'
    mapped = json.loads(mapping.read_text())
    assert mapped['source'].encode() == source.read_bytes()
    assert all(segment['kind'] == 'original' for segment in mapped['segments'])
    shutil.copy2(mapping, work / (label + '-source-map.json'))
    if label == 'migrated':
        census = directory / 'lib/lean/MatchHostBootstrap.ilean.ps0-source-census.json'
        observed = json.loads(census.read_text())
        rows = [c['declaration'] for c in observed['commands'] if c['declaration']]
        assert observed['imports'] == ['Init']
        assert len(rows) == 18 and all(d['mode'] == 'mapped-ps' for d in rows)
        shutil.copy2(census, work / 'migrated-source-census.json')
    for relative in ['ir/MatchHostBootstrap.c', 'lib/lean/MatchHostBootstrap.olean']:
        file = directory / relative
        comparisons.setdefault(relative, {})[label] = hashlib.sha256(file.read_bytes()).hexdigest()
        shutil.copy2(file, work / (label + '-MatchHostBootstrap' + file.suffix))
assert all(pair['baseline'] == pair['migrated'] for pair in comparisons.values())
(work / 'evidence.json').write_text(json.dumps(dict(source=os.environ['PS0_SOURCE_SHA'],
    comparisons=comparisons, mapped_definitions=9, mapped_theorems=9, logical_imports=['Init'],
    native_patterns_preserved=True, prepared_source_identity=True,
    scope='finite native term-match and pattern-lambda bodies; motive/discriminant/alternative operands with native pattern roles',
    grammar_migration_complete=False, verified_execution=False), indent=2) + '\n')
print('PS0_MATCH_HOST_NATIVE_PARITY: PASS', flush=True)
