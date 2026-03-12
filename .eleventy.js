const markdownIt = require("markdown-it");

module.exports = function(eleventyConfig) {
  // Markdown configuration
  const md = markdownIt({
    html: true,
    linkify: true,
    typographer: true,
  });
  eleventyConfig.setLibrary("md", md);

  // Static asset passthrough copies
  eleventyConfig.addPassthroughCopy("src/style.css");
  eleventyConfig.addPassthroughCopy("src/output.css");
  eleventyConfig.addPassthroughCopy("src/app.js");
  eleventyConfig.addPassthroughCopy("src/data.json");
  eleventyConfig.addPassthroughCopy("src/data-real-benchmarks.json");
  eleventyConfig.addPassthroughCopy("src/favicon.svg");
  eleventyConfig.addPassthroughCopy("src/robots.txt");
  eleventyConfig.addPassthroughCopy("src/ads.txt");
  eleventyConfig.addPassthroughCopy("src/_headers");

  // Blog static assets passthrough (JSON data files, images)
  // HTML blog posts are processed by Eleventy so transforms can inject the nav
  eleventyConfig.addPassthroughCopy("src/blog/**/*.json");
  eleventyConfig.addPassthroughCopy("src/blog/**/*.png");
  eleventyConfig.addPassthroughCopy("src/blog/**/*.jpg");

  // Inject consistent site nav into legacy HTML blog posts that are missing it
  const PROPER_HEADER = `    <header class="bg-white border-b border-gray-200 sticky top-0 z-50">
        <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div class="flex justify-between items-center">
                <div class="flex items-center space-x-2">
                    <a href="/" class="text-2xl font-bold text-blue-600">TopClanker</a>
                    <span class="text-sm text-gray-500 hidden sm:inline">AI Agent Rankings</span>
                </div>
                <div class="flex space-x-6">
                    <a href="/#rankings" class="text-gray-700 hover:text-blue-600 font-medium">Rankings</a>
                    <a href="/#categories" class="text-gray-700 hover:text-blue-600 font-medium hidden sm:inline">Categories</a>
                    <a href="/methodology.html" class="text-gray-700 hover:text-blue-600 font-medium">Methodology</a>
                    <a href="/blog/" class="text-gray-700 hover:text-blue-600 font-medium">Blog</a>
                    <a href="/#learn" class="text-gray-700 hover:text-blue-600 font-medium hidden sm:inline">Learn</a>
                </div>
            </div>
        </nav>
    </header>`;

  eleventyConfig.addTransform("fix-blog-nav", function(content, outputPath) {
    if (!outputPath || !outputPath.endsWith(".html") || !outputPath.includes("/blog/")) {
      return content;
    }
    // Already has the proper Blog nav link — nothing to do
    if (content.includes('href="/blog/" class="text-gray-700 hover:text-blue-600 font-medium">Blog')) {
      return content;
    }

    // Dark-theme legacy posts (body is bg-gray-900): fix body class + replace minimal dark header
    if (/<body[^>]*bg-gray-900/.test(content)) {
      content = content.replace(
        /(<body[^>]*class=")[^"]*(")/,
        '$1bg-gray-50 text-gray-900$2'
      );
      content = content.replace(
        /<header[^>]*class="border-b border-gray-800"[\s\S]*?<\/header>/,
        PROPER_HEADER
      );
      return content;
    }

    // Light-theme posts missing Blog link: replace their old nav header
    if (/<header[^>]*class="bg-white border-b border-gray-200[^"]*"/.test(content)) {
      content = content.replace(
        /<header[^>]*class="bg-white border-b border-gray-200[^"]*"[\s\S]*?<\/header>/,
        PROPER_HEADER
      );
      return content;
    }

    return content;
  });

  // Blog posts collection — sorted newest first
  eleventyConfig.addCollection("posts", function(collectionApi) {
    return collectionApi.getFilteredByGlob("src/blog/*.md")
      .sort((a, b) => b.date - a.date);
  });

  // Date formatting filter
  eleventyConfig.addFilter("dateDisplay", function(date) {
    const d = date instanceof Date ? date : new Date(date);
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
      timeZone: "UTC",
    });
  });

  eleventyConfig.addFilter("dateISO", function(date) {
    const d = date instanceof Date ? date : new Date(date);
    return d.toISOString().split("T")[0];
  });

  // Limit filter — Nunjucks `slice` is chunking, not Array.slice
  eleventyConfig.addFilter("limit", (arr, n) => arr.slice(0, n));

  return {
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
      layouts: "_includes/layouts",
      data: "_data",
    },
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
    templateFormats: ["njk", "md", "html"],
  };
};
