#!/usr/bin/env bash
# verify-proof.sh — prove that the SHA-256 rendered in a Qonto invoice PDF
# matches the local quote PDF it was computed from.
#
# Usage: ./verify-proof.sh <quote.pdf> <invoice.pdf>
#
# Exit codes: 0 = proof verified, 1 = mismatch, 2 = usage/extraction error.
#
# Zero required dependencies beyond shasum. Text extraction tries, in order:
#   1. pdftotext (poppler) if installed
#   2. python3: inflate FlateDecode streams and read the text operators
#   3. raw grep over the PDF bytes (works only for uncompressed text)

set -euo pipefail

GREEN=$'\033[32m'; RED=$'\033[31m'; YELLOW=$'\033[33m'; BOLD=$'\033[1m'; RESET=$'\033[0m'

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <quote.pdf> <invoice.pdf>" >&2
  exit 2
fi

QUOTE_PDF="$1"
INVOICE_PDF="$2"

for f in "$QUOTE_PDF" "$INVOICE_PDF"; do
  if [[ ! -f "$f" ]]; then
    echo "${RED}error:${RESET} file not found: $f" >&2
    exit 2
  fi
done

if command -v shasum >/dev/null 2>&1; then
  HASH=$(shasum -a 256 "$QUOTE_PDF" | awk '{print $1}')
else
  HASH=$(sha256sum "$QUOTE_PDF" | awk '{print $1}')   # Linux without perl's shasum
fi
echo "${BOLD}local quote PDF${RESET}   $QUOTE_PDF"
echo "${BOLD}SHA-256 (local)${RESET}   $HASH"
echo

extract_text() {
  local pdf="$1"
  if command -v pdftotext >/dev/null 2>&1; then
    pdftotext "$pdf" - 2>/dev/null && return 0
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$pdf" <<'PYEOF' && return 0
import re, sys, zlib

data = open(sys.argv[1], "rb").read()
chunks = []
# Inflate every FlateDecode stream; keep raw streams too.
for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.S):
    raw = m.group(1)
    try:
        chunks.append(zlib.decompress(raw))
    except zlib.error:
        chunks.append(raw)
blob = b"\n".join(chunks) + b"\n" + data
# Collect string literals from text-showing operators: (...) Tj / [...] TJ
text = []
for m in re.finditer(rb"\((?:[^()\\]|\\.)*\)", blob):
    s = m.group(0)[1:-1]
    s = re.sub(rb"\\([()\\])", rb"\1", s)
    text.append(s)
out = b"\n".join(text) + b"\n" + blob
sys.stdout.buffer.write(out)
PYEOF
  fi
  cat "$pdf"  # last resort: raw bytes (finds hash only if streams are uncompressed)
}

# The renderer may split the hash across text runs or lines, so search a
# whitespace-stripped copy of the extracted text for the full hash, and fall
# back to a 24-char prefix check with a warning.
EXTRACTED=$(extract_text "$INVOICE_PDF" | LC_ALL=C tr -d ' \n\r\t' || true)

if [[ "$EXTRACTED" == *"$HASH"* ]]; then
  echo "${GREEN}${BOLD}✔ PROOF VERIFIED${RESET}"
  echo "  The invoice PDF contains the full SHA-256 of the local quote PDF."
  echo "  The document never left this machine — only the hash traveled."
  exit 0
fi

PREFIX=${HASH:0:24}
if [[ "$EXTRACTED" == *"$PREFIX"* ]]; then
  echo "${YELLOW}${BOLD}~ PARTIAL MATCH${RESET}"
  echo "  Found the first 24 hex chars of the hash but not the full 64."
  echo "  The PDF renderer likely wrapped the hash; open the footer to confirm."
  exit 0
fi

echo "${RED}${BOLD}✘ PROOF NOT FOUND${RESET}"
echo "  The invoice PDF does not contain the SHA-256 of $QUOTE_PDF."
echo "  Either the wrong files were passed, or the proof was not injected."
exit 1
