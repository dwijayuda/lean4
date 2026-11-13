#!/usr/bin/env python3
# Copyright (c) 2026 Dwijayuda. All rights reserved.
# Released under Apache 2.0 license as described in LICENSE.
"""Qualify finite R2 call obligations through the ordinary PS0 checker."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

NEGATIVES = [
    ("01", "function f(x: Nat): Nat := x", "f (1)", "PS0V1-CALL-GAP"),
    ("02", "function f(x: Nat × Nat): Nat := x.1", "f (1, 2)", "PS0V1-CALL-GAP"),
    ("03", "function f(x: Unit): Nat := 1", "f ()", "PS0V1-CALL-GAP"),
    ("04", "function f(x: Nat): Nat := x", "f/- gap -/(1)", "PS0V1-CALL-GAP"),
    ("05", "const answer: Nat := 42", "answer()", "PS0V1-CALL-EMPTY: head is not callable"),
    ("06", "function one(x: Nat): Nat := x", "one()", "PS0V1-CALL-EMPTY: unresolved required non-Unit argument"),
    ("07", "function two(x: Unit, y: Unit): Nat := 2", "two()", "PS0V1-CALL-EMPTY: more than one required argument"),
    ("08", "def f {α : Type} (x : α) : Nat := 1", "f()", "PS0V1-CALL-EMPTY: unresolved implicit argument|PS0V1-CALL-EMPTY: unresolved required non-Unit argument"),
    ("09", "function f(name: Nat, y: Nat): Nat := name + y", "f(name := 1, 2)", "PS0V1-CALL-ORDER"),
    ("10", "function f(name: Nat): Nat := name", "f(name := 1, name := 2)", "PS0V1-CALL-NAMED"),
    ("11", "function f(name: Nat): Nat := name", "f(unknownName := 1)", "Invalid argument name.*unknownName|Invalid named argument.*unknownName"),
    ("12a", "function f(x: Nat): Nat := x", "f(,)", "unexpected token ','|expected term"),
    ("12b", "function f(x: Nat, y: Nat): Nat := x + y", "f(1,,2)", "unexpected token ','|expected term"),
]


def check(driver, fixture):
    result = subprocess.run([str(driver), 'check', str(fixture)], text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=45)
    return result.returncode, result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('driver', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    fixture = Path(__file__).parent / 'v1/r2_calls.ps'
    code, log = check(args.driver, fixture)
    (args.output / 'positive.log').write_text(log)
    passed = []
    failures = []
    if code == 0:
        passed.extend(f'PS0-P-CALL-{i:02}' for i in range(2, 11))
    else:
        failures.append('positive')
        print(log)
    for suffix, setup, expression, diagnostic in NEGATIVES:
        case = 'PS0-N-CALL-' + suffix
        path = args.output / (case + '.ps')
        path.write_text(setup + '\nconst bad: Nat := ' + expression + '\n')
        code, log = check(args.driver, path)
        (args.output / (case + '.log')).write_text(log)
        if code == 1 and any(re.search(diagnostic, line, re.IGNORECASE)
                             for line in log.splitlines() if re.search(r':2:\d+: error:', line)):
            passed.append(case)
        else:
            failures.append(case)
            print(case, code, log)
    result = {'passed': passed, 'failures': failures,
              'fixture_sha256': hashlib.sha256(fixture.read_bytes()).hexdigest(),
              'driver_sha256': hashlib.sha256(args.driver.read_bytes()).hexdigest()}
    (args.output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print('PS0_R2_CALLS', json.dumps(result), flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
