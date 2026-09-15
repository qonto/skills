#!/usr/bin/env node
// Privacy / secret scan for committed files. Fails if a KNOWN real sandbox value
// or a credential/URL pattern leaks into the repo. Synthetic fixture IBANs (fake)
// are intentionally allowed.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, extname } from 'node:path';

const ROOT = process.cwd();
const SKIP_DIRS = new Set(['node_modules', 'dist', '.git', '.finance-pr', 'coverage']);
const SKIP_EXT = new Set(['.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.pdf', '.lock']);

// Real values observed from the live sandbox during discovery — must never be committed.
const REAL_VALUES = [
  'FR7616958000017150169722768', // real main account IBAN
  'FR7618706000007218230636390',
  'FR7611315000010801687165972',
  'FR3720041010030807036V02448',
  '856160e6-2169-40b6-b670-d02a7f80248b', // real org id
  '019f55f1-0261-7d67-a6a4-55acde6d84d8', // real membership id
  '019f55f1-03b1-7936-a650-d428569e1a4b', // real bank account id
  '019f55f1-1fcf-78c2-8ab8-0185dd866d3d', // real supplier invoice id
  'victor.pimshin@edhec.com',
  'pimvic@gmail.com',
  '+33987654321',
];

// Credential / temporary-URL patterns that should never appear in committed files.
const PATTERNS = [
  { re: /X-Amz-(Signature|Credential|Security-Token)/i, label: 'presigned S3 URL param' },
  { re: /Authorization:\s*Bearer\s+[A-Za-z0-9._-]{16,}/i, label: 'bearer token' },
  { re: /\bsk-[A-Za-z0-9]{20,}\b/, label: 'OpenAI-style secret key' },
  { re: /https:\/\/[^\s"']*\.amazonaws\.com\/[^\s"']*token=/i, label: 'presigned attachment URL' },
];

// Files that legitimately reference the scan itself or document the denylist.
const ALLOW_FILES = new Set(['scripts/scan-secrets.mjs']);

function* walk(dir) {
  for (const name of readdirSync(dir)) {
    if (SKIP_DIRS.has(name)) continue;
    const full = join(dir, name);
    const st = statSync(full);
    if (st.isDirectory()) yield* walk(full);
    else if (!SKIP_EXT.has(extname(name))) yield full;
  }
}

const findings = [];
for (const file of walk(ROOT)) {
  const rel = file.slice(ROOT.length + 1);
  if (ALLOW_FILES.has(rel)) continue;
  let text;
  try {
    text = readFileSync(file, 'utf8');
  } catch {
    continue;
  }
  for (const v of REAL_VALUES) {
    if (text.includes(v)) findings.push(`${rel}: contains real sandbox value "${v.slice(0, 12)}…"`);
  }
  for (const { re, label } of PATTERNS) {
    if (re.test(text)) findings.push(`${rel}: matches ${label}`);
  }
}

if (findings.length) {
  console.error('✗ secret scan FAILED:\n' + findings.map((f) => '  - ' + f).join('\n'));
  process.exit(1);
}
console.log('✓ secret scan passed — no real sandbox values or credential patterns in committed files.');
