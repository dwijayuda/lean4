#!/usr/bin/env bash
# Copyright (c) 2026 Dwijayuda. All rights reserved.
# Released under Apache 2.0 license as described in LICENSE.
set -euo pipefail

if [[ $# != 1 ]]; then
  printf 'Usage: %s NEW_OUTPUT_DIRECTORY\n' "$0" >&2
  exit 2
fi

asset='ps0-bootstrap-lean4.35.0-978d594a-linux-x86_64.zip'
url='https://github.com/dwijayuda/pskernel/releases/download/ps0-bootstrap-lean4.35.0-978d594a-linux-x86_64'
digest='8c206edde04ade42d72faa33e191575c05b0662d757fd51d77b649baadc4dbbd'

mkdir -- "$1"
cd -- "$1"
curl --fail --silent --show-error --location --retry 5 --retry-all-errors \
  --connect-timeout 20 --max-time 600 "$url/$asset" -o "$asset"
curl --fail --silent --show-error --location --retry 5 --retry-all-errors \
  --connect-timeout 20 --max-time 120 "$url/SHA256SUMS" -o SHA256SUMS
printf '%s  %s\n' "$digest" "$asset" | cmp - SHA256SUMS
sha256sum -c SHA256SUMS
unzip -q "$asset"
printf 'PS0_RELEASE_BOOTSTRAP_VERIFIED: %s %s\n' "$asset" "$digest"
