#!/usr/bin/env bash
# Regenerate all synthetic CSVs under tests/testdata_generation/generated/.
# Run from repository root: ./tests/testdata_generation/run_all_generators.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPTS="$ROOT/tests/testdata_generation/scripts"
SEED="${TESTDATA_GEN_SEED:-42}"

cd "$SCRIPTS"

python3 generate_assets.py --size small --seed "$SEED"
python3 generate_assets.py --size medium --seed "$SEED"
python3 generate_assets.py --size large --seed "$SEED"

MEDIUM_MANIFEST="$ROOT/tests/testdata_generation/generated/assets/asset_registry_medium_manifest.json"
LARGE_MANIFEST="$ROOT/tests/testdata_generation/generated/assets/asset_registry_large_manifest.json"

python3 generate_firewall_rules.py --scenario clean --seed "$SEED" --asset-manifest "$MEDIUM_MANIFEST"
python3 generate_firewall_rules.py --scenario security_audit --seed "$SEED" --asset-manifest "$MEDIUM_MANIFEST"
python3 generate_firewall_rules.py --scenario all_facts --seed "$SEED" --asset-manifest "$MEDIUM_MANIFEST"
python3 generate_firewall_rules.py --scenario cross_zone --seed "$SEED" --asset-manifest "$MEDIUM_MANIFEST"
python3 generate_firewall_rules.py --scenario scale --seed "$SEED" --asset-manifest "$LARGE_MANIFEST"

python3 generate_error_scenarios.py

echo "All generators finished (seed=$SEED). Output under tests/testdata_generation/generated/"
