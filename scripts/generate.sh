#!/usr/bin/env bash
# Regenerate the TypeScript client from spec/swagger.json.
# Uses the same openapi-generator image as CI, so local output matches CI output.
# Requires: docker, python3, node (CI does its own install/build).
set -euo pipefail

cd "$(dirname "$0")/.."

IMAGE="openapitools/openapi-generator-cli:v7.12.0"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Pulling $IMAGE ..."
  docker pull "$IMAGE"
fi

# swag leaves a few operations without responses; openapi-generator refuses
# those. Backfill before generating (no-op once the backend annotations land).
python3 scripts/normalize-spec.py spec/swagger.json

# The generator writes but never cleans; stale files from earlier specs would
# linger and break the build. Wipe generated output first (README.md, LICENSE,
# scripts/, spec/, .github/ and the generator-ignore file are hand-maintained
# or protected and stay).
rm -f package.json package-lock.json tsconfig.json tsconfig.esm.json
rm -rf src dist

docker run --rm \
  -u "$(id -u):$(id -g)" \
  -v "$PWD:/work" \
  -w /work \
  "$IMAGE" \
  generate \
    -i /work/spec/swagger.json \
    -g typescript-fetch \
    -o /work \
    -c /work/openapi-generator-config.json

echo
echo "Regenerated. Review with: git status && git diff"
