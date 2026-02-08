// Copyright © 2024–2026 Faith Frontier Ecclesiastical Trust. All rights reserved.
// PROPRIETARY — See LICENSE.

#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const site = path.join(root, "site");

function walk(dir, exts) {
  let results = [];
  fs.readdirSync(dir, { withFileTypes: true }).forEach((d) => {
    const full = path.join(dir, d.name);
    if (d.isDirectory()) results = results.concat(walk(full, exts));
    else if (d.isFile()) {
      if (!exts || exts.includes(path.extname(d.name))) results.push(full);
    }
  });
  return results;
}

// CSS files: replace .Evident-... selectors (scan site for any .css files)
const cssFiles = walk(site).filter((f) => f.endsWith(".css"));
let cssCount = 0;
cssFiles.forEach((file) => {
  if (!file.endsWith(".css")) return;
  const src = fs.readFileSync(file, "utf8");
  const replaced = src.replace(
    /\.Evident-([A-Za-z0-9_-]+)/g,
    (m, p1) => `.evident-${p1.toLowerCase()}`,
  );
  if (replaced !== src) {
    fs.writeFileSync(file, replaced, "utf8");
    console.log("CSS updated:", path.relative(root, file));
    cssCount++;
  }
});

// Markup and JS files: replace class and className occurrences
const markupExts = [".html", ".md", ".js", ".jsx", ".ts", ".tsx"];
const markupFiles = walk(site, markupExts);
let markupCount = 0;
markupFiles.forEach((file) => {
  const src = fs.readFileSync(file, "utf8");
  let replaced = src.replace(
    /(class(?:Name)?=\")(.*?\")/gs,
    (m, attr, rest) => {
      const inner = rest.slice(0, -1);
      const replacedInner = inner.replace(
        /Evident-([A-Za-z0-9_-]+)/g,
        (m2, p1) => `evident-${p1.toLowerCase()}`,
      );
      return `${attr}${replacedInner}\"`;
    },
  );
  // Also handle single-quoted attributes
  replaced = replaced.replace(
    /(class(?:Name)?=\')(.*?\')/gs,
    (m, attr, rest) => {
      const inner = rest.slice(0, -1);
      const replacedInner = inner.replace(
        /Evident-([A-Za-z0-9_-]+)/g,
        (m2, p1) => `evident-${p1.toLowerCase()}`,
      );
      return `${attr}${replacedInner}\'`;
    },
  );
  // classList.add('Evident-...') and similar
  replaced = replaced.replace(
    /(['\"])Evident-([A-Za-z0-9_-]+)(['\"])/g,
    (m, q1, p1, q2) => `${q1}evident-${p1.toLowerCase()}${q2}`,
  );

  if (replaced !== src) {
    fs.writeFileSync(file, replaced, "utf8");
    console.log("Markup updated:", path.relative(root, file));
    markupCount++;
  }
});

console.log(
  `Done. CSS files updated: ${cssCount}, markup files updated: ${markupCount}`,
);
