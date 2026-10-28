#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
mkdir -p build/verified-logs
expected=eb6cafb7290e8bd5f2937522d8d804f58f02bafc
printf 'import Lean\n#eval Lean.githash\n' > build/verified-logs/SlicePin.lean
lake env lean build/verified-logs/SlicePin.lean > build/verified-logs/slice-pin.log 2>&1
grep -Fx "\"$expected\"" build/verified-logs/slice-pin.log
test "$(node --version)" = v22.23.3
: "${PS0_TSC:?PS0_TSC must point to the pinned tsc.js}"
test "$(node "$PS0_TSC" --version)" = 'Version 5.7.3'
command -v bwrap
# An unavailable sandbox is a gate failure. Do not disable the sandbox or
# globally relax runner security to manufacture a passing qualification.
bwrap --ro-bind / / --unshare-all --die-with-parent -- /bin/true
lake build +PS0.Verified.Extract
lake env lean tests/verified-resource-bound.lean > build/verified-logs/resource-bound.log 2>&1 || {
  cat build/verified-logs/resource-bound.log
  exit 1
}
python3 tests/test-proof-linked-host.py
python3 tests/proof-linked-qualification.py
