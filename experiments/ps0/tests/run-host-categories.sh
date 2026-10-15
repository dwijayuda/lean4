#!/usr/bin/env bash
# Focused component test, not a certificate of complete .ps frontend behavior.
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
logs=build/host-categories
mkdir -p "$logs"
expected=eb6cafb7290e8bd5f2937522d8d804f58f02bafc

# The exact official toolchain is required even in this isolated component lane.
cat > "$logs/Toolchain.lean" <<'LEAN'
import Lean
#eval Lean.githash
LEAN
lake env lean "$logs/Toolchain.lean" > "$logs/toolchain.log" 2>&1 || {
  cat "$logs/toolchain.log"
  exit 1
}
grep -Fx "\"$expected\"" "$logs/toolchain.log"
lake build +PS0.HostCategories 2>&1 | tee "$logs/build.log"

# Use the SAME committed fixtures in a deliberately minimal native harness.
# This does not replace the full ps0 check lane or claim module-source fidelity.
prepare() {
  local name="$1"
  printf 'import PS0.HostCategories\n' > "$logs/$name.lean"
  cat "tests/v1/$name.ps" >> "$logs/$name.lean"
}
for name in host_category_bridge host_postfix_calls; do
  prepare "$name"
  lake env lean "$logs/$name.lean" > "$logs/$name.log" 2>&1 || {
    cat "$logs/$name.log"
    exit 1
  }
done
for spec in \
  'host_call_named_then_positional|PS0V1-CALL-ORDER' \
  'host_call_duplicate_named|PS0V1-CALL-NAMED' \
  "host_call_comma_only|unexpected token ','" \
  "host_call_repeated_comma|unexpected token ','"; do
  name="${spec%%|*}"
  reason="${spec#*|}"
  prepare "$name"
  if lake env lean "$logs/$name.lean" > "$logs/$name.log" 2>&1; then
    echo "PS0_HOST_TEST: incorrectly accepted $name"
    exit 1
  fi
  grep -F "$reason" "$logs/$name.log" || {
    cat "$logs/$name.log"
    echo "PS0_HOST_TEST: failed for the wrong reason: $name"
    exit 1
  }
done
printf '%s\n' 'PS0_HOST_CATEGORIES: PASS (2 positive, 4 intended negative fixtures)'
