const fs = require('fs');
const path = require('path');

function copyFile(src, dest) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
}

function copyDirectory(src, dest) {
  if (!fs.existsSync(src)) {
    console.warn(`Missing source directory: ${src}`);
    return;
  }
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirectory(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
      console.log(`Copied ${srcPath} -> ${destPath}`);
    }
  }
}

const filesToCopy = [
  { src: 'src/assets/css/tokens.css', dest: '_site/assets/css/tokens.css' },
  { src: 'assets/css/core.css', dest: '_site/assets/css/core.css' },
  { src: 'src/assets/img/logo/light-variant-logo.svg', dest: '_site/assets/img/logo/light-variant-logo.svg' },
  { src: 'src/assets/img/brand/evident-wordmark-light-hd.svg', dest: '_site/assets/img/brand/evident-wordmark-light-hd.svg' },
  { src: 'src/assets/img/apple-touch-icon.png', dest: '_site/assets/img/apple-touch-icon.png' },
  { src: 'src/assets/images/apple-touch-icon.png', dest: '_site/assets/images/apple-touch-icon.png' },
  { src: 'src/assets/images/logo-source.svg', dest: '_site/assets/images/logo-source.svg' },
  { src: 'src/favicon.ico', dest: '_site/favicon.ico' },
  { src: 'src/assets/media/flag.mp4', dest: '_site/assets/media/flag.mp4' },
];

filesToCopy.forEach(({ src, dest }) => {
  if (fs.existsSync(src)) {
    copyFile(src, dest);
    console.log(`Copied ${src} -> ${dest}`);
  } else {
    console.warn(`Missing source file: ${src}`);
  }
});

// Copy video renditions directory if it exists
if (fs.existsSync('src/assets/media/renditions')) {
  console.log('Copying video renditions...');
  copyDirectory('src/assets/media/renditions', '_site/assets/media/renditions');
}