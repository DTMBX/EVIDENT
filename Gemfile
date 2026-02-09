source "https://rubygems.org"

# Ruby version specification
ruby ">= 3.3.0"

# Jekyll for static site generation
gem "jekyll", "~> 4.4.1"

# Required for Ruby 3.0+
gem "csv"
gem "base64"
gem "bigdecimal"

# Core Jekyll plugins for SEO and feeds
gem "jekyll-feed", "~> 0.17"
gem "jekyll-sitemap", "~> 1.4"
gem "jekyll-seo-tag", "~> 2.8"

# Web server for local development (Ruby 3.0+)
gem "webrick", "~> 1.8"

# HTTP parser (performance)
gem "http_parser.rb", "~> 0.8.1"

group :development do
  gem "bundler", ">= 2.4.0"
end

# Platform-specific dependencies
platforms :mingw, :x64_mingw, :mswin, :jruby do
  gem "tzinfo", ">= 1", "< 3"
  gem "tzinfo-data"
end

# Windows performance optimization
gem "wdm", "~> 0.1", platforms: [:mingw, :x64_mingw, :mswin]

