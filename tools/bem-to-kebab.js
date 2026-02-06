// Copyright © 2024–2026 Faith Frontier Ecclesiastical Trust. All rights reserved.
// PROPRIETARY — See LICENSE.

#!/usr/bin/env node
const fs = require("fs").promises;
const path = require("path");

const root = path.join(__dirname, "..", "site");
const exts = new Set([
  ".html",
  ".htm",
  ".md",
  ".js",
  ".jsx",
  ".ts",
  ".tsx",
  ".njk",
  ".jinja",
  ".jinja2",
  ".txt",
]);

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) {
      await walk(full);
    } else if (e.isFile()) {
      const ext = path.extname(e.name).toLowerCase();
      if (exts.has(ext)) await processFile(full);
    }
  }
}

async function processFile(file) {
  let s = await fs.readFile(file, "utf8");
  const orig = s;

  // 1) Replace in class and className attribute values
  s = s.replace(/(class(Name)?\s*=\s*['\"][^'\"]*['\"])/g, (m) => {
    return m.replace(/(__|--)/g, "-");
  });

  // 2) Replace in classList.add/remove/toggle calls
  s = s.replace(
    /(classList\.(?:add|remove|toggle)\s*\(\s*['\"][^'\"]*['\"]\s*\))/g,
    (m) => m.replace(/(__|--)/g, "-"),
  );

  // 3) Replace --${ to -${ inside templates
  s = s.replace(/--\$\{/g, "-${");
  s = s.replace(/__\$\{/g, "-${");

  // 4) General token replacement for class-like tokens appearing after whitespace or delimiters
  // Use lookarounds to avoid changing CSS variables or other leading dashes
  s = s.replace(
    /(?<=['"`\s>])([A-Za-z0-9_-]*(?:__|--)[A-Za-z0-9_-]*)(?=[\s'"`<>\)])/g,
    (m) => m.replace(/(__|--)/g, "-"),
  );

  if (s !== orig) {
    await fs.writeFile(file, s, "utf8");
    console.log("Updated:", path.relative(process.cwd(), file));
  }
}

(async () => {
  try {
    console.log("Scanning", root);
    await walk(root);
    console.log("Done. Review changes and run stylelint.");
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
})();
