const fs = require('fs');

module.exports = function (eleventyConfig) {
  // Assets passthrough with key static files
  eleventyConfig.addPassthroughCopy({
    'src/assets/': 'assets/',
    'src/robots.txt': 'robots.txt',
    'src/sitemap.xml': 'sitemap.xml',
  });

  // Optimized BrowserSync config
  eleventyConfig.setBrowserSyncConfig({
    notify: false,
    ui: false,
    ghostMode: false,
    delay: 500,
  });

  // Collections for organized template authoring
  eleventyConfig.addCollection('all', (collection) =>
    collection.getFilteredByGlob('src/**/*.{md,html,njk}')
  );

  // Utility filters
  eleventyConfig.addFilter('readableDate', (dateObj) => {
    return new Date(dateObj).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  });

  // Environment variable check
  const isDev = process.env.ELEVENTY_ENV === 'development';
  const isProd = process.env.ELEVENTY_ENV === 'production';

  return {
    dir: {
      input: 'src',
      includes: '_includes',
      layouts: '_includes/layouts',
      output: '_site',
      data: '_data',
    },
    passthroughFileCopy: true,
    markdownTemplateEngine: 'njk',
    htmlTemplateEngine: 'njk',
    templateFormats: ['md', 'njk', 'html', 'json'],
    incremental: isDev,
    quietMode: isProd,
  };
};
