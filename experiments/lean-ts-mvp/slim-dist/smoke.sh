#!/usr/bin/env bash
# Exercise Lean in an isolated environment: no elan, Lake or upstream LEAN_PATH.
set -euo pipefail
DIST="$(cd "$1" && pwd -P)"
MODE="$2"
run_slim() {
  env -i HOME=/tmp PATH=/usr/bin:/bin \
    LEAN_SYSROOT="$DIST" LEAN_PATH="$DIST/lib/lean" \
    LD_LIBRARY_PATH="$DIST/lib/lean:$DIST/lib" \
    "$DIST/bin/lean" "$@"
}
run_slim --version
"$DIST/bin/lean-ts-lean" --version
if ! run_slim slim-dist/Smoke.lean > slim-smoke.log 2>&1; then
  cat slim-smoke.log
  exit 1
fi
cat slim-smoke.log
if ! run_slim Example.lean > slim-output.log 2>&1; then
  cat slim-output.log
  exit 1
fi
grep -q '@@LEAN_TS_BEGIN:increment@@' slim-output.log

if run_slim Reject.lean > slim-reject.log 2>&1; then
  echo "ERROR: unsupported constant was accepted" >&2
  exit 1
fi
grep -q 'unsupported executable constant' slim-reject.log
if run_slim BadProof.lean > slim-bad-proof.log 2>&1; then
  echo "ERROR: invalid proof was accepted" >&2
  exit 1
fi
grep -q 'error:' slim-bad-proof.log
test ! -e generated/afterBadProof.ts

node publish.mjs slim-output.log
npm run build
npm test
if [ -x "$DIST/bin/pscv0" ]; then
  run_pscv0() {
    env -i HOME=/tmp PATH=/usr/bin:/bin \
      LEAN_SYSROOT="$DIST" LEAN_PATH="$DIST/lib/lean" \
      LD_LIBRARY_PATH="$DIST/lib/lean:$DIST/lib" \
      "$DIST/bin/pscv0" "$@"
  }
  run_pscv0 check pscv0-tests/pass_minimal.ps > slim-pscv0.log 2>&1 || { cat slim-pscv0.log; exit 1; }
  grep -q "UNCERTIFIED" slim-pscv0.log
  if run_pscv0 check pscv0-tests/fail_gap_call.ps > slim-pscv0-rejected.log 2>&1; then
    echo "ERROR: distributed PSCV0 accepted forbidden spaced call" >&2
    exit 1
  fi
  grep -q "PSCV0-APP-02" slim-pscv0-rejected.log
  "$DIST/bin/psc" check pscv0-tests/pass_minimal.ps > slim-psc-launcher.log 2>&1 || { cat slim-psc-launcher.log; exit 1; }
  grep -q "UNCERTIFIED" slim-psc-launcher.log
  echo "DISTRIBUTED_PSCV0_PASSED:$MODE"
fi
echo "SLIM_SMOKE_PASSED:$MODE"
