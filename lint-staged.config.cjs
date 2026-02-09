module.exports = {
  '*.{css,scss}': ['prettier --write', 'stylelint --fix', 'git add'],
  '*.html': ['prettier --write', 'git add'],
  '*.{js,jsx,ts,tsx}': ['prettier --write', 'eslint --fix', 'git add'],
  '*.md': ['prettier --write', 'git add'],
  '*.json': ['prettier --write', 'git add'],
};
