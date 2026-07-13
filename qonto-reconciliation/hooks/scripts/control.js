#!/usr/bin/env node
"use strict";

const { execFileSync } = require("child_process");
const path = require("path");

function main() {
  const action = process.argv[2];
  if (!["register-manifest", "close-run", "reset-run"].includes(action)) {
    throw new Error(`Unsupported control action: ${action || "missing"}`);
  }
  let manifest;
  if (action === "register-manifest") {
    let parsed;
    try {
      parsed = JSON.parse(process.argv[3] || "null");
    } catch (error) {
      throw new Error(`register-manifest argument is not valid JSON: ${error.message}`);
    }
    if (!parsed || !Array.isArray(parsed.suppliers)) {
      throw new Error('register-manifest argument must be an object shaped like {"suppliers":[...]}, not wrapped further (no extra "manifest" key).');
    }
    manifest = parsed;
  }
  const payload = action === "register-manifest" ? { manifest } : {};
  execFileSync(process.execPath, [path.join(__dirname, "harness.js"), action], {
    input: JSON.stringify(payload),
    stdio: ["pipe", "inherit", "inherit"]
  });
}

try {
  main();
} catch (error) {
  process.stderr.write(`qonto-reconciliation control failed: ${error.message}\n`);
  process.exitCode = 1;
}
