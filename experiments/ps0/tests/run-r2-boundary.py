#!/usr/bin/env python3
"""Run the numbered R2 source witnesses from the pinned reference."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

REFERENCE = Path(__file__).resolve().parents[1] / 'PS0_V1_LANGUAGE_REFERENCE.md'
NEGATIVE = {
    '01': r'unsolved goals',
    '05': r'Invalid pattern: Not enough arguments',
    '07': r'Invalid pattern: Not enough arguments',
    '11': r'PS0V1-CALL-GAP',
    '14': r'PS0V1-CALL|protected.*call|ambiguous.*call',
    '16': r'expected term|unexpected token',
    '20': r'adjacent explicit groups|unexpected token',
    '24': r'PS0V1-CALL-NAMED|duplicate.*argument',
    '25': r'PS0V1-CALL-EMPTY:.*required',
    '26': r'PS0V1-CALL-EMPTY:.*required',
    '28': r'unproved verification conditions for the contract',
    '31': r'PS0V1-CALL-GAP',
}
# Supplement the literal examples with observations that their stated oracles require.
SUPPLEMENT = {
    '02': ('example : True', 'theorem sequenceCloses : True', '#print axioms sequenceCloses\n'),
    '13': (None, None, '''open Lean in
run_cmd do
  let native ← Elab.liftMacroM nativeQ
  let host ← Elab.liftMacroM hostQ
  let tuple ← Elab.liftMacroM hostTupleQ
  let host ← Elab.liftMacroM (PS0.Syntax.lower `psTerm host.raw)
  let tuple ← Elab.liftMacroM (PS0.Syntax.lower `psTerm tuple.raw)
  unless native.raw.isOfKind ``Parser.Term.app && native.raw[1].getArgs.size == 1 &&
      host.isOfKind ``Parser.Term.app && host[1].getArgs.size == 2 &&
      tuple.isOfKind ``Parser.Term.app && tuple[1].getArgs.size == 1 do
    throwError "quotation argument partition"
'''),
    '21': (None, None, '''open Lean in
run_cmd do
  for (name, annotation) in [(``ordinaryDefault, ``optParam), (``automatic, ``autoParam)] do
    let .forallE _ type _ _ := (← getConstInfo name).type | throwError "missing telescope"
    unless type.getAppFn.isConstOf annotation do throwError "incorrect binder annotation"
'''),
    '27': (None, None, '''open Lean in
run_cmd do
  let some (.thmInfo _) := (← getEnv).find? ``plusOne.spec | throwError "missing checked spec"
  let assumptions ← collectAxioms ``plusOne.spec
  if assumptions.contains ``sorryAx then throwError "spec depends on sorry"
  logInfo m!"PS0_R2_SPEC_ASSUMPTIONS {assumptions}"
'''),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('driver', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True)
    examples = re.findall(r'^### R2-(\d\d)\.[^\n]*\n(?:(?!^### ).)*?^```proofscript\n(.*?)^```',
                          REFERENCE.read_text(encoding='utf-8'), re.M | re.S)
    if [case for case, _ in examples] != [f'{i:02}' for i in range(1, 32)]:
        raise ValueError('reference witness inventory changed')
    passed, failures, fixtures = [], [], {}
    for case, source in examples:
        if case in SUPPLEMENT:
            old, new, extra = SUPPLEMENT[case]
            if old:
                if source.count(old) != 1:
                    raise ValueError(f'missing exact source anchor for R2-{case}')
                source = source.replace(old, new)
            source += extra
        case_id = 'R2-' + case
        path = args.output / (case_id + '.ps')
        path.write_text(source, encoding='utf-8')
        fixtures[case_id] = hashlib.sha256(path.read_bytes()).hexdigest()
        result = subprocess.run([args.driver, 'check', path], text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
        log = result.stdout
        (args.output / (case_id + '.log')).write_text(log, encoding='utf-8')
        diagnostic = NEGATIVE.get(case)
        errors = [line for line in log.splitlines() if re.search(r':\d+:\d+: error(?:\([^)]*\))?:', line)]
        if diagnostic:
            ok = result.returncode == 1 and bool(errors) and all(
                re.search(diagnostic, line, re.I) for line in errors)
        else:
            ok = result.returncode == 0
        if case == '02':
            ok = ok and 'does not depend on any axioms' in log
        if case == '25':
            ok = ok and 'Nat → Nat' in log
        (passed if ok else failures).append(case_id)
        print(case_id, 'PASS' if ok else 'FAIL', result.returncode, log, flush=True)
    evidence = {'passed': passed, 'failures': failures, 'fixtures': fixtures,
                'driver_sha256': hashlib.sha256(args.driver.read_bytes()).hexdigest()}
    (args.output / 'result.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print('PS0_R2_BOUNDARY', json.dumps(evidence), flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
