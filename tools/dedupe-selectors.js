// Copyright © 2024–2026 Faith Frontier Ecclesiastical Trust. All rights reserved.
// PROPRIETARY — See LICENSE.

#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const site = path.join(root, "site");

function walk(dir) {
  let results = [];
  fs.readdirSync(dir, { withFileTypes: true }).forEach((d) => {
    const full = path.join(dir, d.name);
    if (d.isDirectory()) results = results.concat(walk(full));
    else if (d.isFile() && full.endsWith(".css")) results.push(full);
  });
  return results;
}

function dedupeSelectorsIn(content) {
  return content.replace(/(^|\n)([^@\n][^{\n]*)\{/gm, (m, pre, sel) => {
    // sel is selector list possibly spanning multiple lines
    const parts = sel
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const seen = new Set();
    const unique = [];
    parts.forEach((p) => {
      if (!seen.has(p)) {
        seen.add(p);
        unique.push(p);
      }
    });
    return (pre || "") + unique.join(", ") + " {";
  });
}

const files = walk(site);
let total = 0;
files.forEach((file) => {
  const src = fs.readFileSync(file, "utf8");
  const out = dedupeSelectorsIn(src);
  if (out !== src) {
    fs.writeFileSync(file, out, "utf8");
    console.log("Deduped:", path.relative(root, file));
    total++;
  }
});
console.log(`Done. Processed ${total} files.`);
