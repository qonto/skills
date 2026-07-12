#!/usr/bin/env bash
# Parallel PUT of PDFs to signed Qonto S3 URLs.
#
# The agent handles `request_attachment_upload` and `upload_attachment` MCP calls
# directly (those live in MCP-land, not shell-land). This script only wraps the
# middle step: the fast, parallel curl PUTs to S3.
#
# Input: TSV lines on stdin, each `<url>\t<file_path>`. Empty lines and
# lines starting with `#` are skipped.
#
# Output: `<file_path>\t<http_status>` on stdout per PUT, in input order.
#
# Exit code: 0 if every PUT returned 200; 1 otherwise.
#
# Timing rule of thumb: keep the batch ≤ 6 URLs to stay well under the
# 15-minute signed URL expiry.
#
# Usage:
#   scripts/upload_batch_put.sh < batch.tsv
#   printf 'https://s3....\t/tmp/inv1.pdf\nhttps://s3....\t/tmp/inv2.pdf\n' \
#     | scripts/upload_batch_put.sh
set -euo pipefail

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

pids=()
lines=()
i=0

while IFS=$'\t' read -r url path; do
  [[ -z "$url" || "$url" == \#* ]] && continue
  if [[ ! -f "$path" ]]; then
    echo "$path	MISSING_FILE"
    continue
  fi
  lines+=("$path")
  (
    status=$(curl -sX PUT "$url" \
      -H "Content-Type: application/pdf" \
      --data-binary "@$path" \
      -w "%{http_code}" -o "$TMPDIR/body.$i")
    echo -n "$status" > "$TMPDIR/status.$i"
  ) &
  pids+=($!)
  i=$((i + 1))
done

wait "${pids[@]}" 2>/dev/null || true

fail=0
for j in "${!lines[@]}"; do
  status="$(cat "$TMPDIR/status.$j" 2>/dev/null || echo "?")"
  echo -e "${lines[$j]}\t${status}"
  if [[ "$status" != "200" ]]; then
    fail=1
    # Surface the first bit of the S3 error body to stderr (usually XML)
    head -c 400 "$TMPDIR/body.$j" >&2 || true
    echo >&2
  fi
done

exit $fail
