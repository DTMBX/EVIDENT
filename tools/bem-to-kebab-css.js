// Copyright © 2024–2026 Faith Frontier Ecclesiastical Trust. All rights reserved.
// PROPRIETARY — See LICENSE.

#!/usr/bin/env node
const fs = require("fs").promises;
const path = require("path");

const root = path.join(__dirname, "..", "site");

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) {
      await walk(full);
    } else if (e.isFile()) {
      if (full.endsWith(".css")) await processCss(full);
    }
  }
}

async function processCss(file) {
  let s = await fs.readFile(file, "utf8");
  const orig = s;

  // Replace BEM-style class selectors in the CSS (only when preceded by a dot)
  s = s.replace(/\.([A-Za-z0-9_:-]*?(?:__|--)[A-Za-z0-9_:-]*)/g, (m, cls) => {
    // don't touch CSS variables (they start with -- and are not preceded by a dot)
    // transform the class token by replacing __ or -- with -
    const newCls = cls.replace(/__|--/g, "-");
    return "." + newCls;
  });

  if (s !== orig) {
    await fs.writeFile(file, s, "utf8");
    console.log("Updated CSS:", path.relative(process.cwd(), file));
  }
}

(async () => {
  try {
    console.log("Scanning CSS under", root);
    await walk(root);
    console.log("CSS conversion done. Run stylelint to verify.");
  } catch (err) {
    console.error(err);
    process.exit(1);
  }
})();
