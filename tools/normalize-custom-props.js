// Copyright © 2024–2026 Faith Frontier Ecclesiastical Trust. All rights reserved.
// PROPRIETARY — See LICENSE.

#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const base = path.join(root, "site", "assets", "css");

function walk(dir) {
  let results = [];
  fs.readdirSync(dir, { withFileTypes: true }).forEach((d) => {
    const full = path.join(dir, d.name);
    if (d.isDirectory()) results = results.concat(walk(full));
    else if (d.isFile() && full.endsWith(".css")) results.push(full);
  });
  return results;
}

const files = walk(base);
let count = 0;
files.forEach((file) => {
  let src = fs.readFileSync(file, "utf8");
  const replaced = src
    .replace(
      /--Evident-([A-Za-z0-9-_]+)/g,
      (m, p1) => `--evident-${p1.toLowerCase()}`,
    )
    .replace(
      /var\(--Evident-([A-Za-z0-9-_]+)/g,
      (m, p1) => `var(--evident-${p1.toLowerCase()}`,
    );
  if (replaced !== src) {
    fs.writeFileSync(file, replaced, "utf8");
    console.log("Updated:", path.relative(root, file));
    count++;
  }
});
console.log(`Done. Updated ${count} files.`);
