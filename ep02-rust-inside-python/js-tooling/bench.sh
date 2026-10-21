#!/usr/bin/env bash
# Same codebase, four tools. Run: npm install && npm run make-code && npm run bench
set -uo pipefail
cd "$(dirname "$0")"
[ -d src ] || node make-code.mjs
t() { local label=$1; shift; local s=$(date +%s.%N); "$@" >/dev/null 2>&1; local e=$(date +%s.%N); printf "%-22s %6.2fs\n" "$label" "$(echo "$e - $s" | bc)"; }
echo "Linting"
t "eslint (JavaScript)"  ./node_modules/.bin/eslint .
t "oxlint (Rust)"        ./node_modules/.bin/oxlint .
echo "Formatting check"
t "prettier (JavaScript)" ./node_modules/.bin/prettier --check src
t "biome (Rust)"          ./node_modules/.bin/biome format src
