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
echo "SLIM_SMOKE_PASSED:$MODE"
