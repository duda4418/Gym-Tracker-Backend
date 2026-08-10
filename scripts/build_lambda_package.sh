#!/usr/bin/env bash
set -euo pipefail

rm -rf build/lambda
mkdir -p build/lambda/package

python -m pip install \
  --disable-pip-version-check \
  --no-cache-dir \
  --requirement requirements-lambda.txt \
  --target build/lambda/package

cp -R app build/lambda/package/app
rm -rf \
  build/lambda/package/app/logs \
  build/lambda/package/app/scripts \
  build/lambda/package/app/tests \
  build/lambda/package/app/uploads/exercises
rm -f \
  build/lambda/package/app/uploads/exercises.json \
  "build/lambda/package/app/uploads/generate exercises.py"

(
  cd build/lambda/package
  zip -q -r ../lambda.zip .
)

compressed_bytes=$(stat --format=%s build/lambda/lambda.zip)
uncompressed_bytes=$(du --bytes --summarize build/lambda/package | cut --fields=1)

if (( compressed_bytes > 50 * 1024 * 1024 )); then
  echo "Lambda ZIP exceeds the 50 MB direct upload limit: ${compressed_bytes} bytes" >&2
  exit 1
fi

if (( uncompressed_bytes > 250 * 1024 * 1024 )); then
  echo "Lambda package exceeds the 250 MB extracted limit: ${uncompressed_bytes} bytes" >&2
  exit 1
fi

echo "Lambda package: ${compressed_bytes} compressed bytes, ${uncompressed_bytes} extracted bytes"