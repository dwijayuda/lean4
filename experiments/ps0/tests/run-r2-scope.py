#!/usr/bin/env python3
# Copyright (c) 2026 Dwijayuda. All rights reserved.
# Released under Apache 2.0 license as described in LICENSE.
"""Run finite R2 scope and module witnesses with the native Lake frontend."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

MODULES = {
    'Scopes.Explicit': '''module
public import Init
namespace Explicit
def internalDefault : Nat := 7
private def hidden : Nat := 11
public section
def visible : Nat := 13
theorem visibleOracle : visible = 13 := rfl
end Explicit
''',
    'Scopes.Implicit': '''public import Init
namespace Implicit
def visible : Nat := 17
theorem visibleOracle : visible = 17 := rfl
end Implicit
''',
    'Scopes.MetaPublic': '''module
public import Init
public meta import Lean
public section
meta def metaPublic : Lean.Name := `r2Scope
''',
    'Scopes.MetaPrivate': '''module
import Init
meta import Lean
run_cmd do
  let name : Lean.Name := `r2Scope
  unless name.toString == "r2Scope" do Lean.throwError "private meta import"
''',
    'Scopes.Prelude': '''module
prelude
public section
inductive Marker where
  | witness : Marker
''',
    'Scopes.Grouping': '''public import Init
section
variable (n: Nat)
def scopedInc : Nat := n + 1
example : scopedInc 4 = 5 := rfl
end

section
variable (f : Nat → Nat) (x : Nat)
#check (f x)
theorem groupedExact (p : Prop) (hp : p) : p := by exact (hp)
end

namespace R2Scope
def original : Nat := 19
scoped notation "r2ScopedLit" => 23
end R2Scope

open scoped R2Scope
example : r2ScopedLit = 23 := rfl
open R2Scope renaming original → renamed
example : renamed = 19 := rfl
''',
    'Scopes.Consumer': '''module
public import Scopes.Explicit
public import Scopes.Implicit
meta import Scopes.MetaPublic
public section
example : Explicit.visible = 13 := Explicit.visibleOracle
example : Implicit.visible = 17 := Implicit.visibleOracle
run_cmd do
  unless metaPublic.toString == "r2Scope" do Lean.throwError "public meta import"
def main : IO Unit := IO.println s!"PS0_R2_SCOPE:{Explicit.visible}:{Implicit.visible}"
''',
    'Scopes.PrivateConsumer': '''module
import all Scopes.Explicit
example : Explicit.hidden = 11 := rfl
example : Explicit.internalDefault = 7 := rfl
''',
    'Scopes.Restricted': '''module
import Scopes.Explicit
def bad : Nat := Explicit.internalDefault
''',
    'Scopes.PublicAll': '''module
public import all Scopes.Explicit
''',
    'Scopes.LateImport': '''public import Init
def beforeImport : Nat := 2
import Init
''',
    'Scopes.MetaRuntime': '''module
import Init
meta import Lean
meta def metaValue : Nat := 2
def runtimeValue : Nat := metaValue
''',
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('driver', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    driver = args.driver.resolve()
    work = args.output.resolve()
    src = work / 'src'
    src.mkdir(parents=True)
    for name, raw in MODULES.items():
        path = src / Path(*name.split('.')).with_suffix('.ps')
        path.parent.mkdir(exist_ok=True)
        path.write_text(raw, encoding='utf-8')
    build = work / 'native'
    lake = ['lake', '-R', '-f', 'lakefile.project.lean', f'-KsourceRoot={src}',
            '-Kroots=Scopes', '-KrootModule=Scopes.Consumer',
            f'-Kdriver={driver}', f'-KprojectBuildDir={build}']
    passed = []
    failures = []

    def probe(label, command, check):
        result = subprocess.run([str(x) for x in command], stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, timeout=300)
        log = result.stdout
        (work / (label + '.log')).write_text(log, encoding='utf-8')
        if not check(result.returncode, log):
            failures.append(label)
            print(label, result.returncode, log, flush=True)
            return False
        return True

    positive = probe('positive', [*lake, 'build', 'ps0project', 'Scopes.PrivateConsumer',
                     'Scopes.Grouping', 'Scopes.Prelude', 'Scopes.MetaPrivate'],
                     lambda code, log: code == 0 and re.search(r'\(?f x\)? : Nat', log) is not None)
    if positive:
        assert probe('runtime', [build / 'bin/ps0project'],
                     lambda code, log: code == 0 and log.strip() == 'PS0_R2_SCOPE:13:17')
        prelude = build / 'lib/lean/Scopes/Prelude.ilean.ps0-source-map.json'
        data = json.loads(prelude.read_text())
        receipt = json.loads((build / 'ps0-inputs/Scopes.Prelude.json').read_text())
        assert receipt['header']['imports'] == []
        assert data['nativeSource'] == data['source'] == MODULES['Scopes.Prelude']
        assert all(span['kind'] == 'original' for span in data['segments'])
        passed.extend(f'PS0-P-SCOPE-{i:02}' for i in range(1, 9))
    if probe('PS0-N-MOD-01', [driver, 'lake-header', src / 'Scopes/PublicAll.ps'],
             lambda code, log: code == 1 and log.strip() == 'PS0-MODULE-HEADER: invalid import header'):
        passed.append('PS0-N-MOD-01')
    for label, module, match in [
        ('restricted', 'Restricted', r'Unknown identifier.*Explicit\.internalDefault|unknown constant.*Explicit\.internalDefault'),
        ('PS0-N-MOD-02', 'LateImport', r'import.*(?:beginning|header)|unexpected token .import.|invalid.*import'),
        ('PS0-N-MOD-03', 'MetaRuntime', r'Invalid definition .*runtimeValue.*may not access declaration .*metaValue.*marked as .meta.'),
    ]:
        if probe(label, [*lake, 'build', 'Scopes.' + module],
                 lambda code, log: code == 1 and any(re.search(match, line, re.I)
                    for line in log.splitlines() if re.search(r'error(?:\([^)]*\))?:', line) and f'{module}.ps:' in line)):
            if label != 'restricted':
                passed.append(label)
    result = {'passed': passed, 'failures': failures,
              'driver_sha256': hashlib.sha256(driver.read_bytes()).hexdigest(),
              'fixtures': {name: hashlib.sha256(raw.encode()).hexdigest() for name, raw in MODULES.items()}}
    (work / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PS0_R2_SCOPE', json.dumps(result), flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
